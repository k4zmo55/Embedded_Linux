// SPDX-License-Identifier: GPL-2.0
/*
 * hello_lib.c — Başka modüllerin kullanması için bir fonksiyon dışa açar
 * (EXPORT_SYMBOL). hello_user.ko bu modüle bağımlıdır.
 */
#define pr_fmt(fmt) KBUILD_MODNAME ": " fmt

#include <linux/init.h>
#include <linux/module.h>

#include "hello_lib.h"

static int calls;

/* İki sayıyı toplar ve kaç kez çağrıldığını sayar. */
int hello_lib_add(int a, int b)
{
	calls++;
	pr_info("hello_lib_add(%d, %d) called, %d call(s) so far\n", a, b, calls);
	return a + b;
}
EXPORT_SYMBOL_GPL(hello_lib_add);

static int __init hello_lib_init(void)
{
	pr_info("loaded, hello_lib_add() is available\n");
	return 0;
}

static void __exit hello_lib_exit(void)
{
	pr_info("unloaded after %d call(s)\n", calls);
}

module_init(hello_lib_init);
module_exit(hello_lib_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Embedded Linux kitabı");
MODULE_DESCRIPTION("Exports a symbol for hello_user");
