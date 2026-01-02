# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import os
import asyncio
import feedparser
import random
from flask import Flask
from threading import Thread

TOKEN = os.environ["DISCORD_TOKEN"]

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="b!", intents=intents)

RSS_LIST = {
    "haruhi": "https://feeds.megaphone.fm/FNCOMMUNICATIONSINC3656403561",
}

random_mode = set()

# ---------------- Flask ----------------
app = Flask("")

@app.route("/")
def home():
    return "バキバキ童貞が接続されるよ。オンラインにならなかったり、コマンドに反応しない時は何度かアクセスして様子を見てね。", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)

Thread(target=run_flask, daemon=True).start()

# ---------------- Discord BOT ----------------
@bot.event
async def on_ready():
    print("Bot 起動したよ")
    await bot.change_presence(status=discord.Status.online)

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

    vc = ctx.voice_client
    if not vc:
        vc = await ctx.author.voice.channel.connect(timeout=10)

    random_mode.add(ctx.guild.id)
    await bot.change_presence(status=discord.Status.online)

    if not vc.is_playing():
        await play_random_next(ctx)

    await ctx.send("連続でランダムに再生するよ")

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
    await ctx.send("切断したよ")
    await bot.change_presence(status=discord.Status.offline)

# ---------------- 自動VC監視 ----------------
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
                await text_ch.send(
                    "誰もいないから切断するよ。"
                )
            await vc.disconnect()
            random_mode.discard(member.guild.id)
            await bot.change_presence(status=discord.Status.offline)

bot.run(TOKEN)
