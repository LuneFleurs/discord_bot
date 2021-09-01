import discord
import asyncio
import os           # 파일 입출력
import traceback

import youtube_dl

from discord.ext import commands

# 선언부
DISCORD_TOKEN = YOURTOKEN
bot = commands.Bot(command_prefix='!')

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


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases = ['넣기', 'JOINTO', 'goto', 'GOTO'])
    async def jointo(self, ctx, *, channel: discord.VoiceChannel):
        """Joins a voice channel"""

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()
 
    #@commands.command()
    #async def play(self, ctx, *, query):
    #    """Plays a file from the local filesystem"""
    #
    #    source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(query))
    #    ctx.voice_client.play(source, after=lambda e: print('Player error: %s' % e) if e else None)
    #
    #    await ctx.send('Now playing: {}'.format(query))


    @commands.command(aliases = ['youtube', '유튜브', '유튭', 'ㅇㅌㅂ', 'ㅇㅌ'])
    async def yt(self, ctx, *, url):
        """Plays from a url (almost anything youtube_dl supports)"""

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop)
            ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

        await ctx.send('Now playing: {}'.format(player.title))

    @commands.command()
    async def stream(self, ctx, *, url):
        """Streams from a url (same as yt, but doesn't predownload)"""

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

        await ctx.send('Now playing: {}'.format(player.title))

    @commands.command()
    async def volume(self, ctx, volume: int):
        """Changes the player's volume"""

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send("Changed volume to {}%".format(volume))

    @commands.command(aliases = ['연결끊기', '연결해제', 'LEAVE', 'quit', "QUIT"])
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""

        await ctx.voice_client.disconnect()

    @commands.command(aliases = ['연결', '참여', 'JOIN'])
    async def join(self, ctx):
        """Join the bot to voice channel"""

        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("voice channel에 먼저 입장해주세요.")
                raise commands.CommandError("Author not connected to a voice channel.")

    #@play.before_invoke
    @yt.before_invoke
    @stream.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("voice channel에 먼저 입장해주세요.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()


# 시작시 
@bot.event
async def on_ready():
    print('다음으로 로그인합니다: ')
    print(bot.user.name)
    print('connection was succesful')
    await bot.change_presence(status=discord.Status.online, activity=None)

# 명령어 
@bot.command(name = '예티')   #생존 확인용 
async def ping(ctx):
    await ctx.send("PONG!")


# status 변경
@bot.command(aliases=['방해금지', 'DND', 'donotdisturb', 'do not disturb'])
@commands.is_owner()
async def dnd(ctx):
    await bot.change_presence(status=discord.Status.dnd)
    await ctx.send('봇 상태를 방해금지로 변경!')

@bot.command(aliases=['온라인', "ONLINE"])
@commands.is_owner()
async def online(ctx):
    await bot.change_presence(status=discord.Status.online)
    await ctx.send('봇 상태를 온라인으로 변경!')


# 예외 처리
async def on_command_error(ctx, error):
    tb = traceback.format_exception(type(error), error, error.__traceback__)
    err = [line.rstrip() for line in tb]
    errstr = '\n'.join(err)
    if isinstance(error, commands.NotOwner):
        await ctx.send('에러가 발생했습니다.')
    else:
        await ctx.send('봇 주인만 사용 가능한 명령어입니다')
        print(errstr)
     
bot.add_cog(Music(bot))
bot.run(DISCORD_TOKEN)
