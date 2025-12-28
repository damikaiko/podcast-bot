# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import subprocess
import os

TOKEN = os.environ["DISCORD_TOKEN"]

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="b!", intents=intents)

@bot.event
async def on_ready():
    print("バキバキ童貞です")

@bot.command()
async def p(ctx, url: str):
    if not ctx.author.voice:
        await ctx.send("VCに入ってね")
        return

    # yt-dlpで直リンク取得
    audio_url = subprocess.check_output(
        ["yt-dlp", "-g", "-f", "bestaudio", url]
    ).decode().strip()

    # 既存VCを再利用
    vc = ctx.voice_client
    if not vc:
        vc = await ctx.author.voice.channel.connect()

    # 再生
    if not vc.is_playing():
        vc.play(discord.FFmpegPCMAudio(audio_url))
        await ctx.send("再生するよ")
    else:
        await ctx.send("既に再生中だよ")

bot.run(TOKEN)


