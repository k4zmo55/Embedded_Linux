<!-- Bu dosya otomatik üretildi. Düzenlemek için chapters/ altındaki kaynağı değiştir. -->
# Bölüm 11 — Linux Device Tree

> <b>Bu bölümde:</b>
> - Kernel'in, kendini tanıtmayan donanımı (UART, I2C, GPIO...) nereden öğrendiğini anlayacaksın.
> - DTS, DTSI, DTB, DTBO dosyalarını ve `dtc` derleyicisini tanıyacaksın.
> - Device tree söz dizimini, `compatible` ile driver eşleşmesini ve BeagleBone Black'in include zincirini göreceksin.
> - Çalışan sistemde device tree'yi `/proc/device-tree` altından inceleyeceksin.
>
> <b>Ön koşul:</b> [Bölüm 3](03_boot_process.md) — boot zinciri, [Bölüm 4](04_sd_card_boot.md) — U-Boot'un DTB'yi RAM'e yüklemesi.

---

## 11.1 Problem: Kernel Donanımı Nereden Bilecek?

Kernel'in çalışabilmesi için kartta <b>hangi donanımların olduğunu, nerede durduklarını ve nasıl bağlandıklarını</b> bilmesi gerekir. Örneğin:

- UART denetleyicisinin register'ları hangi adreste?
- Kaç MB RAM var, hangi adresten başlıyor?
- I2C hattına hangi çip, hangi adresle bağlı?
- USR0 LED'i hangi GPIO pinine bağlı?
- Hangi cihaz hangi interrupt hattını kullanıyor?

### Keşfedilebilen ve keşfedilemeyen donanım

| | Keşfedilebilir (discoverable) | Keşfedilemez (non-discoverable) |
|---|---|---|
| <b>Örnek</b> | PCI, PCIe, USB | UART, I2C, SPI, GPIO, Ethernet MAC, NAND, SoC içindeki çoğu çevre birimi |
| <b>Nasıl bulunur?</b> | Cihaz kendini tanıtır (Vendor ID / Device ID). Kernel bus'ı tarayarak bulur. | Cihaz kendini tanıtmaz. Kernel'e <b>birinin söylemesi gerekir</b>. |

Masaüstü PC'lerde (x86) bu bilgi BIOS/UEFI tarafından <b>ACPI tabloları</b> ile verilir. Gömülü sistemlerde (ARM, RISC-V, PowerPC) ise donanımın büyük kısmı SoC'un içinde, belirli adreslerde duran ve kendini tanıtmayan bloklardır. Bu yüzden bu bilgiyi kernel'e bir şekilde aktarmak gerekir.

### Eski yöntem: board file'lar

Device Tree'den önce ARM'da her kart için kernel kaynak kodunda bir C dosyası (<b>board file</b>) yazılırdı (`arch/arm/mach-xxx/board-yyy.c`). Donanım bilgisi bu dosyalara sabit olarak gömülürdü:

```c
/* Eski usül: donanım C koduna gömülü (temsili örnek) */
static struct resource uart0_resources[] = {
    { .start = 0x44E09000, .end = 0x44E09FFF, .flags = IORESOURCE_MEM },
    { .start = 72,         .end = 72,         .flags = IORESOURCE_IRQ },
};
```

Bu yöntemin sorunları:

- Her yeni kart = kernel'e yeni C kodu. `arch/arm` altında binlerce kart dosyası birikti.
- Kartta küçük bir değişiklik (ör. LED'in başka pine taşınması) bile <b>kernel'i yeniden derlemeyi</b> gerektiriyordu.
- Her kart için ayrı bir kernel image'ı gerekiyordu. <b>Tek bir kernel, birden fazla kartta çalışamıyordu.</b>

![Linus Torvalds'ın ARM board file karmaşası hakkındaki e-postası](../images/{142EA865-24C8-4CD5-AA3D-0C747F50EB5D}.png)

2011'de Linus Torvalds ARM tarafındaki bu karmaşadan açıkça şikayet etti. Bunun üzerine ARM dünyası, PowerPC'de zaten kullanılan <b>Device Tree</b>'ye geçti (kernel 3.x serisi). Bugün yeni ARM32 ve ARM64 kartları için Device Tree zorunludur.

> [!NOTE]
> Temel fikir: <b>Donanım tarifi koddan ayrılır.</b> Kernel aynı kalır, kartı tarif eden küçük bir veri dosyası (DTB) değişir. Böylece aynı `zImage` hem BeagleBone Black'te hem de başka bir AM335x kartında çalışabilir. Sadece DTB farklıdır.

---

## 11.2 Device Tree Nedir?

<b>Device Tree (DT)</b>, bir sistemdeki donanımı tarif eden, <b>ağaç (tree) şeklinde bir veri yapısıdır</b>.

- Ağaç <b>node</b>'lardan (düğüm) oluşur. Her node bir donanım bloğunu temsil eder (CPU, bellek, UART, I2C denetleyicisi, EEPROM...).
- Her node'un <b>property</b>'leri (özellikleri) vardır: adres, interrupt numarası, uyumlu driver adı, durum vb.
- Node'lar iç içe olabilir. Bir I2C denetleyicisinin altında ona bağlı I2C cihazları alt node olarak yer alır. Bu, donanımdaki <b>fiziksel bağlantı hiyerarşisini</b> yansıtır.
- Kökeni Sun'ın <b>OpenFirmware</b> standardına dayanır. Bugün <b>devicetree.org</b> tarafından [Devicetree Specification](https://www.devicetree.org/specifications/) olarak standartlaştırılmıştır.
- <b>İşletim sisteminden bağımsızdır</b>: Linux, U-Boot, FreeBSD, Zephyr gibi projeler de kullanır.

> [!IMPORTANT]
> Device Tree <b>donanımın ne olduğunu</b> tarif eder, <b>nasıl kullanılacağını</b> değil. "Bu kartta 0x44E09000 adresinde bir UART var" bir DT bilgisidir. "Bu UART'ı 115200 baud ile konsol olarak kullan" ise bir yapılandırma tercihidir ve genelde kernel command line'a (`bootargs`) aittir.

Device Tree'de olmayan bir şey kernel tarafından <b>bilinemez</b>. Driver kernel'e derlenmiş olsa bile, DT'de ona uyan bir node yoksa o driver hiç çalışmaz (probe edilmez).

---

## 11.3 Dosya Türleri: DTS, DTSI, DTC, DTB, DTBO

![Device Tree: kaynaktan blob'a (DTS → dtc → DTB)](../images/device_tree/dts_to_dtb.png)

*Görsel: Bootlin, "Linux kernel and driver development" eğitim slaytları (CC BY-SA 3.0)*

| Kısaltma | Açılımı | Ne? |
|---|---|---|
| <b>DT</b> | Device Tree | Genel kavram: donanımı tarif eden ağaç yapısı |
| <b>.dts</b> | Device Tree <b>Source</b> | İnsanın okuyup yazabildiği <b>metin</b> kaynak dosyası. Bir kartı tarif eder. Örn: `am335x-boneblack.dts` |
| <b>.dtsi</b> | Device Tree Source <b>Include</b> | Başka dosyalara `#include` edilen ortak parça. Genelde SoC'u ya da bir kart ailesini tarif eder. Örn: `am33xx.dtsi`. C'deki `.h` dosyalarına benzer. |
| <b>dtc</b> | Device Tree <b>Compiler</b> | `.dts` dosyasını `.dtb`'ye derleyen (ve tersini yapabilen) araç |
| <b>.dtb</b> | Device Tree <b>Blob</b> (Binary) | Derlenmiş, <b>ikili (binary)</b> çıktı. Bootloader bunu RAM'e yükler ve kernel bunu okur. Örn: `am335x-boneblack.dtb` |
| <b>FDT</b> | Flattened Device Tree | DTB'nin bellekteki "düzleştirilmiş" formatının adı. U-Boot'taki `fdt` komutu ve `fdtaddr` değişkeni buradan gelir. |
| <b>.dtbo</b> | Device Tree Blob <b>Overlay</b> | Var olan bir DTB'ye çalışma/boot anında eklenen <b>yama</b>. Cape/HAT gibi eklenti kartlar için kullanılır. ([11.12](#1112-device-tree-overlay-dtbo)) |

### Derleme akışı

```
am33xx.dtsi ─┐
am335x-bone-common.dtsi ─┤  #include
am335x-boneblack-common.dtsi ─┤
                              ▼
            am335x-boneblack.dts
                    │
                    │  1) C preprocessor (cpp): #include, #define çözülür
                    │  2) dtc: metin → binary
                    ▼
            am335x-boneblack.dtb   (~60-70 KB)
                    │
                    │  U-Boot RAM'e yükler (fdtaddr)
                    ▼
                 Linux kernel
```

- Kernel kaynak ağacında `.dts` dosyaları önce <b>C ön işlemcisinden (cpp)</b> geçer. Bu sayede `#include <dt-bindings/gpio/gpio.h>` ve `GPIO_ACTIVE_HIGH` gibi sabitler kullanılabilir. Sonra `dtc` ile derlenir.
- DTB küçüktür (birkaç on KB) ve kernel'in hızlıca okuyabileceği bir formattadır.
- Her DTB dosyası <b>`0xd00dfeed`</b> sihirli sayısı (magic number) ile başlar. Bir dosyanın gerçekten DTB olup olmadığını böyle anlayabilirsin:

```bash
$ hexdump -C am335x-boneblack.dtb | head -1     # ilk 4 byte: d0 0d fe ed
00000000  d0 0d fe ed 00 01 0a 5c  00 00 00 38 00 00 f8 a8  |.......\...8....|
```

> [!NOTE]
> Kernel tarafındaki `.dts` dosyaları kernel kaynak kodunun içindedir: ARM32 için `arch/arm/boot/dts/`, ARM64 için `arch/arm64/boot/dts/<vendor>/`. Kernel 6.5'ten itibaren ARM32 dosyaları da vendor klasörlerine taşındı. BeagleBone Black'in dosyası yeni kernel'lerde `arch/arm/boot/dts/ti/omap/am335x-boneblack.dts` konumundadır.

---

## 11.4 Söz Dizimi (Syntax)

![Device Tree temel söz dizimi](../images/device_tree/dt_temel_soz_dizimi.png)

*Görsel: Bootlin eğitim materyalleri (CC BY-SA 3.0)*

### Node

```dts
[label:] node-name[@unit-address] {
    [properties]
    [child nodes]
};
```

| Parça | Açıklama | Örnek |
|---|---|---|
| <b>`/`</b> | Kök (root) node. Her DT'de bir tane vardır ve tüm sistemi temsil eder. | `/ { ... };` |
| <b>node-name</b> | Cihazın <b>türünü</b> anlatan genel bir isim | `serial`, `i2c`, `gpio`, `memory`, `eeprom` |
| <b>@unit-address</b> | Node'un adresi. Genelde `reg` property'sinin ilk değeriyle aynıdır. | `serial@44e09000`, `eeprom@50` |
| <b>label</b> | Node'a verilen takma ad. Başka yerlerden `&label` diye referans verilir. | `uart0: serial@44e09000` |
| <b>`;`</b> | Her node ve property `;` ile biter. Unutmak en sık yapılan derleme hatasıdır. | |

Bir node'un tam yolu (path) dosya sistemi yoluna benzer: `/ocp/interconnect@44c00000/.../serial@0`.

### Property

Property'ler `isim = değer;` şeklindedir. Değer türleri:

| Tür | Yazım | Örnek |
|---|---|---|
| <b>Boş (boolean)</b> | Sadece isim. Varsa "true", yoksa "false" demektir. | `gpio-controller;` |
| <b>String</b> | Çift tırnak | `status = "okay";` |
| <b>String listesi</b> | Virgülle ayrılmış string'ler | `compatible = "ti,am3352-uart", "ti,omap3-uart";` |
| <b>Cell (u32) listesi</b> | `< >` içinde 32-bit sayılar | `reg = <0x44e09000 0x2000>;` |
| <b>Byte dizisi</b> | `[ ]` içinde hex byte'lar | `local-mac-address = [00 11 22 33 44 55];` |
| <b>phandle (referans)</b> | `< >` içinde `&label` | `gpios = <&gpio1 21 GPIO_ACTIVE_HIGH>;` |

> [!TIP]
> <b>phandle</b>, bir node'un başka bir node'a "işaretçi" (pointer) gibi referans vermesidir. Yukarıdaki `gpios` örneği şunu söyler: "Bu LED, `gpio1` denetleyicisinin <b>21.</b> pinine bağlı ve <b>active-high</b>." dtc derleme sırasında `&gpio1`'i o node'a ait benzersiz bir sayıya (phandle) çevirir.

---

## 11.5 Bir Device Tree'nin Genel Yapısı

![DT genel yapısı: kod ve donanım karşılığı](../images/device_tree/dt_genel_yapi.png)

*Görsel: Bootlin eğitim slaytları (CC BY-SA 3.0). Soldaki ağaç, sağdaki AM335x tabanlı donanımı tarif ediyor.*

Görseldeki eşleşmeye dikkat et: DT'deki iç içe yapı <b>donanımdaki bağlantıyı</b> birebir yansıtır. EEPROM, I2C denetleyicisine bağlı olduğu için DT'de de `i2c@40012000` node'unun <b>altındadır</b>.

Hemen her DT'de bulunan standart node'lar:

| Node | Görevi |
|---|---|
| <b>`/`</b> | Kök. `model` (kartın adı) ve `compatible` (kartın kimliği) burada tanımlanır. |
| <b>`cpus`</b> | İşlemci çekirdekleri (BBB'de tek bir Cortex-A8) |
| <b>`memory@...`</b> | RAM'in başlangıç adresi ve boyutu |
| <b>`chosen`</b> | Donanım değil, bootloader ile kernel arasındaki bilgiler: `bootargs`, `stdout-path` (konsol) |
| <b>`aliases`</b> | Kısa isimler. Örn: `serial0 = &uart0;` sayesinde `uart0` → `/dev/ttyS0` olur. |
| <b>`ocp` / `soc`</b> | SoC içindeki çevre birimlerinin bulunduğu bus. AM335x'te adı `ocp`'dir (On-Chip Peripherals). |

### BeagleBone Black'ten gerçek bir örnek

BBB'nin ana DTS dosyası aslında çok kısadır. Asıl iş include ettiği dosyalardadır:

```dts
/* am335x-boneblack.dts (kısaltılmış) */
/dts-v1/;

#include "am33xx.dtsi"                    /* AM335x SoC tanımı */
#include "am335x-bone-common.dtsi"        /* Tüm BeagleBone'larda ortak */
#include "am335x-boneblack-common.dtsi"   /* BBB ve BBB Wireless'ta ortak */
#include "am335x-boneblack-hdmi.dtsi"     /* HDMI desteği */

/ {
	model = "TI AM335x BeagleBone Black";
	compatible = "ti,am335x-bone-black", "ti,am335x-bone", "ti,am33xx";
};
```

`am335x-bone-common.dtsi` içinden USR LED tanımı (kısaltılmış):

```dts
leds {
	pinctrl-names = "default";
	pinctrl-0 = <&user_leds_s0>;      /* pin mux ayarı */
	compatible = "gpio-leds";         /* hangi driver? → leds-gpio */

	led2 {
		label = "beaglebone:green:usr0";
		gpios = <&gpio1 21 GPIO_ACTIVE_HIGH>;    /* GPIO1_21 pini */
		linux,default-trigger = "heartbeat";    /* kalp atışı gibi yanıp söner */
		default-state = "off";
	};
	/* usr1, usr2, usr3 ... */
};
```

> [!TIP]
> Kart açıldığında USR0 LED'inin "kalp atışı" gibi yanıp sönmesinin sebebi tam olarak bu satırdır: `linux,default-trigger = "heartbeat";`. Yani bu davranış kernel kodunda değil, <b>Device Tree'de</b> tanımlıdır.

---

## 11.6 Önemli Property'ler

| Property | Anlamı | Örnek |
|---|---|---|
| <b>`compatible`</b> | <b>En önemli property.</b> Cihazın ne olduğunu ve hangi driver'ın onu yöneteceğini belirler. Format: `"üretici,model"`. En özelden en genele doğru sıralanır. | `"ti,am3352-uart", "ti,omap3-uart"` |
| <b>`reg`</b> | Cihazın adresi. Memory-mapped cihazlarda <b>(başlangıç adresi, boyut)</b> çifti. I2C/SPI cihazlarında bus üzerindeki adres. | `reg = <0x44e09000 0x2000>;` <br> `reg = <0x50>;` |
| <b>`#address-cells`</b> | Alt node'ların `reg` değerindeki <b>adresin</b> kaç adet 32-bit cell olduğu | `<1>` |
| <b>`#size-cells`</b> | Alt node'ların `reg` değerindeki <b>boyutun</b> kaç cell olduğu. I2C'de boyut yoktur, bu yüzden `<0>`. | `<1>` veya `<0>` |
| <b>`status`</b> | Cihaz kullanılıyor mu? `"okay"` → evet, `"disabled"` → hayır (driver probe edilmez). | `status = "okay";` |
| <b>`interrupts`</b> | Cihazın kullandığı interrupt hattı | `interrupts = <72>;` |
| <b>`interrupt-parent`</b> | Interrupt'ın hangi interrupt denetleyicisine gittiği (phandle) | `<&intc>` |
| <b>`clocks`</b> | Cihazın beslendiği saat (clock) kaynakları | `clocks = <&l4ls_gclk>;` |
| <b>`pinctrl-0`, `pinctrl-names`</b> | Pin multiplexing: SoC pinlerinin bu cihaz için hangi moda alınacağı | `pinctrl-0 = <&uart0_pins>;` |
| <b>`gpios`, `*-gpios`</b> | Kullanılan GPIO pinleri (phandle + pin no + flag) | `<&gpio1 21 GPIO_ACTIVE_HIGH>` |

### reg, #address-cells ve #size-cells ilişkisi

`reg`'in nasıl okunacağını <b>parent node'daki</b> `#address-cells` ve `#size-cells` belirler:

```dts
ocp {
	#address-cells = <1>;   /* alt node'larda adres = 1 cell */
	#size-cells = <1>;      /* alt node'larda boyut = 1 cell */

	serial@44e09000 {
		reg = <0x44e09000 0x2000>;   /* adres=0x44E09000, boyut=8 KB */
	};
};

i2c0: i2c@44e0b000 {
	#address-cells = <1>;
	#size-cells = <0>;      /* I2C cihazlarının "boyutu" yok */

	baseboard_eeprom: eeprom@50 {
		compatible = "atmel,24c256";
		reg = <0x50>;       /* I2C adresi 0x50 */
	};
};
```

> [!NOTE]
> BBB'nin üzerindeki <b>EEPROM</b> (kart adını ve seri numarasını tutan çip) gerçekten de I2C0 hattında <b>0x50</b> adresindedir. U-Boot bu EEPROM'u okuyarak kartın BeagleBone Black olduğunu anlar ve doğru DTB'yi (`am335x-boneblack.dtb`) seçer.

---

## 11.7 compatible ile Driver Eşleşmesi

Kernel DTB'yi okuduğunda her node için bir <b>device</b> oluşturur. Sonra her device için `compatible` string'ine bakar ve <b>aynı string'i destekleyen bir driver</b> arar. Eşleşme bulunursa driver'ın `probe()` fonksiyonu çağrılır ve cihaz o driver'a <b>bağlanır (bind)</b>.

![compatible property ve kernel driver eşleşmesi](../images/device_tree/dt_compatible_driver.png)

*Görsel: Bootlin eğitim slaytları (CC BY-SA 3.0)*

- Kök node'un hemen altındaki ve `simple-bus` altındaki node'lar → <b>platform device</b> olur.
- I2C denetleyicisinin altındaki node'lar → <b>I2C device</b> olur.
- SPI denetleyicisinin altındaki node'lar → <b>SPI device</b> olur.

Driver tarafında bu eşleşme `of_device_id` tablosu ile yapılır (`of` = OpenFirmware):

```c
/* drivers/i2c/busses/i2c-omap.c (kısaltılmış) */
static const struct of_device_id omap_i2c_of_match[] = {
	{ .compatible = "ti,omap4-i2c", .data = &omap4_pdata },
	{ .compatible = "ti,omap3-i2c", .data = &omap3_pdata },
	{ },
};
MODULE_DEVICE_TABLE(of, omap_i2c_of_match);

static struct platform_driver omap_i2c_driver = {
	.probe  = omap_i2c_probe,
	.remove = omap_i2c_remove,
	.driver = {
		.name           = "omap_i2c",
		.of_match_table = omap_i2c_of_match,   /* DT eşleşme tablosu */
	},
};
```

```
DT node:   compatible = "ti,omap4-i2c"
                    │
                    │  string eşleşmesi
                    ▼
Driver:    { .compatible = "ti,omap4-i2c" }  →  omap_i2c_probe() çağrılır
```

Driver `probe()` içinde `reg`, `interrupts`, `clocks` gibi property'leri okuyarak cihazı başlatır (`platform_get_resource()`, `of_property_read_u32()` vb.).

> [!TIP]
> `compatible` listesinde birden fazla string olmasının sebebi <b>geriye dönük uyumluluktur</b>. `"ti,am3352-uart", "ti,omap3-uart"` şunu söyler: "Ben aslında AM3352 UART'ıyım. Bana özel driver yoksa OMAP3 UART driver'ı da beni sürebilir." Kernel listeyi soldan sağa dener.

> [!NOTE]
> Bir cihazın property'lerinin nasıl yazılacağı (hangi property zorunlu, hangi değerler geçerli) <b>binding</b> denen belgelerle tanımlanır. Bunlar kernel'de `Documentation/devicetree/bindings/` altındadır ve günümüzde YAML formatındadır. Yeni bir cihaz eklerken ilk bakılacak yer burasıdır.

---

## 11.8 Kalıtım: .dtsi, include ve Label ile Override

Aynı SoC'u kullanan onlarca kart vardır. Her kart için SoC'un tamamını baştan yazmak yerine:

1. SoC'un tüm çevre birimleri bir <b>`.dtsi`</b> dosyasında tanımlanır. Çoğu `status = "disabled"` olarak bırakılır.
2. Kartın <b>`.dts`</b> dosyası bu `.dtsi`'yi include eder. Kartta kullanılan birimleri `status = "okay"` yaparak açar ve karta özel cihazları (EEPROM, LED, PMIC...) ekler.

Aynı node birden fazla kez tanımlanırsa dtc bunları <b>birleştirir</b>. Aynı property iki yerde varsa <b>sonra gelen kazanır</b>.

### BeagleBone Black'in include zinciri

![BeagleBone Black Device Tree kalıtım yapısı](../images/device_tree/dt_bbb_inheritance.png)

*Görsel: Bootlin eğitim slaytları (CC BY-SA 3.0)*

| Dosya | Seviye | İçerik |
|---|---|---|
| `am33xx.dtsi` | SoC | AM335x işlemcinin genel tanımı. `am33xx-l4.dtsi` (çevre birimleri) ve `am33xx-clocks.dtsi` (saatler) dosyalarını include eder. |
| `am335x-bone-common.dtsi` | Kart ailesi | Tüm BeagleBone'larda ortak olanlar: LED'ler, EEPROM, PMIC (TPS65217), 256 MB RAM |
| `am335x-boneblack-common.dtsi` | Kart ailesi | BBB ve BBB Wireless'ta ortak olanlar: eMMC, 512 MB RAM |
| `am335x-boneblack-hdmi.dtsi` | Ek özellik | HDMI çıkışı (TDA19988 çipi) |
| `am335x-boneblack.dts` | Kart | Sadece BBB'ye özel olanlar: `model`, `compatible` |

Override'a güzel bir örnek RAM boyutudur. `am335x-bone-common.dtsi` RAM'i 256 MB tanımlar (eski BeagleBone White'ta 256 MB vardı). `am335x-boneblack-common.dtsi` aynı node'u tekrar yazarak bunu 512 MB'a çıkarır:

```dts
/* am335x-bone-common.dtsi */
memory@80000000 {
	device_type = "memory";
	reg = <0x80000000 0x10000000>;   /* 256 MB */
};

/* am335x-boneblack-common.dtsi (sonra include edildiği için kazanır) */
memory@80000000 {
	device_type = "memory";
	reg = <0x80000000 0x20000000>;   /* 512 MB */
};
```

### Label ile override (tercih edilen yöntem)

Bir node'u değiştirmek için tam yolunu tekrar yazmak yerine, <b>label</b>'ı ile doğrudan ona erişmek tercih edilir:

![Label ile override](../images/device_tree/dt_label_override.png)

*Görsel: Bootlin eğitim slaytları (CC BY-SA 3.0). Soldaki ve sağdaki board.dts tamamen aynı sonucu üretir. Sağdaki `&uart0 { ... };` yazımı tercih edilir.*

```dts
/* Kart dosyasında: SoC'ta "disabled" olan I2C2'yi aç ve hızını ayarla */
&i2c2 {
	status = "okay";
	clock-frequency = <100000>;
};
```

---

## 11.9 dtc Kullanımı

![dtc ile derleme ve geri derleme örneği](../images/device_tree/dtc_ornek.png)

*Görsel: Bootlin eğitim slaytları (CC BY-SA 3.0)*

### Kurulum

```bash
sudo apt install device-tree-compiler
```

### Temel komutlar

```bash
# DTS → DTB (derleme)
dtc -I dts -O dtb -o foo.dtb foo.dts

# DTB → DTS (geri derleme / decompile)
dtc -I dtb -O dts -o foo_geri.dts foo.dtb

# Çalışan sistemin canlı device tree'sini DTS olarak dök
dtc -I fs -O dts /proc/device-tree
```

| Parametre | Anlamı |
|---|---|
| `-I` | Girdi formatı: `dts`, `dtb` veya `fs` (dosya sistemi, ör. `/proc/device-tree`) |
| `-O` | Çıktı formatı: `dts`, `dtb` veya `asm` |
| `-o` | Çıktı dosyası |
| `-@` | Label'ları (`__symbols__`) DTB'ye ekle. Overlay kullanılacaksa gereklidir. |

> [!TIP]
> Geri derleme (`-I dtb -O dts`) çok işe yarar: Elinde sadece bir `.dtb` varsa (ör. hazır bir image'dan çıkan) içinde ne olduğunu görebilirsin. Ancak çıkan DTS'te yorumlar, `#include`'lar, `#define` isimleri ve label'lar kaybolmuştur. Sayılar ham hex olarak görünür (`GPIO_ACTIVE_HIGH` yerine `0x00` gibi).

### Kernel kaynak ağacında DTB derleme

Kernel'in içindeki `.dts` dosyaları elle `dtc` çağırmak yerine kernel'in build sistemiyle derlenir. Bu yöntem cpp ön işleme adımını da otomatik yapar:

```bash
# Tüm DTB'leri derle (kernel kaynak klasöründe)
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- dtbs

# Sadece BBB'nin DTB'sini derle (kernel 6.5+ yol yapısı)
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- ti/omap/am335x-boneblack.dtb

# Çıktı:
#   arch/arm/boot/dts/ti/omap/am335x-boneblack.dtb
```

> [!NOTE]
> Kernel 6.5'ten eski sürümlerde hedef sadece `am335x-boneblack.dtb`'dir ve çıktı `arch/arm/boot/dts/am335x-boneblack.dtb` konumuna yazılır.

---

## 11.10 Boot Sürecinde Device Tree

[Linux boot sürecinde](03_boot_process.md) gördüğümüz gibi U-Boot, kernel'i başlatmadan önce <b>hem kernel image'ını hem de DTB'yi</b> RAM'e yükler:

```
eMMC / SD kart
  /boot/zImage, /boot/am335x-boneblack.dtb
        │  U-Boot: load
        ▼
DDR RAM
  loadaddr = 0x82000000 → kernel
  fdtaddr  = 0x88000000 → DTB
        │  bootz / bootm   (r2 = DTB adresi)
        ▼
Linux kernel
  DTB'yi okur (unflatten), device'ları oluşturur
        │
        ▼
Driver'lar compatible ile eşleşir ve probe edilir
```

[SD karttan boot](04_sd_card_boot.md) bölümündeki `uEnv.txt` ile birebir aynı mantık:

```bash
fdtaddr=0x88000000                                    # DTB'nin RAM'deki adresi
load mmc 0:2 ${fdtaddr} /boot/am335x-boneblack.dtb    # DTB'yi RAM'e yükle
bootm ${loadaddr} - ${fdtaddr}                        # kernel'i başlat ve DTB adresini ver
```

`bootm`/`bootz` komutunun üç parametresi:

| Parametre | Anlamı |
|---|---|
| `${loadaddr}` | Kernel image'ının RAM adresi |
| `-` | initramfs adresi (`-` = yok) |
| `${fdtaddr}` | <b>DTB'nin RAM adresi</b> |

ARM32'de U-Boot kernel'e atlarken DTB'nin fiziksel adresini <b>`r2` register'ında</b> verir. Kernel açılışta bu adresteki blob'u okur, `0xd00dfeed` magic number'ını kontrol eder ve DTB'yi bellekte gezilebilir bir ağaca dönüştürür (<b>unflatten</b>).

> [!NOTE]
> U-Boot, kernel'e vermeden önce DTB'yi <b>değiştirebilir</b> de. Örneğin `bootargs` değişkenini DTB'deki `/chosen` node'una yazar ve RAM boyutunu `/memory` node'una işler. Kernel command line'ının kernel'e ulaşma yollarından biri budur.

### U-Boot'ta DTB'yi incelemek

U-Boot'un `fdt` komutuyla RAM'deki DTB'ye bakılabilir:

```
=> load mmc 0:2 ${fdtaddr} /boot/am335x-boneblack.dtb
=> fdt addr ${fdtaddr}           # hangi adresteki DTB ile çalışılacak
=> fdt print /                   # tüm ağacı yazdır
=> fdt print /leds               # sadece leds node'u
=> fdt list /ocp                 # sadece alt node isimleri
```

---

## 11.11 Çalışan Sistemde Device Tree'yi İncelemek

Kernel, okuduğu device tree'yi bir dosya sistemi olarak dışarı açar:

```
/sys/firmware/devicetree/base/     # asıl konum
/proc/device-tree                  # → yukarıdakine sembolik link
```

Burada <b>her node bir klasör, her property bir dosyadır</b>:

```bash
# Kartın modeli
$ cat /proc/device-tree/model
TI AM335x BeagleBone Black

# Kök node'un compatible listesi (string'ler \0 ile ayrılmıştır)
$ cat /proc/device-tree/compatible | tr '\0' '\n'
ti,am335x-bone-black
ti,am335x-bone
ti,am33xx

# LED node'larına bak
$ ls /proc/device-tree/leds/

# Bootloader'ın kernel'e verdiği bootargs
$ cat /proc/device-tree/chosen/bootargs

# Sayısal property'leri hex olarak gör (ör. RAM adresi ve boyutu)
$ hexdump -C /proc/device-tree/memory@80000000/reg
00000000  80 00 00 00 20 00 00 00                           |.... ...|
#         adres=0x80000000  boyut=0x20000000 (512 MB)
```

Tüm ağacı tek seferde okunabilir DTS olarak görmek için:

```bash
sudo apt install device-tree-compiler
dtc -I fs -O dts /proc/device-tree > canli.dts 2>/dev/null
less canli.dts
```

Bir cihazın hangi driver'a bağlandığını görmek için:

```bash
ls /sys/bus/platform/devices/          # DT'den oluşturulan platform device'lar
ls -l /sys/bus/platform/devices/44e09000.serial/driver
#  → .../drivers/omap8250   (UART0'ı süren driver, kernel config'e göre serial-omap da olabilir)
```

BBB'nin Debian image'larında DTB dosyaları `/boot/dtbs/<kernel-sürümü>/` klasöründedir:

```bash
ls /boot/dtbs/$(uname -r)/ | grep boneblack
```

> [!TIP]
> Bir donanım çalışmıyorsa ilk kontrol: `/proc/device-tree` altında o cihazın node'u var mı ve `status` değeri `okay` mi? Node yoksa ya da `disabled` ise driver hiç devreye girmez. `dmesg | grep -i <cihaz>` ile de probe hatalarına bakılabilir.

---

## 11.12 Device Tree Overlay (.dtbo)

BeagleBone'a <b>cape</b> (P8/P9 header'larına takılan eklenti kart) takıldığında donanım değişir. Her cape kombinasyonu için ayrı bir `.dts` yazmak mantıklı değildir. Bunun çözümü <b>overlay</b>'dir.

- Overlay, ana DTB'ye <b>sonradan uygulanan bir yamadır</b>. Node ekleyebilir veya mevcut node'ları değiştirebilir.
- `.dts` kaynağından `dtc -@` ile <b>`.dtbo`</b> olarak derlenir.
- Ana DTB'nin de `-@` ile derlenmiş olması gerekir (label'ların bulunabilmesi için).
- Genellikle U-Boot tarafından boot sırasında uygulanır.

Basit bir overlay örneği (P9 header'ındaki I2C2'yi açar):

```dts
/dts-v1/;
/plugin/;                 /* bu bir overlay */

&i2c2 {                   /* ana DTB'deki i2c2 label'ına yama */
	status = "okay";
	clock-frequency = <100000>;
};
```

```bash
dtc -@ -I dts -O dtb -o BB-I2C2-ORNEK.dtbo BB-I2C2-ORNEK.dts
```

BBB'nin resmi Debian image'larında overlay'ler `/boot/uEnv.txt` dosyasından yönetilir. Hazır overlay'ler `/lib/firmware/` klasöründedir:

```bash
# /boot/uEnv.txt (ilgili satırlar)
enable_uboot_overlays=1
uboot_overlay_addr0=/lib/firmware/BB-I2C2-00A0.dtbo
#disable_uboot_overlay_video=1      # HDMI'ı kapatıp o pinleri serbest bırakır
```

> [!NOTE]
> Raspberry Pi'deki `config.txt` içindeki `dtoverlay=...` satırları da aynı mekanizmadır. Overlay kavramı BeagleBone'a özel değildir.

---

## 11.13 Özet

| Kavram | Bir cümlede |
|---|---|
| <b>Device Tree</b> | Keşfedilemeyen donanımı kernel'e tarif eden, ağaç yapısındaki veri |
| <b>.dts</b> | Bir kartın insan tarafından okunabilir kaynak tarifi |
| <b>.dtsi</b> | Birden fazla `.dts` tarafından include edilen ortak (genelde SoC) tarif |
| <b>dtc</b> | DTS ↔ DTB dönüşümü yapan derleyici |
| <b>.dtb</b> | Derlenmiş binary. Bootloader RAM'e yükler, kernel okur. |
| <b>.dtbo</b> | DTB'ye sonradan uygulanan yama (cape/HAT için) |
| <b>compatible</b> | Node ile driver'ı eşleştiren string |
| <b>reg</b> | Cihazın adresi (ve memory-mapped ise boyutu) |
| <b>status</b> | `"okay"` → kullan, `"disabled"` → kullanma |
| <b>label / phandle</b> | Node'a takma ad ve başka node'dan ona referans (`&label`) |
| <b>/proc/device-tree</b> | Çalışan kernel'in gördüğü device tree |

BeagleBone Black için akış:

```
am33xx.dtsi + am335x-bone*.dtsi + am335x-boneblack.dts
        │  (cpp + dtc  /  make dtbs)
        ▼
am335x-boneblack.dtb  ──►  SD/eMMC: /boot/...
        │  U-Boot: load → fdtaddr (0x88000000)
        ▼
bootz/bootm ${loadaddr} - ${fdtaddr}   (r2 = DTB adresi)
        │
        ▼
Kernel DTB'yi okur → device'ları oluşturur → compatible ile driver'ları probe eder
```

---

### Kaynaklar

- Görseller: [Bootlin - Linux kernel and driver development training](https://bootlin.com/training/kernel/) slaytları ve [bootlin/training-materials](https://github.com/bootlin/training-materials) deposu. Lisans: [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)
- [Devicetree Specification - devicetree.org](https://www.devicetree.org/specifications/)
- [Linux kernel dokümantasyonu: Devicetree](https://docs.kernel.org/devicetree/index.html)
- [Bootlin - Device Tree 101 webinar](https://bootlin.com/blog/device-tree-101-webinar-slides-and-videos/)
- [eLinux.org - Device Tree Usage](https://elinux.org/Device_Tree_Usage)

---

[← Bölüm 10: Linux Kernel: Kaynak Ağacı ve Derleme](10_linux_kernel.md) · [İçindekiler](README.md) · [Bölüm 12: BusyBox ile Minimal Root Filesystem →](12_busybox_rootfs.md)
