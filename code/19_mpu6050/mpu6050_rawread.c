/*
 * mpu6050_rawread.c — MPU6050'nin ham ve dönüştürülmüş değerlerini yazdırır.
 *
 * Kursun Project_Src/MPU6050_raw_read/mpu6050_rawread.c programının
 * düzeltilmiş hali (düzeltmeler için bkz. mpu6050.c).
 *
 * Derleme (code/ klasöründe):
 *   arm-linux-gnueabihf-gcc -Wall -o mpu6050_rawread \
 *       19_mpu6050/mpu6050_rawread.c 19_mpu6050/mpu6050.c
 * Kullanım: ./mpu6050_rawread [-p]
 *   -p : sadece ivme değerlerini (g) sekmeyle ayrılmış sütunlar halinde yazar
 *        (kursun "#if 1" çıktısı; grafik çizdirmek için)
 */
#include <stdio.h>
#include <string.h>
#include <signal.h>
#include <unistd.h>

#include "mpu6050.h"

#define ACC_FS      ACC_FS_2G
#define GYRO_FS     GYRO_FS_250
#define PERIOD_MS   250

static volatile sig_atomic_t running = 1;

static void on_sigint(int sig)
{
	(void)sig;
	running = 0;
}

int main(int argc, char *argv[])
{
	struct mpu6050_raw raw;
	struct mpu6050_data d;
	int plot = argc > 1 && strcmp(argv[1], "-p") == 0;
	int fd;

	fd = mpu6050_open(MPU6050_I2C_DEV, MPU6050_ADDR);
	if (fd < 0)
		return 1;

	if (mpu6050_init(fd, ACC_FS, GYRO_FS) < 0) {
		printf("Error: MPU6050 init failed\n");
		close(fd);
		return 1;
	}

	signal(SIGINT, on_sigint);

	while (running) {
		if (mpu6050_read_raw(fd, &raw) < 0)
			break;
		mpu6050_convert(&raw, ACC_FS, GYRO_FS, &d);

		if (plot) {
			printf("%0.2f\t%0.2f\t%0.2f\n", d.acc[0], d.acc[1], d.acc[2]);
		} else {
			printf("Acc(raw)  X:%6d Y:%6d Z:%6d   Gyro(raw)  X:%6d Y:%6d Z:%6d\n",
			       raw.acc[0], raw.acc[1], raw.acc[2],
			       raw.gyro[0], raw.gyro[1], raw.gyro[2]);
			printf("Acc(g)    X:%6.2f Y:%6.2f Z:%6.2f   Gyro(dps)  X:%6.1f Y:%6.1f Z:%6.1f   T:%.1f C\n",
			       d.acc[0], d.acc[1], d.acc[2],
			       d.gyro[0], d.gyro[1], d.gyro[2], d.temp);
		}
		fflush(stdout);
		usleep(PERIOD_MS * 1000);
	}

	close(fd);
	return 0;
}
