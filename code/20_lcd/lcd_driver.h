/*
 * lcd_driver.h — HD44780 uyumlu 16x2 karakter LCD'yi 4 bit modunda GPIO'larla sürer.
 *
 * Kursun Project_Src/Drivers/lcd kütüphanesinin düzeltilmiş hali. Fonksiyon
 * adları kursla aynıdır.
 *
 * Bağlantı (kursla aynı):
 *
 *   BBB pini  GPIO   LCD pini
 *   P8_7       66    4  RS
 *   P8_8       67    5  RW   (GND'ye bağlanması önerilir; program yine de 0 yapar)
 *   P8_9       69    6  E
 *   P8_10      68    11 D4
 *   P8_11      45    12 D5
 *   P8_12      44    13 D6
 *   P8_14      26    14 D7
 *   P9_7      5 V    2  VDD
 *   P9_1      GND    1  VSS
 *   potansiyometre   3  V0 (kontrast)
 */
#ifndef LCD_DRIVER_H_
#define LCD_DRIVER_H_

#include <stdint.h>

#define LCD_ROWS                    2
#define LCD_COLUMNS                 16

/* GPIO numaraları */
#define LCD_GPIO_RS                 66
#define LCD_GPIO_RW                 67
#define LCD_GPIO_EN                 69
#define LCD_GPIO_D4                 68
#define LCD_GPIO_D5                 45
#define LCD_GPIO_D6                 44
#define LCD_GPIO_D7                 26

/* RS: 0 = komut, 1 = karakter (veri) */
#define COMMAND_MODE                0
#define USER_DATA_MODE              1

/*
 * HD44780 komutları (datasheet Table 6). Her komutun üst bitleri komutu,
 * alt bitleri seçenekleri belirler: komut | seçenek | seçenek ...
 */
#define LCD_CMD_CLEAR_DISPLAY               0x01
#define LCD_CMD_RETURN_HOME                 0x02

#define LCD_CMD_ENTRY_MODESET               0x04
#define INC_CURSOR                          (1 << 1)    /* I/D = 1; 0 ise azalt */
#define ACCOMPANY_DISPLAY_SHIFT             (1 << 0)    /* S = 1 */

#define LCD_CMD_DISPLAY_CURSOR_ONOFF_CONTROL 0x08
#define DISPLAY_ON                          (1 << 2)    /* D */
#define CURSOR_ON                           (1 << 1)    /* C */
#define BLINK_CURSOR_ON                     (1 << 0)    /* B */

#define LCD_CMD_CURSOR_DISPLAY_SHIFT_CONTROL 0x10
#define DISPLAY_SHIFT                       (1 << 3)    /* S/C = 1; 0 ise imleç */
#define SHIFT_TO_RIGHT                      (1 << 2)    /* R/L = 1; 0 ise sola */

#define LCD_CMD_FUNCTION_SET                0x20
#define DATA_LEN_8                          (1 << 4)    /* DL = 1; 0 ise 4 bit */
#define DISPLAY_2_LINES                     (1 << 3)    /* N = 1 */
#define MATRIX_5_X_10                       (1 << 2)    /* F = 1; 0 ise 5x8 */

#define LCD_CMD_SET_CGRAM_ADDRESS           0x40
#define LCD_CMD_SET_DDRAM_ADDRESS           0x80

/* 2 satır modunda satırların DDRAM başlangıç adresleri */
#define DDRAM_FIRST_LINE_BASE_ADDR          0x00
#define DDRAM_SECOND_LINE_BASE_ADDR         0x40

int lcd_init(void);
void lcd_release(void);
void lcd_send_command(uint8_t command);
void lcd_print_char(uint8_t ascii_value);
void lcd_print_string(const char *message);
void lcd_printf(const char *fmt, ...);
void lcd_set_cursor(uint8_t row, uint8_t column);
void lcd_clear(void);
void lcd_load_cgram(const uint8_t tab[], uint8_t charnum);

#endif /* LCD_DRIVER_H_ */
