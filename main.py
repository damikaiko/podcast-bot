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
    print("起動したよ")

playing = set()

@bot.command()
async def p(ctx, url: str):
    if not ctx.author.voice:
        await ctx.send("VCに入ってね")
        return

    if ctx.channel.id in playing:
        await ctx.send("再生中だよ")
        return

    playing.add(ctx.channel.id)
    try:
        audio_url = subprocess.check_output(
            ["yt-dlp", "-g", "-f", "bestaudio", url]
        ).decode().strip()

        vc = ctx.voice_client or await ctx.author.voice.channel.connect()

        if not vc.is_playing():
            vc.play(discord.FFmpegPCMAudio(audio_url))
            await ctx.send("再生するよ")
        else:
            await ctx.send("もう鳴ってるよ")

        while vc.is_playing():
            await asyncio.sleep(1)

    finally:
        playing.discard(ctx.channel.id)

@bot.command()
async def stop(ctx):
    vc = ctx.voice_client
    if vc:
        vc.stop()
        await ctx.send("止めたよ")

@bot.command()
async def leave(ctx):
    vc = ctx.voice_client
    if vc:
        await vc.disconnect()
        await ctx.send("抜けたよ")

bot.run(TOKEN)
