# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import subprocess
import os
import asyncio

TOKEN = os.environ["DISCORD_TOKEN"]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="b!", intents=intents)

@bot.event
async def on_ready():
    print("Bot起動したよ")

playing = set()

FFMPEG_PATH = "./ffmpeg/ffmpeg"  # 同梱したffmpegバイナリ

@bot.command()
async def p(ctx, url: str):
    if not ctx.author.voice:
        await ctx.send("VCに入ってね")
        return

    if ctx.channel.id in playing:
        await ctx.send("今は再生中だよ、少し待ってね")
        return

    playing.add(ctx.channel.id)
    try:
        # yt-dlpで直リンク取得
        audio_url = subprocess.check_output(
            ["yt-dlp", "-g", "-f", "bestaudio", "--no-check-certificate", "--http-chunk-size", "10M", url]
        ).decode().strip()

        vc = ctx.voice_client
        if not vc:
            vc = await ctx.author.voice.channel.connect()

        if not vc.is_playing():
            FFMPEG_OPTIONS = {
                'executable': FFMPEG_PATH,
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
            }
            vc.play(discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS))
            await ctx.send("バキバキ童貞です")
        else:
            await ctx.send("既に再生中だよ")

        while vc.is_playing():
            await asyncio.sleep(1)
        await asyncio.sleep(2)

    finally:
        playing.discard(ctx.channel.id)

@bot.command()
async def stop(ctx):
    vc = ctx.voice_client
    if vc and vc.is_playing():
        vc.stop()
        await ctx.send("再生を止めたよ")
    else:
        await ctx.send("再生中じゃないよ")

bot.run(TOKEN)
