// SPDX-License-Identifier: GPL-2.0
/*
 * hello.c — İlk kernel modülü: yüklenince ve çıkarılınca kernel log'una yazar.
 *
 * Parametreler:
 *   name  : selamlanacak isim (sadece yüklerken verilir)
 *   count : selamın kaç kez yazılacağı (1-10); çalışırken de değiştirilebilir
 *
 * Derleme: make            (bkz. Makefile)
 * Kartta:  insmod hello.ko name=Mehmet count=3
 *          dmesg | tail
 *          rmmod hello
 */
#define pr_fmt(fmt) KBUILD_MODNAME ": " fmt     /* her mesajın başına "hello: " */

#include <linux/init.h>
#include <linux/module.h>
#include <linux/moduleparam.h>
#include <linux/utsname.h>

static char *name = "BeagleBone";
module_param(name, charp, 0444);                /* /sys/module/hello/parameters/name: salt okunur */
MODULE_PARM_DESC(name, "Name to greet");

static int count = 1;
module_param(count, int, 0644);                 /* root çalışırken değiştirebilir */
MODULE_PARM_DESC(count, "How many times to greet (1-10)");

/* insmod sırasında bir kez çalışır. 0 dışı dönüş, modülün yüklenmesini iptal eder. */
static int __init hello_init(void)
{
	int i;

	if (count < 1 || count > 10) {
		pr_err("count must be 1-10, got %d\n", count);
		return -EINVAL;
	}

	for (i = 0; i < count; i++)
		pr_info("Hello %s! (%d/%d)\n", name, i + 1, count);

	pr_info("running on Linux %s (%s)\n", utsname()->release, utsname()->machine);
	return 0;
}

/* rmmod sırasında çalışır; init'te alınan her şey burada bırakılır. */
static void __exit hello_exit(void)
{
	pr_info("Goodbye %s, count was %d\n", name, count);
}

module_init(hello_init);
module_exit(hello_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Embedded Linux kitabı");
MODULE_DESCRIPTION("First kernel module: hello with parameters");
