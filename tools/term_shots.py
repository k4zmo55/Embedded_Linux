"""Linux terminal görünümlü PNG ekran görüntüleri üretir.

Satır biçimi: her satır [(metin, renk), ...] listesidir.
Sürüm, IP gibi değerler book.toml'den V("grup.isim") ile okunur.
Çıktı klasörü: komut satırında verilirse o, verilmezse betiğin set_default_out() ile seçtiği klasör.
"""
import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from book import ROOT, load_config  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else None
_VARS = load_config()[1]


def V(key):
    """book.toml'deki [vars] değeri, ör. V("network.host_ip")."""
    return _VARS[key]


PB_UBOOT = V("prebuilt.uboot_version")
KVER = V("prebuilt.kernel_version")


def set_default_out(path):
    global OUT
    if OUT is None:
        OUT = str(ROOT / path)
    os.makedirs(OUT, exist_ok=True)

FONT = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 20)
FONT_B = ImageFont.truetype(r"C:\Windows\Fonts\consolab.ttf", 20)
TITLE_FONT = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 16)

BG = (30, 30, 36)
BAR = (52, 52, 60)
FG = (220, 220, 220)
DIM = (130, 135, 145)
GREEN = (120, 220, 110)
BLUE = (110, 170, 255)
YELLOW = (240, 200, 90)
CYAN = (100, 215, 215)
RED = (255, 110, 100)
MAGENTA = (210, 140, 230)
ORANGE = (255, 160, 80)

P_UBOOT = ("U-Boot# ", YELLOW)
P_HOST = [("mehmet@ubuntu", GREEN), (":", FG), ("~/bbb", BLUE), ("$ ", FG)]
P_BBB = [("root@beaglebone", GREEN), (":", FG), ("~", BLUE), ("# ", FG)]


def ub(cmd):
    return [P_UBOOT, (cmd, FG)]


def host(cmd):
    return P_HOST + [(cmd, FG)]


def bbb(cmd):
    return P_BBB + [(cmd, FG)]


def t(text, color=FG):
    return [(text, color)]


def render(name, title, lines, min_cols=72):
    cw = FONT.getbbox("M")[2]
    lh = 27
    cols = max([min_cols] + [sum(len(s) for s, _ in ln) for ln in lines])
    pad_x, pad_y, bar_h = 22, 18, 36
    w = pad_x * 2 + cols * cw
    h = bar_h + pad_y * 2 + lh * len(lines)

    # Gölge için kenar boşluklu tuval
    m = 14
    img = Image.new("RGB", (w + 2 * m, h + 2 * m), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((m + 3, m + 5, m + w + 3, m + h + 5), 12, fill=(205, 205, 210))
    d.rounded_rectangle((m, m, m + w, m + h), 12, fill=BG)
    d.rounded_rectangle((m, m, m + w, m + bar_h + 12), 12, fill=BAR)
    d.rectangle((m, m + bar_h, m + w, m + bar_h + 12), fill=BG)

    for i, c in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
        cx = m + 20 + i * 22
        d.ellipse((cx - 6, m + bar_h / 2 - 6, cx + 6, m + bar_h / 2 + 6), fill=c)
    tw = d.textlength(title, font=TITLE_FONT)
    d.text((m + (w - tw) / 2, m + bar_h / 2 - 9), title, font=TITLE_FONT, fill=(200, 200, 205))

    y = m + bar_h + pad_y
    for ln in lines:
        x = m + pad_x
        for seg, color in ln:
            font = FONT_B if color in (YELLOW, GREEN) else FONT
            d.text((x, y), seg, font=font, fill=color)
            x += len(seg) * cw
        y += lh

    path = os.path.join(OUT, name)
    img.save(path, optimize=True)
    print(path, img.size)


def main():
    MINICOM = "mehmet@ubuntu: ~/bbb — minicom -D /dev/ttyUSB0 -b 115200"

    # 1) Bilgisayarda uEnv.txt'yi hazırlama
    render("01_uenv_hazirla.png", "mehmet@ubuntu: ~/bbb", [
        host("cat uEnv.txt"),
        t("mypcip=setenv serverip 192.168.1.2", CYAN),
        t("ipaddr=192.168.27.1", CYAN),
        t("bootargs=console=ttyO0,115200 root=/dev/mmcblk0p2 rw", CYAN),
        t('bootcmd=echo "**********Booting from memory**********";load mmc 0:1 0x82000000', CYAN),
        t("uImage;load mmc 0:1 0x88000000 am335x-boneblack.dtb;bootm 0x82000000 - 0x88000000", CYAN),
        host("ls -l uEnv.txt"),
        t("-rw-rw-r-- 1 mehmet mehmet 269 Eki 16 17:05 uEnv.txt"),
        host("sudo minicom -D /dev/ttyUSB0 -b 115200"),
    ])

    # 2) U-Boot'u durdurma
    render("02_uboot_durdur.png", MINICOM, [
        t(f"U-Boot SPL {PB_UBOOT} (Oct 16 2026 - 10:12:41)", DIM),
        t("reading u-boot.img", DIM),
        t(""),
        t(f"U-Boot {PB_UBOOT} (Oct 16 2026 - 10:12:41)", FG),
        t(""),
        t("I2C:   ready"),
        t("DRAM:  512 MiB"),
        t("MMC:   OMAP SD/MMC: 0, OMAP SD/MMC: 1"),
        t("Net:   cpsw, usb_ether"),
        [("Hit any key to stop autoboot:  ", FG), ("0", ORANGE), ("    <-- herhangi bir tuşa bas", MAGENTA)],
        ub(""),
    ])

    # 3) loady ile YMODEM alımı
    render("03_loady.png", MINICOM, [
        ub("loady 0x82000000"),
        t("## Ready for binary (ymodem) download to 0x82000000 at 115200 bps..."),
        t("C", DIM),
        t("+-----------[ YMODEM upload - Press CTRL-C to quit ]-----------+", BLUE),
        t("| Sending: uEnv.txt                                            |", BLUE),
        t("| Bytes Sent:    269   BPS:189                                 |", BLUE),
        t("| Sending:                                                     |", BLUE),
        t("| Ymodem sectors/kbytes sent:   0/ 0k                          |", BLUE),
        t("| Transfer complete                                            |", GREEN),
        t("+--------------------------------------------------------------+", BLUE),
        t("## Total Size      = 0x0000010D = 269 Bytes", YELLOW),
        ub(""),
    ])

    # 4) env import ve kontrol
    render("04_env_import.png", MINICOM, [
        ub("env import -t 0x82000000 ${filesize}"),
        ub("printenv bootargs"),
        t("bootargs=console=ttyO0,115200 root=/dev/mmcblk0p2 rw", CYAN),
        ub("printenv bootcmd"),
        t('bootcmd=echo "**********Booting from memory**********";load mmc 0:1 0x82000000', CYAN),
        t("uImage;load mmc 0:1 0x88000000 am335x-boneblack.dtb;bootm 0x82000000 - 0x88000000", CYAN),
        ub("run mypcip"),
        ub("printenv serverip"),
        t("serverip=192.168.1.2", CYAN),
        ub(""),
    ])

    # 5) boot
    render("05_boot.png", MINICOM, [
        ub("boot"),
        t("**********Booting from memory**********", ORANGE),
        t("reading uImage"),
        t("4380760 bytes read in 245 ms (17.1 MiB/s)"),
        t("reading am335x-boneblack.dtb"),
        t("24884 bytes read in 9 ms (2.6 MiB/s)"),
        t("## Booting kernel from Legacy Image at 82000000 ..."),
        t(f"   Image Name:   Linux-{KVER}"),
        t("   Image Type:   ARM Linux Kernel Image (uncompressed)"),
        t("## Flattened Device Tree blob at 88000000"),
        t("   Loading Device Tree to 8fff6000, end 8ffff133 ... OK"),
        t(""),
        t("Starting kernel ...", GREEN),
    ])

    # 6) MMC aygıtlarını doğrulama
    render("06_mmc_list.png", MINICOM, [
        ub("mmc list"),
        t("OMAP SD/MMC: 0       <-- mmc 0 : microSD kart", FG),
        t("OMAP SD/MMC: 1       <-- mmc 1 : dahili eMMC", FG),
        ub("mmc dev 1"),
        t("mmc1(part 0) is current device"),
        ub("mmc part"),
        t(""),
        t("Partition Map for MMC device 1  --   Partition Type: DOS"),
        t(""),
        t("Part    Start Sector    Num Sectors     UUID            Type", DIM),
        t("  1     2048            196608          00000000-01     0c Boot"),
        [("  2     198656          7266304         00000000-02     83", FG), ("   <-- rootfs", MAGENTA)],
        ub(""),
    ])

    # 7) bootargs'ı eMMC rootfs'e çevirme
    render("07_bootargs_emmc.png", MINICOM, [
        ub("printenv bootargs"),
        [("bootargs=console=ttyO0,115200 root=", CYAN), ("/dev/mmcblk0p2", RED), (" rw", CYAN)],
        ub("setenv bootargs console=ttyO0,115200 root=/dev/mmcblk1p2 rw"),
        ub("printenv bootargs"),
        [("bootargs=console=ttyO0,115200 root=", CYAN), ("/dev/mmcblk1p2", GREEN), (" rw", CYAN)],
        ub("boot"),
        t("**********Booting from memory**********", ORANGE),
        t("reading uImage"),
        t("..."),
        t("Starting kernel ...", GREEN),
    ])

    # 8) Linux'ta doğrulama
    render("08_linux_dogrula.png", "root@beaglebone: ~ (seri konsol)", [
        bbb("cat /proc/cmdline"),
        t("console=ttyO0,115200 root=/dev/mmcblk1p2 rw"),
        bbb("lsblk"),
        t("NAME         MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT", DIM),
        t("mmcblk0      179:0    0  7.4G  0 disk"),
        t("|-mmcblk0p1  179:1    0   96M  0 part"),
        t("`-mmcblk0p2  179:2    0  7.3G  0 part"),
        t("mmcblk1      179:8    0  3.6G  0 disk"),
        t("|-mmcblk1p1  179:9    0   96M  0 part"),
        [("`-mmcblk1p2  179:10   0  3.5G  0 part ", FG), ("/", GREEN), ("          <-- rootfs eMMC'de", MAGENTA)],
        bbb("findmnt /"),
        t("TARGET SOURCE         FSTYPE OPTIONS", DIM),
        t("/      /dev/mmcblk1p2 ext4   rw,relatime"),
    ])


if __name__ == "__main__":
    set_default_out("images/uenv")
    main()
