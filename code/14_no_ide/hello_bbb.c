/*
 * hello_bbb.c — Bölüm 14'teki programın IDE'siz sürümü (Bölüm 14.8).
 *
 * Derleme:  make            (ya da make STATIC=1)
 * Kartta:   make run
 */
#include <stdio.h>
#include <sys/utsname.h>

int main(void)
{
	struct utsname u;
	int i, sum = 0;

	printf("Merhaba BeagleBone! (make + scp ile gönderildi)\n");
	if (uname(&u) == 0)
		printf("Kernel: %s %s %s %s\n", u.sysname, u.nodename, u.release, u.machine);

	/* gdb ile adım adım izlemek için küçük bir döngü (Bölüm 14.8.4) */
	for (i = 1; i <= 5; i++)
		sum += i;
	printf("1+2+3+4+5 = %d\n", sum);
	return 0;
}
