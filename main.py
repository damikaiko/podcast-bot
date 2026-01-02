# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import os
import asyncio
import feedparser
import random
from flask import Flask
from threading import Thread
import requests
import time

TOKEN = os.environ["DISCORD_TOKEN"]

# ---------------- Flask ----------------
app = Flask("")

bot_task = None  # BOT起動状態を保持
keep_alive_task = None  # Keep Aliveスレッド制御

@app.route("/")
def home():
    global bot_task
    loop = asyncio.get_event_loop()
    if not bot_task or bot_task.done():
        bot_task = loop.create_task(start_bot())
        return "バキバキ童貞を起動したよ。", 200
    return "バキバキ童貞はすでに起動中だよ。", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)

Thread(target=run_flask, daemon=True).start()

# ---------------- Discord BOT ----------------
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="b!", intents=intents)

RSS_LIST = {
    "haruhi": "https://feeds.megaphone.fm/FNCOMMUNICATIONSINC3656403561",
}

random_mode = set()

async def start_bot():
    await bot.start(TOKEN)

@bot.event
async def on_ready():
    print("Bot 起動したよ")

def get_audio_from_entry(entry):
    if entry.enclosures:
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
    vc = ctx.voice_client
    if not vc:
        return

    url = get_random_audio_url()
    if not url:
        return

    if not vc.is_playing():
        vc.play(
            discord.FFmpegPCMAudio(url),
            after=lambda e: asyncio.run_coroutine_threadsafe(
                play_random_next(ctx), bot.loop
            )
        )

@bot.command(name="r")
async def random_play(ctx):
    if not ctx.author.voice:
        await ctx.send("VC入ってね")
        return

    vc = ctx.voice_client
    try:
        if not vc:
            vc = await ctx.author.voice.channel.connect(timeout=10)
    except asyncio.TimeoutError:
        await ctx.send("VCに接続できなかったよ。再度コマンドを入力してね。")
        return

    random_mode.add(ctx.guild.id)
    await play_random_next(ctx)
    await ctx.send("連続ランダム再生だよ")

    # ランダム再生中のみKeep Alive開始
    global keep_alive_task
    if not keep_alive_task:
        keep_alive_task = Thread(target=keep_alive, daemon=True)
        keep_alive_task.start()

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
        await ctx.send("VCから切断したよ。オフラインになるよ。")
        await bot.close()
        global bot_task, keep_alive_task
        bot_task = None
        keep_alive_task = None

@bot.event
async def on_voice_state_update(member, before, after):
    vc = member.guild.voice_client
    if not vc:
        return

    if before.channel == vc.channel and after.channel != vc.channel:
        humans = [m for m in vc.channel.members if not m.bot]
        if len(humans) == 0:
            text_ch = discord.utils.get(
                member.guild.text_channels,
                name=vc.channel.name
            )
            if text_ch:
                await text_ch.send("誰もいないから切断したよ。オフラインになるよ。")
            await vc.disconnect()
            random_mode.discard(member.guild.id)
            await bot.close()
            global bot_task, keep_alive_task
            bot_task = None
            keep_alive_task = None

# ---------------- Keep Alive ----------------
def keep_alive():
    url = os.environ.get("APP_URL")  # Render の自分のアプリURL
    while random_mode:  # ランダム再生中のみ動く
        try:
            if url:
                requests.get(url)
        except Exception:
            pass
        time.sleep(60 * 5)  # 5分ごとにアクセス
