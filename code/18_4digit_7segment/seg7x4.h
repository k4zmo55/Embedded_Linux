/*
 * seg7x4.h — 4 haneli 7-segment göstergeyi çoğullama (multiplexing) ile sürer.
 *
 * Bağlantı (kursla aynı; gösterge pinleri 12 pinli 5641 tipi için):
 *
 *   Pin     GPIO   gösterge pini         Pin     GPIO   gösterge pini
 *   P8_7     66    11 (a)                P9_15    48    12 (hane 1, en sol)
 *   P8_8     67     7 (b)                P9_23    49     9 (hane 2)
 *   P8_9     69     4 (c)                P9_30   112     8 (hane 3)
 *   P8_11    45     2 (d)                P9_27   115     6 (hane 4, en sağ)
 *   P8_12    44     1 (e)
 *   P8_14    26    10 (f)
 *   P8_16    46     5 (g)
 *   P8_10    68     3 (dp)
 *
 * Derleme seçenekleri:
 *   -DCOMMON_ANODE       ortak anot gösterge (kursun göstergesi). Yoksa ortak katot.
 *   -DDIGIT_TRANSISTOR   haneler transistörle sürülüyor (ortak anotta PNP, ortak
 *                        katotta NPN); hane seçme mantığı terslenir.
 */
#ifndef SEG7X4_H_
#define SEG7X4_H_

#include <stdint.h>

#define SEG7X4_DIGITS       4

int seg7x4_init(void);
int seg7x4_refresh(const uint8_t digits[SEG7X4_DIGITS], uint8_t dp_mask);
void seg7x4_release(void);

#endif /* SEG7X4_H_ */
