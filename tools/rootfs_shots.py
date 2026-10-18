"""ROOTFS notu için terminal ekran görüntülerini üretir.

Kullanım: python tools/rootfs_shots.py images/rootfs
"""
from term_shots import (render, ub, bbb, t, FG, DIM, GREEN, BLUE, YELLOW,
                        CYAN, RED, MAGENTA, ORANGE)
from term_shots import V, set_default_out

KVER = V("prebuilt.kernel_version")
set_default_out("images/rootfs")


def host_at(path, cmd):
    return [("mehmet@ubuntu", GREEN), (":", FG), (path, BLUE), ("$ ", FG), (cmd, FG)]


def bbb_at(path, cmd):
    return [("root@beaglebone", GREEN), (":", FG), (path, BLUE), ("# ", FG), (cmd, FG)]


MINICOM = "mehmet@ubuntu: ~/bbb — minicom -D /dev/ttyUSB0 -b 115200"
BBB = "root@beaglebone: ~ (seri konsol)"
R = "/media/mehmet/ROOTFS"

# 1) Bilgisayardan: SD kart takılıyken ROOTFS bölümü
render("01_host_rootfs.png", "mehmet@ubuntu: /media/mehmet/ROOTFS", [
    host_at("~", "lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINT /dev/sdb"),
    t("NAME     SIZE FSTYPE LABEL  MOUNTPOINT", DIM),
    t("sdb      7.4G"),
    t("├─sdb1     1G vfat   BOOT   /media/mehmet/BOOT"),
    [("└─sdb2   6.3G ext3   ROOTFS ", FG), (R, GREEN), ("   <-- buraya bağlı", MAGENTA)],
    host_at("~", "cd /media/mehmet/ROOTFS"),
    host_at(R, "ls"),
    t("bin   dev  home  media  proc  sbin  tmp  var", BLUE),
    t("boot  etc  lib   mnt    run   sys   usr", BLUE),
    host_at(R, "ls boot/"),
    [("am335x-boneblack.dtb  ", FG), ("uImage", CYAN), (f"  uImage-{KVER}", FG)],
    host_at(R, "du -sh ."),
    t("412M    ."),
])

# 2) Bilgisayardan: sanal klasörler boş, programlar ARM için derlenmiş
render("02_host_sanal_ve_arm.png", "mehmet@ubuntu: /media/mehmet/ROOTFS", [
    host_at(R, "ls proc/ sys/ dev/"),
    t("dev/:"),
    t(""),
    t("proc/:"),
    t(""),
    [("sys/:", FG), ("                 <-- boş! kernel çalışınca dolar", MAGENTA)],
    host_at(R, "file bin/bash"),
    [("bin/bash: ELF 32-bit LSB executable, ", FG), ("ARM", ORANGE), (", EABI5 version 1 (SYSV),", FG)],
    t("dynamically linked, interpreter /lib/ld-linux.so.3, for GNU/Linux 2.6.32"),
    host_at(R, "cat etc/hostname"),
    t("beaglebone", CYAN),
    [("mehmet@ubuntu", GREEN), (":", FG), (R, BLUE), ("$ ", FG), ("cat /etc/hostname", FG),
     ("   <-- DİKKAT: baştaki /", MAGENTA)],
    [("ubuntu", RED), ("                    <-- bu bilgisayarın kendi /etc'si!", MAGENTA)],
])

# 3) U-Boot'tan: ROOTFS bölümünü listeleme
render("03_uboot_ls.png", MINICOM, [
    ub("ls mmc 0:2 /"),
    t("<DIR>       4096 ."),
    t("<DIR>       4096 .."),
    t("<DIR>       4096 bin"),
    t("<DIR>       4096 boot"),
    t("<DIR>       4096 dev"),
    t("<DIR>       4096 etc"),
    t("<DIR>       4096 home"),
    t("<DIR>       4096 lib"),
    t("   ...", DIM),
    t("<DIR>       4096 usr"),
    t("<DIR>       4096 var"),
    ub("ls mmc 0:2 /boot"),
    t("             24884 am335x-boneblack.dtb"),
    [("           4380760 uImage", CYAN)],
    ub("ls mmc 1:2 /          # eMMC'deki rootfs (Debian)"),
    t("<DIR>       4096 bin"),
    t("   ...", DIM),
])

# 4) BBB Linux: kök dizinde dolaşma
render("04_bbb_ls.png", BBB, [
    bbb("pwd"),
    t("/home/root"),
    bbb("cd /"),
    bbb_at("/", "ls"),
    t("bin   dev  home  media  proc  sbin  tmp  var", BLUE),
    t("boot  etc  lib   mnt    run   sys   usr", BLUE),
    bbb_at("/", "ls /bin | head -5"),
    t("bash"),
    t("busybox"),
    t("cat"),
    t("chmod"),
    t("cp"),
    bbb_at("/", "which ls"),
    t("/bin/ls"),
    bbb_at("/", "ls -l /bin/ls"),
    [("lrwxrwxrwx 1 root root 12 Dec 13  2012 /bin/ls -> ", FG), ("busybox", CYAN)],
])

# 5) BBB Linux: /etc ayar dosyaları
render("05_bbb_etc.png", BBB, [
    bbb("cat /etc/hostname"),
    t("beaglebone", CYAN),
    bbb("cat /etc/os-release"),
    t('NAME="Angstrom"', CYAN),
    t('VERSION="v2012.12"', CYAN),
    t('ID="angstrom"', CYAN),
    bbb("cat /etc/fstab"),
    t("# <file system>  <mount pt>  <type>  <options>          <dump> <pass>", DIM),
    t("rootfs           /           auto    defaults            1      1"),
    t("proc             /proc       proc    defaults            0      0"),
    t("tmpfs            /tmp        tmpfs   defaults            0      0"),
    bbb("head -2 /etc/passwd"),
    t("root::0:0:root:/home/root:/bin/sh"),
    t("daemon:*:1:1:daemon:/usr/sbin:/bin/sh"),
])

# 6) BBB Linux: /proc ve /sys
render("06_bbb_proc_sys.png", BBB, [
    bbb("cat /proc/version"),
    t(f"Linux version {KVER} (gcc version 4.7.3) #1 SMP Wed Oct 16 2026"),
    bbb("grep -m2 -E 'model name|BogoMIPS' /proc/cpuinfo"),
    t("model name      : ARMv7 Processor rev 2 (v7l)"),
    t("BogoMIPS        : 990.68"),
    bbb("head -2 /proc/meminfo"),
    t("MemTotal:         510316 kB"),
    t("MemFree:          402148 kB"),
    bbb("ls /sys/class/leds/"),
    t("beaglebone:green:usr0  beaglebone:green:usr2", CYAN),
    t("beaglebone:green:usr1  beaglebone:green:usr3", CYAN),
    bbb("echo none > /sys/class/leds/beaglebone:green:usr0/trigger"),
    [("root@beaglebone", GREEN), (":", FG), ("~", BLUE), ("# ", FG),
     ("echo 1 > /sys/class/leds/beaglebone:green:usr0/brightness", FG)],
    t("                                     <-- USR0 LED'i yandı", MAGENTA),
])

# 7) BBB Linux: /dev, /boot ve disk kullanımı
render("07_bbb_dev_boot.png", BBB, [
    bbb("ls /dev/mmcblk* /dev/ttyO*"),
    t("/dev/mmcblk0    /dev/mmcblk0p2  /dev/mmcblk1p1  /dev/ttyO0", YELLOW),
    t("/dev/mmcblk0p1  /dev/mmcblk1    /dev/mmcblk1p2", YELLOW),
    bbb("ls -l /boot"),
    t("-rw-r--r-- 1 root root   24884 Dec 13  2012 am335x-boneblack.dtb"),
    t(f"lrwxrwxrwx 1 root root      14 Dec 13  2012 uImage -> uImage-{KVER}"),
    t(f"-rw-r--r-- 1 root root 4380760 Dec 13  2012 uImage-{KVER}"),
    bbb("df -h /"),
    t("Filesystem      Size  Used Avail Use% Mounted on", DIM),
    t("/dev/mmcblk0p2  6.2G  412M  5.5G   7% /"),
    bbb("du -sh /usr /lib /etc 2>/dev/null"),
    t("287M    /usr"),
    t("61M     /lib"),
    t("3.1M    /etc"),
    bbb("mount | grep -E ' / | /proc | /sys | /dev '"),
    t("/dev/mmcblk0p2 on / type ext3 (rw,relatime)"),
    t("devtmpfs on /dev type devtmpfs (rw,relatime)"),
    t("proc on /proc type proc (rw,relatime)"),
    t("sysfs on /sys type sysfs (rw,relatime)"),
])
