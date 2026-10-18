<!-- Bu dosya otomatik üretildi. Düzenlemek için chapters/ altındaki kaynağı değiştir. -->
# Bölüm 13 — Buildroot

> <b>Bu bölümde:</b>
> - Buildroot'un ne olduğunu ve önceki bölümlerde elle yaptığımız işleri nasıl tek komuta indirdiğini öğreneceksin.
> - Buildroot'un klasör yapısını ve temel komutlarını tanıyacaksın.
> - BeagleBone Black için toolchain, U-Boot, kernel ve rootfs'i tek seferde derleyip hazır bir SD kart imajı üreteceksin.
> - Rootfs'e SSH (Dropbear), root şifresi ve ağ ayarı ekleyeceksin.
> - Buildroot içinden kernel ve U-Boot ayarlarını değiştirip yeniden derleyeceksin.
>
> <b>Ön koşul:</b> [Bölüm 9](09_uboot_build.md) — U-Boot derleme, [Bölüm 10](10_linux_kernel.md) — kernel derleme, [Bölüm 12](12_busybox_rootfs.md) — BusyBox rootfs.

---

## 13.1 Buildroot Nedir?

Şimdiye kadar bir Embedded Linux sisteminin dört parçasını <b>tek tek, elle</b> hazırladık:

| Parça | Elle (önceki bölümler) | Buildroot ile |
|---|---|---|
| Cross toolchain | Linaro arşivini indir, `PATH`'e ekle ([Bölüm 9](09_uboot_build.md)) | Hazır toolchain'i kendisi indirir ya da sıfırdan derler |
| U-Boot + SPL | Kaynağı indir, `defconfig`, `make` ([Bölüm 9](09_uboot_build.md)) | `make` |
| Kernel + DTB + modüller | Kaynağı indir, `defconfig`, `uImage dtbs modules` ([Bölüm 10](10_linux_kernel.md)) | `make` |
| Rootfs | BusyBox derle, klasörleri ve betikleri elle yaz ([Bölüm 12](12_busybox_rootfs.md)) | `make` |
| Ek programlar (Dropbear, kütüphaneler...) | Her birini ayrı cross compile et | Menüden seç, `make` |
| SD kart | GParted ile bölümle, dosyaları kopyala ([Bölüm 4](04_sd_card_boot.md)) | Hazır `sdcard.img`'yi karta yaz |

<b>Buildroot</b>, bütün bu adımları yapan bir <b>derleme sistemidir</b>. Makefile'lar ve Kconfig'den oluşur: ne istediğini `menuconfig` ile seçersin, `make` her şeyi indirip doğru sırayla derler ve kartına yazılacak imajları üretir.

```
                           ┌───────────────── make ─────────────────┐
  .config  ──►  Buildroot  │ indir → yamala → yapılandır → derle → kur │ ──►  output/images/
 (menuconfig)              └─────────────────────────────────────────┘      MLO, u-boot.img, zImage,
                                                                            *.dtb, rootfs.ext4, sdcard.img
```

> [!NOTE]
> Benzer bir araç olan <b>Yocto Project</b> çok daha esnek ama öğrenmesi de çok daha zordur. Buildroot küçük ve orta ölçekli projeler, öğrenme ve hızlı prototip için idealdir. İkisi de aynı fikre dayanır: bütün sistemi tarif eden bir yapılandırma ve onu derleyen bir sistem.

---

## 13.2 Sürüm ve Kurulum

Buildroot her üç ayda bir sürüm çıkarır (`YYYY.02`, `.05`, `.08`, `.11`). Şubat sürümleri bir yıl desteklenen <b>LTS</b> sürümlerdir. Bu kitapta güncel LTS olan <b>2026.02.3</b> kullanılıyor.

> [!NOTE]
> Kursun videoları Buildroot'un 2017 sürümünü kullanıyor. Menüler ve komutlar büyük ölçüde aynı; değişenler: kernel artık `uImage` yerine `zImage` olarak üretiliyor, varsayılan toolchain artık hazır <b>Bootlin</b> toolchain'i ve kart dosyaları `board/beaglebone/` yerine `board/beagleboard/beaglebone/` altında.

<b>Host paketleri</b> (Buildroot kılavuzundaki zorunlu liste + `menuconfig`):

```bash
sudo apt install which sed make binutils build-essential diffutils gcc g++ bash patch gzip bzip2 perl \
     tar cpio unzip rsync file bc findutils wget libncurses-dev python3 git
```

<b>İndir ve aç:</b>

![Buildroot'u indirme, klasörler ve BBB defconfig'i](../images/buildroot/01_download.png)

```bash
cd ~/bbb
wget https://buildroot.org/downloads/buildroot-2026.02.3.tar.gz
tar -xzf buildroot-2026.02.3.tar.gz
cd buildroot-2026.02.3
make list-defconfigs | grep -i beagle
```

---

## 13.3 Klasör Yapısı

| Klasör | İçinde ne var? |
|---|---|
| `arch/` | Mimari seçenekleri (ARM, ARM64, RISC-V...) |
| `board/` | Karta özel dosyalar: SD kart düzeni (`genimage.cfg`), `uEnv.txt`, betikler, yamalar. BBB için `board/beagleboard/beaglebone/`. |
| `boot/` | Bootloader tarifleri (U-Boot, Barebox, GRUB...) |
| `configs/` | Hazır kart ayarları (`*_defconfig`). BBB için `beaglebone_defconfig`. |
| `docs/` | Buildroot kılavuzu |
| `fs/` | Rootfs imaj türleri (ext4, squashfs, cpio/initramfs, tar...) |
| `linux/` | Kernel'in nasıl derleneceğinin tarifi |
| `package/` | <b>~3000 paketin</b> tarifi. Her paket bir klasör: `Config.in` (menü), `<paket>.mk` (nasıl derlenir), `.hash` (indirmenin doğrulaması). |
| `support/` | Yardımcı betikler (ör. `genimage.sh`) |
| `system/` | Rootfs iskeleti ve "System configuration" menüsü (init, hostname, şifre...) |
| `toolchain/` | Toolchain seçenekleri |
| `utils/` | Geliştirici araçları |

`make` çalıştıktan sonra iki klasör daha oluşur:

| Klasör | İçinde ne var? |
|---|---|
| `dl/` | İndirilen kaynak arşivleri. Bir kere indirilir, sonraki derlemelerde tekrar kullanılır. |
| <b>`output/`</b> | Bütün derleme çıktıları (aşağıda) |

![output klasörünün yapısı](../images/buildroot/04_output_tree.png)

| `output/` altı | İçinde ne var? |
|---|---|
| `build/` | Her paketin açılıp derlendiği klasör (`busybox-1.37.0/`, `linux-6.18.1/`...) |
| `host/` | <b>Host'ta</b> çalışan araçlar: cross toolchain (`arm-buildroot-linux-gnueabihf-gcc`), `mkimage`, `genimage`... |
| `staging/` | Hedefin kütüphaneleri ve başlık dosyaları (sysroot). Uygulama derlerken bunlara karşı derlenir. |
| `target/` | <b>Rootfs'in kendisi</b>, sadeleştirilmiş haliyle. İmajlar bundan üretilir. Elle değiştirme; bir sonraki derlemede ezilir. |
| <b>`images/`</b> | <b>Karta gidecek dosyalar</b> |

---

## 13.4 Temel Komutlar

| Komut | Görevi |
|---|---|
| `make list-defconfigs` | Hazır kart ayarlarını listeler |
| `make <kart>_defconfig` | Hazır ayarı `.config`'e yükler |
| `make menuconfig` | Buildroot'un ayar menüsü |
| `make` | Her şeyi derler. <b>`-j` verme</b>: Buildroot paketlerin içinde zaten paralel derler. |
| `make <paket>-rebuild` | Bir paketi yeniden derler (ör. `make busybox-rebuild`) |
| `make <paket>-dirclean` | Paketin derleme klasörünü siler; bir sonraki `make`'te sıfırdan derlenir |
| `make linux-menuconfig` / `uboot-menuconfig` / `busybox-menuconfig` | Kernel'in, U-Boot'un, BusyBox'ın kendi menüsü ([13.9](#139-buildrootta-kernel-ve-u-boot-ayarları)) |
| `make savedefconfig` | Ayarlarını küçük bir defconfig olarak kaydeder |
| `make clean` | `output/`'u siler (indirmeler `dl/`'de kalır) |
| `make help` | Bütün hedefleri listeler |

> [!IMPORTANT]
> Buildroot bir ayarı değiştirdiğinde neyin etkilendiğini <b>her zaman takip edemez</b>. Bir paketi eklemek için `make` yeterlidir. Ama <b>toolchain'i, mimariyi, init sistemini</b> veya bir paketi kaldırmak gibi büyük değişikliklerde `make clean all` ile baştan derle.

---

## 13.5 Adım Adım: BBB İçin Derleme

> [!NOTE]
> Aşağıdaki ekran görüntüleri <b>temsilidir</b>. İlk derleme indirmelerle birlikte bilgisayarına göre <b>30 dakika ile 2 saat</b> sürer ve birkaç GB yer kaplar.

### Adım 1 — Hazır ayarı yükle

![beaglebone_defconfig ve önemli ayarlar](../images/buildroot/02_defconfig.png)

```bash
make beaglebone_defconfig
make menuconfig          # isteğe bağlı: incele
```

![Buildroot menuconfig ana ekranı](../images/buildroot/bootlin_buildroot_menuconfig.png)

*Görsel: Bootlin, "Buildroot" eğitim slaytları (CC BY-SA 3.0)*

### Adım 2 — Derle

![Buildroot derleme çıktısı ve üretilen imajlar](../images/buildroot/03_build.png)

```bash
make 2>&1 | tee build.log
ls output/images
```

`tee` ile çıktıyı `build.log`'a da yazmak, bir hata olduğunda log'a geri bakmanı sağlar.

### `beaglebone_defconfig` ne seçiyor?

| Ayar | Değer | Anlamı |
|---|---|---|
| `BR2_arm`, `BR2_cortex_a8`, `BR2_ARM_FPU_VFPV3` | | Hedef: ARM Cortex-A8, donanımsal FPU |
| `BR2_TOOLCHAIN_EXTERNAL_BOOTLIN` | Bootlin armv7-eabihf glibc stable 2025.08-1 | Bootlin'in hazır derlenmiş toolchain'i indirilir. Toolchain'i sıfırdan derlemekten çok daha hızlıdır. |
| `BR2_LINUX_KERNEL_CUSTOM_VERSION_VALUE` | 6.18.1 | Mainline kernel sürümü |
| `BR2_LINUX_KERNEL_DEFCONFIG` | `omap2plus` | Kernel'in `omap2plus_defconfig`'i ([10.5](10_linux_kernel.md#105-kart-yapılandırma-dosyaları)) |
| `BR2_LINUX_KERNEL_INTREE_DTS_NAME` | `ti/omap/am335x-boneblack` ve diğer Beagle kartları | Derlenecek DTB'ler. Kernel 6.5'ten beri DTS'ler `ti/omap/` altında ([11.9](11_device_tree.md#119-dtc-kullanımı)). |
| `BR2_TARGET_UBOOT_CUSTOM_VERSION_VALUE` | 2026.01 | U-Boot sürümü |
| `BR2_TARGET_UBOOT_BOARD_DEFCONFIG` | `am335x_evm` | U-Boot'un `am335x_evm_defconfig`'i ([9.3](09_uboot_build.md#93-adım-adım-toolchain-kurulumu-ve-u-boot-derleme)) |
| `BR2_TARGET_UBOOT_SPL_NAME` | `MLO` | SPL'in SD kart için başlıklı hali |
| `BR2_ROOTFS_DEVICE_CREATION_DYNAMIC_MDEV` | | `/dev` için BusyBox'ın `mdev`'i kullanılır |
| `BR2_TARGET_ROOTFS_EXT2_4` | | Rootfs ext4 imajı olarak üretilir |
| `BR2_ROOTFS_POST_IMAGE_SCRIPT` | `genimage.sh` + `genimage.cfg` | Bütün dosyalardan hazır bir SD kart imajı (`sdcard.img`) üretilir |

### Üretilen dosyalar (`output/images/`)

| Dosya | Ne? |
|---|---|
| `MLO`, `u-boot.img` | SPL ve U-Boot 2026.01 |
| `zImage` | Kernel 6.18.1. <b>`uImage` değil</b>; U-Boot `bootz` ile başlatır. |
| `am335x-boneblack.dtb` (+ diğer Beagle'lar) | Device tree'ler |
| `uEnv.txt`, `extlinux/extlinux.conf` | U-Boot'a kernel'i nasıl açacağını söyleyen dosyalar |
| `rootfs.ext4` (= `rootfs.ext2`), `rootfs.tar` | Rootfs: imaj olarak ve arşiv olarak |
| `boot.vfat` | BOOT bölümünün (FAT, 16 MB) imajı |
| <b>`sdcard.img`</b> | Bölüm tablosu + `boot.vfat` + `rootfs.ext4`. <b>Karta doğrudan yazılacak dosya.</b> |

---

## 13.6 Kartta Test

### SD karta yazmak

`sdcard.img`, [Bölüm 5](05_emmc_boot.md)'teki Debian imajı gibi <b>bütün bir diskin kopyasıdır</b>. Karta byte byte yazılır, bölümlemeye gerek yoktur:

![sdcard.img'yi dd ile SD karta yazma](../images/buildroot/06_flash_sd.png)

```bash
lsblk                                         # SD kartın adını bul (ör. /dev/sdb)
sudo umount /dev/sdb1 /dev/sdb2
sudo dd if=output/images/sdcard.img of=/dev/sdb bs=4M status=progress conv=fsync
```

> [!CAUTION]
> `dd`'nin `of=` kısmına yanlış diski yazarsan (ör. `/dev/sda`) <b>bilgisayarının diski silinir</b>. `lsblk` ile boyuta bakarak kontrol et. Emin değilsen [5.4.5](05_emmc_boot.md#545-imageı-sd-karta-yaz-balenaetcher)'teki gibi balenaEtcher kullan.

### U-Boot kernel'i nasıl açıyor?

Buildroot'un BOOT bölümüne koyduğu `uEnv.txt` (`board/beagleboard/beaglebone/uEnv.txt`):

```text
bootpart=0:1
devtype=mmc
bootdir=
bootfile=zImage
bootpartition=mmcblk0p2
console=ttyS0,115200n8
loadaddr=0x82000000
fdtaddr=0x88000000
set_mmc1=if test $board_name = A33515BB; then setenv bootpartition mmcblk1p2; fi
set_bootargs=setenv bootargs console=${console} root=/dev/${bootpartition} rw rootfstype=ext4 rootwait
uenvcmd=run set_mmc1; run set_bootargs;run loadimage;run loadfdt;printenv bootargs;bootz ${loadaddr} - ${fdtaddr}
```

| Parça | Anlamı |
|---|---|
| `bootpart`, `devtype`, `bootdir`, `bootfile` | U-Boot'un kendi `loadimage` makrosunun kullandığı değişkenler: "`mmc 0:1`'deki `zImage`'ı yükle" |
| `run loadimage`, `run loadfdt` | U-Boot'un varsayılan ortamındaki hazır makrolar. [Bölüm 6](06_uboot_uenv.md)'daki `load mmc 0:1 ...` komutlarını onlar çalıştırır. |
| `set_mmc1` | Kartın EEPROM'undaki ada (`board_name`) göre rootfs'i eMMC'ye çevirir |
| `bootz` | <b>`zImage`</b> başlatır. `bootm` ise U-Boot başlıklı <b>`uImage`</b> ister ([4.9](04_sd_card_boot.md#49-uimage-nedir)). |

Buildroot ayrıca `extlinux/extlinux.conf` da koyar. Yeni U-Boot sürümleri BOOT bölümünde bu dosyayı da arar ("standard boot"). Hangisinin kullanılacağı U-Boot'un ortamına bağlıdır; ikisi de aynı kernel'i, aynı DTB'yi ve aynı `root=` ayarını kullanır.

### Aç

Kartı S2'ye basılı tutarak aç. `Welcome to Buildroot` ve `buildroot login:` geldiğinde `root` yaz. Varsayılan ayarda şifre yoktur.

---

## 13.7 SSH, Şifre ve Ağ Ayarı

Kursun "Testing buildroot RFS and ssh support on BBB" dersi. Önce `menuconfig`'te üç değişiklik yap:

| Menü | Ayar | Neden? |
|---|---|---|
| Target packages → Networking applications | `[*] dropbear` | SSH sunucusu ([12.10](12_busybox_rootfs.md#1210-challenge-1-ssh-ve-tftp-desteği)'deki Dropbear, bu sefer Buildroot derliyor ve açılışta başlatıyor) |
| System configuration → Root password | Bir şifre | Dropbear şifresiz root girişine izin vermez |
| System configuration → Root filesystem overlay directories | `board/bbb/overlay` | Rootfs'e kendi dosyalarını eklemek için (aşağıda) |

<b>Rootfs overlay</b>, Buildroot'un rootfs'i ürettikten sonra üzerine <b>kopyaladığı</b> bir klasördür. `output/target/`'ı elle değiştirmek yerine kendi dosyalarını buraya koyarsın. Statik IP için:

```bash
mkdir -p board/bbb/overlay/etc/network
cat > board/bbb/overlay/etc/network/interfaces <<'EOF'
auto lo
iface lo inet loopback

auto eth0
iface eth0 inet static
    address 192.168.27.2
    netmask 255.255.255.0
EOF
```

![Dropbear, root şifresi ve overlay ayarları](../images/buildroot/05_ssh_config.png)

```bash
make
```

> [!TIP]
> Ağında bir DHCP sunucusu (modem) varsa overlay yerine System configuration → <b>Network interface to configure through DHCP</b> = `eth0` ayarı yeterli.

Yeni `sdcard.img`'yi karta yaz ve aç. Bilgisayardan bağlan:

![Buildroot açılışı ve SSH ile bağlantı](../images/buildroot/07_boot_ssh.png)

```bash
ssh root@192.168.27.2
```

---

## 13.8 Buildroot Rootfs'ini Tek Başına Kullanmak

Bazen Buildroot'un sadece rootfs'ini istersin; kernel'i ve U-Boot'u kendin derlemeye devam edersin. `rootfs.tar` bunun içindir:

| Nereye? | Komut |
|---|---|
| SD kartın ROOTFS bölümüne | `sudo tar -xf output/images/rootfs.tar -C /media/$USER/ROOTFS` |
| NFS klasörüne ([12.8](12_busybox_rootfs.md#128-rootfsi-nfs-ile-bilgisayardan-bağlamak)) | `sudo tar -xf output/images/rootfs.tar -C /srv/nfs/bbb` |

> [!NOTE]
> Buildroot rootfs'indeki kernel modülleri Buildroot'un derlediği kernel (6.18.1) içindir. Kendi kernel'ini kullanıyorsan modülleri [10.8](10_linux_kernel.md#108-adım-adım-kerneli-derleme)'deki gibi `modules_install` ile aynı rootfs'e kur.

---

## 13.9 Buildroot'ta Kernel ve U-Boot Ayarları

Kursun "Buildroot Linux and U-Boot configurations" ve "image generation and testing" dersleri.

### Hangi sürüm, hangi ayar?

Buildroot `menuconfig`'teki <b>Kernel</b> ve <b>Bootloaders → U-Boot</b> menüleri, [Bölüm 9](09_uboot_build.md) ve [Bölüm 10](10_linux_kernel.md)'da elle verdiğimiz bilgileri sorar:

| Menü (Kernel) | Elle karşılığı |
|---|---|
| Kernel version | Hangi kaynak: resmi sürüm, özel sürüm numarası, özel git deposu veya arşiv |
| Kernel configuration → Defconfig name | `make xxx_defconfig` |
| Kernel binary format | `zImage` / `uImage` (uImage için *load address* = `0x80008000`) |
| Build a Device Tree Blob → In-tree Device Tree Source file names | `make ... am335x-boneblack.dtb` |

| Menü (Bootloaders → U-Boot) | Elle karşılığı |
|---|---|
| U-Boot Version | Hangi U-Boot kaynağı |
| Board defconfig | `make am335x_evm_defconfig` |
| U-Boot binary format → u-boot.img | `u-boot.img` |
| Install U-Boot SPL binary image + SPL name `MLO` | `MLO` |

### Kernel'in ve U-Boot'un kendi menüleri

![Buildroot içinden kernel ve U-Boot ayarları](../images/buildroot/08_linux_uboot_config.png)

```bash
make linux-menuconfig          # kernel'in menuconfig'i (output/build/linux-.../.config)
make uboot-menuconfig          # U-Boot'un menuconfig'i
make busybox-menuconfig        # BusyBox'ın menuconfig'i
make linux-rebuild uboot-rebuild all
```

> [!IMPORTANT]
> `linux-menuconfig` ile yaptığın değişiklikler `output/build/` altında durur ve `make clean`'de <b>kaybolur</b>. Kalıcı yapmak için:
> 1. Kernel menüsünde *Kernel configuration* = <b>Using a custom (def)config file</b> seç ve bir dosya yolu ver (ör. `board/bbb/linux.config`).
> 2. `make linux-update-defconfig` ile değişiklikleri o dosyaya yaz.
>
> U-Boot ve BusyBox için de aynısı: `uboot-update-defconfig`, `busybox-update-config`.

### Örnek: Kursun BeagleBoard kernel'ini kullanmak

Kursta Buildroot'un içinde BeagleBoard'un kernel'i ve `bb.org_defconfig` kullanılıyor. 2026.02.3'te bunu şöyle seçersin:

| Menü | Değer |
|---|---|
| Kernel version | <b>Custom Git repository</b> |
| URL of custom repository | `https://github.com/beagleboard/linux.git` |
| Custom repository version | `5.10` |
| Defconfig name | `bb.org` (sonuna `_defconfig` yazılmaz) |
| In-tree Device Tree Source file names | `am335x-boneblack` (kernel 6.5'ten eski olduğu için `ti/omap/` öneki yok) |
| Build options → Force all downloads to have a valid hash | <b>Kapat</b> (`beaglebone_defconfig` bunu açıyor; git dalının önceden bilinen bir hash'i yok) |

> [!WARNING]
> Eski bir kernel'i (5.10) Buildroot'un yeni toolchain'iyle derlemek, [9.2](09_uboot_build.md#92-sürüm-uyumu-hangi-toolchain)'teki "eski kaynak + yeni GCC" sorununa yol açabilir. Derleme hata verirse Buildroot'un varsayılan kernel'ine (6.18.1) dön; o, bu toolchain ile test edilmiştir.

### Kendi defconfig'ini kaydet

Bütün değişikliklerden sonra ayarlarını küçük bir dosyada sakla. Böylece aynı sistemi başka bir bilgisayarda ya da `make clean` sonrasında tek komutla yeniden üretebilirsin:

```bash
make savedefconfig BR2_DEFCONFIG=configs/my_bbb_defconfig
# sonra, sıfırdan:
make my_bbb_defconfig && make
```

---

## 13.10 Özet

- Buildroot; toolchain, U-Boot, kernel ve rootfs'i tek bir `.config`'ten derleyip hazır `sdcard.img` üretir.
- Akış: `make beaglebone_defconfig` → `make menuconfig` → `make` → `output/images/sdcard.img` → `dd` ile SD karta.
- `output/`: `build` (derleme), `host` (toolchain ve araçlar), `staging` (sysroot), `target` (rootfs), `images` (karta gidenler).
- Paket eklemek: menüden seç, `make`. Kendi dosyaların: <b>rootfs overlay</b>. Büyük değişiklik: `make clean all`.
- Kernel/U-Boot/BusyBox ayarları: `make linux-menuconfig` vb. Kalıcı yapmak için `*-update-defconfig`, bütün sistem için `savedefconfig`.

## 13.11 Karşılaşılabilecek Problemler

![Sık görülen Buildroot hataları (temsili)](../images/buildroot/09_errors.png)

| Belirti | Sebep | Çözüm |
|---|---|---|
| `You seem to have the current working directory in your LD_LIBRARY_PATH` | Ortam değişkeni Buildroot'u bozuyor | `unset LD_LIBRARY_PATH` ve tekrar `make` |
| `You must install 'unzip' on your build machine` (veya başka bir araç) | Host paketi eksik | [13.2](#132-sürüm-ve-kurulum)'deki paketleri kur |
| `ERROR: No hash found for linux-...` | Özel kernel/U-Boot kaynağı + "Force all downloads to have a valid hash" açık | Build options'tan bu ayarı kapat ya da `.hash` dosyası ekle |
| `No rule to make target 'bb.org_defconfig_defconfig'` | Defconfig adına `_defconfig` eklenmiş | Menüye sadece `bb.org` yaz |
| Ayar değiştirdim ama sonuç değişmedi | Buildroot o paketi yeniden derlemedi | `make <paket>-rebuild` veya `make clean all` |
| `No space left on device` | `output/` ve `dl/` birkaç GB tutar | En az 15 GB boş yer bırak |
| Kart `Starting kernel ...`'dan sonra sessiz | `console=` yanlış | Kernel 6.18.1'de `console=ttyS0,115200n8` |
| SSH: `Permission denied` | Root şifresi boş | System configuration → Root password |
| `output/target/`'ta yaptığım değişiklik kayboldu | `target/` her derlemede yeniden üretilir | Dosyalarını rootfs overlay'e koy |

---

[← Bölüm 12: BusyBox ile Minimal Root Filesystem](12_busybox_rootfs.md) · [İçindekiler](README.md) · [Bölüm 14: Eclipse ile Uygulama Geliştirme →](14_eclipse.md)
