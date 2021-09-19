from itertools import repeat
import discord
from discord.ext import commands, tasks
from discord.voice_client import VoiceClient
import youtube_dl
import asyncio

from random import choice

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

def is_connected(ctx):
    voice_client = ctx.message.guild.voice_client
    return voice_client and voice_client.is_connected()

client = commands.Bot(command_prefix='?')

status = ['Jamming out to music!', 'Eating!', 'Sleeping!']
queue = []
loop = False

@client.event
async def on_ready():
    change_status.start()
    print('At your disposal!')


# COMMANDS


@client.command(name='ping')
async def ping(ctx):
    await ctx.send(f'**Pong!** Latency: {round(client.latency * 1000)}ms')

@client.command(name='join')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel")
        return
    
    else:
        channel = ctx.message.author.voice.channel

    await channel.connect()
    
@client.command(name='leave')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    await voice_client.disconnect()

@client.command(name='loop')
async def loop_(ctx):
    global loop

    if loop:
        await ctx.send('Loop mode is now `False!`')
        loop = False
    
    else: 
        await ctx.send('Loop mode is now `True!`')
        loop = True



@client.command(name='play')
async def play(ctx):
    global queue

    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel")
        return
    
    else:
        channel = ctx.message.author.voice.channel

    try: await channel.connect()
    except: pass

    server = ctx.message.guild
    voice_channel = server.voice_client
    y = len(queue)
    try:
       
        async with ctx.typing():
            
            player = await YTDLSource.from_url(queue[0], loop=client.loop)
            voice_channel.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
            
            if loop:
                queue.append(queue[0])

            del(queue[0])
            
            
            
        await ctx.send('**Now playing:** {}'.format(player.title))

    except:
        await ctx.send('Nothing in your queue! Use `?queue` to add a song!')


@client.command(name='skip')
async def skip(ctx):
    global queue
    voice = discord.utils.get(client.voice_clients,guild=ctx.guild)
    voice.pause()
    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel")
        return
    
    else:
        channel = ctx.message.author.voice.channel

    try: await channel.connect()
    except: pass

    server = ctx.message.guild
    voice_channel = server.voice_client
    y = len(queue)
    try:
        del(queue[0])
        async with ctx.typing():
            
            player = await YTDLSource.from_url(queue[0], loop=client.loop)
            voice_channel.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
            
            if loop:
                queue.append(queue[0])

            del(queue[0])
            
            
            
        await ctx.send('**Now playing:** {}'.format(player.title))

    except:
        await ctx.send('Nothing in your queue! Use `?queue` to add a song!')


@client.command(name='pause')
async def pause(ctx):
    voice = discord.utils.get(client.voice_clients,guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
    else:
        await ctx.send("I am not singing")

@client.command(name='resume')
async def resume(ctx):
    voice = discord.utils.get(client.voice_clients,guild=ctx.guild)
    if voice.is_paused():
        voice.resume()
    else:
        await ctx.send("Resume singing")

@client.command(name='stop')
async def stop(ctx):
    voice = discord.utils.get(client.voice_clients,guild=ctx.guild)
    voice.stop()

@client.command(name='queue')
async def queue_(ctx, url):
    global queue

    queue.append(url)
    await ctx.send(f'`{url}` added to queue!')

@client.command(name='remove')
async def remove(ctx, number):
    global queue

    try:
        del(queue[int(number)])
        await ctx.send(f'Your queue is now `{queue}!`')
    
    except:
        await ctx.send('Your queue is either **empty** or the index is **out of range**')

@client.command(name='view')
async def view(ctx):
    await ctx.send(f'Your queue is now `{queue}!`')

@tasks.loop(seconds=20)
async def change_status():
    await client.change_presence(activity=discord.Game(choice(status)))

client.run('ODg4MzU4MDAyMzU5NDA2NjA0.YURh3A.7VXvwdnMrfZLl2oWNdwyY81_RlI')
