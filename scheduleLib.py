from __future__ import annotations
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import json
import string

# ----------------- Config -----------------
CONFIG: Dict[str, Any] = {
    "rotation_length": 8,
    "start_anchor": {"date": "2025-09-04", "cycle_day": 1},
    "school_weekdays": {0, 1, 2, 3, 4},
    "holidays": [
        {"date":"2025-10-13", "note":"dia de la hispanidad"},
        {"date":"2025-11-10", "note":"3 day weekend"},
        {"date":"2025-12-08", "note":"3 day weekend"},
        {"date":"2026-05-01", "note":"3 day weekend"},
        {"date":"2026-05-15", "note":"3 day weekend"},
    ],
    "holiday_ranges": [
        {"start":"2025-11-27", "end":"2025-11-28", "note":"thanksgiving"},
        {"start":"2025-12-22", "end":"2026-01-07", "note":"winter break"},
        {"start":"2026-02-16", "end":"2026-02-20", "note":"la semana blanca"},
        {"start":"2026-03-30", "end":"2026-04-03", "note":"spring break"},
    ],
    "half_days": {
        "2025-09-17","2025-10-15","2025-11-19","2025-12-10","2025-01-21",
        "2025-02-25","2025-03-18","2025-04-08","2025-05-13","2025-06-10"
    },
    "carry_over": True,
}

SCHEDULES: Dict[int, str] = {
    1: "ABCD", 2: "EFGH", 3: "BCDA", 4: "FGHE",
    5: "ADCB", 6: "EHGF", 7: "BADC", 8: "FEHG",
}

# ----------------- File utils -----------------
def load_from_file(filename: str | Path) -> Dict[str, Any]:
    p = Path(filename)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)

def jsonToCustomFormat(json_filename: str | Path) -> str:
    data = load_from_file(json_filename)
    out = [f"Schedule for {data['Name'].capitalize()}:", "=" * 40, ""]
    for block in string.ascii_uppercase[:8]:
        subj, room = data[block]
        out.append(f"{block} | {subj:15s} | Room: {room}")
    out.extend(["", "=" * 40])
    return "\n".join(out)

# ----------------- Core helpers -----------------
def _in_range(d: date, start_iso: str, end_iso: str) -> bool:
    s = date.fromisoformat(start_iso); e = date.fromisoformat(end_iso)
    return s <= d <= e

def _anchor(cfg: Dict[str, Any] = CONFIG) -> Tuple[date, int]:
    a = cfg["start_anchor"]
    return date.fromisoformat(a["date"]), int(a["cycle_day"])

def is_weekend(d: date, cfg: Dict[str, Any] = CONFIG) -> bool:
    return d.weekday() not in cfg["school_weekdays"]

def is_holiday(d: date, cfg: Dict[str, Any] = CONFIG) -> Optional[str]:
    key = d.isoformat()
    for h in cfg.get("holidays", []):
        if h["date"] == key:
            return h.get("note", "Holiday")
    for r in cfg.get("holiday_ranges", []):
        if _in_range(d, r["start"], r["end"]):
            return r.get("note", "Holiday")
    return None

def is_half_day(d: date, cfg: Dict[str, Any] = CONFIG) -> bool:
    return d.isoformat() in cfg.get("half_days", set())

def is_school_day(d: date, cfg: Dict[str, Any] = CONFIG) -> bool:
    return (not is_weekend(d, cfg)) and (is_holiday(d, cfg) is None)

def school_days_between(start: date, end: date, cfg: Dict[str, Any] = CONFIG) -> int:
    cur, count = start, 0
    while cur < end:
        cur += timedelta(days=1)
        if is_school_day(cur, cfg):
            count += 1
    return count

def compute_cycle_day(target: date, cfg: Dict[str, Any] = CONFIG) -> Optional[int]:
    start_date, day = _anchor(cfg)
    rot_len = cfg["rotation_length"]
    passed = school_days_between(start_date, target, cfg)
    day = ((day - 1 + passed) % rot_len) + 1
    return day if is_school_day(target, cfg) else None

def day_status_and_order(target: date, cfg: Dict[str, Any] = CONFIG) -> Dict[str, Any]:
    note = is_holiday(target, cfg)
    if note:
        return {"status": "Holiday", "note": note, "order": None}
    if is_weekend(target, cfg):
        return {"status": "Weekend", "order": None}
    cd = compute_cycle_day(target, cfg)
    order = SCHEDULES.get(cd)
    if is_half_day(target, cfg):
        return {"status": "Half Day", "cycle_day": cd, "order": order}
    return {"status": "Normal", "cycle_day": cd, "order": order}

def get_current_block(order: Optional[str],
                      now: Optional[time] = None) -> Tuple[str, Optional[str],Optional[str]]:
    if not order:
        return ("No classes (Weekend/Holiday)", None,None)
    now = time(13,30)
    b1,b2,b3,b4 = order[0], order[1], order[2], order[3]

    def between(a: tuple[int,int], b: tuple[int,int]) -> bool:
        return time(*a) <= now <= time(*b)

    if   between((8,45),(10,5)):   return (f"Block {b1}", b1,b2)
    elif between((10,6),(10,54)):  return ("Multipurpose time", None,b2)
    elif between((10,55),(12,14)): return (f"Block {b2}", b2,b3)
    elif between((12,15),(13,4)):  return ("Lunch", None,b3)
    elif between((13,5),(14,25)):  return (f"Block {b3}", b3,b4)
    elif between((14,26),(14,29)): return ("3-4 transition", None,b4)
    elif between((14,30),(15,50)): return (f"Block {b4}", b4,None)
    elif between((15,51),(15,59)): return ("ASA transition", None,None)
    elif between((16,0),(17,0)):   return ("ASAs in session", None,None)
    else:                           return ("Out of schedule hours", None,None)

def get_today_order_and_status() -> Tuple[date, Optional[str], Dict[str, Any]]:
    t = date.today()
    res = day_status_and_order(t)
    return t, (res["order"] if res["status"] == "Normal" else None), res
