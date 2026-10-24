"""
shell.py - The BanOnaS command shell (command interpreter).

Owner: Member 2 (CLI Developer)

How it works
------------
1. Show the prompt, e.g.  BanOnaS:admin\\Documents>
2. Read a line and split it into a command and its arguments.
   Quotes are supported:  create "my notes.txt"
3. Look the command up in the command table (self.commands) and call
   its handler function with the argument list.
4. Every handler runs inside try/except, so a bug or bad input in one
   command prints an error message instead of crashing BanOnaS.

Handlers may return a "signal":
    "exit"   -> shut down BanOnaS
    "logout" -> go back to the login screen
"""

import ast
import difflib
import os
import shlex

import ui


class Command:
    def __init__(self, handler, category, usage, description):
        self.handler = handler
        self.category = category
        self.usage = usage
        self.description = description


class Shell:
    CATEGORIES = ["General", "File Management", "Process Management",
                  "Memory Management", "User Management"]

    def __init__(self, users, filesystem, memory, processes, sysinfo):
        self.users = users
        self.fs = filesystem
        self.memory = memory
        self.processes = processes
        self.sysinfo = sysinfo
        self.history = []
        self.commands = {}
        self._register_commands()

    # ---------- command table ----------
    def register(self, name, handler, category, usage, description):
        self.commands[name] = Command(handler, category, usage, description)

    def _register_commands(self):
        r = self.register
        # General
        r("help", self.cmd_help, "General", "help [command]", "Show available commands")
        r("clear", self.cmd_clear, "General", "clear", "Clear the screen")
        r("date", self.sysinfo.cmd_date, "General", "date", "Show the current date")
        r("time", self.sysinfo.cmd_time, "General", "time", "Show the current time")
        r("systeminfo", self.sysinfo.cmd_systeminfo, "General", "systeminfo", "Show system information")
        r("status", self.sysinfo.cmd_status, "General", "status", "Show a quick system summary")
        r("version", self.sysinfo.cmd_version, "General", "version", "Show the BanOnaS version")
        r("echo", self.cmd_echo, "General", "echo <text>", "Print text to the screen")
        r("calculator", self.cmd_calculator, "General", "calculator <expr>", "Evaluate a math expression (or start process)")
        r("history", self.cmd_history, "General", "history", "Show previously typed commands")
        r("exit", self.cmd_exit, "General", "exit", "Shut down BanOnaS")
        r("shutdown", self.cmd_exit, "General", "shutdown", "Same as exit")
        # File management
        r("dir", self.fs.cmd_dir, "File Management", "dir [folder]", "List files and folders")
        r("cd", self.fs.cmd_cd, "File Management", "cd <folder>", "Change directory (cd .. / cd \\)")
        r("mkdir", self.fs.cmd_mkdir, "File Management", "mkdir <folder>", "Create a directory")
        r("create", self.fs.cmd_create, "File Management", "create <file> [text]", "Create a new file")
        r("read", self.fs.cmd_read, "File Management", "read <file>", "Display a file's contents")
        r("write", self.fs.cmd_write, "File Management", "write <file> [text]", "Add text to a file")
        r("rename", self.fs.cmd_rename, "File Management", "rename <old> <new>", "Rename a file or folder")
        r("delete", self.fs.cmd_delete, "File Management", "delete <file|folder>", "Delete a file or folder")
        # Process management
        r("process", self.processes.cmd_process, "Process Management", "process", "List running processes")
        r("run", self.processes.cmd_run, "Process Management", "run <program> [MB]", "Start a simulated process")
        r("kill", self.processes.cmd_kill, "Process Management", "kill <PID>", "Terminate a process")
        # Memory management
        r("memory", self.memory.cmd_memory, "Memory Management", "memory", "Show memory usage")
        r("allocate", self.memory.cmd_allocate, "Memory Management", "allocate <MB>", "Allocate memory")
        r("free", self.memory.cmd_free, "Memory Management", "free <MB>", "Release allocated memory")
        # User management
        r("whoami", self.users.cmd_whoami, "User Management", "whoami", "Show the current user")
        r("users", self.users.cmd_users, "User Management", "users", "List all user accounts")
        r("logout", self.cmd_logout, "User Management", "logout", "Log out and return to login")
        r("login", self.cmd_logout, "User Management", "login", "Switch to another user")

    # ---------- main loop ----------
    def prompt(self):
        user = self.users.current_user.username
        return (f"{ui.color('BanOnaS', ui.YELLOW + ui.BOLD)}:"
                f"{ui.color(user, ui.GREEN)}"
                f"{ui.color(self.fs.display_path(), ui.BLUE)}> ")

    @staticmethod
    def parse(line):
        """Split a command line into words. Supports "quoted names"."""
        lexer = shlex.shlex(line, posix=False)
        lexer.whitespace_split = True
        lexer.commenters = ""      # '#' is normal text
        lexer.quotes = '"'         # only double quotes group words (so "don't" works)
        parts = list(lexer)        # posix=False keeps backslashes: Docs\notes.txt
        return [p[1:-1] if len(p) >= 2 and p[0] == p[-1] == '"' else p
                for p in parts]

    def execute(self, line):
        """Run one command line. Returns a signal ("exit"/"logout") or None."""
        line = line.strip()
        if not line:
            return None
        self.history.append(line)

        try:
            words = self.parse(line)
        except ValueError:
            ui.error("Missing closing quote.")
            return None

        name, args = words[0].lower(), words[1:]
        command = self.commands.get(name)
        if command is None:
            print(ui.color("Unknown command.", ui.RED))
            suggestion = difflib.get_close_matches(name, self.commands, n=1)
            if suggestion:
                print(f"Did you mean '{suggestion[0]}'?")
            print("Type 'help' to see the available commands.")
            return None

        try:
            return command.handler(args)
        except PermissionError as e:
            ui.error(str(e) if "BanOnaS" in str(e) else "Access denied.")
        except OSError as e:
            ui.error(f"Disk operation failed ({e.strerror or e}).")
        except Exception as e:  # Last line of defense: never crash the OS
            ui.error(f"Unexpected problem while running '{name}': {e}")
        return None

    def run(self):
        """Read and execute commands until exit or logout."""
        while True:
            try:
                line = input(self.prompt())
            except KeyboardInterrupt:
                print()
                ui.warning("Use 'exit' to shut down BanOnaS.")
                continue
            except EOFError:
                return "exit"
            signal = self.execute(line)
            if signal in ("exit", "logout"):
                return signal

    # ---------- built-in shell commands ----------
    def cmd_help(self, args):
        if args:
            command = self.commands.get(args[0].lower())
            if command is None:
                ui.error(f"No help for '{args[0]}'. Type 'help' to see all commands.")
                return
            print(f"\nCOMMAND:  {args[0].lower()}")
            print(f"Purpose:  {command.description}")
            print(f"Syntax:   {command.usage}\n")
            return

        print()
        print(ui.color("Available Commands:", ui.BOLD))
        for category in self.CATEGORIES:
            print()
            print(ui.color(f"  {category}", ui.YELLOW))
            for name, command in self.commands.items():
                if command.category == category:
                    print(f"    {command.usage:<24}{command.description}")
        print()
        print("Type 'help <command>' for details on one command.")
        print()

    def cmd_clear(self, args):
        os.system("cls" if os.name == "nt" else "clear")

    def cmd_echo(self, args):
        print(" ".join(args))

    def cmd_calculator(self, args):
        if not args:
            ui.info("Starting simulated calculator process...")
            self.processes.cmd_run(["calculator"])
            return

        expr = "".join(args)
        allowed_operators = (
            ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv,
            ast.Mod, ast.Pow, ast.USub, ast.UAdd
        )

        def eval_node(node):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                return node.value
            elif isinstance(node, ast.BinOp):
                left = eval_node(node.left)
                right = eval_node(node.right)
                op_type = type(node.op)
                if op_type not in allowed_operators:
                    raise ValueError("Unsupported operator.")
                if op_type is ast.Add: return left + right
                if op_type is ast.Sub: return left - right
                if op_type is ast.Mult: return left * right
                if op_type is ast.Div:
                    if right == 0: raise ZeroDivisionError("division by zero")
                    return left / right
                if op_type is ast.FloorDiv:
                    if right == 0: raise ZeroDivisionError("division by zero")
                    return left // right
                if op_type is ast.Mod:
                    if right == 0: raise ZeroDivisionError("division by zero")
                    return left % right
                if op_type is ast.Pow: return left ** right
            elif isinstance(node, ast.UnaryOp):
                operand = eval_node(node.operand)
                op_type = type(node.op)
                if op_type is ast.USub: return -operand
                if op_type is ast.UAdd: return +operand
            raise ValueError("Invalid mathematical expression.")

        try:
            tree = ast.parse(expr, mode='eval')
            result = eval_node(tree.body)
            print(f"{expr} = {result}")
        except ZeroDivisionError:
            ui.error("Math error: Division by zero.")
        except Exception:
            ui.error(f"Invalid math expression '{expr}'. Usage: calculator [expression]")

    def cmd_history(self, args):
        for number, line in enumerate(self.history, start=1):
            print(f"  {number:>3}  {line}")

    def cmd_exit(self, args):
        return "exit"

    def cmd_logout(self, args):
        return "logout"
