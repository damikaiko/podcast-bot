# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import subprocess
import os

TOKEN = os.environ["MTQ1NDcwMjU4OTU1OTE4MTM4OQ.GIcyMy.hI9p0XCVwrzF99_a_6O2QQrkQmOiVJYcblQkFI"]

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="b!", intents=intents)

@bot.event
async def join():
    print("バキバキ童貞です")

@bot.command()
async def p(ctx, url: str):
    if not ctx.author.voice:
        await ctx.send("VCに入ってね")
        return

    audio_url = subprocess.check_output(
        ["yt-dlp", "-g", "-f", "bestaudio", url]
    ).decode().strip()

    vc = ctx.voice_client or await ctx.author.voice.channel.connect()
    vc.play(discord.FFmpegPCMAudio(audio_url))
    await ctx.send("再生するよ")

bot.run(TOKEN)

