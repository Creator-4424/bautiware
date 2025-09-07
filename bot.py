# bot.py — Bautiware Discord bot
from __future__ import annotations
import os
from datetime import date, datetime
from pathlib import Path
import discord
from discord import app_commands

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
    return date.fromisoformat(s) if s else date.today()

def list_usernames() -> list[str]:
    if not USERS_DIR.exists():
        return []
    return sorted(p.stem.lower() for p in USERS_DIR.glob("*.json"))


# ---------- lifecycle ----------
@bot.event
async def on_ready():
    """Sync slash commands (instantly if DISCORD_GUILD_ID is set) and keep heartbeat logs."""
    try:
        gid = os.getenv("DISCORD_GUILD_ID")
        if gid:
            guild = discord.Object(id=int(gid))
            # copy any global cmds to guild (optional) then sync for instant availability
            tree.copy_global_to(guild=guild)
            synced = await tree.sync(guild=guild)
            print(f"[sync] Guild {gid}: {len(synced)} cmds")
        else:
            synced = await tree.sync()
            print(f"[sync] Global: {len(synced)} cmds (may take up to 1h to appear)")

        print(f"Logged in as {bot.user} (id={bot.user.id})")

        # heartbeat so Railway logs show the process is alive
        import asyncio
        async def heartbeat():
            while True:
                print("[heartbeat] alive")
                await asyncio.sleep(60)
        bot.loop.create_task(heartbeat())

    except Exception as e:
        print("[on_ready error]", repr(e))


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


@tree.command(name="period", description="Show the current period for today.")
async def period(inter: discord.Interaction):
    await inter.response.defer(thinking=True)
    d = date(2025,9,5)
    res = day_status_and_order(d)
    if res["status"] != "Normal":
        note = f" — {res.get('note')}" if "note" in res else ""
        await inter.followup.send(f"{d}: **{res['status']}**{note}")
        return

    order = res["order"]
    label, letter, next_letter = get_current_block(order, now=datetime.now().time())
    extra = f" (Block {letter})" if letter else ""
    await inter.followup.send(
        f"{d}\nStatus: **Normal**\nCycle Day: **{res['cycle_day']}**\n"
        f"Order: **{order}**\nCurrent: **{label}**{extra}"
    )


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
