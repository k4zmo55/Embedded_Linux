/*
 * mpu6050_tilt.c — MPU6050 ile eğim açısını (roll ve pitch) ölçer.
 *
 * İki yöntem yan yana yazdırılır:
 *  - acc : Sadece ivmeölçerden. Sensör dururken doğru, titreşimde gürültülü.
 *  - filt: Tamamlayıcı filtre (complementary filter). Kısa vadede jiroskobun
 *          açısal hızını toplar, uzun vadede ivmeölçerin açısına yaklaşır.
 *
 * Derleme (code/ klasöründe):
 *   arm-linux-gnueabihf-gcc -Wall -o mpu6050_tilt \
 *       19_mpu6050/mpu6050_tilt.c 19_mpu6050/mpu6050.c -lm
 * Kullanım: ./mpu6050_tilt        (Ctrl-C ile dur)
 */
#include <stdio.h>
#include <math.h>
#include <signal.h>
#include <time.h>
#include <unistd.h>

#include "mpu6050.h"

#define ACC_FS      ACC_FS_2G
#define GYRO_FS     GYRO_FS_250
#define PERIOD_MS   20              /* 50 Hz örnekleme */
#define ALPHA       0.98            /* filtrede jiroskobun ağırlığı */
#define RAD_TO_DEG  (180.0 / M_PI)

static volatile sig_atomic_t running = 1;

static void on_sigint(int sig)
{
	(void)sig;
	running = 0;
}

static double now_s(void)
{
	struct timespec ts;

	clock_gettime(CLOCK_MONOTONIC, &ts);
	return ts.tv_sec + ts.tv_nsec / 1e9;
}

/*
 * Yerçekimi vektöründen eğim açıları (derece):
 *   roll  : X ekseni etrafında dönme
 *   pitch : Y ekseni etrafında dönme
 */
static void acc_angles(const double a[3], double *roll, double *pitch)
{
	*roll  = atan2(a[1], a[2]) * RAD_TO_DEG;
	*pitch = atan2(-a[0], sqrt(a[1] * a[1] + a[2] * a[2])) * RAD_TO_DEG;
}

int main(void)
{
	struct mpu6050_raw raw;
	struct mpu6050_data d;
	double roll_acc, pitch_acc, roll = 0, pitch = 0;
	double t, last_t, dt;
	int fd, n = 0;

	fd = mpu6050_open(MPU6050_I2C_DEV, MPU6050_ADDR);
	if (fd < 0)
		return 1;

	if (mpu6050_init(fd, ACC_FS, GYRO_FS) < 0) {
		printf("Error: MPU6050 init failed\n");
		close(fd);
		return 1;
	}

	signal(SIGINT, on_sigint);

	/* Filtreyi ivmeölçerin açısıyla başlat. */
	if (mpu6050_read_raw(fd, &raw) < 0) {
		close(fd);
		return 1;
	}
	mpu6050_convert(&raw, ACC_FS, GYRO_FS, &d);
	acc_angles(d.acc, &roll, &pitch);
	last_t = now_s();

	printf("   roll(acc) pitch(acc)   roll(filt) pitch(filt)\n");

	while (running) {
		usleep(PERIOD_MS * 1000);

		if (mpu6050_read_raw(fd, &raw) < 0)
			break;
		mpu6050_convert(&raw, ACC_FS, GYRO_FS, &d);

		t = now_s();
		dt = t - last_t;
		last_t = t;

		acc_angles(d.acc, &roll_acc, &pitch_acc);

		/* açı = ALPHA * (açı + jiroskop * dt) + (1 - ALPHA) * ivmeölçer açısı */
		roll  = ALPHA * (roll  + d.gyro[0] * dt) + (1 - ALPHA) * roll_acc;
		pitch = ALPHA * (pitch + d.gyro[1] * dt) + (1 - ALPHA) * pitch_acc;

		/* 50 Hz'de okuyup ekrana saniyede 5 kez yaz */
		if (++n % 10 == 0) {
			printf("   %8.1f  %8.1f     %8.1f   %8.1f\n",
			       roll_acc, pitch_acc, roll, pitch);
			fflush(stdout);
		}
	}

	close(fd);
	return 0;
}
