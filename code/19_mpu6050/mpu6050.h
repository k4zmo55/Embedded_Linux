/*
 * mpu6050.h — MPU6050 ivmeölçer/jiroskobunu Linux I2C (/dev/i2c-N) üzerinden okur.
 *
 * Bağlantı (kursla aynı):
 *   P9_19  I2C2_SCL  ->  SCL
 *   P9_20  I2C2_SDA  ->  SDA
 *   P9_3   3.3 V     ->  VCC
 *   P9_1   GND       ->  GND
 * Kernel'de bu veriyolu /dev/i2c-2'dir (BeagleBoard 4.x ve sonrası kernel'ler).
 *
 * Kaynak: MPU-6000/MPU-6050 Product Specification Rev 3.4,
 *         Register Map and Descriptions Rev 4.2
 */
#ifndef MPU6050_H_
#define MPU6050_H_

#include <stdint.h>

#define MPU6050_I2C_DEV         "/dev/i2c-2"
#define MPU6050_ADDR            0x68    /* AD0 = 0; AD0 = 1 ise 0x69 */

/* Register'lar */
#define MPU6050_REG_GYRO_CONFIG     0x1B
#define MPU6050_REG_ACCEL_CONFIG    0x1C
#define MPU6050_REG_ACCEL_XOUT_H    0x3B    /* 0x3B-0x48: ivme, sıcaklık, jiroskop */
#define MPU6050_REG_PWR_MGMT_1      0x6B
#define MPU6050_REG_WHO_AM_I        0x75    /* her zaman 0x68 okunur */

/* Ölçek aralığı (full scale). Değer, CONFIG register'ının 4:3 bitlerine yazılır. */
enum mpu6050_acc_fs  { ACC_FS_2G, ACC_FS_4G, ACC_FS_8G, ACC_FS_16G };
enum mpu6050_gyro_fs { GYRO_FS_250, GYRO_FS_500, GYRO_FS_1000, GYRO_FS_2000 };

struct mpu6050_raw {
	int16_t acc[3];         /* x, y, z */
	int16_t temp;
	int16_t gyro[3];        /* x, y, z */
};

struct mpu6050_data {
	double acc[3];          /* g */
	double temp;            /* °C */
	double gyro[3];         /* °/s */
};

int mpu6050_open(const char *dev, uint8_t addr);
int mpu6050_init(int fd, enum mpu6050_acc_fs afs, enum mpu6050_gyro_fs gfs);
int mpu6050_read_raw(int fd, struct mpu6050_raw *raw);
void mpu6050_convert(const struct mpu6050_raw *raw, enum mpu6050_acc_fs afs,
		     enum mpu6050_gyro_fs gfs, struct mpu6050_data *out);

#endif /* MPU6050_H_ */
