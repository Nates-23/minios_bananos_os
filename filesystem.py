"""
filesystem.py - File management for BanOnaS.

Owner: Member 3 (File Management)

How it works
------------
* BanOnaS uses a real folder, `disk/`, as its virtual hard drive.
  Every file and folder a user creates is a real file inside `disk/`,
  so the data is still there after BanOnaS shuts down.
* Inside BanOnaS the disk root is shown as "\" (like C:\ on Windows).
* `self.cwd` is the current working directory (changed with `cd`).
* SANDBOX SECURITY: every path typed by the user goes through
  `_resolve()`. It turns the path into an absolute path and refuses any
  path that is outside `disk/` (for example `..\..\Windows`). This way
  BanOnaS can never touch the rest of the real computer.
"""

import shutil
from datetime import datetime
from pathlib import Path

from config import DISK_ROOT
import ui

INVALID_CHARS = set('<>:"/\\|?*')


def read_multiline(prompt_text):
    """Read lines of text until the user types END on its own line."""
    ui.info(prompt_text)
    lines = []
    while True:
        try:
            text = input()
        except EOFError:
            break
        if text.strip().upper() == "END":
            break
        lines.append(text)
    return "\n".join(lines)


def format_size(size):
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


class FileSystem:
    def __init__(self, root=DISK_ROOT):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.cwd = self.root
        self._create_welcome_file()

    def _create_welcome_file(self):
        """Put a sample file on a brand-new (empty) disk."""
        if not self._visible_entries(self.root):
            (self.root / "welcome.txt").write_text(
                "Welcome to BanOnaS OS!\n"
                "This file lives on the BanOnaS virtual disk.\n"
                "Type 'help' to see what you can do.\n",
                encoding="utf-8",
            )

    # ---------- path helpers ----------
    @staticmethod
    def _visible_entries(folder):
        """Folder contents without hidden system files (names starting with '.')."""
        return [p for p in folder.iterdir() if not p.name.startswith(".")]

    def display_path(self, path=None):
        """Show a real path as a BanOnaS path, e.g. disk/Docs/a.txt -> \\Docs\\a.txt"""
        relative = (path or self.cwd).relative_to(self.root)
        text = str(relative)
        return "\\" if text == "." else "\\" + text.replace("/", "\\")

    def _resolve(self, user_path):
        """Turn a user-typed path into a real path INSIDE the disk, or raise."""
        if user_path.startswith(("\\", "/")):
            base, user_path = self.root, user_path.lstrip("\\/")
        else:
            base = self.cwd
        target = (base / user_path).resolve()
        if target != self.root and self.root not in target.parents:
            raise PermissionError("Access denied. Path is outside the BanOnaS disk.")
        return target

    @staticmethod
    def _valid_name(name):
        return (
            name.strip() != ""
            and name not in (".", "..")
            and not any(c in INVALID_CHARS for c in name)
        )

    def _check_new_item(self, user_path):
        """Common checks before creating a file/folder. Returns target or None."""
        target = self._resolve(user_path)
        if not self._valid_name(target.name):
            ui.error(f"Invalid name '{target.name}'. Names cannot contain {' '.join(sorted(INVALID_CHARS))}")
            return None
        if target.exists():
            kind = "Directory" if target.is_dir() else "File"
            ui.error(f"{kind} '{target.name}' already exists.")
            return None
        if not target.parent.is_dir():
            ui.error(f"Directory '{self.display_path(target.parent)}' does not exist.")
            return None
        return target

    # ---------- shell commands ----------
    def cmd_dir(self, args):
        target = self._resolve(args[0]) if args else self.cwd
        if not target.exists():
            ui.error("Directory does not exist.")
            return
        if not target.is_dir():
            ui.error(f"'{target.name}' is a file, not a directory.")
            return

        entries = sorted(self._visible_entries(target), key=lambda p: (p.is_file(), p.name.lower()))
        print()
        print(f" Directory of {self.display_path(target)}")
        print()
        files = folders = total = 0
        for entry in entries:
            modified = datetime.fromtimestamp(entry.stat().st_mtime).strftime("%Y-%m-%d  %H:%M")
            if entry.is_dir():
                folders += 1
                print(f" {modified}    {ui.color('<DIR>', ui.BLUE):<10}           {ui.color(entry.name, ui.BLUE)}")
            else:
                files += 1
                size = entry.stat().st_size
                total += size
                print(f" {modified}    {'':<5}{format_size(size):>12}     {entry.name}")
        if not entries:
            print(" (empty)")
        print()
        print(f" {files} file(s), {folders} folder(s), {format_size(total)} total")
        print()

    def cmd_mkdir(self, args):
        if len(args) != 1:
            ui.error("Usage: mkdir <folder>   (example: mkdir Documents)")
            return
        target = self._check_new_item(args[0])
        if target:
            target.mkdir()
            ui.success("Directory created.")

    def cmd_create(self, args):
        if not args:
            ui.error("Usage: create <file> [text]   (example: create notes.txt)")
            return
        target = self._check_new_item(args[0])
        if not target:
            return
        if len(args) > 1:
            content = " ".join(args[1:])
        else:
            content = read_multiline("Enter file content. Type END on a new line to save.")
        target.write_text(content + ("\n" if content else ""), encoding="utf-8")
        ui.success("File created.")

    def cmd_read(self, args):
        if len(args) != 1:
            ui.error("Usage: read <file>   (example: read notes.txt)")
            return
        target = self._resolve(args[0])
        if not target.exists():
            ui.error("File does not exist.")
            return
        if target.is_dir():
            ui.error(f"'{target.name}' is a directory. Use 'dir' to see its contents.")
            return
        content = target.read_text(encoding="utf-8", errors="replace")
        print()
        print(content.rstrip("\n") if content else ui.color("(file is empty)", ui.GRAY))
        print()

    def cmd_write(self, args):
        if not args:
            ui.error("Usage: write <file> [text]   (adds text to the end of a file)")
            return
        target = self._resolve(args[0])
        if not target.exists():
            ui.error("File does not exist. Use 'create' to make a new file.")
            return
        if target.is_dir():
            ui.error(f"'{target.name}' is a directory.")
            return
        if len(args) > 1:
            content = " ".join(args[1:])
        else:
            content = read_multiline("Enter text to add. Type END on a new line to save.")
        with target.open("a", encoding="utf-8") as f:
            f.write(content + "\n")
        ui.success("File updated.")

    def cmd_delete(self, args):
        if len(args) != 1:
            ui.error("Usage: delete <file|folder>   (example: delete notes.txt)")
            return
        target = self._resolve(args[0])
        if target == self.root:
            ui.error("Access denied. The root directory cannot be deleted.")
            return
        if not target.exists():
            ui.error("File does not exist.")
            return
        if target == self.cwd or target in self.cwd.parents:
            ui.error("Cannot delete the directory you are currently in. Use 'cd ..' first.")
            return
        if target.is_file():
            target.unlink()
            ui.success("File deleted.")
            return
        if any(target.iterdir()):
            answer = input(f"Directory '{target.name}' is not empty. Delete it and everything inside? (y/n): ")
            if answer.strip().lower() not in ("y", "yes"):
                ui.warning("Delete cancelled.")
                return
            shutil.rmtree(target)
        else:
            target.rmdir()
        ui.success("Directory deleted.")

    def cmd_cd(self, args):
        if not args:
            print(self.display_path())
            return
        if len(args) != 1:
            ui.error("Usage: cd <folder>   (cd .. = go up, cd \\ = go to root)")
            return
        target = self._resolve(args[0])
        if not target.exists():
            ui.error("Directory does not exist.")
            return
        if not target.is_dir():
            ui.error(f"'{target.name}' is a file, not a directory.")
            return
        self.cwd = target

    def cmd_rename(self, args):
        if len(args) != 2:
            ui.error("Usage: rename <old_name> <new_name>   (example: rename a.txt b.txt)")
            return
        source = self._resolve(args[0])
        if source == self.root:
            ui.error("Access denied. The root directory cannot be renamed.")
            return
        if not source.exists():
            ui.error("File does not exist.")
            return
        new_name = args[1]
        if not self._valid_name(new_name):
            ui.error(f"Invalid name '{new_name}'.")
            return
        destination = source.parent / new_name
        if destination.exists():
            ui.error(f"'{new_name}' already exists.")
            return
        if source == self.cwd or source in self.cwd.parents:
            ui.error("Cannot rename the directory you are currently in. Use 'cd ..' first.")
            return
        source.rename(destination)
        ui.success(f"Renamed '{source.name}' to '{new_name}'.")
