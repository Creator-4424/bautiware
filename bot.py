# bot.py
from __future__ import annotations
import os
from datetime import date, datetime
import discord
from discord import app_commands

# import your library module (NOT main.py)
from scheduleLib import (
    day_status_and_order,
    get_current_block,
    jsonToCustomFormat,
)

# ---- Bot setup ----
intents = discord.Intents.none()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

GUILD_ID = os.getenv("DISCORD_GUILD_ID")  # optional: speeds up sync in one server

def parse_date(s: str | None) -> date:
    return date.fromisoformat(s) if s else date.today()

# ---- /schedule ----
@tree.command(name="schedule", description="Show schedule status; default = today.")
@app_commands.describe(when="YYYY-MM-DD (optional)")
async def schedule(inter: discord.Interaction, when: str | None = None):
    try:
        d = parse_date(when)
    except ValueError:
        await inter.response.send_message("Invalid date. Use YYYY-MM-DD.", ephemeral=True)
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
    await inter.response.send_message(msg)

# ---- /period ----
@tree.command(name="period", description="Show the current period for today.")
async def period(inter: discord.Interaction):
    d = date.today()
    res = day_status_and_order(d)
    if res["status"] != "Normal":
        note = f" — {res.get('note')}" if "note" in res else ""
        await inter.response.send_message(f"{d}: **{res['status']}**{note}")
        return
    order = res["order"]
    label, letter = get_current_block(order, now=datetime.now().time())
    extra = f" (Block {letter})" if letter else ""
    await inter.response.send_message(
        f"{d}\nStatus: **Normal**\nCycle Day: **{res['cycle_day']}**\n"
        f"Order: **{order}**\nCurrent: **{label}**{extra}"
    )

# ---- /user ----
@tree.command(name="user", description="Show a user's stored schedule (users/<name>.json).")
@app_commands.describe(name="User name (file without .json)")
async def user(inter: discord.Interaction, name: str):
    path = os.path.join("users", f"{name.lower()}.json")
    if not os.path.exists(path):
        await inter.response.send_message(f"No user file found for `{name}`.", ephemeral=True)
        return
    try:
        pretty = jsonToCustomFormat(path)
    except Exception as e:
        await inter.response.send_message(f"Failed to read `{name}`: {e}", ephemeral=True)
        return
    await inter.response.send_message(f"```\n{pretty}\n```")

@bot.event
async def on_ready():
    try:
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            await tree.sync(guild=guild)
        else:
            await tree.sync()
        print(f"Logged in as {bot.user}. Commands synced.")
    except Exception as e:
        print("Slash command sync failed:", e)

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise SystemExit("Set DISCORD_TOKEN env var.")
    bot.run(token)
