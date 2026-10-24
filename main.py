"""
main.py - Entry point of BanOnaS OS.

Run from Windows Command Prompt:
    python main.py

Boot sequence:
    1. Show the banner and "boot" the subsystems (memory, processes,
       file system, users)
    2. Ask the user to log in
    3. Start the command shell
    4. On 'logout' -> back to step 2.  On 'exit' -> shut down.
"""

import sys
import time

from config import OS_FULL_NAME, VERSION, TAGLINE
from filesystem import FileSystem
from memory import MemoryManager
from processes import ProcessManager
from shell import Shell
from sysinfo import SystemInfo
from users import UserManager
import ui

BANANA = r"""
          _
         //\
        V  \
         \  \_
          \,'.`-.
           |\ `. `.
           ( \  `. `-.                        _,.-:\
            \ \   `.  `-._             __..--' ,-';/
             \ `.   `-.   `-..___..---'   _.--' ,'/
              `. `.    `-._        __..--'    ,' /
                `. `-_     ``--..''       _.-' ,'
                  `-_ `-.___        __,--'   ,'
                     `-.__  `----'''    __.-'
                          `--..____..--'
"""


def show_banner():
    print(ui.color(BANANA, ui.YELLOW))
    ui.line()
    print(ui.color(f"{OS_FULL_NAME.upper()} v{VERSION}".center(ui.WIDTH), ui.BOLD + ui.YELLOW))
    print(TAGLINE.center(ui.WIDTH))
    ui.line()


def boot_step(message):
    """Print a boot message with a short pause (no pause in automated runs)."""
    print(f"  {message:<36}", end="", flush=True)
    if sys.stdout.isatty():
        time.sleep(0.2)
    print(ui.color("[ OK ]", ui.GREEN))


def shutdown(processes):
    print()
    ui.warning(f"Shutting down {OS_FULL_NAME}...")
    count = len(processes.table)
    print(f"  Terminating {count} process(es)... done")
    print("  Saving disk... done")
    print()
    print(ui.color("Goodbye!", ui.BOLD + ui.YELLOW))


def main():
    if not sys.stdin.isatty():
        # Commands are being piped in (e.g. a test script). PowerShell adds an
        # invisible byte-order mark; "utf-8-sig" removes it.
        sys.stdin.reconfigure(encoding="utf-8-sig")
    show_banner()
    print()
    print("Booting system...")
    memory = MemoryManager()
    boot_step(f"Initializing memory ({memory.total_mb} MB)")
    users = UserManager()
    boot_step("Loading user accounts")
    processes = ProcessManager(memory, users)
    boot_step("Starting system processes")
    filesystem = FileSystem()
    boot_step("Mounting virtual disk")
    sysinfo = SystemInfo(users, memory, processes, filesystem)
    shell = Shell(users, filesystem, memory, processes, sysinfo)
    boot_step("Starting command shell")

    while True:
        try:
            logged_in = users.login_screen()
        except (KeyboardInterrupt, EOFError):
            print()
            logged_in = False
        if not logged_in:
            shutdown(processes)
            return

        filesystem.cwd = filesystem.root
        print("Type 'help' to see the available commands.")
        print()
        signal = shell.run()

        if signal == "logout":
            username = users.current_user.username
            ended = processes.terminate_user_processes(username)
            users.logout()
            print()
            ui.info(f"User '{username}' logged out. {ended} process(es) terminated.")
            continue

        shutdown(processes)
        return


if __name__ == "__main__":
    main()
