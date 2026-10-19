#!/bin/sh
# tilt.sh — bbb_mpu6050 sürücüsünün IIO dosyalarından eğim açısını hesaplar.
#
# Bölüm 19.10'daki roll/pitch formülünün kabuk betiği hali. Kartta BusyBox'ın
# awk'ı yeterli; C programına gerek yok.
#
# Kullanım: ./tilt.sh          (Ctrl-C ile dur)

# IIO aygıtını adından bul (iio:device0 ADC olabilir).
DEV=
for d in /sys/bus/iio/devices/iio:device*; do
	[ "$(cat "$d/name" 2>/dev/null)" = "bbb_mpu6050" ] && DEV=$d && break
done
if [ -z "$DEV" ]; then
	echo "bbb_mpu6050 IIO device not found" >&2
	exit 1
fi
echo "using $DEV"

while true; do
	x=$(cat "$DEV/in_accel_x_raw")
	y=$(cat "$DEV/in_accel_y_raw")
	z=$(cat "$DEV/in_accel_z_raw")
	# Açı birimden bağımsızdır: scale ile çarpmadan ham değerlerle hesaplanır.
	awk -v x="$x" -v y="$y" -v z="$z" 'BEGIN {
		r2d = 180 / 3.14159265
		printf "roll %6.1f   pitch %6.1f\n", atan2(y, z) * r2d, atan2(-x, sqrt(y*y + z*z)) * r2d
	}'
	sleep 1
done
