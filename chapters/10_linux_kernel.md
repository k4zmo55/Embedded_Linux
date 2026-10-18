# Bölüm 10 — Linux Kernel: Kaynak Ağacı ve Derleme

> <b>Bu bölümde:</b>
> - {{board.name}} için hangi kernel kaynağının kullanıldığını ve kursun kernel sürüm geçmişini öğreneceksin.
> - Kernel kaynak ağacında gezinmeyi öğreneceksin: ARM mimarisi kodu, kart yapılandırma dosyaları ve SoC sürücüleri nerede durur?
> - Kernel'i `{{kernel.defconfig}}` ile yapılandırıp `uImage`, `am335x-boneblack.dtb` ve modülleri derleyeceksin.
> - Kendi derlediğin kernel ile kartı açacaksın.
>
> <b>Ön koşul:</b> [Bölüm 3](03_boot_process.md) — boot zinciri, [Bölüm 9](09_uboot_build.md) — cross toolchain kurulumu.

---

## 10.1 Hangi Kernel?

Linux kernel'in "resmi" kaynağı Linus Torvalds'ın yönettiği <b>mainline</b> ağaçtır (kernel.org). Kart üreticileri bunun üzerine kendi kartlarına özel yamaları ekleyip <b>vendor</b> ağaçları yayınlar. {{board.name}} için iki seçenek var:

| Kaynak | Adres | Ne zaman? |
|---|---|---|
| <b>BeagleBoard kernel'i</b> (vendor) | `{{kernel.repo}}` | Kursta ve bu kitapta kullanılan. BBB'ye özel ayar (`{{kernel.defconfig}}`), cape ve PRU desteği hazır gelir. |
| <b>Mainline</b> | `https://git.kernel.org` | En yeni özellikler. BBB'de temel donanım çalışır, bazı ekstralar eksik olabilir. |

Kursun kullandığı kernel sürümleri zamanla değişti:

| Nerede? | Kernel |
|---|---|
| Kursun ilk hazır imajları (Ångström) | {{prebuilt.kernel_version}} |
| Kursun eski derleme notları | 4.4 (`bb.org_defconfig`) ve 4.11 (`omap2plus_defconfig`) |
| <b>Kursun güncel imajları</b> | <b>{{prebuilt.sd_kernel_version}}</b> |

Kursun başındaki "Important Update on Linux Kernel Version" notu bu güncellemeyi anlatıyor. Bu kitap BeagleBoard'un <b>{{kernel.branch}}</b> dalını kullanıyor. 5.10 bir <b>LTS</b> (Long Term Support, uzun süre desteklenen) sürümdür.

> [!NOTE]
> Dal (branch) zamanla güncellenir. Bu kitap yazılırken `{{kernel.branch}}` dalının ucu <b>{{kernel.version}}</b> sürümündeydi. Kursun hazır imajı {{prebuilt.sd_kernel_version}}. Aradaki fark sadece küçük düzeltmelerdir, anlatılan her şey ikisinde de aynıdır.

---

## 10.2 Kaynak Kodu İndirme

```bash
cd ~/bbb
git clone --depth=1 -b {{kernel.branch}} {{kernel.repo}}
cd {{kernel.dir}}
head -4 Makefile
```

![Kernel kaynağını git ile indirme](../images/kernel/01_clone.png)

| Parça | Anlamı |
|---|---|
| `--depth=1` | Sadece son sürümü indir, binlerce commit'lik geçmişi indirme. İndirme birkaç GB yerine birkaç yüz MB olur. |
| `-b {{kernel.branch}}` | `{{kernel.branch}}` dalını al |
| `Makefile` başı | `VERSION`, `PATCHLEVEL`, `SUBLEVEL` satırları indirdiğin sürümü gösterir |

> [!TIP]
> Kaynak kodda bir fonksiyonun ya da sürücünün nerede tanımlandığını bulmak için tarayıcıdan <b>Elixir</b>'i kullan: <https://elixir.bootlin.com/linux/v5.10/source>. Her sembole tıklayınca tanımına ve kullanıldığı yerlere gider. Bilgisayarda ise `grep -rn "aranan" drivers/` iş görür.

---

## 10.3 Kaynak Ağacının Genel Yapısı

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
| `Documentation/` | Kernel'in kendi belgeleri. Device tree binding'leri `Documentation/devicetree/bindings/` altında ([11.7](11_device_tree.md#117-compatible-ile-driver-eşleşmesi)). |
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

## 10.4 ARM Mimarisi Kodunun Düzeni (`arch/arm`)

![arch/arm, defconfig'ler, mach-omap2 ve DTS dosyaları](../images/kernel/03_arch_arm.png)

| Klasör | İçinde ne var? |
|---|---|
| `arch/arm/boot/` | Derlenen imajlar (`Image`, `zImage`, `uImage`) buraya çıkar. |
| `arch/arm/boot/compressed/` | `zImage`'in başındaki, kernel'i RAM'de açan küçük program ([4.9](04_sd_card_boot.md#49-uimage-nedir)) |
| `arch/arm/boot/dts/` | Device tree kaynakları (`am335x-boneblack.dts` ve `.dtsi`'leri) |
| `arch/arm/configs/` | Hazır ayar dosyaları (<b>defconfig</b>) |
| `arch/arm/kernel/` | ARM'a özel çekirdek kodu. Kernel'in ilk çalışan komutları `arch/arm/kernel/head.S`'tedir. |
| `arch/arm/mm/` | ARM'a özel bellek yönetimi (MMU, cache) |
| `arch/arm/mach-omap2/` | <b>TI OMAP/AM335x ailesine özel kod:</b> güç ve saat alanları, uyku modu (`sleep33xx.S`), DT ile açılan kartların ortak girişi (`board-generic.c`) |
| `arch/arm/mach-*/` | Diğer SoC aileleri: `mach-imx` (NXP i.MX), `mach-stm32`, `mach-at91`... |

> [!NOTE]
> Device tree'den önce her kart için `arch/arm/mach-omap2/board-xxx.c` gibi bir <b>board file</b> yazılırdı. Bugün `mach-omap2` içinde kart dosyası yoktur. Kartları device tree tarif eder, `board-generic.c` sadece "bu SoC ailesi DT ile açılıyor" der ([11.1](11_device_tree.md#111-problem-kernel-donanımı-nereden-bilecek)).

---

## 10.5 Kart Yapılandırma Dosyaları

Bir kart için kernel hazırlarken iki tür dosya kullanılır:

| Dosya türü | Ne tarif eder? | BBB için |
|---|---|---|
| <b>defconfig</b> (`arch/arm/configs/`) | <b>Kernel'e hangi özelliklerin ve sürücülerin derleneceğini</b> | `{{kernel.defconfig}}` |
| <b>Device tree</b> (`arch/arm/boot/dts/`) | <b>Kartta hangi donanımın nerede olduğunu</b> | `am335x-boneblack.dts` |

Kullanılabilecek defconfig'ler:

| defconfig | Kapsamı |
|---|---|
| `{{kernel.defconfig}}` | BeagleBoard'un BBB ve diğer Beagle kartları için hazırladığı ayar. Cape, PRU, USB gadget desteği açık. <b>Bu kitapta kullanılan.</b> |
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

Device tree'nin yapısı ve include zinciri [Bölüm 11](11_device_tree.md)'de anlatılıyor.

---

## 10.6 SoC Sürücülerinin Düzeni (`drivers/`)

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
> UART sürücüsü konsolun adını belirler: `8250_omap` → `/dev/ttyS0`, eski `omap-serial` → `/dev/ttyO0`. Kernel 5.10'da `8250_omap` kullanıldığı için `bootargs`'ta <b>`console={{kernel.console}}`</b> yazılır ([3.4](03_boot_process.md#34-linux-kernel-ve-root-filesystem)).

---

## 10.7 Kernel Yapılandırması: Kconfig, `.config`, menuconfig

Kernel'de binlerce seçenek var ve her biri `CONFIG_` ile başlayan bir isimle temsil edilir.

| Parça | Görevi |
|---|---|
| `Kconfig` dosyaları | Her klasörde bulunur. Seçenekleri, açıklamalarını ve birbirine bağımlılıklarını tanımlar. |
| `.config` | Derlemede kullanılan <b>gerçek</b> ayar dosyası. Binlerce satır, kaynak klasörünün kökünde. |
| `defconfig` | `.config`'in kısaltılmış hali: sadece varsayılandan farklı olan satırlar. `make xxx_defconfig` bunu açıp `.config` üretir. |
| `make menuconfig` | `.config`'i menüden düzenler. U-Boot'taki menüyle aynı ([9.3](09_uboot_build.md#93-adım-adım-toolchain-kurulumu-ve-u-boot-derleme)). |
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

## 10.8 Adım Adım: Kernel'i Derleme

> [!NOTE]
> Aşağıdaki ekran görüntüleri <b>temsilidir</b>. Örneklerde çalışma klasörü `~/bbb/{{kernel.dir}}`, toolchain [Bölüm 9](09_uboot_build.md)'da kurulan Linaro GCC {{build.gcc_version}}.

### Adım 1 — Host paketlerini kur

```bash
sudo apt install build-essential bc bison flex libssl-dev libncurses-dev lzop u-boot-tools git
```

| Paket | Neden? |
|---|---|
| `bc` | Derleme sırasında bazı sabitler `bc` ile hesaplanır |
| `lzop` | `{{kernel.defconfig}}` kernel'i <b>LZO</b> ile sıkıştırır (`CONFIG_KERNEL_LZO=y`) |
| `libssl-dev` | Modül imzalama ve sertifika araçları |
| `u-boot-tools` | `mkimage`: `uImage` üretmek için |
| `bison`, `flex`, `libncurses-dev` | Kconfig ve `menuconfig` |

### Adım 2 — Yapılandır

![distclean, defconfig ve önemli ayarlar](../images/kernel/04_config.png)

```bash
make ARCH=arm CROSS_COMPILE={{build.cross_compile}} distclean
make ARCH=arm CROSS_COMPILE={{build.cross_compile}} {{kernel.defconfig}}
make ARCH=arm CROSS_COMPILE={{build.cross_compile}} menuconfig     # isteğe bağlı
```

Kernel'de U-Boot'tan farklı olarak <b>`ARCH=arm` her komutta zorunludur</b>. Yazmazsan kernel host'un mimarisini (x86) varsayar ve yanlış `.config` üretir.

### Adım 3 — Kernel imajını ve device tree'yi derle

![uImage ve dtbs derleme çıktısı](../images/kernel/05_build.png)

```bash
make ARCH=arm CROSS_COMPILE={{build.cross_compile}} uImage dtbs LOADADDR={{kernel.loadaddr}} -j$(nproc)
```

| Parça | Anlamı |
|---|---|
| `uImage` | `vmlinux` → `Image` → `zImage` → `uImage` zincirini üretir ([4.9](04_sd_card_boot.md#49-uimage-nedir)) |
| `dtbs` | Bütün `.dts` dosyalarını `.dtb`'ye derler |
| `LOADADDR={{kernel.loadaddr}}` | `uImage` başlığına yazılan yükleme ve giriş adresi. AM335x'te DDR `0x80000000`'da başlar; kernel ilk 32 KB'ın (`0x8000`) arkasına yerleşir. |
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

### Adım 4 — Modülleri derle ve kur

`m` olarak seçilen sürücüler ayrı derlenir ve rootfs'e kurulur:

![Modülleri derleme ve rootfs'e kurma](../images/kernel/06_modules.png)

```bash
make ARCH=arm CROSS_COMPILE={{build.cross_compile}} modules -j$(nproc)
make ARCH=arm CROSS_COMPILE={{build.cross_compile}} INSTALL_MOD_PATH={{rootfs.dir}} modules_install
```

`modules_install`, modülleri `<INSTALL_MOD_PATH>/lib/modules/{{kernel.version}}/` altına kopyalar ve `modprobe`'un kullandığı `modules.dep` dosyasını üretir. Buradaki rootfs klasörünü [Bölüm 12](12_busybox_rootfs.md)'de BusyBox ile dolduracağız.

> [!CAUTION]
> `INSTALL_MOD_PATH`'i <b>unutma</b>. Yazmazsan `sudo make modules_install` modülleri <b>host bilgisayarının</b> `/lib/modules` klasörüne kurar; ARM modülleri Ubuntu'nun klasörüne karışır.

### Komutların kısa özeti

```bash
cd ~/bbb
git clone --depth=1 -b {{kernel.branch}} {{kernel.repo}}
cd {{kernel.dir}}
make ARCH=arm CROSS_COMPILE={{build.cross_compile}} distclean
make ARCH=arm CROSS_COMPILE={{build.cross_compile}} {{kernel.defconfig}}
make ARCH=arm CROSS_COMPILE={{build.cross_compile}} uImage dtbs LOADADDR={{kernel.loadaddr}} -j$(nproc)
make ARCH=arm CROSS_COMPILE={{build.cross_compile}} modules -j$(nproc)
make ARCH=arm CROSS_COMPILE={{build.cross_compile}} INSTALL_MOD_PATH={{rootfs.dir}} modules_install
```

---

## 10.9 Yeni Kernel'i Kartta Denemek

Kernel'i tam olarak denemek için bir rootfs gerekir. Kendi rootfs'imizi [Bölüm 12](12_busybox_rootfs.md)'de hazırlayacağız. Kernel'in açıldığını görmek için şimdilik <b>eMMC'deki Debian'ın rootfs'ini</b> kullanabilirsin.

<b>1) Dosyaları SD kartın BOOT bölümüne kopyala:</b>

```bash
cp arch/arm/boot/uImage arch/arm/boot/dts/am335x-boneblack.dtb /media/$USER/BOOT/
```

<b>2) BOOT bölümündeki `uEnv.txt`'yi yaz.</b> Kursun `uEnv-SD.txt` dosyası temel alındı; konsol `{{kernel.console}}`, rootfs eMMC:

```text
console={{kernel.console}},115200n8
netargs=setenv bootargs console=${console} root=/dev/mmcblk1p2 rw rootwait
netboot=echo Booting from microSD ...; setenv autoload no; load mmc 0:1 ${loadaddr} uImage; load mmc 0:1 ${fdtaddr} am335x-boneblack.dtb; run netargs; bootm ${loadaddr} - ${fdtaddr}
uenvcmd=run netboot
```

> [!IMPORTANT]
> eMMC'deki rootfs'in hangi bölümde olduğu Debian imajına göre değişir. Eski imajlarda 2. bölüm (`mmcblk1p2`), yenilerinde tek bölüm (`mmcblk1p1`) olabilir. U-Boot'ta `mmc dev 1` ve `mmc part` ile kontrol et ([6.5](06_uboot_uenv.md#65-ek-alıştırma-kernel-ve-dtb-sd-karttan-rootfs-emmcden)).

<b>3) Kartı S2'ye basılı tutarak aç.</b> Açılış mesajlarında kendi kernel sürümünü, derleme makineni ve toolchain'ini görmelisin:

![Kendi derlediğin kernel ile açılış](../images/kernel/07_boot_new_kernel.png)

```bash
cat /proc/version
```

> [!NOTE]
> eMMC'deki Debian kendi kernel modüllerini (`/lib/modules/<eski sürüm>`) içerir, senin kernel'inin modüllerini içermez. Kernel açılır ama bazı sürücüler (Wi-Fi, USB gadget...) yüklenmeyebilir. Bu bir sorun değil; amacımız sadece kernel'in açıldığını görmek. Modüller [Bölüm 12](12_busybox_rootfs.md)'deki rootfs'e kurulacak.

---

## 10.10 Özet

- {{board.name}} için BeagleBoard'un kernel ağacı kullanılıyor: `{{kernel.repo}}`, dal `{{kernel.branch}}`.
- `arch/arm` mimariye özel kodu, `arch/arm/configs` defconfig'leri, `arch/arm/boot/dts` device tree'leri, `drivers/` sürücüleri tutar. AM335x'e özel SoC kodu `arch/arm/mach-omap2`'de.
- `defconfig` → `.config` → `menuconfig` ile ayarlanır. `y` = kernel'in içinde, `m` = modül.
- Derleme: `distclean` → `{{kernel.defconfig}}` → `uImage dtbs LOADADDR={{kernel.loadaddr}}` → `modules` → `modules_install INSTALL_MOD_PATH=...`. Her komutta `ARCH=arm CROSS_COMPILE={{build.cross_compile}}`.
- Karta giden dosyalar: `uImage`, `am335x-boneblack.dtb` ve rootfs'e kurulan modüller.

## 10.11 Karşılaşılabilecek Problemler

![Sık görülen kernel derleme hataları (temsili)](../images/kernel/08_errors.png)

| Belirti | Sebep | Çözüm |
|---|---|---|
| `Specify LOADADDR on the commandline to build an uImage` | `uImage` için yükleme adresi verilmedi | Komuta `LOADADDR={{kernel.loadaddr}}` ekle |
| `"mkimage" command not found` | `u-boot-tools` kurulu değil | `sudo apt install u-boot-tools` |
| `lzop: not found` | Kernel LZO ile sıkıştırılıyor | `sudo apt install lzop` |
| `openssl/bio.h: No such file` | `libssl-dev` eksik | `sudo apt install libssl-dev` |
| `bc: not found` | `bc` eksik | `sudo apt install bc` |
| Derleme x86 için yapılıyor, `.config`'te ARM seçenekleri yok | Bir komutta `ARCH=arm` unutuldu | `distclean` ile temizleyip her komutta `ARCH=arm` yazarak baştan başla |
| `Starting kernel ...` sonrası hiçbir şey yok | `console=` yanlış ya da DTB uyumsuz | Kernel 5.10'da `console={{kernel.console}}`. DTB'yi aynı kernel kaynağından derle. |
| `VFS: Unable to mount root fs on unknown-block(179,...)` | `root=` yanlış bölümü gösteriyor | U-Boot'ta `mmc part`, Linux'ta (açılabiliyorsa) `lsblk` ile doğru bölümü bul |
| Ubuntu'nun `/lib/modules` klasöründe ARM modülleri var | `modules_install` `INSTALL_MOD_PATH` olmadan `sudo` ile çalıştırıldı | O sürüm klasörünü `/lib/modules`'ten sil, komutu `INSTALL_MOD_PATH` ile tekrar çalıştır |
