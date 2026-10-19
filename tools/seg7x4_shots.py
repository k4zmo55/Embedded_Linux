"""4 haneli 7-segment gösterge bölümü için terminal ekran görüntülerini üretir.

Kullanım: python tools/seg7x4_shots.py [çıktı klasörü]
"""
from term_shots import (render, t, FG, DIM, GREEN, BLUE, YELLOW, CYAN, RED,
                        MAGENTA, ORANGE)
from term_shots import V, set_default_out

CC = V("build.cross_compile")
BOARD_IP = V("network.board_ip")
set_default_out("images/seg7x4")

BBB = "root@beaglebone: ~ (SSH)"


def r(cmd, path="~"):
    return [("root@beaglebone", GREEN), (":", FG), (path, BLUE), ("# ", FG), (cmd, FG)]


def host(cmd, path="~/code"):
    return [("mehmet@ubuntu", GREEN), (":", FG), (path, BLUE), ("$ ", FG), (cmd, FG)]


def note(text, color=FG, ann=""):
    return [(text, color), (ann, MAGENTA)] if ann else [(text, color)]


# 1) Hane pinlerinin GPIO modunu kontrol etme
render("01_pin_check.png", BBB, [
    r("for p in P9_15 P9_23 P9_30 P9_27; do config-pin $p gpio; config-pin -q $p; done"),
    note("P9_15 Mode: gpio Direction: in Value: 0", GREEN),
    note("P9_23 Mode: gpio Direction: in Value: 0", GREEN),
    note("P9_30 Mode: gpio Direction: in Value: 0", GREEN),
    note("P9_27 Mode: gpio Direction: in Value: 0", GREEN),
    r("grep -E '44e10(840|844|998|9a4)' /sys/kernel/debug/pinctrl/44e10800.pinmux*/pins"),
    note("pin 16 (PIN16) 16:gpio-32-63 44e10840 00000027 pinctrl-single", ORANGE, "   <-- P9_15"),
    note("pin 17 (PIN17) 17:gpio-32-63 44e10844 00000027 pinctrl-single", ORANGE, "   <-- P9_23"),
    note("pin 102 (PIN102) 16:gpio-96-127 44e10998 00000027 pinctrl-single", ORANGE, " <-- P9_30"),
    note("pin 105 (PIN105) 19:gpio-96-127 44e109a4 00000027 pinctrl-single", ORANGE, " <-- P9_27"),
])

# 2) Komut satırından: segmentler ortak, hane pini seçer (ortak anot)
render("02_cmdline_test.png", BBB + " (ortak anot gösterge)", [
    r("for g in 66 67 69 68 45 44 26 46 48 49 112 115; do \\"),
    note("    echo $g > /sys/class/gpio/export; echo out > /sys/class/gpio/gpio$g/direction; done", FG),
    r("for g in 66 67 69 68 45 44 26 46; do echo 1 > /sys/class/gpio/gpio$g/value; done"),
    note("", FG, "                                   <-- ortak anot: segment 1 = sönük"),
    r("for g in 66 67 69; do echo 0 > /sys/class/gpio/gpio$g/value; done"),
    note("", FG, "                                   <-- a, b, c seçili: \"7\""),
    r("echo 1 > /sys/class/gpio/gpio48/value"),
    note("", FG, "                                   <-- sadece 1. hanede 7"),
    r("echo 1 > /sys/class/gpio/gpio115/value"),
    note("", FG, "                                   <-- 4. hanede de aynı 7: segmentler ortak"),
    r("echo 0 > /sys/class/gpio/gpio48/value; echo 0 > /sys/class/gpio/gpio115/value"),
])

# 3) Derleme ve sayaç
render("03_build_run.png", "mehmet@ubuntu + BBB", [
    host(f"{CC}gcc -Wall -Ilib -I17_7segment -DCOMMON_ANODE \\"),
    note("      -o counter_4digit 18_4digit_7segment/counter_4digit.c \\", FG),
    note("      18_4digit_7segment/seg7x4.c 17_7segment/seg7.c lib/gpio_driver.c", FG),
    host(f"scp counter_4digit root@{BOARD_IP}:~/"),
    t("--- BBB ---", MAGENTA),
    r("./counter_4digit up 100"),
    note("4 digit 7seg LED up/down/random counter and clock application", FG),
    note("up counting every 100 ms, press Ctrl-C to stop", GREEN, "     <-- 0000 0001 0002 ..."),
    note("^C", DIM),
    note("Display off, GPIOs released", GREEN),
    r("./counter_4digit down 50"),
    note("4 digit 7seg LED up/down/random counter and clock application", FG),
    note("down counting every 50 ms, press Ctrl-C to stop", GREEN, "    <-- 9999 9998 ... 0000 9999"),
])

# 4) Dijital saat
render("04_clock.png", BBB, [
    r("timedatectl | grep -E 'Local time|synchronized|Time zone'"),
    note("               Local time: Mon 2026-10-19 14:37:52 +03", CYAN),
    note("                Time zone: Europe/Istanbul (+03, +0300)", CYAN),
    note("System clock synchronized: yes", CYAN, "                   <-- NTP ile ayarlı"),
    r("./counter_4digit clock"),
    note("4 digit 7seg LED up/down/random counter and clock application", FG),
    note("clock mode (HH.MM), press Ctrl-C to stop", GREEN, "           <-- göstergede 14.37"),
])

# 5) Hatalar
render("05_errors.png", BBB + " (temsili hatalar)", [
    note("Bütün hanelerde aynı rakam görünüyor", RED, "         <-- haneler aynı anda açık / tarama yok"),
    note("Rakamlar titriyor, parlaklık dalgalanıyor", RED, "     <-- CPU meşgul, tarama gecikiyor"),
    r("chrt -f 50 ./counter_4digit up 100"),
    note("", FG, "                                   <-- gerçek zamanlı öncelikle çalıştır"),
    t(""),
    r("./counter_4digit up 100"),
    note("/sys/class/gpio/export: Device or resource busy", RED, "     <-- P9_23 hâlâ butonda / overlay'de"),
    note("GPIO 49 could not be configured as output", RED),
    note("Error: GPIO init failed !", RED),
])
