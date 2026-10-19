/*
 * seg7.h — Tek haneli 7-segment göstergeyi GPIO'larla sürer.
 *
 * Bağlantı (kursla aynı):
 *
 *   P8 pini   GPIO   segment
 *   P8_7       66      a
 *   P8_8       67      b
 *   P8_9       69      c
 *   P8_10      68      dp (nokta)
 *   P8_11      45      d
 *   P8_12      44      e
 *   P8_14      26      f
 *   P8_16      46      g
 *
 * Varsayılan ortak katot (common cathode) göstergedir: segment 1 ile yanar.
 * Ortak anot (common anode) gösterge için -DCOMMON_ANODE ile derle.
 */
#ifndef SEG7_H_
#define SEG7_H_

#include <stdint.h>

#define SEG7_BLANK          10      /* seg7_show(SEG7_BLANK): hepsi sönük */

int seg7_init(void);
void seg7_show(uint8_t digit);
void seg7_dp(uint8_t on);
void seg7_release(void);

#endif /* SEG7_H_ */
