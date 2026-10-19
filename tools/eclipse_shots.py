"""Eclipse bölümü için terminal / konsol ekran görüntülerini üretir.

Kullanım: python tools/eclipse_shots.py [çıktı klasörü]
"""
from term_shots import (render, t, FG, DIM, GREEN, BLUE, YELLOW, CYAN, RED,
                        MAGENTA, ORANGE)
from term_shots import V, set_default_out

CC = V("build.cross_compile")
GCC_VER = V("build.gcc_version")
LINARO_REL = V("build.linaro_release")
TC_DIR = V("build.toolchain_dir")
PRJ = V("eclipse.project")
USER = V("eclipse.target_user")
BOARD_IP = V("network.board_ip")
set_default_out("images/eclipse")


def host(cmd, path="~"):
    return [("mehmet@ubuntu", GREEN), (":", FG), (path, BLUE), ("$ ", FG), (cmd, FG)]


def note(text, color=FG, ann=""):
    return [(text, color), (ann, MAGENTA)] if ann else [(text, color)]


# 1) Toolchain kontrolü
render("01_toolchain_check.png", "mehmet@ubuntu: ~", [
    host(f"which {CC}gcc"),
    note(f"/home/mehmet/bbb/{TC_DIR}/bin/{CC}gcc", CYAN, ""),
    host(f"{CC}gcc --version | head -1"),
    t(f"{CC}gcc (Linaro GCC {LINARO_REL}) {GCC_VER}"),
    note("", FG, ""),
    note(f"   Eclipse → Cross GCC → Path: /home/mehmet/bbb/{TC_DIR}/bin", DIM, ""),
    note(f"                        Prefix: {CC}", DIM, "      <-- sondaki '-' dahil"),
])

# 2) Eclipse derleme konsolu
render("02_build_console.png", f"Eclipse — Console: CDT Build Console [{PRJ}]", [
    t(f"16:42:07 **** Build of configuration Debug for project {PRJ} ****", DIM),
    t("make all"),
    t(f"Building file: ../src/{PRJ}.c"),
    t("Invoking: Cross GCC Compiler"),
    note(f"{CC}gcc -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF\"src/{PRJ}.d\" -MT\"src/{PRJ}.o\"", ORANGE, ""),
    t(f"    -o \"src/{PRJ}.o\" \"../src/{PRJ}.c\"", ORANGE),
    t(f"Finished building: ../src/{PRJ}.c"),
    t(""),
    t(f"Building target: {PRJ}"),
    t("Invoking: Cross GCC Linker"),
    note(f"{CC}gcc  -o \"{PRJ}\"  ./src/{PRJ}.o", ORANGE, "      <-- cross derleyici çağrılıyor"),
    t(f"Finished building target: {PRJ}"),
    t(""),
    note("16:42:08 Build Finished. 0 errors, 0 warnings. (took 512ms)", GREEN, ""),
])

# 3) Çıktının ARM olduğunu doğrulama
render("03_file_check.png", f"mehmet@ubuntu: ~/eclipse-workspace/{PRJ}", [
    host("ls Debug", f"~/eclipse-workspace/{PRJ}"),
    t(f"{PRJ}  makefile  objects.mk  sources.mk  src", CYAN),
    host(f"file Debug/{PRJ}", f"~/eclipse-workspace/{PRJ}"),
    note(f"Debug/{PRJ}: ELF 32-bit LSB executable, ARM, EABI5 version 1 (SYSV),", CYAN, ""),
    note("dynamically linked, interpreter /lib/ld-linux-armhf.so.3, with debug_info", CYAN, "  <-- ARM"),
    host(f"./Debug/{PRJ}", f"~/eclipse-workspace/{PRJ}"),
    note(f"bash: ./Debug/{PRJ}: cannot execute binary file: Exec format error", RED, "  <-- PC'de çalışmaz"),
])

# 4) Uzak çalıştırma
render("04_remote_run.png", f"Eclipse — Console: {PRJ} [C/C++ Remote Application]", [
    note(f"{USER}@{BOARD_IP}:~$ echo $PWD'>'", DIM, ""),
    t(f"/home/{USER}>"),
    note(f"{USER}@{BOARD_IP}:~$ chmod 755 /home/{USER}/{PRJ};/home/{USER}/{PRJ};exit", DIM,
         "  <-- Eclipse'in gönderdiği komut"),
    t("logout"),
    note("Merhaba BeagleBone! (Eclipse'ten uzaktan çalıştırıldı)", GREEN, ""),
    t("Kernel: Linux beaglebone 5.10.168-ti-r71 armv7l", CYAN),
])

# 5) SSH ile elle çalıştırma (alternatif)
render("05_manual_scp.png", f"mehmet@ubuntu: ~/eclipse-workspace/{PRJ}", [
    host(f"scp Debug/{PRJ} {USER}@{BOARD_IP}:~/", f"~/eclipse-workspace/{PRJ}"),
    t(f"{PRJ}                                   100%   14KB   1.1MB/s   00:00"),
    host(f"ssh {USER}@{BOARD_IP} ./{PRJ}", f"~/eclipse-workspace/{PRJ}"),
    t("Merhaba BeagleBone! (Eclipse'ten uzaktan çalıştırıldı)", GREEN),
    t("Kernel: Linux beaglebone 5.10.168-ti-r71 armv7l", CYAN),
])

NOIDE = "~/code/14_no_ide"
USB_IP = V("rootfs.usb_board_ip")
SYSROOT = f"/home/mehmet/bbb/{TC_DIR}/arm-linux-gnueabihf/libc"

# 7) IDE'siz: make + scp + ssh
render("07_make_run.png", f"mehmet@ubuntu: {NOIDE}", [
    host("make", NOIDE),
    t(f"{CC}gcc -Wall -O0 -g -c -o hello_bbb.o hello_bbb.c", ORANGE),
    t(f"{CC}gcc  -o hello_bbb hello_bbb.o", ORANGE),
    host("make run", NOIDE),
    t(f"scp hello_bbb debian@{USB_IP}:./"),
    t("hello_bbb                                     100%   14KB   1.2MB/s   00:00"),
    t(f"ssh debian@{USB_IP} ./hello_bbb"),
    note("Merhaba BeagleBone! (make + scp ile gönderildi)", GREEN, ""),
    t("Kernel: Linux beaglebone 5.10.168-ti-r71 armv7l", CYAN),
    t("1+2+3+4+5 = 15", GREEN),
    host("make run BOARD=root@" + BOARD_IP, NOIDE),
    note(f"scp hello_bbb root@{BOARD_IP}:./", FG, "        <-- kart adresini komut satırından değiştir"),
])

# 8) gdbserver ile uzaktan hata ayıklama
render("08_gdbserver.png", "BBB (ssh) + mehmet@ubuntu (gdb-multiarch)", [
    t("--- BBB ---", MAGENTA),
    [("debian@beaglebone", GREEN), (":~$ ", FG), ("gdbserver :2345 ./hello_bbb", FG)],
    t("Process ./hello_bbb created; pid = 1873"),
    note("Listening on port 2345", CYAN, "                          <-- host'un bağlanmasını bekliyor"),
    t("--- host ---", MAGENTA),
    host("gdb-multiarch -q hello_bbb", NOIDE),
    t("Reading symbols from hello_bbb..."),
    note(f"(gdb) set sysroot {SYSROOT}", FG, ""),
    note(f"(gdb) target remote {USB_IP}:2345", FG, ""),
    note(f"Remote debugging using {USB_IP}:2345", CYAN, ""),
    t("(gdb) break main"),
    t("Breakpoint 1 at 0x4005a2: file hello_bbb.c, line 15."),
    t("(gdb) continue"),
    t("Breakpoint 1, main () at hello_bbb.c:15"),
    t('15          printf("Merhaba BeagleBone! (make + scp ile gönderildi)\\n");', YELLOW),
    t("(gdb) break 21 if i == 4"),
    t("(gdb) continue"),
    t("Breakpoint 2, main () at hello_bbb.c:21"),
    t("(gdb) print sum"),
    note("$1 = 6", GREEN, "                                           <-- 1+2+3"),
    t("(gdb) continue"),
    note("[Inferior 1 (process 1873) exited normally]", GREEN, "      <-- program kartta bitti"),
])

# 6) Hatalar
render("06_errors.png", "Eclipse — Problems / Console (temsili hatalar)", [
    note(f"Program \"{CC}gcc\" not found in PATH", RED, "              <-- Cross GCC Path yanlış"),
    t(""),
    note("make: *** No rule to make target 'all'.  Stop.", RED, "          <-- proje 'Makefile project' seçilmiş"),
    t(""),
    note(f"./{PRJ}: /lib/arm-linux-gnueabihf/libc.so.6: version `GLIBC_2.34' not found", RED, ""),
    note("", FG, "    <-- toolchain'in glibc'si karttakinden yeni: aynı/eski toolchain ya da -static"),
    t(""),
    note(f"-sh: ./{PRJ}: not found", RED, "                             <-- BusyBox rootfs'te /lib yok: -static"),
    t(""),
    note("Error during file upload. Failure", RED, "                    <-- kartta SFTP sunucusu yok"),
    t(""),
    note("Remote 'g' packet reply is too long (expected 260 bytes, got 328 bytes)", RED, ""),
    note("", FG, "    <-- host'un x86 gdb'si kullanıldı: gdb-multiarch"),
    t(""),
    note(f"{USB_IP}:2345: Connection timed out.", RED, "           <-- kartta gdbserver çalışmıyor"),
])
