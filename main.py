# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import os
import asyncio
import feedparser
import random
from flask import Flask
from threading import Thread

TOKEN = os.environ["DISCORD_TOKEN"]

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="b!", intents=intents)

RSS_LIST = {
    "haruhi": "https://feeds.megaphone.fm/FNCOMMUNICATIONSINC3656403561",
}

random_mode = set()

# ---------------- Flask ----------------
app = Flask("")
shutdown_task = None

@app.route("/")
def home():
    global shutdown_task

    # 既存の終了予約があればキャンセル
    if shutdown_task:
        shutdown_task.cancel()

    # 10分後にBOT終了を予約
    shutdown_task = asyncio.run_coroutine_threadsafe(
        shutdown_after_10min(), bot.loop
    )

    return "BOT is online for 10 minutes", 200


async def shutdown_after_10min():
    await asyncio.sleep(600)
    await bot.close()


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)

Thread(target=run_flask).start()


# ---------------- Discord BOT ----------------
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

    audio_url = get_random_audio_url()
    if not audio_url:
        return

    vc.play(
        discord.FFmpegPCMAudio(audio_url),
        after=lambda e: asyncio.run_coroutine_threadsafe(
            play_random_next(ctx), bot.loop)
    )

# ---------------- コマンド ----------------
# 追加：ギルドごとの送信先
last_text_channel = {}

@bot.command(name="r")
async def random_play(ctx):
    if not ctx.author.voice:
        await ctx.send("VC入ってね")
        return

    last_text_channel[ctx.guild.id] = ctx.channel  # ← ここ重要

    vc = ctx.voice_client or await ctx.author.voice.channel.connect()
    random_mode.add(ctx.guild.id)

    if not vc.is_playing():
        await play_random_next(ctx)

    await ctx.send("連続ランダム再生だよ")

@bot.command(name="s")
async def skip(ctx):
    vc = ctx.voice_client
    if vc and vc.is_playing():
        last_text_channel[ctx.guild.id] = ctx.channel
        vc.stop()
        await ctx.send("飛ばすよ")


@bot.command(name="l")
async def leave(ctx):
    vc = ctx.voice_client
    if vc:
        last_text_channel[ctx.guild.id] = ctx.channel

        ch = last_text_channel.get(ctx.guild.id)
        if ch:
            await ch.send("切断したよ。オフラインになるよ。")

        await vc.disconnect()
        random_mode.discard(ctx.guild.id)
        await bot.close()


# ---------------- 自動終了 ----------------
@bot.event
async def on_voice_state_update(member, before, after):
    vc = member.guild.voice_client
    if not vc:
        return

    # BOTがいるVCから人が抜けた時だけ見る
    if before.channel == vc.channel and after.channel != vc.channel:
        humans = [m for m in vc.channel.members if not m.bot]

        # 人間が0人になったら
        if len(humans) == 0:
            if member.guild.system_channel:
                await member.guild.system_channel.send(
                    "誰もいないから切断したよ。オフラインになるよ。"
                )

            await vc.disconnect()
            random_mode.discard(member.guild.id)
            await asyncio.sleep(1)
            await bot.close()


bot.run(TOKEN)




