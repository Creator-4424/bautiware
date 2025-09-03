# simple_rotation.py
from datetime import date, timedelta
import pygame
pygame.mixer.init()

# load and play
pygame.mixer.music.load("music.mp3")   # put your file path here
pygame.mixer.music.play(-1)  # -1 loops forever

today = date.today()
CONFIG = {
    "rotation_length": 8,
    "start_anchor": {"date": "2025-09-04", "cycle_day": 1},  # set yours
    "school_weekdays": {0, 1, 2, 3, 4},  # Indexes monday-friday (Mon=0)
    "holidays": {  # YYYY-MM-DD dates
        "2025-10-12",
        "2025-12-25",
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

def _anchor(cfg=CONFIG):
    a = cfg["start_anchor"]
    return date.fromisoformat(a["date"]), int(a["cycle_day"])

def is_weekend(d, cfg=CONFIG):
    return d.weekday() not in cfg["school_weekdays"]

def is_holiday(d, cfg=CONFIG):
    return d.isoformat() in cfg["holidays"]

def is_school_day(d, cfg=CONFIG):
    return not is_weekend(d, cfg) and not is_holiday(d, cfg)

def school_days_between(start: date, end: date, cfg=CONFIG):
    """
    Count how many SCHOOL days between two dates (exclusive of start).
    Assumes start <= end.
    """
    cur = start
    count = 0
    while cur < end:
        cur += timedelta(days=1)
        if is_school_day(cur, cfg):
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
    if is_holiday(target, cfg):
        return {"status": "Holiday", "order": None}
    if is_weekend(target, cfg):
        return {"status": "Weekend", "order": None}
    cd = compute_cycle_day(target, cfg)
    return {"status": "Normal", "cycle_day": cd, "order": SCHEDULES.get(cd)}
def get_current_data():
    result = day_status_and_order(today)
    print(f"\nToday is {today}:")
    anchor_date = date.fromisoformat(CONFIG["start_anchor"]["date"])
    if anchor_date > today:
        print(f"WARNING: CURRENT DATE IS BEFORE ANCHOR, DATA UNRELIABLE")
    if result["status"] == "Normal":
        print(f"  Status: {result['status']}")
        print(f"  Cycle Day: {result['cycle_day']}")
        print(f"  Schedule: {result['order']}")
    else:
        print(f"  Status: {result['status']}")

# --- demo ---
if __name__ == "__main__":
    anchor_date, anchor_day = _anchor()

    # How many school days since the anchor?
    diff = school_days_between(anchor_date, today)

    print("software ready")
    print(r"""⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡎⣮⠳⢄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢲⠀⠉⢣⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠑⢤⠀⠈⠣⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡀⠀⣼⢣⣀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢤⠄⠀⠈⢂⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣱⣧⠞⢅⡿⢌⡆⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠹⡀⠀⠀⠈⠰⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣇⠸⠙⠯⡊⢑⡾⠁⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢷⠀⠀⠀⠈⣷⢱⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⣶⡴⢁⢠⣿⣮⠇⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠇⣄⠀⠀⡇⠈⡌⠣⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⡍⠙⢿⣬⠟⠛⠁⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠹⡀⠀⠣⡉⡇⠀⣺⠀⣠⠞⣹⣶⡏⠲⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣾⣟⡿⠂⡰⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⢠⠠⠤⣄⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠢⡤⢰⠉⢸⠁⢰⠁⣾⢫⠉⡝⣷⠈⡆⠀⠀⠀⠀⠀⠀⢀⠔⠉⠻⡿⠊⢀⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⡀⢰⡔⠀⠀⠀⠈⠁⠒⠒⠤⠤⣀⣀⠀⢀⣀⡀⠀⠀⠀⠀⠀⠀⠈⠛⠀⡇⠀⠘⡀⠻⣮⡤⣵⠟⢀⠇⠀⠀⠀⠀⢀⣀⣼⣆⡀⠀⠀⣶⡆⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠉⠑⠂⠤⣄⣀⠀⠀⠀⠀⠀⠀⠉⠙⠑⢄⠩⡑⠲⢦⠀⠀⠀⢸⣥⡇⠀⠀⠘⣄⣷⠀⣿⣨⠋⠀⠀⠀⢀⠔⠁⡠⠘⣿⡿⣶⢾⠙⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⢀⣉⣒⡢⢤⣀⣀⠀⠀⠈⠂⠥⡈⠢⢸⡆⠀⠀⡸⢟⠡⣕⠶⣶⣮⡿⠿⢿⣴⣶⠴⣀⢐⢍⠳⣮⢠⣤⠏⡠⠃⠸⣢⠏⠁⠀⠀⠀⠀⠀⣀⣀⡀⠀⠀⠀
⠀⠀⠀⠀⣤⡤⡤⣼⡾⢦⡛⣦⠤⠭⠿⠿⠶⢖⠒⢚⣾⣍⠉⠉⣹⣖⣡⣾⡿⠉⠙⢠⠽⠭⠿⡔⠋⠁⢿⣦⡍⡢⢔⠈⠂⠤⠵⣤⠒⠒⠲⠲⠶⢒⡒⣦⠮⠴⣷⡧⣤⢤⣤
⠀⠀⠀⠀⢧⢦⠧⣼⣇⣀⡁⣿⠈⢀⣒⣢⡀⠀⠑⢽⣿⡿⠉⠉⠷⣮⢻⣿⠀⠀⠀⠀⢠⠤⡄⠀⢀⣀⠈⣯⡣⡇⠠⢱⠀⠀⣀⠼⡠⡠⢒⢒⣒⡎⠁⢿⢃⣸⣸⡧⠴⡤⡼
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠁⠀⠀⠈⠒⠓⠚⠉⠙⢍⢿⣟⢦⣙⣥⣨⢙⠷⠇⢸⣤⡇⠸⠾⡛⣅⣼⣮⠜⠃⢾⣍⠙⠤⠤⠜⠒⠒⠁⠀⠉⠉⠁⠀⠀⠉⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⢀⡀⠀⠙⢞⣿⣿⣏⣯⢱⣶⣲⣿⣿⣽⣶⣶⡮⣿⠙⠌⡢⠀⠐⢌⢢⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡤⠔⢊⣁⣘⣈⠢⣀⠀⠀⢀⡴⣿⣻⢷⣿⣾⣿⣿⡿⣻⣟⠇⠀⠀⠈⢪⣑⡬⠛⠑⠢⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⠔⠚⠖⠬⠭⠽⠄⠀⠀⢘⢉⣹⣹⢞⡽⣯⢳⣿⠫⠿⠟⣿⡟⡼⢄⠀⠀⠀⠘⢄⠰⣄⠀⠀⡩⢆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⡄⠾⠃⠀⠀⠀⠀⠀⠀⣀⣤⣴⡿⠟⠀⠀⠀⢸⣇⣠⡳⣧⣶⣶⢶⣼⢟⣄⣸⠆⠀⠀⠀⠀⠛⢦⢻⡞⣦⣳⣷⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⡀⠤⠂⠉⠀⠀⠀⠀⣀⣠⠤⠖⠒⠉⠉⠀⣀⣀⣀⣀⡄⡞⠻⣿⣁⠈⢛⣒⠚⡁⣼⣯⢟⢂⢤⠀⠀⠀⠀⠀⠈⠓⢕⢇⣾⣿⣖⠒⠦⣤⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⢐⠂⣭⠀⠀⣀⣀⠤⠖⠒⠉⠉⠀⠀⠀⠀⠀⢠⠏⢁⠑⡭⠙⣇⢀⠀⠈⠻⣿⡔⠶⢀⣿⠟⠁⠀⡄⡿⠀⠀⠀⠀⠀⠀⠀⠀⠛⡿⣿⣿⣷⡖⢄⡵⠄⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠑⠒⠒⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⡇⠴⠠⢊⠔⠚⡼⣦⡀⠀⠉⠸⡏⠀⢻⠇⠉⠀⢀⣤⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠑⢜⡽⡿⡿⡇⣞⢄⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡰⠆⠂⠐⠁⢰⠞⠧⣿⣻⠀⠀⠘⡇⠀⢸⠃⠀⠀⣿⣿⠟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⠛⠛⡵⢕⣪⠟⠁⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡰⠃⠀⠀⢀⣠⠇⠀⠀⠙⡿⠀⠀⠀⡇⠀⢸⡁⠀⠀⣿⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡴⠃⠀⠀⢀⡎⠁⠀⠀⠀⠀⢸⡁⠀⠀⡇⠀⢸⠆⠀⢈⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡴⠃⠀⠀⡬⠋⠀⠀⠀⠀⠀⠀⠀⢧⠀⠀⡇⠀⢸⡁⠀⣼⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡰⠃⠀⢠⠼⠁⠀⠀⠀⠀⠀⠀⠀⢀⢸⡅⣠⢻⠀⡟⡅⢄⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡰⣃⢀⣠⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠉⠻⣿⢿⣾⣿⣿⠟⠉⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⣋⣥⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⡒⢆⡸⣿⣴⡾⠇⡸⢒⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠱⡘⢁⢠⠙⡄⡈⢃⠎⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣗⠀⣹⠀⣏⠀⣺⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⠀⣿⠀⣯⠀⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⣸⠀⣇⠀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢶⢚⣤⢸⢴⡇⡤⢓⡶⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠅⣿⣻⣿⢽⣿⠸⡁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡤⠒⠣⣎⣞⡫⠈⢝⣱⣱⠜⠒⢄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠓⠄⠤⠟⠁⠀⠀⠀⠀⠚⠠⠤⠼⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                                                       
            ______  ___  _   _ _____ _____ _    _  ___  ______ _____ 
            | ___ \/ _ \| | | |_   _|_   _| |  | |/ _ \ | ___ \  ___|
            | |_/ / /_\ \ | | | | |   | | | |  | / /_\ \| |_/ / |__  
            | ___ \  _  | | | | | |   | | | |/\| |  _  ||    /|  __| 
            | |_/ / | | | |_| | | |  _| |_\  /\  / | | || |\ \| |___ 
            \____/\_| |_/\___/  \_/  \___/ \/  \/\_| |_/\_| \_\____/ 
                                                         
                                                         """)
    print("welcome to bautiware V1.0")
    while True:
        print("Actions:\n1: get current date data\n2: Get anchor data\n3: change music\n\nenter a date in YY-MM-DD format for specific data on that day")
        action = input("Action: ")
        if action == "1":
            print(get_current_data())
        elif action == "2":
            print(f"Anchor date: {anchor_date} (Cycle Day {anchor_day})")
            print(f"School days since anchor: {diff}")
        elif action == "3":
            print("what? you think im productive enough to add more than just the ultrakill terminal music? hell no. come back later for more music")
        else:
            pass