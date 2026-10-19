import discord
from discord.ext import commands
import random

class Geral(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ajuda(self, ctx):
        embed = discord.Embed(title="🐥 Patinho • Central de Ajuda", color=discord.Color.blue())
        embed.add_field(name="🏨 Verificação", value="`hbl perfil` `hbl painelverificar` `hbl setarcargo`", inline=False)
        embed.add_field(name="🎵 Música", value="`hbl play` `hbl add` `hbl pause` `hbl resume` `hbl skip` `hbl stop` `hbl playlist` `hbl nowplaying` `hbl remove` `hbl clear`", inline=False)
        embed.add_field(name="📻 Rádio", value="`hbl radio` `hbl playradio` `hbl listradio` `hbl favradio` `hbl delfavradio` `hbl radio247`", inline=False)
        embed.add_field(name="📰 Site", value="`hbl locutor` `hbl noticia`", inline=False)
        embed.add_field(name="🎮 Jogos", value="`hbl rps` `hbl rpg` `hbl plantar` `hbl regar` `hbl colher` `hbl fazenda` `hbl uno` `hbl mao` `hbl jogar` `hbl trivia`", inline=False)
        embed.add_field(name="💰 Economia", value="`hbl daily` `hbl saldo` `hbl pagar` `hbl top`", inline=False)
        embed.add_field(name="🎮 Geral", value="`hbl ajuda` `hbl ping` `hbl ola` `hbl diga` `hbl moeda` `hbl nivel` `hbl ranking` `hbl visu` `hbl hotel`", inline=False)
        embed.add_field(name="🎫 Tickets", value="`hbl painelticket` `hbl fecharticket`", inline=False)
        embed.add_field(name="🛡️ Moderação", value="`hbl limpar` `hbl kick` `hbl ban` `hbl unban` `hbl mute` `hbl unmute` `hbl warn` `hbl warns`", inline=False)
        embed.set_footer(text="Prefixo: hbl | 🐥 Patinho v1.0")
        await ctx.send(embed=embed)

    @commands.command()
    async def ping(self, ctx):
        lat = round(self.bot.latency * 1000)
        embed = discord.Embed(title="🏓 Pong!", color=discord.Color.green())
        embed.add_field(name="📡 Latência", value=f"**{lat}ms**", inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def ola(self, ctx):
        await ctx.send(f"Olá {ctx.author.mention}! 👋")

    @commands.command()
    async def diga(self, ctx, *, t: str):
        await ctx.send(t)

    @commands.command()
    async def moeda(self, ctx):
        await ctx.send(f"🪙 **{random.choice(['Cara', 'Coroa'])}**!")

async def setup(bot):
    await bot.add_cog(Geral(bot))