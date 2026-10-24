"""
sysinfo.py - System information commands for BanOnaS.

Owner: Member 6 (User/System + QA)

Shows simulated machine information (OS name, CPU, memory...) mixed
with live values from the other managers (current user, memory usage,
process count, uptime since boot).
"""

import platform
from datetime import datetime

from config import OS_FULL_NAME, OS_NAME, VERSION, ARCHITECTURE, CPU_NAME, TAGLINE
import ui


class SystemInfo:
    def __init__(self, users, memory, processes, filesystem):
        self.users = users
        self.memory = memory
        self.processes = processes
        self.filesystem = filesystem
        self.boot_time = datetime.now()

    def uptime(self):
        seconds = int((datetime.now() - self.boot_time).total_seconds())
        hours, rest = divmod(seconds, 3600)
        minutes, seconds = divmod(rest, 60)
        return f"{hours}h {minutes}m {seconds}s"

    # ---------- shell commands ----------
    def cmd_systeminfo(self, args):
        user = self.users.current_user
        print()
        ui.header("SYSTEM INFORMATION")
        print()
        rows = [
            ("OS Name", OS_FULL_NAME),
            ("Version", VERSION),
            ("Architecture", ARCHITECTURE),
            ("CPU", CPU_NAME),
            ("Memory", f"{self.memory.total_mb} MB total, {self.memory.free_mb} MB free"),
            ("Processes", f"{len(self.processes.table)} running"),
            ("User", f"{user.username} ({user.role})"),
            ("Boot Time", self.boot_time.strftime("%Y-%m-%d %H:%M:%S")),
            ("Uptime", self.uptime()),
            ("Host System", f"{platform.system()} {platform.release()}"),
            ("Python", platform.python_version()),
        ]
        for label, value in rows:
            print(f"{label + ':':<15}{value}")
        print()
        ui.line()

    def cmd_date(self, args):
        print(f"Current Date: {datetime.now().strftime('%A, %B %d, %Y')}")

    def cmd_time(self, args):
        print(f"Current Time: {datetime.now().strftime('%I:%M:%S %p')}")

    def cmd_version(self, args):
        print(f"{OS_FULL_NAME} version {VERSION}")
        print(TAGLINE)

    def cmd_status(self, args):
        """Quick one-screen summary of the whole system."""
        print()
        print(ui.color(f"{OS_NAME} Status", ui.BOLD))
        ui.line("-", 40)
        print(f"User:        {self.users.current_user.username}")
        print(f"Directory:   {self.filesystem.display_path()}")
        print(f"Memory:      {self.memory.used_mb}/{self.memory.total_mb} MB used")
        print(f"Processes:   {len(self.processes.table)}")
        print(f"Uptime:      {self.uptime()}")
        ui.line("-", 40)
        print()
