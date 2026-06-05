import discord
from discord.ext import commands
import os
import threading
from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn
import asyncio

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -----------------------
# In-memory cache
# -----------------------
guild_cache = {}   # guild_id -> name of guild
channel_cache = {} # guild_id -> list of (channel_id, name)
user_cache = {}    # guild_id -> list of (user_id, name)

# -----------------------
# Discord events
# -----------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    for g in bot.guilds:
        guild_cache[g.id] = g.name
        channel_cache[g.id] = [
            (c.id, c.name)
            for c in g.text_channels
        ]
        user_cache[g.id] = [
            (u.id, u.name)
            for u in g.members
        ]


# -----------------------
# IPC API (FastAPI)
# -----------------------
app = FastAPI()

@app.get("/guilds")
def get_guilds():
    return guild_cache

@app.get("/channels/{guild_id}")
def get_channels(guild_id: int):
    return channel_cache.get(guild_id, [])

@app.get("/users/{guild_id}")
def get_users(guild_id: int):
    return user_cache.get(guild_id, [])

@app.post("/send")
def send_message(payload: dict):
    guild_id = payload["guild_id"]
    channel_id = payload["channel_id"]
    message = payload["message"]

    async def _send():
        channel = bot.get_channel(channel_id)
        if channel:
            await channel.send(message)

    asyncio.run_coroutine_threadsafe(_send(), bot.loop)
    return {"status": "sent"}


# -----------------------
# Run FastAPI in thread
# -----------------------
def run_api():
    uvicorn.run(app, host="127.0.0.1", port=8000)

threading.Thread(target=run_api, daemon=True).start()

bot.run(TOKEN)
