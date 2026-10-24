"""
Automated tests for BanOnaS OS.

Run from the project folder:
    python -m unittest discover -s tests -v

Unit tests use a temporary disk folder, so your real disk/ is never touched.
The end-to-end test starts main.py as a real program, types commands into
it, and checks the output.
"""

import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from filesystem import FileSystem          # noqa: E402
from memory import MemoryManager, parse_mb  # noqa: E402
from processes import ProcessManager       # noqa: E402
from shell import Shell                    # noqa: E402
from sysinfo import SystemInfo             # noqa: E402
from users import UserManager              # noqa: E402


def make_system(disk):
    memory = MemoryManager()
    users = UserManager()
    users.current_user = users.users["admin"]
    processes = ProcessManager(memory, users)
    fs = FileSystem(disk)
    sysinfo = SystemInfo(users, memory, processes, fs)
    shell = Shell(users, fs, memory, processes, sysinfo)
    return shell


class BanOnaSTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.disk = Path(self.tmp.name) / "disk"
        self.shell = make_system(self.disk)

    def tearDown(self):
        self.tmp.cleanup()

    def run_cmd(self, line, user_input=None):
        """Run a command and return what it printed."""
        out = io.StringIO()
        with redirect_stdout(out):
            if user_input is not None:
                with mock.patch("builtins.input", side_effect=user_input):
                    self.shell.execute(line)
            else:
                self.shell.execute(line)
        return out.getvalue()


class TestUsers(unittest.TestCase):
    def test_correct_and_wrong_passwords(self):
        users = UserManager()
        self.assertIsNotNone(users.authenticate("admin", "admin123"))
        self.assertIsNotNone(users.authenticate("student", "student123"))
        self.assertIsNone(users.authenticate("admin", "wrong"))
        self.assertIsNone(users.authenticate("nobody", "admin123"))

    def test_passwords_not_stored_in_plain_text(self):
        users = UserManager()
        self.assertNotIn("admin123", vars(users.users["admin"]).values())


class TestMemory(unittest.TestCase):
    def test_parse_mb(self):
        self.assertEqual(parse_mb("200"), 200)
        self.assertEqual(parse_mb("200mb"), 200)
        self.assertIsNone(parse_mb("-5"))
        self.assertIsNone(parse_mb("0"))
        self.assertIsNone(parse_mb("abc"))

    def test_allocate_and_free(self):
        m = MemoryManager(1024, 128)
        self.assertEqual(m.free_mb, 896)
        self.assertTrue(m.allocate(200))
        self.assertEqual(m.used_mb, 328)
        self.assertFalse(m.allocate(10_000))
        self.assertFalse(m.free(500))
        self.assertTrue(m.free(200))
        self.assertEqual(m.used_mb, 128)


class TestFileSystem(BanOnaSTestCase):
    def test_create_read_delete(self):
        self.assertIn("File created.", self.run_cmd("create notes.txt Operating Systems Final Project"))
        self.assertTrue((self.disk / "notes.txt").exists())
        self.assertIn("Operating Systems Final Project", self.run_cmd("read notes.txt"))
        self.assertIn("File deleted.", self.run_cmd("delete notes.txt"))
        self.assertFalse((self.disk / "notes.txt").exists())

    def test_create_with_multiline_prompt(self):
        self.run_cmd("create poem.txt", user_input=["line one", "line two", "END"])
        self.assertEqual((self.disk / "poem.txt").read_text(), "line one\nline two\n")

    def test_mkdir_cd_dir(self):
        self.assertIn("Directory created.", self.run_cmd("mkdir Documents"))
        self.run_cmd("cd Documents")
        self.assertEqual(self.shell.fs.display_path(), "\\Documents")
        self.run_cmd("create a.txt hi")
        self.assertIn("a.txt", self.run_cmd("dir"))
        self.run_cmd("cd ..")
        self.assertEqual(self.shell.fs.display_path(), "\\")

    def test_errors(self):
        self.assertIn("File does not exist.", self.run_cmd("read missing.txt"))
        self.assertIn("File does not exist.", self.run_cmd("delete missing.txt"))
        self.run_cmd("create a.txt x")
        self.assertIn("already exists", self.run_cmd("create a.txt y"))
        self.assertIn("Invalid name", self.run_cmd("mkdir bad*name"))

    def test_sandbox_cannot_escape(self):
        out = self.run_cmd("read ..\\..\\secret.txt")
        self.assertIn("outside the BanOnaS disk", out)
        out = self.run_cmd("cd C:\\Windows")
        self.assertIn("outside the BanOnaS disk", out)
        self.assertEqual(self.shell.fs.cwd, self.shell.fs.root)

    def test_rename_and_write(self):
        self.run_cmd("create a.txt first")
        self.run_cmd("write a.txt second")
        self.run_cmd("rename a.txt b.txt")
        self.assertEqual((self.disk / "b.txt").read_text(), "first\nsecond\n")

    def test_quoted_names(self):
        self.run_cmd('create "my notes.txt" hello')
        self.assertTrue((self.disk / "my notes.txt").exists())


class TestProcesses(BanOnaSTestCase):
    def test_run_list_kill(self):
        out = self.run_cmd("run calculator")
        self.assertIn("Process started.", out)
        self.assertIn("RUNNING", out)
        pid = self.shell.processes.next_pid - 1
        self.assertIn("calculator", self.run_cmd("process"))
        used_before = self.shell.memory.used_mb
        self.assertIn(f"Process {pid} terminated.", self.run_cmd(f"kill {pid}"))
        self.assertEqual(self.shell.memory.used_mb, used_before - 32)

    def test_kill_errors(self):
        self.assertIn("Process does not exist.", self.run_cmd("kill 999"))
        self.assertIn("PID must be a number.", self.run_cmd("kill abc"))
        self.assertIn("system process", self.run_cmd("kill 1"))

    def test_out_of_memory(self):
        self.assertIn("Cannot start", self.run_cmd("run huge 5000"))

    def test_student_cannot_kill_admin_process(self):
        self.run_cmd("run editor")
        pid = self.shell.processes.next_pid - 1
        self.shell.users.current_user = self.shell.users.users["student"]
        self.assertIn("Access denied", self.run_cmd(f"kill {pid}"))


class TestShell(BanOnaSTestCase):
    def test_unknown_command(self):
        out = self.run_cmd("hellooo")
        self.assertIn("Unknown command.", out)
        self.assertIn("Type 'help'", out)

    def test_help_lists_required_commands(self):
        out = self.run_cmd("help")
        for cmd in ["help", "clear", "date", "time", "whoami", "dir", "mkdir", "create",
                    "read", "delete", "process", "run", "kill", "memory", "allocate",
                    "free", "systeminfo", "exit"]:
            self.assertIn(cmd, out)

    def test_exit_signal(self):
        self.assertEqual(self.shell.execute("exit"), "exit")
        self.assertEqual(self.shell.execute("logout"), "logout")

    def test_bad_arguments_never_crash(self):
        for line in ["allocate", "allocate -1", "free abc", "run", "kill", "mkdir",
                     "read", 'create "unclosed', "rename a", "cd nowhere"]:
            self.run_cmd(line)  # Must not raise

    def test_calculator(self):
        out = self.run_cmd("calculator 10 + 5 * 2")
        self.assertIn("= 20", out)
        out_err = self.run_cmd("calculator 10 / 0")
        self.assertIn("Division by zero", out_err)
        out_proc = self.run_cmd("calculator")
        self.assertIn("Process started.", out_proc)


class TestEndToEnd(unittest.TestCase):
    """Start main.py for real and type a whole session into it."""

    def test_full_session(self):
        session = "\n".join([
            "admin", "wrongpass",          # failed login
            "admin", "admin123",           # successful login
            "help", "whoami", "mkdir Documents", "cd Documents",
            "create notes.txt Hello BanOnaS", "read notes.txt", "dir",
            "run calculator", "process", "allocate 200", "memory",
            "free 200", "systeminfo", "hellooo", "kill 999", "exit",
        ]) + "\n"
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, BANONAS_DISK=str(Path(tmp) / "disk"), NO_COLOR="1")
            result = subprocess.run(
                [sys.executable, "main.py"], input=session, capture_output=True,
                text=True, cwd=PROJECT_DIR, env=env, timeout=30,
            )
        out = result.stdout
        self.assertEqual(result.returncode, 0, result.stderr)
        for expected in ["Invalid username or password", "Login successful.",
                         "Welcome, admin!", "Current User: admin", "Directory created.",
                         "File created.", "Hello BanOnaS", "Process started.",
                         "200 MB allocated.", "200 MB released.", "SYSTEM INFORMATION",
                         "Unknown command.", "Process does not exist.", "Goodbye!"]:
            self.assertIn(expected, out)


if __name__ == "__main__":
    unittest.main()
