"""
config.py - Global settings for BanOnaS OS.

All "magic numbers" of the simulated machine live here so every module
uses the same values (OS name, version, memory size, disk location...).
"""

import os
from pathlib import Path

# ----- Operating system identity -----
OS_NAME = "BanOnaS"
OS_FULL_NAME = "BanOnaS OS"
VERSION = "1.0"
TAGLINE = "The a-peel-ing Command-Line Operating System"

# ----- Simulated hardware -----
ARCHITECTURE = "64-bit (simulated)"
CPU_NAME = "Virtual Banana CPU @ 1.00 GHz (1 core)"
TOTAL_MEMORY_MB = 1024      # Total simulated RAM
KERNEL_MEMORY_MB = 128      # RAM reserved for the kernel / system processes

# ----- Virtual hard drive -----
# Real files are stored inside this folder. BanOnaS can never read or
# write anything outside of it (see filesystem.py -> _resolve()).
# The BANONAS_DISK environment variable lets tests use a temporary disk.
BASE_DIR = Path(__file__).resolve().parent
DISK_ROOT = Path(os.environ.get("BANONAS_DISK", BASE_DIR / "disk"))

# ----- Security -----
MAX_LOGIN_ATTEMPTS = 3
