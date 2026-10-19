import discord
from discord.ext import commands
import random

COSMETICS = {
    "abracar": {"emoji": "💕", "msg": "deu um abraço apertado em", "g1": "sml", "g2": "sml", "a1": "std", "a2": "std", "d1": 2, "d2": 4},
    "beijar": {"emoji": "😘", "msg": "deu um beijão em", "g1": "sml", "g2": "sml", "a1": "std", "a2": "std", "d1": 2, "d2": 6},
    "carinho": {"emoji": "🥰", "msg": "fez carinho em", "g1": "sml", "g2": "sml", "a1": "std", "a2": "std", "d1": 2, "d2": 4},
    "namoro": {"emoji": "💑", "msg": "pediu em namoro", "g1": "sml", "g2": "sml", "a1": "std", "a2": "std", "d1": 2, "d2": 4},
    "presente": {"emoji": "🎁", "msg": "entregou um presente para", "g1": "sml", "g2": "srp", "a1": "std", "a2": "std", "d1": 2, "d2": 4},
    "dancar": {"emoji": "💃", "msg": "chamou para dançar com", "g1": "sml", "g2": "sml", "a1": "std", "a2": "std", "d1": 3, "d2": 3},
    "festa": {"emoji": "🎉", "msg": "começou a festejar com", "g1": "sml", "g2": "sml", "a1": "std", "a2": "std", "d1": 2, "d2": 4},
    "brindar": {"emoji": "🥂", "msg": "fez um brinde com", "g1": "sml", "g2": "sml", "a1": "drk", "a2": "drk", "d1": 2, "d2": 4},
    "highfive": {"emoji": "🖐️", "msg": "mandou um HIGH FIVE para", "g1": "sml", "g2": "sml", "a1": "wav", "a2": "wav", "d1": 2, "d2": 4},
    "selfie": {"emoji": "📸", "msg": "tirou uma selfie com", "g1": "sml", "g2": "sml", "a1": "std", "a2": "std", "d1": 3, "d2": 3},
    "brigar": {"emoji": "😡", "msg": "partiu pra cima de", "g1": "agr", "g2": "agr", "a1": "std", "a2": "std", "d1": 2, "d2": 6},
    "tapa": {"emoji": "👋", "msg": "deu um tapa em", "g1": "agr", "g2": "sad", "a1": "wav", "a2": "std", "d1": 2, "d2": 4},
    "zoar": {"emoji": "😂", "msg": "zoou a cara de", "g1": "sml", "g2": "sad", "a1": "std", "a2": "std", "d1": 2, "d2": 4},
    "ignorar": {"emoji": "🙄", "msg": "ignorou completamente", "g1": "std", "g2": "sad", "a1": "std", "a2": "std", "d1": 6, "d2": 2},
    "chorar": {"emoji": "😢", "msg": "começou a chorar na frente de", "g1": "sad", "g2": "std", "a1": "std", "a2": "std", "d1": 2, "d2": 4},
    "tchau": {"emoji": "👋", "msg": "se despediu de", "g1": "sad", "g2": "std", "a1": "wav", "a2": "std", "d1": 6, "d2": 2},
    "respeito": {"emoji": "🤝", "msg": "mandou respeito para", "g1": "std", "g2": "std", "a1": "std", "a2": "std", "d1": 2, "d2": 4},
    "desculpa": {"emoji": "🥺", "msg": "pediu desculpas de joelhos para", "g1": "sad", "g2": "std", "a1": "std", "a2": "std", "d1": 2, "d2": 4},
    "sentar": {"emoji": "🪑", "msg": "sentou para conversar com", "g1": "sml", "g2": "sml", "a1": "sit", "a2": "sit", "d1": 2, "d2": 4},
}

SOLO_COSMETICS = {
    "humor": {"emoji": "😤", "msg2": "hoje é:", "g": ["std", "sml", "sad", "agr", "eyb", "srp"], "nicks": ["Normal", "Feliz", "Triste", "Raivoso", "Duvidoso", "Surpreso"]},
    "deitado": {"emoji": "😴", "msg2": "foi descansar deitadinho no hotel!", "g": "sml", "a": "lay"},
    "bebendo": {"emoji": "🍹", "msg2": "está relaxando e tomando uma bebida gelada!", "g": "sml", "a": "drk"},
    "dancando": {"emoji": "🕺", "msg2": "começou a quebrar tudo dançando sozinho!", "g": "sml", "a": "std", "d": 3},
    "pose": {"emoji": "✨", "msg2": "fez uma pose incrível para as câmeras!", "g": "eyb", "a": "std"},
}

class Interacoes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._registrar_comandos()

    def _registrar_comandos(self):
        for nome, dados in COSMETICS.items():
            if self.bot.get_command(nome): self.bot.remove_command(nome)
            def criar_duo(d):
                @commands.command(name=nome)
                async def cmd(ctx, membro: discord.Member = None):
                    if not membro: return await ctx.send(f"⚠️ Marque alguém! Ex: `hbl {ctx.invoked_with} @usuario`")
                    anick = self.bot.config.get("verificados", {}).get(str(ctx.author.id), ctx.author.display_name)
                    tnick = self.bot.config.get("verificados", {}).get(str(membro.id), membro.display_name)
                    av1 = f"https://imaging.habblet.city/avatarimage?user={anick}&gesture={d['g1']}&action={d['a1']}&direction={d['d1']}&head_direction={d['d1']}&size=l"
                    av2 = f"https://imaging.habblet.city/avatarimage?user={tnick}&gesture={d['g2']}&action={d['a2']}&direction={d['d2']}&head_direction={d['d2']}&size=l"
                    embed = discord.Embed(description=f"{d['emoji']} **{ctx.author.mention}** {d['msg']} **{membro.mention}**!", color=discord.Color.purple())
                    embed.set_thumbnail(url=av1)
                    embed.set_image(url=av2)
                    await ctx.send(embed=embed)
                return cmd
            self.bot.add_command(criar_duo(dados))

        for nome, dados in SOLO_COSMETICS.items():
            if self.bot.get_command(nome): self.bot.remove_command(nome)
            def criar_solo(n, d):
                @commands.command(name=nome)
                async def cmd(ctx):
                    nick = self.bot.config.get("verificados", {}).get(str(ctx.author.id), ctx.author.display_name)
                    g = d.get("g", "std")
                    msg_f = d["msg2"]
                    if n == "humor":
                        idx = random.randint(0, len(d["g"]) - 1)
                        g = d["g"][idx]
                        msg_f = f"{d['msg2']} **{d['nicks'][idx]}**!"
                    av = f"https://imaging.habblet.city/avatarimage?user={nick}&gesture={g}&action={d.get('a','std')}&direction={d.get('d',2)}&head_direction={d.get('d',2)}&size=l"
                    embed = discord.Embed(description=f"{d['emoji']} **{ctx.author.mention}** {msg_f}", color=discord.Color.purple())
                    embed.set_image(url=av)
                    await ctx.send(embed=embed)
                return cmd
            self.bot.add_command(criar_solo(nome, dados))

    @commands.command()
    async def apostar(self, ctx, valor: str = None):
        embed = discord.Embed(
            title="🚫 APOSTA BLOQUEADA!",
            description=f"⚠️ {ctx.author.mention}, o Patinho apoia o Jogo Responsável!\n\n🎰 Apostas no Brasil são regulamentadas. Se precisar de ajuda:\n📞 **Ligue 141** (CVV).",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def obaoba(self, ctx, membro: discord.Member = None):
        membro = membro or ctx.author
        embed = discord.Embed(
            title="🚨 ADVERTÊNCIA AUTOMÁTICA",
            description=f"⚠️ {membro.mention}, você recebeu uma **ADVERTÊNCIA FALSA** por oba-oba em público! 😳\n\n*(Brincadeira! Nenhum warn real foi aplicado.)*",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def xingar(self, ctx, *, alvo: str = None):
        if alvo and "lapidei" in alvo.lower():
            await ctx.send(f"❤️ {ctx.author.mention} tentou xingar o Lapidei, mas no fundo... **ELE(A) TE AMA MUITO!** 🥰🌹")
        else:
            await ctx.send(f"😡 {ctx.author.mention} chamou {alvo or 'os pixels'} de **bobba-lixe**!")

async def setup(bot):
    await bot.add_cog(Interacoes(bot))