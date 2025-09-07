# bot.py — Bautiware Discord bot
from __future__ import annotations
import os
from datetime import date, datetime, time
from pathlib import Path
import discord
from discord import app_commands
import json
# load .env locally (Railway uses env vars directly, this is harmless)
try:
    from dotenv import load_dotenv  # optional
    load_dotenv()
except Exception:
    pass

# --- import your core logic (no side effects) ---
from scheduleLib import (
    day_status_and_order,
    get_current_block,
    jsonToCustomFormat,
)

# ---------- Discord client / command tree ----------
intents = discord.Intents.none()  # we don't need message content
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

USERS_DIR = Path("users")


# ---------- helpers ----------
def parse_date(s: str | None) -> date:
    return date.fromisoformat(s) if s else date(2025,9,5)

def list_usernames() -> list[str]:
    if not USERS_DIR.exists():
        return []
    return sorted(p.stem.lower() for p in USERS_DIR.glob("*.json"))

USERS_DIR = Path("users")

def _load_user(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def build_class_roster(current_letter: str, order: str) -> list[str]:
    """
    Returns lines like:
    'Name — CurrentClass (Room 101) → Next: NextClass (Room 202)'
    """
    lines = []
    if not USERS_DIR.exists():
        return lines

    # Figure out the next letter in today's order
    next_letter = None
    if current_letter and order:
        try:
            idx = order.index(current_letter)
            next_letter = order[(idx + 1) % len(order)]
        except ValueError:
            next_letter = None

    # Go through every user JSON and grab their current + next classes
    for p in sorted(USERS_DIR.glob("*.json"), key=lambda x: x.stem.lower()):
        try:
            data = _load_user(p)
            name = data.get("Name", p.stem).strip()

            # Current block info
            cls, room = data.get(current_letter, [None, None])

            # Next block info (if it exists)
            if next_letter:
                next_cls, next_room = data.get(next_letter, [None, None])
                next_info = f" → Next: {next_cls} (Room {next_room})" if next_cls else " → Next: Free"
            else:
                next_info = ""

            if cls:
                lines.append(f"{name} — {cls} (Room {room}){next_info}")
            else:
                lines.append(f"{name} — <no class data>{next_info}")
        except Exception as e:
            lines.append(f"{p.stem} — <error: {e}>")

    return lines


# ---------- commands ----------
@tree.command(name="schedule", description="Show schedule status; default = today.")
@app_commands.describe(when="YYYY-MM-DD (optional)")
async def schedule(inter: discord.Interaction, when: str | None = None):
    await inter.response.defer(thinking=True)
    try:
        d = parse_date(when)
    except ValueError:
        await inter.followup.send("Invalid date. Use YYYY-MM-DD.", ephemeral=True)
        return

    res = day_status_and_order(d)
    if res["status"] == "Normal":
        msg = (
            f"**{d.isoformat()}**\n"
            f"Status: **Normal**\n"
            f"Cycle Day: **{res['cycle_day']}**\n"
            f"Order: **{res['order']}**"
        )
    elif res["status"] == "Holiday":
        note = res.get("note", "Holiday")
        msg = f"**{d.isoformat()}**\nStatus: **Holiday** — {note}"
    else:
        msg = f"**{d.isoformat()}**\nStatus: **{res['status']}**"
    await inter.followup.send(msg)


@tree.command(name="period", description="Show the current period for today, plus everyone’s class.")
async def period(inter: discord.Interaction):
    await inter.response.defer(thinking=True)

    d = date(2025,9,5)
    res = day_status_and_order(d)

    # Not a normal school day
    if res["status"] != "Normal":
        note = f" — {res.get('note')}" if "note" in res else ""
        await inter.followup.send(f"{d}: **{res['status']}**{note}")
        return

    order = res["order"]
    label, letter, next_letter = get_current_block(order, now=time(14,20))

    # If it's Lunch/ASA/etc. there is no block letter
    header = (
        f"**{d}**\n"
        f"Status: **Normal**  •  Cycle Day: **{res['cycle_day']}**  •  Order: **{order}**\n"
        f"Current: **{label}**" + (f" (Block {letter})" if letter else "")
    )

    if not letter:
        await inter.followup.send(header + "\n\n_No active class block right now._")
        return

    # Build roster for the current block
    roster = build_class_roster(letter,order)

    if not roster:
        await inter.followup.send(header + f"\n\n_No user schedules found for Block **{letter}**._")
        return

    # Send roster in tidy chunks to avoid the 2000-char limit
    lines = roster
    chunks = []
    cur = "```\n"
    for line in lines:
        if len(cur) + len(line) + 2 > 1900:  # keep margin
            cur += "```"
            chunks.append(cur)
            cur = "```\n"
        cur += line + "\n"
    cur += "```"
    chunks.append(cur)

    # First message: header + first chunk. Then any remaining chunks.
    await inter.followup.send(header + "\n\n" + chunks[0])
    for extra in chunks[1:]:
        await inter.followup.send(extra)


@tree.command(name="user", description="Show a user's stored schedule (users/<name>.json).")
@app_commands.describe(name="User name (file without .json)")
async def user(inter: discord.Interaction, name: str):
    await inter.response.defer(thinking=True, ephemeral=False)
    path = USERS_DIR / f"{name.lower()}.json"
    if not path.exists():
        await inter.followup.send(f"No user file found for `{name}`.", ephemeral=True)
        return
    try:
        pretty = jsonToCustomFormat(path)
    except Exception as e:
        await inter.followup.send(f"Failed to read `{name}`: {e}", ephemeral=True)
        return
    await inter.followup.send(f"```\n{pretty}\n```")


# ---- autocomplete for /user name ----
@user.autocomplete("name")
async def user_autocomplete(interaction: discord.Interaction, current: str):
    names = list_usernames()
    q = current.lower()
    starts = [n for n in names if n.startswith(q)]
    contains = [n for n in names if q in n and n not in starts] if q else []
    picks = (starts + contains)[:25]  # Discord limit
    return [app_commands.Choice(name=n, value=n) for n in picks]


# ---- global error handler (so failures show in logs + user gets a message) ----
@tree.error
async def on_app_cmd_error(interaction: discord.Interaction, error: Exception):
    print("[command error]", repr(error))
    try:
        if interaction.response.is_done():
            await interaction.followup.send("Something broke running that command.", ephemeral=True)
        else:
            await interaction.response.send_message("Something broke running that command.", ephemeral=True)
    except Exception as e:
        print("[error notify failed]", e)


# ---------- entry ----------
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise SystemExit("Set DISCORD_TOKEN env var.")
    print("[start] launching bot…")
    bot.run(token)  # blocks forever
