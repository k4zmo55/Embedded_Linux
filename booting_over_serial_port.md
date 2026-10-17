# Seri Port (UART) Üzerinden Boot (BeagleBone Black)

Bu dokümanda BeagleBone Black'i <b>SD kart ve eMMC kullanmadan</b>, bütün boot dosyalarını bilgisayardan <b>seri port (UART0)</b> üzerinden göndererek açmayı inceleyeceğiz.

> [!NOTE]
> SD karttan boot için: [booting.md](booting.md) · U-Boot'a seri porttan dosya gönderme (`loady`) için: [uboot_uEnv_ve_seri_yukleme.md](uboot_uEnv_ve_seri_yukleme.md)

---

## 1. Dosya Transfer Protokolleri

![IP ağı ve UART üzerinden dosya transfer protokolleri](images/{CD17FB50-958F-4863-B8A4-DED33A61A342}.png)

Bilgisayardan karta dosya göndermenin iki yolu var:

| Bağlantı | Protokoller | Ne zaman kullanılır? |
|---|---|---|
| <b>IP ağı (Ethernet)</b> | TFTP, HTTP, FTP, SMTP... | Kartta çalışan bir ağ yığını (U-Boot veya Linux) varsa. Hızlıdır. |
| <b>UART (seri port)</b> | Xmodem, Ymodem, Zmodem, Kermit... | Ağ yokken veya kartta henüz hiçbir yazılım yokken. Yavaştır ama çok basittir. |

UART sadece ham baytları taşır; "dosya nerede başlıyor, nerede bitiyor, veri bozuldu mu?" gibi bilgileri taşımaz. <b>Xmodem / Ymodem</b> gibi protokoller veriyi paketlere bölüp her pakete kontrol bilgisi (checksum / CRC) ekler, bozuk paketi tekrar istetir.

| Protokol | Özellik |
|---|---|
| <b>Xmodem</b> | 128 bayt (Xmodem-1K'da 1024 bayt) paketler. Dosya adı ve boyutu göndermez. AM335x'in <b>ROM kodu</b> bunu kullanır. |
| <b>Ymodem</b> | Xmodem'in geliştirilmiş hali: dosya adını ve boyutunu da gönderir. U-Boot'ta `loady` komutu. |

---

## 2. Seri Boot Fikri

![Boot dosyaları bilgisayarda, UART0 ile karta seri bağlantı](images/{E3C79A57-76F0-41F6-B314-EE88AB46B638}.png)

Bütün boot dosyaları — <b>SPL, U-Boot, Linux kernel (uImage), DTB ve dosya sistemi</b> — kartta değil, <b>bilgisayarda (HOST)</b> durur. Kart ile bilgisayar arasındaki tek bağlantı, J1 header'daki <b>UART0</b> pinlerine bağlı USB-TTL seri kablodur. Kart açılırken her dosyayı bu kablo üzerinden sırayla göndeririz.

Bu yöntem şu durumlarda işe yarar:
- SD kart ve eMMC boşsa veya içindeki bootloader bozulduysa (kartı "kurtarmak" için).
- Yeni derlenmiş bir SPL / U-Boot'u karta yazmadan denemek için.

---

## 3. Kartı UART Boot Moduna Sokmak

![Seri boot nasıl çalışır: S2 basılı tutulur, S3 ile açılır, SD kart takılı olmaz](images/{A0655836-7172-4895-8690-5553D0FF2841}.png)

Kartı UART'tan boot ettirmek için SD karttan boot ederken yaptığımızın aynısını yaparız:

1. <b>S2 (BOOT)</b> butonuna basılı tut,
2. <b>S3 (POWER)</b> butonuna basıp bırak (veya beslemeyi tak),
3. Boot başladıktan sonra S2'yi bırak.

Tek fark: <b>SD kart takılı olmamalı.</b> Takılıysa ROM kodu boot dosyalarını SD karttan bulur ve UART'a hiç sıra gelmez.

### AM335x boot sırası

![AM335x boot sırası: S2 basılı değilken ve basılıyken](images/{A096CE0C-645B-42AB-8840-75924AC5A492}.png)

AM335x'in içindeki ROM kodu, açılışta `SYSBOOT[4:0]` pinlerine bakarak hangi çevre birimlerini hangi sırayla deneyeceğine karar verir. BBB'de S2 butonu bu pinlerden birinin değerini değiştirir:

| Sıra | S2 basılı <b>değil</b> | S2 <b>basılı</b> |
|---|---|---|
| 1 | MMC1 (eMMC) | SPI0 |
| 2 | MMC0 (SD kart) | MMC0 (SD kart) |
| 3 | UART0 | <b>USB0</b> |
| 4 | USB0 | <b>UART0</b> |

S2 basılı bir şekilde boot işlemi yaparsak ROM kodu sırayla her çevre biriminde geçerli bir boot image'ı olup olmadığını kontrol eder:

- <b>SPI0</b>: BBB'de SPI flash yok → hemen geçer.
- <b>MMC0</b>: SD kart takılı değil → hemen geçer.
- <b>USB0</b>: Burada farklı bir durum oluşuyor (aşağıda).
- <b>UART0</b>: Bizim istediğimiz yer.

### USB0 sorunu: 4.5 dakikalık bekleme

Eğer USB kablosu bu sırada karta takılıysa ve image dosyası USB üzerinden gönderilmiyorsa, ROM kodu bir sonraki boot aygıtı olan UART0'a geçmeden önce <b>4.5 dakikaya kadar</b> bekliyor. Bu süre dolduktan sonra UART0'a geçiyor.

![AM335x TRM: UART boot ayrıntıları ve USB boot için Silicon Errata notu](images/{F394BE8C-59F6-4D82-A192-63B1BE6F6FBA}.png)

AM335x Technical Reference Manual'ın (TRM) <b>26.1.8.6 USB Boot Procedure</b> bölümünde, USB boot'un kısıtlamaları için <b>Silicon Errata (SPRZ360)</b> belgesine bakılması söyleniyor:

![Silicon Errata Advisory 1.0.25: Ethernet boot başarısız olursa sistem 4.5 dakika bekler](images/{17AE38E2-B3D5-4F02-ADA3-822CF3DD8D76}.png)

Errata'daki <b>Advisory 1.0.25</b>'te Ethernet denilmiş, ancak bu durum USB için de geçerli. Çünkü AM335x'in ROM kodu USB boot'u, USB kablosu üzerinden <b>sanal bir Ethernet bağlantısı (RNDIS)</b> kurarak yapar. Yani USB boot aslında "USB üzerinden Ethernet boot"tur ve aynı 4.5 dakikalık beklemeye takılır.

### Çözüm: Kartı harici adaptörle beslemek

![SD kart ve P4 mini USB kablosu takılı olmamalı, kart güç adaptörüyle beslenmeli](images/{8D57F348-9C21-4AF9-9546-9BBA20F8C501}.png)

Peki bu bekleme süresinden nasıl kurtulabiliriz? Beslemeyi <b>P4 mini USB portundan değil</b>, harici bir <b>5V - 2A adaptör</b> yardımıyla (DC jack) yapacağız. USB kablosu takılı olmayınca ROM kodu USB0'da hiçbir şey bulamaz, hiç beklemeden UART0 sekansına geçer ve image yüklemesini oradan yaparız.

| Koşul | Neden? |
|---|---|
| <b>SD kart takılı olmamalı</b> | ROM, UART0'dan önce MMC0'ı dener; SD kartta MLO varsa oradan açılır. |
| <b>P4 (mini USB) kablosu takılı olmamalı</b> | Takılıysa USB0 boot denenir ve 4.5 dakika beklenir. |
| <b>Kart DC jack'ten 5V adaptörle beslenmeli</b> | USB kablosu çıkınca kartın beslemesi başka yerden gelmeli. |
| <b>UART0 seri kablosu bağlı olmalı</b> | Bütün dosyalar buradan gidecek. |

> [!WARNING]
> Seri kablonun (USB-TTL) <b>VCC / 5V</b> ucunu karta bağlama. J1 header'da sadece <b>GND, RX ve TX</b> bağlanır; kart zaten adaptörden besleniyor.

---

## 4. ROM Kodunun UART Boot Davranışı

![AM335x TRM 26.1.9.5: UART boot prosedürü](images/{18BDEDD5-58AF-4A87-AF53-C576A14BD9E6}.png)

TRM'nin <b>26.1.9.5 UART Boot Procedure</b> bölümüne göre:

| Konu | Değer |
|---|---|
| Kullanılan port | <b>UART0</b> (pinler: `uart0_rxd`, `uart0_txd`) |
| Ayarlar | <b>115200 baud, 8 bit, parity yok, 1 stop bit, flow control yok</b> (115200 8N1) |
| Protokol | <b>Xmodem</b> (ROM kodu Xmodem istemcisi olarak dosyayı alır) |
| Bilgisayar tarafı | HyperTerminal, Tera Term, <b>Minicom</b> gibi programlar kullanılabilir |
| Hız | 1K paketlerle yaklaşık <b>4 KB/s</b> |
| Zaman aşımı | ROM, 3 saniye içinde 10 kez bilgisayarı "dürter" (ekrana `C` karakteri basar). Cevap gelmezse veya transfer başladıktan sonra 3 saniye paket gelmezse UART boot iptal olur. |
| Hata kontrolü | Xmodem'in CRC-16 desteği; bozuk paket tekrar istenir |

> [!TIP]
> Minicom ekranında art arda `CCCC...` görmek, kartın UART boot moduna girip <b>dosya beklediği</b> anlamına gelir. 3 saniyelik süre kısa olduğu için Minicom'da gönderme menüsünü (`Ctrl-A` → `S` → <b>xmodem</b>) önceden hazırla.

---

## 5. Önerilen RAM Yükleme Adresleri

![Önerilen DDR RAM yükleme adresleri](images/{41B45262-4937-487E-BD2D-CC0D2D385CBF}.png)

U-Boot'a geldikten sonra kernel, DTB ve dosya sistemini RAM'e (DDR, `0x80000000`'dan başlar) yükleyeceğiz. Dosyaların birbirinin üzerine yazmaması için şu adresler kullanılır:

| Dosya | DDR RAM adresi |
|---|---|
| Linux kernel image (`uImage`) | `0x82000000` |
| FDT / DTB (`am335x-boneblack.dtb`) | `0x88000000` |
| RAMDISK / INITRAMFS | `0x88080000` |

Seri boot'ta SD kart ve eMMC kullanılmadığı için rootfs'i bağlayacak bir disk yoktur. Bu yüzden dosya sistemi de RAM'e yüklenir: <b>RAMDISK / INITRAMFS</b>, RAM'de duran küçük bir rootfs'tir. DTB'ye ayrılan alan `0x88000000` – `0x8807FFFF` arası (512 KB) olduğu için initramfs hemen arkasından, `0x88080000`'dan başlar.

---

## 6. Özet: Seri Boot Adımları

![Özet: UART boot modu, SPL, U-Boot ve diğer image'lar](images/{0208A16B-4B49-45CB-9126-49CCBFA1CF0F}.png)

```
Bilgisayar (HOST)                          BeagleBone Black
──────────────────                         ────────────────────────────────────────
                                           ROM kodu (S2 basılı, SD kart yok) → UART0
u-boot-spl.bin ──── Xmodem ──────────────► SPL çalışır (DDR'ı hazırlar)
u-boot.img     ──── Ymodem ──────────────► U-Boot çalışır → U-Boot# komut satırı
uImage         ──── loadx / loady ───────► 0x82000000
.dtb           ──── loadx / loady ───────► 0x88000000
initramfs      ──── loadx / loady ───────► 0x88080000
                                           bootm → Linux açılır
```

1. Önce kartı <b>UART boot moduna</b> sokarız (SD kart yok, USB kablosu yok, S2 basılı, adaptörle besleme).
2. UART boot moduna girince ROM kodu, <b>SPL</b>'i UART üzerinden <b>Xmodem</b> protokolüyle bekler. Bu yüzden bilgisayardan önce SPL'i göndeririz.
3. SPL kartta çalışır (DDR RAM'i hazırlar) ve bu sefer <b>U-Boot</b> image'ını bekler. U-Boot'u da göndeririz.
4. U-Boot'un kontrolü ele geçince, U-Boot'un <b>Xmodem / Ymodem</b> komutlarıyla (`loadx` / `loady`) diğer bütün boot image'larını (kernel, DTB, initramfs) kartın DDR belleğine indirir ve kartı boot ederiz.

> [!NOTE]
> ROM kodu SD karttaki `MLO` dosyasından farklı olarak, UART'tan gelen SPL'in başında <b>GP header</b> beklemez. Bu yüzden UART boot'ta `MLO` değil, U-Boot derlemesinin ürettiği ham <b>`u-boot-spl.bin`</b> gönderilir.
