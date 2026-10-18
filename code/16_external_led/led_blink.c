/*
 * led_blink.c — Bir GPIO'ya bağlı harici LED'i yakıp söndürür.
 *
 * Derleme:  arm-linux-gnueabihf-gcc -Wall -I../lib -o led_blink led_blink.c ../lib/gpio_driver.c
 * Kullanım: ./led_blink <gpio numarası> [yarım periyot ms]     (root olarak)
 *           ./led_blink 60 500      -> P9_12, 500 ms yanık / 500 ms sönük
 * Ctrl-C ile durdurulunca LED söndürülür ve GPIO bırakılır.
 */
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>

#include "gpio_driver.h"

static volatile sig_atomic_t running = 1;

static void on_sigint(int sig)
{
	(void)sig;
	running = 0;
}

int main(int argc, char *argv[])
{
	unsigned int gpio, half_period_ms = 500;
	int on = 0;

	if (argc < 2) {
		printf("usage: %s <gpio number> [half period ms]\n", argv[0]);
		printf("  example: %s 60 500   (P9_12)\n", argv[0]);
		return 1;
	}
	gpio = (unsigned int)atoi(argv[1]);
	if (argc > 2)
		half_period_ms = (unsigned int)atoi(argv[2]);

	/* Zaten export edilmişse hata verir; bu sorun değil, devam ediyoruz. */
	gpio_export(gpio);

	if (gpio_configure_dir(gpio, GPIO_DIR_OUT) < 0) {
		printf("GPIO %u could not be configured as output\n", gpio);
		return 1;
	}

	signal(SIGINT, on_sigint);
	printf("GPIO %u blinking every %u ms, press Ctrl-C to stop\n", gpio, half_period_ms);

	while (running) {
		on = !on;
		gpio_write_value(gpio, on);
		usleep(half_period_ms * 1000);
	}

	gpio_write_value(gpio, GPIO_LOW_VALUE);
	gpio_unexport(gpio);
	printf("\nLED off, GPIO %u released\n", gpio);
	return 0;
}
