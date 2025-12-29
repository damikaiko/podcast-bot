# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import subprocess
import os
import asyncio
from threading import Thread
from flask import Flask

TOKEN = os.environ["DISCORD_TOKEN"]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="b!", intents=intents)

# ---------------- ffmpeg セットアップ ----------------
FFMPEG_DIR = "./ffmpeg"
FFMPEG_PATH = f"{FFMPEG_DIR}/ffmpeg"
FFPROBE_PATH = f"{FFMPEG_DIR}/ffprobe"

def setup_ffmpeg():
    if not os.path.exists(FFMPEG_DIR):
        os.makedirs(FFMPEG_DIR)
    if not os.path.exists(FFMPEG_PATH):
        print("ffmpeg をダウンロード中...")
        subprocess.run([
            "wget", "-O", "ffmpeg.tar.xz",
            "https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz"
        ], check=True)
        subprocess.run(["tar", "xJf", "ffmpeg.tar.xz"], check=True)
        extracted = [
            d for d in os.listdir(".")
            if d.startswith("ffmpeg-git") and os.path.isdir(d)
        ][0]
        subprocess.run(["cp", f"{extracted}/ffmpeg", FFMPEG_PATH], check=True)
        subprocess.run(["cp", f"{extracted}/ffprobe", FFPROBE_PATH], check=True)
        subprocess.run(["chmod", "+x", FFMPEG_PATH, FFPROBE_PATH], check=True)
        print("ffmpeg ダウンロード完了")

setup_ffmpeg()

# ---------------- Discord BOT ----------------
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
        audio_url = subprocess.check_output([
            "yt-dlp", "-g", "-f", "bestaudio", "--no-check-certificate",
            "--http-chunk-size", "10M", url
        ]).decode().strip()

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

@bot.command()
@commands.is_owner()
async def restart(ctx):
    await ctx.send("再起動するよ…")
    await bot.close()

@bot.command()
async def leave(ctx):
    vc = ctx.voice_client
    if vc:
        await vc.disconnect()
        await ctx.send("VCから切断したよ")
    else:
        await ctx.send("VCに接続してないよ")

# ---------------- Flask ----------------
app = Flask("")

@app.route("/")
def home():
    # 軽く OK を返すだけ
    return "OK", 200

def run_flask():
    # PORT 環境変数があればそれを使う
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)

# Flask を別スレッドで起動
Thread(target=run_flask).start()

# Discord BOT を起動
bot.run(TOKEN)
