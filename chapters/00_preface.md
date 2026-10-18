# Önsöz

Bu kitap, gömülü Linux'a (Embedded Linux) yeni başlayan biri için yazıldı. Bir <b>{{board.name}}</b> kartını sıfırdan alıp önce hazır dosyalarla, sonra kendi derlediğin bootloader ile açacaksın. Her adımda <b>neyi neden yaptığını</b> görmen hedefleniyor.

Kitap, bir Embedded Linux kursunu ([{{course.repo}}]({{course.repo}})) takip ederken alınan notlardan oluştu. Kursla birlikte de tek başına da okunabilir.

---

## Bir Embedded Linux Sistemi Nelerden Oluşur?

Masaüstü bilgisayarda bu parçaları hiç görmeyiz; hepsi hazır gelir. Gömülü sistemde ise her birini tek tek hazırlamak, karta koymak ve birbirine bağlamak bizim işimizdir:

```
           ┌──────────────────────────────────────────────────┐
  KART     │ 4. Root filesystem  /bin /etc /lib ... programlar │  Bölüm 4, 6, 7
           │ 3. Linux kernel  +  Device Tree (.dtb)            │  Bölüm 3, 10
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
| <b>Linux kernel + Device Tree</b> | İşletim sisteminin çekirdeği ve kartın donanımını kernel'e tarif eden dosya | [Bölüm 10](10_device_tree.md) |
| <b>Root filesystem</b> | Kernel açıldıktan sonra çalışan her şey: kabuk, komutlar, ayar dosyaları | [Bölüm 4](04_sd_card_boot.md), [Bölüm 6](06_uboot_uenv.md), [Bölüm 7](07_uart_boot.md) |

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
| <b>IV — Linux Kernel</b> | [10. Linux Device Tree](10_device_tree.md) | Kernel'in donanımı nasıl tanıdığını öğren |

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
| {{board.name}} (Rev C) | Kitabın kartı |
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
| Cross toolchain, U-Boot kaynağı | Derleme bölümünde kurulur ([Bölüm 9](09_uboot_build.md)) |

---

## Bu Kitaptaki Sürümler

Komutlarda ve ekran görüntülerinde geçen sürümler şunlardır. Kendi kurulumunda farklı bir sürüm kullanıyorsan komutlardaki sürüm numaralarını ona göre değiştir.

| Ne? | Değer | Bölüm |
|---|---|---|
| Kursun hazır imajları: MLO / U-Boot | U-Boot {{prebuilt.uboot_version}} | 4, 6, 7, 8 |
| Kursun hazır imajları: Linux kernel | {{prebuilt.kernel_version}} (Ångström) | 4, 6, 7, 8 |
| eMMC'ye yüklenen Debian imajı | `{{prebuilt.debian_image}}` | 5 |
| Kendi derlediğimiz U-Boot | {{build.uboot_version}} (`{{build.uboot_defconfig}}`) | 9 |
| Cross toolchain | Linaro GCC {{build.gcc_version}} ({{build.linaro_release}}) | 9 |
| Host PC IP / kart IP | {{network.host_ip}} / {{network.board_ip}} | 8 |

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

- Kursun deposu: [{{course.repo}}]({{course.repo}})
- [BeagleBone Black resmi dokümanı](https://docs.beagleboard.org/boards/beaglebone/black/index.html)
- AM335x Technical Reference Manual (TRM): repodaki `am335x_referance_manuel.pdf`
- [U-Boot dokümantasyonu](https://docs.u-boot.org/)
- [Bootlin eğitim materyalleri](https://bootlin.com/training/) (CC BY-SA 3.0)
