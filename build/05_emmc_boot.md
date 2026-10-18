<!-- Bu dosya otomatik üretildi. Düzenlemek için chapters/ altındaki kaynağı değiştir. -->
# Bölüm 5 — eMMC'den Boot

> <b>Bu bölümde:</b>
> - eMMC'nin ne olduğunu ve DDR RAM'den farkını öğreneceksin.
> - Güncel bir Debian imajını önce SD karta yazıp sonra <b>flasher script</b> ile eMMC'ye aktaracaksın.
> - Karta USB üzerinden SSH ile bağlanmayı göreceksin.
>
> <b>Ön koşul:</b> [Bölüm 3](03_boot_process.md) — boot sırası ve S2, [Bölüm 4](04_sd_card_boot.md) — SD karttan boot.

---

## 5.1 Hatırlatma: eMMC Nedir?

<b>eMMC (embedded MultiMediaCard)</b>, BeagleBone Black'in üzerine lehimli olarak gelen dahili depolama birimidir. Aslında içinde bir SD kart vardır ve doğrudan karta lehimlenmiştir. Kapasitesi Rev C'de <b>4 GB</b>, eski Rev B'de <b>2 GB</b>'tır.

- Kartın <b>kalıcı depolama alanıdır</b>. Bilgisayardaki HDD/SSD gibi düşünebilirsin.
- Kart fabrikadan eMMC'de yüklü bir Debian ile gelir. Bu yüzden SD kart takmadan güç verildiğinde Linux açılır.
- SD karta göre <b>daha hızlı ve güvenilirdir</b>: 8-bit veri yolu ve dahili denetleyicisi vardır. Kartın üzerinde olduğu için çıkmaz, kaybolmaz, temas sorunu yaşamaz. Bu yüzden ürünlerde (sahadaki cihazlarda) tercih edilir.

### DDR RAM ile farkı

| | DDR RAM | eMMC |
|---|---|---|
| <b>PC karşılığı</b> | RAM | HDD / SSD |
| <b>Kalıcılık</b> | Geçici, güç gidince silinir | Kalıcı |
| <b>Görevi</b> | Çalışma alanı | Depolama |
| <b>BBB'de boyut</b> | 512 MB DDR3L | 4 GB (Rev C) |

> [!NOTE]
> İşlemci kodu doğrudan eMMC'den çalıştırmaz. Açılışta MLO, U-Boot, kernel ve device tree eMMC'den okunur, adım adım RAM'e yüklenir ve orada çalıştırılır.

---

## 5.2 Donanım Bağlantısı

![BBB'de eMMC, SD kart ve DDR bağlantısı](../images/{E7E4FC4C-DBAC-4C4E-8FE5-D1274DAB2D14}.png)

| Bileşen | AM335x'e bağlantısı | Linux'ta (genelde) |
|---|---|---|
| <b>4 GB eMMC</b> | <b>mmc1</b> arayüzü (8-bit) | `mmcblk1` |
| <b>microSD kart</b> | <b>mmc0</b> arayüzü | `mmcblk0` |
| <b>DDR (512 MB)</b> | DDR arayüzü | - |

> [!CAUTION]
> Numaralandırma kernel sürümüne ve device tree'ye göre değişebilir. Bir diske bir şey yazmadan önce <b>`lsblk` ile mutlaka kontrol et</b>. Yanlış diske yazmak oradaki sistemi siler.

Varsayılan boot sırasında eMMC ilk sıradadır. eMMC'de geçerli bir MLO varsa kart oradan açılır, SD kart takılı olsa bile ona bakmaz. SD karttan açmak için <b>güç verirken S2'ye basılı tutulmalıdır</b> ([3.5](03_boot_process.md#35-boot-kaynakları-ve-boot-sırası-sysboot-pinleri)).

---

## 5.3 eMMC'ye Debian Yükleme (Teori)

eMMC'ye doğrudan bilgisayardan yazılamaz, çünkü kartın üzerine lehimlidir. Bu yüzden önce <b>SD karttan</b> boot edilir, sonra SD karttaki her şey eMMC'ye kopyalanır.

![eMMC'ye Debian yükleme adımları](../images/{BEFA8946-6220-443D-B624-79EA686B7EC1}.png)

1. En güncel <b>Debian OS</b> image'ını indir.
2. Bootable image'ı önce <b>SD karta</b> yaz.
3. Kartı <b>SD karttan boot et</b> (güç verirken S2'ye basılı tut).
4. <b>eMMC flasher script</b>'ini çalıştır.
5. Flasher script, <b>SD karttaki her şeyi eMMC'ye kopyalar</b>.

### eMMC flasher script ne yapar?

![eMMC flasher script akışı](../images/{5F2184FB-5B91-43CB-8B04-0FDA7014DD3B}.png)

1. Script <b>SD karttan</b> çalıştırılır.
2. eMMC iki bölüme (partition) ayrılır: <b>FAT</b> ve <b>EXT4</b>.
3. Bu bölümler formatlanır ve dosya sistemleri oluşturulur:
   - <b>FAT</b>: Boot dosyaları (MLO, u-boot.img vb.)
   - <b>EXT4</b>: Root dosya sistemi (rootfs)
4. SD karttaki tüm içerik yeni oluşturulan bölümlere kopyalanır.
5. İş bitince kart <b>kapatılır</b>.

> [!NOTE]
> Bu, [Bölüm 4](04_sd_card_boot.md)'te SD kart için GParted ile elle yaptığımız bölümlendirme ve kopyalama işleminin eMMC için otomatik yapılan halidir.

---

## 5.4 Uygulama: eMMC'yi Güncelleme

### 5.4.1 Kartın IP adresini öğren

Kartı bilgisayara bağladığın yönteme göre IP adresi değişir. Güncel liste: <https://beagleboard.org/getting-started>

![BeagleBone IP adresleri](../images/{C5156823-84C4-41B0-8EC4-B5835A0CD1A6}.png)

| Bağlantı | Bilgisayarın işletim sistemi | IP adresi |
|---|---|---|
| USB | Windows | `192.168.7.2` |
| USB | Mac OS X, <b>Linux</b> | `192.168.6.2` |
| WiFi | Hepsi | `192.168.8.1` |
| Hepsi (mDNS) | Hepsi | `beaglebone.local` |

Bağlantıyı test etmek için:

```bash
ping 192.168.6.2
```

### 5.4.2 SSH ile karta bağlan

> [!TIP]
> SSH'ın bilgisayarında yüklü olup olmadığını `ssh -V` komutuyla kontrol edebilirsin. Yüklü değilse Ubuntu'da `sudo apt install openssh-client`, Fedora'da `sudo dnf install openssh-clients` ile kurabilirsin.

```bash
ssh debian@192.168.6.2
```

![SSH ile BeagleBone'a bağlanma](../images/{A9566984-B563-4C49-A9A1-9816B21F6E62}.png)

Bağlanınca kart karşılama mesajında varsayılan kullanıcı adını ve şifreyi gösterir. `password:` satırına şifreyi yaz:

| Kullanıcı adı | Şifre |
|---|---|
| `debian` | `temppwd` |

> [!NOTE]
> Şifre yazarken ekranda hiçbir karakter görünmez. Bu normaldir, yazmaya devam edip Enter'a bas.

> [!IMPORTANT]
> `temppwd` şifresi kartla gelen <b>eski image'larda</b> geçerlidir. En güncel image'larda varsayılan şifre yoktur. Kullanıcı adı ve şifre, SD karta yazdıktan sonra FAT bölümündeki <b>`sysconf.txt`</b> dosyasından ilk açılıştan önce ayarlanmalıdır ([5.4.4](#544-en-güncel-imageı-indir)).

İlk bağlantıda `Are you sure you want to continue connecting (yes/no)?` diye sorarsa `yes` yaz.

### 5.4.3 Karttaki Debian sürümünü kontrol et

```bash
lsb_release -da
```

![Debian sürümünü kontrol etme](../images/{636C391B-AE68-4635-A859-93F6D5533991}.png)

Bu örnekte kartta <b>Debian 10 (buster)</b> yüklü.

> [!TIP]
> Kartında zaten en güncel Debian image'ı yüklüyse bu bölümün geri kalanını atlayabilirsin.

### 5.4.4 En güncel image'ı indir

Güncel image'lar: <https://beagleboard.org/latest-images>

![En güncel BeagleBone Black Debian image'ı](../images/{F642D326-33B6-4A9D-B77A-6F9932E2AF22}.png)

Bu notun yazıldığı tarihte en güncel sürüm <b>Debian 13.7 (2026-10-09, IoT)</b> idi. Karttaki Debian 10'dan çok daha yeni olduğu için eMMC'yi güncellemek gerekiyor.

- <b>Image</b> butonu ile `.img.xz` dosyasını indir.
- İstersen <b>sha256</b> ile indirdiğin dosyanın bozulmadığını kontrol edebilirsin:
  ```bash
  sha256sum <indirilen-dosya>.img.xz
  ```
  Çıkan değer sitedeki sha256 değeriyle aynı olmalı.

> [!IMPORTANT]
> Sitedeki açıklamada da yazdığı gibi, bu image'da kullanıcı şifresi <b>ilk açılıştan önce</b> FAT32 bölümündeki `sysconf.txt` dosyasından ayarlanmalıdır.

### 5.4.5 Image'ı SD karta yaz (balenaEtcher)

Bu image doğrudan eMMC'ye yazılamaz. Önce <b>SD karta</b> yazılır, ardından kart SD karttan açılıp eMMC'ye aktarılır ([5.3](#53-emmcye-debian-yükleme-teori)). SD karta yazmak için bir programa ihtiyacımız var: <b>balenaEtcher</b> (<https://etcher.balena.io>).

![balenaEtcher](../images/{A7E04BE8-B7AF-43AA-A284-2D62653B27FF}.png)

#### Neden dosyayı SD karta kopyalamak yetmiyor?

İndirilen `.img.xz` dosyası normal bir dosya değil, <b>bütün bir diskin birebir kopyasıdır</b>:

```
Debian image'ı (.img)
├── Bölüm tablosu (partition table)   → diskin hangi kısmı hangi bölüm
├── BOOT bölümü (FAT)                  → MLO, u-boot.img, sysconf.txt ...
└── rootfs bölümü (EXT4)               → Debian'ın tamamı
```

Dosyayı sürükle-bırak ile kopyalarsan SD kartta sadece tek bir büyük `.img` dosyası olur ve kart açılmaz. Etcher ise image'ı <b>diskin en başından itibaren ham olarak (byte byte) yazar</b>. Böylece SD kart image'daki bölümlere birebir sahip olur ve boot edilebilir hale gelir.

#### Etcher ile yazma adımları

![balenaEtcher image ve hedef seçimi](../images/{89A9E107-ACD1-4ABC-8E08-3421A12E07A1}.png)

1. <b>Flash from file</b> ile indirdiğin image dosyasını seç (kursta: `bone-debian-10.3-iot-armhf-2020-04-06-4gb.img.xz`).
2. <b>Select target</b> ile SD kartı seç. Kart okuyucu bilgisayarda bir USB depolama aygıtı olarak görünür.
3. <b>Flash!</b> butonuna bas. Yazma ve doğrulama (verify) bitene kadar bekle.

![balenaEtcher hedef listesi](../images/{2B998CAA-4FFD-45B2-B007-FC0D16591C0A}.png)

Bu örnekte iki aygıt görünüyor:

| Aygıt | Boyut | Konum | Açıklama |
|---|---|---|---|
| Compute Module | 18.9 MB | `/dev/sdb` | <b>Locked / Too small</b>, seçilemez |
| <b>Generic STORAGE DEVICE</b> | <b>15.9 GB</b> | <b>`/dev/sdc`</b> | <b>SD kart</b> → bunu seç |

#### Hangisi SD kart? (`dmesg`)

Listede birden fazla aygıt çıkarsa ve hangisinin SD kart olduğundan emin değilsen, SD kartı taktıktan hemen sonra terminalde şunu çalıştır:

```bash
sudo dmesg | tail -20
```

![dmesg çıktısında SD kart](../images/{234B1B38-C164-43DF-806A-DEDC74BC56D7}.png)

Son satırlarda yeni takılan aygıtın adı ve boyutu görünür. Bu örnekte `[sdc] ... (15.9 GB/14.8 GiB)` satırı, SD kartın <b>`/dev/sdc`</b> olduğunu gösteriyor.

> [!TIP]
> `lsblk` komutu da aygıtları boyutlarıyla listeler. Harf (`sdb`, `sdc` ...) bilgisayardan bilgisayara değişir. Her seferinde boyuta bakarak kontrol et.

### 5.4.6 Kartı SD karttan boot et

1. Kartın <b>gücünü kes</b>.
2. SD kartı BeagleBone'a <b>tak</b>.
3. Güç kablosunu tak.
4. <b>Power</b> butonuna LED'ler sönene kadar basılı tut, LED'ler sönünce bırak. Kart artık kapalı.
5. <b>S2</b> butonunu basılı tut ve bu sırada <b>Power</b> butonuna bir kez basıp bırak.
6. S2'yi <b>2-3 saniye</b> daha basılı tut, sonra bırak.
7. Kart SD karttan açılmaya başlar. Bu sırada LED'ler hızlı hızlı yanıp söner.

![Bilgisayarda BEAGLEBONE sürücüsünün görünmesi](../images/{2FE13611-4F3E-470D-A47B-6F11660D9A1E}.png)

Bilgisayarında <b>BEAGLEBONE</b> adında bir sürücü göründüyse kart açılmıştır. Şimdi [5.4.2](#542-ssh-ile-karta-bağlan)'deki SSH komutuyla tekrar bağlan:

```bash
ssh debian@192.168.6.2
```

> [!NOTE]
> Bağlanırken `REMOTE HOST IDENTIFICATION HAS CHANGED!` uyarısı alırsan bu normaldir. Kart farklı bir sistemden (SD karttan) açıldığı için SSH anahtarı değişmiştir. Eski kaydı silip tekrar bağlan:
> ```bash
> ssh-keygen -R 192.168.6.2
> ```

### 5.4.7 eMMC flasher script'ini çalıştır

Flasher script'leri `/opt/scripts/tools/eMMC` klasöründe bulunur:

```bash
cd /opt/scripts/tools/eMMC
ls
```

![/opt/scripts/tools klasörü](../images/{BAD46DD7-DA20-4EB4-8CE6-B29608D5247C}.png)

![eMMC klasöründeki flasher script'leri](../images/{5EA08989-D8DE-4213-8D3E-F2E49B150C0F}.png)

Listede birçok script var. BeagleBone Black için kullanılan <b>`init-eMMC-flasher-v3.sh`</b>:

```bash
sudo ./init-eMMC-flasher-v3.sh
```

> [!CAUTION]
> Bu script eMMC'deki <b>her şeyi siler</b> ve yerine SD karttaki sistemi yazar. eMMC'de saklamak istediğin dosya varsa önce yedekle.

> [!NOTE]
> Bu klasör ve script adı kursta kullanılan <b>Debian 10.3</b> image'ına göredir. Daha yeni image'larda flasher farklı bir yerde veya farklı bir adla olabilir. Klasör yoksa image'ın açıklamasına bakarak flasher yöntemini kontrol et.

Script çalışırken [5.3](#emmc-flasher-script-ne-yapar)'te anlatılan adımları sırayla yapar: bölümlendirme → formatlama → kopyalama. Bu birkaç dakika sürer.

![Flash işleminin başarıyla bitmesi](../images/{AD5A6E4A-82A3-42BB-AF46-ED6CD3D8F487}.png)

Flash işlemi başarılıysa şu mesajı görürsün:

```
eMMC has been flashed: please wait for device to power down.
```

Ardından kart kendini kapatır ve SSH bağlantısı kopar (`Connection to 192.168.6.2 closed by remote host.`). Bu normaldir.

### 5.4.8 eMMC'den boot et

1. SD kartı BeagleBone'dan <b>çıkar</b>. Artık ona ihtiyacın yok.
2. <b>Power</b> butonuna bir kez bas (S2'ye <b>basmadan</b>). Kart artık eMMC'den açılır.
3. SSH ile tekrar bağlan:
   ```bash
   ssh debian@192.168.6.2
   ```
4. Yeni sürümün yüklendiğini kontrol et:
   ```bash
   lsb_release -da
   ```

---

## 5.5 Özet

- eMMC kartın kalıcı, dahili deposudur (MMC1). DDR ise geçici çalışma belleğidir.
- eMMC'ye doğrudan yazılamaz: imaj önce <b>balenaEtcher</b> ile SD karta yazılır, kart <b>S2</b> ile SD karttan açılır, <b>flasher script</b> SD karttaki sistemi eMMC'ye kopyalar.
- USB üzerinden kartın adresi Linux'ta `192.168.6.2`, Windows'ta `192.168.7.2`. Bağlantı: `ssh debian@192.168.6.2`.

## 5.6 Karşılaşılabilecek Problemler

| Belirti | Sebep | Çözüm |
|---|---|---|
| `ping 192.168.6.2` cevap vermiyor | Kart henüz açılmadı ya da Windows'tasın | 1–2 dakika bekle. Windows'ta adres `192.168.7.2`. `beaglebone.local` da denenebilir. |
| `REMOTE HOST IDENTIFICATION HAS CHANGED!` | Kart farklı bir sistemden açıldı | `ssh-keygen -R 192.168.6.2` |
| Şifre kabul edilmiyor | Yeni image'da varsayılan şifre yok | SD karttaki `sysconf.txt` ile kullanıcı/şifre belirle ([5.4.4](#544-en-güncel-imageı-indir)) |
| `/opt/scripts/tools/eMMC` yok | Image sürümü farklı | Image'ın açıklamasındaki flasher yöntemini kullan |
| Kart flash'tan sonra yine eski sistemle açılıyor | SD kart hâlâ takılı ve S2'ye basıldı / flash yarıda kaldı | SD kartı çıkar, S2'ye basmadan aç. Gerekirse flash'ı tekrarla. |

---

[← Bölüm 4: SD Karttan Boot](04_sd_card_boot.md) · [İçindekiler](README.md) · [Bölüm 6: U-Boot Komut Satırı ve uEnv.txt →](06_uboot_uenv.md)
