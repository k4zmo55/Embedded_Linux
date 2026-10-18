<!-- Bu dosya otomatik üretildi. Düzenlemek için chapters/ altındaki kaynağı değiştir. -->
# Bölüm 12 — BusyBox ile Minimal Root Filesystem

> <b>Bu bölümde:</b>
> - BusyBox'ın ne olduğunu ve neden gömülü sistemlerde bu kadar yaygın kullanıldığını öğreneceksin.
> - BusyBox 1.36.1'i ARM için <b>statik</b> derleyip kendi root filesystem'ini sıfırdan kuracaksın.
> - Kernel modüllerini rootfs'e kurup kartı kendi kernel'in ve kendi rootfs'inle açacaksın.
> - BusyBox `init`'ini, `inittab`'ı ve `rcS` başlangıç betiklerini anlayacaksın.
> - USB üzerinden Ethernet sürücüsünü (`g_ether`) açılışta otomatik yükleyeceksin.
> - Rootfs'i NFS ile bilgisayardan bağlamayı göreceksin.
> - İki challenge: SSH ve TFTP desteği eklemek, BusyBox'ı dinamik derlemek.
>
> <b>Ön koşul:</b> [Bölüm 6](06_uboot_uenv.md) — rootfs klasörleri, [Bölüm 9](09_uboot_build.md) — cross toolchain, [Bölüm 10](10_linux_kernel.md) — kernel ve modüller.

---

## 12.1 Root Filesystem'de Neler Olmalı?

Kernel açılışın sonunda `root=` ile gösterilen dosya sistemini `/` olarak bağlar ve içindeki <b>`/sbin/init`</b>'i çalıştırır ([3.4](03_boot_process.md#34-linux-kernel-ve-root-filesystem)). Bundan sonra olan her şey rootfs'in işidir. Klasörlerin görevlerini [6.6.1](06_uboot_uenv.md#661-klasörler-ve-görevleri)'de görmüştük. Çalışan en küçük bir Linux için gerekenler şunlar:

| Gereken | Neden? | Bu bölümde nereden? |
|---|---|---|
| `/sbin/init` | Kernel'in çalıştırdığı ilk program (PID 1) | BusyBox |
| Bir kabuk (`/bin/sh`) ve temel komutlar | Sisteme komut verebilmek | BusyBox |
| `/dev`, `/proc`, `/sys` klasörleri | Kernel'in sanal dosya sistemleri buraya bağlanır | `mkdir` |
| `/etc/inittab`, `/etc/init.d/rcS` | `init`'in açılışta ne yapacağı | Elle yazacağız |
| `/lib/modules/<sürüm>/` | Modül olarak derlenen sürücüler | [Bölüm 10](10_linux_kernel.md)'daki `modules_install` |
| `/lib/*.so` (sadece dinamik derlemede) | Paylaşılan kütüphaneler | [12.11](#1211-challenge-2-busyboxı-dinamik-derlemek) |

> [!NOTE]
> Kursun "About RFS" ve "About initramfs" makaleleri bu konunun teorisini anlatıyor. initramfs, bu bölümde kuracağımız klasör yapısının sıkıştırılıp RAM'e yüklenen halidir. [Bölüm 7](07_uart_boot.md)'de kullandığımız `initramfs` dosyası da böyle bir BusyBox rootfs'idir.

---

## 12.2 BusyBox Nedir?

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

## 12.3 Adım Adım: BusyBox'ı Derlemek

> [!NOTE]
> Aşağıdaki ekran görüntüleri <b>temsilidir</b>. Çalışma klasörü `~/bbb`, rootfs `~/bbb/rootfs`. Toolchain [Bölüm 9](09_uboot_build.md)'da kurulan Linaro GCC 7.5.0.

### Adım 1 — İndir ve yapılandır

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
| Rootfs'te `/lib` gerekir mi? | Hayır | Evet ([12.11](#1211-challenge-2-busyboxı-dinamik-derlemek)) |
| Ne zaman? | İlk deneme, en basit rootfs. <b>Kursta kullanılan.</b> | Rootfs'e başka dinamik programlar da konacaksa |

### Adım 2 — Derle ve rootfs klasörüne kur

![BusyBox'ı derleme ve kurma](../images/busybox/02_build_install.png)

```bash
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- -j$(nproc)
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- CONFIG_PREFIX=~/bbb/rootfs install
file ~/bbb/rootfs/bin/busybox
```

`install` hedefi `busybox`'ı `~/bbb/rootfs/bin/` altına koyar ve bütün applet linklerini (`bin/`, `sbin/`, `usr/bin/`, `usr/sbin/`) oluşturur. `file` çıktısında <b>ARM</b> ve <b>statically linked</b> görmelisin.

> [!TIP]
> Statik derlemede `Using 'getpwnam' in statically linked applications requires at runtime the shared libraries...` gibi uyarılar görebilirsin. Bunlar glibc'nin statik bağlamadaki bilinen uyarılarıdır, derleme başarılıdır.

### Adım 3 — Kernel modüllerini kur

Kursun "Kernel Modules installation" dersi: [Bölüm 10](10_linux_kernel.md)'da derlediğin modülleri aynı rootfs klasörüne kur. Bunu daha önce yaptıysan atlayabilirsin.

```bash
cd ~/bbb/linux
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- INSTALL_MOD_PATH=~/bbb/rootfs modules_install
ls ~/bbb/rootfs/lib/modules/          # 5.10.162
```

> [!IMPORTANT]
> `/lib/modules/` altındaki klasör adı, çalışan kernel'in `uname -r` çıktısıyla <b>birebir aynı</b> olmalı. Kernel'i yeniden derleyip sürüm değiştiysen modülleri de yeniden kur. Aksi halde `modprobe` modülleri bulamaz.

---

## 12.4 Rootfs'i Tamamlamak

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

## 12.5 BusyBox `init`, `inittab` ve `rcS`

Kernel rootfs'i bağladıktan sonra şu zincir çalışır:

```
kernel  ──►  /sbin/init  (BusyBox, PID 1)
                 │  /etc/inittab'ı okur
                 ├── ::sysinit   → /etc/init.d/rcS        (bir kez, açılışta)
                 │                    └── /etc/init.d/S??*  sırayla "start" ile
                 ├── ::askfirst  → /bin/sh                (konsolda Enter'a basınca kabuk)
                 └── ::shutdown  → /etc/init.d/rcK        (kapanırken, ters sırayla "stop")
```

### `/etc/inittab`

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

### `/etc/init.d/rcS` — kursun betiği

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

`echo "Mounting proc"` satırından sonraya şu iki satırı da eklemeni öneririm. `sysfs` birçok aracın ve [Bölüm 1](01_bbb_hardware.md)'deki LED komutlarının, `devpts` ise SSH'ın ([12.10](#1210-challenge-1-ssh-ve-tftp-desteği)) çalışması için gerekli:

```sh
mount -t sysfs sysfs /sys
mkdir -p /dev/pts && mount -t devpts devpts /dev/pts
```

`rcK` aynı döngüyü <b>ters sırada</b> ve `stop` parametresiyle çalıştırır. Numaralar sırayı belirler: `S01` önce, `S50` sonra başlar; kapanırken tersi.

Kursun reposundaki betikler:

| Betik | Görevi |
|---|---|
| `S01logging` | `syslogd` ve `klogd`'yi başlatır (loglar `/var/log/messages`'a) |
| `S02module` | Açılışta kernel modüllerini yükler ([12.7](#127-usb-üzerinden-ethernet-ve-sürücüleri-açılışta-yüklemek)) |
| `S40network` | `/etc/network/interfaces`'teki arayüzleri `ifup -a` ile açar |
| `S50sshd` | OpenSSH sunucusunu başlatır. BusyBox rootfs'inde OpenSSH olmadığı için kendi başına çalışmaz ([12.10](#1210-challenge-1-ssh-ve-tftp-desteği)'da yerine Dropbear kullanıyoruz) |

Betiklerin hepsini rootfs'e koy ve <b>çalıştırılabilir</b> yap:

```bash
cd ~/bbb/rootfs/etc/init.d
# rcS, rcK, S01logging, S02module, S40network dosyalarını buraya kopyala
chmod +x rcS rcK S*
```

---

## 12.6 Kartta Test: Rootfs SD Kartta

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

<b>2) BOOT bölümündeki `uEnv.txt`</b> ([10.9](10_linux_kernel.md#109-yeni-kerneli-kartta-denemek)'dakinin rootfs'i SD kart olan hali):

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

## 12.7 USB Üzerinden Ethernet ve Sürücüleri Açılışta Yüklemek

Kursun "Enabling ethernet over usb by driver integration" ve "Auto loading drivers during system startup" dersleri.

### USB gadget: `g_ether`

BBB'nin mini-USB portu (USB0) <b>gadget</b> (cihaz) modunda çalışabilir. `g_ether` sürücüsü yüklenince kart, bilgisayara USB üzerinden bir <b>ağ kartı</b> gibi görünür. Ethernet kablosu olmadan SSH, TFTP, NFS yapılabilir. Kursun `192.168.7.x` adresleri bu ağdan gelir.

`bb.org_defconfig`'te bu sürücü <b>modül</b> olarak derlenir (`CONFIG_USB_ETH=m`, [10.8](10_linux_kernel.md#108-adım-adım-kerneli-derleme)). Başka bir defconfig kullanıyorsan `menuconfig`'te açman gerekir:

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

### Açılışta otomatik yüklemek

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

## 12.8 Rootfs'i NFS ile Bilgisayardan Bağlamak

Rootfs'i her değişiklikte SD karta kopyalamak yorucu. <b>NFS</b> (Network File System) ile kart, rootfs'i doğrudan bilgisayardaki bir klasörden bağlar. Bilgisayarda bir dosyayı değiştirdiğin anda kart da görür. [Bölüm 8](08_tftp_boot.md)'deki TFTP ile birlikte geliştirme döngüsü şöyle olur:

```
Host PC                                      BBB
 /var/lib/tftpboot/uImage, .dtb  ── TFTP ──►  U-Boot: RAM'e yükle, bootm
 /srv/nfs/bbb/  (rootfs)     ── NFS  ──►  Kernel: / olarak bağla
```

### Adım 1 — Host'ta NFS sunucusu

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

### Adım 2 — `uEnv.txt`

Kursun `uEnv-nfs.txt` dosyası temel alındı. Kursun dosyası USB ağı (`192.168.7.x`) kullanıyor; burada [Bölüm 8](08_tftp_boot.md)'deki Ethernet kablosu ve adresleri kullanılıyor:

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
| `ip=<kart>:<sunucu>::<maske>::eth0:off` | Kernel'in IP'sini kendisi ayarlaması. U-Boot'un IP'si kernel'e geçmez ([8.7](08_tftp_boot.md#87-linux-açıldıktan-sonra-tftp-ile-dosya-çekme)). |
| `init=/sbin/init` | Çalıştırılacak ilk program (varsayılan da budur) |

`uImage` ve `am335x-boneblack.dtb`'yi `/var/lib/tftpboot`'a kopyalamayı unutma.

### Adım 3 — Aç ve doğrula

![Rootfs'in NFS'ten bağlanması](../images/busybox/08_nfs_boot.png)

```text
/ # mount | head -1
192.168.27.1:/srv/nfs/bbb on / type nfs (rw,...,vers=3,...)
```

> [!WARNING]
> Rootfs NFS'ten geliyorken kartta <b>`eth0`'ı yeniden yapılandırma</b> (`ifconfig eth0 ...`, `/etc/network/interfaces`'e `eth0` eklemek). Ağ bir an bile kesilirse kernel rootfs'e ulaşamaz ve sistem donar. `eth0`'ı kernel `ip=` ile ayarlıyor; `interfaces` dosyasında sadece `lo` ve `usb0` kalsın.

> [!NOTE]
> Kursun `uEnv-nfs.txt`'si NFS'i USB ağı (`usb0`) üzerinden yapar. Bunun için `g_ether`'in modül değil <b>kernel'e gömülü</b> (`CONFIG_USB_ETH=y`) olması gerekir; çünkü rootfs bağlanmadan modül yüklenemez ([10.7](10_linux_kernel.md#107-kernel-yapılandırması-kconfig-config-menuconfig)). Ethernet kablosunda bu sorun yok, CPSW sürücüsü zaten gömülü.

---

## 12.9 Geliştirme Döngüsü

| Ne değişti? | Ne yaparsın? |
|---|---|
| Kendi uygulaman / bir betik | Dosyayı `/srv/nfs/bbb` içine kopyala. Kart hemen görür, yeniden başlatma yok. |
| Kernel veya DTB | `uImage` / `.dtb`'yi `/var/lib/tftpboot`'a kopyala, kartı resetle. |
| Kernel modülleri | `modules_install INSTALL_MOD_PATH=/srv/nfs/bbb` (sudo ile), kartta `modprobe` ya da reset |
| BusyBox ayarları | BusyBox'ı yeniden derle, `CONFIG_PREFIX=/srv/nfs/bbb` ile kur |

---

## 12.10 Challenge 1: SSH ve TFTP Desteği

Kursun bu bölümdeki ilk challenge'ı:

> <i>BusyBox ile minimal bir dosya sistemi kurup kartta test ettin. Şimdi onu birkaç araçla zenginleştir: kart ile bilgisayar arasında <b>TFTP</b> ve <b>SSH</b> ile dosya aktarımı yapılabilsin. BusyBox'ta SSH desteği yoktur; üçüncü parti bir kaynaktan eklenmesi gerekir. İpucu: <https://busybox.net/tinyutils.html></i>

### TFTP

BusyBox'ın `defconfig`'inde `tftp` applet'i zaten açık (`Networking Utilities → tftp`). Kullanımı [8.7](08_tftp_boot.md#87-linux-açıldıktan-sonra-tftp-ile-dosya-çekme)'deki gibi:

```text
/ # tftp -g -r dosya 192.168.27.1        # host'tan al
/ # tftp -p -l dosya 192.168.27.1        # host'a gönder
```

### SSH: Dropbear

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
> Dropbear, kabuk açmak için `/dev/pts`'e ihtiyaç duyar. [12.5](#125-busybox-init-inittab-ve-rcs)'te `rcS`'e eklediğimiz `mount -t devpts devpts /dev/pts` satırı yoksa bağlantı `PTY allocation request failed` ile kapanır.

---

## 12.11 Challenge 2: BusyBox'ı Dinamik Derlemek

Kursun ikinci challenge'ı:

> <i>BusyBox derslerinin hepsinde "statik" derlenmiş programlar kullandık. Dinamik bağlanarak (dynamic linking) cross compile edilmiş bir uygulamayı bu dosya sisteminde çalıştırırsan çalışmaz. BusyBox'ı <b>dinamik</b> bağlanmış programlar üretecek şekilde yeniden derle ve dinamik bağlanmış bir uygulamanın çalıştığını test et.</i>

### Neden dinamik program çalışmıyor?

Dinamik bağlanmış bir program, çalışırken iki şeye ihtiyaç duyar:
1. <b>Dinamik yükleyici</b>: ARM hard-float'ta `/lib/ld-linux-armhf.so.3`. Kernel programı başlatırken önce bunu çalıştırır.
2. Programın kullandığı <b>paylaşılan kütüphaneler</b>: `libc.so.6`, `libm.so.6`...

Statik BusyBox rootfs'inde `/lib` altında sadece kernel modülleri vardır. Yükleyici yoksa kernel programı hiç başlatamaz ve kabuk yanıltıcı bir şekilde `not found` der.

### Çözüm

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

## 12.12 Özet

- BusyBox, yüzlerce komutu tek bir programda toplar; komutlar ona giden sembolik linklerdir.
- Minimal rootfs = BusyBox + `dev proc sys etc tmp var` klasörleri + `/etc/inittab` + `/etc/init.d/rcS` + `/lib/modules`.
- Açılış: kernel → `/sbin/init` (PID 1) → `inittab` → `rcS` → `S??*` betikleri sırayla → konsolda kabuk.
- `g_ether` kartı USB üzerinden bir ağ kartı yapar; `S02module` + `S40network` ile açılışta otomatik yüklenir.
- NFS + TFTP ile rootfs ve kernel bilgisayardan gelir; dosyayı kopyalamak, kartta denemek için yeterli olur.
- SSH için Dropbear, dinamik programlar için `/lib`'e toolchain sysroot'undaki kütüphaneler gerekir.

## 12.13 Karşılaşılabilecek Problemler

![Sık görülen hatalar (temsili)](../images/busybox/11_errors.png)

| Belirti | Sebep | Çözüm |
|---|---|---|
| `Kernel panic - not syncing: No working init found` | `/sbin/init` yok, ARM için derlenmemiş ya da dinamik derlenmiş ama `/lib`'te kütüphane yok | `file bin/busybox` → ARM ve statik olmalı (veya [12.11](#1211-challenge-2-busyboxı-dinamik-derlemek)) |
| `can't open /dev/tty2: No such file or directory` | `/etc/inittab` yok, BusyBox varsayılan olarak tty2–tty4'ü açmaya çalışıyor | [12.5](#125-busybox-init-inittab-ve-rcs)'teki `inittab`'ı ekle |
| `/etc/init.d/rcS: Permission denied` | Betik çalıştırılabilir değil | `chmod +x etc/init.d/rcS etc/init.d/S*` |
| `modprobe: can't change directory to '/lib/modules'` | Modüller kurulmamış ya da sürüm klasörü `uname -r` ile uyuşmuyor | `modules_install INSTALL_MOD_PATH=...` ile yeniden kur |
| `VFS: Unable to mount root fs via NFS` | NFS sürümü (v2), `exports` hatası, yanlış `ip=` / `nfsroot=` | `nfsroot=...,v3,tcp`; host'ta `showmount -e`; firewall'da NFS'e izin |
| `ifup: can't open '/etc/network/interfaces'` | Dosya yok | [12.7](#127-usb-üzerinden-ethernet-ve-sürücüleri-açılışta-yüklemek)'deki dosyayı oluştur |
| `run-parts: /etc/network/if-pre-up.d: No such file or directory` | BusyBox `ifup`'ın aradığı klasörler yok | `mkdir -p etc/network/if-{pre-up,up,down,post-down}.d` |
| SSH: `PTY allocation request failed` | `/dev/pts` bağlı değil | `rcS`'e `mount -t devpts devpts /dev/pts` ekle |
| SSH: `Permission denied` | root'un şifresi yok | Kartta `passwd` |
| Derleme: `networking/tc.c: error: 'TCA_CBQ_MAX' undeclared` | Toolchain'in kernel başlıkları çok yeni (6.8+), BusyBox 1.36'nın `tc` applet'i derlenmiyor | `menuconfig` → Networking Utilities → `tc`'yi kapat |
| Kartta dosyalar `root` yerine `nobody` sahipliğinde görünüyor | `no_root_squash` eksik | `/etc/exports`'a ekle, `sudo exportfs -ra` |

---

[← Bölüm 11: Linux Device Tree](11_device_tree.md) · [İçindekiler](README.md)
