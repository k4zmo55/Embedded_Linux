# bbb_mpu6050 I2C/IIO sürücüsü (kernel modülü).
#
#   make          sürücüyü derler (bbb_mpu6050.ko)
#   make install INSTALL_MOD_PATH=~/bbb/rootfs
#                 rootfs'e kurar; modprobe IIO çekirdek modülünü de yükleyebilsin
#   make clean    çıktıları siler
#
# Ayrıntılar: Bölüm 21.4 (Makefile'ın iki kez okunması, KDIR).

ifneq ($(KERNELRELEASE),)

obj-m := bbb_mpu6050.o

else

KDIR ?= $(HOME)/bbb/linux
ARCH ?= arm
CROSS_COMPILE ?= arm-linux-gnueabihf-

KMAKE = $(MAKE) -C $(KDIR) M=$(CURDIR) ARCH=$(ARCH) CROSS_COMPILE=$(CROSS_COMPILE)

all:
	$(KMAKE) modules

install:
	$(KMAKE) INSTALL_MOD_PATH=$(INSTALL_MOD_PATH) modules_install

clean:
	$(KMAKE) clean

.PHONY: all install clean

endif
