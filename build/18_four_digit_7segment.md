<!-- Bu dosya otomatik üretildi. Düzenlemek için chapters/ altındaki kaynağı değiştir. -->
# Bölüm 18 — 4 Haneli 7-Segment Gösterge

> <b>Bu bölümde:</b>
> - 4 haneli bir göstergenin segmentleri neden ortak kullandığını ve çoğullamanın (multiplexing) nasıl çalıştığını öğreneceksin.
> - Göstergeyi 12 GPIO pinine bağlayacak, hane pinlerinin akım sınırını göreceksin.
> - Göstergeyi kullanıcı alanından çoğullayan bir C modülü yazacaksın.
> - 0000–9999 sayan bir sayaç ve kursun ödevi olan dijital saati yazacaksın.
> - Kullanıcı alanında çoğullamanın sınırlarını göreceksin.
>
> <b>Ön koşul:</b> [Bölüm 17](17_seven_segment.md) — tek haneli 7-segment gösterge, segment tablosu ve `seg7.c`.

> [!NOTE]
> Bu bölümdeki komutlar kartta <b>root</b> olarak çalıştırılır. Kart BeagleBoard Debian imajı ve kernel 5.10 ile çalışıyor; GPIO numaraları bu kernel'e göre. Terminal görüntüleri temsilidir.

---

## 18.1 4 Haneli Göstergenin Yapısı

4 haneli bir göstergede 4 × 8 = 32 LED vardır. Her LED'e ayrı pin verilseydi 32 segment pini ve COM pinleri gerekirdi. Bunun yerine üretici, dört hanenin <b>aynı harfli segmentlerini</b> içeride birbirine bağlar: dört hanenin `a` segmentleri tek bir `a` pinine çıkar, `b`'ler tek bir `b` pinine, ve böyle devam eder. Her hanenin sadece ortak pini (COM) ayrı kalır:

```
           hane 1      hane 2      hane 3      hane 4
          ┌───────┐   ┌───────┐   ┌───────┐   ┌───────┐
  a ──────┤ a     ├───┤ a     ├───┤ a     ├───┤ a     │
  b ──────┤ b     ├───┤ b     ├───┤ b     ├───┤ b     │
  ...     │ ...   │   │ ...   │   │ ...   │   │ ...   │
  dp ─────┤ dp    ├───┤ dp    ├───┤ dp    ├───┤ dp    │
          └───┬───┘   └───┬───┘   └───┬───┘   └───┬───┘
              │           │           │           │
            COM1        COM2        COM3        COM4
           (pin 12)    (pin 9)     (pin 8)     (pin 6)
```

Böylece 8 segment pini + 4 hane pini = <b>12 pin</b> yeter. Bedeli şudur: segment pinlerine bir desen yazıp iki haneyi birden açarsan iki hanede de <b>aynı rakam</b> görünür. Farklı hanelerde farklı rakam göstermenin tek yolu, haneleri sırayla açmaktır ([18.2](#182-çoğullama-multiplexing)).

Hane pinleri [17.1](17_seven_segment.md#171-7-segment-gösterge)'deki ortak katot/anot mantığıyla çalışır:

| | Segment yakmak | Haneyi açmak |
|---|---|---|
| Ortak anot (ör. 5641BS) | segment pini <b>0</b> | hane pini <b>1</b> (3.3 V) |
| Ortak katot (ör. 5641AS) | segment pini <b>1</b> | hane pini <b>0</b> (0 V) |

Kursun programı <b>ortak anot</b> gösterge kullanır.

### Pin dizilimi

Yaygın 12 pinli 0.56" göstergelerde (5641 serisi) pinler şöyledir. Göstergeye önden bakıldığında pin 1 sol alttadır:

```
     12   11   10    9    8    7
     D1    a    f   D2   D3    b
   ┌──────────────────────────────┐
   │   8.     8.     8.     8.    │
   └──────────────────────────────┘
      e    d   dp    c    g   D4
      1    2    3    4    5    6
```

`D1`–`D4` hanelerin ortak pinleridir; `D1` en soldaki hane. Farklı üreticilerin dizilimi farklı olabilir; datasheet'e bak ya da [17.1](17_seven_segment.md#171-7-segment-gösterge)'deki gibi pinleri tek tek dene.

---

## 18.2 Çoğullama (Multiplexing)

Çoğullama, aynı anda sadece <b>bir</b> haneyi açıp ona ait rakamı göstermek ve bunu dört hane için hızla tekrarlamaktır:

```
  zaman →   0       2.5      5       7.5      10      12.5 ms
            ├────────┼────────┼────────┼────────┼────────┼──
  segment:  │ "1"    │ "2"    │ "3"    │ "4"    │ "1"    │ ...
  hane 1:   ████████
  hane 2:            ████████
  hane 3:                     ████████
  hane 4:                              ████████
  hane 1:                                       ████████
            └────────── bir tarama: 10 ms ─────┘
```

Göz, saniyede ~50 kereden hızlı yanıp sönen bir ışığı sürekli yanıyor algılar (görmenin sürekliliği). Burada her hane her 10 ms'de bir yanar, yani tarama frekansı 100 Hz'dir; dört hane aynı anda yanıyor görünür.

Hesap:

```
  hane başına süre × hane sayısı = tarama periyodu
       2.5 ms     ×      4      =     10 ms   →   1 / 10 ms = 100 Hz
```

Tarama yavaşlarsa (ör. hane başına 10 ms → 25 Hz) titreme görünür; daha da yavaşlarsa rakamların sırayla yandığını gözle görürsün.

> [!IMPORTANT]
> Gösterge sadece <b>program onu taradığı sürece</b> yanar. Program uyursa ya da başka bir işle meşgul olursa ekranda tek bir hane kalır ya da gösterge söner. Bu yüzden sayaç programı sayıyı değiştirmek için `sleep()` ile beklemez; sürekli tarar ve sırası gelince sayıyı değiştirir ([18.7](#187-sayaç-ve-dijital-saat)).

Her hane zamanın sadece dörtte birinde yanık olduğu için aynı dirençle tek haneli göstergeden daha <b>soluk</b> görünür.

---

## 18.3 Devre

Kursun bağlantısı: segmentler [Bölüm 17](17_seven_segment.md)'deki P8 pinlerinde kalır, dört hane pini P9'a bağlanır.

| Pin | AM335x | GPIO | Gösterge pini | | Pin | AM335x | GPIO | Gösterge pini |
|---|---|---|---|---|---|---|---|---|
| P8_7 | GPIO2_2 | 66 | 11 (a) | | P9_15 | GPIO1_16 | 48 | 12 (D1) |
| P8_8 | GPIO2_3 | 67 | 7 (b) | | P9_23 | GPIO1_17 | 49 | 9 (D2) |
| P8_9 | GPIO2_5 | 69 | 4 (c) | | P9_30 | GPIO3_16 | 112 | 8 (D3) |
| P8_11 | GPIO1_13 | 45 | 2 (d) | | P9_27 | GPIO3_19 | 115 | 6 (D4) |
| P8_12 | GPIO1_12 | 44 | 1 (e) | | | | | |
| P8_14 | GPIO0_26 | 26 | 10 (f) | | | | | |
| P8_16 | GPIO1_14 | 46 | 5 (g) | | | | | |
| P8_10 | GPIO2_4 | 68 | 3 (dp) | | | | | |

Segment pinlerine [17.2](17_seven_segment.md#172-devre)'deki gibi birer direnç konur. Hane pinlerine direnç konmaz.

> [!NOTE]
> Kursun kodunda P9_30'un makro adı `GPIO_117_P9_30_DIGIT3`, değeri ise `112`. Doğrusu 112: P9_30 = GPIO3_16 = 3 × 32 + 16 ([15.1](15_gpio_sysfs.md#151-am335x-gpio-alt-sistemi)). P9_23'ü [Bölüm 17](17_seven_segment.md#177-ek-butonla-sayma)'de buton için kullandıysan butonu söküp pull-down direncini de çıkar.

### Hane pininin akımı

Bir hane açıkken o hanenin bütün segment akımları <b>tek bir hane pininden</b> geçer. Ortak anot göstergede `8.` rakamı için:

```
  8 segment × ~3 mA (470 Ω) ≈ 24 mA   → hepsi hane pininden çıkar
```

AM335x'in bir GPIO pini ise sadece birkaç mA verebilir ([16.1](16_external_led.md#161-gerekenler-ve-devre)). Kursun bağlantısında hane pinleri göstergeye doğrudan bağlıdır; bu, pini sınırının üzerinde zorlar. İki çözüm var:

| Çözüm | Bağlantı | Program |
|---|---|---|
| <b>Büyük segment direnci</b> (deneme için) | Segmentlere 2.2 kΩ: segment başına ~0.6 mA, hane pininden en fazla ~5 mA | Kursla aynı (`-DCOMMON_ANODE`). Gösterge soluk olur. |
| <b>Hane başına transistör</b> (önerilen) | Ortak anotta PNP (BC557, 2N3906): emitör 3.3 V'a, kolektör hane pinine, baz 1 kΩ ile GPIO'ya | `-DCOMMON_ANODE -DDIGIT_TRANSISTOR`: GPIO <b>0</b> olunca transistör iletir, hane açılır |

```
  Hane başına PNP (ortak anot)

  P9_3 (3.3 V) ●─────────────┐
                             │ E
  P9_15 (48) ●──[ 1 kΩ ]──B─┤  BC557 (PNP)
                             │ C
                             └──────● D1 (gösterge pin 12)

  (D2, D3, D4 için aynısı: P9_23, P9_30, P9_27)
```

Ortak katot göstergede transistör NPN olur (BC547, 2N2222): emitör GND'ye, kolektör hane pinine; GPIO <b>1</b> olunca hane açılır. Program bunu da `-DDIGIT_TRANSISTOR` ile bilir.

> [!WARNING]
> Kabloları kart <b>kapalıyken</b> bağla. Ortak anot göstergenin hane pinlerini ya da PNP'lerin emitörünü <b>5 V'a bağlama</b>; GPIO pinleri 3.3 V'tur ([17.2](17_seven_segment.md#172-devre)).

---

## 18.4 Pinleri Kontrol Et ve Komut Satırından Dene

Kursun "4 digit 7 segment LED Counter implementation" dersi. Segment pinlerini [17.3](17_seven_segment.md#173-pinlerin-gpio-modunda-olduğunu-doğrula)'te kontrol etmiştin; şimdi hane pinlerine bak:

![Hane pinlerinin GPIO modunu kontrol etme](../images/seg7x4/01_pin_check.png)

```bash
for p in P9_15 P9_23 P9_30 P9_27; do config-pin $p gpio; config-pin -q $p; done
grep -E '44e10(840|844|998|9a4)' /sys/kernel/debug/pinctrl/44e10800.pinmux*/pins
```

| Pin | Register |
|---|---|
| P9_15 | `0x44E10840` |
| P9_23 | `0x44E10844` |
| P9_30 | `0x44E10998` |
| P9_27 | `0x44E109A4` |

Sonra segmentlerin gerçekten ortak olduğunu gör. Ortak anot göstergede bir `7` deseni yazıp önce 1. haneyi, sonra 4. haneyi aç:

![Segmentlerin haneler arasında ortak olduğunu gösteren deneme](../images/seg7x4/02_cmdline_test.png)

```bash
for g in 66 67 69 68 45 44 26 46 48 49 112 115; do
    echo $g > /sys/class/gpio/export
    echo out > /sys/class/gpio/gpio$g/direction
done

for g in 66 67 69 68 45 44 26 46; do echo 1 > /sys/class/gpio/gpio$g/value; done  # hepsi sönük
for g in 66 67 69; do echo 0 > /sys/class/gpio/gpio$g/value; done                 # a, b, c: "7"
echo 1 > /sys/class/gpio/gpio48/value      # 1. hanede 7
echo 1 > /sys/class/gpio/gpio115/value     # 4. hanede de 7
echo 0 > /sys/class/gpio/gpio48/value; echo 0 > /sys/class/gpio/gpio115/value

for g in 66 67 69 68 45 44 26 46 48 49 112 115; do echo $g > /sys/class/gpio/unexport; done
```

Ortak katot göstergede 0 ve 1'leri tersle. Hane transistörle sürülüyorsa hane pinleri için de tersle.

---

## 18.5 Kursun Programı ve Düzeltmeler

Kursun programı `Project_Src/4digitcount/src/4_digit_7seg.c`. Tek haneli sayaçla aynı argümanları alır (`up`, `down`, `updown`, `random` ve bir gecikme). Çoğullamayı `dispaly_numbers()` fonksiyonu yapar: haneyi açar, rakamı yazar, `usleep(10)` bekler, segmentleri ve haneleri kapatır.

Kodda `updown`, `random` ve dijital saat öğrenciye bırakılmış (`TODOs for the students`, "Convert this application to implement Digital clock"). Ayrıca şu sorunlar var:

| Sorun | Sonucu | Düzeltme |
|---|---|---|
| Gecikme argümanı milisaniye değil, <b>tarama sayısı</b> (`for (i = 0; i < delay_value; i++) dispaly_numbers(number);`) | Sayma hızı CPU'ya ve sysfs'in hızına bağlı; aynı değer farklı kartlarda farklı hız verir | Gecikme ms cinsinden; zaman `clock_gettime()` ile ölçülür |
| `down` modunda `uint32_t number` 0'dan sonra azaltılıyor | 0000'dan sonra 9999 değil <b>7295</b> görünür (4294967295'in son dört hanesi) | 0'dan sonra 9999'a dön |
| Her segment yazımı `open()` + `write()` + `close()` | Hane başına 19 dosya yazımı (~57 sistem çağrısı); tarama yavaş, gösterge soluk ve titrek | `value` dosyaları bir kez açılır, sadece `pwrite()` yapılır; sadece değişen segment yazılır ([18.6](#186-çoğullama-kodu-seg7x4)) |
| Hane `usleep(10)` kadar açık, ardından 11 dosya yazımıyla kapatılıyor | Hane, zamanın küçük bir kısmında açık: gösterge soluk | Her hane 2.5 ms açık |
| Hane önce açılıyor, sonra segmentler tek tek yazılıyor | Rakam yazılırken hane yanık: ara desenler kısa süre görünür | Segmentler bütün haneler kapalıyken yazılır, sonra hane açılır |
| `COMMON_CATHODE` tanımlanırsa sadece segment mantığı değişiyor, hane hep `HIGH` ile açılıyor | Ortak katot göstergede hiçbir hane yanmaz | Hane mantığı da gösterge türüne göre seçilir |
| Hane pinleri doğrudan göstergeye bağlı | Hane pininden ~24 mA çekilir ([18.3](#183-devre)) | Transistör seçeneği (`-DDIGIT_TRANSISTOR`) |
| Hata kontrolü yok, Ctrl-C ile öldürülüyor | Gösterge son durumda kalır, GPIO'lar export edilmiş kalır | Hatalar kontrol edilir, `SIGINT` yakalanır |

---

## 18.6 Çoğullama Kodu: seg7x4

Çoğullama ayrı bir modülde: [`code/18_4digit_7segment/seg7x4.c`](../code/18_4digit_7segment/seg7x4.c), [`seg7x4.h`](../code/18_4digit_7segment/seg7x4.h). Rakamların segment desenleri [Bölüm 17](17_seven_segment.md#175-rakamları-kodlamak-segment-tablosu)'deki `seg7_pattern()`'dan gelir.

| Fonksiyon | Yaptığı iş |
|---|---|
| `seg7x4_init()` | 12 GPIO'yu export eder, çıkış yapar, `value` dosyalarını açar; haneler kapalı başlar |
| `seg7x4_refresh(digits, dp_mask)` | Dört haneyi bir kez tarar (~10 ms). `digits`: soldan sağa 4 rakam; `dp_mask`: hangi hanenin noktası yanacak |
| `seg7x4_release()` | Göstergeyi söndürür, dosyaları kapatır, GPIO'ları bırakır |

### value dosyasını açık tutmak

[Bölüm 16](16_external_led.md#164-kursun-gpio-kütüphanesi)'daki `gpio_write_value()` her çağrıda dosyayı açıp kapatır. Saniyede birkaç kez yazan bir LED programı için sorun değil; ama çoğullama saniyede yüzlerce kez yazar. Dosyayı bir kez açıp hep aynı tanımlayıcıya yazmak çok daha ucuzdur:

```c
/* Açık value dosyasına 0/1 yazar. pwrite() dosya konumunu değiştirmez. */
static int put(int fd, int value)
{
	return pwrite(fd, value ? "1" : "0", 1, 0) == 1 ? 0 : -1;
}
```

`pwrite()`, `write()`'ın belirli bir konuma (burada 0) yazan halidir; her yazmadan önce `lseek()` gerekmez.

### Tarama

```c
int seg7x4_refresh(const uint8_t digits[SEG7X4_DIGITS], uint8_t dp_mask)
{
	uint8_t bits;
	int i;

	for (i = 0; i < SEG7X4_DIGITS; i++) {
		bits = seg7_pattern(digits[i]);
		if (dp_mask & (1 << i))
			bits |= 1 << 7;

		/* Bütün haneler kapalıyken segmentleri değiştir, sonra haneyi aç. */
		if (set_segments(bits) < 0 || put(digit_fd[i], DIGIT_ON) < 0)
			return -1;

		usleep(DIGIT_ON_TIME_US);           /* 2500 µs */

		if (put(digit_fd[i], DIGIT_OFF) < 0)
			return -1;
	}
	return 0;
}
```

Sıralama önemli: önce hane kapanır, segmentler değişir, sonra yeni hane açılır. Bir hane açıkken segmentler değişirse önceki hanenin rakamı yeni hanede soluk bir "gölge" (ghosting) olarak görünür.

`set_segments()` her segmentin son yazılan değerini tutar ve sadece değişenleri yazar. `1111` gösterilirken tarama başına segment yazımı sıfıra iner; sadece hane pinleri yazılır.

### Gösterge türü

Segment ve hane mantığı derleme sırasında seçilir:

| Derleme seçeneği | Gösterge | Segment yanar | Hane açılır |
|---|---|---|---|
| (yok) | Ortak katot | 1 | 0 |
| `-DDIGIT_TRANSISTOR` | Ortak katot + NPN | 1 | 1 |
| `-DCOMMON_ANODE` | Ortak anot (kursun göstergesi) | 0 | 1 |
| `-DCOMMON_ANODE -DDIGIT_TRANSISTOR` | Ortak anot + PNP | 0 | 0 |

```c
#ifdef COMMON_ANODE
#define SEGMENT_ON          LOW_VALUE
#else
#define SEGMENT_ON          HIGH_VALUE
#endif

#ifdef DIGIT_TRANSISTOR
#define DIGIT_ON            SEGMENT_ON
#else
#define DIGIT_ON            (!SEGMENT_ON)
#endif
```

---

## 18.7 Sayaç ve Dijital Saat

Program: [`code/18_4digit_7segment/counter_4digit.c`](../code/18_4digit_7segment/counter_4digit.c).

| Mod | Davranış |
|---|---|
| `up <ms>` | 0000 → 9999 → 0000 … |
| `down <ms>` | 9999 → 0000 → 9999 … |
| `updown <ms>` | 0000 → 9999 → 0000 …; uçlar tekrarlanmaz |
| `random <ms>` | 0000–9999 arası rastgele sayılar; aynı sayı art arda gelmez |
| `clock` | Saat `SS.DD` (ör. `14.37`); 2. hanenin noktası saniyede bir yanıp söner |

Ana döngü hiç uyumaz; her turda bir kez tarar ve sayıyı değiştirme zamanı gelip gelmediğine bakar:

```c
last_step = now_ms();

while (running) {
	if (mode == CLOCK) {
		t = time(NULL);
		localtime_r(&t, &tm);
		split(tm.tm_hour * 100 + tm.tm_min, digits);
		dp_mask = tm.tm_sec % 2 ? 0 : 1 << 1;
	} else {
		if (now_ms() - last_step >= delay_ms) {
			last_step = now_ms();
			number = next_number(mode, number, &step);
		}
		split(number, digits);
	}

	if (seg7x4_refresh(digits, dp_mask) < 0)
		break;
}
```

`split()` sayıyı soldan sağa dört rakama ayırır (`42` → `0 0 4 2`). `next_number()` her modun bir sonraki değerini hesaplar; `updown` [17.6](17_seven_segment.md#176-kursun-sayaç-programı-ve-düzeltmeler)'daki gibi bir adım değişkeniyle yön değiştirir.

`now_ms()` `CLOCK_MONOTONIC` kullanır: sistem saati NTP ile ileri geri ayarlansa bile geriye gitmez. Saat modu ise duvar saatini (`time()` + `localtime_r()`) gösterir.

### Saat doğru mu?

AM335x'in içinde bir RTC var ama BeagleBone Black'te pil yok; kart kapanınca saat sıfırlanır. Debian, ağ varsa saati NTP ile (`systemd-timesyncd`) ayarlar. Saat modunu çalıştırmadan önce kontrol et:

![Saati kontrol edip saat modunu çalıştırma](../images/seg7x4/04_clock.png)

```bash
timedatectl                                   # "System clock synchronized: yes" olmalı
timedatectl set-timezone Europe/Istanbul      # gerekiyorsa saat dilimi
./counter_4digit clock
```

Kart internete çıkamıyorsa saati elle ayarla: `date -s "2026-10-19 14:37"`.

### Derle ve çalıştır

Repodaki `code/` klasöründe:

![Sayaç programını derleme ve çalıştırma](../images/seg7x4/03_build_run.png)

```bash
arm-linux-gnueabihf-gcc -Wall -Ilib -I17_7segment -DCOMMON_ANODE \
      -o counter_4digit 18_4digit_7segment/counter_4digit.c \
      18_4digit_7segment/seg7x4.c 17_7segment/seg7.c lib/gpio_driver.c
scp counter_4digit root@192.168.27.2:~/
```

Haneler transistörle sürülüyorsa `-DDIGIT_TRANSISTOR` ekle; ortak katot göstergede `-DCOMMON_ANODE`'u çıkar.

Kartta:

```bash
./counter_4digit up 100        # saniyede 10 artar
./counter_4digit down 50
./counter_4digit updown 10
./counter_4digit random 1000
./counter_4digit clock
```

Eclipse kullanıyorsan ([Bölüm 14](14_eclipse.md)): projeye `seg7x4.c`, `17_7segment/seg7.c` ve `lib/gpio_driver.c`'yi ekle, *Includes*'a `lib` ve `17_7segment` klasörlerini, *Defined symbols*'a `COMMON_ANODE` (ve gerekirse `DIGIT_TRANSISTOR`) yaz.

---

## 18.8 Kullanıcı Alanında Çoğullamanın Sınırları

Linux gerçek zamanlı bir işletim sistemi değildir. Kernel, programını herhangi bir anda durdurup başka bir süreci çalıştırabilir. Program durduğu sürece o an açık olan hane yanık kalır, diğerleri söner. Kart meşgulken (ör. `apt upgrade` sırasında) bunu parlaklık dalgalanması ve titreme olarak görürsün.

Yapabileceklerin:

- Programı gerçek zamanlı öncelikle çalıştır: `chrt -f 50 ./counter_4digit up 100`. Kernel, programını sıradan süreçlerden önce çalıştırır. Program `usleep()` ile beklediği için CPU'yu tekeline almaz.
- `top` ile programın CPU kullanımına bak. Sürekli tarama, sysfs üzerinden saniyede yüzlerce yazma demektir; bunun da bir maliyeti vardır.

Gerçek projelerde çoğullama genellikle yazılıma bırakılmaz:

| Yöntem | Açıklama |
|---|---|
| Sürücü entegresi | MAX7219 (SPI), TM1637 (2 kablo), HT16K33 (I2C) gibi entegreler taramayı kendileri yapar; işlemci sadece gösterilecek rakamları bir kez gönderir. Pin sayısı da 12'den 2–3'e iner. |
| Mikrodenetleyici | Taramayı küçük bir mikrodenetleyici zamanlayıcı kesmesiyle yapar; BBB ona UART/I2C ile rakam gönderir. AM335x'in PRU çekirdekleri de bu tür zamanlama işleri için vardır. |
| Kernel sürücüsü | Tarama kernel'de bir zamanlayıcıyla yapılır; kullanıcı alanına sadece "göster" arayüzü açılır. |

Kursun sonraki konusu MPU6050 sensörü I2C ile okur; HT16K33 gibi I2C'li bir gösterge sürücüsüyle de aynı yolla konuşulur.

---

## 18.9 Özet

- 4 haneli göstergede dört hanenin aynı harfli segmentleri içeride ortaktır; sadece hane pinleri (COM) ayrıdır. 8 + 4 = 12 pin.
- Çoğullama: segmentlere bir hanenin rakamını yaz, sadece o haneyi aç, kısa süre bekle, sıradakine geç. 4 × 2.5 ms = 10 ms tarama = 100 Hz, titreme görünmez.
- Gösterge sadece program taradığı sürece yanar; sayıyı değiştirmek için `sleep()` ile beklenmez, zaman `clock_gettime()` ile ölçülür.
- Segmentleri bütün haneler kapalıyken değiştir; yoksa gölgelenme olur.
- Hızlı tarama için `value` dosyalarını bir kez aç ve `pwrite()` ile yaz; sadece değişen segmentleri yaz.
- Bir hane pininden 8 segmentin akımı geçer; GPIO'yu korumak için hane başına transistör kullan (ortak anotta PNP, ortak katotta NPN).
- Kullanıcı alanında çoğullama Linux'un zamanlamasına bağlıdır; gerçek projelerde sürücü entegresi (MAX7219, TM1637, HT16K33) kullanılır.

## 18.10 Karşılaşılabilecek Problemler

![Sık görülen hatalar (temsili)](../images/seg7x4/05_errors.png)

| Belirti | Sebep | Çözüm |
|---|---|---|
| Bütün hanelerde aynı rakam | Haneler aynı anda açık: hane mantığı ters ya da tarama yapılmıyor | Gösterge türüne uygun `-DCOMMON_ANODE` / `-DDIGIT_TRANSISTOR` seçeneklerini kontrol et ([18.6](#186-çoğullama-kodu-seg7x4)) |
| Hiçbir hane yanmıyor | Hane mantığı ters (ör. ortak katot göstergeyi ortak anot için derlemek) ya da COM pinleri yanlış | [18.4](#184-pinleri-kontrol-et-ve-komut-satırından-dene)'teki gibi elle dene |
| Rakamlar ters (`8` yerine boşluk) | Segment mantığı ters | `-DCOMMON_ANODE` seçeneğini ekle/çıkar |
| Rakamlar titriyor, parlaklık dalgalanıyor | CPU meşgul, tarama gecikiyor | `chrt -f 50 ./counter_4digit ...`; diğer yükleri azalt |
| Bir hanede komşu hanenin rakamı soluk görünüyor | Segmentler hane açıkken değiştiriliyor (kursun kodu) | Önce haneyi kapat, segmentleri yaz, sonra sıradaki haneyi aç |
| Gösterge çok soluk | Segment direnci büyük; hane pini akımı sınırlıyor | Hane başına transistör ve 470 Ω segment direnci ([18.3](#183-devre)) |
| Geri sayımda 0000'dan sonra 7295 (kursun kodu) | `uint32_t` 0'dan sonra 4294967295'e döner | 0'dan sonra 9999'a dön |
| Aynı gecikme değeri farklı hızda sayıyor (kursun kodu) | Gecikme tarama sayısı olarak kullanılıyor | Zamanı `clock_gettime()` ile ölç |
| `export`: `Device or resource busy` (GPIO 49) | P9_23 hâlâ başka bir yerde kullanılıyor ([17.7](17_seven_segment.md#177-ek-butonla-sayma)) | `cat /sys/kernel/debug/gpio`; programı ya da overlay'i kapat |
| Saat yanlış | Kartta RTC pili yok, NTP ile eşitlenmedi ya da saat dilimi UTC | `timedatectl`, `timedatectl set-timezone ...`, gerekirse `date -s` |
| `Permission denied` | Program root olarak çalışmıyor | `sudo ./counter_4digit ...` |

---

[← Bölüm 17: 7-Segment Gösterge](17_seven_segment.md) · [İçindekiler](README.md) · [Bölüm 19: MPU6050 ile Eğim Ölçmek (I2C) →](19_mpu6050.md)
