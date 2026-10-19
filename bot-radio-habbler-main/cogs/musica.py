import asyncio
import shutil

import discord
from discord.ext import commands, tasks

try:
    import imageio_ffmpeg
except ImportError:
    imageio_ffmpeg = None

try:
    import yt_dlp
    HAS_YTDLP = True
except ImportError:
    yt_dlp = None
    HAS_YTDLP = False

FFMPEG_EXE = shutil.which("ffmpeg")
if not FFMPEG_EXE and imageio_ffmpeg:
    try:
        FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        FFMPEG_EXE = "ffmpeg"
if not FFMPEG_EXE:
    FFMPEG_EXE = "ffmpeg"

CANAL_VOZ_247_ID = 1458950146434924594
RADIO_247_URL = "https://painel.dedicado.stream/8044/stream"

# Reconecta em quedas do stream (Icecast/Shoutcast) e não limita a entrada em tempo real.
FFMPEG_BEFORE_OPTIONS = (
    "-reconnect 1 -reconnect_streamed 1 -reconnect_at_eof 1 "
    "-reconnect_on_network_error 1 -reconnect_delay_max 5"
)
FFMPEG_OPTIONS = {"options": "-vn"}


def get_audio_source(url: str) -> discord.AudioSource:
    return discord.FFmpegPCMAudio(
        url,
        executable=FFMPEG_EXE,
        before_options=FFMPEG_BEFORE_OPTIONS,
        **FFMPEG_OPTIONS,
    )


class Musica(commands.Cog):
    """Player com uma única rotina de conexão por guild.

    A rádio 24/7 não move o bot à força se comandos de música o colocarem
    em outro canal: isso evita o ciclo entrar/sair entre dois canais.
    """

    def __init__(self, bot):
        self.bot = bot
        self._voice_locks = {}
        self._radio_start_lock = asyncio.Lock()
        self.manter_radio_247.start()
        self.checar_vazia.start()

    def _lock_for(self, guild_id):
        return self._voice_locks.setdefault(guild_id, asyncio.Lock())

    def cog_unload(self):
        self.manter_radio_247.cancel()
        self.checar_vazia.cancel()

    @tasks.loop(seconds=25)
    async def manter_radio_247(self):
        if not self.bot.is_ready():
            return
        try:
            canal = self.bot.get_channel(CANAL_VOZ_247_ID)
            if canal is None:
                canal = await self.bot.fetch_channel(CANAL_VOZ_247_ID)
            if not isinstance(canal, (discord.VoiceChannel, discord.StageChannel)):
                print("⚠️ Rádio 24/7: ID não é canal de voz/stage.", flush=True)
                return

            guild = canal.guild
            async with self._lock_for(guild.id):
                voice = guild.voice_client

                # Estado zumbi: encerra a sessão antiga antes de tentar conectar novamente.
                if voice is not None and not voice.is_connected():
                    try:
                        await voice.disconnect(force=True)
                    except Exception as e:
                        print(f"⚠️ Limpando voice client antigo: {type(e).__name__}: {e}", flush=True)
                    voice = None

                if voice is None:
                    try:
                        voice = await canal.connect(reconnect=True, timeout=25.0)
                        print(f"📻 Rádio 24/7 conectada em {canal.name}", flush=True)
                    except Exception as e:
                        print(f"⚠️ Conexão da rádio falhou: {type(e).__name__}: {e}", flush=True)
                        return

                # Não mover o bot de outro canal a cada ciclo: comandos de música
                # podem estar usando outra call no mesmo servidor.
                if not voice.is_connected() or voice.channel is None:
                    return
                if voice.channel.id != canal.id:
                    return

                gid = guild.id
                q = getattr(self.bot, "music_queues", {}).get(gid, {})
                tem_musica = bool(q.get("current") or q.get("queue"))
                if not tem_musica and not voice.is_playing() and not voice.is_paused():
                    try:
                        voice.play(get_audio_source(RADIO_247_URL))
                        print("📻 Transmissão 24/7 iniciada.", flush=True)
                    except Exception as e:
                        print(f"⚠️ Play da rádio falhou: {type(e).__name__}: {e}", flush=True)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            # Não esconder a exceção: o pass original ocultava a causa real.
            print(f"⚠️ manter_radio_247: {type(e).__name__}: {e}", flush=True)

    @manter_radio_247.before_loop
    async def before_radio_247(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(8)

    @tasks.loop(seconds=30)
    async def checar_vazia(self):
        try:
            for guild in self.bot.guilds:
                voice = guild.voice_client
                if not voice or not voice.is_connected() or voice.channel is None:
                    continue
                if voice.channel.id == CANAL_VOZ_247_ID:
                    continue

                queues = getattr(self.bot, "music_queues", {})
                queues.setdefault(guild.id, {"queue": [], "current": None, "current_title": None})
                q = queues[guild.id]
                membros_reais = [m for m in voice.channel.members if not m.bot]
                if not membros_reais:
                    q.setdefault("vazio", self.bot.loop.time())
                    if self.bot.loop.time() - q["vazio"] >= 120:
                        async with self._lock_for(guild.id):
                            # Revalida após adquirir o lock para não derrubar uma call ativa.
                            atual = guild.voice_client
                            if atual and atual.is_connected() and atual.channel:
                                humanos = [m for m in atual.channel.members if not m.bot]
                                if atual.channel.id != CANAL_VOZ_247_ID and not humanos:
                                    await atual.disconnect(force=True)
                            q.pop("vazio", None)
                else:
                    q.pop("vazio", None)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"⚠️ checar_vazia: {type(e).__name__}: {e}", flush=True)

    @checar_vazia.before_loop
    async def before_checar_vazia(self):
        await self.bot.wait_until_ready()

    def buscar_musica(self, query):
        if not HAS_YTDLP:
            return None, None
        try:
            opts = {"format": "bestaudio/best", "quiet": True, "noplaylist": True}
            with yt_dlp.YoutubeDL(opts) as ydl:
                if any(x in query for x in ("youtube.com", "youtu.be", "spotify.com")):
                    info = ydl.extract_info(query, download=False)
                else:
                    info = ydl.extract_info(f"ytsearch1:{query}", download=False)
                    if info.get("entries"):
                        info = info["entries"][0]
                    else:
                        return None, None
                return info.get("webpage_url", query), info.get("title", "?")
        except Exception as e:
            print(f"⚠️ yt-dlp: {type(e).__name__}: {e}", flush=True)
            return None, None

    async def _connect_to(self, channel):
        """Conecta/move uma vez, protegido contra chamadas concorrentes."""
        async with self._lock_for(channel.guild.id):
            voice = channel.guild.voice_client
            if voice is not None and not voice.is_connected():
                try:
                    await voice.disconnect(force=True)
                except Exception:
                    pass
                voice = None
            if voice is None:
                return await channel.connect(reconnect=True, timeout=25.0)
            if voice.channel.id != channel.id:
                await voice.move_to(channel)
            return voice

    async def player_loop(self, guild):
        gid = guild.id
        while True:
            voice = guild.voice_client
            if not voice or not voice.is_connected():
                break
            q = getattr(self.bot, "music_queues", {}).get(gid)
            if not q or not q.get("queue"):
                if q:
                    q["current"] = q["current_title"] = None
                break

            entry = q["queue"].pop(0)
            q["current"], q["current_title"] = entry["url"], entry["title"]
            source = None
            try:
                if entry.get("is_radio"):
                    source = get_audio_source(entry["url"])
                else:
                    if not HAS_YTDLP:
                        raise RuntimeError("yt-dlp não está instalado")
                    loop = asyncio.get_running_loop()
                    with yt_dlp.YoutubeDL({"format": "bestaudio/best", "quiet": True, "noplaylist": True}) as ydl:
                        info = await loop.run_in_executor(
                            None, lambda: ydl.extract_info(entry["url"], download=False)
                        )
                    source = get_audio_source(info["url"])

                finished = asyncio.Event()
                def after(error):
                    if error:
                        print(f"⚠️ Erro no player de áudio: {error}", flush=True)
                    self.bot.loop.call_soon_threadsafe(finished.set)

                voice.play(source, after=after)
                await finished.wait()
            except asyncio.CancelledError:
                if source:
                    source.cleanup()
                raise
            except Exception as e:
                print(f"⚠️ Erro no player: {type(e).__name__}: {e}", flush=True)
                if source:
                    source.cleanup()
                await asyncio.sleep(1)
            finally:
                q["current"] = q["current_title"] = None

    async def _start_player(self, guild):
        tasks_by_guild = getattr(self.bot, "player_tasks", None)
        if tasks_by_guild is None:
            self.bot.player_tasks = {}
            tasks_by_guild = self.bot.player_tasks
        task = tasks_by_guild.get(guild.id)
        if task is None or task.done():
            tasks_by_guild[guild.id] = asyncio.create_task(self.player_loop(guild))

    @commands.command(name="radio", aliases=["playradio", "tocaradio", "habbler", "247", "radio247"])
    async def radio(self, ctx, *, link: str = None):
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send("❌ Você precisa estar em um canal de voz!")
        target = link.strip() if link else RADIO_247_URL
        is_default = not link or target == RADIO_247_URL
        title = "📻 Rádio Habbler 24/7 (Oficial)" if is_default else "📻 Rádio Web"
        gid = ctx.guild.id
        self.bot.music_queues.setdefault(gid, {"queue": [], "current": None, "current_title": None})
        q = self.bot.music_queues[gid]
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        q["queue"].insert(0, {"url": target, "title": title, "requester": ctx.author, "is_radio": True})
        await ctx.send(f"📻 Sintonizando **{title}** em {ctx.author.voice.channel.mention}...")
        try:
            await self._connect_to(ctx.author.voice.channel)
            await self._start_player(ctx.guild)
        except Exception as e:
            await ctx.send(f"❌ Erro ao conectar ao canal de voz: `{type(e).__name__}: {e}`")

    @commands.command(name="play")
    async def play(self, ctx, *, q: str):
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send("❌ Entre numa call!")
        msg = await ctx.send(f"🔍 `{q}`...")
        loop = asyncio.get_running_loop()
        url, title = await loop.run_in_executor(None, self.buscar_musica, q)
        if not url:
            return await msg.edit(content="❌ Música não encontrada!")
        gid = ctx.guild.id
        self.bot.music_queues.setdefault(gid, {"queue": [], "current": None, "current_title": None})
        self.bot.music_queues[gid]["queue"].append(
            {"url": url, "title": title, "requester": ctx.author, "is_radio": False}
        )
        await msg.edit(content=f"✅ **{title}**")
        try:
            await self._connect_to(ctx.author.voice.channel)
            await self._start_player(ctx.guild)
        except Exception as e:
            await ctx.send(f"❌ Erro ao iniciar áudio: `{type(e).__name__}: {e}`")

    @commands.command(name="listradio", aliases=["radios", "estacoes"])
    async def listradio(self, ctx):
        embed = discord.Embed(
            title="📻 Estações de Rádio Disponíveis",
            description="Use `hbl radio` para ouvir no seu canal de voz!",
            color=discord.Color.gold(),
        )
        embed.add_field(name="1. 🟡 Rádio Habbler 24/7 (Oficial)", value="`hbl radio` | `hbl playradio` | `hbl 247`", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="pause")
    async def pause(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸️ Pausado")

    @commands.command(name="resume")
    async def resume(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ Despausado")

    @commands.command(name="skip")
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭️ Pulado")

    @commands.command(name="stop")
    async def stop(self, ctx):
        gid = ctx.guild.id
        if gid in getattr(self.bot, "music_queues", {}):
            self.bot.music_queues[gid] = {"queue": [], "current": None, "current_title": None}
        if ctx.voice_client:
            if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                ctx.voice_client.stop()
            await ctx.voice_client.disconnect(force=True)
        await ctx.send("⏹️ Parado")

    @commands.command(name="playlist")
    async def playlist(self, ctx):
        q = getattr(self.bot, "music_queues", {}).get(ctx.guild.id, {})
        if not q.get("queue") and not q.get("current"):
            return await ctx.send("📋 Fila vazia!")
        embed = discord.Embed(title="📋 Fila de Músicas", color=discord.Color.green())
        if q.get("current"):
            embed.add_field(name="🎵 Tocando Agora", value=q.get("current_title") or "Áudio", inline=False)
        if q.get("queue"):
            embed.add_field(name="⏳ Próximas", value="\n".join(
                f"**{i + 1}.** {item['title']}" for i, item in enumerate(q["queue"][:10])
            ), inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="nowplaying")
    async def nowplaying(self, ctx):
        q = getattr(self.bot, "music_queues", {}).get(ctx.guild.id, {})
        if not q.get("current"):
            return await ctx.send("❌ Nada tocando no momento!")
        await ctx.send(f"🎵 **{q.get('current_title') or 'Áudio'}**")

    @commands.command(name="clear")
    async def clear(self, ctx):
        if ctx.guild.id in getattr(self.bot, "music_queues", {}):
            self.bot.music_queues[ctx.guild.id]["queue"] = []
        await ctx.send("🧹 Fila limpa!")


async def setup(bot):
    await bot.add_cog(Musica(bot))
