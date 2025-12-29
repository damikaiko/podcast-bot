# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import os
import asyncio
import feedparser
from collections import deque

TOKEN = os.environ["DISCORD_TOKEN"]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="b!", intents=intents)

RSS_LIST = {
    "haruhi": "https://feeds.megaphone.fm/FNCOMMUNICATIONSINC3656403561",
}

queues = {}  # guild_id: deque

@bot.event
async def on_ready():
    print("起動したよ")

def get_entries(name):
    feed = feedparser.parse(RSS_LIST[name])
    return feed.entries

def get_audio(entry):
    if "enclosures" in entry and entry.enclosures:
        return entry.enclosures[0].href
    return None

async def play_next(ctx):
    q = queues.get(ctx.guild.id)
    if not q:
        return

    url = q.popleft()
    vc = ctx.voice_client
    vc.play(
        discord.FFmpegPCMAudio(
            url,
            options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
        ),
        after=lambda e: asyncio.run_coroutine_threadsafe(
            play_next(ctx), bot.loop
        )
    )

@bot.command(name="ep")
async def episodes(ctx, name: str):
    if name not in RSS_LIST:
        await ctx.send("RSSないよ")
        return
    entries = get_entries(name)
    text = "\n".join([f"{i+1}. {e.title}" for i, e in enumerate(entries[:10])])
    await ctx.send(text)

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

    url = get_audio(entries[num-1])
    if not url:
        await ctx.send("音声取れないよ")
        return

    q = queues.setdefault(ctx.guild.id, deque())
    q.append(url)

    vc = ctx.voice_client or await ctx.author.voice.channel.connect()
    if not vc.is_playing():
        await play_next(ctx)
        await ctx.send("再生するよ")
    else:
        await ctx.send("キュー入れたよ")

@bot.command(name="q")
async def queue(ctx):
    q = queues.get(ctx.guild.id)
    await ctx.send(f"{len(q) if q else 0}件だよ")

@bot.command(name="s")
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("飛ばすよ")

@bot.command(name="st")
async def stop(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        queues.get(ctx.guild.id, deque()).clear()
        await ctx.send("止めたよ")

@bot.command(name="l")
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        queues.pop(ctx.guild.id, None)
        await ctx.send("抜けたよ")

bot.run(TOKEN)
