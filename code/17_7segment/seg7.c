/*
 * seg7.c — Tek haneli 7-segment göstergeyi GPIO'larla sürer.
 *
 * Kursun counter_7seg.c dosyasındaki Write_number_to_7segdisplay() ve
 * initialize_all_gpios() fonksiyonlarının yerine geçer:
 *  - Her rakam için 7 satırlık switch-case yerine tek bir tablo kullanılır.
 *  - GPIO'lar export edilir (kursun kodu önceden elle export edilmiş olmasını
 *    bekliyordu) ve hatalar kontrol edilir.
 *  - Segment mantığı (ortak katot / anot) tek bir yerden seçilir.
 */
#include <stdio.h>

#include "gpio_driver.h"
#include "seg7.h"

#ifdef COMMON_ANODE
#define SEGMENT_ON          LOW_VALUE
#define SEGMENT_OFF         HIGH_VALUE
#else
#define SEGMENT_ON          HIGH_VALUE
#define SEGMENT_OFF         LOW_VALUE
#endif

/* Segment sırası: a, b, c, d, e, f, g */
static const uint32_t seg_gpio[7] = { 66, 67, 69, 45, 44, 26, 46 };
#define DP_GPIO             68

/*
 * Her rakamın yanacak segmentleri: bit 0 = a, bit 1 = b, ... bit 6 = g
 *
 *      a
 *    f   b
 *      g
 *    e   c
 *      d   dp
 */
static const uint8_t digit_segments[11] = {
	0x3F,   /* 0: a b c d e f   */
	0x06,   /* 1:   b c         */
	0x5B,   /* 2: a b   d e   g */
	0x4F,   /* 3: a b c d     g */
	0x66,   /* 4:   b c     f g */
	0x6D,   /* 5: a   c d   f g */
	0x7D,   /* 6: a   c d e f g */
	0x07,   /* 7: a b c         */
	0x7F,   /* 8: a b c d e f g */
	0x6F,   /* 9: a b c d   f g */
	0x00,   /* SEG7_BLANK       */
};

/* GPIO'yu export edip çıkış yapar ve segmenti söndürür. */
static int setup_output(uint32_t gpio)
{
	/* Zaten export edilmişse hata verir; bu sorun değil. */
	gpio_export(gpio);

	if (gpio_configure_dir(gpio, GPIO_DIR_OUT) < 0) {
		printf("GPIO %u could not be configured as output\n", gpio);
		return -1;
	}
	return gpio_write_value(gpio, SEGMENT_OFF);
}

/* Bütün segment GPIO'larını hazırlar. Başarılıysa 0, değilse -1 döner. */
int seg7_init(void)
{
	int i;

	for (i = 0; i < 7; i++)
		if (setup_output(seg_gpio[i]) < 0)
			return -1;

	return setup_output(DP_GPIO);
}

/* Rakamın segment deseni (bit 0 = a ... bit 6 = g); 0-9 dışı değerler için 0. */
uint8_t seg7_pattern(uint8_t digit)
{
	return digit_segments[digit <= 9 ? digit : SEG7_BLANK];
}

/* 0-9 arası rakamı gösterir; başka bir değer göstergeyi söndürür. */
void seg7_show(uint8_t digit)
{
	uint8_t bits = seg7_pattern(digit);
	int i;

	for (i = 0; i < 7; i++)
		gpio_write_value(seg_gpio[i], (bits >> i) & 1 ? SEGMENT_ON : SEGMENT_OFF);
}

void seg7_dp(uint8_t on)
{
	gpio_write_value(DP_GPIO, on ? SEGMENT_ON : SEGMENT_OFF);
}

/* Göstergeyi söndürür ve GPIO'ları bırakır. */
void seg7_release(void)
{
	int i;

	seg7_show(SEG7_BLANK);
	seg7_dp(0);

	for (i = 0; i < 7; i++)
		gpio_unexport(seg_gpio[i]);
	gpio_unexport(DP_GPIO);
}
