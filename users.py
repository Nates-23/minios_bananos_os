"""
users.py - User accounts and the login system for BanOnaS.

Owner: Member 6 (User/System + QA)

How it works
------------
* Accounts are stored in a dictionary: username -> User object.
* Passwords are NOT stored as plain text. Each user gets a random "salt",
  and we store SHA-256(salt + password). At login, the typed password is
  hashed the same way and the two hashes are compared.
* The password is hidden while typing (shown as ****).
* After MAX_LOGIN_ATTEMPTS wrong tries the system locks and shuts down.

Default accounts:
    admin   / admin123     (administrator)
    student / student123   (standard user)
"""

import hashlib
import os
import sys

from config import MAX_LOGIN_ATTEMPTS
import ui


def _hash_password(password, salt):
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def masked_input(prompt):
    """Read a password and echo '*' for each character (Windows CMD)."""
    if os.name == "nt" and sys.stdin.isatty():
        import msvcrt

        sys.stdout.write(prompt)
        sys.stdout.flush()
        chars = []
        while True:
            ch = msvcrt.getwch()
            if ch in ("\r", "\n"):          # Enter
                print()
                break
            if ch == "\x03":                # Ctrl+C
                raise KeyboardInterrupt
            if ch in ("\x00", "\xe0"):      # Arrow/function keys: ignore
                msvcrt.getwch()
                continue
            if ch == "\b":                  # Backspace
                if chars:
                    chars.pop()
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
                continue
            chars.append(ch)
            sys.stdout.write("*")
            sys.stdout.flush()
        return "".join(chars)

    if sys.stdin.isatty():                  # Other real terminals
        import getpass
        return getpass.getpass(prompt)

    return input(prompt)                    # Piped input (automated tests)


class User:
    def __init__(self, username, password, role, full_name):
        self.username = username
        self.role = role
        self.full_name = full_name
        self.salt = os.urandom(8).hex()
        self.password_hash = _hash_password(password, self.salt)

    def check_password(self, password):
        return _hash_password(password, self.salt) == self.password_hash

    @property
    def is_admin(self):
        return self.role == "administrator"


class UserManager:
    def __init__(self):
        self.users = {}
        self.current_user = None
        self.add_user("admin", "admin123", "administrator", "System Administrator")
        self.add_user("student", "student123", "standard", "Student User")

    def add_user(self, username, password, role, full_name):
        self.users[username] = User(username, password, role, full_name)

    def authenticate(self, username, password):
        """Return the User if the credentials are correct, otherwise None."""
        user = self.users.get(username)
        if user and user.check_password(password):
            return user
        return None

    def login_screen(self):
        """Show the login prompt. Returns True on success, False if locked out."""
        print()
        ui.header("BanOnaS Login")
        print()
        for attempt in range(1, MAX_LOGIN_ATTEMPTS + 1):
            username = input("Username: ").strip()
            password = masked_input("Password: ")
            user = self.authenticate(username, password)
            if user:
                self.current_user = user
                print()
                ui.success("Login successful.")
                print()
                print(f"Welcome, {ui.color(user.username, ui.BOLD + ui.YELLOW)}!")
                return True
            remaining = MAX_LOGIN_ATTEMPTS - attempt
            if remaining:
                ui.error(f"Invalid username or password. {remaining} attempt(s) left.")
                print()
        ui.error("Too many failed login attempts. System locked.")
        return False

    def logout(self):
        self.current_user = None

    # ---------- shell commands ----------
    def cmd_whoami(self, args):
        user = self.current_user
        print(f"Current User: {user.username}")
        print(f"Full Name:    {user.full_name}")
        print(f"Role:         {user.role}")

    def cmd_users(self, args):
        print()
        print(f"{'USERNAME':<12}{'ROLE':<16}{'FULL NAME':<24}")
        ui.line("-", 52)
        for user in self.users.values():
            marker = "  <- you" if user is self.current_user else ""
            print(f"{user.username:<12}{user.role:<16}{user.full_name:<24}{marker}")
        print()
