import asyncio
import discord
from discord.ext import commands

from youtube_dl import YoutubeDL

import sql

intents = discord.Intents.default()
intents.members = True

client = commands.Bot(commands.when_mentioned_or("!"), case_insensitive=True, intents=intents, description="Radialista")
client.remove_command('help')
_QUEUE = []
walk_man = None
_YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True', 'quiet' : 'True',
                'no_color': 'True'}
_FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                   'options': '-vn'}


def search_yt(item: str):
    """
    Pesquisa uma música.

    :param item: Nome ou url
    """
    with YoutubeDL(_YDL_OPTIONS) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch:{item}", download=False)['entries'][0]
        except Exception:
            return False
    # retorna a url e o titulo
    return {'source': info['formats'][0]['url'], 'title': info['title']}


async def user_connected(contexto: discord.ext.commands.Context):
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
        if walk_man.is_connected():
            if len(walk_man.channel.members) == 1:
                await walk_man.disconnect()
                _QUEUE.clear()
                return
    except Exception:
        return


def flow():
    if _QUEUE:
        _QUEUE.pop(0)
        walk_man.stop()
        try:
            next_music = _QUEUE[0]["source"]
        except IndexError:
            walk_man.pause()
        else:
            walk_man.play(discord.FFmpegPCMAudio(next_music, **_FFMPEG_OPTIONS, executable="./ffmpeg"),
                            after=lambda x: flow())


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
    global walk_man
    try:
        SERV = sql.get_serv(ctx.guild.id)[0]
    except IndexError:
        await ctx.send(ctx.author.mention + "Seu servidor não foi adicionado.")
        return

    pedidos = client.get_channel(SERV[1])

    if ctx.channel.id != pedidos.id:
        embedvc = discord.Embed(
            colour=12255232,
            description=f'Você não está no meu canal de pedidos, vai lá em {pedidos.mention} e manda de novo.'
        )
        await ctx.send(embed=embedvc)
        return

    channel = client.get_channel(SERV[2])
    voice = await user_connected(ctx)

    if not all((channel, voice)) or not any((channel, voice)):
        embedvc = discord.Embed(
            colour=1646116,
            description='Para eu tocar uma música, se conecte a um canal de voz cara.'
        )
        await ctx.send(embed=embedvc)
        return
    elif channel == voice:
        if walk_man is None:
            await ctx.guild.change_voice_state(channel=voice)
            walk_man = await voice.connect()

        embedvc = discord.Embed(colour=32768)
        embedvc.description = "**Buscando...**"
        await ctx.send(embed=embedvc)

        query = " ".join(args)
        song = search_yt(query)

        if not song:
            embedvc = discord.Embed(
                colour=12255232,
                description='Hmmm... Algo deu errado Brow! Tente mudar ou configurar a playlist/'
                            'vídeo ou escrever o nome dele novamente!'
            )
            await ctx.send(embed=embedvc)
        else:
            _QUEUE.append(song)
            embedvc.description = f"**{song['title']}** adicionada há fila meu chapa!"
            await ctx.send(embed=embedvc)
            if not walk_man.is_playing():
                m_url = _QUEUE[0]['source']
                try:
                    walk_man.play(discord.FFmpegPCMAudio(m_url, **_FFMPEG_OPTIONS, executable="./ffmpeg"),
                                    after=lambda x: flow())
                except Exception as error:
                    print("Um erro bizarro ocorreu ao carregar o audio", error)


@client.command(name="next", aliases=["n", "proximo", "outra"], help="Toco outra música no meu bloco de notas.")
@commands.has_permissions(manage_channels=True)
async def _next(ctx):
    """
    Comando para pular a música.

    :param ctx: argumento tipo Context.
    :return: None
    """
    if walk_man:
        embedvc = discord.Embed(
            colour=1646116,
            description=f"Vamos para a próxima..."
        )
        await ctx.send(embed=embedvc)
        flow()


@client.command(aliases=["lista", "playlist", "musicas"], help="Mostro meus pedidos de músicas.")
async def queue(ctx):
    """
    Mostra a lista de reprodução.

    :param ctx: argumento tipo Context.
    :return: None
    """
    music_info = ""
    for index, music in enumerate(_QUEUE):
        if index == 0:
            music["title"] = f"**{music['title']}**"
        music_info += "**{}** - {}\n".format(index+1, music["title"])

    if music_info:
        embedvc = discord.Embed(
            colour=12255232,
            description=f"{music_info}"
        )
        await ctx.send(embed=embedvc)
    else:
        embedvc = discord.Embed(
            colour=1646116,
            description='Não há músicas para eu tocar chará.'
        )
        await ctx.send(embed=embedvc)


@client.command(aliases=["rebobina", "fabrica"], help="Fico zero, versão de fabrica.")
@commands.has_permissions(administrator=True)
async def reset(ctx):
    embedreset = discord.Embed(colour=1646116)
    global walk_man

    if walk_man is not None:
        embedreset.description = "Hora do re-start."
        await ctx.send(embed=embedreset)
        walk_man.stop()
        await walk_man.disconnect()
        _QUEUE.clear()
        walk_man = None
    else:
        embedreset.description = "Já estou zerado."
        await ctx.send(embed=embedreset)


@client.command(aliases=["set"], help="Adiciono ou apago seu servidor.")
@commands.has_permissions(administrator=True)
async def config(ctx, _cmd:str, _id_channel:int = 0, _id_voice:int = 0):
    if _cmd == "+":
        sql.add_serv(ctx.guild.id, _id_channel, _id_voice)
        await ctx.send("Servidor adicionado.")
    elif _cmd == "-":
        sql._del(ctx.guild.id)
        await ctx.send("Servidor apagado.")
    elif _cmd == "#":
        sql.update(ctx.guild.id, _id_channel, _id_voice)
        await ctx.send("Servidor atualizado.")
    else:
        await ctx.send("Não entendi... Use: !help")


@client.command(aliases=["comandos", "help"], help="Pedidos aceitáveis.")
async def ajuda(ctx):
    """
    Comando de ajuda.

    :param ctx: argumento tipo Context.
    :return: None
    """
    helptxt = ''
    for command in client.commands:
        helptxt += f'**{command} | [{", ".join(command.aliases)}]** - {command.help}\n'
    helptxt += "\n**!config**:\nUse !config + ID_CANAL_DE_TEXTO ID_CANAL_DE_VOZ para adicionar. **!config -** para apagar"
    helptxt += " e **!config #** ID_CANAL_DE_TEXTO ID_CANAL_DE_VOZ para atualizar."
    embedhelp = discord.Embed(
        colour=1646116,
        title=f'Comandos do {client.user.name}',
        description=helptxt
    )
    embedhelp.set_thumbnail(url=client.user.avatar_url)
    await ctx.send(embed=embedhelp)


if __name__ == "__main__":
    client.run('OTM4NTQ2NDM1NzIzNTE4MDEy.Yfr3ew.bYQW4k8TPVgJnK5rjOHE9_X4DFY')
