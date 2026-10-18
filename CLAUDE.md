# Embedded Linux Kitabı — Çalışma Kuralları

Bu repo, bir Embedded Linux kursunun (BeagleBone Black) notlarından oluşan Türkçe bir kitaptır. Hedef okur: gömülü Linux'a yeni başlayan biri.

## Yapı

| Yer | Görev |
|---|---|
| `chapters/NN_isim.md` | Bölüm kaynakları. Bütün düzenlemeler burada yapılır. |
| `book.toml` | Bölüm sırası (`[[book.parts]]`) ve kursa bağlı değerler (`[vars.*]`). |
| `images/` | Görseller. `images/<konu>/NN_isim.png` terminal görüntüleri `tools/*_shots.py` ile üretilir. |
| `build/` | `python tools/book.py build` çıktısı (bölümler, `Embedded_Linux.md`, `Embedded_Linux.pdf`). Elle düzenlenmez. Kök `README.md` de build tarafından üretilir. |
| `tools/book.py` | `check`, `build`, `renumber` komutları |
| `sources/` | Git'e gönderilmeyen kaynaklar: kursun ders listesi (`sources/course_outline/`), slayt görüntüleri, ham notlar. Okunur ama kitaba konmaz. |

## Kaynaklar ve kursla eşleşme

- Kursun ders listesi: `sources/course_outline/ders_bolum_icerik.md` (kurs bölüm 12–21). Kursun reposu: https://github.com/niekiran/EmbeddedLinuxBBB (challenge'lar, makaleler, `notes/compilation_commands`, hazır imajlar, init betikleri).
- Kurs slaytları sadece kaynaktır; kitaba kendi metnimiz, diyagramlarımız ve terminal görüntülerimiz girer. Bootlin / beagleboard.org gibi CC BY-SA kaynaklardan görsel alınabilir, altına kaynak ve lisans yazılır.
- Kursun reposu eski (2017), videolar güncellenmiş. Sürüm iddialarını imajların kendisinden doğrula (ör. uImage başlığı, `strings u-boot.img`).
- Kitap her zaman güncel kalmalı: eskimiş bir komut/sürüm görürsen düzelt ve kursun farkını bir NOTE ile belirt.

Oturum başında SessionStart hook'u `book.py check --brief` çalıştırır. Çıktıda "Kitaba eklenmemiş notlar" görürsen aşağıdaki **Yeni not ekleme** adımlarını uygula; "build güncel değil" görürsen değişiklik yaptıktan sonra build al.

## Yeni not ekleme (kökte veya başka yerde yeni bir .md görünce)

1. Notu oku. Konusuna göre hangi kısma ve sıraya gireceğine karar ver (boot, U-Boot, kernel, rootfs, sürücü...). Yeni bir kısım gerekiyorsa `book.toml`'e `[[book.parts]]` ekle. Var olan bir bölümün devamıysa o bölüme yeni başlık olarak ekle; ayrı bir bölüm açma.
2. Dosyayı `chapters/NN_ingilizce_isim.md` olarak taşı (`git mv`; takip edilmiyorsa `mv`). Dosya adı **İngilizce**, snake_case.
3. `book.toml`'deki listeye ekle. Araya girdiyse `python tools/book.py renumber` çalıştır (dosya adlarını, `# Bölüm N` başlıklarını, `N.x` başlıklarını ve linkleri günceller).
4. Metni aşağıdaki **Yazım kuralları**na göre düzenle. Kullanıcının yazdığı teknik içeriği koru; yanlış/eski komutları düzelt ve neyi neden düzelttiğini kullanıcıya söyle.
5. Kursa bağlı değerleri (sürüm, IP, dosya adı...) `{{grup.isim}}` yer tutucusuyla yaz; yoksa `book.toml`'e ekle.
6. Terminal komutları için görüntü üret: `tools/<konu>_shots.py` (bkz. mevcut betikler; `set_default_out("images/<konu>")`, değerleri `V("grup.isim")` ile al).
7. Önsözdeki **Kitabın Haritası** tablosunu ve gerekirse diğer bölümlerdeki çapraz linkleri güncelle.
8. `python tools/book.py build` → `Kitap: N bölüm, sorun yok.` görene kadar düzelt.

## Kurs değişirse (kart, U-Boot/kernel/toolchain sürümü, IP...)

1. `book.toml`'deki ilgili `[vars]` değerini değiştir.
2. `python tools/book.py build` — bölümler, terminal görüntüleri ve PDF yeni değerle üretilir.
3. Değer değişikliği davranış değişikliği de getiriyorsa (ör. defconfig adı, `ethact` aygıt adı, `U-Boot#` → `=>` istemi, kernel'de `ttyO0` → `ttyS0`) ilgili bölümlerin metnini de güncelle; yer tutucu bunu tek başına çözmez. Kontrol edilmeyen bir iddia yazma.

## Yazım kuralları

- Dil Türkçe, okura "sen" diye hitap. Kısa, net cümleler. Sohbet ifadeleri yok ("senin notundaki", "önceki soruda" gibi).
- Her bölüm şu düzende:
  ```
  # Bölüm N — Başlık

  > <b>Bu bölümde:</b>
  > - ... (neler öğrenilecek)
  >
  > <b>Ön koşul:</b> [Bölüm X](0X_...md) — ...

  ---

  ## N.1 ...
  ...
  ## N.k Özet
  ## N.k+1 Karşılaşılabilecek Problemler   (varsa; Belirti | Sebep | Çözüm tablosu)
  ```
- Alt başlıklar `## N.x`, `### N.x.y`; adımlar `### Adım 1 — ...`. "Bölüm" kelimesi sadece bölümler için kullanılır; alt başlıklara `[4.5](#45-...)` biçiminde link verilir.
- Bölüm ve başlık referansları **her zaman link** olsun (`renumber` sadece linkleri günceller). Büyük **İ** ile başlayan başlığa link verme (slug'ı bozuk çıkar).
- Vurgu `<b>...</b>`, kod `` `...` ``, kutular GitHub alert'leri: `> [!NOTE]`, `[!TIP]`, `[!IMPORTANT]`, `[!WARNING]`, `[!CAUTION]`.
- Kod blokları dil etiketli: host komutları ```` ```bash ````, U-Boot ve kart komutları ```` ``` ```` veya ```` ```text ````. Mermaid kullanma (PDF'te çizilmez), diyagramlar metin.
- Komutlar hem terminal görüntüsü (temsili, `tools/term_shots.py` stili) hem de altında kopyalanabilir kod bloğu olarak verilir. Görüntülerin temsili olduğunu bölümde bir NOTE ile belirt.
- Görsel yolları `../images/...`, alt metin açıklayıcı (asla `alt text`).
- Kaynak gösterilen görseller (kurs slaytı, TRM, Bootlin) olduğu gibi kalır; lisansı/kaynağı altına yazılır.
