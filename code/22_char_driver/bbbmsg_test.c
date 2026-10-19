/*
 * bbbmsg_test.c — /dev/bbbmsg sürücüsünü kullanıcı alanından dener.
 *
 * Mesajı yazar, ioctl ile uzunluğunu sorar, baştan okur, ioctl ile siler ve
 * tekrar okur.
 *
 * Derleme (code/22_char_driver klasöründe): make test
 * Kullanım: ./bbbmsg_test "mesaj"      (root olarak)
 */
#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>

#include "bbbmsg.h"

#define DEV_PATH    "/dev/bbbmsg"

int main(int argc, char *argv[])
{
	char buf[300];
	ssize_t n;
	int fd, len;

	if (argc != 2) {
		printf("usage: %s <message>\n", argv[0]);
		return 1;
	}

	fd = open(DEV_PATH, O_RDWR);
	if (fd < 0) {
		perror(DEV_PATH);
		return 1;
	}

	n = write(fd, argv[1], strlen(argv[1]));
	if (n < 0) {
		perror("write");
		goto out;
	}
	printf("write: %zd bytes\n", n);

	if (ioctl(fd, BBBMSG_GET_LEN, &len) < 0) {
		perror("ioctl BBBMSG_GET_LEN");
		goto out;
	}
	printf("ioctl GET_LEN: %d\n", len);

	/* Yazdıktan sonra konum mesajın sonunda; okumak için başa dön. */
	lseek(fd, 0, SEEK_SET);
	n = read(fd, buf, sizeof(buf) - 1);
	if (n < 0) {
		perror("read");
		goto out;
	}
	buf[n] = '\0';
	printf("read: \"%s\" (%zd bytes)\n", buf, n);

	if (ioctl(fd, BBBMSG_CLEAR) < 0) {
		perror("ioctl BBBMSG_CLEAR");
		goto out;
	}
	lseek(fd, 0, SEEK_SET);
	n = read(fd, buf, sizeof(buf) - 1);
	printf("after CLEAR, read: %zd bytes\n", n);

out:
	close(fd);
	return 0;
}
