# Bölüm 17 — 7-Segment Gösterge

> <b>Bu bölümde:</b>
> - 7-segment göstergenin yapısını, ortak katot ve ortak anot farkını öğreneceksin.
> - Tek haneli bir göstergeyi sekiz GPIO pinine dirençlerle bağlayacaksın.
> - Segmentleri komut satırından tek tek yakıp devreyi test edeceksin.
> - Rakamları bir segment tablosuyla kodlayan, yukarı/aşağı/yukarı-aşağı/rastgele sayan bir C programı yazacaksın.
> - Ek: Butonun her basışında sayıyı artıran, kesme (edge) ile çalışan bir program yazacaksın.
>
> <b>Ön koşul:</b> [Bölüm 15](15_gpio_sysfs.md) — GPIO numaraları ve sysfs, [Bölüm 16](16_external_led.md) — LED bağlama ve kursun GPIO kütüphanesi.

> [!NOTE]
> Bu bölümdeki komutlar kartta <b>root</b> olarak çalıştırılır. Kart BeagleBoard Debian imajı ve kernel {{kernel.branch}} ile çalışıyor; GPIO numaraları bu kernel'e göre. Terminal görüntüleri temsilidir.

---

## 17.1 7-Segment Gösterge

7-segment gösterge, tek bir kılıfa konmuş <b>8 LED</b>'dir: rakamı çizen 7 çubuk (segment) ve bir nokta (dp, decimal point). Segmentler `a`'dan `g`'ye harflerle adlandırılır:

```
        a
     ┌─────┐
     │     │
   f │     │ b
     │  g  │
     ├─────┤
     │     │
   e │     │ c
     │     │
     └─────┘  ●
        d      dp
```

Hangi segmentlerin yandığı hangi rakamın göründüğünü belirler. Örneğin `1` için sadece `b` ve `c`, `7` için `a`, `b` ve `c` yanar.

### Ortak katot ve ortak anot

Sekiz LED'in birer bacağı içeride birleştirilip tek bir <b>COM</b> (ortak) pinine bağlanmıştır. Hangi bacağın birleştirildiğine göre iki tür gösterge vardır:

```
  Ortak katot (common cathode)                    Ortak anot (common anode)

  a  ───►|───┐                                         ┌───►|───  a
  b  ───►|───┤                                         ├───►|───  b
  ...        ├─── COM ─── GND         3.3 V ─── COM ───┤          ...
  g  ───►|───┤                                         ├───►|───  g
  dp ───►|───┘                                         └───►|───  dp

  Segment pini 1 (3.3 V) → yanar                  Segment pini 0 (0 V) → yanar
```

| | Ortak katot | Ortak anot |
|---|---|---|
| COM bağlantısı | GND | 3.3 V |
| Segmenti yakmak | GPIO = <b>1</b> (aktif yüksek) | GPIO = <b>0</b> (aktif düşük) |
| Örnek parça | 5161AS | 5161BS |

Kursun sayaç programı <b>ortak katot</b> gösterge kullanır. Elindeki göstergenin türünü parça numarasından ya da datasheet'inden öğren; emin değilsen COM'u GND'ye bağla, bir segment pinini dirençle 3.3 V'a değdir. Yanıyorsa ortak katottur.

### Pin dizilimi

Yaygın 10 pinli tek haneli göstergelerde (0.56", 5161 serisi) pinler şöyledir. Göstergeye önden bakıldığında pin 1 sol alttadır:

```
     10   9   8   7   6
      g   f  COM  a   b
    ┌───────────────────┐
    │      ┌─────┐      │
    │      │     │      │
    │      ├─────┤      │
    │      │     │      │
    │      └─────┘ ●    │
    └───────────────────┘
      e   d  COM  c   dp
      1   2   3   4   5
```

İki COM pini içeride birbirine bağlıdır; birini bağlamak yeter.

> [!TIP]
> Farklı üreticilerin dizilimi farklı olabilir. Datasheet'in yoksa COM'u bağlayıp diğer pinleri dirençle tek tek dene; her pinin hangi segmenti yaktığını not al.

---

## 17.2 Devre

Kursun bağlantısı: segmentler P8 header'ındaki sekiz GPIO pinine bağlanır. Bu pinler varsayılan olarak GPIO modundadır ve eMMC/HDMI tarafından kullanılmaz ([15.2](15_gpio_sysfs.md#152-genişleme-headerlarındaki-gpiolar)).

| P8 pini | AM335x | GPIO numarası | Segment | Gösterge pini (5161) |
|---|---|---|---|---|
| P8_7 | GPIO2_2 | 66 | a | 7 |
| P8_8 | GPIO2_3 | 67 | b | 6 |
| P8_9 | GPIO2_5 | 69 | c | 4 |
| P8_10 | GPIO2_4 | 68 | dp | 5 |
| P8_11 | GPIO1_13 | 45 | d | 2 |
| P8_12 | GPIO1_12 | 44 | e | 1 |
| P8_14 | GPIO0_26 | 26 | f | 9 |
| P8_16 | GPIO1_14 | 46 | g | 10 |
| P8_1 / P8_2 | GND | — | COM (ortak katot) | 3 veya 8 |

```
 P8 header                                         7-segment (ortak katot)
 ┌───────────┐
 │ P8_1  GND ●────────────────────────────────────● COM (3/8)
 │ P8_7  (66)●────[ 470 Ω ]───────────────────────● a   (7)
 │ P8_8  (67)●────[ 470 Ω ]───────────────────────● b   (6)
 │ P8_9  (69)●────[ 470 Ω ]───────────────────────● c   (4)
 │ P8_10 (68)●────[ 470 Ω ]───────────────────────● dp  (5)
 │ P8_11 (45)●────[ 470 Ω ]───────────────────────● d   (2)
 │ P8_12 (44)●────[ 470 Ω ]───────────────────────● e   (1)
 │ P8_14 (26)●────[ 470 Ω ]───────────────────────● f   (9)
 │ P8_16 (46)●────[ 470 Ω ]───────────────────────● g   (10)
 └───────────┘
```

Her segment ayrı bir LED olduğu için <b>her segmente ayrı bir direnç</b> konur. Direnç hesabı [16.1](16_external_led.md#161-gerekenler-ve-devre)'dekiyle aynı: 470 Ω ile kırmızı bir segmentten ~3 mA akar.

> [!IMPORTANT]
> Tek bir direnci COM hattına koymak cazip gelebilir ama yanlıştır: o zaman bütün segmentler aynı akımı paylaşır. `1` (2 segment) parlak, `8` (7 segment) soluk görünür.

> [!WARNING]
> - Kabloları kart <b>kapalıyken</b> bağla.
> - Ortak anot gösterge kullanıyorsan COM'u <b>3.3 V</b>'a (P9_3/P9_4) bağla, asla 5 V'a bağlama. COM 5 V'ta olursa GPIO pini 3.3 V'ta iken bile segmentten pine akım akar, segment sönmez ve pin zarar görebilir.

---

## 17.3 Pinlerin GPIO Modunda Olduğunu Doğrula

Kursun "7-Segment Display basics and Interfacing" dersleri. Pinleri bağlamadan önce sekizinin de GPIO modunda olduğunu kontrol et ([16.2](16_external_led.md#162-pinin-gpio-modunda-olduğunu-doğrula)):

![Sekiz pinin GPIO modunu kontrol etme](../images/seg7/01_pin_check.png)

```bash
for p in P8_07 P8_08 P8_09 P8_10 P8_11 P8_12 P8_14 P8_16; do config-pin $p gpio; done
for p in P8_07 P8_08 P8_09 P8_10 P8_11 P8_12 P8_14 P8_16; do config-pin -q $p; done
grep -E '44e10(890|834)' /sys/kernel/debug/pinctrl/44e10800.pinmux*/pins
```

> [!NOTE]
> Güncel `config-pin` P8'in tek haneli pinlerini başında sıfırla ister: `P8_7` değil `P8_07`. Eski sürümler iki yazımı da kabul eder.

Pin ayar register'larının adresleri ([15.3](15_gpio_sysfs.md#153-pin-multiplexing-ve-pin-ayar-registerları)):

| Pin | Register | Pin | Register |
|---|---|---|---|
| P8_7 | `0x44E10890` | P8_11 | `0x44E10834` |
| P8_8 | `0x44E10894` | P8_12 | `0x44E10830` |
| P8_9 | `0x44E1089C` | P8_14 | `0x44E10828` |
| P8_10 | `0x44E10898` | P8_16 | `0x44E10838` |

---

## 17.4 Komut Satırından Segment Testi

Program yazmadan önce her segmentin doğru pine bağlandığını görmek için segmentleri tek tek yak:

![Segmentleri sysfs ile tek tek yakma](../images/seg7/02_cmdline_test.png)

```bash
for g in 66 67 69 68 45 44 26 46; do
    echo $g > /sys/class/gpio/export
    echo out > /sys/class/gpio/gpio$g/direction
done

echo 1 > /sys/class/gpio/gpio66/value                       # a
for g in 67 69; do echo 1 > /sys/class/gpio/gpio$g/value; done   # b, c → "7"

for g in 66 67 69 68 45 44 26 46; do echo 0 > /sys/class/gpio/gpio$g/value; done
for g in 66 67 69 68 45 44 26 46; do echo $g > /sys/class/gpio/unexport; done
```

Beklemediğin bir segment yanıyorsa o pinin kablosu yer değiştirmiştir. Hiçbiri yanmıyorsa COM bağlantısına ve gösterge türüne bak ([17.1](#171-7-segment-gösterge)).

---

## 17.5 Rakamları Kodlamak: Segment Tablosu

Bir rakamı göstermek, 7 segmentin her birini açıp kapatmaktır. Her segmente bir bit verirsek bir rakam tek bir bayt olur:

```
  bit:     6   5   4   3   2   1   0
  segment: g   f   e   d   c   b   a
```

| Rakam | Yanan segmentler | g f e d c b a | Hex |
|---|---|---|---|
| 0 | a b c d e f | 0 1 1 1 1 1 1 | `0x3F` |
| 1 | b c | 0 0 0 0 1 1 0 | `0x06` |
| 2 | a b d e g | 1 0 1 1 0 1 1 | `0x5B` |
| 3 | a b c d g | 1 0 0 1 1 1 1 | `0x4F` |
| 4 | b c f g | 1 1 0 0 1 1 0 | `0x66` |
| 5 | a c d f g | 1 1 0 1 1 0 1 | `0x6D` |
| 6 | a c d e f g | 1 1 1 1 1 0 1 | `0x7D` |
| 7 | a b c | 0 0 0 0 1 1 1 | `0x07` |
| 8 | a b c d e f g | 1 1 1 1 1 1 1 | `0x7F` |
| 9 | a b c d f g | 1 1 0 1 1 1 1 | `0x6F` |

Kursun programı her rakam için 7 satırlık bir `case` yazar (`Write_number_to_7segdisplay()`, 10 rakam × 7 satır). Tablo kullanınca aynı iş birkaç satıra iner ve bir rakamın şeklini değiştirmek tek bir sayıyı değiştirmek olur. Bu bölümün kodunda göstergeyi süren kısım ayrı bir dosyada: [`code/17_7segment/seg7.c`](../code/17_7segment/seg7.c), [`code/17_7segment/seg7.h`](../code/17_7segment/seg7.h).

```c
/* Segment sırası: a, b, c, d, e, f, g */
static const uint32_t seg_gpio[7] = { 66, 67, 69, 45, 44, 26, 46 };

static const uint8_t digit_segments[11] = {
	0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x6D, 0x7D, 0x07, 0x7F, 0x6F,
	0x00,   /* SEG7_BLANK: hepsi sönük */
};

void seg7_show(uint8_t digit)
{
	uint8_t bits = digit_segments[digit <= 9 ? digit : SEG7_BLANK];
	int i;

	for (i = 0; i < 7; i++)
		gpio_write_value(seg_gpio[i], (bits >> i) & 1 ? SEGMENT_ON : SEGMENT_OFF);
}
```

`SEGMENT_ON` ve `SEGMENT_OFF`, gösterge türüne göre derleme sırasında seçilir:

```c
#ifdef COMMON_ANODE
#define SEGMENT_ON          LOW_VALUE
#define SEGMENT_OFF         HIGH_VALUE
#else
#define SEGMENT_ON          HIGH_VALUE      /* ortak katot (varsayılan) */
#define SEGMENT_OFF         LOW_VALUE
#endif
```

| Fonksiyon | Yaptığı iş |
|---|---|
| `seg7_init()` | 8 GPIO'yu export eder, çıkış yapar, segmentleri söndürür |
| `seg7_show(n)` | `0`–`9` arası rakamı gösterir; `SEG7_BLANK` göstergeyi söndürür |
| `seg7_dp(on)` | Noktayı yakar/söndürür |
| `seg7_release()` | Göstergeyi söndürür ve GPIO'ları bırakır |

`seg7.c`, GPIO işlemleri için [16.4](16_external_led.md#164-kursun-gpio-kütüphanesi)'teki düzeltilmiş kütüphaneyi ([`code/lib/`](../code/lib/gpio_driver.c)) kullanır. Sonraki bölümlerde de aynı dosyalar kullanılacak.

---

## 17.6 Kursun Sayaç Programı ve Düzeltmeler

Kursun "7segment display up-down counter implementation" dersleri `Project_Src/counter_7seg/src/counter_7seg.c` programını yazar. Program iki argüman alır: sayma yönü ve iki rakam arasındaki bekleme süresi (ms).

| Mod | Davranış |
|---|---|
| `up` | 0, 1, … 9, 0, 1, … |
| `down` | 9, 8, … 0, 9, 8, … |
| `updown` | 0, 1, … 9, 8, … 1, 0, 1, … |
| `random` | Rastgele rakamlar |

Kursun kodunda `updown` ve `random` modları öğrenciye bırakılmış (`TODOs for the students`), fonksiyonlar sadece bir mesaj yazdırıyor. Kodda ayrıca şu sorunlar var:

| Sorun | Sonucu | Düzeltme |
|---|---|---|
| GPIO'lar export edilmiyor | Program, pinlerin önceden elle export edilmiş olmasını bekliyor; değilse her `open()` hata verir ama program yine de "sayıyor" | `seg7_init()` export eder |
| `initialize_all_gpios()` hataları kontrol etmiyor, her zaman `0` döndürüyor (kodda `TODO`) | Pin export edilmemişse ya da root değilsen hata görmezsin, gösterge boş kalır | Her adımın sonucu kontrol edilir |
| Program sonsuz döngüde, Ctrl-C ile öldürülüyor | Gösterge son rakamda yanık kalır, GPIO'lar export edilmiş kalır | `SIGINT` yakalanır, gösterge söndürülüp GPIO'lar bırakılır ([16.5](16_external_led.md#165-c-programıyla-ledi-yanıp-söndürmek)) |
| `write(fd, "1", 2)` | Sona fazladan `NUL` karakteri yazılıyor | Düzeltilmiş kütüphane ([16.4](16_external_led.md#164-kursun-gpio-kütüphanesi)) |

### Çözüm: updown ve random

Düzeltilmiş program: [`code/17_7segment/counter_7seg.c`](../code/17_7segment/counter_7seg.c). `updown` modu bir adım değişkeni tutar ve uçlarda yönünü değiştirir; böylece 9 ve 0 iki kez gösterilmez:

```c
static void start_updowncounting(unsigned int delay_ms)
{
	int i = 0, step = 1;

	while (running) {
		show_and_wait(i, delay_ms);
		if (i == 9)
			step = -1;
		else if (i == 0)
			step = 1;
		i += step;
	}
}
```

`random` modu `rand() % 10` ile rakam seçer. Aynı rakam art arda gelirse gösterge değişmez ve program donmuş gibi görünür; bu yüzden bir önceki rakam tekrar seçilmez:

```c
static void start_randomcounting(unsigned int delay_ms)
{
	int last = -1, n;

	srand((unsigned int)time(NULL));    /* her çalıştırmada farklı dizi */

	while (running) {
		do
			n = rand() % 10;
		while (n == last);
		last = n;
		show_and_wait(n, delay_ms);
	}
}
```

> [!TIP]
> `srand()` çağrılmazsa `rand()` her çalıştırmada <b>aynı</b> diziyi üretir. Dizi "rastgele" görünür ama programı her açışında aynı rakamlar aynı sırayla gelir.

### Derle ve çalıştır

Repodaki `code/` klasöründe:

![Sayaç programını derleme ve çalıştırma](../images/seg7/03_build_run.png)

```bash
{{build.cross_compile}}gcc -Wall -Ilib -o counter_7seg 17_7segment/counter_7seg.c \
      17_7segment/seg7.c lib/gpio_driver.c
scp counter_7seg root@{{network.board_ip}}:~/
```

Ortak anot gösterge kullanıyorsan derleme komutuna `-DCOMMON_ANODE` ekle.

Kartta:

```bash
./counter_7seg up 500         # yarım saniyede bir artar
./counter_7seg down 500
./counter_7seg updown 300
./counter_7seg random 1000
```

Eclipse kullanıyorsan ([Bölüm 14](14_eclipse.md)): projeye `seg7.c` ve `lib/gpio_driver.c`'yi ekle, *Cross GCC Compiler → Includes*'a `lib` klasörünü yaz, ortak anot için *Preprocessor → Defined symbols*'a `COMMON_ANODE` ekle.

---

## 17.7 Ek: Butonla Sayma

> [!NOTE]
> Kursun reposunda `Project_Src/button_counter_7seg/` olarak bulunan program. Göstergeye bir buton ekler: her basışta sayı bir artar. Buton girişini <b>kesme</b> (edge) ile beklemeyi gösterir.

### Buton devresi

```
  P9_3 (3.3 V) ●──────┐
                      │
                   ┌──┴──┐
                   │ BTN │
                   └──┬──┘
                      │
  P9_23 (GPIO 49) ●───┼──── basılınca 1
                      │
                   [ 10 kΩ ]   pull-down
                      │
  P9_1 (GND)   ●──────┘
```

Buton basılı değilken pin, <b>pull-down</b> direnci sayesinde 0'da kalır; basılınca 3.3 V'a bağlanır ve 1 olur. Pull-down olmazsa pin <b>boşta</b> (floating) kalır: elini yaklaştırmak bile 0/1 arasında rastgele değişime ve sahte basışlara yol açar.

AM335x'in her pininde dahili pull-up/pull-down vardır ([15.3](15_gpio_sysfs.md#153-pin-multiplexing-ve-pin-ayar-registerları)). BeagleBoard Debian'da `config-pin P9_23 gpio_pd` pini GPIO yapıp dahili pull-down'ı açar. Harici 10 kΩ direnç yine de önerilir; dahili direnç zayıftır ve pinmux yanlışsa iş görmez.

### Kesme ile beklemek: poll()

Butonu bir döngüde sürekli okumak (polling) işlemciyi boşuna meşgul eder. sysfs bunun yerine kesmeyi kullanmana izin verir:

1. `edge` dosyasına `rising` yaz: yükselen kenarda (0 → 1, basış anı) kernel bir olay üretir.
2. `value` dosyasını aç ve `poll()` ile `POLLPRI` olayını bekle. Program olay gelene kadar uyur, CPU harcamaz.
3. Olay gelince `value`'yu <b>başa sarıp oku</b> (`lseek` + `read`). Okumazsan olay temizlenmez ve `poll()` hemen tekrar döner.

```c
gpio_configure_dir(BUTTON_GPIO, GPIO_DIR_IN);
gpio_configure_edge(BUTTON_GPIO, "rising");
fd = gpio_file_open(BUTTON_GPIO);         /* value, O_RDONLY | O_NONBLOCK */

read_value_fd(fd);                        /* açılıştaki bekleyen olayı temizle */

while (running) {
	pfd.fd = fd;
	pfd.events = POLLPRI | POLLERR;
	pfd.revents = 0;

	rc = poll(&pfd, 1, -1);               /* basılana kadar uyu */
	...
	if (read_value_fd(fd) != '1')         /* olayı temizle, hâlâ basılı mı? */
		continue;

	if (now_ms() - last_press < DEBOUNCE_MS)
		continue;                         /* kontak sekmesi */
	last_press = now_ms();

	counter = (counter + 1) % 10;
	seg7_show(counter);
}
```

### Kontak sekmesi (debounce)

Mekanik bir butonun metal kontakları basıldığı anda birkaç milisaniye boyunca birbirine çarpıp ayrılır. GPIO bunu art arda birkaç yükselen kenar olarak görür:

```
  Gerçek basış:       ────┐                ┌─────
                          │                │
                          └────────────────┘

  GPIO'nun gördüğü:   ────┐ ┌┐ ┌┐          ┌─────
                          └─┘└─┘└──────────┘
                          ↑ ↑  ↑
                          3 kenar, ~1-5 ms içinde
```

Önlem alınmazsa tek basış sayıyı 2–3 artırır. Programda bir basıştan sonraki 200 ms içinde gelen kenarlar sayılmaz (yazılımla debounce). Donanımla çözmek de mümkündür: butona paralel ~100 nF kondansatör.

### Kursun kodundaki hatalar

[`code/17_7segment/button_counter_7seg.c`](../code/17_7segment/button_counter_7seg.c) bunları düzeltir:

| Sorun | Sonucu |
|---|---|
| Sayaç (`uint8_t led_counter`) ilk değer verilmeden kullanılıyor | Başlangıç değeri belirsiz; ilk basışta herhangi bir şey görünebilir |
| Sayaç 9'dan sonra başa dönmüyor | 10'da gösterge söner (`case 10`), 11'den sonra `switch`'te karşılığı yok: gösterge 245 basış boyunca boş kalır |
| İlk `poll()`'dan önce `value` okunmuyor | sysfs, dosya açılınca bir olay bekler halde başlar; ilk `poll()` hemen döner ve basılmadan bir sayılır |
| Debounce yok | Tek basış birkaç kez sayılır |
| `initialize_button_gpio()` buton yerine `GPIO_68`'e (nokta segmenti) yazıyor | Kopyala-yapıştır hatası; butona `value` yazmak zaten anlamsız (pin giriş) |
| `SEGMENT_ON` = `LOW` (sayaç programında `HIGH`) | Aynı gösterge ile iki program birbirinin tersini gösterir: biri ortak katot, öbürü ortak anot varsayar. Bizim kodda tür tek yerden seçilir ([17.5](#175-rakamları-kodlamak-segment-tablosu)) |
| `pollfd` dizisinin ilk elemanı boş (`fd = 0`, stdin) | Zararsız ama gereksiz; tek eleman yeterli |

### Derle ve çalıştır

![Butonla sayma programı](../images/seg7/04_button_counter.png)

```bash
{{build.cross_compile}}gcc -Wall -Ilib -o button_counter_7seg 17_7segment/button_counter_7seg.c \
      17_7segment/seg7.c lib/gpio_driver.c
scp button_counter_7seg root@{{network.board_ip}}:~/
```

Kartta:

```bash
config-pin P9_23 gpio_pd
./button_counter_7seg
```

Program çalışırken `top`'a bakarsan CPU kullanımının ~%0 olduğunu görürsün: `poll()` beklerken süreç uyur.

> [!NOTE]
> Aynı işi libgpiod ile de yapabilirsin ([15.6](15_gpio_sysfs.md#156-gpioları-kullanıcı-alanından-kontrol-etmek)): `gpiomon` komutu ya da kütüphanenin olay fonksiyonları. libgpiod, kernel'de debounce süresini doğrudan ayarlama seçeneği de sunar; yazılım tarafında zaman tutmaya gerek kalmaz.

---

## 17.8 Özet

- 7-segment gösterge 8 LED'dir (a–g ve dp). <b>Ortak katot</b>: COM GND'ye, segment 1 ile yanar. <b>Ortak anot</b>: COM 3.3 V'a, segment 0 ile yanar.
- Her segmente ayrı direnç (470 Ω) koy; COM'a tek direnç parlaklığı rakama göre değiştirir.
- Kursun bağlantısı: a–g ve dp → P8_7, P8_8, P8_9, P8_11, P8_12, P8_14, P8_16 ve P8_10 (GPIO 66, 67, 69, 45, 44, 26, 46, 68).
- Bir rakam bir bayttır (bit 0 = a … bit 6 = g); 10 rakamlık tablo 70 satırlık `switch`'in yerini alır.
- `updown` modu uçlarda yön değiştiren bir adım değişkeni, `random` modu `srand()` + `rand() % 10` ile yazılır.
- Butonu `edge` + `poll()` ile bekle; olaydan sonra `value`'yu başa sarıp oku, ilk `poll()`'dan önce de bir kez oku. Mekanik buton için debounce şart.

## 17.9 Karşılaşılabilecek Problemler

![Sık görülen hatalar (temsili)](../images/seg7/05_errors.png)

| Belirti | Sebep | Çözüm |
|---|---|---|
| Rakamlar ters: `8` gösterilirken her şey sönük, boşken her şey yanık | Ortak anot gösterge, program ortak katot için derlenmiş (ya da tersi) | `-DCOMMON_ANODE` ile derle; COM'u 3.3 V'a bağla |
| Hiçbir segment yanmıyor | COM bağlı değil ya da yanlış yerde; pinler GPIO modunda değil | COM'u kontrol et; [17.3](#173-pinlerin-gpio-modunda-olduğunu-doğrula), [17.4](#174-komut-satırından-segment-testi) |
| Rakamlar bozuk görünüyor (ör. `2` yerine anlamsız bir şekil) | İki segmentin kablosu yer değiştirmiş | [17.4](#174-komut-satırından-segment-testi)'teki gibi segmentleri tek tek yak |
| Bazı rakamlar soluk, bazıları parlak | Direnç segmentlerde değil COM hattında | Her segmente ayrı direnç |
| `Permission denied` / `GPIO init failed` | Program root olarak çalışmıyor | `sudo ./counter_7seg up 500` |
| `export`: `Device or resource busy` | Pin bir overlay'de ya da başka sürücüde | `cat /sys/kernel/debug/gpio` ile kimin kullandığına bak |
| `config-pin P8_7 gpio` hata veriyor | Güncel `config-pin` sıfırlı yazım istiyor | `P8_07` yaz |
| Butona basmadan sayı artıyor | Pull-down yok, pin boşta | 10 kΩ pull-down ekle, `config-pin P9_23 gpio_pd` |
| Tek basışta sayı 2–3 artıyor | Kontak sekmesi | Yazılımla debounce ([17.7](#177-ek-butonla-sayma)) ya da 100 nF kondansatör |
| Program başlar başlamaz bir basış sayıyor (kursun kodu) | İlk `poll()`'dan önce `value` okunmamış | `poll()` döngüsünden önce `lseek` + `read` |
| `poll()` sürekli dönüyor, CPU %100 | Olaydan sonra `value` okunmuyor | Her olaydan sonra `lseek(fd, 0, SEEK_SET)` + `read()` |
| GPIO numaraları yeni kernel'de çalışmıyor | Kernel 6.x'te GPIO numaraları 512'den başlayabilir | [15.6](15_gpio_sysfs.md#156-gpioları-kullanıcı-alanından-kontrol-etmek)'teki uyarı; `ls /sys/class/gpio/` ile bankaların ilk numarasını bul |
