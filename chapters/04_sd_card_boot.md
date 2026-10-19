# Bölüm 4 — SD Karttan Boot

> <b>Bu bölümde:</b>
> - Bir microSD kartı GParted ile BOOT (FAT) ve ROOTFS (ext3) bölümlerine ayıracaksın.
> - Kursun hazır dosyalarını karta <b>tek tek</b> koyup her seferinde kartı açarak boot zincirinin her halkasının çalıştığını göreceksin.
> - `uEnv.txt`'nin bu açılışta ne yaptığını ve `uImage` dosyasının yapısını öğreneceksin.
> - U-Boot'u durdurup kernel'in başlığını (header) bellekten byte byte okuyacaksın.
>
> <b>Ön koşul:</b> [Bölüm 2](02_serial_console.md) — seri konsol, [Bölüm 3](03_boot_process.md) — boot zinciri.

---

## 4.1 Büyük Resim

Kart açılırken programlar sırayla birbirini çalıştırır. Buna <b>boot zinciri</b> denir ([Bölüm 3](03_boot_process.md)):

```
Güç → RBL → MLO → U-Boot → Linux Kernel → Root Filesystem → login ekranı
```

| Aşama | Ne yapar? | Nerede durur? |
|---|---|---|
| <b>RBL</b> (ROM Boot Loader) | Kart açılınca ilk çalışan kod. MLO'yu bulup çalıştırır. | İşlemcinin içinde, değiştirilemez |
| <b>MLO</b> | RAM'i (DDR) hazırlar, U-Boot'u yükler. | SD kart → BOOT bölümü |
| <b>U-Boot</b> | Kernel'i ve device tree'yi RAM'e yükleyip Linux'u başlatır. | SD kart → BOOT bölümü |
| <b>Linux Kernel</b> | İşletim sisteminin çekirdeği. | SD kart → ROOTFS bölümü (`/boot`) |
| <b>Root Filesystem</b> | Linux'un tüm dosyaları (`/bin`, `/etc`, ...). | SD kart → ROOTFS bölümü |

![SD karttan boot zinciri](../images/{5796B774-2D25-45F8-9CD2-47E21A76B361}.png)

*Görsel: kursun slaytı.*

<b>SD kartın son hali</b> şöyle olacak:

```
SD Kart
├── BOOT   (FAT16, ~1 GB)  →  MLO, u-boot.img, uEnv.txt
└── ROOTFS (ext3, kalan)   →  Linux dosyaları (kernel ve .dtb dahil)
```

### Yol haritası

Dosyalar karta <b>tek tek</b> eklenir ve her seferinde kart açılıp test edilir. Böylece zincirin her halkasının çalıştığı görülür:

| Adım | Ne yapılıyor? | Sonuç |
|---|---|---|
| [4.2](#42-hazırlık) – [4.4](#44-sd-kartı-bölümlere-ayırma-gparted) | Dosyaları indir, SD kartı bölümle | SD kart hazır |
| [4.6](#46-aşama-1-mlo) | MLO'yu kopyala, test et | RBL ✓ → MLO ✓ → U-Boot ✗ |
| [4.7](#47-aşama-2-u-boot) | U-Boot'u kopyala, test et | ... → U-Boot ✓ |
| [4.8](#48-aşama-3-root-filesystem-ve-uenvtxt) | Rootfs ve uEnv.txt'yi kopyala, test et | Linux açılır ✓ |
| [4.10](#410-uygulama-uimage-headerını-u-bootta-elle-okuma) | U-Boot'u durdur, uImage header'ını elle oku | Header çözüldü ✓ |

Her testte kart aynı şekilde açılır. Bu işlem [4.5](#45-boot-prosedürü-her-testte-tekrarlanır)'te bir kez anlatılıyor.

---

## 4.2 Hazırlık

<b>Gerekenler:</b>
- microSD kart (en az 4 GB) ve kart okuyucu
- USB-TTL seri dönüştürücü (3.3V). Kartın açılış mesajlarını görmek için gerekli.
- Mini USB kablo (karta güç vermek için)

<b>Dosyaları indir.</b> Kursun GitHub reposundaki <b>4 dosyanın hepsini</b> indir:
{{course.prebuilt_url}}

![Kursun hazır Ångström dosyaları](../images/{937BAE12-C277-4498-83B6-3422541AD131}.png)

*Görsel: kursun GitHub reposu ([niekiran/EmbeddedLinuxBBB]({{course.repo}})).*

| İndirilen dosya | Ne? | Nereye kopyalanacak? |
|---|---|---|
| `{{prebuilt.mlo_file}}` | MLO | BOOT → adı `MLO` olacak |
| `{{prebuilt.uboot_file}}` | U-Boot | BOOT → adı `u-boot.img` olacak |
| `uEnv.txt` | U-Boot ayar dosyası | BOOT → adı aynı kalacak |
| `{{prebuilt.rootfs_file}}` | Root filesystem (içinde kernel `/boot/uImage` ve device tree `/boot/am335x-boneblack.dtb` da var) | ROOTFS → arşivden çıkarılacak |

---

## 4.3 SD Kartı Bilgisayarda Bulma

Kartı takıp terminalde çalıştır:

```bash
sudo dmesg
```

![dmesg çıktısında SD kart](../images/{E9587DCB-9493-4652-93CF-47B08EA122B9}.png)

*Görsel: kursun videosundan ekran görüntüsü.*

- `sdb` → SD kartın adı (`/dev/sdb`). Yanında boyutu yazar (7.81 GB). Doğru cihaz olduğunu boyuttan anlarsın.
- `sdb1` → kartta zaten var olan bölüm (partition).

> [!TIP]
> `lsblk` komutu tüm diskleri boyutlarıyla birlikte daha okunaklı gösterir.

> [!NOTE]
> GParted'da aynı kart <b>7.28 GiB</b> görünür. Kart eksik değil, birimler farklı: 1 GB = 1.000.000.000 byte, 1 GiB = 1.073.741.824 byte.

---

## 4.4 SD Kartı Bölümlere Ayırma (GParted)

Kart 2 bölüme ayrılacak. <b>Karttaki tüm veriler silinir.</b>

![Planlanan bölümler](../images/{791DE154-AB54-40F6-897E-9011C17F5EFB}.png)

*Görsel: kursun slaytı.*

| Bölüm | Label | Dosya sistemi | Boyut | Neden? |
|---|---|---|---|---|
| 1 | `BOOT` | `fat16` | ~1 GB | RBL, MLO'yu sadece FAT bölümde arar |
| 2 | `ROOTFS` | `ext3` | Kalan alan | Linux dosyaları Linux dosya sistemi ister |

GParted'ı kur ve aç:

```bash
sudo apt install gparted
sudo gparted
```

> [!CAUTION]
> Sağ üstteki listeden <b>SD kartı seç</b> (`/dev/sdb`, 7.28 GiB). Yanlışlıkla bilgisayarının diskini (`/dev/sda`) seçersen <b>bilgisayarındaki veriler silinir</b>.

![GParted'da SD kartı seçme](../images/{1A89BAAC-496D-403C-B4E4-B5037CBDDC49}.png)

*Görsel: kursun videosundan ekran görüntüsü.*

### 4.4.1 Unmount et

Bölüm şu an sistem tarafından kullanılıyor (yanındaki 🔑 simgesi). Kullanımdayken silinemez. <b>Sağ tık → Unmount.</b>

![Unmount](../images/{F664732C-758E-43D3-8642-8651DD082B29}.png)

*Görsel: kursun videosundan ekran görüntüsü.*

### 4.4.2 Eski bölümü sil

<b>Sağ tık → Delete.</b> Kartın tamamı `unallocated` (boş alan) olur.

![Delete](../images/{78D43D2E-1A50-4CA0-B366-FCDDB6818431}.png)

![Kartın tamamı unallocated](../images/{0125CA5B-146A-4D42-9B02-440035AE3BE3}.png)

*Görseller: kursun videosundan ekran görüntüleri.*

> [!NOTE]
> GParted işlemleri hemen uygulamaz, sıraya koyar ("1 operation pending"). Hepsi en sonda [4.4.5](#445-değişiklikleri-uygula)'te uygulanır. O ana kadar her şey geri alınabilir.

### 4.4.3 BOOT bölümünü oluştur

`unallocated` alana <b>sağ tık → New.</b>

![New](../images/{4CE141F8-591A-4682-A76A-BEDCC2CDCA35}.png)

*Görsel: kursun videosundan ekran görüntüsü.*

Açılan pencerede 3 ayar yap, sonra <b>Add</b>'e bas:

| Alan | Değer |
|---|---|
| File system | `fat16` |
| Label | `BOOT` |
| New size (MiB) | `1013` (yaklaşık 1 GB) |

![Dosya sistemi seçimi](../images/{09B1300E-BAF9-4E27-A1EB-516C1D1F8C5A}.png)

![fat16 seçildi](../images/{5B17659C-D05D-4364-8726-118408CC54FA}.png)

![Label: BOOT](../images/{F03EC26C-791B-4AB1-89BE-72A6FAFA0E17}.png)

*Görseller: kursun videosundan ekran görüntüleri.*

> [!NOTE]
> fat16 seçilince boyut kendiliğinden <b>4095 MiB</b> olur, çünkü FAT16 en fazla ~4 GiB olabilir. Bunu 1013'e düşürüyoruz. Boot dosyaları zaten birkaç MB.

![Boyut 1013 MiB](../images/{5F06ECDC-BB20-47C8-B8D1-BA39D8C519AD}.png)

![BOOT bölümü planlandı](../images/{A7350810-4850-4C65-904E-84485A598EA3}-1.png)

*Görseller: kursun videosundan ekran görüntüleri.*

### 4.4.4 ROOTFS bölümünü oluştur

Kalan `unallocated` alana yine <b>sağ tık → New</b>, sonra <b>Add</b>:

| Alan | Değer |
|---|---|
| File system | `ext3` |
| Label | `ROOTFS` |
| New size (MiB) | Değiştirme (kalan alanın tamamı) |

![ROOTFS ayarları](../images/{F8D61470-50C8-4030-BCAE-39B8B0A4E54C}.png)

![ROOTFS planlandı](../images/{143DC429-6748-42C3-9A4A-691238D4A073}.png)

*Görseller: kursun videosundan ekran görüntüleri.*

Planlanan durum: 1 GB BOOT + 6.29 GiB ROOTFS.

![Planlanan durum](../images/{370CABEB-C929-493B-8996-1FB867457DED}.png)

*Görsel: kursun videosundan ekran görüntüsü.*

### 4.4.5 Değişiklikleri uygula

<b>Yeşil tik</b> (Apply All Operations) → onay penceresinde <b>Apply</b>.

> [!WARNING]
> Bu adımdan sonra geri dönüş yok, karttaki eski veriler silinir.

![Apply All Operations](../images/{D2522D38-67E5-45CF-83E8-6B2A8877C758}.png)

![İşlemler tamamlandı](../images/{01D7E3F3-77AF-4578-AF99-AE21A1EFE350}.png)

*Görseller: kursun videosundan ekran görüntüleri.*

### 4.4.6 BOOT bölümüne `boot` bayrağı ekle

Bu bayrak, bölümü "açılış bölümü" olarak işaretler. RBL, MLO'yu bu bölümde arar.

<b>BOOT'a sağ tık → Manage Flags → `boot` kutucuğunu işaretle → Close.</b>

![Manage Flags](../images/{D9F3687E-CF84-43DE-B409-44A80C7170C3}.png)

![boot bayrağı](../images/{5D758CCD-B40D-468F-8D1B-F2D8C97545E6}.png)

*Görseller: kursun videosundan ekran görüntüleri.*

Flags sütununda `boot` yazıyorsa tamam. GParted'ı kapatabilirsin.

![Son durum](../images/{19CCA067-203C-4FA1-BE7A-CB2A0FF54A8B}.png)

*Görsel: kursun videosundan ekran görüntüsü.*

---

## 4.5 Boot Prosedürü (her testte tekrarlanır)

Aşağıdaki aşamaların her birinde dosya kopyaladıktan sonra bu adımları uygula.

### 4.5.1 Kartı bilgisayardan güvenli çıkar

```bash
sync
sudo umount /media/$USER/BOOT
sudo umount /media/$USER/ROOTFS
```

- `sync` → Bekleyen yazma işlemlerini karta yazar. Atlanırsa kopyalanan dosya eksik kalabilir.
- `umount` → Bölümlerin bağlantısını keser. Artık kart çıkarılabilir.

### 4.5.2 Seri konsolu hazırla (sadece ilk seferde)

1. USB-TTL'yi kartın <b>J1</b> header'ına bağla ([1.8](01_bbb_hardware.md#18-seri-debug-header-j1)).
2. Minicom'u aç: <b>115200 baud, 8N1, Hardware Flow Control kapalı</b> ([Bölüm 2](02_serial_console.md)).

### 4.5.3 Kartı SD karttan aç (S2 butonu)

{{board.name}} normalde <b>kendi eMMC belleğinden</b> açılır. SD karttan açılması için <b>kart açılırken S2 (BOOT) butonu basılı olmalı</b>. RBL bu butona sadece açılış anında bakar ([3.5](03_boot_process.md#35-boot-kaynakları-ve-boot-sırası-sysboot-pinleri)).

SD kartı BeagleBone'a tak, sonra iki yöntemden birini uygula:

| Yöntem | Ne zaman? | Adımlar |
|---|---|---|
| <b>A: Güç vererek</b> | Kartta güç yokken | S2'yi basılı tut → USB kablosunu tak → 2–3 sn sonra S2'yi bırak |
| <b>B: Power butonuyla</b> | Kart zaten güç alıyorsa | Power'a LED'ler sönene kadar uzun bas (kapanır) → S2'yi basılı tut → Power'a kısa bas (açılır) → S2'yi bırak |

---

## 4.6 Aşama 1: MLO

### Kopyala

İndirme klasörüne git ve MLO'yu BOOT bölümüne <b>`MLO` adıyla</b> kopyala:

```bash
cd ~/BBB_Workspace/Downloads/
cp {{prebuilt.mlo_file}} /media/$USER/BOOT/MLO
```

![MLO'yu kopyalama](../images/{9BE9E6D2-720E-4ED7-A6F6-9337BBB04BB1}.png)

*Görsel: kursun videosundan ekran görüntüsü.*

> [!IMPORTANT]
> <b>Neden sonda `MLO` yazıyoruz?</b> `cp` komutunda hedefin sonuna bir ad yazılırsa dosya o adla kopyalanır:
> ```
> cp  {{prebuilt.mlo_file}}   /media/$USER/BOOT/MLO
>     └───── kaynak ─────┘     └─ hedef klasör + YENİ AD ─┘
> ```
> RBL, BOOT bölümünde <b>tam olarak `MLO` adlı</b> dosyayı arar. Dosya uzun adıyla kalırsa bulunamaz.

> [!TIP]
> `$USER` senin kullanıcı adındır (kursta `kiran`). Dosya adlarını elle yazmak yerine ilk birkaç harfi yazıp <b>Tab</b>'a bas, terminal tamamlar.

### Test et

[4.5](#45-boot-prosedürü-her-testte-tekrarlanır)'teki adımlarla kartı aç. Minicom'da şunu görmelisin:

![MLO çalıştı, u-boot.img bulunamadı](../images/{E4B8C846-49BA-43F8-A7A8-B2D8B9BDA0E8}.png)

*Görsel: kursun videosundan ekran görüntüsü.*

| Satır | Anlamı |
|---|---|
| `U-Boot SPL {{prebuilt.uboot_version}}-dirty ...` | <b>MLO çalıştı.</b> RBL dosyayı buldu. |
| `musb-hdrc ...`, `USB ... controller` | MLO USB donanımını başlatıyor, önemli değil. |
| `reading u-boot.img` | MLO bir sonraki aşamayı (U-Boot) arıyor. |
| `spl: error reading image u-boot.img` | U-Boot bulunamadı, çünkü henüz kopyalamadık. <b>Beklenen hata.</b> |

Sonuç: <b>RBL ✓ → MLO ✓ → U-Boot ✗</b>

> [!NOTE]
> "dirty" bir hata değildir. MLO derlenirken kaynak kodda kaydedilmemiş (commit edilmemiş) değişiklik olduğunu belirtir.

---

## 4.7 Aşama 2: U-Boot

### Kopyala

Kartı tekrar bilgisayara tak ve U-Boot'u <b>`u-boot.img` adıyla</b> kopyala. MLO, U-Boot'u bu adla arar:

```bash
cp {{prebuilt.uboot_file}} /media/$USER/BOOT/u-boot.img
```

![u-boot.img'yi kopyalama](../images/{33002E3B-4D53-4327-96B8-7109DF21F826}.png)

*Görsel: kursun GitHub reposu ([niekiran/EmbeddedLinuxBBB]({{course.repo}})).*

### Test et

[4.5](#45-boot-prosedürü-her-testte-tekrarlanır)'teki adımlarla kartı aç.

- `U-Boot SPL` satırlarından sonra <b>U-Boot'un kendi mesajları</b> görünüyorsa bu aşama başarılı.
- Kernel ve `uEnv.txt` henüz olmadığı için Linux SD karttan açılmaz.

Sonuç: <b>RBL ✓ → MLO ✓ → U-Boot ✓ → Kernel ✗</b>

---

## 4.8 Aşama 3: Root Filesystem ve uEnv.txt

### Kopyala

Kartı tekrar bilgisayara tak.

<b>1) Root filesystem'i ROOTFS bölümüne çıkar:</b>

```bash
sudo tar -xvf {{prebuilt.rootfs_file}} -C /media/$USER/ROOTFS
```

| Parça | Anlamı |
|---|---|
| `sudo` | Linux dosyalarının sahibi `root`. Dosya izinlerinin korunması için gerekli. |
| `-x` `-v` `-f` | Arşivi aç (e<b>x</b>tract), açılan dosyaları göster (<b>v</b>erbose), arşiv dosyası (<b>f</b>ile) |
| `-C /media/$USER/ROOTFS` | Dosyaları bu klasöre çıkar |

![Rootfs arşivini açma](../images/{DA993575-2D08-4D85-AA87-3047E71E40D6}.png)

*Görsel: kursun GitHub reposu ([niekiran/EmbeddedLinuxBBB]({{course.repo}})).*

<b>2) uEnv.txt'yi BOOT bölümüne kopyala</b> (adı değişmiyor, U-Boot bu adla arar):

```bash
cp uEnv.txt /media/$USER/BOOT/
```

<b>Kontrol et:</b>

```bash
ls /media/$USER/BOOT/            # MLO  u-boot.img  uEnv.txt
ls /media/$USER/ROOTFS/boot/     # uImage ve am335x-boneblack.dtb burada olmalı
```

### Test et

[4.5](#45-boot-prosedürü-her-testte-tekrarlanır)'teki adımlarla kartı aç. Rootfs büyük olduğu için `sync` biraz uzun sürebilir, bitmesini bekle.

Kernel mesajları akar ve sonunda <b>Ångström</b> logosu ile `beaglebone login:` satırı çıkar:

![Ångström login ekranı](../images/{F2BBFA98-4148-45FB-B849-710BC7F58DE9}.png)

*Görsel: kursun videosundan ekran görüntüsü.*

Sonuç: <b>RBL ✓ → MLO ✓ → U-Boot ✓ → Kernel ✓ → Rootfs ✓</b> 🎉

> [!TIP]
> Giriş için kullanıcı adı `root` yaz. Bu demo imajında genelde şifre yoktur.

### Bu açılışta uEnv.txt ne yaptı?

`uEnv.txt`, U-Boot'un davranışını değiştiren ayar dosyasıdır. BBB'nin U-Boot'u açılırken BOOT bölümündeki bu dosyayı okur ve içindeki `uenvcmd` komutunu çalıştırır.

![Kursun uEnv.txt dosyası](../images/{840192A1-87BA-43CA-887C-D739774088B9}.png)

*Görsel: kursun videosundan ekran görüntüsü.*

| Satır | Anlamı |
|---|---|
| `console=ttyO0,115200n8` | Linux mesajları UART0'a (J1 header) 115200 baud ile yazılsın. |
| `ipaddr`, `serverip` | Ağdan boot için IP adresleri. SD karttan boot'ta kullanılmıyor. |
| `loadaddr=0x82000000` | Kernel'in (uImage) <b>RAM'de (DDR) yükleneceği adres</b>. |
| `fdtaddr=0x88000000` | Device tree (.dtb) dosyasının RAM'de yükleneceği adres. |
| `loadfromsd=load mmc 0:2 ...` | `mmc 0:2` = SD kart, 2. bölüm (ROOTFS). Oradaki `/boot/uImage` → `loadaddr`'e, `/boot/am335x-boneblack.dtb` → `fdtaddr`'e yüklenir. |
| `linuxbootargs=... root=/dev/mmcblk0p2 rw` | Kernel'e "root filesystem SD kartın 2. bölümünde, okuma-yazma modunda" bilgisini verir. |
| `uenvcmd=...` | U-Boot'un çalıştırdığı komut: önce `loadfromsd`, sonra `linuxbootargs`, en son `bootm` ile kernel'i başlat. `bootm`'deki `-` "initramfs yok" demek. |

> [!NOTE]
> AM335x'te DDR'in başlangıç adresi `0x80000000`'dır. `0x82000000` ise DDR'in içinde, kernel için seçilmiş bir adres.

Aynı dosya farklı yazılarak U-Boot'a kernel'i <b>ağdan (TFTP)</b>, rootfs'u da <b>bilgisayardaki bir klasörden (NFS)</b> aldırmak mümkün ([Bölüm 8](08_tftp_boot.md)):

![TFTP ve NFS için uEnv.txt örneği](../images/{F9C9F3D8-B461-4FAC-A040-0F0ECEB76A7E}.png)

*Görsel: kursun videosundan ekran görüntüsü.*

`uEnv.txt`'nin her satırını ve U-Boot komut satırını [Bölüm 6](06_uboot_uenv.md)'da ayrıntılı göreceğiz.

---

## 4.9 uImage Nedir?

`uImage`, U-Boot'un `bootm` komutuyla başlatabildiği kernel formatıdır. Yeni bir derleme yapılmaz. `zImage` dosyasının başına <b>64 byte'lık bir U-Boot header'ı</b> eklenir. Bu işi `mkimage` aracı yapar.

```
+-------------------+--------------------------------------+
| U-Boot Header     |               zImage                 |
|   (64 byte)       | (sıkıştırılmış, kendini açan kernel) |
+-------------------+--------------------------------------+
|<------------------------ uImage ------------------------>|
```

<b>Kernel imajları zinciri:</b>

| Dosya | Açıklama |
|---|---|
| `vmlinux` | Derlenmiş kernel. ELF formatında, sıkıştırılmamış. |
| `Image` | `vmlinux`'tan `objcopy` ile çıkarılmış ham binary |
| `zImage` | Sıkıştırılmış `Image` ve başında onu RAM'de açan küçük bir program |
| `uImage` | 64 byte U-Boot header + `zImage` |

<b>Header'ın içeriği</b> (`struct image_header`, tüm alanlar big-endian):

| Offset | Boyut | Alan | Anlamı |
|---|---|---|---|
| 0x00 | 4 | `ih_magic` | Sihirli sayı: `0x27051956` |
| 0x04 | 4 | `ih_hcrc` | Header'ın CRC32 değeri |
| 0x08 | 4 | `ih_time` | Oluşturulma zamanı |
| 0x0C | 4 | `ih_size` | zImage'in boyutu |
| 0x10 | 4 | `ih_load` | RAM'de kopyalanacağı adres |
| 0x14 | 4 | `ih_ep` | Çalıştırmanın başlayacağı adres (entry point) |
| 0x18 | 4 | `ih_dcrc` | zImage'in CRC32 değeri |
| 0x1C | 1 | `ih_os` | İşletim sistemi (Linux) |
| 0x1D | 1 | `ih_arch` | Mimari (ARM) |
| 0x1E | 1 | `ih_type` | İmaj tipi (kernel, ramdisk, script...) |
| 0x1F | 1 | `ih_comp` | Sıkıştırma tipi |
| 0x20 | 32 | `ih_name` | İmaj adı |

U-Boot bu header sayesinde dosyanın geçerli bir imaj olup olmadığını (magic number), bozulup bozulmadığını (CRC) ve RAM'de nereye yüklenip nereden çalıştırılacağını anlar.

---

## 4.10 Uygulama: uImage Header'ını U-Boot'ta Elle Okuma

<b>Amaç:</b> uImage'ın başındaki 64 byte'lık U-Boot header'ını ([4.9](#49-uimage-nedir)) kendi gözümüzle görmek.

<b>Neredeyiz?</b> [4.8](#48-aşama-3-root-filesystem-ve-uenvtxt)'de U-Boot, `uEnv.txt`'deki komutları <b>otomatik</b> çalıştırıp Linux'u açtı. Bu sefer U-Boot'u durdurup aynı işin ilk yarısını <b>elle</b> yapacağız:

```
4.8:   RBL → MLO → U-Boot → Kernel → Rootfs → login     (otomatik)
4.10:  RBL → MLO → U-Boot ■ DUR → komutları elle yaz
```

| Adım | Komut | Ne yapar? |
|---|---|---|
| 1 | Açılışta bir tuşa bas | U-Boot'u durdurur, `U-Boot#` komut satırı gelir |
| 2 | `load mmc 0:2 0x82000000 /boot/uImage` | uImage'ı SD karttan DDR'e kopyalar |
| 3 | `md.b 0x82000000 40` | DDR'deki ilk 64 byte'ı (header) ekrana döker |
| 4 | — | Byte'ları header tablosuyla eşleştirip çözeriz |

> [!NOTE]
> <b>Neden önce DDR'e yüklüyoruz?</b> `md` (memory display) komutu sadece <b>belleği</b> okuyabilir. SD kart bir bellek adresi değil, depolama cihazıdır. Bu yüzden dosyayı önce RAM'e kopyalıyoruz.

Kursun bu dersinde Windows'ta Tera Term kullanılıyor. Minicom ile de komutlar ve çıktılar aynıdır ([2.6](02_serial_console.md#26-windowsta-tera-term)).

### 4.10.1 U-Boot'u durdur

1. Seri terminali aç ve kartı [4.5.3](#453-kartı-sd-karttan-aç-s2-butonu)'teki gibi SD karttan başlat.
2. Ekranda <b>`Hit any key to stop autoboot`</b> yazısı görünür görünmez bir tuşa (ör. <b>Space</b>) bas.
3. <b>`U-Boot#`</b> komut satırı geldiyse hazırsın.

> [!TIP]
> Geri sayım çok kısa (1–3 saniye). Kaçırırsan Linux açılır. Kartı yeniden başlatıp daha erken bas. Kart açılırken Space'e art arda basmak işe yarar.

### 4.10.2 uImage'ı DDR'e yükle

Önce dosyanın orada olduğunu gör:

```text
U-Boot# ls mmc 0:2 /boot
```

Sonra DDR'e yükle:

```text
U-Boot# load mmc 0:2 0x82000000 /boot/uImage
```

| Parça | Anlamı |
|---|---|
| `load` | Bir dosya sisteminden dosyayı belleğe kopyala |
| `mmc 0:2` | MMC cihazı 0 (SD kart), 2. bölüm (ROOTFS) |
| `0x82000000` | DDR'de dosyanın yazılacağı adres (`uEnv.txt`'deki `loadaddr` ile aynı) |
| `/boot/uImage` | Bölüm içindeki dosyanın yolu |

#### `mmc X:Y` ne demek?

```
load  mmc 0:2      0x82000000   /boot/uImage
      └─ NEREDEN ─┘ └─ NEREYE ─┘ └─ HANGİ DOSYA ┘
      SD kart,      DDR'deki      partition içindeki
      2. partition  bu adrese     dosya yolu
```

- <b>`X` = hangi MMC cihazı.</b> {{board.name}}'te:
  - `mmc 0` → <b>microSD kart</b>
  - `mmc 1` → <b>eMMC</b> (karta lehimli dahili bellek)
- <b>`Y` = o cihazın kaçıncı partition'ı.</b> Numaralandırma <b>1'den</b> başlar.

> [!IMPORTANT]
> `load` her zaman <b>DDR'e</b> yükler. `mmc 0:2` dosyanın <b>nereye</b> yazılacağını değil, <b>nereden okunacağını</b> söyler. Yani "2. partition'a yükle" değil, "<b>2. partition'dan oku</b>, DDR'e yükle".

Bizim SD kartımız için:

| Yazım | Anlamı | İçinde ne var? |
|---|---|---|
| `mmc 0:1` | SD kart, 1. partition | BOOT (FAT16): `MLO`, `u-boot.img`, `uEnv.txt` |
| `mmc 0:2` | SD kart, 2. partition | ROOTFS (ext3): `/boot/uImage`, `/boot/am335x-boneblack.dtb`, Linux dosyaları |
| `mmc 1:...` | eMMC'nin partition'ları | Kartla fabrikadan gelen sistem (ör. Ångström/Debian) |

Örnekler:

```text
U-Boot# ls mmc 0:1                                  # BOOT bölümünü listele
U-Boot# ls mmc 0:2 /boot                            # ROOTFS'taki /boot klasörünü listele
U-Boot# load mmc 0:1 0x82000000 uEnv.txt            # BOOT'taki uEnv.txt'yi DDR'e yükle
U-Boot# mmc list                                    # U-Boot'un gördüğü MMC cihazlarını listele
U-Boot# mmc dev 0                                   # SD kartı seç
U-Boot# mmc part                                    # Seçili cihazın partition tablosunu göster
```

> [!NOTE]
> Linux'ta da benzer bir numaralandırma vardır: `/dev/mmcblk0p2` = MMC cihazı 0, partition 2. `uEnv.txt`'deki `root=/dev/mmcblk0p2` ifadesi, U-Boot'taki `mmc 0:2` ile aynı yeri gösterir. Ancak Linux'un numaraları kernel sürümüne göre U-Boot'tan farklı olabilir, bu yüzden ikisinin her zaman aynı olacağını varsayma.

Çıktıda kaç byte okunduğu yazar (`xxxxxxx bytes read`). Bu sayı uImage'ın boyutudur, yani 64 byte header + zImage.

> [!NOTE]
> Bu komut `uEnv.txt`'deki `loadfromsd` satırının yaptığı işin aynısı. Fark sadece bu sefer elle yazmamız.

> [!TIP]
> `load` komutu tanınmazsa eski adı olan `ext2load mmc 0:2 0x82000000 /boot/uImage` komutunu kullan (ext3 de bu komutla okunur). `ls` yerine de `ext2ls mmc 0:2 /boot` kullanılır.

### 4.10.3 Header'ı ekrana dök

```text
U-Boot# md.b 0x82000000 40
```

| Parça | Anlamı |
|---|---|
| `md` | memory display: belleği ekrana dök |
| `.b` | byte byte göster |
| `0x82000000` | Başlangıç adresi (uImage'ı yüklediğimiz yer) |
| `40` | Kaç byte gösterilecek. <b>U-Boot sayıları hex kabul eder:</b> `0x40` = <b>64 byte</b> = header'ın tamamı |

Çıktı 4 satırdır. Her satırda adres, 16 byte ve sağda bu byte'ların ASCII karşılığı bulunur.

> [!WARNING]
> `md` komutu nokta olmadan (`md 0x82000000 10`) yazılırsa veriyi <b>4 byte'lık word'ler</b> halinde gösterir. ARM işlemci <b>little-endian</b>, header ise <b>big-endian</b> olduğu için byte'lar ters görünür. Örneğin magic number `27051956` yerine <b>`56190527`</b> olarak görünür. Header'ı okurken `md.b` kullanmak daha kolaydır.

### 4.10.4 Byte'ları çöz

Çıktının her satırı header'ın şu alanlarına denk gelir:

```
82000000: [27 05 19 56] [.. .. .. ..] [.. .. .. ..] [.. .. .. ..]
            ih_magic      ih_hcrc       ih_time       ih_size
82000010: [.. .. .. ..] [.. .. .. ..] [.. .. .. ..] [..][..][..][..]
            ih_load       ih_ep         ih_dcrc      os arch type comp
82000020: [ ih_name: 32 byte imaj adı, sağdaki ASCII sütununda okunur ...
82000030:   ...                                                        ]
```

| Alan | Nasıl kontrol edilir? |
|---|---|
| `ih_magic` | `27 05 19 56` olmalı. Değilse bu adreste geçerli bir uImage yok. |
| `ih_time` | Unix zaman damgası. Linux'ta tarihe çevir: `date -d @$((0xXXXXXXXX))` |
| `ih_size` | zImage boyutu. Ondalığa çevir: `echo $((0xXXXXXXXX))`. Bu değer + 64 = `load` komutunun okuduğu byte sayısı olmalı. |
| `ih_load`, `ih_ep` | Kernel'in DDR'de çalışacağı adres ve başlangıç noktası |
| `os` | `05` = Linux |
| `arch` | `02` = ARM |
| `type` | `02` = Kernel |
| `comp` | `00` = sıkıştırma yok. zImage zaten kendini açtığı için U-Boot ayrıca açmaz. |
| `ih_name` | Sağdaki ASCII sütununda imajın adı okunur |

> [!TIP]
> Hex'i ondalığa çevirmek için Windows Hesap Makinesi'nin <b>Programcı</b> modunu da kullanabilirsin.

### 4.10.5 Sonucu U-Boot'a doğrulat

Elle çözdüğün değerleri U-Boot'un kendi çözümüyle karşılaştır:

```text
U-Boot# iminfo 0x82000000
```

`iminfo` komutu header'ı okuyup Image Name, Created, Image Type, Data Size, Load Address ve Entry Point bilgilerini yazar. Ayrıca CRC'yi kontrol eder (`Verifying Checksum ... OK`). Değerler senin bulduklarınla aynı olmalı.

### 4.10.6 Linux'u başlat

İşin bitince Linux'u normal şekilde açmak için:

```text
U-Boot# boot
```

Ya da kartı yeniden başlat (`reset` veya Power butonu).

### Komut özeti

| Komut | Ne yapar? |
|---|---|
| `ls mmc 0:2 /boot` | SD kartın 2. bölümündeki `/boot` klasörünü listeler |
| `load mmc 0:2 0x82000000 /boot/uImage` | uImage'ı DDR'de `0x82000000` adresine yükler |
| `md.b 0x82000000 40` | O adresten başlayarak 64 byte'ı byte byte gösterir |
| `iminfo 0x82000000` | O adresteki uImage header'ını çözüp yazar |
| `boot` | Normal açılışa devam eder (Linux'u başlatır) |
| `reset` | Kartı yeniden başlatır |
| `help` | Tüm U-Boot komutlarını listeler (`help md` gibi tek komut için de olur) |

---

## 4.11 Kursun Güncel SD Kart İmajları (U-Boot {{prebuilt.sd_uboot_version}} + Kernel {{prebuilt.sd_kernel_version}})

Bu bölümde kullandığımız Ångström dosyaları kursun ilk sürümünden kalma (2013). Kursun reposundaki `pre-built-images/SD-boot` klasöründe güncel bir set de var:

| Dosya | İçerik | SD kartta nereye? |
|---|---|---|
| `MLO`, `u-boot.img` | U-Boot {{prebuilt.sd_uboot_version}} | BOOT |
| `uImage` | Linux {{prebuilt.sd_kernel_version}} | BOOT |
| `am335x-boneblack.dtb` | Aynı kernel'in device tree'si | BOOT |
| `uEnv.txt` | Aşağıda | BOOT |

Farklar:
- Kernel ve DTB artık ROOTFS'teki `/boot` klasöründe değil, <b>BOOT (FAT) bölümünde</b> duruyor. `load mmc 0:1 ...` ile okunuyor.
- Bu set bir rootfs içermiyor. ROOTFS bölümüne [Bölüm 12](12_busybox_rootfs.md)'de BusyBox ile hazırlayacağımız dosya sistemini koyacağız. Kernel 5.10 ile 2012 tarihli Ångström rootfs'i birlikte çalışmaz.
- Bu U-Boot'ta `bootdelay=0`: geri sayım yok. U-Boot'u durdurmak için kart açılırken <b>Space'e basılı tut</b>. Bekleme süresini uzatmak [9.4](09_uboot_build.md#94-challenge-autoboot-bekleme-süresini-10-saniyeye-çıkarmak)'ün konusu.

Kursun `uEnv.txt`'si:

```text
console=ttyS0,115200n8
netargs=setenv bootargs console=ttyO0,115200n8 root=/dev/mmcblk0p2 rw rootfstype=ext4 rootwait debug earlyprintk mem=512M
netboot=echo Booting from microSD ...; setenv autoload no ; load mmc 0:1 ${loadaddr} uImage ; load mmc 0:1 ${fdtaddr} am335x-boneblack.dtb ; run netargs ; bootm ${loadaddr} - ${fdtaddr}
uenvcmd=run netboot
```

| Parça | Anlamı |
|---|---|
| `rootfstype=ext4` | Rootfs'in dosya sistemi türü. ext4 sürücüsü ext3 bölümleri de bağlayabilir. |
| `rootwait` | Kernel, rootfs'in bulunduğu aygıt (SD kart) hazır olana kadar bekler. MMC aygıtları geç algılandığı için önemli. |
| `debug earlyprintk` | Açılışta daha fazla mesaj basar. Sorun ayıklarken işe yarar. |
| `mem=512M` | Kernel'e kullanacağı RAM miktarını söyler. |
| `${loadaddr}`, `${fdtaddr}` | U-Boot'un kendi varsayılan değişkenleri (`0x82000000`, `0x88000000`). Dosyada tanımlanmadıkları halde çalışır. |

> [!WARNING]
> Dosyanın ilk satırında `console=ttyS0` tanımlanmış ama `netargs` bu değişkeni kullanmıyor, `console=ttyO0` yazıyor. Kernel 5.10'da UART0'ın adı `ttyS0`'dır ([3.4](03_boot_process.md#34-linux-kernel-ve-root-filesystem)). Açılışta `Starting kernel ...`'dan sonra mesaj göremezsen `netargs` içinde `console=${console}` kullan.

## 4.12 Özet

- SD kart iki bölümden oluşur: <b>BOOT</b> (FAT16, `boot` bayraklı: `MLO`, `u-boot.img`, `uEnv.txt`) ve <b>ROOTFS</b> (ext3: kernel, DTB ve Linux dosyaları).
- Dosya adları önemli: RBL tam olarak <b>`MLO`</b>'yu, MLO tam olarak <b>`u-boot.img`</b>'yi arar.
- Kartı SD karttan açmak için güç verirken <b>S2</b>'yi basılı tut.
- U-Boot `uEnv.txt`'deki `uenvcmd`'yi çalıştırır: kernel ve DTB'yi `mmc 0:2`'den RAM'e yükler, `bootargs`'ı ayarlar, `bootm` ile başlatır.
- `uImage` = 64 byte U-Boot header + `zImage`. `md.b` ile byte byte, `iminfo` ile çözülmüş halde okunabilir.

## 4.13 Karşılaşılabilecek Problemler

| Belirti | Sebep | Çözüm |
|---|---|---|
| Minicom'da hiçbir şey yok | TX/RX düz bağlı, baud yanlış ya da Hardware Flow Control açık | Bağlantıyı ve 115200 8N1 ayarını kontrol et ([2.8](02_serial_console.md#28-karşılaşılabilecek-problemler)) |
| Sürekli `CCCCCCCC...` | RBL, MLO'yu bulamadı | Dosya adı tam `MLO` mu, BOOT bölümü FAT mı, `boot` bayrağı açık mı? ([4.4](#44-sd-kartı-bölümlere-ayırma-gparted)) |
| `error reading image u-boot.img` | BOOT'ta `u-boot.img` yok veya adı yanlış | Dosyayı `u-boot.img` adıyla kopyala ([4.7](#47-aşama-2-u-boot)) |
| Eski Linux açılıyor (Debian vb.) | Kart eMMC'den açıldı; S2 açılış anında basılı değildi | Gücü kes, S2 basılıyken tekrar ver ([4.5.3](#453-kartı-sd-karttan-aç-s2-butonu)) |
| U-Boot `/boot/uImage` bulamıyor | Rootfs ROOTFS bölümüne çıkarılmamış veya yanlış klasöre çıkarılmış | `ls /media/$USER/ROOTFS/boot/` ile kontrol et, arşivi `-C` ile doğru yere çıkar |
| `Kernel panic ... Unable to mount root fs` | ROOTFS bölümü boş veya `sync` yapılmadan kart çıkarılmış | Rootfs'i yeniden çıkar, `sync` + `umount` ile güvenli çıkar |
