# Bölüm 21 — Kernel Modülü Yazmak

> <b>Bu bölümde:</b>
> - Kernel modülünün ne olduğunu, kullanıcı programından farkını ve neden modül yazıldığını öğreneceksin.
> - İlk modülünü yazıp kernel ağacının dışında (out-of-tree) cross compile edeceksin.
> - Modülü kartta `insmod`, `lsmod`, `rmmod`, `modinfo` ve `dmesg` ile yükleyip izleyeceksin.
> - Modüle parametre verecek ve bu parametreleri çalışırken sysfs'ten değiştireceksin.
> - Bir modülün dışa açtığı fonksiyonu başka bir modülde kullanacak, bağımlılığı `modprobe`'a çözdüreceksin.
>
> <b>Ön koşul:</b> [Bölüm 10](10_linux_kernel.md) — kernel'i ve modülleri derlemek, [Bölüm 12](12_busybox_rootfs.md) — kendi kernel'in ve BusyBox rootfs'inle (tercihen NFS) açılan kart.

> [!NOTE]
> Bu bölüm kursta yok; kitabın kursun ötesine geçen kısmının ilk bölümü. Kart, [Bölüm 10](10_linux_kernel.md)'da derlediğin kernel {{kernel.version}} ile ve [Bölüm 12](12_busybox_rootfs.md)'deki BusyBox rootfs'iyle açılıyor; komutlar kartta root olarak çalıştırılır. Terminal görüntüleri temsilidir.

---

## 21.1 Kernel Modülü Nedir?

Şimdiye kadar yazdığımız programlar (LED, 7-segment, LCD) <b>kullanıcı alanında</b> (user space) çalıştı. Donanıma kernel'in açtığı dosyalar (`/sys/class/gpio`, `/dev/i2c-2`) üzerinden ulaştılar. Bu dosyaların arkasında kernel'in içindeki <b>sürücüler</b> çalışıyordu.

<b>Kernel modülü</b>, kernel çalışırken içine eklenip çıkarılabilen bir kod parçasıdır (`.ko` dosyası, *kernel object*). Yüklendiği anda kernel'in bir parçası olur:

| | Kullanıcı programı | Kernel modülü |
|---|---|---|
| Nerede çalışır? | Kullanıcı alanı, kendi korumalı belleğinde | Kernel alanı, kernel ile aynı bellekte |
| Başlangıç noktası | `main()` | `module_init()` ile belirtilen fonksiyon |
| Kütüphane | glibc (`printf`, `malloc`...) | Sadece kernel'in fonksiyonları (`printk`, `kmalloc`...) |
| Hata yaparsa | Program çöker (`Segmentation fault`), sistem çalışmaya devam eder | <b>Bütün sistem</b> çökebilir (`Oops`, kernel panic) |
| Donanıma erişim | Kernel'in açtığı arayüzler üzerinden | Doğrudan (register'lar, kesmeler) |
| Çalıştırma | `./program` | `insmod modul.ko` |

```
 Kullanıcı alanı     ./led_blink  ./lcd_text        (Bölüm 16–20)
 ──────────────────────── open / read / write / ioctl ─────────────
 Kernel alanı        kernel  +  hello.ko  +  gpio-omap  +  i2c-omap ...
                             ▲
                             └── insmod ile eklendi, rmmod ile çıkarılır
```

<b>Neden modül?</b>

- Kernel'i yeniden derleyip kartı yeniden başlatmadan sürücü eklemek ve denemek için. Sürücü geliştirirken döngü "derle → `insmod` → dene → `rmmod`" olur.
- Her donanımın sürücüsünü kernel imajına gömmek imajı büyütür. Dağıtımlar sürücülerin çoğunu modül olarak verir; sadece donanımda olan yüklenir ([10.7](10_linux_kernel.md#107-kernel-yapılandırması-kconfig-config-menuconfig)'deki `m` seçeneği).

> [!WARNING]
> Modül kernel'in içinde çalıştığı için bir hata (NULL işaretçi, taşma) bütün sistemi kilitleyebilir. Modülleri geliştirme kartında dene; NFS rootfs ile çalışmak, kart kilitlendiğinde dosyalarının bilgisayarda güvende olması demektir.

---

## 21.2 Hazırlık: Hangi Kernel'e Karşı Derleniyor?

Bir modül, <b>belirli bir kernel için</b> derlenir. Derlenirken o kernel'in başlık dosyaları, `.config`'i ve sembol listesi (`Module.symvers`) kullanılır. Bu yüzden:

1. Elinde kartta çalışan kernel'in <b>derlenmiş kaynak ağacı</b> olmalı: [Bölüm 10](10_linux_kernel.md)'daki `~/bbb/{{kernel.dir}}`. Orada `make ... modules` de çalıştırılmış olmalı; `Module.symvers` dosyası bu adımda üretilir.
2. Kartta <b>aynı kaynaktan, aynı ayarlarla</b> derlenmiş kernel çalışmalı. Modülün içine yazılan <b>vermagic</b> (kernel sürümü + bazı ayarlar) yükleme anında çalışan kernel'le karşılaştırılır; uyuşmazsa modül reddedilir ([21.10](#2110-karşılaşılabilecek-problemler)).

```bash
ls ~/bbb/{{kernel.dir}}/Module.symvers ~/bbb/{{kernel.dir}}/.config     # ikisi de olmalı
```

Kartta:

```text
~ # uname -r
{{kernel.version}}
```

> [!NOTE]
> <b>Kartta eMMC'deki Debian ({{debian.kernel_flavor}}) çalışıyorsa</b> modülü Debian'ın kernel'ine karşı derlemen gerekir; [Bölüm 10](10_linux_kernel.md)'daki ağaç o kernel'in birebir aynısı değildir. En kolayı kartın kendisinde derlemek: `sudo apt install linux-headers-$(uname -r) build-essential`, sonra bu bölümün `code/` klasörünü karta kopyalayıp orada `make KDIR=/lib/modules/$(uname -r)/build` çalıştır. Debian armhf'te derleyicinin adı da `arm-linux-gnueabihf-gcc` olduğu için Makefile değişmeden çalışır.

---

## 21.3 Birinci Modül: `hello.c`

Bölümün kodu: [`code/21_kernel_module/`](../code/21_kernel_module/hello.c). En küçük modül iki fonksiyondan oluşur: biri yüklenirken, biri çıkarılırken çalışır.

```c
#define pr_fmt(fmt) KBUILD_MODNAME ": " fmt     /* her mesajın başına "hello: " */

#include <linux/init.h>
#include <linux/module.h>
#include <linux/moduleparam.h>
#include <linux/utsname.h>

static char *name = "BeagleBone";
module_param(name, charp, 0444);
MODULE_PARM_DESC(name, "Name to greet");

static int count = 1;
module_param(count, int, 0644);
MODULE_PARM_DESC(count, "How many times to greet (1-10)");

static int __init hello_init(void)
{
	int i;

	if (count < 1 || count > 10) {
		pr_err("count must be 1-10, got %d\n", count);
		return -EINVAL;
	}

	for (i = 0; i < count; i++)
		pr_info("Hello %s! (%d/%d)\n", name, i + 1, count);

	pr_info("running on Linux %s (%s)\n", utsname()->release, utsname()->machine);
	return 0;
}

static void __exit hello_exit(void)
{
	pr_info("Goodbye %s, count was %d\n", name, count);
}

module_init(hello_init);
module_exit(hello_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Embedded Linux kitabı");
MODULE_DESCRIPTION("First kernel module: hello with parameters");
```

| Parça | Anlamı |
|---|---|
| `module_init(hello_init)` | `insmod` sırasında çağrılacak fonksiyon. <b>`0` dönerse</b> modül yüklenir; negatif bir hata kodu (`-EINVAL`, `-ENOMEM`...) dönerse yükleme iptal olur ve modül bellekten atılır. |
| `module_exit(hello_exit)` | `rmmod` sırasında çağrılır. Init'te alınan her kaynak (bellek, GPIO, kesme...) burada bırakılmalıdır. |
| `__init` / `__exit` | Fonksiyonları özel bölümlere koyar. `__init` kodu yükleme bittikten sonra bellekten atılır; `__exit` kodu modül kernel'e gömülü derlenirse hiç derlenmez (gömülü kod çıkarılamaz). |
| `pr_info()`, `pr_err()` | Kernel log'una yazar: `printk(KERN_INFO ...)` kısaltması ([21.8](#218-printk-ve-log-seviyeleri)). Çıktı ekrana değil, `dmesg`'e gider. |
| `pr_fmt` | Bütün `pr_*` mesajlarının başına eklenecek metin. `KBUILD_MODNAME` derlemede modülün adıyla (`hello`) değiştirilir. |
| `MODULE_LICENSE("GPL")` | Lisans. GPL dışı bir lisans kernel'i "tainted" (lekeli) yapar ve modül `EXPORT_SYMBOL_GPL` ile açılmış fonksiyonları kullanamaz. |
| `MODULE_AUTHOR`, `MODULE_DESCRIPTION` | `modinfo` çıktısında görünen bilgiler |
| `utsname()` | Çalışan kernel'in adı ve sürümü (`uname` komutunun kernel'deki karşılığı) |

> [!IMPORTANT]
> Kernel kodunda `printf`, `malloc`, `<stdio.h>` yoktur; glibc kullanıcı alanının kütüphanesidir. Kernel'in kendi karşılıkları vardır: `printk`/`pr_info`, `kmalloc`/`kfree`, `<linux/...>` başlıkları. Kernel'de kayan nokta (`float`, `double`) da kullanılmaz.

Kernel mesajlarında Türkçe karakter kullanmadık: kernel log'u seri konsola da gider ve orada bozuk görünebilir ([8.8](08_tftp_boot.md#88-challenge-her-kaynaktan-boot-edebilen-genel-uenvtxt)'deki U-Boot mesajları gibi).

---

## 21.4 Ağaç Dışında Derlemek: Makefile ve kbuild

Modül kernel kaynağının içine konmadan, kendi klasöründe derlenir (<b>out-of-tree</b>). Derlemeyi yine kernel'in derleme sistemi (<b>kbuild</b>) yapar; biz sadece hangi dosyaların modül olacağını söyleriz:

```make
ifneq ($(KERNELRELEASE),)

obj-m := hello.o hello_lib.o hello_user.o

else

KDIR ?= $(HOME)/bbb/linux
ARCH ?= arm
CROSS_COMPILE ?= arm-linux-gnueabihf-

KMAKE = $(MAKE) -C $(KDIR) M=$(CURDIR) ARCH=$(ARCH) CROSS_COMPILE=$(CROSS_COMPILE)

all:
	$(KMAKE) modules

clean:
	$(KMAKE) clean

install:
	$(KMAKE) INSTALL_MOD_PATH=$(INSTALL_MOD_PATH) modules_install

endif
```

| Parça | Anlamı |
|---|---|
| `obj-m := hello.o` | `hello.c`'den `hello.ko` modülü üret (`m` = modül; kernel'e gömülü olsaydı `obj-y`) |
| `-C $(KDIR)` | `make`'i kernel kaynak klasöründe çalıştır; derleme kuralları, `.config` ve başlıklar oradan gelir |
| `M=$(CURDIR)` | Derlenecek modülün klasörü (bu klasör) |
| `ARCH`, `CROSS_COMPILE` | Kernel'i derlerken verdiğin değerlerin aynısı ([10.8](10_linux_kernel.md#108-adım-adım-kerneli-derleme)) |
| `ifneq ($(KERNELRELEASE),)` | Makefile iki kez okunur: önce senin `make` komutunla, sonra kbuild tarafından. kbuild okurken `KERNELRELEASE` tanımlıdır ve sadece `obj-m` kısmı kullanılır. |

> [!TIP]
> Kernel kaynağın başka bir yerdeyse `make KDIR=/yol/linux` yaz. Bir modül birden fazla `.c` dosyasından oluşacaksa: `obj-m := surucu.o` ve `surucu-objs := a.o b.o`.

### Derle

![Modülleri derleme ve modinfo ile inceleme](../images/kmod/01_build.png)

```bash
cd ~/code/21_kernel_module        # repodaki code/21_kernel_module klasörü
make
file hello.ko
modinfo hello.ko
```

Çıktıdaki adımlar:

| Satır | Ne oluyor? |
|---|---|
| `CC [M] hello.o` | C kodu ARM için derleniyor (`[M]` = modül) |
| `MODPOST Module.symvers` | Modülün kullandığı kernel fonksiyonları kernel'in `Module.symvers`'ındaki listeyle eşleştiriliyor. Kernel'de olmayan bir fonksiyon kullanırsan uyarı burada çıkar. |
| `CC [M] hello.mod.o` | Modülün kimlik bilgileri (vermagic, bağımlılıklar, parametreler) ayrı bir dosyada derleniyor |
| `LD [M] hello.ko` | Hepsi `hello.ko`'da birleştiriliyor |

`modinfo` host'ta da çalışır ve modülün içine gömülü bilgileri gösterir. En önemlisi `vermagic`: modülün hangi kernel için derlendiği.

---

## 21.5 Kartta Yüklemek: insmod, lsmod, dmesg, rmmod

Rootfs NFS'ten geliyorsa ([12.8](12_busybox_rootfs.md#128-rootfsi-nfs-ile-bilgisayardan-bağlamak)) modülleri NFS klasörüne kopyalamak yeterli; kart hemen görür. SD kart kullanıyorsan `scp` ya da SD kartı bilgisayara takıp kopyala.

![Modülü kartta yükleme, log'u okuma ve çıkarma](../images/kmod/02_insmod.png)

Host'ta:

```bash
sudo cp *.ko {{network.nfs_dir}}/root/
```

Kartta:

```text
~ # insmod hello.ko name=Mehmet count=3
~ # dmesg | tail -5
~ # lsmod
~ # rmmod hello
~ # dmesg | tail -1
```

| Komut | Görevi |
|---|---|
| `insmod dosya.ko [parametre=değer ...]` | Modülü verilen dosyadan yükler. Bağımlılıklara bakmaz. |
| `lsmod` | Yüklü modüller, boyutları ve kaç modül/kullanıcının onları kullandığı (`/proc/modules`'un okunaklı hali) |
| `rmmod ad` | Modülü çıkarır (`.ko` değil, modülün <b>adı</b> yazılır) |
| `modinfo dosya.ko` | Modülün bilgileri. Host'taki `modinfo` ARM modüllerini de okur; BusyBox'ın `modinfo`'su daha sınırlıdır, host'ta kullan. |
| `dmesg` | Kernel log'u. `pr_info()` mesajları burada. |

`dmesg`'teki ilk satır dikkat çekici: `loading out-of-tree module taints kernel.` Kernel, kendi kaynağında olmayan bir modül yüklendiğini not eder (<b>taint</b>, "leke"). Bu bir hata değildir; kernel bir hata raporu (Oops) basarsa geliştiricilere "sisteme dışarıdan kod yüklenmişti" bilgisini verir. `lsmod`'daki `Tainted: G` ve `/proc/sys/kernel/tainted` de bunu gösterir.

Modül yüklüyken `/sys/module/hello/` klasörü oluşur. Kernel her modül için burada bilgi açar: `refcnt` (kaç kullanıcısı var), `parameters/` ([21.6](#216-modül-parametreleri)), `sections/`.

---

## 21.6 Modül Parametreleri

Kullanıcı programına komut satırı argümanı verir gibi modüle de değer verebilirsin. `module_param(isim, tür, izin)`:

| Tür | C türü |
|---|---|
| `int`, `uint`, `long`, `ulong`, `short`, `ushort` | Tamsayılar |
| `bool`, `invbool` | `true`/`false` (`1`/`0`, `y`/`n`) |
| `charp` | Metin (`char *`); kernel değeri kendi belleğine kopyalar |

Üçüncü argüman, parametrenin `/sys/module/<modül>/parameters/` altındaki dosyasının izinleridir:

| İzin | Anlamı |
|---|---|
| `0` | sysfs'te dosya yok; değer sadece yüklerken verilir |
| `0444` | Herkes okuyabilir, kimse değiştiremez (`name`) |
| `0644` | Herkes okur, root çalışırken değiştirebilir (`count`) |

![Parametreleri sysfs'ten okuma ve değiştirme](../images/kmod/03_params.png)

```text
~ # insmod hello.ko
~ # cat /sys/module/hello/parameters/name /sys/module/hello/parameters/count
~ # echo 5 > /sys/module/hello/parameters/count
~ # echo Ali > /sys/module/hello/parameters/name        # Permission denied: 0444
~ # rmmod hello; dmesg | tail -1                         # count was 5
```

> [!IMPORTANT]
> sysfs'ten yazılan değer değişkene <b>hemen</b> yazılır ama modül bundan haberdar edilmez. `count` init'te kontrol edildi; çalışırken `echo 50 > count` yazılırsa bu kontrol tekrar yapılmaz. Değerin değişince bir şey tetiklemesi ya da doğrulanması gerekiyorsa `module_param_cb()` ile kendi set fonksiyonunu yazarsın.

Modül kernel'e gömülü derlenmişse aynı parametreler kernel komut satırından (`bootargs`) `modül.parametre=değer` biçiminde verilir (ör. `hello.count=3`).

---

## 21.7 Modüller Arası Sembol Paylaşımı ve modprobe

Kernel'in fonksiyonları modüllere kendiliğinden açık değildir; sadece <b>`EXPORT_SYMBOL()`</b> ya da <b>`EXPORT_SYMBOL_GPL()`</b> ile işaretlenenler kullanılabilir. Bir modül de kendi fonksiyonunu böyle dışa açabilir. Örnekte iki modül var:

| Modül | Ne yapar? |
|---|---|
| [`hello_lib.c`](../code/21_kernel_module/hello_lib.c) | `hello_lib_add()` fonksiyonunu `EXPORT_SYMBOL_GPL` ile dışa açar |
| [`hello_user.c`](../code/21_kernel_module/hello_user.c) | Yüklenirken `hello_lib_add(2, 3)`'ü çağırır |

```c
/* hello_lib.c */
int hello_lib_add(int a, int b)
{
	calls++;
	pr_info("hello_lib_add(%d, %d) called, %d call(s) so far\n", a, b, calls);
	return a + b;
}
EXPORT_SYMBOL_GPL(hello_lib_add);

/* hello_user.c */
static int __init hello_user_init(void)
{
	pr_info("2 + 3 = %d\n", hello_lib_add(2, 3));
	return 0;
}
```

`hello_user.ko`, `hello_lib.ko`'ya <b>bağımlıdır</b>: `modinfo hello_user.ko` çıktısında `depends: hello_lib` yazar. `insmod` bağımlılıklara bakmaz; `hello_lib` yüklü değilse `Unknown symbol` hatası verir. Bağımlılıkları <b>`modprobe`</b> çözer:

1. Modüller `/lib/modules/$(uname -r)/` altına kurulur.
2. `depmod` bütün modüllerin bağımlılıklarını `modules.dep` dosyasına yazar.
3. `modprobe hello_user` bu dosyaya bakar, önce `hello_lib`'i, sonra `hello_user`'ı yükler. `modprobe -r` tersini yapar.

![insmod'un bağımlılık hatası ve modprobe ile yükleme](../images/kmod/04_depends.png)

Host'ta, modülleri [Bölüm 12](12_busybox_rootfs.md)'deki rootfs klasörüne kur ve NFS klasörüne kopyala:

```bash
make install INSTALL_MOD_PATH=~/bbb/rootfs
grep hello ~/bbb/rootfs/lib/modules/{{kernel.version}}/modules.dep
sudo cp -a ~/bbb/rootfs/lib/modules/{{kernel.version}} {{network.nfs_dir}}/lib/modules/
```

`modules_install`, dışarıdan derlenen modülleri `lib/modules/<sürüm>/extra/` altına koyar ve `depmod`'u kendisi çalıştırır. `make install`'ı <b>`sudo` olmadan</b> çalıştır: `sudo` altında `HOME` ve `PATH` değişir; Makefile kernel kaynağını (`$(HOME)/bbb/linux`) ve cross derleyiciyi bulamaz.

Kartta:

```text
~ # insmod hello_user.ko        # Unknown symbol: hello_lib yüklü değil
~ # modprobe hello_user         # önce hello_lib, sonra hello_user
~ # lsmod
~ # modprobe -r hello_user      # ikisini de çıkarır
```

`lsmod`'da `hello_lib`'in "Used by" sütununda `1 hello_user` görünür. Bir modülü kullanan başka modül varken onu `rmmod` ile çıkaramazsın.

> [!TIP]
> Bir modülün açılışta otomatik yüklenmesi için [12.7](12_busybox_rootfs.md#127-usb-üzerinden-ethernet-ve-sürücüleri-açılışta-yüklemek)'deki `S02module` betiğine `modprobe hello_user` satırını eklemen yeterli.

---

## 21.8 printk ve Log Seviyeleri

`pr_info()` gibi makrolar `printk()`'ya bir <b>log seviyesi</b> ekler:

| Makro | Seviye | Ne zaman? |
|---|---|---|
| `pr_emerg` | 0 `KERN_EMERG` | Sistem kullanılamaz |
| `pr_alert` | 1 `KERN_ALERT` | Hemen müdahale gerekli |
| `pr_crit` | 2 `KERN_CRIT` | Kritik durum |
| `pr_err` | 3 `KERN_ERR` | Hata |
| `pr_warn` | 4 `KERN_WARNING` | Uyarı |
| `pr_notice` | 5 `KERN_NOTICE` | Önemli ama normal |
| `pr_info` | 6 `KERN_INFO` | Bilgi |
| `pr_debug` | 7 `KERN_DEBUG` | Hata ayıklama; sadece dosyanın başında `#define DEBUG` varsa (ya da dinamik debug açıksa) derlenir |

Bütün mesajlar `dmesg`'e gider. Hangilerinin <b>seri konsola da</b> basılacağını konsol log seviyesi belirler: seviyesi bu değerden küçük olanlar konsolda da görünür.

```text
~ # cat /proc/sys/kernel/printk       # ilk sayı: konsol log seviyesi
~ # dmesg -n 8                        # her şeyi konsolda da göster
~ # dmesg -n 1                        # konsolu sustur (sadece panik mesajları)
~ # dmesg -c                          # log'u gösterip temizle
```

Kernel komut satırına (`bootargs`) `loglevel=8` eklemek açılıştan itibaren aynı etkiyi yapar; `quiet` ise konsolu susturur.

> [!TIP]
> Modül yüklerken mesajları görmek için seri konsolda `dmesg -n 8` yapabilir ya da ikinci bir terminalde (SSH) `dmesg -w` ile log'u canlı izleyebilirsin.

---

## 21.9 Özet

- Kernel modülü (`.ko`) kernel çalışırken eklenip çıkarılan koddur; kernel ile aynı bellekte, aynı yetkiyle çalışır. Hatası bütün sistemi çökertebilir.
- En küçük modül: `module_init()` (0 dönerse yüklenir), `module_exit()`, `MODULE_LICENSE("GPL")`. Çıktı `pr_info()` ile `dmesg`'e yazılır.
- Out-of-tree derleme: `obj-m := x.o` + `make -C <kernel ağacı> M=$(PWD) ARCH=arm CROSS_COMPILE=... modules`. Ağaç, kartta çalışan kernel'in derlenmiş kaynağı olmalı (vermagic).
- Kartta: `insmod x.ko param=değer`, `lsmod`, `rmmod x`, `dmesg`. Parametreler `/sys/module/x/parameters/` altında.
- `EXPORT_SYMBOL[_GPL]` ile modüller birbirinin fonksiyonunu kullanır. `modules_install` + `depmod` → `modprobe` bağımlılıkları kendisi yükler.
- Log seviyeleri `pr_err`…`pr_debug`; konsolda neyin görüneceğini `dmesg -n` belirler.

## 21.10 Karşılaşılabilecek Problemler

![Sık görülen modül hataları (temsili)](../images/kmod/05_errors.png)

| Belirti | Sebep | Çözüm |
|---|---|---|
| `insmod: can't insert ...: invalid module format`, `dmesg`'te `version magic '...' should be '...'` | Modül, kartta çalışan kernel'den farklı bir kernel için derlenmiş | Kartta çalışan kernel'in kaynağıyla derle ([21.2](#212-hazırlık-hangi-kernele-karşı-derleniyor)); kernel'i yeniden derlediysen kartı da yeni kernel'le aç |
| `invalid module format`, vermagic doğru | Modül x86 için derlenmiş (`ARCH`/`CROSS_COMPILE` unutuldu) | `file hello.ko` → ARM yazmalı |
| `make: *** /home/.../bbb/linux: No such file or directory` | `KDIR` yanlış | `make KDIR=<kernel kaynağının yolu>` |
| `WARNING: Module.symvers is missing` | Kernel ağacında `make modules` hiç çalıştırılmamış | Kernel klasöründe `make ARCH=arm CROSS_COMPILE=... modules` ([10.8](10_linux_kernel.md#108-adım-adım-kerneli-derleme)) |
| `insmod: ... unknown symbol in module`, `dmesg`'te `Unknown symbol xxx` | Kullanılan fonksiyonu açan modül yüklü değil ya da fonksiyon dışa açılmamış | `modprobe` kullan; kendi kodunda `EXPORT_SYMBOL` eksik mi bak |
| `Unknown symbol`, ama sembolü açan modül yüklü | Modülün lisansı GPL değil; `EXPORT_SYMBOL_GPL` ile açılan semboller ona görünmez | `MODULE_LICENSE("GPL")` |
| `insmod: ... Invalid argument` | Init fonksiyonu `-EINVAL` döndü (ör. `count=20`) ya da parametre türü yanlış | `dmesg`'teki mesaja bak |
| `insmod: ... File exists` | Modül zaten yüklü | `lsmod`; önce `rmmod` |
| `rmmod: can't unload module ...: Resource temporarily unavailable` | Modülü başka bir modül ya da açık bir dosya kullanıyor | `lsmod`'da "Used by"a bak; önce kullananı çıkar ya da `modprobe -r` |
| `modprobe: module hello_user not found in modules.dep` | Modül kurulmamış ya da `depmod` çalışmamış | [21.7](#217-modüller-arası-sembol-paylaşımı-ve-modprobe)'deki `make install`; kartta `depmod` |
| `pr_info()` mesajları konsolda görünmüyor | Konsol log seviyesi düşük | `dmesg` ile oku ya da `dmesg -n 8` |
| `module verification failed: signature and/or required key missing - tainting kernel` | Kernel imzalı modül bekliyor ama zorunlu kılmıyor | Uyarıdır, modül yüklenir |
