/*
 * counter_7seg.c — 7-segment göstergede yukarı/aşağı/yukarı-aşağı/rastgele sayar.
 *
 * Kursun Project_Src/counter_7seg/src/counter_7seg.c programının düzeltilmiş
 * hali. Kursta öğrenciye bırakılan "updown" ve "random" modları da yazıldı.
 *
 * Derleme:  arm-linux-gnueabihf-gcc -Wall -Ilib -o counter_7seg \
 *               17_7segment/counter_7seg.c 17_7segment/seg7.c lib/gpio_driver.c
 *           (ortak anot gösterge için: -DCOMMON_ANODE ekle)
 * Kullanım: ./counter_7seg <up|down|updown|random> <gecikme ms>    (root olarak)
 * Ctrl-C ile durdurulunca gösterge söndürülür ve GPIO'lar bırakılır.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <time.h>
#include <unistd.h>

#include "seg7.h"

static volatile sig_atomic_t running = 1;

static void on_sigint(int sig)
{
	(void)sig;
	running = 0;
}

static void show_and_wait(uint8_t digit, unsigned int delay_ms)
{
	seg7_show(digit);
	usleep(delay_ms * 1000);
}

/* 0, 1, ... 9, 0, 1, ... */
static void start_upcounting(unsigned int delay_ms)
{
	int i;

	while (running)
		for (i = 0; i <= 9 && running; i++)
			show_and_wait(i, delay_ms);
}

/* 9, 8, ... 0, 9, 8, ... */
static void start_downcounting(unsigned int delay_ms)
{
	int i;

	while (running)
		for (i = 9; i >= 0 && running; i--)
			show_and_wait(i, delay_ms);
}

/* 0, 1, ... 9, 8, ... 1, 0, 1, ... (uçlardaki rakamlar tekrarlanmaz) */
static void start_updowncounting(unsigned int delay_ms)
{
	int i = 0, step = 1;

	while (running) {
		show_and_wait(i, delay_ms);
		if (i == 9)
			step = -1;
		else if (i == 0)
			step = 1;
		i += step;
	}
}

/* Rastgele rakamlar; aynı rakam art arda gelmez, yoksa gösterge donmuş gibi görünür. */
static void start_randomcounting(unsigned int delay_ms)
{
	int last = -1, n;

	srand((unsigned int)time(NULL));

	while (running) {
		do
			n = rand() % 10;
		while (n == last);
		last = n;
		show_and_wait(n, delay_ms);
	}
}

static void usage(const char *prog)
{
	printf("usage: %s <direction> <delay ms>\n", prog);
	printf("valid direction : up, down, updown, random\n");
	printf("recommended delay range in ms : 0 to 1000\n");
}

int main(int argc, char *argv[])
{
	void (*count)(unsigned int);
	unsigned int delay_ms;

	printf("Application for up/down/random counter on 7 seg display\n");

	if (argc != 3) {
		usage(argv[0]);
		return 1;
	}

	if (strcmp(argv[1], "up") == 0)
		count = start_upcounting;
	else if (strcmp(argv[1], "down") == 0)
		count = start_downcounting;
	else if (strcmp(argv[1], "updown") == 0)
		count = start_updowncounting;
	else if (strcmp(argv[1], "random") == 0)
		count = start_randomcounting;
	else {
		printf("Invalid direction value\n");
		usage(argv[0]);
		return 1;
	}
	delay_ms = (unsigned int)atoi(argv[2]);

	if (seg7_init() < 0) {
		printf("Error: GPIO init failed !\n");
		return 1;
	}

	signal(SIGINT, on_sigint);
	printf("%s counting every %u ms, press Ctrl-C to stop\n", argv[1], delay_ms);

	count(delay_ms);

	seg7_release();
	printf("\nDisplay off, GPIOs released\n");
	return 0;
}
