/*
 * counter_4digit.c — 4 haneli 7-segment göstergede sayaç ve dijital saat.
 *
 * Kursun Project_Src/4digitcount/src/4_digit_7seg.c programının düzeltilmiş
 * hali. Kursta öğrenciye bırakılan "updown", "random" ve dijital saat
 * ("clock") modları da yazıldı.
 *
 * Derleme (code/ klasöründe):
 *   arm-linux-gnueabihf-gcc -Wall -Ilib -I17_7segment -DCOMMON_ANODE \
 *       -o counter_4digit 18_4digit_7segment/counter_4digit.c \
 *       18_4digit_7segment/seg7x4.c 17_7segment/seg7.c lib/gpio_driver.c
 *
 * Kullanım: ./counter_4digit <up|down|updown|random> <gecikme ms>
 *           ./counter_4digit clock                         (root olarak)
 * Ctrl-C ile durdurulunca gösterge söndürülür ve GPIO'lar bırakılır.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <time.h>

#include "seg7x4.h"

enum mode { UP, DOWN, UPDOWN, RANDOM, CLOCK };

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

/* 0-9999 arası sayıyı soldan sağa 4 rakama ayırır (baştaki sıfırlar gösterilir). */
static void split(int number, uint8_t digits[SEG7X4_DIGITS])
{
	int i;

	for (i = SEG7X4_DIGITS - 1; i >= 0; i--) {
		digits[i] = number % 10;
		number /= 10;
	}
}

/* Sayacın bir sonraki değeri. step: updown modunun yönü (+1 / -1). */
static int next_number(enum mode mode, int n, int *step)
{
	int r;

	switch (mode) {
	case UP:
		return n == 9999 ? 0 : n + 1;
	case DOWN:
		return n == 0 ? 9999 : n - 1;       /* kursta: 0'dan sonra 7295 */
	case UPDOWN:
		if (n == 9999)
			*step = -1;
		else if (n == 0)
			*step = 1;
		return n + *step;
	case RANDOM:
		do
			r = rand() % 10000;
		while (r == n);
		return r;
	default:
		return n;
	}
}

static void usage(const char *prog)
{
	printf("usage: %s <direction> <delay ms>\n", prog);
	printf("       %s clock\n", prog);
	printf("valid direction : up, down, updown, random\n");
}

int main(int argc, char *argv[])
{
	static const char *names[] = { "up", "down", "updown", "random", "clock" };
	uint8_t digits[SEG7X4_DIGITS];
	uint8_t dp_mask = 0;
	int number = 0, step = 1, delay_ms = 0;
	enum mode mode;
	long last_step;
	struct tm tm;
	time_t t;

	printf("4 digit 7seg LED up/down/random counter and clock application\n");

	if (argc < 2) {
		usage(argv[0]);
		return 1;
	}

	for (mode = UP; mode <= CLOCK; mode++)
		if (strcmp(argv[1], names[mode]) == 0)
			break;

	if (mode > CLOCK || (mode != CLOCK && argc != 3)) {
		usage(argv[0]);
		return 1;
	}
	if (mode != CLOCK)
		delay_ms = atoi(argv[2]);

	if (mode == DOWN)
		number = 9999;
	srand((unsigned int)time(NULL));

	if (seg7x4_init() < 0) {
		printf("Error: GPIO init failed !\n");
		seg7x4_release();
		return 1;
	}

	signal(SIGINT, on_sigint);
	if (mode == CLOCK)
		printf("clock mode (HH.MM), press Ctrl-C to stop\n");
	else
		printf("%s counting every %d ms, press Ctrl-C to stop\n", names[mode], delay_ms);

	last_step = now_ms();

	/* Gösterge sadece tarandığı sürece yanar: döngü hiç beklemeden tarar. */
	while (running) {
		if (mode == CLOCK) {
			t = time(NULL);
			localtime_r(&t, &tm);
			split(tm.tm_hour * 100 + tm.tm_min, digits);
			dp_mask = tm.tm_sec % 2 ? 0 : 1 << 1;    /* 2. hanenin noktası saniyede bir yanıp söner */
		} else {
			if (now_ms() - last_step >= delay_ms) {
				last_step = now_ms();
				number = next_number(mode, number, &step);
			}
			split(number, digits);
		}

		if (seg7x4_refresh(digits, dp_mask) < 0) {
			perror("display refresh");
			break;
		}
	}

	seg7x4_release();
	printf("\nDisplay off, GPIOs released\n");
	return 0;
}
