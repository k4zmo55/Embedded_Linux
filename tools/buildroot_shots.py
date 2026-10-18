"""Buildroot bölümü için terminal ekran görüntülerini üretir.

Kullanım: python tools/buildroot_shots.py [çıktı klasörü]
"""
from term_shots import (render, t, FG, DIM, GREEN, BLUE, YELLOW, CYAN, RED,
                        MAGENTA, ORANGE)
from term_shots import V, set_default_out

BR = V("buildroot.version")
BR_DIR = V("buildroot.dir")
BR_DEF = V("buildroot.defconfig")
BR_K = V("buildroot.kernel_version")
BR_UB = V("buildroot.uboot_version")
BR_BB = V("buildroot.busybox_version")
BR_DB = V("buildroot.dropbear_version")
HOST_IP = V("network.host_ip")
BOARD_IP = V("network.board_ip")
set_default_out("images/buildroot")

TITLE = f"mehmet@ubuntu: ~/bbb/{BR_DIR}"
MINICOM = "mehmet@ubuntu: ~ — minicom -D /dev/ttyUSB0 -b 115200"


def host(cmd, path="~/bbb"):
    return [("mehmet@ubuntu", GREEN), (":", FG), (path, BLUE), ("$ ", FG), (cmd, FG)]


def bh(cmd):
    return host(cmd, f"~/bbb/{BR_DIR}")


def note(text, color=FG, ann=""):
    return [(text, color), (ann, MAGENTA)] if ann else [(text, color)]


# 1) İndirme ve klasörler
render("01_download.png", "mehmet@ubuntu: ~/bbb", [
    host(f"wget https://buildroot.org/downloads/buildroot-{BR}.tar.gz"),
    host(f"tar -xzf buildroot-{BR}.tar.gz && cd {BR_DIR}"),
    bh("ls"),
    t("arch   boot     Config.in  COPYING  DEVELOPERS  fs     Makefile  README   system     utils", CYAN),
    t("board  CHANGES  configs    docs     linux       package  support  toolchain", CYAN),
    bh("ls package | wc -l"),
    note("~3000", FG, "                               <-- hazır paket tarifi"),
    bh("make list-defconfigs | grep -i beagle"),
    t("  beagleboneai_defconfig              - Build for beagleboneai"),
    note(f"  {BR_DEF}                - Build for beaglebone", GREEN, "  <-- BBB"),
    t("  beaglebone_qt5_defconfig            - Build for beaglebone_qt5"),
    t("  beagleplay_defconfig                - Build for beagleplay"),
])

# 2) defconfig ve menuconfig
render("02_defconfig.png", TITLE, [
    bh(f"make {BR_DEF}"),
    t("  ...", DIM),
    t("#", DIM),
    note("# configuration written to .../.config", GREEN, ""),
    t("#", DIM),
    bh("grep -E 'BR2_TOOLCHAIN_EXTERNAL_BOOTLIN_|VERSION_VALUE|KERNEL_DEFCONFIG|UBOOT_BOARD' .config"),
    note("BR2_TOOLCHAIN_EXTERNAL_BOOTLIN_ARMV7_EABIHF_GLIBC_STABLE=y", CYAN, "   <-- hazır toolchain"),
    note(f'BR2_LINUX_KERNEL_CUSTOM_VERSION_VALUE="{BR_K}"', CYAN, "       <-- kernel sürümü"),
    t('BR2_LINUX_KERNEL_DEFCONFIG="omap2plus"', CYAN),
    note(f'BR2_TARGET_UBOOT_CUSTOM_VERSION_VALUE="{BR_UB}"', CYAN, "      <-- U-Boot sürümü"),
    t('BR2_TARGET_UBOOT_BOARD_DEFCONFIG="am335x_evm"', CYAN),
    bh("make menuconfig"),
])

# 3) Derleme
render("03_build.png", TITLE, [
    bh("make 2>&1 | tee build.log"),
    t(">>> toolchain-external-bootlin 2025.08-1 Downloading", DIM),
    t(f">>> busybox {BR_BB} Building", DIM),
    t(f">>> linux {BR_K} Building", DIM),
    t(f">>> uboot {BR_UB} Building", DIM),
    t(">>>   Generating root filesystems common tables", DIM),
    t(">>>   Generating filesystem image rootfs.ext2", DIM),
    t(">>>   Executing post-image script support/scripts/genimage.sh", DIM),
    t("INFO: vfat(boot.vfat): adding file 'MLO' as 'MLO' ...", DIM),
    note("INFO: hdimage(sdcard.img): adding partition 'rootfs' ...", DIM, ""),
    bh("ls output/images"),
    t("am335x-boneblack.dtb  am335x-bonegreen.dtb  boot.vfat  extlinux  MLO       rootfs.ext4  sdcard.img  uEnv.txt", CYAN),
    t("am335x-bone.dtb       am335x-evm.dtb        ...        rootfs.ext2  rootfs.tar  u-boot.img  zImage", CYAN),
    note("", FG, ""),
    bh("du -sh dl output"),
    note("486M    dl", FG, "                                <-- indirilen kaynaklar"),
    t("6.1G    output"),
])

# 4) output klasörü
render("04_output_tree.png", TITLE, [
    bh("ls output"),
    t("build  host  images  staging  target", CYAN),
    bh("ls output/build | head -6"),
    t("busybox-1.37.0  host-dosfstools-4.2  host-genimage-18  linux-" + BR_K + "  ...", DIM),
    bh("ls output/target"),
    t("bin  dev  etc  lib  lib32  linuxrc  media  mnt  opt  proc  root  run  sbin  sys  tmp  usr  var", CYAN),
    bh("file output/target/bin/busybox"),
    note("output/target/bin/busybox: ELF 32-bit LSB executable, ARM, EABI5 version 1 (SYSV), dynamically linked",
         CYAN, ""),
    bh("ls output/host/bin | grep -E 'gcc$|mkimage|genimage' | head -4"),
    note("arm-buildroot-linux-gnueabihf-gcc", GREEN, "        <-- Buildroot'un cross toolchain'i"),
    t("genimage"),
    t("mkimage"),
])

# 5) SSH ve ağ ayarları
render("05_ssh_config.png", TITLE, [
    bh("make menuconfig"),
    note("   Target packages → Networking applications → [*] dropbear", DIM, ""),
    note("   System configuration → Root password: ********", DIM, ""),
    note("   System configuration → Root filesystem overlay directories: board/bbb/overlay", DIM, ""),
    bh("cat board/bbb/overlay/etc/network/interfaces"),
    t("auto lo", CYAN),
    t("iface lo inet loopback", CYAN),
    t("auto eth0", CYAN),
    t("iface eth0 inet static", CYAN),
    t(f"    address {BOARD_IP}", CYAN),
    t("    netmask 255.255.255.0", CYAN),
    bh("make"),
    t(f">>> dropbear {BR_DB} Building", DIM),
    t(">>>   Generating filesystem image rootfs.ext2", DIM),
    note(">>>   Executing post-image script support/scripts/genimage.sh", DIM, "  <-- sdcard.img yenilendi"),
])

# 6) SD karta yazma
render("06_flash_sd.png", TITLE, [
    bh("lsblk -o NAME,SIZE,TYPE,MOUNTPOINT | grep sdb"),
    t("sdb       7.4G disk"),
    t("|-sdb1   1013M part /media/mehmet/BOOT"),
    t("`-sdb2    6.3G part /media/mehmet/ROOTFS"),
    bh("sudo umount /dev/sdb1 /dev/sdb2"),
    bh("sudo dd if=output/images/sdcard.img of=/dev/sdb bs=4M status=progress conv=fsync"),
    t("549453824 bytes (549 MB, 524 MiB) copied, 38 s, 14.5 MB/s"),
    t("131+1 records in"),
    t("131+1 records out"),
    bh("lsblk -o NAME,SIZE,FSTYPE,LABEL /dev/sdb"),
    note("|-sdb1     16M vfat", FG, "                       <-- boot.vfat"),
    note("`-sdb2    512M ext4   rootfs", FG, "              <-- rootfs.ext4"),
])

# 7) Açılış ve SSH
render("07_boot_ssh.png", MINICOM + " + host", [
    t(f"U-Boot SPL {BR_UB} (Oct 21 2026 - 14:02:33 +0300)", DIM),
    t(f"U-Boot {BR_UB} (Oct 21 2026 - 14:02:33 +0300)", ORANGE),
    t("..."),
    t("Starting kernel ...", GREEN),
    t(f"[    0.000000] Linux version {BR_K} (mehmet@ubuntu) (arm-buildroot-linux-gnueabihf-gcc ...)", DIM),
    t("Starting syslogd: OK"),
    t("Starting network: OK"),
    t("Starting dropbear sshd: OK"),
    t(""),
    t("Welcome to Buildroot", ORANGE),
    t("buildroot login: root"),
    t("Password:"),
    [("# ", GREEN), ("uname -r", FG)],
    t(BR_K, CYAN),
    t("--- host ---", MAGENTA),
    host(f"ssh root@{BOARD_IP}"),
    note("# ", GREEN, "                                          <-- SSH ile Buildroot sistemindesin"),
])

# 8) Kernel ve U-Boot ayarları
render("08_linux_uboot_config.png", TITLE, [
    bh("make linux-menuconfig"),
    note("   (kernel'in kendi menuconfig'i)", DIM, ""),
    bh("make linux-update-defconfig"),
    note("   (değişiklikleri BR2_LINUX_KERNEL_CUSTOM_CONFIG_FILE'a yazar)", DIM, ""),
    bh("make uboot-menuconfig"),
    bh("make busybox-menuconfig"),
    bh("make linux-rebuild uboot-rebuild all"),
    t(f">>> linux {BR_K} Building", DIM),
    t(f">>> uboot {BR_UB} Building", DIM),
    t(">>>   Executing post-image script support/scripts/genimage.sh", DIM),
    bh("make savedefconfig BR2_DEFCONFIG=configs/my_bbb_defconfig"),
    note("", FG, ""),
    bh("cat configs/my_bbb_defconfig | wc -l"),
    note("49", FG, "                                      <-- bütün ayarların küçük özeti"),
])

# 9) Hatalar
render("09_errors.png", TITLE + " (temsili hatalar)", [
    note("You seem to have the current working directory in your", RED, ""),
    note("LD_LIBRARY_PATH environment variable. This doesn't work.", RED, "  <-- LD_LIBRARY_PATH temizle"),
    t(""),
    note("You must install 'unzip' on your build machine", RED, "        <-- host paketleri"),
    t(""),
    note("ERROR: No hash found for linux-5.10.tar.gz", RED, "             <-- özel kernel + hash kontrolü"),
    t(""),
    note("make: *** No rule to make target 'bb.org_defconfig'", RED, "       <-- defconfig adı ('_defconfig' eklemeden)"),
    t(""),
    note("No space left on device", RED, "                               <-- output/ birkaç GB tutar"),
])
