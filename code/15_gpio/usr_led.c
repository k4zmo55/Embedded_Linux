/*
 * usr_led.c — BeagleBone Black'in USR0-USR3 LED'lerini sysfs üzerinden kontrol eder.
 *
 * Kursun BBB_led_control.c programının düzeltilmiş ve genelleştirilmiş hali:
 *  - brightness değeri sysfs'e METİN olarak yazılır ("0" / "1").
 *    (Orijinal kod int'in ham baytlarını yazıyordu; kernel bunu reddeder.)
 *  - Sadece USR3 değil, 0-3 arası bütün LED'ler desteklenir.
 *  - Açılan dosyalar kapatılır.
 *
 * Derleme:  arm-linux-gnueabihf-gcc -Wall -o usr_led usr_led.c
 * Kullanım: ./usr_led <led 0-3> <trigger|brightness> <value>   (root olarak)
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>

#define LED_ATTR_PATH "/sys/class/leds/beaglebone:green:usr%d/%s"

/* /sys/class/leds/beaglebone:green:usr<led>/<attr> dosyasına value'yu yazar. */
static int write_attr(int led, const char *attr, const char *value)
{
	char path[128];
	ssize_t n;
	int fd;

	snprintf(path, sizeof(path), LED_ATTR_PATH, led, attr);

	fd = open(path, O_WRONLY);
	if (fd < 0) {
		perror(path);
		return -1;
	}

	n = write(fd, value, strlen(value));
	if (n < 0)
		perror("write");

	close(fd);
	return n < 0 ? -1 : 0;
}

static int is_one_of(const char *s, const char *const list[])
{
	for (; *list; list++)
		if (strcmp(s, *list) == 0)
			return 1;
	return 0;
}

static void usage(const char *prog)
{
	printf("usage: %s <led 0-3> <trigger|brightness> <value>\n", prog);
	printf("  trigger    : none, heartbeat, timer, oneshot, default-on\n");
	printf("  brightness : 0, 1\n");
}

int main(int argc, char *argv[])
{
	static const char *const triggers[] = {
		"none", "heartbeat", "timer", "oneshot", "default-on", NULL
	};
	static const char *const levels[] = { "0", "1", NULL };
	const char *option, *value;
	int led;

	if (argc != 4) {
		usage(argv[0]);
		return 1;
	}

	if (strlen(argv[1]) != 1 || argv[1][0] < '0' || argv[1][0] > '3') {
		printf("Invalid LED number: %s (valid: 0-3)\n", argv[1]);
		return 1;
	}
	led = argv[1][0] - '0';
	option = argv[2];
	value = argv[3];

	if (strcmp(option, "trigger") == 0) {
		if (!is_one_of(value, triggers)) {
			printf("Invalid trigger: %s\n", value);
			usage(argv[0]);
			return 1;
		}
		if (write_attr(led, "trigger", value) < 0)
			return 1;
	} else if (strcmp(option, "brightness") == 0) {
		if (!is_one_of(value, levels)) {
			printf("Invalid brightness: %s\n", value);
			usage(argv[0]);
			return 1;
		}
		if (write_attr(led, "brightness", value) < 0)
			return 1;
	} else {
		printf("Invalid option: %s\n", option);
		usage(argv[0]);
		return 1;
	}

	printf("usr%d %s -> %s\n", led, option, value);
	return 0;
}
