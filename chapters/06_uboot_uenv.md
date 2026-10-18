# Bölüm 6 — U-Boot Komut Satırı ve uEnv.txt

> <b>Bu bölümde:</b>
> - `uEnv.txt` dosyasının <b>satır satır ne yaptığını</b> anlayacaksın.
> - Bu dosyayı SD karta kopyalamadan, <b>seri port (UART) üzerinden</b> doğrudan U-Boot'a göndereceksin (`loady`, `env import`).
> - Kursun challenge'ı: boot imajlarını eMMC yerine <b>SD karttan (MMC0)</b> yükleyeceksin. Ek alıştırmada da tersini yapıp rootfs'i <b>eMMC'den</b> bağlayacaksın.
> - <b>ROOTFS</b> bölümünde hangi klasör ve dosyaların olduğunu ve bunlara <b>hangi komutlarla</b> ulaşacağını göreceksin.
>
> <b>Ön koşul:</b> [Bölüm 4](04_sd_card_boot.md) — SD karttan boot, [Bölüm 5](05_emmc_boot.md) — eMMC'deki Debian.

> [!NOTE]
> Bu bölümdeki terminal görüntüleri temsilidir. Senin kartında U-Boot sürümü, dosya boyutları ve bölüm boyutları farklı görünebilir.

---

## 6.1 Temel Kavramlar

| Kavram | Ne işe yarar? |
|---|---|
| <b>`uEnv.txt`</b> | U-Boot ortam değişkenlerini <b>metin olarak</b> tanımlayan dosya. Her satır `isim=değer` biçimindedir. U-Boot'un bu dosyayı açılışta otomatik okuyup okumaması, U-Boot'un yapılandırmasına bağlıdır (BBB'nin varsayılan U-Boot'u SD karttaki `uEnv.txt`'yi arar). |
| <b>Ortam değişkeni (environment)</b> | U-Boot'un ayarları ve makroları. `printenv` ile görülür, `setenv` ile değiştirilir, `saveenv` ile kalıcı kaydedilir. |
| <b>Minicom</b> | Bilgisayardan seri port (UART) üzerinden karta bağlanmayı sağlayan terminal programı ([Bölüm 2](02_serial_console.md)). |
| <b>`loady`</b> | U-Boot'ta <b>YMODEM</b> protokolüyle seri porttan dosya alıp RAM'e yazan komut. |
| <b>`env import -t <adres> <boyut>`</b> | RAM'deki `isim=değer` metnini okuyup U-Boot'un <b>aktif</b> ortamına ekler. `-t` "düz metin" demektir, `<boyut>` metnin bayt cinsinden uzunluğudur. |

Bütün akış şöyle:

```
Bilgisayar (uEnv.txt) ──YMODEM / UART──► RAM 0x82000000 ──env import──► U-Boot ortamı ──boot──► Linux
```

---

## 6.2 `uEnv.txt` Satır Satır

Kullanacağımız dosya bu:

```text
mypcip=setenv serverip 192.168.1.2
ipaddr=192.168.27.1
bootargs=console=ttyO0,115200 root=/dev/mmcblk0p2 rw
bootcmd=echo "**********Booting from memory**********";load mmc 0:1 0x82000000 uImage;load mmc 0:1 0x88000000 am335x-boneblack.dtb;bootm 0x82000000 - 0x88000000
```

### `mypcip` ve `ipaddr` — ağ ayarları

| Satır | Anlamı |
|---|---|
| `mypcip=setenv serverip 192.168.1.2` | Bir <b>makro</b>. Kendi başına hiçbir şey yapmaz; `run mypcip` yazınca içindeki komut çalışır ve `serverip` (TFTP/NFS sunucusunun, yani bilgisayarın IP'si) `192.168.1.2` olur. |
| `ipaddr=192.168.27.1` | Kartın kendi statik IP adresi. |

> [!WARNING]
> Bu örnekte kart `192.168.27.x`, sunucu `192.168.1.x` ağında. Ağ geçidi (`gatewayip`) tanımlanmadığı sürece TFTP/NFS çalışmaz. Ağdan boot yapacaksan iki adresi <b>aynı alt ağda</b> seç ([Bölüm 8](08_tftp_boot.md)). SD karttan boot için bu iki satır kullanılmaz.

### `bootargs` — kernel'e verilen parametreler

`bootargs=console=ttyO0,115200 root=/dev/mmcblk0p2 rw`

| Parça | Anlamı |
|---|---|
| `console=ttyO0,115200` | Linux mesajları UART0'a (J1 header) 115200 baud ile yazılsın. `ttyO0` eski OMAP kernel'lerindeki addır; yeni kernel'lerde `ttyS0` olur. |
| `root=/dev/mmcblk0p2` | Root filesystem: MMC aygıtı <b>0</b>, bölüm <b>2</b> (`p2`). |
| `rw` | Rootfs okuma-yazma modunda bağlansın. |

### `bootcmd` — otomatik açılış komutu

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
> `mmc 0` ↔ `/dev/mmcblk0` eşleşmesi çoğu kurulumda doğrudur ama <b>garanti değildir</b>. U-Boot tarafında `mmc list`, Linux tarafında `lsblk` ile kontrol et ([6.5](#65-ek-alıştırma-kernel-ve-dtb-sd-karttan-rootfs-emmcden)).

---

## 6.3 Uygulama: `uEnv.txt`'yi Seri Porttan Göndermek

Normalde `uEnv.txt` SD kartın BOOT bölümüne kopyalanır. Her değişiklikte SD kartı çıkar-tak yapmak yerine dosyayı <b>seri porttan</b> gönderip anında deneyebiliriz.

### Adım 1 — Bilgisayarda dosyayı hazırla ve Minicom'u aç

Dosyanın içeriğini ve <b>boyutunu</b> kontrol et, sonra Minicom ile karta bağlan:

![uEnv.txt hazırlama ve Minicom'u açma](../images/uenv/01_uenv_hazirla.png)

> [!TIP]
> Windows'ta port adı `/dev/ttyUSB0` yerine `COM3` gibi olur ([2.6](02_serial_console.md#26-windowsta-tera-term)).

### Adım 2 — U-Boot'u durdur

Kartı aç. `Hit any key to stop autoboot` yazısı çıkınca <b>bir tuşa bas</b>. `U-Boot#` komut satırı gelmeli:

![U-Boot autoboot'u durdurma](../images/uenv/02_uboot_durdur.png)

### Adım 3 — `loady` ile dosyayı RAM'e al

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

### Adım 4 — `env import` ile ortama aktar ve kontrol et

```text
U-Boot# env import -t 0x82000000 ${filesize}
U-Boot# printenv bootargs
U-Boot# printenv bootcmd
```

![env import ve printenv](../images/uenv/04_env_import.png)

`printenv` çıktısı `uEnv.txt`'deki değerlerle aynıysa aktarım başarılıdır. `run mypcip` ile makronun da çalıştığını görebilirsin.

> [!WARNING]
> `${filesize}` yerine boyutu elle yazarsan <b>hex</b> olarak yaz (`0x10d` veya `10d`). U-Boot sayıları varsayılan olarak hex kabul eder; `269` yazarsan `0x269` = 617 bayt okur ve dosyanın sonundaki çöp veriyi de içe aktarmaya çalışır.

### Adım 5 — Boot et

```text
U-Boot# boot
```

`boot` komutu `bootcmd`'yi çalıştırır. Ekrana bizim `echo` mesajımız gelmeli:

![bootcmd ile açılış](../images/uenv/05_boot.png)

### Dikkat edilecekler

| Konu | Açıklama |
|---|---|
| <b>Adres çakışması</b> | `uEnv.txt` `0x82000000`'a yüklendi; `bootcmd` de kernel'i aynı adrese yüklüyor. Sorun değil, çünkü `env import` dosyayı önce okuyup bitiriyor, kernel <b>sonra</b> üzerine yazılıyor. Sıra ters olursa kernel bozulur. |
| <b>Geçicilik</b> | `env import` sadece RAM'deki aktif ortamı değiştirir. Kart yeniden açılınca değişiklikler kaybolur. |
| <b>Kalıcı yapmak</b> | Her şeyin doğru olduğundan emin olduktan sonra `saveenv` ile kaydedilebilir. Bu komut kalıcı U-Boot ortamının üzerine yazar; geri dönmek için `env default -a` + `saveenv` gerekir. |
| <b>Otomatik okumada `bootcmd`</b> | BBB'nin varsayılan U-Boot'u SD karttaki `uEnv.txt`'yi kendi `bootcmd`'si <b>çalışırken</b> okur ve `uenvcmd` değişkenini arar. Bu yüzden SD karttaki `uEnv.txt`'de `bootcmd` tanımlamak o açılışı etkilemez; orada `uenvcmd` kullanılır ([4.8](04_sd_card_boot.md#bu-açılışta-uenvtxt-ne-yaptı)'deki örnek gibi). Seri porttan yüklemede ise `boot` komutunu biz verdiğimiz için `bootcmd` çalışır. |

---

## 6.4 Challenge: Boot İmajlarını MMC0'dan (SD Kart) Yüklemek

### Görev

Kursun bu bölümdeki challenge'ı:

> <i>Derste boot imajları (uImage ve DTB) <b>MMC1</b>'den (eMMC) yüklendi, dosya sistemi olarak <b>MMC0</b>'daki (microSD) rootfs kullanıldı. `uEnv.txt`'yi, boot imajları da <b>MMC0</b>'dan (microSD) yüklenecek şekilde değiştir.</i>

| | Önce | Sonra |
|---|---|---|
| Kernel + DTB | eMMC (`mmc 1`) | <b>SD kart (`mmc 0`)</b> |
| Rootfs | SD kart, 2. bölüm (`/dev/mmcblk0p2`) | Değişmez |

### Çözüm

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

[6.2](#62-uenvtxt-satır-satır)'deki dosyanın `bootcmd` satırı tam olarak bunu yapıyor:

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

## 6.5 Ek Alıştırma: Kernel ve DTB SD Karttan, Rootfs eMMC'den

### Görev

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

### Adım 1 — Aygıt numaralarını doğrula

Önce varsayımımızı kontrol edelim: `mmc 0` gerçekten SD kart, `mmc 1` gerçekten eMMC mi ve eMMC'de 2. bölüm var mı?

```text
U-Boot# mmc list
U-Boot# mmc dev 1
U-Boot# mmc part
```

![mmc list ve mmc part](../images/uenv/06_mmc_list.png)

eMMC'de `83` (Linux) tipinde 2. bölüm görünüyorsa rootfs için doğru yerdeyiz.

### Adım 2 — Sadece `bootargs`'ı değiştir

Kernel ve DTB hâlâ SD karttan yükleneceği için <b>`bootcmd` aynı kalır</b>. Değişen tek şey, kernel'e "rootfs nerede?" bilgisini veren `bootargs`:

| | Değer |
|---|---|
| <b>Eski</b> — rootfs SD kartta | `bootargs=console=ttyO0,115200 root=/dev/mmcblk0p2 rw` |
| <b>Yeni</b> — rootfs eMMC'de | `bootargs=console=ttyO0,115200 root=/dev/mmcblk1p2 rw` |

Bunu iki yolla yapabilirsin:

- <b>a)</b> `uEnv.txt`'deki satırı değiştirip [6.3](#63-uygulama-uenvtxtyi-seri-porttan-göndermek)'teki gibi tekrar gönder.
- <b>b)</b> Doğrudan U-Boot'ta `setenv` ile değiştir:

```text
U-Boot# setenv bootargs console=ttyO0,115200 root=/dev/mmcblk1p2 rw
U-Boot# boot
```

![bootargs'ı eMMC'ye çevirme](../images/uenv/07_bootargs_emmc.png)

### Adım 3 — Linux'ta sonucu doğrula

Kart açılınca rootfs'in gerçekten eMMC'den bağlandığını kontrol et:

```bash
cat /proc/cmdline   # kernel'e giden bootargs
lsblk               # hangi bölüm / olarak bağlı?
findmnt /           # rootfs'in kaynağı
```

![Linux'ta rootfs doğrulama](../images/uenv/08_linux_dogrula.png)

`/` bağlama noktası `mmcblk1p2`'nin yanında görünüyorsa challenge tamam.

### Sonuç

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

## 6.6 ROOTFS Bölümünde Neler Var?

<b>Root filesystem (rootfs)</b>, Linux'un `/` (kök) dizinidir. Kernel açıldıktan sonra `root=` ile gösterilen bölümü `/` olarak bağlar ve bundan sonra çalışan <b>her program, her ayar dosyası ve her kütüphane</b> buradan okunur. Kernel tek başına bir işe yaramaz; kullanıcıya kabuk (shell), komutlar ve servisler rootfs ile gelir.

Rootfs'teki klasör düzeni rastgele değildir; <b>FHS (Filesystem Hierarchy Standard)</b> denen ortak bir standarda uyar. Bu yüzden Ubuntu'da, BeagleBone'daki Ångström'de veya eMMC'deki Debian'da aynı klasörleri görürüz.

### 6.6.1 Klasörler ve görevleri

| Klasör | İçinde ne var? | BBB'de örnek | Bakmak için |
|---|---|---|---|
| <b>`/bin`</b> | Temel kullanıcı komutları (`ls`, `cp`, `cat`, `sh`...) | `bash`, `busybox` | `ls /bin` |
| <b>`/sbin`</b> | Sistem yönetimi komutları (genelde root için) | `init`, `mount`, `ifconfig`, `reboot` | `ls /sbin` |
| <b>`/boot`</b> | Kernel ve device tree dosyaları | `uImage`, `am335x-boneblack.dtb` | `ls -l /boot` |
| <b>`/etc`</b> | Sistem <b>ayar</b> dosyaları (metin) | `hostname`, `fstab`, `passwd`, `os-release` | `cat /etc/hostname` |
| <b>`/lib`</b> | Paylaşılan kütüphaneler (`.so`) ve kernel modülleri | `libc.so.6`, `modules/{{prebuilt.kernel_version}}/` | `ls /lib/modules` |
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

### 6.6.2 ROOTFS'e üç yerden ulaşabiliriz

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

### 6.6.3 a) Bilgisayardan ulaşmak

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
> `file bin/bash` çıktısında `ARM` yazdığı için bu programları bilgisayarda <b>çalıştıramazsın</b> (`./bin/bash` → `Exec format error`). Sadece okuyabilir/kopyalayabilirsin. Bunun sebebini [Bölüm 9](09_uboot_build.md)'da (cross compile) göreceğiz.

### 6.6.4 b) U-Boot'tan ulaşmak

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
| `load mmc 0:2 0x82000000 /boot/uImage` | Dosyayı RAM'e yükler ([4.10.2](04_sd_card_boot.md#4102-uimageı-ddre-yükle)) |
| `ext4ls` / `ext2ls` / `fatls` | Eski U-Boot sürümlerinde dosya sistemine özel `ls` komutları |

> [!NOTE]
> U-Boot'ta `cd` yoktur ve dosya içeriğini `cat` ile göremezsin; her komutta tam yolu yazarsın. U-Boot rootfs'e normalde <b>yazmaz</b>, sadece okur.

### 6.6.5 c) BBB Linux'tan ulaşmak

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

#### Kök dizin ve `/bin`

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

#### `/etc` — ayar dosyaları

```bash
cat /etc/hostname      # kartın adı
cat /etc/os-release    # hangi dağıtım, hangi sürüm
cat /etc/fstab         # açılışta hangi bölüm nereye bağlanacak
head -2 /etc/passwd    # kullanıcı listesi
```

![BBB'de /etc dosyaları](../images/rootfs/05_bbb_etc.png)

#### `/proc` ve `/sys` — kernel ile konuşmak

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

#### `/dev`, `/boot` ve disk kullanımı

```bash
ls /dev/mmcblk* /dev/ttyO*   # MMC bölümleri ve seri portlar
ls -l /boot                  # kernel ve dtb
df -h /                      # rootfs ne kadar dolu, hangi bölümden geliyor
du -sh /usr /lib /etc        # en çok yer kaplayan klasörler
mount | grep -E ' / | /proc | /sys | /dev '   # gerçek ve sanal bağlamalar
```

![BBB'de /dev, /boot ve disk kullanımı](../images/rootfs/07_bbb_dev_boot.png)

`mount` çıktısında `/` gerçek bir diskten (`/dev/mmcblk0p2`, `ext3`) gelirken `/dev`, `/proc` ve `/sys`'in tipi `devtmpfs`, `proc`, `sysfs` olarak görünür. Bu, [6.6.1](#661-klasörler-ve-görevleri)'deki sanal klasörlerin kanıtıdır. Rootfs'i eMMC'den açtıysan ([6.5](#65-ek-alıştırma-kernel-ve-dtb-sd-karttan-rootfs-emmcden)) `df -h /` satırında `/dev/mmcblk1p2` görürsün.

---

## 6.7 Özet

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

## 6.8 Karşılaşılabilecek Problemler

| Belirti | Sebep | Çözüm |
|---|---|---|
| `loady` sonrası transfer başlamıyor | Minicom'da xmodem seçildi ya da `lrzsz` yok | Protokol <b>ymodem</b> olmalı; `sudo apt install lrzsz` |
| `env import` sonrası değişkenler bozuk / fazladan satırlar | Boyut ondalık yazıldı | `${filesize}` kullan ya da boyutu hex yaz |
| `## Error: "mypcip" not defined` | `env import` yapılmadı ya da kart yeniden açıldı | Adım 3–4'ü tekrarla; değişiklikler kalıcı değildir |
| `VFS: Unable to mount root fs` (challenge) | Linux'ta eMMC'nin numarası farklı | `root=/dev/mmcblk0p2` dene; Linux'ta `lsblk` ile kontrol et |
| Açılışta `uEnv.txt`'deki `bootcmd` çalışmıyor | Otomatik okumada `bootcmd` değil `uenvcmd` çalıştırılır | SD karttaki dosyada komutları `uenvcmd`'ye yaz |
