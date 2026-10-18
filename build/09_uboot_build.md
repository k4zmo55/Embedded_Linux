<!-- Bu dosya otomatik üretildi. Düzenlemek için chapters/ altındaki kaynağı değiştir. -->
# Bölüm 9 — Cross Toolchain, SPL ve U-Boot Derleme

> <b>Bu bölümde:</b>
> - Cross compile'ın ne olduğunu ve neden gerektiğini öğreneceksin.
> - Linaro cross toolchain'ini kurup `PATH`'e ekleyeceksin.
> - U-Boot 2022.04 kaynağını indirip BeagleBone Black için yapılandıracak ve derleyeceksin: `MLO`, `u-boot-spl.bin`, `u-boot.img`.
> - Kendi derlediğin U-Boot ile kartı açacaksın.
> - Challenge: U-Boot'un açılıştaki bekleme süresini kaynak koddan 10 saniyeye çıkaracaksın.
>
> <b>Ön koşul:</b> [Bölüm 3](03_boot_process.md) — SPL ve U-Boot'un görevleri, [Bölüm 4](04_sd_card_boot.md) — SD karta dosya koyma.

---

## 9.1 Bu Bölümde Neden Toolchain Kuruyoruz?

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

### Toolchain'in içinde ne var?

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

### Neden U-Boot bölümünde anlatılıyor?

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

## 9.2 Sürüm Uyumu: Hangi Toolchain?

En çok sorun çıkaran konu bu. <b>Eski U-Boot/kernel kaynağını yeni GCC ile derlemek çoğu zaman hata verir.</b> Toolchain'i derleyeceğin kaynağın yaşına göre seç:

| Derlenecek kaynak | Uygun toolchain | Nasıl kurulur? |
|---|---|---|
| U-Boot 2013.x, kernel 3.8 | GCC 4.x (ör. Linaro 4.9-2014.09) | Linaro arşivinden indir |
| U-Boot 2016.x – 2022.x, kernel 4.x | GCC 6 / 7 (ör. Linaro 6.5, 7.5) | Linaro'dan indir (aşağıda) |
| U-Boot 2023+, kernel 5.x / 6.x | Güncel GCC | `sudo apt install gcc-arm-linux-gnueabihf` |

> [!IMPORTANT]
> Bu bölümde kursun videolarında kullanılan <b>U-Boot 2022.04 + Linaro GCC 7.5.0</b> kullanılıyor ([9.3](#93-adım-adım-toolchain-kurulumu-ve-u-boot-derleme) Adım 4'teki menuconfig ekranında görünüyor). Başka sürüm kullanırsan komutlarda sadece sürüm numaraları değişir, adımlar aynıdır.

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

## 9.3 Adım Adım: Toolchain Kurulumu ve U-Boot Derleme

> [!NOTE]
> Aşağıdaki ekran görüntüleri <b>temsilidir</b>; sürüm, tarih ve boyut değerleri senin ortamında farklı olacaktır. Örneklerde çalışma klasörü `~/bbb`.

### Adım 1 — Cross toolchain'i kur

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

### Adım 2 — (İsteğe bağlı) Cross compile'ı kendi gözünle gör

Aynı C dosyasını iki derleyiciyle derleyip `file` ile karşılaştır:

![Aynı kodun x86 ve ARM için derlenmesi](../images/uboot_build/02_cross_compile_demo.png)

```bash
gcc hello.c -o hello_x86
arm-linux-gnueabihf-gcc hello.c -o hello_arm
file hello_x86 hello_arm
./hello_arm          # Exec format error: PC ARM kodu çalıştıramaz
```

`hello_arm` dosyasını karta kopyalarsan orada çalışır. U-Boot da aynı şekilde: PC'de derlenir, kartta çalışır. [6.6.3](06_uboot_uenv.md#663-a-bilgisayardan-ulaşmak)'te rootfs'teki programların PC'de çalışmamasının sebebi de budur.

### Adım 3 — Host paketlerini kur ve U-Boot kaynağını indir

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

### Adım 4 — BBB için yapılandır

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

#### `menuconfig` ekranı

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

### Adım 5 — Derle

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
| `MLO` | SPL + başında <b>GP başlığı</b> (ROM Code'un okuyacağı yükleme adresi ve boyut) | SD kart / eMMC BOOT bölümü ([Bölüm 4](04_sd_card_boot.md)) |
| `spl/u-boot-spl.bin` | Başlıksız ham SPL | Seri (UART) boot, Xmodem ile ([Bölüm 7](07_uart_boot.md)) |
| `u-boot.img` | Tam U-Boot + U-Boot başlığı (SPL bunu okur) | SD kart, seri boot (Ymodem) |
| `u-boot`, `spl/u-boot-spl` | ELF dosyaları (sembollü) | Hata ayıklama (`gdb`) |

`file` çıktısındaki <b>ARM, EABI5</b> ifadesi dosyanın gerçekten ARM için derlendiğini gösterir.

> [!IMPORTANT]
> `MLO` <b>109 KB'tan küçük</b> olmalı. ROM Code onu AM335x'in dahili SRAM'ine koyar ve SRAM'de daha fazla yer yok. U-Boot'a çok özellik eklersen SPL büyüyebilir; o zaman SPL ayarlarından gereksiz özellikleri kapatmak gerekir.

### Adım 6 — SD karta kopyala

![MLO ve u-boot.img'yi SD kartın BOOT bölümüne kopyalama](../images/uboot_build/06_copy_sd.png)

```bash
cp MLO u-boot.img /media/$USER/BOOT/
sync && sudo umount /media/$USER/BOOT
```

Seri boot için ise `spl/u-boot-spl.bin` ve `u-boot.img` dosyalarını kullan ([Bölüm 7](07_uart_boot.md)).

### Adım 7 — Kartta doğrula

Kartı S2'ye basılı tutarak aç. İlk satırlardaki <b>tarih ve saat senin derleme zamanın</b> olmalı:

![Kendi derlediğin U-Boot'un açılışı](../images/uboot_build/07_new_uboot_boot.png)

```
=> version
```

> [!NOTE]
> Yeni U-Boot sürümlerinde komut satırı `U-Boot#` yerine `=>` olarak görünür. Önceki bölümlerdeki komutlar aynı şekilde çalışır.
>
> Bir fark var: Ethernet aygıtının adı değişti. Kursun hazır U-Boot'unda (2013.04) `cpsw` olan aygıt 2022.04'te `ethernet@4a100000` olarak görünür (`Net:` satırına bak). TFTP bölümündeki `setenv ethact cpsw` yerine `setenv ethact ethernet@4a100000` yazman gerekir ([8.5](08_tftp_boot.md#85-yol-1--komutları-elle-yazarak-tftp-ile-boot)). Çoğu zaman varsayılan zaten doğrudur, emin olmak için `printenv ethact` ile bak.

### Komutların kısa özeti

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

## 9.4 Challenge: Autoboot Bekleme Süresini 10 Saniyeye Çıkarmak

### Görev

Kursun bu bölümdeki challenge'ı:

> <i>U-Boot açılınca otomatik açılışa (uEnv.txt'yi okuma, uImage'ı yükleme...) geçmeden önce birkaç saniye bekler. Bu sürede bir tuşa basarsan U-Boot komut satırına düşersin. Bu bekleme süresini <b>10 saniyeye</b> çıkar ve kartta test et. Bunun için U-Boot <b>kaynak kodunu</b> değiştirip yeniden derlemen gerekiyor.</i>

### Bekleme süresi nereden geliyor?

Geri sayımı `bootdelay` ortam değişkeni belirler. Bu değişkenin <b>varsayılan</b> değeri derleme sırasında `CONFIG_BOOTDELAY` ayarından gelir ve U-Boot'un içine gömülür:

| Kaynak | Değer |
|---|---|
| U-Boot 2022.04 varsayılanı (`am335x_evm_defconfig` değiştirmiyor) | 2 saniye |
| Kursun güncel `SD-boot` U-Boot'u | 0 (geri sayım yok, tuşa basılı tutmak gerekir) |
| Kursun eski videolarındaki U-Boot | 5 saniye |

> [!NOTE]
> `setenv bootdelay 10` + `saveenv` ile de aynı sonuç alınır. Ama bu sadece o kartın kayıtlı ortamını değiştirir; challenge, ayarın <b>U-Boot imajının kendisinde</b> değişmesini istiyor. Böylece imajı hangi karta koyarsan koy 10 saniye bekler.

### Çözüm

<b>1) Ayarı değiştir.</b> [9.3](#93-adım-adım-toolchain-kurulumu-ve-u-boot-derleme)'teki U-Boot kaynak klasöründe `menuconfig`'i aç ve şu ayarı `10` yap:

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

## 9.5 Özet

- Cross toolchain, PC'de (x86) çalışıp ARM kodu üretir. Önek: `arm-linux-gnueabihf-`.
- Toolchain'i derlenecek kaynağın yaşına göre seç; eski kaynak + yeni GCC = derleme hatası.
- Derleme üç komut: `distclean` → `am335x_evm_defconfig` → `make -j4`. Hepsinde `ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf-`.
- Çıktılar: `MLO` (SD/eMMC için), `spl/u-boot-spl.bin` (seri boot için), `u-boot.img` (ikisi için de).
- Kendi U-Boot'unun çalıştığını açılıştaki derleme tarihinden anlarsın.
- U-Boot'un davranışını değiştirmenin kalıcı yolu `menuconfig` ile `.config`'i değiştirip yeniden derlemektir (ör. `CONFIG_BOOTDELAY`).

## 9.6 Karşılaşılabilecek Problemler

![Sık görülen derleme hataları (temsili)](../images/uboot_build/08_errors.png)

| Hata | Sebep | Çözüm |
|---|---|---|
| `arm-linux-gnueabihf-gcc: not found` | Toolchain `PATH`'te değil | `echo $PATH` ile kontrol et, `source ~/.bashrc` çalıştır, yolu doğru yazdığından emin ol |
| `fatal error: linux/compiler-gccN.h: No such file or directory` | GCC, U-Boot/kernel kaynağından <b>daha yeni</b>. Eski kaynaklar sadece tanıdıkları GCC sürümleri için başlık dosyası içerir. | [9.2](#92-sürüm-uyumu-hangi-toolchain)'deki tablodan kaynağa uygun toolchain'i kullan |
| `multiple definition of 'yylloc'` | Eski kaynaktaki `dtc` + host'ta GCC 10 veya üstü | `scripts/dtc/dtc-lexer.l` (veya `.lex.c_shipped`) içinde `YYLTYPE yylloc;` satırını `extern YYLTYPE yylloc;` yap |
| `openssl/evp.h: No such file` | `libssl-dev` kurulu değil | `sudo apt install libssl-dev` |
| `bison: not found` / `flex: not found` | Host paketleri eksik | `sudo apt install bison flex` |
| `Your dtc is too old` | Host'taki `dtc` eski | `sudo apt install device-tree-compiler` |
| `*** Can't find default configuration "..."` | Yanlış `defconfig` adı | `ls configs \| grep am335x` |
| 32-bit Linaro 4.x toolchain çalışmıyor: `arm-linux-gnueabihf-gcc: No such file or directory` (dosya varken) | Eski toolchain 32-bit, 64-bit Ubuntu'da 32-bit kütüphaneler eksik | `sudo dpkg --add-architecture i386 && sudo apt update && sudo apt install libc6:i386 libstdc++6:i386 zlib1g:i386` |
| Kart açılıyor ama ekranda eski U-Boot tarihi var | Kart eMMC'den açıldı ya da SD'ye kopyalanan dosyalar eski | S2'ye basılı tutarak aç, `ls -l /media/$USER/BOOT` ile tarihleri kontrol et |
| SPL hiç çalışmıyor | `MLO` yerine `u-boot-spl.bin` kopyalandı ya da `MLO` çok büyük | SD karta `MLO` koy, boyutunu kontrol et (< 109 KB) |

---

[← Bölüm 8: TFTP ile Ağdan Boot](08_tftp_boot.md) · [İçindekiler](README.md) · [Bölüm 10: Linux Kernel: Kaynak Ağacı ve Derleme →](10_linux_kernel.md)
