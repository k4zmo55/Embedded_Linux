# Bölüm 2 — Seri Konsol ve Minicom

> <b>Bu bölümde:</b>
> - USB-TTL dönüştürücüyü bilgisayara tanıtıp port adını (`/dev/ttyUSB0`) bulacaksın.
> - Minicom'u kurup {{board.name}} için doğru ayarlarla (115200 8N1, flow control kapalı) kaydedeceksin.
> - Minicom'un sık kullanılan kısayollarını ve Windows'taki karşılığı Tera Term'i öğreneceksin.
>
> <b>Ön koşul:</b> [Bölüm 1](01_bbb_hardware.md) — J1 debug header'ının pinleri.

---

## 2.1 Seri Konsol Neden Önemli?

Kart açılırken ekrana bir şey basan ilk programlar (ROM Code, SPL, U-Boot) HDMI veya ağ kullanmaz. Bütün mesajlarını <b>UART0</b> üzerinden, yani J1 header'ından gönderirler. Bu mesajları görmenin ve U-Boot'a komut yazmanın tek yolu seri konsoldur:

```
[Klavye] ⇄ [minicom / Tera Term] ⇄ USB-TTL kablo ⇄ J1 (UART0) ⇄ [BeagleBone: ROM / SPL / U-Boot / Linux]
```

Bilgisayardaki program sadece bir penceredir. Komutları bilgisayar değil, <b>kartın üzerindeki</b> program (U-Boot veya Linux) çalıştırır.

## 2.2 Minicom'u Kur

<b>Minicom</b>, Linux'ta kullanılan bir seri port terminal programıdır. `lrzsz` paketi de Minicom'un Xmodem/Ymodem ile dosya göndermesi için gerekir ([Bölüm 6](06_uboot_uenv.md) ve [Bölüm 7](07_uart_boot.md)'de kullanacağız):

```bash
sudo apt update
sudo apt install minicom lrzsz
```

## 2.3 USB-TTL Dönüştürücünün Port Adını Bul

USB-TTL dönüştürücüyü bilgisayara tak ve terminalde şunu çalıştır:

```bash
sudo dmesg | grep tty
```

Çıktı aşağıdakine benzer olmalı:

![dmesg çıktısında USB-TTL dönüştürücü](../images/{D08296A2-927C-4477-88AA-80FA9DC1250A}.png)

- Kernel, dönüştürücünün çipini tanıyıp sürücüsünü yükler. Bu örnekte çip <b>pl2303</b>. Senin dönüştürücünde <b>cp210x</b>, <b>ftdi_sio</b> veya <b>ch341</b> de yazabilir.
- Satırın sonundaki <b>`ttyUSB0`</b>, Minicom'da kullanacağımız portun adıdır: <b>`/dev/ttyUSB0`</b>.

Portu her seferinde `sudo` ile açmamak için kullanıcını `dialout` grubuna ekle (bir kez yapılır, sonra oturumu kapatıp açman gerekir):

```bash
sudo usermod -aG dialout $USER
```

## 2.4 Minicom Ayarlarını Yap

Ayar ekranını aç:

```bash
sudo minicom -s
```

Yön tuşlarıyla menüde gezinebilirsin. <b>Serial port setup</b>'ı seç:

![minicom -s ana menüsü](../images/{F27FC9A5-A70D-479E-9FE1-A48AF82142C0}.png)

Seri port ayarları ekranı açılır:

![Serial port setup ekranı](../images/{46E1CB74-A6AC-4373-91BD-4DC1CC8E5EF1}.png)

Bu ekranda her ayarın başında bir harf vardır. Değiştirmek istediğin ayarın harfine basarsın. Örneğin <b>Serial Device</b>'ı değiştirmek için <b>A</b>'ya bas. İmleç o satıra geçer:

![Serial Device ayarını düzenleme](../images/{230FE2DE-7BE6-49B2-B01E-2F294C2C15FE}.png)

Eski değeri silip `/dev/ttyUSB0` yaz ve <b>Enter</b>'a bas.

Baud rate'i değiştirmek için <b>E</b>'ye bas. Hız ve veri formatı ekranı açılır:

![Baud rate ve veri formatı ekranı](../images/{D297BD35-EB7C-4410-B431-A8B84BC48A9D}.png)

Bu ekranda da her seçeneğin bir harfi var. Örneğin <b>D</b>'ye basınca hız 38400 olur:

![Baud rate 38400 seçildi](../images/{E3A60A5C-888D-4802-8A22-C1E6AC50C300}.png)

Biz {{board.name}} için <b>115200</b> seçeceğiz. Bu ekrandaki harflerle hızı 115200, formatı <b>8N1</b> (8 bit, parity yok, 1 stop bit) yap ve Enter ile çık.

Ayarların son hali:

| Ayar | Değer |
|---|---|
| Serial Device | `/dev/ttyUSB0` |
| Bps/Par/Bits | `115200 8N1` |
| Hardware Flow Control | <b>No</b> |
| Software Flow Control | <b>No</b> |

> [!IMPORTANT]
> {{board.name}}'in seri hattında <b>CTS</b> ve <b>RTS</b> pinleri yoktur. Bu yüzden <b>Hardware Flow Control</b> kullanılamaz ve <b>No</b> olmalıdır. Yes kalırsa ekranda kartın mesajlarını görürsün ama klavyeden yazdıkların karta gitmez. <b>Software Flow Control</b> da <b>No</b> kalsın.

Ayarları bitirince ana menüye dön ve <b>Save setup as dfl</b>'yi seç. Böylece ayarlar varsayılan olarak kaydedilir ve her seferinde yeniden yapman gerekmez. Sonra <b>Exit</b> ile ayar ekranından çık:

![Save setup as dfl](../images/{25B687AC-C882-4EAD-82C6-B4EA24B58170}.png)

## 2.5 Minicom'u Kullanmak

Ayarları kaydettikten sonra Minicom'u doğrudan açabilirsin. Ayarları komut satırında açıkça vermek de mümkün:

```bash
minicom                                  # kayıtlı ayarlarla aç
minicom -D /dev/ttyUSB0 -b 115200        # portu ve hızı açıkça ver
```

Minicom'da bütün kısayollar önce <b>`Ctrl-A`</b>, ardından bir harf ile kullanılır:

| Kısayol | Görevi |
|---|---|
| `Ctrl-A` → `Z` | Yardım: bütün kısayolların listesi |
| `Ctrl-A` → `S` | Dosya gönder (xmodem / ymodem). [Bölüm 6](06_uboot_uenv.md) ve [Bölüm 7](07_uart_boot.md)'de kullanılır. |
| `Ctrl-A` → `P` | Baud rate'i değiştir |
| `Ctrl-A` → `O` | Ayar menüsü (`minicom -s` ile aynı) |
| `Ctrl-A` → `C` | Ekranı temizle |
| `Ctrl-A` → `X` | Minicom'dan çık |

> [!TIP]
> Minicom'u kartı açmadan <b>önce</b> başlat. Böylece açılıştaki ilk mesajları (SPL, U-Boot) kaçırmazsın.

## 2.6 Windows'ta: Tera Term

Kursun bazı derslerinde Windows'ta <b>Tera Term</b> kullanılıyor. Bu bir zorunluluk değil, Tera Term de Minicom gibi bir seri terminal programıdır. Hangisini kullanırsan kullan, komutlar ve çıktılar aynıdır.

| | Linux | Windows |
|---|---|---|
| Program | `minicom` | Tera Term |
| Port adı | `/dev/ttyUSB0` | `COM3` gibi (Aygıt Yöneticisi → Bağlantı Noktaları'na bak) |
| Ayarlar | 115200, 8N1, flow control yok | Setup → Serial port: 115200, 8 bit, none, 1 stop, Flow control: none |

## 2.7 Özet

| Ne? | Komut / Değer |
|---|---|
| Kurulum | `sudo apt install minicom lrzsz` |
| Port adını bulmak | `sudo dmesg \| grep tty` → `/dev/ttyUSB0` |
| Ayarlar | `sudo minicom -s` → 115200 8N1, Hardware/Software Flow Control: <b>No</b> → Save setup as dfl |
| Açmak | `minicom -D /dev/ttyUSB0 -b 115200` |
| Çıkmak | `Ctrl-A` → `X` |

## 2.8 Karşılaşılabilecek Problemler

| Belirti | Sebep | Çözüm |
|---|---|---|
| `cannot open /dev/ttyUSB0: Permission denied` | Kullanıcın `dialout` grubunda değil | `sudo usermod -aG dialout $USER`, sonra oturumu kapatıp aç |
| `dmesg`'de `ttyUSB` hiç görünmüyor | Kablo/sürücü sorunu ya da sanal makine USB'yi görmüyor | Başka USB portu dene. Sanal makinedeysen USB aygıtını VM'e bağla (VirtualBox: Devices → USB). |
| Ekranda hiçbir şey yok | TX/RX düz bağlanmış ya da GND bağlı değil | Dönüştürücünün TX'i → kartın RX'i (J1 pin 4), RX'i → kartın TX'i (J1 pin 5), GND → pin 1 ([1.8](01_bbb_hardware.md#18-seri-debug-header-j1)) |
| Anlamsız / bozuk karakterler | Baud rate yanlış | 115200 8N1 olmalı |
| Mesajlar geliyor ama yazdıklarım gitmiyor | Hardware Flow Control açık | `minicom -s` → Serial port setup → Hardware Flow Control: <b>No</b> |
| `sx: not found` (dosya gönderirken) | `lrzsz` kurulu değil | `sudo apt install lrzsz` |
