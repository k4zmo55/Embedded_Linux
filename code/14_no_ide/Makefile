# hello_bbb — IDE olmadan derleme, karta gönderme ve çalıştırma (Bölüm 14.8).
#
#   make                 ARM için derler (dinamik)
#   make STATIC=1        statik derler (BusyBox rootfs için)
#   make deploy          programı scp ile karta kopyalar
#   make run             kopyalar ve ssh ile kartta çalıştırır
#   make clean           çıktıları siler
#
# Kart adresi komut satırından değiştirilebilir:
#   make run BOARD=root@192.168.27.2

PROG   ?= hello_bbb
SRCS   ?= hello_bbb.c
OBJS    = $(SRCS:.c=.o)

CROSS_COMPILE ?= arm-linux-gnueabihf-
CC      = $(CROSS_COMPILE)gcc
CFLAGS ?= -Wall -O0 -g
LDLIBS ?=

ifeq ($(STATIC),1)
LDFLAGS += -static
endif

BOARD  ?= debian@192.168.7.2
RDIR   ?= .

all: $(PROG)

$(PROG): $(OBJS)
	$(CC) $(LDFLAGS) -o $@ $^ $(LDLIBS)

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

deploy: $(PROG)
	scp $(PROG) $(BOARD):$(RDIR)/

run: deploy
	ssh $(BOARD) $(RDIR)/$(PROG)

clean:
	rm -f $(PROG) $(OBJS)

.PHONY: all deploy run clean
