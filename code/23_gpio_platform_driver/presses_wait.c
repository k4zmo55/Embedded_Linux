/*
 * presses_wait.c — bbb-gpio-demo sürücüsünün "presses" dosyasını poll() ile
 * bekler; butona her basışta yeni sayıyı yazar.
 *
 * Bölüm 17'deki button_counter_7seg.c'nin yaptığının aynısı, ama bu kez kesmeyi
 * sürücü yakalıyor ve debounce'u sürücü yapıyor; program sadece uyanıyor.
 *
 * Derleme: make test
 * Kullanım: ./presses_wait        (Ctrl-C ile dur)
 */
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <poll.h>
#include <unistd.h>

#define PRESSES "/sys/bus/platform/devices/bbb-gpio-demo/presses"

/* Dosyayı baştan okur; okunan sayıyı döner. Okuma olayı da temizler. */
static int read_presses(int fd)
{
	char buf[16];
	ssize_t n;

	lseek(fd, 0, SEEK_SET);
	n = read(fd, buf, sizeof(buf) - 1);
	if (n <= 0)
		return -1;
	buf[n] = '\0';
	return atoi(buf);
}

int main(void)
{
	struct pollfd pfd;
	int fd;

	fd = open(PRESSES, O_RDONLY);
	if (fd < 0) {
		perror(PRESSES);
		return 1;
	}

	/* sysfs_notify'ı beklemeden önce dosya bir kez okunmalı. */
	printf("presses = %d, waiting for the button...\n", read_presses(fd));

	for (;;) {
		pfd.fd = fd;
		pfd.events = POLLPRI | POLLERR;
		pfd.revents = 0;

		if (poll(&pfd, 1, -1) < 0) {
			perror("poll");
			break;
		}
		printf("presses = %d\n", read_presses(fd));
		fflush(stdout);
	}

	close(fd);
	return 0;
}
