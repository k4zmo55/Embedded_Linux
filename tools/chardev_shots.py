"""Karakter aygıt sürücüsü bölümü için terminal ekran görüntülerini üretir.

Kullanım: python tools/chardev_shots.py [çıktı klasörü]
"""
from term_shots import (render, t, FG, DIM, GREEN, BLUE, YELLOW, CYAN, RED,
                        MAGENTA, ORANGE)
from term_shots import V, set_default_out

CC = V("build.cross_compile")
NFS_DIR = V("network.nfs_dir")
set_default_out("images/chardev")

MOD = "~/code/22_char_driver"
ABS = "/home/mehmet/code/22_char_driver"
MINICOM = "mehmet@ubuntu: ~ — minicom (BBB, BusyBox rootfs)"


def host(cmd, path=MOD):
    return [("mehmet@ubuntu", GREEN), (":", FG), (path, BLUE), ("$ ", FG), (cmd, FG)]


def sh(cmd, path="~"):
    return [(f"{path} # ", GREEN), (cmd, FG)]


def note(text, color=FG, ann=""):
    return [(text, color), (ann, MAGENTA)] if ann else [(text, color)]


# 1) Mevcut karakter aygıtları
render("01_dev_numbers.png", MINICOM, [
    sh("ls -l /dev/ttyS0 /dev/null /dev/i2c-2 /dev/mmcblk0"),
    note("crw-rw----    1 root     root        4,  64 Jan  1 00:00 /dev/ttyS0", CYAN, "   <-- c: karakter"),
    note("crw-rw-rw-    1 root     root        1,   3 Jan  1 00:00 /dev/null", CYAN),
    note("crw-------    1 root     root       89,   2 Jan  1 00:00 /dev/i2c-2", CYAN),
    note("brw-rw----    1 root     root      179,   0 Jan  1 00:00 /dev/mmcblk0", ORANGE, "  <-- b: blok"),
    note("", FG, "                                     ↑ major, minor"),
    sh("head -8 /proc/devices"),
    note("Character devices:", FG),
    note("  1 mem", FG),
    note("  4 /dev/vc/0", FG),
    note("  4 tty", FG),
    note("  4 ttyS", FG),
    note("  5 /dev/tty", FG),
    note("  5 /dev/console", FG),
    note("  5 /dev/ptmx", FG),
])

# 2) Derleme ve yükleme
render("02_build_load.png", "mehmet@ubuntu + BBB", [
    host("make && make test"),
    note(f"  CC [M]  {ABS}/bbbmsg.o", FG),
    note(f"  MODPOST {ABS}/Module.symvers", FG),
    note(f"  LD [M]  {ABS}/bbbmsg.ko", GREEN),
    note(f"{CC}gcc -Wall -static -o bbbmsg_test bbbmsg_test.c", FG),
    host(f"sudo cp bbbmsg.ko bbbmsg_test {NFS_DIR}/root/"),
    t("--- BBB ---", MAGENTA),
    sh("insmod bbbmsg.ko"),
    sh("dmesg | tail -1"),
    note("[ 1203.556120] bbbmsg: registered /dev/bbbmsg (major 246, minor 0)", GREEN),
    sh("grep bbbmsg /proc/devices"),
    note("246 bbbmsg", CYAN, "                       <-- çekirdeğin verdiği boş major"),
    sh("ls -l /dev/bbbmsg"),
    note("crw-------    1 root     root      246,   0 Jan  1 00:20 /dev/bbbmsg", CYAN, "  <-- devtmpfs açtı"),
    sh("ls /sys/class/bbbmsg/bbbmsg/"),
    note("dev        power      subsystem  uevent", CYAN),
    sh("cat /sys/class/bbbmsg/bbbmsg/dev"),
    note("246:0", CYAN),
])

# 3) Kabuktan deneme
render("03_shell_test.png", MINICOM, [
    sh('echo "Merhaba BBB" > /dev/bbbmsg'),
    sh("cat /dev/bbbmsg"),
    note("Merhaba BBB", GREEN),
    sh('echo "ikinci satir" >> /dev/bbbmsg'),
    note("", FG, "                        <-- O_APPEND: sona ekler"),
    sh("cat /dev/bbbmsg"),
    note("Merhaba BBB", GREEN),
    note("ikinci satir", GREEN),
    sh("dd if=/dev/bbbmsg bs=1 skip=8 count=3 2>/dev/null; echo"),
    note("BBB", GREEN, "                                     <-- llseek + read"),
    sh("dmesg | tail -4"),
    note("[ 1250.107711] bbbmsg: open (major 246, minor 0)", FG),
    note("[ 1250.112390] bbbmsg: wrote 13 bytes, message is now 25 bytes", FG),
    note("[ 1250.118845] bbbmsg: release", FG),
    note("[ 1255.402126] bbbmsg: open (major 246, minor 0)", FG),
])

# 4) Kullanıcı programı
render("04_user_program.png", MINICOM, [
    sh('./bbbmsg_test "C programindan selam"'),
    note("write: 20 bytes", FG),
    note("ioctl GET_LEN: 20", CYAN, "                  <-- ioctl ile sürücüye soru"),
    note('read: "C programindan selam" (20 bytes)', GREEN),
    note("after CLEAR, read: 0 bytes", CYAN, "        <-- ioctl ile silindi"),
    sh("cat /dev/bbbmsg"),
    note("", FG, "                                     <-- boş"),
    sh("rmmod bbbmsg"),
    sh("ls /dev/bbbmsg"),
    note("ls: /dev/bbbmsg: No such file or directory", YELLOW, "   <-- device_destroy kaldırdı"),
])

# 5) Hatalar
render("05_errors.png", MINICOM + " (temsili hatalar)", [
    sh("printf '%300s' x > /dev/bbbmsg"),
    note("printf: write error: No space left on device", RED, "   <-- 256 bayt yazıldı, kalanına yer yok"),
    t(""),
    [("debian@beaglebone", GREEN), (":", FG), ("~", BLUE), ("$ ", FG), ('echo hi > /dev/bbbmsg', FG)],
    note("-bash: /dev/bbbmsg: Permission denied", RED, "       <-- düğüm 0600, root değilsin"),
    t(""),
    sh("./bbbmsg_test x"),
    note("/dev/bbbmsg: No such file or directory", RED, "      <-- modül yüklü değil"),
    t(""),
    sh("rmmod bbbmsg"),
    note("rmmod: can't unload module 'bbbmsg': Resource temporarily unavailable", RED),
    note("", FG, "                                   <-- aygıt başka bir süreçte açık"),
])
