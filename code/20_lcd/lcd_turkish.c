/*
 * lcd_turkish.c — CGRAM'e Türkçe harfler yükleyip UTF-8 metni LCD'de gösterir.
 *
 * HD44780'in karakter ROM'unda (CGROM) ç, ğ, ı, ş, İ yoktur. CGRAM'e en fazla
 * 8 özel karakter tanımlanabilir; burada küçük ç ğ ı ö ş ü ile büyük İ ve Ş
 * tanımlanır. Ç, Ğ, Ö, Ü için yer kalmadığından C, G, O, U gösterilir.
 *
 * Derleme (code/ klasöründe):
 *   arm-linux-gnueabihf-gcc -Wall -Ilib -I20_lcd -o lcd_turkish \
 *       20_lcd/lcd_turkish.c 20_lcd/lcd_driver.c lib/gpio_driver.c
 * Kullanım: ./lcd_turkish "1. satır" ["2. satır"]
 *           ./lcd_turkish "Gömülü Linux" "Işık ve şimşek"
 */
#include <stdio.h>
#include <stdint.h>

#include "lcd_driver.h"

/*
 * 5x8 karakter desenleri: her bayt bir satır (üstten alta), bit 4 en soldaki
 * nokta. 8. satır normalde imleç satırıdır; imleç kapalıyken kullanılabilir
 * (ç ve ş'nin çengeli için).
 */
static const uint8_t turkish_glyphs[8 * 8] = {
	/* 0: ç */ 0x00, 0x00, 0x0E, 0x10, 0x10, 0x0E, 0x04, 0x0C,
	/* 1: ğ */ 0x11, 0x0E, 0x0F, 0x11, 0x0F, 0x01, 0x0E, 0x00,
	/* 2: ı */ 0x00, 0x00, 0x0C, 0x04, 0x04, 0x04, 0x0E, 0x00,
	/* 3: ö */ 0x0A, 0x00, 0x0E, 0x11, 0x11, 0x11, 0x0E, 0x00,
	/* 4: ş */ 0x00, 0x0E, 0x10, 0x0E, 0x01, 0x1E, 0x04, 0x0C,
	/* 5: ü */ 0x0A, 0x00, 0x11, 0x11, 0x11, 0x13, 0x0D, 0x00,
	/* 6: İ */ 0x04, 0x00, 0x0E, 0x04, 0x04, 0x04, 0x0E, 0x00,
	/* 7: Ş */ 0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E, 0x04,
};

/* Unicode kod noktası -> LCD karakter kodu. CGRAM karakterleri 0x08-0x0F ile yazılır. */
static const struct {
	uint16_t cp;
	uint8_t code;
} turkish_map[] = {
	{ 0x00E7, 0x08 },   /* ç */
	{ 0x011F, 0x09 },   /* ğ */
	{ 0x0131, 0x0A },   /* ı */
	{ 0x00F6, 0x0B },   /* ö */
	{ 0x015F, 0x0C },   /* ş */
	{ 0x00FC, 0x0D },   /* ü */
	{ 0x0130, 0x0E },   /* İ */
	{ 0x015E, 0x0F },   /* Ş */
	{ 0x00C7, 'C' },    /* Ç: CGRAM'de yer yok */
	{ 0x011E, 'G' },    /* Ğ */
	{ 0x00D6, 'O' },    /* Ö */
	{ 0x00DC, 'U' },    /* Ü */
};

static uint8_t lcd_code(uint16_t cp)
{
	unsigned int i;

	if (cp >= 0x20 && cp < 0x7F)
		return (uint8_t)cp;

	for (i = 0; i < sizeof(turkish_map) / sizeof(turkish_map[0]); i++)
		if (turkish_map[i].cp == cp)
			return turkish_map[i].code;
	return '?';
}

/*
 * UTF-8 metni çözer ve en fazla 16 karakter yazar. Türkçe harfler UTF-8'de
 * 2 bayttır: 110xxxxx 10xxxxxx.
 */
static void print_utf8(const char *s)
{
	const uint8_t *p = (const uint8_t *)s;
	uint16_t cp;
	int n = 0;

	while (*p && n < LCD_COLUMNS) {
		if (*p < 0x80) {
			cp = *p++;
		} else if ((p[0] & 0xE0) == 0xC0 && (p[1] & 0xC0) == 0x80) {
			cp = ((p[0] & 0x1F) << 6) | (p[1] & 0x3F);
			p += 2;
		} else {
			/* 3-4 baytlık karakterleri atla */
			cp = '?';
			p++;
			while ((*p & 0xC0) == 0x80)
				p++;
		}
		lcd_print_char(lcd_code(cp));
		n++;
	}
}

int main(int argc, char *argv[])
{
	if (argc < 2) {
		printf("usage: %s <line 1> [line 2]\n", argv[0]);
		return 1;
	}

	if (lcd_init() < 0) {
		printf("Error: LCD init failed\n");
		return 1;
	}

	lcd_load_cgram(turkish_glyphs, 8);

	lcd_set_cursor(1, 1);
	print_utf8(argv[1]);
	if (argc > 2) {
		lcd_set_cursor(2, 1);
		print_utf8(argv[2]);
	}

	/* GPIO'ları bırakmıyoruz: LCD yazıyı göstermeye devam eder. */
	return 0;
}
