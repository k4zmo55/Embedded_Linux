<!-- Bu dosya otomatik üretildi. Düzenlemek için chapters/ altındaki kaynağı değiştir. -->
# Bölüm 3 — Linux Boot Süreci: RBL → SPL → U-Boot

> <b>Bu bölümde:</b>
> - Kart açılırken çalışan programları (RBL, SPL/MLO, U-Boot, kernel) ve her birinin görevini öğreneceksin.
> - Neden tek bir bootloader yerine bir <b>zincir</b> olduğunu anlayacaksın.
> - SYSBOOT pinlerinin boot sırasını nasıl belirlediğini ve S2 butonunun bunu nasıl değiştirdiğini göreceksin.
>
> <b>Ön koşul:</b> [Bölüm 1](01_bbb_hardware.md) — kartın bellekleri (SRAM, DDR, eMMC, SD) ve S2 butonu.

---

![Beaglebone boot aşamaları ve her aşamanın çalıştığı bellek](../images/{6F9A1EE0-B456-4D43-8C5F-C2B7869022CB}.png)

BeagleBone Black'e güç verildiğinde Linux tek adımda açılmaz. Açılış, birbirini yükleyen bir <b>zincir</b> şeklinde ilerler. Her aşama bir sonrakini belleğe yükler ve kontrolü ona devreder:

```
Güç → RBL (ROM) → SPL / MLO (SRAM) → U-Boot (DDR) → Linux kernel (DDR) → Root filesystem → init
```

Şemadaki <b>"Runs out of ..."</b> ifadeleri her aşamanın <b>hangi bellekte çalıştığını</b> gösterir. Zincirin neden bu kadar uzun olduğu da buradan anlaşılır.

> [!NOTE]
> <b>Neden tek bir bootloader yok?</b> Açılışın ilk anında 512 MB'lık <b>DDR RAM henüz kullanılamaz</b>. DDR'ın çalışması için önce saat (clock), zamanlama ve voltaj ayarlarının yapılması gerekir ve bu ayarlar karttan karta değişir. İşlemcinin hemen kullanabildiği tek RAM, SoC'nin içindeki <b>çok küçük dahili SRAM</b>'dir. Bu yüzden önce SRAM'e sığacak kadar küçük bir program (SPL) çalışır, DDR'ı hazırlar, ardından büyük programlar (U-Boot, Kernel) DDR'a yüklenebilir.

---

## 3.1 RBL (ROM Boot Loader)

- Karta enerji verildiğinde SoC (System on Chip) üzerinde çalışan <b><i>ilk kod parçasıdır</i></b>.
- Üretici firma (Texas Instruments) tarafından yazılır ve çip üretilirken SoC'nin içindeki <b>ROM</b> belleğe kaydedilir. ROM'da olduğu için <b>değiştirilemez</b>.
- <b>Nerede çalışır:</b> Doğrudan <b>ROM</b> üzerinden (Runs out of ROM).

<b>Görevleri:</b>
1. İşlemcinin temel donanımını (saat, watchdog vb.) minimum seviyede başlatır.
2. <b>SYSBOOT</b> pinlerinin seviyesini okuyarak <b>boot sırasını</b> belirler. Beaglebone'da bu sırayı <b>S2 (Boot)</b> butonu değiştirir:
   - S2 basılı değilse: <b>eMMC</b> → microSD → UART → USB
   - S2 basılıysa: SPI → <b>microSD</b> → USB → UART
3. Bu sırayla cihazları tek tek dener ve ilk bulduğu geçerli <b>ikinci aşama bootloader</b>'ı (<b>MLO</b>) dahili SRAM'e kopyalar.
4. Kontrolü MLO'ya devreder.

> [!NOTE]
> SD karttan boot ederken RBL, kartın <b>FAT formatlı ilk bölümünde</b> (boot partition) `MLO` adlı dosyayı arar. Bu yüzden kendi boot SD kartımızı hazırlarken MLO dosyasını bu bölüme koyacağız ([Bölüm 4](04_sd_card_boot.md)).

### RBL'in yaptığı işler

![RBL'in yaptığı işler](../images/{FBF63A6C-137A-46DA-9DE4-BB6336EBAF4C}.png)

- <b>Stack Setup:</b> RBL'in C ile yazılmış fonksiyonları çalıştırabilmesi için önce bir <b>stack</b> (yığın) alanı gerekir. Fonksiyon çağrıları ve yerel değişkenler burada tutulur. RBL stack'i dahili SRAM'de kurar.
- <b>Watchdog Timer 1 (3 dakika):</b> Watchdog, belirli bir süre içinde "beslenmezse" (sıfırlanmazsa) sistemi <b>resetleyen</b> bir sayaçtır. Amacı, yazılım bir yerde takılırsa kartı kendiliğinden yeniden başlatmaktır. RBL bu sayacı <b>3 dakikaya</b> kurar ve açık bırakır. Bu yüzden sonraki aşamalar (SPL, U-Boot, Linux) bu watchdog'u ya kapatmalı ya da düzenli olarak beslemelidir. Yoksa kart 3 dakika sonra resetlenir.
- <b>System clock configuration using PLL:</b> İşlemcinin ve çevre birimlerinin saatlerini PLL ile kurar (aşağıda açıklanıyor).
- <b>MLO/SPL'i arar, SRAM'e kopyalar ve çalıştırır:</b> Yukarıdaki görev listesinin 2-4. maddeleri.

### ROM Code Startup Sequence

![ROM Code Startup Sequence (TRM Figure 26-5)](../images/{A84F2AAF-3F3B-4A9D-83A1-E62F89726776}.png)

Bu akış şeması AM335x TRM'den (Figure 26-5) alınmıştır ve RBL'in açılışta yaptığı işleri sırasıyla gösterir:

1. <b>System start-up:</b> Karta güç verilir veya reset gelir.
2. <b>Initialization:</b> İşlemcinin en temel ayarları yapılır.
3. <b>__main() (stack setup):</b> Stack kurulur. Bundan sonra C kodu çalışabilir.
4. <b>main():</b> RBL'in ana fonksiyonu başlar.
5. <b>MPU WDT1 setup:</b> Watchdog Timer 1 kurulur (3 dakika).
6. <b>DPLLs and clocks configuration:</b> PLL'ler ve saatler ayarlanır.
7. <b>Booting:</b> Boot cihazları aranır ve MLO yüklenir. Bu adımın detayı aşağıdaki <b>ROM Code Booting Procedure</b> şemasındadır.

### PLL (Phase Locked Loop) nedir?

![PLL ile kristal frekansından yüksek frekans üretimi](../images/{F870EC8F-9699-4960-8AF1-F7CCCCDE6333}.png)

- Kart üzerindeki kristal osilatör <b>düşük frekanslıdır</b> (BBB'de <b>24 MHz</b>). Ama işlemci yüzlerce MHz ile çalışmak ister.
- <b>PLL</b>, SoC içindeki bir devredir. Kristalden gelen düşük frekansı <b>çarparak</b> (ve gerektiğinde bölerek) yüksek frekanslar üretir. Şemadaki örnekte 24 MHz'lik kristalden <b>800 MHz</b>'e kadar frekans elde edilir.
- Her birim farklı bir frekansa ihtiyaç duyar. Bu yüzden SoC'de birden fazla PLL vardır ve her biri farklı bir birimi besler: <b>işlemci</b>, <b>USB</b>, <b>ekran (display)</b>, <b>bus saatleri</b> (AHB/APB) gibi.
- Doğrudan yüksek frekanslı bir kristal kullanılmamasının sebebi: Düşük frekanslı kristaller ucuz ve kararlıdır. Tek bir kristalden PLL'ler ile ihtiyaç duyulan tüm frekansları üretmek çok daha pratiktir.

### ROM Code Booting Procedure

![ROM Code Booting Procedure (TRM Figure 26-6)](../images/{2C02ED59-04FF-4CB6-8456-C5649CC2C078}.png)

Bu şema (TRM Figure 26-6), RBL'in ikinci aşama bootloader'ı (MLO) nasıl aradığını gösterir:

1. <b>Boot cihaz listesi oluşturulur:</b> RBL, <b>SYSBOOT[4:0]</b> değerine bakarak hangi cihazları hangi sırayla deneyeceğini belirler ([3.5](#35-boot-kaynakları-ve-boot-sırası-sysboot-pinleri)).
2. <b>Process device:</b> Listedeki sıradaki cihaz denenir. Cihazlar iki türe ayrılır:
   - <b>Memory type (bellek türü):</b> eMMC, SD kart, NAND, SPI flash gibi. MLO bu belleğin içinde <b>hazır durur</b>, RBL sadece okur.
   - <b>Peripheral type (çevre birimi türü):</b> UART, USB, Ethernet gibi. MLO kartta yoktur, <b>dışarıdan</b> (bir bilgisayardan) gönderilmesi beklenir. Bu yüzden burada <b>timeout</b> (zaman aşımı) vardır: Belirli süre içinde imaj gelmezse başarısız sayılır.
3. <b>Success:</b> MLO bulunduysa <b>"Jump to Initial SW"</b>, yani MLO'ya atlanır ve kontrol ona geçer.
4. <b>Fail / Timeout:</b> Listede başka cihaz varsa <b>bir sonrakine</b> geçilir.
5. <b>Dead loop:</b> Listedeki hiçbir cihazda MLO bulunamazsa RBL sonsuz bir döngüye girer ve kart hiçbir şey yapmaz.

> [!TIP]
> BBB'nin varsayılan boot listesinde <b>UART0</b> da vardır. eMMC'de ve SD kartta geçerli bir MLO yoksa RBL sırayı UART0'a getirir ve seri konsoldan X-Modem ile imaj bekler. Bu sırada seri konsolda sürekli `CCCCCCCC...` yazdığını görürsün. Bu çıktı, <b>"RBL MLO bulamadı"</b> anlamına gelir. Bu davranışı [Bölüm 7](07_uart_boot.md)'de kartı seri porttan açmak için kullanacağız.

---

## 3.2 SPL / MLO (Secondary Program Loader)

- <b>SPL</b> = Secondary Program Loader (İkinci Aşama Önyükleyici). TI işlemcilerinde bu dosyanın adı <b>MLO</b>'dur (MLO = MMC Loader). SPL ile MLO <b>neredeyse</b> aynı şeydir (farkı aşağıda).
- SPL ayrı bir program değildir. <b>U-Boot'un kaynak kodundan derlenir</b>, ama sadece gerekli kısımları içeren çok küçük bir versiyonudur. U-Boot'u derlediğimizde hem `MLO` hem de `u-boot.img` dosyaları birlikte oluşur ([Bölüm 9](09_uboot_build.md)).
- <b>Nerede çalışır:</b> SoC içindeki <b>dahili SRAM</b> üzerinde (Runs out of internal SRAM). SRAM çok küçük olduğu için SPL de küçük olmak zorundadır.

### SPL ile MLO arasındaki fark

![MLO = image header + SPL](../images/{C970A18C-744B-46D4-A0A8-73AF33EA031A}.png)

- <b>MLO = Image header + SPL</b>. Yani MLO, başına küçük bir <b>başlık (header)</b> eklenmiş SPL'dir.
- Header'da RBL'in ihtiyaç duyduğu bilgiler bulunur:
  - <b>load_addr:</b> SPL'in belleğin <b>hangi adresine</b> kopyalanacağı
  - <b>Size:</b> Header'dan sonra gelen SPL kodunun <b>boyutu</b>
- RBL önce header'ı okur. Böylece SPL'i nereye kopyalayacağını ve ne kadar veri okuyacağını öğrenir, kopyalamayı yapar ve o adrese atlar.
- U-Boot derlendiğinde önce header'sız SPL (`u-boot-spl.bin`) oluşur. Başına header eklenince `MLO` dosyası elde edilir.

> [!NOTE]
> Slayttaki `0x40000000` adresi bir örnektir. AM335x'te MLO gerçekte dahili SRAM'deki `0x402F0400` adresine yüklenir.

<b>Görevleri:</b>
1. <b>DDR RAM'i başlatır.</b> En kritik görevi budur. Saat (PLL) ve DDR zamanlama ayarlarını yapar, böylece 512 MB'lık RAM kullanılabilir hale gelir.
2. Seri konsol (UART0) gibi gerekli birkaç çevre birimini hazırlar. Seri konsolda gördüğün ilk `U-Boot SPL ...` satırı buradan gelir.
3. Üçüncü aşama bootloader'ı, yani <b>U-Boot</b>'u (`u-boot.img`) eMMC/SD karttan okuyup <b>DDR</b>'a yükler.
4. Kontrolü U-Boot'a devreder.

### Soru: AM335x'in RBL'i neden U-Boot'u doğrudan DDR'a yükleyemez?

<b>Cevap:</b> Çünkü RBL, karta <b>hangi DDR belleğin takılı olduğunu bilmez</b>. Bilmediği bir belleği de başlatamaz.

- DDR RAM'den veri okuyup yazabilmek için önce SoC içindeki <b>DDR kontrolcüsünün</b> ve RAM'in <b>doğru parametrelerle</b> ayarlanması gerekir: bellek tipi (DDR2, DDR3, DDR3L...), boyut, hız, zamanlama (timing) değerleri vb.
- Bu parametreler <b>tamamen karta (ürüne) özeldir</b>. Aynı AM335x işlemcisini kullanan farklı firmalar farklı bellekler seçebilir:
  - X firması: Micron marka <b>DDR3</b>
  - Y firması: Başka bir markanın <b>DDR2</b>'si
  - Z firması: Hiç DDR kullanmayabilir
- RBL çip üretilirken ROM'a yazılır. O an çipin hangi kartta, hangi bellekle kullanılacağı belli değildir. Bu yüzden RBL <b>DDR'ı hiç başlatmaz</b>. Sadece her işlemcide garanti olarak bulunan <b>dahili SRAM</b>'i kullanır.
- U-Boot ise dahili SRAM'e <b>sığmayacak kadar büyüktür</b>. Yani RBL'in U-Boot'u yükleyebileceği bir yer yoktur.

<b>Çözüm SPL'dir:</b> SPL, dahili SRAM'e sığacak kadar küçüktür ve kartın DDR ayarlarını <b>bilir</b>, çünkü o kart için derlenmiştir. RBL, SPL'i SRAM'e yükler. SPL de DDR'ı başlatıp U-Boot'u DDR'a yükler.

> [!NOTE]
> Kendi kartını tasarlayıp BBB'den farklı bir DDR kullanırsan, SPL kaynak kodundaki <b>DDR parametrelerini</b> kendi belleğine göre değiştirip SPL'i yeniden derlemen gerekir.

> [!NOTE]
> <b>Saat (clock) ayarları:</b> RBL'in kodu ROM'da olduğu için saat ayarları <b>değiştirilemez</b>. SYSBOOT[15:14] ile sadece karttaki kristalin frekansı bildirilir. İşlemci (MPU), DDR ve çevre birimi frekanslarını asıl kuran <b>SPL</b>'dir. SPL'i kendimiz derlediğimiz için bu ayarları kaynak kodda değiştirip yeniden derleyebiliriz. Açılıştan sonra Linux da <b>cpufreq</b> ile işlemci frekansını çalışma sırasında değiştirebilir.

---

## 3.3 U-Boot (Universal Bootloader)

- Açık kaynak kodlu ve gömülü sistemlerde en yaygın kullanılan bootloader'dır. Üçüncü (ve son) aşama önyükleyicidir.
- <b>Nerede çalışır:</b> <b>DDR RAM</b> üzerinde (Runs out of DDR). Artık bellek kısıtı olmadığı için çok daha fazla özellik içerebilir.

<b>Görevleri:</b>
1. Linux Kernel'i çalıştırmak için gereken donanımları (eMMC, SD kart, Ethernet, USB vb.) başlatır.
2. <b>Linux Kernel</b> imajını (`zImage` / `uImage`) bir kaynaktan (SD kart, eMMC, seri port, ağ üzerinden TFTP vb.) okuyup <b>DDR</b>'a yükler.
3. Kartın donanımını tarif eden <b>Device Tree</b> dosyasını (BeagleBone Black için `am335x-boneblack.dtb`) DDR'a yükler.
4. Kernel'e <b>bootargs</b> (komut satırı parametreleri) iletir. Örneğin root filesystem'in nerede olduğu (`root=`) veya hangi konsolun kullanılacağı (`console=`) bu parametrelerle bildirilir.
5. Kontrolü Linux Kernel'e devreder. Bu noktadan sonra U-Boot'un işi biter.

<b>Neden önemli:</b>
- U-Boot'un kendi <b>komut satırı</b> vardır. Açılışta seri konsolda geri sayım (`Hit any key to stop autoboot`) sırasında bir tuşa basarsan U-Boot komut satırına (`U-Boot#` veya `=>`) düşersin. Buradan bellek okuma/yazma, dosya yükleme, boot ayarlarını değiştirme gibi işlemler yapılabilir ([Bölüm 6](06_uboot_uenv.md)).
- Boot ayarları <b>environment değişkenlerinde</b> (`bootcmd`, `bootargs` vb.) tutulur ve `printenv` / `setenv` komutlarıyla görüntülenip değiştirilebilir.

---

## 3.4 Linux Kernel ve Root Filesystem

U-Boot `bootm` (veya `bootz`) komutuyla kernel'e atladıktan sonra zincirin son iki halkası çalışır:

1. <b>Kernel</b> kendini RAM'de açar (`zImage` sıkıştırılmıştır), U-Boot'un verdiği <b>Device Tree</b>'yi okuyup kartta hangi donanımın olduğunu öğrenir ve sürücüleri başlatır ([Bölüm 11](11_device_tree.md)).
2. Kernel, `bootargs`'taki <b>`root=`</b> parametresine bakarak <b>root filesystem</b>'i (`/`) bağlar. Bu bir SD kart bölümü (`/dev/mmcblk0p2`), eMMC bölümü veya RAM'deki bir initramfs olabilir.
3. Rootfs'teki ilk program olan <b>`init`</b>'i (systemd veya BusyBox init) çalıştırır. Bundan sonra servisler başlar ve `login:` ekranı gelir.

> [!NOTE]
> `console=` parametresindeki konsol adı kernel sürümüne göre değişir. Kursun hazır kernel'inde (3.8.13) UART0'ın adı `ttyO0`, yeni kernel'lerde `ttyS0`'dır. Yanlış ad yazılırsa kernel açılır ama mesajlarını göremezsin.

---

## 3.5 Boot Kaynakları ve Boot Sırası (SYSBOOT Pinleri)

AM335x işlemcisi tek bir yerden boot etmek zorunda değildir. <b>Birçok farklı çevre biriminden</b> (eMMC, SD kart, UART, USB, SPI flash, NAND, Ethernet...) boot edebilir. Peki RBL hangisinden boot edeceğine nasıl karar verir? Bunu işlemcinin <b>SYSBOOT</b> pinleri belirler.

![SYSBOOT Configuration Pins (TRM Table 26-7)](../images/{E888F879-1457-455D-A181-9F3391010FE6}.png)

Bu tablo, AM335x'in <b>Technical Reference Manual (TRM)</b> dokümanındaki <b>Table 26-7: SYSBOOT Configuration Pins</b> tablosudur.

### SYSBOOT pinleri nedir?

- <b>SYSBOOT[15:0]</b>, işlemcinin 16 adet pinidir. Karta <b>güç verildiği anda</b> RBL bu pinlerin seviyesini (1 veya 0) okur.
- Okunan değer, <b>CONTROL_STATUS</b> adlı bir register'a kaydedilir. Tablonun 3. satırındaki `CONTROL_STATUS[...]` ifadeleri, her SYSBOOT bitinin bu register'da hangi bite karşılık geldiğini gösterir.
- Bu pinlerin seviyesi kart üzerindeki <b>pull-up / pull-down dirençleriyle</b> sabitlenir. Yani boot ayarı, kartı tasarlayan kişi tarafından donanımsal olarak belirlenir.

### Tablonun sütunları

| Sütun | Ne işe yarar? |
|---|---|
| <b>SYSBOOT[15:14]</b> | Karttaki kristalin (osilatörün) frekansını bildirir: 19.2 / 24 / 25 / 26 MHz. Beaglebone Black <b>24 MHz</b> kristal kullanır (<b>01b</b>). |
| <b>SYSBOOT[13:12]</b> | Normal çalışma için <b>00b</b> olmalıdır. |
| <b>SYSBOOT[11:10], [9], [8]</b> | Sadece belirli boot türlerinde (XIP, NAND) kullanılan ek ayarlar. Diğer boot türlerinde önemsizdir ("Don't care"). |
| <b>SYSBOOT[7:6]</b> | Ethernet (EMAC) üzerinden boot için PHY modu. |
| <b>SYSBOOT[5]</b> | CLKOUT1 saat çıkışının açık/kapalı olması. |
| <b>SYSBOOT[4:0]</b> | <b>En önemli kısım.</b> Boot modunu, yani <b>hangi cihazların hangi sırayla</b> deneneceğini belirler. |
| <b>Boot Sequence</b> | SYSBOOT[4:0] değerine göre RBL'in deneyeceği cihazlar: <b>1st → 2nd → 3rd → 4th</b>. |

### Boot Sequence (Boot sırası) nasıl çalışır?

Resimde kırmızıyla işaretlenen satırı örnek alalım. <b>SYSBOOT[4:0] = 00001b</b> ise boot sırası şöyledir:

```
1st: UART0  →  2nd: XIP (NOR flash)  →  3rd: MMC0 (SD kart)  →  4th: SPI0
```

1. RBL önce <b>1. cihazı</b> (UART0) dener.
2. O cihazda geçerli bir boot imajı (MLO) bulamazsa veya cihaz yanıt vermezse <b>bir sonraki cihaza</b> geçer.
3. Geçerli bir imaj bulduğu <b>ilk cihazdan</b> boot eder ve diğerlerine bakmaz.
4. Dört cihazın hiçbirinde imaj bulamazsa boot başarısız olur.

SYSBOOT[4:0] 5 bit olduğu için 32 farklı kombinasyon vardır. Her biri farklı bir boot sırası tanımlar. Resimde bunların sadece ilk birkaçı görünüyor, tablonun tamamı TRM'de.

### Tablodaki boot kaynakları

| İsim | Anlamı |
|---|---|
| <b>MMC0</b> | Beaglebone'da <b>microSD kart</b> yuvası |
| <b>MMC1</b> | Beaglebone'da kart üstündeki <b>eMMC</b> |
| <b>UART0</b> | Seri port üzerinden boot. İmaj bilgisayardan seri hat ile (X-Modem protokolü) gönderilir ([Bölüm 7](07_uart_boot.md)). |
| <b>USB0</b> | USB üzerinden boot. Kart, bilgisayara bir ağ cihazı gibi görünür ve imajı oradan alır. |
| <b>SPI0</b> | SPI ile bağlı harici flash bellekten boot |
| <b>XIP</b> | e<b>X</b>ecute <b>I</b>n <b>P</b>lace: Kod, NOR flash'a kopyalanmadan doğrudan orada çalıştırılır. |
| <b>NAND / NANDI2C</b> | Harici NAND flash bellekten boot |
| <b>EMAC</b> | Ethernet üzerinden ağdan boot |

> [!NOTE]
> UART0 ve USB0 boot modları, kartta hiç yazılım olmadığında (örneğin eMMC boşsa veya bozulduysa) kartı <b>kurtarmak</b> için kullanılır.

### BeagleBone Black'te durum

BeagleBone Black'in boot ayarları, resmi dokümandaki şu tabloda görünür:

![BBB SYSBOOT tablosu](../images/beaglebone/bbb_sysboot_tablosu.jpg)

| Durum | SYSBOOT[4:0] | Boot Sequence |
|---|---|---|
| <b>S2 basılı değil</b> (varsayılan) | <b>11100b</b> | <b>MMC1 (eMMC)</b> → MMC0 (SD) → UART0 → USB0 |
| <b>S2 basılı</b> (güç verilirken) | <b>11000b</b> | SPI0 → <b>MMC0 (SD)</b> → USB0 → UART0 |

- İki değer arasında sadece <b>SYSBOOT[2]</b> biti farklıdır: 11<b>1</b>00 → 11<b>0</b>00. Boot (<b>S2</b>) butonu tam olarak bu biti <b>0</b>'a çeker.
- Varsayılan durumda eMMC ilk sırada olduğu için kart <b>eMMC'deki</b> hazır Debian'dan açılır.
- S2'ye basılıyken eMMC listede <b>hiç yoktur</b>. SPI0'da flash olmadığı için o adım atlanır ve kart <b>SD karttan</b> açılır. Kendi derlediğimiz MLO/U-Boot/Kernel'i bu yüzden SD karta koyup S2 ile boot edeceğiz.
- Beaglebone'da SYSBOOT pinleri <b>LCD veri pinleriyle</b> (LCD_DATA0–15) ortaktır ve P8 header'ına çıkar. Bu pinlere boot sırasında dışarıdan sinyal verilirse boot sırası bozulabilir. Bu yüzden kart açılmadan P8'e bir şey bağlarken dikkatli olmak gerekir.
- Listede <b>EMAC (Ethernet) yoktur</b>. ROM Code BBB'de ağdan boot edemez. Ağdan boot için önce SD karttan U-Boot'u açmak gerekir ([Bölüm 8](08_tftp_boot.md)).

> [!IMPORTANT]
> SYSBOOT pinleri <b>sadece güç verildiği anda</b> okunur. Kart açıldıktan sonra S2'ye basmak veya Reset butonuna basmak boot sırasını değiştirmez. S2 ile boot etmek için gücü tamamen kesip, S2'yi basılı tutarak tekrar güç vermelisin.

---

## 3.6 Schematic'te Boot Devresi

Yukarıda anlatılan boot ayarının kart üzerindeki karşılığı, BBB schematic'inin <b>6. sayfasındaki</b> devredir.

![BBB Boot Configuration devresi](../images/beaglebone/bbb_sch_boot_config.png)

> Kaynak: BeagleBone Black Rev C schematic, sayfa 6 ([niekiran/EmbeddedLinuxBBB](https://github.com/niekiran/EmbeddedLinuxBBB) reposundaki `BBB_SCH.pdf`)

Schematic'te dikkat edilecekler:
- Her <b>SYS_BOOTx</b> hattına üstte bir pull-up (R55–R70), altta bir pull-down (R80–R95) direnci için yer var. Bunlardan sadece biri karta takılıdır. <b>DNI</b> (Do Not Install) yazan direnç kartta <b>yoktur</b>.
- Takılı dirençlere bakınca SYS_BOOT[4:0] = <b>11100b</b> çıkar. Bu değer, yukarıdaki tablodaki varsayılan değerle aynıdır.
- <b>S2</b> butonu (üzerinde <b>"uSD BOOT"</b> yazar), <b>R75</b> üzerinden <b>SYS_BOOT2</b> hattını <b>GND</b>'ye bağlar.

---

## 3.7 Özet

| Aşama | Kim yazar? | Nerede saklanır? | Nerede çalışır? | Ana görevi |
|---|---|---|---|---|
| <b>RBL</b> | TI (çip üreticisi) | SoC içindeki ROM | ROM | Boot cihazını seçip MLO'yu SRAM'e yüklemek |
| <b>SPL/MLO</b> | U-Boot projesi (biz derleriz) | eMMC / SD kart | Dahili SRAM | DDR'ı başlatıp U-Boot'u DDR'a yüklemek |
| <b>U-Boot</b> | U-Boot projesi (biz derleriz) | eMMC / SD kart | DDR | Kernel + DTB'yi yükleyip Kernel'i başlatmak |
| <b>Linux kernel</b> | Linux projesi (biz derleriz) | eMMC / SD kart / ağ | DDR | Donanımı başlatmak, rootfs'i bağlamak, `init`'i çalıştırmak |

- Boot sırasını <b>SYSBOOT[4:0]</b> pinleri belirler. BBB'de varsayılan <b>eMMC → SD → UART0 → USB0</b>, S2 basılıyken <b>SPI0 → SD → USB0 → UART0</b>.
- S2 sadece <b>güç verilirken</b> etkilidir.

---

[← Bölüm 2: Seri Konsol ve Minicom](02_serial_console.md) · [İçindekiler](README.md) · [Bölüm 4: SD Karttan Boot →](04_sd_card_boot.md)
