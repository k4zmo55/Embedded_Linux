# Bölüm 15 — AM335x GPIO'ları, Pin Ayarları ve sysfs

> <b>Bu bölümde:</b>
> - AM335x'in GPIO alt sistemini ve GPIO numaralarının nasıl hesaplandığını öğreneceksin.
> - P8/P9 header'larında hangi pinlerin GPIO olarak kullanılabileceğini göreceksin.
> - Pin multiplexing'i (pinmux) ve pin ayar register'larının bitlerini çözeceksin.
> - Çalışan sistemde pinlerin durumunu sysfs/debugfs'ten okuyacaksın.
> - USER LED'leri ve GPIO'ları komut satırından, sonra da bir C programıyla kontrol edeceksin.
>
> <b>Ön koşul:</b> [Bölüm 1](01_bbb_hardware.md) — P8/P9 header'ları, [Bölüm 11](11_device_tree.md) — device tree ve pinctrl, [Bölüm 14](14_eclipse.md) — kartta program çalıştırma.

> [!NOTE]
> Bu bölümdeki komutlar kartta açık bir Linux'ta (eMMC'deki Debian ya da kendi rootfs'in) <b>root</b> olarak çalıştırılır. Debian'da `sudo -i` ile root olabilirsin. Terminal görüntüleri temsilidir; GPIO numaraları kernel 5.10'a göredir ([15.6](#156-gpioları-kullanıcı-alanından-kontrol-etmek)).

---

## 15.1 AM335x GPIO Alt Sistemi

AM335x'te <b>4 GPIO modülü (bankası)</b> vardır ve her biri <b>32 pin</b> yönetir. Toplam 128 GPIO:

| Banka | Register adresi | Linux'taki adı | Kernel 5.10'daki GPIO numaraları |
|---|---|---|---|
| GPIO0 | `0x44E07000` | `gpiochip0` | 0 – 31 |
| GPIO1 | `0x4804C000` | `gpiochip1` | 32 – 63 |
| GPIO2 | `0x481AC000` | `gpiochip2` | 64 – 95 |
| GPIO3 | `0x481AE000` | `gpiochip3` | 96 – 127 |

Datasheet ve şemalarda pinler <b>`GPIOx_y`</b> diye geçer: x banka, y bankadaki bit numarası. Linux'un eski GPIO numarası şöyle hesaplanır:

```
GPIO numarası = banka × 32 + bit

GPIO1_21 (USR0 LED)  →  1 × 32 + 21 =  53
GPIO1_28 (P9_12)     →  1 × 32 + 28 =  60
GPIO2_2  (P8_7)      →  2 × 32 +  2 =  66
```

Her GPIO modülü giriş/çıkış yönü, çıkış değeri, giriş okuma ve <b>kesme (interrupt)</b> için register'lar içerir. Linux'ta bu register'larla `gpio-omap` sürücüsü konuşur ([10.6](10_linux_kernel.md#106-soc-sürücülerinin-düzeni-drivers)); biz sürücünün kullanıcı alanına açtığı arayüzleri kullanacağız.

---

## 15.2 Genişleme Header'larındaki GPIO'lar

![BeagleBone Black P8/P9 header'larındaki GPIO pinleri](../images/gpio/bootlin_bbb_gpios.png)

*Görsel: Bootlin, "Embedded Linux system development" lab materyalleri (CC BY-SA 3.0)*

Görselde mor çerçeveli pinler, başka bir ayar yapmadan doğrudan GPIO olarak kullanılabilen pinlerdir. Sık kullanılanlar:

| Header pini | AM335x adı | GPIO no (5.10) | Pin ayar register'ı (`0x44E10000 +`) |
|---|---|---|---|
| P8_7 | GPIO2_2 | 66 | `0x890` |
| P8_12 | GPIO1_12 | 44 | `0x830` |
| P9_12 | GPIO1_28 | 60 | `0x878` |
| P9_15 | GPIO1_16 | 48 | `0x840` |
| USR0 – USR3 (kart üstü LED) | GPIO1_21 – GPIO1_24 | 53 – 56 | `0x854` – `0x860` |

> [!CAUTION]
> - Pinler <b>3.3V</b>'tur ve 5V toleranslı değildir ([1.9](01_bbb_hardware.md#19-genişleme-headerları-p8-ve-p9)).
> - Bir pin ancak birkaç mA akım verebilir. LED'i mutlaka seri dirençle bağla; röle, motor gibi yükleri transistör üzerinden sür.
> - P8_3 – P8_6, P8_20 – P8_25 <b>eMMC</b>'ye, P8_27 – P8_46 <b>HDMI</b>'ye bağlıdır. eMMC'yi veya HDMI'ı kapatmadan bu pinleri GPIO olarak kullanma.

---

## 15.3 Pin Multiplexing ve Pin Ayar Register'ları

AM335x'in her fiziksel pini <b>8 farklı görevden</b> birini üstlenebilir (mod 0 – mod 7). Örneğin P9_24 pini UART1'in TX'i, I2C1'in SCL'si ya da bir GPIO olabilir. Hangi görevin seçileceğine <b>pin multiplexing (pinmux)</b> denir. GPIO görevi her pinde <b>mod 7</b>'dir.

Pinmux, SoC'nin <b>Control Module</b>'ündeki pin ayar register'larıyla yapılır. Control Module `0x44E10000` adresindedir; pin register'ları `0x800` ofsetinden başlar ve her pinin kendi register'ı vardır (adı `conf_<modül>_<pin>`, ör. USR0 için `conf_gpmc_a5`, `0x44E10854`).

Register'ın bitleri (AM335x TRM, Control Module):

| Bit | Ad | Anlamı |
|---|---|---|
| 2:0 | `MUXMODE` | Mod 0 – 7. <b>7 = GPIO.</b> |
| 3 | `PULLUDEN` | <b>0 = pull direnci açık</b>, 1 = kapalı (ters mantık) |
| 4 | `PULLTYPESEL` | 0 = pull-down, 1 = pull-up |
| 5 | `RXACTIVE` | 1 = giriş tamponu açık (pin okunabilir). Giriş olarak kullanılacak pinlerde 1 olmalı. |
| 6 | `SLEWCTRL` | 0 = hızlı, 1 = yavaş kenar geçişi |

Örnekler:

| Değer | İkili | Anlamı |
|---|---|---|
| `0x07` | `000 0111` | Mod 7 (GPIO), pull-down, giriş kapalı. USER LED'ler böyle (sadece çıkış). |
| `0x27` | `010 0111` | Mod 7, pull-down, <b>giriş açık</b> |
| `0x37` | `011 0111` | Mod 7, <b>pull-up</b>, giriş açık. Butonlar için tipik. |

> [!IMPORTANT]
> Bu register'lar <b>kullanıcı alanından yazılamaz</b>: AM335x'te Control Module'e yazmak için işlemcinin ayrıcalıklı (privileged) modda olması gerekir. Pinmux bu yüzden <b>device tree</b>'de `pinctrl` düğümleriyle yapılır ([11.6](11_device_tree.md#116-önemli-propertyler)), kernel açılırken uygular. BeagleBoard'un Debian imajlarında hazır overlay'ler sayesinde `config-pin` aracıyla da değiştirilebilir (ör. `config-pin P9_12 gpio`, `config-pin -q P9_12`).

Device tree'de bir pin grubu şöyle tanımlanır (`am335x-bone-common.dtsi`'den, USER LED'ler):

```dts
user_leds_s0: user_leds_s0 {
	pinctrl-single,pins = <
		AM33XX_PADCONF(AM335X_PIN_GPMC_A5, PIN_OUTPUT_PULLDOWN, MUX_MODE7)	/* gpmc_a5.gpio1_21 */
		AM33XX_PADCONF(AM335X_PIN_GPMC_A6, PIN_OUTPUT_PULLUP, MUX_MODE7)	/* gpmc_a6.gpio1_22 */
		AM33XX_PADCONF(AM335X_PIN_GPMC_A7, PIN_OUTPUT_PULLDOWN, MUX_MODE7)	/* gpmc_a7.gpio1_23 */
		AM33XX_PADCONF(AM335X_PIN_GPMC_A8, PIN_OUTPUT_PULLUP, MUX_MODE7)	/* gpmc_a8.gpio1_24 */
	>;
};
```

`PIN_OUTPUT_PULLDOWN`, `MUX_MODE7` gibi isimler yukarıdaki bitlerin sabitleridir.

---

## 15.4 Çalışan Sistemde Pin Bilgisini Okumak

Kursun "Exploring Pin details using SYSFS entries" dersleri. Kernel, pinlerin ve GPIO'ların durumunu <b>debugfs</b>'ten (`/sys/kernel/debug`) okunabilir hale getirir. Boşsa önce bağla:

```bash
mount | grep debugfs || mount -t debugfs none /sys/kernel/debug
```

### GPIO'ların durumu

![/sys/kernel/debug/gpio](../images/gpio/02_gpio_debug.png)

```bash
cat /sys/kernel/debug/gpio
```

Her satır bir GPIO'yu, onu kullanan sürücüyü (ör. `beaglebone:green:usr0` LED sürücüsü), yönünü (`in`/`out`) ve değerini (`lo`/`hi`) gösterir.

### Pinmux durumu

![pinctrl debugfs girdileri](../images/gpio/03_pinctrl.png)

```bash
ls /sys/kernel/debug/pinctrl/
cd /sys/kernel/debug/pinctrl/44e10800.pinmux*/
grep 44e10854 pins          # USR0'ın pin register'ı ve değeri
grep "pin 21 " pinmux-pins  # bu pini hangi sürücü/grup kullanıyor?
```

| Dosya | İçinde ne var? |
|---|---|
| `pins` | Her pinin register adresi ve <b>şu anki değeri</b>. [15.3](#153-pin-multiplexing-ve-pin-ayar-registerları)'teki tabloyla çözülür. |
| `pinmux-pins` | Pini hangi sürücünün, hangi pin grubuyla aldığı |
| `pingroups` | Device tree'de tanımlı pin grupları ve içindeki pinler |

`pin 21 ... 44e10854 00000007` satırını çözelim: register `0x854` = `conf_gpmc_a5`, değer `0x07` = mod 7 (GPIO), pull-down, giriş kapalı. Yani USR0 bir GPIO çıkışı.

---

## 15.5 USER LED'leri sysfs ile Kontrol Etmek

Kursun "Controlling USER LEDs using SYSFS entries" dersleri. USER LED'ler kernel'in <b>LED alt sistemi</b> (`leds-gpio` sürücüsü) tarafından yönetilir ve `/sys/class/leds/` altında görünür. Her LED bir klasördür:

![USER LED'leri sysfs ile kontrol](../images/gpio/01_leds_sysfs.png)

| Dosya | Anlamı |
|---|---|
| `brightness` | `0` = sönük, `1` (veya `max_brightness`'a kadar) = yanık |
| `trigger` | LED'i kernel'de hangi olayın süreceği. `cat` ile okununca seçenekler listelenir, köşeli parantezdeki şu anki tetikleyicidir. |
| `delay_on`, `delay_off` | Sadece `timer` tetikleyicisinde görünür: yanık / sönük kalma süresi (ms) |

| Trigger | LED neye göre yanar? |
|---|---|
| `none` | Hiçbir şeye; `brightness`'a ne yazarsan |
| `heartbeat` | Kalp atışı gibi; sistem yükü arttıkça hızlanır |
| `timer` | `delay_on` / `delay_off` sürelerine göre yanıp söner |
| `oneshot` | `shot` dosyasına her yazılışta bir kez yanıp söner |
| `default-on` | Sürekli yanık |
| `mmc0`, `mmc1`, `cpu0`... | SD kart / eMMC erişimi, işlemci etkinliği |

```bash
cd /sys/class/leds/beaglebone:green:usr3
cat trigger
echo none > trigger
echo 1 > brightness                         # yak
echo 0 > brightness                         # söndür
echo timer > trigger
echo 100 > delay_on; echo 900 > delay_off   # 100 ms yanık, 900 ms sönük
echo mmc1 > trigger                         # varsayılana dön
```

> [!TIP]
> Bir tetikleyici aktifken `brightness`'a `1` yazarsan tetikleyici değeri hemen ezer. Önce `trigger`'ı `none` yap. (`brightness`'a `0` yazmak ise tetikleyiciyi kendiliğinden kapatır.)

---

## 15.6 GPIO'ları Kullanıcı Alanından Kontrol Etmek

USER LED'ler bir sürücüye ait. Header'daki boş bir GPIO'yu (ör. P9_12) kontrol etmek için iki arayüz var.

### a) sysfs GPIO arayüzü (kursta kullanılan)

![Eski sysfs GPIO arayüzü](../images/gpio/04_gpio_sysfs_legacy.png)

```bash
echo 60 > /sys/class/gpio/export             # GPIO 60'ı (P9_12) kullanıcı alanına aç
echo out > /sys/class/gpio/gpio60/direction  # çıkış
echo 1 > /sys/class/gpio/gpio60/value        # 3.3 V
echo 0 > /sys/class/gpio/gpio60/value        # 0 V
echo 60 > /sys/class/gpio/unexport           # bırak
```

| Dosya | Anlamı |
|---|---|
| `direction` | `in` / `out` (`high` / `low` yazmak çıkış yapıp değeri de ayarlar) |
| `value` | Okunan veya yazılan değer |
| `edge` | Giriş için kesme: `none`, `rising`, `falling`, `both` (`poll()` ile beklenir) |
| `active_low` | `1` ise mantık terslenir |

> [!WARNING]
> Bu arayüz kernel'de <b>eskimiş (deprecated)</b> olarak işaretlidir. BeagleBoard'un 5.10 kernel'inde hâlâ açık (`CONFIG_GPIO_SYSFS=y`) ve banka numaraları sabit (0, 32, 64, 96). Ama güncel mainline kernel'lerde (ör. [Bölüm 13](13_buildroot.md)'teki {{buildroot.kernel_version}}) GPIO numaraları <b>dinamik</b> verilir ve genelde 512'den başlar: `echo 60 > export` orada başka bir pine denk gelir ya da hata verir. Doğru numarayı `cat /sys/kernel/debug/gpio` veya `ls /sys/class/gpio/` (`gpiochipNNN` = bankanın ilk numarası) ile bul. Yeni projelerde aşağıdaki libgpiod'u kullan.

### b) libgpiod (güncel yöntem)

Kernel'in karakter aygıtı arayüzünü (`/dev/gpiochipN`) kullanır. GPIO'yu <b>banka + bit</b> ile adresler; numara hesabı ve kernel sürümü farkı yoktur. Debian'da `sudo apt install gpiod`, Buildroot'ta *Target packages → Libraries → Hardware handling → libgpiod* (araçlarla birlikte).

![libgpiod araçları](../images/gpio/05_libgpiod.png)

| Araç | Görevi |
|---|---|
| `gpiodetect` | GPIO bankalarını listeler |
| `gpioinfo` | Her hattın adı, yönü ve kim tarafından kullanıldığı |
| `gpioget` | Girişi okur |
| `gpioset` | Çıkışı ayarlar |
| `gpiomon` | Kenar (edge) olaylarını bekler |

libgpiod'un iki sürümünün komut sözdizimi farklıdır:

| İş | libgpiod 1.x (Debian 10/11/12) | libgpiod 2.x (Debian 13 ve sonrası) |
|---|---|---|
| P9_12'yi 1 yap | `gpioset gpiochip1 28=1` | `gpioset -c gpiochip1 28=1` (Ctrl-C'ye kadar tutar) |
| P9_12'yi oku | `gpioget gpiochip1 28` | `gpioget -c gpiochip1 28` |
| Sürümü öğren | `gpioset --version` | `gpioset --version` |

---

## 15.7 C Programıyla USER LED Kontrolü

Kursun "Controlling user LEDs using 'C' Application" dersleri ve repodaki `BBB_led_control` projesi ([14.7](14_eclipse.md#147-kursun-projelerini-eclipsee-aktarmak)). Program, [15.5](#155-user-ledleri-sysfs-ile-kontrol-etmek)'teki `echo` komutlarının aynısını C'de `open()` + `write()` ile yapar.

### Kursun kodundaki hata

Kursun `write_brightness_values()` fonksiyonu değeri şöyle yazıyor:

```c
ret = write(fd, (void *)&value, sizeof(value));   /* value bir int */
```

Bu satır `1` sayısının bellekteki <b>4 ham baytını</b> (`01 00 00 00`) yazar. Oysa sysfs dosyaları `echo`'nun yazdığı gibi <b>metin</b> bekler: `"1"`. Kernel gelen veriyi sayıya çeviremez, `write()` hata döner ve program `trigger value write error` basar. `trigger` kısmı metin yazdığı için çalışır, `brightness` kısmı çalışmaz. Ayrıca açılan dosyalar hiç kapatılmıyor.

Doğrusu, değeri metin olarak yazmak:

```c
write(fd, "1", 1);
```

### Düzeltilmiş ve genelleştirilmiş program

Kursun "TODO" notundaki öneriye uygun olarak program dört LED'in hepsini destekleyecek şekilde genişletildi. Tam kod: [`code/15_gpio/usr_led.c`](../code/15_gpio/usr_led.c).

```c
#define LED_ATTR_PATH "/sys/class/leds/beaglebone:green:usr%d/%s"

/* /sys/class/leds/beaglebone:green:usr<led>/<attr> dosyasına value'yu yazar. */
static int write_attr(int led, const char *attr, const char *value)
{
	char path[128];
	ssize_t n;
	int fd;

	snprintf(path, sizeof(path), LED_ATTR_PATH, led, attr);

	fd = open(path, O_WRONLY);
	if (fd < 0) {
		perror(path);
		return -1;
	}

	n = write(fd, value, strlen(value));   /* metin olarak: "1", "timer" ... */
	if (n < 0)
		perror("write");

	close(fd);
	return n < 0 ? -1 : 0;
}
```

`main()`, argümanları kontrol eder ve `write_attr(led, "trigger", value)` ya da `write_attr(led, "brightness", value)` çağırır.

### Derle ve çalıştır

Eclipse ile ([14.4](14_eclipse.md#144-birinci-proje-oluşturma-ve-derleme)) ya da terminalden:

![LED programını derleme ve kartta çalıştırma](../images/gpio/06_led_app.png)

```bash
{{build.cross_compile}}gcc -Wall -o usr_led code/15_gpio/usr_led.c
scp usr_led debian@{{network.board_ip}}:~/
```

Kartta (root olarak):

```bash
./usr_led 3 trigger none
./usr_led 3 brightness 1
./usr_led 3 trigger heartbeat
```

---

## 15.8 Özet

- AM335x: 4 GPIO bankası × 32 pin. `GPIOx_y` → kernel 5.10'da numara `x × 32 + y`; yeni kernel'lerde numara dinamik.
- Her pinin 8 modu var; GPIO = mod 7. Pin ayar register'ı `0x44E10800`'den başlar: mod, pull-up/down, giriş açık/kapalı. Kullanıcı alanından yazılamaz; device tree (`pinctrl`) ya da `config-pin` ile ayarlanır.
- Durumu okumak: `/sys/kernel/debug/gpio`, `/sys/kernel/debug/pinctrl/.../pins`.
- USER LED'ler: `/sys/class/leds/beaglebone:green:usrN/{trigger,brightness}`.
- Boş GPIO'lar: eski `/sys/class/gpio` (kursta) ya da güncel <b>libgpiod</b> (`gpioset`/`gpioget`).
- sysfs'e C'den yazarken değer <b>metin</b> olmalı.

## 15.9 Karşılaşılabilecek Problemler

![Sık görülen hatalar (temsili)](../images/gpio/07_errors.png)

| Belirti | Sebep | Çözüm |
|---|---|---|
| `Permission denied` (`echo ... > brightness`) | Kullanıcı root değil; `sudo echo 1 > dosya` da çalışmaz (yönlendirmeyi kabuk yapar) | `sudo -i` ile root ol ya da `echo 1 \| sudo tee dosya` |
| `export`: `Device or resource busy` | Pin başka bir sürücüde (ör. LED, eMMC) ya da zaten export edilmiş | `cat /sys/kernel/debug/gpio` ile kimin kullandığına bak |
| `export`: `Invalid argument` | Yeni kernel'de GPIO numaraları 512'den başlıyor | Doğru numarayı `/sys/kernel/debug/gpio`'dan bul ya da libgpiod kullan |
| Pine `1` yazıyorum ama voltaj yok | Pin GPIO modunda değil (pinmux) | `pins` dosyasında register değerinin mod 7 olduğunu kontrol et; değilse `config-pin` / device tree |
| Giriş hep aynı değeri okuyor | `RXACTIVE` kapalı ya da pin boşta ve pull direnci yok | Pin ayarını `0x27`/`0x37` yap; butonda pull-up/down kullan |
| `brightness` yazılıyor ama LED hemen eski haline dönüyor | Tetikleyici (`heartbeat`, `mmc1`) aktif | Önce `echo none > trigger` |
| Kursun programı `trigger value write error` basıyor | Değer metin değil, ham bayt olarak yazılıyor | [15.7](#157-c-programıyla-user-led-kontrolü)'deki düzeltilmiş kod |
| `/sys/kernel/debug` boş | debugfs bağlı değil | `mount -t debugfs none /sys/kernel/debug` |
| `gpioset: invalid option -- 'c'` / `unable to request lines` | libgpiod 1.x ile 2.x sözdizimi karıştı | `gpioset --version` ile sürüme bak, [15.6](#156-gpioları-kullanıcı-alanından-kontrol-etmek)'daki tabloya göre yaz |
