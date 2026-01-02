# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import os
import asyncio
import feedparser
import random
from flask import Flask
from threading import Thread
import os

TOKEN = os.environ["DISCORD_TOKEN"]

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="b!", intents=intents)

RSS_LIST = {
    "haruhi": "https://feeds.megaphone.fm/FNCOMMUNICATIONSINC3656403561",
}

random_mode = set()
last_text_channel = {}

# ---------------- Flask ----------------
app = Flask("")

@app.route("/")
def home():
    return "バキバキ童貞だよ。", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)

Thread(target=run_flask, daemon=True).start()

# ---------------- Discord BOT ----------------
@bot.event
async def on_ready():
    print("Bot 起動したよ")

def get_audio_from_entry(entry):
    if entry.enclosures:
        return entry.enclosures[0].href
    return None

def get_random_audio_url():
    feed = feedparser.parse(random.choice(list(RSS_LIST.values())))
    entry = random.choice(feed.entries)
    return get_audio_from_entry(entry)

async def play_random_next(ctx):
    if ctx.guild.id not in random_mode:
        return

    vc = ctx.voice_client
    if not vc:
        return

    url = get_random_audio_url()
    if not url:
        return

    vc.play(
        discord.FFmpegPCMAudio(url),
        after=lambda e: asyncio.run_coroutine_threadsafe(
            play_random_next(ctx), bot.loop
        )
    )

# ---------------- コマンド ----------------
@bot.command(name="r")
async def random_play(ctx):
    if not ctx.author.voice:
        await ctx.send("VC入ってね")
        return

    last_text_channel[ctx.guild.id] = ctx.channel
    vc = ctx.voice_client or await ctx.author.voice.channel.connect()
    random_mode.add(ctx.guild.id)

    if not vc.is_playing():
        await play_random_next(ctx)

    await ctx.send("連続ランダム再生だよ")

@bot.command(name="s")
async def skip(ctx):
    vc = ctx.voice_client
    if vc and vc.is_playing():
        last_text_channel[ctx.guild.id] = ctx.channel
        vc.stop()
        await ctx.send("飛ばすよ")

@bot.command(name="l")
async def leave(ctx):
    vc = ctx.voice_client
    if vc:
        ch = last_text_channel.get(ctx.guild.id, ctx.channel)
        await ch.send("切断したよ。オフラインになるよ。")
        await vc.disconnect()
        await bot.close()
        os._exit(0)

# ---------------- 自動VC監視 ----------------
@bot.event
async def on_voice_state_update(member, before, after):
    vc = member.guild.voice_client
    if not vc:
        return

    if before.channel == vc.channel and after.channel != vc.channel:
        humans = [m for m in vc.channel.members if not m.bot]
        if len(humans) == 0:
            ch = last_text_channel.get(member.guild.id)
            if ch:
                await ch.send("誰もいないから切断したよ。オフラインになるよ。")
            await vc.disconnect()
            await bot.close()
            os._exit(0)

bot.run(TOKEN)
