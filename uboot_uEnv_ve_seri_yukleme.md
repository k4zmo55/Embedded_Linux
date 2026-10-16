# U-Boot `uEnv.txt`: Seri Porttan Yükleme ve Rootfs'i eMMC'ye Taşıma (BeagleBone Black)

Bu dokümanda üç şey yapacağız:

1. `uEnv.txt` dosyasının <b>satır satır ne yaptığını</b> anlayacağız.
2. Bu dosyayı SD karta kopyalamadan, <b>seri port (UART) üzerinden</b> doğrudan U-Boot'a göndereceğiz.
3. Challenge: Kernel ve DTB'yi <b>SD karttan</b> yükleyip rootfs'i <b>eMMC'den</b> bağlayacağız.

> [!NOTE]
> Bu dokümandaki terminal görüntüleri, adımları göstermek için hazırlanmış <b>temsili</b> çıktılardır. Senin kartında U-Boot sürümü, dosya boyutları ve bölüm boyutları farklı görünebilir.
>
> SD karttan boot'un temelleri için: [booting.md](booting.md) · eMMC'ye kurulum için: [eMMC-booting.md](eMMC-booting.md)

---

## 1. Temel Kavramlar

| Kavram | Ne işe yarar? |
|---|---|
| <b>`uEnv.txt`</b> | U-Boot ortam değişkenlerini <b>metin olarak</b> tanımlayan dosya. Her satır `isim=değer` biçimindedir. U-Boot'un bu dosyayı açılışta otomatik okuyup okumaması, U-Boot'un yapılandırmasına bağlıdır (BBB'nin varsayılan U-Boot'u SD karttaki `uEnv.txt`'yi arar). |
| <b>Ortam değişkeni (environment)</b> | U-Boot'un ayarları ve makroları. `printenv` ile görülür, `setenv` ile değiştirilir, `saveenv` ile kalıcı kaydedilir. |
| <b>Minicom</b> | Bilgisayardan seri port (UART) üzerinden karta bağlanmayı sağlayan terminal programı. Kartın konsolu buraya düşer. |
| <b>`loady`</b> | U-Boot'ta <b>YMODEM</b> protokolüyle seri porttan dosya alıp RAM'e yazan komut. |
| <b>`env import -t <adres> <boyut>`</b> | RAM'deki `isim=değer` metnini okuyup U-Boot'un <b>aktif</b> ortamına ekler. `-t` "düz metin" demektir, `<boyut>` metnin bayt cinsinden uzunluğudur. |

Bütün akış şöyle:

```
Bilgisayar (uEnv.txt) ──YMODEM / UART──► RAM 0x82000000 ──env import──► U-Boot ortamı ──boot──► Linux
```

---

## 2. `uEnv.txt` Satır Satır

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
> Bu örnekte kart `192.168.27.x`, sunucu `192.168.1.x` ağında. Ağ geçidi (`gatewayip`) tanımlanmadığı sürece TFTP/NFS çalışmaz. Ağdan boot yapacaksan iki adresi <b>aynı alt ağda</b> seç. SD karttan boot için bu iki satır kullanılmaz.

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
> `mmc 0` ↔ `/dev/mmcblk0` eşleşmesi çoğu kurulumda doğrudur ama <b>garanti değildir</b>. U-Boot tarafında `mmc list`, Linux tarafında `lsblk` ile kontrol et (bkz. [Bölüm 4](#4-challenge-kernel-ve-dtb-sd-karttan-rootfs-emmcden)).

---

## 3. Uygulama: `uEnv.txt`'yi Seri Porttan Göndermek

Normalde `uEnv.txt` SD kartın BOOT bölümüne kopyalanır. Her değişiklikte SD kartı çıkar-tak yapmak yerine dosyayı <b>seri porttan</b> gönderip anında deneyebiliriz.

### Adım 1 — Bilgisayarda dosyayı hazırla ve Minicom'u aç

Dosyanın içeriğini ve <b>boyutunu</b> kontrol et, sonra Minicom ile karta bağlan:

![uEnv.txt hazırlama ve Minicom'u açma](images/uenv/01_uenv_hazirla.png)

> [!TIP]
> Windows'ta port adı `/dev/ttyUSB0` yerine `COM3` gibi olur. Minicom kurulumu için: [minicom.md](minicom.md)

### Adım 2 — U-Boot'u durdur

Kartı aç. `Hit any key to stop autoboot` yazısı çıkınca <b>bir tuşa bas</b>. `U-Boot#` komut satırı gelmeli:

![U-Boot autoboot'u durdurma](images/uenv/02_uboot_durdur.png)

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

![loady ile YMODEM transferi](images/uenv/03_loady.png)

> [!NOTE]
> `## Total Size = 0x0000010D = 269 Bytes` satırı önemli: Bu değer otomatik olarak <b>`filesize`</b> değişkenine yazılır. Bir sonraki adımda boyutu elle yazmak yerine `${filesize}` kullanabiliriz.

### Adım 4 — `env import` ile ortama aktar ve kontrol et

```text
U-Boot# env import -t 0x82000000 ${filesize}
U-Boot# printenv bootargs
U-Boot# printenv bootcmd
```

![env import ve printenv](images/uenv/04_env_import.png)

`printenv` çıktısı `uEnv.txt`'deki değerlerle aynıysa aktarım başarılıdır. `run mypcip` ile makronun da çalıştığını görebilirsin.

> [!WARNING]
> `${filesize}` yerine boyutu elle yazarsan <b>hex</b> olarak yaz (`0x10d` veya `10d`). U-Boot sayıları varsayılan olarak hex kabul eder; `269` yazarsan `0x269` = 617 bayt okur ve dosyanın sonundaki çöp veriyi de içe aktarmaya çalışır.

### Adım 5 — Boot et

```text
U-Boot# boot
```

`boot` komutu `bootcmd`'yi çalıştırır. Ekrana bizim `echo` mesajımız gelmeli:

![bootcmd ile açılış](images/uenv/05_boot.png)

### Dikkat edilecekler

| Konu | Açıklama |
|---|---|
| <b>Adres çakışması</b> | `uEnv.txt` `0x82000000`'a yüklendi; `bootcmd` de kernel'i aynı adrese yüklüyor. Sorun değil, çünkü `env import` dosyayı önce okuyup bitiriyor, kernel <b>sonra</b> üzerine yazılıyor. Sıra ters olursa kernel bozulur. |
| <b>Geçicilik</b> | `env import` sadece RAM'deki aktif ortamı değiştirir. Kart yeniden açılınca değişiklikler kaybolur. |
| <b>Kalıcı yapmak</b> | Her şeyin doğru olduğundan emin olduktan sonra `saveenv` ile kaydedilebilir. Bu komut kalıcı U-Boot ortamının üzerine yazar; geri dönmek için `env default -a` + `saveenv` gerekir. |
| <b>Otomatik okumada `bootcmd`</b> | BBB'nin varsayılan U-Boot'u SD karttaki `uEnv.txt`'yi kendi `bootcmd`'si <b>çalışırken</b> okur ve `uenvcmd` değişkenini arar. Bu yüzden SD karttaki `uEnv.txt`'de `bootcmd` tanımlamak o açılışı etkilemez; orada `uenvcmd` kullanılır ([booting.md](booting.md)'deki örnek gibi). Seri porttan yüklemede ise `boot` komutunu biz verdiğimiz için `bootcmd` çalışır. |

---

## 4. Challenge: Kernel ve DTB SD Karttan, Rootfs eMMC'den

### Görev

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

![mmc list ve mmc part](images/uenv/06_mmc_list.png)

eMMC'de `83` (Linux) tipinde 2. bölüm görünüyorsa rootfs için doğru yerdeyiz.

### Adım 2 — Sadece `bootargs`'ı değiştir

Kernel ve DTB hâlâ SD karttan yükleneceği için <b>`bootcmd` aynı kalır</b>. Değişen tek şey, kernel'e "rootfs nerede?" bilgisini veren `bootargs`:

| | Değer |
|---|---|
| <b>Eski</b> — rootfs SD kartta | `bootargs=console=ttyO0,115200 root=/dev/mmcblk0p2 rw` |
| <b>Yeni</b> — rootfs eMMC'de | `bootargs=console=ttyO0,115200 root=/dev/mmcblk1p2 rw` |

Bunu iki yolla yapabilirsin:

- <b>a)</b> `uEnv.txt`'deki satırı değiştirip [Bölüm 3](#3-uygulama-uenvtxtyi-seri-porttan-göndermek)'teki gibi tekrar gönder.
- <b>b)</b> Doğrudan U-Boot'ta `setenv` ile değiştir:

```text
U-Boot# setenv bootargs console=ttyO0,115200 root=/dev/mmcblk1p2 rw
U-Boot# boot
```

![bootargs'ı eMMC'ye çevirme](images/uenv/07_bootargs_emmc.png)

### Adım 3 — Linux'ta sonucu doğrula

Kart açılınca rootfs'in gerçekten eMMC'den bağlandığını kontrol et:

```bash
cat /proc/cmdline   # kernel'e giden bootargs
lsblk               # hangi bölüm / olarak bağlı?
findmnt /           # rootfs'in kaynağı
```

![Linux'ta rootfs doğrulama](images/uenv/08_linux_dogrula.png)

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

## 5. Hızlı Tekrar

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
