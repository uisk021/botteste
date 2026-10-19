import discord
from discord.ext import commands
from datetime import datetime

class Economia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def daily(self, ctx):
        uid = str(ctx.author.id)
        hoje = datetime.now().strftime("%Y-%m-%d")
        
        if "daily_cooldown" not in self.bot.config: 
            self.bot.config["daily_cooldown"] = {}
            
        if self.bot.config["daily_cooldown"].get(uid) == hoje:
            return await ctx.send(f"⏰ {ctx.author.mention}, você já resgatou seu daily hoje! Volte amanhã.")
            
        self.bot.config["daily_cooldown"][uid] = hoje
        nick = self.bot.config.get("verificados", {}).get(uid, ctx.author.display_name)
        
        # Salva permanente no MongoDB com o nick do Habblet!
        self.bot.add_saldo(uid, 500, user_name=nick)
        await self.bot.add_xp_jogo(uid, 20, user_name=nick)
        
        saldo_atual = self.bot.get_saldo(uid)
        avatar = f"https://imaging.habblet.city/avatarimage?user={nick}&action=std&direction=2&head_direction=3&gesture=sml&size=l"
        
        embed = discord.Embed(
            title="💰 Daily Resgatado!",
            description=f"{ctx.author.mention} recebeu **+500 moedas**!\n\n💵 Saldo: **{saldo_atual:,}** moedas\n⭐ +20 XP bônus!",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=avatar)
        await ctx.send(embed=embed)

    @commands.command(aliases=["atm", "bal", "carteira", "money"])
    async def saldo(self, ctx, membro: discord.Member = None):
        membro = membro or ctx.author
        uid = str(membro.id)
        s = self.bot.get_saldo(uid)
        nick = self.bot.config.get("verificados", {}).get(uid, membro.display_name)
        avatar = f"https://imaging.habblet.city/avatarimage?user={nick}&action=std&direction=2&head_direction=3&gesture=sml&size=l"
        
        embed = discord.Embed(title=f"💵 Carteira de {nick}", color=discord.Color.gold())
        embed.add_field(name="💰 Moedas", value=f"**{s:,}**", inline=True)
        embed.set_thumbnail(url=avatar)
        await ctx.send(embed=embed)

    @commands.command(aliases=["pay", "transferir"])
    async def pagar(self, ctx, membro: discord.Member, valor: int):
        if membro == ctx.author:
            return await ctx.send("❌ Você não pode transferir moedas para você mesmo!")
        if membro.bot: 
            return await ctx.send("❌ Não pode pagar um bot!")
        if valor <= 0: 
            return await ctx.send("❌ O valor precisa ser maior que 0!")
            
        uid = str(ctx.author.id)
        alvo_id = str(membro.id)
        
        if self.bot.get_saldo(uid) < valor:
            return await ctx.send(f"❌ Saldo insuficiente! Você tem **{self.bot.get_saldo(uid):,}** moedas.")
            
        nick_autor = self.bot.config.get("verificados", {}).get(uid, ctx.author.display_name)
        nick_alvo = self.bot.config.get("verificados", {}).get(alvo_id, membro.display_name)
        
        # Transfere as moedas no MongoDB
        self.bot.add_saldo(uid, -valor, user_name=nick_autor)
        self.bot.add_saldo(alvo_id, valor, user_name=nick_alvo)

        await ctx.send(f"✅ {ctx.author.mention} transferiu **💰 {valor:,} moedas** para {membro.mention}!")

    @commands.command(aliases=["rank", "ricos"])
    async def top(self, ctx):
        # Consulta os mais ricos direto do MongoDB
        ranking = []
        if self.bot.db is not None:
            col = self.bot.db["usuarios"]
            ranking = list(col.find({}, {"user_name": 1, "saldo": 1}).sort("saldo", -1).limit(10))
            
        if not ranking: 
            return await ctx.send("❌ Ninguém tem moedas ainda!")
            
        texto = ""
        for i, user in enumerate(ranking, 1):
            nick = user.get("user_name", "Usuário")
            moedas = user.get("saldo", 0)
            m = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"**{i}.**"
            texto += f"{m} **{nick}** — 💰 {moedas:,} moedas\n"
            
        embed = discord.Embed(title="💰 Ranking dos Mais Ricos", description=texto, color=discord.Color.gold())
        embed.set_footer(text="Veja o ranking completo no site da Rádio!")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Economia(bot))
