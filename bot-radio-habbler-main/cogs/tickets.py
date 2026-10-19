import discord
from discord.ext import commands
import asyncio
import yt_dlp

CATEGORIAS_TICKET = {
    "duvidas": {"emoji": "❓", "nome": "Dúvidas Gerais", "cor": discord.Color.blue(), "tipo": "normal"},
    "musica": {"emoji": "🎵", "nome": "Pedir Música", "cor": discord.Color.green(), "tipo": "musica"},
    "denuncia": {"emoji": "🚨", "nome": "Denúncias", "cor": discord.Color.red(), "tipo": "autobot"},
    "recrutamento": {"emoji": "🎙️", "nome": "Recrutamento", "cor": discord.Color.purple(), "tipo": "autobot"},
    "parceria": {"emoji": "🤝", "nome": "Parcerias", "cor": discord.Color.gold(), "tipo": "autobot"},
    "sugestao": {"emoji": "💡", "nome": "Sugestões", "cor": discord.Color.orange(), "tipo": "sugestao"},
}

CANAL_SUGESTOES_ID = 1555457159037321317
CANAL_RESPOSTAS_TICKET_ID = 1555463317588549672

def buscar_musica_ticket(query):
    try:
        with yt_dlp.YoutubeDL({'format': 'bestaudio', 'quiet': True, 'noplaylist': True}) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            if 'entries' in info and info['entries']:
                info = info['entries'][0]
                return info.get('webpage_url', query), info.get('title', '?'), info.get('duration', 0)
    except:
        pass
    return None, None, None

class TicketModal(discord.ui.Modal, title="📝 Descreva seu problema"):
    descricao = discord.ui.TextInput(
        label="Descreva o motivo do ticket:",
        placeholder="Detalhe aqui...",
        style=discord.TextStyle.paragraph,
        min_length=5,
        max_length=1000,
        required=True
    )

    def __init__(self, bot, cat_key):
        super().__init__()
        self.bot = bot
        self.cat_key = cat_key

    async def on_submit(self, interaction: discord.Interaction):
        cat = CATEGORIAS_TICKET[self.cat_key]
        guild = interaction.guild
        membro = interaction.user

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True),
            membro: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        nome = f"ticket-{self.cat_key}-{membro.name[:10].lower()}"
        try:
            canal = await guild.create_text_channel(name=nome, overwrites=overwrites)
        except:
            return await interaction.response.send_message("❌ Não tenho permissão para criar canais!", ephemeral=True)

        self.bot.config.setdefault("tickets", {})[str(canal.id)] = {"usuario": str(membro.id), "categoria": self.cat_key}
        self.bot.salvar_config()

        embed = discord.Embed(
            title=f"{cat['emoji']} Ticket: {cat['nome']}",
            description=f"**Aberto por:** {membro.mention}\n\n**📝 Mensagem:**\n{self.descricao.value}",
            color=cat["cor"]
        )
        view = TicketBotoesView(self.bot, canal.id) if self.cat_key == "sugestao" else TicketFecharView(self.bot, canal.id)
        await canal.send(content=f"{membro.mention} | Staff", embed=embed, view=view)
        await interaction.response.send_message(f"✅ Ticket criado em {canal.mention}!", ephemeral=True)

class TicketFecharView(discord.ui.View):
    def __init__(self, bot, cid):
        super().__init__(timeout=None)
        self.bot = bot
        self.cid = cid

    @discord.ui.button(label="Fechar Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="btn_fechar_ticket_fecharview")
    async def fechar(self, interaction: discord.Interaction, btn: discord.ui.Button):
        uid = self.bot.config.get("tickets", {}).get(str(interaction.channel_id), {}).get("usuario")
        is_staff = str(interaction.user.id) in self.bot.config.get("staff", {}) or interaction.user.id == interaction.guild.owner_id
        is_dono = str(interaction.user.id) == uid

        if not is_staff and not is_dono:
            return await interaction.response.send_message("❌ Apenas a staff ou o dono do ticket podem fechar!", ephemeral=True)

        if str(interaction.channel_id) in self.bot.config.get("tickets", {}):
            del self.bot.config["tickets"][str(interaction.channel_id)]
            self.bot.salvar_config()

        await interaction.response.send_message("🔒 Fechando e apagando canal em 3 segundos...")
        await asyncio.sleep(3)
        try:
            await interaction.channel.delete()
        except:
            pass

class TicketBotoesView(discord.ui.View):
    def __init__(self, bot, cid):
        super().__init__(timeout=None)
        self.bot = bot
        self.cid = cid

    @discord.ui.button(label="Aprovar Sugestão", style=discord.ButtonStyle.success, emoji="✅", custom_id="btn_aprovar_sugestao")
    async def aprovar(self, interaction: discord.Interaction, btn: discord.ui.Button):
        is_staff = str(interaction.user.id) in self.bot.config.get("staff", {}) or interaction.user.id == interaction.guild.owner_id
        if not is_staff:
            return await interaction.response.send_message("❌ Apenas a staff pode aprovar!", ephemeral=True)

        canal_sug = interaction.guild.get_channel(CANAL_SUGESTOES_ID)
        if canal_sug:
            msgs = [m async for m in interaction.channel.history(limit=5, oldest_first=True) if m.embeds]
            desc = msgs[0].embeds[0].description if msgs else "Sugestão aprovada"
            await canal_sug.send(embed=discord.Embed(title="💡 Nova Sugestão Aprovada!", description=desc, color=discord.Color.green()))

        if str(interaction.channel_id) in self.bot.config.get("tickets", {}):
            del self.bot.config["tickets"][str(interaction.channel_id)]
            self.bot.salvar_config()

        await interaction.response.send_message("✅ Sugestão aprovada e enviada para o canal público! Fechando...")
        await asyncio.sleep(2)
        try:
            await interaction.channel.delete()
        except:
            pass

    @discord.ui.button(label="Rejeitar Sugestão", style=discord.ButtonStyle.danger, emoji="❌", custom_id="btn_rejeitar_sugestao")
    async def rejeitar(self, interaction: discord.Interaction, btn: discord.ui.Button):
        is_staff = str(interaction.user.id) in self.bot.config.get("staff", {}) or interaction.user.id == interaction.guild.owner_id
        if not is_staff:
            return await interaction.response.send_message("❌ Apenas a staff pode rejeitar!", ephemeral=True)

        if str(interaction.channel_id) in self.bot.config.get("tickets", {}):
            del self.bot.config["tickets"][str(interaction.channel_id)]
            self.bot.salvar_config()

        await interaction.response.send_message("❌ Sugestão rejeitada pela staff. Fechando canal...")
        await asyncio.sleep(2)
        try:
            await interaction.channel.delete()
        except:
            pass

class TicketSelectView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.select(
        placeholder="📋 Selecione a categoria do seu atendimento...",
        custom_id="select_ticket_categoria_v2",
        options=[
            discord.SelectOption(label=info["nome"], value=key, emoji=info["emoji"])
            for key, info in CATEGORIAS_TICKET.items()
        ]
    )
    async def sel(self, interaction: discord.Interaction, sel: discord.ui.Select):
        cat_key = sel.values[0]
        cat = CATEGORIAS_TICKET[cat_key]

        # Evita abrir múltiplos tickets
        for cid, info in self.bot.config.get("tickets", {}).items():
            if info.get("usuario") == str(interaction.user.id):
                c = interaction.guild.get_channel(int(cid))
                if c:
                    return await interaction.response.send_message(f"⚠️ Você já possui um atendimento aberto em {c.mention}!", ephemeral=True)

        if cat["tipo"] == "autobot":
            await interaction.response.send_message(f"🤖 Iniciando atendimento para **{cat['nome']}**...", ephemeral=True)
            guild, membro = interaction.guild, interaction.user
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True),
                membro: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            }
            nome = f"ticket-{cat_key}-{membro.name[:10].lower()}"
            try:
                canal = await guild.create_text_channel(name=nome, overwrites=overwrites)
            except:
                return await interaction.followup.send("❌ Não consegui criar o canal de atendimento!", ephemeral=True)

            self.bot.config.setdefault("tickets", {})[str(canal.id)] = {"usuario": str(membro.id), "categoria": cat_key}
            self.bot.salvar_config()
            await interaction.followup.send(f"✅ Canal criado: {canal.mention}", ephemeral=True)

            perguntas = {
                "denuncia": ["🚨 **Qual o Nick do infrator?**", "📝 **O que aconteceu? Descreva com detalhes.**", "📸 **Possui prints ou links de prova?**"],
                "recrutamento": ["🎙️ **Qual seu Nick no Habblet?**", "📅 **Qual sua idade?**", "⏰ **Qual seu horário disponível?**", "💬 **Por que deseja fazer parte da equipe?**"],
                "parceria": ["🤝 **Qual o nome do seu projeto?**", "🔗 **Qual o link oficial?**", "📊 **Quantos membros ativos possuem?**", "💡 **Qual a proposta de parceria?**"]
            }
            respostas = []
            for p in perguntas.get(cat_key, ["Descreva seu caso:"]):
                await canal.send(f"{membro.mention} {p}")
                try:
                    msg = await self.bot.wait_for("message", check=lambda m: m.channel == canal and m.author == membro, timeout=300)
                    respostas.append(f"**{p}**\n{msg.content}")
                except asyncio.TimeoutError:
                    await canal.send("⏰ Tempo limite esgotado. Atendimento cancelado.")
                    del self.bot.config["tickets"][str(canal.id)]
                    self.bot.salvar_config()
                    await asyncio.sleep(3)
                    return await canal.delete()

            canal_staff = guild.get_channel(CANAL_RESPOSTAS_TICKET_ID)
            if canal_staff:
                embed = discord.Embed(title=f"{cat['emoji']} Ficha: {cat['nome']}", description="\n\n".join(respostas), color=cat["cor"])
                embed.set_footer(text=f"Enviado por {membro.display_name} ({membro.id})")
                await canal_staff.send(embed=embed)

            await canal.send("✅ Suas informações foram registradas e enviadas para a Staff!", view=TicketFecharView(self.bot, canal.id))

        elif cat["tipo"] == "musica":
            await interaction.response.send_message("🎵 Criando canal para Pedido de Música...", ephemeral=True)
            guild, membro = interaction.guild, interaction.user
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True),
                membro: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            }
            nome = f"ticket-musica-{membro.name[:10].lower()}"
            try:
                canal = await guild.create_text_channel(name=nome, overwrites=overwrites)
            except:
                return await interaction.followup.send("❌ Não consegui criar o canal!", ephemeral=True)

            self.bot.config.setdefault("tickets", {})[str(canal.id)] = {"usuario": str(membro.id), "categoria": "musica"}
            self.bot.salvar_config()
            await interaction.followup.send(f"✅ Acesse seu pedido em {canal.mention}", ephemeral=True)

            await canal.send(f"{membro.mention} 🎵 **Qual música você gostaria de ouvir na Rádio Habbler?**\nDigite o nome da música ou cole o link:")
            try:
                msg = await self.bot.wait_for("message", check=lambda m: m.channel == canal and m.author == membro, timeout=300)
                query = msg.content
                await canal.send("🔍 Localizando música...")
                loop = asyncio.get_event_loop()
                url, title, dur = await loop.run_in_executor(None, buscar_musica_ticket, query)
                if url:
                    mins, secs = (dur // 60 if dur else 0), (dur % 60 if dur else 0)
                    embed = discord.Embed(title="🎵 Música Encontrada!", description=f"**{title}**\n⏱️ Duração: {mins}:{secs:02d}\n🔗 [Ouvir no YouTube]({url})", color=discord.Color.green())
                    await canal.send(embed=embed, content=f"{membro.mention} **Confirma o envio deste pedido para a programação?** (Digite `sim` ou `nao`)")
                    try:
                        conf = await self.bot.wait_for("message", check=lambda m: m.channel == canal and m.author == membro, timeout=60)
                        if conf.content.lower() in ["sim", "s", "yes"]:
                            canal_staff = guild.get_channel(CANAL_RESPOSTAS_TICKET_ID)
                            if canal_staff:
                                await canal_staff.send(embed=discord.Embed(title="🎵 Pedido de Música para o Locutor", description=f"**Ouvinte:** {membro.mention}\n**Música:** {title}\n**Link:** {url}", color=discord.Color.green()))
                            await canal.send("✅ Pedido enviado ao locutor com sucesso!")
                        else:
                            await canal.send("❌ Pedido cancelado pelo ouvinte.")
                    except:
                        pass
                else:
                    await canal.send("❌ Não encontrei a música especificada.")
            except asyncio.TimeoutError:
                pass
            await canal.send(view=TicketFecharView(self.bot, canal.id))

        else:
            await interaction.response.send_modal(TicketModal(self.bot, cat_key))

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(TicketSelectView(self.bot))
        self.bot.add_view(TicketFecharView(self.bot, 0))
        self.bot.add_view(TicketBotoesView(self.bot, 0))

    @commands.command()
    async def painelticket(self, ctx, senha: str = None):
        """Cria o painel de atendimento interativo"""
        if not self.bot.verificar_autorizacao(ctx, senha):
            return await ctx.send("❌ Sem permissão!")

        embed = discord.Embed(
            title="🎫 Central de Suporte & Atendimento • Rádio Habbler",
            description=(
                "Precisa de suporte ou deseja falar com a equipe da rádio?\n\n"
                "📌 **Selecione a categoria desejada no menu abaixo:**\n\n"
                "❓ **Dúvidas Gerais** — Tire dúvidas sobre o fã-site ou Discord\n"
                "🎵 **Pedir Música** — Peça uma música diretamente para o locutor\n"
                "💡 **Sugestões** — Envie ideias para a equipe avaliar\n"
                "🚨 **Denúncias** — Denuncie infratores de forma privada\n"
                "🎙️ **Recrutamento** — Candidate-se para a equipe da Rádio Habbler\n"
                "🤝 **Parcerias** — Proponha parcerias institucionais"
            ),
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url="https://imaging.habblet.city/avatarimage?figure=hr-3163-61.hd-207-10&size=b")
        embed.set_footer(text="Rádio Habbler • Atendimento Automatizado")

        await ctx.channel.send(embed=embed, view=TicketSelectView(self.bot))
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command()
    async def fecharticket(self, ctx, senha: str = None):
        """Fecha o canal de ticket atual"""
        if not self.bot.verificar_autorizacao(ctx, senha):
            return await ctx.send("❌ Sem permissão!")

        cid = str(ctx.channel.id)
        if cid not in self.bot.config.get("tickets", {}):
            return await ctx.send("❌ Este canal não é um ticket ativo!")

        del self.bot.config["tickets"][cid]
        self.bot.salvar_config()
        await ctx.send("🔒 Fechando canal em 3 segundos...")
        await asyncio.sleep(3)
        await ctx.channel.delete()

async def setup(bot):
    await bot.add_cog(Tickets(bot))
