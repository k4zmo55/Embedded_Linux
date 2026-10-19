// SPDX-License-Identifier: GPL-2.0
/*
 * hello_user.c — hello_lib.ko'nun dışa açtığı hello_lib_add() fonksiyonunu
 * kullanır. hello_lib yüklü değilse insmod "Unknown symbol" hatası verir;
 * modprobe ise önce hello_lib'i kendisi yükler (modules.dep).
 */
#define pr_fmt(fmt) KBUILD_MODNAME ": " fmt

#include <linux/init.h>
#include <linux/module.h>

#include "hello_lib.h"

static int __init hello_user_init(void)
{
	pr_info("2 + 3 = %d\n", hello_lib_add(2, 3));
	return 0;
}

static void __exit hello_user_exit(void)
{
	pr_info("unloaded\n");
}

module_init(hello_user_init);
module_exit(hello_user_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Embedded Linux kitabı");
MODULE_DESCRIPTION("Uses a symbol exported by hello_lib");
