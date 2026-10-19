// SPDX-License-Identifier: GPL-2.0
/*
 * bbb_mpu6050.c — MPU6050 için I2C istemci sürücüsü (IIO alt sistemi).
 *
 * Bölüm 19'da sensörü kullanıcı alanından /dev/i2c-2 ile okuduk. Bu sürücü
 * aynı işi kernel'de yapar ve değerleri IIO'nun standart dosyalarıyla açar:
 *
 *   /sys/bus/iio/devices/iio:deviceN/
 *       name                     bbb_mpu6050
 *       in_accel_{x,y,z}_raw     ham ivme
 *       in_accel_scale           ham değer x scale = m/s^2
 *       in_anglvel_{x,y,z}_raw   ham açısal hız
 *       in_anglvel_scale         ham değer x scale = rad/s
 *       in_temp_raw, in_temp_offset, in_temp_scale
 *                                (raw + offset) x scale = milli °C
 *
 * Aygıtı tanıtmak:
 *   echo bbb_mpu6050 0x68 > /sys/bus/i2c/devices/i2c-2/new_device   (hızlı)
 *   ya da device tree: &i2c2 { imu@68 { compatible = "bbb,mpu6050"; reg = <0x68>; }; };
 *
 * Kernel'de MPU6050 için tam özellikli bir sürücü zaten var (inv_mpu6050);
 * bu sürücü öğrenmek için yazıldı ve ondan farklı bir compatible kullanır.
 */
#include <linux/module.h>
#include <linux/i2c.h>
#include <linux/delay.h>
#include <linux/mutex.h>
#include <linux/version.h>
#include <linux/mod_devicetable.h>
#include <linux/iio/iio.h>

/* Register'lar (MPU-6000/MPU-6050 Register Map Rev 4.2) */
#define MPU6050_REG_GYRO_CONFIG     0x1B
#define MPU6050_REG_ACCEL_CONFIG    0x1C
#define MPU6050_REG_ACCEL_XOUT_H    0x3B
#define MPU6050_REG_TEMP_OUT_H      0x41
#define MPU6050_REG_GYRO_XOUT_H     0x43
#define MPU6050_REG_PWR_MGMT_1      0x6B
#define MPU6050_REG_WHO_AM_I        0x75

#define MPU6050_WHO_AM_I_VALUE      0x68
#define MPU6050_PWR_CLK_PLL_X       0x01    /* SLEEP = 0, saat: jiroskop X PLL */
#define MPU6050_PWR_SLEEP           0x40

struct bbb_mpu {
	struct i2c_client *client;
	struct mutex lock;          /* aynı anda tek I2C işlemi */
};

/* İvme ve jiroskop kanalları: her eksen ayrı "raw", birim çarpanı (scale) ortak. */
#define MPU6050_CHAN(_type, _axis, _reg) {				\
	.type = _type,							\
	.modified = 1,							\
	.channel2 = IIO_MOD_##_axis,					\
	.address = _reg,						\
	.info_mask_separate = BIT(IIO_CHAN_INFO_RAW),			\
	.info_mask_shared_by_type = BIT(IIO_CHAN_INFO_SCALE),		\
}

static const struct iio_chan_spec bbb_mpu_channels[] = {
	MPU6050_CHAN(IIO_ACCEL, X, MPU6050_REG_ACCEL_XOUT_H),
	MPU6050_CHAN(IIO_ACCEL, Y, MPU6050_REG_ACCEL_XOUT_H + 2),
	MPU6050_CHAN(IIO_ACCEL, Z, MPU6050_REG_ACCEL_XOUT_H + 4),
	MPU6050_CHAN(IIO_ANGL_VEL, X, MPU6050_REG_GYRO_XOUT_H),
	MPU6050_CHAN(IIO_ANGL_VEL, Y, MPU6050_REG_GYRO_XOUT_H + 2),
	MPU6050_CHAN(IIO_ANGL_VEL, Z, MPU6050_REG_GYRO_XOUT_H + 4),
	{
		.type = IIO_TEMP,
		.address = MPU6050_REG_TEMP_OUT_H,
		.info_mask_separate = BIT(IIO_CHAN_INFO_RAW) |
				      BIT(IIO_CHAN_INFO_SCALE) |
				      BIT(IIO_CHAN_INFO_OFFSET),
	},
};

static int bbb_mpu_read_raw(struct iio_dev *indio_dev,
			    struct iio_chan_spec const *chan,
			    int *val, int *val2, long mask)
{
	struct bbb_mpu *m = iio_priv(indio_dev);
	int ret;

	switch (mask) {
	case IIO_CHAN_INFO_RAW:
		/* Yüksek bayt önce gelen 16 bit: read_word_swapped baytları çevirir. */
		mutex_lock(&m->lock);
		ret = i2c_smbus_read_word_swapped(m->client, chan->address);
		mutex_unlock(&m->lock);
		if (ret < 0)
			return ret;
		*val = (s16)ret;
		return IIO_VAL_INT;

	case IIO_CHAN_INFO_SCALE:
		switch (chan->type) {
		case IIO_ACCEL:         /* ±2 g: 9.80665 / 16384 = 0.000598550 m/s^2 */
			*val = 0;
			*val2 = 598550;
			return IIO_VAL_INT_PLUS_NANO;
		case IIO_ANGL_VEL:      /* ±250 °/s: (pi / 180) / 131 = 0.000133231 rad/s */
			*val = 0;
			*val2 = 133231;
			return IIO_VAL_INT_PLUS_NANO;
		case IIO_TEMP:          /* 1000 / 340 = 2.941176 milli °C */
			*val = 2;
			*val2 = 941176;
			return IIO_VAL_INT_PLUS_MICRO;
		default:
			return -EINVAL;
		}

	case IIO_CHAN_INFO_OFFSET:      /* sadece sıcaklık: 36.53 °C x 340 = 12420.2 */
		*val = 12420;
		*val2 = 200000;
		return IIO_VAL_INT_PLUS_MICRO;
	}

	return -EINVAL;
}

static const struct iio_info bbb_mpu_info = {
	.read_raw = bbb_mpu_read_raw,
};

/* Sürücü ayrılırken sensörü uyku moduna al. */
static void bbb_mpu_sleep(void *data)
{
	struct bbb_mpu *m = data;

	i2c_smbus_write_byte_data(m->client, MPU6050_REG_PWR_MGMT_1, MPU6050_PWR_SLEEP);
}

static int bbb_mpu_probe(struct i2c_client *client)
{
	struct device *dev = &client->dev;
	struct iio_dev *indio_dev;
	struct bbb_mpu *m;
	int ret;

	ret = i2c_smbus_read_byte_data(client, MPU6050_REG_WHO_AM_I);
	if (ret < 0)
		return dev_err_probe(dev, ret, "no answer at 0x%02x\n", client->addr);
	if (ret != MPU6050_WHO_AM_I_VALUE)
		return dev_err_probe(dev, -ENODEV, "WHO_AM_I = 0x%02x, not an MPU6050\n", ret);

	/* Uyandır, saat kaynağını seç, ölçek aralıklarını ±2 g / ±250 °/s yap. */
	ret = i2c_smbus_write_byte_data(client, MPU6050_REG_PWR_MGMT_1, MPU6050_PWR_CLK_PLL_X);
	if (ret)
		return ret;
	msleep(100);
	ret = i2c_smbus_write_byte_data(client, MPU6050_REG_ACCEL_CONFIG, 0);
	if (!ret)
		ret = i2c_smbus_write_byte_data(client, MPU6050_REG_GYRO_CONFIG, 0);
	if (ret)
		return ret;

	indio_dev = devm_iio_device_alloc(dev, sizeof(*m));
	if (!indio_dev)
		return -ENOMEM;

	m = iio_priv(indio_dev);
	m->client = client;
	mutex_init(&m->lock);

	ret = devm_add_action_or_reset(dev, bbb_mpu_sleep, m);
	if (ret)
		return ret;

	indio_dev->name = "bbb_mpu6050";
	indio_dev->info = &bbb_mpu_info;
	indio_dev->channels = bbb_mpu_channels;
	indio_dev->num_channels = ARRAY_SIZE(bbb_mpu_channels);
	indio_dev->modes = INDIO_DIRECT_MODE;

	ret = devm_iio_device_register(dev, indio_dev);
	if (ret)
		return ret;

	dev_info(dev, "MPU6050 ready as %s\n", dev_name(&indio_dev->dev));
	return 0;
}

/* new_device ile tanıtmak için (echo bbb_mpu6050 0x68 > .../new_device) */
static const struct i2c_device_id bbb_mpu_id[] = {
	{ "bbb_mpu6050", 0 },
	{ }
};
MODULE_DEVICE_TABLE(i2c, bbb_mpu_id);

/* Device tree ile tanıtmak için */
static const struct of_device_id bbb_mpu_of_match[] = {
	{ .compatible = "bbb,mpu6050" },
	{ }
};
MODULE_DEVICE_TABLE(of, bbb_mpu_of_match);

static struct i2c_driver bbb_mpu_driver = {
	.driver = {
		.name           = "bbb_mpu6050",
		.of_match_table = bbb_mpu_of_match,
	},
#if LINUX_VERSION_CODE >= KERNEL_VERSION(6, 3, 0)
	.probe          = bbb_mpu_probe,
#else
	.probe_new      = bbb_mpu_probe,
#endif
	.id_table       = bbb_mpu_id,
};
module_i2c_driver(bbb_mpu_driver);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Embedded Linux kitabı");
MODULE_DESCRIPTION("MPU6050 accelerometer/gyroscope IIO driver (learning example)");
