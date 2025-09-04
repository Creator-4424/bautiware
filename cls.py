import platform
import os
def clear(): # command to clear console, used to reduce clutter
    if platform.system() == "Windows":
        os.system("cls")  # Clear console for Windows
    else:
        os.system("clear")  # Clear console for macOS/Linux
print("test")

