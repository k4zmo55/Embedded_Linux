"""Kernel modülü bölümü için terminal ekran görüntülerini üretir.

Kullanım: python tools/kmod_shots.py [çıktı klasörü]
"""
from term_shots import (render, t, FG, DIM, GREEN, BLUE, YELLOW, CYAN, RED,
                        MAGENTA, ORANGE)
from term_shots import V, set_default_out

KVER = V("kernel.version")
CC = V("build.cross_compile")
NFS_DIR = V("network.nfs_dir")
set_default_out("images/kmod")

MOD = "~/code/21_kernel_module"
ABS = "/home/mehmet/code/21_kernel_module"
VERMAGIC = f"{KVER} SMP preempt mod_unload modversions ARMv7 p2v8"
MINICOM = "mehmet@ubuntu: ~ — minicom (BBB, BusyBox rootfs)"


def host(cmd, path=MOD):
    return [("mehmet@ubuntu", GREEN), (":", FG), (path, BLUE), ("$ ", FG), (cmd, FG)]


def sh(cmd, path="~"):
    return [(f"{path} # ", GREEN), (cmd, FG)]


def note(text, color=FG, ann=""):
    return [(text, color), (ann, MAGENTA)] if ann else [(text, color)]


# 1) Derleme ve modinfo
render("01_build.png", "mehmet@ubuntu: ~/code/21_kernel_module", [
    host("ls"),
    t("Makefile  hello.c  hello_lib.c  hello_lib.h  hello_user.c", FG),
    host("make"),
    note(f"make -C /home/mehmet/bbb/linux M={ABS} ARCH=arm CROSS_COMPILE={CC} modules", DIM),
    note("make[1]: Entering directory '/home/mehmet/bbb/linux'", DIM),
    note(f"  CC [M]  {ABS}/hello.o", FG),
    note(f"  CC [M]  {ABS}/hello_lib.o", FG),
    note(f"  CC [M]  {ABS}/hello_user.o", FG),
    note(f"  MODPOST {ABS}/Module.symvers", YELLOW, "      <-- semboller çözülüyor"),
    note(f"  CC [M]  {ABS}/hello.mod.o", FG),
    note(f"  LD [M]  {ABS}/hello.ko", GREEN),
    note(f"  LD [M]  {ABS}/hello_lib.ko", GREEN),
    note(f"  LD [M]  {ABS}/hello_user.ko", GREEN),
    note("make[1]: Leaving directory '/home/mehmet/bbb/linux'", DIM),
    host("file hello.ko"),
    note("hello.ko: ELF 32-bit LSB relocatable, ARM, EABI5 version 1 (SYSV), not stripped", CYAN),
    host("modinfo hello.ko"),
    note(f"filename:       {ABS}/hello.ko", FG),
    note("description:    First kernel module: hello with parameters", FG),
    note("author:         Embedded Linux kitabı", FG),
    note("license:        GPL", FG),
    note("depends:", FG),
    note("name:           hello", FG),
    note(f"vermagic:       {VERMAGIC}", ORANGE, "  <-- hangi kernel için"),
    note("parm:           name:Name to greet (charp)", CYAN),
    note("parm:           count:How many times to greet (1-10) (int)", CYAN),
])

# 2) Kartta yükleme
render("02_insmod.png", MINICOM, [
    host(f"sudo cp *.ko {NFS_DIR}/root/"),
    t("--- BBB ---", MAGENTA),
    sh("uname -r"),
    note(KVER, CYAN, "                                       <-- vermagic ile aynı olmalı"),
    sh("insmod hello.ko name=Mehmet count=3"),
    sh("dmesg | tail -5"),
    note("[  812.441503] hello: loading out-of-tree module taints kernel.", YELLOW),
    note("[  812.447790] hello: Hello Mehmet! (1/3)", GREEN),
    note("[  812.451622] hello: Hello Mehmet! (2/3)", GREEN),
    note("[  812.455413] hello: Hello Mehmet! (3/3)", GREEN),
    note(f"[  812.459268] hello: running on Linux {KVER} (armv7l)", GREEN),
    sh("lsmod"),
    note("Module                  Size  Used by    Tainted: G", FG),
    note("hello                  16384  0", CYAN),
    sh("rmmod hello"),
    sh("dmesg | tail -1"),
    note("[  840.102755] hello: Goodbye Mehmet, count was 3", GREEN),
])

# 3) Parametreler ve sysfs
render("03_params.png", MINICOM, [
    sh("insmod hello.ko"),
    sh("ls /sys/module/hello/parameters/"),
    note("count  name", CYAN),
    sh("cat /sys/module/hello/parameters/name /sys/module/hello/parameters/count"),
    note("BeagleBone", CYAN),
    note("1", CYAN),
    sh("echo 5 > /sys/module/hello/parameters/count"),
    note("", FG, "                    <-- 0644: root değiştirebilir"),
    sh("echo Ali > /sys/module/hello/parameters/name"),
    note("sh: can't create /sys/module/hello/parameters/name: Permission denied", RED, "  <-- 0444"),
    sh("rmmod hello; dmesg | tail -1"),
    note("[  901.338214] hello: Goodbye BeagleBone, count was 5", GREEN),
])

# 4) Bağımlılık: insmod ve modprobe
render("04_depends.png", "mehmet@ubuntu + BBB", [
    t("--- BBB ---", MAGENTA),
    sh("insmod hello_user.ko"),
    note("insmod: can't insert 'hello_user.ko': unknown symbol in module, or unknown parameter", RED),
    sh("dmesg | tail -1"),
    note("[  950.120347] hello_user: Unknown symbol hello_lib_add (err -2)", RED, "  <-- hello_lib yok"),
    t("--- Host: rootfs'e kur ---", MAGENTA),
    host("make install INSTALL_MOD_PATH=~/bbb/rootfs"),
    note(f"  INSTALL {ABS}/hello.ko", FG),
    note(f"  INSTALL {ABS}/hello_lib.ko", FG),
    note(f"  INSTALL {ABS}/hello_user.ko", FG),
    note(f"  DEPMOD  {KVER}", GREEN, "                                <-- modules.dep güncellendi"),
    host(f"grep hello ~/bbb/rootfs/lib/modules/{KVER}/modules.dep"),
    note("extra/hello.ko:", CYAN),
    note("extra/hello_lib.ko:", CYAN),
    note("extra/hello_user.ko: extra/hello_lib.ko", CYAN, "     <-- bağımlılık"),
    host(f"sudo cp -a ~/bbb/rootfs/lib/modules/{KVER} {NFS_DIR}/lib/modules/"),
    t("--- BBB ---", MAGENTA),
    sh("modprobe hello_user"),
    sh("lsmod"),
    note("Module                  Size  Used by    Tainted: G", FG),
    note("hello_user             16384  0", CYAN),
    note("hello_lib              16384  1 hello_user", CYAN, "       <-- modprobe önce bunu yükledi"),
    sh("modprobe -r hello_user"),
    note("", FG, "                    <-- ikisini de çıkarır"),
])

# 5) Hatalar
render("05_errors.png", MINICOM + " (temsili hatalar)", [
    sh("insmod hello.ko"),
    note("insmod: can't insert 'hello.ko': invalid module format", RED),
    sh("dmesg | tail -1"),
    note("hello: version magic '5.10.168-ti-r71 SMP preempt mod_unload modversions ARMv7 p2v8'", RED),
    note(f"       should be '{VERMAGIC}'", RED),
    note("", FG, "            <-- modül başka bir kernel için derlenmiş"),
    t(""),
    sh("insmod hello.ko count=20"),
    note("insmod: can't insert 'hello.ko': Invalid argument", RED),
    note("[ 1022.517008] hello: count must be 1-10, got 20", RED, "  <-- init -EINVAL döndü"),
    t(""),
    sh("rmmod hello_lib"),
    note("rmmod: can't unload module 'hello_lib': Resource temporarily unavailable", RED),
    note("", FG, "            <-- hello_user hâlâ kullanıyor (Used by 1)"),
])
