"""BusyBox / minimal rootfs bölümü için terminal ekran görüntülerini üretir.

Kullanım: python tools/busybox_shots.py [çıktı klasörü]
"""
from term_shots import (render, t, FG, DIM, GREEN, BLUE, YELLOW, CYAN, RED,
                        MAGENTA, ORANGE)
from term_shots import V, set_default_out

BB = V("rootfs.busybox_version")
DB = V("rootfs.dropbear_version")
KVER = V("kernel.version")
KCON = V("kernel.console")
CC = V("build.cross_compile")
HOST_IP = V("network.host_ip")
BOARD_IP = V("network.board_ip")
NETMASK = V("network.netmask")
NFS_DIR = V("network.nfs_dir")
USB_BOARD = V("rootfs.usb_board_ip")
USB_HOST = V("rootfs.usb_host_ip")
set_default_out("images/busybox")

MAKE = f"make ARCH=arm CROSS_COMPILE={CC}"
MINICOM = "mehmet@ubuntu: ~ — minicom -D /dev/ttyUSB0 -b 115200"


def host(cmd, path="~/bbb"):
    return [("mehmet@ubuntu", GREEN), (":", FG), (path, BLUE), ("$ ", FG), (cmd, FG)]


def bh(cmd):
    return host(cmd, f"~/bbb/busybox-{BB}")


def rh(cmd):
    return host(cmd, "~/bbb/rootfs")


def sh(cmd, path="/"):
    return [(f"{path} # ", GREEN), (cmd, FG)]


def note(text, color=FG, ann=""):
    return [(text, color), (ann, MAGENTA)] if ann else [(text, color)]


BTITLE = f"mehmet@ubuntu: ~/bbb/busybox-{BB}"

# 1) İndirme ve yapılandırma
render("01_download_config.png", "mehmet@ubuntu: ~/bbb", [
    host(f"wget https://busybox.net/downloads/busybox-{BB}.tar.bz2"),
    host(f"tar -xjf busybox-{BB}.tar.bz2 && cd busybox-{BB}"),
    bh(f"{MAKE} defconfig"),
    t("  HOSTCC  scripts/basic/fixdep", DIM),
    t("  ...", DIM),
    t("*", DIM),
    t("* Busybox Configuration", DIM),
    t("*", DIM),
    bh(f"{MAKE} menuconfig"),
    note("   Settings → Build static binary (no shared libs)  [*]", DIM, "   <-- işaretle"),
    bh("grep CONFIG_STATIC= .config"),
    note("CONFIG_STATIC=y", GREEN, "                       <-- statik derlenecek"),
])

# 2) Derleme ve kurulum
render("02_build_install.png", BTITLE, [
    bh(f"{MAKE} -j$(nproc)"),
    t("  ...", DIM),
    t("  LINK    busybox_unstripped", DIM),
    t("Static linking against glibc, can't use --gc-sections", DIM),
    t("Trying libraries: crypt m resolv rt", DIM),
    note("Final link with: m resolv rt", DIM, ""),
    bh(f"{MAKE} CONFIG_PREFIX=~/bbb/rootfs install"),
    t("  ~/bbb/rootfs/bin/ash -> busybox", DIM),
    t("  ~/bbb/rootfs/bin/cat -> busybox", DIM),
    t("  ...", DIM),
    t("--------------------------------------------------", DIM),
    t("You will probably need to make your busybox binary", DIM),
    t("setuid root to ensure all configured applets will", DIM),
    t("work properly.", DIM),
    t("--------------------------------------------------", DIM),
    bh("file ~/bbb/rootfs/bin/busybox"),
    note("~/bbb/rootfs/bin/busybox: ELF 32-bit LSB executable, ARM, EABI5 version 1 (SYSV),", CYAN, ""),
    note("statically linked, for GNU/Linux 3.2.0, stripped", CYAN, "      <-- ARM + statik"),
])

# 3) Rootfs iskeleti
render("03_rootfs_tree.png", "mehmet@ubuntu: ~/bbb/rootfs", [
    rh("ls"),
    note("bin  lib  linuxrc  sbin  usr", CYAN, "            <-- BusyBox + kernel modülleri (lib/modules)"),
    rh("mkdir -p dev proc sys etc/init.d etc/network tmp root var/run var/log mnt"),
    rh("ls"),
    t("bin  dev  etc  lib  linuxrc  mnt  proc  root  sbin  sys  tmp  usr  var", CYAN),
    rh("ls -l sbin | head -4"),
    t("lrwxrwxrwx 1 mehmet mehmet 14 Eki 20 11:12 init -> ../bin/busybox"),
    t("lrwxrwxrwx 1 mehmet mehmet 14 Eki 20 11:12 insmod -> ../bin/busybox"),
    t("lrwxrwxrwx 1 mehmet mehmet 14 Eki 20 11:12 modprobe -> ../bin/busybox"),
    rh("cat etc/inittab"),
    t("::sysinit:/etc/init.d/rcS", CYAN),
    t("::askfirst:-/bin/sh", CYAN),
    t("::restart:/sbin/init", CYAN),
    t("::shutdown:/etc/init.d/rcK", CYAN),
    t("::shutdown:/bin/umount -a -r", CYAN),
    rh("ls etc/init.d"),
    t("rcK  rcS  S01logging  S02module  S40network", CYAN),
])

# 4) SD karta kopyalama
render("04_copy_sd.png", "mehmet@ubuntu: ~/bbb", [
    host("lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINT /dev/sdb"),
    t("NAME     SIZE FSTYPE LABEL  MOUNTPOINT", DIM),
    t("|-sdb1  1013M vfat   BOOT   /media/mehmet/BOOT"),
    t("`-sdb2   6.3G ext3   ROOTFS /media/mehmet/ROOTFS"),
    host("sudo rm -rf /media/mehmet/ROOTFS/*"),
    host("sudo cp -a rootfs/* /media/mehmet/ROOTFS/"),
    host("sudo chown -R root:root /media/mehmet/ROOTFS"),
    host("cp linux/arch/arm/boot/uImage linux/arch/arm/boot/dts/am335x-boneblack.dtb /media/mehmet/BOOT/"),
    host("du -sh /media/mehmet/ROOTFS"),
    note("31M     /media/mehmet/ROOTFS", FG, "          <-- BusyBox ~2 MB, gerisi kernel modülleri"),
    host("sync && sudo umount /media/mehmet/BOOT /media/mehmet/ROOTFS"),
])

# 5) BusyBox ile açılış
render("05_boot_busybox.png", MINICOM, [
    t("Starting kernel ...", GREEN),
    t(f"[    0.000000] Linux version {KVER} (mehmet@ubuntu) ...", DIM),
    t(f"[    0.000000] Kernel command line: console={KCON},115200n8 root=/dev/mmcblk0p2 rw rootwait", DIM),
    t("[    2.891203] EXT4-fs (mmcblk0p2): mounted filesystem with ordered data mode.", DIM),
    note("[    2.899140] VFS: Mounted root (ext3 filesystem) on device 179:2.", DIM, "  <-- rootfs bağlandı"),
    t("[    2.910571] devtmpfs: mounted", DIM),
    note("[    2.921880] Run /sbin/init as init process", ORANGE, "          <-- BusyBox init"),
    note("Mounting proc", FG, "                                         <-- rcS"),
    t("Starting logging: OK"),
    t("Loading kernel modules : OK"),
    t("Starting network: OK"),
    t(""),
    t("Please press Enter to activate this console."),
    sh("uname -r"),
    t(KVER, CYAN),
    sh("ps"),
    t("PID   USER     TIME  COMMAND", DIM),
    note("    1 0         0:00 init", FG, "                          <-- PID 1"),
    t("   97 0         0:00 /sbin/syslogd -n"),
    t("  104 0         0:00 -/bin/sh"),
])

# 6) USB üzerinden Ethernet (g_ether)
render("06_g_ether.png", MINICOM + " + host", [
    sh("modprobe g_ether"),
    t("[  412.330415] using random self ethernet address", DIM),
    t("[  412.335101] using random host ethernet address", DIM),
    note("[  412.341766] usb0: HOST MAC 8e:2a:4f:61:c3:10", DIM, ""),
    note("[  412.352048] g_ether gadget: Ethernet Gadget, version: Memorial Day 2008", ORANGE, ""),
    sh(f"ifconfig usb0 {USB_BOARD} netmask 255.255.255.0 up"),
    t("--- host ---", MAGENTA),
    host("ip -br link | grep enx"),
    note("enx8e2a4f61c310 UP   8e:2a:4f:61:c3:10", FG, "    <-- kartın USB ağ arayüzü"),
    host(f"sudo ip addr add {USB_HOST}/24 dev enx8e2a4f61c310"),
    host(f"ping -c 2 {USB_BOARD}"),
    t(f"64 bytes from {USB_BOARD}: icmp_seq=1 ttl=64 time=0.71 ms", GREEN),
    t(f"64 bytes from {USB_BOARD}: icmp_seq=2 ttl=64 time=0.48 ms", GREEN),
])

# 7) NFS sunucusu
render("07_nfs_host.png", "mehmet@ubuntu: ~/bbb", [
    host("sudo apt install nfs-kernel-server"),
    host(f"sudo mkdir -p {NFS_DIR} && sudo cp -a rootfs/* {NFS_DIR}/"),
    host(f"sudo chown -R root:root {NFS_DIR}"),
    host("cat /etc/exports"),
    note(f"{NFS_DIR}  *(rw,sync,no_root_squash,no_subtree_check)", CYAN, ""),
    host("sudo exportfs -ra"),
    host("showmount -e localhost"),
    t("Export list for localhost:"),
    note(f"{NFS_DIR} *", GREEN, "                    <-- paylaşım hazır"),
])

# 8) NFS ile açılış
render("08_nfs_boot.png", MINICOM, [
    t("Running uenvcmd ..."),
    t("Booting from network ..."),
    t(f"TFTP from server {HOST_IP}; our IP address is {BOARD_IP}"),
    t("Bytes transferred = 10811832 (a4f9b8 hex)", GREEN),
    t("Starting kernel ...", GREEN),
    note(f"[    1.913620] cpsw 4a100000.ethernet eth0: Link is Up - 100Mbps/Full", DIM, ""),
    t("[    1.934409] IP-Config: Complete:", DIM),
    t(f"[    1.937710]      device=eth0, hwaddr=c8:a0:30:b1:7e:2c, ipaddr={BOARD_IP}, mask={NETMASK}", DIM),
    note(f"[    2.218032] VFS: Mounted root (nfs filesystem) on device 0:17.", ORANGE, "  <-- rootfs NFS'ten"),
    t("[    2.225911] Run /sbin/init as init process", DIM),
    t("Mounting proc"),
    t("..."),
    sh("mount | head -1"),
    t(f"{HOST_IP}:{NFS_DIR} on / type nfs (rw,relatime,vers=3,...)", CYAN),
])

# 9) Challenge 1: Dropbear
render("09_dropbear.png", "mehmet@ubuntu: ~/bbb/dropbear-" + DB, [
    host(f"tar -xjf dropbear-{DB}.tar.bz2 && cd dropbear-{DB}"),
    host(f"./configure --host=arm-linux-gnueabihf --disable-zlib --prefix=/usr CC={CC}gcc",
         f"~/bbb/dropbear-{DB}"),
    host('make PROGRAMS="dropbear dropbearkey dbclient scp" STATIC=1 -j4', f"~/bbb/dropbear-{DB}"),
    host('make PROGRAMS="dropbear dropbearkey dbclient scp" STATIC=1 DESTDIR=~/bbb/rootfs install',
         f"~/bbb/dropbear-{DB}"),
    t("--- kart ---", MAGENTA),
    sh("mkdir -p /etc/dropbear && dropbear -R"),
    sh("passwd"),
    t("Changing password for root"),
    t("New password: ********"),
    t("passwd: password for root changed by root", GREEN),
    t("--- host ---", MAGENTA),
    host(f"ssh root@{BOARD_IP}"),
    t("root@" + BOARD_IP + "'s password:"),
    note("~ # uname -m", FG, ""),
    note("armv7l", CYAN, "                                     <-- SSH ile karttasın"),
])

# 10) Challenge 2: dinamik BusyBox
render("10_dynamic.png", BTITLE, [
    bh(f"{MAKE} menuconfig"),
    note("   Settings → Build static binary (no shared libs)  [ ]", DIM, "   <-- kaldır"),
    bh(f"{MAKE} -j$(nproc)"),
    bh(f"{MAKE} CONFIG_PREFIX=~/bbb/rootfs install"),
    bh(f"{CC}readelf -d ~/bbb/rootfs/bin/busybox | grep NEEDED"),
    t(" 0x00000001 (NEEDED)   Shared library: [libm.so.6]", CYAN),
    t(" 0x00000001 (NEEDED)   Shared library: [libresolv.so.2]", CYAN),
    t(" 0x00000001 (NEEDED)   Shared library: [libc.so.6]", CYAN),
    bh(f"SYSROOT=$({CC}gcc -print-sysroot)"),
    bh("cp -a $SYSROOT/lib/*.so* ~/bbb/rootfs/lib/"),
    bh("ls ~/bbb/rootfs/lib | grep -E 'ld-linux|libc\\.so|libm\\.so'"),
    note("ld-linux-armhf.so.3", GREEN, "                     <-- dinamik yükleyici"),
    t("libc.so.6"),
    t("libm.so.6"),
])

# 11) Hatalar
render("11_errors.png", MINICOM + " (temsili hatalar)", [
    note("Kernel panic - not syncing: No working init found.", RED, "   <-- init yok / ARM değil / kütüphane eksik"),
    t(""),
    note("can't open /dev/tty2: No such file or directory", RED, "      <-- /etc/inittab yok"),
    t(""),
    note("/etc/init.d/rcS: Permission denied", RED, "                  <-- chmod +x"),
    t(""),
    note("modprobe: can't change directory to '/lib/modules': No such file", RED, "  <-- modules_install"),
    t(""),
    note("VFS: Unable to mount root fs via NFS.", RED, "                <-- NFS sürümü / exports / ip="),
    t(""),
    note("PTY allocation request failed on channel 0", RED, "          <-- /dev/pts bağlı değil"),
])
