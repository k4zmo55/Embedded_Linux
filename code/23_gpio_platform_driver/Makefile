# bbb-gpio-demo platform sürücüsü (kernel modülü) ve presses_wait programı.
#
#   make          sürücüyü derler (bbb_gpio_demo.ko)
#   make test     kullanıcı programını derler (presses_wait, statik)
#   make clean    çıktıları siler
#
# Ayrıntılar: Bölüm 21.4 (Makefile'ın iki kez okunması, KDIR).
# Device tree dosyaları (am335x-boneblack-gpiodemo.dts, BB-GPIO-DEMO-00A0.dts)
# burada derlenmez; bkz. Bölüm 23.3.

ifneq ($(KERNELRELEASE),)

obj-m := bbb_gpio_demo.o

else

KDIR ?= $(HOME)/bbb/linux
ARCH ?= arm
CROSS_COMPILE ?= arm-linux-gnueabihf-

KMAKE = $(MAKE) -C $(KDIR) M=$(CURDIR) ARCH=$(ARCH) CROSS_COMPILE=$(CROSS_COMPILE)

all:
	$(KMAKE) modules

test: presses_wait.c
	$(CROSS_COMPILE)gcc -Wall -static -o presses_wait presses_wait.c

clean:
	$(KMAKE) clean
	rm -f presses_wait

.PHONY: all test clean

endif
