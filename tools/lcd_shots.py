"""16x2 LCD bölümü için terminal ekran görüntülerini ve temsili LCD görsellerini üretir.

Kullanım: python tools/lcd_shots.py [çıktı klasörü]
"""
from PIL import Image, ImageDraw, ImageFont

from term_shots import (render, t, FG, DIM, GREEN, BLUE, YELLOW, CYAN, RED,
                        MAGENTA, ORANGE, FONT_B)
import term_shots
from term_shots import V, set_default_out

CC = V("build.cross_compile")
BOARD_IP = V("network.board_ip")
set_default_out("images/lcd")

BBB = "root@beaglebone: ~ (SSH)"


def r(cmd, path="~"):
    return [("root@beaglebone", GREEN), (":", FG), (path, BLUE), ("# ", FG), (cmd, FG)]


def host(cmd, path="~/code"):
    return [("mehmet@ubuntu", GREEN), (":", FG), (path, BLUE), ("$ ", FG), (cmd, FG)]


def note(text, color=FG, ann=""):
    return [(text, color), (ann, MAGENTA)] if ann else [(text, color)]


# ---------------------------------------------------------------------------
# Temsili LCD görselleri

LCD_BG = (40, 70, 160)          # mavi arka ışıklı LCD
LCD_CELL = (55, 90, 190)
LCD_ON = (230, 240, 255)
PCB = (20, 110, 60)

# lcd_turkish.c'deki desenlerle aynı
GLYPHS = {
    "ç": [0x00, 0x00, 0x0E, 0x10, 0x10, 0x0E, 0x04, 0x0C],
    "ğ": [0x11, 0x0E, 0x0F, 0x11, 0x0F, 0x01, 0x0E, 0x00],
    "ı": [0x00, 0x00, 0x0C, 0x04, 0x04, 0x04, 0x0E, 0x00],
    "ö": [0x0A, 0x00, 0x0E, 0x11, 0x11, 0x11, 0x0E, 0x00],
    "ş": [0x00, 0x0E, 0x10, 0x0E, 0x01, 0x1E, 0x04, 0x0C],
    "ü": [0x0A, 0x00, 0x11, 0x11, 0x11, 0x13, 0x0D, 0x00],
    "İ": [0x04, 0x00, 0x0E, 0x04, 0x04, 0x04, 0x0E, 0x00],
    "Ş": [0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E, 0x04],
}

DOT = 4
GAP = 1
CW = 5 * (DOT + GAP) + 6        # hücre genişliği
CH = 8 * (DOT + GAP) + 6        # hücre yüksekliği


def draw_glyph(d, x, y, rows, on=LCD_ON, off=LCD_CELL):
    for ry, bits in enumerate(rows):
        for rx in range(5):
            lit = bits & (1 << (4 - rx))
            px = x + 3 + rx * (DOT + GAP)
            py = y + 3 + ry * (DOT + GAP)
            d.rectangle([px, py, px + DOT - 1, py + DOT - 1], fill=on if lit else off)


_RASTER_FONT = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 70)


def _raster(ch):
    im = Image.new("L", (60, 90), 0)
    ImageDraw.Draw(im).text((30, 45), ch, font=_RASTER_FONT, fill=255, anchor="mm")
    return im


_CAP = _raster("H").getbbox()      # büyük harf kutusu = 5x7 nokta


def font_rows(ch):
    """Fonttaki karakteri 5x8 nokta matrisine örnekler (LCD görünümü için, temsili)."""
    im = _raster(ch)
    x0, y0, x1, y1 = _CAP
    cw, chh = (x1 - x0) / 5, (y1 - y0) / 7
    rows = []
    for ry in range(8):
        bits = 0
        for rx in range(5):
            box = (int(x0 + cw * rx), int(y0 + chh * ry),
                   int(x0 + cw * (rx + 1)), int(y0 + chh * (ry + 1)))
            reg = im.crop(box)
            n = max(1, reg.size[0] * reg.size[1])
            if sum(reg.tobytes()) / (n * 255) > 0.4:
                bits |= 1 << (4 - rx)
        rows.append(bits)
    return rows


def lcd_image(name, line1, line2):
    """16x2 LCD'yi 5x8 nokta matrisi görünümünde çizer (Türkçe harfler CGRAM desenleriyle)."""
    margin = 18
    w = margin * 2 + 16 * (CW + 3)
    h = margin * 2 + 2 * (CH + 5) + 18
    img = Image.new("RGB", (w + 24, h + 24), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w + 23, h + 23], 10, fill=PCB)
    d.rectangle([12, 12, w + 11, h + 11], fill=(15, 15, 15))
    d.rectangle([18, 18, w + 5, h + 5], fill=LCD_BG)
    for row, text in enumerate((line1, line2)):
        text = text.ljust(16)[:16]
        for col, ch in enumerate(text):
            x = 18 + margin + col * (CW + 3)
            y = 18 + margin + 9 + row * (CH + 5)
            d.rectangle([x, y, x + CW - 1, y + CH - 1], fill=LCD_CELL)
            draw_glyph(d, x, y, GLYPHS[ch] if ch in GLYPHS else font_rows(ch))
    path = f"{term_shots.OUT}/{name}"
    img.save(path)
    print(path, img.size)


def glyph_sheet(name):
    """CGRAM'e yüklenen 8 karakterin büyütülmüş nokta matrisleri."""
    big = 14
    cw = 5 * (big + 2) + 10
    ch = 8 * (big + 2) + 10
    w = 8 * (cw + 16) + 16
    h = ch + 60
    img = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(img)
    for i, (k, rows) in enumerate(GLYPHS.items()):
        x = 16 + i * (cw + 16)
        y = 10
        d.rectangle([x, y, x + cw - 1, y + ch - 1], fill=LCD_BG)
        for ry, bits in enumerate(rows):
            for rx in range(5):
                lit = bits & (1 << (4 - rx))
                px = x + 5 + rx * (big + 2)
                py = y + 5 + ry * (big + 2)
                d.rectangle([px, py, px + big - 1, py + big - 1],
                            fill=LCD_ON if lit else LCD_CELL)
        d.text((x + cw / 2, y + ch + 22), f"{k}  0x{8 + i:02X}", font=FONT_B,
               fill=(30, 30, 30), anchor="mm")
    path = f"{term_shots.OUT}/{name}"
    img.save(path)
    print(path, img.size)


# ---------------------------------------------------------------------------
# Terminal görüntüleri

# 1) Derleme ve lcd_text
render("01_build_run.png", "mehmet@ubuntu + BBB", [
    host(f"{CC}gcc -Wall -Ilib -I20_lcd -o lcd_text 20_lcd/lcd_text.c \\"),
    note("      20_lcd/lcd_driver.c lib/gpio_driver.c", FG),
    host(f"scp lcd_text root@{BOARD_IP}:~/"),
    t("--- BBB ---", MAGENTA),
    r('./lcd_text "Merhaba BBB, 16x2 LCD calisiyor"'),
    note("This Application prints your message on the 16x2 LCD", FG),
    note("Running, press Ctrl-C to stop", GREEN, "      <-- LCD: başlık, IP, mesaj, saat"),
    note("^C", DIM),
    note("LCD cleared, GPIOs released", GREEN),
])

# 2) Kayan yazı ve Türkçe karakterler
render("02_scroll_turkish.png", "mehmet@ubuntu + BBB", [
    host(f"{CC}gcc -Wall -Ilib -I20_lcd -o lcd_scroll 20_lcd/lcd_scroll.c \\"),
    note("      20_lcd/lcd_driver.c lib/gpio_driver.c", FG),
    host(f"{CC}gcc -Wall -Ilib -I20_lcd -o lcd_turkish 20_lcd/lcd_turkish.c \\"),
    note("      20_lcd/lcd_driver.c lib/gpio_driver.c", FG),
    host(f"scp lcd_scroll lcd_turkish root@{BOARD_IP}:~/"),
    t("--- BBB ---", MAGENTA),
    r('./lcd_scroll "First they ignore you," "then they laugh at you," "then you win!"'),
    note("Application to print text in scrollable fashion on LCD", FG),
    note("Scrolling 3 text(s), press Ctrl-C to stop", GREEN),
    note("^C", DIM),
    note("LCD cleared, GPIOs released", GREEN),
    r('./lcd_turkish "Gömülü Linux" "Işık ve şimşek"'),
])

# 3) Hatalar
render("03_errors.png", BBB + " (temsili hatalar)", [
    note("LCD'nin 1. satırı dolu kareler, 2. satır boş", RED, "  <-- besleme var, LCD başlatılmamış"),
    note("", FG, "                                 (ya da kontrast çok yüksek)"),
    note("LCD tamamen boş, arka ışık yanıyor", RED, "            <-- kontrast (V0) ayarsız"),
    note("Anlamsız karakterler, her çalıştırmada farklı", RED, "  <-- D4-D7 sırası yanlış / 4 bit başlatma yok"),
    t(""),
    r('./lcd_text "test"'),
    note("/sys/class/gpio/gpio66/direction: Permission denied", RED, "   <-- root olarak çalıştır"),
    note("GPIO 66 could not be configured as output", RED),
    note("Error: LCD init failed", RED),
])

# Temsili LCD ekranları
lcd_image("lcd_demo.png", "BBB LCD Demo", "")
lcd_image("lcd_ip.png", "eth0", BOARD_IP)
lcd_image("lcd_clock.png", "2026-10-19 Mon", "14:37:05")
lcd_image("lcd_turkish.png", "Gömülü Linux", "Işık ve şimşek")
glyph_sheet("cgram_glyphs.png")
