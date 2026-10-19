import discord
from discord.ext import commands
from datetime import timedelta

class Moderacao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def setarstaff(self, ctx, m: discord.Member, s: str):
        if ctx.author != ctx.guild.owner: return
        self.bot.config["staff"][str(m.id)] = s
        self.bot.salvar_config()
        await ctx.send(f"✅ {m.mention} agora é staff!")

    @commands.command()
    async def removerstaff(self, ctx, m: discord.Member):
        if ctx.author != ctx.guild.owner: return
        self.bot.config["staff"].pop(str(m.id), None)
        self.bot.salvar_config()
        await ctx.send(f"✅ {m.mention} foi removido da staff!")

    @commands.command()
    async def addpalavra(self, ctx, s: str, *, p: str):
        if not self.bot.verificar_autorizacao(ctx, s): return
        if p.lower() not in self.bot.config["palavras_proibidas"]:
            self.bot.config["palavras_proibidas"].append(p)
            self.bot.salvar_config()
            await ctx.send("✅ Palavra proibida adicionada!")

    @commands.command()
    async def removepalavra(self, ctx, s: str, *, p: str):
        if not self.bot.verificar_autorizacao(ctx, s): return
        if p in self.bot.config["palavras_proibidas"]:
            self.bot.config["palavras_proibidas"].remove(p)
            self.bot.salvar_config()
            await ctx.send("✅ Palavra removida!")

    @commands.command()
    async def addlink(self, ctx, s: str, *, p: str):
        if not self.bot.verificar_autorizacao(ctx, s): return
        self.bot.config["links_proibidos"].append(p)
        self.bot.salvar_config()
        await ctx.send("✅ Filtro de link adicionado!")

    @commands.command()
    async def removelink(self, ctx, s: str, *, p: str):
        if not self.bot.verificar_autorizacao(ctx, s): return
        if p in self.bot.config["links_proibidos"]:
            self.bot.config["links_proibidos"].remove(p)
            self.bot.salvar_config()
            await ctx.send("✅ Filtro de link removido!")

    @commands.command()
    async def setarlog(self, ctx, s: str, c: discord.TextChannel):
        if not self.bot.verificar_autorizacao(ctx, s): return
        self.bot.config["log_channel"] = c.id
        self.bot.salvar_config()
        await ctx.send(f"✅ Canal de logs definido: {c.mention}")

    @commands.command()
    async def verconfig(self, ctx, s: str):
        if not self.bot.verificar_autorizacao(ctx, s): return
        e = discord.Embed(title="⚙️ Configurações Ativas", color=discord.Color.purple())
        e.add_field(name="Staffs", value=str(len(self.bot.config["staff"])))
        e.add_field(name="Palavras Bloqueadas", value=str(len(self.bot.config["palavras_proibidas"])))
        e.add_field(name="Links Bloqueados", value=str(len(self.bot.config["links_proibidos"])))
        e.add_field(name="Verificados", value=str(len(self.bot.config.get("verificados", {}))))
        await ctx.send(embed=e)

    @commands.command()
    async def limpar(self, ctx, s: str, q: int = 5):
        if not self.bot.verificar_autorizacao(ctx, s): return
        await ctx.channel.purge(limit=q + 1)
        await ctx.send("🧹 Limpeza concluída!", delete_after=3)

    @commands.command()
    async def kick(self, ctx, s: str, m: discord.Member, *, r="Sem motivo"):
        if not self.bot.verificar_autorizacao(ctx, s): return
        await m.kick(reason=r)
        await ctx.send(f"👢 {m.mention} foi expulso!")

    @commands.command()
    async def ban(self, ctx, s: str, m: discord.Member, *, r="Sem motivo"):
        if not self.bot.verificar_autorizacao(ctx, s): return
        await m.ban(reason=r)
        await ctx.send(f"🔨 {m.mention} foi banido permanentemente!")

    @commands.command()
    async def unban(self, ctx, s: str, u: str):
        if not self.bot.verificar_autorizacao(ctx, s): return
        user = await self.bot.fetch_user(int(u))
        await ctx.guild.unban(user)
        await ctx.send(f"🔓 {user.mention} foi desbanido!")

    @commands.command()
    async def mute(self, ctx, s: str, m: discord.Member, min: int = 10, *, r=""):
        if not self.bot.verificar_autorizacao(ctx, s): return
        await m.timeout(timedelta(minutes=min), reason=r)
        await ctx.send(f"🔇 {m.mention} silenciado por {min} minutos!")

    @commands.command()
    async def unmute(self, ctx, s: str, m: discord.Member):
        if not self.bot.verificar_autorizacao(ctx, s): return
        await m.timeout(None)
        await ctx.send(f"🔊 {m.mention} foi desmutado!")

    @commands.command()
    async def warn(self, ctx, s: str, m: discord.Member, *, r=""):
        if not self.bot.verificar_autorizacao(ctx, s): return
        uid = str(m.id)
        self.bot.config.setdefault("warns", {}).setdefault(uid, 0)
        self.bot.config["warns"][uid] += 1
        self.bot.salvar_config()
        t = self.bot.config["warns"][uid]
        await ctx.send(f"⚠️ {m.mention} recebeu uma advertência ({t}/3)!")
        if t >= 3:
            await m.ban(reason="3 warns acumulados")
            self.bot.config["warns"][uid] = 0
            self.bot.salvar_config()
            await ctx.send(f"🔨 {m.mention} foi banido automaticamente por acumular 3 advertências!")

    @commands.command()
    async def warns(self, ctx, m: discord.Member):
        t = self.bot.config.get("warns", {}).get(str(m.id), 0)
        await ctx.send(f"⚠️ {m.mention} possui **{t}/3** advertências.")

async def setup(bot):
    await bot.add_cog(Moderacao(bot))