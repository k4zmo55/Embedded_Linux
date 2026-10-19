# Bölüm 22 — Karakter Aygıt Sürücüsü

> <b>Bu bölümde:</b>
> - `/dev` altındaki dosyaların ne olduğunu, karakter ve blok aygıtlarını, major/minor numaralarını öğreneceksin.
> - Bir programın `open()`/`read()`/`write()` çağrısının sürücüdeki fonksiyonlara nasıl ulaştığını göreceksin.
> - `/dev/bbbmsg` adında, kendiliğinden oluşan bir aygıt dosyası açan karakter sürücüsü yazacaksın.
> - Kullanıcı belleğiyle güvenli veri alışverişini (`copy_to_user`, `copy_from_user`), dosya konumunu, mutex'i ve `ioctl`'ü öğreneceksin.
> - Sürücüyü kabuktan ve bir C programından deneyeceksin.
>
> <b>Ön koşul:</b> [Bölüm 21](21_kernel_module.md) — modül derleme, `insmod`/`rmmod`, `dmesg`.

> [!NOTE]
> Bu bölüm kursta yok. Kart, [Bölüm 21](21_kernel_module.md)'deki gibi kendi kernel'in ({{kernel.version}}) ve BusyBox rootfs'inle açılıyor; komutlar kartta root olarak çalıştırılır. Terminal görüntüleri temsilidir.

---

## 22.1 /dev Altındaki Dosyalar

Önceki bölümlerde `/dev/ttyS0`'a (seri port), `/dev/i2c-2`'ye ([Bölüm 19](19_mpu6050.md)) ve `/dev/mmcblk0`'a (SD kart) eriştik. Bunlar diskte veri tutan dosyalar değildir; <b>aygıt dosyalarıdır</b> (device node). Bir programın bu dosyaya yaptığı her `open`, `read`, `write`, `ioctl` çağrısı kernel'de o aygıtın <b>sürücüsüne</b> gider.

![/dev'deki aygıt dosyaları ve /proc/devices](../images/chardev/01_dev_numbers.png)

```text
~ # ls -l /dev/ttyS0 /dev/null /dev/i2c-2 /dev/mmcblk0
~ # head -8 /proc/devices
```

`ls -l` çıktısının ilk harfi aygıtın türünü, boyut sütunundaki iki sayı <b>major</b> ve <b>minor</b> numaralarını gösterir:

| Tür | Harf | Nasıl erişilir? | Örnek |
|---|---|---|---|
| <b>Karakter aygıtı</b> | `c` | Bayt bayt, sırayla (akış gibi) | Seri port, `/dev/null`, `/dev/i2c-*`, `/dev/gpiochip*` |
| <b>Blok aygıtı</b> | `b` | Sabit boyutlu bloklar halinde, rastgele; arada kernel'in önbelleği var | SD kart, eMMC, USB bellek |
| Ağ aygıtı | — | `/dev`'de dosyası yok; soketlerle | `eth0`, `usb0` |

| Numara | Anlamı |
|---|---|
| <b>Major</b> | Hangi <b>sürücü</b>? Kernel, aygıt dosyası açılınca bu numaraya bakarak sürücüyü bulur. `/proc/devices` hangi major'ın hangi sürücüye ait olduğunu listeler. |
| <b>Minor</b> | Sürücünün yönettiği aygıtlardan <b>hangisi</b>? Ör. `ttyS0` = 4/64, `ttyS1` = 4/65: aynı sürücü, farklı UART. |

Bu bölümde kendi karakter aygıtımızı yazacağız. Gerçek bir donanım sürmüyor: aygıta yazılan metni kernel belleğinde saklıyor ve okununca geri veriyor. Böylece sürücünün parçalarına donanım ayrıntısı karışmadan bakabiliriz; [Bölüm 23](23_gpio_platform_driver.md)'te device tree'den tanıtılan gerçek bir LED'i ve butonu süren bir sürücü yazacağız.

---

## 22.2 Bir read() Çağrısının Yolculuğu

```
 Kullanıcı alanı      cat /dev/bbbmsg
                         │  read(fd, buf, 4096)
 ────────────────────────┼──────────────────────────────── sistem çağrısı
 Kernel alanı            ▼
                      VFS (sanal dosya sistemi)
                         │  /dev/bbbmsg → karakter aygıtı, major 246, minor 0
                         ▼
                      cdev tablosu: 246:0 → bbbmsg_fops
                         │
                         ▼
                      bbbmsg_read(file, buf, 4096, &pos)    ← bizim fonksiyonumuz
                         │  copy_to_user(buf, msg, n)
                         ▼
                      n bayt döner → cat ekrana basar
```

Sürücü, kernel'e bir <b>`struct file_operations`</b> tablosu verir. Tablodaki her alan bir sistem çağrısına karşılık gelir; doldurulmayan alanlar için kernel varsayılan davranışı uygular ya da hata döner:

```c
static const struct file_operations bbbmsg_fops = {
	.owner          = THIS_MODULE,
	.open           = bbbmsg_open,
	.release        = bbbmsg_release,
	.read           = bbbmsg_read,
	.write          = bbbmsg_write,
	.llseek         = bbbmsg_llseek,
	.unlocked_ioctl = bbbmsg_ioctl,
};
```

| Alan | Hangi çağrıda? |
|---|---|
| `open` / `release` | `open()` / son `close()` |
| `read` / `write` | `read()` / `write()` |
| `llseek` | `lseek()` |
| `unlocked_ioctl` | `ioctl()` |
| `owner = THIS_MODULE` | Aygıt açıkken modülün kullanımda sayılmasını sağlar; aygıt açıkken `rmmod` reddedilir |

Bölümün kodu: [`code/22_char_driver/`](../code/22_char_driver/bbbmsg.c).

---

## 22.3 Aygıtı Kaydetmek: Numara, cdev, class

Sürücü yüklenirken üç şey yapar:

```c
static int __init bbbmsg_init(void)
{
	struct device *dev;
	int ret;

	/* 1) Boş bir major numara ve 1 minor numara iste. */
	ret = alloc_chrdev_region(&devno, 0, 1, DEV_NAME);
	if (ret)
		return ret;

	/* 2) Bu numarayı file_operations'a bağla. */
	cdev_init(&bbbmsg_cdev, &bbbmsg_fops);
	bbbmsg_cdev.owner = THIS_MODULE;
	ret = cdev_add(&bbbmsg_cdev, devno, 1);
	if (ret)
		goto err_region;

	/* 3) /sys/class/bbbmsg/bbbmsg oluştur; devtmpfs/mdev /dev/bbbmsg'yi açar. */
	bbbmsg_class = class_create(THIS_MODULE, DEV_NAME);
	...
	dev = device_create(bbbmsg_class, NULL, devno, NULL, DEV_NAME);
	...
	return 0;

err_class:
	class_destroy(bbbmsg_class);
err_cdev:
	cdev_del(&bbbmsg_cdev);
err_region:
	unregister_chrdev_region(devno, 1);
	return ret;
}
```

| Adım | Fonksiyon | Ne yapar? |
|---|---|---|
| 1 | `alloc_chrdev_region()` | Kernel'den boş bir major ve istenen sayıda minor numara alır. `devno` (`dev_t`) ikisini birlikte tutar: `MAJOR(devno)`, `MINOR(devno)`. Numara sabit yazılmaz; başka bir sürücüyle çakışabilir. |
| 2 | `cdev_init()` + `cdev_add()` | "Bu numaraya gelen çağrılar şu `file_operations`'a gitsin" kaydını yapar. `cdev_add`'den sonra aygıt <b>canlıdır</b>. |
| 3 | `class_create()` + `device_create()` | `/sys/class/bbbmsg/bbbmsg/` oluşturur. Kernel bunu bir <b>uevent</b> ile duyurur; `/dev/bbbmsg` düğümünü <b>devtmpfs</b> (kernel'in kendisi) ya da `mdev`/`udev` açar. Bu adım olmasaydı düğümü elle `mknod /dev/bbbmsg c 246 0` ile açmak gerekirdi. |

> [!NOTE]
> Kernel 6.4'ten itibaren `class_create()` sadece ismi alır: `class_create("bbbmsg")`. Koddaki `#if LINUX_VERSION_CODE >= KERNEL_VERSION(6, 4, 0)` satırı, sürücünün hem 5.10'da hem yeni kernel'lerde derlenmesini sağlar.

<b>Hata yolu:</b> Her adım başarısız olabilir. Bir adım başarısız olursa o ana kadar alınanlar <b>ters sırada</b> bırakılır (`goto err_...` zinciri). Kernel kodunda bu kalıp çok yaygındır; init yarıda kalırsa bırakılmayan bir numara ya da sınıf, modül tekrar yüklenene kadar sistemde kalır. `bbbmsg_exit()` de aynı sırayla temizler.

---

## 22.4 read ve write: Kullanıcı Belleğiyle Çalışmak

### copy_to_user ve copy_from_user

`read()`'e verilen `buf` işaretçisi <b>kullanıcı programının</b> belleğini gösterir. Kernel bu adrese doğrudan (`memcpy`) yazmamalıdır:

- Adres geçersiz olabilir (program yanlış adres verdi ya da kötü niyetli). Kernel'in o adrese yazması sistemi çökertir ya da güvenlik açığı olur.
- O sayfa o an bellekte olmayabilir.

`copy_to_user(hedef, kaynak, n)` ve `copy_from_user(hedef, kaynak, n)` adresi kontrol eder ve kopyalayamadığı bayt sayısını döner (0 = hepsi kopyalandı). Kopyalanamadıysa sürücü `-EFAULT` döner; program `Bad address` hatası alır. Fonksiyon parametrelerindeki <b>`__user`</b> işareti bu adresin kullanıcı alanına ait olduğunu belirtir; statik analiz araçları (`sparse`) onu doğrudan kullanan kodu yakalar.

### Dosya konumu: *ppos

```c
static ssize_t bbbmsg_read(struct file *file, char __user *ubuf,
			   size_t count, loff_t *ppos)
{
	ssize_t ret;

	if (mutex_lock_interruptible(&msg_lock))
		return -ERESTARTSYS;

	if (*ppos >= msg_len) {
		ret = 0;                        /* dosya sonu (EOF) */
		goto out;
	}
	if (count > msg_len - *ppos)
		count = msg_len - *ppos;

	if (copy_to_user(ubuf, msg + *ppos, count)) {
		ret = -EFAULT;
		goto out;
	}
	*ppos += count;
	ret = count;
out:
	mutex_unlock(&msg_lock);
	return ret;
}
```

`*ppos`, açık dosyanın içinde nerede olduğumuzu tutar. `read()`'in dönüş değeri kuralları:

| Dönüş | Program ne anlar? |
|---|---|
| `> 0` | Bu kadar bayt okundu; tekrar oku |
| `0` | <b>Dosya sonu.</b> `cat` burada durur. |
| `< 0` | Hata (`-EFAULT`, `-EINTR`...); `errno` olarak programa gider |

> [!IMPORTANT]
> `read` her çağrıda aynı veriyi döner ve hiç `0` dönmezse `cat /dev/bbbmsg` sonsuza kadar aynı metni basar. `*ppos`'u ilerletmek ve sonda `0` dönmek bu yüzden gerekli.

`write` aynı mantıkla çalışır: veriyi `*ppos`'tan itibaren `msg`'ye kopyalar, yazılan yerin sonu mesajın yeni sonu olur. Böylece:

- `echo a > /dev/bbbmsg`: dosya baştan (konum 0) açılır, mesaj değişir.
- `echo b >> /dev/bbbmsg`: `O_APPEND` ile açılır. Normal dosyalarda sona eklemeyi dosya sistemi yapar; karakter aygıtlarında <b>sürücü</b> yapmalıdır: `if (file->f_flags & O_APPEND) *ppos = msg_len;`
- Tampon (256 bayt) dolarsa `write` yazabildiği kadarını yazar; yer hiç kalmadıysa `-ENOSPC` döner.

`llseek` için kernel'in hazır yardımcısı kullanılıyor: `generic_file_llseek_size(file, offset, whence, BUF_SIZE, msg_len)`. `SEEK_END` mesajın sonunu, en büyük geçerli konum tampon boyutunu kullanır.

---

## 22.5 Eşzamanlılık: Mutex

Aynı anda iki program aygıta yazabilir; biri yazarken öbürü okuyabilir. `msg` ve `msg_len`'i aynı anda iki yerden değiştirmek veriyi bozar. Bu yüzden onlara her erişim bir <b>mutex</b> ile korunur:

```c
static DEFINE_MUTEX(msg_lock);

if (mutex_lock_interruptible(&msg_lock))
	return -ERESTARTSYS;
/* ... msg ve msg_len'e erişim ... */
mutex_unlock(&msg_lock);
```

| Fonksiyon | Fark |
|---|---|
| `mutex_lock()` | Kilit boşalana kadar bekler; beklerken Ctrl-C ile bile kesilemez |
| `mutex_lock_interruptible()` | Beklerken bir sinyal gelirse (Ctrl-C) vazgeçer ve 0 dışı döner. Kullanıcının çağrısıyla gelen uzun beklemelerde bu tercih edilir; sürücü `-ERESTARTSYS` döner, kernel çağrıyı gerekirse yeniden başlatır. |

> [!TIP]
> AM335x tek çekirdekli ama kernel <b>preemptive</b>: bir süreç `write`'ın ortasında durdurulup başka bir süreç çalıştırılabilir. Tek çekirdekte de kilit gerekir.

---

## 22.6 ioctl: Okuma/Yazma Dışındaki Komutlar

Bazı işler "veri oku/yaz" kalıbına uymaz: baud hızını değiştirmek, I2C adresini seçmek ([Bölüm 19](19_mpu6050.md)'daki `ioctl(fd, I2C_SLAVE, 0x68)`), bir ayarı sormak. Bunlar <b>`ioctl()`</b> ile yapılır. Sürücümüzde iki komut var; komut numaraları sürücü ile programın ortak kullandığı [`bbbmsg.h`](../code/22_char_driver/bbbmsg.h)'de:

```c
#define BBBMSG_IOC_MAGIC    'b'
#define BBBMSG_CLEAR        _IO(BBBMSG_IOC_MAGIC, 0)          /* mesajı sil */
#define BBBMSG_GET_LEN      _IOR(BBBMSG_IOC_MAGIC, 1, int)    /* uzunluğu oku */
```

| Makro | Anlamı |
|---|---|
| `_IO(tip, no)` | Veri taşımayan komut |
| `_IOR(tip, no, tür)` | Sürücüden programa veri (Read: program okur) |
| `_IOW(tip, no, tür)` | Programdan sürücüye veri |
| `_IOWR(tip, no, tür)` | İki yönlü |

Makrolar komut numarasına sihirli harfi (`'b'`), sıra numarasını, veri yönünü ve boyutunu kodlar; böylece başka bir sürücünün komutu yanlışlıkla bizimkine gönderilirse tanınmaz. Sürücü tarafı:

```c
static long bbbmsg_ioctl(struct file *file, unsigned int cmd, unsigned long arg)
{
	int len;

	switch (cmd) {
	case BBBMSG_CLEAR:
		mutex_lock(&msg_lock);
		msg_len = 0;
		mutex_unlock(&msg_lock);
		return 0;

	case BBBMSG_GET_LEN:
		mutex_lock(&msg_lock);
		len = msg_len;
		mutex_unlock(&msg_lock);
		return put_user(len, (int __user *)arg);

	default:
		return -ENOTTY;                 /* bu sürücünün komutu değil */
	}
}
```

`put_user()`, tek bir değişken için `copy_to_user()`'ın kısa yoludur. Bilinmeyen komuta `-ENOTTY` dönmek gelenektir (program `Inappropriate ioctl for device` görür).

---

## 22.7 Derle ve Kabuktan Dene

[`Makefile`](../code/22_char_driver/Makefile) [Bölüm 21](21_kernel_module.md#214-ağaç-dışında-derlemek-makefile-ve-kbuild)'dekinin aynısı; `make test` ayrıca kullanıcı programını statik derler.

![Sürücüyü derleme, yükleme ve /dev düğümü](../images/chardev/02_build_load.png)

Host'ta:

```bash
cd ~/code/22_char_driver
make && make test
sudo cp bbbmsg.ko bbbmsg_test {{network.nfs_dir}}/root/
```

Kartta:

```text
~ # insmod bbbmsg.ko
~ # dmesg | tail -1
~ # grep bbbmsg /proc/devices
~ # ls -l /dev/bbbmsg
~ # cat /sys/class/bbbmsg/bbbmsg/dev
```

Kernel boş bir major numara verdi (örnekte 246; sende farklı olabilir) ve `/dev/bbbmsg` kendiliğinden oluştu. Artık bu dosya her program için sıradan bir dosya gibi:

![Aygıtı echo, cat ve dd ile deneme](../images/chardev/03_shell_test.png)

```text
~ # echo "Merhaba BBB" > /dev/bbbmsg
~ # cat /dev/bbbmsg
~ # echo "ikinci satir" >> /dev/bbbmsg
~ # cat /dev/bbbmsg
~ # dd if=/dev/bbbmsg bs=1 skip=8 count=3 2>/dev/null; echo
~ # dmesg | tail -4
```

`dd ... skip=8` önce `lseek` ile 8. bayta gider, sonra 3 bayt okur: "Merhaba BBB" metnindeki `BBB`. `dmesg`'te her `echo`/`cat` için bir `open` ve `release` satırı görürsün: her komut aygıtı açıp kapatıyor.

---

## 22.8 Kullanıcı Programıyla Dene

[`bbbmsg_test.c`](../code/22_char_driver/bbbmsg_test.c) aygıtı bir C programından kullanır: yazar, `ioctl` ile uzunluğu sorar, başa dönüp okur, `ioctl` ile siler ve tekrar okur.

```c
fd = open(DEV_PATH, O_RDWR);

n = write(fd, argv[1], strlen(argv[1]));
ioctl(fd, BBBMSG_GET_LEN, &len);

lseek(fd, 0, SEEK_SET);                 /* yazdıktan sonra konum sonda */
n = read(fd, buf, sizeof(buf) - 1);

ioctl(fd, BBBMSG_CLEAR);
```

![Kullanıcı programıyla deneme ve modülü çıkarma](../images/chardev/04_user_program.png)

```text
~ # ./bbbmsg_test "C programindan selam"
~ # rmmod bbbmsg
~ # ls /dev/bbbmsg          # yok: device_destroy düğümü kaldırdı
```

Sürücü ile program aynı `bbbmsg.h`'yi kullandığı için komut numaraları iki tarafta da aynıdır. Gerçek sürücülerde bu başlıklar kernel'in `include/uapi/` klasöründe durur ve kullanıcı programlarına `/usr/include/linux/` olarak gelir; [Bölüm 19](19_mpu6050.md)'daki `<linux/i2c-dev.h>` böyle bir başlıktır.

---

## 22.9 Özet

- `/dev` altındaki dosyalar aygıt düğümleridir. `c` karakter, `b` blok aygıtı; <b>major</b> sürücüyü, <b>minor</b> sürücünün aygıtını seçer (`/proc/devices`).
- Karakter sürücüsü: `alloc_chrdev_region()` → `cdev_init()` + `cdev_add()` → `class_create()` + `device_create()` (düğümü devtmpfs/mdev açar). Çıkarken ters sırada bırakılır.
- `struct file_operations` sistem çağrılarını sürücünün fonksiyonlarına bağlar: `open`, `release`, `read`, `write`, `llseek`, `unlocked_ioctl`.
- Kullanıcı belleğine sadece `copy_to_user()` / `copy_from_user()` / `put_user()` ile erişilir; başarısızsa `-EFAULT`.
- `read` konumu (`*ppos`) ilerletir ve sonda `0` döner; yoksa `cat` hiç durmaz. `O_APPEND`'i karakter sürücüsü kendisi uygular.
- Paylaşılan veri mutex ile korunur (`mutex_lock_interruptible`); tek çekirdekte de gerekir.
- Okuma/yazma dışındaki komutlar `ioctl` ile: `_IO`, `_IOR`, `_IOW`; bilinmeyen komuta `-ENOTTY`.

## 22.10 Karşılaşılabilecek Problemler

![Sık görülen hatalar (temsili)](../images/chardev/05_errors.png)

| Belirti | Sebep | Çözüm |
|---|---|---|
| `/dev/bbbmsg` oluşmuyor | `device_create()` çağrılmadı ya da rootfs'te devtmpfs/mdev yok | `dmesg`'e bak; [12.4](12_busybox_rootfs.md#124-rootfsi-tamamlamak)'teki `CONFIG_DEVTMPFS_MOUNT`'u kontrol et ya da elle `mknod /dev/bbbmsg c <major> 0` |
| `cat /dev/bbbmsg` aynı metni durmadan basıyor | `read` `*ppos`'u ilerletmiyor ya da sonda `0` dönmüyor | [22.4](#224-read-ve-write-kullanıcı-belleğiyle-çalışmak)'teki gibi |
| `>>` ile ekleme yapılmıyor, metin baştan yazılıyor | `O_APPEND` sürücüde uygulanmamış | `write`'ta `f_flags & O_APPEND` kontrolü |
| `write error: No space left on device` | 256 baytlık tampon doldu | Beklenen davranış; mesajı `BBBMSG_CLEAR` ioctl'üyle sil (`./bbbmsg_test`). `echo -n > /dev/bbbmsg` silmez: sıfır baytlık yazma sürücünün `write`'ını hiç çağırmaz. |
| `Permission denied` | Düğüm `0600` ve root değilsin | Root ol; kalıcı çözüm için `mdev.conf` / `udev` kuralıyla izni değiştir |
| `rmmod: ... Resource temporarily unavailable` | Aygıt bir süreçte açık (`owner = THIS_MODULE`) | Aygıtı kullanan programı kapat (`fuser /dev/bbbmsg`) |
| `insmod`'da `-EBUSY` / `-EEXIST`, `dmesg`'te `sysfs: cannot create duplicate filename '/class/bbbmsg'` | Önceki yükleme init'te yarıda kaldı ve sınıfı bırakmadı | Hata yolunu (`goto err_...`) kontrol et; kartı yeniden başlat |
| Program `Inappropriate ioctl for device` alıyor | Komut numarası sürücüdekiyle aynı değil | Sürücü ve program aynı `bbbmsg.h`'yi kullanmalı; ikisini birlikte yeniden derle |
| Kernel `Oops`, `Unable to handle kernel paging request` | Kullanıcı adresine `memcpy` ile erişildi ya da tampon taşırıldı | `copy_*_user` kullan, `count`'u tampon boyutuyla sınırla |
| `implicit declaration of function 'class_create'` / argüman sayısı hatası | Kernel 6.4+ ile derleniyor | Koddaki `LINUX_VERSION_CODE` koşulu ([22.3](#223-aygıtı-kaydetmek-numara-cdev-class)) |
