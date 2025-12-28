# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import subprocess
import os
import asyncio

TOKEN = os.environ["DISCORD_TOKEN"]

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="b!", intents=intents)

@bot.event
async def on_ready():
    print("Bot起動したよ")

# 再生ロック用
playing = set()

@bot.command()
async def p(ctx, url: str):
    if not ctx.author.voice:
        await ctx.send("VCに入ってね")
        return

    # 再生中なら待たせる
    if ctx.channel.id in playing:
        await ctx.send("今は再生中だよ、少し待ってね")
        return

    playing.add(ctx.channel.id)
    try:
        # yt-dlpで直リンク取得
        audio_url = subprocess.check_output(
            ["yt-dlp", "-g", "-f", "bestaudio", "--no-check-certificate", "--http-chunk-size", "10M", url]
        ).decode().strip()

        # VC接続は既存VCを再利用
        vc = ctx.voice_client
        if not vc:
            vc = await ctx.author.voice.channel.connect()

        # 再生
        if not vc.is_playing():
            vc.play(discord.FFmpegPCMAudio(audio_url))
            await ctx.send("バキバキ童貞です")
        else:
            await ctx.send("既に再生中だよ")

        # 再生終了まで待機
        while vc.is_playing():
            await asyncio.sleep(1)

        # 再生終了後少し待つ
        await asyncio.sleep(2)  # 次の接続や再生まで少し間隔を空ける

    finally:
        playing.discard(ctx.channel.id)

bot.run(TOKEN)
