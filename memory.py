"""
memory.py - Simulated memory management for BanOnaS.

Owner: Member 5 (Memory Management)

How it works
------------
The machine has TOTAL_MEMORY_MB of "RAM". Memory is tracked in three parts:

    1. Kernel memory   - reserved at boot for the OS (cannot be freed)
    2. Process memory  - each running process owns a block (pid -> MB)
    3. User memory     - memory reserved manually with `allocate`

    used = kernel + process memory + user memory
    free = total - used

Nothing here touches the computer's real RAM. It is bookkeeping only.
"""

from config import TOTAL_MEMORY_MB, KERNEL_MEMORY_MB
import ui


def parse_mb(text):
    """Convert '200' or '200MB' into a positive int, or return None."""
    text = text.strip().upper()
    if text.endswith("MB"):
        text = text[:-2]
    if not text.isdigit():
        return None
    value = int(text)
    return value if value > 0 else None


class MemoryManager:
    def __init__(self, total_mb=TOTAL_MEMORY_MB, kernel_mb=KERNEL_MEMORY_MB):
        self.total_mb = total_mb
        self.kernel_mb = kernel_mb
        self.user_allocated_mb = 0
        self.process_memory = {}  # pid -> MB

    # ---------- calculations ----------
    @property
    def process_mb(self):
        return sum(self.process_memory.values())

    @property
    def used_mb(self):
        return self.kernel_mb + self.process_mb + self.user_allocated_mb

    @property
    def free_mb(self):
        return self.total_mb - self.used_mb

    # ---------- used by the process manager ----------
    def allocate_for_process(self, pid, mb):
        """Reserve memory for a process. Returns False if there is not enough."""
        if mb > self.free_mb:
            return False
        self.process_memory[pid] = mb
        return True

    def release_process(self, pid):
        """Give a terminated process's memory back. Returns MB released."""
        return self.process_memory.pop(pid, 0)

    # ---------- used by the `allocate` / `free` commands ----------
    def allocate(self, mb):
        if mb > self.free_mb:
            return False
        self.user_allocated_mb += mb
        return True

    def free(self, mb):
        if mb > self.user_allocated_mb:
            return False
        self.user_allocated_mb -= mb
        return True

    # ---------- shell commands ----------
    def cmd_memory(self, args):
        percent = self.used_mb / self.total_mb * 100
        bar_width = 30
        filled = round(bar_width * self.used_mb / self.total_mb)
        bar_color = ui.GREEN if percent < 60 else ui.YELLOW if percent < 85 else ui.RED

        print()
        print(ui.color("Memory Status", ui.BOLD))
        ui.line("-", 40)
        print(f"Total Memory: {self.total_mb:>6} MB")
        print(f"Used Memory:  {self.used_mb:>6} MB")
        print(f"Free Memory:  {self.free_mb:>6} MB")
        ui.line("-", 40)
        print(f"  Kernel (reserved): {self.kernel_mb:>5} MB")
        print(f"  Processes ({len(self.process_memory):>2}):    {self.process_mb:>5} MB")
        print(f"  User allocated:    {self.user_allocated_mb:>5} MB")
        ui.line("-", 40)
        bar = "#" * filled + "." * (bar_width - filled)
        print(f"Usage: [{ui.color(bar, bar_color)}] {percent:.1f}%")
        print()

    def cmd_allocate(self, args):
        if len(args) != 1:
            ui.error("Usage: allocate <MB>   (example: allocate 200)")
            return
        mb = parse_mb(args[0])
        if mb is None:
            ui.error("Memory size must be a positive whole number of MB.")
            return
        if not self.allocate(mb):
            ui.error(f"Not enough memory. Requested {mb} MB, only {self.free_mb} MB free.")
            return
        ui.success(f"{mb} MB allocated.")

    def cmd_free(self, args):
        if len(args) != 1:
            ui.error("Usage: free <MB>   (example: free 200)")
            return
        mb = parse_mb(args[0])
        if mb is None:
            ui.error("Memory size must be a positive whole number of MB.")
            return
        if not self.free(mb):
            ui.error(
                f"Cannot free {mb} MB. Only {self.user_allocated_mb} MB was allocated "
                "with 'allocate'. (Process memory is freed with 'kill'.)"
            )
            return
        ui.success(f"{mb} MB released.")
