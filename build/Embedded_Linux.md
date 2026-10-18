# Embedded Linux

**BeagleBone Black ile Adım Adım**

## <a name="icindekiler"></a>İçindekiler

- [Önsöz](#c0-önsöz)

**Kısım I — Başlarken**

- [Bölüm 1 — BeagleBone Black Donanımı](#c1-bölüm-1--beaglebone-black-donanımı)
- [Bölüm 2 — Seri Konsol ve Minicom](#c2-bölüm-2--seri-konsol-ve-minicom)

**Kısım II — Boot Süreci**

- [Bölüm 3 — Linux Boot Süreci: RBL → SPL → U-Boot](#c3-bölüm-3--linux-boot-süreci-rbl--spl--u-boot)
- [Bölüm 4 — SD Karttan Boot](#c4-bölüm-4--sd-karttan-boot)
- [Bölüm 5 — eMMC'den Boot](#c5-bölüm-5--emmcden-boot)

**Kısım III — U-Boot ile Çalışmak**

- [Bölüm 6 — U-Boot Komut Satırı ve uEnv.txt](#c6-bölüm-6--u-boot-komut-satırı-ve-uenvtxt)
- [Bölüm 7 — Seri Porttan (UART) Boot](#c7-bölüm-7--seri-porttan-uart-boot)
- [Bölüm 8 — TFTP ile Ağdan Boot](#c8-bölüm-8--tftp-ile-ağdan-boot)
- [Bölüm 9 — Cross Toolchain, SPL ve U-Boot Derleme](#c9-bölüm-9--cross-toolchain-spl-ve-u-boot-derleme)

**Kısım IV — Linux Kernel**

- [Bölüm 10 — Linux Kernel: Kaynak Ağacı ve Derleme](#c10-bölüm-10--linux-kernel-kaynak-ağacı-ve-derleme)
- [Bölüm 11 — Linux Device Tree](#c11-bölüm-11--linux-device-tree)

**Kısım V — Root Filesystem**

- [Bölüm 12 — BusyBox ile Minimal Root Filesystem](#c12-bölüm-12--busybox-ile-minimal-root-filesystem)

<div class="page-break"></div>

# <a name="c0-önsöz"></a>Önsöz

Bu kitap, gömülü Linux'a (Embedded Linux) yeni başlayan biri için yazıldı. Bir <b>BeagleBone Black</b> kartını sıfırdan alıp önce hazır dosyalarla, sonra kendi derlediğin bootloader ile açacaksın. Her adımda <b>neyi neden yaptığını</b> görmen hedefleniyor.

Kitap, bir Embedded Linux kursunu ([https://github.com/niekiran/EmbeddedLinuxBBB](https://github.com/niekiran/EmbeddedLinuxBBB)) takip ederken alınan notlardan oluştu. Kursla birlikte de tek başına da okunabilir.

---

## <a name="c0-bir-embedded-linux-sistemi-nelerden-oluşur"></a>Bir Embedded Linux Sistemi Nelerden Oluşur?

Masaüstü bilgisayarda bu parçaları hiç görmeyiz; hepsi hazır gelir. Gömülü sistemde ise her birini tek tek hazırlamak, karta koymak ve birbirine bağlamak bizim işimizdir:

```
           ┌──────────────────────────────────────────────────┐
  KART     │ 4. Root filesystem  /bin /etc /lib ... programlar │  Bölüm 6, 12
           │ 3. Linux kernel  +  Device Tree (.dtb)            │  Bölüm 10, 11
           │ 2. Bootloader: ROM Code → SPL (MLO) → U-Boot      │  Bölüm 3 – 9
           └──────────────────────────────────────────────────┘
                            ▲ derlenir
           ┌──────────────────────────────────────────────────┐
  PC       │ 1. Cross toolchain: PC'de çalışıp ARM kodu üretir │  Bölüm 9
           └──────────────────────────────────────────────────┘
```

| Parça | Görevi | Kitaptaki yeri |
|---|---|---|
| <b>Cross toolchain</b> | PC'de (x86) çalışıp karta (ARM) uygun program üreten derleyici ve araçlar | [Bölüm 9](#c9-bölüm-9--cross-toolchain-spl-ve-u-boot-derleme) |
| <b>Bootloader</b> | Kart açılınca belleği hazırlar, kernel'i ve device tree'yi RAM'e yükleyip başlatır | [Bölüm 3](#c3-bölüm-3--linux-boot-süreci-rbl--spl--u-boot) – [Bölüm 9](#c9-bölüm-9--cross-toolchain-spl-ve-u-boot-derleme) |
| <b>Linux kernel + Device Tree</b> | İşletim sisteminin çekirdeği ve kartın donanımını kernel'e tarif eden dosya | [Bölüm 10](#c10-bölüm-10--linux-kernel-kaynak-ağacı-ve-derleme), [Bölüm 11](#c11-bölüm-11--linux-device-tree) |
| <b>Root filesystem</b> | Kernel açıldıktan sonra çalışan her şey: kabuk, komutlar, ayar dosyaları | [Bölüm 6](#c6-bölüm-6--u-boot-komut-satırı-ve-uenvtxt), [Bölüm 12](#c12-bölüm-12--busybox-ile-minimal-root-filesystem) |

---

## <a name="c0-kitabın-haritası"></a>Kitabın Haritası

| Kısım | Bölüm | Ne yapacaksın? |
|---|---|---|
| <b>I — Başlarken</b> | [1. BeagleBone Black Donanımı](#c1-bölüm-1--beaglebone-black-donanımı) | Kartı, butonları, LED'leri ve debug header'ını tanı |
| | [2. Seri Konsol ve Minicom](#c2-bölüm-2--seri-konsol-ve-minicom) | Kartın konsolunu bilgisayarda gör |
| <b>II — Boot Süreci</b> | [3. Linux Boot Süreci](#c3-bölüm-3--linux-boot-süreci-rbl--spl--u-boot) | Kart açılırken hangi programın hangi sırayla çalıştığını öğren |
| | [4. SD Karttan Boot](#c4-bölüm-4--sd-karttan-boot) | SD kartı hazırla, kartı adım adım SD karttan aç |
| | [5. eMMC'den Boot](#c5-bölüm-5--emmcden-boot) | Kartın dahili belleğine güncel Debian yükle |
| <b>III — U-Boot ile Çalışmak</b> | [6. U-Boot Komut Satırı ve uEnv.txt](#c6-bölüm-6--u-boot-komut-satırı-ve-uenvtxt) | U-Boot'u durdur, ayarlarını değiştir, rootfs'i tanı |
| | [7. Seri Porttan (UART) Boot](#c7-bölüm-7--seri-porttan-uart-boot) | Kartı SD kart ve eMMC olmadan, sadece seri kabloyla aç |
| | [8. TFTP ile Ağdan Boot](#c8-bölüm-8--tftp-ile-ağdan-boot) | Kernel'i her seferinde ağdan çekerek geliştirmeyi hızlandır |
| | [9. Cross Toolchain, SPL ve U-Boot Derleme](#c9-bölüm-9--cross-toolchain-spl-ve-u-boot-derleme) | Bootloader'ı kaynak koddan kendin derle |
| <b>IV — Linux Kernel</b> | [10. Linux Kernel: Kaynak Ağacı ve Derleme](#c10-bölüm-10--linux-kernel-kaynak-ağacı-ve-derleme) | Kernel kaynağında gezin, kernel'i ve modülleri derle |
| | [11. Linux Device Tree](#c11-bölüm-11--linux-device-tree) | Kernel'in donanımı nasıl tanıdığını öğren |
| <b>V — Root Filesystem</b> | [12. BusyBox ile Minimal Root Filesystem](#c12-bölüm-12--busybox-ile-minimal-root-filesystem) | Kendi rootfs'ini sıfırdan kur, NFS ile bilgisayardan aç |

<b>Hazırlanan bölümler:</b> Kursun kalan konuları kitaba eklendikçe bu tabloya girecek: Buildroot, Eclipse ile uygulama geliştirme, AM335x GPIO'ları ve sysfs, harici LED, 7-segment gösterge, MPU6050 ivmeölçer/jiroskop, 16x2 LCD.

<b>Okuma sırası:</b> Bölümler birbirinin üzerine kurulu. İlk kez okuyorsan sırayla git. Her bölümün başındaki <b>"Ön koşul"</b> satırı, o bölümden önce hangilerini bilmen gerektiğini söyler.

Her bölüm aynı düzende yazıldı:

1. <b>Bu bölümde:</b> Bölümün sonunda neleri yapabileceğin.
2. <b>Konu anlatımı ve adım adım uygulama:</b> Komutlar hem terminal görüntüsü olarak hem de kopyalanabilir kod bloğu olarak verilir.
3. <b>Özet:</b> Bölümün tek bakışta tekrarı.
4. <b>Karşılaşılabilecek problemler:</b> Sık görülen hatalar, sebepleri ve çözümleri.

---

## <a name="c0-gerekenler"></a>Gerekenler

| Donanım | Neden? |
|---|---|
| BeagleBone Black (Rev C) | Kitabın kartı |
| microSD kart (en az 4 GB) + kart okuyucu | SD karttan boot için |
| USB-TTL seri dönüştürücü (<b>3.3V</b>) | Kartın konsolunu görmek için. En önemli debug aracın. |
| 5V / 2A adaptör (barrel jack) | Seri boot ve TFTP bölümlerinde karta güvenilir güç için |
| Ethernet kablosu | TFTP ile ağdan boot için |
| Mini USB kablo | Karta güç vermek ve USB üzerinden SSH için |

| Yazılım | Not |
|---|---|
| <b>Ubuntu</b> (host PC) | Gerçek kurulum ya da sanal makine. Sanal makinede ağ ayarı <b>Bridged</b> olmalı ([Bölüm 8](#c8-bölüm-8--tftp-ile-ağdan-boot)). |
| `minicom`, `lrzsz` | Seri konsol ve Xmodem/Ymodem ile dosya gönderme ([Bölüm 2](#c2-bölüm-2--seri-konsol-ve-minicom)) |
| `gparted` | SD kartı bölümlemek için ([Bölüm 4](#c4-bölüm-4--sd-karttan-boot)) |
| `tftpd-hpa` | TFTP sunucusu ([Bölüm 8](#c8-bölüm-8--tftp-ile-ağdan-boot)) |
| `nfs-kernel-server` | Rootfs'i ağdan bağlamak için NFS sunucusu ([Bölüm 12](#c12-bölüm-12--busybox-ile-minimal-root-filesystem)) |
| Cross toolchain, U-Boot, kernel, BusyBox kaynakları | Derleme bölümlerinde kurulur ([Bölüm 9](#c9-bölüm-9--cross-toolchain-spl-ve-u-boot-derleme), [Bölüm 10](#c10-bölüm-10--linux-kernel-kaynak-ağacı-ve-derleme), [Bölüm 12](#c12-bölüm-12--busybox-ile-minimal-root-filesystem)) |

---

## <a name="c0-bu-kitaptaki-sürümler"></a>Bu Kitaptaki Sürümler

Komutlarda ve ekran görüntülerinde geçen sürümler şunlardır. Kendi kurulumunda farklı bir sürüm kullanıyorsan komutlardaki sürüm numaralarını ona göre değiştir.

| Ne? | Değer | Bölüm |
|---|---|---|
| Kursun ilk hazır imajları (Ångström): U-Boot / kernel | 2013.04 / 3.8.13 | 4, 6, 7, 8 |
| Kursun seri boot imajları: SPL / U-Boot | 2017.03 / 2016.11-rc1 | 7 |
| Kursun güncel SD kart imajları: U-Boot / kernel | 2022.04 / 5.10.168 | 4, 8 |
| eMMC'ye yüklenen Debian imajı | `bone-debian-10.3-iot-armhf-2020-04-06-4gb.img.xz` | 5 |
| Kendi derlediğimiz U-Boot | 2022.04 (`am335x_evm_defconfig`) | 9 |
| Cross toolchain | Linaro GCC 7.5.0 (7.5-2019.12) | 9, 10, 12 |
| Kendi derlediğimiz kernel | 5.10.162 (BeagleBoard, dal `5.10`, `bb.org_defconfig`) | 10 |
| BusyBox / Dropbear | 1.36.1 / 2022.83 | 12 |
| Host PC IP / kart IP | 192.168.27.1 / 192.168.27.2 | 8 |

---

## <a name="c0-yazım-kuralları"></a>Yazım Kuralları

<b>Komut satırları:</b> Bir komutun nerede çalıştırılacağını başındaki işaretten anlarsın.

| Görünüm | Nerede? |
|---|---|
| `mehmet@ubuntu:~$ komut` veya kod bloğunda `bash` | Host PC'deki Ubuntu terminali |
| `U-Boot# komut` veya `=> komut` | Kartın U-Boot komut satırı (seri konsolda). Eski U-Boot `U-Boot#`, yenisi `=>` gösterir. |
| `root@beaglebone:~# komut` veya `/ # komut` | Kartta açılmış Linux (seri konsol veya SSH) |

<b>Ekran görüntüleri:</b> Koyu renkli terminal görüntüleri adımları göstermek için hazırlanmış <b>temsili</b> çıktılardır. Sürüm, tarih, boyut ve hız değerleri senin kartında farklı görünebilir. Kursun slaytlarından ve programların kendisinden alınan görüntüler ise olduğu gibi kullanıldı.

<b>Kutular:</b>

> [!NOTE]
> Ek bilgi, arka plan.

> [!TIP]
> İşini kolaylaştıracak bir yol.

> [!IMPORTANT]
> Atlarsan adımın çalışmayacağı bilgi.

> [!WARNING]
> Dikkat etmezsen zaman kaybettirecek veya bir şeyi bozacak durum.

> [!CAUTION]
> Veri kaybına veya donanım hasarına yol açabilecek durum.

---

## <a name="c0-kaynaklar"></a>Kaynaklar

- Kursun deposu: [https://github.com/niekiran/EmbeddedLinuxBBB](https://github.com/niekiran/EmbeddedLinuxBBB)
- [BeagleBone Black resmi dokümanı](https://docs.beagleboard.org/boards/beaglebone/black/index.html)
- AM335x Technical Reference Manual (TRM): repodaki `am335x_referance_manuel.pdf`
- [U-Boot dokümantasyonu](https://docs.u-boot.org/)
- [Bootlin eğitim materyalleri](https://bootlin.com/training/) (CC BY-SA 3.0)


<div class="page-break"></div>

<div class="part-title">Kısım I<br>Başlarken</div>

<div class="page-break"></div>

# <a name="c1-bölüm-1--beaglebone-black-donanımı"></a>Bölüm 1 — BeagleBone Black Donanımı

> <b>Bu bölümde:</b>
> - BeagleBone Black'in işlemcisini, belleklerini ve bağlantı noktalarını tanıyacaksın.
> - Kartın üç butonunun (Power, Reset, Boot) ne işe yaradığını öğreneceksin.
> - Seri konsol için kullanacağın J1 debug header'ının pinlerini göreceksin.
>
> <b>Ön koşul:</b> Yok. Kitabın ilk bölümü.

> Kaynak: [BeagleBone Black resmi dokümanı (docs.beagleboard.org)](https://docs.beagleboard.org/boards/beaglebone/black/index.html). Bu bölümdeki kart görselleri bu dokümandan alınmıştır (CC BY-SA).

---

## <a name="c1-11-genel-özellikler"></a>1.1 Genel Özellikler

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

## <a name="c1-12-kart-üzerindeki-bileşenler"></a>1.2 Kart Üzerindeki Bileşenler

![BBB bileşenler](../images/beaglebone/bbb_bilesenler.jpg)

- <b>5VDC</b>: Barrel jack güç girişi (5V, en az 1A).
- <b>USB Client (mini-USB)</b>: Kartı bilgisayara bağlarsın. Hem güç verir hem de USB üzerinden ağ ve depolama sağlar. Kartın USB ağ adresi Windows'ta `192.168.7.2`, Linux ve macOS'ta `192.168.6.2`'dir ([5.4](#c5-54-uygulama-emmcyi-güncelleme)).
- <b>Debug Serial Header (J1)</b>: Seri konsol bağlantısı. Kitap boyunca en çok kullanacağın yer burası.
- <b>Power / Reset / Boot Switch</b>: Kartın üç butonu ([1.5](#c1-15-butonlar)).
- <b>User LEDs</b>: 4 adet mavi LED (USR0-USR3).

### <a name="c1-kart-üzerindeki-çipler"></a>Kart üzerindeki çipler

![BBB çipler](../images/beaglebone/bbb_cipler.jpg)

| Çip | Görevi |
|---|---|
| <b>AM3358BZCZ100</b> | Ana işlemci (SoC) |
| <b>DDR3</b> | 512 MB RAM |
| <b>eMMC</b> | Kart üstündeki flash bellek, varsayılan boot kaynağı |
| <b>TPS65217C</b> | PMIC. Tüm voltaj raylarını üretir ve power butonunu yönetir. |
| <b>Ethernet PHY</b> | Ethernet fiziksel katman çipi |
| <b>HDMI Framer</b> | LCD sinyallerini HDMI'a çevirir |

## <a name="c1-13-blok-diyagram"></a>1.3 Blok Diyagram

![BBB blok diyagram](../images/beaglebone/bbb_blok_diyagram.jpg)

> [!NOTE]
> Diyagramda <b>2G eMMC</b> yazıyor çünkü eski revizyona ait. Rev C kartlarda eMMC <b>4 GB</b>'dır.

Diyagramdan çıkan önemli noktalar:
- <b>MMC1</b> → eMMC, <b>MMC0</b> → microSD. Kernel ve U-Boot tarafında bu isimleri sık göreceksin.
- <b>UART0</b> → Debug header (J1). Linux'ta `/dev/ttyS0` (eski kernel'lerde `/dev/ttyO0`) olarak görünür.
- <b>USB0</b> → Client portu, <b>USB1</b> → Host portu.

## <a name="c1-14-güç"></a>1.4 Güç

- <b>USB'den güç</b>: En fazla ~500 mA çeker. Bu modda P9'daki <b>VDD_5V</b> pinlerine güç gelmez.
- <b>DC jack'ten güç</b>: 5V ±0.25V, 1A önerilir. Cape takıyorsan daha yüksek akımlı bir adaptör gerekebilir.
- <b>Tipik tüketim (5V'ta)</b>: U-Boot'ta boşta ~210 mA, kernel boot sırasında ~460 mA (tepe), kernel boşta ~350 mA.

> [!WARNING]
> Kartı kapatmak için kabloyu çekme. `sudo poweroff` komutunu kullan veya <b>Power</b> butonuna kısa bas. Ani güç kesilmesi eMMC/SD karttaki dosya sistemini bozabilir.

## <a name="c1-15-butonlar"></a>1.5 Butonlar

| Buton | Kart üstündeki adı | Görevi |
|---|---|---|
| <b>Power</b> | S3 | Kısa basış işletim sistemine düzgün kapanma sinyali gönderir. <b>8 saniyeden uzun</b> basılı tutarsan kart zorla kapanır. |
| <b>Reset</b> | S1 | Kartı yeniden başlatır (warm reset). Boot modunu <b>değiştirmez</b>. |
| <b>Boot</b> | S2 | Güç verilirken basılı tutulursa boot sırasını değiştirir ([1.7](#c1-17-boot-sırası-ve-s2-butonu)). |

## <a name="c1-16-ledler"></a>1.6 LED'ler

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
> USR0'ın kalp atışı gibi yanıp sönmesi kernel kodunda değil, <b>Device Tree</b>'de tanımlıdır ([11.5](#c11-115-bir-device-treenin-genel-yapısı)).

## <a name="c1-17-boot-sırası-ve-s2-butonu"></a>1.7 Boot Sırası ve S2 Butonu

Kitap açısından <b>en önemli başlık budur.</b>

AM3358 açılırken <b>SYSBOOT</b> pinlerinin seviyesine bakar ve hangi kaynaktan boot edeceğine bu pinlere göre karar verir. <b>Boot (S2)</b> butonu bu bitlerden birini değiştirir.

![SYSBOOT tablosu](../images/beaglebone/bbb_sysboot_tablosu.jpg)

| Durum | Boot sırası |
|---|---|
| <b>S2 basılı değil</b> (varsayılan) | <b>MMC1 (eMMC)</b> → MMC0 (microSD) → UART0 → USB0 |
| <b>S2 basılı</b> (güç verilirken) | SPI0 → <b>MMC0 (microSD)</b> → USB0 → UART0 |

> [!IMPORTANT]
> Kendi derlediğin U-Boot/kernel'i <b>SD karttan</b> açmak için: Kartın gücünü kes, <b>S2</b>'yi basılı tut, gücü ver, birkaç saniye sonra bırak. Boot modu <b>sadece güç verilirken</b> okunur. Reset butonu boot modunu değiştirmez.

Boot zincirinin (ROM Code → SPL → U-Boot → Kernel) ayrıntıları ve SYSBOOT tablosunun nasıl okunduğu [Bölüm 3](#c3-bölüm-3--linux-boot-süreci-rbl--spl--u-boot)'te anlatılıyor.

## <a name="c1-18-seri-debug-header-j1"></a>1.8 Seri Debug Header (J1)

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
- Ayarlar: <b>115200 8N1</b>, flow control <b>kapalı</b> ([Bölüm 2](#c2-bölüm-2--seri-konsol-ve-minicom)).

> [!WARNING]
> Sinyaller <b>3.3V</b>'tur. USB-TTL dönüştürücünün <b>3.3V</b> modda olduğundan emin ol, 5V'luk dönüştürücü kartı bozabilir. Dönüştürücünün <b>VCC</b> pinini karta <b>bağlama</b>, sadece GND, TX ve RX yeterli.

## <a name="c1-19-genişleme-headerları-p8-ve-p9"></a>1.9 Genişleme Header'ları (P8 ve P9)

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

## <a name="c1-110-özet"></a>1.10 Özet

1. Seri konsol (J1, 115200 8N1) en önemli debug aracın.
2. Varsayılan boot <b>eMMC</b>'den. Kendi imajını <b>SD karttan</b> açmak için <b>S2</b>'yi basılı tutarak güç ver.
3. Boot zinciri: <b>ROM → MLO (SPL) → U-Boot → Kernel + DTB → RootFS</b>.
4. eMMC = <b>MMC1</b>, microSD = <b>MMC0</b>.
5. Tüm I/O <b>3.3V</b>, ADC <b>1.8V</b>.


<div class="page-break"></div>

# <a name="c2-bölüm-2--seri-konsol-ve-minicom"></a>Bölüm 2 — Seri Konsol ve Minicom

> <b>Bu bölümde:</b>
> - USB-TTL dönüştürücüyü bilgisayara tanıtıp port adını (`/dev/ttyUSB0`) bulacaksın.
> - Minicom'u kurup BeagleBone Black için doğru ayarlarla (115200 8N1, flow control kapalı) kaydedeceksin.
> - Minicom'un sık kullanılan kısayollarını ve Windows'taki karşılığı Tera Term'i öğreneceksin.
>
> <b>Ön koşul:</b> [Bölüm 1](#c1-bölüm-1--beaglebone-black-donanımı) — J1 debug header'ının pinleri.

---

## <a name="c2-21-seri-konsol-neden-önemli"></a>2.1 Seri Konsol Neden Önemli?

Kart açılırken ekrana bir şey basan ilk programlar (ROM Code, SPL, U-Boot) HDMI veya ağ kullanmaz. Bütün mesajlarını <b>UART0</b> üzerinden, yani J1 header'ından gönderirler. Bu mesajları görmenin ve U-Boot'a komut yazmanın tek yolu seri konsoldur:

```
[Klavye] ⇄ [minicom / Tera Term] ⇄ USB-TTL kablo ⇄ J1 (UART0) ⇄ [BeagleBone: ROM / SPL / U-Boot / Linux]
```

Bilgisayardaki program sadece bir penceredir. Komutları bilgisayar değil, <b>kartın üzerindeki</b> program (U-Boot veya Linux) çalıştırır.

## <a name="c2-22-minicomu-kur"></a>2.2 Minicom'u Kur

<b>Minicom</b>, Linux'ta kullanılan bir seri port terminal programıdır. `lrzsz` paketi de Minicom'un Xmodem/Ymodem ile dosya göndermesi için gerekir ([Bölüm 6](#c6-bölüm-6--u-boot-komut-satırı-ve-uenvtxt) ve [Bölüm 7](#c7-bölüm-7--seri-porttan-uart-boot)'de kullanacağız):

```bash
sudo apt update
sudo apt install minicom lrzsz
```

## <a name="c2-23-usb-ttl-dönüştürücünün-port-adını-bul"></a>2.3 USB-TTL Dönüştürücünün Port Adını Bul

USB-TTL dönüştürücüyü bilgisayara tak ve terminalde şunu çalıştır:

```bash
sudo dmesg | grep tty
```

Çıktı aşağıdakine benzer olmalı:

![dmesg çıktısında USB-TTL dönüştürücü](../images/{D08296A2-927C-4477-88AA-80FA9DC1250A}.png)

- Kernel, dönüştürücünün çipini tanıyıp sürücüsünü yükler. Bu örnekte çip <b>pl2303</b>. Senin dönüştürücünde <b>cp210x</b>, <b>ftdi_sio</b> veya <b>ch341</b> de yazabilir.
- Satırın sonundaki <b>`ttyUSB0`</b>, Minicom'da kullanacağımız portun adıdır: <b>`/dev/ttyUSB0`</b>.

Portu her seferinde `sudo` ile açmamak için kullanıcını `dialout` grubuna ekle (bir kez yapılır, sonra oturumu kapatıp açman gerekir):

```bash
sudo usermod -aG dialout $USER
```

## <a name="c2-24-minicom-ayarlarını-yap"></a>2.4 Minicom Ayarlarını Yap

Ayar ekranını aç:

```bash
sudo minicom -s
```

Yön tuşlarıyla menüde gezinebilirsin. <b>Serial port setup</b>'ı seç:

![minicom -s ana menüsü](../images/{F27FC9A5-A70D-479E-9FE1-A48AF82142C0}.png)

Seri port ayarları ekranı açılır:

![Serial port setup ekranı](../images/{46E1CB74-A6AC-4373-91BD-4DC1CC8E5EF1}.png)

Bu ekranda her ayarın başında bir harf vardır. Değiştirmek istediğin ayarın harfine basarsın. Örneğin <b>Serial Device</b>'ı değiştirmek için <b>A</b>'ya bas. İmleç o satıra geçer:

![Serial Device ayarını düzenleme](../images/{230FE2DE-7BE6-49B2-B01E-2F294C2C15FE}.png)

Eski değeri silip `/dev/ttyUSB0` yaz ve <b>Enter</b>'a bas.

Baud rate'i değiştirmek için <b>E</b>'ye bas. Hız ve veri formatı ekranı açılır:

![Baud rate ve veri formatı ekranı](../images/{D297BD35-EB7C-4410-B431-A8B84BC48A9D}.png)

Bu ekranda da her seçeneğin bir harfi var. Örneğin <b>D</b>'ye basınca hız 38400 olur:

![Baud rate 38400 seçildi](../images/{E3A60A5C-888D-4802-8A22-C1E6AC50C300}.png)

Biz BeagleBone Black için <b>115200</b> seçeceğiz. Bu ekrandaki harflerle hızı 115200, formatı <b>8N1</b> (8 bit, parity yok, 1 stop bit) yap ve Enter ile çık.

Ayarların son hali:

| Ayar | Değer |
|---|---|
| Serial Device | `/dev/ttyUSB0` |
| Bps/Par/Bits | `115200 8N1` |
| Hardware Flow Control | <b>No</b> |
| Software Flow Control | <b>No</b> |

> [!IMPORTANT]
> BeagleBone Black'in seri hattında <b>CTS</b> ve <b>RTS</b> pinleri yoktur. Bu yüzden <b>Hardware Flow Control</b> kullanılamaz ve <b>No</b> olmalıdır. Yes kalırsa ekranda kartın mesajlarını görürsün ama klavyeden yazdıkların karta gitmez. <b>Software Flow Control</b> da <b>No</b> kalsın.

Ayarları bitirince ana menüye dön ve <b>Save setup as dfl</b>'yi seç. Böylece ayarlar varsayılan olarak kaydedilir ve her seferinde yeniden yapman gerekmez. Sonra <b>Exit</b> ile ayar ekranından çık:

![Save setup as dfl](../images/{25B687AC-C882-4EAD-82C6-B4EA24B58170}.png)

## <a name="c2-25-minicomu-kullanmak"></a>2.5 Minicom'u Kullanmak

Ayarları kaydettikten sonra Minicom'u doğrudan açabilirsin. Ayarları komut satırında açıkça vermek de mümkün:

```bash
minicom                                  # kayıtlı ayarlarla aç
minicom -D /dev/ttyUSB0 -b 115200        # portu ve hızı açıkça ver
```

Minicom'da bütün kısayollar önce <b>`Ctrl-A`</b>, ardından bir harf ile kullanılır:

| Kısayol | Görevi |
|---|---|
| `Ctrl-A` → `Z` | Yardım: bütün kısayolların listesi |
| `Ctrl-A` → `S` | Dosya gönder (xmodem / ymodem). [Bölüm 6](#c6-bölüm-6--u-boot-komut-satırı-ve-uenvtxt) ve [Bölüm 7](#c7-bölüm-7--seri-porttan-uart-boot)'de kullanılır. |
| `Ctrl-A` → `P` | Baud rate'i değiştir |
| `Ctrl-A` → `O` | Ayar menüsü (`minicom -s` ile aynı) |
| `Ctrl-A` → `C` | Ekranı temizle |
| `Ctrl-A` → `X` | Minicom'dan çık |

> [!TIP]
> Minicom'u kartı açmadan <b>önce</b> başlat. Böylece açılıştaki ilk mesajları (SPL, U-Boot) kaçırmazsın.

## <a name="c2-26-windowsta-tera-term"></a>2.6 Windows'ta: Tera Term

Kursun bazı derslerinde Windows'ta <b>Tera Term</b> kullanılıyor. Bu bir zorunluluk değil, Tera Term de Minicom gibi bir seri terminal programıdır. Hangisini kullanırsan kullan, komutlar ve çıktılar aynıdır.

| | Linux | Windows |
|---|---|---|
| Program | `minicom` | Tera Term |
| Port adı | `/dev/ttyUSB0` | `COM3` gibi (Aygıt Yöneticisi → Bağlantı Noktaları'na bak) |
| Ayarlar | 115200, 8N1, flow control yok | Setup → Serial port: 115200, 8 bit, none, 1 stop, Flow control: none |

## <a name="c2-27-özet"></a>2.7 Özet

| Ne? | Komut / Değer |
|---|---|
| Kurulum | `sudo apt install minicom lrzsz` |
| Port adını bulmak | `sudo dmesg \| grep tty` → `/dev/ttyUSB0` |
| Ayarlar | `sudo minicom -s` → 115200 8N1, Hardware/Software Flow Control: <b>No</b> → Save setup as dfl |
| Açmak | `minicom -D /dev/ttyUSB0 -b 115200` |
| Çıkmak | `Ctrl-A` → `X` |

## <a name="c2-28-karşılaşılabilecek-problemler"></a>2.8 Karşılaşılabilecek Problemler

| Belirti | Sebep | Çözüm |
|---|---|---|
| `cannot open /dev/ttyUSB0: Permission denied` | Kullanıcın `dialout` grubunda değil | `sudo usermod -aG dialout $USER`, sonra oturumu kapatıp aç |
| `dmesg`'de `ttyUSB` hiç görünmüyor | Kablo/sürücü sorunu ya da sanal makine USB'yi görmüyor | Başka USB portu dene. Sanal makinedeysen USB aygıtını VM'e bağla (VirtualBox: Devices → USB). |
| Ekranda hiçbir şey yok | TX/RX düz bağlanmış ya da GND bağlı değil | Dönüştürücünün TX'i → kartın RX'i (J1 pin 4), RX'i → kartın TX'i (J1 pin 5), GND → pin 1 ([1.8](#c1-18-seri-debug-header-j1)) |
| Anlamsız / bozuk karakterler | Baud rate yanlış | 115200 8N1 olmalı |
| Mesajlar geliyor ama yazdıklarım gitmiyor | Hardware Flow Control açık | `minicom -s` → Serial port setup → Hardware Flow Control: <b>No</b> |
| `sx: not found` (dosya gönderirken) | `lrzsz` kurulu değil | `sudo apt install lrzsz` |


<div class="page-break"></div>

<div class="part-title">Kısım II<br>Boot Süreci</div>

<div class="page-break"></div>

# <a name="c3-bölüm-3--linux-boot-süreci-rbl--spl--u-boot"></a>Bölüm 3 — Linux Boot Süreci: RBL → SPL → U-Boot

> <b>Bu bölümde:</b>
> - Kart açılırken çalışan programları (RBL, SPL/MLO, U-Boot, kernel) ve her birinin görevini öğreneceksin.
> - Neden tek bir bootloader yerine bir <b>zincir</b> olduğunu anlayacaksın.
> - SYSBOOT pinlerinin boot sırasını nasıl belirlediğini ve S2 butonunun bunu nasıl değiştirdiğini göreceksin.
>
> <b>Ön koşul:</b> [Bölüm 1](#c1-bölüm-1--beaglebone-black-donanımı) — kartın bellekleri (SRAM, DDR, eMMC, SD) ve S2 butonu.

---

![Beaglebone boot aşamaları ve her aşamanın çalıştığı bellek](../images/{6F9A1EE0-B456-4D43-8C5F-C2B7869022CB}.png)

BeagleBone Black'e güç verildiğinde Linux tek adımda açılmaz. Açılış, birbirini yükleyen bir <b>zincir</b> şeklinde ilerler. Her aşama bir sonrakini belleğe yükler ve kontrolü ona devreder:

```
Güç → RBL (ROM) → SPL / MLO (SRAM) → U-Boot (DDR) → Linux kernel (DDR) → Root filesystem → init
```

Şemadaki <b>"Runs out of ..."</b> ifadeleri her aşamanın <b>hangi bellekte çalıştığını</b> gösterir. Zincirin neden bu kadar uzun olduğu da buradan anlaşılır.

> [!NOTE]
> <b>Neden tek bir bootloader yok?</b> Açılışın ilk anında 512 MB'lık <b>DDR RAM henüz kullanılamaz</b>. DDR'ın çalışması için önce saat (clock), zamanlama ve voltaj ayarlarının yapılması gerekir ve bu ayarlar karttan karta değişir. İşlemcinin hemen kullanabildiği tek RAM, SoC'nin içindeki <b>çok küçük dahili SRAM</b>'dir. Bu yüzden önce SRAM'e sığacak kadar küçük bir program (SPL) çalışır, DDR'ı hazırlar, ardından büyük programlar (U-Boot, Kernel) DDR'a yüklenebilir.

---

## <a name="c3-31-rbl-rom-boot-loader"></a>3.1 RBL (ROM Boot Loader)

- Karta enerji verildiğinde SoC (System on Chip) üzerinde çalışan <b><i>ilk kod parçasıdır</i></b>.
- Üretici firma (Texas Instruments) tarafından yazılır ve çip üretilirken SoC'nin içindeki <b>ROM</b> belleğe kaydedilir. ROM'da olduğu için <b>değiştirilemez</b>.
- <b>Nerede çalışır:</b> Doğrudan <b>ROM</b> üzerinden (Runs out of ROM).

<b>Görevleri:</b>
1. İşlemcinin temel donanımını (saat, watchdog vb.) minimum seviyede başlatır.
2. <b>SYSBOOT</b> pinlerinin seviyesini okuyarak <b>boot sırasını</b> belirler. Beaglebone'da bu sırayı <b>S2 (Boot)</b> butonu değiştirir:
   - S2 basılı değilse: <b>eMMC</b> → microSD → UART → USB
   - S2 basılıysa: SPI → <b>microSD</b> → USB → UART
3. Bu sırayla cihazları tek tek dener ve ilk bulduğu geçerli <b>ikinci aşama bootloader</b>'ı (<b>MLO</b>) dahili SRAM'e kopyalar.
4. Kontrolü MLO'ya devreder.

> [!NOTE]
> SD karttan boot ederken RBL, kartın <b>FAT formatlı ilk bölümünde</b> (boot partition) `MLO` adlı dosyayı arar. Bu yüzden kendi boot SD kartımızı hazırlarken MLO dosyasını bu bölüme koyacağız ([Bölüm 4](#c4-bölüm-4--sd-karttan-boot)).

### <a name="c3-rblin-yaptığı-işler"></a>RBL'in yaptığı işler

![RBL'in yaptığı işler](../images/{FBF63A6C-137A-46DA-9DE4-BB6336EBAF4C}.png)

- <b>Stack Setup:</b> RBL'in C ile yazılmış fonksiyonları çalıştırabilmesi için önce bir <b>stack</b> (yığın) alanı gerekir. Fonksiyon çağrıları ve yerel değişkenler burada tutulur. RBL stack'i dahili SRAM'de kurar.
- <b>Watchdog Timer 1 (3 dakika):</b> Watchdog, belirli bir süre içinde "beslenmezse" (sıfırlanmazsa) sistemi <b>resetleyen</b> bir sayaçtır. Amacı, yazılım bir yerde takılırsa kartı kendiliğinden yeniden başlatmaktır. RBL bu sayacı <b>3 dakikaya</b> kurar ve açık bırakır. Bu yüzden sonraki aşamalar (SPL, U-Boot, Linux) bu watchdog'u ya kapatmalı ya da düzenli olarak beslemelidir. Yoksa kart 3 dakika sonra resetlenir.
- <b>System clock configuration using PLL:</b> İşlemcinin ve çevre birimlerinin saatlerini PLL ile kurar (aşağıda açıklanıyor).
- <b>MLO/SPL'i arar, SRAM'e kopyalar ve çalıştırır:</b> Yukarıdaki görev listesinin 2-4. maddeleri.

### <a name="c3-rom-code-startup-sequence"></a>ROM Code Startup Sequence

![ROM Code Startup Sequence (TRM Figure 26-5)](../images/{A84F2AAF-3F3B-4A9D-83A1-E62F89726776}.png)

Bu akış şeması AM335x TRM'den (Figure 26-5) alınmıştır ve RBL'in açılışta yaptığı işleri sırasıyla gösterir:

1. <b>System start-up:</b> Karta güç verilir veya reset gelir.
2. <b>Initialization:</b> İşlemcinin en temel ayarları yapılır.
3. <b>__main() (stack setup):</b> Stack kurulur. Bundan sonra C kodu çalışabilir.
4. <b>main():</b> RBL'in ana fonksiyonu başlar.
5. <b>MPU WDT1 setup:</b> Watchdog Timer 1 kurulur (3 dakika).
6. <b>DPLLs and clocks configuration:</b> PLL'ler ve saatler ayarlanır.
7. <b>Booting:</b> Boot cihazları aranır ve MLO yüklenir. Bu adımın detayı aşağıdaki <b>ROM Code Booting Procedure</b> şemasındadır.

### <a name="c3-pll-phase-locked-loop-nedir"></a>PLL (Phase Locked Loop) nedir?

![PLL ile kristal frekansından yüksek frekans üretimi](../images/{F870EC8F-9699-4960-8AF1-F7CCCCDE6333}.png)

- Kart üzerindeki kristal osilatör <b>düşük frekanslıdır</b> (BBB'de <b>24 MHz</b>). Ama işlemci yüzlerce MHz ile çalışmak ister.
- <b>PLL</b>, SoC içindeki bir devredir. Kristalden gelen düşük frekansı <b>çarparak</b> (ve gerektiğinde bölerek) yüksek frekanslar üretir. Şemadaki örnekte 24 MHz'lik kristalden <b>800 MHz</b>'e kadar frekans elde edilir.
- Her birim farklı bir frekansa ihtiyaç duyar. Bu yüzden SoC'de birden fazla PLL vardır ve her biri farklı bir birimi besler: <b>işlemci</b>, <b>USB</b>, <b>ekran (display)</b>, <b>bus saatleri</b> (AHB/APB) gibi.
- Doğrudan yüksek frekanslı bir kristal kullanılmamasının sebebi: Düşük frekanslı kristaller ucuz ve kararlıdır. Tek bir kristalden PLL'ler ile ihtiyaç duyulan tüm frekansları üretmek çok daha pratiktir.

### <a name="c3-rom-code-booting-procedure"></a>ROM Code Booting Procedure

![ROM Code Booting Procedure (TRM Figure 26-6)](../images/{2C02ED59-04FF-4CB6-8456-C5649CC2C078}.png)

Bu şema (TRM Figure 26-6), RBL'in ikinci aşama bootloader'ı (MLO) nasıl aradığını gösterir:

1. <b>Boot cihaz listesi oluşturulur:</b> RBL, <b>SYSBOOT[4:0]</b> değerine bakarak hangi cihazları hangi sırayla deneyeceğini belirler ([3.5](#c3-35-boot-kaynakları-ve-boot-sırası-sysboot-pinleri)).
2. <b>Process device:</b> Listedeki sıradaki cihaz denenir. Cihazlar iki türe ayrılır:
   - <b>Memory type (bellek türü):</b> eMMC, SD kart, NAND, SPI flash gibi. MLO bu belleğin içinde <b>hazır durur</b>, RBL sadece okur.
   - <b>Peripheral type (çevre birimi türü):</b> UART, USB, Ethernet gibi. MLO kartta yoktur, <b>dışarıdan</b> (bir bilgisayardan) gönderilmesi beklenir. Bu yüzden burada <b>timeout</b> (zaman aşımı) vardır: Belirli süre içinde imaj gelmezse başarısız sayılır.
3. <b>Success:</b> MLO bulunduysa <b>"Jump to Initial SW"</b>, yani MLO'ya atlanır ve kontrol ona geçer.
4. <b>Fail / Timeout:</b> Listede başka cihaz varsa <b>bir sonrakine</b> geçilir.
5. <b>Dead loop:</b> Listedeki hiçbir cihazda MLO bulunamazsa RBL sonsuz bir döngüye girer ve kart hiçbir şey yapmaz.

> [!TIP]
> BBB'nin varsayılan boot listesinde <b>UART0</b> da vardır. eMMC'de ve SD kartta geçerli bir MLO yoksa RBL sırayı UART0'a getirir ve seri konsoldan X-Modem ile imaj bekler. Bu sırada seri konsolda sürekli `CCCCCCCC...` yazdığını görürsün. Bu çıktı, <b>"RBL MLO bulamadı"</b> anlamına gelir. Bu davranışı [Bölüm 7](#c7-bölüm-7--seri-porttan-uart-boot)'de kartı seri porttan açmak için kullanacağız.

---

## <a name="c3-32-spl--mlo-secondary-program-loader"></a>3.2 SPL / MLO (Secondary Program Loader)

- <b>SPL</b> = Secondary Program Loader (İkinci Aşama Önyükleyici). TI işlemcilerinde bu dosyanın adı <b>MLO</b>'dur (MLO = MMC Loader). SPL ile MLO <b>neredeyse</b> aynı şeydir (farkı aşağıda).
- SPL ayrı bir program değildir. <b>U-Boot'un kaynak kodundan derlenir</b>, ama sadece gerekli kısımları içeren çok küçük bir versiyonudur. U-Boot'u derlediğimizde hem `MLO` hem de `u-boot.img` dosyaları birlikte oluşur ([Bölüm 9](#c9-bölüm-9--cross-toolchain-spl-ve-u-boot-derleme)).
- <b>Nerede çalışır:</b> SoC içindeki <b>dahili SRAM</b> üzerinde (Runs out of internal SRAM). SRAM çok küçük olduğu için SPL de küçük olmak zorundadır.

### <a name="c3-spl-ile-mlo-arasındaki-fark"></a>SPL ile MLO arasındaki fark

![MLO = image header + SPL](../images/{C970A18C-744B-46D4-A0A8-73AF33EA031A}.png)

- <b>MLO = Image header + SPL</b>. Yani MLO, başına küçük bir <b>başlık (header)</b> eklenmiş SPL'dir.
- Header'da RBL'in ihtiyaç duyduğu bilgiler bulunur:
  - <b>load_addr:</b> SPL'in belleğin <b>hangi adresine</b> kopyalanacağı
  - <b>Size:</b> Header'dan sonra gelen SPL kodunun <b>boyutu</b>
- RBL önce header'ı okur. Böylece SPL'i nereye kopyalayacağını ve ne kadar veri okuyacağını öğrenir, kopyalamayı yapar ve o adrese atlar.
- U-Boot derlendiğinde önce header'sız SPL (`u-boot-spl.bin`) oluşur. Başına header eklenince `MLO` dosyası elde edilir.

> [!NOTE]
> Slayttaki `0x40000000` adresi bir örnektir. AM335x'te MLO gerçekte dahili SRAM'deki `0x402F0400` adresine yüklenir.

<b>Görevleri:</b>
1. <b>DDR RAM'i başlatır.</b> En kritik görevi budur. Saat (PLL) ve DDR zamanlama ayarlarını yapar, böylece 512 MB'lık RAM kullanılabilir hale gelir.
2. Seri konsol (UART0) gibi gerekli birkaç çevre birimini hazırlar. Seri konsolda gördüğün ilk `U-Boot SPL ...` satırı buradan gelir.
3. Üçüncü aşama bootloader'ı, yani <b>U-Boot</b>'u (`u-boot.img`) eMMC/SD karttan okuyup <b>DDR</b>'a yükler.
4. Kontrolü U-Boot'a devreder.

### <a name="c3-soru-am335xin-rbli-neden-u-bootu-doğrudan-ddra-yükleyemez"></a>Soru: AM335x'in RBL'i neden U-Boot'u doğrudan DDR'a yükleyemez?

<b>Cevap:</b> Çünkü RBL, karta <b>hangi DDR belleğin takılı olduğunu bilmez</b>. Bilmediği bir belleği de başlatamaz.

- DDR RAM'den veri okuyup yazabilmek için önce SoC içindeki <b>DDR kontrolcüsünün</b> ve RAM'in <b>doğru parametrelerle</b> ayarlanması gerekir: bellek tipi (DDR2, DDR3, DDR3L...), boyut, hız, zamanlama (timing) değerleri vb.
- Bu parametreler <b>tamamen karta (ürüne) özeldir</b>. Aynı AM335x işlemcisini kullanan farklı firmalar farklı bellekler seçebilir:
  - X firması: Micron marka <b>DDR3</b>
  - Y firması: Başka bir markanın <b>DDR2</b>'si
  - Z firması: Hiç DDR kullanmayabilir
- RBL çip üretilirken ROM'a yazılır. O an çipin hangi kartta, hangi bellekle kullanılacağı belli değildir. Bu yüzden RBL <b>DDR'ı hiç başlatmaz</b>. Sadece her işlemcide garanti olarak bulunan <b>dahili SRAM</b>'i kullanır.
- U-Boot ise dahili SRAM'e <b>sığmayacak kadar büyüktür</b>. Yani RBL'in U-Boot'u yükleyebileceği bir yer yoktur.

<b>Çözüm SPL'dir:</b> SPL, dahili SRAM'e sığacak kadar küçüktür ve kartın DDR ayarlarını <b>bilir</b>, çünkü o kart için derlenmiştir. RBL, SPL'i SRAM'e yükler. SPL de DDR'ı başlatıp U-Boot'u DDR'a yükler.

> [!NOTE]
> Kendi kartını tasarlayıp BBB'den farklı bir DDR kullanırsan, SPL kaynak kodundaki <b>DDR parametrelerini</b> kendi belleğine göre değiştirip SPL'i yeniden derlemen gerekir.

> [!NOTE]
> <b>Saat (clock) ayarları:</b> RBL'in kodu ROM'da olduğu için saat ayarları <b>değiştirilemez</b>. SYSBOOT[15:14] ile sadece karttaki kristalin frekansı bildirilir. İşlemci (MPU), DDR ve çevre birimi frekanslarını asıl kuran <b>SPL</b>'dir. SPL'i kendimiz derlediğimiz için bu ayarları kaynak kodda değiştirip yeniden derleyebiliriz. Açılıştan sonra Linux da <b>cpufreq</b> ile işlemci frekansını çalışma sırasında değiştirebilir.

---

## <a name="c3-33-u-boot-universal-bootloader"></a>3.3 U-Boot (Universal Bootloader)

- Açık kaynak kodlu ve gömülü sistemlerde en yaygın kullanılan bootloader'dır. Üçüncü (ve son) aşama önyükleyicidir.
- <b>Nerede çalışır:</b> <b>DDR RAM</b> üzerinde (Runs out of DDR). Artık bellek kısıtı olmadığı için çok daha fazla özellik içerebilir.

<b>Görevleri:</b>
1. Linux Kernel'i çalıştırmak için gereken donanımları (eMMC, SD kart, Ethernet, USB vb.) başlatır.
2. <b>Linux Kernel</b> imajını (`zImage` / `uImage`) bir kaynaktan (SD kart, eMMC, seri port, ağ üzerinden TFTP vb.) okuyup <b>DDR</b>'a yükler.
3. Kartın donanımını tarif eden <b>Device Tree</b> dosyasını (BeagleBone Black için `am335x-boneblack.dtb`) DDR'a yükler.
4. Kernel'e <b>bootargs</b> (komut satırı parametreleri) iletir. Örneğin root filesystem'in nerede olduğu (`root=`) veya hangi konsolun kullanılacağı (`console=`) bu parametrelerle bildirilir.
5. Kontrolü Linux Kernel'e devreder. Bu noktadan sonra U-Boot'un işi biter.

<b>Neden önemli:</b>
- U-Boot'un kendi <b>komut satırı</b> vardır. Açılışta seri konsolda geri sayım (`Hit any key to stop autoboot`) sırasında bir tuşa basarsan U-Boot komut satırına (`U-Boot#` veya `=>`) düşersin. Buradan bellek okuma/yazma, dosya yükleme, boot ayarlarını değiştirme gibi işlemler yapılabilir ([Bölüm 6](#c6-bölüm-6--u-boot-komut-satırı-ve-uenvtxt)).
- Boot ayarları <b>environment değişkenlerinde</b> (`bootcmd`, `bootargs` vb.) tutulur ve `printenv` / `setenv` komutlarıyla görüntülenip değiştirilebilir.

---

## <a name="c3-34-linux-kernel-ve-root-filesystem"></a>3.4 Linux Kernel ve Root Filesystem

U-Boot `bootm` (veya `bootz`) komutuyla kernel'e atladıktan sonra zincirin son iki halkası çalışır:

1. <b>Kernel</b> kendini RAM'de açar (`zImage` sıkıştırılmıştır), U-Boot'un verdiği <b>Device Tree</b>'yi okuyup kartta hangi donanımın olduğunu öğrenir ve sürücüleri başlatır ([Bölüm 11](#c11-bölüm-11--linux-device-tree)).
2. Kernel, `bootargs`'taki <b>`root=`</b> parametresine bakarak <b>root filesystem</b>'i (`/`) bağlar. Bu bir SD kart bölümü (`/dev/mmcblk0p2`), eMMC bölümü veya RAM'deki bir initramfs olabilir.
3. Rootfs'teki ilk program olan <b>`init`</b>'i (systemd veya BusyBox init) çalıştırır. Bundan sonra servisler başlar ve `login:` ekranı gelir.

> [!NOTE]
> `console=` parametresindeki konsol adı kernel sürümüne göre değişir. Kursun hazır kernel'inde (3.8.13) UART0'ın adı `ttyO0`, yeni kernel'lerde `ttyS0`'dır. Yanlış ad yazılırsa kernel açılır ama mesajlarını göremezsin.

---

## <a name="c3-35-boot-kaynakları-ve-boot-sırası-sysboot-pinleri"></a>3.5 Boot Kaynakları ve Boot Sırası (SYSBOOT Pinleri)

AM335x işlemcisi tek bir yerden boot etmek zorunda değildir. <b>Birçok farklı çevre biriminden</b> (eMMC, SD kart, UART, USB, SPI flash, NAND, Ethernet...) boot edebilir. Peki RBL hangisinden boot edeceğine nasıl karar verir? Bunu işlemcinin <b>SYSBOOT</b> pinleri belirler.

![SYSBOOT Configuration Pins (TRM Table 26-7)](../images/{E888F879-1457-455D-A181-9F3391010FE6}.png)

Bu tablo, AM335x'in <b>Technical Reference Manual (TRM)</b> dokümanındaki <b>Table 26-7: SYSBOOT Configuration Pins</b> tablosudur.

### <a name="c3-sysboot-pinleri-nedir"></a>SYSBOOT pinleri nedir?

- <b>SYSBOOT[15:0]</b>, işlemcinin 16 adet pinidir. Karta <b>güç verildiği anda</b> RBL bu pinlerin seviyesini (1 veya 0) okur.
- Okunan değer, <b>CONTROL_STATUS</b> adlı bir register'a kaydedilir. Tablonun 3. satırındaki `CONTROL_STATUS[...]` ifadeleri, her SYSBOOT bitinin bu register'da hangi bite karşılık geldiğini gösterir.
- Bu pinlerin seviyesi kart üzerindeki <b>pull-up / pull-down dirençleriyle</b> sabitlenir. Yani boot ayarı, kartı tasarlayan kişi tarafından donanımsal olarak belirlenir.

### <a name="c3-tablonun-sütunları"></a>Tablonun sütunları

| Sütun | Ne işe yarar? |
|---|---|
| <b>SYSBOOT[15:14]</b> | Karttaki kristalin (osilatörün) frekansını bildirir: 19.2 / 24 / 25 / 26 MHz. Beaglebone Black <b>24 MHz</b> kristal kullanır (<b>01b</b>). |
| <b>SYSBOOT[13:12]</b> | Normal çalışma için <b>00b</b> olmalıdır. |
| <b>SYSBOOT[11:10], [9], [8]</b> | Sadece belirli boot türlerinde (XIP, NAND) kullanılan ek ayarlar. Diğer boot türlerinde önemsizdir ("Don't care"). |
| <b>SYSBOOT[7:6]</b> | Ethernet (EMAC) üzerinden boot için PHY modu. |
| <b>SYSBOOT[5]</b> | CLKOUT1 saat çıkışının açık/kapalı olması. |
| <b>SYSBOOT[4:0]</b> | <b>En önemli kısım.</b> Boot modunu, yani <b>hangi cihazların hangi sırayla</b> deneneceğini belirler. |
| <b>Boot Sequence</b> | SYSBOOT[4:0] değerine göre RBL'in deneyeceği cihazlar: <b>1st → 2nd → 3rd → 4th</b>. |

### <a name="c3-boot-sequence-boot-sırası-nasıl-çalışır"></a>Boot Sequence (Boot sırası) nasıl çalışır?

Resimde kırmızıyla işaretlenen satırı örnek alalım. <b>SYSBOOT[4:0] = 00001b</b> ise boot sırası şöyledir:

```
1st: UART0  →  2nd: XIP (NOR flash)  →  3rd: MMC0 (SD kart)  →  4th: SPI0
```

1. RBL önce <b>1. cihazı</b> (UART0) dener.
2. O cihazda geçerli bir boot imajı (MLO) bulamazsa veya cihaz yanıt vermezse <b>bir sonraki cihaza</b> geçer.
3. Geçerli bir imaj bulduğu <b>ilk cihazdan</b> boot eder ve diğerlerine bakmaz.
4. Dört cihazın hiçbirinde imaj bulamazsa boot başarısız olur.

SYSBOOT[4:0] 5 bit olduğu için 32 farklı kombinasyon vardır. Her biri farklı bir boot sırası tanımlar. Resimde bunların sadece ilk birkaçı görünüyor, tablonun tamamı TRM'de.

### <a name="c3-tablodaki-boot-kaynakları"></a>Tablodaki boot kaynakları

| İsim | Anlamı |
|---|---|
| <b>MMC0</b> | Beaglebone'da <b>microSD kart</b> yuvası |
| <b>MMC1</b> | Beaglebone'da kart üstündeki <b>eMMC</b> |
| <b>UART0</b> | Seri port üzerinden boot. İmaj bilgisayardan seri hat ile (X-Modem protokolü) gönderilir ([Bölüm 7](#c7-bölüm-7--seri-porttan-uart-boot)). |
| <b>USB0</b> | USB üzerinden boot. Kart, bilgisayara bir ağ cihazı gibi görünür ve imajı oradan alır. |
| <b>SPI0</b> | SPI ile bağlı harici flash bellekten boot |
| <b>XIP</b> | e<b>X</b>ecute <b>I</b>n <b>P</b>lace: Kod, NOR flash'a kopyalanmadan doğrudan orada çalıştırılır. |
| <b>NAND / NANDI2C</b> | Harici NAND flash bellekten boot |
| <b>EMAC</b> | Ethernet üzerinden ağdan boot |

> [!NOTE]
> UART0 ve USB0 boot modları, kartta hiç yazılım olmadığında (örneğin eMMC boşsa veya bozulduysa) kartı <b>kurtarmak</b> için kullanılır.

### <a name="c3-beaglebone-blackte-durum"></a>BeagleBone Black'te durum

BeagleBone Black'in boot ayarları, resmi dokümandaki şu tabloda görünür:

![BBB SYSBOOT tablosu](../images/beaglebone/bbb_sysboot_tablosu.jpg)

| Durum | SYSBOOT[4:0] | Boot Sequence |
|---|---|---|
| <b>S2 basılı değil</b> (varsayılan) | <b>11100b</b> | <b>MMC1 (eMMC)</b> → MMC0 (SD) → UART0 → USB0 |
| <b>S2 basılı</b> (güç verilirken) | <b>11000b</b> | SPI0 → <b>MMC0 (SD)</b> → USB0 → UART0 |

- İki değer arasında sadece <b>SYSBOOT[2]</b> biti farklıdır: 11<b>1</b>00 → 11<b>0</b>00. Boot (<b>S2</b>) butonu tam olarak bu biti <b>0</b>'a çeker.
- Varsayılan durumda eMMC ilk sırada olduğu için kart <b>eMMC'deki</b> hazır Debian'dan açılır.
- S2'ye basılıyken eMMC listede <b>hiç yoktur</b>. SPI0'da flash olmadığı için o adım atlanır ve kart <b>SD karttan</b> açılır. Kendi derlediğimiz MLO/U-Boot/Kernel'i bu yüzden SD karta koyup S2 ile boot edeceğiz.
- Beaglebone'da SYSBOOT pinleri <b>LCD veri pinleriyle</b> (LCD_DATA0–15) ortaktır ve P8 header'ına çıkar. Bu pinlere boot sırasında dışarıdan sinyal verilirse boot sırası bozulabilir. Bu yüzden kart açılmadan P8'e bir şey bağlarken dikkatli olmak gerekir.
- Listede <b>EMAC (Ethernet) yoktur</b>. ROM Code BBB'de ağdan boot edemez. Ağdan boot için önce SD karttan U-Boot'u açmak gerekir ([Bölüm 8](#c8-bölüm-8--tftp-ile-ağdan-boot)).

> [!IMPORTANT]
> SYSBOOT pinleri <b>sadece güç verildiği anda</b> okunur. Kart açıldıktan sonra S2'ye basmak veya Reset butonuna basmak boot sırasını değiştirmez. S2 ile boot etmek için gücü tamamen kesip, S2'yi basılı tutarak tekrar güç vermelisin.

---

## <a name="c3-36-schematicte-boot-devresi"></a>3.6 Schematic'te Boot Devresi

Yukarıda anlatılan boot ayarının kart üzerindeki karşılığı, BBB schematic'inin <b>6. sayfasındaki</b> devredir.

![BBB Boot Configuration devresi](../images/beaglebone/bbb_sch_boot_config.png)

> Kaynak: BeagleBone Black Rev C schematic, sayfa 6 ([niekiran/EmbeddedLinuxBBB](https://github.com/niekiran/EmbeddedLinuxBBB) reposundaki `BBB_SCH.pdf`)

Schematic'te dikkat edilecekler:
- Her <b>SYS_BOOTx</b> hattına üstte bir pull-up (R55–R70), altta bir pull-down (R80–R95) direnci için yer var. Bunlardan sadece biri karta takılıdır. <b>DNI</b> (Do Not Install) yazan direnç kartta <b>yoktur</b>.
- Takılı dirençlere bakınca SYS_BOOT[4:0] = <b>11100b</b> çıkar. Bu değer, yukarıdaki tablodaki varsayılan değerle aynıdır.
- <b>S2</b> butonu (üzerinde <b>"uSD BOOT"</b> yazar), <b>R75</b> üzerinden <b>SYS_BOOT2</b> hattını <b>GND</b>'ye bağlar.

---

## <a name="c3-37-özet"></a>3.7 Özet

| Aşama | Kim yazar? | Nerede saklanır? | Nerede çalışır? | Ana görevi |
|---|---|---|---|---|
| <b>RBL</b> | TI (çip üreticisi) | SoC içindeki ROM | ROM | Boot cihazını seçip MLO'yu SRAM'e yüklemek |
| <b>SPL/MLO</b> | U-Boot projesi (biz derleriz) | eMMC / SD kart | Dahili SRAM | DDR'ı başlatıp U-Boot'u DDR'a yüklemek |
| <b>U-Boot</b> | U-Boot projesi (biz derleriz) | eMMC / SD kart | DDR | Kernel + DTB'yi yükleyip Kernel'i başlatmak |
| <b>Linux kernel</b> | Linux projesi (biz derleriz) | eMMC / SD kart / ağ | DDR | Donanımı başlatmak, rootfs'i bağlamak, `init`'i çalıştırmak |

- Boot sırasını <b>SYSBOOT[4:0]</b> pinleri belirler. BBB'de varsayılan <b>eMMC → SD → UART0 → USB0</b>, S2 basılıyken <b>SPI0 → SD → USB0 → UART0</b>.
- S2 sadece <b>güç verilirken</b> etkilidir.


<div class="page-break"></div>

# <a name="c4-bölüm-4--sd-karttan-boot"></a>Bölüm 4 — SD Karttan Boot

> <b>Bu bölümde:</b>
> - Bir microSD kartı GParted ile BOOT (FAT) ve ROOTFS (ext3) bölümlerine ayıracaksın.
> - Kursun hazır dosyalarını karta <b>tek tek</b> koyup her seferinde kartı açarak boot zincirinin her halkasının çalıştığını göreceksin.
> - `uEnv.txt`'nin bu açılışta ne yaptığını ve `uImage` dosyasının yapısını öğreneceksin.
> - U-Boot'u durdurup kernel'in başlığını (header) bellekten byte byte okuyacaksın.
>
> <b>Ön koşul:</b> [Bölüm 2](#c2-bölüm-2--seri-konsol-ve-minicom) — seri konsol, [Bölüm 3](#c3-bölüm-3--linux-boot-süreci-rbl--spl--u-boot) — boot zinciri.

---

## <a name="c4-41-büyük-resim"></a>4.1 Büyük Resim

Kart açılırken programlar sırayla birbirini çalıştırır. Buna <b>boot zinciri</b> denir ([Bölüm 3](#c3-bölüm-3--linux-boot-süreci-rbl--spl--u-boot)):

```
Güç → RBL → MLO → U-Boot → Linux Kernel → Root Filesystem → login ekranı
```

| Aşama | Ne yapar? | Nerede durur? |
|---|---|---|
| <b>RBL</b> (ROM Boot Loader) | Kart açılınca ilk çalışan kod. MLO'yu bulup çalıştırır. | İşlemcinin içinde, değiştirilemez |
| <b>MLO</b> | RAM'i (DDR) hazırlar, U-Boot'u yükler. | SD kart → BOOT bölümü |
| <b>U-Boot</b> | Kernel'i ve device tree'yi RAM'e yükleyip Linux'u başlatır. | SD kart → BOOT bölümü |
| <b>Linux Kernel</b> | İşletim sisteminin çekirdeği. | SD kart → ROOTFS bölümü (`/boot`) |
| <b>Root Filesystem</b> | Linux'un tüm dosyaları (`/bin`, `/etc`, ...). | SD kart → ROOTFS bölümü |

![SD karttan boot zinciri](../images/{5796B774-2D25-45F8-9CD2-47E21A76B361}.png)

<b>SD kartın son hali</b> şöyle olacak:

```
SD Kart
├── BOOT   (FAT16, ~1 GB)  →  MLO, u-boot.img, uEnv.txt
└── ROOTFS (ext3, kalan)   →  Linux dosyaları (kernel ve .dtb dahil)
```

### <a name="c4-yol-haritası"></a>Yol haritası

Dosyalar karta <b>tek tek</b> eklenir ve her seferinde kart açılıp test edilir. Böylece zincirin her halkasının çalıştığı görülür:

| Adım | Ne yapılıyor? | Sonuç |
|---|---|---|
| [4.2](#c4-42-hazırlık) – [4.4](#c4-44-sd-kartı-bölümlere-ayırma-gparted) | Dosyaları indir, SD kartı bölümle | SD kart hazır |
| [4.6](#c4-46-aşama-1-mlo) | MLO'yu kopyala, test et | RBL ✓ → MLO ✓ → U-Boot ✗ |
| [4.7](#c4-47-aşama-2-u-boot) | U-Boot'u kopyala, test et | ... → U-Boot ✓ |
| [4.8](#c4-48-aşama-3-root-filesystem-ve-uenvtxt) | Rootfs ve uEnv.txt'yi kopyala, test et | Linux açılır ✓ |
| [4.10](#c4-410-uygulama-uimage-headerını-u-bootta-elle-okuma) | U-Boot'u durdur, uImage header'ını elle oku | Header çözüldü ✓ |

Her testte kart aynı şekilde açılır. Bu işlem [4.5](#c4-45-boot-prosedürü-her-testte-tekrarlanır)'te bir kez anlatılıyor.

---

## <a name="c4-42-hazırlık"></a>4.2 Hazırlık

<b>Gerekenler:</b>
- microSD kart (en az 4 GB) ve kart okuyucu
- USB-TTL seri dönüştürücü (3.3V). Kartın açılış mesajlarını görmek için gerekli.
- Mini USB kablo (karta güç vermek için)

<b>Dosyaları indir.</b> Kursun GitHub reposundaki <b>4 dosyanın hepsini</b> indir:
https://github.com/niekiran/EmbeddedLinuxBBB/tree/master/pre-built-images/Angstrom_Demo

![Kursun hazır Ångström dosyaları](../images/{937BAE12-C277-4498-83B6-3422541AD131}.png)

| İndirilen dosya | Ne? | Nereye kopyalanacak? |
|---|---|---|
| `MLO-beaglebone-2013.04` | MLO | BOOT → adı `MLO` olacak |
| `u-boot-beaglebone-2013.04-r0.img` | U-Boot | BOOT → adı `u-boot.img` olacak |
| `uEnv.txt` | U-Boot ayar dosyası | BOOT → adı aynı kalacak |
| `Angstrom-systemd-image-eglibc-ipk-v2012.12-beagleboard.rootfs.tar.xz` | Root filesystem (içinde kernel `/boot/uImage` ve device tree `/boot/am335x-boneblack.dtb` da var) | ROOTFS → arşivden çıkarılacak |

---

## <a name="c4-43-sd-kartı-bilgisayarda-bulma"></a>4.3 SD Kartı Bilgisayarda Bulma

Kartı takıp terminalde çalıştır:

```bash
sudo dmesg
```

![dmesg çıktısında SD kart](../images/{E9587DCB-9493-4652-93CF-47B08EA122B9}.png)

- `sdb` → SD kartın adı (`/dev/sdb`). Yanında boyutu yazar (7.81 GB). Doğru cihaz olduğunu boyuttan anlarsın.
- `sdb1` → kartta zaten var olan bölüm (partition).

> [!TIP]
> `lsblk` komutu tüm diskleri boyutlarıyla birlikte daha okunaklı gösterir.

> [!NOTE]
> GParted'da aynı kart <b>7.28 GiB</b> görünür. Kart eksik değil, birimler farklı: 1 GB = 1.000.000.000 byte, 1 GiB = 1.073.741.824 byte.

---

## <a name="c4-44-sd-kartı-bölümlere-ayırma-gparted"></a>4.4 SD Kartı Bölümlere Ayırma (GParted)

Kart 2 bölüme ayrılacak. <b>Karttaki tüm veriler silinir.</b>

![Planlanan bölümler](../images/{791DE154-AB54-40F6-897E-9011C17F5EFB}.png)

| Bölüm | Label | Dosya sistemi | Boyut | Neden? |
|---|---|---|---|---|
| 1 | `BOOT` | `fat16` | ~1 GB | RBL, MLO'yu sadece FAT bölümde arar |
| 2 | `ROOTFS` | `ext3` | Kalan alan | Linux dosyaları Linux dosya sistemi ister |

GParted'ı kur ve aç:

```bash
sudo apt install gparted
sudo gparted
```

> [!CAUTION]
> Sağ üstteki listeden <b>SD kartı seç</b> (`/dev/sdb`, 7.28 GiB). Yanlışlıkla bilgisayarının diskini (`/dev/sda`) seçersen <b>bilgisayarındaki veriler silinir</b>.

![GParted'da SD kartı seçme](../images/{1A89BAAC-496D-403C-B4E4-B5037CBDDC49}.png)

### <a name="c4-441-unmount-et"></a>4.4.1 Unmount et

Bölüm şu an sistem tarafından kullanılıyor (yanındaki 🔑 simgesi). Kullanımdayken silinemez. <b>Sağ tık → Unmount.</b>

![Unmount](../images/{F664732C-758E-43D3-8642-8651DD082B29}.png)

### <a name="c4-442-eski-bölümü-sil"></a>4.4.2 Eski bölümü sil

<b>Sağ tık → Delete.</b> Kartın tamamı `unallocated` (boş alan) olur.

![Delete](../images/{78D43D2E-1A50-4CA0-B366-FCDDB6818431}.png)

![Kartın tamamı unallocated](../images/{0125CA5B-146A-4D42-9B02-440035AE3BE3}.png)

> [!NOTE]
> GParted işlemleri hemen uygulamaz, sıraya koyar ("1 operation pending"). Hepsi en sonda [4.4.5](#c4-445-değişiklikleri-uygula)'te uygulanır. O ana kadar her şey geri alınabilir.

### <a name="c4-443-boot-bölümünü-oluştur"></a>4.4.3 BOOT bölümünü oluştur

`unallocated` alana <b>sağ tık → New.</b>

![New](../images/{4CE141F8-591A-4682-A76A-BEDCC2CDCA35}.png)

Açılan pencerede 3 ayar yap, sonra <b>Add</b>'e bas:

| Alan | Değer |
|---|---|
| File system | `fat16` |
| Label | `BOOT` |
| New size (MiB) | `1013` (yaklaşık 1 GB) |

![Dosya sistemi seçimi](../images/{09B1300E-BAF9-4E27-A1EB-516C1D1F8C5A}.png)

![fat16 seçildi](../images/{5B17659C-D05D-4364-8726-118408CC54FA}.png)

![Label: BOOT](../images/{F03EC26C-791B-4AB1-89BE-72A6FAFA0E17}.png)

> [!NOTE]
> fat16 seçilince boyut kendiliğinden <b>4095 MiB</b> olur, çünkü FAT16 en fazla ~4 GiB olabilir. Bunu 1013'e düşürüyoruz. Boot dosyaları zaten birkaç MB.

![Boyut 1013 MiB](../images/{5F06ECDC-BB20-47C8-B8D1-BA39D8C519AD}.png)

![BOOT bölümü planlandı](../images/{A7350810-4850-4C65-904E-84485A598EA3}-1.png)

### <a name="c4-444-rootfs-bölümünü-oluştur"></a>4.4.4 ROOTFS bölümünü oluştur

Kalan `unallocated` alana yine <b>sağ tık → New</b>, sonra <b>Add</b>:

| Alan | Değer |
|---|---|
| File system | `ext3` |
| Label | `ROOTFS` |
| New size (MiB) | Değiştirme (kalan alanın tamamı) |

![ROOTFS ayarları](../images/{F8D61470-50C8-4030-BCAE-39B8B0A4E54C}.png)

![ROOTFS planlandı](../images/{143DC429-6748-42C3-9A4A-691238D4A073}.png)

Planlanan durum: 1 GB BOOT + 6.29 GiB ROOTFS.

![Planlanan durum](../images/{370CABEB-C929-493B-8996-1FB867457DED}.png)

### <a name="c4-445-değişiklikleri-uygula"></a>4.4.5 Değişiklikleri uygula

<b>Yeşil tik</b> (Apply All Operations) → onay penceresinde <b>Apply</b>.

> [!WARNING]
> Bu adımdan sonra geri dönüş yok, karttaki eski veriler silinir.

![Apply All Operations](../images/{D2522D38-67E5-45CF-83E8-6B2A8877C758}.png)

![İşlemler tamamlandı](../images/{01D7E3F3-77AF-4578-AF99-AE21A1EFE350}.png)

### <a name="c4-446-boot-bölümüne-boot-bayrağı-ekle"></a>4.4.6 BOOT bölümüne `boot` bayrağı ekle

Bu bayrak, bölümü "açılış bölümü" olarak işaretler. RBL, MLO'yu bu bölümde arar.

<b>BOOT'a sağ tık → Manage Flags → `boot` kutucuğunu işaretle → Close.</b>

![Manage Flags](../images/{D9F3687E-CF84-43DE-B409-44A80C7170C3}.png)

![boot bayrağı](../images/{5D758CCD-B40D-468F-8D1B-F2D8C97545E6}.png)

Flags sütununda `boot` yazıyorsa tamam. GParted'ı kapatabilirsin.

![Son durum](../images/{19CCA067-203C-4FA1-BE7A-CB2A0FF54A8B}.png)

---

## <a name="c4-45-boot-prosedürü-her-testte-tekrarlanır"></a>4.5 Boot Prosedürü (her testte tekrarlanır)

Aşağıdaki aşamaların her birinde dosya kopyaladıktan sonra bu adımları uygula.

### <a name="c4-451-kartı-bilgisayardan-güvenli-çıkar"></a>4.5.1 Kartı bilgisayardan güvenli çıkar

```bash
sync
sudo umount /media/$USER/BOOT
sudo umount /media/$USER/ROOTFS
```

- `sync` → Bekleyen yazma işlemlerini karta yazar. Atlanırsa kopyalanan dosya eksik kalabilir.
- `umount` → Bölümlerin bağlantısını keser. Artık kart çıkarılabilir.

### <a name="c4-452-seri-konsolu-hazırla-sadece-ilk-seferde"></a>4.5.2 Seri konsolu hazırla (sadece ilk seferde)

1. USB-TTL'yi kartın <b>J1</b> header'ına bağla ([1.8](#c1-18-seri-debug-header-j1)).
2. Minicom'u aç: <b>115200 baud, 8N1, Hardware Flow Control kapalı</b> ([Bölüm 2](#c2-bölüm-2--seri-konsol-ve-minicom)).

### <a name="c4-453-kartı-sd-karttan-aç-s2-butonu"></a>4.5.3 Kartı SD karttan aç (S2 butonu)

BeagleBone Black normalde <b>kendi eMMC belleğinden</b> açılır. SD karttan açılması için <b>kart açılırken S2 (BOOT) butonu basılı olmalı</b>. RBL bu butona sadece açılış anında bakar ([3.5](#c3-35-boot-kaynakları-ve-boot-sırası-sysboot-pinleri)).

SD kartı BeagleBone'a tak, sonra iki yöntemden birini uygula:

| Yöntem | Ne zaman? | Adımlar |
|---|---|---|
| <b>A: Güç vererek</b> | Kartta güç yokken | S2'yi basılı tut → USB kablosunu tak → 2–3 sn sonra S2'yi bırak |
| <b>B: Power butonuyla</b> | Kart zaten güç alıyorsa | Power'a LED'ler sönene kadar uzun bas (kapanır) → S2'yi basılı tut → Power'a kısa bas (açılır) → S2'yi bırak |

---

## <a name="c4-46-aşama-1-mlo"></a>4.6 Aşama 1: MLO

### <a name="c4-kopyala"></a>Kopyala

İndirme klasörüne git ve MLO'yu BOOT bölümüne <b>`MLO` adıyla</b> kopyala:

```bash
cd ~/BBB_Workspace/Downloads/
cp MLO-beaglebone-2013.04 /media/$USER/BOOT/MLO
```

![MLO'yu kopyalama](../images/{9BE9E6D2-720E-4ED7-A6F6-9337BBB04BB1}.png)

> [!IMPORTANT]
> <b>Neden sonda `MLO` yazıyoruz?</b> `cp` komutunda hedefin sonuna bir ad yazılırsa dosya o adla kopyalanır:
> ```
> cp  MLO-beaglebone-2013.04   /media/$USER/BOOT/MLO
>     └───── kaynak ─────┘     └─ hedef klasör + YENİ AD ─┘
> ```
> RBL, BOOT bölümünde <b>tam olarak `MLO` adlı</b> dosyayı arar. Dosya uzun adıyla kalırsa bulunamaz.

> [!TIP]
> `$USER` senin kullanıcı adındır (kursta `kiran`). Dosya adlarını elle yazmak yerine ilk birkaç harfi yazıp <b>Tab</b>'a bas, terminal tamamlar.

### <a name="c4-test-et"></a>Test et

[4.5](#c4-45-boot-prosedürü-her-testte-tekrarlanır)'teki adımlarla kartı aç. Minicom'da şunu görmelisin:

![MLO çalıştı, u-boot.img bulunamadı](../images/{E4B8C846-49BA-43F8-A7A8-B2D8B9BDA0E8}.png)

| Satır | Anlamı |
|---|---|
| `U-Boot SPL 2013.04-dirty ...` | <b>MLO çalıştı.</b> RBL dosyayı buldu. |
| `musb-hdrc ...`, `USB ... controller` | MLO USB donanımını başlatıyor, önemli değil. |
| `reading u-boot.img` | MLO bir sonraki aşamayı (U-Boot) arıyor. |
| `spl: error reading image u-boot.img` | U-Boot bulunamadı, çünkü henüz kopyalamadık. <b>Beklenen hata.</b> |

Sonuç: <b>RBL ✓ → MLO ✓ → U-Boot ✗</b>

> [!NOTE]
> "dirty" bir hata değildir. MLO derlenirken kaynak kodda kaydedilmemiş (commit edilmemiş) değişiklik olduğunu belirtir.

---

## <a name="c4-47-aşama-2-u-boot"></a>4.7 Aşama 2: U-Boot

### <a name="c4-kopyala-1"></a>Kopyala

Kartı tekrar bilgisayara tak ve U-Boot'u <b>`u-boot.img` adıyla</b> kopyala. MLO, U-Boot'u bu adla arar:

```bash
cp u-boot-beaglebone-2013.04-r0.img /media/$USER/BOOT/u-boot.img
```

![u-boot.img'yi kopyalama](../images/{33002E3B-4D53-4327-96B8-7109DF21F826}.png)

### <a name="c4-test-et-1"></a>Test et

[4.5](#c4-45-boot-prosedürü-her-testte-tekrarlanır)'teki adımlarla kartı aç.

- `U-Boot SPL` satırlarından sonra <b>U-Boot'un kendi mesajları</b> görünüyorsa bu aşama başarılı.
- Kernel ve `uEnv.txt` henüz olmadığı için Linux SD karttan açılmaz.

Sonuç: <b>RBL ✓ → MLO ✓ → U-Boot ✓ → Kernel ✗</b>

---

## <a name="c4-48-aşama-3-root-filesystem-ve-uenvtxt"></a>4.8 Aşama 3: Root Filesystem ve uEnv.txt

### <a name="c4-kopyala-2"></a>Kopyala

Kartı tekrar bilgisayara tak.

<b>1) Root filesystem'i ROOTFS bölümüne çıkar:</b>

```bash
sudo tar -xvf Angstrom-systemd-image-eglibc-ipk-v2012.12-beagleboard.rootfs.tar.xz -C /media/$USER/ROOTFS
```

| Parça | Anlamı |
|---|---|
| `sudo` | Linux dosyalarının sahibi `root`. Dosya izinlerinin korunması için gerekli. |
| `-x` `-v` `-f` | Arşivi aç (e<b>x</b>tract), açılan dosyaları göster (<b>v</b>erbose), arşiv dosyası (<b>f</b>ile) |
| `-C /media/$USER/ROOTFS` | Dosyaları bu klasöre çıkar |

![Rootfs arşivini açma](../images/{DA993575-2D08-4D85-AA87-3047E71E40D6}.png)

<b>2) uEnv.txt'yi BOOT bölümüne kopyala</b> (adı değişmiyor, U-Boot bu adla arar):

```bash
cp uEnv.txt /media/$USER/BOOT/
```

<b>Kontrol et:</b>

```bash
ls /media/$USER/BOOT/            # MLO  u-boot.img  uEnv.txt
ls /media/$USER/ROOTFS/boot/     # uImage ve am335x-boneblack.dtb burada olmalı
```

### <a name="c4-test-et-2"></a>Test et

[4.5](#c4-45-boot-prosedürü-her-testte-tekrarlanır)'teki adımlarla kartı aç. Rootfs büyük olduğu için `sync` biraz uzun sürebilir, bitmesini bekle.

Kernel mesajları akar ve sonunda <b>Ångström</b> logosu ile `beaglebone login:` satırı çıkar:

![Ångström login ekranı](../images/{F2BBFA98-4148-45FB-B849-710BC7F58DE9}.png)

Sonuç: <b>RBL ✓ → MLO ✓ → U-Boot ✓ → Kernel ✓ → Rootfs ✓</b> 🎉

> [!TIP]
> Giriş için kullanıcı adı `root` yaz. Bu demo imajında genelde şifre yoktur.

### <a name="c4-bu-açılışta-uenvtxt-ne-yaptı"></a>Bu açılışta uEnv.txt ne yaptı?

`uEnv.txt`, U-Boot'un davranışını değiştiren ayar dosyasıdır. BBB'nin U-Boot'u açılırken BOOT bölümündeki bu dosyayı okur ve içindeki `uenvcmd` komutunu çalıştırır.

![Kursun uEnv.txt dosyası](../images/{840192A1-87BA-43CA-887C-D739774088B9}.png)

| Satır | Anlamı |
|---|---|
| `console=ttyO0,115200n8` | Linux mesajları UART0'a (J1 header) 115200 baud ile yazılsın. |
| `ipaddr`, `serverip` | Ağdan boot için IP adresleri. SD karttan boot'ta kullanılmıyor. |
| `loadaddr=0x82000000` | Kernel'in (uImage) <b>RAM'de (DDR) yükleneceği adres</b>. |
| `fdtaddr=0x88000000` | Device tree (.dtb) dosyasının RAM'de yükleneceği adres. |
| `loadfromsd=load mmc 0:2 ...` | `mmc 0:2` = SD kart, 2. bölüm (ROOTFS). Oradaki `/boot/uImage` → `loadaddr`'e, `/boot/am335x-boneblack.dtb` → `fdtaddr`'e yüklenir. |
| `linuxbootargs=... root=/dev/mmcblk0p2 rw` | Kernel'e "root filesystem SD kartın 2. bölümünde, okuma-yazma modunda" bilgisini verir. |
| `uenvcmd=...` | U-Boot'un çalıştırdığı komut: önce `loadfromsd`, sonra `linuxbootargs`, en son `bootm` ile kernel'i başlat. `bootm`'deki `-` "initramfs yok" demek. |

> [!NOTE]
> AM335x'te DDR'in başlangıç adresi `0x80000000`'dır. `0x82000000` ise DDR'in içinde, kernel için seçilmiş bir adres.

Aynı dosya farklı yazılarak U-Boot'a kernel'i <b>ağdan (TFTP)</b>, rootfs'u da <b>bilgisayardaki bir klasörden (NFS)</b> aldırmak mümkün ([Bölüm 8](#c8-bölüm-8--tftp-ile-ağdan-boot)):

![TFTP ve NFS için uEnv.txt örneği](../images/{F9C9F3D8-B461-4FAC-A040-0F0ECEB76A7E}.png)

`uEnv.txt`'nin her satırını ve U-Boot komut satırını [Bölüm 6](#c6-bölüm-6--u-boot-komut-satırı-ve-uenvtxt)'da ayrıntılı göreceğiz.

---

## <a name="c4-49-uimage-nedir"></a>4.9 uImage Nedir?

`uImage`, U-Boot'un `bootm` komutuyla başlatabildiği kernel formatıdır. Yeni bir derleme yapılmaz. `zImage` dosyasının başına <b>64 byte'lık bir U-Boot header'ı</b> eklenir. Bu işi `mkimage` aracı yapar.

```
+-------------------+--------------------------------------+
| U-Boot Header     |               zImage                 |
|   (64 byte)       | (sıkıştırılmış, kendini açan kernel) |
+-------------------+--------------------------------------+
|<------------------------ uImage ------------------------>|
```

<b>Kernel imajları zinciri:</b>

| Dosya | Açıklama |
|---|---|
| `vmlinux` | Derlenmiş kernel. ELF formatında, sıkıştırılmamış. |
| `Image` | `vmlinux`'tan `objcopy` ile çıkarılmış ham binary |
| `zImage` | Sıkıştırılmış `Image` ve başında onu RAM'de açan küçük bir program |
| `uImage` | 64 byte U-Boot header + `zImage` |

<b>Header'ın içeriği</b> (`struct image_header`, tüm alanlar big-endian):

| Offset | Boyut | Alan | Anlamı |
|---|---|---|---|
| 0x00 | 4 | `ih_magic` | Sihirli sayı: `0x27051956` |
| 0x04 | 4 | `ih_hcrc` | Header'ın CRC32 değeri |
| 0x08 | 4 | `ih_time` | Oluşturulma zamanı |
| 0x0C | 4 | `ih_size` | zImage'in boyutu |
| 0x10 | 4 | `ih_load` | RAM'de kopyalanacağı adres |
| 0x14 | 4 | `ih_ep` | Çalıştırmanın başlayacağı adres (entry point) |
| 0x18 | 4 | `ih_dcrc` | zImage'in CRC32 değeri |
| 0x1C | 1 | `ih_os` | İşletim sistemi (Linux) |
| 0x1D | 1 | `ih_arch` | Mimari (ARM) |
| 0x1E | 1 | `ih_type` | İmaj tipi (kernel, ramdisk, script...) |
| 0x1F | 1 | `ih_comp` | Sıkıştırma tipi |
| 0x20 | 32 | `ih_name` | İmaj adı |

U-Boot bu header sayesinde dosyanın geçerli bir imaj olup olmadığını (magic number), bozulup bozulmadığını (CRC) ve RAM'de nereye yüklenip nereden çalıştırılacağını anlar.

---

## <a name="c4-410-uygulama-uimage-headerını-u-bootta-elle-okuma"></a>4.10 Uygulama: uImage Header'ını U-Boot'ta Elle Okuma

<b>Amaç:</b> uImage'ın başındaki 64 byte'lık U-Boot header'ını ([4.9](#c4-49-uimage-nedir)) kendi gözümüzle görmek.

<b>Neredeyiz?</b> [4.8](#c4-48-aşama-3-root-filesystem-ve-uenvtxt)'de U-Boot, `uEnv.txt`'deki komutları <b>otomatik</b> çalıştırıp Linux'u açtı. Bu sefer U-Boot'u durdurup aynı işin ilk yarısını <b>elle</b> yapacağız:

```
4.8:   RBL → MLO → U-Boot → Kernel → Rootfs → login     (otomatik)
4.10:  RBL → MLO → U-Boot ■ DUR → komutları elle yaz
```

| Adım | Komut | Ne yapar? |
|---|---|---|
| 1 | Açılışta bir tuşa bas | U-Boot'u durdurur, `U-Boot#` komut satırı gelir |
| 2 | `load mmc 0:2 0x82000000 /boot/uImage` | uImage'ı SD karttan DDR'e kopyalar |
| 3 | `md.b 0x82000000 40` | DDR'deki ilk 64 byte'ı (header) ekrana döker |
| 4 | — | Byte'ları header tablosuyla eşleştirip çözeriz |

> [!NOTE]
> <b>Neden önce DDR'e yüklüyoruz?</b> `md` (memory display) komutu sadece <b>belleği</b> okuyabilir. SD kart bir bellek adresi değil, depolama cihazıdır. Bu yüzden dosyayı önce RAM'e kopyalıyoruz.

Kursun bu dersinde Windows'ta Tera Term kullanılıyor. Minicom ile de komutlar ve çıktılar aynıdır ([2.6](#c2-26-windowsta-tera-term)).

### <a name="c4-4101-u-bootu-durdur"></a>4.10.1 U-Boot'u durdur

1. Seri terminali aç ve kartı [4.5.3](#c4-453-kartı-sd-karttan-aç-s2-butonu)'teki gibi SD karttan başlat.
2. Ekranda <b>`Hit any key to stop autoboot`</b> yazısı görünür görünmez bir tuşa (ör. <b>Space</b>) bas.
3. <b>`U-Boot#`</b> komut satırı geldiyse hazırsın.

> [!TIP]
> Geri sayım çok kısa (1–3 saniye). Kaçırırsan Linux açılır. Kartı yeniden başlatıp daha erken bas. Kart açılırken Space'e art arda basmak işe yarar.

### <a name="c4-4102-uimageı-ddre-yükle"></a>4.10.2 uImage'ı DDR'e yükle

Önce dosyanın orada olduğunu gör:

```bash
U-Boot# ls mmc 0:2 /boot
```

Sonra DDR'e yükle:

```bash
U-Boot# load mmc 0:2 0x82000000 /boot/uImage
```

| Parça | Anlamı |
|---|---|
| `load` | Bir dosya sisteminden dosyayı belleğe kopyala |
| `mmc 0:2` | MMC cihazı 0 (SD kart), 2. bölüm (ROOTFS) |
| `0x82000000` | DDR'de dosyanın yazılacağı adres (`uEnv.txt`'deki `loadaddr` ile aynı) |
| `/boot/uImage` | Bölüm içindeki dosyanın yolu |

#### <a name="c4-mmc-xy-ne-demek"></a>`mmc X:Y` ne demek?

```
load  mmc 0:2      0x82000000   /boot/uImage
      └─ NEREDEN ─┘ └─ NEREYE ─┘ └─ HANGİ DOSYA ┘
      SD kart,      DDR'deki      partition içindeki
      2. partition  bu adrese     dosya yolu
```

- <b>`X` = hangi MMC cihazı.</b> BeagleBone Black'te:
  - `mmc 0` → <b>microSD kart</b>
  - `mmc 1` → <b>eMMC</b> (karta lehimli dahili bellek)
- <b>`Y` = o cihazın kaçıncı partition'ı.</b> Numaralandırma <b>1'den</b> başlar.

> [!IMPORTANT]
> `load` her zaman <b>DDR'e</b> yükler. `mmc 0:2` dosyanın <b>nereye</b> yazılacağını değil, <b>nereden okunacağını</b> söyler. Yani "2. partition'a yükle" değil, "<b>2. partition'dan oku</b>, DDR'e yükle".

Bizim SD kartımız için:

| Yazım | Anlamı | İçinde ne var? |
|---|---|---|
| `mmc 0:1` | SD kart, 1. partition | BOOT (FAT16): `MLO`, `u-boot.img`, `uEnv.txt` |
| `mmc 0:2` | SD kart, 2. partition | ROOTFS (ext3): `/boot/uImage`, `/boot/am335x-boneblack.dtb`, Linux dosyaları |
| `mmc 1:...` | eMMC'nin partition'ları | Kartla fabrikadan gelen sistem (ör. Ångström/Debian) |

Örnekler:

```bash
U-Boot# ls mmc 0:1                                  # BOOT bölümünü listele
U-Boot# ls mmc 0:2 /boot                            # ROOTFS'taki /boot klasörünü listele
U-Boot# load mmc 0:1 0x82000000 uEnv.txt            # BOOT'taki uEnv.txt'yi DDR'e yükle
U-Boot# mmc list                                    # U-Boot'un gördüğü MMC cihazlarını listele
U-Boot# mmc dev 0                                   # SD kartı seç
U-Boot# mmc part                                    # Seçili cihazın partition tablosunu göster
```

> [!NOTE]
> Linux'ta da benzer bir numaralandırma vardır: `/dev/mmcblk0p2` = MMC cihazı 0, partition 2. `uEnv.txt`'deki `root=/dev/mmcblk0p2` ifadesi, U-Boot'taki `mmc 0:2` ile aynı yeri gösterir. Ancak Linux'un numaraları kernel sürümüne göre U-Boot'tan farklı olabilir, bu yüzden ikisinin her zaman aynı olacağını varsayma.

Çıktıda kaç byte okunduğu yazar (`xxxxxxx bytes read`). Bu sayı uImage'ın boyutudur, yani 64 byte header + zImage.

> [!NOTE]
> Bu komut `uEnv.txt`'deki `loadfromsd` satırının yaptığı işin aynısı. Fark sadece bu sefer elle yazmamız.

> [!TIP]
> `load` komutu tanınmazsa eski adı olan `ext2load mmc 0:2 0x82000000 /boot/uImage` komutunu kullan (ext3 de bu komutla okunur). `ls` yerine de `ext2ls mmc 0:2 /boot` kullanılır.

### <a name="c4-4103-headerı-ekrana-dök"></a>4.10.3 Header'ı ekrana dök

```bash
U-Boot# md.b 0x82000000 40
```

| Parça | Anlamı |
|---|---|
| `md` | memory display: belleği ekrana dök |
| `.b` | byte byte göster |
| `0x82000000` | Başlangıç adresi (uImage'ı yüklediğimiz yer) |
| `40` | Kaç byte gösterilecek. <b>U-Boot sayıları hex kabul eder:</b> `0x40` = <b>64 byte</b> = header'ın tamamı |

Çıktı 4 satırdır. Her satırda adres, 16 byte ve sağda bu byte'ların ASCII karşılığı bulunur.

> [!WARNING]
> `md` komutu nokta olmadan (`md 0x82000000 10`) yazılırsa veriyi <b>4 byte'lık word'ler</b> halinde gösterir. ARM işlemci <b>little-endian</b>, header ise <b>big-endian</b> olduğu için byte'lar ters görünür. Örneğin magic number `27051956` yerine <b>`56190527`</b> olarak görünür. Header'ı okurken `md.b` kullanmak daha kolaydır.

### <a name="c4-4104-byteları-çöz"></a>4.10.4 Byte'ları çöz

Çıktının her satırı header'ın şu alanlarına denk gelir:

```
82000000: [27 05 19 56] [.. .. .. ..] [.. .. .. ..] [.. .. .. ..]
            ih_magic      ih_hcrc       ih_time       ih_size
82000010: [.. .. .. ..] [.. .. .. ..] [.. .. .. ..] [..][..][..][..]
            ih_load       ih_ep         ih_dcrc      os arch type comp
82000020: [ ih_name: 32 byte imaj adı, sağdaki ASCII sütununda okunur ...
82000030:   ...                                                        ]
```

| Alan | Nasıl kontrol edilir? |
|---|---|
| `ih_magic` | `27 05 19 56` olmalı. Değilse bu adreste geçerli bir uImage yok. |
| `ih_time` | Unix zaman damgası. Linux'ta tarihe çevir: `date -d @$((0xXXXXXXXX))` |
| `ih_size` | zImage boyutu. Ondalığa çevir: `echo $((0xXXXXXXXX))`. Bu değer + 64 = `load` komutunun okuduğu byte sayısı olmalı. |
| `ih_load`, `ih_ep` | Kernel'in DDR'de çalışacağı adres ve başlangıç noktası |
| `os` | `05` = Linux |
| `arch` | `02` = ARM |
| `type` | `02` = Kernel |
| `comp` | `00` = sıkıştırma yok. zImage zaten kendini açtığı için U-Boot ayrıca açmaz. |
| `ih_name` | Sağdaki ASCII sütununda imajın adı okunur |

> [!TIP]
> Hex'i ondalığa çevirmek için Windows Hesap Makinesi'nin <b>Programcı</b> modunu da kullanabilirsin.

### <a name="c4-4105-sonucu-u-boota-doğrulat"></a>4.10.5 Sonucu U-Boot'a doğrulat

Elle çözdüğün değerleri U-Boot'un kendi çözümüyle karşılaştır:

```bash
U-Boot# iminfo 0x82000000
```

`iminfo` komutu header'ı okuyup Image Name, Created, Image Type, Data Size, Load Address ve Entry Point bilgilerini yazar. Ayrıca CRC'yi kontrol eder (`Verifying Checksum ... OK`). Değerler senin bulduklarınla aynı olmalı.

### <a name="c4-4106-linuxu-başlat"></a>4.10.6 Linux'u başlat

İşin bitince Linux'u normal şekilde açmak için:

```bash
U-Boot# boot
```

Ya da kartı yeniden başlat (`reset` veya Power butonu).

### <a name="c4-komut-özeti"></a>Komut özeti

| Komut | Ne yapar? |
|---|---|
| `ls mmc 0:2 /boot` | SD kartın 2. bölümündeki `/boot` klasörünü listeler |
| `load mmc 0:2 0x82000000 /boot/uImage` | uImage'ı DDR'de `0x82000000` adresine yükler |
| `md.b 0x82000000 40` | O adresten başlayarak 64 byte'ı byte byte gösterir |
| `iminfo 0x82000000` | O adresteki uImage header'ını çözüp yazar |
| `boot` | Normal açılışa devam eder (Linux'u başlatır) |
| `reset` | Kartı yeniden başlatır |
| `help` | Tüm U-Boot komutlarını listeler (`help md` gibi tek komut için de olur) |

---

## <a name="c4-411-kursun-güncel-sd-kart-i̇majları-u-boot-202204--kernel-510168"></a>4.11 Kursun Güncel SD Kart İmajları (U-Boot 2022.04 + Kernel 5.10.168)

Bu bölümde kullandığımız Ångström dosyaları kursun ilk sürümünden kalma (2013). Kursun reposundaki `pre-built-images/SD-boot` klasöründe güncel bir set de var:

| Dosya | İçerik | SD kartta nereye? |
|---|---|---|
| `MLO`, `u-boot.img` | U-Boot 2022.04 | BOOT |
| `uImage` | Linux 5.10.168 | BOOT |
| `am335x-boneblack.dtb` | Aynı kernel'in device tree'si | BOOT |
| `uEnv.txt` | Aşağıda | BOOT |

Farklar:
- Kernel ve DTB artık ROOTFS'teki `/boot` klasöründe değil, <b>BOOT (FAT) bölümünde</b> duruyor. `load mmc 0:1 ...` ile okunuyor.
- Bu set bir rootfs içermiyor. ROOTFS bölümüne [Bölüm 12](#c12-bölüm-12--busybox-ile-minimal-root-filesystem)'de BusyBox ile hazırlayacağımız dosya sistemini koyacağız. Kernel 5.10 ile 2012 tarihli Ångström rootfs'i birlikte çalışmaz.
- Bu U-Boot'ta `bootdelay=0`: geri sayım yok. U-Boot'u durdurmak için kart açılırken <b>Space'e basılı tut</b>. Bekleme süresini uzatmak [9.4](#c9-94-challenge-autoboot-bekleme-süresini-10-saniyeye-çıkarmak)'ün konusu.

Kursun `uEnv.txt`'si:

```text
console=ttyS0,115200n8
netargs=setenv bootargs console=ttyO0,115200n8 root=/dev/mmcblk0p2 rw rootfstype=ext4 rootwait debug earlyprintk mem=512M
netboot=echo Booting from microSD ...; setenv autoload no ; load mmc 0:1 ${loadaddr} uImage ; load mmc 0:1 ${fdtaddr} am335x-boneblack.dtb ; run netargs ; bootm ${loadaddr} - ${fdtaddr}
uenvcmd=run netboot
```

| Parça | Anlamı |
|---|---|
| `rootfstype=ext4` | Rootfs'in dosya sistemi türü. ext4 sürücüsü ext3 bölümleri de bağlayabilir. |
| `rootwait` | Kernel, rootfs'in bulunduğu aygıt (SD kart) hazır olana kadar bekler. MMC aygıtları geç algılandığı için önemli. |
| `debug earlyprintk` | Açılışta daha fazla mesaj basar. Sorun ayıklarken işe yarar. |
| `mem=512M` | Kernel'e kullanacağı RAM miktarını söyler. |
| `${loadaddr}`, `${fdtaddr}` | U-Boot'un kendi varsayılan değişkenleri (`0x82000000`, `0x88000000`). Dosyada tanımlanmadıkları halde çalışır. |

> [!WARNING]
> Dosyanın ilk satırında `console=ttyS0` tanımlanmış ama `netargs` bu değişkeni kullanmıyor, `console=ttyO0` yazıyor. Kernel 5.10'da UART0'ın adı `ttyS0`'dır ([3.4](#c3-34-linux-kernel-ve-root-filesystem)). Açılışta `Starting kernel ...`'dan sonra mesaj göremezsen `netargs` içinde `console=${console}` kullan.

## <a name="c4-412-özet"></a>4.12 Özet

- SD kart iki bölümden oluşur: <b>BOOT</b> (FAT16, `boot` bayraklı: `MLO`, `u-boot.img`, `uEnv.txt`) ve <b>ROOTFS</b> (ext3: kernel, DTB ve Linux dosyaları).
- Dosya adları önemli: RBL tam olarak <b>`MLO`</b>'yu, MLO tam olarak <b>`u-boot.img`</b>'yi arar.
- Kartı SD karttan açmak için güç verirken <b>S2</b>'yi basılı tut.
- U-Boot `uEnv.txt`'deki `uenvcmd`'yi çalıştırır: kernel ve DTB'yi `mmc 0:2`'den RAM'e yükler, `bootargs`'ı ayarlar, `bootm` ile başlatır.
- `uImage` = 64 byte U-Boot header + `zImage`. `md.b` ile byte byte, `iminfo` ile çözülmüş halde okunabilir.

## <a name="c4-413-karşılaşılabilecek-problemler"></a>4.13 Karşılaşılabilecek Problemler

| Belirti | Olası sebep |
|---|---|
| Minicom'da hiçbir şey yok | TX/RX çapraz bağlı mı? Baud 115200 mü? Hardware Flow Control kapalı mı? ([2.8](#c2-28-karşılaşılabilecek-problemler)) |
| Sürekli `CCCCCCCC...` | RBL, MLO'yu bulamadı. Dosya adı tam `MLO` mu? BOOT bölümü FAT mı? `boot` bayrağı var mı? |
| `error reading image u-boot.img` | BOOT'ta `u-boot.img` yok veya adı yanlış. |
| Eski Linux açılıyor (Debian vb.) | Kart eMMC'den açıldı. S2 açılış anında basılı değildi. |
| U-Boot `/boot/uImage` bulamıyor | Rootfs ROOTFS bölümüne çıkarılmamış veya yanlış klasöre çıkarılmış. |
| `Kernel panic ... Unable to mount root fs` | ROOTFS bölümü boş veya `sync` yapılmadan kart çıkarılmış. |


<div class="page-break"></div>

# <a name="c5-bölüm-5--emmcden-boot"></a>Bölüm 5 — eMMC'den Boot

> <b>Bu bölümde:</b>
> - eMMC'nin ne olduğunu ve DDR RAM'den farkını öğreneceksin.
> - Güncel bir Debian imajını önce SD karta yazıp sonra <b>flasher script</b> ile eMMC'ye aktaracaksın.
> - Karta USB üzerinden SSH ile bağlanmayı göreceksin.
>
> <b>Ön koşul:</b> [Bölüm 3](#c3-bölüm-3--linux-boot-süreci-rbl--spl--u-boot) — boot sırası ve S2, [Bölüm 4](#c4-bölüm-4--sd-karttan-boot) — SD karttan boot.

---

## <a name="c5-51-hatırlatma-emmc-nedir"></a>5.1 Hatırlatma: eMMC Nedir?

<b>eMMC (embedded MultiMediaCard)</b>, BeagleBone Black'in üzerine lehimli olarak gelen dahili depolama birimidir. Aslında içinde bir SD kart vardır ve doğrudan karta lehimlenmiştir. Kapasitesi Rev C'de <b>4 GB</b>, eski Rev B'de <b>2 GB</b>'tır.

- Kartın <b>kalıcı depolama alanıdır</b>. Bilgisayardaki HDD/SSD gibi düşünebilirsin.
- Kart fabrikadan eMMC'de yüklü bir Debian ile gelir. Bu yüzden SD kart takmadan güç verildiğinde Linux açılır.
- SD karta göre <b>daha hızlı ve güvenilirdir</b>: 8-bit veri yolu ve dahili denetleyicisi vardır. Kartın üzerinde olduğu için çıkmaz, kaybolmaz, temas sorunu yaşamaz. Bu yüzden ürünlerde (sahadaki cihazlarda) tercih edilir.

### <a name="c5-ddr-ram-ile-farkı"></a>DDR RAM ile farkı

| | DDR RAM | eMMC |
|---|---|---|
| <b>PC karşılığı</b> | RAM | HDD / SSD |
| <b>Kalıcılık</b> | Geçici, güç gidince silinir | Kalıcı |
| <b>Görevi</b> | Çalışma alanı | Depolama |
| <b>BBB'de boyut</b> | 512 MB DDR3L | 4 GB (Rev C) |

> [!NOTE]
> İşlemci kodu doğrudan eMMC'den çalıştırmaz. Açılışta MLO, U-Boot, kernel ve device tree eMMC'den okunur, adım adım RAM'e yüklenir ve orada çalıştırılır.

---

## <a name="c5-52-donanım-bağlantısı"></a>5.2 Donanım Bağlantısı

![BBB'de eMMC, SD kart ve DDR bağlantısı](../images/{E7E4FC4C-DBAC-4C4E-8FE5-D1274DAB2D14}.png)

| Bileşen | AM335x'e bağlantısı | Linux'ta (genelde) |
|---|---|---|
| <b>4 GB eMMC</b> | <b>mmc1</b> arayüzü (8-bit) | `mmcblk1` |
| <b>microSD kart</b> | <b>mmc0</b> arayüzü | `mmcblk0` |
| <b>DDR (512 MB)</b> | DDR arayüzü | - |

> [!CAUTION]
> Numaralandırma kernel sürümüne ve device tree'ye göre değişebilir. Bir diske bir şey yazmadan önce <b>`lsblk` ile mutlaka kontrol et</b>. Yanlış diske yazmak oradaki sistemi siler.

Varsayılan boot sırasında eMMC ilk sıradadır. eMMC'de geçerli bir MLO varsa kart oradan açılır, SD kart takılı olsa bile ona bakmaz. SD karttan açmak için <b>güç verirken S2'ye basılı tutulmalıdır</b> ([3.5](#c3-35-boot-kaynakları-ve-boot-sırası-sysboot-pinleri)).

---

## <a name="c5-53-emmcye-debian-yükleme-teori"></a>5.3 eMMC'ye Debian Yükleme (Teori)

eMMC'ye doğrudan bilgisayardan yazılamaz, çünkü kartın üzerine lehimlidir. Bu yüzden önce <b>SD karttan</b> boot edilir, sonra SD karttaki her şey eMMC'ye kopyalanır.

![eMMC'ye Debian yükleme adımları](../images/{BEFA8946-6220-443D-B624-79EA686B7EC1}.png)

1. En güncel <b>Debian OS</b> image'ını indir.
2. Bootable image'ı önce <b>SD karta</b> yaz.
3. Kartı <b>SD karttan boot et</b> (güç verirken S2'ye basılı tut).
4. <b>eMMC flasher script</b>'ini çalıştır.
5. Flasher script, <b>SD karttaki her şeyi eMMC'ye kopyalar</b>.

### <a name="c5-emmc-flasher-script-ne-yapar"></a>eMMC flasher script ne yapar?

![eMMC flasher script akışı](../images/{5F2184FB-5B91-43CB-8B04-0FDA7014DD3B}.png)

1. Script <b>SD karttan</b> çalıştırılır.
2. eMMC iki bölüme (partition) ayrılır: <b>FAT</b> ve <b>EXT4</b>.
3. Bu bölümler formatlanır ve dosya sistemleri oluşturulur:
   - <b>FAT</b>: Boot dosyaları (MLO, u-boot.img vb.)
   - <b>EXT4</b>: Root dosya sistemi (rootfs)
4. SD karttaki tüm içerik yeni oluşturulan bölümlere kopyalanır.
5. İş bitince kart <b>kapatılır</b>.

> [!NOTE]
> Bu, [Bölüm 4](#c4-bölüm-4--sd-karttan-boot)'te SD kart için GParted ile elle yaptığımız bölümlendirme ve kopyalama işleminin eMMC için otomatik yapılan halidir.

---

## <a name="c5-54-uygulama-emmcyi-güncelleme"></a>5.4 Uygulama: eMMC'yi Güncelleme

### <a name="c5-541-kartın-ip-adresini-öğren"></a>5.4.1 Kartın IP adresini öğren

Kartı bilgisayara bağladığın yönteme göre IP adresi değişir. Güncel liste: <https://beagleboard.org/getting-started>

![BeagleBone IP adresleri](../images/{C5156823-84C4-41B0-8EC4-B5835A0CD1A6}.png)

| Bağlantı | Bilgisayarın işletim sistemi | IP adresi |
|---|---|---|
| USB | Windows | `192.168.7.2` |
| USB | Mac OS X, <b>Linux</b> | `192.168.6.2` |
| WiFi | Hepsi | `192.168.8.1` |
| Hepsi (mDNS) | Hepsi | `beaglebone.local` |

Bağlantıyı test etmek için:

```bash
ping 192.168.6.2
```

### <a name="c5-542-ssh-ile-karta-bağlan"></a>5.4.2 SSH ile karta bağlan

> [!TIP]
> SSH'ın bilgisayarında yüklü olup olmadığını `ssh -V` komutuyla kontrol edebilirsin. Yüklü değilse Ubuntu'da `sudo apt install openssh-client`, Fedora'da `sudo dnf install openssh-clients` ile kurabilirsin.

```bash
ssh debian@192.168.6.2
```

![SSH ile BeagleBone'a bağlanma](../images/{A9566984-B563-4C49-A9A1-9816B21F6E62}.png)

Bağlanınca kart karşılama mesajında varsayılan kullanıcı adını ve şifreyi gösterir. `password:` satırına şifreyi yaz:

| Kullanıcı adı | Şifre |
|---|---|
| `debian` | `temppwd` |

> [!NOTE]
> Şifre yazarken ekranda hiçbir karakter görünmez. Bu normaldir, yazmaya devam edip Enter'a bas.

> [!IMPORTANT]
> `temppwd` şifresi kartla gelen <b>eski image'larda</b> geçerlidir. En güncel image'larda varsayılan şifre yoktur. Kullanıcı adı ve şifre, SD karta yazdıktan sonra FAT bölümündeki <b>`sysconf.txt`</b> dosyasından ilk açılıştan önce ayarlanmalıdır ([5.4.4](#c5-544-en-güncel-imageı-indir)).

İlk bağlantıda `Are you sure you want to continue connecting (yes/no)?` diye sorarsa `yes` yaz.

### <a name="c5-543-karttaki-debian-sürümünü-kontrol-et"></a>5.4.3 Karttaki Debian sürümünü kontrol et

```bash
lsb_release -da
```

![Debian sürümünü kontrol etme](../images/{636C391B-AE68-4635-A859-93F6D5533991}.png)

Bu örnekte kartta <b>Debian 10 (buster)</b> yüklü.

> [!TIP]
> Kartında zaten en güncel Debian image'ı yüklüyse bu bölümün geri kalanını atlayabilirsin.

### <a name="c5-544-en-güncel-imageı-indir"></a>5.4.4 En güncel image'ı indir

Güncel image'lar: <https://beagleboard.org/latest-images>

![En güncel BeagleBone Black Debian image'ı](../images/{F642D326-33B6-4A9D-B77A-6F9932E2AF22}.png)

Bu notun yazıldığı tarihte en güncel sürüm <b>Debian 13.7 (2026-10-09, IoT)</b> idi. Karttaki Debian 10'dan çok daha yeni olduğu için eMMC'yi güncellemek gerekiyor.

- <b>Image</b> butonu ile `.img.xz` dosyasını indir.
- İstersen <b>sha256</b> ile indirdiğin dosyanın bozulmadığını kontrol edebilirsin:
  ```bash
  sha256sum <indirilen-dosya>.img.xz
  ```
  Çıkan değer sitedeki sha256 değeriyle aynı olmalı.

> [!IMPORTANT]
> Sitedeki açıklamada da yazdığı gibi, bu image'da kullanıcı şifresi <b>ilk açılıştan önce</b> FAT32 bölümündeki `sysconf.txt` dosyasından ayarlanmalıdır.

### <a name="c5-545-imageı-sd-karta-yaz-balenaetcher"></a>5.4.5 Image'ı SD karta yaz (balenaEtcher)

Bu image doğrudan eMMC'ye yazılamaz. Önce <b>SD karta</b> yazılır, ardından kart SD karttan açılıp eMMC'ye aktarılır ([5.3](#c5-53-emmcye-debian-yükleme-teori)). SD karta yazmak için bir programa ihtiyacımız var: <b>balenaEtcher</b> (<https://etcher.balena.io>).

![balenaEtcher](../images/{A7E04BE8-B7AF-43AA-A284-2D62653B27FF}.png)

#### <a name="c5-neden-dosyayı-sd-karta-kopyalamak-yetmiyor"></a>Neden dosyayı SD karta kopyalamak yetmiyor?

İndirilen `.img.xz` dosyası normal bir dosya değil, <b>bütün bir diskin birebir kopyasıdır</b>:

```
Debian image'ı (.img)
├── Bölüm tablosu (partition table)   → diskin hangi kısmı hangi bölüm
├── BOOT bölümü (FAT)                  → MLO, u-boot.img, sysconf.txt ...
└── rootfs bölümü (EXT4)               → Debian'ın tamamı
```

Dosyayı sürükle-bırak ile kopyalarsan SD kartta sadece tek bir büyük `.img` dosyası olur ve kart açılmaz. Etcher ise image'ı <b>diskin en başından itibaren ham olarak (byte byte) yazar</b>. Böylece SD kart image'daki bölümlere birebir sahip olur ve boot edilebilir hale gelir.

#### <a name="c5-etcher-ile-yazma-adımları"></a>Etcher ile yazma adımları

![balenaEtcher image ve hedef seçimi](../images/{89A9E107-ACD1-4ABC-8E08-3421A12E07A1}.png)

1. <b>Flash from file</b> ile indirdiğin image dosyasını seç (kursta: `bone-debian-10.3-iot-armhf-2020-04-06-4gb.img.xz`).
2. <b>Select target</b> ile SD kartı seç. Kart okuyucu bilgisayarda bir USB depolama aygıtı olarak görünür.
3. <b>Flash!</b> butonuna bas. Yazma ve doğrulama (verify) bitene kadar bekle.

![balenaEtcher hedef listesi](../images/{2B998CAA-4FFD-45B2-B007-FC0D16591C0A}.png)

Bu örnekte iki aygıt görünüyor:

| Aygıt | Boyut | Konum | Açıklama |
|---|---|---|---|
| Compute Module | 18.9 MB | `/dev/sdb` | <b>Locked / Too small</b>, seçilemez |
| <b>Generic STORAGE DEVICE</b> | <b>15.9 GB</b> | <b>`/dev/sdc`</b> | <b>SD kart</b> → bunu seç |

#### <a name="c5-hangisi-sd-kart-dmesg"></a>Hangisi SD kart? (`dmesg`)

Listede birden fazla aygıt çıkarsa ve hangisinin SD kart olduğundan emin değilsen, SD kartı taktıktan hemen sonra terminalde şunu çalıştır:

```bash
sudo dmesg | tail -20
```

![dmesg çıktısında SD kart](../images/{234B1B38-C164-43DF-806A-DEDC74BC56D7}.png)

Son satırlarda yeni takılan aygıtın adı ve boyutu görünür. Bu örnekte `[sdc] ... (15.9 GB/14.8 GiB)` satırı, SD kartın <b>`/dev/sdc`</b> olduğunu gösteriyor.

> [!TIP]
> `lsblk` komutu da aygıtları boyutlarıyla listeler. Harf (`sdb`, `sdc` ...) bilgisayardan bilgisayara değişir. Her seferinde boyuta bakarak kontrol et.

### <a name="c5-546-kartı-sd-karttan-boot-et"></a>5.4.6 Kartı SD karttan boot et

1. Kartın <b>gücünü kes</b>.
2. SD kartı BeagleBone'a <b>tak</b>.
3. Güç kablosunu tak.
4. <b>Power</b> butonuna LED'ler sönene kadar basılı tut, LED'ler sönünce bırak. Kart artık kapalı.
5. <b>S2</b> butonunu basılı tut ve bu sırada <b>Power</b> butonuna bir kez basıp bırak.
6. S2'yi <b>2-3 saniye</b> daha basılı tut, sonra bırak.
7. Kart SD karttan açılmaya başlar. Bu sırada LED'ler hızlı hızlı yanıp söner.

![Bilgisayarda BEAGLEBONE sürücüsünün görünmesi](../images/{2FE13611-4F3E-470D-A47B-6F11660D9A1E}.png)

Bilgisayarında <b>BEAGLEBONE</b> adında bir sürücü göründüyse kart açılmıştır. Şimdi [5.4.2](#c5-542-ssh-ile-karta-bağlan)'deki SSH komutuyla tekrar bağlan:

```bash
ssh debian@192.168.6.2
```

> [!NOTE]
> Bağlanırken `REMOTE HOST IDENTIFICATION HAS CHANGED!` uyarısı alırsan bu normaldir. Kart farklı bir sistemden (SD karttan) açıldığı için SSH anahtarı değişmiştir. Eski kaydı silip tekrar bağlan:
> ```bash
> ssh-keygen -R 192.168.6.2
> ```

### <a name="c5-547-emmc-flasher-scriptini-çalıştır"></a>5.4.7 eMMC flasher script'ini çalıştır

Flasher script'leri `/opt/scripts/tools/eMMC` klasöründe bulunur:

```bash
cd /opt/scripts/tools/eMMC
ls
```

![/opt/scripts/tools klasörü](../images/{BAD46DD7-DA20-4EB4-8CE6-B29608D5247C}.png)

![eMMC klasöründeki flasher script'leri](../images/{5EA08989-D8DE-4213-8D3E-F2E49B150C0F}.png)

Listede birçok script var. BeagleBone Black için kullanılan <b>`init-eMMC-flasher-v3.sh`</b>:

```bash
sudo ./init-eMMC-flasher-v3.sh
```

> [!CAUTION]
> Bu script eMMC'deki <b>her şeyi siler</b> ve yerine SD karttaki sistemi yazar. eMMC'de saklamak istediğin dosya varsa önce yedekle.

> [!NOTE]
> Bu klasör ve script adı kursta kullanılan <b>Debian 10.3</b> image'ına göredir. Daha yeni image'larda flasher farklı bir yerde veya farklı bir adla olabilir. Klasör yoksa image'ın açıklamasına bakarak flasher yöntemini kontrol et.

Script çalışırken [5.3](#c5-emmc-flasher-script-ne-yapar)'te anlatılan adımları sırayla yapar: bölümlendirme → formatlama → kopyalama. Bu birkaç dakika sürer.

![Flash işleminin başarıyla bitmesi](../images/{AD5A6E4A-82A3-42BB-AF46-ED6CD3D8F487}.png)

Flash işlemi başarılıysa şu mesajı görürsün:

```
eMMC has been flashed: please wait for device to power down.
```

Ardından kart kendini kapatır ve SSH bağlantısı kopar (`Connection to 192.168.6.2 closed by remote host.`). Bu normaldir.

### <a name="c5-548-emmcden-boot-et"></a>5.4.8 eMMC'den boot et

1. SD kartı BeagleBone'dan <b>çıkar</b>. Artık ona ihtiyacın yok.
2. <b>Power</b> butonuna bir kez bas (S2'ye <b>basmadan</b>). Kart artık eMMC'den açılır.
3. SSH ile tekrar bağlan:
   ```bash
   ssh debian@192.168.6.2
   ```
4. Yeni sürümün yüklendiğini kontrol et:
   ```bash
   lsb_release -da
   ```

---

## <a name="c5-55-özet"></a>5.5 Özet

- eMMC kartın kalıcı, dahili deposudur (MMC1). DDR ise geçici çalışma belleğidir.
- eMMC'ye doğrudan yazılamaz: imaj önce <b>balenaEtcher</b> ile SD karta yazılır, kart <b>S2</b> ile SD karttan açılır, <b>flasher script</b> SD karttaki sistemi eMMC'ye kopyalar.
- USB üzerinden kartın adresi Linux'ta `192.168.6.2`, Windows'ta `192.168.7.2`. Bağlantı: `ssh debian@192.168.6.2`.

## <a name="c5-56-karşılaşılabilecek-problemler"></a>5.6 Karşılaşılabilecek Problemler

| Belirti | Sebep | Çözüm |
|---|---|---|
| `ping 192.168.6.2` cevap vermiyor | Kart henüz açılmadı ya da Windows'tasın | 1–2 dakika bekle. Windows'ta adres `192.168.7.2`. `beaglebone.local` da denenebilir. |
| `REMOTE HOST IDENTIFICATION HAS CHANGED!` | Kart farklı bir sistemden açıldı | `ssh-keygen -R 192.168.6.2` |
| Şifre kabul edilmiyor | Yeni image'da varsayılan şifre yok | SD karttaki `sysconf.txt` ile kullanıcı/şifre belirle ([5.4.4](#c5-544-en-güncel-imageı-indir)) |
| `/opt/scripts/tools/eMMC` yok | Image sürümü farklı | Image'ın açıklamasındaki flasher yöntemini kullan |
| Kart flash'tan sonra yine eski sistemle açılıyor | SD kart hâlâ takılı ve S2'ye basıldı / flash yarıda kaldı | SD kartı çıkar, S2'ye basmadan aç. Gerekirse flash'ı tekrarla. |


<div class="page-break"></div>

<div class="part-title">Kısım III<br>U-Boot ile Çalışmak</div>

<div class="page-break"></div>

# <a name="c6-bölüm-6--u-boot-komut-satırı-ve-uenvtxt"></a>Bölüm 6 — U-Boot Komut Satırı ve uEnv.txt

> <b>Bu bölümde:</b>
> - `uEnv.txt` dosyasının <b>satır satır ne yaptığını</b> anlayacaksın.
> - Bu dosyayı SD karta kopyalamadan, <b>seri port (UART) üzerinden</b> doğrudan U-Boot'a göndereceksin (`loady`, `env import`).
> - Kursun challenge'ı: boot imajlarını eMMC yerine <b>SD karttan (MMC0)</b> yükleyeceksin. Ek alıştırmada da tersini yapıp rootfs'i <b>eMMC'den</b> bağlayacaksın.
> - <b>ROOTFS</b> bölümünde hangi klasör ve dosyaların olduğunu ve bunlara <b>hangi komutlarla</b> ulaşacağını göreceksin.
>
> <b>Ön koşul:</b> [Bölüm 4](#c4-bölüm-4--sd-karttan-boot) — SD karttan boot, [Bölüm 5](#c5-bölüm-5--emmcden-boot) — eMMC'deki Debian.

> [!NOTE]
> Bu bölümdeki terminal görüntüleri temsilidir. Senin kartında U-Boot sürümü, dosya boyutları ve bölüm boyutları farklı görünebilir.

---

## <a name="c6-61-temel-kavramlar"></a>6.1 Temel Kavramlar

| Kavram | Ne işe yarar? |
|---|---|
| <b>`uEnv.txt`</b> | U-Boot ortam değişkenlerini <b>metin olarak</b> tanımlayan dosya. Her satır `isim=değer` biçimindedir. U-Boot'un bu dosyayı açılışta otomatik okuyup okumaması, U-Boot'un yapılandırmasına bağlıdır (BBB'nin varsayılan U-Boot'u SD karttaki `uEnv.txt`'yi arar). |
| <b>Ortam değişkeni (environment)</b> | U-Boot'un ayarları ve makroları. `printenv` ile görülür, `setenv` ile değiştirilir, `saveenv` ile kalıcı kaydedilir. |
| <b>Minicom</b> | Bilgisayardan seri port (UART) üzerinden karta bağlanmayı sağlayan terminal programı ([Bölüm 2](#c2-bölüm-2--seri-konsol-ve-minicom)). |
| <b>`loady`</b> | U-Boot'ta <b>YMODEM</b> protokolüyle seri porttan dosya alıp RAM'e yazan komut. |
| <b>`env import -t <adres> <boyut>`</b> | RAM'deki `isim=değer` metnini okuyup U-Boot'un <b>aktif</b> ortamına ekler. `-t` "düz metin" demektir, `<boyut>` metnin bayt cinsinden uzunluğudur. |

Bütün akış şöyle:

```
Bilgisayar (uEnv.txt) ──YMODEM / UART──► RAM 0x82000000 ──env import──► U-Boot ortamı ──boot──► Linux
```

---

## <a name="c6-62-uenvtxt-satır-satır"></a>6.2 `uEnv.txt` Satır Satır

Kullanacağımız dosya bu:

```text
mypcip=setenv serverip 192.168.1.2
ipaddr=192.168.27.1
bootargs=console=ttyO0,115200 root=/dev/mmcblk0p2 rw
bootcmd=echo "**********Booting from memory**********";load mmc 0:1 0x82000000 uImage;load mmc 0:1 0x88000000 am335x-boneblack.dtb;bootm 0x82000000 - 0x88000000
```

### <a name="c6-mypcip-ve-ipaddr--ağ-ayarları"></a>`mypcip` ve `ipaddr` — ağ ayarları

| Satır | Anlamı |
|---|---|
| `mypcip=setenv serverip 192.168.1.2` | Bir <b>makro</b>. Kendi başına hiçbir şey yapmaz; `run mypcip` yazınca içindeki komut çalışır ve `serverip` (TFTP/NFS sunucusunun, yani bilgisayarın IP'si) `192.168.1.2` olur. |
| `ipaddr=192.168.27.1` | Kartın kendi statik IP adresi. |

> [!WARNING]
> Bu örnekte kart `192.168.27.x`, sunucu `192.168.1.x` ağında. Ağ geçidi (`gatewayip`) tanımlanmadığı sürece TFTP/NFS çalışmaz. Ağdan boot yapacaksan iki adresi <b>aynı alt ağda</b> seç ([Bölüm 8](#c8-bölüm-8--tftp-ile-ağdan-boot)). SD karttan boot için bu iki satır kullanılmaz.

### <a name="c6-bootargs--kernele-verilen-parametreler"></a>`bootargs` — kernel'e verilen parametreler

`bootargs=console=ttyO0,115200 root=/dev/mmcblk0p2 rw`

| Parça | Anlamı |
|---|---|
| `console=ttyO0,115200` | Linux mesajları UART0'a (J1 header) 115200 baud ile yazılsın. `ttyO0` eski OMAP kernel'lerindeki addır; yeni kernel'lerde `ttyS0` olur. |
| `root=/dev/mmcblk0p2` | Root filesystem: MMC aygıtı <b>0</b>, bölüm <b>2</b> (`p2`). |
| `rw` | Rootfs okuma-yazma modunda bağlansın. |

### <a name="c6-bootcmd--otomatik-açılış-komutu"></a>`bootcmd` — otomatik açılış komutu

`bootcmd`, `;` ile ayrılmış komutlardan oluşur. U-Boot bunları sırayla çalıştırır:

| Sıra | Komut | Ne yapar? |
|---|---|---|
| 1 | `echo "****Booting from memory****"` | Ekrana mesaj basar (hangi yoldan açıldığını görmek için). |
| 2 | `load mmc 0:1 0x82000000 uImage` | `mmc 0:1` = SD kart, 1. bölüm (BOOT). Oradaki `uImage` dosyasını RAM'de `0x82000000` adresine yükler. |
| 3 | `load mmc 0:1 0x88000000 am335x-boneblack.dtb` | Aynı bölümdeki device tree dosyasını (DTB) `0x88000000` adresine yükler. |
| 4 | `bootm 0x82000000 - 0x88000000` | Kernel'i başlatır. Ortadaki `-` "initramfs yok" demektir, son adres DTB'nin adresidir. |

```
RAM (DDR, 0x80000000'dan başlar)
├── 0x82000000  →  uImage   (kernel)
└── 0x88000000  →  am335x-boneblack.dtb
```

> [!NOTE]
> `mmc 0` ↔ `/dev/mmcblk0` eşleşmesi çoğu kurulumda doğrudur ama <b>garanti değildir</b>. U-Boot tarafında `mmc list`, Linux tarafında `lsblk` ile kontrol et ([6.5](#c6-65-ek-alıştırma-kernel-ve-dtb-sd-karttan-rootfs-emmcden)).

---

## <a name="c6-63-uygulama-uenvtxtyi-seri-porttan-göndermek"></a>6.3 Uygulama: `uEnv.txt`'yi Seri Porttan Göndermek

Normalde `uEnv.txt` SD kartın BOOT bölümüne kopyalanır. Her değişiklikte SD kartı çıkar-tak yapmak yerine dosyayı <b>seri porttan</b> gönderip anında deneyebiliriz.

### <a name="c6-adım-1--bilgisayarda-dosyayı-hazırla-ve-minicomu-aç"></a>Adım 1 — Bilgisayarda dosyayı hazırla ve Minicom'u aç

Dosyanın içeriğini ve <b>boyutunu</b> kontrol et, sonra Minicom ile karta bağlan:

![uEnv.txt hazırlama ve Minicom'u açma](../images/uenv/01_uenv_hazirla.png)

> [!TIP]
> Windows'ta port adı `/dev/ttyUSB0` yerine `COM3` gibi olur ([2.6](#c2-26-windowsta-tera-term)).

### <a name="c6-adım-2--u-bootu-durdur"></a>Adım 2 — U-Boot'u durdur

Kartı aç. `Hit any key to stop autoboot` yazısı çıkınca <b>bir tuşa bas</b>. `U-Boot#` komut satırı gelmeli:

![U-Boot autoboot'u durdurma](../images/uenv/02_uboot_durdur.png)

### <a name="c6-adım-3--loady-ile-dosyayı-rame-al"></a>Adım 3 — `loady` ile dosyayı RAM'e al

U-Boot'ta YMODEM alımını başlat:

```text
U-Boot# loady 0x82000000
```

U-Boot `C` karakterleri basarak beklemeye başlar. Şimdi Minicom'da:

1. `Ctrl-A` → `S` (Send files)
2. Protokol olarak <b>ymodem</b> seç
3. `uEnv.txt` dosyasını seçip gönder

Transfer bitince U-Boot alınan dosyanın boyutunu yazar:

![loady ile YMODEM transferi](../images/uenv/03_loady.png)

> [!NOTE]
> `## Total Size = 0x0000010D = 269 Bytes` satırı önemli: Bu değer otomatik olarak <b>`filesize`</b> değişkenine yazılır. Bir sonraki adımda boyutu elle yazmak yerine `${filesize}` kullanabiliriz.

### <a name="c6-adım-4--env-import-ile-ortama-aktar-ve-kontrol-et"></a>Adım 4 — `env import` ile ortama aktar ve kontrol et

```text
U-Boot# env import -t 0x82000000 ${filesize}
U-Boot# printenv bootargs
U-Boot# printenv bootcmd
```

![env import ve printenv](../images/uenv/04_env_import.png)

`printenv` çıktısı `uEnv.txt`'deki değerlerle aynıysa aktarım başarılıdır. `run mypcip` ile makronun da çalıştığını görebilirsin.

> [!WARNING]
> `${filesize}` yerine boyutu elle yazarsan <b>hex</b> olarak yaz (`0x10d` veya `10d`). U-Boot sayıları varsayılan olarak hex kabul eder; `269` yazarsan `0x269` = 617 bayt okur ve dosyanın sonundaki çöp veriyi de içe aktarmaya çalışır.

### <a name="c6-adım-5--boot-et"></a>Adım 5 — Boot et

```text
U-Boot# boot
```

`boot` komutu `bootcmd`'yi çalıştırır. Ekrana bizim `echo` mesajımız gelmeli:

![bootcmd ile açılış](../images/uenv/05_boot.png)

### <a name="c6-dikkat-edilecekler"></a>Dikkat edilecekler

| Konu | Açıklama |
|---|---|
| <b>Adres çakışması</b> | `uEnv.txt` `0x82000000`'a yüklendi; `bootcmd` de kernel'i aynı adrese yüklüyor. Sorun değil, çünkü `env import` dosyayı önce okuyup bitiriyor, kernel <b>sonra</b> üzerine yazılıyor. Sıra ters olursa kernel bozulur. |
| <b>Geçicilik</b> | `env import` sadece RAM'deki aktif ortamı değiştirir. Kart yeniden açılınca değişiklikler kaybolur. |
| <b>Kalıcı yapmak</b> | Her şeyin doğru olduğundan emin olduktan sonra `saveenv` ile kaydedilebilir. Bu komut kalıcı U-Boot ortamının üzerine yazar; geri dönmek için `env default -a` + `saveenv` gerekir. |
| <b>Otomatik okumada `bootcmd`</b> | BBB'nin varsayılan U-Boot'u SD karttaki `uEnv.txt`'yi kendi `bootcmd`'si <b>çalışırken</b> okur ve `uenvcmd` değişkenini arar. Bu yüzden SD karttaki `uEnv.txt`'de `bootcmd` tanımlamak o açılışı etkilemez; orada `uenvcmd` kullanılır ([4.8](#c4-bu-açılışta-uenvtxt-ne-yaptı)'deki örnek gibi). Seri porttan yüklemede ise `boot` komutunu biz verdiğimiz için `bootcmd` çalışır. |

---

## <a name="c6-64-challenge-boot-i̇majlarını-mmc0dan-sd-kart-yüklemek"></a>6.4 Challenge: Boot İmajlarını MMC0'dan (SD Kart) Yüklemek

### <a name="c6-görev"></a>Görev

Kursun bu bölümdeki challenge'ı:

> <i>Derste boot imajları (uImage ve DTB) <b>MMC1</b>'den (eMMC) yüklendi, dosya sistemi olarak <b>MMC0</b>'daki (microSD) rootfs kullanıldı. `uEnv.txt`'yi, boot imajları da <b>MMC0</b>'dan (microSD) yüklenecek şekilde değiştir.</i>

| | Önce | Sonra |
|---|---|---|
| Kernel + DTB | eMMC (`mmc 1`) | <b>SD kart (`mmc 0`)</b> |
| Rootfs | SD kart, 2. bölüm (`/dev/mmcblk0p2`) | Değişmez |

### <a name="c6-çözüm"></a>Çözüm

Değişen tek şey `load` komutlarındaki <b>aygıt numarası</b> (ve dosyanın o aygıttaki yeri). `bootargs` değişmez, çünkü rootfs zaten SD kartta.

<b>1) Dosyaları SD karta koy.</b> `uImage` ve `am335x-boneblack.dtb`'yi SD kartın BOOT bölümüne kopyala:

```bash
cp uImage am335x-boneblack.dtb /media/$USER/BOOT/
sync && sudo umount /media/$USER/BOOT /media/$USER/ROOTFS
```

<b>2) `load` satırlarını `mmc 0:1`'e çevir.</b>

```text
eski:  load mmc 1:2 0x82000000 /boot/uImage                    (eMMC, 2. bölüm)
yeni:  load mmc 0:1 0x82000000 uImage                          (SD kart, 1. bölüm: BOOT)

eski:  load mmc 1:2 0x88000000 /boot/am335x-boneblack.dtb
yeni:  load mmc 0:1 0x88000000 am335x-boneblack.dtb
```

[6.2](#c6-62-uenvtxt-satır-satır)'deki dosyanın `bootcmd` satırı tam olarak bunu yapıyor:

```text
bootcmd=echo "**********Booting from memory**********";load mmc 0:1 0x82000000 uImage;load mmc 0:1 0x88000000 am335x-boneblack.dtb;bootm 0x82000000 - 0x88000000
```

<b>3) Doğrula.</b> U-Boot'u durdurup dosyaların orada olduğunu gör, sonra boot et:

```text
=> ls mmc 0:1
=> boot
```

Ekranda `**********Booting from memory**********` yazısından sonra `reading uImage` görüyorsan imajlar SD karttan geliyor.

> [!TIP]
> SD kart dosyayı U-Boot'a FAT bölümünden de ext bölümünden de verebilir. `uImage`'ı BOOT (FAT) bölümüne koymak, dosyayı Windows'tan bile kopyalayabilmeni sağlar. ROOTFS bölümündeki `/boot` klasöründe tutmak istersen `load mmc 0:2 ... /boot/uImage` yaz.

---

## <a name="c6-65-ek-alıştırma-kernel-ve-dtb-sd-karttan-rootfs-emmcden"></a>6.5 Ek Alıştırma: Kernel ve DTB SD Karttan, Rootfs eMMC'den

### <a name="c6-görev-1"></a>Görev

Challenge'ın tersi: kernel ve DTB SD karttan gelsin, ama rootfs eMMC'deki Debian olsun.

| Ne? | Nereden? |
|---|---|
| Kernel (`uImage`) | <b>MMC0</b> — microSD kart, 1. bölüm |
| Device tree (`.dtb`) | <b>MMC0</b> — microSD kart, 1. bölüm |
| Root filesystem | <b>MMC1</b> — dahili eMMC, 2. bölüm |

```
microSD (mmc 0)                      eMMC (mmc 1)
├── p1 BOOT  → uImage, .dtb  ──┐     ├── p1 BOOT
└── p2 ROOTFS                  │     └── p2 ROOTFS  ◄── root=/dev/mmcblk1p2
                               ▼
                        U-Boot RAM'e yükler → kernel başlar → rootfs'i eMMC'den bağlar
```

### <a name="c6-adım-1--aygıt-numaralarını-doğrula"></a>Adım 1 — Aygıt numaralarını doğrula

Önce varsayımımızı kontrol edelim: `mmc 0` gerçekten SD kart, `mmc 1` gerçekten eMMC mi ve eMMC'de 2. bölüm var mı?

```text
U-Boot# mmc list
U-Boot# mmc dev 1
U-Boot# mmc part
```

![mmc list ve mmc part](../images/uenv/06_mmc_list.png)

eMMC'de `83` (Linux) tipinde 2. bölüm görünüyorsa rootfs için doğru yerdeyiz.

### <a name="c6-adım-2--sadece-bootargsı-değiştir"></a>Adım 2 — Sadece `bootargs`'ı değiştir

Kernel ve DTB hâlâ SD karttan yükleneceği için <b>`bootcmd` aynı kalır</b>. Değişen tek şey, kernel'e "rootfs nerede?" bilgisini veren `bootargs`:

| | Değer |
|---|---|
| <b>Eski</b> — rootfs SD kartta | `bootargs=console=ttyO0,115200 root=/dev/mmcblk0p2 rw` |
| <b>Yeni</b> — rootfs eMMC'de | `bootargs=console=ttyO0,115200 root=/dev/mmcblk1p2 rw` |

Bunu iki yolla yapabilirsin:

- <b>a)</b> `uEnv.txt`'deki satırı değiştirip [6.3](#c6-63-uygulama-uenvtxtyi-seri-porttan-göndermek)'teki gibi tekrar gönder.
- <b>b)</b> Doğrudan U-Boot'ta `setenv` ile değiştir:

```text
U-Boot# setenv bootargs console=ttyO0,115200 root=/dev/mmcblk1p2 rw
U-Boot# boot
```

![bootargs'ı eMMC'ye çevirme](../images/uenv/07_bootargs_emmc.png)

### <a name="c6-adım-3--linuxta-sonucu-doğrula"></a>Adım 3 — Linux'ta sonucu doğrula

Kart açılınca rootfs'in gerçekten eMMC'den bağlandığını kontrol et:

```bash
cat /proc/cmdline   # kernel'e giden bootargs
lsblk               # hangi bölüm / olarak bağlı?
findmnt /           # rootfs'in kaynağı
```

![Linux'ta rootfs doğrulama](../images/uenv/08_linux_dogrula.png)

`/` bağlama noktası `mmcblk1p2`'nin yanında görünüyorsa challenge tamam.

### <a name="c6-sonuç"></a>Sonuç

| Bileşen | Durum |
|---|---|
| <b>Kernel ve DTB</b> | microSD'nin 1. bölümünden RAM'e yüklenir. |
| <b>Rootfs</b> | Kernel açıldıktan sonra eMMC'nin 2. bölümünden bağlanır. |
| <b>`bootcmd`</b> | Değişmez; yükleme kaynağı hâlâ SD kart. |
| <b>`bootargs`</b> | `root=/dev/mmcblk1p2` olarak güncellenir. |

> [!IMPORTANT]
> Bunun çalışması için:
> - eMMC'nin 2. bölümünde gerçekten bir Linux rootfs olmalı.
> - Kernel'de MMC sürücüsü ve rootfs'in dosya sistemi (ör. ext4) desteği <b>built-in</b> olmalı (veya bir initramfs'ten yüklenmeli).
> - Linux'taki numaralandırma U-Boot'unkiyle aynı olmalı. Değilse kernel `VFS: Unable to mount root fs` hatasıyla durur; bu durumda `root=/dev/mmcblk0p2` dene veya `root=PARTUUID=...` kullan.

---

## <a name="c6-66-rootfs-bölümünde-neler-var"></a>6.6 ROOTFS Bölümünde Neler Var?

<b>Root filesystem (rootfs)</b>, Linux'un `/` (kök) dizinidir. Kernel açıldıktan sonra `root=` ile gösterilen bölümü `/` olarak bağlar ve bundan sonra çalışan <b>her program, her ayar dosyası ve her kütüphane</b> buradan okunur. Kernel tek başına bir işe yaramaz; kullanıcıya kabuk (shell), komutlar ve servisler rootfs ile gelir.

Rootfs'teki klasör düzeni rastgele değildir; <b>FHS (Filesystem Hierarchy Standard)</b> denen ortak bir standarda uyar. Bu yüzden Ubuntu'da, BeagleBone'daki Ångström'de veya eMMC'deki Debian'da aynı klasörleri görürüz.

### <a name="c6-661-klasörler-ve-görevleri"></a>6.6.1 Klasörler ve görevleri

| Klasör | İçinde ne var? | BBB'de örnek | Bakmak için |
|---|---|---|---|
| <b>`/bin`</b> | Temel kullanıcı komutları (`ls`, `cp`, `cat`, `sh`...) | `bash`, `busybox` | `ls /bin` |
| <b>`/sbin`</b> | Sistem yönetimi komutları (genelde root için) | `init`, `mount`, `ifconfig`, `reboot` | `ls /sbin` |
| <b>`/boot`</b> | Kernel ve device tree dosyaları | `uImage`, `am335x-boneblack.dtb` | `ls -l /boot` |
| <b>`/etc`</b> | Sistem <b>ayar</b> dosyaları (metin) | `hostname`, `fstab`, `passwd`, `os-release` | `cat /etc/hostname` |
| <b>`/lib`</b> | Paylaşılan kütüphaneler (`.so`) ve kernel modülleri | `libc.so.6`, `modules/3.8.13/` | `ls /lib/modules` |
| <b>`/usr`</b> | Ek programlar, kütüphaneler, belgeler (rootfs'in en büyük kısmı) | `/usr/bin`, `/usr/lib` | `du -sh /usr` |
| <b>`/home`</b> | Kullanıcıların kişisel klasörleri | `/home/root` (Ångström'de root'un ev dizini) | `ls /home` |
| <b>`/root`</b> | root kullanıcısının ev dizini (Debian/Ubuntu'da) | eMMC'deki Debian'da kullanılır | `ls /root` |
| <b>`/var`</b> | Zamanla değişen veriler: loglar, kuyruklar, önbellek | `/var/log` | `ls /var/log` |
| <b>`/tmp`</b> | Geçici dosyalar (açılışta temizlenir, genelde RAM'de) | | `ls /tmp` |
| <b>`/media`, `/mnt`</b> | Harici diskleri (USB, SD) bağlama noktaları | `mount /dev/mmcblk1p1 /mnt` | `ls /mnt` |
| <b>`/dev`</b> <i>(sanal)</i> | Donanım aygıt dosyaları | `mmcblk0p2`, `ttyO0` | `ls /dev` |
| <b>`/proc`</b> <i>(sanal)</i> | Kernel ve süreç bilgileri | `cpuinfo`, `meminfo`, `cmdline` | `cat /proc/cpuinfo` |
| <b>`/sys`</b> <i>(sanal)</i> | Aygıt ve sürücü ayarları (sysfs) | `/sys/class/leds/...` | `ls /sys/class` |
| <b>`/run`</b> <i>(sanal)</i> | Çalışma anı bilgileri (PID dosyaları, soketler) | | `ls /run` |

> [!IMPORTANT]
> <i>(sanal)</i> işaretli klasörler <b>sanal (virtual)</b> dosya sistemleridir. Diskte gerçek dosya içermezler; kernel çalışırken içlerini <b>RAM'de</b> doldurur (`devtmpfs`, `proc`, `sysfs`, `tmpfs`). Bu yüzden SD kartı bilgisayara takıp baktığında bu klasörler <b>boş</b> görünür. Bu bir hata değildir.

### <a name="c6-662-rootfse-üç-yerden-ulaşabiliriz"></a>6.6.2 ROOTFS'e üç yerden ulaşabiliriz

```
                  ┌─────────────────────────────────────────────────┐
 a) Bilgisayar ──►│ SD kart takılı → /media/$USER/ROOTFS/...        │  (cd, ls, cat, file)
 b) U-Boot     ──►│ ls mmc 0:2 /...   (sadece okur, Linux yok)      │  (ls, load)
 c) BBB Linux  ──►│ Kart açık → /  (kök dizin)                      │  (cd, ls, cat, df, mount)
                  └─────────────────────────────────────────────────┘
```

| Nereden? | Ne zaman? | Rootfs'in yolu |
|---|---|---|
| <b>a) Bilgisayar</b> | SD kart okuyucuya takılıyken, kartı açmadan dosya kopyalamak / düzeltmek için | `/media/$USER/ROOTFS` |
| <b>b) U-Boot</b> | Linux açılmadan önce, dosya gerçekten orada mı diye bakmak için | `mmc 0:2` (SD) veya `mmc 1:2` (eMMC) |
| <b>c) BBB Linux</b> | Kart açıldıktan sonra, seri konsol (Minicom) veya SSH üzerinden | `/` |

### <a name="c6-663-a-bilgisayardan-ulaşmak"></a>6.6.3 a) Bilgisayardan ulaşmak

SD kartı bilgisayara tak. Ubuntu bölümleri <b>etiket (label)</b> adlarıyla otomatik bağlar. Önce kartın nereye bağlandığını bul, sonra klasöre gir:

```bash
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINT   # SD kart hangi aygıt, nereye bağlı?
cd /media/$USER/ROOTFS                         # rootfs'in içine gir
ls                                             # kök klasörleri listele
ls boot/                                       # kernel ve dtb burada
du -sh .                                       # rootfs'in toplam boyutu
```

![Bilgisayardan ROOTFS bölümüne girme](../images/rootfs/01_host_rootfs.png)

Burada iki şeyi gözlemle: sanal klasörler boş, programlar ise bilgisayarın değil <b>ARM</b> işlemcinin komut setiyle derlenmiş:

```bash
ls proc/ sys/ dev/      # boş görünür
file bin/bash           # "ARM" yazısını gör
cat etc/hostname        # BBB'nin hostname'i (başta / YOK)
```

![Sanal klasörler ve ARM programları](../images/rootfs/02_host_sanal_ve_arm.png)

> [!WARNING]
> Bilgisayardayken yolun başına <b>`/` koyma</b>. `cat /etc/hostname` bilgisayarın <b>kendi</b> dosyasını okur; BBB'ninki `etc/hostname` (ROOTFS klasöründeyken) veya `/media/$USER/ROOTFS/etc/hostname` yolundadır. Bu karışıklıkla bilgisayarın `/etc/fstab` gibi dosyalarını yanlışlıkla bozmak mümkündür. Rootfs'e yazmak için `sudo` gerekir ve işin bitince kartı çıkarmadan önce `sync` + `umount` yap.
>
> `file bin/bash` çıktısında `ARM` yazdığı için bu programları bilgisayarda <b>çalıştıramazsın</b> (`./bin/bash` → `Exec format error`). Sadece okuyabilir/kopyalayabilirsin. Bunun sebebini [Bölüm 9](#c9-bölüm-9--cross-toolchain-spl-ve-u-boot-derleme)'da (cross compile) göreceğiz.

### <a name="c6-664-b-u-boottan-ulaşmak"></a>6.6.4 b) U-Boot'tan ulaşmak

U-Boot dosya sistemini <b>okuyabilir</b> (ext2/3/4 ve FAT). Linux açılmadan önce kernel'in gerçekten orada olup olmadığını görmek için kullanışlıdır:

```text
U-Boot# ls mmc 0:2 /          # SD kartın 2. bölümü (ROOTFS) kökü
U-Boot# ls mmc 0:2 /boot      # kernel ve dtb
U-Boot# ls mmc 1:2 /          # eMMC'nin 2. bölümü (Debian rootfs)
```

![U-Boot'ta ls ile ROOTFS'i listeleme](../images/rootfs/03_uboot_ls.png)

| Komut | Anlamı |
|---|---|
| `ls mmc <aygıt>:<bölüm> <yol>` | Bölümdeki klasörü listeler |
| `load mmc 0:2 0x82000000 /boot/uImage` | Dosyayı RAM'e yükler ([4.10.2](#c4-4102-uimageı-ddre-yükle)) |
| `ext4ls` / `ext2ls` / `fatls` | Eski U-Boot sürümlerinde dosya sistemine özel `ls` komutları |

> [!NOTE]
> U-Boot'ta `cd` yoktur ve dosya içeriğini `cat` ile göremezsin; her komutta tam yolu yazarsın. U-Boot rootfs'e normalde <b>yazmaz</b>, sadece okur.

### <a name="c6-665-c-bbb-linuxtan-ulaşmak"></a>6.6.5 c) BBB Linux'tan ulaşmak

Kart açılıp `root` olarak giriş yaptıktan sonra rootfs artık `/` dizinidir. Dolaşmak için temel komutlar:

| Komut | Görevi |
|---|---|
| `pwd` | Şu an hangi klasördeyim? |
| `cd /` · `cd /etc` · `cd ..` · `cd ~` | Kök dizine / bir klasöre / bir üste / ev dizinine git |
| `ls` · `ls -l` · `ls -a` | Listele / ayrıntılı (izin, boyut, tarih) / gizli dosyalarla |
| `cat <dosya>` · `head -n 5` · `less` | Metin dosyasını göster / ilk satırları / sayfa sayfa |
| `which <komut>` | Bir komutun hangi dosya olduğunu bul |
| `find / -name "*.dtb" 2>/dev/null` | Rootfs'te dosya ara |
| `df -h /` · `du -sh <klasör>` | Rootfs'in doluluk oranı / klasör boyutu |
| `mount` | Hangi bölüm nereye bağlı? |

#### <a name="c6-kök-dizin-ve-bin"></a>Kök dizin ve `/bin`

```bash
pwd                 # /home/root  (Ångström'de root'un ev dizini)
cd /
ls
ls /bin | head -5
which ls
ls -l /bin/ls       # Ångström'de birçok komut busybox'a link
```

![BBB'de kök dizinde dolaşma](../images/rootfs/04_bbb_ls.png)

> [!TIP]
> <b>BusyBox</b>, `ls`, `cp`, `mount` gibi yüzlerce komutu <b>tek bir küçük programda</b> toplayan araçtır. Gömülü sistemlerde yer kazanmak için yaygın kullanılır; `/bin/ls` gibi dosyalar aslında `busybox`'a giden <b>sembolik linklerdir</b>.

#### <a name="c6-etc--ayar-dosyaları"></a>`/etc` — ayar dosyaları

```bash
cat /etc/hostname      # kartın adı
cat /etc/os-release    # hangi dağıtım, hangi sürüm
cat /etc/fstab         # açılışta hangi bölüm nereye bağlanacak
head -2 /etc/passwd    # kullanıcı listesi
```

![BBB'de /etc dosyaları](../images/rootfs/05_bbb_etc.png)

#### <a name="c6-proc-ve-sys--kernel-ile-konuşmak"></a>`/proc` ve `/sys` — kernel ile konuşmak

```bash
cat /proc/version                                   # kernel sürümü
cat /proc/cmdline                                   # U-Boot'un verdiği bootargs
grep -m2 -E 'model name|BogoMIPS' /proc/cpuinfo     # işlemci bilgisi
head -2 /proc/meminfo                               # RAM bilgisi
ls /sys/class/leds/                                 # kartın USR LED'leri
echo none > /sys/class/leds/beaglebone:green:usr0/trigger
echo 1    > /sys/class/leds/beaglebone:green:usr0/brightness   # LED'i yak (0 = söndür)
```

![BBB'de /proc ve /sys](../images/rootfs/06_bbb_proc_sys.png)

`/sys` altındaki dosyalara yazmak, sürücüye doğrudan komut vermek demektir. `trigger` dosyasını `none` yapmadan `brightness`'a yazarsan LED'in varsayılan görevi (ör. `heartbeat`) senin değerini hemen ezer.

#### <a name="c6-dev-boot-ve-disk-kullanımı"></a>`/dev`, `/boot` ve disk kullanımı

```bash
ls /dev/mmcblk* /dev/ttyO*   # MMC bölümleri ve seri portlar
ls -l /boot                  # kernel ve dtb
df -h /                      # rootfs ne kadar dolu, hangi bölümden geliyor
du -sh /usr /lib /etc        # en çok yer kaplayan klasörler
mount | grep -E ' / | /proc | /sys | /dev '   # gerçek ve sanal bağlamalar
```

![BBB'de /dev, /boot ve disk kullanımı](../images/rootfs/07_bbb_dev_boot.png)

`mount` çıktısında `/` gerçek bir diskten (`/dev/mmcblk0p2`, `ext3`) gelirken `/dev`, `/proc` ve `/sys`'in tipi `devtmpfs`, `proc`, `sysfs` olarak görünür. Bu, [6.6.1](#c6-661-klasörler-ve-görevleri)'deki sanal klasörlerin kanıtıdır. Rootfs'i eMMC'den açtıysan ([6.5](#c6-65-ek-alıştırma-kernel-ve-dtb-sd-karttan-rootfs-emmcden)) `df -h /` satırında `/dev/mmcblk1p2` görürsün.

---

## <a name="c6-67-özet"></a>6.7 Özet

| Komut / Değişken | Görevi |
|---|---|
| `uEnv.txt` | U-Boot ortam değişkenlerini metin olarak tanımlar |
| `loady <adres>` | YMODEM ile seri porttan RAM'e dosya alır, boyutu `filesize`'a yazar |
| `env import -t <adres> ${filesize}` | RAM'deki metin değişkenlerini aktif ortama aktarır |
| `printenv <isim>` | Değişkenin değerini gösterir |
| `setenv <isim> <değer>` | Değişkeni değiştirir (geçici) |
| `run <makro>` | Değişkendeki komutları çalıştırır (ör. `run mypcip`) |
| `boot` | `bootcmd`'yi çalıştırır |
| `bootcmd` | Otomatik açılışta çalışan komut dizisi |
| `bootargs` | Linux kernel'ine verilen açılış parametreleri |
| `root=/dev/mmcblk1p2` | Rootfs'in eMMC'nin 2. bölümünde olduğunu söyler |
| `mmc list` / `mmc part` | U-Boot'un gördüğü MMC aygıtlarını ve bölümleri listeler |
| `saveenv` | Aktif ortamı kalıcı olarak kaydeder (dikkatli kullan) |
| `/media/$USER/ROOTFS` | SD kart bilgisayara takılıyken rootfs'in yolu |
| `ls mmc 0:2 /boot` | U-Boot'tan rootfs'teki klasörü listeler |
| `/bin`, `/sbin`, `/usr` | Programlar |
| `/etc` | Ayar dosyaları (`hostname`, `fstab`, `passwd`) |
| `/boot` | Kernel (`uImage`) ve device tree (`.dtb`) |
| `/lib` | Kütüphaneler ve kernel modülleri |
| `/dev`, `/proc`, `/sys` | Sanal klasörler; kernel çalışırken dolar |
| `cat /proc/cmdline` | Kernel'e giden bootargs |
| `df -h /` · `mount` | Rootfs hangi bölümden geliyor? |

## <a name="c6-68-karşılaşılabilecek-problemler"></a>6.8 Karşılaşılabilecek Problemler

| Belirti | Sebep | Çözüm |
|---|---|---|
| `loady` sonrası transfer başlamıyor | Minicom'da xmodem seçildi ya da `lrzsz` yok | Protokol <b>ymodem</b> olmalı; `sudo apt install lrzsz` |
| `env import` sonrası değişkenler bozuk / fazladan satırlar | Boyut ondalık yazıldı | `${filesize}` kullan ya da boyutu hex yaz |
| `## Error: "mypcip" not defined` | `env import` yapılmadı ya da kart yeniden açıldı | Adım 3–4'ü tekrarla; değişiklikler kalıcı değildir |
| `VFS: Unable to mount root fs` (challenge) | Linux'ta eMMC'nin numarası farklı | `root=/dev/mmcblk0p2` dene; Linux'ta `lsblk` ile kontrol et |
| Açılışta `uEnv.txt`'deki `bootcmd` çalışmıyor | Otomatik okumada `bootcmd` değil `uenvcmd` çalıştırılır | SD karttaki dosyada komutları `uenvcmd`'ye yaz |


<div class="page-break"></div>

# <a name="c7-bölüm-7--seri-porttan-uart-boot"></a>Bölüm 7 — Seri Porttan (UART) Boot

> <b>Bu bölümde:</b>
> - BeagleBone Black'i <b>SD kart ve eMMC kullanmadan</b>, bütün boot dosyalarını bilgisayardan <b>seri port (UART0)</b> üzerinden göndererek açacaksın.
> - Xmodem ve Ymodem protokollerinin farkını ve ROM Code'un UART boot davranışını öğreneceksin.
> - Kernel, DTB ve initramfs'i RAM'de nereye yükleyeceğini ve `bootm` ile nasıl başlatacağını göreceksin.
>
> <b>Ön koşul:</b> [Bölüm 2](#c2-bölüm-2--seri-konsol-ve-minicom) — Minicom, [Bölüm 3](#c3-bölüm-3--linux-boot-süreci-rbl--spl--u-boot) — boot sırası, [Bölüm 6](#c6-bölüm-6--u-boot-komut-satırı-ve-uenvtxt) — `loady` ile dosya gönderme.

---

## <a name="c7-71-dosya-transfer-protokolleri"></a>7.1 Dosya Transfer Protokolleri

![IP ağı ve UART üzerinden dosya transfer protokolleri](../images/{CD17FB50-958F-4863-B8A4-DED33A61A342}.png)

Bilgisayardan karta dosya göndermenin iki yolu var:

| Bağlantı | Protokoller | Ne zaman kullanılır? |
|---|---|---|
| <b>IP ağı (Ethernet)</b> | TFTP, HTTP, FTP, SMTP... | Kartta çalışan bir ağ yığını (U-Boot veya Linux) varsa. Hızlıdır ([Bölüm 8](#c8-bölüm-8--tftp-ile-ağdan-boot)). |
| <b>UART (seri port)</b> | Xmodem, Ymodem, Zmodem, Kermit... | Ağ yokken veya kartta henüz hiçbir yazılım yokken. Yavaştır ama çok basittir. |

UART sadece ham baytları taşır; "dosya nerede başlıyor, nerede bitiyor, veri bozuldu mu?" gibi bilgileri taşımaz. <b>Xmodem / Ymodem</b> gibi protokoller veriyi paketlere bölüp her pakete kontrol bilgisi (checksum / CRC) ekler, bozuk paketi tekrar istetir.

| Protokol | Özellik |
|---|---|
| <b>Xmodem</b> | 128 bayt (Xmodem-1K'da 1024 bayt) paketler. Dosya adı ve boyutu göndermez. AM335x'in <b>ROM kodu</b> bunu kullanır. |
| <b>Ymodem</b> | Xmodem'in geliştirilmiş hali: dosya adını ve boyutunu da gönderir. U-Boot'ta `loady` komutu. |

---

## <a name="c7-72-seri-boot-fikri"></a>7.2 Seri Boot Fikri

![Boot dosyaları bilgisayarda, UART0 ile karta seri bağlantı](../images/{E3C79A57-76F0-41F6-B314-EE88AB46B638}.png)

Bütün boot dosyaları — <b>SPL, U-Boot, Linux kernel (uImage), DTB ve dosya sistemi</b> — kartta değil, <b>bilgisayarda (HOST)</b> durur. Kart ile bilgisayar arasındaki tek bağlantı, J1 header'daki <b>UART0</b> pinlerine bağlı USB-TTL seri kablodur. Kart açılırken her dosyayı bu kablo üzerinden sırayla göndeririz.

Bu yöntem şu durumlarda işe yarar:
- SD kart ve eMMC boşsa veya içindeki bootloader bozulduysa (kartı "kurtarmak" için).
- Yeni derlenmiş bir SPL / U-Boot'u karta yazmadan denemek için.

---

## <a name="c7-73-kartı-uart-boot-moduna-sokmak"></a>7.3 Kartı UART Boot Moduna Sokmak

![Seri boot nasıl çalışır: S2 basılı tutulur, S3 ile açılır, SD kart takılı olmaz](../images/{A0655836-7172-4895-8690-5553D0FF2841}.png)

Kartı UART'tan boot ettirmek için SD karttan boot ederken yaptığımızın aynısını yaparız:

1. <b>S2 (BOOT)</b> butonuna basılı tut,
2. <b>S3 (POWER)</b> butonuna basıp bırak (veya beslemeyi tak),
3. Boot başladıktan sonra S2'yi bırak.

Tek fark: <b>SD kart takılı olmamalı.</b> Takılıysa ROM kodu boot dosyalarını SD karttan bulur ve UART'a hiç sıra gelmez.

### <a name="c7-am335x-boot-sırası"></a>AM335x boot sırası

![AM335x boot sırası: S2 basılı değilken ve basılıyken](../images/{A096CE0C-645B-42AB-8840-75924AC5A492}.png)

AM335x'in içindeki ROM kodu, açılışta `SYSBOOT[4:0]` pinlerine bakarak hangi çevre birimlerini hangi sırayla deneyeceğine karar verir ([3.5](#c3-35-boot-kaynakları-ve-boot-sırası-sysboot-pinleri)). BBB'de S2 butonu bu pinlerden birinin değerini değiştirir:

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

### <a name="c7-usb0-sorunu-45-dakikalık-bekleme"></a>USB0 sorunu: 4.5 dakikalık bekleme

Eğer USB kablosu bu sırada karta takılıysa ve image dosyası USB üzerinden gönderilmiyorsa, ROM kodu bir sonraki boot aygıtı olan UART0'a geçmeden önce <b>4.5 dakikaya kadar</b> bekliyor. Bu süre dolduktan sonra UART0'a geçiyor.

![AM335x TRM: UART boot ayrıntıları ve USB boot için Silicon Errata notu](../images/{F394BE8C-59F6-4D82-A192-63B1BE6F6FBA}.png)

AM335x Technical Reference Manual'ın (TRM) <b>26.1.8.6 USB Boot Procedure</b> bölümünde, USB boot'un kısıtlamaları için <b>Silicon Errata (SPRZ360)</b> belgesine bakılması söyleniyor:

![Silicon Errata Advisory 1.0.25: Ethernet boot başarısız olursa sistem 4.5 dakika bekler](../images/{17AE38E2-B3D5-4F02-ADA3-822CF3DD8D76}.png)

Errata'daki <b>Advisory 1.0.25</b>'te Ethernet denilmiş, ancak bu durum USB için de geçerli. Çünkü AM335x'in ROM kodu USB boot'u, USB kablosu üzerinden <b>sanal bir Ethernet bağlantısı (RNDIS)</b> kurarak yapar. Yani USB boot aslında "USB üzerinden Ethernet boot"tur ve aynı 4.5 dakikalık beklemeye takılır.

### <a name="c7-çözüm-kartı-harici-adaptörle-beslemek"></a>Çözüm: Kartı harici adaptörle beslemek

![SD kart ve P4 mini USB kablosu takılı olmamalı, kart güç adaptörüyle beslenmeli](../images/{8D57F348-9C21-4AF9-9546-9BBA20F8C501}.png)

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

## <a name="c7-74-rom-kodunun-uart-boot-davranışı"></a>7.4 ROM Kodunun UART Boot Davranışı

![AM335x TRM 26.1.9.5: UART boot prosedürü](../images/{18BDEDD5-58AF-4A87-AF53-C576A14BD9E6}.png)

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

## <a name="c7-75-önerilen-ram-yükleme-adresleri"></a>7.5 Önerilen RAM Yükleme Adresleri

![Önerilen DDR RAM yükleme adresleri](../images/{41B45262-4937-487E-BD2D-CC0D2D385CBF}.png)

U-Boot'a geldikten sonra kernel, DTB ve dosya sistemini RAM'e (DDR, `0x80000000`'dan başlar) yükleyeceğiz. Dosyaların birbirinin üzerine yazmaması için bu adresler kullanılır:

| Dosya | Adres |
|---|---|
| Kernel (`uImage`) | `0x82000000` |
| Device tree (`.dtb`) | `0x88000000` |
| initramfs | `0x88080000` |

Seri boot'ta SD kart ve eMMC kullanılmadığı için rootfs'i bağlayacak bir disk yoktur. Bu yüzden dosya sistemi de RAM'e yüklenir: <b>RAMDISK / INITRAMFS</b>, RAM'de duran küçük bir rootfs'tir. DTB'ye ayrılan alan `0x88000000` – `0x8807FFFF` arası (512 KB) olduğu için initramfs hemen arkasından, `0x88080000`'dan başlar.

---

## <a name="c7-76-özet-seri-boot-adımları"></a>7.6 Özet: Seri Boot Adımları

![Özet: UART boot modu, SPL, U-Boot ve diğer image'lar](../images/{0208A16B-4B49-45CB-9126-49CCBFA1CF0F}.png)

```
Bilgisayar (HOST)                          BeagleBone Black
──────────────────                         ────────────────────────────────────────
                                           ROM kodu (S2 basılı, SD kart yok) → UART0
u-boot-spl.bin ──── Xmodem ──────────────► SPL çalışır (DDR'ı hazırlar)
u-boot.img     ──── Ymodem ──────────────► U-Boot çalışır → => komut satırı komut satırı
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

---

## <a name="c7-77-elimizdeki-boot-dosyaları-nedir"></a>7.7 Elimizdeki Boot Dosyaları Nedir?

Seri boot için bilgisayarda (HOST) şu 5 dosya hazır olmalı. Her biri boot zincirinin bir halkasıdır; her dosyanın işi bir sonrakini yükleyip çalıştırmaktır:

| Dosya | Nedir? | Kim yükler? | Nereye yüklenir? | Protokol |
|---|---|---|---|---|
| <b>`u-boot-spl.bin`</b> | <b>SPL</b> (Secondary Program Loader). U-Boot'un küçük ilk aşaması. Saatleri, pin ayarlarını, UART'ı ve en önemlisi <b>DDR RAM</b>'i hazırlar. | ROM kodu | AM335x'in iç SRAM'i (`0x402F0400`, en fazla ~109 KB) | Xmodem |
| <b>`u-boot.img`</b> | Asıl <b>U-Boot</b>. Başında 64 baytlık U-Boot (mkimage) başlığı vardır. Komut satırını (`=>`) bize o verir. | SPL | DDR (`0x80800000`) | Ymodem |
| <b>`uImage`</b> | <b>Linux kernel</b>. `zImage`'in başına U-Boot başlığı (yükleme adresi, giriş noktası, CRC) eklenmiş hali ([4.9](#c4-49-uimage-nedir)). | U-Boot (`loadx`) | `0x82000000` | Xmodem |
| <b>`am335x-boneblack.dtb`</b> | <b>Device Tree Blob</b>. Kernel'e kartta hangi donanımın olduğunu anlatan derlenmiş dosya ([Bölüm 11](#c11-bölüm-11--linux-device-tree)). | U-Boot (`loadx`) | `0x88000000` | Xmodem |
| <b>`initramfs`</b> | RAM'de çalışan küçük <b>kök dosya sistemi</b> (genellikle BusyBox). `cpio` arşivi + gzip + U-Boot başlığı. SD/eMMC olmadığı için rootfs'i buradan alırız. | U-Boot (`loadx`) | `0x88080000` | Xmodem |

### <a name="c7-bu-dosyaları-nereden-bulurum"></a>Bu dosyaları nereden bulurum?

Bu dosyaları <b>kendin yazmazsın</b>. Hepsi açık kaynak projelerden (U-Boot, Linux kernel, BusyBox) çıkar; senin işin kaynak kodu indirip ayarlamak ve derlemektir. Üç yol vardır:

| Yol | Ne zaman? | Artısı / eksisi |
|---|---|---|
| <b>1. Hazır (prebuilt) dosyalar</b> | İlk deneme, "kart çalışıyor mu?" testi | En hızlısı; ama içinde ne olduğunu sen seçmezsin. |
| <b>2. Kaynak koddan elle derleme</b> | Öğrenirken (kursta yapılan) | Her adımı görürsün; daha uzun sürer. |
| <b>3. Buildroot / Yocto</b> | Gerçek projeler | Hepsini tek komutla üretir; ilk derleme uzun sürer. |

#### <a name="c7-yol-1--hazır-dosyalar"></a>Yol 1 — Hazır dosyalar

- <b>Kursun kaynakları:</b> Kurslar bu dosyaları genelde derlenmiş olarak verir (Udemy ekleri / kursun GitHub reposu). Kursla birebir uyumlu oldukları için ilk seri boot denemesinde en kolayı bunlar.
- <b>TI Processor SDK (AM335x):</b> TI'ın sitesinden indirilir. `board-support/prebuilt-images/` klasöründe genellikle `MLO`, `u-boot-spl.bin`, `u-boot.img`, `zImage`, `.dtb` dosyaları ve bir rootfs hazır gelir.
- <b>BeagleBoard.org Debian imajı:</b> Bootloader, kernel ve DTB içerir ama hazır initramfs yoktur; seri boot için daha az uygundur.

#### <a name="c7-yol-2--kaynak-koddan-derleme"></a>Yol 2 — Kaynak koddan derleme

Cross toolchain kurulumu ve SPL/U-Boot derlemesi [Bölüm 9](#c9-bölüm-9--cross-toolchain-spl-ve-u-boot-derleme)'da adım adım anlatılıyor. `mkimage` aracı için `sudo apt install u-boot-tools` yeterli.

| Dosya | Kaynak kod | Çıktının yeri |
|---|---|---|
| `u-boot-spl.bin`, `u-boot.img` | <b>U-Boot</b> ([Bölüm 9](#c9-bölüm-9--cross-toolchain-spl-ve-u-boot-derleme)) | `spl/u-boot-spl.bin`, `u-boot.img` |
| `uImage` | <b>Linux kernel</b> (BBB için genelde `github.com/beagleboard/linux`) | `arch/arm/boot/uImage` |
| `am335x-boneblack.dtb` | Aynı kernel kaynağı | `arch/arm/boot/dts/am335x-boneblack.dtb` |
| `initramfs` | <b>BusyBox</b> (`busybox.net`) ile hazırlanan rootfs klasörü | Senin oluşturduğun dosya |

```bash
# U-Boot  -> spl/u-boot-spl.bin ve u-boot.img  (ayrıntılar: Bölüm 9)
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- am335x_evm_defconfig
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- -j4

# Kernel + DTB  -> arch/arm/boot/uImage ve .../dts/am335x-boneblack.dtb
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- bb.org_defconfig
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- uImage dtbs LOADADDR=0x80008000

# BusyBox  -> _install/ klasörü (rootfs'in temeli)
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- defconfig
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- CONFIG_PREFIX=../rootfs install

# initramfs: rootfs klasöründen cpio arşivi + U-Boot başlığı
cd rootfs
find . | cpio -H newc -o | gzip -9 > ../initramfs.cpio.gz
cd ..
mkimage -A arm -O linux -T ramdisk -C gzip -n initramfs -d initramfs.cpio.gz initramfs
```

Son satırdaki `mkimage` önemli: `bootm` komutu ramdisk'in başında <b>U-Boot başlığı</b> görmek ister. Ham `initramfs.cpio.gz` gönderirsen `Wrong Ramdisk Image Format` hatası alırsın ([7.9 (g)](#c7-g-bootm-hataları)).

#### <a name="c7-yol-3--buildroot-ile-hepsini-tek-seferde"></a>Yol 3 — Buildroot ile hepsini tek seferde

Buildroot toolchain'i, U-Boot'u, kernel'i, DTB'yi ve rootfs'i senin yerine indirip derler:

```bash
git clone https://gitlab.com/buildroot.org/buildroot.git
cd buildroot
make beaglebone_defconfig
make menuconfig
make                     # ilk derleme 30 dk - 1 saat sürebilir
ls -1 output/images/
```

`make menuconfig`'te seri boot için iki ayar yap:

| Menü | Ayar | Neden? |
|---|---|---|
| Bootloaders → U-Boot → U-Boot SPL binary name | `MLO spl/u-boot-spl.bin` | Varsayılan sadece `MLO`'yu kopyalar; seri boot için ham SPL gerekir. |
| Filesystem images → cpio the root filesystem → <b>Create U-Boot image of the root filesystem</b> | Aç | `rootfs.cpio.uboot` üretir: başında U-Boot başlığı olan initramfs. |

![Buildroot output/images klasörü](../images/serial_boot/12_buildroot_images.png)

Buildroot kernel'i `zImage` olarak verir. `bootm` için `uImage`'e çevir (ya da `uImage` yerine `zImage` gönderip `bootm` yerine `bootz` kullan):

```bash
mkimage -A arm -O linux -T kernel -C none -a 0x80008000 -e 0x80008000 -n Linux -d zImage uImage
```

### <a name="c7-her-projede-baştan-mı-derleyeceğim"></a>Her projede baştan mı derleyeceğim?

Hayır. Hangi dosyanın ne zaman yeniden üretildiği:

| Dosya | Ne zaman yeniden derlenir? |
|---|---|
| SPL + U-Boot | Neredeyse hiç. Bir kez derlenir, uzun süre aynısı kullanılır. |
| Kernel (`uImage`) | Yeni bir sürücü eklendiğinde veya kernel ayarı değiştiğinde. |
| DTB | Donanım ayarı (pin, I2C/SPI cihazı vb.) değiştiğinde; sadece `make dtbs` yeterli. |
| initramfs / rootfs | En sık değişen kısım; kendi uygulamanı buraya koyarsın. Sadece `cpio` + `mkimage` adımı tekrarlanır. |

Gerçekten <b>senin yazdığın</b> kısım: kendi uygulaman, gerekirse bir kernel sürücüsü ve DTS'teki küçük değişiklikler. Geri kalanı hazır projelerin derlenmesidir.

> [!TIP]
> Önce kursun hazır dosyalarıyla seri boot'u bir kez çalıştır. Sonra dosyaları <b>teker teker</b> kendi derlediklerinle değiştir. Bir şey bozulursa hangi dosyada olduğunu hemen anlarsın.

---

## <a name="c7-78-adım-adım-seri-porttan-boot"></a>7.8 Adım Adım Seri Porttan Boot

> [!NOTE]
> Aşağıdaki ekran görüntüleri <b>temsilidir</b>; sürüm numaraları, tarih, boyut ve hız değerleri senin derlemene göre farklı olacaktır.

### <a name="c7-adım-0--bilgisayarda-hazırlık"></a>Adım 0 — Bilgisayarda hazırlık

Bütün dosyaları tek bir klasörde topla (örnekte `~/bbb`) ve U-Boot başlıklarını `mkimage -l` ile kontrol et:

![Bilgisayarda boot dosyalarını kontrol etme](../images/serial_boot/01_host_dosyalar.png)

```bash
cd ~/bbb
ls -l
mkimage -l uImage
mkimage -l initramfs
```

`u-boot-spl.bin` <b>109 KB'tan küçük</b> olmalı; ROM kodu onu iç SRAM'e koyar ve SRAM'de daha fazla yer yoktur.

### <a name="c7-adım-1--seri-kabloyu-bağla-minicomu-hazırla"></a>Adım 1 — Seri kabloyu bağla, Minicom'u hazırla

USB-TTL kablosunu J1 header'a bağla (<b>GND, RX, TX</b>; kablonun RX'i kartın TX'ine, TX'i kartın RX'ine). Port adını bulma, `dialout` grubu ve Minicom ayarları [Bölüm 2](#c2-bölüm-2--seri-konsol-ve-minicom)'de anlatıldı. Kısaca:

![Seri port aygıtını bulma, dialout izni ve lrzsz kurulumu](../images/serial_boot/02_host_seri_port.png)

```bash
sudo dmesg | tail -3
sudo usermod -aG dialout $USER      # bir kez; sonra oturumu kapatıp aç
sudo apt install minicom lrzsz
minicom -s                          # ayarlar (aşağıda)
cd ~/bbb && minicom -D /dev/ttyUSB0 -b 115200
```

> [!IMPORTANT]
> Minicom Xmodem/Ymodem gönderirken işi kendisi yapmaz, <b>`lrzsz`</b> paketindeki `sx` (Xmodem) ve `sb` (Ymodem) programlarını çalıştırır. `lrzsz` kurulu değilse dosya gönderilemez.

`minicom -s` → <b>Serial port setup</b> ekranında ayarlar şöyle olmalı. <b>Filenames and paths</b> menüsünde upload klasörünü `~/bbb` yaparsan dosya seçerken her seferinde klasör aramazsın:

![Minicom seri port ayarları: 115200 8N1, flow control kapalı](../images/serial_boot/03_minicom_ayar.png)

### <a name="c7-adım-2--kartı-uart-boot-modunda-aç-ve-spli-gönder-xmodem"></a>Adım 2 — Kartı UART boot modunda aç ve SPL'i gönder (Xmodem)

1. SD kartı çıkar, P4 mini USB kablosunu çıkar, 5V adaptörü hazırla ([7.3](#c7-73-kartı-uart-boot-moduna-sokmak)).
2. Minicom açıkken <b>S2</b>'ye basılı tut, adaptörü tak / <b>S3</b>'e bas, sonra S2'yi bırak.
3. Ekranda `CCCC...` akmaya başlar: ROM kodu UART0'da Xmodem ile dosya bekliyor.
4. Minicom'da `Ctrl-A` → `S` → <b>xmodem</b> → <b>`u-boot-spl.bin`</b> seç, gönder.

![ROM kodu CCCC basıyor, SPL Xmodem ile gönderiliyor](../images/serial_boot/04_rom_spl_xmodem.png)

Transfer bitince SPL çalışır, DDR'ı hazırlar, `U-Boot SPL ...` yazısını basar ve tekrar `CCCC` basmaya başlar. Bu sefer bekleyen <b>SPL</b>'dir ve <b>Ymodem</b> ister.

### <a name="c7-adım-3--u-bootu-gönder-ymodem"></a>Adım 3 — U-Boot'u gönder (Ymodem)

> [!NOTE]
> Kursun `serial-boot` klasöründeki dosyalar: SPL <b>2017.03</b>, U-Boot <b>2016.11-rc1</b>. Bu sürümlerde U-Boot'un komut istemi `=>`'dir. [Bölüm 4](#c4-bölüm-4--sd-karttan-boot)'teki eski Ångström U-Boot'u (2013.04) ise `U-Boot#` gösterir. Komutlar ikisinde de aynıdır.

1. `Ctrl-A` → `S` → <b>ymodem</b> → <b>`u-boot.img`</b> seç, gönder.
2. U-Boot açılır. `Hit any key to stop autoboot` çıkınca <b>hemen bir tuşa bas.</b>

![u-boot.img Ymodem ile gönderiliyor, U-Boot komut satırı](../images/serial_boot/05_spl_uboot_ymodem.png)

> [!WARNING]
> Autoboot'u durdurmazsan U-Boot kendi `bootcmd`'ini çalıştırır ve kartın <b>eMMC</b>'sindeki Linux'u (ör. Debian) açar. O zaman seri boot'un amacı boşa gider; kartı kapatıp Adım 2'den başla.

### <a name="c7-adım-4--kerneli-rame-al-loadx-0x82000000"></a>Adım 4 — Kernel'i RAM'e al: `loadx 0x82000000`

```text
=> loadx 0x82000000
```

U-Boot Xmodem ile beklemeye başlar. Minicom'da `Ctrl-A` → `S` → <b>xmodem</b> → <b>`uImage`</b>.

![loadx ile uImage gönderimi](../images/serial_boot/06_loadx_uimage.png)

> [!NOTE]
> 115200 baud'da hız en fazla ~11 KB/s'dir. 4 MB'lık bir `uImage` yaklaşık <b>6–7 dakika</b> sürer; bu normaldir. Xmodem son paketi 128 bayta tamamladığı için `Total Size` dosya boyutundan biraz büyük görünür, sorun değil.

### <a name="c7-adım-5--dtb-ve-initramfsi-rame-al"></a>Adım 5 — DTB ve initramfs'i RAM'e al

```text
=> loadx 0x88000000        (Minicom: xmodem -> am335x-boneblack.dtb)
=> loadx 0x88080000        (Minicom: xmodem -> initramfs)
```

![loadx ile DTB ve initramfs gönderimi](../images/serial_boot/07_loadx_dtb_initramfs.png)

### <a name="c7-adım-6--yüklenenleri-kontrol-et-isteğe-bağlı-ama-önerilir"></a>Adım 6 — Yüklenenleri kontrol et (isteğe bağlı ama önerilir)

Boot etmeden önce dosyaların sağlam geldiğini görmek, sonradan "neden açılmadı?" diye uğraşmaktan iyidir:

```text
=> iminfo 0x82000000
=> iminfo 0x88080000
=> md.b 0x88000000 4
```

![iminfo ile CRC kontrolü, md ile DTB sihirli sayısı](../images/serial_boot/08_iminfo_kontrol.png)

- `iminfo`, U-Boot başlığındaki CRC'yi RAM'deki veriyle karşılaştırır. `Verifying Checksum ... OK` görmelisin.
- DTB'nin U-Boot başlığı yoktur; ilk 4 baytı her zaman <b>`d0 0d fe ed`</b> olmalıdır.

### <a name="c7-adım-7--bootargs-ayarla-ve-bootm-ile-boot-et"></a>Adım 7 — `bootargs` ayarla ve `bootm` ile boot et

```text
=> setenv bootargs console=ttyO0,115200 root=/dev/ram0 rw initrd=0x88080000
=> bootm 0x82000000 0x88080000 0x88000000
```

Boot etmeden önce kernel'e <b>rootfs'in nerede olduğunu</b> `bootargs` ile bildiriyoruz:

| Parametre | Anlamı |
|---|---|
| `console=ttyO0,115200` | Kernel mesajlarını UART0'a, 115200 baud ile bas (kursun kernel'i 3.8.13 için `ttyO0`; [7.9 (h)](#c7-h-starting-kernel--yazıp-donuyor)). |
| `root=/dev/ram0` | Kök dosya sistemi (rootfs) bir disk değil, <b>RAM</b>'de duruyor. |
| `rw` | Rootfs okunur-yazılır bağlansın. |
| `initrd=0x88080000` | initramfs'i RAM'de <b>`0x88080000`</b> adresine yüklediğimizi kernel'e bildirir (Adım 5'teki `loadx` adresiyle aynı olmalı). |
| `bootm <kernel> <initramfs> <dtb>` | Sıra önemli: <b>kernel – ramdisk – DTB</b>. Ramdisk yoksa ortaya `-` yazılır (`bootm 0x82000000 - 0x88000000`). |

> [!NOTE]
> `bootm`'in ikinci parametresi (`0x88080000`) de initramfs'in adresini ve boyutunu kernel'e DTB'nin `/chosen` düğümü üzerinden bildirir. Yani adres iki yerden veriliyor; `bootargs`'taki `initrd=` ile `bootm`'deki adresin <b>aynı</b> olduğuna dikkat et. `printenv bootargs` ile yazdığını kontrol edebilirsin.

![bootm ile kernel, initramfs ve DTB'den boot](../images/serial_boot/09_bootm.png)

### <a name="c7-adım-8--linux-açıldı"></a>Adım 8 — Linux açıldı

Kernel initramfs'i açar, içindeki `/init` (BusyBox) çalışır ve seri konsoldan kabuk gelir:

![initramfs'ten açılan BusyBox kabuğu](../images/serial_boot/10_linux_shell.png)

`mount` çıktısında `/`'nin <b>`rootfs`</b> olduğunu görürsün: Kart ne SD karta ne eMMC'ye dokunmadan, tamamen seri porttan gelen dosyalarla RAM'den çalışıyor.

> [!TIP]
> RAM'deki her şey kart kapanınca silinir. Bir sonraki açılışta bütün adımları (SPL'den itibaren) tekrar yapman gerekir.

### <a name="c7-komutların-kısa-özeti"></a>Komutların kısa özeti

```text
[Kart: S2 basılı + güç, ekranda CCCC]
Minicom: Ctrl-A S -> xmodem -> u-boot-spl.bin
Minicom: Ctrl-A S -> ymodem -> u-boot.img
[Hit any key -> tuşa bas]
=> loadx 0x82000000          -> xmodem -> uImage
=> loadx 0x88000000          -> xmodem -> am335x-boneblack.dtb
=> loadx 0x88080000          -> xmodem -> initramfs
=> setenv bootargs console=ttyO0,115200 root=/dev/ram0 rw initrd=0x88080000
=> bootm 0x82000000 0x88080000 0x88000000
```

---

## <a name="c7-79-karşılaşılabilecek-problemler"></a>7.9 Karşılaşılabilecek Problemler

![Sık görülen hata çıktıları (temsili)](../images/serial_boot/11_hatalar.png)

### <a name="c7-a-ekranda-hiç-cccc-çıkmıyor"></a>a) Ekranda hiç `CCCC` çıkmıyor

| Olası neden | Çözüm |
|---|---|
| SD kart takılı | ROM önce MMC0'ı dener, SD'de MLO varsa oradan açılır. SD kartı çıkar. |
| P4 mini USB kablosu takılı | ROM USB0'da 4.5 dakika bekler. Kabloyu çıkar, kartı 5V adaptörle besle ([7.3](#c7-73-kartı-uart-boot-moduna-sokmak)). |
| S2 basılı değildi | Kart eMMC'den açılır (ekranda eMMC'deki U-Boot/Linux çıkar). Kartı kapat, S2 basılıyken tekrar aç. |
| TX / RX ters bağlı ya da GND bağlı değil | Kablonun TX'i → kartın RX'i, RX'i → kartın TX'i. GND mutlaka bağlı olmalı. |
| Yanlış port / baud | `dmesg` ile doğru `/dev/ttyUSBx`'i bul; ayar 115200 8N1 olmalı. |
| Minicom'u kart açıldıktan sonra açtın | `C`'leri kaçırmış olabilirsin. Önce Minicom'u aç, sonra kartı aç. |

### <a name="c7-b-cccc-var-ama-transfer-başlamıyor--yarıda-kesiliyor"></a>b) `CCCC` var ama transfer başlamıyor / yarıda kesiliyor

| Olası neden | Çözüm |
|---|---|
| <b>Hardware Flow Control: Yes</b> | Minicom karta veri göndermez. `minicom -s` ile <b>No</b> yap (en sık yapılan hata!). |
| `lrzsz` kurulu değil (`sx: not found`) | `sudo apt install lrzsz` |
| Dosya seçmek çok uzun sürdü, ROM vazgeçti | Upload klasörünü önceden ayarla, `C` görünür görünmez gönder. `C` akışı durduysa kartın gücünü kesip S2 ile baştan aç. |
| Yanlış protokol | ROM ve `loadx` → <b>xmodem</b>; SPL'in `u-boot.img` için beklediği ve `loady` → <b>ymodem</b>. Karıştırılırsa transfer hiç başlamaz veya `Transfer incomplete` olur. |
| Transfer sırasında klavyeye basıldı | Gelen tuşlar Xmodem paketlerini bozar. Transfer bitene kadar dokunma. |

### <a name="c7-c-spl-gönderildi-ama-hiçbir-şey-olmuyor"></a>c) SPL gönderildi ama hiçbir şey olmuyor

| Olası neden | Çözüm |
|---|---|
| `u-boot-spl.bin` yerine <b>`MLO`</b> gönderildi | MLO'nun başında GP header var; ROM onu kod sanıp çalıştırır ve kilitlenir. UART boot'ta <b>ham `u-boot-spl.bin`</b> gönderilir. |
| SPL 109 KB'tan büyük | ROM iç SRAM'e sığdıramaz. SPL'deki gereksiz özellikleri kapatıp yeniden derle. |
| SPL farklı bir kart/işlemci için derlenmiş | BBB için uygun defconfig ile yeniden derle ([9.3](#c9-93-adım-adım-toolchain-kurulumu-ve-u-boot-derleme)). |

### <a name="c7-d-spl-çalışıyor-ama-u-bootimg-yüklenmiyor"></a>d) SPL çalışıyor ama `u-boot.img` yüklenmiyor

| Olası neden | Çözüm |
|---|---|
| SPL, UART'tan Ymodem alma desteğiyle derlenmemiş (`CONFIG_SPL_YMODEM_SUPPORT`) | SPL başka bir aygıt (MMC) arar ve hata verir. Config'te YMODEM desteğini aç, yeniden derle. |
| `u-boot.img` Xmodem ile gönderildi | SPL Ymodem bekler; <b>ymodem</b> seç. |
| `u-boot.img` yerine `u-boot.bin` gönderildi | SPL, başında mkimage başlığı olan `u-boot.img`'i bekler. |

### <a name="c7-e-u-boot-açıldı-ama-kendi-kendine-emmcden-boot-etti"></a>e) U-Boot açıldı ama kendi kendine eMMC'den boot etti

`Hit any key to stop autoboot` sırasında tuşa basılmadı. Kartı kapatıp baştan başla; geri sayım başlar başlamaz bir tuşa bas.

> [!CAUTION]
> Seri boot sırasında U-Boot'ta <b>`saveenv` yapma</b>. Değişkenler eMMC'deki ortama yazılır ve kartın normal açılışını bozabilir.

### <a name="c7-f-transfer-çok-yavaş"></a>f) Transfer çok yavaş

115200 baud'da ~11 KB/s normaldir; `uImage` 6–7 dakika, initramfs birkaç dakika sürer. Hızlandırmak için:

- <b>Baud yükseltme:</b> `loadx`/`loady` ikinci parametre olarak baud alır: `loady 0x82000000 460800`. U-Boot hızı değiştirmeni ister; Minicom'da `Ctrl-A` → `P` ile aynı hıza geç, Enter'a bas, gönder. Bitince U-Boot 115200'e dönmeni ister; Minicom'u geri al ve <b>ESC</b>'ye bas. (Her USB-TTL kablo yüksek hızlarda güvenilir çalışmaz; hata alırsan 115200'e dön.)
- <b>Ymodem:</b> `loady` 1 KB'lık paketlerle çalıştığı için `loadx`'ten biraz daha hızlıdır.
- <b>TFTP:</b> U-Boot açıldıktan sonra Ethernet kablosu varsa `tftpboot` ile saniyeler içinde yüklenir ([Bölüm 8](#c8-bölüm-8--tftp-ile-ağdan-boot)).

### <a name="c7-g-bootm-hataları"></a>g) `bootm` hataları

| Hata | Neden | Çözüm |
|---|---|---|
| `Wrong Ramdisk Image Format` / `Ramdisk image is corrupt or invalid` | initramfs'in başında U-Boot başlığı yok veya yanlış adrese yüklendi | Bilgisayarda `mkimage -T ramdisk ...` ile başlık ekle ([7.7](#c7-77-elimizdeki-boot-dosyaları-nedir)). `iminfo 0x88080000` ile kontrol et. |
| `Bad Data CRC` | Transfer sırasında veri bozuldu ya da bir dosya diğerinin üstüne yazıldı | Dosyayı tekrar gönder. Adresleri [7.5](#c7-75-önerilen-ram-yükleme-adresleri)'teki gibi kullan; DTB 512 KB'ı aşmamalı. |
| `Bad Magic Number` / `Wrong Image Format for bootm command` | `uImage` yerine `zImage` gönderildi veya adres yanlış | Kernel'i `make uImage LOADADDR=0x80008000` ile derle ya da `zImage` için `bootz` kullan. |
| DTB bulunamadı / `FDT_ERR_BADMAGIC` | DTB bozuk ya da yanlış adrese yüklendi | `md.b 0x88000000 4` → `d0 0d fe ed` görmelisin. Görmüyorsan DTB'yi tekrar gönder. |

### <a name="c7-h-starting-kernel--yazıp-donuyor"></a>h) `Starting kernel ...` yazıp donuyor

| Olası neden | Çözüm |
|---|---|
| `console=` yanlış | Eski kernel'ler (3.x, TI omap-serial sürücüsü) → `ttyO0`. Daha yeni (4.x ve sonrası) kernel'lerde genellikle `ttyS0`. Kernel aslında açılmış olabilir, sadece mesajları başka yere basıyordur. |
| DTB, kernel sürümüyle uyumsuz | DTB'yi <b>aynı kernel kaynağından</b> derlenmiş olanla değiştir; BBB için `am335x-boneblack.dtb` (`am335x-bone.dtb` değil). |
| `bootm` parametre sırası yanlış | Sıra: `bootm <kernel> <ramdisk> <dtb>`. |

### <a name="c7-i-kernel-açılıyor-ama-panic-veriyor"></a>i) Kernel açılıyor ama panic veriyor

| Hata | Neden | Çözüm |
|---|---|---|
| `VFS: Unable to mount root fs on unknown-block(1,0)` | initramfs içinde <b>`/init`</b> yok; kernel `root=/dev/ram0`'ı bağlamaya çalışıyor ve başarısız oluyor | rootfs klasöründe `ln -s sbin/init init` yapıp initramfs'i yeniden oluştur, ya da `bootargs`'a `rdinit=/sbin/init` ekle. |
| `VFS: Unable to mount root fs on unknown-block(0,0)` | Kernel ramdisk'i hiç almamış veya `CONFIG_BLK_DEV_INITRD` kapalı | `bootm`'in ikinci parametresini kontrol et; kernel config'te initramfs/initrd desteğini aç. |
| `Failed to execute /init` / `No working init found` | initramfs'teki programlar ARM için derlenmemiş veya kütüphaneler eksik | BusyBox'ı `CROSS_COMPILE=arm-linux-gnueabihf-` ile ve tercihen <b>static</b> derle; dinamik derlediysen `lib/` klasörüne gerekli kütüphaneleri koy. `file bin/busybox` → `ARM` yazmalı. |
| `RAMDISK: incomplete write` | initramfs yerine ext2 <b>initrd</b> imajı kullanılıyor ve kernel'in varsayılan ramdisk boyutundan büyük | `bootargs`'a `ramdisk_size=<KB>` ekle. |

### <a name="c7-j-ekranda-bozuk--anlamsız-karakterler"></a>j) Ekranda bozuk / anlamsız karakterler

Baud rate uyuşmuyor. Minicom 115200 8N1 olmalı. Baud yükseltme ([f](#c7-f-transfer-çok-yavaş)) denediysen Minicom'u tekrar 115200'e al.


<div class="page-break"></div>

# <a name="c8-bölüm-8--tftp-ile-ağdan-boot"></a>Bölüm 8 — TFTP ile Ağdan Boot

> <b>Bu bölümde:</b>
> - Bilgisayarına bir TFTP sunucusu (`tftpd-hpa`) kuracaksın.
> - Kernel, DTB ve initramfs'i her açılışta <b>Ethernet üzerinden</b> host'tan çekerek kartı açacaksın: önce komutları elle yazarak, sonra `uEnv.txt` ile otomatik olarak.
> - Neden bazı dosyaların yine de SD kartta durmak zorunda olduğunu anlayacaksın.
> - Challenge: eMMC → SD → TFTP → NFS sırasıyla deneyen genel bir `uEnv.txt` yazacaksın.
>
> <b>Ön koşul:</b> [Bölüm 4](#c4-bölüm-4--sd-karttan-boot) — SD kart, [Bölüm 6](#c6-bölüm-6--u-boot-komut-satırı-ve-uenvtxt) — `uEnv.txt` ve U-Boot komutları, [Bölüm 7](#c7-bölüm-7--seri-porttan-uart-boot) — RAM adresleri ve `bootm`.

---

## <a name="c8-81-genel-bakış"></a>8.1 Genel Bakış

Host bilgisayar <b>TFTP sunucusu</b>, BeagleBone Black ise <b>TFTP istemcisi</b> olur. İkisi Ethernet kablosuyla bağlanır:

![Host PC (TFTP sunucu) ile BBB (TFTP istemci) Ethernet ile bağlı](../images/{620FFBBE-4366-4EF5-A39A-249B1E305F30}.png)

Dosyalar iki gruba ayrılır:

![Host PC'de dtb, uImage, initramfs; SD kartta SPL, u-boot.img, uEnv.txt](../images/{7656F595-68A7-41D9-B830-F647EF669264}.png)

| Nerede? | Dosyalar |
|---|---|
| <b>SD kart</b> | SPL (MLO), u-boot.img, uEnv.txt |
| <b>Host PC</b> `/var/lib/tftpboot` | am335x-boneblack.dtb, uImage, initramfs |

Kart önce SD karttan U-Boot'a kadar açılır. Sonra U-Boot, uEnv.txt'deki `tftp` komutlarıyla diğer dosyaları host'tan çekip DDR'a yerleştirir:

![U-Boot TFTP komutuyla dtb, uImage ve dosya sistemini host'tan çeker](../images/{B63514F3-1414-44B0-9ED0-67D141EF6F4E}.png)

![Özet](../images/{5831DAB2-E3ED-4587-A75C-C006E2D88880}.png)

---

## <a name="c8-82-neden-bütün-dosyalar-tftp-ile-gönderilmiyor"></a>8.2 Neden Bütün Dosyalar TFTP ile Gönderilmiyor?

Kısaca: <b>TFTP isteğini yapacak kod U-Boot'un içinde.</b> U-Boot ağdan gelecek olsaydı, onu ağdan isteyecek bir program olmazdı. Bu bir tavuk-yumurta problemi.

### <a name="c8-boot-zinciri"></a>Boot zinciri

```
1. ROM Code (çipin içinde, değiştirilemez)
   │  SD karttan MLO/SPL'i bulur, dahili SRAM'e (~109 KB) yükler
   ▼
2. SPL / MLO
   │  saatleri ve pinleri ayarlar, DDR RAM'i başlatır,
   │  u-boot.img'yi DDR'a yükler
   ▼
3. u-boot.img  (tam U-Boot)
   │  Ethernet + MMC + UART sürücülerini başlatır,
   │  uEnv.txt'yi okur, TFTP istemcisini çalıştırır
   ▼
TFTP ile host'tan:  uImage, .dtb, initramfs  →  DDR  →  bootm
```

- <b>SPL</b>, DDR RAM'i başlatır. DDR hazır olmadan büyük dosyalar (U-Boot, kernel) bir yere yüklenemez.
- <b>u-boot.img</b>, U-Boot'un kendisidir. Ethernet sürücüsü ve TFTP istemcisi buradadır.
- <b>uEnv.txt</b>, U-Boot'a `ipaddr`, `serverip` ve hangi dosyayı hangi adrese çekeceğini söyler. U-Boot bu bilgiyi okuyabilmek için dosyanın yerel bir depolamada durması gerekir.
- <b>TFTP istemci/sunucu protokolüdür.</b> Host dosyayı kendiliğinden göndermez, kartın istemesi gerekir. İsteyecek kod (U-Boot) çalışmadan kart ağdan hiçbir şey alamaz.
- <b>ROM Code'un okuyabileceği yerler sabittir.</b> BBB'nin boot listesinde Ethernet yoktur ([3.5](#c3-35-boot-kaynakları-ve-boot-sırası-sysboot-pinleri)). AM335x'in ROM'u aslında Ethernet'ten boot'u destekler, ama BBB'de bu seçeneği açmak için donanımda değişiklik gerekir.

> [!NOTE]
> U-Boot'un başlattığı sürücüler <b>kalıcı değildir</b>. U-Boot sadece dosya yükleyip kernel'i çalıştırmak için gereken sürücüleri başlatır. Kernel açılınca bütün donanımı kendi sürücüleriyle <b>yeniden</b> başlatır.

### <a name="c8-bunun-amacı-geliştirmeyi-hızlandırmak"></a>Bunun amacı: geliştirmeyi hızlandırmak

| Dosya | Ne sıklıkla değişir? | Nerede durur? |
|---|---|---|
| SPL, u-boot.img, uEnv.txt | Neredeyse hiç | SD kart (bir kere kopyalanır) |
| uImage, .dtb, initramfs | Sürekli (kernel derle, DT düzenle, rootfs'e ekle) | Host PC, `/var/lib/tftpboot` |

- Kernel ya da device tree değişince SD kartı çıkarıp takmaya gerek kalmaz. Yeni dosyayı `/var/lib/tftpboot` içine kopyalayıp kartı resetlemek yeterli.
- SD kartın yıpranma ve bozulma riski azalır.
- Sektörde de böyle çalışılır: bootloader kartta sabit durur, kernel (ve sonra NFS ile rootfs) ağdan gelir.

> [!TIP]
> Tek cümleyle: SD karttaki SPL + U-Boot kartı <b>"ağdan dosya isteyebilir"</b> hale getirir. Ondan sonra gelen her şey TFTP ile host'tan alınır.

---

## <a name="c8-83-tftp-hostu-hazırlama"></a>8.3 TFTP Host'u Hazırlama

> [!NOTE]
> Aşağıdaki ekran görüntüleri <b>temsilidir</b>; sürüm numaraları, tarih ve PID değerleri senin bilgisayarında farklı olacaktır.

### <a name="c8-adım-1--paket-listesini-güncelle"></a>Adım 1 — Paket listesini güncelle

![apt-get update ve apt upgrade](../images/tftp_boot/01_apt_update.png)

```bash
sudo apt-get update
sudo apt upgrade
```

### <a name="c8-adım-2--tftp-sunucusunu-kur"></a>Adım 2 — TFTP sunucusunu kur

`tftpd-hpa`, Trivial File Transfer Protocol için bir sunucu (daemon) programıdır.

![tftpd-hpa kurulumu](../images/tftp_boot/02_install_tftpd.png)

```bash
sudo apt-get install tftpd-hpa
```

### <a name="c8-adım-3--ayar-dosyasını-düzenle"></a>Adım 3 — Ayar dosyasını düzenle

`/etc/default/tftpd-hpa` dosyasını aç ve içeriği aşağıdaki gibi yap:

![/etc/default/tftpd-hpa ayar dosyası](../images/tftp_boot/03_tftpd_config.png)

```bash
sudo vim /etc/default/tftpd-hpa
```

```
TFTP_USERNAME="tftp"
TFTP_DIRECTORY="/var/lib/tftpboot"
TFTP_ADDRESS=":69"
TFTP_OPTIONS="--create --secure"
```

| Ayar | Anlamı |
|---|---|
| `TFTP_USERNAME` | Servis bu kullanıcının yetkileriyle çalışır |
| `TFTP_DIRECTORY` | Kartın dosya çekeceği klasör |
| `TFTP_ADDRESS=":69"` | Bütün ağ arayüzlerinde UDP 69 portunu dinle |
| `--secure` | Dosya yolları bu klasöre göre yazılır (`tftp ... uImage` yeterli, tam yol gerekmez) |
| `--create` | İstemcinin klasöre yeni dosya yüklemesine izin verir |

> [!WARNING]
> Ayar dosyasında portu <b>69</b> olarak bırak. `TFTP_ADDRESS="0.0.0.0:6900"` gibi farklı bir port yazarsan U-Boot'un `tftpboot` komutu sunucuyu bulamaz, çünkü varsayılan olarak 69'a bağlanır. `TFTP_DIRECTORY` için `/home/<user>/tftp` gibi başka bir klasör de kullanabilirsin, ama bu kitapta her yerde `/var/lib/tftpboot` geçiyor.

### <a name="c8-adım-4--tftpboot-klasörünü-oluştur"></a>Adım 4 — tftpboot klasörünü oluştur

![tftpboot klasörünü oluşturma ve izinler](../images/tftp_boot/04_tftpboot_dir.png)

```bash
sudo mkdir -p /var/lib/tftpboot
sudo chown tftp:tftp /var/lib/tftpboot
sudo chmod -R 777 /var/lib/tftpboot
```

### <a name="c8-adım-5--tftp-servisini-başlat-ve-kontrol-et"></a>Adım 5 — TFTP servisini başlat ve kontrol et

![tftpd-hpa servisini başlatma ve durum kontrolü](../images/tftp_boot/05_tftpd_start.png)

```bash
sudo systemctl start tftpd-hpa
systemctl status tftpd-hpa       # "active (running)" görmelisin
sudo ss -ulpn | grep :69         # UDP 69 dinleniyor mu?
```

> [!TIP]
> Ayar dosyasını sonradan değiştirirsen servisi yeniden başlat: `sudo systemctl restart tftpd-hpa`

---

## <a name="c8-84-bağlantılar"></a>8.4 Bağlantılar

| Kablo | Görevi |
|---|---|
| 5V adaptör (barrel jack) | Güç. Bilgisayarın USB'si 500 mA ile sınırlı, kart boot sırasında resetlenebilir. |
| USB-TTL kablo (J1 header) | Seri konsol (minicom): U-Boot'u durdurmak ve mesajları görmek |
| <b>Ethernet kablosu</b> (host ↔ BBB) | <b>TFTP dosya aktarımı</b> |

Bu bölümde kullanılan adresler:

| Cihaz | IP | U-Boot değişkeni |
|---|---|---|
| Host PC (TFTP sunucu) | `192.168.27.1` | `serverip` |
| BBB (TFTP istemci) | `192.168.27.2` | `ipaddr` |

İki adres <b>aynı alt ağda</b> (`192.168.27.x`) olmalı. Kursun şemasındaki `192.168.7.x` adreslerini de kullanabilirsin; önemli olan host ile kartın aynı ağda olması.

---

## <a name="c8-85-yol-1--komutları-elle-yazarak-tftp-ile-boot"></a>8.5 Yol 1 — Komutları Elle Yazarak TFTP ile Boot

İki yol var:

| | Yol 1 — Elle (bu başlık) | Yol 2 — uEnv.txt ile otomatik ([8.6](#c8-86-yol-2--uenvtxt-ile-otomatik-tftp-boot)) |
|---|---|---|
| Nasıl? | Her açılışta U-Boot'u durdurup komutları minicom'a yazarsın | Komutlar SD karttaki `uEnv.txt`'de durur, U-Boot kendisi çalıştırır |
| Ne zaman? | İlk deneme, hata ayıklama: hangi komutun nerede takıldığını görürsün | Kurulum bir kez çalıştıktan sonra, günlük geliştirmede |

Önce Yol 1 ile bir kere çalıştır, sonra Yol 2'ye geç. Yol 2'deki `uEnv.txt` aynı komutları içerdiği için bir hata olursa Yol 1'e dönüp tek tek denersin.

<b>Hangi dosyalar?</b>

| Nerede? | Dosya | Kaynak |
|---|---|---|
| SD kart (BOOT) | `MLO`, `u-boot.img` | Kursun güncel `SD-boot` imajları (U-Boot 2022.04) ya da [Bölüm 9](#c9-bölüm-9--cross-toolchain-spl-ve-u-boot-derleme)'da kendi derlediklerin |
| Host (`/var/lib/tftpboot`) | `uImage`, `am335x-boneblack.dtb`, `initramfs` | Kursun `tftp-boot` klasörü (Ångström kernel 3.8.13) ya da kendi derlediklerin |

> [!WARNING]
> Kursun güncel `SD-boot` U-Boot'unda `bootdelay=0`. Yani `Hit any key to stop autoboot` geri sayımı yok denecek kadar kısa. U-Boot'u durdurmak için kart açılırken <b>Space tuşuna basılı tut</b> ya da art arda bas. Bekleme süresini uzatmak [9.4](#c9-94-challenge-autoboot-bekleme-süresini-10-saniyeye-çıkarmak)'teki challenge'ın konusu.

> [!NOTE]
> Aşağıdaki ekran görüntüleri <b>temsilidir</b>; arayüz adı (`enp3s0`), sürüm, tarih, boyut ve hız değerleri senin ortamında farklı olacaktır.

### <a name="c8-adım-1--hostun-ethernet-arayüzüne-ip-ver-dosyaları-kopyala"></a>Adım 1 — Host'un Ethernet arayüzüne IP ver, dosyaları kopyala

Önce kartın bağlı olduğu Ethernet arayüzünün adını bul. Sonra o arayüze statik IP ver ve boot dosyalarını TFTP klasörüne kopyala:

![Host Ethernet arayüzüne IP verme ve dosyaları tftpboot'a kopyalama](../images/tftp_boot/06_host_ip.png)

```bash
ip -br a                                                          # arayüz adını bul (örn. enp3s0, eth0)
sudo ip addr add 192.168.27.1/24 dev enp3s0       # geçici: yeniden başlatınca silinir
sudo cp uImage am335x-boneblack.dtb initramfs /var/lib/tftpboot/
ls -l /var/lib/tftpboot
```

> [!TIP]
> <b>`ifconfig` eski bir komut.</b> Yeni Ubuntu'larda kurulu bile gelmez (`net-tools` paketi gerekir). Yerine `ip a` / `ip -br a` kullan.
>
> IP adresinin kalıcı olmasını istersen NetworkManager ile bir profil oluştur:
> ```bash
> nmcli con add type ethernet ifname enp3s0 con-name bbb ipv4.method manual ipv4.addresses 192.168.27.1/24
> nmcli con up bbb
> ```

> [!IMPORTANT]
> <b>Ubuntu sanal makinedeyse</b> (VirtualBox/VMware), VM'in ağ ayarını <b>Bridged</b> yap ve fiziksel Ethernet kartını seç. NAT modunda kart host'a ulaşamaz.
>
> Güvenlik duvarı açıksa UDP 69'a izin ver: `sudo ufw allow 69/udp`

### <a name="c8-adım-2--sd-kartı-hazırla-1-bölüm-boot"></a>Adım 2 — SD kartı hazırla (1. bölüm: BOOT)

Dosyalar SD kartın <b>1. bölümüne (BOOT, FAT)</b> gider. ROM Code ve U-Boot sadece bu FAT bölümünü okur. 2. bölüm (ROOTFS, ext4) bu yöntemde kullanılmaz, çünkü kök dosya sistemi initramfs olarak ağdan geliyor.

![SD kart BOOT bölümüne MLO, u-boot.img ve uEnv.txt kopyalama](../images/tftp_boot/07_sd_boot_part.png)

```bash
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINT
cp MLO u-boot.img uEnv.txt /media/$USER/BOOT/
sync && sudo umount /media/$USER/BOOT
```

> [!IMPORTANT]
> SD karttaki SPL dosyasının adı tam olarak <b>`MLO`</b> olmalı. Seri boot'ta gönderdiğimiz `u-boot-spl.bin` SD kart için uygun değil, çünkü ROM Code SD karttan okurken başında GP başlığı olan `MLO` dosyasını arar. İkisi de U-Boot derlemesinde birlikte çıkar.

`uEnv.txt`'nin içeriği için iki seçenek var:
- <b>Elle deneyeceksen (Adım 3–5):</b> Önceki bölümlerdeki `uEnv.txt`'yi ya hiç koyma ya da U-Boot açılırken bir tuşa basıp autoboot'u durdur. Aksi halde kart kendi kendine SD/eMMC'den boot eder.
- <b>Otomatik boot için:</b> [8.6](#c8-86-yol-2--uenvtxt-ile-otomatik-tftp-boot)'daki `uEnv.txt`'yi koy.

Kartı SD karttan açmak için <b>S2 butonuna basılı tutarak</b> güç ver. Basmazsan kart eMMC'den açılır.

### <a name="c8-adım-3--u-bootu-durdur-ağ-ayarlarını-yap-ping-at"></a>Adım 3 — U-Boot'u durdur, ağ ayarlarını yap, ping at

Minicom açıkken kartı S2'ye basılı tutarak başlat, `Hit any key to stop autoboot` yazısı çıkınca bir tuşa bas:

![U-Boot'ta ipaddr, serverip, ethact ayarlama ve ping](../images/tftp_boot/08_uboot_net.png)

```
=> setenv ipaddr 192.168.27.2
=> setenv serverip 192.168.27.1
=> setenv ethact ethernet@4a100000
=> printenv ipaddr serverip ethact
=> ping 192.168.27.1
```

| Komut | Açıklama |
|---|---|
| `setenv ipaddr ...` | Kartın (istemci) IP adresi |
| `setenv serverip ...` | TFTP sunucusunun (host) IP adresi. `tftpboot` dosyayı bu adresten ister. |
| `setenv ethact ethernet@4a100000` | Kullanılacak ağ aygıtı. BBB'nin U-Boot'unda iki aygıt var: Ethernet portu ve USB üzerinden ağ (`usb_ether`). Adlarını açılıştaki `Net:` satırında görürsün. U-Boot 2022.04'te Ethernet'in adı `ethernet@4a100000`, 2016–2017 öncesi sürümlerde `cpsw`'dir. Çoğu zaman zaten varsayılandır, ama `Using usb_ether device` görürsen bu satır gerekir. |
| `ping ...` | Kablo ve IP ayarlarını test eder. `is alive` görmelisin. |

> [!NOTE]
> U-Boot sadece <b>ping atabilir</b>, gelen ping'e cevap vermez. Host'tan karta `ping 192.168.27.2` atarsan cevap gelmez, bu normaldir. Testi her zaman kart tarafından yap.

### <a name="c8-adım-4--dosyaları-tftp-ile-rame-çek"></a>Adım 4 — Dosyaları TFTP ile RAM'e çek

![tftpboot ile uImage, dtb ve initramfs'i RAM'e çekme](../images/tftp_boot/09_tftpboot.png)

```
=> tftpboot 0x82000000 uImage
=> tftpboot 0x88000000 am335x-boneblack.dtb
=> tftpboot 0x88080000 initramfs
```

Adresler seri boot bölümündekiyle aynı ([7.5](#c7-75-önerilen-ram-yükleme-adresleri)): kernel `0x82000000`, DTB `0x88000000`, initramfs `0x88080000`. `Bytes transferred` değeri host'taki `ls -l` boyutuyla aynı olmalı. (`tftp` ve `tftpboot` U-Boot'ta aynı komuttur.)

### <a name="c8-adım-5--bootargs-ayarla-ve-boot-et"></a>Adım 5 — `bootargs` ayarla ve boot et

![bootargs ayarlama ve bootm ile boot](../images/tftp_boot/10_bootm.png)

```
=> setenv bootargs console=ttyO0,115200 root=/dev/ram0 rw initrd=0x88080000
=> bootm 0x82000000 0x88080000 0x88000000
```

`bootm` argüman sırası: <b>kernel – initramfs – DTB</b>. Komuta sadece adresler yazılır. `bootargs`'ın ayrıntıları: [7.8 Adım 7](#c7-adım-7--bootargs-ayarla-ve-bootm-ile-boot-et).

### <a name="c8-komutların-kısa-özeti"></a>Komutların kısa özeti

```
# Host
sudo ip addr add 192.168.27.1/24 dev enp3s0
sudo cp uImage am335x-boneblack.dtb initramfs /var/lib/tftpboot/

# U-Boot (minicom)
setenv ipaddr 192.168.27.2
setenv serverip 192.168.27.1
ping 192.168.27.1
tftpboot 0x82000000 uImage
tftpboot 0x88000000 am335x-boneblack.dtb
tftpboot 0x88080000 initramfs
setenv bootargs console=ttyO0,115200 root=/dev/ram0 rw initrd=0x88080000
bootm 0x82000000 0x88080000 0x88000000
```

---

## <a name="c8-86-yol-2--uenvtxt-ile-otomatik-tftp-boot"></a>8.6 Yol 2 — uEnv.txt ile Otomatik TFTP Boot

Yol 1'deki U-Boot komutlarının hepsi `uEnv.txt`'ye yazılır. Kart açılınca U-Boot bu dosyayı SD kartın BOOT bölümünden okur ve `uenvcmd` içindeki komutları kendisi çalıştırır. Böylece <b>minicom'a hiçbir şey yazmana gerek kalmaz</b>; minicom'u sadece açılışı izlemek için kullanırsın.

Host tarafındaki hazırlık (IP verme, dosyaları `/var/lib/tftpboot`'a kopyalama) iki yolda da aynı. Yol 2 sadece U-Boot'ta elle yazdığın kısmı (Yol 1, Adım 3–5) otomatik yapar.

### <a name="c8-adım-1--hostu-hazırla"></a>Adım 1 — Host'u hazırla

Yol 1'in Adım 1'i ile aynı: Ethernet arayüzüne `192.168.27.1` ver, `uImage`, `am335x-boneblack.dtb`, `initramfs` dosyalarını `/var/lib/tftpboot`'a kopyala ve `systemctl status tftpd-hpa` ile servisin çalıştığını kontrol et.

### <a name="c8-adım-2--uenvtxt-dosyasını-yaz"></a>Adım 2 — `uEnv.txt` dosyasını yaz

Host'ta aşağıdaki içerikle bir `uEnv.txt` oluştur. Her değişken <b>tek satırda</b> olmalı; satırları bölme.

```
console=ttyO0,115200n8
serverip=192.168.27.1
ipaddr=192.168.27.2
loadaddr=0x82000000
fdtaddr=0x88000000
initrdaddr=0x88080000
loadfromtftp=echo "*** Booting From Network ***";tftpboot ${loadaddr} uImage;tftpboot ${fdtaddr} am335x-boneblack.dtb;tftpboot ${initrdaddr} initramfs
linuxbootargs=setenv bootargs console=${console} root=/dev/ram0 rw initrd=${initrdaddr}
uenvcmd=setenv autoload no;run loadfromtftp;run linuxbootargs;bootm ${loadaddr} ${initrdaddr} ${fdtaddr}
```

![Host'ta uEnv.txt içeriği ve tftpboot'a kopyalama](../images/tftp_boot/14_uenv_host.png)

| Satır | Açıklama | Yol 1'deki karşılığı |
|---|---|---|
| `console=ttyO0,115200n8` | Kendi tanımladığımız bir değişken; aşağıda `${console}` ile kullanılıyor. `n8`: parity yok, 8 bit. | `bootargs` içindeki `console=...` |
| `serverip=...` | TFTP sunucusunun (host) IP'si | `setenv serverip 192.168.27.1` |
| `ipaddr=...` | Kartın IP'si | `setenv ipaddr 192.168.27.2` |
| `loadaddr`, `fdtaddr`, `initrdaddr` | Kernel, DTB ve initramfs'in RAM adresleri. Adresleri bir kere yazıp aşağıda `${...}` ile kullanıyoruz; değiştirmek gerekirse tek yerden değişir. | `0x82000000`, `0x88000000`, `0x88080000` |
| `loadfromtftp=...` | Bir <b>makro</b>: ekrana mesaj basar, sonra 3 dosyayı TFTP ile RAM'e çeker. `run loadfromtftp` yazılınca çalışır. | 3 adet `tftpboot` komutu |
| `linuxbootargs=...` | Bir makro: `bootargs`'ı ayarlar | `setenv bootargs ...` |
| `uenvcmd=...` | U-Boot'un `uEnv.txt`'yi okuduktan sonra <b>otomatik çalıştırdığı</b> komut. Sırayla: makroları çalıştır, sonra `bootm`. | Yazdığın bütün komutların sırası |
| `setenv autoload no` | `dhcp`/`bootp` komutlarının IP aldıktan sonra kendiliğinden TFTP ile dosya çekmesini engeller. Statik IP kullandığımız için şart değil, ama zararı yok ve ileride `dhcp` eklersen sürpriz yaşatmaz. | — |

> [!WARNING]
> En sık yapılan iki hata:
> - `setenv booargs ...` gibi bir yazım hatası. U-Boot hata vermez, `booargs` adında yeni bir değişken oluşturur. Kernel'e gerçek `bootargs` gitmez, `Starting kernel ...` sonrası ekran boş kalabilir veya kernel rootfs bulamadan panic verir.
> - Makroyu bir adla tanımlayıp başka bir adla çağırmak (ör. `loadftp=...` tanımlayıp `run loadfromtftp` yazmak). U-Boot `## Error: "loadfromtftp" not defined` der ve dosyalar hiç çekilmez. Tanımladığın ad ile çağırdığın ad <b>birebir aynı</b> olmalı.

> [!IMPORTANT]
> Komutu `bootcmd` içine değil <b>`uenvcmd`</b> içine yaz. BBB'nin U-Boot'u `uEnv.txt`'yi kendi `bootcmd`'si çalışırken okur ve ardından `uenvcmd`'yi çalıştırır. Bu yüzden dosyadaki `bootcmd` o açılışı etkilemez ([6.3](#c6-63-uygulama-uenvtxtyi-seri-porttan-göndermek)).

### <a name="c8-adım-3--uenvtxtyi-sd-kartın-boot-bölümüne-koy"></a>Adım 3 — `uEnv.txt`'yi SD kartın BOOT bölümüne koy

İki seçenek var.

<b>a) Kart okuyucuyla (en basiti):</b> SD kartı bilgisayara tak ve dosyayı 1. bölüme kopyala.

```bash
cp uEnv.txt /media/$USER/BOOT/
sync && sudo umount /media/$USER/BOOT
```

<b>b) SD kartı çıkarmadan, TFTP ile:</b> Kart Linux'a açıkken (örneğin Yol 1 ile açtıktan sonra) dosyayı host'tan doğrudan SD karta çekebilirsin. Bunun için BusyBox'taki `tftp -g -r uEnv.txt 192.168.27.1` komutu kullanılır ([8.7](#c8-87-linux-açıldıktan-sonra-tftp-ile-dosya-çekme)).

Önce host'ta dosyayı TFTP klasörüne koy (`sudo cp uEnv.txt /var/lib/tftpboot/`). Sonra kartta:

![uEnv.txt'yi kartın içinden TFTP ile SD karta yazma](../images/tftp_boot/15_uenv_tftp_to_sd.png)

```
ifconfig eth0 192.168.27.2 netmask 255.255.255.0 up
mount /dev/mmcblk0p1 /mnt
cd /mnt
tftp -g -r uEnv.txt 192.168.27.1
ls
cd / && sync && umount /mnt
reboot
```

> [!IMPORTANT]
> `tftp` dosyayı <b>bulunduğun klasöre</b> kaydeder. Önce SD kartın BOOT bölümünü bağlayıp (`mount`) o klasöre girmezsen dosya initramfs'e, yani RAM'e yazılır ve yeniden başlatınca kaybolur. `mmcblk0` SD kart, `mmcblk1` eMMC'dir; `p1` 1. bölüm demek.

### <a name="c8-adım-4--kartı-başlat-ve-hiçbir-tuşa-basma"></a>Adım 4 — Kartı başlat ve hiçbir tuşa basma

S2'ye basılı tutarak güç ver (veya `reboot` sırasında basılı tut). Bu sefer `Hit any key to stop autoboot` çıkınca <b>dokunma</b>; U-Boot `uEnv.txt`'yi okur ve `uenvcmd`'yi çalıştırır:

![uEnv.txt ile otomatik TFTP boot](../images/tftp_boot/11_uenv_auto.png)

Ekranda `Running uenvcmd ...`, ardından `*** Booting From Network ***` ve üç tane `Bytes transferred` görmelisin.

### <a name="c8-adım-5--doğrula"></a>Adım 5 — Doğrula

Linux açılınca `bootargs`'ın gerçekten kernel'e gittiğini kontrol et:

![/proc/cmdline ile bootargs doğrulama](../images/tftp_boot/16_cmdline.png)

```
cat /proc/cmdline
```

Burada `console=ttyO0,115200n8 root=/dev/ram0 ...` görmüyorsan `linuxbootargs` çalışmamış demektir (değişken adını kontrol et).

### <a name="c8-adım-6--s2ye-basmadan-açılış-challenge"></a>Adım 6 — S2'ye basmadan açılış (Challenge)

Kursun bu bölümdeki challenge'ı: <i>TFTP boot'u `uEnv.txt` ile otomatikleştir; kart güç alınca ya da reset'e basılınca imajlar kendiliğinden insin ve <b>S2'ye basmadan</b> açılsın.</i>

S2'ye basmadan güç verince ROM Code <b>eMMC</b>'deki MLO/U-Boot'u çalıştırır ([3.5](#c3-35-boot-kaynakları-ve-boot-sırası-sysboot-pinleri)). Çözüm, eMMC'deki U-Boot'un `uEnv.txt`'yi nerede aradığına bağlı:

1. <b>Önce kontrol et.</b> U-Boot'u durdur ve ortamına bak:
   ```
   => printenv mmcdev bootenvfile bootenv
   => printenv bootcmd
   ```
   `mmcdev=0` ve `bootcmd` içinde `loadbootenv` / `envboot` gibi bir adım varsa, U-Boot açılışta önce <b>SD kartın 1. bölümündeki</b> `uEnv.txt`'yi okur (`mmc 0` = SD kart).
2. <b>Bu durumda yapman gereken tek şey</b> Adım 3'teki `uEnv.txt`'yi SD kartın BOOT bölümüne koymak. Kart eMMC'den açılsa bile SD karttaki dosyayı okur ve `uenvcmd` ile TFTP boot'u başlatır. S2'ye basmana gerek kalmaz.
3. eMMC'deki U-Boot dosyayı başka bir yerde arıyorsa (BeagleBoard'un yeni Debian imajları gibi, ör. eMMC'nin rootfs'indeki `/boot/uEnv.txt`), iki seçenek var:
   - Komutları U-Boot'un okuduğu dosyaya yaz, ya da
   - eMMC'deki `MLO`'yu devre dışı bırak. ROM Code eMMC'de geçerli MLO bulamayınca SD karta geçer ([3.1](#c3-31-rbl-rom-boot-loader)).

> [!CAUTION]
> eMMC'deki `MLO`'yu silmek, eMMC'deki sistemin kendi başına açılmamasına yol açar. Geri dönmek için [Bölüm 5](#c5-bölüm-5--emmcden-boot)'teki gibi eMMC'yi yeniden flash'lamak gerekir. Önce 1. ve 2. maddeyi dene.

### <a name="c8-yol-2nin-özeti"></a>Yol 2'nin özeti

Artık geliştirme döngüsü şu kadar:

```bash
# Host: kernel'i / DTB'yi yeniden derledin
sudo cp uImage am335x-boneblack.dtb /var/lib/tftpboot/
# Kartın reset butonuna bas → U-Boot yeni dosyaları kendisi çeker ve boot eder
```

> [!TIP]
> <b>Yol 2'yi kullanınca Yol 1'deki komutlara gerek kalmaz mı?</b> Her açılışta yazmana gerek kalmaz, ama komutları bilmek yine de gerekli. Bir şey bozulduğunda U-Boot'u durdurup `run loadfromtftp`, `printenv bootargs` gibi komutları tek tek çalıştırarak hangi adımın bozulduğunu bulursun. `uEnv.txt` sadece aynı komutları senin yerine yazar.

---

## <a name="c8-87-linux-açıldıktan-sonra-tftp-ile-dosya-çekme"></a>8.7 Linux Açıldıktan Sonra TFTP ile Dosya Çekme

Kart Linux'a açıldıktan sonra BusyBox'taki `tftp` istemcisiyle host'tan dosya alabilirsin.

<b>Host PC'de:</b>

```bash
echo "Merhaba BeagleBone, TFTP!" > helloworld     # veya: vi helloworld
sudo cp helloworld /var/lib/tftpboot/
```

<b>BeagleBone'da (seri konsol):</b>

![Linux'ta eth0'a IP verme ve tftp ile dosya çekme](../images/tftp_boot/12_linux_tftp.png)

```
ifconfig eth0 192.168.27.2 netmask 255.255.255.0 up
ping -c 2 192.168.27.1
cd /tmp
tftp -g -r helloworld 192.168.27.1
cat helloworld
```

| Komut / seçenek | Açıklama |
|---|---|
| `ifconfig eth0 ... up` | U-Boot'un IP ayarı kernel'e <b>geçmez</b>. Kernel ağ kartını sıfırdan başlatır, bu yüzden Linux'ta IP'yi her açılışta tekrar vermek gerekir. BusyBox'ta `ifconfig` vardır; `ip addr add 192.168.27.2/24 dev eth0` ve `ip link set eth0 up` da çalışır. |
| `tftp` | Tek başına yazarsan kullanım yardımını gösterir. |
| `-g` | get: sunucudan dosya al |
| `-r helloworld` | remote: sunucudaki dosya adı |
| `-l isim` | local: kartta farklı bir adla kaydet (isteğe bağlı) |
| `192.168.27.1` | TFTP sunucusunun IP'si |
| `-p -l dosya 192.168.27.1` | put: karttan host'a dosya gönder (`--create` ayarı sayesinde) |

> [!NOTE]
> initramfs RAM'de çalışır. Kartta oluşturduğun veya indirdiğin dosyalar <b>yeniden başlatınca kaybolur</b>.

---

## <a name="c8-88-challenge-her-kaynaktan-boot-edebilen-genel-uenvtxt"></a>8.8 Challenge: Her Kaynaktan Boot Edebilen Genel uEnv.txt

### <a name="c8-görev"></a>Görev

Tek bir `uEnv.txt` yazacağız. Bu dosya kaynakları sırayla deneyecek ve ilk çalışan kaynaktan boot edecek: <b>eMMC → SD → TFTP → NFS</b>. eMMC'de boot dosyaları yoksa SD karta, SD kart yoksa TFTP'ye geçecek.

### <a name="c8-çözüm-fikri"></a>Çözüm fikri

U-Boot'un komut satırı (hush) `if ... then ... fi` ve `&&` destekler. Komutların başarılı olup olmadığına göre karar verebiliriz:

- `load` dosyayı bulamazsa hata döner.
- `mmc rescan` kart yoksa hata döner.
- `tftpboot` dosya yoksa ya da sunucu cevap vermezse hata döner.
- `bootm` başarılı olursa <b>geri dönmez</b>, kernel çalışır. Başarısız olursa (bozuk imaj vb.) bir sonraki satıra geçilir.

Her kaynak için bir `try_...` makrosu yazıyoruz. Makro önce dosyaları yüklemeyi dener; yükleme başarılıysa `bootargs`'ı ayarlayıp `bootm` çalıştırır. Başarısızsa hiçbir şey yapmaz ve `uenvcmd` sıradaki makroya geçer:

```
uenvcmd
  ├─ try_emmc : eMMC'de uImage + dtb var mı? ─ evet → bootm (rootfs: eMMC p2)
  │                                          └ hayır ↓
  ├─ try_sd   : SD kart takılı ve imajlar var mı? ─ evet → bootm (rootfs: SD p2)
  │                                               └ hayır ↓
  ├─ try_tftp : TFTP'den uImage + dtb + initramfs ─ evet → bootm (rootfs: RAM)
  │                                               └ hayır ↓
  ├─ try_nfs  : TFTP'den uImage + dtb ─ evet → bootm (rootfs: NFS, host'ta)
  │                                   └ hayır ↓
  └─ "Hicbir kaynaktan boot edilemedi"
```

### <a name="c8-çözüm-uenvtxt"></a>Çözüm: `uEnv.txt`

Her değişken <b>tek satırda</b> olmalı. Bu çözümde varsayılan dosya düzeni şu: her MMC aygıtında 1. bölüm (FAT, BOOT) içinde `uImage` ve `am335x-boneblack.dtb`, 2. bölüm (ext4) rootfs.

```
console=ttyO0,115200n8
ipaddr=192.168.27.2
serverip=192.168.27.1
netretry=once
loadaddr=0x82000000
fdtaddr=0x88000000
initrdaddr=0x88080000
nfspath=/srv/nfs/bbb,nolock,wsize=1024,rsize=1024
mmc_load=mmc dev ${mmcnum} && mmc rescan && load mmc ${mmcnum}:1 ${loadaddr} uImage && load mmc ${mmcnum}:1 ${fdtaddr} am335x-boneblack.dtb
mmc_args=setenv bootargs console=${console} root=${mmcroot} rw rootwait
emmc_root=if mmc dev 0 && mmc rescan; then setenv mmcroot /dev/mmcblk1p2; else setenv mmcroot /dev/mmcblk0p2; fi
try_emmc=echo "[1/4] eMMC deneniyor ..."; setenv mmcnum 1; if run mmc_load; then run emmc_root; run mmc_args; bootm ${loadaddr} - ${fdtaddr}; fi
try_sd=echo "[2/4] SD kart deneniyor ..."; setenv mmcnum 0; if run mmc_load; then setenv mmcroot /dev/mmcblk0p2; run mmc_args; bootm ${loadaddr} - ${fdtaddr}; fi
net_load=tftpboot ${loadaddr} uImage && tftpboot ${fdtaddr} am335x-boneblack.dtb
try_tftp=echo "[3/4] TFTP (initramfs) deneniyor ..."; if run net_load && tftpboot ${initrdaddr} initramfs; then setenv bootargs console=${console} root=/dev/ram0 rw initrd=${initrdaddr}; bootm ${loadaddr} ${initrdaddr} ${fdtaddr}; fi
try_nfs=echo "[4/4] TFTP + NFS deneniyor ..."; if run net_load; then setenv bootargs console=${console} root=/dev/nfs rw nfsroot=${serverip}:${nfspath} ip=${ipaddr}:${serverip}::255.255.255.0::eth0:off rootwait; bootm ${loadaddr} - ${fdtaddr}; fi
uenvcmd=if test "${generic_tried}" != "yes"; then setenv generic_tried yes; setenv autoload no; run try_emmc; run try_sd; run try_tftp; run try_nfs; echo "!!! Hicbir kaynaktan boot edilemedi"; fi
```

### <a name="c8-satırların-açıklaması"></a>Satırların açıklaması

| Satır | Açıklama |
|---|---|
| `console`, `ipaddr`, `serverip`, `*addr` | Yol 2'deki ile aynı: konsol, IP'ler ve RAM adresleri |
| `netretry=once` | <b>Önemli.</b> Varsayılan olarak `tftpboot` sunucu cevap vermezse <b>sonsuza kadar</b> tekrar dener (`Retry count exceeded; starting again`). O zaman NFS adımına hiç geçilmez. `once` ile bir kere dener, olmazsa hata döner. |
| `nfspath` | NFS rootfs'in host'taki yolu ve NFS seçenekleri: `nolock` (kartta kilit servisi yok), `wsize/rsize=1024` (küçük paket boyutu, yavaş ama güvenilir) |
| `mmc_load` | Ortak MMC yükleyici. `${mmcnum}` hangi aygıt olduğunu söyler (`1` = eMMC, `0` = SD). Dört komut `&&` ile bağlı: biri başarısız olursa geri kalanlar çalışmaz ve makro hata döner. |
| `mmc_args` | MMC için `bootargs`. Rootfs, `${mmcroot}` ile belirtilen bölüm. |
| `emmc_root` | Kernel'de eMMC'nin adını bulur (aşağıdaki uyarıya bak). SD kart varsa eMMC `mmcblk1`, yoksa `mmcblk0` olur. |
| `try_emmc`, `try_sd` | `mmc_load` başarılıysa → `bootargs` ayarla → `bootm`. `-`: initramfs yok. |
| `net_load` | TFTP ile kernel + DTB. TFTP ve NFS adımları ortak kullanır. |
| `try_tftp` | Kernel + DTB + <b>initramfs</b>. Rootfs RAM'de (Yol 2 ile aynı). |
| `try_nfs` | Kernel + DTB TFTP'den gelir, rootfs NFS ile host'tan bağlanır. `ip=...` kernel'e kendi IP'sini verir; U-Boot'un IP'si kernel'e geçmediği için NFS'te şart. Bu adım, host'ta `initramfs` dosyası yoksa devreye girer. |
| `uenvcmd` | Makroları sırayla çağırır. `generic_tried` bir <b>koruma bayrağı</b>: U-Boot sürümüne göre varsayılan `bootcmd` önce SD'de, sonra eMMC'de `uEnv.txt` arayabilir, yani `uenvcmd` iki kez çalışabilir. Bayrak sayesinde zincir sadece bir kez denenir. |

> [!WARNING]
> <b>eMMC'nin kernel'deki adı değişebilir.</b> U-Boot'ta eMMC her zaman `mmc 1`'dir. Ama eski kernel'lerde (3.8.13 gibi) SD kart <b>takılı değilse</b> eMMC `mmcblk0` olarak görünür, takılıysa `mmcblk1` olarak görünür. `emmc_root` makrosu SD kartın olup olmadığına bakıp doğru adı seçer. Yeni kernel'lerde DTB'deki `aliases` ile bu sabitlenebilir.

### <a name="c8-dosya-nereye-konur"></a>Dosya nereye konur?

Burada da bir tavuk-yumurta durumu var: `uEnv.txt`'nin kendisi yerel bir depolamada olmalı. U-Boot onu önce SD'de (`mmcdev 0`), bulamazsa eMMC'de (`mmcdev 1`) arar.

| Senaryo | `uEnv.txt` nerede olmalı? |
|---|---|
| SD kart her zaman takılı | SD kartın 1. bölümü (BOOT) yeterli |
| "SD kart yoksa TFTP'ye geç" durumu da çalışsın | <b>eMMC'nin 1. bölümüne de</b> aynı dosyayı koy |

En güvenlisi aynı `uEnv.txt`'yi hem SD'nin hem eMMC'nin BOOT bölümüne koymak.

### <a name="c8-örnek-açılış-emmcde-imaj-yok-sd-kart-takılı-değil"></a>Örnek açılış: eMMC'de imaj yok, SD kart takılı değil

![Genel uEnv.txt: eMMC ve SD başarısız, TFTP'den açılış](../images/tftp_boot/17_generic_fallback.png)

### <a name="c8-nasıl-test-edilir"></a>Nasıl test edilir?

Her satırda tek bir şeyi değiştirip kartı yeniden başlat. Hangi `[n/4]` satırından sonra `Starting kernel ...` geldiğine bak.

| Test | Ne yaparsın? | Beklenen |
|---|---|---|
| 1 | Her şey yerinde | `[1/4] eMMC` → boot |
| 2 | eMMC'deki `uImage`'ın adını değiştir (`mv uImage uImage.bak`) | eMMC başarısız → `[2/4] SD` → boot |
| 3 | SD kartı çıkar (`uEnv.txt` eMMC'de olmalı) | eMMC, SD başarısız → `[3/4] TFTP` → boot |
| 4 | Host'ta `/var/lib/tftpboot/initramfs`'i taşı | ... → `[4/4] NFS` → boot (NFS sunucusu kurulu olmalı) |
| 5 | Ethernet kablosunu da çıkar | `!!! Hicbir kaynaktan boot edilemedi`, U-Boot komut satırı |

Bir adımı elle denemek istersen U-Boot'u durdurup `uEnv.txt`'yi yükle (`run loadbootenv; run importbootenv`), sonra makroları tek tek çalıştır: `run try_sd`, `printenv bootargs` gibi.

### <a name="c8-sınırlamalar"></a>Sınırlamalar

- Bu zincir sadece <b>U-Boot aşamasındaki</b> hataları yakalar (dosya yok, kart yok, sunucu yok). Kernel açılıp sonra panic verirse (yanlış rootfs vb.) U-Boot'a geri dönülmez.
- `MLO` ve `u-boot.img` yine eMMC'de ya da SD'de olmalı. ROM Code BBB'de ağdan boot edemez ([8.2](#c8-82-neden-bütün-dosyalar-tftp-ile-gönderilmiyor)).
- `uEnv.txt` içindeki U-Boot `echo` mesajlarında Türkçe karakter kullanma; seri konsolda bozuk görünebilir.

---

## <a name="c8-89-özet"></a>8.9 Özet

- Host: `tftpd-hpa` kur, `/var/lib/tftpboot`'u hazırla, Ethernet arayüzüne `192.168.27.1` ver, dosyaları kopyala.
- SD kart: sadece `MLO`, `u-boot.img`, `uEnv.txt`. Kernel, DTB ve initramfs ağdan gelir.
- U-Boot: `setenv ipaddr` / `serverip` → `ping` → `tftpboot` (3 dosya) → `setenv bootargs` → `bootm kernel initrd dtb`.
- Bu komutları `uEnv.txt`'deki `uenvcmd`'ye yazarsan açılış otomatik olur; geliştirme döngüsü "dosyayı kopyala, reset'e bas"a iner.
- U-Boot'taki IP ayarı kernel'e geçmez; Linux'ta `eth0`'a IP'yi yeniden ver.

## <a name="c8-810-karşılaşılabilecek-problemler"></a>8.10 Karşılaşılabilecek Problemler

![Sık görülen TFTP hataları (temsili)](../images/tftp_boot/13_hatalar.png)

| Hata | Sebep | Çözüm |
|---|---|---|
| `*** ERROR: 'serverip' not set` | Sunucu IP'si tanımlı değil | `setenv serverip 192.168.27.1` |
| `Using usb_ether device` | U-Boot USB ağını kullanmaya çalışıyor | `setenv ethact ethernet@4a100000` (eski U-Boot'larda `setenv ethact cpsw`) |
| `Loading: T T T T ...` / `Retry count exceeded` | Paket gidiyor ama cevap gelmiyor | Host IP'si ve alt ağ doğru mu? `systemctl status tftpd-hpa` çalışıyor mu? Firewall (`sudo ufw allow 69/udp`)? VM ise Bridged mi? Sunucu port 69'da mı? |
| `TFTP error: 'File not found' (1)` | Dosya `/var/lib/tftpboot` içinde değil ya da adı yanlış | `ls -l /var/lib/tftpboot`. Linux'ta büyük-küçük harf farklıdır: `uImage` ≠ `uimage` |
| `TFTP error: 'Permission denied'` | Dosya okunamıyor | `sudo chmod -R 777 /var/lib/tftpboot` |
| `ping failed; host ... is not alive` | Host'un o arayüzde IP'si yok / kablo takılı değil | `ip -br a` ile kontrol et, Ethernet ışıklarına bak |
| Kart U-Boot'a gelmeden eMMC'den açılıyor | S2'ye basılmadı | Güç verirken S2'yi basılı tut |
| Kart SD'den hiç açılmıyor | SPL dosyasının adı yanlış / BOOT bölümü FAT değil | Dosya adı `MLO` olmalı; 1. bölüm FAT ve boot bayrağı açık olmalı |
| `bootm` sonrası `Wrong Ramdisk Image Format` | initramfs'te U-Boot başlığı yok | `mkimage -A arm -T ramdisk -C gzip -d initramfs.cpio.gz initramfs` ([7.9 (g)](#c7-g-bootm-hataları)) |
| `## Error: "loadfromtftp" not defined` | `uenvcmd` içinde çağrılan makro adı, tanımlanan adla aynı değil | `uEnv.txt`'de iki adı birebir aynı yaz |
| `Running uenvcmd ...` hiç çıkmıyor | `uEnv.txt` okunmadı: BOOT bölümünde değil, adı yanlış (`uenv.txt`) veya kart eMMC'den açıldı | Dosyayı 1. bölüme koy, S2'ye basılı tutarak aç |
| `Starting kernel ...` sonrası ekran boş | `bootargs` ayarlanmamış (ör. `booargs` yazım hatası) ya da `console` yanlış | U-Boot'ta `printenv bootargs` ile kontrol et |


<div class="page-break"></div>

# <a name="c9-bölüm-9--cross-toolchain-spl-ve-u-boot-derleme"></a>Bölüm 9 — Cross Toolchain, SPL ve U-Boot Derleme

> <b>Bu bölümde:</b>
> - Cross compile'ın ne olduğunu ve neden gerektiğini öğreneceksin.
> - Linaro cross toolchain'ini kurup `PATH`'e ekleyeceksin.
> - U-Boot 2022.04 kaynağını indirip BeagleBone Black için yapılandıracak ve derleyeceksin: `MLO`, `u-boot-spl.bin`, `u-boot.img`.
> - Kendi derlediğin U-Boot ile kartı açacaksın.
> - Challenge: U-Boot'un açılıştaki bekleme süresini kaynak koddan 10 saniyeye çıkaracaksın.
>
> <b>Ön koşul:</b> [Bölüm 3](#c3-bölüm-3--linux-boot-süreci-rbl--spl--u-boot) — SPL ve U-Boot'un görevleri, [Bölüm 4](#c4-bölüm-4--sd-karttan-boot) — SD karta dosya koyma.

---

## <a name="c9-91-bu-bölümde-neden-toolchain-kuruyoruz"></a>9.1 Bu Bölümde Neden Toolchain Kuruyoruz?

Şimdiye kadar kullandığımız `MLO`, `u-boot.img`, `uImage` hazır dosyalardı. Bu bölümde <b>SPL ve U-Boot'u kaynak koddan kendimiz derleyeceğiz</b>. Bunun için ARM kodu üretebilen bir derleyiciye ihtiyacımız var.

| | Host PC | BeagleBone Black |
|---|---|---|
| İşlemci | x86_64 (Intel/AMD) | ARM Cortex-A8 (AM335x) |
| Komut seti | x86 makine kodu | ARM makine kodu |

Ubuntu'daki `gcc` x86 için kod üretir. Onunla derlenen U-Boot'u ROM Code yükler ama ARM işlemci çalıştıramaz.

> <b>Cross compile:</b> Bir mimaride (x86) çalışıp <b>başka bir mimari</b> (ARM) için çalıştırılabilir kod üretmek. Bunu yapan derleyici ve yardımcı araçların toplamına <b>cross toolchain</b> denir.

<b>Neden kartın üzerinde derlemiyoruz?</b>
- Kart yavaş ve RAM'i az. U-Boot dakikalar, kernel saatler sürer.
- Tavuk-yumurta: kartta derleme yapmak için önce çalışan bir Linux gerekir. O Linux'u açacak olan da derleyeceğimiz U-Boot.

### <a name="c9-toolchainin-içinde-ne-var"></a>Toolchain'in içinde ne var?

| Araç | Görevi |
|---|---|
| `arm-linux-gnueabihf-gcc` | C kodunu ARM assembly'ye çevirir |
| `arm-linux-gnueabihf-as` | Assembly'yi makine koduna çevirir (binutils) |
| `arm-linux-gnueabihf-ld` | Parçaları birleştirir; kodu linker script'e göre SRAM/DDR adreslerine yerleştirir |
| `arm-linux-gnueabihf-objcopy` | ELF dosyasından ham binary üretir (`u-boot.bin`, `u-boot-spl.bin`) |
| glibc ve kütüphaneler | Kernel ve kullanıcı programları için. U-Boot kullanmaz. |
| `arm-linux-gnueabihf-gdb` | Hata ayıklama |

<b>İsimdeki önek (`arm-linux-gnueabihf-`):</b>

| Parça | Anlamı |
|---|---|
| `arm` | Hedef mimari |
| `linux` | Hedef işletim sistemi: Linux üzerinde çalışacak programlar |
| `gnueabi` | GNU ABI (Application Binary Interface) |
| `hf` | <b>h</b>ard-<b>f</b>loat: ondalıklı sayı işlemleri donanımdaki FPU ile yapılır (Cortex-A8'de FPU var) |

### <a name="c9-neden-u-boot-bölümünde-anlatılıyor"></a>Neden U-Boot bölümünde anlatılıyor?

U-Boot, kitapta <b>derlediğimiz ilk parça</b>. Toolchain burada bir kere kuruluyor ve sonraki her aşamada aynısı kullanılıyor:

```
cross toolchain ──┬── SPL + U-Boot          (bu bölüm)
                  ├── Linux kernel + DTB     (uImage, am335x-boneblack.dtb)
                  ├── BusyBox / rootfs / initramfs
                  └── kendi uygulamaların ve sürücülerin
```

> [!NOTE]
> U-Boot "bare-metal" çalışır: altında işletim sistemi yoktur ve glibc kullanmaz. Teknik olarak `arm-none-eabi-` (işletim sistemi olmayan) toolchain ile de derlenebilir. `arm-linux-gnueabihf-` seçilmesinin sebebi, aynı toolchain'in kernel ve kullanıcı programları için de gerekli olması. Tek toolchain her şeye yetiyor.

---

## <a name="c9-92-sürüm-uyumu-hangi-toolchain"></a>9.2 Sürüm Uyumu: Hangi Toolchain?

En çok sorun çıkaran konu bu. <b>Eski U-Boot/kernel kaynağını yeni GCC ile derlemek çoğu zaman hata verir.</b> Toolchain'i derleyeceğin kaynağın yaşına göre seç:

| Derlenecek kaynak | Uygun toolchain | Nasıl kurulur? |
|---|---|---|
| U-Boot 2013.x, kernel 3.8 | GCC 4.x (ör. Linaro 4.9-2014.09) | Linaro arşivinden indir |
| U-Boot 2016.x – 2022.x, kernel 4.x | GCC 6 / 7 (ör. Linaro 6.5, 7.5) | Linaro'dan indir (aşağıda) |
| U-Boot 2023+, kernel 5.x / 6.x | Güncel GCC | `sudo apt install gcc-arm-linux-gnueabihf` |

> [!IMPORTANT]
> Bu bölümde kursun videolarında kullanılan <b>U-Boot 2022.04 + Linaro GCC 7.5.0</b> kullanılıyor ([9.3](#c9-93-adım-adım-toolchain-kurulumu-ve-u-boot-derleme) Adım 4'teki menuconfig ekranında görünüyor). Başka sürüm kullanırsan komutlarda sadece sürüm numaraları değişir, adımlar aynıdır.

> [!NOTE]
> Kursun GitHub reposundaki eski derleme notları (`notes/compilation_commands`) Linaro GCC 6.3.1 ve `am335x_boneblack_defconfig` kullanıyor. Bu, kursun 2017 sürümüne ait; güncellenen videolarda U-Boot 2022.04 kullanılıyor. Bu kitap videolardaki güncel sürümü takip ediyor.

İndirme adresleri:

| Dosya | Adres |
|---|---|
| Linaro GCC 7.5 | `https://releases.linaro.org/components/toolchain/binaries/7.5-2019.12/arm-linux-gnueabihf/` |
| Linaro GCC 6.5 | `https://releases.linaro.org/components/toolchain/binaries/6.5-2018.12/arm-linux-gnueabihf/` |
| Linaro GCC 4.9 | `https://releases.linaro.org/archive/14.09/components/toolchain/binaries/` |
| U-Boot kaynakları | `https://ftp.denx.de/pub/u-boot/` |

---

## <a name="c9-93-adım-adım-toolchain-kurulumu-ve-u-boot-derleme"></a>9.3 Adım Adım: Toolchain Kurulumu ve U-Boot Derleme

> [!NOTE]
> Aşağıdaki ekran görüntüleri <b>temsilidir</b>; sürüm, tarih ve boyut değerleri senin ortamında farklı olacaktır. Örneklerde çalışma klasörü `~/bbb`.

### <a name="c9-adım-1--cross-toolchaini-kur"></a>Adım 1 — Cross toolchain'i kur

Linaro toolchain hazır derlenmiş bir arşiv olarak gelir. İndirip açman ve `bin` klasörünü `PATH`'e eklemen yeterli:

![Linaro toolchain indirme, açma ve PATH'e ekleme](../images/uboot_build/01_toolchain_install.png)

```bash
cd ~/bbb
wget https://releases.linaro.org/components/toolchain/binaries/7.5-2019.12/arm-linux-gnueabihf/gcc-linaro-7.5.0-2019.12-x86_64_arm-linux-gnueabihf.tar.xz
tar -xf gcc-linaro-7.5.0-2019.12-x86_64_arm-linux-gnueabihf.tar.xz
echo 'export PATH=$HOME/bbb/gcc-linaro-7.5.0-2019.12-x86_64_arm-linux-gnueabihf/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
arm-linux-gnueabihf-gcc --version
```

`~/.bashrc`'ye eklediğimiz için her yeni terminalde `PATH` hazır olur.

> [!TIP]
> Güncel U-Boot (2023+) derleyeceksen indirmeye gerek yok: `sudo apt install gcc-arm-linux-gnueabihf` yeterli. Bu paket `/usr/bin`'e kurulur, `PATH` ayarı gerekmez.

### <a name="c9-adım-2--i̇steğe-bağlı-cross-compileı-kendi-gözünle-gör"></a>Adım 2 — (İsteğe bağlı) Cross compile'ı kendi gözünle gör

Aynı C dosyasını iki derleyiciyle derleyip `file` ile karşılaştır:

![Aynı kodun x86 ve ARM için derlenmesi](../images/uboot_build/02_cross_compile_demo.png)

```bash
gcc hello.c -o hello_x86
arm-linux-gnueabihf-gcc hello.c -o hello_arm
file hello_x86 hello_arm
./hello_arm          # Exec format error: PC ARM kodu çalıştıramaz
```

`hello_arm` dosyasını karta kopyalarsan orada çalışır. U-Boot da aynı şekilde: PC'de derlenir, kartta çalışır. [6.6.3](#c6-663-a-bilgisayardan-ulaşmak)'te rootfs'teki programların PC'de çalışmamasının sebebi de budur.

### <a name="c9-adım-3--host-paketlerini-kur-ve-u-boot-kaynağını-indir"></a>Adım 3 — Host paketlerini kur ve U-Boot kaynağını indir

U-Boot derlenirken bazı yardımcı programlar (`mkimage`, `kconfig` vb.) <b>PC için</b> derlenip çalıştırılır. Bu yüzden host'ta da bazı paketler gerekir:

![Host paketleri ve U-Boot kaynağını indirme](../images/uboot_build/03_uboot_source.png)

```bash
sudo apt install build-essential bison flex libssl-dev device-tree-compiler \
     u-boot-tools bc lzop libncurses-dev libgnutls28-dev
wget https://ftp.denx.de/pub/u-boot/u-boot-2022.04.tar.bz2
tar -xjf u-boot-2022.04.tar.bz2
cd u-boot-2022.04
ls configs | grep am335x
```

| Paket | Neden? |
|---|---|
| `build-essential` | Host'un kendi `gcc`'si ve `make` (yardımcı araçlar için) |
| `bison`, `flex` | Kconfig ve dtc ayrıştırıcıları |
| `libssl-dev`, `libgnutls28-dev` | `mkimage` ve diğer host araçlarının imza/özet özellikleri |
| `device-tree-compiler` | `dtc`: U-Boot'un kendi device tree'si için |
| `libncurses-dev` | `make menuconfig` menüsü |
| `u-boot-tools` | Hazır `mkimage` (kernel/initramfs'e başlık eklemek için) |

> [!TIP]
> `git clone https://source.denx.de/u-boot/u-boot.git` ve ardından `git checkout v2022.04` ile de alabilirsin. Kaynağı değiştirip deneyeceksen git daha kullanışlı, çünkü `git diff` ile ne değiştirdiğini görürsün.

### <a name="c9-adım-4--bbb-için-yapılandır"></a>Adım 4 — BBB için yapılandır

`configs/` klasöründe her kart için hazır bir ayar dosyası (`defconfig`) bulunur. Önce eski derleme kalıntılarını temizle, sonra BBB'nin ayarını yükle:

![distclean ve defconfig](../images/uboot_build/04_uboot_config.png)

```bash
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- distclean
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- am335x_evm_defconfig
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- menuconfig     # isteğe bağlı
```

| Parça | Anlamı |
|---|---|
| `ARCH=arm` | Hedef mimari: `arch/arm/` altındaki kodlar kullanılır |
| `CROSS_COMPILE=arm-linux-gnueabihf-` | Makefile'daki `gcc`, `ld`, `objcopy` komutlarının <b>başına eklenir</b>. `gcc` yerine `arm-linux-gnueabihf-gcc` çalışır. Sondaki `-` önemli. |
| `distclean` | Önceki derlemeden kalan her şeyi (`.config` dahil) siler |
| `am335x_evm_defconfig` | BBB'nin hazır ayarlarını `.config` dosyasına yazar |
| `menuconfig` | `.config`'i menüden düzenler (ör. `bootdelay`, komutlar) |

> [!NOTE]
> Ayar adı sürüme göre değişir: U-Boot 2013.10'da `am335x_evm_config`, 2017–2019 arası `am335x_boneblack_defconfig`, 2020 ve sonrası `am335x_evm_defconfig`. Bu sonuncusu tek bir SPL/U-Boot ile BBB, Bone, Bone Green, PocketBeagle ve EVM kartlarını kapsar; U-Boot açılırken kartın EEPROM'unu okuyup doğru DTB'yi seçer. Doğru adı `ls configs | grep am335x` ile bul.

#### <a name="c9-menuconfig-ekranı"></a>`menuconfig` ekranı

`make ... menuconfig` komutu aşağıdaki menüyü açar (kursun ekran görüntüsü). İsteğe bağlı bir adım; hiçbir şeyi değiştirmeden `Exit` ile çıkabilirsin.

![U-Boot menuconfig ekranı](../images/{F68E97EF-71C8-47C1-AB23-8CEC39146A69}.png)

| Ekranda | Anlamı |
|---|---|
| `U-Boot 2022.04 Configuration` | Derlenen U-Boot sürümü. Başka sürüm indirdiysen burada o yazar. |
| `*** Compiler: arm-linux-gnueabihf-gcc (Linaro GCC 7.5-2019.12) 7.5.0 ***` | `CROSS_COMPILE` ile verdiğin derleyici. <b>Toolchain'in doğru bulunduğunu buradan anlarsın.</b> Burada Ubuntu'nun `gcc`'si görünüyorsa `CROSS_COMPILE` yazılmamış ya da `PATH` yanlış demektir. |
| `Architecture select (ARM architecture)` | `ARCH=arm` ve defconfig'in seçtiği mimari |
| `[*]` / `[ ]` | Seçili (U-Boot'a dahil) / seçili değil. <b>Boşluk</b> tuşu ile değiştirilir. |
| `--->` | Alt menü, <b>Enter</b> ile girilir |
| `v(+)` | Listenin devamı var, aşağı ok ile kaydır |
| `<Save>` / `<Exit>` | Değişiklikleri `.config`'e yazar / çıkar (değişiklik varsa kaydetmek ister) |
| `/` | Ayar arama (ör. `BOOTDELAY`) |

Kursta sık bakılan yerler: <b>Boot options</b> (`bootdelay`, `bootcmd`), <b>Command line interface</b> (hangi U-Boot komutlarının derleneceği), <b>Environment</b> (ortam değişkenlerinin nereye kaydedileceği).

### <a name="c9-adım-5--derle"></a>Adım 5 — Derle

![U-Boot derleme çıktısı: MLO, u-boot-spl.bin, u-boot.img](../images/uboot_build/05_uboot_build.png)

```bash
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- -j4
ls -l MLO u-boot.img spl/u-boot-spl.bin
file spl/u-boot-spl u-boot
```

`-j4`: 4 iş parçacığıyla paralel derle (çekirdek sayına göre artırabilirsin, `nproc` ile öğren).

Derleme sonunda çıkan dosyalar:

| Dosya | Ne işe yarar? | Nerede kullandık? |
|---|---|---|
| `MLO` | SPL + başında <b>GP başlığı</b> (ROM Code'un okuyacağı yükleme adresi ve boyut) | SD kart / eMMC BOOT bölümü ([Bölüm 4](#c4-bölüm-4--sd-karttan-boot)) |
| `spl/u-boot-spl.bin` | Başlıksız ham SPL | Seri (UART) boot, Xmodem ile ([Bölüm 7](#c7-bölüm-7--seri-porttan-uart-boot)) |
| `u-boot.img` | Tam U-Boot + U-Boot başlığı (SPL bunu okur) | SD kart, seri boot (Ymodem) |
| `u-boot`, `spl/u-boot-spl` | ELF dosyaları (sembollü) | Hata ayıklama (`gdb`) |

`file` çıktısındaki <b>ARM, EABI5</b> ifadesi dosyanın gerçekten ARM için derlendiğini gösterir.

> [!IMPORTANT]
> `MLO` <b>109 KB'tan küçük</b> olmalı. ROM Code onu AM335x'in dahili SRAM'ine koyar ve SRAM'de daha fazla yer yok. U-Boot'a çok özellik eklersen SPL büyüyebilir; o zaman SPL ayarlarından gereksiz özellikleri kapatmak gerekir.

### <a name="c9-adım-6--sd-karta-kopyala"></a>Adım 6 — SD karta kopyala

![MLO ve u-boot.img'yi SD kartın BOOT bölümüne kopyalama](../images/uboot_build/06_copy_sd.png)

```bash
cp MLO u-boot.img /media/$USER/BOOT/
sync && sudo umount /media/$USER/BOOT
```

Seri boot için ise `spl/u-boot-spl.bin` ve `u-boot.img` dosyalarını kullan ([Bölüm 7](#c7-bölüm-7--seri-porttan-uart-boot)).

### <a name="c9-adım-7--kartta-doğrula"></a>Adım 7 — Kartta doğrula

Kartı S2'ye basılı tutarak aç. İlk satırlardaki <b>tarih ve saat senin derleme zamanın</b> olmalı:

![Kendi derlediğin U-Boot'un açılışı](../images/uboot_build/07_new_uboot_boot.png)

```
=> version
```

> [!NOTE]
> Yeni U-Boot sürümlerinde komut satırı `U-Boot#` yerine `=>` olarak görünür. Önceki bölümlerdeki komutlar aynı şekilde çalışır.
>
> Bir fark var: Ethernet aygıtının adı değişti. Kursun hazır U-Boot'unda (2013.04) `cpsw` olan aygıt 2022.04'te `ethernet@4a100000` olarak görünür (`Net:` satırına bak). TFTP bölümündeki `setenv ethact cpsw` yerine `setenv ethact ethernet@4a100000` yazman gerekir ([8.5](#c8-85-yol-1--komutları-elle-yazarak-tftp-ile-boot)). Çoğu zaman varsayılan zaten doğrudur, emin olmak için `printenv ethact` ile bak.

### <a name="c9-komutların-kısa-özeti"></a>Komutların kısa özeti

```bash
# Toolchain (bir kere)
wget https://releases.linaro.org/components/toolchain/binaries/7.5-2019.12/arm-linux-gnueabihf/gcc-linaro-7.5.0-2019.12-x86_64_arm-linux-gnueabihf.tar.xz
tar -xf gcc-linaro-7.5.0-2019.12-x86_64_arm-linux-gnueabihf.tar.xz
echo 'export PATH=$HOME/bbb/gcc-linaro-7.5.0-2019.12-x86_64_arm-linux-gnueabihf/bin:$PATH' >> ~/.bashrc
source ~/.bashrc

# U-Boot
sudo apt install build-essential bison flex libssl-dev device-tree-compiler u-boot-tools bc lzop libncurses-dev libgnutls28-dev
wget https://ftp.denx.de/pub/u-boot/u-boot-2022.04.tar.bz2 && tar -xjf u-boot-2022.04.tar.bz2 && cd u-boot-2022.04
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- distclean
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- am335x_evm_defconfig
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- -j4
cp MLO u-boot.img /media/$USER/BOOT/ && sync
```

---

## <a name="c9-94-challenge-autoboot-bekleme-süresini-10-saniyeye-çıkarmak"></a>9.4 Challenge: Autoboot Bekleme Süresini 10 Saniyeye Çıkarmak

### <a name="c9-görev"></a>Görev

Kursun bu bölümdeki challenge'ı:

> <i>U-Boot açılınca otomatik açılışa (uEnv.txt'yi okuma, uImage'ı yükleme...) geçmeden önce birkaç saniye bekler. Bu sürede bir tuşa basarsan U-Boot komut satırına düşersin. Bu bekleme süresini <b>10 saniyeye</b> çıkar ve kartta test et. Bunun için U-Boot <b>kaynak kodunu</b> değiştirip yeniden derlemen gerekiyor.</i>

### <a name="c9-bekleme-süresi-nereden-geliyor"></a>Bekleme süresi nereden geliyor?

Geri sayımı `bootdelay` ortam değişkeni belirler. Bu değişkenin <b>varsayılan</b> değeri derleme sırasında `CONFIG_BOOTDELAY` ayarından gelir ve U-Boot'un içine gömülür:

| Kaynak | Değer |
|---|---|
| U-Boot 2022.04 varsayılanı (`am335x_evm_defconfig` değiştirmiyor) | 2 saniye |
| Kursun güncel `SD-boot` U-Boot'u | 0 (geri sayım yok, tuşa basılı tutmak gerekir) |
| Kursun eski videolarındaki U-Boot | 5 saniye |

> [!NOTE]
> `setenv bootdelay 10` + `saveenv` ile de aynı sonuç alınır. Ama bu sadece o kartın kayıtlı ortamını değiştirir; challenge, ayarın <b>U-Boot imajının kendisinde</b> değişmesini istiyor. Böylece imajı hangi karta koyarsan koy 10 saniye bekler.

### <a name="c9-çözüm"></a>Çözüm

<b>1) Ayarı değiştir.</b> [9.3](#c9-93-adım-adım-toolchain-kurulumu-ve-u-boot-derleme)'teki U-Boot kaynak klasöründe `menuconfig`'i aç ve şu ayarı `10` yap:

```
Boot options  --->
    Autoboot options  --->
        (10) delay in seconds before automatically booting
```

Ayarı bulmak için menüde `/` tuşuna basıp `BOOTDELAY` aramak daha hızlı. Kaydedip çık.

<b>2) Kontrol et, derle, SD karta kopyala.</b>

![bootdelay ayarını değiştirip derleme](../images/uboot_build/09_bootdelay_config.png)

```bash
grep BOOTDELAY .config                                   # CONFIG_BOOTDELAY=10 görmelisin
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- -j4
cp MLO u-boot.img /media/$USER/BOOT/ && sync && sudo umount /media/$USER/BOOT
```

<b>3) Kartta test et.</b> Kartı S2'ye basılı tutarak aç. Geri sayım 10'dan başlamalı:

![10 saniyelik geri sayım](../images/uboot_build/10_bootdelay_boot.png)

> [!IMPORTANT]
> Geri sayım hâlâ eski değerdeyse, kartta daha önce `saveenv` ile kaydedilmiş bir ortam vardır. Kayıtlı ortam derlemedeki varsayılanı ezer. U-Boot'ta `env default -a` ile varsayılanlara dön ve `saveenv` ile kaydet. Ayrıca `uEnv.txt`'de `bootdelay=` satırı olmadığından emin ol.

> [!TIP]
> Değişikliğin kaynak kodda kalıcı olmasını istersen `make savedefconfig` ile küçük bir `defconfig` dosyası üret ve onu `configs/` altına kendi adınla kaydet (ör. `configs/my_bbb_defconfig`). Sonraki derlemelerde `make my_bbb_defconfig` yeterli olur.

## <a name="c9-95-özet"></a>9.5 Özet

- Cross toolchain, PC'de (x86) çalışıp ARM kodu üretir. Önek: `arm-linux-gnueabihf-`.
- Toolchain'i derlenecek kaynağın yaşına göre seç; eski kaynak + yeni GCC = derleme hatası.
- Derleme üç komut: `distclean` → `am335x_evm_defconfig` → `make -j4`. Hepsinde `ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf-`.
- Çıktılar: `MLO` (SD/eMMC için), `spl/u-boot-spl.bin` (seri boot için), `u-boot.img` (ikisi için de).
- Kendi U-Boot'unun çalıştığını açılıştaki derleme tarihinden anlarsın.
- U-Boot'un davranışını değiştirmenin kalıcı yolu `menuconfig` ile `.config`'i değiştirip yeniden derlemektir (ör. `CONFIG_BOOTDELAY`).

## <a name="c9-96-karşılaşılabilecek-problemler"></a>9.6 Karşılaşılabilecek Problemler

![Sık görülen derleme hataları (temsili)](../images/uboot_build/08_errors.png)

| Hata | Sebep | Çözüm |
|---|---|---|
| `arm-linux-gnueabihf-gcc: not found` | Toolchain `PATH`'te değil | `echo $PATH` ile kontrol et, `source ~/.bashrc` çalıştır, yolu doğru yazdığından emin ol |
| `fatal error: linux/compiler-gccN.h: No such file or directory` | GCC, U-Boot/kernel kaynağından <b>daha yeni</b>. Eski kaynaklar sadece tanıdıkları GCC sürümleri için başlık dosyası içerir. | [9.2](#c9-92-sürüm-uyumu-hangi-toolchain)'deki tablodan kaynağa uygun toolchain'i kullan |
| `multiple definition of 'yylloc'` | Eski kaynaktaki `dtc` + host'ta GCC 10 veya üstü | `scripts/dtc/dtc-lexer.l` (veya `.lex.c_shipped`) içinde `YYLTYPE yylloc;` satırını `extern YYLTYPE yylloc;` yap |
| `openssl/evp.h: No such file` | `libssl-dev` kurulu değil | `sudo apt install libssl-dev` |
| `bison: not found` / `flex: not found` | Host paketleri eksik | `sudo apt install bison flex` |
| `Your dtc is too old` | Host'taki `dtc` eski | `sudo apt install device-tree-compiler` |
| `*** Can't find default configuration "..."` | Yanlış `defconfig` adı | `ls configs \| grep am335x` |
| 32-bit Linaro 4.x toolchain çalışmıyor: `arm-linux-gnueabihf-gcc: No such file or directory` (dosya varken) | Eski toolchain 32-bit, 64-bit Ubuntu'da 32-bit kütüphaneler eksik | `sudo dpkg --add-architecture i386 && sudo apt update && sudo apt install libc6:i386 libstdc++6:i386 zlib1g:i386` |
| Kart açılıyor ama ekranda eski U-Boot tarihi var | Kart eMMC'den açıldı ya da SD'ye kopyalanan dosyalar eski | S2'ye basılı tutarak aç, `ls -l /media/$USER/BOOT` ile tarihleri kontrol et |
| SPL hiç çalışmıyor | `MLO` yerine `u-boot-spl.bin` kopyalandı ya da `MLO` çok büyük | SD karta `MLO` koy, boyutunu kontrol et (< 109 KB) |


<div class="page-break"></div>

<div class="part-title">Kısım IV<br>Linux Kernel</div>

<div class="page-break"></div>

# <a name="c10-bölüm-10--linux-kernel-kaynak-ağacı-ve-derleme"></a>Bölüm 10 — Linux Kernel: Kaynak Ağacı ve Derleme

> <b>Bu bölümde:</b>
> - BeagleBone Black için hangi kernel kaynağının kullanıldığını ve kursun kernel sürüm geçmişini öğreneceksin.
> - Kernel kaynak ağacında gezinmeyi öğreneceksin: ARM mimarisi kodu, kart yapılandırma dosyaları ve SoC sürücüleri nerede durur?
> - Kernel'i `bb.org_defconfig` ile yapılandırıp `uImage`, `am335x-boneblack.dtb` ve modülleri derleyeceksin.
> - Kendi derlediğin kernel ile kartı açacaksın.
>
> <b>Ön koşul:</b> [Bölüm 3](#c3-bölüm-3--linux-boot-süreci-rbl--spl--u-boot) — boot zinciri, [Bölüm 9](#c9-bölüm-9--cross-toolchain-spl-ve-u-boot-derleme) — cross toolchain kurulumu.

---

## <a name="c10-101-hangi-kernel"></a>10.1 Hangi Kernel?

Linux kernel'in "resmi" kaynağı Linus Torvalds'ın yönettiği <b>mainline</b> ağaçtır (kernel.org). Kart üreticileri bunun üzerine kendi kartlarına özel yamaları ekleyip <b>vendor</b> ağaçları yayınlar. BeagleBone Black için iki seçenek var:

| Kaynak | Adres | Ne zaman? |
|---|---|---|
| <b>BeagleBoard kernel'i</b> (vendor) | `https://github.com/beagleboard/linux.git` | Kursta ve bu kitapta kullanılan. BBB'ye özel ayar (`bb.org_defconfig`), cape ve PRU desteği hazır gelir. |
| <b>Mainline</b> | `https://git.kernel.org` | En yeni özellikler. BBB'de temel donanım çalışır, bazı ekstralar eksik olabilir. |

Kursun kullandığı kernel sürümleri zamanla değişti:

| Nerede? | Kernel |
|---|---|
| Kursun ilk hazır imajları (Ångström) | 3.8.13 |
| Kursun eski derleme notları | 4.4 (`bb.org_defconfig`) ve 4.11 (`omap2plus_defconfig`) |
| <b>Kursun güncel imajları</b> | <b>5.10.168</b> |

Kursun başındaki "Important Update on Linux Kernel Version" notu bu güncellemeyi anlatıyor. Bu kitap BeagleBoard'un <b>5.10</b> dalını kullanıyor. 5.10 bir <b>LTS</b> (Long Term Support, uzun süre desteklenen) sürümdür.

> [!NOTE]
> Dal (branch) zamanla güncellenir. Bu kitap yazılırken `5.10` dalının ucu <b>5.10.162</b> sürümündeydi. Kursun hazır imajı 5.10.168. Aradaki fark sadece küçük düzeltmelerdir, anlatılan her şey ikisinde de aynıdır.

---

## <a name="c10-102-kaynak-kodu-i̇ndirme"></a>10.2 Kaynak Kodu İndirme

```bash
cd ~/bbb
git clone --depth=1 -b 5.10 https://github.com/beagleboard/linux.git
cd linux
head -4 Makefile
```

![Kernel kaynağını git ile indirme](../images/kernel/01_clone.png)

| Parça | Anlamı |
|---|---|
| `--depth=1` | Sadece son sürümü indir, binlerce commit'lik geçmişi indirme. İndirme birkaç GB yerine birkaç yüz MB olur. |
| `-b 5.10` | `5.10` dalını al |
| `Makefile` başı | `VERSION`, `PATCHLEVEL`, `SUBLEVEL` satırları indirdiğin sürümü gösterir |

> [!TIP]
> Kaynak kodda bir fonksiyonun ya da sürücünün nerede tanımlandığını bulmak için tarayıcıdan <b>Elixir</b>'i kullan: <https://elixir.bootlin.com/linux/v5.10/source>. Her sembole tıklayınca tanımına ve kullanıldığı yerlere gider. Bilgisayarda ise `grep -rn "aranan" drivers/` iş görür.

---

## <a name="c10-103-kaynak-ağacının-genel-yapısı"></a>10.3 Kaynak Ağacının Genel Yapısı

![Kernel kaynağının üst düzey klasörleri](../images/kernel/02_top_tree.png)

| Klasör | İçinde ne var? |
|---|---|
| <b>`arch/`</b> | Mimariye özel kod: `arch/arm`, `arch/arm64`, `arch/x86`... Açılış kodu, bellek yönetiminin mimariye bağlı kısmı, <b>device tree</b> dosyaları ve <b>defconfig</b>'ler burada. |
| <b>`drivers/`</b> | Bütün aygıt sürücüleri: GPIO, I2C, SPI, UART, MMC, USB, ağ... Kaynağın yaklaşık yarısı. |
| `include/` | Ortak başlık dosyaları (`include/linux/`, `include/dt-bindings/`...) |
| `init/` | Kernel'in açılışı: `start_kernel()` (`init/main.c`) ve ilk kullanıcı programını (`init`) başlatan kod |
| `kernel/` | Çekirdeğin kalbi: zamanlayıcı (scheduler), süreç yönetimi, sinyaller, zamanlayıcılar |
| `mm/` | Bellek yönetimi |
| `fs/` | Dosya sistemleri: ext4, FAT, NFS, proc, sysfs... |
| `net/` | Ağ yığını: TCP/IP, soketler |
| `block/` | Blok aygıt katmanı (diskler, SD kart) |
| `lib/`, `crypto/`, `security/`, `sound/`, `ipc/` | Yardımcı kütüphaneler, şifreleme, güvenlik modülleri, ses, süreçler arası iletişim |
| `Documentation/` | Kernel'in kendi belgeleri. Device tree binding'leri `Documentation/devicetree/bindings/` altında ([11.7](#c11-117-compatible-ile-driver-eşleşmesi)). |
| `scripts/` | Derleme sistemi araçları (`kconfig`, `dtc`...) |
| `Makefile`, `Kconfig` | Derleme sisteminin girişi ve ayar menüsünün kökü |

Kernel'in kullanıcı programlarıyla ilişkisi:

```
 Kullanıcı alanı (user space)     uygulamalar, BusyBox, kütüphaneler (glibc)
 ─────────────────────────────── sistem çağrıları (open, read, write, ioctl...)
 Kernel alanı (kernel space)      kernel/ mm/ fs/ net/ ipc/   ← mimariden bağımsız çekirdek
                                  drivers/                     ← aygıt sürücüleri
                                  arch/arm/                    ← ARM'a özel kod
 ─────────────────────────────── 
 Donanım                          AM335x: Cortex-A8, UART, GPIO, I2C, MMC, Ethernet...
```

---

## <a name="c10-104-arm-mimarisi-kodunun-düzeni-archarm"></a>10.4 ARM Mimarisi Kodunun Düzeni (`arch/arm`)

![arch/arm, defconfig'ler, mach-omap2 ve DTS dosyaları](../images/kernel/03_arch_arm.png)

| Klasör | İçinde ne var? |
|---|---|
| `arch/arm/boot/` | Derlenen imajlar (`Image`, `zImage`, `uImage`) buraya çıkar. |
| `arch/arm/boot/compressed/` | `zImage`'in başındaki, kernel'i RAM'de açan küçük program ([4.9](#c4-49-uimage-nedir)) |
| `arch/arm/boot/dts/` | Device tree kaynakları (`am335x-boneblack.dts` ve `.dtsi`'leri) |
| `arch/arm/configs/` | Hazır ayar dosyaları (<b>defconfig</b>) |
| `arch/arm/kernel/` | ARM'a özel çekirdek kodu. Kernel'in ilk çalışan komutları `arch/arm/kernel/head.S`'tedir. |
| `arch/arm/mm/` | ARM'a özel bellek yönetimi (MMU, cache) |
| `arch/arm/mach-omap2/` | <b>TI OMAP/AM335x ailesine özel kod:</b> güç ve saat alanları, uyku modu (`sleep33xx.S`), DT ile açılan kartların ortak girişi (`board-generic.c`) |
| `arch/arm/mach-*/` | Diğer SoC aileleri: `mach-imx` (NXP i.MX), `mach-stm32`, `mach-at91`... |

> [!NOTE]
> Device tree'den önce her kart için `arch/arm/mach-omap2/board-xxx.c` gibi bir <b>board file</b> yazılırdı. Bugün `mach-omap2` içinde kart dosyası yoktur. Kartları device tree tarif eder, `board-generic.c` sadece "bu SoC ailesi DT ile açılıyor" der ([11.1](#c11-111-problem-kernel-donanımı-nereden-bilecek)).

---

## <a name="c10-105-kart-yapılandırma-dosyaları"></a>10.5 Kart Yapılandırma Dosyaları

Bir kart için kernel hazırlarken iki tür dosya kullanılır:

| Dosya türü | Ne tarif eder? | BBB için |
|---|---|---|
| <b>defconfig</b> (`arch/arm/configs/`) | <b>Kernel'e hangi özelliklerin ve sürücülerin derleneceğini</b> | `bb.org_defconfig` |
| <b>Device tree</b> (`arch/arm/boot/dts/`) | <b>Kartta hangi donanımın nerede olduğunu</b> | `am335x-boneblack.dts` |

Kullanılabilecek defconfig'ler:

| defconfig | Kapsamı |
|---|---|
| `bb.org_defconfig` | BeagleBoard'un BBB ve diğer Beagle kartları için hazırladığı ayar. Cape, PRU, USB gadget desteği açık. <b>Bu kitapta kullanılan.</b> |
| `omap2plus_defconfig` | Mainline'daki bütün OMAP2+ / AM335x / AM437x / DRA7 kartları için ortak ayar |
| `multi_v7_defconfig` | Bütün ARMv7 kartları (TI, NXP, ST, Rockchip...) için tek kernel. En büyük imaj. |

BBB ailesinin device tree dosyaları:

| DTS | Kart |
|---|---|
| `am335x-boneblack.dts` | BeagleBone Black |
| `am335x-boneblack-wireless.dts` | BeagleBone Black Wireless |
| `am335x-bonegreen.dts` | SeeedStudio BeagleBone Green |
| `am335x-bone.dts` | Eski BeagleBone (White) |
| `am335x-pocketbeagle.dts` | PocketBeagle |

Device tree'nin yapısı ve include zinciri [Bölüm 11](#c11-bölüm-11--linux-device-tree)'de anlatılıyor.

---

## <a name="c10-106-soc-sürücülerinin-düzeni-drivers"></a>10.6 SoC Sürücülerinin Düzeni (`drivers/`)

Sürücüler mimariye göre değil, <b>aygıt türüne</b> göre klasörlenir. AM335x'in çevre birimlerini süren sürücüler:

| AM335x birimi | Sürücü dosyası | Kernel ayarı |
|---|---|---|
| UART | `drivers/tty/serial/8250/8250_omap.c` | `CONFIG_SERIAL_8250_OMAP` |
| GPIO | `drivers/gpio/gpio-omap.c` | `CONFIG_GPIO_OMAP` |
| I2C | `drivers/i2c/busses/i2c-omap.c` | `CONFIG_I2C_OMAP` |
| SPI (McSPI) | `drivers/spi/spi-omap2-mcspi.c` | `CONFIG_SPI_OMAP24XX` |
| MMC / SD / eMMC | `drivers/mmc/host/sdhci-omap.c` (eski: `omap_hsmmc.c`) | `CONFIG_MMC_SDHCI_OMAP` |
| Ethernet (CPSW) | `drivers/net/ethernet/ti/cpsw.c`, `cpsw_new.c` | `CONFIG_TI_CPSW` |
| USB (MUSB) | `drivers/usb/musb/musb_dsps.c` | `CONFIG_USB_MUSB_DSPS` |
| USB gadget: Ethernet (`g_ether`) | `drivers/usb/gadget/legacy/ether.c` | `CONFIG_USB_ETH` |
| RTC | `drivers/rtc/rtc-omap.c` | `CONFIG_RTC_DRV_OMAP` |
| Watchdog | `drivers/watchdog/omap_wdt.c` | `CONFIG_OMAP_WATCHDOG` |
| PWM (EHRPWM) | `drivers/pwm/pwm-tiehrpwm.c` | `CONFIG_PWM_TIEHRPWM` |
| ADC | `drivers/iio/adc/ti_am335x_adc.c` | `CONFIG_TI_AM335X_ADC` |
| LCD / HDMI | `drivers/gpu/drm/tilcdc/` | `CONFIG_DRM_TILCDC` |
| PMIC (TPS65217) | `drivers/mfd/tps65217.c` | `CONFIG_MFD_TPS65217` |

Bir sürücünün hangi device tree düğümüyle eşleştiğini `compatible` dizisinden bulursun:

```bash
grep -n "compatible" drivers/gpio/gpio-omap.c          # "ti,omap4-gpio" ...
grep -rn "ti,omap4-gpio" arch/arm/boot/dts/am33xx*.dtsi # DT'deki karşılığı
```

> [!NOTE]
> UART sürücüsü konsolun adını belirler: `8250_omap` → `/dev/ttyS0`, eski `omap-serial` → `/dev/ttyO0`. Kernel 5.10'da `8250_omap` kullanıldığı için `bootargs`'ta <b>`console=ttyS0`</b> yazılır ([3.4](#c3-34-linux-kernel-ve-root-filesystem)).

---

## <a name="c10-107-kernel-yapılandırması-kconfig-config-menuconfig"></a>10.7 Kernel Yapılandırması: Kconfig, `.config`, menuconfig

Kernel'de binlerce seçenek var ve her biri `CONFIG_` ile başlayan bir isimle temsil edilir.

| Parça | Görevi |
|---|---|
| `Kconfig` dosyaları | Her klasörde bulunur. Seçenekleri, açıklamalarını ve birbirine bağımlılıklarını tanımlar. |
| `.config` | Derlemede kullanılan <b>gerçek</b> ayar dosyası. Binlerce satır, kaynak klasörünün kökünde. |
| `defconfig` | `.config`'in kısaltılmış hali: sadece varsayılandan farklı olan satırlar. `make xxx_defconfig` bunu açıp `.config` üretir. |
| `make menuconfig` | `.config`'i menüden düzenler. U-Boot'taki menüyle aynı ([9.3](#c9-93-adım-adım-toolchain-kurulumu-ve-u-boot-derleme)). |
| `make savedefconfig` | Değiştirdiğin `.config`'ten tekrar küçük bir `defconfig` üretir. |

![Kernel menuconfig ekranı](../images/kernel/bootlin_menuconfig.png)

*Görsel: Bootlin, "Embedded Linux system development" eğitim slaytları (CC BY-SA 3.0)*

Her sürücü veya özellik için üç seçenek var:

| Değer | menuconfig'te | Anlamı |
|---|---|---|
| `y` | `[*]` / `<*>` | Kernel imajının <b>içine</b> derlenir (built-in). Kernel açılır açılmaz hazırdır. |
| `m` | `<M>` | <b>Modül</b> olarak ayrı bir `.ko` dosyasına derlenir. Rootfs'ten `modprobe` / `insmod` ile sonradan yüklenir. |
| `n` | `[ ]` / `< >` | Derlenmez |

> [!IMPORTANT]
> Rootfs'i bağlamak için gereken sürücüler (MMC, ext4, NFS için ağ sürücüsü) <b>`y`</b> olmalıdır. Kernel bunlar olmadan rootfs'i bağlayamaz, rootfs'i bağlamadan da modül yükleyemez. Modüller (`m`) ancak rootfs bağlandıktan sonra kullanılabilir.

---

## <a name="c10-108-adım-adım-kerneli-derleme"></a>10.8 Adım Adım: Kernel'i Derleme

> [!NOTE]
> Aşağıdaki ekran görüntüleri <b>temsilidir</b>. Örneklerde çalışma klasörü `~/bbb/linux`, toolchain [Bölüm 9](#c9-bölüm-9--cross-toolchain-spl-ve-u-boot-derleme)'da kurulan Linaro GCC 7.5.0.

### <a name="c10-adım-1--host-paketlerini-kur"></a>Adım 1 — Host paketlerini kur

```bash
sudo apt install build-essential bc bison flex libssl-dev libncurses-dev lzop u-boot-tools git
```

| Paket | Neden? |
|---|---|
| `bc` | Derleme sırasında bazı sabitler `bc` ile hesaplanır |
| `lzop` | `bb.org_defconfig` kernel'i <b>LZO</b> ile sıkıştırır (`CONFIG_KERNEL_LZO=y`) |
| `libssl-dev` | Modül imzalama ve sertifika araçları |
| `u-boot-tools` | `mkimage`: `uImage` üretmek için |
| `bison`, `flex`, `libncurses-dev` | Kconfig ve `menuconfig` |

### <a name="c10-adım-2--yapılandır"></a>Adım 2 — Yapılandır

![distclean, defconfig ve önemli ayarlar](../images/kernel/04_config.png)

```bash
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- distclean
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- bb.org_defconfig
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- menuconfig     # isteğe bağlı
```

Kernel'de U-Boot'tan farklı olarak <b>`ARCH=arm` her komutta zorunludur</b>. Yazmazsan kernel host'un mimarisini (x86) varsayar ve yanlış `.config` üretir.

### <a name="c10-adım-3--kernel-imajını-ve-device-treeyi-derle"></a>Adım 3 — Kernel imajını ve device tree'yi derle

![uImage ve dtbs derleme çıktısı](../images/kernel/05_build.png)

```bash
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- uImage dtbs LOADADDR=0x80008000 -j$(nproc)
```

| Parça | Anlamı |
|---|---|
| `uImage` | `vmlinux` → `Image` → `zImage` → `uImage` zincirini üretir ([4.9](#c4-49-uimage-nedir)) |
| `dtbs` | Bütün `.dts` dosyalarını `.dtb`'ye derler |
| `LOADADDR=0x80008000` | `uImage` başlığına yazılan yükleme ve giriş adresi. AM335x'te DDR `0x80000000`'da başlar; kernel ilk 32 KB'ın (`0x8000`) arkasına yerleşir. |
| `-j$(nproc)` | İşlemcinin çekirdek sayısı kadar paralel derle |

İlk derleme bilgisayarına göre 10–40 dakika sürer. Paralel derlemenin etkisi:

![make ve make -j8 karşılaştırması](../images/kernel/bootlin_parallel_make.png)

*Görsel: Bootlin, "Embedded Linux system development" eğitim slaytları (CC BY-SA 3.0)*

Derleme sonunda çıkan dosyalar:

| Dosya | Ne? |
|---|---|
| `vmlinux` | Derlenmiş kernel, ELF formatında (sembollü, hata ayıklama için) |
| `arch/arm/boot/Image` | Ham binary kernel |
| `arch/arm/boot/zImage` | Sıkıştırılmış, kendini açan kernel |
| <b>`arch/arm/boot/uImage`</b> | `zImage` + U-Boot başlığı. <b>Karta giden dosya.</b> |
| <b>`arch/arm/boot/dts/am335x-boneblack.dtb`</b> | BBB'nin device tree'si. <b>Karta giden dosya.</b> |
| `System.map` | Kernel sembollerinin adresleri |

### <a name="c10-adım-4--modülleri-derle-ve-kur"></a>Adım 4 — Modülleri derle ve kur

`m` olarak seçilen sürücüler ayrı derlenir ve rootfs'e kurulur:

![Modülleri derleme ve rootfs'e kurma](../images/kernel/06_modules.png)

```bash
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- modules -j$(nproc)
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- INSTALL_MOD_PATH=~/bbb/rootfs modules_install
```

`modules_install`, modülleri `<INSTALL_MOD_PATH>/lib/modules/5.10.162/` altına kopyalar ve `modprobe`'un kullandığı `modules.dep` dosyasını üretir. Buradaki rootfs klasörünü [Bölüm 12](#c12-bölüm-12--busybox-ile-minimal-root-filesystem)'de BusyBox ile dolduracağız.

> [!CAUTION]
> `INSTALL_MOD_PATH`'i <b>unutma</b>. Yazmazsan `sudo make modules_install` modülleri <b>host bilgisayarının</b> `/lib/modules` klasörüne kurar; ARM modülleri Ubuntu'nun klasörüne karışır.

### <a name="c10-komutların-kısa-özeti"></a>Komutların kısa özeti

```bash
cd ~/bbb
git clone --depth=1 -b 5.10 https://github.com/beagleboard/linux.git
cd linux
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- distclean
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- bb.org_defconfig
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- uImage dtbs LOADADDR=0x80008000 -j$(nproc)
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- modules -j$(nproc)
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- INSTALL_MOD_PATH=~/bbb/rootfs modules_install
```

---

## <a name="c10-109-yeni-kerneli-kartta-denemek"></a>10.9 Yeni Kernel'i Kartta Denemek

Kernel'i tam olarak denemek için bir rootfs gerekir. Kendi rootfs'imizi [Bölüm 12](#c12-bölüm-12--busybox-ile-minimal-root-filesystem)'de hazırlayacağız. Kernel'in açıldığını görmek için şimdilik <b>eMMC'deki Debian'ın rootfs'ini</b> kullanabilirsin.

<b>1) Dosyaları SD kartın BOOT bölümüne kopyala:</b>

```bash
cp arch/arm/boot/uImage arch/arm/boot/dts/am335x-boneblack.dtb /media/$USER/BOOT/
```

<b>2) BOOT bölümündeki `uEnv.txt`'yi yaz.</b> Kursun `uEnv-SD.txt` dosyası temel alındı; konsol `ttyS0`, rootfs eMMC:

```text
console=ttyS0,115200n8
netargs=setenv bootargs console=${console} root=/dev/mmcblk1p2 rw rootwait
netboot=echo Booting from microSD ...; setenv autoload no; load mmc 0:1 ${loadaddr} uImage; load mmc 0:1 ${fdtaddr} am335x-boneblack.dtb; run netargs; bootm ${loadaddr} - ${fdtaddr}
uenvcmd=run netboot
```

> [!IMPORTANT]
> eMMC'deki rootfs'in hangi bölümde olduğu Debian imajına göre değişir. Eski imajlarda 2. bölüm (`mmcblk1p2`), yenilerinde tek bölüm (`mmcblk1p1`) olabilir. U-Boot'ta `mmc dev 1` ve `mmc part` ile kontrol et ([6.5](#c6-65-ek-alıştırma-kernel-ve-dtb-sd-karttan-rootfs-emmcden)).

<b>3) Kartı S2'ye basılı tutarak aç.</b> Açılış mesajlarında kendi kernel sürümünü, derleme makineni ve toolchain'ini görmelisin:

![Kendi derlediğin kernel ile açılış](../images/kernel/07_boot_new_kernel.png)

```bash
cat /proc/version
```

> [!NOTE]
> eMMC'deki Debian kendi kernel modüllerini (`/lib/modules/<eski sürüm>`) içerir, senin kernel'inin modüllerini içermez. Kernel açılır ama bazı sürücüler (Wi-Fi, USB gadget...) yüklenmeyebilir. Bu bir sorun değil; amacımız sadece kernel'in açıldığını görmek. Modüller [Bölüm 12](#c12-bölüm-12--busybox-ile-minimal-root-filesystem)'deki rootfs'e kurulacak.

---

## <a name="c10-1010-özet"></a>10.10 Özet

- BeagleBone Black için BeagleBoard'un kernel ağacı kullanılıyor: `https://github.com/beagleboard/linux.git`, dal `5.10`.
- `arch/arm` mimariye özel kodu, `arch/arm/configs` defconfig'leri, `arch/arm/boot/dts` device tree'leri, `drivers/` sürücüleri tutar. AM335x'e özel SoC kodu `arch/arm/mach-omap2`'de.
- `defconfig` → `.config` → `menuconfig` ile ayarlanır. `y` = kernel'in içinde, `m` = modül.
- Derleme: `distclean` → `bb.org_defconfig` → `uImage dtbs LOADADDR=0x80008000` → `modules` → `modules_install INSTALL_MOD_PATH=...`. Her komutta `ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf-`.
- Karta giden dosyalar: `uImage`, `am335x-boneblack.dtb` ve rootfs'e kurulan modüller.

## <a name="c10-1011-karşılaşılabilecek-problemler"></a>10.11 Karşılaşılabilecek Problemler

![Sık görülen kernel derleme hataları (temsili)](../images/kernel/08_errors.png)

| Belirti | Sebep | Çözüm |
|---|---|---|
| `Specify LOADADDR on the commandline to build an uImage` | `uImage` için yükleme adresi verilmedi | Komuta `LOADADDR=0x80008000` ekle |
| `"mkimage" command not found` | `u-boot-tools` kurulu değil | `sudo apt install u-boot-tools` |
| `lzop: not found` | Kernel LZO ile sıkıştırılıyor | `sudo apt install lzop` |
| `openssl/bio.h: No such file` | `libssl-dev` eksik | `sudo apt install libssl-dev` |
| `bc: not found` | `bc` eksik | `sudo apt install bc` |
| Derleme x86 için yapılıyor, `.config`'te ARM seçenekleri yok | Bir komutta `ARCH=arm` unutuldu | `distclean` ile temizleyip her komutta `ARCH=arm` yazarak baştan başla |
| `Starting kernel ...` sonrası hiçbir şey yok | `console=` yanlış ya da DTB uyumsuz | Kernel 5.10'da `console=ttyS0`. DTB'yi aynı kernel kaynağından derle. |
| `VFS: Unable to mount root fs on unknown-block(179,...)` | `root=` yanlış bölümü gösteriyor | U-Boot'ta `mmc part`, Linux'ta (açılabiliyorsa) `lsblk` ile doğru bölümü bul |
| Ubuntu'nun `/lib/modules` klasöründe ARM modülleri var | `modules_install` `INSTALL_MOD_PATH` olmadan `sudo` ile çalıştırıldı | O sürüm klasörünü `/lib/modules`'ten sil, komutu `INSTALL_MOD_PATH` ile tekrar çalıştır |


<div class="page-break"></div>

# <a name="c11-bölüm-11--linux-device-tree"></a>Bölüm 11 — Linux Device Tree

> <b>Bu bölümde:</b>
> - Kernel'in, kendini tanıtmayan donanımı (UART, I2C, GPIO...) nereden öğrendiğini anlayacaksın.
> - DTS, DTSI, DTB, DTBO dosyalarını ve `dtc` derleyicisini tanıyacaksın.
> - Device tree söz dizimini, `compatible` ile driver eşleşmesini ve BeagleBone Black'in include zincirini göreceksin.
> - Çalışan sistemde device tree'yi `/proc/device-tree` altından inceleyeceksin.
>
> <b>Ön koşul:</b> [Bölüm 3](#c3-bölüm-3--linux-boot-süreci-rbl--spl--u-boot) — boot zinciri, [Bölüm 4](#c4-bölüm-4--sd-karttan-boot) — U-Boot'un DTB'yi RAM'e yüklemesi.

---

## <a name="c11-111-problem-kernel-donanımı-nereden-bilecek"></a>11.1 Problem: Kernel Donanımı Nereden Bilecek?

Kernel'in çalışabilmesi için kartta <b>hangi donanımların olduğunu, nerede durduklarını ve nasıl bağlandıklarını</b> bilmesi gerekir. Örneğin:

- UART denetleyicisinin register'ları hangi adreste?
- Kaç MB RAM var, hangi adresten başlıyor?
- I2C hattına hangi çip, hangi adresle bağlı?
- USR0 LED'i hangi GPIO pinine bağlı?
- Hangi cihaz hangi interrupt hattını kullanıyor?

### <a name="c11-keşfedilebilen-ve-keşfedilemeyen-donanım"></a>Keşfedilebilen ve keşfedilemeyen donanım

| | Keşfedilebilir (discoverable) | Keşfedilemez (non-discoverable) |
|---|---|---|
| <b>Örnek</b> | PCI, PCIe, USB | UART, I2C, SPI, GPIO, Ethernet MAC, NAND, SoC içindeki çoğu çevre birimi |
| <b>Nasıl bulunur?</b> | Cihaz kendini tanıtır (Vendor ID / Device ID). Kernel bus'ı tarayarak bulur. | Cihaz kendini tanıtmaz. Kernel'e <b>birinin söylemesi gerekir</b>. |

Masaüstü PC'lerde (x86) bu bilgi BIOS/UEFI tarafından <b>ACPI tabloları</b> ile verilir. Gömülü sistemlerde (ARM, RISC-V, PowerPC) ise donanımın büyük kısmı SoC'un içinde, belirli adreslerde duran ve kendini tanıtmayan bloklardır. Bu yüzden bu bilgiyi kernel'e bir şekilde aktarmak gerekir.

### <a name="c11-eski-yöntem-board-filelar"></a>Eski yöntem: board file'lar

Device Tree'den önce ARM'da her kart için kernel kaynak kodunda bir C dosyası (<b>board file</b>) yazılırdı (`arch/arm/mach-xxx/board-yyy.c`). Donanım bilgisi bu dosyalara sabit olarak gömülürdü:

```c
/* Eski usül: donanım C koduna gömülü (temsili örnek) */
static struct resource uart0_resources[] = {
    { .start = 0x44E09000, .end = 0x44E09FFF, .flags = IORESOURCE_MEM },
    { .start = 72,         .end = 72,         .flags = IORESOURCE_IRQ },
};
```

Bu yöntemin sorunları:

- Her yeni kart = kernel'e yeni C kodu. `arch/arm` altında binlerce kart dosyası birikti.
- Kartta küçük bir değişiklik (ör. LED'in başka pine taşınması) bile <b>kernel'i yeniden derlemeyi</b> gerektiriyordu.
- Her kart için ayrı bir kernel image'ı gerekiyordu. <b>Tek bir kernel, birden fazla kartta çalışamıyordu.</b>

![Linus Torvalds'ın ARM board file karmaşası hakkındaki e-postası](../images/{142EA865-24C8-4CD5-AA3D-0C747F50EB5D}.png)

2011'de Linus Torvalds ARM tarafındaki bu karmaşadan açıkça şikayet etti. Bunun üzerine ARM dünyası, PowerPC'de zaten kullanılan <b>Device Tree</b>'ye geçti (kernel 3.x serisi). Bugün yeni ARM32 ve ARM64 kartları için Device Tree zorunludur.

> [!NOTE]
> Temel fikir: <b>Donanım tarifi koddan ayrılır.</b> Kernel aynı kalır, kartı tarif eden küçük bir veri dosyası (DTB) değişir. Böylece aynı `zImage` hem BeagleBone Black'te hem de başka bir AM335x kartında çalışabilir. Sadece DTB farklıdır.

---

## <a name="c11-112-device-tree-nedir"></a>11.2 Device Tree Nedir?

<b>Device Tree (DT)</b>, bir sistemdeki donanımı tarif eden, <b>ağaç (tree) şeklinde bir veri yapısıdır</b>.

- Ağaç <b>node</b>'lardan (düğüm) oluşur. Her node bir donanım bloğunu temsil eder (CPU, bellek, UART, I2C denetleyicisi, EEPROM...).
- Her node'un <b>property</b>'leri (özellikleri) vardır: adres, interrupt numarası, uyumlu driver adı, durum vb.
- Node'lar iç içe olabilir. Bir I2C denetleyicisinin altında ona bağlı I2C cihazları alt node olarak yer alır. Bu, donanımdaki <b>fiziksel bağlantı hiyerarşisini</b> yansıtır.
- Kökeni Sun'ın <b>OpenFirmware</b> standardına dayanır. Bugün <b>devicetree.org</b> tarafından [Devicetree Specification](https://www.devicetree.org/specifications/) olarak standartlaştırılmıştır.
- <b>İşletim sisteminden bağımsızdır</b>: Linux, U-Boot, FreeBSD, Zephyr gibi projeler de kullanır.

> [!IMPORTANT]
> Device Tree <b>donanımın ne olduğunu</b> tarif eder, <b>nasıl kullanılacağını</b> değil. "Bu kartta 0x44E09000 adresinde bir UART var" bir DT bilgisidir. "Bu UART'ı 115200 baud ile konsol olarak kullan" ise bir yapılandırma tercihidir ve genelde kernel command line'a (`bootargs`) aittir.

Device Tree'de olmayan bir şey kernel tarafından <b>bilinemez</b>. Driver kernel'e derlenmiş olsa bile, DT'de ona uyan bir node yoksa o driver hiç çalışmaz (probe edilmez).

---

## <a name="c11-113-dosya-türleri-dts-dtsi-dtc-dtb-dtbo"></a>11.3 Dosya Türleri: DTS, DTSI, DTC, DTB, DTBO

![Device Tree: kaynaktan blob'a (DTS → dtc → DTB)](../images/device_tree/dts_to_dtb.png)

*Görsel: Bootlin, "Linux kernel and driver development" eğitim slaytları (CC BY-SA 3.0)*

| Kısaltma | Açılımı | Ne? |
|---|---|---|
| <b>DT</b> | Device Tree | Genel kavram: donanımı tarif eden ağaç yapısı |
| <b>.dts</b> | Device Tree <b>Source</b> | İnsanın okuyup yazabildiği <b>metin</b> kaynak dosyası. Bir kartı tarif eder. Örn: `am335x-boneblack.dts` |
| <b>.dtsi</b> | Device Tree Source <b>Include</b> | Başka dosyalara `#include` edilen ortak parça. Genelde SoC'u ya da bir kart ailesini tarif eder. Örn: `am33xx.dtsi`. C'deki `.h` dosyalarına benzer. |
| <b>dtc</b> | Device Tree <b>Compiler</b> | `.dts` dosyasını `.dtb`'ye derleyen (ve tersini yapabilen) araç |
| <b>.dtb</b> | Device Tree <b>Blob</b> (Binary) | Derlenmiş, <b>ikili (binary)</b> çıktı. Bootloader bunu RAM'e yükler ve kernel bunu okur. Örn: `am335x-boneblack.dtb` |
| <b>FDT</b> | Flattened Device Tree | DTB'nin bellekteki "düzleştirilmiş" formatının adı. U-Boot'taki `fdt` komutu ve `fdtaddr` değişkeni buradan gelir. |
| <b>.dtbo</b> | Device Tree Blob <b>Overlay</b> | Var olan bir DTB'ye çalışma/boot anında eklenen <b>yama</b>. Cape/HAT gibi eklenti kartlar için kullanılır. ([11.12](#c11-1112-device-tree-overlay-dtbo)) |

### <a name="c11-derleme-akışı"></a>Derleme akışı

```
am33xx.dtsi ─┐
am335x-bone-common.dtsi ─┤  #include
am335x-boneblack-common.dtsi ─┤
                              ▼
            am335x-boneblack.dts
                    │
                    │  1) C preprocessor (cpp): #include, #define çözülür
                    │  2) dtc: metin → binary
                    ▼
            am335x-boneblack.dtb   (~60-70 KB)
                    │
                    │  U-Boot RAM'e yükler (fdtaddr)
                    ▼
                 Linux kernel
```

- Kernel kaynak ağacında `.dts` dosyaları önce <b>C ön işlemcisinden (cpp)</b> geçer. Bu sayede `#include <dt-bindings/gpio/gpio.h>` ve `GPIO_ACTIVE_HIGH` gibi sabitler kullanılabilir. Sonra `dtc` ile derlenir.
- DTB küçüktür (birkaç on KB) ve kernel'in hızlıca okuyabileceği bir formattadır.
- Her DTB dosyası <b>`0xd00dfeed`</b> sihirli sayısı (magic number) ile başlar. Bir dosyanın gerçekten DTB olup olmadığını böyle anlayabilirsin:

```bash
$ hexdump -C am335x-boneblack.dtb | head -1     # ilk 4 byte: d0 0d fe ed
00000000  d0 0d fe ed 00 01 0a 5c  00 00 00 38 00 00 f8 a8  |.......\...8....|
```

> [!NOTE]
> Kernel tarafındaki `.dts` dosyaları kernel kaynak kodunun içindedir: ARM32 için `arch/arm/boot/dts/`, ARM64 için `arch/arm64/boot/dts/<vendor>/`. Kernel 6.5'ten itibaren ARM32 dosyaları da vendor klasörlerine taşındı. BeagleBone Black'in dosyası yeni kernel'lerde `arch/arm/boot/dts/ti/omap/am335x-boneblack.dts` konumundadır.

---

## <a name="c11-114-söz-dizimi-syntax"></a>11.4 Söz Dizimi (Syntax)

![Device Tree temel söz dizimi](../images/device_tree/dt_temel_soz_dizimi.png)

*Görsel: Bootlin eğitim materyalleri (CC BY-SA 3.0)*

### <a name="c11-node"></a>Node

```dts
[label:] node-name[@unit-address] {
    [properties]
    [child nodes]
};
```

| Parça | Açıklama | Örnek |
|---|---|---|
| <b>`/`</b> | Kök (root) node. Her DT'de bir tane vardır ve tüm sistemi temsil eder. | `/ { ... };` |
| <b>node-name</b> | Cihazın <b>türünü</b> anlatan genel bir isim | `serial`, `i2c`, `gpio`, `memory`, `eeprom` |
| <b>@unit-address</b> | Node'un adresi. Genelde `reg` property'sinin ilk değeriyle aynıdır. | `serial@44e09000`, `eeprom@50` |
| <b>label</b> | Node'a verilen takma ad. Başka yerlerden `&label` diye referans verilir. | `uart0: serial@44e09000` |
| <b>`;`</b> | Her node ve property `;` ile biter. Unutmak en sık yapılan derleme hatasıdır. | |

Bir node'un tam yolu (path) dosya sistemi yoluna benzer: `/ocp/interconnect@44c00000/.../serial@0`.

### <a name="c11-property"></a>Property

Property'ler `isim = değer;` şeklindedir. Değer türleri:

| Tür | Yazım | Örnek |
|---|---|---|
| <b>Boş (boolean)</b> | Sadece isim. Varsa "true", yoksa "false" demektir. | `gpio-controller;` |
| <b>String</b> | Çift tırnak | `status = "okay";` |
| <b>String listesi</b> | Virgülle ayrılmış string'ler | `compatible = "ti,am3352-uart", "ti,omap3-uart";` |
| <b>Cell (u32) listesi</b> | `< >` içinde 32-bit sayılar | `reg = <0x44e09000 0x2000>;` |
| <b>Byte dizisi</b> | `[ ]` içinde hex byte'lar | `local-mac-address = [00 11 22 33 44 55];` |
| <b>phandle (referans)</b> | `< >` içinde `&label` | `gpios = <&gpio1 21 GPIO_ACTIVE_HIGH>;` |

> [!TIP]
> <b>phandle</b>, bir node'un başka bir node'a "işaretçi" (pointer) gibi referans vermesidir. Yukarıdaki `gpios` örneği şunu söyler: "Bu LED, `gpio1` denetleyicisinin <b>21.</b> pinine bağlı ve <b>active-high</b>." dtc derleme sırasında `&gpio1`'i o node'a ait benzersiz bir sayıya (phandle) çevirir.

---

## <a name="c11-115-bir-device-treenin-genel-yapısı"></a>11.5 Bir Device Tree'nin Genel Yapısı

![DT genel yapısı: kod ve donanım karşılığı](../images/device_tree/dt_genel_yapi.png)

*Görsel: Bootlin eğitim slaytları (CC BY-SA 3.0). Soldaki ağaç, sağdaki AM335x tabanlı donanımı tarif ediyor.*

Görseldeki eşleşmeye dikkat et: DT'deki iç içe yapı <b>donanımdaki bağlantıyı</b> birebir yansıtır. EEPROM, I2C denetleyicisine bağlı olduğu için DT'de de `i2c@40012000` node'unun <b>altındadır</b>.

Hemen her DT'de bulunan standart node'lar:

| Node | Görevi |
|---|---|
| <b>`/`</b> | Kök. `model` (kartın adı) ve `compatible` (kartın kimliği) burada tanımlanır. |
| <b>`cpus`</b> | İşlemci çekirdekleri (BBB'de tek bir Cortex-A8) |
| <b>`memory@...`</b> | RAM'in başlangıç adresi ve boyutu |
| <b>`chosen`</b> | Donanım değil, bootloader ile kernel arasındaki bilgiler: `bootargs`, `stdout-path` (konsol) |
| <b>`aliases`</b> | Kısa isimler. Örn: `serial0 = &uart0;` sayesinde `uart0` → `/dev/ttyS0` olur. |
| <b>`ocp` / `soc`</b> | SoC içindeki çevre birimlerinin bulunduğu bus. AM335x'te adı `ocp`'dir (On-Chip Peripherals). |

### <a name="c11-beaglebone-blackten-gerçek-bir-örnek"></a>BeagleBone Black'ten gerçek bir örnek

BBB'nin ana DTS dosyası aslında çok kısadır. Asıl iş include ettiği dosyalardadır:

```dts
/* am335x-boneblack.dts (kısaltılmış) */
/dts-v1/;

#include "am33xx.dtsi"                    /* AM335x SoC tanımı */
#include "am335x-bone-common.dtsi"        /* Tüm BeagleBone'larda ortak */
#include "am335x-boneblack-common.dtsi"   /* BBB ve BBB Wireless'ta ortak */
#include "am335x-boneblack-hdmi.dtsi"     /* HDMI desteği */

/ {
	model = "TI AM335x BeagleBone Black";
	compatible = "ti,am335x-bone-black", "ti,am335x-bone", "ti,am33xx";
};
```

`am335x-bone-common.dtsi` içinden USR LED tanımı (kısaltılmış):

```dts
leds {
	pinctrl-names = "default";
	pinctrl-0 = <&user_leds_s0>;      /* pin mux ayarı */
	compatible = "gpio-leds";         /* hangi driver? → leds-gpio */

	led2 {
		label = "beaglebone:green:usr0";
		gpios = <&gpio1 21 GPIO_ACTIVE_HIGH>;    /* GPIO1_21 pini */
		linux,default-trigger = "heartbeat";    /* kalp atışı gibi yanıp söner */
		default-state = "off";
	};
	/* usr1, usr2, usr3 ... */
};
```

> [!TIP]
> Kart açıldığında USR0 LED'inin "kalp atışı" gibi yanıp sönmesinin sebebi tam olarak bu satırdır: `linux,default-trigger = "heartbeat";`. Yani bu davranış kernel kodunda değil, <b>Device Tree'de</b> tanımlıdır.

---

## <a name="c11-116-önemli-propertyler"></a>11.6 Önemli Property'ler

| Property | Anlamı | Örnek |
|---|---|---|
| <b>`compatible`</b> | <b>En önemli property.</b> Cihazın ne olduğunu ve hangi driver'ın onu yöneteceğini belirler. Format: `"üretici,model"`. En özelden en genele doğru sıralanır. | `"ti,am3352-uart", "ti,omap3-uart"` |
| <b>`reg`</b> | Cihazın adresi. Memory-mapped cihazlarda <b>(başlangıç adresi, boyut)</b> çifti. I2C/SPI cihazlarında bus üzerindeki adres. | `reg = <0x44e09000 0x2000>;` <br> `reg = <0x50>;` |
| <b>`#address-cells`</b> | Alt node'ların `reg` değerindeki <b>adresin</b> kaç adet 32-bit cell olduğu | `<1>` |
| <b>`#size-cells`</b> | Alt node'ların `reg` değerindeki <b>boyutun</b> kaç cell olduğu. I2C'de boyut yoktur, bu yüzden `<0>`. | `<1>` veya `<0>` |
| <b>`status`</b> | Cihaz kullanılıyor mu? `"okay"` → evet, `"disabled"` → hayır (driver probe edilmez). | `status = "okay";` |
| <b>`interrupts`</b> | Cihazın kullandığı interrupt hattı | `interrupts = <72>;` |
| <b>`interrupt-parent`</b> | Interrupt'ın hangi interrupt denetleyicisine gittiği (phandle) | `<&intc>` |
| <b>`clocks`</b> | Cihazın beslendiği saat (clock) kaynakları | `clocks = <&l4ls_gclk>;` |
| <b>`pinctrl-0`, `pinctrl-names`</b> | Pin multiplexing: SoC pinlerinin bu cihaz için hangi moda alınacağı | `pinctrl-0 = <&uart0_pins>;` |
| <b>`gpios`, `*-gpios`</b> | Kullanılan GPIO pinleri (phandle + pin no + flag) | `<&gpio1 21 GPIO_ACTIVE_HIGH>` |

### <a name="c11-reg-address-cells-ve-size-cells-ilişkisi"></a>reg, #address-cells ve #size-cells ilişkisi

`reg`'in nasıl okunacağını <b>parent node'daki</b> `#address-cells` ve `#size-cells` belirler:

```dts
ocp {
	#address-cells = <1>;   /* alt node'larda adres = 1 cell */
	#size-cells = <1>;      /* alt node'larda boyut = 1 cell */

	serial@44e09000 {
		reg = <0x44e09000 0x2000>;   /* adres=0x44E09000, boyut=8 KB */
	};
};

i2c0: i2c@44e0b000 {
	#address-cells = <1>;
	#size-cells = <0>;      /* I2C cihazlarının "boyutu" yok */

	baseboard_eeprom: eeprom@50 {
		compatible = "atmel,24c256";
		reg = <0x50>;       /* I2C adresi 0x50 */
	};
};
```

> [!NOTE]
> BBB'nin üzerindeki <b>EEPROM</b> (kart adını ve seri numarasını tutan çip) gerçekten de I2C0 hattında <b>0x50</b> adresindedir. U-Boot bu EEPROM'u okuyarak kartın BeagleBone Black olduğunu anlar ve doğru DTB'yi (`am335x-boneblack.dtb`) seçer.

---

## <a name="c11-117-compatible-ile-driver-eşleşmesi"></a>11.7 compatible ile Driver Eşleşmesi

Kernel DTB'yi okuduğunda her node için bir <b>device</b> oluşturur. Sonra her device için `compatible` string'ine bakar ve <b>aynı string'i destekleyen bir driver</b> arar. Eşleşme bulunursa driver'ın `probe()` fonksiyonu çağrılır ve cihaz o driver'a <b>bağlanır (bind)</b>.

![compatible property ve kernel driver eşleşmesi](../images/device_tree/dt_compatible_driver.png)

*Görsel: Bootlin eğitim slaytları (CC BY-SA 3.0)*

- Kök node'un hemen altındaki ve `simple-bus` altındaki node'lar → <b>platform device</b> olur.
- I2C denetleyicisinin altındaki node'lar → <b>I2C device</b> olur.
- SPI denetleyicisinin altındaki node'lar → <b>SPI device</b> olur.

Driver tarafında bu eşleşme `of_device_id` tablosu ile yapılır (`of` = OpenFirmware):

```c
/* drivers/i2c/busses/i2c-omap.c (kısaltılmış) */
static const struct of_device_id omap_i2c_of_match[] = {
	{ .compatible = "ti,omap4-i2c", .data = &omap4_pdata },
	{ .compatible = "ti,omap3-i2c", .data = &omap3_pdata },
	{ },
};
MODULE_DEVICE_TABLE(of, omap_i2c_of_match);

static struct platform_driver omap_i2c_driver = {
	.probe  = omap_i2c_probe,
	.remove = omap_i2c_remove,
	.driver = {
		.name           = "omap_i2c",
		.of_match_table = omap_i2c_of_match,   /* DT eşleşme tablosu */
	},
};
```

```
DT node:   compatible = "ti,omap4-i2c"
                    │
                    │  string eşleşmesi
                    ▼
Driver:    { .compatible = "ti,omap4-i2c" }  →  omap_i2c_probe() çağrılır
```

Driver `probe()` içinde `reg`, `interrupts`, `clocks` gibi property'leri okuyarak cihazı başlatır (`platform_get_resource()`, `of_property_read_u32()` vb.).

> [!TIP]
> `compatible` listesinde birden fazla string olmasının sebebi <b>geriye dönük uyumluluktur</b>. `"ti,am3352-uart", "ti,omap3-uart"` şunu söyler: "Ben aslında AM3352 UART'ıyım. Bana özel driver yoksa OMAP3 UART driver'ı da beni sürebilir." Kernel listeyi soldan sağa dener.

> [!NOTE]
> Bir cihazın property'lerinin nasıl yazılacağı (hangi property zorunlu, hangi değerler geçerli) <b>binding</b> denen belgelerle tanımlanır. Bunlar kernel'de `Documentation/devicetree/bindings/` altındadır ve günümüzde YAML formatındadır. Yeni bir cihaz eklerken ilk bakılacak yer burasıdır.

---

## <a name="c11-118-kalıtım-dtsi-include-ve-label-ile-override"></a>11.8 Kalıtım: .dtsi, include ve Label ile Override

Aynı SoC'u kullanan onlarca kart vardır. Her kart için SoC'un tamamını baştan yazmak yerine:

1. SoC'un tüm çevre birimleri bir <b>`.dtsi`</b> dosyasında tanımlanır. Çoğu `status = "disabled"` olarak bırakılır.
2. Kartın <b>`.dts`</b> dosyası bu `.dtsi`'yi include eder. Kartta kullanılan birimleri `status = "okay"` yaparak açar ve karta özel cihazları (EEPROM, LED, PMIC...) ekler.

Aynı node birden fazla kez tanımlanırsa dtc bunları <b>birleştirir</b>. Aynı property iki yerde varsa <b>sonra gelen kazanır</b>.

### <a name="c11-beaglebone-blackin-include-zinciri"></a>BeagleBone Black'in include zinciri

![BeagleBone Black Device Tree kalıtım yapısı](../images/device_tree/dt_bbb_inheritance.png)

*Görsel: Bootlin eğitim slaytları (CC BY-SA 3.0)*

| Dosya | Seviye | İçerik |
|---|---|---|
| `am33xx.dtsi` | SoC | AM335x işlemcinin genel tanımı. `am33xx-l4.dtsi` (çevre birimleri) ve `am33xx-clocks.dtsi` (saatler) dosyalarını include eder. |
| `am335x-bone-common.dtsi` | Kart ailesi | Tüm BeagleBone'larda ortak olanlar: LED'ler, EEPROM, PMIC (TPS65217), 256 MB RAM |
| `am335x-boneblack-common.dtsi` | Kart ailesi | BBB ve BBB Wireless'ta ortak olanlar: eMMC, 512 MB RAM |
| `am335x-boneblack-hdmi.dtsi` | Ek özellik | HDMI çıkışı (TDA19988 çipi) |
| `am335x-boneblack.dts` | Kart | Sadece BBB'ye özel olanlar: `model`, `compatible` |

Override'a güzel bir örnek RAM boyutudur. `am335x-bone-common.dtsi` RAM'i 256 MB tanımlar (eski BeagleBone White'ta 256 MB vardı). `am335x-boneblack-common.dtsi` aynı node'u tekrar yazarak bunu 512 MB'a çıkarır:

```dts
/* am335x-bone-common.dtsi */
memory@80000000 {
	device_type = "memory";
	reg = <0x80000000 0x10000000>;   /* 256 MB */
};

/* am335x-boneblack-common.dtsi (sonra include edildiği için kazanır) */
memory@80000000 {
	device_type = "memory";
	reg = <0x80000000 0x20000000>;   /* 512 MB */
};
```

### <a name="c11-label-ile-override-tercih-edilen-yöntem"></a>Label ile override (tercih edilen yöntem)

Bir node'u değiştirmek için tam yolunu tekrar yazmak yerine, <b>label</b>'ı ile doğrudan ona erişmek tercih edilir:

![Label ile override](../images/device_tree/dt_label_override.png)

*Görsel: Bootlin eğitim slaytları (CC BY-SA 3.0). Soldaki ve sağdaki board.dts tamamen aynı sonucu üretir. Sağdaki `&uart0 { ... };` yazımı tercih edilir.*

```dts
/* Kart dosyasında: SoC'ta "disabled" olan I2C2'yi aç ve hızını ayarla */
&i2c2 {
	status = "okay";
	clock-frequency = <100000>;
};
```

---

## <a name="c11-119-dtc-kullanımı"></a>11.9 dtc Kullanımı

![dtc ile derleme ve geri derleme örneği](../images/device_tree/dtc_ornek.png)

*Görsel: Bootlin eğitim slaytları (CC BY-SA 3.0)*

### <a name="c11-kurulum"></a>Kurulum

```bash
sudo apt install device-tree-compiler
```

### <a name="c11-temel-komutlar"></a>Temel komutlar

```bash
# DTS → DTB (derleme)
dtc -I dts -O dtb -o foo.dtb foo.dts

# DTB → DTS (geri derleme / decompile)
dtc -I dtb -O dts -o foo_geri.dts foo.dtb

# Çalışan sistemin canlı device tree'sini DTS olarak dök
dtc -I fs -O dts /proc/device-tree
```

| Parametre | Anlamı |
|---|---|
| `-I` | Girdi formatı: `dts`, `dtb` veya `fs` (dosya sistemi, ör. `/proc/device-tree`) |
| `-O` | Çıktı formatı: `dts`, `dtb` veya `asm` |
| `-o` | Çıktı dosyası |
| `-@` | Label'ları (`__symbols__`) DTB'ye ekle. Overlay kullanılacaksa gereklidir. |

> [!TIP]
> Geri derleme (`-I dtb -O dts`) çok işe yarar: Elinde sadece bir `.dtb` varsa (ör. hazır bir image'dan çıkan) içinde ne olduğunu görebilirsin. Ancak çıkan DTS'te yorumlar, `#include`'lar, `#define` isimleri ve label'lar kaybolmuştur. Sayılar ham hex olarak görünür (`GPIO_ACTIVE_HIGH` yerine `0x00` gibi).

### <a name="c11-kernel-kaynak-ağacında-dtb-derleme"></a>Kernel kaynak ağacında DTB derleme

Kernel'in içindeki `.dts` dosyaları elle `dtc` çağırmak yerine kernel'in build sistemiyle derlenir. Bu yöntem cpp ön işleme adımını da otomatik yapar:

```bash
# Tüm DTB'leri derle (kernel kaynak klasöründe)
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- dtbs

# Sadece BBB'nin DTB'sini derle (kernel 6.5+ yol yapısı)
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- ti/omap/am335x-boneblack.dtb

# Çıktı:
#   arch/arm/boot/dts/ti/omap/am335x-boneblack.dtb
```

> [!NOTE]
> Kernel 6.5'ten eski sürümlerde hedef sadece `am335x-boneblack.dtb`'dir ve çıktı `arch/arm/boot/dts/am335x-boneblack.dtb` konumuna yazılır.

---

## <a name="c11-1110-boot-sürecinde-device-tree"></a>11.10 Boot Sürecinde Device Tree

[Linux boot sürecinde](#c3-bölüm-3--linux-boot-süreci-rbl--spl--u-boot) gördüğümüz gibi U-Boot, kernel'i başlatmadan önce <b>hem kernel image'ını hem de DTB'yi</b> RAM'e yükler:

```
eMMC / SD kart
  /boot/zImage, /boot/am335x-boneblack.dtb
        │  U-Boot: load
        ▼
DDR RAM
  loadaddr = 0x82000000 → kernel
  fdtaddr  = 0x88000000 → DTB
        │  bootz / bootm   (r2 = DTB adresi)
        ▼
Linux kernel
  DTB'yi okur (unflatten), device'ları oluşturur
        │
        ▼
Driver'lar compatible ile eşleşir ve probe edilir
```

[SD karttan boot](#c4-bölüm-4--sd-karttan-boot) bölümündeki `uEnv.txt` ile birebir aynı mantık:

```bash
fdtaddr=0x88000000                                    # DTB'nin RAM'deki adresi
load mmc 0:2 ${fdtaddr} /boot/am335x-boneblack.dtb    # DTB'yi RAM'e yükle
bootm ${loadaddr} - ${fdtaddr}                        # kernel'i başlat ve DTB adresini ver
```

`bootm`/`bootz` komutunun üç parametresi:

| Parametre | Anlamı |
|---|---|
| `${loadaddr}` | Kernel image'ının RAM adresi |
| `-` | initramfs adresi (`-` = yok) |
| `${fdtaddr}` | <b>DTB'nin RAM adresi</b> |

ARM32'de U-Boot kernel'e atlarken DTB'nin fiziksel adresini <b>`r2` register'ında</b> verir. Kernel açılışta bu adresteki blob'u okur, `0xd00dfeed` magic number'ını kontrol eder ve DTB'yi bellekte gezilebilir bir ağaca dönüştürür (<b>unflatten</b>).

> [!NOTE]
> U-Boot, kernel'e vermeden önce DTB'yi <b>değiştirebilir</b> de. Örneğin `bootargs` değişkenini DTB'deki `/chosen` node'una yazar ve RAM boyutunu `/memory` node'una işler. Kernel command line'ının kernel'e ulaşma yollarından biri budur.

### <a name="c11-u-bootta-dtbyi-incelemek"></a>U-Boot'ta DTB'yi incelemek

U-Boot'un `fdt` komutuyla RAM'deki DTB'ye bakılabilir:

```
=> load mmc 0:2 ${fdtaddr} /boot/am335x-boneblack.dtb
=> fdt addr ${fdtaddr}           # hangi adresteki DTB ile çalışılacak
=> fdt print /                   # tüm ağacı yazdır
=> fdt print /leds               # sadece leds node'u
=> fdt list /ocp                 # sadece alt node isimleri
```

---

## <a name="c11-1111-çalışan-sistemde-device-treeyi-i̇ncelemek"></a>11.11 Çalışan Sistemde Device Tree'yi İncelemek

Kernel, okuduğu device tree'yi bir dosya sistemi olarak dışarı açar:

```
/sys/firmware/devicetree/base/     # asıl konum
/proc/device-tree                  # → yukarıdakine sembolik link
```

Burada <b>her node bir klasör, her property bir dosyadır</b>:

```bash
# Kartın modeli
$ cat /proc/device-tree/model
TI AM335x BeagleBone Black

# Kök node'un compatible listesi (string'ler \0 ile ayrılmıştır)
$ cat /proc/device-tree/compatible | tr '\0' '\n'
ti,am335x-bone-black
ti,am335x-bone
ti,am33xx

# LED node'larına bak
$ ls /proc/device-tree/leds/

# Bootloader'ın kernel'e verdiği bootargs
$ cat /proc/device-tree/chosen/bootargs

# Sayısal property'leri hex olarak gör (ör. RAM adresi ve boyutu)
$ hexdump -C /proc/device-tree/memory@80000000/reg
00000000  80 00 00 00 20 00 00 00                           |.... ...|
#         adres=0x80000000  boyut=0x20000000 (512 MB)
```

Tüm ağacı tek seferde okunabilir DTS olarak görmek için:

```bash
sudo apt install device-tree-compiler
dtc -I fs -O dts /proc/device-tree > canli.dts 2>/dev/null
less canli.dts
```

Bir cihazın hangi driver'a bağlandığını görmek için:

```bash
ls /sys/bus/platform/devices/          # DT'den oluşturulan platform device'lar
ls -l /sys/bus/platform/devices/44e09000.serial/driver
#  → .../drivers/omap8250   (UART0'ı süren driver, kernel config'e göre serial-omap da olabilir)
```

BBB'nin Debian image'larında DTB dosyaları `/boot/dtbs/<kernel-sürümü>/` klasöründedir:

```bash
ls /boot/dtbs/$(uname -r)/ | grep boneblack
```

> [!TIP]
> Bir donanım çalışmıyorsa ilk kontrol: `/proc/device-tree` altında o cihazın node'u var mı ve `status` değeri `okay` mi? Node yoksa ya da `disabled` ise driver hiç devreye girmez. `dmesg | grep -i <cihaz>` ile de probe hatalarına bakılabilir.

---

## <a name="c11-1112-device-tree-overlay-dtbo"></a>11.12 Device Tree Overlay (.dtbo)

BeagleBone'a <b>cape</b> (P8/P9 header'larına takılan eklenti kart) takıldığında donanım değişir. Her cape kombinasyonu için ayrı bir `.dts` yazmak mantıklı değildir. Bunun çözümü <b>overlay</b>'dir.

- Overlay, ana DTB'ye <b>sonradan uygulanan bir yamadır</b>. Node ekleyebilir veya mevcut node'ları değiştirebilir.
- `.dts` kaynağından `dtc -@` ile <b>`.dtbo`</b> olarak derlenir.
- Ana DTB'nin de `-@` ile derlenmiş olması gerekir (label'ların bulunabilmesi için).
- Genellikle U-Boot tarafından boot sırasında uygulanır.

Basit bir overlay örneği (P9 header'ındaki I2C2'yi açar):

```dts
/dts-v1/;
/plugin/;                 /* bu bir overlay */

&i2c2 {                   /* ana DTB'deki i2c2 label'ına yama */
	status = "okay";
	clock-frequency = <100000>;
};
```

```bash
dtc -@ -I dts -O dtb -o BB-I2C2-ORNEK.dtbo BB-I2C2-ORNEK.dts
```

BBB'nin resmi Debian image'larında overlay'ler `/boot/uEnv.txt` dosyasından yönetilir. Hazır overlay'ler `/lib/firmware/` klasöründedir:

```bash
# /boot/uEnv.txt (ilgili satırlar)
enable_uboot_overlays=1
uboot_overlay_addr0=/lib/firmware/BB-I2C2-00A0.dtbo
#disable_uboot_overlay_video=1      # HDMI'ı kapatıp o pinleri serbest bırakır
```

> [!NOTE]
> Raspberry Pi'deki `config.txt` içindeki `dtoverlay=...` satırları da aynı mekanizmadır. Overlay kavramı BeagleBone'a özel değildir.

---

## <a name="c11-1113-özet"></a>11.13 Özet

| Kavram | Bir cümlede |
|---|---|
| <b>Device Tree</b> | Keşfedilemeyen donanımı kernel'e tarif eden, ağaç yapısındaki veri |
| <b>.dts</b> | Bir kartın insan tarafından okunabilir kaynak tarifi |
| <b>.dtsi</b> | Birden fazla `.dts` tarafından include edilen ortak (genelde SoC) tarif |
| <b>dtc</b> | DTS ↔ DTB dönüşümü yapan derleyici |
| <b>.dtb</b> | Derlenmiş binary. Bootloader RAM'e yükler, kernel okur. |
| <b>.dtbo</b> | DTB'ye sonradan uygulanan yama (cape/HAT için) |
| <b>compatible</b> | Node ile driver'ı eşleştiren string |
| <b>reg</b> | Cihazın adresi (ve memory-mapped ise boyutu) |
| <b>status</b> | `"okay"` → kullan, `"disabled"` → kullanma |
| <b>label / phandle</b> | Node'a takma ad ve başka node'dan ona referans (`&label`) |
| <b>/proc/device-tree</b> | Çalışan kernel'in gördüğü device tree |

BeagleBone Black için akış:

```
am33xx.dtsi + am335x-bone*.dtsi + am335x-boneblack.dts
        │  (cpp + dtc  /  make dtbs)
        ▼
am335x-boneblack.dtb  ──►  SD/eMMC: /boot/...
        │  U-Boot: load → fdtaddr (0x88000000)
        ▼
bootz/bootm ${loadaddr} - ${fdtaddr}   (r2 = DTB adresi)
        │
        ▼
Kernel DTB'yi okur → device'ları oluşturur → compatible ile driver'ları probe eder
```

---

### <a name="c11-kaynaklar"></a>Kaynaklar

- Görseller: [Bootlin - Linux kernel and driver development training](https://bootlin.com/training/kernel/) slaytları ve [bootlin/training-materials](https://github.com/bootlin/training-materials) deposu. Lisans: [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)
- [Devicetree Specification - devicetree.org](https://www.devicetree.org/specifications/)
- [Linux kernel dokümantasyonu: Devicetree](https://docs.kernel.org/devicetree/index.html)
- [Bootlin - Device Tree 101 webinar](https://bootlin.com/blog/device-tree-101-webinar-slides-and-videos/)
- [eLinux.org - Device Tree Usage](https://elinux.org/Device_Tree_Usage)


<div class="page-break"></div>

<div class="part-title">Kısım V<br>Root Filesystem</div>

<div class="page-break"></div>

# <a name="c12-bölüm-12--busybox-ile-minimal-root-filesystem"></a>Bölüm 12 — BusyBox ile Minimal Root Filesystem

> <b>Bu bölümde:</b>
> - BusyBox'ın ne olduğunu ve neden gömülü sistemlerde bu kadar yaygın kullanıldığını öğreneceksin.
> - BusyBox 1.36.1'i ARM için <b>statik</b> derleyip kendi root filesystem'ini sıfırdan kuracaksın.
> - Kernel modüllerini rootfs'e kurup kartı kendi kernel'in ve kendi rootfs'inle açacaksın.
> - BusyBox `init`'ini, `inittab`'ı ve `rcS` başlangıç betiklerini anlayacaksın.
> - USB üzerinden Ethernet sürücüsünü (`g_ether`) açılışta otomatik yükleyeceksin.
> - Rootfs'i NFS ile bilgisayardan bağlamayı göreceksin.
> - İki challenge: SSH ve TFTP desteği eklemek, BusyBox'ı dinamik derlemek.
>
> <b>Ön koşul:</b> [Bölüm 6](#c6-bölüm-6--u-boot-komut-satırı-ve-uenvtxt) — rootfs klasörleri, [Bölüm 9](#c9-bölüm-9--cross-toolchain-spl-ve-u-boot-derleme) — cross toolchain, [Bölüm 10](#c10-bölüm-10--linux-kernel-kaynak-ağacı-ve-derleme) — kernel ve modüller.

---

## <a name="c12-121-root-filesystemde-neler-olmalı"></a>12.1 Root Filesystem'de Neler Olmalı?

Kernel açılışın sonunda `root=` ile gösterilen dosya sistemini `/` olarak bağlar ve içindeki <b>`/sbin/init`</b>'i çalıştırır ([3.4](#c3-34-linux-kernel-ve-root-filesystem)). Bundan sonra olan her şey rootfs'in işidir. Klasörlerin görevlerini [6.6.1](#c6-661-klasörler-ve-görevleri)'de görmüştük. Çalışan en küçük bir Linux için gerekenler şunlar:

| Gereken | Neden? | Bu bölümde nereden? |
|---|---|---|
| `/sbin/init` | Kernel'in çalıştırdığı ilk program (PID 1) | BusyBox |
| Bir kabuk (`/bin/sh`) ve temel komutlar | Sisteme komut verebilmek | BusyBox |
| `/dev`, `/proc`, `/sys` klasörleri | Kernel'in sanal dosya sistemleri buraya bağlanır | `mkdir` |
| `/etc/inittab`, `/etc/init.d/rcS` | `init`'in açılışta ne yapacağı | Elle yazacağız |
| `/lib/modules/<sürüm>/` | Modül olarak derlenen sürücüler | [Bölüm 10](#c10-bölüm-10--linux-kernel-kaynak-ağacı-ve-derleme)'daki `modules_install` |
| `/lib/*.so` (sadece dinamik derlemede) | Paylaşılan kütüphaneler | [12.11](#c12-1211-challenge-2-busyboxı-dinamik-derlemek) |

> [!NOTE]
> Kursun "About RFS" ve "About initramfs" makaleleri bu konunun teorisini anlatıyor. initramfs, bu bölümde kuracağımız klasör yapısının sıkıştırılıp RAM'e yüklenen halidir. [Bölüm 7](#c7-bölüm-7--seri-porttan-uart-boot)'de kullandığımız `initramfs` dosyası da böyle bir BusyBox rootfs'idir.

---

## <a name="c12-122-busybox-nedir"></a>12.2 BusyBox Nedir?

<b>BusyBox</b>, `ls`, `cp`, `mount`, `sh`, `init`, `ifconfig`, `vi`, `tftp` gibi yüzlerce Unix komutunu <b>tek bir küçük programda</b> toplayan bir projedir. Her komuta <b>applet</b> denir.

- Tek bir `busybox` dosyası vardır (birkaç yüz KB ile 2 MB arası).
- `/bin/ls`, `/sbin/init` gibi komutlar bu dosyaya giden <b>sembolik linklerdir</b>.
- `ls` olarak çağrılınca BusyBox, çağrıldığı adı (`argv[0]`) okur ve `ls` gibi davranır. `busybox ls` yazmak da aynı işi yapar.

![BusyBox kurulumu sonrası rootfs ağacı](../images/busybox/bootlin_busybox_tree.png)

*Görsel: Bootlin, "Embedded Linux system development" eğitim slaytları (CC BY-SA 3.0)*

| | Masaüstü Linux (GNU coreutils vb.) | BusyBox |
|---|---|---|
| Boyut | Yüzlerce MB, her komut ayrı program | Tek dosya, ~1–2 MB |
| Özellik | Bütün seçenekler | En çok kullanılan seçenekler |
| Yapılandırma | — | Kernel gibi `menuconfig` ile hangi applet'lerin derleneceği seçilir |

---

## <a name="c12-123-adım-adım-busyboxı-derlemek"></a>12.3 Adım Adım: BusyBox'ı Derlemek

> [!NOTE]
> Aşağıdaki ekran görüntüleri <b>temsilidir</b>. Çalışma klasörü `~/bbb`, rootfs `~/bbb/rootfs`. Toolchain [Bölüm 9](#c9-bölüm-9--cross-toolchain-spl-ve-u-boot-derleme)'da kurulan Linaro GCC 7.5.0.

### <a name="c12-adım-1--i̇ndir-ve-yapılandır"></a>Adım 1 — İndir ve yapılandır

![BusyBox'ı indirme ve statik derleme ayarı](../images/busybox/01_download_config.png)

```bash
cd ~/bbb
wget https://busybox.net/downloads/busybox-1.36.1.tar.bz2
tar -xjf busybox-1.36.1.tar.bz2
cd busybox-1.36.1
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- defconfig
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- menuconfig
```

`menuconfig`'te tek bir ayarı değiştir:

```
Settings  --->
    [*] Build static binary (no shared libs)
```

![BusyBox menuconfig ekranı](../images/busybox/bootlin_busybox_menuconfig.png)

*Görsel: Bootlin, "Embedded Linux system development" eğitim slaytları (CC BY-SA 3.0)*

| | Statik (`CONFIG_STATIC=y`) | Dinamik |
|---|---|---|
| Kütüphaneler | `busybox` dosyasının <b>içine</b> gömülür | Çalışırken rootfs'teki `/lib/*.so` dosyalarından yüklenir |
| Rootfs'te `/lib` gerekir mi? | Hayır | Evet ([12.11](#c12-1211-challenge-2-busyboxı-dinamik-derlemek)) |
| Ne zaman? | İlk deneme, en basit rootfs. <b>Kursta kullanılan.</b> | Rootfs'e başka dinamik programlar da konacaksa |

### <a name="c12-adım-2--derle-ve-rootfs-klasörüne-kur"></a>Adım 2 — Derle ve rootfs klasörüne kur

![BusyBox'ı derleme ve kurma](../images/busybox/02_build_install.png)

```bash
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- -j$(nproc)
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- CONFIG_PREFIX=~/bbb/rootfs install
file ~/bbb/rootfs/bin/busybox
```

`install` hedefi `busybox`'ı `~/bbb/rootfs/bin/` altına koyar ve bütün applet linklerini (`bin/`, `sbin/`, `usr/bin/`, `usr/sbin/`) oluşturur. `file` çıktısında <b>ARM</b> ve <b>statically linked</b> görmelisin.

> [!TIP]
> Statik derlemede `Using 'getpwnam' in statically linked applications requires at runtime the shared libraries...` gibi uyarılar görebilirsin. Bunlar glibc'nin statik bağlamadaki bilinen uyarılarıdır, derleme başarılıdır.

### <a name="c12-adım-3--kernel-modüllerini-kur"></a>Adım 3 — Kernel modüllerini kur

Kursun "Kernel Modules installation" dersi: [Bölüm 10](#c10-bölüm-10--linux-kernel-kaynak-ağacı-ve-derleme)'da derlediğin modülleri aynı rootfs klasörüne kur. Bunu daha önce yaptıysan atlayabilirsin.

```bash
cd ~/bbb/linux
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- INSTALL_MOD_PATH=~/bbb/rootfs modules_install
ls ~/bbb/rootfs/lib/modules/          # 5.10.162
```

> [!IMPORTANT]
> `/lib/modules/` altındaki klasör adı, çalışan kernel'in `uname -r` çıktısıyla <b>birebir aynı</b> olmalı. Kernel'i yeniden derleyip sürüm değiştiysen modülleri de yeniden kur. Aksi halde `modprobe` modülleri bulamaz.

---

## <a name="c12-124-rootfsi-tamamlamak"></a>12.4 Rootfs'i Tamamlamak

BusyBox sadece programları kurar. Kalan klasörleri ve ayar dosyalarını elle oluşturuyoruz:

![Rootfs iskeleti, inittab ve init.d](../images/busybox/03_rootfs_tree.png)

```bash
cd ~/bbb/rootfs
mkdir -p dev proc sys etc/init.d tmp root var/run var/log mnt
mkdir -p etc/network/if-pre-up.d etc/network/if-up.d etc/network/if-down.d etc/network/if-post-down.d
```

| Klasör | Neden boş da olsa gerekli? |
|---|---|
| `dev` | Kernel buraya `devtmpfs`'i bağlar ve aygıt dosyalarını (`/dev/ttyS0`, `/dev/mmcblk0`...) kendisi oluşturur. `bb.org_defconfig`'te `CONFIG_DEVTMPFS_MOUNT=y` olduğu için ayrıca bir şey yapmana gerek yok. |
| `proc`, `sys` | `rcS` buraya `proc` ve `sysfs` sanal dosya sistemlerini bağlayacak |
| `tmp`, `var/run`, `var/log` | Geçici dosyalar, PID dosyaları ve loglar |
| `etc/network/if-*.d` | BusyBox'ın `ifup` komutu bu klasörleri arar; yoksa hata verir |

> [!NOTE]
> `/dev` klasörünü elle doldurmana (`mknod`) gerek yok. Eskiden aygıt dosyaları elle oluşturulurdu; bugün `devtmpfs` bunu kernel tarafında otomatik yapar.

---

## <a name="c12-125-busybox-init-inittab-ve-rcs"></a>12.5 BusyBox `init`, `inittab` ve `rcS`

Kernel rootfs'i bağladıktan sonra şu zincir çalışır:

```
kernel  ──►  /sbin/init  (BusyBox, PID 1)
                 │  /etc/inittab'ı okur
                 ├── ::sysinit   → /etc/init.d/rcS        (bir kez, açılışta)
                 │                    └── /etc/init.d/S??*  sırayla "start" ile
                 ├── ::askfirst  → /bin/sh                (konsolda Enter'a basınca kabuk)
                 └── ::shutdown  → /etc/init.d/rcK        (kapanırken, ters sırayla "stop")
```

### <a name="c12-etcinittab"></a>`/etc/inittab`

`inittab` her satırda <b>`<tty>:<runlevel>:<eylem>:<program>`</b> biçimindedir. BusyBox `runlevel` alanını kullanmaz. `tty` boşsa konsol kullanılır.

```text
::sysinit:/etc/init.d/rcS
::askfirst:-/bin/sh
::restart:/sbin/init
::shutdown:/etc/init.d/rcK
::shutdown:/bin/umount -a -r
```

| Eylem | Anlamı |
|---|---|
| `sysinit` | Açılışta bir kez çalışır, bitene kadar beklenir |
| `askfirst` | "Please press Enter to activate this console." yazar, Enter'a basınca programı başlatır. Program kapanırsa yeniden başlatır. `-/bin/sh`'teki `-` kabuğu "login shell" yapar. |
| `respawn` | `askfirst` gibi ama sormadan başlatır |
| `restart` | `init` yeniden başlatılırken çalışır |
| `shutdown` | `reboot` / `poweroff` sırasında çalışır |

> [!TIP]
> `inittab` hiç yoksa BusyBox varsayılan bir tane kullanır: `rcS`'i çalıştırır, konsolda ve <b>tty2–tty4</b>'te kabuk açmaya çalışır. BBB'de bu terminaller olmadığı için `can't open /dev/tty2` hataları görürsün. Kendi `inittab`'ını yazmak bunu önler.

### <a name="c12-etcinitdrcs--kursun-betiği"></a>`/etc/init.d/rcS` — kursun betiği

Kursun reposundaki (`scripts/etc/init.d/rcS`) betik `/proc`'u bağlar ve `/etc/init.d` altındaki `S` ile başlayan iki haneli numaralı betikleri <b>sırayla</b> `start` parametresiyle çalıştırır. Sona `.sh` eklenmiş betikler ayrı süreç açmadan, aynı kabukta çalıştırılır:

```sh
#!/bin/sh

# Start all init scripts in /etc/init.d
# executing them in numerical order.
#
echo "Mounting proc"
mount -t proc /proc /proc

for i in /etc/init.d/S??* ;do

     # Ignore dangling symlinks (if any).
     [ ! -f "$i" ] && continue

     case "$i" in
	*.sh)
	    # Source shell script for speed.
	    (
		trap - INT QUIT TSTP
		set start
		. $i
	    )
	    ;;
	*)
	    # No sh extension, so fork subprocess.
	    $i start
	    ;;
    esac
done
```

`echo "Mounting proc"` satırından sonraya şu iki satırı da eklemeni öneririm. `sysfs` birçok aracın ve [Bölüm 1](#c1-bölüm-1--beaglebone-black-donanımı)'deki LED komutlarının, `devpts` ise SSH'ın ([12.10](#c12-1210-challenge-1-ssh-ve-tftp-desteği)) çalışması için gerekli:

```sh
mount -t sysfs sysfs /sys
mkdir -p /dev/pts && mount -t devpts devpts /dev/pts
```

`rcK` aynı döngüyü <b>ters sırada</b> ve `stop` parametresiyle çalıştırır. Numaralar sırayı belirler: `S01` önce, `S50` sonra başlar; kapanırken tersi.

Kursun reposundaki betikler:

| Betik | Görevi |
|---|---|
| `S01logging` | `syslogd` ve `klogd`'yi başlatır (loglar `/var/log/messages`'a) |
| `S02module` | Açılışta kernel modüllerini yükler ([12.7](#c12-127-usb-üzerinden-ethernet-ve-sürücüleri-açılışta-yüklemek)) |
| `S40network` | `/etc/network/interfaces`'teki arayüzleri `ifup -a` ile açar |
| `S50sshd` | OpenSSH sunucusunu başlatır. BusyBox rootfs'inde OpenSSH olmadığı için kendi başına çalışmaz ([12.10](#c12-1210-challenge-1-ssh-ve-tftp-desteği)'da yerine Dropbear kullanıyoruz) |

Betiklerin hepsini rootfs'e koy ve <b>çalıştırılabilir</b> yap:

```bash
cd ~/bbb/rootfs/etc/init.d
# rcS, rcK, S01logging, S02module, S40network dosyalarını buraya kopyala
chmod +x rcS rcK S*
```

---

## <a name="c12-126-kartta-test-rootfs-sd-kartta"></a>12.6 Kartta Test: Rootfs SD Kartta

Kursun "Testing boot images and busybox on BBB" dersleri: kernel ve DTB SD kartın BOOT bölümünden, rootfs ROOTFS bölümünden gelir.

<b>1) Rootfs'i SD karta kopyala.</b>

![Rootfs'i ve kernel'i SD karta kopyalama](../images/busybox/04_copy_sd.png)

```bash
cd ~/bbb
sudo rm -rf /media/$USER/ROOTFS/*
sudo cp -a rootfs/* /media/$USER/ROOTFS/
sudo chown -R root:root /media/$USER/ROOTFS
cp linux/arch/arm/boot/uImage linux/arch/arm/boot/dts/am335x-boneblack.dtb /media/$USER/BOOT/
sync && sudo umount /media/$USER/BOOT /media/$USER/ROOTFS
```

> [!CAUTION]
> `sudo rm -rf /media/$USER/ROOTFS/*` komutundaki yolu iki kez kontrol et. Yol yanlış yazılırsa bilgisayarındaki dosyaları silebilir.

<b>2) BOOT bölümündeki `uEnv.txt`</b> ([10.9](#c10-109-yeni-kerneli-kartta-denemek)'dakinin rootfs'i SD kart olan hali):

```text
console=ttyS0,115200n8
netargs=setenv bootargs console=${console} root=/dev/mmcblk0p2 rw rootwait
netboot=echo Booting from microSD ...; setenv autoload no; load mmc 0:1 ${loadaddr} uImage; load mmc 0:1 ${fdtaddr} am335x-boneblack.dtb; run netargs; bootm ${loadaddr} - ${fdtaddr}
uenvcmd=run netboot
```

<b>3) Kartı S2'ye basılı tutarak aç.</b> `rcS`'in mesajlarından sonra Enter'a bas:

![Kendi kernel'in ve BusyBox rootfs'inle açılış](../images/busybox/05_boot_busybox.png)

`ps` çıktısında PID 1'in `init` olduğunu görürsün. Artık kartta çalışan her şeyi sen derledin: SPL, U-Boot, kernel, DTB ve rootfs.

---

## <a name="c12-127-usb-üzerinden-ethernet-ve-sürücüleri-açılışta-yüklemek"></a>12.7 USB Üzerinden Ethernet ve Sürücüleri Açılışta Yüklemek

Kursun "Enabling ethernet over usb by driver integration" ve "Auto loading drivers during system startup" dersleri.

### <a name="c12-usb-gadget-g_ether"></a>USB gadget: `g_ether`

BBB'nin mini-USB portu (USB0) <b>gadget</b> (cihaz) modunda çalışabilir. `g_ether` sürücüsü yüklenince kart, bilgisayara USB üzerinden bir <b>ağ kartı</b> gibi görünür. Ethernet kablosu olmadan SSH, TFTP, NFS yapılabilir. Kursun `192.168.7.x` adresleri bu ağdan gelir.

`bb.org_defconfig`'te bu sürücü <b>modül</b> olarak derlenir (`CONFIG_USB_ETH=m`, [10.8](#c10-108-adım-adım-kerneli-derleme)). Başka bir defconfig kullanıyorsan `menuconfig`'te açman gerekir:

```
Device Drivers  --->
    [*] USB support  --->
        <*>   USB Gadget Support  --->
            <M>   USB Gadget precomposed configurations
                <M>   Ethernet Gadget (with CDC Ethernet support)
```

Elle denemek için kartta:

![g_ether ile USB üzerinden ağ](../images/busybox/06_g_ether.png)

```text
/ # modprobe g_ether
/ # ifconfig usb0 192.168.7.2 netmask 255.255.255.0 up
```

Bilgisayarda yeni bir ağ arayüzü (`enx...` veya `usb0`) belirir. Ona `192.168.7.1` ver ve ping at:

```bash
ip -br link
sudo ip addr add 192.168.7.1/24 dev enx8e2a4f61c310     # arayüz adını kendi çıktından al
ping 192.168.7.2
```

### <a name="c12-açılışta-otomatik-yüklemek"></a>Açılışta otomatik yüklemek

Her açılışta bu komutları yazmamak için iki betik kullanılır.

<b>`S02module`</b> (kursun reposundan) `g_ether`'i yükler:

```sh
#!/bin/sh
#
# load the kernel modules at startup
#

case "$1" in
  start)
	printf "Loading kernel modules : "
	/sbin/modprobe g_ether
	[ $? = 0 ] && echo "OK" || echo "FAIL"
	;;
  stop)
	printf "Unloading kernel modules : "
	/sbin/rmmod g_ether
	[ $? = 0 ] && echo "OK" || echo "FAIL"
	;;
  restart|reload)
	"$0" stop
	"$0" start
	;;
  *)
	echo "Usage: $0 {start|stop|restart}"
	exit 1
esac

exit $?
```

<b>`S40network`</b> `ifup -a` ile `/etc/network/interfaces` dosyasındaki arayüzleri açar. Bu dosyayı oluştur:

```text
# /etc/network/interfaces
auto lo
iface lo inet loopback

auto usb0
iface usb0 inet static
    address 192.168.7.2
    netmask 255.255.255.0
```

Numaralar sırayı garanti eder: önce `S02` sürücüyü yükler, sonra `S40` arayüzü açar. Kartı yeniden başlatınca ekranda `Loading kernel modules : OK` ve `Starting network: OK` görürsün.

---

## <a name="c12-128-rootfsi-nfs-ile-bilgisayardan-bağlamak"></a>12.8 Rootfs'i NFS ile Bilgisayardan Bağlamak

Rootfs'i her değişiklikte SD karta kopyalamak yorucu. <b>NFS</b> (Network File System) ile kart, rootfs'i doğrudan bilgisayardaki bir klasörden bağlar. Bilgisayarda bir dosyayı değiştirdiğin anda kart da görür. [Bölüm 8](#c8-bölüm-8--tftp-ile-ağdan-boot)'deki TFTP ile birlikte geliştirme döngüsü şöyle olur:

```
Host PC                                      BBB
 /var/lib/tftpboot/uImage, .dtb  ── TFTP ──►  U-Boot: RAM'e yükle, bootm
 /srv/nfs/bbb/  (rootfs)     ── NFS  ──►  Kernel: / olarak bağla
```

### <a name="c12-adım-1--hostta-nfs-sunucusu"></a>Adım 1 — Host'ta NFS sunucusu

![NFS sunucusunu kurma ve paylaşımı açma](../images/busybox/07_nfs_host.png)

```bash
sudo apt install nfs-kernel-server
sudo mkdir -p /srv/nfs/bbb
sudo cp -a ~/bbb/rootfs/* /srv/nfs/bbb/
sudo chown -R root:root /srv/nfs/bbb
echo "/srv/nfs/bbb  *(rw,sync,no_root_squash,no_subtree_check)" | sudo tee -a /etc/exports
sudo exportfs -ra
showmount -e localhost
```

| `/etc/exports` seçeneği | Anlamı |
|---|---|
| `*` | Her IP'den erişime izin ver (yerine `192.168.27.2` yazarak sadece karta açabilirsin) |
| `rw` | Okuma-yazma |
| `sync` | Yazmalar diske yazıldıktan sonra onay ver |
| `no_root_squash` | Karttaki `root` kullanıcısı paylaşımda da `root` olsun. Rootfs için şart. |
| `no_subtree_check` | Alt klasör kontrollerini kapat (daha hızlı ve sorunsuz) |

### <a name="c12-adım-2--uenvtxt"></a>Adım 2 — `uEnv.txt`

Kursun `uEnv-nfs.txt` dosyası temel alındı. Kursun dosyası USB ağı (`192.168.7.x`) kullanıyor; burada [Bölüm 8](#c8-bölüm-8--tftp-ile-ağdan-boot)'deki Ethernet kablosu ve adresleri kullanılıyor:

```text
console=ttyS0,115200n8
ipaddr=192.168.27.2
serverip=192.168.27.1
rootpath=/srv/nfs/bbb
loadtftp=echo Booting from network ...; tftpboot ${loadaddr} uImage; tftpboot ${fdtaddr} am335x-boneblack.dtb
netargs=setenv bootargs console=${console} root=/dev/nfs rw nfsroot=${serverip}:${rootpath},nolock,v3,tcp rootwait ip=${ipaddr}:${serverip}::255.255.255.0::eth0:off init=/sbin/init
uenvcmd=setenv autoload no; run loadtftp; run netargs; bootm ${loadaddr} - ${fdtaddr}
```

| `bootargs` parçası | Anlamı |
|---|---|
| `root=/dev/nfs` | Rootfs bir disk değil, NFS |
| `nfsroot=<sunucu>:<klasör>,...` | NFS sunucusu ve paylaşılan klasör |
| `nolock` | NFS dosya kilitlemesini kapat (kartta kilit servisi yok) |
| `v3,tcp` | NFS sürüm 3, TCP üzerinden. <b>Önemli:</b> kernel varsayılan olarak NFSv2 dener; Ubuntu 22.04 ve sonrasında NFSv2 kapalıdır. |
| `ip=<kart>:<sunucu>::<maske>::eth0:off` | Kernel'in IP'sini kendisi ayarlaması. U-Boot'un IP'si kernel'e geçmez ([8.7](#c8-87-linux-açıldıktan-sonra-tftp-ile-dosya-çekme)). |
| `init=/sbin/init` | Çalıştırılacak ilk program (varsayılan da budur) |

`uImage` ve `am335x-boneblack.dtb`'yi `/var/lib/tftpboot`'a kopyalamayı unutma.

### <a name="c12-adım-3--aç-ve-doğrula"></a>Adım 3 — Aç ve doğrula

![Rootfs'in NFS'ten bağlanması](../images/busybox/08_nfs_boot.png)

```text
/ # mount | head -1
192.168.27.1:/srv/nfs/bbb on / type nfs (rw,...,vers=3,...)
```

> [!WARNING]
> Rootfs NFS'ten geliyorken kartta <b>`eth0`'ı yeniden yapılandırma</b> (`ifconfig eth0 ...`, `/etc/network/interfaces`'e `eth0` eklemek). Ağ bir an bile kesilirse kernel rootfs'e ulaşamaz ve sistem donar. `eth0`'ı kernel `ip=` ile ayarlıyor; `interfaces` dosyasında sadece `lo` ve `usb0` kalsın.

> [!NOTE]
> Kursun `uEnv-nfs.txt`'si NFS'i USB ağı (`usb0`) üzerinden yapar. Bunun için `g_ether`'in modül değil <b>kernel'e gömülü</b> (`CONFIG_USB_ETH=y`) olması gerekir; çünkü rootfs bağlanmadan modül yüklenemez ([10.7](#c10-107-kernel-yapılandırması-kconfig-config-menuconfig)). Ethernet kablosunda bu sorun yok, CPSW sürücüsü zaten gömülü.

---

## <a name="c12-129-geliştirme-döngüsü"></a>12.9 Geliştirme Döngüsü

| Ne değişti? | Ne yaparsın? |
|---|---|
| Kendi uygulaman / bir betik | Dosyayı `/srv/nfs/bbb` içine kopyala. Kart hemen görür, yeniden başlatma yok. |
| Kernel veya DTB | `uImage` / `.dtb`'yi `/var/lib/tftpboot`'a kopyala, kartı resetle. |
| Kernel modülleri | `modules_install INSTALL_MOD_PATH=/srv/nfs/bbb` (sudo ile), kartta `modprobe` ya da reset |
| BusyBox ayarları | BusyBox'ı yeniden derle, `CONFIG_PREFIX=/srv/nfs/bbb` ile kur |

---

## <a name="c12-1210-challenge-1-ssh-ve-tftp-desteği"></a>12.10 Challenge 1: SSH ve TFTP Desteği

Kursun bu bölümdeki ilk challenge'ı:

> <i>BusyBox ile minimal bir dosya sistemi kurup kartta test ettin. Şimdi onu birkaç araçla zenginleştir: kart ile bilgisayar arasında <b>TFTP</b> ve <b>SSH</b> ile dosya aktarımı yapılabilsin. BusyBox'ta SSH desteği yoktur; üçüncü parti bir kaynaktan eklenmesi gerekir. İpucu: <https://busybox.net/tinyutils.html></i>

### <a name="c12-tftp"></a>TFTP

BusyBox'ın `defconfig`'inde `tftp` applet'i zaten açık (`Networking Utilities → tftp`). Kullanımı [8.7](#c8-87-linux-açıldıktan-sonra-tftp-ile-dosya-çekme)'deki gibi:

```text
/ # tftp -g -r dosya 192.168.27.1        # host'tan al
/ # tftp -p -l dosya 192.168.27.1        # host'a gönder
```

### <a name="c12-ssh-dropbear"></a>SSH: Dropbear

İpucundaki sayfa küçük sistemler için araçları listeler. SSH için önerilen <b>Dropbear</b>: SSH sunucusu, istemcisi ve `scp`'yi birkaç yüz KB'ta sunan bir proje. Kursun derleme notlarındaki adımlar:

![Dropbear'ı derleme, kurma ve SSH ile bağlanma](../images/busybox/09_dropbear.png)

```bash
cd ~/bbb
wget https://matt.ucc.asn.au/dropbear/releases/dropbear-2022.83.tar.bz2
tar -xjf dropbear-2022.83.tar.bz2 && cd dropbear-2022.83
./configure --host=arm-linux-gnueabihf --disable-zlib --prefix=/usr CC=arm-linux-gnueabihf-gcc
make PROGRAMS="dropbear dropbearkey dbclient scp" STATIC=1 -j4
make PROGRAMS="dropbear dropbearkey dbclient scp" STATIC=1 DESTDIR=~/bbb/rootfs install
```

| Parça | Anlamı |
|---|---|
| `--host=arm-linux-gnueabihf` | ARM için cross compile |
| `--disable-zlib` | zlib sıkıştırma kütüphanesi olmadan derle (rootfs'te zlib yok) |
| `--prefix=/usr` + `DESTDIR=...` | Kartta `/usr/sbin/dropbear` olacak şekilde rootfs klasörüne kur |
| `STATIC=1` | BusyBox gibi statik derle, kütüphane gerekmesin |

Kartta SSH'a giriş yapabilmek için bir <b>kullanıcı ve şifre</b> gerekir. Rootfs'e şu iki dosyayı ekle:

```bash
cd ~/bbb/rootfs
echo 'root:x:0:0:root:/root:/bin/sh' > etc/passwd
echo 'root::0:0:99999:7:::' > etc/shadow
chmod 600 etc/shadow
```

Kartta şifreyi belirle ve sunucuyu başlat:

```text
/ # passwd
/ # mkdir -p /etc/dropbear
/ # dropbear -R
```

`-R`, sunucu anahtarlarını ilk bağlantıda otomatik üretir. Bilgisayardan bağlan ve dosya gönder:

```bash
ssh root@192.168.27.2
scp dosya root@192.168.27.2:/root/
```

Açılışta otomatik başlaması için `S50sshd` yerine şu küçük betiği koy:

```sh
#!/bin/sh
# /etc/init.d/S50dropbear
case "$1" in
  start) printf "Starting dropbear: "; mkdir -p /etc/dropbear; /usr/sbin/dropbear -R && echo "OK" ;;
  stop)  printf "Stopping dropbear: "; killall dropbear; echo "OK" ;;
  *)     echo "Usage: $0 {start|stop}"; exit 1 ;;
esac
```

> [!IMPORTANT]
> Dropbear, kabuk açmak için `/dev/pts`'e ihtiyaç duyar. [12.5](#c12-125-busybox-init-inittab-ve-rcs)'te `rcS`'e eklediğimiz `mount -t devpts devpts /dev/pts` satırı yoksa bağlantı `PTY allocation request failed` ile kapanır.

---

## <a name="c12-1211-challenge-2-busyboxı-dinamik-derlemek"></a>12.11 Challenge 2: BusyBox'ı Dinamik Derlemek

Kursun ikinci challenge'ı:

> <i>BusyBox derslerinin hepsinde "statik" derlenmiş programlar kullandık. Dinamik bağlanarak (dynamic linking) cross compile edilmiş bir uygulamayı bu dosya sisteminde çalıştırırsan çalışmaz. BusyBox'ı <b>dinamik</b> bağlanmış programlar üretecek şekilde yeniden derle ve dinamik bağlanmış bir uygulamanın çalıştığını test et.</i>

### <a name="c12-neden-dinamik-program-çalışmıyor"></a>Neden dinamik program çalışmıyor?

Dinamik bağlanmış bir program, çalışırken iki şeye ihtiyaç duyar:
1. <b>Dinamik yükleyici</b>: ARM hard-float'ta `/lib/ld-linux-armhf.so.3`. Kernel programı başlatırken önce bunu çalıştırır.
2. Programın kullandığı <b>paylaşılan kütüphaneler</b>: `libc.so.6`, `libm.so.6`...

Statik BusyBox rootfs'inde `/lib` altında sadece kernel modülleri vardır. Yükleyici yoksa kernel programı hiç başlatamaz ve kabuk yanıltıcı bir şekilde `not found` der.

### <a name="c12-çözüm"></a>Çözüm

![BusyBox'ı dinamik derleme ve kütüphaneleri rootfs'e kopyalama](../images/busybox/10_dynamic.png)

<b>1) Statik ayarı kapat, yeniden derle ve kur:</b>

```bash
cd ~/bbb/busybox-1.36.1
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- menuconfig      # Settings → Build static binary: [ ]
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- -j$(nproc)
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- CONFIG_PREFIX=~/bbb/rootfs install
```

<b>2) Hangi kütüphanelerin gerektiğine bak:</b>

```bash
arm-linux-gnueabihf-readelf -d ~/bbb/rootfs/bin/busybox | grep NEEDED
arm-linux-gnueabihf-readelf -l ~/bbb/rootfs/bin/busybox | grep interpreter
```

<b>3) Kütüphaneleri toolchain'den rootfs'e kopyala.</b> Toolchain, ARM için derlenmiş glibc'yi kendi <b>sysroot</b> klasöründe taşır:

```bash
SYSROOT=$(arm-linux-gnueabihf-gcc -print-sysroot)
cp -a $SYSROOT/lib/*.so* ~/bbb/rootfs/lib/
```

> [!TIP]
> Bu komut toolchain'deki bütün kütüphaneleri kopyalar (birkaç on MB). Sadece gerekenleri istiyorsan `readelf` çıktısındaki dosyaları ve `ld-linux-armhf.so.3`'ü kopyala. Kopyaladıktan sonra `arm-linux-gnueabihf-strip` ile küçültebilirsin.

<b>4) Dinamik bir uygulamayla test et:</b>

```bash
arm-linux-gnueabihf-gcc hello.c -o hello          # varsayılan: dinamik
file hello                                            # "dynamically linked, interpreter /lib/ld-linux-armhf.so.3"
cp hello ~/bbb/rootfs/root/                         # NFS kullanıyorsan /srv/nfs/bbb/root/
```

Kartta `/root/hello` çalışıyorsa challenge tamam.

---

## <a name="c12-1212-özet"></a>12.12 Özet

- BusyBox, yüzlerce komutu tek bir programda toplar; komutlar ona giden sembolik linklerdir.
- Minimal rootfs = BusyBox + `dev proc sys etc tmp var` klasörleri + `/etc/inittab` + `/etc/init.d/rcS` + `/lib/modules`.
- Açılış: kernel → `/sbin/init` (PID 1) → `inittab` → `rcS` → `S??*` betikleri sırayla → konsolda kabuk.
- `g_ether` kartı USB üzerinden bir ağ kartı yapar; `S02module` + `S40network` ile açılışta otomatik yüklenir.
- NFS + TFTP ile rootfs ve kernel bilgisayardan gelir; dosyayı kopyalamak, kartta denemek için yeterli olur.
- SSH için Dropbear, dinamik programlar için `/lib`'e toolchain sysroot'undaki kütüphaneler gerekir.

## <a name="c12-1213-karşılaşılabilecek-problemler"></a>12.13 Karşılaşılabilecek Problemler

![Sık görülen hatalar (temsili)](../images/busybox/11_errors.png)

| Belirti | Sebep | Çözüm |
|---|---|---|
| `Kernel panic - not syncing: No working init found` | `/sbin/init` yok, ARM için derlenmemiş ya da dinamik derlenmiş ama `/lib`'te kütüphane yok | `file bin/busybox` → ARM ve statik olmalı (veya [12.11](#c12-1211-challenge-2-busyboxı-dinamik-derlemek)) |
| `can't open /dev/tty2: No such file or directory` | `/etc/inittab` yok, BusyBox varsayılan olarak tty2–tty4'ü açmaya çalışıyor | [12.5](#c12-125-busybox-init-inittab-ve-rcs)'teki `inittab`'ı ekle |
| `/etc/init.d/rcS: Permission denied` | Betik çalıştırılabilir değil | `chmod +x etc/init.d/rcS etc/init.d/S*` |
| `modprobe: can't change directory to '/lib/modules'` | Modüller kurulmamış ya da sürüm klasörü `uname -r` ile uyuşmuyor | `modules_install INSTALL_MOD_PATH=...` ile yeniden kur |
| `VFS: Unable to mount root fs via NFS` | NFS sürümü (v2), `exports` hatası, yanlış `ip=` / `nfsroot=` | `nfsroot=...,v3,tcp`; host'ta `showmount -e`; firewall'da NFS'e izin |
| `ifup: can't open '/etc/network/interfaces'` | Dosya yok | [12.7](#c12-127-usb-üzerinden-ethernet-ve-sürücüleri-açılışta-yüklemek)'deki dosyayı oluştur |
| `run-parts: /etc/network/if-pre-up.d: No such file or directory` | BusyBox `ifup`'ın aradığı klasörler yok | `mkdir -p etc/network/if-{pre-up,up,down,post-down}.d` |
| SSH: `PTY allocation request failed` | `/dev/pts` bağlı değil | `rcS`'e `mount -t devpts devpts /dev/pts` ekle |
| SSH: `Permission denied` | root'un şifresi yok | Kartta `passwd` |
| Derleme: `networking/tc.c: error: 'TCA_CBQ_MAX' undeclared` | Toolchain'in kernel başlıkları çok yeni (6.8+), BusyBox 1.36'nın `tc` applet'i derlenmiyor | `menuconfig` → Networking Utilities → `tc`'yi kapat |
| Kartta dosyalar `root` yerine `nobody` sahipliğinde görünüyor | `no_root_squash` eksik | `/etc/exports`'a ekle, `sudo exportfs -ra` |

