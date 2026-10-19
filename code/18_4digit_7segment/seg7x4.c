/*
 * seg7x4.c — 4 haneli 7-segment göstergeyi çoğullama (multiplexing) ile sürer.
 *
 * Dört hanenin a-g ve dp segmentleri göstergenin içinde birbirine bağlıdır;
 * her hanenin sadece ortak (COM) pini ayrıdır. Aynı anda tek bir hane açılır,
 * ona ait rakam yazılır, kısa bir süre beklenir ve sıradaki haneye geçilir.
 * Tarama yeterince hızlıysa göz dört haneyi aynı anda yanıyor görür.
 *
 * Kursun 4_digit_7seg.c programından farklar:
 *  - Her yazmada /sys/class/gpio/gpioN/value dosyası açılıp kapatılmaz; dosyalar
 *    başta bir kez açılır, sonra sadece pwrite() yapılır. Sadece değişen
 *    segmentler yazılır.
 *  - Segmentler tüm haneler kapalıyken değiştirilir; bir hanenin rakamı
 *    komşu haneye "gölge" olarak düşmez.
 *  - Hane seçme mantığı gösterge türüne (ve transistör kullanımına) göre seçilir.
 */
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>

#include "gpio_driver.h"
#include "seg7.h"
#include "seg7x4.h"

/*
 *                     segment yanar   hane açılır
 *  ortak anot              0          1 (anot 3.3 V)
 *  ortak anot + PNP        0          0 (PNP tabanı 0 V ile iletir)
 *  ortak katot             1          0 (katot 0 V)
 *  ortak katot + NPN       1          1 (NPN tabanı 3.3 V ile iletir)
 */
#ifdef COMMON_ANODE
#define SEGMENT_ON          LOW_VALUE
#else
#define SEGMENT_ON          HIGH_VALUE
#endif

#ifdef DIGIT_TRANSISTOR
#define DIGIT_ON            SEGMENT_ON
#else
#define DIGIT_ON            (!SEGMENT_ON)
#endif

#define SEGMENT_OFF         (!SEGMENT_ON)
#define DIGIT_OFF           (!DIGIT_ON)

/* Bir hanenin yanık kaldığı süre. 4 hane x 2.5 ms = 10 ms, yani ~100 Hz tarama. */
#define DIGIT_ON_TIME_US    2500

/* Segment sırası: a, b, c, d, e, f, g, dp */
static const uint32_t seg_gpio[8] = { 66, 67, 69, 45, 44, 26, 46, 68 };
/* Hane sırası: soldan sağa */
static const uint32_t digit_gpio[SEG7X4_DIGITS] = { 48, 49, 112, 115 };

static int seg_fd[8];
static int digit_fd[SEG7X4_DIGITS];
static int seg_state[8];        /* son yazılan değer; -1 = bilinmiyor */

/* Açık value dosyasına 0/1 yazar. pwrite() dosya konumunu değiştirmez. */
static int put(int fd, int value)
{
	return pwrite(fd, value ? "1" : "0", 1, 0) == 1 ? 0 : -1;
}

/* GPIO'yu export eder, çıkış yapar, value dosyasını yazmak için açar. */
static int open_output(uint32_t gpio, int initial)
{
	char path[SOME_BYTES];
	int fd;

	/* Zaten export edilmişse hata verir; bu sorun değil. */
	gpio_export(gpio);

	if (gpio_configure_dir(gpio, GPIO_DIR_OUT) < 0) {
		printf("GPIO %u could not be configured as output\n", gpio);
		return -1;
	}

	snprintf(path, sizeof(path), SYS_GPIO_PATH "/gpio%u/value", gpio);
	fd = open(path, O_WRONLY);
	if (fd < 0) {
		perror(path);
		return -1;
	}

	if (put(fd, initial) < 0) {
		perror(path);
		close(fd);
		return -1;
	}
	return fd;
}

/* Bütün GPIO'ları hazırlar; haneler kapalı başlar. Başarılıysa 0, değilse -1. */
int seg7x4_init(void)
{
	int i;

	for (i = 0; i < SEG7X4_DIGITS; i++)
		digit_fd[i] = -1;
	for (i = 0; i < 8; i++)
		seg_fd[i] = -1;

	for (i = 0; i < SEG7X4_DIGITS; i++) {
		digit_fd[i] = open_output(digit_gpio[i], DIGIT_OFF);
		if (digit_fd[i] < 0)
			return -1;
	}

	for (i = 0; i < 8; i++) {
		seg_fd[i] = open_output(seg_gpio[i], SEGMENT_OFF);
		if (seg_fd[i] < 0)
			return -1;
		seg_state[i] = SEGMENT_OFF;
	}
	return 0;
}

/* Segmentleri desene göre ayarlar; sadece değişenleri yazar. */
static int set_segments(uint8_t bits)
{
	int i, v;

	for (i = 0; i < 8; i++) {
		v = (bits >> i) & 1 ? SEGMENT_ON : SEGMENT_OFF;
		if (v == seg_state[i])
			continue;
		if (put(seg_fd[i], v) < 0)
			return -1;
		seg_state[i] = v;
	}
	return 0;
}

/*
 * Dört haneyi bir kez tarar (~10 ms). Sürekli çağrılmalıdır; çağrılmazsa
 * gösterge söner.
 *   digits : soldan sağa 4 rakam (0-9; başka değer = boş hane)
 *   dp_mask: bit 0 = 1. hanenin noktası ... bit 3 = 4. hanenin noktası
 */
int seg7x4_refresh(const uint8_t digits[SEG7X4_DIGITS], uint8_t dp_mask)
{
	uint8_t bits;
	int i;

	for (i = 0; i < SEG7X4_DIGITS; i++) {
		bits = seg7_pattern(digits[i]);
		if (dp_mask & (1 << i))
			bits |= 1 << 7;

		/* Bütün haneler kapalıyken segmentleri değiştir, sonra haneyi aç. */
		if (set_segments(bits) < 0 || put(digit_fd[i], DIGIT_ON) < 0)
			return -1;

		usleep(DIGIT_ON_TIME_US);

		if (put(digit_fd[i], DIGIT_OFF) < 0)
			return -1;
	}
	return 0;
}

/* Göstergeyi söndürür, dosyaları kapatır ve GPIO'ları bırakır.
 * seg7x4_init() yarıda kalmış olsa da çağrılabilir. */
void seg7x4_release(void)
{
	int i;

	for (i = 0; i < SEG7X4_DIGITS; i++) {
		if (digit_fd[i] >= 0) {
			put(digit_fd[i], DIGIT_OFF);
			close(digit_fd[i]);
			digit_fd[i] = -1;
		}
		gpio_unexport(digit_gpio[i]);
	}

	for (i = 0; i < 8; i++) {
		if (seg_fd[i] >= 0) {
			put(seg_fd[i], SEGMENT_OFF);
			close(seg_fd[i]);
			seg_fd[i] = -1;
		}
		gpio_unexport(seg_gpio[i]);
	}
}
