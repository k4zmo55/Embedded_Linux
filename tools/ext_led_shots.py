"""Harici LED bölümü için terminal ekran görüntülerini üretir.

Kullanım: python tools/ext_led_shots.py [çıktı klasörü]
"""
from term_shots import (render, t, FG, DIM, GREEN, BLUE, YELLOW, CYAN, RED,
                        MAGENTA, ORANGE)
from term_shots import V, set_default_out

CC = V("build.cross_compile")
BOARD_IP = V("network.board_ip")
set_default_out("images/ext_led")

BBB = "root@beaglebone: ~ (SSH)"


def r(cmd, path="~"):
    return [("root@beaglebone", GREEN), (":", FG), (path, BLUE), ("# ", FG), (cmd, FG)]


def host(cmd, path="~/code"):
    return [("mehmet@ubuntu", GREEN), (":", FG), (path, BLUE), ("$ ", FG), (cmd, FG)]


def note(text, color=FG, ann=""):
    return [(text, color), (ann, MAGENTA)] if ann else [(text, color)]


# 1) Pin kontrolü
render("01_pin_check.png", BBB, [
    r("config-pin -q P9_12"),
    note("P9_12 Mode: default Direction: in Value: 0", FG, "            <-- BeagleBoard Debian'da"),
    r("config-pin P9_12 gpio"),
    r("config-pin -q P9_12"),
    note("P9_12 Mode: gpio Direction: in Value: 0", GREEN, ""),
    r("grep 44e10878 /sys/kernel/debug/pinctrl/44e10800.pinmux*/pins"),
    note("pin 30 (PIN30) 28:gpio-32-63 44e10878 00000027 pinctrl-single", ORANGE, "  <-- mod 7 = GPIO"),
])

# 2) Komut satırından test
render("02_cmdline_test.png", BBB, [
    r("echo 60 > /sys/class/gpio/export"),
    r("echo out > /sys/class/gpio/gpio60/direction"),
    r("echo 1 > /sys/class/gpio/gpio60/value"),
    note("", FG, "                                     <-- harici LED yandı"),
    r("echo 0 > /sys/class/gpio/gpio60/value"),
    note("", FG, "                                     <-- söndü"),
    r("echo 60 > /sys/class/gpio/unexport"),
    t("--- ya da libgpiod 1.x ile ---", MAGENTA),
    r("gpioset gpiochip1 28=1"),
    r("gpioset gpiochip1 28=0"),
])

# 3) Derleme ve çalıştırma
render("03_build_run.png", "mehmet@ubuntu + BBB", [
    host(f"{CC}gcc -Wall -Ilib -o led_blink 16_external_led/led_blink.c lib/gpio_driver.c"),
    host(f"scp led_blink root@{BOARD_IP}:~/"),
    t("--- BBB ---", MAGENTA),
    r("./led_blink 60 250"),
    note("GPIO 60 blinking every 250 ms, press Ctrl-C to stop", GREEN, ""),
    note("^C", DIM, "                                          <-- Ctrl-C"),
    note("LED off, GPIO 60 released", GREEN, "                     <-- temiz kapanış"),
    r("ls /sys/class/gpio"),
    note("export  gpiochip0  gpiochip32  gpiochip64  gpiochip96  unexport", CYAN, "  <-- gpio60 yok, bırakıldı"),
])

# 4) Overlay ile LED alt sistemine bağlama
render("04_overlay.png", BBB, [
    r("dtc -@ -I dts -O dtb -o BB-EXT-LED-00A0.dtbo BB-EXT-LED-00A0.dts"),
    r("cp BB-EXT-LED-00A0.dtbo /lib/firmware/"),
    r("grep -E '^(uboot_overlay_addr4|enable_uboot_cape_universal)' /boot/uEnv.txt"),
    note("uboot_overlay_addr4=/lib/firmware/BB-EXT-LED-00A0.dtbo", CYAN, ""),
    note("#enable_uboot_cape_universal=1", CYAN, "                    <-- P9_12'yi serbest bırakır"),
    r("reboot"),
    t("..."),
    r("ls /sys/class/leds/"),
    note("beaglebone:green:usr0  ...  beaglebone:green:usr3  ext:red:p9_12", GREEN, "  <-- yeni LED"),
    r("cat /sys/class/leds/ext:red:p9_12/trigger | grep -o '\\[.*\\]'"),
    note("[heartbeat]", CYAN, "                                     <-- DT'deki varsayılan tetikleyici"),
])

# 5) Hatalar
render("05_errors.png", BBB + " (temsili hatalar)", [
    note("LED hiç yanmıyor, value=1", RED, "                 <-- LED ters takılı / GND bağlı değil / pinmux"),
    t(""),
    r("echo 60 > /sys/class/gpio/export"),
    note("bash: echo: write error: Device or resource busy", RED, "   <-- pin overlay'de / başka sürücüde"),
    t(""),
    r("./led_blink 60"),
    note("/sys/class/gpio/gpio60/direction: Permission denied", RED, "   <-- root olarak çalıştır"),
    t(""),
    r("config-pin P9_12 gpio"),
    note("ERROR: open() for /sys/devices/platform/ocp/ocp:P9_12_pinmux/state failed", RED, ""),
    note("", FG, "                    <-- cape-universal kapalı / overlay pini aldı"),
])
