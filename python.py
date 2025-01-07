import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import sys

sys.stdout.reconfigure(encoding='utf-8')

intent = discord.Intents.default()
intent.message_content = True

bot = commands.Bot(command_prefix='!', intents=intent)

queue = []  # Черга для пісень

@bot.event
async def on_ready():
    print(f'Бот ({bot.user.name}) запущений і готовий!')

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if not ctx.voice_client:  # Приєднується, тільки якщо ще не підключений
            await channel.connect()
            await ctx.send(f'Приєднався до каналу: {channel}')
        else:
            await ctx.send('Я вже приєднаний до голосового каналу!')
    else:
        await ctx.send('Спочатку приєднайся до голосового каналу!')

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.guild.voice_client.disconnect()
        await ctx.send('Від\'єднався від каналу!')
    else:
        await ctx.send('Я не приєднаний до жодного каналу!')

async def play_next(ctx):
    if queue:
        song_name, url = queue.pop(0)
        source = discord.FFmpegPCMAudio(
            url,
            executable="C:/ffmpeg/bin/ffmpeg.exe",
            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            options="-vn"
        )
        ctx.voice_client.play(source, after=lambda e: bot.loop.create_task(play_next(ctx)))
        await ctx.send(f'Відтворюю: {song_name}')
    else:
        await ctx.send('Черга порожня!')
        await ctx.voice_client.disconnect()

@bot.command()
async def play(ctx, *, song_name: str):
    if ctx.voice_client:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            'quiet': True
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{song_name}", download=False)
            if 'entries' in info and info['entries']:
                url = info['entries'][0]['url']
                song_name = info['entries'][0]['title']
            else:
                await ctx.send('Не вдалося знайти пісню.')
                return

        if ctx.voice_client.is_playing():
            queue.append((song_name, url))
            await ctx.send(f'Пісня додана в чергу: {song_name}')
        else:
            source = discord.FFmpegPCMAudio(
                url,
                executable="C:/ffmpeg/bin/ffmpeg.exe",
                before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                options="-vn"
            )
            ctx.voice_client.play(source, after=lambda e: bot.loop.create_task(play_next(ctx)))
            await ctx.send(f'Відтворюю: {song_name}')

    else:
        await ctx.send('Я не приєднаний до голосового каналу!')

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send('Пісня пропущена!')
        await play_next(ctx)
    else:
        await ctx.send('Немає пісні для пропуску!')

TOKEN = ''
bot.run(TOKEN)
