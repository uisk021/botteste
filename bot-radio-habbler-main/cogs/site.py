import discord
from discord.ext import commands, tasks
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
from datetime import datetime

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
SITE_URL = "https://radiohabbler.com.br"
CANAL_LOCUTOR_ID = 1458855777191202833
CANAL_NOTICIAS_ID = 1554620684208963645
CANAL_BOASVINDAS_ID = 1458855776931283239

class Site(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ultimo_locutor = None
        self.checar_locucao.start()
        self.checar_noticias.start()
        self.status_dyn.start()
        self.checar_aniversario.start()

    def cog_unload(self):
        self.checar_locucao.cancel()
        self.checar_noticias.cancel()
        self.status_dyn.cancel()
        self.checar_aniversario.cancel()

    async def raspar_locutor(self):
        try:
            async with aiohttp.ClientSession(headers=HEADERS) as s:
                async with s.get(SITE_URL, timeout=10) as r:
                    if r.status != 200: return None
                    soup = BeautifulSoup(await r.text(), "html.parser")
                    img = soup.find('img', src=re.compile(r'imaging\.habblet\.city', re.I))
                    avatar = img['src'] if img else "https://imaging.habblet.city/avatarimage?figure=hr-3163-61&size=b"
                    loc, prog = "AutoDJ", "Normal"
                    if img:
                        c = img.find_parent()
                        while c and len(c.get_text(strip=True)) < 4: c = c.find_parent()
                        if c:
                            t = [x for x in c.stripped_strings if x.upper() not in ["ON AIR","AO VIVO","NO AR","RÁDIO"]]
                            if len(t) >= 1: loc = t[0]
                            if len(t) >= 2: prog = t[1]
                    return {"locutor": loc, "programa": prog, "avatar": avatar}
        except: return None

    async def raspar_noticia(self):
        try:
            async with aiohttp.ClientSession(headers=HEADERS) as s:
                async with s.get(SITE_URL, timeout=10) as r:
                    if r.status != 200: return None
                    soup = BeautifulSoup(await r.text(), "html.parser")
                    links = soup.find_all("a", href=re.compile(r"/(noticia|post|artigo)/", re.I))
                    if not links: links = soup.find_all("a", href=re.compile(r"noticia\.php\?id=", re.I))
                    if links:
                        l = links[0]
                        url = urljoin(SITE_URL, l.get("href", ""))
                        titulo = l.get_text(strip=True) or "Nova Notícia"
                        img = l.find("img")
                        return {"url": url, "titulo": titulo, "imagem": urljoin(SITE_URL, img["src"]) if img and img.get("src") else None}
        except: return None

    # Tasks
    @tasks.loop(seconds=30)
    async def checar_locucao(self):
        canal = self.bot.get_channel(CANAL_LOCUTOR_ID)
        if not canal: return
        d = await self.raspar_locutor()
        if not d: return
        loc = d["locutor"]
        if "autodj" not in loc.lower() and "habbler" not in loc.lower() and loc != self.ultimo_locutor:
            self.ultimo_locutor = loc
            embed = discord.Embed(title="📻 AO VIVO NA RÁDIO HABBLER!", description=f"**{loc}** assumiu a transmissão!", color=discord.Color.gold(), url=SITE_URL)
            embed.add_field(name="🎙️ Locutor:", value=f"**{loc}**", inline=True)
            embed.add_field(name="🎧 Programa:", value=f"**{d['programa']}**", inline=True)
            embed.set_thumbnail(url=d["avatar"])
            await canal.send(content=f"🚨 @everyone **{loc}** está AO VIVO!", embed=embed)
        elif "autodj" in loc.lower(): self.ultimo_locutor = "AutoDJ"

    @checar_locucao.before_loop
    async def before_locucao(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=2)
    async def checar_noticias(self):
        canal = self.bot.get_channel(CANAL_NOTICIAS_ID)
        if not canal: return
        n = await self.raspar_noticia()
        if not n or n["url"] == self.bot.config.get("ultima_noticia_url"): return
        self.bot.config["ultima_noticia_url"] = n["url"]
        self.bot.salvar_config()
        embed = discord.Embed(title=f"📰 {n['titulo']}", url=n["url"], color=discord.Color.blue())
        if n.get("imagem"): embed.set_image(url=n["imagem"])
        await canal.send(content="🔔 @everyone **Nova Notícia!**", embed=embed)

    @checar_noticias.before_loop
    async def before_noticias(self):
        await self.bot.wait_until_ready()

    @tasks.loop(seconds=15)
    async def status_dyn(self):
        try:
            d = await self.raspar_locutor()
            loc = d["locutor"] if d else "AutoDJ"
            if "autodj" not in loc.lower():
                await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"🎧 {loc} no ar!"))
            else:
                await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.streaming, name="Rádio Habbler", url=SITE_URL))
        except: pass

    @status_dyn.before_loop
    async def before_status(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=24)
    async def checar_aniversario(self):
        hoje = datetime.now().strftime("%d/%m")
        for uid, data in self.bot.config.get("aniversarios", {}).items():
            if data == hoje:
                nick = self.bot.config.get("verificados", {}).get(uid, "Membro")
                canal = self.bot.get_channel(CANAL_BOASVINDAS_ID)
                if canal:
                    avatar = f"https://imaging.habblet.city/avatarimage?user={nick}&action=std&direction=2&head_direction=3&gesture=sml&size=l"
                    embed = discord.Embed(title="🎂 Feliz Aniversário de Conta!", description=f"Parabéns <@{uid}> (**{nick}**)!\nHoje sua conta do Habblet faz aniversário! 🎉🎈", color=discord.Color.gold())
                    embed.set_thumbnail(url=avatar)
                    await canal.send(embed=embed)

    @checar_aniversario.before_loop
    async def before_aniv(self):
        await self.bot.wait_until_ready()

    # Comandos informativos
    @commands.command(aliases=["aovivo"])
    async def locutor(self, ctx):
        m = await ctx.send("🔍...")
        d = await self.raspar_locutor()
        if not d: return await m.edit(content="❌ Erro ao consultar!")
        e = discord.Embed(title="📻 No Ar", color=discord.Color.purple(), url=SITE_URL)
        e.add_field(name="🎙️ Locutor(a):", value=f"**{d['locutor']}**", inline=True)
        e.set_thumbnail(url=d["avatar"])
        await m.edit(content=None, embed=e)

    @commands.command(aliases=["noticias"])
    async def noticia(self, ctx):
        m = await ctx.send("🔍...")
        n = await self.raspar_noticia()
        if not n: return await m.edit(content="❌ Erro ao buscar notícia!")
        e = discord.Embed(title=f"📰 {n['titulo']}", url=n["url"], color=discord.Color.blue())
        if n.get("imagem"): e.set_image(url=n["imagem"])
        await m.edit(content=None, embed=e)

    @commands.command()
    async def visu(self, ctx, *, nick: str):
        avatar = f"https://imaging.habblet.city/avatarimage?user={nick}&action=std&direction=2&head_direction=3&gesture=sml&size=l"
        embed = discord.Embed(title=f"🎨 Visual de {nick}", color=discord.Color.purple())
        embed.set_image(url=avatar)
        await ctx.send(embed=embed)

    @commands.command()
    async def hotel(self, ctx):
        await ctx.send("🔍 Consultando Habblet...")
        try:
            async with aiohttp.ClientSession(headers=HEADERS) as s:
                async with s.get("https://habblet.city", timeout=10) as r:
                    if r.status == 200:
                        soup = BeautifulSoup(await r.text(), "html.parser")
                        players = soup.find(string=re.compile(r"\d+\s*(online|players|usuários)", re.I))
                        embed = discord.Embed(title="🏨 Status do Habblet", color=discord.Color.green())
                        embed.add_field(name="🟢 Status", value="**Online**", inline=True)
                        embed.add_field(name="👥 Players", value=players.strip() if players else "Indisponível", inline=True)
                        await ctx.send(embed=embed)
                    else: await ctx.send("❌ Habblet offline!")
        except: await ctx.send("❌ Erro ao consultar!")

    @commands.command()
    async def nivel(self, ctx, membro: discord.Member = None):
        membro = membro or ctx.author
        uid = str(membro.id)
        xp_total = self.bot.config.get("xp", {}).get(uid, 0)
        nivel, xp = 1, xp_total
        while xp >= nivel * 100:
            xp -= nivel * 100
            nivel += 1
        xp_next = nivel * 100
        cargo = "🏆 Lenda" if nivel >= 20 else "⭐ Veterano" if nivel >= 10 else "🎧 Fã" if nivel >= 5 else "👤 Ouvinte"
        barra = "█" * int((xp / xp_next) * 10) + "░" * (10 - int((xp / xp_next) * 10))
        nick = self.bot.config.get("verificados", {}).get(uid, membro.display_name)
        avatar = f"https://imaging.habblet.city/avatarimage?user={nick}&action=std&direction=2&head_direction=3&gesture=sml&size=l"
        embed = discord.Embed(title=f"🏆 Nível de {nick}", color=discord.Color.purple())
        embed.add_field(name="📊 Nível", value=f"**{nivel}** {cargo}", inline=True)
        embed.add_field(name="⭐ XP", value=f"{xp}/{xp_next}", inline=True)
        embed.add_field(name="📈 Progresso", value=f"`{barra}`", inline=False)
        embed.set_thumbnail(url=avatar)
        await ctx.send(embed=embed)

    @commands.command()
    async def ranking(self, ctx):
        xp_data = self.bot.config.get("xp", {})
        if not xp_data: return await ctx.send("❌ Ninguém tem XP ainda!")
        top = sorted(xp_data.items(), key=lambda x: x[1], reverse=True)[:10]
        texto = ""
        for i, (uid, xp_total) in enumerate(top, 1):
            niv, xp = 1, xp_total
            while xp >= niv * 100:
                xp -= niv * 100
                niv += 1
            nick = self.bot.config.get("verificados", {}).get(uid, f"<@{uid}>")
            m = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"**{i}.**"
            texto += f"{m} **{nick}** — Nível {niv} ({xp_total} XP)\n"
        embed = discord.Embed(title="🏆 Ranking de Atividade", description=texto, color=discord.Color.gold())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Site(bot))
