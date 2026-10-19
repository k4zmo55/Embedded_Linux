"""7-segment gösterge bölümü için terminal ekran görüntülerini üretir.

Kullanım: python tools/seg7_shots.py [çıktı klasörü]
"""
from term_shots import (render, t, FG, DIM, GREEN, BLUE, YELLOW, CYAN, RED,
                        MAGENTA, ORANGE)
from term_shots import V, set_default_out

CC = V("build.cross_compile")
BOARD_IP = V("network.board_ip")
set_default_out("images/seg7")

BBB = "root@beaglebone: ~ (SSH)"


def r(cmd, path="~"):
    return [("root@beaglebone", GREEN), (":", FG), (path, BLUE), ("# ", FG), (cmd, FG)]


def host(cmd, path="~/code"):
    return [("mehmet@ubuntu", GREEN), (":", FG), (path, BLUE), ("$ ", FG), (cmd, FG)]


def note(text, color=FG, ann=""):
    return [(text, color), (ann, MAGENTA)] if ann else [(text, color)]


# 1) Pinlerin GPIO modunda olduğunu kontrol etme
PINS = [("P8_07", "44e10890", "66"), ("P8_08", "44e10894", "67"),
        ("P8_09", "44e1089c", "69"), ("P8_10", "44e10898", "68"),
        ("P8_11", "44e10834", "45"), ("P8_12", "44e10830", "44"),
        ("P8_14", "44e10828", "26"), ("P8_16", "44e10838", "46")]
lines = [r("for p in P8_07 P8_08 P8_09 P8_10 P8_11 P8_12 P8_14 P8_16; do config-pin $p gpio; done"),
         r("for p in P8_07 P8_08 P8_09 P8_10 P8_11 P8_12 P8_14 P8_16; do config-pin -q $p; done")]
for p, _, _ in PINS:
    lines.append(note(f"{p} Mode: gpio Direction: in Value: 0", GREEN))
lines.append(r("grep -E '44e10(890|834)' /sys/kernel/debug/pinctrl/44e10800.pinmux*/pins"))
lines.append(note("pin 13 (PIN13) 13:gpio-32-63 44e10834 00000027 pinctrl-single", ORANGE, "  <-- P8_11, mod 7"))
lines.append(note("pin 36 (PIN36) 2:gpio-64-95 44e10890 00000027 pinctrl-single", ORANGE, "   <-- P8_7, mod 7"))
render("01_pin_check.png", BBB, lines)

# 2) Segmentleri komut satırından tek tek yakmak
render("02_cmdline_test.png", BBB, [
    r("for g in 66 67 69 68 45 44 26 46; do echo $g > /sys/class/gpio/export; \\"),
    note("    echo out > /sys/class/gpio/gpio$g/direction; done", FG),
    r("echo 1 > /sys/class/gpio/gpio66/value"),
    note("", FG, "                                     <-- a segmenti yandı"),
    r("for g in 67 69; do echo 1 > /sys/class/gpio/gpio$g/value; done"),
    note("", FG, "                                     <-- a, b, c: \"7\""),
    r("for g in 66 67 69 68 45 44 26 46; do echo 0 > /sys/class/gpio/gpio$g/value; done"),
    note("", FG, "                                     <-- hepsi söndü"),
])

# 3) Derleme ve sayaç
render("03_build_run.png", "mehmet@ubuntu + BBB", [
    host(f"{CC}gcc -Wall -Ilib -o counter_7seg 17_7segment/counter_7seg.c \\"),
    note("      17_7segment/seg7.c lib/gpio_driver.c", FG),
    host(f"scp counter_7seg root@{BOARD_IP}:~/"),
    t("--- BBB ---", MAGENTA),
    r("./counter_7seg"),
    note("Application for up/down/random counter on 7 seg display", FG),
    note("usage: ./counter_7seg <direction> <delay ms>", YELLOW),
    note("valid direction : up, down, updown, random", YELLOW),
    note("recommended delay range in ms : 0 to 1000", YELLOW),
    r("./counter_7seg updown 300"),
    note("Application for up/down/random counter on 7 seg display", FG),
    note("updown counting every 300 ms, press Ctrl-C to stop", GREEN, "   <-- 0 1 ... 9 8 ... 1 0 1 ..."),
    note("^C", DIM),
    note("Display off, GPIOs released", GREEN, "                      <-- temiz kapanış"),
])

# 4) Butonla sayma
render("04_button_counter.png", "mehmet@ubuntu + BBB", [
    host(f"{CC}gcc -Wall -Ilib -o button_counter_7seg 17_7segment/button_counter_7seg.c \\"),
    note("      17_7segment/seg7.c lib/gpio_driver.c", FG),
    host(f"scp button_counter_7seg root@{BOARD_IP}:~/"),
    t("--- BBB ---", MAGENTA),
    r("config-pin P9_23 gpio_pd"),
    r("./button_counter_7seg"),
    note("This program counts button presses (0-9) on 7segment display", FG),
    note("Waiting for the button press, press Ctrl-C to stop", GREEN, "  <-- göstergede 0"),
    note("button pressed, count = 1", CYAN),
    note("button pressed, count = 2", CYAN),
    note("...", DIM),
    note("button pressed, count = 9", CYAN),
    note("button pressed, count = 0", CYAN, "                       <-- 9'dan sonra başa döner"),
    note("^C", DIM),
    note("Display off, GPIOs released", GREEN),
])

# 5) Hatalar
render("05_errors.png", BBB + " (temsili hatalar)", [
    note("Rakamlar ters: \"8\" sönük, boşlukta segmentler yanık", RED, "  <-- ortak anot gösterge"),
    note("", FG, "                    -DCOMMON_ANODE ile derle, COM'u 3.3 V'a bağla"),
    t(""),
    [("debian@beaglebone", GREEN), (":", FG), ("~", BLUE), ("$ ", FG), ("./counter_7seg up 500", FG)],
    note("/sys/class/gpio/gpio66/direction: Permission denied", RED, "   <-- root olarak çalıştır"),
    note("GPIO 66 could not be configured as output", RED),
    note("Error: GPIO init failed !", RED),
    t(""),
    r("./button_counter_7seg"),
    note("button pressed, count = 1", CYAN),
    note("button pressed, count = 2", CYAN, "      <-- hiç basılmadı: pin boşta (pull-down yok)"),
    note("button pressed, count = 3", CYAN),
])
