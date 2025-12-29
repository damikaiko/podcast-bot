# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import os
import asyncio
import feedparser
from collections import deque
from flask import Flask
from threading import Thread

TOKEN = os.environ["DISCORD_TOKEN"]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="b!", intents=intents)

# 名前付きRSS
RSS_LIST = {
    "haruhi": "https://feeds.megaphone.fm/FNCOMMUNICATIONSINC3656403561",
}

queues = {}  # guild_id: deque

# ---------------- Flask 部分 ----------------
app = Flask("")

@app.route("/")
def home():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)

Thread(target=run_flask).start()  # 別スレッドで起動

# ---------------- Discord BOT ----------------
@bot.event
async def on_ready():
    print("Bot 起動したよ")

def get_entries(name):
    feed = feedparser.parse(RSS_LIST[name])
    return feed.entries

def get_audio_from_entry(entry):
    if "enclosures" in entry and entry.enclosures:
        return entry.enclosures[0].href
    return None

async def play_next(ctx):
    q = queues.get(ctx.guild.id)
    if not q or not q:
        return

    audio_url = q.popleft()
    vc = ctx.voice_client
    vc.play(discord.FFmpegPCMAudio(audio_url),
            after=lambda e: asyncio.run_coroutine_threadsafe(
                play_next(ctx), bot.loop))

# 話数一覧
@bot.command(name="ep")
async def episodes(ctx, name: str):
    if name not in RSS_LIST:
        await ctx.send("知らないRSSだよ")
        return

    entries = get_entries(name)
    msg = "\n".join([f"{i+1}. {e.title}" for i, e in enumerate(entries[:10])])
    await ctx.send(msg)

# 再生 / 追加
@bot.command(name="p")
async def play(ctx, name: str, num: int):
    if not ctx.author.voice:
        await ctx.send("VC入ってね")
        return
    if name not in RSS_LIST:
        await ctx.send("RSSないよ")
        return

    entries = get_entries(name)
    if num < 1 or num > len(entries):
        await ctx.send("番号違うよ")
        return

    audio_url = get_audio_from_entry(entries[num-1])
    if not audio_url:
        await ctx.send("音声取れないよ")
        return

    q = queues.setdefault(ctx.guild.id, deque())
    q.append(audio_url)

    vc = ctx.voice_client or await ctx.author.voice.channel.connect()
    if not vc.is_playing():
        await play_next(ctx)
        await ctx.send("再生するよ")
    else:
        await ctx.send("キューに入れたよ")

# キュー表示
@bot.command(name="q")
async def queue(ctx):
    q = queues.get(ctx.guild.id)
    if not q:
        await ctx.send("空だよ")
        return
    await ctx.send(f"{len(q)}件入ってるよ")

# スキップ
@bot.command(name="s")
async def skip(ctx):
    vc = ctx.voice_client
    if vc and vc.is_playing():
        vc.stop()
        await ctx.send("飛ばすよ")

# 停止
@bot.command(name="st")
async def stop(ctx):
    vc = ctx.voice_client
    if vc:
        vc.stop()
        queues[ctx.guild.id].clear()
        await ctx.send("止めたよ")

# 退出
@bot.command(name="l")
async def leave(ctx):
    vc = ctx.voice_client
    if vc:
        await vc.disconnect()
        queues.pop(ctx.guild.id, None)
        await ctx.send("抜けたよ")

bot.run(TOKEN)
