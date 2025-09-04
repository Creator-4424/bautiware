# simple_rotation.py
from datetime import date, timedelta, datetime, time
import pygame
import platform
import os
from cls import clear
from printf import printb
from clear_last import clear_last_line
import ascii as a
import sys
from time import sleep

pygame.mixer.init()

today = date.today()
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

def _in_range(d: date, start_iso: str, end_iso: str) -> bool: # within a multi day holiday:
    # ISO (YYYY-MM-DD) compares lexicographically, but convert to be safe
    s = date.fromisoformat(start_iso); e = date.fromisoformat(end_iso)
    return s <= d <= e

def _anchor(cfg=CONFIG): # gets the start anchor as a date object
    a = cfg["start_anchor"]
    return date.fromisoformat(a["date"]), int(a["cycle_day"])

def is_weekend(d, cfg=CONFIG): # checks if the day is a weekend
    return d.weekday() not in cfg["school_weekdays"]

def is_holiday(d: date, cfg=CONFIG): # checks for single day holidays and multi day holidays
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

def is_half_day(d, cfg=CONFIG): # for half days
    return d.isoformat() in cfg.get("half_days", set())

def is_school_day(d, cfg=CONFIG): # for school days
    return not is_weekend(d, cfg) and not is_holiday(d, cfg)

def school_days_between(start: date, end: date, cfg=CONFIG): # counts how many school days since the anchor to a specified date

    cur = start
    count = 0
    while cur < end: # while its less than the end date: keep countin up
        cur += timedelta(days=1)
        if is_school_day(cur, cfg): # only count up if its a weekday (weekends dont avance the schedule)
            count += 1
    return count

def compute_cycle_day(target, cfg=CONFIG):
    """Return cycle day number 1..8 for school days; None on weekend/holiday."""
    start_date, day = _anchor(cfg)
    rot_len = cfg["rotation_length"]

    # count how many school days since the anchor
    passed = school_days_between(start_date, target, cfg)
    # cycle advances only on school days
    day = ((day - 1 + passed) % rot_len) + 1
    return day if is_school_day(target, cfg) else None

def day_status_and_order(target, cfg=CONFIG):
    holiday_note = is_holiday(target, cfg)
    if holiday_note:
        return {"status": "Holiday", "note": holiday_note, "order": None}
    if is_weekend(target, cfg):
        return {"status": "Weekend", "order": None}

    cd = compute_cycle_day(target, cfg)
    order = SCHEDULES.get(cd)

    if is_half_day(target, cfg):
        return {"status": "Half Day", "cycle_day": cd, "order": order}

    return {"status": "Normal", "cycle_day": cd, "order": order}
def get_current_block():
    now = datetime.now().time()
    cd = compute_cycle_day(today)
    order = SCHEDULES.get(cd)
    if time(8,45) <= now <= time(10,5):
        current = f"Block {order[0]}"
    elif time(10,6) <= now <= time(10,54):
        current = "Multipurpose time"
    elif time(10,55) <= now <= time(12,14):
        current = f"Block {order[1]}"
    elif time(12,15) <= now <= time(13,4):
        current = "Lunch"
    elif time(13,5) <= now <= time(14,25):
        current = f"Block {order[2]}"
    elif time(14,26) <= now <= time(14,29):
        current = "3-4 transition"
    elif time(14,30) <= now <= time(15,50):
        current = f"Block {order[3]}"
    elif time(15,51) <= now <= time(15,59):
        current = "ASA transition"
    elif time(16) <= now <= time(17):
        current = "ASAs in session"
    else:
        current = f"Out of schedule hours"
    return current
def get_current_data():
    result = day_status_and_order(today)
    print(f"\nToday is {today}:")
    anchor_date = date.fromisoformat(CONFIG["start_anchor"]["date"])
    if anchor_date > today:
        print(f"WARNING: CURRENT DATE IS BEFORE ANCHOR, DATA UNRELIABLE")
    if result["status"] == "Normal":
        print(f"Status: {result['status']}")
        print(f"Cycle Day: {result['cycle_day']}")
        print(f"Schedule: {result['order']}")
        print(f"Period: {get_current_block()}")
    else:
        print(f"  Status: {result['status']}")
def get_manual_date(d):
    anchor_date = date.fromisoformat(CONFIG["start_anchor"]["date"])
    manual = date.fromisoformat(d)
    result = day_status_and_order(manual)
    if anchor_date > today:
        print(f"WARNING: DATE IS BEFORE ANCHOR, DATA UNRELIABLE")
    print(f"{manual} date info:")
    if result["status"] == "Normal":
        print(f"Status: {result['status']}")
        print(f"Cycle Day: {result['cycle_day']}")
        print(f"Schedule: {result['order']}")
    else:
        print(f"Status: {result['status']}")
def change_track(new_track):
    pygame.mixer.music.load(f"music/track{new_track}.mp3")   # put your file path here
    pygame.mixer.music.play(-1)  # -1 loops forever

# --- demo ---
anchor_date, anchor_day = _anchor()

# How many school days since the anchor?
diff = school_days_between(anchor_date, today)

clear()
print("Loading.", end="\r") # Overwrites same line
sleep(0.6)
print("Loading..", end="\r")
sleep(0.6)
print("Loading...", end="\r")
sleep(1)

printb("software ready")
sleep(0.5)

# load and play
pygame.mixer.music.load("music/track1.mp3")   # put your file path here
pygame.mixer.music.play(-1)  # -1 loops forever

print(a.main)

print("welcome to bautiware V1.3")
while True:
    print("Actions:\n1: get current date data\n2: Get anchor data\n3: change music\n\nenter a date in YYYY-MM-DD format for specific data on that day")
    action = input("Action: ")
    if action == "1":
        get_current_data()
    elif action == "2":
        print(f"Anchor date: {anchor_date} (Cycle Day {anchor_day})")
        print(f"School days since anchor: {diff}")
    elif action == "3":
        clear()
        printb("Choose some music: \n1. Take care by Heaven Pierce Her\n2. Silver Lighting by MathewTimes2\n3. sans. by Toby Fox\n")
        new = input()
        printb(f"playing new track...")
        change_track(new)
        sleep(1)
    else:
        try:
            get_manual_date(action)
        except ValueError:
            print("invalid date or format")
    clear()