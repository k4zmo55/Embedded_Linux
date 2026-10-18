"""TFTP ile boot notu için terminal ekran görüntülerini üretir.

Kullanım: python tools/tftp_boot_shots.py images/tftp_boot
"""
from term_shots import (render, t, FG, DIM, GREEN, BLUE, CYAN, MAGENTA, RED, YELLOW,
                        ORANGE)
from term_shots import V, set_default_out

PB_UBOOT = V("prebuilt.uboot_version")
KVER = V("prebuilt.kernel_version")
HOST_IP = V("network.host_ip")
BOARD_IP = V("network.board_ip")
NETMASK = V("network.netmask")
IFACE = V("network.host_iface")
TFTP_DIR = V("network.tftp_dir")
set_default_out("images/tftp_boot")

TITLE = "mehmet@ubuntu: ~"


def host(cmd):
    return [("mehmet@ubuntu", GREEN), (":", FG), ("~", BLUE), ("$ ", FG), (cmd, FG)]


def note(text, color=FG, ann=""):
    return [(text, color), (ann, MAGENTA)] if ann else [(text, color)]


# 1) Paket listesini güncelleme
render("01_apt_update.png", TITLE, [
    host("sudo apt-get update"),
    t("[sudo] password for mehmet:", DIM),
    t("Hit:1 http://tr.archive.ubuntu.com/ubuntu jammy InRelease"),
    t("Get:2 http://tr.archive.ubuntu.com/ubuntu jammy-updates InRelease [128 kB]"),
    t("Get:3 http://security.ubuntu.com/ubuntu jammy-security InRelease [129 kB]"),
    t("Fetched 257 kB in 1s (215 kB/s)"),
    t("Reading package lists... Done"),
    host("sudo apt upgrade"),
    t("Reading package lists... Done"),
    t("Building dependency tree... Done"),
    t("Calculating upgrade... Done"),
    t("0 upgraded, 0 newly installed, 0 to remove and 0 not upgraded."),
])

# 2) tftpd-hpa kurulumu
render("02_install_tftpd.png", TITLE, [
    host("sudo apt-get install tftpd-hpa"),
    t("Reading package lists... Done"),
    t("The following NEW packages will be installed:"),
    t("  tftpd-hpa", CYAN),
    t("Unpacking tftpd-hpa (5.2+20150808-1.2build2) ..."),
    t("Setting up tftpd-hpa (5.2+20150808-1.2build2) ..."),
    note("Created symlink ... tftpd-hpa.service", FG, "   <-- servis kuruldu"),
    host("which in.tftpd"),
    note("/usr/sbin/in.tftpd", CYAN, "                    <-- TFTP sunucu programı"),
])

# 3) Ayar dosyası
render("03_tftpd_config.png", TITLE, [
    host("sudo vim /etc/default/tftpd-hpa"),
    note("   (dosyayı düzenle, :wq ile kaydet)", DIM),
    host("cat /etc/default/tftpd-hpa"),
    t("# /etc/default/tftpd-hpa", DIM),
    t(""),
    note('TFTP_USERNAME="tftp"', CYAN, "                 <-- servis bu kullanıcıyla çalışır"),
    note(f'TFTP_DIRECTORY="{TFTP_DIR}"', CYAN, "   <-- paylaşılan klasör"),
    note('TFTP_ADDRESS=":69"', CYAN, "                   <-- tüm arayüzler, UDP 69"),
    note('TFTP_OPTIONS="--create --secure"', CYAN, "     <-- izinler (aşağıda)"),
])

# 4) tftpboot klasörü
render("04_tftpboot_dir.png", TITLE, [
    host(f"sudo mkdir -p {TFTP_DIR}"),
    host(f"sudo chown tftp:tftp {TFTP_DIR}"),
    host(f"sudo chmod -R 777 {TFTP_DIR}"),
    host(f"ls -ld {TFTP_DIR}"),
    note(f"drwxrwxrwx 2 tftp tftp 4096 Eki 18 11:20 {TFTP_DIR}", FG,
         "  <-- sahibi tftp, herkes yazabilir"),
])

# 5) Servisi başlatma ve kontrol
render("05_tftpd_start.png", TITLE, [
    host("sudo systemctl start tftpd-hpa"),
    host("systemctl status tftpd-hpa"),
    t("* tftpd-hpa.service - LSB: HPA's tftp server", GREEN),
    t("     Loaded: loaded (/etc/init.d/tftpd-hpa; generated)"),
    note("     Active: active (running) since Sat 2026-10-18 11:21:04 +03", GREEN,
         "  <-- çalışıyor"),
    t("   Main PID: 2741 (in.tftpd)"),
    t("     CGroup: /system.slice/tftpd-hpa.service"),
    t("             `-2741 /usr/sbin/in.tftpd --listen --user tftp --address :69", DIM),
    t(f"                    --create --secure {TFTP_DIR}", DIM),
    host("sudo ss -ulpn | grep :69"),
    note('UNCONN 0 0   0.0.0.0:69   0.0.0.0:*   users:(("in.tftpd",pid=2741))', ORANGE,
         "  <-- UDP 69 dinleniyor"),
])

MINICOM = "mehmet@ubuntu: ~ — minicom -D /dev/ttyUSB0 -b 115200"


def ub(cmd):
    return [("U-Boot# ", YELLOW), (cmd, FG)]


def sh(cmd):
    return [("/ # ", GREEN), (cmd, FG)]


# 6) Host'un Ethernet arayüzüne IP verme ve dosyaları kopyalama
render("06_host_ip.png", TITLE, [
    host("ip -br a"),
    t("lo        UNKNOWN  127.0.0.1/8 ::1/128"),
    note(f"{IFACE}    UP       fe80::a00:27ff:fe4e:66a1/64", FG,
         "      <-- BBB'ye giden kablo, IPv4 yok"),
    t("wlp2s0    UP       192.168.1.34/24"),
    host(f"sudo ip addr add {HOST_IP}/24 dev {IFACE}"),
    host(f"ip -br a show {IFACE}"),
    note(f"{IFACE}    UP       {HOST_IP}/24 fe80::a00:27ff:fe4e:66a1/64", GREEN,
         "  <-- hazır"),
    host(f"sudo cp uImage am335x-boneblack.dtb initramfs {TFTP_DIR}/"),
    host(f"ls -l {TFTP_DIR}"),
    t("-rw-r--r-- 1 root root   24884 Eki 18 11:40 am335x-boneblack.dtb"),
    t("-rw-r--r-- 1 root root 1867312 Eki 18 11:40 initramfs"),
    t("-rw-r--r-- 1 root root 4380760 Eki 18 11:40 uImage"),
])

# 7) SD kart BOOT bölümü
render("07_sd_boot_part.png", TITLE, [
    host("lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINT /dev/sdb"),
    t("NAME     SIZE FSTYPE LABEL  MOUNTPOINT", DIM),
    t("sdb      7.4G"),
    note("|-sdb1    96M vfat   BOOT   /media/mehmet/BOOT", FG, "     <-- 1. bölüm (FAT)"),
    t("`-sdb2   7.3G ext4   ROOTFS /media/mehmet/ROOTFS"),
    host("cp MLO u-boot.img uEnv.txt /media/mehmet/BOOT/"),
    host("ls -l /media/mehmet/BOOT"),
    note("-rw-r--r-- 1 mehmet mehmet  92720 Eki 18 11:45 MLO", FG,
         "        <-- adı tam olarak MLO"),
    t("-rw-r--r-- 1 mehmet mehmet 403524 Eki 18 11:45 u-boot.img"),
    t("-rw-r--r-- 1 mehmet mehmet    412 Eki 18 11:45 uEnv.txt"),
    host("sync && sudo umount /media/mehmet/BOOT /media/mehmet/ROOTFS"),
])

# 8) U-Boot'ta ağ ayarları ve ping
render("08_uboot_net.png", MINICOM, [
    t(f"U-Boot {PB_UBOOT} (Oct 16 2026 - 10:12:41)", FG),
    t("Net:   cpsw, usb_ether"),
    note("Hit any key to stop autoboot:  0", FG, "    <-- herhangi bir tuşa bas"),
    ub(f"setenv ipaddr {BOARD_IP}"),
    ub(f"setenv serverip {HOST_IP}"),
    ub("setenv ethact cpsw"),
    ub("printenv ipaddr serverip ethact"),
    t(f"ipaddr={BOARD_IP}", CYAN),
    t(f"serverip={HOST_IP}", CYAN),
    t("ethact=cpsw", CYAN),
    ub(f"ping {HOST_IP}"),
    t("link up on port 0, speed 100, full duplex"),
    t("Using cpsw device"),
    note(f"host {HOST_IP} is alive", GREEN, "                 <-- bağlantı tamam"),
])

# 9) tftpboot ile dosyaları çekme
render("09_tftpboot.png", MINICOM, [
    ub("tftpboot 0x82000000 uImage"),
    t("link up on port 0, speed 100, full duplex"),
    t("Using cpsw device"),
    t(f"TFTP from server {HOST_IP}; our IP address is {BOARD_IP}"),
    t("Filename 'uImage'."),
    t("Load address: 0x82000000"),
    t("Loading: #################################################################", BLUE),
    t("         ##########################################", BLUE),
    t("         2.8 MiB/s"),
    t("done"),
    note("Bytes transferred = 4380760 (42d858 hex)", GREEN, "  <-- ls -l ile aynı"),
    ub("tftpboot 0x88000000 am335x-boneblack.dtb"),
    t("..."),
    t("Bytes transferred = 24884 (6134 hex)", GREEN),
    ub("tftpboot 0x88080000 initramfs"),
    t("..."),
    t("Bytes transferred = 1867312 (1c7e30 hex)", GREEN),
])

# 10) bootm
render("10_bootm.png", MINICOM, [
    ub("setenv bootargs console=ttyO0,115200 root=/dev/ram0 rw initrd=0x88080000"),
    ub("bootm 0x82000000 0x88080000 0x88000000"),
    t("## Booting kernel from Legacy Image at 82000000 ..."),
    t(f"   Image Name:   Linux-{KVER}"),
    t("   Verifying Checksum ... OK"),
    t("## Loading init Ramdisk from Legacy Image at 88080000 ..."),
    t("   Image Name:   initramfs"),
    t("   Verifying Checksum ... OK"),
    t("## Flattened Device Tree blob at 88000000"),
    t("   Loading Device Tree to 8fff6000, end 8ffff133 ... OK"),
    t(""),
    t("Starting kernel ...", GREEN),
    t("..."),
    t("Please press Enter to activate this console."),
    sh(""),
])

# 11) uEnv.txt ile otomatik TFTP boot
render("11_uenv_auto.png", MINICOM, [
    t(f"U-Boot {PB_UBOOT} (Oct 16 2026 - 10:12:41)", FG),
    t("Hit any key to stop autoboot:  0"),
    t("mmc0 is current device"),
    note("reading uEnv.txt", FG, "                           <-- SD kart, 1. bölüm"),
    t("412 bytes read in 4 ms (100.6 KiB/s)"),
    t("Importing environment from mmc ..."),
    note("Running uenvcmd ...", FG, "                        <-- bizim komutumuz"),
    t("*** Booting From Network ***", ORANGE),
    t("Using cpsw device"),
    t(f"TFTP from server {HOST_IP}; our IP address is {BOARD_IP}"),
    t("Filename 'uImage'."),
    t("Bytes transferred = 4380760 (42d858 hex)", GREEN),
    t("Filename 'am335x-boneblack.dtb'."),
    t("Bytes transferred = 24884 (6134 hex)", GREEN),
    t("Filename 'initramfs'."),
    t("Bytes transferred = 1867312 (1c7e30 hex)", GREEN),
    t("## Booting kernel from Legacy Image at 82000000 ..."),
    t("Starting kernel ...", GREEN),
])

# 12) Linux açıldıktan sonra tftp ile dosya çekme
render("12_linux_tftp.png", "root@beaglebone (initramfs) — seri konsol", [
    sh(f"ifconfig eth0 {BOARD_IP} netmask {NETMASK} up"),
    t("libphy: 4a101000.mdio:00 - Link is Up - 100/Full", DIM),
    sh(f"ping -c 2 {HOST_IP}"),
    t(f"64 bytes from {HOST_IP}: seq=0 ttl=64 time=0.612 ms"),
    t(f"64 bytes from {HOST_IP}: seq=1 ttl=64 time=0.398 ms"),
    sh("cd /tmp"),
    note(f"/tmp # tftp -g -r helloworld {HOST_IP}", FG, "   <-- -g: get, -r: uzak dosya adı"),
    [("/tmp # ", GREEN), ("ls -l helloworld", FG)],
    t("-rw-r--r--    1 root     root            27 Jan  1 00:03 helloworld"),
    [("/tmp # ", GREEN), ("cat helloworld", FG)],
    t("Merhaba BeagleBone, TFTP!", CYAN),
])

# 13) Sık görülen hatalar
render("13_hatalar.png", MINICOM + " (temsili hatalar)", [
    ub("tftpboot 0x82000000 uImage"),
    note("*** ERROR: `serverip' not set", RED, "              <-- setenv serverip ..."),
    ub("tftpboot 0x82000000 uImage"),
    note("Using usb_ether device", RED, "                     <-- setenv ethact cpsw"),
    ub("tftpboot 0x82000000 uImage"),
    t(f"TFTP from server {HOST_IP}; our IP address is {BOARD_IP}"),
    t("Loading: T T T T T T T T T T", RED),
    note("Retry count exceeded; starting again", RED, "       <-- IP/kablo/firewall/VM ağı"),
    ub("tftpboot 0x82000000 uimage"),
    note("TFTP error: 'File not found' (1)", RED, "           <-- ad/klasör yanlış (büyük-küçük harf!)"),
    ub(f"ping {HOST_IP}"),
    note(f"ping failed; host {HOST_IP} is not alive", RED, " <-- host IP'si yok / kablo"),
])

# 14) Host'ta uEnv.txt hazırlama
render("14_uenv_host.png", TITLE, [
    host("cat uEnv.txt"),
    t("console=ttyO0,115200n8", CYAN),
    t(f"serverip={HOST_IP}", CYAN),
    t(f"ipaddr={BOARD_IP}", CYAN),
    t("loadaddr=0x82000000", CYAN),
    t("fdtaddr=0x88000000", CYAN),
    t("initrdaddr=0x88080000", CYAN),
    t('loadfromtftp=echo "*** Booting From Network ***";tftpboot ${loadaddr} uImage;', CYAN),
    t("  tftpboot ${fdtaddr} am335x-boneblack.dtb;tftpboot ${initrdaddr} initramfs", CYAN),
    t("linuxbootargs=setenv bootargs console=${console} root=/dev/ram0 rw initrd=${initrdaddr}", CYAN),
    t("uenvcmd=setenv autoload no;run loadfromtftp;run linuxbootargs;", CYAN),
    t("  bootm ${loadaddr} ${initrdaddr} ${fdtaddr}", CYAN),
    note("  (uzun satırlar burada okunsun diye bölündü; dosyada tek satır)", DIM),
    host(f"sudo cp uEnv.txt {TFTP_DIR}/"),
])

# 15) uEnv.txt'yi kartın içinden TFTP ile SD karta yazma
render("15_uenv_tftp_to_sd.png", "root@beaglebone (initramfs) — seri konsol", [
    sh(f"ifconfig eth0 {BOARD_IP} netmask {NETMASK} up"),
    note("/ # mount /dev/mmcblk0p1 /mnt", FG, "              <-- SD kart, 1. bölüm (BOOT)"),
    sh("cd /mnt"),
    [("/mnt # ", GREEN), ("ls", FG)],
    t("MLO         u-boot.img"),
    note(f"/mnt # tftp -g -r uEnv.txt {HOST_IP}", FG, "   <-- host'tan SD karta"),
    [("/mnt # ", GREEN), ("ls", FG)],
    t("MLO         u-boot.img  uEnv.txt", FG),
    [("/mnt # ", GREEN), ("cd / && sync && umount /mnt", FG)],
    note("/ # reboot", FG, "                                 <-- S2'ye basılı tut"),
])

# 16) Linux'ta bootargs doğrulama
render("16_cmdline.png", "root@beaglebone (initramfs) — seri konsol", [
    sh("cat /proc/cmdline"),
    note("console=ttyO0,115200n8 root=/dev/ram0 rw initrd=0x88080000", CYAN,
         "  <-- linuxbootargs çalışmış"),
])

# 17) Genel uEnv.txt: eMMC ve SD başarısız, TFTP ile açılış
render("17_generic_fallback.png", MINICOM + " (SD kart takılı değil)", [
    t(f"U-Boot {PB_UBOOT} (Oct 16 2026 - 10:12:41)", FG),
    note("Card did not respond to voltage select!", DIM, "     <-- mmcdev 0 (SD) yok"),
    note("SD/MMC found on device 1", FG, "                    <-- eMMC'ye geçti"),
    t("reading uEnv.txt"),
    t("Running uenvcmd ..."),
    t("[1/4] eMMC deneniyor ...", ORANGE),
    note("** Unable to read file uImage **", RED, "            <-- eMMC'de imaj yok"),
    t("[2/4] SD kart deneniyor ...", ORANGE),
    note("Card did not respond to voltage select!", RED, "     <-- SD yok"),
    t("[3/4] TFTP (initramfs) deneniyor ...", ORANGE),
    t("Using cpsw device"),
    t(f"TFTP from server {HOST_IP}; our IP address is {BOARD_IP}"),
    t("Bytes transferred = 4380760 (42d858 hex)", GREEN),
    t("Bytes transferred = 24884 (6134 hex)", GREEN),
    t("Bytes transferred = 1867312 (1c7e30 hex)", GREEN),
    t("## Booting kernel from Legacy Image at 82000000 ..."),
    note("Starting kernel ...", GREEN, "                         <-- TFTP'den açıldı"),
])
