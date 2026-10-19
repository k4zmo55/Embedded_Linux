"""GPIO / sysfs bölümü için terminal ekran görüntülerini üretir.

Kullanım: python tools/gpio_shots.py [çıktı klasörü]
"""
from term_shots import (render, t, FG, DIM, GREEN, BLUE, YELLOW, CYAN, RED,
                        MAGENTA, ORANGE)
from term_shots import V, set_default_out

CC = V("build.cross_compile")
BOARD_IP = V("network.board_ip")
set_default_out("images/gpio")

BBB = "debian@beaglebone: ~ (SSH)"


def b(cmd, path="~"):
    return [("debian@beaglebone", GREEN), (":", FG), (path, BLUE), ("$ ", FG), (cmd, FG)]


def r(cmd, path="~"):
    return [("root@beaglebone", GREEN), (":", FG), (path, BLUE), ("# ", FG), (cmd, FG)]


def host(cmd, path="~/bbb/apps"):
    return [("mehmet@ubuntu", GREEN), (":", FG), (path, BLUE), ("$ ", FG), (cmd, FG)]


def note(text, color=FG, ann=""):
    return [(text, color), (ann, MAGENTA)] if ann else [(text, color)]


LED = "/sys/class/leds/beaglebone:green:usr3"

# 1) USER LED'ler
render("01_leds_sysfs.png", BBB, [
    b("ls /sys/class/leds/"),
    t("beaglebone:green:usr0  beaglebone:green:usr1  beaglebone:green:usr2  beaglebone:green:usr3", CYAN),
    r(f"cd {LED}"),
    r("ls", "usr3"),
    t("brightness  device  max_brightness  power  subsystem  trigger  uevent", CYAN),
    r("cat trigger", "usr3"),
    note("none ... timer oneshot heartbeat ... default-on ... [mmc1] ...", FG, "  <-- [..] = şu anki"),
    r("echo none > trigger", "usr3"),
    note("", FG, ""),
    r("echo 1 > brightness", "usr3"),
    note("", FG, "                                     <-- LED yandı"),
    r("echo timer > trigger", "usr3"),
    r("echo 100 > delay_on; echo 900 > delay_off", "usr3"),
    note("", FG, "                                     <-- 100 ms yanık, 900 ms sönük"),
    r("echo mmc1 > trigger", "usr3"),
    note("", FG, "                                     <-- varsayılana dön (eMMC erişimi)"),
])

# 2) GPIO tablosu
render("02_gpio_debug.png", BBB, [
    r("cat /sys/kernel/debug/gpio | head -12"),
    t("gpiochip0: GPIOs 0-31, parent: platform/44e07000.gpio, gpio-0-31:", CYAN),
    t(" gpio-6   (                    |cd                  ) in  lo IRQ ACTIVE LOW"),
    t("..."),
    note("gpiochip1: GPIOs 32-63, parent: platform/4804c000.gpio, gpio-32-63:", CYAN, "  <-- GPIO1 bankası"),
    note(" gpio-53  (P8_.. / usr0          |beaglebone:green:usr0) out lo", FG, "  <-- GPIO1_21 = 32+21"),
    t(" gpio-54  (                    |beaglebone:green:usr1) out lo"),
    t(" gpio-55  (                    |beaglebone:green:usr2) out hi"),
    t(" gpio-56  (                    |beaglebone:green:usr3) out lo"),
    t("gpiochip2: GPIOs 64-95, parent: platform/481ac000.gpio, gpio-64-95:", CYAN),
    t("gpiochip3: GPIOs 96-127, parent: platform/481ae000.gpio, gpio-96-127:", CYAN),
])

# 3) pinctrl
render("03_pinctrl.png", BBB, [
    r("ls /sys/kernel/debug/pinctrl/"),
    note("44e10800.pinmux-pinctrl-single  pinctrl-devices  pinctrl-handles  pinctrl-maps", CYAN, ""),
    r("cd /sys/kernel/debug/pinctrl/44e10800.pinmux-pinctrl-single"),
    r("grep -E '44e10854|44e10878' pins", "/sys/kernel/debug/pinctrl/44e10800.pinmux-pinctrl-single"),
    note("pin 21 (PIN21) 21:gpio-32-63 44e10854 00000007 pinctrl-single", ORANGE, "  <-- USR0: mod 7 (GPIO)"),
    note("pin 30 (PIN30) 28:gpio-32-63 44e10878 00000037 pinctrl-single", ORANGE, "  <-- P9_12: mod 7, giriş, pull-up"),
    r("grep 'pin 21 ' pinmux-pins", "/sys/kernel/debug/pinctrl/44e10800.pinmux-pinctrl-single"),
    note("pin 21 (PIN21): 4a326000.target-module... function user_leds_s0 group user_leds_s0", FG, ""),
])

# 4) Eski sysfs GPIO arayüzü
render("04_gpio_sysfs_legacy.png", BBB, [
    r("echo 60 > /sys/class/gpio/export"),
    r("ls /sys/class/gpio/gpio60"),
    t("active_low  device  direction  edge  label  power  subsystem  uevent  value", CYAN),
    r("cat /sys/class/gpio/gpio60/direction"),
    t("in"),
    r("echo out > /sys/class/gpio/gpio60/direction"),
    r("echo 1 > /sys/class/gpio/gpio60/value"),
    note("", FG, "                                          <-- P9_12 = 3.3 V"),
    r("echo 0 > /sys/class/gpio/gpio60/value"),
    r("echo 60 > /sys/class/gpio/unexport"),
])

# 5) libgpiod
render("05_libgpiod.png", BBB, [
    r("gpiodetect"),
    t("gpiochip0 [44e07000.gpio] (32 lines)"),
    note("gpiochip1 [4804c000.gpio] (32 lines)", FG, "        <-- GPIO1 bankası"),
    t("gpiochip2 [481ac000.gpio] (32 lines)"),
    t("gpiochip3 [481ae000.gpio] (32 lines)"),
    r("gpioinfo gpiochip1 | sed -n '22p;29p'"),
    note('	line  21: "P8_.."   "beaglebone:green:usr0" output active-high [used]', FG, ""),
    note('	line  28: "P9_12"   unused input active-high', FG, "       <-- GPIO1_28"),
    t("--- libgpiod 1.x (Debian 10/11/12) ---", MAGENTA),
    r("gpioset gpiochip1 28=1"),
    r("gpioget gpiochip1 28"),
    t("1"),
    t("--- libgpiod 2.x (Debian 13 ve sonrası) ---", MAGENTA),
    r("gpioset -c gpiochip1 28=1"),
    note("^C", DIM, "                                           <-- v2: Ctrl-C'ye kadar tutar"),
])

# 6) C uygulaması
render("06_led_app.png", "mehmet@ubuntu: ~/bbb/apps + BBB", [
    host(f"{CC}gcc -Wall -o usr_led usr_led.c"),
    host(f"scp usr_led debian@{BOARD_IP}:~/"),
    t("--- BBB ---", MAGENTA),
    r("./usr_led"),
    t("usage: ./usr_led <led 0-3> <trigger|brightness> <value>", DIM),
    t("  trigger    : none, heartbeat, timer, oneshot, default-on", DIM),
    t("  brightness : 0, 1", DIM),
    r("./usr_led 3 trigger none"),
    note("usr3 trigger -> none", GREEN, ""),
    r("./usr_led 3 brightness 1"),
    note("usr3 brightness -> 1", GREEN, "                             <-- LED yandı"),
    r("./usr_led 3 trigger heartbeat"),
    note("usr3 trigger -> heartbeat", GREEN, ""),
    r("./usr_led 5 brightness 1"),
    note("Invalid LED number: 5 (valid: 0-3)", RED, ""),
])

# 7) Hatalar
render("07_errors.png", BBB + " (temsili hatalar)", [
    b(f"echo 1 > {LED}/brightness"),
    note("-bash: /sys/class/leds/.../brightness: Permission denied", RED, "   <-- root/sudo"),
    t(""),
    r("echo 60 > /sys/class/gpio/export"),
    note("bash: echo: write error: Device or resource busy", RED, "         <-- pin başka sürücüde / zaten export"),
    t(""),
    r("echo 60 > /sys/class/gpio/export"),
    note("bash: echo: write error: Invalid argument", RED, "             <-- yeni kernel: numaralar 512+"),
    t(""),
    r("./led_control brightness 1"),
    note("trigger value write error", RED, "                          <-- kursun kodundaki hata (15.7)"),
    t(""),
    r("ls /sys/kernel/debug"),
    note("(boş)", DIM, "                                             <-- mount -t debugfs none /sys/kernel/debug"),
])
