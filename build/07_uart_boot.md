<!-- Bu dosya otomatik üretildi. Düzenlemek için chapters/ altındaki kaynağı değiştir. -->
# Bölüm 7 — Seri Porttan (UART) Boot

> <b>Bu bölümde:</b>
> - BeagleBone Black'i <b>SD kart ve eMMC kullanmadan</b>, bütün boot dosyalarını bilgisayardan <b>seri port (UART0)</b> üzerinden göndererek açacaksın.
> - Xmodem ve Ymodem protokollerinin farkını ve ROM Code'un UART boot davranışını öğreneceksin.
> - Kernel, DTB ve initramfs'i RAM'de nereye yükleyeceğini ve `bootm` ile nasıl başlatacağını göreceksin.
>
> <b>Ön koşul:</b> [Bölüm 2](02_serial_console.md) — Minicom, [Bölüm 3](03_boot_process.md) — boot sırası, [Bölüm 6](06_uboot_uenv.md) — `loady` ile dosya gönderme.

---

## 7.1 Dosya Transfer Protokolleri

![IP ağı ve UART üzerinden dosya transfer protokolleri](../images/{CD17FB50-958F-4863-B8A4-DED33A61A342}.png)

Bilgisayardan karta dosya göndermenin iki yolu var:

| Bağlantı | Protokoller | Ne zaman kullanılır? |
|---|---|---|
| <b>IP ağı (Ethernet)</b> | TFTP, HTTP, FTP, SMTP... | Kartta çalışan bir ağ yığını (U-Boot veya Linux) varsa. Hızlıdır ([Bölüm 8](08_tftp_boot.md)). |
| <b>UART (seri port)</b> | Xmodem, Ymodem, Zmodem, Kermit... | Ağ yokken veya kartta henüz hiçbir yazılım yokken. Yavaştır ama çok basittir. |

UART sadece ham baytları taşır; "dosya nerede başlıyor, nerede bitiyor, veri bozuldu mu?" gibi bilgileri taşımaz. <b>Xmodem / Ymodem</b> gibi protokoller veriyi paketlere bölüp her pakete kontrol bilgisi (checksum / CRC) ekler, bozuk paketi tekrar istetir.

| Protokol | Özellik |
|---|---|
| <b>Xmodem</b> | 128 bayt (Xmodem-1K'da 1024 bayt) paketler. Dosya adı ve boyutu göndermez. AM335x'in <b>ROM kodu</b> bunu kullanır. |
| <b>Ymodem</b> | Xmodem'in geliştirilmiş hali: dosya adını ve boyutunu da gönderir. U-Boot'ta `loady` komutu. |

---

## 7.2 Seri Boot Fikri

![Boot dosyaları bilgisayarda, UART0 ile karta seri bağlantı](../images/{E3C79A57-76F0-41F6-B314-EE88AB46B638}.png)

Bütün boot dosyaları — <b>SPL, U-Boot, Linux kernel (uImage), DTB ve dosya sistemi</b> — kartta değil, <b>bilgisayarda (HOST)</b> durur. Kart ile bilgisayar arasındaki tek bağlantı, J1 header'daki <b>UART0</b> pinlerine bağlı USB-TTL seri kablodur. Kart açılırken her dosyayı bu kablo üzerinden sırayla göndeririz.

Bu yöntem şu durumlarda işe yarar:
- SD kart ve eMMC boşsa veya içindeki bootloader bozulduysa (kartı "kurtarmak" için).
- Yeni derlenmiş bir SPL / U-Boot'u karta yazmadan denemek için.

---

## 7.3 Kartı UART Boot Moduna Sokmak

![Seri boot nasıl çalışır: S2 basılı tutulur, S3 ile açılır, SD kart takılı olmaz](../images/{A0655836-7172-4895-8690-5553D0FF2841}.png)

Kartı UART'tan boot ettirmek için SD karttan boot ederken yaptığımızın aynısını yaparız:

1. <b>S2 (BOOT)</b> butonuna basılı tut,
2. <b>S3 (POWER)</b> butonuna basıp bırak (veya beslemeyi tak),
3. Boot başladıktan sonra S2'yi bırak.

Tek fark: <b>SD kart takılı olmamalı.</b> Takılıysa ROM kodu boot dosyalarını SD karttan bulur ve UART'a hiç sıra gelmez.

### AM335x boot sırası

![AM335x boot sırası: S2 basılı değilken ve basılıyken](../images/{A096CE0C-645B-42AB-8840-75924AC5A492}.png)

AM335x'in içindeki ROM kodu, açılışta `SYSBOOT[4:0]` pinlerine bakarak hangi çevre birimlerini hangi sırayla deneyeceğine karar verir ([3.5](03_boot_process.md#35-boot-kaynakları-ve-boot-sırası-sysboot-pinleri)). BBB'de S2 butonu bu pinlerden birinin değerini değiştirir:

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

![AM335x TRM: UART boot ayrıntıları ve USB boot için Silicon Errata notu](../images/{F394BE8C-59F6-4D82-A192-63B1BE6F6FBA}.png)

AM335x Technical Reference Manual'ın (TRM) <b>26.1.8.6 USB Boot Procedure</b> bölümünde, USB boot'un kısıtlamaları için <b>Silicon Errata (SPRZ360)</b> belgesine bakılması söyleniyor:

![Silicon Errata Advisory 1.0.25: Ethernet boot başarısız olursa sistem 4.5 dakika bekler](../images/{17AE38E2-B3D5-4F02-ADA3-822CF3DD8D76}.png)

Errata'daki <b>Advisory 1.0.25</b>'te Ethernet denilmiş, ancak bu durum USB için de geçerli. Çünkü AM335x'in ROM kodu USB boot'u, USB kablosu üzerinden <b>sanal bir Ethernet bağlantısı (RNDIS)</b> kurarak yapar. Yani USB boot aslında "USB üzerinden Ethernet boot"tur ve aynı 4.5 dakikalık beklemeye takılır.

### Çözüm: Kartı harici adaptörle beslemek

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

## 7.4 ROM Kodunun UART Boot Davranışı

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

## 7.5 Önerilen RAM Yükleme Adresleri

![Önerilen DDR RAM yükleme adresleri](../images/{41B45262-4937-487E-BD2D-CC0D2D385CBF}.png)

U-Boot'a geldikten sonra kernel, DTB ve dosya sistemini RAM'e (DDR, `0x80000000`'dan başlar) yükleyeceğiz. Dosyaların birbirinin üzerine yazmaması için bu adresler kullanılır:

| Dosya | Adres |
|---|---|
| Kernel (`uImage`) | `0x82000000` |
| Device tree (`.dtb`) | `0x88000000` |
| initramfs | `0x88080000` |

Seri boot'ta SD kart ve eMMC kullanılmadığı için rootfs'i bağlayacak bir disk yoktur. Bu yüzden dosya sistemi de RAM'e yüklenir: <b>RAMDISK / INITRAMFS</b>, RAM'de duran küçük bir rootfs'tir. DTB'ye ayrılan alan `0x88000000` – `0x8807FFFF` arası (512 KB) olduğu için initramfs hemen arkasından, `0x88080000`'dan başlar.

---

## 7.6 Özet: Seri Boot Adımları

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

## 7.7 Elimizdeki Boot Dosyaları Nedir?

Seri boot için bilgisayarda (HOST) şu 5 dosya hazır olmalı. Her biri boot zincirinin bir halkasıdır; her dosyanın işi bir sonrakini yükleyip çalıştırmaktır:

| Dosya | Nedir? | Kim yükler? | Nereye yüklenir? | Protokol |
|---|---|---|---|---|
| <b>`u-boot-spl.bin`</b> | <b>SPL</b> (Secondary Program Loader). U-Boot'un küçük ilk aşaması. Saatleri, pin ayarlarını, UART'ı ve en önemlisi <b>DDR RAM</b>'i hazırlar. | ROM kodu | AM335x'in iç SRAM'i (`0x402F0400`, en fazla ~109 KB) | Xmodem |
| <b>`u-boot.img`</b> | Asıl <b>U-Boot</b>. Başında 64 baytlık U-Boot (mkimage) başlığı vardır. Komut satırını (`=>`) bize o verir. | SPL | DDR (`0x80800000`) | Ymodem |
| <b>`uImage`</b> | <b>Linux kernel</b>. `zImage`'in başına U-Boot başlığı (yükleme adresi, giriş noktası, CRC) eklenmiş hali ([4.9](04_sd_card_boot.md#49-uimage-nedir)). | U-Boot (`loadx`) | `0x82000000` | Xmodem |
| <b>`am335x-boneblack.dtb`</b> | <b>Device Tree Blob</b>. Kernel'e kartta hangi donanımın olduğunu anlatan derlenmiş dosya ([Bölüm 11](11_device_tree.md)). | U-Boot (`loadx`) | `0x88000000` | Xmodem |
| <b>`initramfs`</b> | RAM'de çalışan küçük <b>kök dosya sistemi</b> (genellikle BusyBox). `cpio` arşivi + gzip + U-Boot başlığı. SD/eMMC olmadığı için rootfs'i buradan alırız. | U-Boot (`loadx`) | `0x88080000` | Xmodem |

### Bu dosyaları nereden bulurum?

Bu dosyaları <b>kendin yazmazsın</b>. Hepsi açık kaynak projelerden (U-Boot, Linux kernel, BusyBox) çıkar; senin işin kaynak kodu indirip ayarlamak ve derlemektir. Üç yol vardır:

| Yol | Ne zaman? | Artısı / eksisi |
|---|---|---|
| <b>1. Hazır (prebuilt) dosyalar</b> | İlk deneme, "kart çalışıyor mu?" testi | En hızlısı; ama içinde ne olduğunu sen seçmezsin. |
| <b>2. Kaynak koddan elle derleme</b> | Öğrenirken (kursta yapılan) | Her adımı görürsün; daha uzun sürer. |
| <b>3. Buildroot / Yocto</b> | Gerçek projeler | Hepsini tek komutla üretir; ilk derleme uzun sürer. |

#### Yol 1 — Hazır dosyalar

- <b>Kursun kaynakları:</b> Kurslar bu dosyaları genelde derlenmiş olarak verir (Udemy ekleri / kursun GitHub reposu). Kursla birebir uyumlu oldukları için ilk seri boot denemesinde en kolayı bunlar.
- <b>TI Processor SDK (AM335x):</b> TI'ın sitesinden indirilir. `board-support/prebuilt-images/` klasöründe genellikle `MLO`, `u-boot-spl.bin`, `u-boot.img`, `zImage`, `.dtb` dosyaları ve bir rootfs hazır gelir.
- <b>BeagleBoard.org Debian imajı:</b> Bootloader, kernel ve DTB içerir ama hazır initramfs yoktur; seri boot için daha az uygundur.

#### Yol 2 — Kaynak koddan derleme

Cross toolchain kurulumu ve SPL/U-Boot derlemesi [Bölüm 9](09_uboot_build.md)'da adım adım anlatılıyor. `mkimage` aracı için `sudo apt install u-boot-tools` yeterli.

| Dosya | Kaynak kod | Çıktının yeri |
|---|---|---|
| `u-boot-spl.bin`, `u-boot.img` | <b>U-Boot</b> ([Bölüm 9](09_uboot_build.md)) | `spl/u-boot-spl.bin`, `u-boot.img` |
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

Son satırdaki `mkimage` önemli: `bootm` komutu ramdisk'in başında <b>U-Boot başlığı</b> görmek ister. Ham `initramfs.cpio.gz` gönderirsen `Wrong Ramdisk Image Format` hatası alırsın ([7.9 (g)](#g-bootm-hataları)).

#### Yol 3 — Buildroot ile hepsini tek seferde

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

### Her projede baştan mı derleyeceğim?

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

## 7.8 Adım Adım Seri Porttan Boot

> [!NOTE]
> Aşağıdaki ekran görüntüleri <b>temsilidir</b>; sürüm numaraları, tarih, boyut ve hız değerleri senin derlemene göre farklı olacaktır.

### Adım 0 — Bilgisayarda hazırlık

Bütün dosyaları tek bir klasörde topla (örnekte `~/bbb`) ve U-Boot başlıklarını `mkimage -l` ile kontrol et:

![Bilgisayarda boot dosyalarını kontrol etme](../images/serial_boot/01_host_dosyalar.png)

```bash
cd ~/bbb
ls -l
mkimage -l uImage
mkimage -l initramfs
```

`u-boot-spl.bin` <b>109 KB'tan küçük</b> olmalı; ROM kodu onu iç SRAM'e koyar ve SRAM'de daha fazla yer yoktur.

### Adım 1 — Seri kabloyu bağla, Minicom'u hazırla

USB-TTL kablosunu J1 header'a bağla (<b>GND, RX, TX</b>; kablonun RX'i kartın TX'ine, TX'i kartın RX'ine). Port adını bulma, `dialout` grubu ve Minicom ayarları [Bölüm 2](02_serial_console.md)'de anlatıldı. Kısaca:

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

### Adım 2 — Kartı UART boot modunda aç ve SPL'i gönder (Xmodem)

1. SD kartı çıkar, P4 mini USB kablosunu çıkar, 5V adaptörü hazırla ([7.3](#73-kartı-uart-boot-moduna-sokmak)).
2. Minicom açıkken <b>S2</b>'ye basılı tut, adaptörü tak / <b>S3</b>'e bas, sonra S2'yi bırak.
3. Ekranda `CCCC...` akmaya başlar: ROM kodu UART0'da Xmodem ile dosya bekliyor.
4. Minicom'da `Ctrl-A` → `S` → <b>xmodem</b> → <b>`u-boot-spl.bin`</b> seç, gönder.

![ROM kodu CCCC basıyor, SPL Xmodem ile gönderiliyor](../images/serial_boot/04_rom_spl_xmodem.png)

Transfer bitince SPL çalışır, DDR'ı hazırlar, `U-Boot SPL ...` yazısını basar ve tekrar `CCCC` basmaya başlar. Bu sefer bekleyen <b>SPL</b>'dir ve <b>Ymodem</b> ister.

### Adım 3 — U-Boot'u gönder (Ymodem)

> [!NOTE]
> Kursun `serial-boot` klasöründeki dosyalar: SPL <b>2017.03</b>, U-Boot <b>2016.11-rc1</b>. Bu sürümlerde U-Boot'un komut istemi `=>`'dir. [Bölüm 4](04_sd_card_boot.md)'teki eski Ångström U-Boot'u (2013.04) ise `U-Boot#` gösterir. Komutlar ikisinde de aynıdır.

1. `Ctrl-A` → `S` → <b>ymodem</b> → <b>`u-boot.img`</b> seç, gönder.
2. U-Boot açılır. `Hit any key to stop autoboot` çıkınca <b>hemen bir tuşa bas.</b>

![u-boot.img Ymodem ile gönderiliyor, U-Boot komut satırı](../images/serial_boot/05_spl_uboot_ymodem.png)

> [!WARNING]
> Autoboot'u durdurmazsan U-Boot kendi `bootcmd`'ini çalıştırır ve kartın <b>eMMC</b>'sindeki Linux'u (ör. Debian) açar. O zaman seri boot'un amacı boşa gider; kartı kapatıp Adım 2'den başla.

### Adım 4 — Kernel'i RAM'e al: `loadx 0x82000000`

```text
=> loadx 0x82000000
```

U-Boot Xmodem ile beklemeye başlar. Minicom'da `Ctrl-A` → `S` → <b>xmodem</b> → <b>`uImage`</b>.

![loadx ile uImage gönderimi](../images/serial_boot/06_loadx_uimage.png)

> [!NOTE]
> 115200 baud'da hız en fazla ~11 KB/s'dir. 4 MB'lık bir `uImage` yaklaşık <b>6–7 dakika</b> sürer; bu normaldir. Xmodem son paketi 128 bayta tamamladığı için `Total Size` dosya boyutundan biraz büyük görünür, sorun değil.

### Adım 5 — DTB ve initramfs'i RAM'e al

```text
=> loadx 0x88000000        (Minicom: xmodem -> am335x-boneblack.dtb)
=> loadx 0x88080000        (Minicom: xmodem -> initramfs)
```

![loadx ile DTB ve initramfs gönderimi](../images/serial_boot/07_loadx_dtb_initramfs.png)

### Adım 6 — Yüklenenleri kontrol et (isteğe bağlı ama önerilir)

Boot etmeden önce dosyaların sağlam geldiğini görmek, sonradan "neden açılmadı?" diye uğraşmaktan iyidir:

```text
=> iminfo 0x82000000
=> iminfo 0x88080000
=> md.b 0x88000000 4
```

![iminfo ile CRC kontrolü, md ile DTB sihirli sayısı](../images/serial_boot/08_iminfo_kontrol.png)

- `iminfo`, U-Boot başlığındaki CRC'yi RAM'deki veriyle karşılaştırır. `Verifying Checksum ... OK` görmelisin.
- DTB'nin U-Boot başlığı yoktur; ilk 4 baytı her zaman <b>`d0 0d fe ed`</b> olmalıdır.

### Adım 7 — `bootargs` ayarla ve `bootm` ile boot et

```text
=> setenv bootargs console=ttyO0,115200 root=/dev/ram0 rw initrd=0x88080000
=> bootm 0x82000000 0x88080000 0x88000000
```

Boot etmeden önce kernel'e <b>rootfs'in nerede olduğunu</b> `bootargs` ile bildiriyoruz:

| Parametre | Anlamı |
|---|---|
| `console=ttyO0,115200` | Kernel mesajlarını UART0'a, 115200 baud ile bas (kursun kernel'i 3.8.13 için `ttyO0`; [7.9 (h)](#h-starting-kernel--yazıp-donuyor)). |
| `root=/dev/ram0` | Kök dosya sistemi (rootfs) bir disk değil, <b>RAM</b>'de duruyor. |
| `rw` | Rootfs okunur-yazılır bağlansın. |
| `initrd=0x88080000` | initramfs'i RAM'de <b>`0x88080000`</b> adresine yüklediğimizi kernel'e bildirir (Adım 5'teki `loadx` adresiyle aynı olmalı). |
| `bootm <kernel> <initramfs> <dtb>` | Sıra önemli: <b>kernel – ramdisk – DTB</b>. Ramdisk yoksa ortaya `-` yazılır (`bootm 0x82000000 - 0x88000000`). |

> [!NOTE]
> `bootm`'in ikinci parametresi (`0x88080000`) de initramfs'in adresini ve boyutunu kernel'e DTB'nin `/chosen` düğümü üzerinden bildirir. Yani adres iki yerden veriliyor; `bootargs`'taki `initrd=` ile `bootm`'deki adresin <b>aynı</b> olduğuna dikkat et. `printenv bootargs` ile yazdığını kontrol edebilirsin.

![bootm ile kernel, initramfs ve DTB'den boot](../images/serial_boot/09_bootm.png)

### Adım 8 — Linux açıldı

Kernel initramfs'i açar, içindeki `/init` (BusyBox) çalışır ve seri konsoldan kabuk gelir:

![initramfs'ten açılan BusyBox kabuğu](../images/serial_boot/10_linux_shell.png)

`mount` çıktısında `/`'nin <b>`rootfs`</b> olduğunu görürsün: Kart ne SD karta ne eMMC'ye dokunmadan, tamamen seri porttan gelen dosyalarla RAM'den çalışıyor.

> [!TIP]
> RAM'deki her şey kart kapanınca silinir. Bir sonraki açılışta bütün adımları (SPL'den itibaren) tekrar yapman gerekir.

### Komutların kısa özeti

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

## 7.9 Karşılaşılabilecek Problemler

![Sık görülen hata çıktıları (temsili)](../images/serial_boot/11_hatalar.png)

### a) Ekranda hiç `CCCC` çıkmıyor

| Olası neden | Çözüm |
|---|---|
| SD kart takılı | ROM önce MMC0'ı dener, SD'de MLO varsa oradan açılır. SD kartı çıkar. |
| P4 mini USB kablosu takılı | ROM USB0'da 4.5 dakika bekler. Kabloyu çıkar, kartı 5V adaptörle besle ([7.3](#73-kartı-uart-boot-moduna-sokmak)). |
| S2 basılı değildi | Kart eMMC'den açılır (ekranda eMMC'deki U-Boot/Linux çıkar). Kartı kapat, S2 basılıyken tekrar aç. |
| TX / RX ters bağlı ya da GND bağlı değil | Kablonun TX'i → kartın RX'i, RX'i → kartın TX'i. GND mutlaka bağlı olmalı. |
| Yanlış port / baud | `dmesg` ile doğru `/dev/ttyUSBx`'i bul; ayar 115200 8N1 olmalı. |
| Minicom'u kart açıldıktan sonra açtın | `C`'leri kaçırmış olabilirsin. Önce Minicom'u aç, sonra kartı aç. |

### b) `CCCC` var ama transfer başlamıyor / yarıda kesiliyor

| Olası neden | Çözüm |
|---|---|
| <b>Hardware Flow Control: Yes</b> | Minicom karta veri göndermez. `minicom -s` ile <b>No</b> yap (en sık yapılan hata!). |
| `lrzsz` kurulu değil (`sx: not found`) | `sudo apt install lrzsz` |
| Dosya seçmek çok uzun sürdü, ROM vazgeçti | Upload klasörünü önceden ayarla, `C` görünür görünmez gönder. `C` akışı durduysa kartın gücünü kesip S2 ile baştan aç. |
| Yanlış protokol | ROM ve `loadx` → <b>xmodem</b>; SPL'in `u-boot.img` için beklediği ve `loady` → <b>ymodem</b>. Karıştırılırsa transfer hiç başlamaz veya `Transfer incomplete` olur. |
| Transfer sırasında klavyeye basıldı | Gelen tuşlar Xmodem paketlerini bozar. Transfer bitene kadar dokunma. |

### c) SPL gönderildi ama hiçbir şey olmuyor

| Olası neden | Çözüm |
|---|---|
| `u-boot-spl.bin` yerine <b>`MLO`</b> gönderildi | MLO'nun başında GP header var; ROM onu kod sanıp çalıştırır ve kilitlenir. UART boot'ta <b>ham `u-boot-spl.bin`</b> gönderilir. |
| SPL 109 KB'tan büyük | ROM iç SRAM'e sığdıramaz. SPL'deki gereksiz özellikleri kapatıp yeniden derle. |
| SPL farklı bir kart/işlemci için derlenmiş | BBB için uygun defconfig ile yeniden derle ([9.3](09_uboot_build.md#93-adım-adım-toolchain-kurulumu-ve-u-boot-derleme)). |

### d) SPL çalışıyor ama `u-boot.img` yüklenmiyor

| Olası neden | Çözüm |
|---|---|
| SPL, UART'tan Ymodem alma desteğiyle derlenmemiş (`CONFIG_SPL_YMODEM_SUPPORT`) | SPL başka bir aygıt (MMC) arar ve hata verir. Config'te YMODEM desteğini aç, yeniden derle. |
| `u-boot.img` Xmodem ile gönderildi | SPL Ymodem bekler; <b>ymodem</b> seç. |
| `u-boot.img` yerine `u-boot.bin` gönderildi | SPL, başında mkimage başlığı olan `u-boot.img`'i bekler. |

### e) U-Boot açıldı ama kendi kendine eMMC'den boot etti

`Hit any key to stop autoboot` sırasında tuşa basılmadı. Kartı kapatıp baştan başla; geri sayım başlar başlamaz bir tuşa bas.

> [!CAUTION]
> Seri boot sırasında U-Boot'ta <b>`saveenv` yapma</b>. Değişkenler eMMC'deki ortama yazılır ve kartın normal açılışını bozabilir.

### f) Transfer çok yavaş

115200 baud'da ~11 KB/s normaldir; `uImage` 6–7 dakika, initramfs birkaç dakika sürer. Hızlandırmak için:

- <b>Baud yükseltme:</b> `loadx`/`loady` ikinci parametre olarak baud alır: `loady 0x82000000 460800`. U-Boot hızı değiştirmeni ister; Minicom'da `Ctrl-A` → `P` ile aynı hıza geç, Enter'a bas, gönder. Bitince U-Boot 115200'e dönmeni ister; Minicom'u geri al ve <b>ESC</b>'ye bas. (Her USB-TTL kablo yüksek hızlarda güvenilir çalışmaz; hata alırsan 115200'e dön.)
- <b>Ymodem:</b> `loady` 1 KB'lık paketlerle çalıştığı için `loadx`'ten biraz daha hızlıdır.
- <b>TFTP:</b> U-Boot açıldıktan sonra Ethernet kablosu varsa `tftpboot` ile saniyeler içinde yüklenir ([Bölüm 8](08_tftp_boot.md)).

### g) `bootm` hataları

| Hata | Neden | Çözüm |
|---|---|---|
| `Wrong Ramdisk Image Format` / `Ramdisk image is corrupt or invalid` | initramfs'in başında U-Boot başlığı yok veya yanlış adrese yüklendi | Bilgisayarda `mkimage -T ramdisk ...` ile başlık ekle ([7.7](#77-elimizdeki-boot-dosyaları-nedir)). `iminfo 0x88080000` ile kontrol et. |
| `Bad Data CRC` | Transfer sırasında veri bozuldu ya da bir dosya diğerinin üstüne yazıldı | Dosyayı tekrar gönder. Adresleri [7.5](#75-önerilen-ram-yükleme-adresleri)'teki gibi kullan; DTB 512 KB'ı aşmamalı. |
| `Bad Magic Number` / `Wrong Image Format for bootm command` | `uImage` yerine `zImage` gönderildi veya adres yanlış | Kernel'i `make uImage LOADADDR=0x80008000` ile derle ya da `zImage` için `bootz` kullan. |
| DTB bulunamadı / `FDT_ERR_BADMAGIC` | DTB bozuk ya da yanlış adrese yüklendi | `md.b 0x88000000 4` → `d0 0d fe ed` görmelisin. Görmüyorsan DTB'yi tekrar gönder. |

### h) `Starting kernel ...` yazıp donuyor

| Olası neden | Çözüm |
|---|---|
| `console=` yanlış | Eski kernel'ler (3.x, TI omap-serial sürücüsü) → `ttyO0`. Daha yeni (4.x ve sonrası) kernel'lerde genellikle `ttyS0`. Kernel aslında açılmış olabilir, sadece mesajları başka yere basıyordur. |
| DTB, kernel sürümüyle uyumsuz | DTB'yi <b>aynı kernel kaynağından</b> derlenmiş olanla değiştir; BBB için `am335x-boneblack.dtb` (`am335x-bone.dtb` değil). |
| `bootm` parametre sırası yanlış | Sıra: `bootm <kernel> <ramdisk> <dtb>`. |

### i) Kernel açılıyor ama panic veriyor

| Hata | Neden | Çözüm |
|---|---|---|
| `VFS: Unable to mount root fs on unknown-block(1,0)` | initramfs içinde <b>`/init`</b> yok; kernel `root=/dev/ram0`'ı bağlamaya çalışıyor ve başarısız oluyor | rootfs klasöründe `ln -s sbin/init init` yapıp initramfs'i yeniden oluştur, ya da `bootargs`'a `rdinit=/sbin/init` ekle. |
| `VFS: Unable to mount root fs on unknown-block(0,0)` | Kernel ramdisk'i hiç almamış veya `CONFIG_BLK_DEV_INITRD` kapalı | `bootm`'in ikinci parametresini kontrol et; kernel config'te initramfs/initrd desteğini aç. |
| `Failed to execute /init` / `No working init found` | initramfs'teki programlar ARM için derlenmemiş veya kütüphaneler eksik | BusyBox'ı `CROSS_COMPILE=arm-linux-gnueabihf-` ile ve tercihen <b>static</b> derle; dinamik derlediysen `lib/` klasörüne gerekli kütüphaneleri koy. `file bin/busybox` → `ARM` yazmalı. |
| `RAMDISK: incomplete write` | initramfs yerine ext2 <b>initrd</b> imajı kullanılıyor ve kernel'in varsayılan ramdisk boyutundan büyük | `bootargs`'a `ramdisk_size=<KB>` ekle. |

### j) Ekranda bozuk / anlamsız karakterler

Baud rate uyuşmuyor. Minicom 115200 8N1 olmalı. Baud yükseltme ([f](#f-transfer-çok-yavaş)) denediysen Minicom'u tekrar 115200'e al.

---

[← Bölüm 6: U-Boot Komut Satırı ve uEnv.txt](06_uboot_uenv.md) · [İçindekiler](README.md) · [Bölüm 8: TFTP ile Ağdan Boot →](08_tftp_boot.md)
