"""SPL ve U-Boot derleme notu için terminal ekran görüntülerini üretir.

Kullanım: python tools/uboot_build_shots.py images/uboot_build
"""
from term_shots import (render, t, FG, DIM, GREEN, BLUE, CYAN, RED, MAGENTA,
                        ORANGE)
from term_shots import V, set_default_out

TC_DIR = V("build.toolchain_dir")
DEFCONFIG = V("build.uboot_defconfig")
ETH_DEV = V("build.eth_device")
LINARO_REL = V("build.linaro_release")
GCC_VER = V("build.gcc_version")
UBOOT_VER = V("build.uboot_version")
set_default_out("images/uboot_build")


def host(cmd, path="~/bbb"):
    return [("mehmet@ubuntu", GREEN), (":", FG), (path, BLUE), ("$ ", FG), (cmd, FG)]


def ubh(cmd):
    return host(cmd, f"~/bbb/u-boot-{UBOOT_VER}")


def note(text, color=FG, ann=""):
    return [(text, color), (ann, MAGENTA)] if ann else [(text, color)]


TITLE = "mehmet@ubuntu: ~/bbb"
UTITLE = f"mehmet@ubuntu: ~/bbb/u-boot-{UBOOT_VER}"

# 1) Linaro toolchain kurulumu
render("01_toolchain_install.png", TITLE, [
    host(f"wget https://releases.linaro.org/components/toolchain/binaries/{LINARO_REL}/"),
    t(f"       arm-linux-gnueabihf/{TC_DIR}.tar.xz", FG),
    t(f"{TC_DIR}.tar.xz 100%[=====>] 115.97M  8.4MB/s"),
    host(f"tar -xf {TC_DIR}.tar.xz"),
    host(f"ls {TC_DIR}/bin | head -4"),
    t("arm-linux-gnueabihf-addr2line", CYAN),
    t("arm-linux-gnueabihf-ar", CYAN),
    t("arm-linux-gnueabihf-as", CYAN),
    t("arm-linux-gnueabihf-c++", CYAN),
    host(f'echo \'export PATH=$HOME/bbb/{TC_DIR}/bin:$PATH\' >> ~/.bashrc'),
    host("source ~/.bashrc"),
    host("arm-linux-gnueabihf-gcc --version"),
    note(f"arm-linux-gnueabihf-gcc (Linaro GCC {LINARO_REL}) {GCC_VER}", GREEN, "   <-- PATH'te, hazır"),
])

# 2) Cross compile ne demek: aynı kod, iki mimari
render("02_cross_compile_demo.png", TITLE, [
    host("cat hello.c"),
    t('#include <stdio.h>', CYAN),
    t('int main(void) { printf("Merhaba BBB\\n"); return 0; }', CYAN),
    host("gcc hello.c -o hello_x86"),
    host("arm-linux-gnueabihf-gcc hello.c -o hello_arm"),
    host("file hello_x86 hello_arm"),
    note("hello_x86: ELF 64-bit LSB pie executable, x86-64, ...", FG, "        <-- PC için"),
    note("hello_arm: ELF 32-bit LSB pie executable, ARM, EABI5 ..., hard-float", ORANGE,
         " <-- BBB için"),
    host("./hello_x86"),
    t("Merhaba BBB"),
    host("./hello_arm"),
    note("bash: ./hello_arm: cannot execute binary file: Exec format error", RED,
         "  <-- PC ARM kodu çalıştıramaz"),
])

# 3) Gerekli host paketleri ve U-Boot kaynağı
render("03_uboot_source.png", TITLE, [
    host("sudo apt install build-essential bison flex libssl-dev device-tree-compiler \\"),
    t("     u-boot-tools bc lzop libncurses-dev libgnutls28-dev"),
    host(f"wget https://ftp.denx.de/pub/u-boot/u-boot-{UBOOT_VER}.tar.bz2"),
    host(f"tar -xjf u-boot-{UBOOT_VER}.tar.bz2"),
    host(f"cd u-boot-{UBOOT_VER}"),
    [("mehmet@ubuntu", GREEN), (":", FG), (f"~/bbb/u-boot-{UBOOT_VER}", BLUE), ("$ ", FG), ("ls", FG)],
    t("api   arch    board  cmd     common  configs  disk  doc  drivers  dts  env ..."),
    [("mehmet@ubuntu", GREEN), (":", FG), (f"~/bbb/u-boot-{UBOOT_VER}", BLUE), ("$ ", FG),
     ("ls configs | grep am335x", FG)],
    t("am335x_boneblack_vboot_defconfig", CYAN),
    note(f"{DEFCONFIG}", CYAN, "              <-- BBB dahil tüm AM335x kartlar"),
    t("am335x_evm_spiboot_defconfig", CYAN),
    t("am335x_hs_evm_defconfig", CYAN),
    t("...", DIM),
])

# 4) Yapılandırma
render("04_uboot_config.png", UTITLE, [
    ubh("make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- distclean"),
    ubh(f"make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- {DEFCONFIG}"),
    t("  HOSTCC  scripts/basic/fixdep", DIM),
    t("  HOSTCC  scripts/kconfig/conf.o", DIM),
    t("  YACC    scripts/kconfig/parser.tab.[ch]", DIM),
    t("  LEX     scripts/kconfig/lexer.lex.c", DIM),
    t("  HOSTLD  scripts/kconfig/conf", DIM),
    t("#", DIM),
    note("# configuration written to .config", GREEN, "        <-- ayarlar .config'e yazıldı"),
    t("#", DIM),
    ubh("make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- menuconfig"),
    note("   (isteğe bağlı: ayarları menüden incele/değiştir)", DIM),
])

# 5) Derleme
render("05_uboot_build.png", UTITLE, [
    ubh("make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- -j4"),
    t("  CC      arch/arm/mach-omap2/am33xx/board.o", DIM),
    t("  ...", DIM),
    t("  LD      spl/u-boot-spl", DIM),
    t("  OBJCOPY spl/u-boot-spl-nodtb.bin", DIM),
    t("  COPY    spl/u-boot-spl.bin", DIM),
    note("  MKIMAGE MLO", ORANGE, "                         <-- SD kart için SPL"),
    t("  LD      u-boot", DIM),
    t("  OBJCOPY u-boot-nodtb.bin", DIM),
    note("  MKIMAGE u-boot.img", ORANGE, "                  <-- tam U-Boot"),
    ubh("ls -l MLO u-boot.img spl/u-boot-spl.bin"),
    t("-rw-rw-r-- 1 mehmet mehmet  86124 Eki 19 14:02 MLO"),
    note("-rw-rw-r-- 1 mehmet mehmet  86104 Eki 19 14:02 spl/u-boot-spl.bin", FG,
         "  <-- seri boot için"),
    t("-rw-rw-r-- 1 mehmet mehmet 425388 Eki 19 14:02 u-boot.img"),
    ubh("file spl/u-boot-spl u-boot"),
    t("spl/u-boot-spl: ELF 32-bit LSB executable, ARM, EABI5 version 1 (SYSV), statically linked", CYAN),
    t("u-boot:         ELF 32-bit LSB executable, ARM, EABI5 version 1 (SYSV), statically linked", CYAN),
])

# 6) SD karta kopyalama
render("06_copy_sd.png", UTITLE, [
    ubh("cp MLO u-boot.img /media/mehmet/BOOT/"),
    ubh("ls -l /media/mehmet/BOOT"),
    t("-rw-r--r-- 1 mehmet mehmet  86124 Eki 19 14:05 MLO"),
    t("-rw-r--r-- 1 mehmet mehmet 425388 Eki 19 14:05 u-boot.img"),
    t("-rw-r--r-- 1 mehmet mehmet    412 Eki 18 11:45 uEnv.txt"),
    ubh("sync && sudo umount /media/mehmet/BOOT"),
])

# 7) Kartta yeni U-Boot'u doğrulama
render("07_new_uboot_boot.png", "mehmet@ubuntu: ~ — minicom -D /dev/ttyUSB0 -b 115200", [
    note(f"U-Boot SPL {UBOOT_VER} (Oct 19 2026 - 14:02:11)", ORANGE, "   <-- senin derleme tarihin"),
    t("Trying to boot from MMC1"),
    t("reading u-boot.img"),
    t(""),
    note(f"U-Boot {UBOOT_VER} (Oct 19 2026 - 14:02:11 +0300)", ORANGE, "   <-- senin derlemen"),
    t(""),
    t("CPU  : AM335X-GP rev 2.1"),
    t("Model: TI AM335x BeagleBone Black"),
    t("DRAM:  512 MiB"),
    t("MMC:   OMAP SD/MMC: 0, OMAP SD/MMC: 1"),
    note(f"Net:   eth2: {ETH_DEV}, eth3: usb_ether", FG, "  <-- yeni adlar"),
    t("Hit any key to stop autoboot:  0"),
    [("=> ", ORANGE), ("version", FG)],
    t(f"U-Boot {UBOOT_VER} (Oct 19 2026 - 14:02:11 +0300)"),
    t(f"arm-linux-gnueabihf-gcc (Linaro GCC {LINARO_REL}) {GCC_VER}", CYAN),
])

# 8) Sık görülen hatalar
render("08_errors.png", UTITLE + " (temsili hatalar)", [
    ubh("make CROSS_COMPILE=arm-linux-gnueabihf- -j4"),
    note("/bin/sh: 1: arm-linux-gnueabihf-gcc: not found", RED, "     <-- PATH ayarlı değil"),
    t(""),
    note("include/linux/compiler-gcc.h:121:30: fatal error: linux/compiler-gcc11.h:", RED, ""),
    note("No such file or directory", RED, "                            <-- GCC U-Boot'tan yeni"),
    t(""),
    note("multiple definition of `yylloc'; ...dtc-lexer.lex.o: first defined here", RED,
         "  <-- host GCC 10+"),
    t(""),
    note("tools/../include/image.h:...: fatal error: openssl/evp.h: No such file", RED,
         "  <-- libssl-dev"),
    t(""),
    note("/bin/sh: 1: bison: not found", RED, "                         <-- bison/flex eksik"),
])
