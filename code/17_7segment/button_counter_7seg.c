/*
 * button_counter_7seg.c — Butona her basışta 7-segment göstergedeki sayıyı artırır (0-9).
 *
 * Kursun Project_Src/button_counter_7seg/src/button_counter_7seg.c programının
 * düzeltilmiş hali. Kursun kodundaki hatalar:
 *  - Sayaç (led_counter) ilk değer verilmeden kullanılıyor ve 9'dan sonra
 *    başa dönmüyordu (10'da gösterge söner, sonra hiç değişmez).
 *  - poll() ilk çağrıda butona basılmadan döner; bu bir basış sayılıyordu.
 *  - Buton kontağı sektiği (bounce) için tek basış birkaç kez sayılabiliyordu.
 *  - initialize_button_gpio() buton yerine nokta (dp) GPIO'suna yazıyordu.
 *  - Segment mantığı counter_7seg.c'nin tersiydi (SEGMENT_ON = LOW).
 *
 * Buton: 3.3 V (P9_3) ile P9_23 (GPIO 49) arasında; P9_23 ile GND arasında
 * 10 kΩ pull-down. Basınca pin 1 olur, yükselen kenar (rising) beklenir.
 *
 * Derleme:  arm-linux-gnueabihf-gcc -Wall -Ilib -o button_counter_7seg \
 *               17_7segment/button_counter_7seg.c 17_7segment/seg7.c lib/gpio_driver.c
 * Kullanım: ./button_counter_7seg      (root olarak, Ctrl-C ile dur)
 */
#include <stdio.h>
#include <errno.h>
#include <poll.h>
#include <signal.h>
#include <time.h>
#include <unistd.h>

#include "gpio_driver.h"
#include "seg7.h"

#define BUTTON_GPIO         49      /* P9_23 */
#define DEBOUNCE_MS         200     /* bu süre içindeki yeni kenarlar sayılmaz */

static volatile sig_atomic_t running = 1;

static void on_sigint(int sig)
{
	(void)sig;
	running = 0;
}

static long now_ms(void)
{
	struct timespec ts;

	clock_gettime(CLOCK_MONOTONIC, &ts);
	return ts.tv_sec * 1000L + ts.tv_nsec / 1000000L;
}

/* value dosyasını baştan okur; bekleyen olayı temizler, okunan karakteri döner. */
static char read_value_fd(int fd)
{
	char c = 0;

	lseek(fd, 0, SEEK_SET);
	if (read(fd, &c, 1) != 1)
		perror("button read");
	return c;
}

int main(void)
{
	struct pollfd pfd;
	long last_press = 0;
	uint8_t counter = 0;
	int fd, rc;

	printf("This program counts button presses (0-9) on 7segment display\n");

	if (seg7_init() < 0) {
		printf("Error: could not initialize the display GPIOs\n");
		return 1;
	}

	gpio_export(BUTTON_GPIO);
	if (gpio_configure_dir(BUTTON_GPIO, GPIO_DIR_IN) < 0 ||
	    gpio_configure_edge(BUTTON_GPIO, "rising") < 0) {
		printf("Error: could not initialize the button GPIO\n");
		seg7_release();
		return 1;
	}

	fd = gpio_file_open(BUTTON_GPIO);
	if (fd < 0) {
		seg7_release();
		return 1;
	}

	/* Açılıştaki bekleyen olayı temizle; yoksa ilk poll() hemen döner. */
	read_value_fd(fd);

	signal(SIGINT, on_sigint);
	seg7_show(counter);
	printf("Waiting for the button press, press Ctrl-C to stop\n");

	while (running) {
		pfd.fd = fd;
		pfd.events = POLLPRI | POLLERR;
		pfd.revents = 0;

		/* Butona basılana kadar burada bekler (zaman aşımı yok). */
		rc = poll(&pfd, 1, -1);
		if (rc < 0) {
			if (errno == EINTR)     /* Ctrl-C */
				continue;
			perror("poll");
			break;
		}

		if (!(pfd.revents & POLLPRI))
			continue;

		/* Kenar geldi; olayı temizle ve hâlâ basılı mı diye bak. */
		if (read_value_fd(fd) != '1')
			continue;

		if (now_ms() - last_press < DEBOUNCE_MS)
			continue;
		last_press = now_ms();

		counter = (counter + 1) % 10;
		seg7_show(counter);
		printf("button pressed, count = %u\n", counter);
	}

	gpio_file_close(fd);
	gpio_configure_edge(BUTTON_GPIO, "none");
	gpio_unexport(BUTTON_GPIO);
	seg7_release();
	printf("\nDisplay off, GPIOs released\n");
	return 0;
}
