import discord
from discord.ext import commands
from youtube_dl import YoutubeDL
import asyncio

intents = discord.Intents.default()
intents.members = True

client = commands.Bot(commands.when_mentioned_or("!"), case_insensitive=True, intents=intents, description="Radialista")
client.remove_command('help')
_QUEUE = []
_canal_aud_id = 938832934008406067  # id do canal de musica
_pedidos_id = 938832825321398382  # id do canal de texto para comandos
_CANAL_AUD: discord.VoiceChannel
reprodutor: discord.VoiceClient
_YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
_FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                   'options': '-vn'}


def search_yt(item):
    """
    Pesquisa uma música.

    :param item: Nome ou url
    """
    with YoutubeDL(_YDL_OPTIONS) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch:{str(item)}", download=False)['entries'][0]
        except Exception:
            return False
    return {'source': info['formats'][0]['url'], 'title': info['title']}


async def user_connected(contexto: discord.ext.commands.Context) -> bool | discord.VoiceChannel:
    """
    Verifica se o usuario está conectado à um canal de voz.

    :param contexto: variavel tipo Context
    :return: False ou o canal de voz conectado
    """
    canal = False
    try:
        canal = contexto.author.voice.channel
    except AttributeError:
        pass
    finally:
        return canal


async def ouvintes():
    """
    Verifica se o canal não está vazio.

    :return: None
    """
    try:
        if reprodutor.is_connected():
            if len(reprodutor.channel.members) == 1:
                await reprodutor.disconnect()
                _QUEUE.clear()
                return
    except Exception:
        pass


def play_next():
    """
    Toca a próxima música

    :return: None
    """
    if _QUEUE:
        m_url = _QUEUE[0][0]['source']
        _QUEUE.pop(0)
        try:
            reprodutor.play(discord.FFmpegPCMAudio(m_url, **_FFMPEG_OPTIONS, executable="./ffmpeg"),
                            after=lambda e: play_next())
        except Exception as error:
            print("Um erro bizarro ocorreu", error)


async def play_music(ctx: discord.ext.commands.Context):
    """
    Toca uma música.

    :param ctx: argumento tipo Context.
    :return: None
    """
    global reprodutor
    if _QUEUE:
        m_url = _QUEUE[0][0]['source']
        if not reprodutor.is_connected() or reprodutor is None:
            reprodutor = await _QUEUE[0][1].connect()
        else:
            await reprodutor.move_to(_QUEUE[0][1])
        _QUEUE.pop(0)
        try:
            await ouvintes()
            reprodutor.play(discord.FFmpegPCMAudio(m_url, **_FFMPEG_OPTIONS, executable="./ffmpeg"),
                            after=lambda e: play_next())
        except Exception as error:
            print("Um erro bizarro ocorreu", error)
    else:
        embedvc = discord.Embed(
            colour=1646116,
            description='Não há músicas para eu tocar chará.'
        )
        await ctx.send(embed=embedvc)
        await reprodutor.disconnect()


@client.event
async def on_ready():
    """
    Inicia o bot.
    """
    print("SHOW TIME")
    print(client.user)

    while True:
        await ouvintes()
        await asyncio.sleep(3)


@client.command(aliases=["p", "tocar", "manda"], help="Pego uns 'songs' do Youtube.")
async def play(ctx, *args):
    """
    Comando para tocar música.

    :param ctx: argumento tipo Context.
    :param args: palavras-chaves para a busca.
    :return: None
    """
    global reprodutor
    global _CANAL_AUD
    pedidos = client.get_channel(_pedidos_id)
    if ctx.channel != pedidos:
        embedvc = discord.Embed(
            colour=12255232,
            description=f'Você não está no meu canal de pedidos, vai lá em {pedidos.mention} e manda de novo.'
        )
        await ctx.send(embed=embedvc)
        return
    query = " ".join(args)
    _CANAL_AUD = client.get_channel(_canal_aud_id)
    voice = await user_connected(ctx)
    if (_CANAL_AUD is None and not voice) or (_CANAL_AUD is None or not voice):
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

            if not reprodutor.is_playing() and reprodutor.is_connected():
                await play_music(ctx)
            else:
                embedvc = discord.Embed(
                    colour=12255232,
                    description="Não pude acessar meu local de trabalho!"
                )
                await ctx.send(embed=embedvc)


@client.command(name="next", aliases=["n", "proximo", "outra"], help="Toco outra música no meu bloco de notas.")
@commands.has_permissions(manage_channels=True)
async def _next(ctx):
    """
    Comando para pular a música.

    :param ctx: argumento tipo Context.
    :return: None
    """
    if reprodutor:
        embedvc = discord.Embed(
            colour=1646116,
            description=f"Vamos para a próxima..."
        )
        await ctx.send(embed=embedvc)
        reprodutor.stop()
        await play_music(ctx)


@client.command(aliases=["lista", "playlist", "musicas"], help="Mostro meus pedidos de músicas.")
async def queue(ctx):
    """
    Mostra a lista de reprodução.

    :param ctx: argumento tipo Context.
    :return: None
    """
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
    """
    Comando de ajuda.

    :param ctx: argumento tipo Context.
    :return: None
    """
    helptxt = ''
    for command in client.commands:
        helptxt += f'**{command} | [{", ".join(command.aliases)}]** - {command.help}\n'
    embedhelp = discord.Embed(
        colour=1646116,
        title=f'Comandos do {client.user.name}',
        description=helptxt
    )
    embedhelp.set_thumbnail(url=client.user.avatar_url)
    await ctx.send(embed=embedhelp)


client.run('TOKEN AQUI')
