/*
 * lcd_driver.c — HD44780 uyumlu 16x2 karakter LCD'yi 4 bit modunda GPIO'larla sürer.
 *
 * Kursun Project_Src/Drivers/lcd/lcd_driver.c dosyasının düzeltilmiş hali:
 *  - Açılışta datasheet'teki 4 bit başlatma dizisi (Figure 24: 0x3, 0x3, 0x3,
 *    0x2) uygulanır. Kurs doğrudan 0x28 gönderiyordu; LCD henüz 8 bit
 *    modundayken bu, nibble'ların kaymasına yol açar.
 *  - Her komuttan sonra datasheet'teki çalışma süresi kadar beklenir
 *    (temizle/başa dön 1.52 ms, diğerleri 37 µs).
 *  - lcd_print_string() boş string'te string'in dışını okumaz.
 *  - lcd_printf() tampon taşırmaz (vsnprintf).
 *  - lcd_load_cgram() CGRAM adresini kendisi ayarlar.
 *  - GPIO'lar export edilir, hatalar kontrol edilir.
 */
#include <stdio.h>
#include <stdarg.h>
#include <unistd.h>

#include "gpio_driver.h"
#include "lcd_driver.h"

static const uint32_t lcd_gpios[] = {
	LCD_GPIO_RS, LCD_GPIO_RW, LCD_GPIO_EN,
	LCD_GPIO_D4, LCD_GPIO_D5, LCD_GPIO_D6, LCD_GPIO_D7,
};
#define LCD_GPIO_COUNT      (sizeof(lcd_gpios) / sizeof(lcd_gpios[0]))

/* Datasheet Table 6: 270 kHz'te en fazla 37 µs ve 1.52 ms; pay bırakıyoruz. */
#define CMD_WAIT_US         50
#define CLEAR_WAIT_US       2000

/*
 * D4-D7'ye 4 biti koyar ve E'de bir darbe üretir. LCD, E'nin düşen kenarında
 * okur. Datasheet en az 230-450 ns'lik bir E darbesi ister; sysfs'e bir
 * yazma bundan çok daha uzun sürdüğü için ayrıca beklemeye gerek yoktur.
 */
static void write_nibble(uint8_t nibble)
{
	gpio_write_value(LCD_GPIO_D4, (nibble >> 0) & 1);
	gpio_write_value(LCD_GPIO_D5, (nibble >> 1) & 1);
	gpio_write_value(LCD_GPIO_D6, (nibble >> 2) & 1);
	gpio_write_value(LCD_GPIO_D7, (nibble >> 3) & 1);

	gpio_write_value(LCD_GPIO_EN, 1);
	gpio_write_value(LCD_GPIO_EN, 0);
}

/* Bir baytı önce yüksek, sonra düşük 4 bit olarak gönderir. rs: komut/veri */
static void write_byte(uint8_t value, uint8_t rs)
{
	gpio_write_value(LCD_GPIO_RS, rs);
	write_nibble(value >> 4);
	write_nibble(value & 0x0F);
}

void lcd_send_command(uint8_t command)
{
	write_byte(command, COMMAND_MODE);

	if (command == LCD_CMD_CLEAR_DISPLAY || command == LCD_CMD_RETURN_HOME)
		usleep(CLEAR_WAIT_US);
	else
		usleep(CMD_WAIT_US);
}

void lcd_print_char(uint8_t ascii_value)
{
	write_byte(ascii_value, USER_DATA_MODE);
	usleep(CMD_WAIT_US);
}

void lcd_print_string(const char *message)
{
	while (*message != '\0')
		lcd_print_char((uint8_t)*message++);
}

/*
 * printf gibi yazar. Ekrana sığmayan kısım kesilir; '\n'de durur;
 * yazdırılamayan karakterler atlanır.
 */
void lcd_printf(const char *fmt, ...)
{
	char text[LCD_ROWS * LCD_COLUMNS + 1];
	va_list args;
	int i;

	va_start(args, fmt);
	vsnprintf(text, sizeof(text), fmt, args);
	va_end(args);

	for (i = 0; text[i] != '\0' && text[i] != '\n'; i++)
		if (text[i] >= 0x20 && text[i] < 0x7F)
			lcd_print_char((uint8_t)text[i]);
}

/* row: 1-2, column: 1-16 */
void lcd_set_cursor(uint8_t row, uint8_t column)
{
	uint8_t base = row == 2 ? DDRAM_SECOND_LINE_BASE_ADDR : DDRAM_FIRST_LINE_BASE_ADDR;

	if (row < 1 || row > LCD_ROWS || column < 1)
		return;

	/* 16. sütunun ötesi DDRAM'de vardır (satır başına 40 karakter), sadece görünmez. */
	lcd_send_command(LCD_CMD_SET_DDRAM_ADDRESS | (base + column - 1));
}

void lcd_clear(void)
{
	lcd_send_command(LCD_CMD_CLEAR_DISPLAY);
}

/*
 * charnum kadar özel karakteri (her biri 8 satır = 8 bayt) CGRAM'e yükler.
 * Karakterler sonra 0x08-0x0F kodlarıyla yazdırılır (0x00-0x07 ile de olur,
 * ama 0x00 C string'lerinde sonu belirtir).
 */
void lcd_load_cgram(const uint8_t tab[], uint8_t charnum)
{
	int i;

	if (charnum > 8)
		charnum = 8;

	lcd_send_command(LCD_CMD_SET_CGRAM_ADDRESS);    /* CGRAM adresi 0 */
	for (i = 0; i < charnum * 8; i++)
		lcd_print_char(tab[i]);

	lcd_send_command(LCD_CMD_SET_DDRAM_ADDRESS);    /* yazmaya DDRAM'den devam */
}

/*
 * GPIO'ları hazırlar ve LCD'yi datasheet'teki 4 bit başlatma dizisiyle
 * (Figure 24) başlatır. Başarılıysa 0, değilse -1 döner.
 */
int lcd_init(void)
{
	unsigned int i;

	for (i = 0; i < LCD_GPIO_COUNT; i++) {
		/* Zaten export edilmişse hata verir; bu sorun değil. */
		gpio_export(lcd_gpios[i]);
		if (gpio_configure_dir(lcd_gpios[i], GPIO_DIR_OUT) < 0 ||
		    gpio_write_value(lcd_gpios[i], 0) < 0) {
			printf("GPIO %u could not be configured as output\n", lcd_gpios[i]);
			return -1;
		}
	}

	/* RW = 0: sadece yazıyoruz. LCD hiçbir zaman veri hatlarını sürmez. */
	gpio_write_value(LCD_GPIO_RW, 0);
	gpio_write_value(LCD_GPIO_RS, COMMAND_MODE);

	/* Besleme geldikten sonra en az 40 ms (VCC 2.7 V) / 15 ms (4.5 V) */
	usleep(50 * 1000);

	/*
	 * LCD açılışta 8 bit modundadır; ama program önceden yarım kalmışsa 4 bit
	 * modunda ve bir nibble'ın ortasında da olabilir. Üç kez "8 bit" demek
	 * her durumda LCD'yi bilinen 8 bit durumuna getirir.
	 */
	write_nibble(0x3);
	usleep(4500);           /* > 4.1 ms */
	write_nibble(0x3);
	usleep(150);            /* > 100 µs */
	write_nibble(0x3);
	usleep(CMD_WAIT_US);

	write_nibble(0x2);      /* artık 4 bit */
	usleep(CMD_WAIT_US);

	/* Bundan sonra her komut iki nibble. Satır sayısı ve font sadece burada ayarlanabilir. */
	lcd_send_command(LCD_CMD_FUNCTION_SET | DISPLAY_2_LINES);              /* 0x28 */
	lcd_send_command(LCD_CMD_DISPLAY_CURSOR_ONOFF_CONTROL);                /* ekran kapalı */
	lcd_clear();
	lcd_send_command(LCD_CMD_ENTRY_MODESET | INC_CURSOR);                  /* 0x06 */
	lcd_send_command(LCD_CMD_DISPLAY_CURSOR_ONOFF_CONTROL | DISPLAY_ON);   /* 0x0C */
	return 0;
}

/* Ekranı temizler ve GPIO'ları bırakır. */
void lcd_release(void)
{
	unsigned int i;

	lcd_clear();
	for (i = 0; i < LCD_GPIO_COUNT; i++)
		gpio_unexport(lcd_gpios[i]);
}
