import discord
from discord.ext import commands
import aiohttp
import random
import string
import asyncio
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

CANAL_STAFF_VERIFICACAO_ID = 1555463317588549672  # Canal fechado da Staff
CANAL_BOASVINDAS_ID = 1458855776931283239         # Canal público de boas-vindas

# ==========================================
# PAINEL DA STAFF (BOTÕES APROVAR / REJEITAR)
# ==========================================
class PainelStaffVerificacaoView(discord.ui.View):
    def __init__(self, bot, user_id: int, nick: str):
        super().__init__(timeout=None)
        self.bot = bot
        self.user_id = user_id
        self.nick = nick

    @discord.ui.button(label="Aprovar Verificação", style=discord.ButtonStyle.success, emoji="✅", custom_id="btn_aprovar_verif_staff")
    async def aprovar(self, interaction: discord.Interaction, btn: discord.ui.Button):
        is_staff = str(interaction.user.id) in self.bot.config.get("staff", {}) or interaction.user.id == interaction.guild.owner_id
        if not is_staff:
            return await interaction.response.send_message("❌ Apenas a Staff pode aprovar verificações!", ephemeral=True)

        guild = interaction.guild
        membro = guild.get_member(self.user_id)

        # 1. Salva o vínculo no banco
        self.bot.config.setdefault("verificados", {})[str(self.user_id)] = self.nick
        self.bot.config.setdefault("aniversarios", {})[str(self.user_id)] = datetime.now().strftime("%d/%m")
        self.bot.salvar_config()

        # 2. Altera o apelido do membro no Discord
        if membro:
            try:
                await membro.edit(nick=self.nick)
            except discord.Forbidden:
                pass

            # 3. Entrega o cargo configurado
            cid = self.bot.config.get("cargo_verificado")
            if cid:
                cargo = guild.get_role(cid)
                if cargo:
                    try:
                        await membro.add_roles(cargo)
                    except discord.Forbidden:
                        pass

        # 4. Atualiza a mensagem na Staff
        embed_original = interaction.message.embeds[0]
        embed_original.color = discord.Color.green()
        embed_original.title = "✅ VERIFICAÇÃO APROVADA"
        embed_original.add_field(name="🛡️ Aprovado por:", value=interaction.user.mention, inline=False)
        self.clear_items()
        await interaction.response.edit_message(embed=embed_original, view=self)

        # 5. Avisa o membro por DM
        if membro:
            try:
                await membro.send(f"🎉 **Sua conta do Habblet ({self.nick}) foi aprovada pela Staff!** Seu acesso foi liberado!")
            except:
                pass

        # 6. Manda mensagem de Boas-Vindas no canal público
        canal_bv = guild.get_channel(CANAL_BOASVINDAS_ID)
        if canal_bv and membro:
            avatar = f"https://imaging.habblet.city/avatarimage?user={self.nick}&action=std&direction=2&head_direction=3&gesture=sml&size=l"
            bv_embed = discord.Embed(
                title="🎉 Novo Membro Verificado!",
                description=f"{membro.mention} comprovou ser **{self.nick}** no Habblet!\nBem-vindo(a) à **Rádio Habbler**! 🏨",
                color=discord.Color.gold()
            )
            bv_embed.set_thumbnail(url=avatar)
            bv_embed.set_footer(text=f"Membro #{len(guild.members)}")
            await canal_bv.send(embed=bv_embed)

    @discord.ui.button(label="Rejeitar Verificação", style=discord.ButtonStyle.danger, emoji="❌", custom_id="btn_rejeitar_verif_staff")
    async def rejeitar(self, interaction: discord.Interaction, btn: discord.ui.Button):
        is_staff = str(interaction.user.id) in self.bot.config.get("staff", {}) or interaction.user.id == interaction.guild.owner_id
        if not is_staff:
            return await interaction.response.send_message("❌ Apenas a Staff pode rejeitar verificações!", ephemeral=True)

        guild = interaction.guild
        membro = guild.get_member(self.user_id)

        embed_original = interaction.message.embeds[0]
        embed_original.color = discord.Color.red()
        embed_original.title = "❌ VERIFICAÇÃO REJEITADA"
        embed_original.add_field(name="🛡️ Rejeitado por:", value=interaction.user.mention, inline=False)
        self.clear_items()
        await interaction.response.edit_message(embed=embed_original, view=self)

        if membro:
            try:
                await membro.send(f"❌ **Sua verificação para a conta ({self.nick}) foi rejeitada pela Staff.** Tente novamente ajustando sua missão no jogo.")
            except:
                pass

# ==========================================
# MODAL E INTERAÇÃO COM O USUÁRIO
# ==========================================
class VerificarModal(discord.ui.Modal, title="🏨 Identificação Habblet"):
    nick_habblet = discord.ui.TextInput(
        label="Qual é o seu Nick no Habblet?",
        placeholder="Ex: Uisk.",
        min_length=2,
        max_length=25,
        required=True
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        nick = self.nick_habblet.value.strip()
        user_id = interaction.user.id
        guild = interaction.guild

        # Checa duplicidade
        for u, n in self.bot.config.get("verificados", {}).items():
            if n.lower() == nick.lower() and u != str(user_id):
                return await interaction.response.send_message(
                    f"❌ O nick **{nick}** já foi vinculado por outra conta neste servidor!",
                    ephemeral=True
                )

        await interaction.response.defer(ephemeral=True)

        codigo = "HABBLER-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
        }

        nome_canal = f"verif-{nick.lower()[:12]}"
        try:
            canal_temp = await guild.create_text_channel(name=nome_canal, overwrites=overwrites)
        except Exception as e:
            return await interaction.followup.send("❌ Não consegui criar a sala de verificação. Verifique as permissões do bot!", ephemeral=True)

        avatar_url = f"https://imaging.habblet.city/avatarimage?user={nick}&action=std&direction=2&head_direction=3&gesture=sml&size=l"

        embed_instrucoes = discord.Embed(
            title="📸 Envie o Print do seu Perfil!",
            description=(
                f"Olá {interaction.user.mention}! Para comprovar que a conta **{nick}** é sua:\n\n"
                f"1️⃣ Entre no **Habblet** com o seu personagem.\n"
                f"2️⃣ Altere a sua **Missão (Mote)** no jogo para exatamente:\n"
                f"👉 **`{codigo}`**\n\n"
                f"3️⃣ Abra o seu **Perfil no Habblet**.\n"
                f"4️⃣ Envie o **PRINT DA TELA** ou uma mensagem de confirmação aqui no canal!\n\n"
                f"⏰ *Esta sala será apagada automaticamente em 5 minutos.*"
            ),
            color=discord.Color.gold()
        )
        embed_instrucoes.set_thumbnail(url=avatar_url)
        await canal_temp.send(content=f"{interaction.user.mention}", embed=embed_instrucoes)

        await interaction.followup.send(
            f"✅ Abra o canal {canal_temp.mention} para enviar seu print/confirmação! O canal será apagado em 5 minutos.",
            ephemeral=True
        )

        # Aguarda qualquer mensagem do usuário no canal por até 5 minutos (300 segundos)
        try:
            msg_user = await self.bot.wait_for(
                "message", 
                check=lambda m: m.channel == canal_temp and m.author == interaction.user, 
                timeout=300
            )
            
            imagem_url = msg_user.attachments[0].url if msg_user.attachments else None

            canal_staff = guild.get_channel(CANAL_STAFF_VERIFICACAO_ID)
            if canal_staff:
                embed_staff = discord.Embed(
                    title="🏨 SOLICITAÇÃO DE VERIFICAÇÃO",
                    description=(
                        f"👤 **Membro:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                        f"🎮 **Nick solicitado:** `{nick}`\n"
                        f"🔑 **Código exigido:** `{codigo}`\n"
                        f"💬 **Texto enviado:** {msg_user.content or 'Apenas imagem'}\n"
                    ),
                    color=discord.Color.gold()
                )
                embed_staff.set_thumbnail(url=avatar_url)
                if imagem_url:
                    embed_staff.set_image(url=imagem_url)
                embed_staff.set_footer(text=f"Solicitado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")

                await canal_staff.send(
                    embed=embed_staff,
                    view=PainelStaffVerificacaoView(self.bot, user_id=interaction.user.id, nick=nick)
                )

            await canal_temp.send("✅ **Solicitação enviada para a Staff!** Este canal será apagado em 5 segundos...")
            await asyncio.sleep(5)
            try:
                await canal_temp.delete()
            except:
                pass

        except asyncio.TimeoutError:
            try:
                await canal_temp.delete()
            except:
                pass

class BotaoVerificarView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Vincular Conta Habblet", style=discord.ButtonStyle.success, emoji="🏨", custom_id="btn_abrir_modal_verificacao")
    async def cb(self, interaction: discord.Interaction, btn: discord.ui.Button):
        await interaction.response.send_modal(VerificarModal(self.bot))

class Verificacao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(BotaoVerificarView(self.bot))

    @commands.command()
    async def painelverificar(self, ctx, senha: str = None):
        """Cria o painel oficial de verificação no canal"""
        if not self.bot.verificar_autorizacao(ctx, senha):
            return await ctx.send("❌ Sem permissão!")

        embed = discord.Embed(
            title="🏨 Registro & Verificação • Rádio Habbler",
            description=(
                "Seja bem-vindo(a) à comunidade oficial da **Rádio Habbler**!\n\n"
                "Para vincular seu personagem do **Habblet** e ter acesso ao servidor:\n\n"
                "1️⃣ Clique no botão verde **'Vincular Conta Habblet'**.\n"
                "2️⃣ Digite o seu Nick exatamente como está no jogo.\n"
                "3️⃣ Siga as instruções da sala privada para enviar o print do seu perfil!\n\n"
                "🛡️ *Sistema 100% seguro com validação manual da Staff.*"
            ),
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url="https://imaging.habblet.city/avatarimage?figure=hr-3163-61.hd-207-10&size=b")
        embed.set_footer(text="Rádio Habbler • Sistema de Identificação")

        await ctx.channel.send(embed=embed, view=BotaoVerificarView(self.bot))
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command()
    async def setarcargo(self, ctx, cargo: discord.Role, senha: str = None):
        if not self.bot.verificar_autorizacao(ctx, senha):
            return await ctx.send("❌ Sem permissão!")
        self.bot.config["cargo_verificado"] = cargo.id
        self.bot.salvar_config()
        await ctx.send(f"✅ Cargo de verificado configurado para: {cargo.mention}!")

    @commands.command()
    async def desvincular(self, ctx, membro: discord.Member, senha: str = None):
        if not self.bot.verificar_autorizacao(ctx, senha):
            return await ctx.send("❌ Sem permissão!")
        uid = str(membro.id)
        if uid in self.bot.config.get("verificados", {}):
            n = self.bot.config["verificados"].pop(uid)
            self.bot.salvar_config()
            await ctx.send(f"✅ O vínculo de {membro.mention} (Nick: `{n}`) foi removido!")
        else:
            await ctx.send("❌ Este membro não possui nenhuma conta vinculada!")

    @commands.command()
    async def perfil(self, ctx, membro: discord.Member = None):
        membro = membro or ctx.author
        nick = self.bot.config.get("verificados", {}).get(str(membro.id))
        if not nick:
            return await ctx.send("❌ Este membro ainda não vinculou a conta do Habblet!")

        avatar = f"https://imaging.habblet.city/avatarimage?user={nick}&action=std&direction=2&head_direction=3&gesture=sml&size=l"
        embed = discord.Embed(title=f"🏨 Perfil Habblet • {nick}", color=discord.Color.purple())
        embed.add_field(name="👤 Discord:", value=membro.mention, inline=True)
        embed.add_field(name="🎮 Nick no Jogo:", value=f"**{nick}**", inline=True)
        embed.set_thumbnail(url=avatar)
        embed.set_footer(text="Rádio Habbler")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Verificacao(bot))
