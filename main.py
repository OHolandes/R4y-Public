import discord
from discord.ext import commands
from youtube_dl import YoutubeDL

intents = discord.Intents.default()
intents.members = True

client = commands.Bot(commands.when_mentioned_or("!"), case_insensitive=True, intents=intents)
client.remove_command('help')
_canal_aud_id = 938832934008406067
_CANAL_AUD = None
_QUEUE = []
_YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
_FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                   'options': '-vn'}
tocando = False
reprodutor = None


def search_yt(item):
    with YoutubeDL(_YDL_OPTIONS) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch:{str(item)}", download=False)['entries'][0]
        except Exception:
            return False
    return {'source': info['formats'][0]['url'], 'title': info['title']}


def play_next():
    global tocando
    if len(_QUEUE) > 0:
        tocando = True

        m_url = _QUEUE[0][0]['source']

        _QUEUE.pop(0)
        try:
            reprodutor.play(discord.FFmpegPCMAudio(m_url, **_FFMPEG_OPTIONS, executable="./ffmpeg"),
                            after=lambda e: play_next())
        except Exception as error:
            print("Um erro bizarro ocorreu", error)
    else:
        tocando = False


async def play_music():
    global reprodutor
    global tocando
    if len(_QUEUE) > 0:
        tocando = True

        m_url = _QUEUE[0][0]['source']

        if not reprodutor.is_connected() or reprodutor is None:
            reprodutor = await _QUEUE[0][1].connect()
        else:
            await reprodutor.move_to(_QUEUE[0][1])

        _QUEUE.pop(0)
        try:
            reprodutor.play(discord.FFmpegPCMAudio(m_url, **_FFMPEG_OPTIONS, executable="./ffmpeg"),
                            after=lambda e: play_next())
        except Exception as error:
            print("Um erro bizarro ocorreu", error)
    else:
        tocando = False
        await _CANAL_AUD.disconnect()


@client.event
async def on_ready():
    print("Online!")
    print(client.user)


@client.command(aliases=["p", "tocar", "manda"], help="Pego uns 'songs' do Youtube.")
async def play(ctx, *args):
    global reprodutor
    global _CANAL_AUD
    query = " ".join(args)
    _CANAL_AUD = client.get_channel(_canal_aud_id)
    voice = ctx.author.voice.channel
    if (voice is None or _CANAL_AUD is None) or (voice is None and _CANAL_AUD is None):
        embedvc = discord.Embed(
            colour=1646116,
            description='Para eu tocar uma música, se conecte a um canal de voz cara.'
        )
        await ctx.send(embed=embedvc)
        return
    elif _CANAL_AUD == voice:
        reprodutor = await _CANAL_AUD.connect()
        song = search_yt(query)
        if type(song) == bool:
            embedvc = discord.Embed(
                colour=12255232,
                description='Hmmm... Algo deu errado Brow! Tente mudar ou configurar a playlist/'
                            'vídeo ou escrever o nome dele novamente!'
            )
            await ctx.send(embed=embedvc)
        else:
            embedvc = discord.Embed(
                colour=32768,
                description=f"**{song['title']}** adicionada à fila meu chapa!"
            )
            await ctx.send(embed=embedvc)
            _QUEUE.append([song, voice])

            if not tocando:
                await play_music()
    else:
        embedvc = discord.Embed(
            colour=12255232,
            description="Não pude acessar meu local de trabalho!"
        )
        await ctx.send(embed=embedvc)


@client.command(name="next", aliases=["n", "proximo", "outra"], help="Toco outra música no meu bloco de notas.")
@commands.has_permissions(manage_channels=True)
async def _next(ctx):
    if reprodutor and reprodutor is not None:
        reprodutor.stop()
        await play_music()
        embedvc = discord.Embed(
            colour=1646116,
            description=f"Vamos para a próxima..."
        )
        await ctx.send(embed=embedvc)


@client.command(aliases=["lista", "playlist", "musicas"], help="Mostro meus pedidos de músicas.")
async def queue(ctx):
    retval = ""
    for i in range(len(_QUEUE)):
        retval += f'**{i + 1} - **' + _QUEUE[i][0]['title'] + "\n"

    if retval != "":
        embedvc = discord.Embed(
            colour=12255232,
            description=f"{retval}"
        )
        await ctx.send(embed=embedvc)
    else:
        embedvc = discord.Embed(
            colour=1646116,
            description='Não há músicas para eu tocar chará.'
        )
        await ctx.send(embed=embedvc)


@client.command(aliases=["comandos"], help="Pedidos aceitáveis.")
async def ajuda(ctx):
    helptxt = ''
    for command in client.commands:
        helptxt += f'**{command}{command.aliases}** - {command.help}\n'
    embedhelp = discord.Embed(
        colour=1646116,
        title=f'Comandos do {client.user.name}',
        description=helptxt
    )
    embedhelp.set_thumbnail(url=client.user.avatar_url)
    await ctx.send(embed=embedhelp)


client.run('TOKEN AQUI')
