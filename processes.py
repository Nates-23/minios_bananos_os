"""
processes.py - Simulated process management for BanOnaS.

Owner: Member 4 (Process Management)

How it works
------------
* Every process is a `Process` object with a PID, name, owner, status,
  memory size and start time. All processes live in a "process table"
  (a dictionary: pid -> Process), just like a real OS keeps a table of
  Process Control Blocks (PCBs).
* PIDs are handed out in increasing order and are never reused.
* `run` asks the memory manager for memory first. If there is not
  enough free memory, the process cannot start.
* `kill` removes the process and returns its memory.
* Two system processes (init, bshell) start at boot. They live in the
  kernel's reserved memory and cannot be killed.
* Standard users can only kill their own processes; admin can kill any.

No real Windows programs are started or stopped.
"""

from datetime import datetime

from memory import parse_mb
import ui

# Memory (MB) used by known programs. Unknown programs use DEFAULT_PROGRAM_MB.
PROGRAM_SIZES = {
    "calculator": 32,
    "editor": 64,
    "notepad": 48,
    "terminal": 24,
    "music": 96,
    "browser": 256,
    "game": 192,
}
DEFAULT_PROGRAM_MB = 16


class Process:
    def __init__(self, pid, name, owner, memory_mb, system=False):
        self.pid = pid
        self.name = name
        self.owner = owner
        self.memory_mb = memory_mb
        self.status = "RUNNING"
        self.start_time = datetime.now()
        self.system = system


class ProcessManager:
    def __init__(self, memory, users):
        self.memory = memory
        self.users = users
        self.table = {}
        self.next_pid = 1
        self._boot_system_processes()

    def _boot_system_processes(self):
        # These run inside the kernel's reserved memory (not charged again).
        for name, mb in (("init", 16), ("bshell", 32)):
            self.table[self.next_pid] = Process(self.next_pid, name, "SYSTEM", mb, system=True)
            self.next_pid += 1

    def user_processes(self):
        return [p for p in self.table.values() if not p.system]

    def start(self, name, memory_mb, owner):
        """Create a process. Returns the Process, or None if out of memory."""
        pid = self.next_pid
        if not self.memory.allocate_for_process(pid, memory_mb):
            return None
        self.next_pid += 1
        process = Process(pid, name, owner, memory_mb)
        self.table[pid] = process
        return process

    def terminate(self, pid):
        """Remove a process and return its memory. Returns MB released."""
        self.table.pop(pid)
        return self.memory.release_process(pid)

    def terminate_user_processes(self, username):
        """Called on logout: end every process the user owns."""
        pids = [p.pid for p in self.user_processes() if p.owner == username]
        for pid in pids:
            self.terminate(pid)
        return len(pids)

    # ---------- shell commands ----------
    def cmd_run(self, args):
        if not args or len(args) > 2:
            ui.error("Usage: run <program> [memory_MB]   (example: run calculator)")
            return
        name = args[0].lower()
        if len(args) == 2:
            memory_mb = parse_mb(args[1])
            if memory_mb is None:
                ui.error("Memory size must be a positive whole number of MB.")
                return
        else:
            memory_mb = PROGRAM_SIZES.get(name, DEFAULT_PROGRAM_MB)

        process = self.start(name, memory_mb, self.users.current_user.username)
        if process is None:
            ui.error(
                f"Cannot start '{name}': needs {memory_mb} MB but only "
                f"{self.memory.free_mb} MB is free."
            )
            return
        ui.success("Process started.")
        print()
        print(f"PID:    {process.pid}")
        print(f"Name:   {process.name}")
        print(f"Status: {process.status}")
        print(f"Memory: {process.memory_mb} MB")

    def cmd_process(self, args):
        print()
        print(f"{'PID':<6}{'NAME':<14}{'STATUS':<10}{'MEMORY':>8}  {'OWNER':<10}{'STARTED':<10}")
        ui.line("-", 60)
        for p in self.table.values():
            row = (
                f"{p.pid:<6}{p.name:<14}{p.status:<10}{str(p.memory_mb) + ' MB':>8}  "
                f"{p.owner:<10}{p.start_time.strftime('%H:%M:%S'):<10}"
            )
            print(ui.color(row, ui.GRAY) if p.system else row)
        ui.line("-", 60)
        print(f"Total processes: {len(self.table)}  "
              f"(system: {len(self.table) - len(self.user_processes())}, "
              f"user: {len(self.user_processes())})")
        print()

    def cmd_kill(self, args):
        if len(args) != 1:
            ui.error("Usage: kill <PID>   (example: kill 3)")
            return
        if not args[0].isdigit():
            ui.error("PID must be a number.")
            return
        pid = int(args[0])
        process = self.table.get(pid)
        if process is None:
            ui.error("Process does not exist.")
            return
        if process.system:
            ui.error(f"Access denied. '{process.name}' is a system process and cannot be terminated.")
            return
        user = self.users.current_user
        if process.owner != user.username and not user.is_admin:
            ui.error(f"Access denied. Process {pid} belongs to '{process.owner}'.")
            return
        released = self.terminate(pid)
        ui.success(f"Process {pid} terminated. {released} MB of memory released.")
