// SPDX-License-Identifier: GPL-2.0
/*
 * bbb_gpio_demo.c — Device tree'den tanıtılan bir LED ve bir butonu süren
 * platform sürücüsü.
 *
 * Device tree düğümü (bkz. am335x-boneblack-gpiodemo.dts):
 *
 *   bbb-gpio-demo {
 *       compatible = "bbb,gpio-demo";
 *       led-gpios = <&gpio1 28 GPIO_ACTIVE_HIGH>;      P9_12
 *       button-gpios = <&gpio1 17 GPIO_ACTIVE_HIGH>;   P9_23
 *   };
 *
 * Sürücü:
 *   - compatible eşleşince probe() çağrılır; GPIO'ları devm_gpiod_get() ile alır
 *   - butonun yükselen kenarında kesme gelir; LED'in durumu değişir
 *   - /sys/bus/platform/devices/bbb-gpio-demo/ altında iki dosya açar:
 *       led     : LED'i oku / yaz (0, 1)
 *       presses : kaç kez basıldı; her basışta poll() ile bekleyenler uyanır
 */
#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/mod_devicetable.h>
#include <linux/gpio/consumer.h>
#include <linux/interrupt.h>
#include <linux/jiffies.h>
#include <linux/mutex.h>
#include <linux/atomic.h>

#define DEBOUNCE_MS         50

struct gpio_demo {
	struct device *dev;
	struct gpio_desc *led;
	struct gpio_desc *button;
	int irq;
	unsigned long last_press;   /* son geçerli basışın zamanı (jiffies) */
	atomic_t presses;
	bool led_on;
	struct mutex lock;          /* led_on'u korur */
};

/* Çağıran lock'u tutmalı. */
static void demo_set_led(struct gpio_demo *d, bool on)
{
	d->led_on = on;
	gpiod_set_value_cansleep(d->led, on);
}

/*
 * Butonun kesmesi. "Threaded" kesme: kernel bu fonksiyonu ayrı bir kernel
 * thread'inde çalıştırır; içinde uyuyabilen fonksiyonlar (mutex) kullanılabilir.
 */
static irqreturn_t demo_button_thread(int irq, void *data)
{
	struct gpio_demo *d = data;
	unsigned long now = jiffies;
	int n;

	/* Kontak sekmesi: son basıştan bu yana DEBOUNCE_MS geçmediyse sayma. */
	if (time_before(now, d->last_press + msecs_to_jiffies(DEBOUNCE_MS)))
		return IRQ_HANDLED;
	d->last_press = now;

	mutex_lock(&d->lock);
	demo_set_led(d, !d->led_on);
	mutex_unlock(&d->lock);

	n = atomic_inc_return(&d->presses);
	dev_info(d->dev, "button pressed (%d), LED %s\n", n, d->led_on ? "on" : "off");

	/* presses dosyasını poll() ile bekleyen programları uyandır. */
	sysfs_notify(&d->dev->kobj, NULL, "presses");
	return IRQ_HANDLED;
}

static ssize_t led_show(struct device *dev, struct device_attribute *attr, char *buf)
{
	struct gpio_demo *d = dev_get_drvdata(dev);

	return sysfs_emit(buf, "%d\n", d->led_on);
}

static ssize_t led_store(struct device *dev, struct device_attribute *attr,
			 const char *buf, size_t count)
{
	struct gpio_demo *d = dev_get_drvdata(dev);
	bool on;
	int ret;

	ret = kstrtobool(buf, &on);         /* "0", "1", "y", "n", "on", "off" */
	if (ret)
		return ret;

	mutex_lock(&d->lock);
	demo_set_led(d, on);
	mutex_unlock(&d->lock);
	return count;
}
static DEVICE_ATTR_RW(led);

static ssize_t presses_show(struct device *dev, struct device_attribute *attr, char *buf)
{
	struct gpio_demo *d = dev_get_drvdata(dev);

	return sysfs_emit(buf, "%d\n", atomic_read(&d->presses));
}
static DEVICE_ATTR_RO(presses);

static struct attribute *gpio_demo_attrs[] = {
	&dev_attr_led.attr,
	&dev_attr_presses.attr,
	NULL,
};
ATTRIBUTE_GROUPS(gpio_demo);

/* Sürücü ayrılırken (rmmod, unbind) LED'i söndürür. */
static void demo_led_off(void *data)
{
	struct gpio_demo *d = data;

	gpiod_set_value_cansleep(d->led, 0);
}

static int gpio_demo_probe(struct platform_device *pdev)
{
	struct device *dev = &pdev->dev;
	struct gpio_demo *d;
	int ret;

	d = devm_kzalloc(dev, sizeof(*d), GFP_KERNEL);
	if (!d)
		return -ENOMEM;
	d->dev = dev;
	mutex_init(&d->lock);
	atomic_set(&d->presses, 0);

	/* DT'deki "led-gpios" ve "button-gpios" property'leri */
	d->led = devm_gpiod_get(dev, "led", GPIOD_OUT_LOW);
	if (IS_ERR(d->led))
		return dev_err_probe(dev, PTR_ERR(d->led), "cannot get led-gpios\n");

	d->button = devm_gpiod_get(dev, "button", GPIOD_IN);
	if (IS_ERR(d->button))
		return dev_err_probe(dev, PTR_ERR(d->button), "cannot get button-gpios\n");

	/* AM335x'in GPIO modülü donanımsal debounce yapabilir; olmazsa yazılımdaki kontrol yeter. */
	if (gpiod_set_debounce(d->button, DEBOUNCE_MS * 1000))
		dev_info(dev, "no hardware debounce, using software debounce\n");

	d->irq = gpiod_to_irq(d->button);
	if (d->irq < 0)
		return dev_err_probe(dev, d->irq, "button has no irq\n");

	platform_set_drvdata(pdev, d);

	/* devm eylemleri ters sırada çalışır: önce kesme bırakılır, sonra LED söner. */
	ret = devm_add_action_or_reset(dev, demo_led_off, d);
	if (ret)
		return ret;

	ret = devm_request_threaded_irq(dev, d->irq, NULL, demo_button_thread,
					IRQF_TRIGGER_RISING | IRQF_ONESHOT,
					dev_name(dev), d);
	if (ret)
		return dev_err_probe(dev, ret, "cannot request irq %d\n", d->irq);

	dev_info(dev, "ready: LED off, button on irq %d\n", d->irq);
	return 0;
}

static const struct of_device_id gpio_demo_of_match[] = {
	{ .compatible = "bbb,gpio-demo" },
	{ }
};
MODULE_DEVICE_TABLE(of, gpio_demo_of_match);

static struct platform_driver gpio_demo_driver = {
	.probe = gpio_demo_probe,
	.driver = {
		.name           = "bbb-gpio-demo",
		.of_match_table = gpio_demo_of_match,
		.dev_groups     = gpio_demo_groups,
	},
};
module_platform_driver(gpio_demo_driver);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Embedded Linux kitabı");
MODULE_DESCRIPTION("Device tree based LED + button platform driver");
