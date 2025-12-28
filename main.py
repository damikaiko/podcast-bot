# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import subprocess
import os
import asyncio
import sys

TOKEN = os.environ["DISCORD_TOKEN"]
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="b!", intents=intents)

# Render 上で自動的に ffmpeg を置くパス
FFMPEG_DIR = "./ffmpeg"
FFMPEG_PATH = f"{FFMPEG_DIR}/ffmpeg"
FFPROBE_PATH = f"{FFMPEG_DIR}/ffprobe"

# ffmpeg がなければダウンロード
def setup_ffmpeg():
    if not os.path.exists(FFMPEG_DIR):
        os.makedirs(FFMPEG_DIR)
    if not os.path.exists(FFMPEG_PATH):
        print("ffmpeg をダウンロード中...")
        # Linux 64bit 静的ビルドを wget で取得
        subprocess.run([
            "wget",
            "-O", "ffmpeg.tar.xz",
            "https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz"
        ], check=True)
        subprocess.run(["tar", "xJf", "ffmpeg.tar.xz"], check=True)
        # バイナリをコピー
        extracted = [d for d in os.listdir(".") if d.startswith("ffmpeg-git") and os.path.isdir(d)][0]
        subprocess.run(["cp", f"{extracted}/ffmpeg", FFMPEG_PATH], check=True)
        subprocess.run(["cp", f"{extracted}/ffprobe", FFPROBE_PATH], check=True)
        subprocess.run(["chmod", "+x", FFMPEG_PATH, FFPROBE_PATH], check=True)
        print("ffmpeg ダウンロード完了")

setup_ffmpeg()

@bot.event
async def on_ready():
    print("Bot 起動したよ")

playing = set()

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
        # yt-dlp で音声 URL 取得
        audio_url = subprocess.check_output(
            ["yt-dlp", "-g", "-f", "bestaudio", "--no-check-certificate", "--http-chunk-size", "10M", url]
        ).decode().strip()

        vc = ctx.voice_client or await ctx.author.voice.channel.connect()
        if not vc.is_playing():
            opts = {
                "executable": FFMPEG_PATH,
                "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
            }
            vc.play(discord.FFmpegPCMAudio(audio_url, **opts))
            await ctx.send("再生するよ")
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
        await ctx.send("止めたよ")
    else:
        await ctx.send("再生してないよ")

bot.run(TOKEN)
