/* SPDX-License-Identifier: GPL-2.0 */
/*
 * bbbmsg.h — bbbmsg sürücüsünün ioctl komutları.
 *
 * Bu dosya hem sürücüde (kernel) hem de kullanıcı programında kullanılır;
 * bu yüzden sadece <linux/ioctl.h>'ye bağlıdır.
 */
#ifndef BBBMSG_H_
#define BBBMSG_H_

#include <linux/ioctl.h>

#define BBBMSG_IOC_MAGIC    'b'

/* Mesajı siler. Argüman yok. */
#define BBBMSG_CLEAR        _IO(BBBMSG_IOC_MAGIC, 0)
/* Mesajın uzunluğunu (bayt) argümandaki int'e yazar. */
#define BBBMSG_GET_LEN      _IOR(BBBMSG_IOC_MAGIC, 1, int)

#endif /* BBBMSG_H_ */
