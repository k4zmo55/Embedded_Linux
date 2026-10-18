"""Linux kernel bölümü için terminal ekran görüntülerini üretir.

Kullanım: python tools/kernel_shots.py [çıktı klasörü]
"""
from term_shots import (render, t, FG, DIM, GREEN, BLUE, YELLOW, CYAN, RED,
                        MAGENTA, ORANGE)
from term_shots import V, set_default_out

KBRANCH = V("kernel.branch")
KVER = V("kernel.version")
KREPO = V("kernel.repo")
KDEFCONFIG = V("kernel.defconfig")
KLOAD = V("kernel.loadaddr")
KCONSOLE = V("kernel.console")
CC = V("build.cross_compile")
GCC_VER = V("build.gcc_version")
LINARO_REL = V("build.linaro_release")
SD_UB = V("prebuilt.sd_uboot_version")
set_default_out("images/kernel")

MAJ, MIN, SUB = (KVER.split(".") + ["0", "0"])[:3]
MAKE = f"make ARCH=arm CROSS_COMPILE={CC}"


def host(cmd, path="~/bbb"):
    return [("mehmet@ubuntu", GREEN), (":", FG), (path, BLUE), ("$ ", FG), (cmd, FG)]


def kh(cmd):
    return host(cmd, "~/bbb/linux")


def note(text, color=FG, ann=""):
    return [(text, color), (ann, MAGENTA)] if ann else [(text, color)]


TITLE = "mehmet@ubuntu: ~/bbb"
KTITLE = "mehmet@ubuntu: ~/bbb/linux"
MINICOM = "mehmet@ubuntu: ~ — minicom -D /dev/ttyUSB0 -b 115200"

# 1) Kaynak kodu indirme
render("01_clone.png", TITLE, [
    host(f"git clone --depth=1 -b {KBRANCH} {KREPO}"),
    t("Cloning into 'linux'..."),
    t("remote: Enumerating objects: 78214, done."),
    t("Receiving objects: 100% (78214/78214), 213.47 MiB | 9.80 MiB/s, done."),
    t("Updating files: 100% (73619/73619), done."),
    host("cd linux"),
    kh("head -4 Makefile"),
    t("# SPDX-License-Identifier: GPL-2.0", DIM),
    note(f"VERSION = {MAJ}", CYAN, "              <-- sürüm: "
         f"{MAJ}.{MIN}.{SUB}"),
    t(f"PATCHLEVEL = {MIN}", CYAN),
    t(f"SUBLEVEL = {SUB}", CYAN),
    kh("du -sh ."),
    note("1.2G    .", FG, "                     <-- --depth=1 ile tarihçe indirilmez"),
])

# 2) Üst düzey klasörler
render("02_top_tree.png", KTITLE, [
    kh("ls"),
    t("arch     COPYING  crypto         fs       ipc      kernel    MAINTAINERS  net      scripts   sound  usr", CYAN),
    t("block    CREDITS  Documentation  include  Kbuild   lib       Makefile     README   security  tools  virt", CYAN),
    t("certs    drivers  firmware       init     Kconfig  LICENSES  mm           samples  ", CYAN),
    kh("ls arch"),
    note("alpha  arc  arm  arm64  csky  h8300  hexagon  ia64  m68k  ... riscv  s390  sh  sparc  x86", FG),
    kh("du -sh drivers arch fs net"),
    note("531M    drivers", FG, "                 <-- kaynağın yarısı sürücü"),
    t("140M    arch"),
    t(" 44M    fs"),
    t(" 34M    net"),
])

# 3) arch/arm
render("03_arch_arm.png", KTITLE, [
    kh("ls arch/arm"),
    t("boot    configs  include  Kconfig.debug  lib       mach-davinci  mach-imx  mach-omap2  ...", CYAN),
    t("common  crypto   kernel   Makefile       mach-at91 mach-exynos   mach-mvebu mach-stm32  mm  ...", CYAN),
    kh("ls arch/arm/configs | grep -E 'bb.org|omap2plus|multi_v7'"),
    note(f"{KDEFCONFIG}", GREEN, "                       <-- BeagleBoard'un ayarı"),
    t("multi_v7_defconfig"),
    t("omap2plus_defconfig"),
    kh("ls arch/arm/mach-omap2 | grep -E 'am33|board-generic|sleep33'"),
    t("am33xx.h"),
    t("am33xx-restart.c"),
    note("board-generic.c", FG, "                       <-- DT ile açılan OMAP kartlarının ortak girişi"),
    t("sleep33xx.S"),
    kh("ls arch/arm/boot/dts | grep 'am335x-bone'"),
    t("am335x-bone.dts                  am335x-boneblack.dts      am335x-boneblack-wireless.dts"),
    t("am335x-bone-common.dtsi          am335x-boneblack-common.dtsi  am335x-bonegreen.dts  ..."),
])

# 4) Yapılandırma
render("04_config.png", KTITLE, [
    kh(f"{MAKE} distclean"),
    kh(f"{MAKE} {KDEFCONFIG}"),
    t("  HOSTCC  scripts/basic/fixdep", DIM),
    t("  HOSTCC  scripts/kconfig/conf.o", DIM),
    t("  YACC    scripts/kconfig/parser.tab.[ch]", DIM),
    t("  HOSTLD  scripts/kconfig/conf", DIM),
    note("# configuration written to .config", GREEN, "        <-- ayarlar .config'e yazıldı"),
    kh("grep -E 'CONFIG_USB_ETH=|CONFIG_ROOT_NFS|CONFIG_KERNEL_LZO|CONFIG_SERIAL_8250_OMAP=' .config"),
    note("CONFIG_KERNEL_LZO=y", CYAN, "                  <-- kernel LZO ile sıkıştırılır (lzop gerekir)"),
    note("CONFIG_SERIAL_8250_OMAP=y", CYAN, "            <-- UART0 = ttyS0"),
    note("CONFIG_ROOT_NFS=y", CYAN, "                    <-- rootfs NFS'ten bağlanabilir"),
    note("CONFIG_USB_ETH=m", CYAN, "                     <-- g_ether: modül (m)"),
    kh(f"{MAKE} menuconfig"),
    note("   (isteğe bağlı: ayarları menüden incele/değiştir)", DIM),
])

# 5) Derleme
render("05_build.png", KTITLE, [
    kh(f"{MAKE} uImage dtbs LOADADDR={KLOAD} -j$(nproc)"),
    t("  CC      init/main.o", DIM),
    t("  ...", DIM),
    t("  LD      vmlinux", DIM),
    t("  OBJCOPY arch/arm/boot/Image", DIM),
    t("  Kernel: arch/arm/boot/Image is ready"),
    t("  LZO     arch/arm/boot/compressed/piggy_data", DIM),
    t("  LD      arch/arm/boot/compressed/vmlinux", DIM),
    t("  OBJCOPY arch/arm/boot/zImage", DIM),
    t("  Kernel: arch/arm/boot/zImage is ready"),
    note("  UIMAGE  arch/arm/boot/uImage", ORANGE, "        <-- zImage + 64 bayt U-Boot başlığı"),
    t(f"Image Name:   Linux-{KVER}", CYAN),
    t("Image Type:   ARM Linux Kernel Image (uncompressed)", CYAN),
    t(f"Load Address: {KLOAD}", CYAN),
    t(f"Entry Point:  {KLOAD}", CYAN),
    note("  Kernel: arch/arm/boot/uImage is ready", GREEN, ""),
    note("  DTC     arch/arm/boot/dts/am335x-boneblack.dtb", ORANGE, "  <-- device tree"),
    kh("ls -l arch/arm/boot/uImage arch/arm/boot/dts/am335x-boneblack.dtb"),
    t("-rw-rw-r-- 1 mehmet mehmet 10811832 Eki 20 10:41 arch/arm/boot/uImage"),
    t("-rw-rw-r-- 1 mehmet mehmet    67924 Eki 20 10:41 arch/arm/boot/dts/am335x-boneblack.dtb"),
])

# 6) Modüller
render("06_modules.png", KTITLE, [
    kh(f"{MAKE} modules -j$(nproc)"),
    t("  ...", DIM),
    note("  LD [M]  drivers/usb/gadget/legacy/g_ether.ko", ORANGE, "     <-- USB üzerinden Ethernet"),
    t("  LD [M]  drivers/usb/gadget/function/usb_f_ecm.ko", DIM),
    t("  ...", DIM),
    kh(f"{MAKE} INSTALL_MOD_PATH=~/bbb/rootfs modules_install"),
    t("  INSTALL drivers/usb/gadget/legacy/g_ether.ko", DIM),
    t("  ...", DIM),
    note(f"  DEPMOD  {KVER}", GREEN, "                              <-- modules.dep üretildi"),
    kh("ls ~/bbb/rootfs/lib/modules/"),
    t(KVER, CYAN),
    kh(f"find ~/bbb/rootfs/lib/modules/{KVER} -name '*.ko' | wc -l"),
    t("1874"),
])

# 7) Kartta yeni kernel
render("07_boot_new_kernel.png", MINICOM, [
    t("Running uenvcmd ..."),
    t("Booting from microSD ..."),
    t("10811832 bytes read in 682 ms (15.1 MiB/s)"),
    t("67924 bytes read in 8 ms (8.1 MiB/s)"),
    t("## Booting kernel from Legacy Image at 82000000 ..."),
    t(f"   Image Name:   Linux-{KVER}"),
    t("   Verifying Checksum ... OK"),
    t("## Flattened Device Tree blob at 88000000"),
    t("Starting kernel ...", GREEN),
    t(""),
    t("[    0.000000] Booting Linux on physical CPU 0x0"),
    note(f"[    0.000000] Linux version {KVER} (mehmet@ubuntu) (arm-linux-gnueabihf-gcc (Linaro GCC "
         f"{LINARO_REL}) {GCC_VER}", ORANGE, ""),
    note("[    0.000000] Machine model: TI AM335x BeagleBone Black", FG, "   <-- DTB'deki model"),
    note(f"[    0.000000] Kernel command line: console={KCONSOLE},115200n8 root=/dev/mmcblk1p2 rw rootwait",
         DIM, ""),
    t("..."),
    t("debian@beaglebone:~$ cat /proc/version"),
    note(f"Linux version {KVER} (mehmet@ubuntu) ...", CYAN, "      <-- senin derlediğin kernel"),
])

# 8) Sık görülen hatalar
render("08_errors.png", KTITLE + " (temsili hatalar)", [
    kh(f"{MAKE} uImage dtbs -j4"),
    note("multiple (or no) load addresses: ", RED, ""),
    t("This is incompatible with uImages", RED),
    note("Specify LOADADDR on the commandline to build an uImage", RED, "  <-- LOADADDR=... eksik"),
    t(""),
    note('"mkimage" command not found - U-Boot images will not be built', RED, "  <-- u-boot-tools"),
    t(""),
    note("/bin/sh: 1: lzop: not found", RED, "                              <-- sudo apt install lzop"),
    t(""),
    note("scripts/extract-cert.c:21:10: fatal error: openssl/bio.h: No such file", RED, "  <-- libssl-dev"),
    t(""),
    note("/bin/sh: 1: bc: not found", RED, "                                <-- sudo apt install bc"),
])
