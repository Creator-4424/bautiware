# BAUTIWARE V1.5

# Imports ---
from __future__ import annotations
from datetime import date, timedelta, datetime, time
from pathlib import Path
from typing import Optional, Tuple, Dict, List, Set, Any
import pygame
import platform
import os
from cls import clear
from printf import printb
from clear_last import clear_last_line
import ascii as a
import sys
from time import sleep
import json
import string

# initializing mixer software ---
pygame.mixer.init()

# Config files ---
CONFIG = { # gonna have to manually update the config every year unfortunately
    "rotation_length": 8, # 8 day rotation
    "start_anchor": {"date": "2025-09-04", "cycle_day": 1},  # first day of normal school, may be changed later
    "school_weekdays": {0, 1, 2, 3, 4},  # Indexes monday-friday (Mon=0)
    "holidays": [  # YYYY-MM-DD dates
        {"date":"2025-10-13", "note":"dia de la hispanidad"}, # dia de la hispanidad
        {"date":"2025-11-10", "note":"3 day weekend"}, 
        {"date":"2025-12-08", "note":"3 day weekend"},
        {"date":"2026-05-01", "note":"3 day weekend"},
        {"date":"2026-05-15", "note":"3 day weekend"},
    ],

    "holiday_ranges": [ # all holidays that are 3 or more days
        {"start":"2025-11-27", "end":"2025-11-28", "note":"thanksgiving"}, # thanksgiving break
        {"start":"2025-12-22", "end":"2026-01-07", "note":"winter break"}, # winter break
        {"start":"2026-02-16", "end":"2026-02-20", "note":"la semana blanca"}, # la semana blanca
        {"start":"2026-03-30", "end":"2026-04-03", "note":"spring break"}, # spring break
    ],

    "half_days": { # all half days, doesnt do anything yet
        "2025-09-17",
        "2025-10-15",
        "2025-11-19",
        "2025-12-10",
        "2025-01-21",
        "2025-02-25",
        "2025-03-18",
        "2025-04-08",
        "2025-05-13",
        "2025-06-10"
    },

    "carry_over": True,  # when this is true, weekends and holidays dont advance the schedule
}

SCHEDULES = { # All schedule orders
    1: "ABCD",
    2: "EFGH",
    3: "BCDA",
    4: "FGHE",
    5: "ADCB",
    6: "EHGF",
    7: "BADC",
    8: "FEHG",
}

# Methods ---

def today(): return date.today() # every call returns an unexpired date, as opposed to a static object

def _in_range(d: date, start_iso: str, end_iso: str) -> bool: # within a multi day holiday:
    # ISO (YYYY-MM-DD) compares lexicographically, but convert to be safe
    s = date.fromisoformat(start_iso); e = date.fromisoformat(end_iso)
    return s <= d <= e

def load_from_file(filename: str | os.PathLike[str]) -> Dict[str, Any]:
    with open(f"{filename}", "r") as f:
        data = json.load(f)
    return data

def _anchor(cfg: Dict[str, Any] = CONFIG) -> Tuple[date, Any]: # gets the start anchor as a date object
    a = cfg["start_anchor"]
    return date.fromisoformat(a["date"]), int(a["cycle_day"])

def is_weekend(d: date, cfg: Dict[str, Any] = CONFIG) -> bool: # checks if the day is a weekend
    return d.weekday() not in cfg["school_weekdays"]

def is_holiday(d: date, cfg: Dict[str, Any] = CONFIG) -> Optional[str]: # checks for single day holidays and multi day holidays

    key = d.isoformat()
    
    # Check single-day holidays
    for h in cfg.get("holidays", []): # for all holidays:
        if h["date"] == key: # if it is today, then return necessary data
            return h.get("note", "Holiday")
    
    # Check multi day holidays
    for r in cfg.get("holiday_ranges", []): # same stuff basically
        if _in_range(d, r["start"], r["end"]):
            return r.get("note", "Holiday")
    
    return None

def is_half_day(d: date, cfg: Dict[str, Any] = CONFIG) -> bool: # for half days
    return d.isoformat() in cfg.get("half_days", set())

def is_school_day(d: date, cfg: Dict[str, Any] = CONFIG) -> bool: # for school days
    return not is_weekend(d, cfg) and not is_holiday(d, cfg)

def school_days_between(start: date, end: date, cfg: Dict[str, Any] = CONFIG) -> int: # counts how many school days since the anchor to a specified date

    cur = start
    count = 0

    while cur < end: # while its less than the end date: keep countin up
        cur += timedelta(days=1)
        if is_school_day(cur, cfg): # only count up if its a weekday (weekends dont avance the schedule)
            count += 1

    return count

def compute_cycle_day(target: date, cfg: Dict[str, Any] = CONFIG) -> Any:

    start_date, day = _anchor(cfg)
    rot_len = cfg["rotation_length"]

    # count how many school days since the anchor
    passed = school_days_between(start_date, target, cfg)
    # cycle advances only on school days
    day = ((day - 1 + passed) % rot_len) + 1

    return day if is_school_day(target, cfg) else None

def day_status_and_order(target: date, cfg: Dict[str, Any] = CONFIG) -> Any:

    holiday_note = is_holiday(target, cfg)
    if holiday_note: return {"status": "Holiday", "note": holiday_note, "order": None}
    if is_weekend(target, cfg): return {"status": "Weekend", "order": None}

    cd = compute_cycle_day(target, cfg)
    order = SCHEDULES.get(cd)

    if is_half_day(target, cfg): return {"status": "Half Day", "cycle_day": cd, "order": order}

    return {"status": "Normal", "cycle_day": cd, "order": order}

def get_today_order_and_status() -> Any:

    t = date.today()  # dynamically fetch today's date
    res = day_status_and_order(t)

    return t, (res["order"] if res["status"] == "Normal" else None), res


def get_current_block(order: str | None, now: time | None = None) -> tuple[str, str | None]:

    if not order: return ("No classes (Weekend/Holiday)", None)

    if now is None: now = datetime.now().time()

    b1, b2, b3, b4 = order[0], order[1], order[2], order[3]

    if   time(8,45)  <= now <= time(10,5): return (f"Block {b1}", b1)
    elif time(10,6)  <= now <= time(10,54): return ("Multipurpose time", None)
    elif time(10,55) <= now <= time(12,14): return (f"Block {b2}", b2)
    elif time(12,15) <= now <= time(13,4): return ("Lunch", None)
    elif time(13,5)  <= now <= time(14,25): return (f"Block {b3}", b3)
    elif time(14,26) <= now <= time(14,29): return ("3-4 transition", None)
    elif time(14,30) <= now <= time(15,50): return (f"Block {b4}", b4)
    elif time(15,51) <= now <= time(15,59): return ("ASA transition", None)
    elif time(16,0)  <= now <= time(17,0): return ("ASAs in session", None)
    else: return ("Out of schedule hours", None)

def get_current_data() -> None:

    clear()
    t, order, res = get_today_order_and_status()
    printb(f"\nToday is {t}:\n")
    anchor_date = date.fromisoformat(CONFIG["start_anchor"]["date"])
    if anchor_date > today(): printb("WARNING: CURRENT DATE IS BEFORE ANCHOR, DATA UNRELIABLE\n")

    printb(f"Status: {res['status']}\n")
    if 'note' in res: print(f"Note: {res['note']}")

    if res["status"] == "Normal":
        printb(f"Cycle Day: {res['cycle_day']}\n")
        printb(f"Schedule: {order}\n")
        label, current_letter = get_current_block(order)
        printb(f"Period: {label}\n")

        if current_letter:
            for entry in Path("users").glob("*.json"):
                data = load_from_file(entry)   # your loader already returns dict
                printb(f"\n{data['Name']} is in {data[current_letter][0]}, in room {data[current_letter][1]}\n\n")

def get_that_date(d)-> None: # you know you want it

    clear()
    anchor_date = date.fromisoformat(CONFIG["start_anchor"]["date"])
    manual = date.fromisoformat(d)
    result = day_status_and_order(manual)
    if anchor_date > manual: printb(f"WARNING: DATE IS BEFORE ANCHOR, DATA UNRELIABLE\n")
    print(f"{manual} Date info:\n")
    if result["status"] == "Normal":
        printb(f"Status: {result['status']}\n")
        printb(f"Cycle Day: {result['cycle_day']}\n")
        printb(f"Schedule: {result['order']}\n")

    else: printb(f"Status: {result['status']}\n")

def change_track(new_track: str)-> None:
    pygame.mixer.music.load(f"music/track{new_track}.mp3")   # put your file path here
    pygame.mixer.music.play(-1)  # -1 loops forever

def jsonToCustomFormat(json_filename: os.path) -> str:
    # Read the JSON file
    with open(f"{json_filename}", "r") as f:
        data = json.load(f)
    
    # Create custom formatted string
    output = f"Schedule for {data['Name'].capitalize()}:\n"
    output += "=" * 40 + "\n\n"
    
    for block in string.ascii_uppercase[:8]:
        subject, room = data[block.upper()]
        output += f"{block.upper()} | {subject:15s} | Room: {room}\n"
    
    output += "\n" + "=" * 40
    return output
# getting the anchor date ---
anchor_date, anchor_day = _anchor()
diff = school_days_between(anchor_date, today())

clear()
print("Loading.", end="\r") # Overwrites same line
sleep(0.6)
print("Loading..", end="\r")
sleep(0.6)
print("Loading...", end="\r")
sleep(1)

printb("Software ready")
sleep(0.5)

# load and play
pygame.mixer.music.load("music/track2.mp3") # default song
pygame.mixer.music.play(-1)  # -1 loops forever

printb(f"{a.main}\n",0.0005)

print("welcome to bautiware V1.5")
while True:
    printb("\nActions:\n1: Get current date data\n2: Get anchor data\n3: Change music\n\nEnter a date in YYYY-MM-DD format for specific data on that day, or name for their schedule\n",0.01)
    printb("Action: ")
    action = input()
    if action == "1": get_current_data()

    elif action == "2":
        clear()
        printb(f"Anchor date: {anchor_date} (Cycle Day {anchor_day})\n")
        printb(f"School days since anchor: {diff}\n\n")
    elif action == "3":
        clear()
        printb("Choose some music: \n1. Take care by Heaven Pierce Her\n2. Silver Lighting by MathewTimes2\n3. sans. by Toby Fox\n")
        new = input()
        printb(f"Playing new track...")
        change_track(new)
        sleep(1)
        clear()
    elif action == "q": break
    else:
        if not os.path.exists(f"users/{action.lower()}.json"):
            try:
                get_that_date(action)
            except ValueError:
                printb("invalid date or format")
                sleep(.5)
                clear()
        else:
            printb(f"{jsonToCustomFormat(f"users/{action}.json")}",0.02)