# Kernel ağacının dışında (out-of-tree) modül derleme.
#
#   make                  modülleri derler (hello.ko, hello_lib.ko, hello_user.ko)
#   make clean            derleme çıktılarını siler
#   make install INSTALL_MOD_PATH=~/bbb/rootfs
#                         modülleri rootfs'e kurar ve modules.dep'i günceller
#
# Bu dosya iki kez okunur: önce senin "make" komutunla (else kısmı), sonra
# kernel'in derleme sistemi (kbuild) tarafından; o zaman KERNELRELEASE
# tanımlıdır ve sadece obj-m satırı kullanılır.

ifneq ($(KERNELRELEASE),)

obj-m := hello.o hello_lib.o hello_user.o

else

# Bölüm 10'da derlenmiş kernel kaynağı. Modüller tam olarak bu kernel için
# derlenir; kartta da aynı kernel çalışmalıdır.
KDIR ?= $(HOME)/bbb/linux
ARCH ?= arm
CROSS_COMPILE ?= arm-linux-gnueabihf-

KMAKE = $(MAKE) -C $(KDIR) M=$(CURDIR) ARCH=$(ARCH) CROSS_COMPILE=$(CROSS_COMPILE)

all:
	$(KMAKE) modules

clean:
	$(KMAKE) clean

install:
	$(KMAKE) INSTALL_MOD_PATH=$(INSTALL_MOD_PATH) modules_install

endif
