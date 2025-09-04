import sys

def clear_last_line(amount = 1):
    for i in range(amount):
        sys.stdout.write("\033[F")      # Move cursor up one line
        sys.stdout.write("\033[K")      # Clear to the end of the line
