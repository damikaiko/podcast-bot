# -*- coding: utf-8 -*-
import os
import asyncio
import feedparser
import random
from quart import Quart
from discord.ext import commands
import discord
import ffmpeg_static  # 追加

TOKEN = os.environ["DISCORD_TOKEN"]
AUTO_OFF_MINUTES = 10  # 放置で自動オフライン化する時間（分）

# ---------------- Quart ----------------
app = Quart(__name__)
bot_task = None
last_access_time = 0

# ---------------- Discord BOT ----------------
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="b!", intents=intents)

RSS_LIST = {
    "haruhi": "https://feeds.megaphone.fm/FNCOMMUNICATIONSINC3656403561",
}
random_mode = set()

@bot.event
async def on_ready():
    print("Bot 起動したよ")

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
    if not vc.is_playing():
        # ffmpeg-static を使うように変更
        vc.play(
            discord.FFmpegPCMAudio(url, executable=ffmpeg_static.path),
            after=lambda e: asyncio.run_coroutine_threadsafe(
                play_random_next(ctx), bot.loop
            )
        )

@bot.command(name="r")
async def random_play(ctx):
    global last_access_time
    last_access_time = asyncio.get_event_loop().time()
    if not ctx.author.voice:
        await ctx.send("VC入ってね")
        return
    vc = ctx.voice_client
    try:
        if not vc:
            vc = await ctx.author.voice.channel.connect(timeout=10)
    except asyncio.TimeoutError:
        await ctx.send("VCに接続できなかったよ。再度コマンドを入力してね。")
        return
    random_mode.add(ctx.guild.id)
    await play_random_next(ctx)
    await ctx.send("連続ランダム再生だよ")

# ---------------- Quart ルート ----------------
@app.route("/")
async def home():
    global last_access_time, bot_task
    last_access_time = asyncio.get_event_loop().time()
    if not bot_task or bot_task.done():
        bot_task = asyncio.create_task(bot.start(TOKEN))
    return "バキバキ童貞を起動したよ。", 200

# ---------------- 放置自動オフライン ----------------
async def auto_offline_check():
    global bot_task
    while True:
        await asyncio.sleep(30)
        if bot_task and not bot_task.done():
            elapsed = asyncio.get_event_loop().time() - last_access_time
            if elapsed > AUTO_OFF_MINUTES * 60 and not random_mode:
                print("放置時間が経過したのでBOTをオフライン化します")
                await bot.close()
                bot_task = None

# ---------------- メイン ----------------
async def main():
    asyncio.create_task(auto_offline_check())
    await app.run_task(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

if __name__ == "__main__":
    asyncio.run(main())
