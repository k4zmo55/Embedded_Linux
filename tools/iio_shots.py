"""I2C/IIO sürücüsü bölümü için terminal ekran görüntülerini üretir.

Kullanım: python tools/iio_shots.py [çıktı klasörü]
"""
from term_shots import (render, t, FG, DIM, GREEN, BLUE, YELLOW, CYAN, RED,
                        MAGENTA, ORANGE)
from term_shots import V, set_default_out

CC = V("build.cross_compile")
KVER = V("kernel.version")
NFS_DIR = V("network.nfs_dir")
TFTP_DIR = V("network.tftp_dir")
KDIR = "~/bbb/" + V("kernel.dir")
set_default_out("images/iio")

MOD = "~/code/24_i2c_iio_driver"
ABS = "/home/mehmet/code/24_i2c_iio_driver"
MINICOM = "mehmet@ubuntu: ~ — minicom (BBB, BusyBox rootfs)"
IIO = "/sys/bus/iio/devices/iio:device1"


def host(cmd, path=MOD):
    return [("mehmet@ubuntu", GREEN), (":", FG), (path, BLUE), ("$ ", FG), (cmd, FG)]


def sh(cmd, path="~"):
    return [(f"{path} # ", GREEN), (cmd, FG)]


def note(text, color=FG, ann=""):
    return [(text, color), (ann, MAGENTA)] if ann else [(text, color)]


# 1) Derleme, kurma, yükleme
render("01_build_load.png", "mehmet@ubuntu + BBB", [
    host("make"),
    note(f"  CC [M]  {ABS}/bbb_mpu6050.o", FG),
    note(f"  LD [M]  {ABS}/bbb_mpu6050.ko", GREEN),
    host("make install INSTALL_MOD_PATH=~/bbb/rootfs"),
    note(f"  INSTALL {ABS}/bbb_mpu6050.ko", FG),
    note(f"  DEPMOD  {KVER}", GREEN),
    host(f"sudo cp -a ~/bbb/rootfs/lib/modules/{KVER} {NFS_DIR}/lib/modules/"),
    host("modinfo -F depends bbb_mpu6050.ko"),
    note("industrialio", CYAN, "                      <-- IIO çekirdeği (modülse önce o yüklenir)"),
    t("--- BBB ---", MAGENTA),
    sh("modprobe bbb_mpu6050"),
    sh("ls /sys/bus/i2c/drivers/bbb_mpu6050/"),
    note("bind  module  uevent  unbind", CYAN, "     <-- sürücü kayıtlı, aygıt yok"),
])

# 2) new_device ile tanıtma
render("02_new_device.png", MINICOM, [
    sh("echo bbb_mpu6050 0x68 > /sys/bus/i2c/devices/i2c-2/new_device"),
    sh("dmesg | tail -2"),
    note("[  412.330918] i2c i2c-2: new_device: Instantiated device bbb_mpu6050 at 0x68", FG),
    note("[  412.441207] bbb_mpu6050 2-0068: MPU6050 ready as iio:device1", GREEN),
    sh("ls /sys/bus/i2c/devices/"),
    note("0-0024  0-0050  0-0070  2-0054  2-0055  2-0056  2-0057  2-0068  i2c-0  i2c-2", CYAN),
    sh("i2cdetect -y -r 2 | grep 60:"),
    note("60: -- -- -- -- -- -- -- -- UU -- -- -- -- -- -- --", CYAN, "  <-- UU: sürücüde"),
    sh("cat /sys/bus/iio/devices/iio:device*/name"),
    note("TI-am335x-adc.0.auto", FG, "              <-- iio:device0: AM335x ADC"),
    note("bbb_mpu6050", GREEN, "                        <-- iio:device1"),
])

# 3) IIO dosyaları
render("03_iio_files.png", MINICOM, [
    sh(f"cd {IIO} && ls"),
    note("dev               in_accel_z_raw    in_anglvel_z_raw  in_temp_scale  subsystem", CYAN),
    note("in_accel_scale    in_anglvel_scale  in_temp_offset    name           uevent", CYAN),
    note("in_accel_x_raw    in_anglvel_x_raw  in_temp_raw       of_node", CYAN),
    note("in_accel_y_raw    in_anglvel_y_raw  power", CYAN),
    sh("cat in_accel_x_raw in_accel_y_raw in_accel_z_raw in_accel_scale", "iio:device1"),
    note("-100", FG),
    note("164", FG),
    note("16360", FG, "                                <-- Z: yerçekimi"),
    note("0.000598550", CYAN, "                          <-- m/s^2 / LSB"),
    sh("awk 'BEGIN { print 16360 * 0.000598550 }'", "iio:device1"),
    note("9.79228", GREEN, "                              <-- m/s^2 ~ 1 g"),
    sh("cat in_temp_raw in_temp_offset in_temp_scale", "iio:device1"),
    note("-4226", FG),
    note("12420.200000", FG),
    note("2.941176", FG),
    sh("awk 'BEGIN { print (-4226 + 12420.2) * 2.941176 / 1000 }'", "iio:device1"),
    note("24.1006", GREEN, "                              <-- °C"),
])

# 4) Eğim betiği
render("04_tilt.png", MINICOM, [
    sh("./tilt.sh"),
    note(f"using {IIO}", FG),
    note("roll    0.6   pitch    0.3", GREEN, "        <-- düz"),
    note("roll   30.4   pitch    0.1", GREEN, "        <-- X ekseni etrafında eğildi"),
    note("roll   44.8   pitch   -0.2", GREEN),
    note("^C", DIM),
    sh("echo 0x68 > /sys/bus/i2c/devices/i2c-2/delete_device"),
    sh("dmesg | tail -1"),
    note("[  530.008764] i2c i2c-2: delete_device: Deleting device bbb_mpu6050 at 0x68", FG),
])

# 5) Hatalar
render("05_errors.png", MINICOM + " (temsili hatalar)", [
    sh("insmod bbb_mpu6050.ko"),
    note("insmod: can't insert 'bbb_mpu6050.ko': unknown symbol in module, or unknown parameter", RED),
    note("bbb_mpu6050: Unknown symbol devm_iio_device_register (err -2)", RED, "  <-- IIO modülü yüklü değil"),
    t(""),
    sh("echo bbb_mpu6050 0x68 > /sys/bus/i2c/devices/i2c-2/new_device; dmesg | tail -1"),
    note("bbb_mpu6050 2-0068: error -EREMOTEIO: no answer at 0x68", RED, "  <-- sensör bağlı değil / adres yanlış"),
    t(""),
    sh("./mpu6050_rawread"),
    note("I2C_SLAVE: Device or resource busy", RED, "        <-- adres sürücüde (Bölüm 19'un programı)"),
])
