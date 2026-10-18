<!-- Bu dosya otomatik üretildi. Düzenlemek için chapters/ altındaki kaynağı değiştir. -->
# Bölüm 1 — BeagleBone Black Donanımı

> <b>Bu bölümde:</b>
> - BeagleBone Black'in işlemcisini, belleklerini ve bağlantı noktalarını tanıyacaksın.
> - Kartın üç butonunun (Power, Reset, Boot) ne işe yaradığını öğreneceksin.
> - Seri konsol için kullanacağın J1 debug header'ının pinlerini göreceksin.
>
> <b>Ön koşul:</b> Yok. Kitabın ilk bölümü.

> Kaynak: [BeagleBone Black resmi dokümanı (docs.beagleboard.org)](https://docs.beagleboard.org/boards/beaglebone/black/index.html). Bu bölümdeki kart görselleri bu dokümandan alınmıştır (CC BY-SA).

---

## 1.1 Genel Özellikler

| Özellik | Değer |
|---|---|
| <b>İşlemci (SoC)</b> | TI Sitara <b>AM3358BZCZ100</b>, ARM <b>Cortex-A8</b>, <b>1 GHz</b>'e kadar |
| <b>Cache</b> | 64 KB L1, 256 KB L2 |
| <b>RAM</b> | <b>512 MB DDR3L</b> (400 MHz clock, 800 MHz efektif) |
| <b>Dahili depolama</b> | <b>4 GB eMMC</b> (Rev C, eski revizyonlarda 2 GB), MMC1 üzerinden 8-bit |
| <b>Harici depolama</b> | <b>microSD</b> yuvası (MMC0) |
| <b>EEPROM</b> | 4 KB, I2C0 üzerinde. Kart adı, seri numarası ve revizyon bilgisini tutar. |
| <b>PMIC</b> | <b>TPS65217C</b> (güç yönetimi) + 3.3V için harici LDO (TLV70233) |
| <b>Ethernet</b> | 10/100 Mbit (RJ45) |
| <b>USB</b> | USB0: mini-USB <b>client</b> (PC bağlantısı), USB1: Type-A <b>host</b> (500 mA) |
| <b>Görüntü</b> | micro-HDMI (NXP TDA19988 HDMI framer) |
| <b>Genişleme</b> | <b>P8</b> ve <b>P9</b> (2 x 46 pin) header'ları, en fazla 4 cape takılabilir |
| <b>PRU-ICSS</b> | 2 adet 200 MHz gerçek zamanlı yardımcı çekirdek (PRU) |
| <b>Debug</b> | <b>J1</b>: 6 pinli seri debug header (UART0), opsiyonel 20 pinli JTAG (lehimli gelmez) |

## 1.2 Kart Üzerindeki Bileşenler

![BBB bileşenler](../images/beaglebone/bbb_bilesenler.jpg)

- <b>5VDC</b>: Barrel jack güç girişi (5V, en az 1A).
- <b>USB Client (mini-USB)</b>: Kartı bilgisayara bağlarsın. Hem güç verir hem de USB üzerinden ağ ve depolama sağlar. Kartın USB ağ adresi Windows'ta `192.168.7.2`, Linux ve macOS'ta `192.168.6.2`'dir ([5.4](05_emmc_boot.md#54-uygulama-emmcyi-güncelleme)).
- <b>Debug Serial Header (J1)</b>: Seri konsol bağlantısı. Kitap boyunca en çok kullanacağın yer burası.
- <b>Power / Reset / Boot Switch</b>: Kartın üç butonu ([1.5](#15-butonlar)).
- <b>User LEDs</b>: 4 adet mavi LED (USR0-USR3).

### Kart üzerindeki çipler

![BBB çipler](../images/beaglebone/bbb_cipler.jpg)

| Çip | Görevi |
|---|---|
| <b>AM3358BZCZ100</b> | Ana işlemci (SoC) |
| <b>DDR3</b> | 512 MB RAM |
| <b>eMMC</b> | Kart üstündeki flash bellek, varsayılan boot kaynağı |
| <b>TPS65217C</b> | PMIC. Tüm voltaj raylarını üretir ve power butonunu yönetir. |
| <b>Ethernet PHY</b> | Ethernet fiziksel katman çipi |
| <b>HDMI Framer</b> | LCD sinyallerini HDMI'a çevirir |

## 1.3 Blok Diyagram

![BBB blok diyagram](../images/beaglebone/bbb_blok_diyagram.jpg)

> [!NOTE]
> Diyagramda <b>2G eMMC</b> yazıyor çünkü eski revizyona ait. Rev C kartlarda eMMC <b>4 GB</b>'dır.

Diyagramdan çıkan önemli noktalar:
- <b>MMC1</b> → eMMC, <b>MMC0</b> → microSD. Kernel ve U-Boot tarafında bu isimleri sık göreceksin.
- <b>UART0</b> → Debug header (J1). Linux'ta `/dev/ttyS0` (eski kernel'lerde `/dev/ttyO0`) olarak görünür.
- <b>USB0</b> → Client portu, <b>USB1</b> → Host portu.

## 1.4 Güç

- <b>USB'den güç</b>: En fazla ~500 mA çeker. Bu modda P9'daki <b>VDD_5V</b> pinlerine güç gelmez.
- <b>DC jack'ten güç</b>: 5V ±0.25V, 1A önerilir. Cape takıyorsan daha yüksek akımlı bir adaptör gerekebilir.
- <b>Tipik tüketim (5V'ta)</b>: U-Boot'ta boşta ~210 mA, kernel boot sırasında ~460 mA (tepe), kernel boşta ~350 mA.

> [!WARNING]
> Kartı kapatmak için kabloyu çekme. `sudo poweroff` komutunu kullan veya <b>Power</b> butonuna kısa bas. Ani güç kesilmesi eMMC/SD karttaki dosya sistemini bozabilir.

## 1.5 Butonlar

| Buton | Kart üstündeki adı | Görevi |
|---|---|---|
| <b>Power</b> | S3 | Kısa basış işletim sistemine düzgün kapanma sinyali gönderir. <b>8 saniyeden uzun</b> basılı tutarsan kart zorla kapanır. |
| <b>Reset</b> | S1 | Kartı yeniden başlatır (warm reset). Boot modunu <b>değiştirmez</b>. |
| <b>Boot</b> | S2 | Güç verilirken basılı tutulursa boot sırasını değiştirir ([1.7](#17-boot-sırası-ve-s2-butonu)). |

## 1.6 LED'ler

![BBB LED'ler](../images/beaglebone/bbb_ledler.jpg)

- <b>Power LED</b> (mavi): Güç varken yanar. Açılışta yanıp sönüyorsa PMIC aşırı akım nedeniyle kartı kapatmış demektir.
- <b>User LED'ler (USR0-USR3)</b>: Yazılımdan GPIO ile kontrol edilir. Hazır Debian imajındaki varsayılan görevleri:

| LED | GPIO | Varsayılan görev (Debian imajı) |
|---|---|---|
| USR0 | GPIO1_21 | <b>heartbeat</b>: Kalp atışı gibi yanıp söner, "kernel çalışıyor" demektir |
| USR1 | GPIO1_22 | microSD erişimi |
| USR2 | GPIO1_23 | CPU aktivitesi |
| USR3 | GPIO1_24 | eMMC erişimi |

Linux'ta LED'leri şu dizinden kontrol edebilirsin:

```bash
ls /sys/class/leds/
echo none > /sys/class/leds/beaglebone:green:usr0/trigger
echo 1 > /sys/class/leds/beaglebone:green:usr0/brightness
```

User LED'lerin devre şeması (her LED bir transistör üzerinden GPIO ile sürülür):

![User LED şeması](../images/beaglebone/bbb_user_led_sema.png)

> [!TIP]
> USR0'ın kalp atışı gibi yanıp sönmesi kernel kodunda değil, <b>Device Tree</b>'de tanımlıdır ([10.5](10_device_tree.md#105-bir-device-treenin-genel-yapısı)).

## 1.7 Boot Sırası ve S2 Butonu

Kitap açısından <b>en önemli başlık budur.</b>

AM3358 açılırken <b>SYSBOOT</b> pinlerinin seviyesine bakar ve hangi kaynaktan boot edeceğine bu pinlere göre karar verir. <b>Boot (S2)</b> butonu bu bitlerden birini değiştirir.

![SYSBOOT tablosu](../images/beaglebone/bbb_sysboot_tablosu.jpg)

| Durum | Boot sırası |
|---|---|
| <b>S2 basılı değil</b> (varsayılan) | <b>MMC1 (eMMC)</b> → MMC0 (microSD) → UART0 → USB0 |
| <b>S2 basılı</b> (güç verilirken) | SPI0 → <b>MMC0 (microSD)</b> → USB0 → UART0 |

> [!IMPORTANT]
> Kendi derlediğin U-Boot/kernel'i <b>SD karttan</b> açmak için: Kartın gücünü kes, <b>S2</b>'yi basılı tut, gücü ver, birkaç saniye sonra bırak. Boot modu <b>sadece güç verilirken</b> okunur. Reset butonu boot modunu değiştirmez.

Boot zincirinin (ROM Code → SPL → U-Boot → Kernel) ayrıntıları ve SYSBOOT tablosunun nasıl okunduğu [Bölüm 3](03_boot_process.md)'te anlatılıyor.

## 1.8 Seri Debug Header (J1)

![J1 debug header](../images/beaglebone/bbb_debug_header_j1.jpg)

| J1 Pini | Sinyal | USB-TTL dönüştürücüde bağlanacağı yer |
|---|---|---|
| <b>1</b> | GND | GND |
| 2 | — | — |
| 3 | — | — |
| <b>4</b> | RX (kartın alıcısı) | Dönüştürücünün <b>TX</b>'i |
| <b>5</b> | TX (kartın vericisi) | Dönüştürücünün <b>RX</b>'i |
| 6 | — | — |

- 1 numaralı pin kart üzerinde <b>beyaz nokta</b> ile işaretlidir. FTDI kablosu kullanıyorsan siyah kablo (GND) bu pine gelir.
- Ayarlar: <b>115200 8N1</b>, flow control <b>kapalı</b> ([Bölüm 2](02_serial_console.md)).

> [!WARNING]
> Sinyaller <b>3.3V</b>'tur. USB-TTL dönüştürücünün <b>3.3V</b> modda olduğundan emin ol, 5V'luk dönüştürücü kartı bozabilir. Dönüştürücünün <b>VCC</b> pinini karta <b>bağlama</b>, sadece GND, TX ve RX yeterli.

## 1.9 Genişleme Header'ları (P8 ve P9)

![P8 ve P9](../images/beaglebone/bbb_p8_p9_header.jpg)

- Her biri 2x23 = <b>46 pin</b>. Toplam 92 pin.
- Pinler <b>multiplexed</b>: Aynı pin GPIO, UART, I2C, SPI, PWM gibi farklı görevlerde kullanılabilir. Hangi görevin seçileceği <b>pinmux</b> (device tree / overlay) ile belirlenir.

| Pin(ler) | Sinyal |
|---|---|
| P8_1, P8_2, P9_1, P9_2, P9_43-46 | <b>GND</b> |
| P9_3, P9_4 | <b>3.3V</b> |
| P9_5, P9_6 | <b>VDD_5V</b> (sadece DC jack'ten güç verilirken var) |
| P9_7, P9_8 | <b>SYS_5V</b> |
| P9_9 | PWR_BUT |
| P9_10 | SYS_RESETn |
| P9_32 | VADC (ADC referansı) |
| P9_33-40 | <b>AIN0-AIN6</b> (analog girişler) |
| P9_34 | AGND |

> [!CAUTION]
> - GPIO pinleri <b>3.3V</b>'tur ve <b>5V toleranslı değildir</b>. 5V sinyal bağlarsan işlemci bozulur.
> - Analog girişler (AIN) en fazla <b>1.8V</b> kabul eder.
> - Kart tamamen açılmadan (SYS_RESETn HIGH olmadan) pinlere dışarıdan sinyal verme.

## 1.10 Özet

1. Seri konsol (J1, 115200 8N1) en önemli debug aracın.
2. Varsayılan boot <b>eMMC</b>'den. Kendi imajını <b>SD karttan</b> açmak için <b>S2</b>'yi basılı tutarak güç ver.
3. Boot zinciri: <b>ROM → MLO (SPL) → U-Boot → Kernel + DTB → RootFS</b>.
4. eMMC = <b>MMC1</b>, microSD = <b>MMC0</b>.
5. Tüm I/O <b>3.3V</b>, ADC <b>1.8V</b>.

---

[← Önsöz](00_preface.md) · [İçindekiler](README.md) · [Bölüm 2: Seri Konsol ve Minicom →](02_serial_console.md)
