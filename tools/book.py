"""Embedded Linux kitabını kontrol eder ve derler.

Kullanım:
    python tools/book.py check [--brief]    sorunları listeler (kitaba eklenmemiş notlar, kırık linkler...)
    python tools/book.py build [--no-pdf] [--no-shots]
                                           book.toml'deki değerlerle build/ klasörünü üretir:
                                           bölümler, birleşik kitap (md + pdf), terminal görüntüleri
    python tools/book.py renumber          dosya adlarını ve bölüm/başlık numaralarını book.toml'deki
                                           sıraya göre yeniden düzenler (araya bölüm eklendiğinde)

Kaynak bölümler chapters/ altındadır. build/ klasörü otomatik üretilir, elle düzenlenmez.
"""
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tomllib
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHAPTERS = ROOT / "chapters"
BUILD = ROOT / "build"
CONFIG = ROOT / "book.toml"
STAMP = BUILD / ".stamp"
# Kitaba ait olmayan, kökte durabilecek md dosyaları
NOT_NOTES = {"README.md", "CLAUDE.md"}
EDGE_PATHS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome",
]

VAR_RE = re.compile(r"\{\{\s*([A-Za-z0-9_.]+)\s*\}\}")
LINK_RE = re.compile(r"(!?)\[((?:[^\[\]]|\[[^\]]*\])*)\]\(([^)\s]+)\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
FENCE_RE = re.compile(r"^\s*(?:>\s*)*(```|~~~)")
CHAPTER_H1_RE = re.compile(r"^# Bölüm (\d+) — (.+)$")
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# --------------------------------------------------------------------------- ayarlar

def load_config():
    with open(CONFIG, "rb") as f:
        cfg = tomllib.load(f)
    flat = {}

    def walk(prefix, node):
        for k, v in node.items():
            key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                walk(key, v)
            else:
                flat[key] = str(v)

    walk("", cfg.get("vars", {}))
    for _ in range(10):  # değerlerin içindeki {{...}} referanslarını çöz
        changed = False
        for k, v in flat.items():
            nv = VAR_RE.sub(lambda m: flat.get(m.group(1), m.group(0)), v)
            if nv != v:
                flat[k], changed = nv, True
        if not changed:
            break
    return cfg["book"], flat


def chapter_list(book):
    """[(numara, dosya adı, kısım başlığı veya None)] — önsöz 0 numaralıdır."""
    out = [(0, book["preface"], None)]
    n = 1
    for part in book["parts"]:
        for ch in part["chapters"]:
            out.append((n, ch, part["title"]))
            n += 1
    return out


def render_vars(text, flat, errors=None, where=""):
    def sub(m):
        if m.group(1) in flat:
            return flat[m.group(1)]
        if errors is not None:
            errors.append(f"{where}: bilinmeyen değişken {{{{{m.group(1)}}}}}")
        return m.group(0)
    return VAR_RE.sub(sub, text)


# --------------------------------------------------------------------------- markdown yardımcıları

def strip_inline(text):
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.replace("`", "").replace("**", "").replace("__", "")


def gh_slug(text):
    """GitHub'ın başlık id'si üretme kuralı (github-slugger)."""
    text = strip_inline(text).strip().lower()
    keep = "".join(c for c in text
                   if c in " -_" or unicodedata.category(c)[0] in "LMN")
    return keep.replace(" ", "-")


def iter_lines(text):
    """(satır no, satır, kod bloğu içinde mi) üretir."""
    in_code, fence = False, None
    for i, line in enumerate(text.split("\n")):
        m = FENCE_RE.match(line)
        if m:
            if not in_code:
                in_code, fence = True, m.group(1)
                yield i, line, True
                continue
            if m.group(1) == fence:
                in_code = False
                yield i, line, True
                continue
        yield i, line, in_code


def headings(text):
    """[(satır no, seviye, başlık metni, slug)] — GitHub gibi tekrar edenlere -1, -2 ekler."""
    seen, out = {}, []
    for i, line, code in iter_lines(text):
        if code:
            continue
        m = HEADING_RE.match(line)
        if not m:
            continue
        base = gh_slug(m.group(2))
        slug = base if base not in seen else f"{base}-{seen[base]}"
        seen[base] = seen.get(base, 0) + 1
        out.append((i, len(m.group(1)), m.group(2), slug))
    return out


def iter_links(text):
    """Kod blokları ve satır içi kod dışındaki linkleri (satır no, resim mi, metin, hedef) olarak verir."""
    for i, line, code in iter_lines(text):
        if code:
            continue
        clean = re.sub(r"`[^`]*`", lambda m: " " * len(m.group(0)), line)
        for m in LINK_RE.finditer(clean):
            yield i, m.group(1) == "!", line[m.start(2):m.end(2)], line[m.start(3):m.end(3)]


def is_external(target):
    return re.match(r"^[a-z]+:", target) is not None


# --------------------------------------------------------------------------- check

def find_orphans(listed):
    skip_dirs = {".git", ".claude", "build", "chapters", "sources", "node_modules", ".vscode"}
    out = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for fn in filenames:
            p = Path(dirpath) / fn
            if fn.endswith(".md") and not (p.parent == ROOT and fn in NOT_NOTES):
                out.append(p.relative_to(ROOT).as_posix())
    for p in CHAPTERS.glob("*.md"):
        if p.name not in listed:
            out.append(p.relative_to(ROOT).as_posix())
    return sorted(out)


def check_chapter_links(name, text, slugs_by_file, problems):
    for ln, is_img, label, target in iter_links(text):
        if is_external(target):
            continue
        path, _, anchor = target.partition("#")
        where = f"chapters/{name}:{ln + 1}"
        if path:
            dest = (CHAPTERS / path).resolve()
            if not dest.exists():
                problems.append(f"{where}: bulunamayan {'resim' if is_img else 'dosya'} → {target}")
                continue
            file_key = dest.name if dest.parent == CHAPTERS.resolve() else None
        else:
            file_key = name
        if anchor and file_key:
            if anchor not in slugs_by_file.get(file_key, set()):
                problems.append(f"{where}: bulunamayan başlık → {target}")


def inputs_hash(chapters):
    h = hashlib.sha256()
    files = [CONFIG] + [CHAPTERS / c for _, c, _ in chapters] + sorted((ROOT / "tools").glob("*.py"))
    for f in files:
        if f.exists():
            h.update(f.name.encode() + f.read_bytes())
    return h.hexdigest()


def check(brief=False):
    book, flat = load_config()
    chapters = chapter_list(book)
    listed = {c for _, c, _ in chapters}
    problems = []

    for _, name, _ in chapters:
        if not (CHAPTERS / name).exists():
            problems.append(f"book.toml'de var ama dosya yok: chapters/{name}")

    orphans = find_orphans(listed)

    texts, slugs = {}, {}
    for num, name, _ in chapters:
        p = CHAPTERS / name
        if not p.exists():
            continue
        src = p.read_text(encoding="utf-8")
        texts[name] = render_vars(src, flat, problems, f"chapters/{name}")
        slugs[name] = {s for _, _, _, s in headings(texts[name])}
        first = next((l for l in src.split("\n") if l.startswith("# ")), "")
        if num and not CHAPTER_H1_RE.match(first):
            problems.append(f"chapters/{name}: ilk başlık '# Bölüm {num} — Başlık' biçiminde değil")
        elif num and int(CHAPTER_H1_RE.match(first).group(1)) != num:
            problems.append(f"chapters/{name}: başlıktaki bölüm numarası {num} olmalı (renumber çalıştır)")
        if num and not name.startswith(f"{num:02d}_"):
            problems.append(f"chapters/{name}: dosya adı {num:02d}_ ile başlamalı (renumber çalıştır)")
    for name, text in texts.items():
        check_chapter_links(name, text, slugs, problems)

    stale = not STAMP.exists() or STAMP.read_text().strip() != inputs_hash(chapters)

    if brief:
        lines = []
        if orphans:
            lines.append("Kitaba eklenmemiş notlar: " + ", ".join(orphans)
                         + " → CLAUDE.md'deki 'Yeni not ekleme' adımlarını uygula.")
        if problems:
            lines.append(f"Kitapta {len(problems)} sorun var → python tools/book.py check")
        if stale:
            lines.append("build/ güncel değil → python tools/book.py build")
        print("\n".join(lines) if lines else f"Kitap: {len(chapters) - 1} bölüm, sorun yok.")
        return 0

    print(f"Kitap: önsöz + {len(chapters) - 1} bölüm")
    if orphans:
        print("\nKitaba eklenmemiş notlar:")
        for o in orphans:
            print(f"  - {o}")
    if problems:
        print(f"\nSorunlar ({len(problems)}):")
        for p in problems:
            print(f"  - {p}")
    if stale:
        print("\nbuild/ güncel değil: python tools/book.py build")
    if not (orphans or problems or stale):
        print("Sorun yok.")
    return 1 if (orphans or problems) else 0


# --------------------------------------------------------------------------- build

def chapter_title(text):
    first = next((l for l in text.split("\n") if l.startswith("# ")), "# ?")
    m = CHAPTER_H1_RE.match(first)
    return m.group(2) if m else first[2:].strip()


def nav_line(chapters, idx, titles):
    parts = []
    if idx > 0:
        n, name, _ = chapters[idx - 1]
        label = f"Bölüm {n}: {titles[name]}" if n else titles[name]
        parts.append(f"[← {label}]({name})")
    parts.append("[İçindekiler](README.md)")
    if idx + 1 < len(chapters):
        n, name, _ = chapters[idx + 1]
        parts.append(f"[Bölüm {n}: {titles[name]} →]({name})")
    return "\n\n---\n\n" + " · ".join(parts) + "\n"


def toc_lines(chapters, titles, link):
    lines, part = [], None
    for n, name, ptitle in chapters:
        if ptitle != part and ptitle is not None:
            pi = [p for _, _, p in chapters if p][::1]
            idx = list(dict.fromkeys(pi)).index(ptitle)
            lines.append(f"\n**Kısım {ROMAN[idx]} — {ptitle}**\n")
            part = ptitle
        label = f"Bölüm {n} — {titles[name]}" if n else titles[name]
        lines.append(f"- [{label}]({link(n, name)})")
    return lines


def combined_markdown(book, flat, chapters, texts, titles):
    """Bütün bölümleri tek dosyada birleştirir; başlıklara c<n>- önekli id verir ve linkleri yeniden yazar."""
    anchors = {}
    for n, name, _ in chapters:
        anchors[name] = {s: f"c{n}-{s}" for _, _, _, s in headings(texts[name])}

    def h1_anchor(n, name):
        return f"#c{n}-{headings(texts[name])[0][3]}"

    out = [f"# {book['title']}", "", f"**{book['subtitle']}**", "",
           '## <a name="icindekiler"></a>İçindekiler', ""]
    out += toc_lines(chapters, titles, h1_anchor)
    part = None
    for n, name, ptitle in chapters:
        text = texts[name]
        hs = {i: s for i, _, _, s in headings(text)}
        lines = text.split("\n")
        for i, s in hs.items():
            m = HEADING_RE.match(lines[i])
            lines[i] = f"{m.group(1)} <a name=\"{anchors[name][s]}\"></a>{m.group(2)}"
        body = "\n".join(lines)

        def relink(m):
            bang, label, target = m.group(1), m.group(2), m.group(3)
            if bang or is_external(target):
                return m.group(0)
            path, _, anchor = target.partition("#")
            dest = path or name
            if dest in anchors:
                dn = next(c for c, nm, _ in chapters if nm == dest)
                a = anchors[dest].get(anchor) if anchor else h1_anchor(dn, dest)[1:]
                if a:
                    return f"[{label}](#{a})"
            if path == "README.md":
                return f"[{label}](#icindekiler)"
            return m.group(0)

        body = LINK_RE.sub(relink, body)
        out.append('\n<div class="page-break"></div>\n')
        if ptitle != part and ptitle is not None:
            idx = list(dict.fromkeys(p for _, _, p in chapters if p)).index(ptitle)
            out.append(f'<div class="part-title">Kısım {ROMAN[idx]}<br>{ptitle}</div>\n')
            out.append('<div class="page-break"></div>\n')
            part = ptitle
        out.append(body)
    return "\n".join(out) + "\n"


PDF_CSS = """
@page { size: A4; margin: 18mm 16mm; }
body { font-family: 'Segoe UI', 'DejaVu Sans', sans-serif; font-size: 10.5pt; line-height: 1.5; color: #1f2328; }
h1 { font-size: 22pt; border-bottom: 2px solid #d0d7de; padding-bottom: 6px; margin-top: 0; }
h2 { font-size: 15pt; border-bottom: 1px solid #d0d7de; padding-bottom: 4px; margin-top: 26px; }
h3 { font-size: 12.5pt; margin-top: 20px; }
h2, h3, h4 { break-after: avoid; }
code { font-family: Consolas, 'DejaVu Sans Mono', monospace; font-size: 9pt; background: #f2f4f7; padding: 1px 4px; border-radius: 4px; }
pre { background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 6px; padding: 10px 12px; overflow-x: auto; white-space: pre-wrap; break-inside: avoid; }
pre code { background: none; padding: 0; font-size: 8.8pt; }
table { border-collapse: collapse; margin: 10px 0; width: 100%; font-size: 9.5pt; break-inside: auto; }
th, td { border: 1px solid #d0d7de; padding: 5px 8px; vertical-align: top; text-align: left; }
th { background: #f6f8fa; }
tr { break-inside: avoid; }
img { max-width: 100%; display: block; margin: 10px auto; break-inside: avoid; }
blockquote { margin: 12px 0; padding: 6px 14px; border-left: 4px solid #d0d7de; color: #3d444d; background: #fafbfc; break-inside: avoid; }
blockquote.callout { border-left-color: var(--c); background: color-mix(in srgb, var(--c) 7%, white); }
.callout-title { font-weight: 700; color: var(--c); margin-bottom: 2px; }
.note { --c: #0969da; } .tip { --c: #1a7f37; } .important { --c: #8250df; }
.warning { --c: #9a6700; } .caution { --c: #cf222e; }
.page-break { break-after: page; }
.part-title { font-size: 30pt; font-weight: 700; text-align: center; margin-top: 35vh; color: #24292f; line-height: 1.4; }
.cover { text-align: center; margin-top: 30vh; }
.cover h1 { border: none; font-size: 40pt; }
.cover p { font-size: 18pt; color: #57606a; }
a { color: #0969da; text-decoration: none; }
"""
CALLOUT_TITLES = {"NOTE": "Not", "TIP": "İpucu", "IMPORTANT": "Önemli",
                  "WARNING": "Uyarı", "CAUTION": "Dikkat"}


LIST_ITEM_RE = re.compile(r"^(\s*(?:>\s*)*)(?:[-*+]|\d+\.)\s")


def github_compat(md_text):
    """python-markdown'ı GitHub gibi davrandırır: listeden önce boş satır ister,
    ardışık alıntı bloklarını birleştirir. Bu farkları kapatmak için satır ekler."""
    out, prev, prev_code = [], "", False
    for _, line, code in iter_lines(md_text):
        if not code and not prev_code:
            m = LIST_ITEM_RE.match(line)
            pm = LIST_ITEM_RE.match(prev)
            quote = re.match(r"^((?:>\s*)*)", line).group(1)
            prev_body = prev[len(re.match(r"^((?:>\s*)*)", prev).group(1)):].strip()
            if m and not pm and prev_body and not prev.startswith("|") \
                    and re.match(r"^((?:>\s*)*)", prev).group(1).strip() == quote.strip():
                out.append(quote.rstrip())  # listeden önce boş satır
            if line.startswith(">") and prev == "" and out[-2:-1] and out[-2].startswith(">"):
                out.insert(len(out) - 1, "\n<!-- -->")  # iki ayrı alıntı bloğu
        out.append(line)
        prev, prev_code = line, code
    return "\n".join(out)


def markdown_to_html(md_text, title):
    import markdown
    md_text = github_compat(md_text)
    html = markdown.markdown(md_text, extensions=[
        "tables", "sane_lists", "pymdownx.superfences", "md_in_html"])
    html = re.sub(
        r"<blockquote>\s*<p>\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*",
        lambda m: (f'<blockquote class="callout {m.group(1).lower()}">'
                   f'<p class="callout-title">{CALLOUT_TITLES[m.group(1)]}</p><p>'),
        html)
    return (f"<!doctype html><html lang=\"tr\"><head><meta charset=\"utf-8\">"
            f"<title>{title}</title><style>{PDF_CSS}</style></head><body>{html}</body></html>")


def make_pdf(html_path, pdf_path):
    exe = next((p for p in EDGE_PATHS if Path(p).exists()), None) or shutil.which("msedge") \
        or shutil.which("chromium") or shutil.which("google-chrome")
    if not exe:
        print("  ! Edge/Chrome bulunamadı, PDF atlandı")
        return False
    if pdf_path.exists():
        pdf_path.unlink()
    profile = html_path.parent / "browser-profile"  # açık tarayıcı oturumundan bağımsız çalışsın
    subprocess.run([exe, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--user-data-dir={profile}", "--no-first-run", "--disable-extensions",
                    "--allow-file-access-from-files", "--virtual-time-budget=15000",
                    f"--print-to-pdf={pdf_path}", html_path.as_uri()],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
    return pdf_path.exists()


def run_shots():
    for script in sorted((ROOT / "tools").glob("*_shots.py")):
        r = subprocess.run([sys.executable, str(script)], cwd=ROOT,
                           capture_output=True, text=True, encoding="utf-8")
        status = "ok" if r.returncode == 0 else "HATA"
        print(f"  {status:4} {script.name}")
        if r.returncode:
            print(r.stderr.strip()[-800:])


def build(no_pdf=False, no_shots=False):
    book, flat = load_config()
    chapters = chapter_list(book)
    errors = []
    texts = {}
    for _, name, _ in chapters:
        texts[name] = render_vars((CHAPTERS / name).read_text(encoding="utf-8"),
                                  flat, errors, f"chapters/{name}")
    if errors:
        print("\n".join(errors))
        return 1
    titles = {name: chapter_title(texts[name]) for _, name, _ in chapters}

    if not no_shots:
        print("Terminal görüntüleri:")
        run_shots()

    BUILD.mkdir(exist_ok=True)
    for old in BUILD.glob("*.md"):
        old.unlink()
    for idx, (n, name, _) in enumerate(chapters):
        banner = "<!-- Bu dosya otomatik üretildi. Düzenlemek için chapters/ altındaki kaynağı değiştir. -->\n"
        (BUILD / name).write_text(banner + texts[name].rstrip() + nav_line(chapters, idx, titles),
                                  encoding="utf-8")

    toc = toc_lines(chapters, titles, lambda n, name: name)
    readme = [f"# {book['title']}", "", f"**{book['subtitle']}**", "",
              "> Otomatik üretildi: `python tools/book.py build`. Tek parça kitap: "
              "[Embedded_Linux.md](Embedded_Linux.md) · [Embedded_Linux.pdf](Embedded_Linux.pdf)", "",
              "## İçindekiler", ""] + toc
    (BUILD / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")

    root_toc = toc_lines(chapters, titles, lambda n, name: f"build/{name}")
    root_readme = [
        f"# {book['title']}", "", f"**{book['subtitle']}**", "",
        "<!-- Bu dosya otomatik üretildi (python tools/book.py build). Elle düzenleme. -->", "",
        "Gömülü Linux'a yeni başlayanlar için adım adım bir rehber: kartı tanımaktan, SD karttan, "
        "seri porttan ve ağdan boot etmeye, bootloader'ı kendin derlemeye ve device tree'ye kadar.", "",
        "📖 <b>Okumak için:</b> [build/README.md](build/README.md) (bölüm bölüm) · "
        "[Embedded_Linux.md](build/Embedded_Linux.md) (tek parça) · "
        "[Embedded_Linux.pdf](build/Embedded_Linux.pdf)", "",
        "## İçindekiler", ""] + root_toc + [
        "", "## Bu Repo Nasıl Çalışır?", "",
        "| Yer | Ne var? |", "|---|---|",
        "| `chapters/` | Bölümlerin kaynağı. Düzenleme burada yapılır. |",
        "| `book.toml` | Bölüm sırası ve kursa bağlı değerler (sürümler, IP'ler). Bölümlerde `{{grup.isim}}` olarak geçer. |",
        "| `images/` | Görseller. Terminal görüntüleri `tools/*_shots.py` ile üretilir. |",
        "| `build/` | Otomatik üretilen, okunacak kitap. Elle düzenlenmez. |",
        "| `CLAUDE.md` | Yazım kuralları ve yeni not ekleme adımları |", "",
        "```bash",
        "python tools/book.py check     # kitaba eklenmemiş not, kırık link, eski build var mı?",
        "python tools/book.py build     # build/ klasörünü, terminal görüntülerini ve PDF'i üret",
        "python tools/book.py renumber  # araya bölüm eklendiyse numaraları yeniden düzenle",
        "```", ""]
    (ROOT / "README.md").write_text("\n".join(root_readme), encoding="utf-8")

    combined = combined_markdown(book, flat, chapters, texts, titles)
    (BUILD / "Embedded_Linux.md").write_text(combined, encoding="utf-8")
    print(f"Bölümler: build/ ({len(chapters)} dosya) + build/Embedded_Linux.md")

    if not no_pdf:
        cover = (f'<div class="cover"><h1>{book["title"]}</h1><p>{book["subtitle"]}</p></div>\n'
                 '<div class="page-break"></div>\n')
        body = cover + "\n".join(combined.split("\n")[4:])  # başlık satırları yerine kapak
        cache = BUILD / ".cache"
        cache.mkdir(exist_ok=True)
        html_path = cache / "Embedded_Linux.html"
        html = markdown_to_html(body, book["title"]).replace('src="../images/', 'src="../../images/')
        html_path.write_text(html, encoding="utf-8")
        ok = make_pdf(html_path, BUILD / "Embedded_Linux.pdf")
        print("PDF: build/Embedded_Linux.pdf" if ok else "PDF üretilemedi")

    STAMP.write_text(inputs_hash(chapters))
    return check(brief=True)


# --------------------------------------------------------------------------- renumber

def renumber():
    book, _ = load_config()
    chapters = chapter_list(book)
    old_files = {name: (CHAPTERS / name).read_text(encoding="utf-8") for _, name, _ in chapters}
    rename = {}
    for n, name, _ in chapters:
        base = re.sub(r"^\d+_", "", name)
        rename[name] = f"{n:02d}_{base}"

    new_texts, slug_maps, num_maps = {}, {}, {}
    for n, name, _ in chapters:
        text = old_files[name]
        old_h = headings(text)
        lines = text.split("\n")
        m = CHAPTER_H1_RE.match(next((l for l in lines if l.startswith("# ")), ""))
        old_num = int(m.group(1)) if m else None
        if n and m:
            for i, _, _, _ in old_h:
                lines[i] = re.sub(rf"^(#+ (?:Bölüm )?){old_num}(?=\.\d| —)", rf"\g<1>{n}", lines[i])
        text = "\n".join(lines)
        new_h = headings(text)
        slug_maps[name] = {o[3]: nw[3] for o, nw in zip(old_h, new_h)}
        num_maps[name] = (old_num, n)
        new_texts[name] = text

    def relink(name):
        def sub(m):
            bang, label, target = m.group(1), m.group(2), m.group(3)
            if is_external(target):
                return m.group(0)
            path, sep, anchor = target.partition("#")
            dest = path or name
            if dest not in slug_maps:
                return m.group(0)
            if anchor:
                anchor = slug_maps[dest].get(anchor, anchor)
            old_num, new_num = num_maps[dest]
            if old_num is not None and new_num:
                label = re.sub(rf"^(Bölüm ){old_num}\b", rf"\g<1>{new_num}", label)
                label = re.sub(rf"^{old_num}(?=\.(\d|\s))", str(new_num), label)
            new_path = rename[path] if path else ""
            return f"{bang}[{label}]({new_path}{sep}{anchor})"
        return sub

    changed = 0
    for _, name, _ in chapters:
        text = LINK_RE.sub(relink(name), new_texts[name])
        target = CHAPTERS / rename[name]
        if rename[name] != name:
            subprocess.run(["git", "mv", str(CHAPTERS / name), str(target)], cwd=ROOT)
            changed += 1
        target.write_text(text, encoding="utf-8")

    cfg_text = CONFIG.read_text(encoding="utf-8")
    for old, new in rename.items():
        cfg_text = cfg_text.replace(f'"{old}"', f'"{new}"')
    CONFIG.write_text(cfg_text, encoding="utf-8")
    print(f"{changed} dosya yeniden adlandırıldı; başlık numaraları ve linkler güncellendi.")
    return check()


def main():
    args = sys.argv[1:]
    if not args or args[0] not in {"check", "build", "renumber"}:
        print(__doc__)
        return 2
    if args[0] == "check":
        return check(brief="--brief" in args)
    if args[0] == "build":
        return build(no_pdf="--no-pdf" in args, no_shots="--no-shots" in args)
    return renumber()


if __name__ == "__main__":
    sys.exit(main())
