# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import os
import asyncio
import feedparser
import random
from collections import deque
from flask import Flask
from threading import Thread

TOKEN = os.environ["DISCORD_TOKEN"]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="b!", intents=intents)

RSS_LIST = {
    "haruhi": "https://feeds.megaphone.fm/FNCOMMUNICATIONSINC3656403561",
}

queues = {}
random_mode = set()  # guild_id 管理

# ---------------- Flask ----------------
app = Flask("")

@app.route("/")
def home():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)

Thread(target=run_flask).start()

# ---------------- Discord BOT ----------------
@bot.event
async def on_ready():
    print("Bot 起動したよ")

def get_audio_from_entry(entry):
    if "enclosures" in entry and entry.enclosures:
        return entry.enclosures[0].href
    return None

def get_random_audio_url():
    feed_url = random.choice(list(RSS_LIST.values()))
    feed = feedparser.parse(feed_url)
    entry = random.choice(feed.entries)
    return get_audio_from_entry(entry)

async def play_random_next(ctx):
    if ctx.guild.id not in random_mode:
        return

    audio_url = get_random_audio_url()
    if not audio_url:
        return

    vc = ctx.voice_client
    vc.play(
        discord.FFmpegPCMAudio(audio_url),
        after=lambda e: asyncio.run_coroutine_threadsafe(
            play_random_next(ctx), bot.loop)
    )

# ---------------- コマンド ----------------

@bot.command(name="r")
async def random_play(ctx):
    if not ctx.author.voice:
        await ctx.send("VC入ってね")
        return

    vc = ctx.voice_client or await ctx.author.voice.channel.connect()
    random_mode.add(ctx.guild.id)

    if not vc.is_playing():
        await play_random_next(ctx)

    await ctx.send("連続ランダム再生だよ")

@bot.command(name="s")
async def skip(ctx):
    vc = ctx.voice_client
    if vc and vc.is_playing():
        vc.stop()
        await ctx.send("飛ばすよ")

@bot.command(name="l")
async def leave(ctx):
    vc = ctx.voice_client
    if vc:
        await vc.disconnect()
        random_mode.discard(ctx.guild.id)
        await ctx.send("抜けたよ")

bot.run(TOKEN)


