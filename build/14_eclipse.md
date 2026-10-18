<!-- Bu dosya otomatik üretildi. Düzenlemek için chapters/ altındaki kaynağı değiştir. -->
# Bölüm 14 — Eclipse ile Uygulama Geliştirme

> <b>Bu bölümde:</b>
> - Eclipse'i (2026-09) kurup [Bölüm 9](09_uboot_build.md)'daki cross toolchain'e bağlayacaksın.
> - Bir C projesi oluşturup ARM için derleyeceksin ve derleme ayarlarını öğreneceksin.
> - Programı Eclipse'ten tek tıkla karta gönderip çalıştıracaksın.
> - Kursun hazır Eclipse projelerini içe aktaracaksın.
>
> <b>Ön koşul:</b> [Bölüm 9](09_uboot_build.md) — cross toolchain, kartta SSH ile bağlanılabilen bir Linux ([Bölüm 5](05_emmc_boot.md)'teki Debian ya da [Bölüm 13](13_buildroot.md)'teki Buildroot sistemi).

---

## 14.1 Neden Eclipse?

Şimdiye kadar her şeyi terminalden derledik. Kendi uygulamalarını yazmaya başladığında bir IDE işini kolaylaştırır: kod tamamlama, hataların satırında gösterilmesi, tek tuşla derleme ve programı karta gönderip çalıştırma.

```
 Host PC (Eclipse)                                       BeagleBone Black
 ┌──────────────────────────────────────┐   SSH + SFTP   ┌──────────────────────┐
 │ kodu yaz → Cross GCC ile derle       │ ─────────────► │ /home/debian/program │
 │ (arm-linux-gnueabihf-gcc)            │ ◄───────────── │ çalışır, çıktısı     │
 │ Console'da çıktıyı gör               │    çıktı       │ Eclipse'e döner      │
 └──────────────────────────────────────┘                └──────────────────────┘
```

Eclipse kendisi derlemez. Arka planda [Bölüm 9](09_uboot_build.md)'da kurduğun `arm-linux-gnueabihf-gcc`'yi çağırır. Bu yüzden komut satırında öğrendiğin her şey burada da geçerlidir.

> [!NOTE]
> Kurs bu bölümü <b>Windows</b> üzerinde anlatıyor; kitapta Ubuntu kullanılıyor. Adımlar iki sistemde de aynıdır, farkları [14.3](#143-eclipsei-kurmak)'te belirtildi.

---

## 14.2 Kursa Göre Değişenler

| Kursta | Bugün (2026-09) |
|---|---|
| Önce <b>Java JDK</b> kurulur, Eclipse onsuz açılmaz | Eclipse paketleri <b>kendi Java'sıyla (JRE)</b> gelir. Ayrıca Java kurmana gerek yok. |
| Uygulama karta <b>Remote System Explorer (RSE)</b> ile gönderilir | RSE artık Eclipse'in C/C++ araçlarıyla gelmiyor. Aynı işi CDT'nin <b>C/C++ Remote Launch</b> özelliği SSH üzerinden yapar ([14.6](#146-uygulamayı-kartta-çalıştırmak)). |

---

## 14.3 Eclipse'i Kurmak

<b>1) İndir.</b> <https://www.eclipse.org/downloads/packages/> adresinden <b>Eclipse IDE for C/C++ Developers</b> paketini, işletim sistemine uygun olanı indir. ("Eclipse IDE for Embedded C/C++ Developers" paketi de olur; o, mikrodenetleyiciler için ek araçlar içerir.)

<b>2) Aç ve çalıştır.</b>

```bash
cd ~
tar -xzf ~/Downloads/eclipse-cpp-2026-09-R-linux-gtk-x86_64.tar.gz
~/eclipse/eclipse &
```

İlk açılışta bir <b>workspace</b> (projelerin duracağı klasör) sorar. Varsayılan `~/eclipse-workspace` uygundur.

<b>3) Cross toolchain'in hazır olduğunu kontrol et.</b> Eclipse'in toolchain'i bulabilmesi için tam yolunu bilmen gerekir:

![Toolchain'in yolunu bulma](../images/eclipse/01_toolchain_check.png)

```bash
which arm-linux-gnueabihf-gcc
```

| Host | Toolchain |
|---|---|
| Ubuntu | [9.3](09_uboot_build.md#93-adım-adım-toolchain-kurulumu-ve-u-boot-derleme)'te kurduğun Linaro toolchain: `~/bbb/gcc-linaro-7.5.0-2019.12-x86_64_arm-linux-gnueabihf/bin` |
| Windows | Linaro'nun Windows sürümü: `gcc-linaro-7.5.0-2019.12-i686-mingw32_arm-linux-gnueabihf.tar.xz` ([indir](https://releases.linaro.org/components/toolchain/binaries/7.5-2019.12/arm-linux-gnueabihf/gcc-linaro-7.5.0-2019.12-i686-mingw32_arm-linux-gnueabihf.tar.xz)). Bir klasöre aç; içindeki `bin` klasörünün yolu Eclipse'e verilecek. Windows'ta `make` de gerekir (ör. MSYS2 veya "Windows Build Tools"). |

<b>4) Gerekli eklentileri kontrol et.</b> <i>Help → About Eclipse IDE → Installation Details</i> listesinde şu iki özellik olmalı. Yoksa <i>Help → Install New Software</i>'da <i>Work with</i> kutusuna `https://download.eclipse.org/releases/2026-09/` yaz ve aratıp kur:

| Özellik | Ne işe yarar? |
|---|---|
| <b>C/C++ GCC Cross Compiler Support</b> | Proje sihirbazındaki "Cross GCC" araç zinciri |
| <b>C/C++ Remote Launch</b> | Programı SSH ile karta gönderip çalıştırma |

---

## 14.4 Birinci Proje: Oluşturma ve Derleme

Kursun "Eclipse project creation and build settings" dersi.

### Adım 1 — Projeyi oluştur

<i>File → New → C/C++ Project → C Managed Build</i>, sonra:

| Alan | Değer |
|---|---|
| Project name | `hello_bbb` |
| Project type | Executable → <b>Hello World ANSI C Project</b> |
| Toolchains | <b>Cross GCC</b> |

<i>Next</i> ile ilerle. <b>Cross GCC Command</b> sayfasında:

| Alan | Değer |
|---|---|
| Cross compiler prefix | `arm-linux-gnueabihf-` (sondaki `-` dahil) |
| Cross compiler path | Toolchain'in `bin` klasörü, ör. `/home/<kullanıcı>/bbb/gcc-linaro-7.5.0-2019.12-x86_64_arm-linux-gnueabihf/bin` |

<i>Finish</i>'e bas. Eclipse `src/hello_bbb.c` dosyasını oluşturur. İçeriğini kartta çalıştığını gösterecek şekilde değiştir:

```c
#include <stdio.h>
#include <sys/utsname.h>

int main(void)
{
	struct utsname u;

	printf("Merhaba BeagleBone! (Eclipse'ten uzaktan çalıştırıldı)\n");
	if (uname(&u) == 0)
		printf("Kernel: %s %s %s %s\n", u.sysname, u.nodename, u.release, u.machine);
	return 0;
}
```

### Adım 2 — Derle

<i>Project → Build Project</i> (veya çekiç simgesi). <b>Console</b> görünümünde Eclipse'in çağırdığı komutları görürsün:

![Eclipse'in derleme konsolu](../images/eclipse/02_build_console.png)

Eclipse proje klasöründe bir `Debug/` klasörü ve içine kendi `makefile`'ını üretir. Çıktının gerçekten ARM için olduğunu terminalden doğrulayabilirsin:

![Çıktının ARM için derlendiğini doğrulama](../images/eclipse/03_file_check.png)

```bash
file ~/eclipse-workspace/hello_bbb/Debug/hello_bbb
```

### Derleme ayarları

<i>Project → Properties → C/C++ Build → Settings → Tool Settings</i>:

| Bölüm | Ne ayarlanır? |
|---|---|
| <b>Cross Settings</b> | <b>Prefix</b> ve <b>Path</b>: hangi toolchain kullanılacak. Toolchain'i taşıdıysan ya da başka bir bilgisayardan proje aldıysan burayı düzelt. |
| Cross GCC Compiler → Optimization | `-O0` (Debug) / `-O2` (Release) |
| Cross GCC Compiler → Warnings | `-Wall` (tüm uyarılar) |
| Cross GCC Compiler → Includes | Ek başlık klasörleri (`-I`) |
| Cross GCC Linker → Libraries | Bağlanacak kütüphaneler (ör. `m` → `-lm`, `pthread`) |
| Cross GCC Linker → Miscellaneous → Linker flags | Ek bağlayıcı seçenekleri. Programı <b>`-static`</b> derlemek için buraya yaz ([14.5](#145-karttaki-sistemle-uyum-dinamik-mi-statik-mi)). |

Üst kısımdaki <b>Configuration</b> kutusu <b>Debug</b> ve <b>Release</b> arasında seçim yapar. Her yapılandırmanın kendi ayarları ve kendi çıktı klasörü vardır.

---

## 14.5 Karttaki Sistemle Uyum: Dinamik mi, Statik mi?

Eclipse varsayılan olarak <b>dinamik</b> bağlanmış program üretir. Dinamik program kartta çalışırken iki koşul sağlanmalı ([12.11](12_busybox_rootfs.md#1211-challenge-2-busyboxı-dinamik-derlemek)):

| Karttaki sistem | Dinamik program çalışır mı? | Ne yapmalı? |
|---|---|---|
| eMMC'deki Debian ([Bölüm 5](05_emmc_boot.md)) | Genelde evet | Toolchain'in glibc'si karttakinden <b>eski veya aynı</b> olmalı. Kartta `ldd --version` ile bak. |
| Buildroot ([Bölüm 13](13_buildroot.md)) | Buildroot'un kendi toolchain'iyle derlenirse evet | Cross Settings'te Path = `output/host/bin`, Prefix = `arm-buildroot-linux-gnueabihf-` |
| BusyBox (statik) rootfs ([Bölüm 12](12_busybox_rootfs.md)) | Hayır, `/lib`'te kütüphane yok | Linker flags'e `-static` ekle ya da kütüphaneleri kopyala |

> [!TIP]
> Emin değilsen `-static` ile derle. Program biraz büyür ama karttaki kütüphanelere bağımlı olmaz, her rootfs'te çalışır.

---

## 14.6 Uygulamayı Kartta Çalıştırmak

Kursun "Installing Remote System Explorer and Testing Application" dersi. Eclipse programı <b>SSH</b> ile karta kopyalar, çalıştırır ve çıktısını Console'da gösterir.

> [!IMPORTANT]
> Dosya kopyalama için kartta bir <b>SFTP sunucusu</b> olmalı.
> - Debian'da OpenSSH ile birlikte gelir, ek bir şey gerekmez.
> - Buildroot'ta Dropbear tek başına SFTP sunmaz. <i>Target packages → Networking applications</i>'dan <b>gesftpserver</b> paketini de ekle (ya da Dropbear yerine `openssh` seç).

### Adım 1 — Bağlantı ve çalıştırma ayarı

<i>Run → Run Configurations...</i> → sol listede <b>C/C++ Remote Application</b>'a sağ tık → <i>New Configuration</i>:

| Alan | Değer |
|---|---|
| Project / C/C++ Application | `hello_bbb` / `Debug/hello_bbb` |
| Connection | <i>New...</i> → <b>SSH</b> → Host: `192.168.27.2`, User: `debian`, şifre |
| Remote Absolute File Path for C/C++ Application | `/home/debian/hello_bbb` |
| Commands to execute before application | Boş bırakabilirsin |
| Skip download to target path | İşaretleme (her çalıştırmada yeni derlenen dosya kopyalansın) |

> [!NOTE]
> Kartın IP'si bağlantı yöntemine göre değişir: Ethernet ile `192.168.27.2` ([8.4](08_tftp_boot.md#84-bağlantılar)), USB ile Debian'da `192.168.7.2` / `192.168.6.2` ([5.4.1](05_emmc_boot.md#541-kartın-ip-adresini-öğren)). Buildroot'ta kullanıcı `root`'tur.

### Adım 2 — Çalıştır

<i>Run</i>'a bas. Eclipse programı `/home/debian/` altına kopyalar, çalıştırılabilir yapar ve çalıştırır:

![Eclipse'ten kartta çalıştırma](../images/eclipse/04_remote_run.png)

Bundan sonra yeşil <i>Run</i> düğmesi bu ayarı hatırlar: kodu değiştir, kaydet, <i>Run</i>'a bas. Eclipse önce derler, sonra karta gönderip çalıştırır.

> [!TIP]
> Kartın dosyalarını görmek ve kartta kabuk açmak için <i>Window → Show View → Other...</i>'dan <b>Connections</b> ve <b>Terminal</b> görünümlerini aç. Kursta RSE'nin "Remote Systems" görünümüyle yapılan dosya gezme ve terminal işlerini bunlar karşılar.

### Eclipse olmadan: `scp` + `ssh`

Aynı işi terminalden de yapabilirsin. Bir şey ters giderse sorunun Eclipse'te mi, kartta mı olduğunu anlamak için iyi bir testtir:

![scp ve ssh ile elle çalıştırma](../images/eclipse/05_manual_scp.png)

```bash
scp Debug/hello_bbb debian@192.168.27.2:~/
ssh debian@192.168.27.2 ./hello_bbb
```

---

## 14.7 Kursun Projelerini Eclipse'e Aktarmak

Kursun "Importing Eclipse Projects" dersi. Kursun reposundaki `Project_Src/` klasörü sonraki bölümlerin bütün uygulamalarını içeriyor.

<b>1) Repoyu indir:</b>

```bash
cd ~
git clone https://github.com/niekiran/EmbeddedLinuxBBB.git
```

<b>2) İçe aktar:</b> <i>File → Import → General → Existing Projects into Workspace</i> → <i>Select root directory</i>: `~/EmbeddedLinuxBBB/Project_Src` → istediğin projeleri işaretle → <i>Copy projects into workspace</i>'i işaretle → <i>Finish</i>.

<b>3) Toolchain yolunu düzelt.</b> Projelerdeki <b>Path</b> eğitmenin bilgisayarındaki yolu gösterir. Her proje için <i>Properties → C/C++ Build → Settings → Cross Settings → Path</i>'i kendi toolchain klasörünle değiştir. Prefix (`arm-linux-gnueabihf-`) zaten doğru.

<b>4) Temiz derle:</b> <i>Project → Clean...</i>, sonra <i>Build Project</i>. Repoda eğitmenin derlediği eski `Debug/` dosyaları da var; temizlemek bunları siler.

| Proje | Ne yapar? | Kursta |
|---|---|---|
| `BBB_led_control` | Kartın USR3 LED'ini sysfs ile kontrol eder | AM335x GPIO ve sysfs |
| `counter_7seg`, `button_counter_7seg` | Tek haneli 7-segment gösterge, sayıcı | 7-segment gösterge |
| `4digitcount` | 4 haneli 7-segment sayıcı | 4 haneli 7-segment |
| `MPU6050_raw_read` | I2C ile ivmeölçer/jiroskop okuma | MPU6050 |
| `lcd_text`, `lcd_scrollable_text`, `lcd_news` | 16x2 LCD'ye yazı yazma | 16x2 LCD |
| `Drivers/gpio`, `Drivers/lcd` | Projelerin ortak kullandığı GPIO ve LCD fonksiyonları | — |

> [!NOTE]
> Repodaki `.metadata` ve `RemoteSystemsTempFiles` klasörleri eğitmenin Eclipse çalışma alanına ait. İçe aktarırken bunları seçme.

---

## 14.8 Özet

- Eclipse (Eclipse IDE for C/C++ Developers) Java'sıyla birlikte gelir. Gereken eklentiler: <b>C/C++ GCC Cross Compiler Support</b> ve <b>C/C++ Remote Launch</b>.
- Proje: <i>C Managed Build → Executable → Cross GCC</i>. Toolchain'i <b>Prefix</b> (`arm-linux-gnueabihf-`) ve <b>Path</b> (`.../bin`) belirler.
- Karta gönderip çalıştırma: <i>Run Configurations → C/C++ Remote Application</i>, SSH bağlantısı; kartta SFTP sunucusu gerekir.
- Karttaki rootfs'te kütüphane yoksa ya da glibc eskiyse programı `-static` derle.
- Kursun projeleri: <i>Import → Existing Projects into Workspace</i>, sonra Cross Settings → Path'i düzelt.

## 14.9 Karşılaşılabilecek Problemler

![Sık görülen hatalar (temsili)](../images/eclipse/06_errors.png)

| Belirti | Sebep | Çözüm |
|---|---|---|
| `Program "arm-linux-gnueabihf-gcc" not found in PATH` | Cross Settings → Path yanlış ya da boş | `which arm-linux-gnueabihf-gcc` çıktısının klasörünü yaz |
| Proje sihirbazında "Cross GCC" yok | C/C++ GCC Cross Compiler Support eklentisi kurulu değil | [14.3](#143-eclipsei-kurmak) Adım 4 |
| Run Configurations'ta "C/C++ Remote Application" yok | C/C++ Remote Launch eklentisi kurulu değil | [14.3](#143-eclipsei-kurmak) Adım 4 |
| `make: *** No rule to make target 'all'` | Proje "Makefile Project" türünde açılmış, Eclipse makefile üretmiyor | Projeyi "C Managed Build → Executable" olarak yeniden oluştur |
| Kartta `version 'GLIBC_2.xx' not found` | Toolchain'in glibc'si karttakinden yeni | Karttakiyle uyumlu toolchain kullan ya da `-static` |
| Kartta `./program: not found` (dosya varken) | Dinamik program, rootfs'te `/lib/ld-linux-armhf.so.3` yok | `-static` ile derle |
| `Error during file upload` | Kartta SFTP sunucusu yok | Buildroot'a `gesftpserver` ekle |
| `Permission denied` (çalıştırırken) | Dosya çalıştırılabilir değil ya da yanlış klasöre kopyalandı | Remote path'in kullanıcının yazabildiği bir yer olduğundan emin ol |
| Kartta `Exec format error` | Program ARM için değil, host için derlenmiş | Toolchain olarak Cross GCC seçildiğini, `file` çıktısında ARM yazdığını kontrol et |

---

[← Bölüm 13: Buildroot](13_buildroot.md) · [İçindekiler](README.md) · [Bölüm 15: AM335x GPIO'ları, Pin Ayarları ve sysfs →](15_gpio_sysfs.md)
