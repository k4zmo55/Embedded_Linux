/*
 * mpu6050.c — MPU6050 ivmeölçer/jiroskobunu Linux I2C (/dev/i2c-N) üzerinden okur.
 *
 * Kursun mpu6050_rawread.c dosyasındaki fonksiyonların düzeltilmiş hali:
 *  - Baytlar uint8_t olarak tutulur. Kursta "char" kullanılıyor; ARM'da char
 *    işaretsiz olduğu için tesadüfen çalışıyor, x86'da düşük bayt işaretle
 *    genişleyip değeri bozar.
 *  - İvme, sıcaklık ve jiroskop tek bir okumayla (14 bayt) alınır; üçü aynı
 *    ölçüm anına aittir.
 *  - Register adresi yazma ve okuma tek bir I2C işleminde yapılır (I2C_RDWR,
 *    araya STOP girmeden "repeated start").
 *  - Okuma/yazma hataları ve eksik okumalar çağırana bildirilir.
 *  - Saat kaynağı olarak jiroskobun PLL'i seçilir (datasheet önerisi).
 */
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <linux/i2c.h>
#include <linux/i2c-dev.h>

#include "mpu6050.h"

/* LSB/g ve LSB/(°/s); Product Specification tablo 6.1 ve 6.2 */
static const double acc_lsb_per_g[4]    = { 16384.0, 8192.0, 4096.0, 2048.0 };
static const double gyro_lsb_per_dps[4] = { 131.0, 65.5, 32.8, 16.4 };

static uint8_t dev_addr = MPU6050_ADDR;     /* mpu6050_open() ile seçilen adres */

/* I2C aygıt dosyasını açar ve sensörün adresini seçer. Dosya tanımlayıcısı döner. */
int mpu6050_open(const char *dev, uint8_t addr)
{
	int fd;

	fd = open(dev, O_RDWR);
	if (fd < 0) {
		perror(dev);
		return -1;
	}

	if (ioctl(fd, I2C_SLAVE, addr) < 0) {
		perror("I2C_SLAVE");
		close(fd);
		return -1;
	}
	dev_addr = addr;
	return fd;
}

/* reg register'ına bir bayt yazar: [reg, data] */
static int write_reg(int fd, uint8_t reg, uint8_t data)
{
	uint8_t buf[2] = { reg, data };

	if (write(fd, buf, 2) != 2) {
		perror("i2c write");
		return -1;
	}
	return 0;
}

/*
 * reg'den başlayarak len bayt okur. İki mesaj tek işlemde gider:
 *   START, adres+W, reg, (repeated) START, adres+R, len bayt, STOP
 */
static int read_regs(int fd, uint8_t reg, uint8_t *buf, uint16_t len)
{
	struct i2c_msg msgs[2] = {
		{ .addr = dev_addr, .flags = 0,        .len = 1,   .buf = &reg },
		{ .addr = dev_addr, .flags = I2C_M_RD, .len = len, .buf = buf  },
	};
	struct i2c_rdwr_ioctl_data xfer = { .msgs = msgs, .nmsgs = 2 };

	if (ioctl(fd, I2C_RDWR, &xfer) != 2) {
		perror("i2c read");
		return -1;
	}
	return 0;
}

/* Sensörü uyandırır ve ölçek aralıklarını ayarlar. Başarılıysa 0, değilse -1. */
int mpu6050_init(int fd, enum mpu6050_acc_fs afs, enum mpu6050_gyro_fs gfs)
{
	uint8_t id;

	if (read_regs(fd, MPU6050_REG_WHO_AM_I, &id, 1) < 0)
		return -1;
	if (id != 0x68) {
		printf("WHO_AM_I = 0x%02x, expected 0x68: is this an MPU6050?\n", id);
		return -1;
	}

	/* Açılışta uykudadır. SLEEP = 0, saat kaynağı = jiroskop X PLL (CLKSEL = 1). */
	if (write_reg(fd, MPU6050_REG_PWR_MGMT_1, 0x01) < 0)
		return -1;
	usleep(100 * 1000);         /* PLL'in oturmasını bekle */

	if (write_reg(fd, MPU6050_REG_ACCEL_CONFIG, afs << 3) < 0 ||
	    write_reg(fd, MPU6050_REG_GYRO_CONFIG, gfs << 3) < 0)
		return -1;
	return 0;
}

/* Yüksek bayt önce (big endian) gelen 16 bitlik işaretli değer */
static int16_t be16(const uint8_t *p)
{
	return (int16_t)((p[0] << 8) | p[1]);
}

/* 0x3B-0x48 arasındaki 14 baytı tek seferde okur. */
int mpu6050_read_raw(int fd, struct mpu6050_raw *raw)
{
	uint8_t b[14];
	int i;

	if (read_regs(fd, MPU6050_REG_ACCEL_XOUT_H, b, sizeof(b)) < 0)
		return -1;

	for (i = 0; i < 3; i++) {
		raw->acc[i]  = be16(&b[i * 2]);         /* 0x3B-0x40 */
		raw->gyro[i] = be16(&b[8 + i * 2]);     /* 0x43-0x48 */
	}
	raw->temp = be16(&b[6]);                    /* 0x41-0x42 */
	return 0;
}

/* Ham değerleri g, °C ve °/s'ye çevirir. */
void mpu6050_convert(const struct mpu6050_raw *raw, enum mpu6050_acc_fs afs,
		     enum mpu6050_gyro_fs gfs, struct mpu6050_data *out)
{
	int i;

	for (i = 0; i < 3; i++) {
		out->acc[i]  = raw->acc[i] / acc_lsb_per_g[afs];
		out->gyro[i] = raw->gyro[i] / gyro_lsb_per_dps[gfs];
	}
	out->temp = raw->temp / 340.0 + 36.53;     /* Register Map, bölüm 4.18 */
}
