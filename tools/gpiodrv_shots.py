"""GPIO platform sürücüsü bölümü için terminal ekran görüntülerini üretir.

Kullanım: python tools/gpiodrv_shots.py [çıktı klasörü]
"""
from term_shots import (render, t, FG, DIM, GREEN, BLUE, YELLOW, CYAN, RED,
                        MAGENTA, ORANGE)
from term_shots import V, set_default_out

CC = V("build.cross_compile")
NFS_DIR = V("network.nfs_dir")
TFTP_DIR = V("network.tftp_dir")
KDIR = "~/bbb/" + V("kernel.dir")
set_default_out("images/gpiodrv")

MOD = "~/code/23_gpio_platform_driver"
ABS = "/home/mehmet/code/23_gpio_platform_driver"
MINICOM = "mehmet@ubuntu: ~ — minicom (BBB, BusyBox rootfs)"
DEV = "/sys/bus/platform/devices/bbb-gpio-demo"


def host(cmd, path=MOD):
    return [("mehmet@ubuntu", GREEN), (":", FG), (path, BLUE), ("$ ", FG), (cmd, FG)]


def sh(cmd, path="~"):
    return [(f"{path} # ", GREEN), (cmd, FG)]


def note(text, color=FG, ann=""):
    return [(text, color), (ann, MAGENTA)] if ann else [(text, color)]


# 1) DTB'yi derleme
render("01_dtb_build.png", "mehmet@ubuntu: ~/bbb/linux", [
    host("cp ~/code/23_gpio_platform_driver/am335x-boneblack-gpiodemo.dts arch/arm/boot/dts/", KDIR),
    host("echo 'dtb-$(CONFIG_SOC_AM33XX) += am335x-boneblack-gpiodemo.dtb' >> arch/arm/boot/dts/Makefile", KDIR),
    host(f"make ARCH=arm CROSS_COMPILE={CC} am335x-boneblack-gpiodemo.dtb", KDIR),
    note("  DTC     arch/arm/boot/dts/am335x-boneblack-gpiodemo.dtb", GREEN),
    host(f"sudo cp arch/arm/boot/dts/am335x-boneblack-gpiodemo.dtb {TFTP_DIR}/am335x-boneblack.dtb", KDIR),
    note("", FG, "             <-- uEnv.txt bu adla çekiyor (Bölüm 12.8)"),
    t("--- BBB yeniden açıldıktan sonra ---", MAGENTA),
    sh("ls /proc/device-tree/bbb-gpio-demo/"),
    note("button-gpios  compatible  led-gpios  name  phandle  pinctrl-0  pinctrl-names", CYAN),
    sh("cat /proc/device-tree/bbb-gpio-demo/compatible; echo"),
    note("bbb,gpio-demo", CYAN),
    sh(f"ls {DEV}/"),
    note("driver_override  modalias  of_node  power  subsystem  uevent", CYAN, "  <-- henüz 'driver' yok"),
])

# 2) Sürücüyü yükleme
render("02_insmod.png", "mehmet@ubuntu + BBB", [
    host("make && make test"),
    note(f"  CC [M]  {ABS}/bbb_gpio_demo.o", FG),
    note(f"  LD [M]  {ABS}/bbb_gpio_demo.ko", GREEN),
    note(f"{CC}gcc -Wall -static -o presses_wait presses_wait.c", FG),
    host(f"sudo cp bbb_gpio_demo.ko presses_wait {NFS_DIR}/root/"),
    t("--- BBB ---", MAGENTA),
    sh("insmod bbb_gpio_demo.ko"),
    sh("dmesg | tail -1"),
    note("[  611.204587] bbb-gpio-demo bbb-gpio-demo: ready: LED off, button on irq 66", GREEN),
    sh(f"ls {DEV}/"),
    note("driver  driver_override  led  modalias  of_node  power  presses  subsystem  uevent", CYAN),
    sh("grep -E 'gpio-(49|60) ' /sys/kernel/debug/gpio"),
    note(" gpio-49  (                    |button              ) in  lo IRQ", CYAN, "  <-- sürücü aldı"),
    note(" gpio-60  (                    |led                 ) out lo", CYAN),
    sh("grep bbb-gpio-demo /proc/interrupts"),
    note(" 66:          0  4804c000.gpio  17 Edge      bbb-gpio-demo", CYAN),
])

# 3) Deneme: sysfs ve buton
render("03_use.png", MINICOM, [
    sh(f"echo 1 > {DEV}/led"),
    note("", FG, "                          <-- LED yandı"),
    sh(f"cat {DEV}/led {DEV}/presses"),
    note("1", CYAN),
    note("0", CYAN),
    note("(butona üç kez basıldı)", DIM),
    sh("dmesg | tail -3"),
    note("[  650.880312] bbb-gpio-demo bbb-gpio-demo: button pressed (1), LED off", GREEN),
    note("[  652.115407] bbb-gpio-demo bbb-gpio-demo: button pressed (2), LED on", GREEN),
    note("[  653.020981] bbb-gpio-demo bbb-gpio-demo: button pressed (3), LED off", GREEN),
    sh("grep bbb-gpio-demo /proc/interrupts"),
    note(" 66:          3  4804c000.gpio  17 Edge      bbb-gpio-demo", CYAN, "     <-- 3 kesme"),
    sh("./presses_wait"),
    note("presses = 3, waiting for the button...", FG),
    note("presses = 4", GREEN, "                                <-- poll() uyandı"),
    note("presses = 5", GREEN),
    note("^C", DIM),
])

# 4) unbind / bind
render("04_bind.png", MINICOM, [
    sh("ls /sys/bus/platform/drivers/bbb-gpio-demo/"),
    note("bbb-gpio-demo  bind  module  uevent  unbind", CYAN),
    sh("echo bbb-gpio-demo > /sys/bus/platform/drivers/bbb-gpio-demo/unbind"),
    note("", FG, "                          <-- LED söner, kesme ve GPIO'lar bırakılır"),
    sh("grep -E 'gpio-(49|60) ' /sys/kernel/debug/gpio"),
    note("", FG, "                          <-- boş: GPIO'lar artık serbest"),
    sh("echo bbb-gpio-demo > /sys/bus/platform/drivers/bbb-gpio-demo/bind"),
    sh("dmesg | tail -1"),
    note("[  702.551236] bbb-gpio-demo bbb-gpio-demo: ready: LED off, button on irq 66", GREEN, "  <-- probe tekrar"),
    sh("rmmod bbb_gpio_demo"),
])

# 5) Hatalar
render("05_errors.png", MINICOM + " (temsili hatalar)", [
    sh("insmod bbb_gpio_demo.ko; dmesg | tail -1"),
    note("", FG, "            <-- hiçbir mesaj yok: DT'de compatible eşleşen düğüm yok"),
    t(""),
    sh("echo 60 > /sys/class/gpio/export; insmod bbb_gpio_demo.ko; dmesg | tail -1"),
    note("bbb-gpio-demo bbb-gpio-demo: error -EBUSY: cannot get led-gpios", RED),
    note("", FG, "            <-- GPIO 60 sysfs'te export edilmiş"),
    t(""),
    sh("dmesg | grep pinctrl"),
    note("pinctrl-single 44e10800.pinmux: pin PIN30 already requested by ocp:P9_12_pinmux; cannot claim for bbb-gpio-demo", RED),
    note("", FG, "            <-- Debian'da cape-universal açık (Bölüm 16.6)"),
])
