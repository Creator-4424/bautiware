# BAUTIWARE CLI — V1.8
from __future__ import annotations
from datetime import date, datetime, time
from pathlib import Path
import os, sys, time as t

# Local imports
from scheduleLib import (
    CONFIG, SCHEDULES,
    get_today_order_and_status, get_current_block, get_half_block,
    day_status_and_order, compute_cycle_day,
    _anchor, school_days_between, next_school_day,
    jsonToCustomFormat, load_from_file
)

# Helpers
from printf import printb
from cls import clear
import ascii as a

# ---------- settings ----------
AFTER_SCHOOL_CUTOFF = time(15, 55)
DEBUG_TIME: time | None = None  # Example: time(17, 30) to test “after school”
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
    finally:
        sys.stderr.close()
        sys.stderr = old
    return pygame

def play_track(pg, n: str | int = "2"):
    if not pg:
        return
    path = MUSIC_DIR / f"track{n}.mp3"
    if not path.exists():
        printb(f"Missing track: {path.name}\n")
        return
    try:
        pg.mixer.music.load(str(path))
        pg.mixer.music.play(-1)
    except Exception as e:
        printb(f"[audio error] {e}\n")

# ---------- reusable user printer ----------
def print_next_classes(next_letter: str):
    if not USERS_DIR.exists():
        printb("No users directory found.\n")
        return
    for p in USERS_DIR.glob("*.json"):
        try:
            data = load_from_file(p)
            name = data.get("Name", p.stem)
            nxt_cls, nxt_room = data.get(next_letter, [None, None])
            if nxt_cls:
                print(f"{name} → {nxt_cls} (room {nxt_room})")
            else:
                print(f"{name} → ")
        except Exception as e:
            printb(f"{p.name}: {e}\n")

# ---------- CLI actions ----------
def show_current():
    clear()
    today_date, order, res = get_today_order_and_status()
    printb(f"\nToday is {today_date}:\n")

    anchor_date, _ = _anchor(CONFIG)
    if anchor_date > today_date:
        printb("WARNING: CURRENT DATE IS BEFORE ANCHOR, DATA UNRELIABLE\n")

    printb(f"Status: {res['status']}\n")
    if "note" in res:
        printb(f"Note: {res['note']}\n")

    # Handle weekends / holidays
    if res["status"] not in ("Normal", "Half Day"):
        nd = next_school_day(today_date, CONFIG)
        nres = day_status_and_order(nd, CONFIG)
        if nres["status"] in ("Normal", "Half Day"):
            next_letter = nres["order"][0]
            printb(f"Next school day: {nd} (Order {nres['order']})\n")
            print_next_classes(next_letter)
        return

    # Normal or half-day
    printb(f"Cycle Day: {res['cycle_day']}\n")
    printb(f"Schedule: {order}\n")

    now = DEBUG_TIME or datetime.now().time()

    # --- choose correct block function ---
    if res["status"] == "Half Day":
        gb = get_half_block(order, now=now)
    else:
        gb = get_current_block(order, now=now)

    # --- unpack safely ---
    if not isinstance(gb, tuple):
        label, letter, next_letter = str(gb), None, None
    else:
        label, letter, next_letter = (gb + (None,) * (3 - len(gb)))[:3]

    # --- display which mode we're using ---
    if res["status"] == "Half Day":
        printb(f"Current Period (Half Day Schedule): {label}\n")
    else:
        printb(f"Current Period: {label}\n")

    # --- after-school → move to next day ---
        # --- Determine next day's info if we're after school or not in a class ---
    next_day_date = None
    next_day_order = None

    if (now >= AFTER_SCHOOL_CUTOFF) or (not letter):
        nd = next_school_day(today_date, CONFIG)
        nres = day_status_and_order(nd, CONFIG)
        if nres["status"] in ("Normal", "Half Day"):
            next_day_date = nd
            next_day_order = nres["order"]
            next_letter = next_day_order[0]
            printb(f"Next school day: {nd} (Order {next_day_order})\n")
        else:
            next_letter = order[0] if order else None
    else:
        next_day_order = order

    # --- print CURRENT block classes ---
    if letter:
        printb(f"\nCURRENT CLASS ({letter}):\n")
        for p in Path(USERS_DIR).glob("*.json"):
            try:
                data = load_from_file(p)
                name = data.get("Name", p.stem)
                cls, room = data.get(letter, ["—", "—"])
                print(f"{name} → {cls} (room {room})")
            except Exception as e:
                printb(f"{p.name}: {e}\n")

    # --- print NEXT block classes (uses next day's order if applicable) ---
    printb(f"\nNEXT CLASS ({next_letter}):\n")
    if next_letter:
        for p in Path(USERS_DIR).glob("*.json"):
            try:
                data = load_from_file(p)
                name = data.get("Name", p.stem)
                nxt_cls, nxt_room = data.get(next_letter, ["—", "—"])
                print(f"{name} → {nxt_cls} (room {nxt_room})")
            except Exception as e:
                printb(f"{p.name}: {e}\n")
def show_anchor():
    clear()
    anchor_date, anchor_day = _anchor(CONFIG)
    diff = school_days_between(anchor_date, date.today(), CONFIG)
    printb(f"Anchor date: {anchor_date} (Cycle Day {anchor_day})\n")
    printb(f"School days since anchor: {diff}\n\n")

def show_date_or_user(arg: str):
    user_path = USERS_DIR / f"{arg.lower()}.json"
    if user_path.exists():
        clear()
        printb(jsonToCustomFormat(user_path), 0.02)
        return
    try:
        d = date.fromisoformat(arg)
    except ValueError:
        printb("Invalid date or format.\n")
        return
    clear()
    anchor_date, _ = _anchor(CONFIG)
    if anchor_date > d:
        printb("WARNING: DATE IS BEFORE ANCHOR, DATA UNRELIABLE\n")
    res = day_status_and_order(d, CONFIG)
    printb(f"{d} Date info:\n")
    printb(f"Status: {res['status']}\n")
    if "note" in res:
        printb(f"Note: {res['note']}\n")
    if res["status"] == "Normal":
        printb(f"Cycle Day: {res['cycle_day']}\n")
        printb(f"Schedule: {res['order']}\n")

# ---------- main loop ----------
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
    print("Welcome to Bautiware CLI V1.7")
    print(f"Next school day: {next_school_day(date.today(), CONFIG)}")

    while True:
        printb("\nActions:\n1: Get current date data\n2: Get anchor data\n3: Change music\n\nEnter a date (YYYY-MM-DD) or a name (q to quit)\n", 0.01)
        action = input("> ").strip()
        if action == "1":
            show_current(); input("\n<enter>"); clear()
        elif action == "2":
            show_anchor(); input("\n<enter>"); clear()
        elif action == "3":
            clear()
            printb("Choose music:\n1. Take Care\n2. Silver Lighting\n3. sans.\n")
            new = input("> ").strip()
            printb("Playing new track...\n")
            play_track(pg, new); t.sleep(0.6); clear()
        elif action.lower() == "q":
            break
        else:
            show_date_or_user(action); input("\n<enter>"); clear()

if __name__ == "__main__":
    main()