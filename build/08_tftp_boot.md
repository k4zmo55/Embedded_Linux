<!-- Bu dosya otomatik üretildi. Düzenlemek için chapters/ altındaki kaynağı değiştir. -->
# Bölüm 8 — TFTP ile Ağdan Boot

> <b>Bu bölümde:</b>
> - Bilgisayarına bir TFTP sunucusu (`tftpd-hpa`) kuracaksın.
> - Kernel, DTB ve initramfs'i her açılışta <b>Ethernet üzerinden</b> host'tan çekerek kartı açacaksın: önce komutları elle yazarak, sonra `uEnv.txt` ile otomatik olarak.
> - Neden bazı dosyaların yine de SD kartta durmak zorunda olduğunu anlayacaksın.
> - Challenge: eMMC → SD → TFTP → NFS sırasıyla deneyen genel bir `uEnv.txt` yazacaksın.
>
> <b>Ön koşul:</b> [Bölüm 4](04_sd_card_boot.md) — SD kart, [Bölüm 6](06_uboot_uenv.md) — `uEnv.txt` ve U-Boot komutları, [Bölüm 7](07_uart_boot.md) — RAM adresleri ve `bootm`.

---

## 8.1 Genel Bakış

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

## 8.2 Neden Bütün Dosyalar TFTP ile Gönderilmiyor?

Kısaca: <b>TFTP isteğini yapacak kod U-Boot'un içinde.</b> U-Boot ağdan gelecek olsaydı, onu ağdan isteyecek bir program olmazdı. Bu bir tavuk-yumurta problemi.

### Boot zinciri

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
- <b>ROM Code'un okuyabileceği yerler sabittir.</b> BBB'nin boot listesinde Ethernet yoktur ([3.5](03_boot_process.md#35-boot-kaynakları-ve-boot-sırası-sysboot-pinleri)). AM335x'in ROM'u aslında Ethernet'ten boot'u destekler, ama BBB'de bu seçeneği açmak için donanımda değişiklik gerekir.

> [!NOTE]
> U-Boot'un başlattığı sürücüler <b>kalıcı değildir</b>. U-Boot sadece dosya yükleyip kernel'i çalıştırmak için gereken sürücüleri başlatır. Kernel açılınca bütün donanımı kendi sürücüleriyle <b>yeniden</b> başlatır.

### Bunun amacı: geliştirmeyi hızlandırmak

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

## 8.3 TFTP Host'u Hazırlama

> [!NOTE]
> Aşağıdaki ekran görüntüleri <b>temsilidir</b>; sürüm numaraları, tarih ve PID değerleri senin bilgisayarında farklı olacaktır.

### Adım 1 — Paket listesini güncelle

![apt-get update ve apt upgrade](../images/tftp_boot/01_apt_update.png)

```bash
sudo apt-get update
sudo apt upgrade
```

### Adım 2 — TFTP sunucusunu kur

`tftpd-hpa`, Trivial File Transfer Protocol için bir sunucu (daemon) programıdır.

![tftpd-hpa kurulumu](../images/tftp_boot/02_install_tftpd.png)

```bash
sudo apt-get install tftpd-hpa
```

### Adım 3 — Ayar dosyasını düzenle

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

### Adım 4 — tftpboot klasörünü oluştur

![tftpboot klasörünü oluşturma ve izinler](../images/tftp_boot/04_tftpboot_dir.png)

```bash
sudo mkdir -p /var/lib/tftpboot
sudo chown tftp:tftp /var/lib/tftpboot
sudo chmod -R 777 /var/lib/tftpboot
```

### Adım 5 — TFTP servisini başlat ve kontrol et

![tftpd-hpa servisini başlatma ve durum kontrolü](../images/tftp_boot/05_tftpd_start.png)

```bash
sudo systemctl start tftpd-hpa
systemctl status tftpd-hpa       # "active (running)" görmelisin
sudo ss -ulpn | grep :69         # UDP 69 dinleniyor mu?
```

> [!TIP]
> Ayar dosyasını sonradan değiştirirsen servisi yeniden başlat: `sudo systemctl restart tftpd-hpa`

---

## 8.4 Bağlantılar

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

## 8.5 Yol 1 — Komutları Elle Yazarak TFTP ile Boot

İki yol var:

| | Yol 1 — Elle (bu başlık) | Yol 2 — uEnv.txt ile otomatik ([8.6](#86-yol-2--uenvtxt-ile-otomatik-tftp-boot)) |
|---|---|---|
| Nasıl? | Her açılışta U-Boot'u durdurup komutları minicom'a yazarsın | Komutlar SD karttaki `uEnv.txt`'de durur, U-Boot kendisi çalıştırır |
| Ne zaman? | İlk deneme, hata ayıklama: hangi komutun nerede takıldığını görürsün | Kurulum bir kez çalıştıktan sonra, günlük geliştirmede |

Önce Yol 1 ile bir kere çalıştır, sonra Yol 2'ye geç. Yol 2'deki `uEnv.txt` aynı komutları içerdiği için bir hata olursa Yol 1'e dönüp tek tek denersin.

> [!NOTE]
> Aşağıdaki ekran görüntüleri <b>temsilidir</b>; arayüz adı (`enp3s0`), sürüm, tarih, boyut ve hız değerleri senin ortamında farklı olacaktır.

### Adım 1 — Host'un Ethernet arayüzüne IP ver, dosyaları kopyala

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

### Adım 2 — SD kartı hazırla (1. bölüm: BOOT)

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
- <b>Otomatik boot için:</b> [8.6](#86-yol-2--uenvtxt-ile-otomatik-tftp-boot)'daki `uEnv.txt`'yi koy.

Kartı SD karttan açmak için <b>S2 butonuna basılı tutarak</b> güç ver. Basmazsan kart eMMC'den açılır.

### Adım 3 — U-Boot'u durdur, ağ ayarlarını yap, ping at

Minicom açıkken kartı S2'ye basılı tutarak başlat, `Hit any key to stop autoboot` yazısı çıkınca bir tuşa bas:

![U-Boot'ta ipaddr, serverip, ethact ayarlama ve ping](../images/tftp_boot/08_uboot_net.png)

```
U-Boot# setenv ipaddr 192.168.27.2
U-Boot# setenv serverip 192.168.27.1
U-Boot# setenv ethact cpsw
U-Boot# printenv ipaddr serverip ethact
U-Boot# ping 192.168.27.1
```

| Komut | Açıklama |
|---|---|
| `setenv ipaddr ...` | Kartın (istemci) IP adresi |
| `setenv serverip ...` | TFTP sunucusunun (host) IP adresi. `tftpboot` dosyayı bu adresten ister. |
| `setenv ethact cpsw` | Kullanılacak ağ aygıtı. Kursun hazır U-Boot'unda (2013.04) iki aygıt var (`Net: cpsw, usb_ether`); `cpsw` Ethernet portudur. Çoğu zaman zaten varsayılandır, ama `Using usb_ether device` görürsen bu satır gerekir. Kendi derlediğin U-Boot 2022.04'te aygıtın adı `ethernet@4a100000`'dir ([9.3](09_uboot_build.md#93-adım-adım-toolchain-kurulumu-ve-u-boot-derleme)). |
| `ping ...` | Kablo ve IP ayarlarını test eder. `is alive` görmelisin. |

> [!NOTE]
> U-Boot sadece <b>ping atabilir</b>, gelen ping'e cevap vermez. Host'tan karta `ping 192.168.27.2` atarsan cevap gelmez, bu normaldir. Testi her zaman kart tarafından yap.

### Adım 4 — Dosyaları TFTP ile RAM'e çek

![tftpboot ile uImage, dtb ve initramfs'i RAM'e çekme](../images/tftp_boot/09_tftpboot.png)

```
U-Boot# tftpboot 0x82000000 uImage
U-Boot# tftpboot 0x88000000 am335x-boneblack.dtb
U-Boot# tftpboot 0x88080000 initramfs
```

Adresler seri boot bölümündekiyle aynı ([7.5](07_uart_boot.md#75-önerilen-ram-yükleme-adresleri)): kernel `0x82000000`, DTB `0x88000000`, initramfs `0x88080000`. `Bytes transferred` değeri host'taki `ls -l` boyutuyla aynı olmalı. (`tftp` ve `tftpboot` U-Boot'ta aynı komuttur.)

### Adım 5 — `bootargs` ayarla ve boot et

![bootargs ayarlama ve bootm ile boot](../images/tftp_boot/10_bootm.png)

```
U-Boot# setenv bootargs console=ttyO0,115200 root=/dev/ram0 rw initrd=0x88080000
U-Boot# bootm 0x82000000 0x88080000 0x88000000
```

`bootm` argüman sırası: <b>kernel – initramfs – DTB</b>. Komuta sadece adresler yazılır. `bootargs`'ın ayrıntıları: [7.8 Adım 7](07_uart_boot.md#adım-7--bootargs-ayarla-ve-bootm-ile-boot-et).

### Komutların kısa özeti

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

## 8.6 Yol 2 — uEnv.txt ile Otomatik TFTP Boot

Yol 1'deki U-Boot komutlarının hepsi `uEnv.txt`'ye yazılır. Kart açılınca U-Boot bu dosyayı SD kartın BOOT bölümünden okur ve `uenvcmd` içindeki komutları kendisi çalıştırır. Böylece <b>minicom'a hiçbir şey yazmana gerek kalmaz</b>; minicom'u sadece açılışı izlemek için kullanırsın.

Host tarafındaki hazırlık (IP verme, dosyaları `/var/lib/tftpboot`'a kopyalama) iki yolda da aynı. Yol 2 sadece U-Boot'ta elle yazdığın kısmı (Yol 1, Adım 3–5) otomatik yapar.

### Adım 1 — Host'u hazırla

Yol 1'in Adım 1'i ile aynı: Ethernet arayüzüne `192.168.27.1` ver, `uImage`, `am335x-boneblack.dtb`, `initramfs` dosyalarını `/var/lib/tftpboot`'a kopyala ve `systemctl status tftpd-hpa` ile servisin çalıştığını kontrol et.

### Adım 2 — `uEnv.txt` dosyasını yaz

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
> Komutu `bootcmd` içine değil <b>`uenvcmd`</b> içine yaz. BBB'nin U-Boot'u `uEnv.txt`'yi kendi `bootcmd`'si çalışırken okur ve ardından `uenvcmd`'yi çalıştırır. Bu yüzden dosyadaki `bootcmd` o açılışı etkilemez ([6.3](06_uboot_uenv.md#63-uygulama-uenvtxtyi-seri-porttan-göndermek)).

### Adım 3 — `uEnv.txt`'yi SD kartın BOOT bölümüne koy

İki seçenek var.

<b>a) Kart okuyucuyla (en basiti):</b> SD kartı bilgisayara tak ve dosyayı 1. bölüme kopyala.

```bash
cp uEnv.txt /media/$USER/BOOT/
sync && sudo umount /media/$USER/BOOT
```

<b>b) SD kartı çıkarmadan, TFTP ile:</b> Kart Linux'a açıkken (örneğin Yol 1 ile açtıktan sonra) dosyayı host'tan doğrudan SD karta çekebilirsin. Bunun için BusyBox'taki `tftp -g -r uEnv.txt 192.168.27.1` komutu kullanılır ([8.7](#87-linux-açıldıktan-sonra-tftp-ile-dosya-çekme)).

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

### Adım 4 — Kartı başlat ve hiçbir tuşa basma

S2'ye basılı tutarak güç ver (veya `reboot` sırasında basılı tut). Bu sefer `Hit any key to stop autoboot` çıkınca <b>dokunma</b>; U-Boot `uEnv.txt`'yi okur ve `uenvcmd`'yi çalıştırır:

![uEnv.txt ile otomatik TFTP boot](../images/tftp_boot/11_uenv_auto.png)

Ekranda `Running uenvcmd ...`, ardından `*** Booting From Network ***` ve üç tane `Bytes transferred` görmelisin.

### Adım 5 — Doğrula

Linux açılınca `bootargs`'ın gerçekten kernel'e gittiğini kontrol et:

![/proc/cmdline ile bootargs doğrulama](../images/tftp_boot/16_cmdline.png)

```
cat /proc/cmdline
```

Burada `console=ttyO0,115200n8 root=/dev/ram0 ...` görmüyorsan `linuxbootargs` çalışmamış demektir (değişken adını kontrol et).

### Yol 2'nin özeti

Artık geliştirme döngüsü şu kadar:

```bash
# Host: kernel'i / DTB'yi yeniden derledin
sudo cp uImage am335x-boneblack.dtb /var/lib/tftpboot/
# Kartın reset butonuna bas → U-Boot yeni dosyaları kendisi çeker ve boot eder
```

> [!TIP]
> <b>Yol 2'yi kullanınca Yol 1'deki komutlara gerek kalmaz mı?</b> Her açılışta yazmana gerek kalmaz, ama komutları bilmek yine de gerekli. Bir şey bozulduğunda U-Boot'u durdurup `run loadfromtftp`, `printenv bootargs` gibi komutları tek tek çalıştırarak hangi adımın bozulduğunu bulursun. `uEnv.txt` sadece aynı komutları senin yerine yazar.

---

## 8.7 Linux Açıldıktan Sonra TFTP ile Dosya Çekme

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

## 8.8 Challenge: Her Kaynaktan Boot Edebilen Genel uEnv.txt

### Görev

Tek bir `uEnv.txt` yazacağız. Bu dosya kaynakları sırayla deneyecek ve ilk çalışan kaynaktan boot edecek: <b>eMMC → SD → TFTP → NFS</b>. eMMC'de boot dosyaları yoksa SD karta, SD kart yoksa TFTP'ye geçecek.

### Çözüm fikri

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

### Çözüm: `uEnv.txt`

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

### Satırların açıklaması

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
| `uenvcmd` | Makroları sırayla çağırır. `generic_tried` bir <b>koruma bayrağı</b>: BBB'nin varsayılan `bootcmd`'si önce SD'de, sonra eMMC'de `mmcboot` çalıştırır, yani `uenvcmd` iki kez çalışabilir. Bayrak sayesinde zincir sadece bir kez denenir. |

> [!WARNING]
> <b>eMMC'nin kernel'deki adı değişebilir.</b> U-Boot'ta eMMC her zaman `mmc 1`'dir. Ama eski kernel'lerde (3.8.13 gibi) SD kart <b>takılı değilse</b> eMMC `mmcblk0` olarak görünür, takılıysa `mmcblk1` olarak görünür. `emmc_root` makrosu SD kartın olup olmadığına bakıp doğru adı seçer. Yeni kernel'lerde DTB'deki `aliases` ile bu sabitlenebilir.

### Dosya nereye konur?

Burada da bir tavuk-yumurta durumu var: `uEnv.txt`'nin kendisi yerel bir depolamada olmalı. U-Boot onu önce SD'de (`mmcdev 0`), bulamazsa eMMC'de (`mmcdev 1`) arar.

| Senaryo | `uEnv.txt` nerede olmalı? |
|---|---|
| SD kart her zaman takılı | SD kartın 1. bölümü (BOOT) yeterli |
| "SD kart yoksa TFTP'ye geç" durumu da çalışsın | <b>eMMC'nin 1. bölümüne de</b> aynı dosyayı koy |

En güvenlisi aynı `uEnv.txt`'yi hem SD'nin hem eMMC'nin BOOT bölümüne koymak.

### Örnek açılış: eMMC'de imaj yok, SD kart takılı değil

![Genel uEnv.txt: eMMC ve SD başarısız, TFTP'den açılış](../images/tftp_boot/17_generic_fallback.png)

### Nasıl test edilir?

Her satırda tek bir şeyi değiştirip kartı yeniden başlat. Hangi `[n/4]` satırından sonra `Starting kernel ...` geldiğine bak.

| Test | Ne yaparsın? | Beklenen |
|---|---|---|
| 1 | Her şey yerinde | `[1/4] eMMC` → boot |
| 2 | eMMC'deki `uImage`'ın adını değiştir (`mv uImage uImage.bak`) | eMMC başarısız → `[2/4] SD` → boot |
| 3 | SD kartı çıkar (`uEnv.txt` eMMC'de olmalı) | eMMC, SD başarısız → `[3/4] TFTP` → boot |
| 4 | Host'ta `/var/lib/tftpboot/initramfs`'i taşı | ... → `[4/4] NFS` → boot (NFS sunucusu kurulu olmalı) |
| 5 | Ethernet kablosunu da çıkar | `!!! Hicbir kaynaktan boot edilemedi`, U-Boot komut satırı |

Bir adımı elle denemek istersen U-Boot'u durdurup `uEnv.txt`'yi yükle (`run loadbootenv; run importbootenv`), sonra makroları tek tek çalıştır: `run try_sd`, `printenv bootargs` gibi.

### Sınırlamalar

- Bu zincir sadece <b>U-Boot aşamasındaki</b> hataları yakalar (dosya yok, kart yok, sunucu yok). Kernel açılıp sonra panic verirse (yanlış rootfs vb.) U-Boot'a geri dönülmez.
- `MLO` ve `u-boot.img` yine eMMC'de ya da SD'de olmalı. ROM Code BBB'de ağdan boot edemez ([8.2](#82-neden-bütün-dosyalar-tftp-ile-gönderilmiyor)).
- `uEnv.txt` içindeki U-Boot `echo` mesajlarında Türkçe karakter kullanma; seri konsolda bozuk görünebilir.

---

## 8.9 Özet

- Host: `tftpd-hpa` kur, `/var/lib/tftpboot`'u hazırla, Ethernet arayüzüne `192.168.27.1` ver, dosyaları kopyala.
- SD kart: sadece `MLO`, `u-boot.img`, `uEnv.txt`. Kernel, DTB ve initramfs ağdan gelir.
- U-Boot: `setenv ipaddr` / `serverip` → `ping` → `tftpboot` (3 dosya) → `setenv bootargs` → `bootm kernel initrd dtb`.
- Bu komutları `uEnv.txt`'deki `uenvcmd`'ye yazarsan açılış otomatik olur; geliştirme döngüsü "dosyayı kopyala, reset'e bas"a iner.
- U-Boot'taki IP ayarı kernel'e geçmez; Linux'ta `eth0`'a IP'yi yeniden ver.

## 8.10 Karşılaşılabilecek Problemler

![Sık görülen TFTP hataları (temsili)](../images/tftp_boot/13_hatalar.png)

| Hata | Sebep | Çözüm |
|---|---|---|
| `*** ERROR: 'serverip' not set` | Sunucu IP'si tanımlı değil | `setenv serverip 192.168.27.1` |
| `Using usb_ether device` | U-Boot USB ağını kullanmaya çalışıyor | `setenv ethact cpsw` (U-Boot 2022.04'te: `setenv ethact ethernet@4a100000`) |
| `Loading: T T T T ...` / `Retry count exceeded` | Paket gidiyor ama cevap gelmiyor | Host IP'si ve alt ağ doğru mu? `systemctl status tftpd-hpa` çalışıyor mu? Firewall (`sudo ufw allow 69/udp`)? VM ise Bridged mi? Sunucu port 69'da mı? |
| `TFTP error: 'File not found' (1)` | Dosya `/var/lib/tftpboot` içinde değil ya da adı yanlış | `ls -l /var/lib/tftpboot`. Linux'ta büyük-küçük harf farklıdır: `uImage` ≠ `uimage` |
| `TFTP error: 'Permission denied'` | Dosya okunamıyor | `sudo chmod -R 777 /var/lib/tftpboot` |
| `ping failed; host ... is not alive` | Host'un o arayüzde IP'si yok / kablo takılı değil | `ip -br a` ile kontrol et, Ethernet ışıklarına bak |
| Kart U-Boot'a gelmeden eMMC'den açılıyor | S2'ye basılmadı | Güç verirken S2'yi basılı tut |
| Kart SD'den hiç açılmıyor | SPL dosyasının adı yanlış / BOOT bölümü FAT değil | Dosya adı `MLO` olmalı; 1. bölüm FAT ve boot bayrağı açık olmalı |
| `bootm` sonrası `Wrong Ramdisk Image Format` | initramfs'te U-Boot başlığı yok | `mkimage -A arm -T ramdisk -C gzip -d initramfs.cpio.gz initramfs` ([7.9 (g)](07_uart_boot.md#g-bootm-hataları)) |
| `## Error: "loadfromtftp" not defined` | `uenvcmd` içinde çağrılan makro adı, tanımlanan adla aynı değil | `uEnv.txt`'de iki adı birebir aynı yaz |
| `Running uenvcmd ...` hiç çıkmıyor | `uEnv.txt` okunmadı: BOOT bölümünde değil, adı yanlış (`uenv.txt`) veya kart eMMC'den açıldı | Dosyayı 1. bölüme koy, S2'ye basılı tutarak aç |
| `Starting kernel ...` sonrası ekran boş | `bootargs` ayarlanmamış (ör. `booargs` yazım hatası) ya da `console` yanlış | U-Boot'ta `printenv bootargs` ile kontrol et |

---

[← Bölüm 7: Seri Porttan (UART) Boot](07_uart_boot.md) · [İçindekiler](README.md) · [Bölüm 9: Cross Toolchain, SPL ve U-Boot Derleme →](09_uboot_build.md)
