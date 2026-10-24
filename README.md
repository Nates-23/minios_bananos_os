# 🍌 BanOnaS OS

**BanOnaS OS v1.0** is a simple command-line operating system simulator written in Python.
It runs in Windows Command Prompt (CMD) and shows the main ideas of an operating system:
a command shell, file management, process management, memory management, user login, and system information.

> This is a **simulation**. BanOnaS does not boot, does not control real Windows processes, and does not touch your real RAM.
> Files are real, but they are kept inside the `disk/` folder, which acts as BanOnaS's virtual hard drive.

---

## Group Members

**Group:** Buok

| # | Name | Role |
|---|------|------|
| 1 | Sabanal | Project Leader |
| 2 | Macauyam | CLI Developer (`shell.py`, `main.py`) |
| 3 | Masigon | File Management Developer (`filesystem.py`) |
| 4 | Hechanova | Process Management Developer (`processes.py`) |
| 5 | Alojado | Memory Management Developer (`memory.py`) |
| 6 | Zidge Escleto | User/System Developer + QA (`users.py`, `sysinfo.py`, tests) |

---

## Project Description

When BanOnaS starts, it shows a boot screen and asks the user to log in.
After logging in, the user gets a `BanOnaS:admin\>` prompt and can type commands to:

- create, read, edit, rename and delete files and folders on the virtual disk
- start and stop simulated programs (processes), each with its own PID and memory
- view, allocate and free simulated memory (1024 MB total)
- check who is logged in and view system information

Invalid commands and bad input never crash the system. BanOnaS shows a helpful error instead.

## Features

- **Command-line interface** with its own prompt, a command history, and typo suggestions ("Did you mean 'help'?")
- **File management** using real files, sandboxed inside `disk/` so the rest of your computer can't be touched
- **Process simulation**: a process table with PID, status, memory and owner, plus system processes that can't be killed
- **Memory simulation**: kernel memory, process memory and user allocations, with a usage bar
- **User login**: 2 accounts, salted SHA-256 password hashes, hidden password input, 3-attempt lockout
- **System information**: simulated hardware details plus live uptime, memory and process counts
- **Error handling**: unknown commands, missing files, invalid PIDs, out of memory, bad arguments
- **Automated tests**: 21 unit and end-to-end tests (100% passing)

## Requirements

- Windows 10/11 with Command Prompt (CMD)
- Python 3.8 or newer
- No extra packages (standard library only)

## How to Run

1. Clone the repository:
   ```
   git clone <your-repo-link>
   ```
2. Open **CMD**.
3. Go to the components folder:
   ```
   cd minios_bananos_os\bananaos
   ```
4. Run:
   ```
   python main.py
   ```
5. Log in with one of these accounts:

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | administrator |
| `student` | `student123` | standard user |

### Run the tests
```
python -m unittest discover -s tests -v
```

## Available Commands

### General
| Command | Description |
|---|---|
| `help [command]` | Show all commands, or details for one command |
| `clear` | Clear the screen |
| `date` | Show the current date |
| `time` | Show the current time |
| `systeminfo` | Show system information |
| `status` | Show a quick system summary |
| `version` | Show the BanOnaS version |
| `echo <text>` | Print text |
| `calculator [expr]` | Evaluate math expression or start calculator process |
| `history` | Show previously typed commands |
| `exit` / `shutdown` | Shut down BanOnaS |

### File Management
| Command | Description |
|---|---|
| `dir [folder]` | List files and folders |
| `cd <folder>` | Change directory (`cd ..` goes up, `cd \` goes to root) |
| `mkdir <folder>` | Create a directory |
| `create <file> [text]` | Create a file (asks for content if no text is given) |
| `read <file>` | Show a file's contents |
| `write <file> [text]` | Add text to the end of a file |
| `rename <old> <new>` | Rename a file or folder |
| `delete <file\|folder>` | Delete a file or folder |

### Process Management
| Command | Description |
|---|---|
| `process` | List running processes |
| `run <program> [MB]` | Start a simulated process |
| `kill <PID>` | Terminate a process |

### Memory Management
| Command | Description |
|---|---|
| `memory` | Show memory usage |
| `allocate <MB>` | Allocate memory |
| `free <MB>` | Release allocated memory |

### User Management
| Command | Description |
|---|---|
| `whoami` | Show the current user |
| `users` | List all accounts |
| `logout` / `login` | Log out and return to the login screen |

## Project Structure

```
bananaos/
├── main.py               Entry point: banner, boot, login loop
├── shell.py              Command interpreter (prompt, parsing, dispatch)
├── filesystem.py         File management (sandboxed to disk/)
├── processes.py          Process table simulation
├── memory.py             Memory simulation
├── users.py              Accounts and login
├── sysinfo.py            systeminfo, date, time, version, status
├── config.py             OS name, version, memory size, disk location
├── ui.py                 Colors and output helpers
├── requirements.txt      Dependency manifest (Python stdlib)
├── disk/                 Virtual hard drive
├── tests/                Automated test suite
├── .gitignore
└── README.md
```

## Project Documents & Demo Video

- **Demo Video & PDFs Folder:** [Google Drive - Group Buok BanOnaS OS](https://drive.google.com/drive/folders/1gYvzwWuc_t76QvKe0XQL8HCVu2wzSsms?usp=sharing)
- **Included Documents:**
  - `User_Manual.pdf`
  - `Technical_Documentation.pdf`
  - `Group Buok individual report.pdf`
  - `Grou Buok - Banonas OS.mp4`
