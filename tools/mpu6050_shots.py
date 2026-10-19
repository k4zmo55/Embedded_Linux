"""MPU6050 bölümü için terminal ekran görüntülerini üretir.

Kullanım: python tools/mpu6050_shots.py [çıktı klasörü]
"""
from term_shots import (render, t, FG, DIM, GREEN, BLUE, YELLOW, CYAN, RED,
                        MAGENTA, ORANGE)
from term_shots import V, set_default_out

CC = V("build.cross_compile")
BOARD_IP = V("network.board_ip")
set_default_out("images/mpu6050")

BBB = "root@beaglebone: ~ (SSH)"


def r(cmd, path="~"):
    return [("root@beaglebone", GREEN), (":", FG), (path, BLUE), ("# ", FG), (cmd, FG)]


def host(cmd, path="~/code"):
    return [("mehmet@ubuntu", GREEN), (":", FG), (path, BLUE), ("$ ", FG), (cmd, FG)]


def note(text, color=FG, ann=""):
    return [(text, color), (ann, MAGENTA)] if ann else [(text, color)]


# 1) I2C veriyolları ve pinmux
render("01_i2c_bus.png", BBB, [
    r("i2cdetect -l"),
    note("i2c-0   i2c        OMAP I2C adapter                  I2C adapter", CYAN, "  <-- dahili: PMIC, EEPROM"),
    note("i2c-2   i2c        OMAP I2C adapter                  I2C adapter", CYAN, "  <-- P9_19 / P9_20"),
    r("ls -l /sys/bus/i2c/devices/i2c-2"),
    note("lrwxrwxrwx 1 root root 0 ... /sys/bus/i2c/devices/i2c-2 -> ../../../devices/platform/ocp/", FG),
    note("    48000000.interconnect/48000000.interconnect:segment@100000/4819c000.target-module/4819c000.i2c/i2c-2", FG),
    r("grep -E '44e1097[8c]' /sys/kernel/debug/pinctrl/44e10800.pinmux*/pins"),
    note("pin 94 (PIN94) 44e10978 00000033 pinctrl-single", ORANGE, "  <-- P9_20: mod 3 = I2C2_SDA, pull-up"),
    note("pin 95 (PIN95) 44e1097c 00000033 pinctrl-single", ORANGE, "  <-- P9_19: mod 3 = I2C2_SCL, pull-up"),
])

# 2) i2cdetect ve i2c-tools ile ilk temas
render("02_i2c_tools.png", BBB, [
    r("i2cdetect -y -r 2"),
    note("     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f", FG),
    note("00:                         -- -- -- -- -- -- -- --", FG),
    note("10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --", FG),
    note("20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --", FG),
    note("30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --", FG),
    note("40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --", FG),
    note("50: -- -- -- -- UU UU UU UU -- -- -- -- -- -- -- --", FG, "  <-- cape EEPROM'ları (sürücüde)"),
    note("60: -- -- -- -- -- -- -- -- 68 -- -- -- -- -- -- --", FG, "  <-- MPU6050"),
    note("70: -- -- -- -- -- -- -- --", FG),
    r("i2cget -y 2 0x68 0x75"),
    note("0x68", CYAN, "                                 <-- WHO_AM_I"),
    r("i2cget -y 2 0x68 0x6b"),
    note("0x40", CYAN, "                                 <-- PWR_MGMT_1: SLEEP = 1"),
    r("i2cset -y 2 0x68 0x6b 0x01"),
    r("i2cdump -y -r 0x3b-0x48 2 0x68 b"),
    note("     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f", FG),
    note("30:                                  ff 9c 00 a4 3f", FG, "  <-- ivme X, Y, Z(yüksek)"),
    note("40: e8 ef 7e ff 4f 00 2c ff f4", FG, "                     <-- Z(düşük), sıcaklık, jiroskop"),
])

# 3) Derleme ve ham okuma
render("03_rawread.png", "mehmet@ubuntu + BBB", [
    host(f"{CC}gcc -Wall -o mpu6050_rawread 19_mpu6050/mpu6050_rawread.c 19_mpu6050/mpu6050.c"),
    host(f"scp mpu6050_rawread root@{BOARD_IP}:~/"),
    t("--- BBB --- sensör masada, düz duruyor", MAGENTA),
    r("./mpu6050_rawread"),
    note("Acc(raw)  X:  -100 Y:   164 Z: 16360   Gyro(raw)  X:  -177 Y:    44 Z:   -12", FG),
    note("Acc(g)    X: -0.01 Y:  0.01 Z:  1.00   Gyro(dps)  X:  -1.4 Y:   0.3 Z:  -0.1   T:24.1 C", GREEN),
    note("Acc(raw)  X:   -92 Y:   170 Z: 16348   Gyro(raw)  X:  -180 Y:    40 Z:   -10", FG),
    note("Acc(g)    X: -0.01 Y:  0.01 Z:  1.00   Gyro(dps)  X:  -1.4 Y:   0.3 Z:  -0.1   T:24.1 C", GREEN),
    note("", FG, "             Z = 1 g: yerçekimi    jiroskop ~0: dönmüyor (küçük ofset var)"),
    note("^C", DIM),
    r("./mpu6050_rawread -p | head -3"),
    note("-0.01\t0.01\t1.00".replace("\t", "    "), CYAN),
    note("-0.01\t0.01\t1.00".replace("\t", "    "), CYAN),
    note("-0.01\t0.01\t0.99".replace("\t", "    "), CYAN),
])

# 4) Eğim açısı
render("04_tilt.png", "mehmet@ubuntu + BBB", [
    host(f"{CC}gcc -Wall -o mpu6050_tilt 19_mpu6050/mpu6050_tilt.c 19_mpu6050/mpu6050.c -lm"),
    host(f"scp mpu6050_tilt root@{BOARD_IP}:~/"),
    t("--- BBB ---", MAGENTA),
    r("./mpu6050_tilt"),
    note("   roll(acc) pitch(acc)   roll(filt) pitch(filt)", FG),
    note("        0.6      -0.3          0.6       -0.3", GREEN, "     <-- düz"),
    note("       14.8      -0.1         12.9       -0.2", GREEN, "     <-- X ekseni etrafında eğiliyor"),
    note("       31.2       0.4         30.6        0.3", GREEN),
    note("       44.7       0.2         44.9        0.2", GREEN, "     <-- ~45°"),
    note("       38.1       1.7         45.1        0.3", YELLOW, "     <-- sallandı: acc sıçrar, filtre sakin"),
    note("       45.3       0.1         45.0        0.2", GREEN),
    note("^C", DIM),
])

# 5) Hatalar
render("05_errors.png", BBB + " (temsili hatalar)", [
    r("./mpu6050_rawread"),
    note("i2c read: Remote I/O error", RED, "                  <-- sensör yanıt vermiyor (NACK): kablo, adres"),
    note("Error: MPU6050 init failed", RED),
    t(""),
    r("i2cdetect -y -r 2"),
    note("60: -- -- -- -- -- -- -- -- -- 69 -- -- -- -- -- --", FG, "  <-- AD0 = 1: adres 0x69"),
    t(""),
    r("./mpu6050_rawread"),
    note("/dev/i2c-2: No such file or directory", RED, "       <-- i2c-dev modülü yok / yanlış veriyolu"),
    r("modprobe i2c-dev; i2cdetect -l"),
    t(""),
    note("Acc(g)    X:  0.00 Y:  0.00 Z:  0.00   Gyro(dps)  X:   0.0 Y:   0.0 Z:   0.0", RED, ""),
    note("", FG, "                                      <-- sensör uykuda (PWR_MGMT_1 yazılmadı)"),
])
