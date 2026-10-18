<!-- Bu dosya otomatik üretildi. Düzenlemek için chapters/ altındaki kaynağı değiştir. -->
# Önsöz

Bu kitap, gömülü Linux'a (Embedded Linux) yeni başlayan biri için yazıldı. Bir <b>BeagleBone Black</b> kartını sıfırdan alıp önce hazır dosyalarla, sonra kendi derlediğin bootloader ile açacaksın. Her adımda <b>neyi neden yaptığını</b> görmen hedefleniyor.

Kitap, bir Embedded Linux kursunu ([https://github.com/niekiran/EmbeddedLinuxBBB](https://github.com/niekiran/EmbeddedLinuxBBB)) takip ederken alınan notlardan oluştu. Kursla birlikte de tek başına da okunabilir.

---

## Bir Embedded Linux Sistemi Nelerden Oluşur?

Masaüstü bilgisayarda bu parçaları hiç görmeyiz; hepsi hazır gelir. Gömülü sistemde ise her birini tek tek hazırlamak, karta koymak ve birbirine bağlamak bizim işimizdir:

```
           ┌──────────────────────────────────────────────────┐
  KART     │ 4. Root filesystem  /bin /etc /lib ... programlar │  Bölüm 6, 12, 13
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
| <b>Cross toolchain</b> | PC'de (x86) çalışıp karta (ARM) uygun program üreten derleyici ve araçlar | [Bölüm 9](09_uboot_build.md) |
| <b>Bootloader</b> | Kart açılınca belleği hazırlar, kernel'i ve device tree'yi RAM'e yükleyip başlatır | [Bölüm 3](03_boot_process.md) – [Bölüm 9](09_uboot_build.md) |
| <b>Linux kernel + Device Tree</b> | İşletim sisteminin çekirdeği ve kartın donanımını kernel'e tarif eden dosya | [Bölüm 10](10_linux_kernel.md), [Bölüm 11](11_device_tree.md) |
| <b>Root filesystem</b> | Kernel açıldıktan sonra çalışan her şey: kabuk, komutlar, ayar dosyaları | [Bölüm 6](06_uboot_uenv.md), [Bölüm 12](12_busybox_rootfs.md), [Bölüm 13](13_buildroot.md) |

---

## Kitabın Haritası

| Kısım | Bölüm | Ne yapacaksın? |
|---|---|---|
| <b>I — Başlarken</b> | [1. BeagleBone Black Donanımı](01_bbb_hardware.md) | Kartı, butonları, LED'leri ve debug header'ını tanı |
| | [2. Seri Konsol ve Minicom](02_serial_console.md) | Kartın konsolunu bilgisayarda gör |
| <b>II — Boot Süreci</b> | [3. Linux Boot Süreci](03_boot_process.md) | Kart açılırken hangi programın hangi sırayla çalıştığını öğren |
| | [4. SD Karttan Boot](04_sd_card_boot.md) | SD kartı hazırla, kartı adım adım SD karttan aç |
| | [5. eMMC'den Boot](05_emmc_boot.md) | Kartın dahili belleğine güncel Debian yükle |
| <b>III — U-Boot ile Çalışmak</b> | [6. U-Boot Komut Satırı ve uEnv.txt](06_uboot_uenv.md) | U-Boot'u durdur, ayarlarını değiştir, rootfs'i tanı |
| | [7. Seri Porttan (UART) Boot](07_uart_boot.md) | Kartı SD kart ve eMMC olmadan, sadece seri kabloyla aç |
| | [8. TFTP ile Ağdan Boot](08_tftp_boot.md) | Kernel'i her seferinde ağdan çekerek geliştirmeyi hızlandır |
| | [9. Cross Toolchain, SPL ve U-Boot Derleme](09_uboot_build.md) | Bootloader'ı kaynak koddan kendin derle |
| <b>IV — Linux Kernel</b> | [10. Linux Kernel: Kaynak Ağacı ve Derleme](10_linux_kernel.md) | Kernel kaynağında gezin, kernel'i ve modülleri derle |
| | [11. Linux Device Tree](11_device_tree.md) | Kernel'in donanımı nasıl tanıdığını öğren |
| <b>V — Root Filesystem</b> | [12. BusyBox ile Minimal Root Filesystem](12_busybox_rootfs.md) | Kendi rootfs'ini sıfırdan kur, NFS ile bilgisayardan aç |
| | [13. Buildroot](13_buildroot.md) | Bütün sistemi tek komutla derle, hazır SD kart imajı üret |
| <b>VI — Uygulama Geliştirme ve Donanım</b> | [14. Eclipse ile Uygulama Geliştirme](14_eclipse.md) | Eclipse'te ARM için program yaz, tek tıkla kartta çalıştır |
| | [15. AM335x GPIO'ları, Pin Ayarları ve sysfs](15_gpio_sysfs.md) | Pinmux'u çöz, LED'leri ve GPIO'ları komut satırından ve C'den kontrol et |

<b>Hazırlanan bölümler:</b> Kursun kalan konuları kitaba eklendikçe bu tabloya girecek: harici LED, 7-segment gösterge, MPU6050 ivmeölçer/jiroskop, 16x2 LCD.

<b>Okuma sırası:</b> Bölümler birbirinin üzerine kurulu. İlk kez okuyorsan sırayla git. Her bölümün başındaki <b>"Ön koşul"</b> satırı, o bölümden önce hangilerini bilmen gerektiğini söyler.

Her bölüm aynı düzende yazıldı:

1. <b>Bu bölümde:</b> Bölümün sonunda neleri yapabileceğin.
2. <b>Konu anlatımı ve adım adım uygulama:</b> Komutlar hem terminal görüntüsü olarak hem de kopyalanabilir kod bloğu olarak verilir.
3. <b>Özet:</b> Bölümün tek bakışta tekrarı.
4. <b>Karşılaşılabilecek problemler:</b> Sık görülen hatalar, sebepleri ve çözümleri.

---

## Gerekenler

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
| <b>Ubuntu</b> (host PC) | Gerçek kurulum ya da sanal makine. Sanal makinede ağ ayarı <b>Bridged</b> olmalı ([Bölüm 8](08_tftp_boot.md)). |
| `minicom`, `lrzsz` | Seri konsol ve Xmodem/Ymodem ile dosya gönderme ([Bölüm 2](02_serial_console.md)) |
| `gparted` | SD kartı bölümlemek için ([Bölüm 4](04_sd_card_boot.md)) |
| `tftpd-hpa` | TFTP sunucusu ([Bölüm 8](08_tftp_boot.md)) |
| `nfs-kernel-server` | Rootfs'i ağdan bağlamak için NFS sunucusu ([Bölüm 12](12_busybox_rootfs.md)) |
| Eclipse (Eclipse IDE for C/C++ Developers) | Uygulama geliştirme ([Bölüm 14](14_eclipse.md)) |
| Cross toolchain, U-Boot, kernel, BusyBox kaynakları | Derleme bölümlerinde kurulur ([Bölüm 9](09_uboot_build.md), [Bölüm 10](10_linux_kernel.md), [Bölüm 12](12_busybox_rootfs.md)) |

---

## Bu Kitaptaki Sürümler

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
| Buildroot (LTS) | 2026.02.3 (kernel 6.18.1, U-Boot 2026.01) | 13 |
| Eclipse | 2026-09 (Eclipse IDE for C/C++ Developers) | 14 |
| Host PC IP / kart IP | 192.168.27.1 / 192.168.27.2 | 8 |

---

## Yazım Kuralları

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

## Kaynaklar

- Kursun deposu: [https://github.com/niekiran/EmbeddedLinuxBBB](https://github.com/niekiran/EmbeddedLinuxBBB)
- [BeagleBone Black resmi dokümanı](https://docs.beagleboard.org/boards/beaglebone/black/index.html)
- AM335x Technical Reference Manual (TRM): repodaki `am335x_referance_manuel.pdf`
- [U-Boot dokümantasyonu](https://docs.u-boot.org/)
- [Bootlin eğitim materyalleri](https://bootlin.com/training/) (CC BY-SA 3.0)

---

[İçindekiler](README.md) · [Bölüm 1: BeagleBone Black Donanımı →](01_bbb_hardware.md)
