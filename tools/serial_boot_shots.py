"""Seri porttan boot notu için terminal ekran görüntülerini üretir.

Kullanım: python tools/serial_boot_shots.py images/serial_boot
"""
from term_shots import (render, ub, host, t, FG, DIM, GREEN, BLUE, YELLOW,
                        CYAN, RED, MAGENTA, ORANGE)
from term_shots import V, set_default_out

PB_UBOOT = V("prebuilt.uboot_version")
KVER = V("prebuilt.kernel_version")
set_default_out("images/serial_boot")

MINICOM = "mehmet@ubuntu: ~/bbb — minicom -D /dev/ttyUSB0 -b 115200"


def sh(cmd):
    return [("/ # ", GREEN), (cmd, FG)]


def note(text, color=FG, ann=""):
    return [(text, color), (ann, MAGENTA)] if ann else [(text, color)]


# 1) Bilgisayarda dosyaları kontrol etme
render("01_host_dosyalar.png", "mehmet@ubuntu: ~/bbb", [
    host("ls -l"),
    t("-rw-r--r-- 1 mehmet mehmet   24884 Eki 17 10:02 am335x-boneblack.dtb"),
    t("-rw-r--r-- 1 mehmet mehmet 1867312 Eki 17 10:05 initramfs"),
    t("-rw-r--r-- 1 mehmet mehmet  403524 Eki 17 09:58 u-boot.img"),
    note("-rw-r--r-- 1 mehmet mehmet   92612 Eki 17 09:58 u-boot-spl.bin", FG,
         "   <-- < 109 KB olmalı"),
    t("-rw-r--r-- 1 mehmet mehmet 4380760 Eki 17 10:01 uImage"),
    host("mkimage -l uImage"),
    t(f"Image Name:   Linux-{KVER}", CYAN),
    t("Image Type:   ARM Linux Kernel Image (uncompressed)", CYAN),
    t("Data Size:    4380696 Bytes = 4278.02 KiB = 4.18 MiB", CYAN),
    t("Load Address: 80008000", CYAN),
    t("Entry Point:  80008000", CYAN),
    host("mkimage -l initramfs"),
    t("Image Name:   initramfs", CYAN),
    note("Image Type:   ARM Linux RAMDisk Image (gzip compressed)", CYAN,
         "  <-- U-Boot başlığı var"),
    t("Data Size:    1867248 Bytes = 1823.48 KiB = 1.78 MiB", CYAN),
])

# 2) Seri kabloyu bulma ve izin
render("02_host_seri_port.png", "mehmet@ubuntu: ~/bbb", [
    host("sudo dmesg | tail -3"),
    t("[ 5121.33] usb 1-2: FTDI USB Serial Device converter detected", DIM),
    note("[ 5121.34] usb 1-2: FTDI USB Serial Device converter now attached to ttyUSB0",
         DIM, "  <--"),
    host("ls -l /dev/ttyUSB0"),
    t("crw-rw---- 1 root dialout 188, 0 Eki 17 10:10 /dev/ttyUSB0"),
    host("sudo usermod -aG dialout $USER     # bir kez; sonra oturumu kapat-aç"),
    host("sudo apt install minicom lrzsz      # lrzsz = sx / sb / rz programları"),
    host("which sx sb"),
    t("/usr/bin/sx"),
    t("/usr/bin/sb"),
    host("cd ~/bbb && minicom -D /dev/ttyUSB0 -b 115200"),
])

# 3) Minicom seri port ayarları
render("03_minicom_ayar.png", "minicom -s — Serial port setup", [
    t("+-----------------------------------------------------------------------+", BLUE),
    t("| A -    Serial Device      : /dev/ttyUSB0                              |", BLUE),
    t("| B - Lockfile Location     : /var/lock                                 |", BLUE),
    t("| C -   Callin Program      :                                           |", BLUE),
    t("| D -  Callout Program      :                                           |", BLUE),
    t("| E -    Bps/Par/Bits       : 115200 8N1                                |", BLUE),
    [("| F - Hardware Flow Control : ", BLUE), ("No", GREEN),
     ("                                        |", BLUE), ("  <-- mutlaka No", MAGENTA)],
    [("| G - Software Flow Control : ", BLUE), ("No", GREEN),
     ("                                        |", BLUE)],
    t("+-----------------------------------------------------------------------+", BLUE),
    t(""),
    t("Filenames and paths  ->  B - Upload directory : /home/mehmet/bbb", CYAN),
])

# 4) ROM kodu: CCCC ve SPL gönderimi (Xmodem)
render("04_rom_spl_xmodem.png", MINICOM, [
    note("CCCCCCCCCCCCCCCC", ORANGE, "      <-- ROM kodu UART0'da Xmodem bekliyor"),
    t(""),
    t("        Ctrl-A  S  ->  xmodem  ->  u-boot-spl.bin", MAGENTA),
    t(""),
    t("+-----------[xmodem upload - Press CTRL-C to quit]------------+", BLUE),
    t("|Sending u-boot-spl.bin, 724 blocks: Give your local XMODEM   |", BLUE),
    t("|receive command now.                                         |", BLUE),
    t("|Bytes Sent:  92672   BPS:10931                               |", BLUE),
    t("|Transfer complete                                            |", GREEN),
    t("+-------------------------------------------------------------+", BLUE),
    t(""),
    t(f"U-Boot SPL {PB_UBOOT} (Oct 17 2026 - 09:58:12)", FG),
    note("CCCCCCCC", ORANGE, "      <-- şimdi SPL, u-boot.img'i Ymodem ile bekliyor"),
])

# 5) U-Boot gönderimi (Ymodem) ve U-Boot komut satırı
render("05_spl_uboot_ymodem.png", MINICOM, [
    t("        Ctrl-A  S  ->  ymodem  ->  u-boot.img", MAGENTA),
    t(""),
    t("+-----------[ymodem upload - Press CTRL-C to quit]------------+", BLUE),
    t("|Sending: u-boot.img                                          |", BLUE),
    t("|Bytes Sent: 403524   BPS:11105                               |", BLUE),
    t("|Ymodem sectors/kbytes sent:   0/ 0k                          |", BLUE),
    t("|Transfer complete                                            |", GREEN),
    t("+-------------------------------------------------------------+", BLUE),
    t("Loaded 403524 bytes", DIM),
    t(""),
    t(f"U-Boot {PB_UBOOT} (Oct 17 2026 - 09:58:12)", FG),
    t(""),
    t("I2C:   ready"),
    t("DRAM:  512 MiB"),
    t("MMC:   OMAP SD/MMC: 0, OMAP SD/MMC: 1"),
    t("Net:   cpsw, usb_ether"),
    [("Hit any key to stop autoboot:  ", FG), ("0", ORANGE),
     ("    <-- hemen bir tuşa bas!", MAGENTA)],
    ub(""),
])

# 6) Kernel'i loadx ile alma
render("06_loadx_uimage.png", MINICOM, [
    ub("loadx 0x82000000"),
    t("## Ready for binary (xmodem) download to 0x82000000 at 115200 bps..."),
    t("C", DIM),
    t("        Ctrl-A  S  ->  xmodem  ->  uImage", MAGENTA),
    t("+-----------[xmodem upload - Press CTRL-C to quit]------------+", BLUE),
    t("|Sending uImage, 34225 blocks: Give your local XMODEM receive |", BLUE),
    t("|command now.                                                 |", BLUE),
    note("|Bytes Sent:4380800   BPS:11012                               |", BLUE,
         "  <-- ~6.5 dk sürer"),
    t("|Transfer complete                                            |", GREEN),
    t("+-------------------------------------------------------------+", BLUE),
    t("## Total Size      = 0x0042d880 = 4380800 Bytes", YELLOW),
    t("## Start Addr      = 0x82000000", YELLOW),
    ub(""),
])

# 7) DTB ve initramfs
render("07_loadx_dtb_initramfs.png", MINICOM, [
    ub("loadx 0x88000000"),
    t("## Ready for binary (xmodem) download to 0x88000000 at 115200 bps..."),
    t("        Ctrl-A  S  ->  xmodem  ->  am335x-boneblack.dtb", MAGENTA),
    t("|Transfer complete                                            |", GREEN),
    t("## Total Size      = 0x00006180 = 24960 Bytes", YELLOW),
    t("## Start Addr      = 0x88000000", YELLOW),
    ub("loadx 0x88080000"),
    t("## Ready for binary (xmodem) download to 0x88080000 at 115200 bps..."),
    t("        Ctrl-A  S  ->  xmodem  ->  initramfs", MAGENTA),
    t("|Transfer complete                                            |", GREEN),
    t("## Total Size      = 0x001c7e80 = 1867392 Bytes", YELLOW),
    t("## Start Addr      = 0x88080000", YELLOW),
    ub(""),
])

# 8) Yüklenenleri kontrol etme
render("08_iminfo_kontrol.png", MINICOM, [
    ub("iminfo 0x82000000"),
    t(""),
    t("## Checking Image at 82000000 ..."),
    t("   Legacy image found"),
    t(f"   Image Name:   Linux-{KVER}"),
    t("   Image Type:   ARM Linux Kernel Image (uncompressed)"),
    t("   Data Size:    4380696 Bytes = 4.2 MiB"),
    note("   Verifying Checksum ... OK", GREEN, "        <-- kernel sağlam geldi"),
    ub("iminfo 0x88080000"),
    t(""),
    t("## Checking Image at 88080000 ..."),
    t("   Legacy image found"),
    t("   Image Type:   ARM Linux RAMDisk Image (gzip compressed)"),
    t("   Data Size:    1867248 Bytes = 1.8 MiB"),
    note("   Verifying Checksum ... OK", GREEN, "        <-- initramfs sağlam geldi"),
    ub("md.b 0x88000000 4"),
    note("88000000: d0 0d fe ed    ....", FG, "              <-- DTB sihirli sayısı"),
    ub(""),
])

# 9) bootargs ve bootm
render("09_bootm.png", MINICOM, [
    ub("setenv bootargs console=ttyO0,115200 root=/dev/ram0 rw initrd=0x88080000"),
    ub("bootm 0x82000000 0x88080000 0x88000000"),
    t("## Booting kernel from Legacy Image at 82000000 ..."),
    t(f"   Image Name:   Linux-{KVER}"),
    t("   Verifying Checksum ... OK"),
    t("## Loading init Ramdisk from Legacy Image at 88080000 ..."),
    t("   Image Type:   ARM Linux RAMDisk Image (gzip compressed)"),
    t("   Verifying Checksum ... OK"),
    t("## Flattened Device Tree blob at 88000000"),
    t("   Booting using the fdt blob at 0x88000000"),
    t("   Loading Kernel Image ... OK"),
    t("   Loading Ramdisk to 8fe38000, end 8ffffdf0 ... OK"),
    t("   Loading Device Tree to 8fe2e000, end 8fe37133 ... OK"),
    t(""),
    t("Starting kernel ...", GREEN),
    t(""),
    t("[    0.000000] Booting Linux on physical CPU 0x0", DIM),
    t(f"[    0.000000] Linux version {KVER} (mehmet@ubuntu) (gcc 4.9) #1 SMP", DIM),
    note("[    0.000000] Kernel command line: console=ttyO0,115200 root=/dev/ram0 rw initrd=0x88080000",
         DIM),
    note("[    1.732050] Trying to unpack rootfs image as initramfs...", DIM,
         "  <-- initramfs"),
    t("[    2.104512] Freeing unused kernel memory: 380K", DIM),
])

# 10) Linux kabuğu
render("10_linux_shell.png", "BusyBox (initramfs) — seri konsol", [
    t("Please press Enter to activate this console.", CYAN),
    sh("cat /proc/cmdline"),
    t("console=ttyO0,115200 root=/dev/ram0 rw initrd=0x88080000"),
    sh("mount"),
    note("rootfs on / type rootfs (rw)", FG, "        <-- rootfs RAM'de"),
    t("proc on /proc type proc (rw,relatime)"),
    t("sysfs on /sys type sysfs (rw,relatime)"),
    sh("uname -a"),
    t(f"Linux (none) {KVER} #1 SMP Sat Oct 17 10:01:44 2026 armv7l GNU/Linux"),
    sh("free -m"),
    t("             total       used       free     shared    buffers", DIM),
    t("Mem:           497         14        483          0          0"),
])

# 11) Sık görülen hata çıktıları
render("11_hatalar.png", MINICOM, [
    ub("bootm 0x82000000 0x88080000 0x88000000"),
    t("## Loading init Ramdisk from Legacy Image at 88080000 ..."),
    note("Wrong Ramdisk Image Format", RED, "            <-- initramfs'te U-Boot başlığı yok"),
    t("Ramdisk image is corrupt or invalid", RED),
    ub("iminfo 0x82000000"),
    t("## Checking Image at 82000000 ..."),
    note("   Verifying Checksum ... Bad Data CRC", RED, "  <-- transfer bozuk / adres çakışması"),
    t(""),
    t("Starting kernel ...", GREEN),
    note("", FG, "    <-- sonrası boş: console= yanlış ya da DTB uyumsuz"),
    t(""),
    t("[    2.11] VFS: Cannot open root device \"ram0\" or unknown-block(1,0)", DIM),
    note("[    2.11] Kernel panic - not syncing: VFS: Unable to mount root fs", RED,
         "  <-- /init yok"),
    t(""),
    note("[    2.20] Failed to execute /init.  Attempting defaults...", RED,
         "    <-- ARM değil / kütüphane eksik"),
])

# 12) Buildroot çıktıları
render("12_buildroot_images.png", "mehmet@ubuntu: ~/buildroot", [
    [("mehmet@ubuntu", GREEN), (":", FG), ("~/buildroot", BLUE), ("$ ", FG),
     ("make beaglebone_defconfig", FG)],
    t("#", DIM),
    t("# configuration written to /home/mehmet/buildroot/.config", DIM),
    t("#", DIM),
    [("mehmet@ubuntu", GREEN), (":", FG), ("~/buildroot", BLUE), ("$ ", FG), ("make", FG)],
    t("...", DIM),
    [("mehmet@ubuntu", GREEN), (":", FG), ("~/buildroot", BLUE), ("$ ", FG),
     ("ls -1 output/images/", FG)],
    t("am335x-boneblack.dtb", CYAN),
    note("MLO", CYAN, "                       <-- SD karttan boot için"),
    t("rootfs.cpio", CYAN),
    note("rootfs.cpio.uboot", CYAN, "         <-- seri boot: initramfs"),
    t("rootfs.ext2", CYAN),
    t("sdcard.img", CYAN),
    note("u-boot-spl.bin", CYAN, "            <-- seri boot: SPL"),
    note("u-boot.img", CYAN, "                <-- seri boot: U-Boot"),
    note("zImage", CYAN, "                    <-- mkimage ile uImage yapılır"),
])
