/*
 * lcd_scroll.c — Komut satırından verilen yazıları LCD'nin 1. satırında
 * sağdan sola kaydırır (kayan yazı).
 *
 * Kursun Project_Src/lcd_scrollable_text programının yeniden yazılmış hali.
 * Kursta yazılar programa gömülüydü ve komut satırından alınmaları öğrenciye
 * bırakılmıştı (TODO). Kursun kodu ayrıca derlenmiyordu
 * ("LCD_CMD_CLEAR_DISPLAY yo") ve başlatmadan sonra 1 satır moduna geçmeye
 * çalışıyordu; HD44780 bunu kabul etmez (datasheet: satır sayısı function set
 * dışında değiştirilemez).
 *
 * Burada kaydırma yazılımla yapılır: yazının 16 karakterlik bir penceresi her
 * adımda 1. satıra yeniden yazılır. Böylece yazı uzunluğu DDRAM'in satır
 * başına 40 karakteriyle sınırlı kalmaz.
 *
 * Derleme (code/ klasöründe):
 *   arm-linux-gnueabihf-gcc -Wall -Ilib -I20_lcd -o lcd_scroll \
 *       20_lcd/lcd_scroll.c 20_lcd/lcd_driver.c lib/gpio_driver.c
 * Kullanım: ./lcd_scroll "birinci yazı" "ikinci yazı" ...   (Ctrl-C ile dur)
 */
#include <stdio.h>
#include <string.h>
#include <signal.h>
#include <unistd.h>

#include "lcd_driver.h"

#define STEP_MS     300

static volatile sig_atomic_t running = 1;

static void on_sigint(int sig)
{
	(void)sig;
	running = 0;
}

/*
 * text'i 1. satırda sağdan girip soldan çıkacak şekilde kaydırır.
 * Pencere, metnin önüne ve arkasına 16'şar boşluk eklenmiş haline bakar.
 */
static void scroll_text(const char *text)
{
	int len = (int)strlen(text);
	int pos, i, c;

	for (pos = -LCD_COLUMNS; pos <= len && running; pos++) {
		lcd_set_cursor(1, 1);
		for (i = 0; i < LCD_COLUMNS; i++) {
			c = pos + i;
			lcd_print_char(c >= 0 && c < len ? (uint8_t)text[c] : ' ');
		}
		usleep(STEP_MS * 1000);
	}
}

int main(int argc, char *argv[])
{
	int i;

	printf("Application to print text in scrollable fashion on LCD\n");

	if (argc < 2) {
		printf("usage: %s <text> [text] ...\n", argv[0]);
		return 1;
	}

	if (lcd_init() < 0) {
		printf("Error: LCD init failed\n");
		return 1;
	}

	signal(SIGINT, on_sigint);
	printf("Scrolling %d text(s), press Ctrl-C to stop\n", argc - 1);

	while (running) {
		for (i = 1; i < argc && running; i++) {
			/* 2. satırda hangi yazıda olduğumuzu göster: "1/5" */
			lcd_set_cursor(2, 1);
			lcd_printf("%d/%d            ", i, argc - 1);
			scroll_text(argv[i]);
		}
	}

	lcd_release();
	printf("\nLCD cleared, GPIOs released\n");
	return 0;
}
