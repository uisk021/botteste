import discord
from discord.ext import commands
import re
import asyncio

EMOJI_CANAL = {
    "anúncio": "📢", "regra": "📜", "regras": "📜", "verificação": "🏨",
    "verificacao": "🏨", "link": "🔗", "chat": "💬", "geral": "💬",
    "rádio": "📻", "radio": "📻", "notícia": "📰", "noticia": "📰",
    "música": "🎵", "musica": "🎵", "foto": "📸", "imagem": "📸",
    "comando": "🤖", "bot": "🤖", "suporte": "🎫", "ticket": "🎫",
    "sugestão": "💡", "sugestao": "💡", "live": "🔴", "evento": "📅",
    "voz": "🔊", "call": "🔊", "boas-vindas": "👋", "boasvindas": "👋",
    "nível": "🏆", "nivel": "🏆", "xp": "⭐", "ranking": "🏅",
    "staff": "🛡️", "log": "📋", "logs": "📋", "confissão": "🤫",
    "confissao": "🤫", "sorteio": "🎁", "loja": "🛒", "banco": "💰",
}

EMOJI_CARGO = {
    "dono": "👑", "diretor": "👑", "fundador": "👑",
    "admin": "⚙️", "administrador": "⚙️",
    "locutor": "🎙️", "dj": "🎙️",
    "mod": "🛡️", "moderador": "🛡️", "staff": "🛡️",
    "jornalista": "📰", "promotor": "📰", "repórter": "📰",
    "vip": "⭐", "apoiador": "⭐", "premium": "⭐",
    "verificado": "🏨", "cidadão": "🏨", "membro": "🏨",
    "ouvinte": "🎧", "fã": "🎧", "fan": "🎧",
    "veterano": "🏅", "lenda": "🏆", "bot": "🤖",
}

def pegar_emoji_canal(nome):
    nome_lower = nome.lower()
    for palavra, emoji in EMOJI_CANAL.items():
        if palavra in nome_lower: return emoji
    return "📌"

def pegar_emoji_cargo(nome):
    nome_lower = nome.lower()
    for palavra, emoji in EMOJI_CARGO.items():
        if palavra in nome_lower: return emoji
    return "🎭"

class Decoracao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def decorar(self, ctx, senha: str = None):
        if ctx.author != ctx.guild.owner and not self.bot.verificar_autorizacao(ctx, senha):
            return await ctx.send("❌ Sem permissão!")

        guild = ctx.guild
        msg = await ctx.send("🎨 **Iniciando redecoração do servidor...**\n⏳ Aguarde alguns segundos!")

        canais_renomeados, cargos_renomeados, canais_criados, erros = 0, 0, 0, 0

        # Categorias
        for cat in [c for c in guild.channels if isinstance(c, discord.CategoryChannel)]:
            nome_puro = re.sub(r'[^\w\sáàâãéèêíïóôõúüçÁÀÂÃÉÈÊÍÏÓÔÕÚÜÇ-]', '', cat.name.strip()).strip() or cat.name.strip()
            novo = f"━━━「{nome_puro.upper()}」━━━"
            if cat.name != novo:
                try:
                    await cat.edit(name=novo)
                    canais_renomeados += 1
                    await asyncio.sleep(0.5)
                except: erros += 1

        # Canais
        for channel in guild.channels:
            if isinstance(channel, discord.CategoryChannel): continue
            if channel.name.startswith("ticket-"): continue
            nome_puro = re.sub(r'[^\w\sáàâãéèêíïóôõúüçÁÀÂÃÉÈÊÍÏÓÔÕÚÜÇ-]', '', channel.name.strip()).strip().replace(" ", "-").lower() or channel.name.strip()
            emoji = pegar_emoji_canal(nome_puro)
            if isinstance(channel, discord.VoiceChannel) and emoji == "📌": emoji = "🔊"
            novo = f"{emoji}・{nome_puro}"
            if channel.name != novo:
                try:
                    await channel.edit(name=novo)
                    canais_renomeados += 1
                    await asyncio.sleep(0.5)
                except: erros += 1

        # Cargos
        for role in guild.roles:
            if role.name == "@everyone" or role.managed or "〣" in role.name: continue
            nome_puro = re.sub(r'[^\w\sáàâãéèêíïóôõúüçÁÀÂÃÉÈÊÍÏÓÔÕÚÜÇ ]', '', role.name.strip()).strip() or role.name.strip()
            emoji = pegar_emoji_cargo(nome_puro)
            novo = f"{emoji} 〣 {nome_puro}"
            if role.name != novo:
                try:
                    await role.edit(name=novo)
                    cargos_renomeados += 1
                    await asyncio.sleep(0.5)
                except: erros += 1

        # Cria canais de nível se não existirem
        canais_existentes = [c.name.lower() for c in guild.channels]
        cat_niveis = discord.utils.get(guild.categories, name=lambda n: "NÍVEL" in n.upper() or "XP" in n.upper())
        if not cat_niveis:
            try:
                cat_niveis = await guild.create_category("━━━「NÍVEIS E XP」━━━")
                await asyncio.sleep(0.5)
            except: cat_niveis = None

        canais_nivel = {
            "🏆・ranking-geral": "Ranking de atividade",
            "📊・meu-nível": "Consulte seu nível (hbl nivel)",
            "🎉・level-up": "Avisos de subida de nível",
        }
        for nome_c, topico in canais_nivel.items():
            if not any(nome_c.split("・")[-1] in c for c in canais_existentes):
                try:
                    await guild.create_text_channel(name=nome_c, category=cat_niveis, topic=topico)
                    canais_criados += 1
                    await asyncio.sleep(0.5)
                except: erros += 1

        embed = discord.Embed(
            title="🎨 Redecoração Concluída!",
            description=f"✅ Canais: {canais_renomeados}\n✅ Cargos: {cargos_renomeados}\n✅ Canais criados: {canais_criados}\n❌ Erros: {erros}",
            color=discord.Color.green()
        )
        await msg.edit(content=None, embed=embed)

async def setup(bot):
    await bot.add_cog(Decoracao(bot))