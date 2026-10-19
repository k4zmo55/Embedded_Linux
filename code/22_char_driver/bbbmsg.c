// SPDX-License-Identifier: GPL-2.0
/*
 * bbbmsg.c — Basit bir karakter aygıt sürücüsü: /dev/bbbmsg
 *
 * Aygıta yazılan metni kernel belleğinde (en fazla 256 bayt) saklar, okununca
 * geri verir. Donanım yoktur; amaç karakter sürücüsünün parçalarını
 * göstermektir:
 *   - aygıt numarası (major/minor) almak ve cdev ile kaydolmak
 *   - class + device ile /dev/bbbmsg düğümünü kendiliğinden oluşturmak
 *   - file_operations: open, release, read, write, llseek, unlocked_ioctl
 *   - kullanıcı belleğiyle veri alışverişi: copy_to_user / copy_from_user
 *   - eşzamanlı erişime karşı mutex
 *
 * Kartta:
 *   insmod bbbmsg.ko
 *   echo "Merhaba" > /dev/bbbmsg
 *   cat /dev/bbbmsg
 */
#define pr_fmt(fmt) KBUILD_MODNAME ": " fmt

#include <linux/init.h>
#include <linux/module.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/device.h>
#include <linux/mutex.h>
#include <linux/uaccess.h>
#include <linux/version.h>

#include "bbbmsg.h"

#define DEV_NAME            "bbbmsg"
#define BUF_SIZE            256

static dev_t devno;                 /* major + minor */
static struct cdev bbbmsg_cdev;
static struct class *bbbmsg_class;

static char msg[BUF_SIZE];          /* saklanan mesaj */
static size_t msg_len;              /* mesajın uzunluğu */
static DEFINE_MUTEX(msg_lock);      /* msg ve msg_len'i korur */

static int bbbmsg_open(struct inode *inode, struct file *file)
{
	pr_info("open (major %d, minor %d)\n", imajor(inode), iminor(inode));
	return 0;
}

static int bbbmsg_release(struct inode *inode, struct file *file)
{
	pr_info("release\n");
	return 0;
}

/*
 * Kullanıcının tamponuna en fazla count bayt kopyalar. *ppos, dosyada
 * nerede olduğumuzu tutar; mesajın sonuna gelince 0 döneriz ve cat durur.
 */
static ssize_t bbbmsg_read(struct file *file, char __user *ubuf,
			   size_t count, loff_t *ppos)
{
	ssize_t ret;

	if (mutex_lock_interruptible(&msg_lock))
		return -ERESTARTSYS;

	if (*ppos >= msg_len) {
		ret = 0;                        /* dosya sonu (EOF) */
		goto out;
	}
	if (count > msg_len - *ppos)
		count = msg_len - *ppos;

	if (copy_to_user(ubuf, msg + *ppos, count)) {
		ret = -EFAULT;
		goto out;
	}
	*ppos += count;
	ret = count;
out:
	mutex_unlock(&msg_lock);
	return ret;
}

/*
 * Kullanıcının verisini *ppos konumundan itibaren mesaja yazar. Yazılan yerin
 * sonu mesajın yeni sonu olur: "echo a > /dev/bbbmsg" mesajı değiştirir,
 * "echo b >> /dev/bbbmsg" (O_APPEND) sona ekler.
 */
static ssize_t bbbmsg_write(struct file *file, const char __user *ubuf,
			    size_t count, loff_t *ppos)
{
	ssize_t ret;

	if (mutex_lock_interruptible(&msg_lock))
		return -ERESTARTSYS;

	/* Karakter aygıtlarında O_APPEND'i sürücü uygular. */
	if (file->f_flags & O_APPEND)
		*ppos = msg_len;

	if (*ppos >= BUF_SIZE) {
		ret = -ENOSPC;                  /* yer kalmadı */
		goto out;
	}
	if (count > BUF_SIZE - *ppos)
		count = BUF_SIZE - *ppos;

	if (copy_from_user(msg + *ppos, ubuf, count)) {
		ret = -EFAULT;
		goto out;
	}
	*ppos += count;
	msg_len = *ppos;
	ret = count;
	pr_info("wrote %zu bytes, message is now %zu bytes\n", count, msg_len);
out:
	mutex_unlock(&msg_lock);
	return ret;
}

/* lseek: SEEK_END mesajın sonunu, en büyük konum tampon boyutunu kullanır. */
static loff_t bbbmsg_llseek(struct file *file, loff_t offset, int whence)
{
	return generic_file_llseek_size(file, offset, whence, BUF_SIZE, msg_len);
}

static long bbbmsg_ioctl(struct file *file, unsigned int cmd, unsigned long arg)
{
	int len;

	switch (cmd) {
	case BBBMSG_CLEAR:
		mutex_lock(&msg_lock);
		msg_len = 0;
		mutex_unlock(&msg_lock);
		pr_info("message cleared\n");
		return 0;

	case BBBMSG_GET_LEN:
		mutex_lock(&msg_lock);
		len = msg_len;
		mutex_unlock(&msg_lock);
		/* arg, kullanıcı alanındaki bir int'in adresi */
		return put_user(len, (int __user *)arg);

	default:
		return -ENOTTY;                 /* bu sürücünün komutu değil */
	}
}

static const struct file_operations bbbmsg_fops = {
	.owner          = THIS_MODULE,
	.open           = bbbmsg_open,
	.release        = bbbmsg_release,
	.read           = bbbmsg_read,
	.write          = bbbmsg_write,
	.llseek         = bbbmsg_llseek,
	.unlocked_ioctl = bbbmsg_ioctl,
};

static int __init bbbmsg_init(void)
{
	struct device *dev;
	int ret;

	/* 1) Boş bir major numara ve 1 minor numara iste. */
	ret = alloc_chrdev_region(&devno, 0, 1, DEV_NAME);
	if (ret)
		return ret;

	/* 2) Bu numarayı file_operations'a bağla. */
	cdev_init(&bbbmsg_cdev, &bbbmsg_fops);
	bbbmsg_cdev.owner = THIS_MODULE;
	ret = cdev_add(&bbbmsg_cdev, devno, 1);
	if (ret)
		goto err_region;

	/* 3) /sys/class/bbbmsg/bbbmsg oluştur; devtmpfs/mdev /dev/bbbmsg'yi açar. */
#if LINUX_VERSION_CODE >= KERNEL_VERSION(6, 4, 0)
	bbbmsg_class = class_create(DEV_NAME);
#else
	bbbmsg_class = class_create(THIS_MODULE, DEV_NAME);
#endif
	if (IS_ERR(bbbmsg_class)) {
		ret = PTR_ERR(bbbmsg_class);
		goto err_cdev;
	}

	dev = device_create(bbbmsg_class, NULL, devno, NULL, DEV_NAME);
	if (IS_ERR(dev)) {
		ret = PTR_ERR(dev);
		goto err_class;
	}

	pr_info("registered /dev/%s (major %d, minor %d)\n",
		DEV_NAME, MAJOR(devno), MINOR(devno));
	return 0;

	/* Hata olursa o ana kadar alınanları ters sırada bırak. */
err_class:
	class_destroy(bbbmsg_class);
err_cdev:
	cdev_del(&bbbmsg_cdev);
err_region:
	unregister_chrdev_region(devno, 1);
	return ret;
}

static void __exit bbbmsg_exit(void)
{
	device_destroy(bbbmsg_class, devno);
	class_destroy(bbbmsg_class);
	cdev_del(&bbbmsg_cdev);
	unregister_chrdev_region(devno, 1);
	pr_info("unregistered\n");
}

module_init(bbbmsg_init);
module_exit(bbbmsg_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Embedded Linux kitabı");
MODULE_DESCRIPTION("Simple character device that stores a message");
