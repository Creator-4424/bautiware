from __future__ import annotations
from datetime import date, datetime
from pathlib import Path
import os, sys, time as t

# Local modules
from scheduleLib import (
    CONFIG, SCHEDULES,
    get_today_order_and_status, get_current_block,
    day_status_and_order, compute_cycle_day,
    _anchor, school_days_between,
    jsonToCustomFormat,
    load_from_file
)

# Optional helpers you had
from printf import printb
from cls import clear
import ascii as a

BASE_DIR = Path(__file__).resolve().parent
USERS_DIR = BASE_DIR / "users"
MUSIC_DIR = BASE_DIR / "music"

# ---------- audio guarded ----------
def safe_audio_init():
    try:
        import pygame
        old = sys.stderr
        sys.stderr = open(os.devnull, "w")
        pygame.mixer.init()
        sys.stderr.close(); sys.stderr = old
        return pygame
    except Exception as e:
        print(f"[audio disabled] {e}")
        return None

def play_track(pg, n: str | int = "2"):
    if not pg: return
    try:
        pg.mixer.music.load(os.path.join(MUSIC_DIR, f"track{n}.mp3"))
        pg.mixer.music.play(-1)
    except Exception as e:
        print(f"[audio] {e}")

# ---------- CLI actions ----------
def show_current():
    clear()
    today, order, res = get_today_order_and_status()
    printb(f"\nToday is {today}:\n")
    anchor_date, _ = _anchor(CONFIG)
    if anchor_date > today:
        printb("WARNING: CURRENT DATE IS BEFORE ANCHOR, DATA UNRELIABLE\n")

    printb(f"Status: {res['status']}\n")
    if 'note' in res: printb(f"Note: {res['note']}\n")
    if res["status"] != "Normal":
        return

    printb(f"Cycle Day: {res['cycle_day']}\n")
    printb(f"Schedule: {order}\n")
    label, letter, next_letter = get_current_block(order)
    printb(f"Period: {label}\n")

    # Optional: per-user location for current block
    if letter:
        users_dir = Path(USERS_DIR)
        for p in users_dir.glob("*.json"):
            try:
                # data_str = jsonToCustomFormat(p)  # reuse formatter if you want pretty output per user
                # Or just short line per user:
                data = load_from_file(p); name = data['Name']; cls, room = data[letter]; next = data[next_letter][0]
                print(f"{name} is in {cls}, room {room}. next class: {next}\n")
                pass
            except Exception as e:
                printb(f"{p.name}: {e}\n")

def show_anchor():
    clear()
    anchor_date, anchor_day = _anchor(CONFIG)
    diff = school_days_between(anchor_date, date.today(), CONFIG)
    printb(f"Anchor date: {anchor_date} (Cycle Day {anchor_day})\n")
    printb(f"School days since anchor: {diff}\n\n")

def show_date_or_user(arg: str):
    # user file wins if exists
    user_path = Path("users") / f"{arg.lower()}.json"
    if user_path.exists():
        clear()
        printb(jsonToCustomFormat(user_path), 0.02)
        return
    # else treat as date
    try:
        d = date.fromisoformat(arg)
    except ValueError:
        printb("invalid date or format\n")
        return
    clear()
    anchor_date, _ = _anchor(CONFIG)
    if anchor_date > d:
        printb("WARNING: DATE IS BEFORE ANCHOR, DATA UNRELIABLE\n")
    res = day_status_and_order(d, CONFIG)
    printb(f"{d} Date info:\n")
    printb(f"Status: {res['status']}\n")
    if 'note' in res: printb(f"Note: {res['note']}\n")
    if res["status"] == "Normal":
        printb(f"Cycle Day: {res['cycle_day']}\n")
        printb(f"Schedule: {res['order']}\n")

def main():
    clear()
    print("Loading.", end="\r"); t.sleep(0.6)
    print("Loading..", end="\r"); t.sleep(0.6)
    print("Loading...", end="\r"); t.sleep(1.0)
    printb("Software ready\n"); t.sleep(0.3)
    pg = safe_audio_init()
    play_track(pg, "1")  # default song
    clear()

    print(f"{a.main}\n")


    print("welcome to bautiware V1.6")
    while True:
        printb("\nActions:\n1: Get current date data\n2: Get anchor data\n3: Change music\n\nEnter a date (YYYY-MM-DD) or a name for their schedule (q to quit)\n", 0.01)
        action = input("> ").strip()
        if action == "1":
            show_current(); input("\n<enter>"); clear()
        elif action == "2":
            show_anchor(); input("\n<enter>"); clear()
        elif action == "3":
            clear()
            printb("Choose some music: \n1. Take care by Heaven Pierce Her\n2. Silver Lighting by MathewTimes2\n3. sans. by Toby Fox\n")
            new = input("> ").strip()
            printb("Playing new track...\n")
            play_track(pg, new); t.sleep(0.6); clear()
        elif action.lower() == "q":
            break
        else:
            show_date_or_user(action); input("\n<enter>"); clear()

if __name__ == "__main__":
    main()
