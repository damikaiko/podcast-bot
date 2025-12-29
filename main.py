# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import subprocess
import os
import asyncio
import feedparser

TOKEN = os.environ["DISCORD_TOKEN"]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="b!", intents=intents)

# 名前付きRSSだよ
RSS_LIST = {
    "gera": "https://feeds.soundcloud.com/users/soundcloud:users:XXXXX/sounds.rss",
}

@bot.event
async def on_ready():
    print("起動したよ")

playing = set()

def get_rss_audio(rss_url: str) -> str | None:
    feed = feedparser.parse(rss_url)
    if not feed.entries:
        return None
    entry = feed.entries[0]
    if "enclosures" in entry and entry.enclosures:
        return entry.enclosures[0].href
    return None

@bot.command()
async def list(ctx):
    names = ", ".join(RSS_LIST.keys())
    await ctx.send(f"登録RSS: {names}")

@bot.command()
async def p(ctx, arg: str):
    if not ctx.author.voice:
        await ctx.send("VCに入ってね")
        return

    if ctx.channel.id in playing:
        await ctx.send("再生中だよ")
        return

    playing.add(ctx.channel.id)
    try:
        # 名前付きRSS
        if arg in RSS_LIST:
            audio_url = get_rss_audio(RSS_LIST[arg])
            if not audio_url:
                await ctx.send("RSS取得できなかったよ")
                return
        else:
            # 通常URL
            try:
                audio_url = subprocess.check_output(
                    ["yt-dlp", "-g", "-f", "bestaudio", arg],
                    stderr=subprocess.DEVNULL
                ).decode().strip()
            except subprocess.CalledProcessError:
                await ctx.send("URL失敗だよ")
                return

        vc = ctx.voice_client or await ctx.author.voice.channel.connect()
        vc.play(discord.FFmpegPCMAudio(audio_url))
        await ctx.send("再生するよ")

        while vc.is_playing():
            await asyncio.sleep(1)

    finally:
        playing.discard(ctx.channel.id)

@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.send("止めたよ")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("抜けたよ")

bot.run(TOKEN)
