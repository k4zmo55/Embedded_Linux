/*
 * gpio_driver.c — /sys/class/gpio üzerinden basit GPIO fonksiyonları.
 *
 * Kursun Project_Src/Drivers/gpio/gpio_driver.c dosyasının düzeltilmiş hali:
 *  - gpio_read_value(): dosya O_RDONLY açılır (orijinali O_WRONLY açıp read()
 *    çağırıyordu, okuma hep başarısız oluyordu) ve ASCII '0'/'1' yerine 0/1 döner.
 *  - write() dönüş değerleri kontrol edilir.
 *  - Sonuna NUL karakteri yazılmaz ("out" için 3 bayt, "1" için 1 bayt).
 *  - gpio_unexport() eklendi.
 *
 * Not: /sys/class/gpio kernel'de eskimiş (deprecated) bir arayüzdür ve yeni
 * kernel'lerde GPIO numaraları 512'den başlayabilir (bkz. kitap Bölüm 15.6).
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>

#include "gpio_driver.h"

/* path dosyasına str'yi yazar. Başarılıysa 0, değilse -1 döner. */
static int write_str(const char *path, const char *str)
{
	ssize_t n;
	int fd;

	fd = open(path, O_WRONLY);
	if (fd < 0) {
		perror(path);
		return -1;
	}

	n = write(fd, str, strlen(str));
	if (n < 0)
		perror(path);

	close(fd);
	return n < 0 ? -1 : 0;
}

/* GPIO'yu kullanıcı alanına açar (/sys/class/gpio/gpioN klasörü oluşur). */
int gpio_export(uint32_t gpio_num)
{
	char buf[SOME_BYTES];

	snprintf(buf, sizeof(buf), "%u", gpio_num);
	return write_str(SYS_GPIO_PATH "/export", buf);
}

/* GPIO'yu bırakır. */
int gpio_unexport(uint32_t gpio_num)
{
	char buf[SOME_BYTES];

	snprintf(buf, sizeof(buf), "%u", gpio_num);
	return write_str(SYS_GPIO_PATH "/unexport", buf);
}

/* dir_value: GPIO_DIR_OUT (1) = çıkış, GPIO_DIR_IN (0) = giriş */
int gpio_configure_dir(uint32_t gpio_num, uint8_t dir_value)
{
	char path[SOME_BYTES];

	snprintf(path, sizeof(path), SYS_GPIO_PATH "/gpio%u/direction", gpio_num);
	return write_str(path, dir_value ? "out" : "in");
}

/* out_value: 0 veya 1 */
int gpio_write_value(uint32_t gpio_num, uint8_t out_value)
{
	char path[SOME_BYTES];

	snprintf(path, sizeof(path), SYS_GPIO_PATH "/gpio%u/value", gpio_num);
	return write_str(path, out_value ? "1" : "0");
}

/* Girişi okur: 0 veya 1, hata durumunda -1 döner. */
int gpio_read_value(uint32_t gpio_num)
{
	char path[SOME_BYTES];
	char c = 0;
	ssize_t n;
	int fd;

	snprintf(path, sizeof(path), SYS_GPIO_PATH "/gpio%u/value", gpio_num);

	fd = open(path, O_RDONLY);
	if (fd < 0) {
		perror(path);
		return -1;
	}

	n = read(fd, &c, 1);
	close(fd);
	if (n != 1) {
		perror(path);
		return -1;
	}

	return c == '1' ? 1 : 0;
}

/* edge: "none", "rising", "falling" veya "both" */
int gpio_configure_edge(uint32_t gpio_num, char *edge)
{
	char path[SOME_BYTES];

	snprintf(path, sizeof(path), SYS_GPIO_PATH "/gpio%u/edge", gpio_num);
	return write_str(path, edge);
}

/* value dosyasını poll() ile beklemek için açar. */
int gpio_file_open(uint32_t gpio_num)
{
	char path[SOME_BYTES];
	int fd;

	snprintf(path, sizeof(path), SYS_GPIO_PATH "/gpio%u/value", gpio_num);

	fd = open(path, O_RDONLY | O_NONBLOCK);
	if (fd < 0)
		perror(path);
	return fd;
}

int gpio_file_close(int fd)
{
	return close(fd);
}
