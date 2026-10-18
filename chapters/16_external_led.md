# Bölüm 16 — Harici LED Bağlamak

> <b>Bu bölümde:</b>
> - Bir LED'i doğru dirençle bir GPIO pinine bağlayacaksın.
> - Pinin GPIO modunda olduğunu doğrulayıp LED'i komut satırından yakıp söndüreceksin.
> - Kursun GPIO kütüphanesini (düzeltilmiş haliyle) kullanan bir C programıyla LED'i yanıp söndüreceksin.
> - Ek: LED'i bir device tree overlay ile kernel'in LED alt sistemine bağlayacaksın.
>
> <b>Ön koşul:</b> [Bölüm 15](15_gpio_sysfs.md) — GPIO numaraları, pinmux ve sysfs.

> [!NOTE]
> Bu bölümdeki komutlar kartta <b>root</b> olarak çalıştırılır. Örneklerde LED <b>P9_12</b>'ye (GPIO1_28, kernel 5.10'da GPIO 60) bağlı. Terminal görüntüleri temsilidir.

---

## 16.1 Gerekenler ve Devre

| Malzeme | Not |
|---|---|
| LED (5 mm, kırmızı) | Uzun bacak <b>anot (+)</b>, kısa bacak / düz kenar <b>katot (−)</b> |
| Direnç: 470 Ω – 1 kΩ | Akımı sınırlar (hesap aşağıda) |
| Breadboard ve erkek-erkek kablolar | |

### Direnç hesabı

GPIO pini yüksek olunca 3.3 V verir. LED'in üzerinde kendi <b>ileri yön gerilimi</b> (V<sub>F</sub>) kadar gerilim düşer, kalan gerilim dirence kalır:

```
        V_GPIO − V_F        3.3 V − 2.0 V
  R  =  ────────────   =   ──────────────   ≈ 430 Ω   →  470 Ω (standart değer)
            I                  3 mA
```

| LED rengi | Tipik V<sub>F</sub> | 470 Ω ile akım | 1 kΩ ile akım |
|---|---|---|---|
| Kırmızı | ~2.0 V | ~2.8 mA | ~1.3 mA |
| Yeşil / sarı | ~2.1 V | ~2.6 mA | ~1.2 mA |
| Mavi / beyaz | ~3.0 V | ~0.6 mA (soluk) | çok soluk |

> [!CAUTION]
> AM335x pinleri sadece <b>birkaç mA</b> akım verebilir. LED'i dirençsiz bağlama; akımı birkaç mA ile sınırlı tut. Daha fazla akım çeken yükleri (parlak LED'ler, röle, motor) bir <b>transistör</b> üzerinden sür: GPIO → ~1 kΩ → NPN transistörün (ör. BC547, 2N2222) bazı; yük, 5 V/3.3 V ile transistörün kolektörü arasında.

### Bağlantı

```
 P9 header                                         Breadboard
 ┌──────────┐
 │ P9_1 GND ●──────────────────────────────────────┐
 │          │                                       │
 │ P9_12    ●───────[ 470 Ω ]────────►|────────────┘
 │ GPIO1_28 │                       anot  katot
 └──────────┘                       (uzun) (kısa)
```

Bu bağlantıda pin <b>1</b> olunca LED yanar (aktif yüksek). Tersi de mümkündür: LED'i 3.3 V (P9_3) ile pin arasına bağlarsan pin <b>0</b> olunca yanar (aktif düşük); o zaman sysfs'te `active_low` dosyasına `1` yazmak mantığı düzeltir ([15.6](15_gpio_sysfs.md#156-gpioları-kullanıcı-alanından-kontrol-etmek)).

> [!WARNING]
> Kabloları kart <b>kapalıyken</b> bağla. P9_1/P9_2 GND, P9_3/P9_4 3.3 V, P9_5–P9_8 5 V'tur. Bir GPIO pinini yanlışlıkla 5 V'a değdirmek işlemciyi bozabilir ([1.9](01_bbb_hardware.md#19-genişleme-headerları-p8-ve-p9)).

---

## 16.2 Pinin GPIO Modunda Olduğunu Doğrula

P9_12 varsayılan olarak GPIO modundadır. Yine de bir pine LED bağlamadan önce kontrol etmek iyi alışkanlıktır ([15.4](15_gpio_sysfs.md#154-çalışan-sistemde-pin-bilgisini-okumak)):

![P9_12'nin pin modunu kontrol etme](../images/ext_led/01_pin_check.png)

```bash
config-pin -q P9_12                 # BeagleBoard Debian imajlarında
config-pin P9_12 gpio
grep 44e10878 /sys/kernel/debug/pinctrl/44e10800.pinmux*/pins
```

Register değerinin son hanesi `7` (mod 7) ise pin GPIO'dur. `config-pin` BeagleBoard'un Debian imajlarına özel bir araçtır; kendi rootfs'inde ([Bölüm 12](12_busybox_rootfs.md)) yoktur, orada pinmux device tree ile yapılır.

---

## 16.3 Komut Satırından Test

Kursun "Interfacing external LED - Part 1" dersi. [15.6](15_gpio_sysfs.md#156-gpioları-kullanıcı-alanından-kontrol-etmek)'teki komutlarla:

![Harici LED'i sysfs ve libgpiod ile yakıp söndürme](../images/ext_led/02_cmdline_test.png)

```bash
echo 60 > /sys/class/gpio/export
echo out > /sys/class/gpio/gpio60/direction
echo 1 > /sys/class/gpio/gpio60/value      # yanar
echo 0 > /sys/class/gpio/gpio60/value      # söner
echo 60 > /sys/class/gpio/unexport
```

LED yanmıyorsa önce devreyi kontrol et: LED'in yönü, GND bağlantısı ve direnç değeri. LED'i ters takmak bir şeye zarar vermez, sadece yanmaz.

---

## 16.4 Kursun GPIO Kütüphanesi

Kursun reposundaki `Project_Src/Drivers/gpio/` klasörü, sysfs GPIO işlemlerini fonksiyonlara saran küçük bir kütüphanedir. Sonraki bölümlerin projeleri (7-segment, LCD) de bunu kullanır.

| Fonksiyon | Yaptığı iş | Karşılığı |
|---|---|---|
| `gpio_export(n)` | GPIO'yu kullanıcı alanına açar | `echo n > export` |
| `gpio_configure_dir(n, dir)` | Yön: `GPIO_DIR_OUT` / `GPIO_DIR_IN` | `echo out > direction` |
| `gpio_write_value(n, v)` | Çıkışı 0/1 yapar | `echo 1 > value` |
| `gpio_read_value(n)` | Girişi okur | `cat value` |
| `gpio_configure_edge(n, edge)` | Kesme kenarı: `rising`, `falling`, `both` | `echo rising > edge` |
| `gpio_file_open(n)` / `gpio_file_close(fd)` | `value` dosyasını `poll()` ile beklemek için açar | — |

### Kütüphanedeki hata

`gpio_read_value()` `value` dosyasını <b>sadece yazma</b> modunda (`O_WRONLY`) açıp ardından `read()` çağırıyor. Yazmak için açılmış bir dosyadan okunamaz; `read()` her seferinde hata verir ve fonksiyon hep `0` döndürür. Ayrıca okunan değer `'0'`/`'1'` karakteri olarak (48/49) dönecekti.

Düzeltilmiş kütüphane: [`code/lib/gpio_driver.c`](../code/lib/gpio_driver.c), [`code/lib/gpio_driver.h`](../code/lib/gpio_driver.h). Fonksiyon adları kursla aynı, sadece:

- `gpio_read_value()` dosyayı `O_RDONLY` açar ve `0`/`1` (hata durumunda `-1`) döner.
- `write()` sonuçları kontrol edilir; sona gereksiz `NUL` karakteri yazılmaz.
- GPIO'yu bırakmak için `gpio_unexport()` eklendi.

```c
/* Girişi okur: 0 veya 1, hata durumunda -1 döner. */
int gpio_read_value(uint32_t gpio_num)
{
	char path[SOME_BYTES];
	char c = 0;
	ssize_t n;
	int fd;

	snprintf(path, sizeof(path), SYS_GPIO_PATH "/gpio%u/value", gpio_num);

	fd = open(path, O_RDONLY);          /* kursta: O_WRONLY */
	...
	n = read(fd, &c, 1);
	...
	return c == '1' ? 1 : 0;            /* kursta: ASCII karakterin kendisi */
}
```

---

## 16.5 C Programıyla LED'i Yanıp Söndürmek

Kursun "Interfacing external LED - Part 2" dersi. [`code/16_external_led/led_blink.c`](../code/16_external_led/led_blink.c), kütüphaneyi kullanarak verilen GPIO'daki LED'i yanıp söndürür ve <b>Ctrl-C</b> ile durdurulunca LED'i söndürüp GPIO'yu bırakır:

```c
static volatile sig_atomic_t running = 1;

static void on_sigint(int sig)
{
	(void)sig;
	running = 0;        /* döngüye "dur" der; temizliği main yapar */
}

int main(int argc, char *argv[])
{
	...
	gpio_export(gpio);
	gpio_configure_dir(gpio, GPIO_DIR_OUT);
	signal(SIGINT, on_sigint);

	while (running) {
		on = !on;
		gpio_write_value(gpio, on);
		usleep(half_period_ms * 1000);
	}

	gpio_write_value(gpio, GPIO_LOW_VALUE);
	gpio_unexport(gpio);
	...
}
```

> [!TIP]
> `SIGINT` (Ctrl-C) yakalanmazsa program o anda ölür ve LED yanık kalabilir, GPIO da export edilmiş halde kalır. Sinyal fonksiyonu içinde sadece bir bayrağı değiştirip asıl temizliği `main`'de yapmak güvenli yöntemdir.

### Derle ve çalıştır

Repodaki `code/` klasöründe:

![Programı derleme ve kartta çalıştırma](../images/ext_led/03_build_run.png)

```bash
{{build.cross_compile}}gcc -Wall -Ilib -o led_blink 16_external_led/led_blink.c lib/gpio_driver.c
scp led_blink root@{{network.board_ip}}:~/
```

Kartta:

```bash
./led_blink 60 250       # 250 ms yanık, 250 ms sönük; Ctrl-C ile dur
```

Eclipse kullanıyorsan ([Bölüm 14](14_eclipse.md)): projeye `lib/gpio_driver.c`'yi ekle, *Cross GCC Compiler → Includes*'a `lib` klasörünü yaz.

---

## 16.6 Ek: LED'i Kernel'in LED Alt Sistemine Bağlamak

> [!NOTE]
> Bu başlık kursta yok; [Bölüm 11](11_device_tree.md) ve [Bölüm 15](15_gpio_sysfs.md)'i birleştiren bir uygulama. İlk okumada atlayabilirsin.

USER LED'ler `/sys/class/leds` altında görünüyor ve `heartbeat`, `timer` gibi tetikleyicilerle çalışıyordu ([15.5](15_gpio_sysfs.md#155-user-ledleri-sysfs-ile-kontrol-etmek)), çünkü device tree'de `gpio-leds` sürücüsüne tanıtılmışlardı. Harici LED'imizi de aynı şekilde tanıtabiliriz. Bunun için ana DTB'yi değiştirmek yerine bir <b>overlay</b> yazarız ([11.12](11_device_tree.md#1112-device-tree-overlay-dtbo)): [`code/16_external_led/BB-EXT-LED-00A0.dts`](../code/16_external_led/BB-EXT-LED-00A0.dts).

```dts
/dts-v1/;
/plugin/;

&am33xx_pinmux {
	ext_led_pins: ext-led-pins {
		pinctrl-single,pins = <
			0x078 0x07	/* P9_12: gpmc_be1n.gpio1_28, mod 7, çıkış */
		>;
	};
};

&{/} {
	ext-leds {
		compatible = "gpio-leds";
		pinctrl-names = "default";
		pinctrl-0 = <&ext_led_pins>;

		ext-led {
			label = "ext:red:p9_12";
			gpios = <&gpio1 28 0>;			/* GPIO1_28, aktif yüksek */
			linux,default-trigger = "heartbeat";
			default-state = "off";
		};
	};
};
```

| Parça | Anlamı |
|---|---|
| `&am33xx_pinmux { ... }` | AM335x'in pin ayar düğümüne yeni bir pin grubu ekler. `0x078`, `0x44E10878` register'ının `0x44E10800`'e göre ofseti; `0x07` değeri [15.3](15_gpio_sysfs.md#153-pin-multiplexing-ve-pin-ayar-registerları)'teki tablodan. |
| `&{/} { ... }` | Kök düğüme yeni bir düğüm ekler |
| `compatible = "gpio-leds"` | Bu düğümü `leds-gpio` sürücüsü sürer ([11.7](11_device_tree.md#117-compatible-ile-driver-eşleşmesi)) |
| `gpios = <&gpio1 28 0>` | GPIO1 bankasının 28. hattı, `0` = aktif yüksek |
| `linux,default-trigger` | Açılıştaki tetikleyici |

Derleyip kurmak (BeagleBoard Debian imajında, kartta):

![Overlay'i derleme, kurma ve sonuç](../images/ext_led/04_overlay.png)

```bash
dtc -@ -I dts -O dtb -o BB-EXT-LED-00A0.dtbo BB-EXT-LED-00A0.dts
cp BB-EXT-LED-00A0.dtbo /lib/firmware/
nano /boot/uEnv.txt
#   uboot_overlay_addr4=/lib/firmware/BB-EXT-LED-00A0.dtbo   satırını ekle/aç
#   enable_uboot_cape_universal=1                            satırını # ile kapat
reboot
ls /sys/class/leds/
```

Açılıştan sonra LED kalp atışı gibi yanıp sönmeye başlar ve `/sys/class/leds/ext:red:p9_12/` altında USER LED'lerle aynı dosyalara sahip olur.

> [!IMPORTANT]
> - BeagleBoard Debian imajlarında <b>cape-universal</b> açıkken P9_12 gibi pinler `config-pin` için ayrılmış durumdadır; overlay aynı pini alamaz. Bu yüzden overlay'i kullanırken cape-universal'ı kapatıyoruz (bu, `config-pin`'i de devre dışı bırakır).
> - Overlay, ana DTB'deki `am33xx_pinmux` ve `gpio1` etiketlerine başvurur; ana DTB'nin `-@` ile (sembollerle) derlenmiş olması gerekir. BeagleBoard'un kernel'leri böyle derler.
> - Overlay kurulduktan sonra GPIO 60'ı `/sys/class/gpio` ile export edemezsin; artık LED sürücüsüne aittir.

---

## 16.7 Özet

- LED'i GPIO'ya <b>seri direnç</b>le bağla: `R = (3.3 V − V_F) / I`, birkaç mA yeterli. Büyük yükler için transistör.
- Pinin GPIO modunda olduğunu `config-pin -q` ya da debugfs'teki `pins` dosyasıyla doğrula.
- Komut satırından: `/sys/class/gpio` veya libgpiod. C'den: kursun GPIO kütüphanesi (düzeltilmiş haliyle `code/lib/`).
- Program sonlanırken LED'i söndürüp GPIO'yu bırakmak için `SIGINT`'i yakala.
- LED'i device tree overlay ile `gpio-leds`'e bağlarsan kernel'in LED tetikleyicileri de kullanılabilir.

## 16.8 Karşılaşılabilecek Problemler

![Sık görülen hatalar (temsili)](../images/ext_led/05_errors.png)

| Belirti | Sebep | Çözüm |
|---|---|---|
| `value` 1 ama LED yanmıyor | LED ters, GND bağlı değil, yanlış header pini ya da pin GPIO modunda değil | Bacakları kontrol et; multimetreyle pinde 3.3 V ölç; [16.2](#162-pinin-gpio-modunda-olduğunu-doğrula) |
| LED çok soluk | Direnç büyük ya da LED mavi/beyaz (V<sub>F</sub> ~3 V) | 470 Ω kullan; mavi/beyaz LED'i transistörle sür |
| `export`: `Device or resource busy` | Pin bir overlay'de ya da başka sürücüde | `cat /sys/kernel/debug/gpio` ile kimin kullandığına bak |
| `Permission denied` | Program root olarak çalışmıyor | `sudo ./led_blink 60` ya da root olarak çalıştır |
| Ctrl-C sonrası LED yanık kaldı / sonraki çalıştırmada `export` hatası | Program sinyali yakalamadan sonlandı, GPIO export edilmiş kaldı | `echo 60 > /sys/class/gpio/unexport`; kendi programında `SIGINT`'i yakala |
| `config-pin: ... P9_12_pinmux/state failed` | cape-universal kapalı ya da pin bir overlay'de | Overlay kullanıyorsan beklenen durum; değilse `/boot/uEnv.txt`'de cape-universal'ı aç |
| `gpio_read_value()` hep 0 döndürüyor (kursun kodu) | Dosya `O_WRONLY` açılıp okunuyor | [16.4](#164-kursun-gpio-kütüphanesi)'teki düzeltilmiş kütüphane |
