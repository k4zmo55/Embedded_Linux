# bbbmsg sürücüsü (kernel modülü) ve onu deneyen kullanıcı programı.
#
#   make          sürücüyü derler (bbbmsg.ko)
#   make test     kullanıcı programını derler (bbbmsg_test, statik)
#   make clean    çıktıları siler
#
# Ayrıntılar: Bölüm 21.4 (Makefile'ın iki kez okunması, KDIR).

ifneq ($(KERNELRELEASE),)

obj-m := bbbmsg.o

else

KDIR ?= $(HOME)/bbb/linux
ARCH ?= arm
CROSS_COMPILE ?= arm-linux-gnueabihf-

KMAKE = $(MAKE) -C $(KDIR) M=$(CURDIR) ARCH=$(ARCH) CROSS_COMPILE=$(CROSS_COMPILE)

all:
	$(KMAKE) modules

# BusyBox rootfs'te kütüphane olmayabilir; statik derliyoruz (Bölüm 14.5).
test: bbbmsg_test.c bbbmsg.h
	$(CROSS_COMPILE)gcc -Wall -static -o bbbmsg_test bbbmsg_test.c

clean:
	$(KMAKE) clean
	rm -f bbbmsg_test

.PHONY: all test clean

endif
