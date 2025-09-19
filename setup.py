import sys
from cx_Freeze import setup, Executable

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="TEAbulator",
    version="1.0",
    description="A tabulator for the TEA (Threshold Equivalent Approval) election system.",
    executables=[Executable("gui.py", base=base, icon="assets/icon.ico", target_name="TEAbulator.exe")],
    author="knettel",
    options={
        "build_exe": {
            "packages": [],
            "include_files": ["classes.py", "tabulator.py", "assets"],
            "includes": ["tkinter"]
        }
    }
)
