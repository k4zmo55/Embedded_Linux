# Embedded Linux

**BeagleBone Black ile Adım Adım**

<!-- Bu dosya otomatik üretildi (python tools/book.py build). Elle düzenleme. -->

Gömülü Linux'a yeni başlayanlar için adım adım bir rehber: kartı tanımaktan, SD karttan, seri porttan ve ağdan boot etmeye, bootloader'ı kendin derlemeye ve device tree'ye kadar.

📖 <b>Okumak için:</b> [build/README.md](build/README.md) (bölüm bölüm) · [Embedded_Linux.md](build/Embedded_Linux.md) (tek parça) · [Embedded_Linux.pdf](build/Embedded_Linux.pdf)

## İçindekiler

- [Önsöz](build/00_preface.md)

**Kısım I — Başlarken**

- [Bölüm 1 — BeagleBone Black Donanımı](build/01_bbb_hardware.md)
- [Bölüm 2 — Seri Konsol ve Minicom](build/02_serial_console.md)

**Kısım II — Boot Süreci**

- [Bölüm 3 — Linux Boot Süreci: RBL → SPL → U-Boot](build/03_boot_process.md)
- [Bölüm 4 — SD Karttan Boot](build/04_sd_card_boot.md)
- [Bölüm 5 — eMMC'den Boot](build/05_emmc_boot.md)

**Kısım III — U-Boot ile Çalışmak**

- [Bölüm 6 — U-Boot Komut Satırı ve uEnv.txt](build/06_uboot_uenv.md)
- [Bölüm 7 — Seri Porttan (UART) Boot](build/07_uart_boot.md)
- [Bölüm 8 — TFTP ile Ağdan Boot](build/08_tftp_boot.md)
- [Bölüm 9 — Cross Toolchain, SPL ve U-Boot Derleme](build/09_uboot_build.md)

**Kısım IV — Linux Kernel**

- [Bölüm 10 — Linux Kernel: Kaynak Ağacı ve Derleme](build/10_linux_kernel.md)
- [Bölüm 11 — Linux Device Tree](build/11_device_tree.md)

**Kısım V — Root Filesystem**

- [Bölüm 12 — BusyBox ile Minimal Root Filesystem](build/12_busybox_rootfs.md)
- [Bölüm 13 — Buildroot](build/13_buildroot.md)

**Kısım VI — Uygulama Geliştirme ve Donanım**

- [Bölüm 14 — Eclipse ile Uygulama Geliştirme](build/14_eclipse.md)
- [Bölüm 15 — AM335x GPIO'ları, Pin Ayarları ve sysfs](build/15_gpio_sysfs.md)
- [Bölüm 16 — Harici LED Bağlamak](build/16_external_led.md)
- [Bölüm 17 — 7-Segment Gösterge](build/17_seven_segment.md)

## Bu Repo Nasıl Çalışır?

| Yer | Ne var? |
|---|---|
| `chapters/` | Bölümlerin kaynağı. Düzenleme burada yapılır. |
| `book.toml` | Bölüm sırası ve kursa bağlı değerler (sürümler, IP'ler). Bölümlerde `{{grup.isim}}` olarak geçer. |
| `images/` | Görseller. Terminal görüntüleri `tools/*_shots.py` ile üretilir. |
| `build/` | Otomatik üretilen, okunacak kitap. Elle düzenlenmez. |
| `CLAUDE.md` | Yazım kuralları ve yeni not ekleme adımları |

```bash
python tools/book.py check     # kitaba eklenmemiş not, kırık link, eski build var mı?
python tools/book.py build     # build/ klasörünü, terminal görüntülerini ve PDF'i üret
python tools/book.py renumber  # araya bölüm eklendiyse numaraları yeniden düzenle
```
