import discord
from discord.ext import commands
import asyncio
import threading
import json
import os
import sys
import dotenv

dotenv.load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

CHANNEL_FILE = "channels.json"


# ----------------------------
# Persistent channel registry
# ----------------------------
def load_channels():
    if not os.path.exists(CHANNEL_FILE):
        return {}
    with open(CHANNEL_FILE, "r") as f:
        return json.load(f)


def save_channels(data):
    with open(CHANNEL_FILE, "w") as f:
        json.dump(data, f, indent=2)


channels = load_channels()


# ----------------------------
# Discord setup
# ----------------------------
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"[BOT] Logged in as {bot.user} ({bot.user.id})")
    print("[BOT] Ready for CLI commands: send <message>")


# ----------------------------
# Optional: register channel
# ----------------------------
@bot.command()
@commands.has_permissions(administrator=True)
async def register(ctx):
    """Registers the current channel as a broadcast target"""
    guild_id = str(ctx.guild.id)
    channel_id = ctx.channel.id

    channels[guild_id] = channel_id
    save_channels(channels)

    await ctx.send("✅ This channel is now registered for broadcasts.")


# ----------------------------
# Broadcast logic
# ----------------------------
async def broadcast_message(message: str):
    if not channels:
        print("[WARN] No channels registered.")
        return

    print("\n[BROADCAST PLAN]")
    targets = []

    for guild_id, channel_id in channels.items():
        guild = bot.get_guild(int(guild_id))
        if not guild:
            continue

        channel = guild.get_channel(channel_id)
        if not channel:
            continue

        targets.append(channel)
        print(f"- {guild.name} -> #{channel.name}")

    if not targets:
        print("[WARN] No valid channels found.")
        return

    confirm = input("\nType YES to send: ")
    if confirm != "YES":
        print("Cancelled.")
        return

    for channel in targets:
        try:
            await channel.send(message)
        except Exception as e:
            print(f"[ERROR] Failed in {channel}: {e}")

    print("[DONE] Message sent.")


# ----------------------------
# CLI thread
# ----------------------------
def cli_loop():
    while True:
        try:
            cmd = input("> ").strip()

            if cmd.startswith("send "):
                msg = cmd[len("send "):]

                fut = asyncio.run_coroutine_threadsafe(
                    broadcast_message(msg),
                    bot.loop
                )
                fut.result()

            elif cmd == "list":
                print(json.dumps(channels, indent=2))

            elif cmd.startswith("add "):
                print("Use !register inside Discord instead.")

            elif cmd in ("exit", "quit"):
                print("Shutting down...")
                os._exit(0)

            else:
                print("Commands: send <msg>, list, exit")

        except Exception as e:
            print(f"[CLI ERROR] {e}")


# ----------------------------
# Run bot + CLI
# ----------------------------
def start_cli():
    thread = threading.Thread(target=cli_loop, daemon=True)
    thread.start()


if __name__ == "__main__":
    if not TOKEN:
        print("Missing DISCORD_TOKEN env var")
        sys.exit(1)

    start_cli()
    bot.run(TOKEN)
