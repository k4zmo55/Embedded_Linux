/*
 * lcd_text.c — 16x2 LCD'de sırayla bir başlık, kartın IP adresi, kullanıcının
 * mesajı ve tarih/saat gösterir.
 *
 * Kursun Project_Src/lcd_text/src/lcd_text.c programının düzeltilmiş hali:
 *  - Tarih/saat doğru gösterilir (kursta ay 0'dan başlıyordu ve sıfır dolgusu
 *    yoktu; kodda öğrenciye bırakılan TODO buydu).
 *  - IP adresi sabit "usb0" yerine çalışan ilk IPv4 arayüzünden alınır;
 *    hatalar kontrol edilir.
 *  - Kullanıcının mesajı biçim (format) string'i olarak kullanılmaz (kursta
 *    lcd_printf(msg_buf): mesajda '%' varsa tanımsız davranış) ve taşmaz.
 *
 * Derleme (code/ klasöründe):
 *   arm-linux-gnueabihf-gcc -Wall -Ilib -I20_lcd -o lcd_text \
 *       20_lcd/lcd_text.c 20_lcd/lcd_driver.c lib/gpio_driver.c
 * Kullanım: ./lcd_text "mesaj"        (root olarak, Ctrl-C ile dur)
 */
#include <stdio.h>
#include <string.h>
#include <signal.h>
#include <time.h>
#include <unistd.h>
#include <ifaddrs.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#include "lcd_driver.h"

static volatile sig_atomic_t running = 1;

static void on_sigint(int sig)
{
	(void)sig;
	running = 0;
}

/* Sinyal gelirse erken döner; ekranlar arasında beklemek için. */
static void wait_s(int seconds)
{
	while (seconds-- > 0 && running)
		sleep(1);
}

/* 1. satır: "2026-10-19 Mon", 2. satır: "14:37:05" */
static void print_time_and_date(void)
{
	struct tm tm;
	time_t t;
	char line[LCD_COLUMNS + 1];

	t = time(NULL);
	localtime_r(&t, &tm);

	strftime(line, sizeof(line), "%Y-%m-%d %a", &tm);
	lcd_set_cursor(1, 1);
	lcd_print_string(line);

	strftime(line, sizeof(line), "%H:%M:%S", &tm);
	lcd_set_cursor(2, 1);
	lcd_print_string(line);
}

/* Çalışan ilk IPv4 arayüzünün adını ve adresini gösterir (lo hariç). */
static void print_ip_address(void)
{
	struct ifaddrs *list = NULL, *ifa;
	char addr[INET_ADDRSTRLEN] = "";
	const char *name = "no network";

	if (getifaddrs(&list) == 0) {
		for (ifa = list; ifa != NULL; ifa = ifa->ifa_next) {
			if (ifa->ifa_addr == NULL || ifa->ifa_addr->sa_family != AF_INET ||
			    strcmp(ifa->ifa_name, "lo") == 0)
				continue;
			inet_ntop(AF_INET, &((struct sockaddr_in *)ifa->ifa_addr)->sin_addr,
				  addr, sizeof(addr));
			name = ifa->ifa_name;
			break;
		}
	}

	lcd_set_cursor(1, 1);
	lcd_printf("%s", name);
	lcd_set_cursor(2, 1);
	lcd_printf("%s", addr);

	if (list)
		freeifaddrs(list);
}

/* Kursun geçiş efekti: 1. satır soldan sağa, 2. satır sağdan sola yıldızlarla dolar. */
static void transition_graphics(void)
{
	int i;

	lcd_clear();

	lcd_set_cursor(1, 1);
	for (i = 0; i < LCD_COLUMNS && running; i++) {
		lcd_print_char('*');
		usleep(75 * 1000);
	}

	/* Entry mode: imleç her karakterden sonra azalır, yani sola yazar. */
	lcd_send_command(LCD_CMD_ENTRY_MODESET);
	lcd_set_cursor(2, LCD_COLUMNS);
	for (i = 0; i < LCD_COLUMNS && running; i++) {
		lcd_print_char('*');
		usleep(75 * 1000);
	}
	lcd_send_command(LCD_CMD_ENTRY_MODESET | INC_CURSOR);

	usleep(450 * 1000);
	lcd_clear();
}

int main(int argc, char *argv[])
{
	printf("This Application prints your message on the 16x2 LCD\n");

	if (argc != 2) {
		printf("usage: %s <message>\n", argv[0]);
		return 1;
	}

	if (lcd_init() < 0) {
		printf("Error: LCD init failed\n");
		return 1;
	}

	signal(SIGINT, on_sigint);
	printf("Running, press Ctrl-C to stop\n");

	while (running) {
		lcd_set_cursor(1, 1);
		lcd_print_string("BBB LCD Demo");
		wait_s(2);
		transition_graphics();

		print_ip_address();
		wait_s(3);
		transition_graphics();

		/* İlk 16 karakter 1. satıra, sonraki 16 karakter 2. satıra */
		lcd_set_cursor(1, 1);
		lcd_printf("%.16s", argv[1]);
		if (strlen(argv[1]) > LCD_COLUMNS) {
			lcd_set_cursor(2, 1);
			lcd_printf("%.16s", argv[1] + LCD_COLUMNS);
		}
		wait_s(3);
		transition_graphics();

		/* Saat 5 saniye boyunca her saniye güncellenir. */
		for (int i = 0; i < 5 && running; i++) {
			print_time_and_date();
			wait_s(1);
		}
		transition_graphics();
	}

	lcd_release();
	printf("\nLCD cleared, GPIOs released\n");
	return 0;
}
