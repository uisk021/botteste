import discord
from discord.ext import commands
import random
import asyncio
from datetime import datetime

# ==========================================
# 1. PEDRA, PAPEL, TESOURA (RPS)
# ==========================================
class RPSView(discord.ui.View):
    def __init__(self, bot, user_id):
        super().__init__(timeout=30)
        self.bot = bot
        self.user_id = user_id

    async def jogar(self, interaction: discord.Interaction, escolha: str):
        if str(interaction.user.id) != str(self.user_id):
            return await interaction.response.send_message("❌ Essa jogada não é sua!", ephemeral=True)
        self.clear_items()
        bot_escolha = random.choice(["🪨", "📄", "✂️"])
        vitorias = {"🪨": "✂️", "📄": "🪨", "✂️": "📄"}
        nomes = {"🪨": "Pedra", "📄": "Papel", "✂️": "Tesoura"}

        if escolha == bot_escolha:
            moedas, xp, msg = 10, 5, "🤝 **Empate!**"
            cor = discord.Color.orange()
        elif vitorias[escolha] == bot_escolha:
            moedas, xp, msg = 30, 15, "🏆 **Você venceu!**"
            cor = discord.Color.green()
        else:
            moedas, xp, msg = 5, 5, "😢 **Você perdeu!**"
            cor = discord.Color.red()

        self.bot.add_saldo(self.user_id, moedas)
        await self.bot.add_xp_jogo(self.user_id, xp)
        embed = discord.Embed(
            title="✂️ Pedra, Papel, Tesoura",
            description=f"{msg}\n\nVocê: {escolha} **{nomes[escolha]}**\nBot: {bot_escolha} **{nomes[bot_escolha]}**\n\n💰 +{moedas} moedas | ⭐ +{xp} XP",
            color=cor
        )
        embed.set_footer(text=f"Saldo: {self.bot.get_saldo(self.user_id)} moedas")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Pedra", emoji="🪨", style=discord.ButtonStyle.primary)
    async def pedra(self, i, b): await self.jogar(i, "🪨")
    @discord.ui.button(label="Papel", emoji="📄", style=discord.ButtonStyle.primary)
    async def papel(self, i, b): await self.jogar(i, "📄")
    @discord.ui.button(label="Tesoura", emoji="✂️", style=discord.ButtonStyle.primary)
    async def tesoura(self, i, b): await self.jogar(i, "✂️")

# ==========================================
# 2. BATALLA RPG
# ==========================================
MONSTROS = [
    {"nome": "Slime Bobba", "emoji": "🟢", "hp": 30, "atk": 5, "xp": 20, "moedas": 40},
    {"nome": "Frank Furioso", "emoji": "😡", "hp": 50, "atk": 10, "xp": 35, "moedas": 70},
    {"nome": "Pato de Borracha Gigante", "emoji": "🦆", "hp": 40, "atk": 8, "xp": 25, "moedas": 50},
    {"nome": "Troll do Chat", "emoji": "👹", "hp": 60, "atk": 12, "xp": 40, "moedas": 80},
    {"nome": "Habbo Fantasma", "emoji": "👻", "hp": 45, "atk": 9, "xp": 30, "moedas": 60},
    {"nome": "Dragão de Pixels", "emoji": "🐉", "hp": 80, "atk": 15, "xp": 60, "moedas": 120},
    {"nome": "Boss: Moderador Corrupto", "emoji": "💀", "hp": 100, "atk": 20, "xp": 80, "moedas": 200},
]

class RPGView(discord.ui.View):
    def __init__(self, bot, user_id, monstro, hp_jogador):
        super().__init__(timeout=60)
        self.bot = bot
        self.user_id = user_id
        self.monstro = monstro.copy()
        self.hp_jogador = hp_jogador
        self.hp_max = hp_jogador

    def barra_hp(self, atual, maximo):
        cheio = int((max(0, atual) / maximo) * 10)
        return "❤️" * cheio + "🖤" * (10 - cheio)

    @discord.ui.button(label="⚔️ Atacar", style=discord.ButtonStyle.danger)
    async def atacar(self, interaction: discord.Interaction, btn: discord.ui.Button):
        if str(interaction.user.id) != str(self.user_id):
            return await interaction.response.send_message("❌ Não é sua vez!", ephemeral=True)
        
        dano_jogador = random.randint(8, 18)
        crit = random.random() < 0.15
        if crit: dano_jogador *= 2
        self.monstro["hp"] -= dano_jogador

        if self.monstro["hp"] <= 0:
            self.clear_items()
            xp, moedas = self.monstro["xp"], self.monstro["moedas"]
            self.bot.add_saldo(self.user_id, moedas)
            await self.bot.add_xp_jogo(self.user_id, xp)
            embed = discord.Embed(
                title="🏆 Vitória!",
                description=f"Você derrotou {self.monstro['emoji']} **{self.monstro['nome']}**!\n\n💰 +{moedas} moedas | ⭐ +{xp} XP",
                color=discord.Color.gold()
            )
            return await interaction.response.edit_message(embed=embed, view=self)

        dano_monstro = random.randint(max(1, self.monstro["atk"] - 3), self.monstro["atk"] + 3)
        self.hp_jogador -= dano_monstro

        if self.hp_jogador <= 0:
            self.clear_items()
            await self.bot.add_xp_jogo(self.user_id, 5)
            embed = discord.Embed(title="💀 Derrota!", description=f"O {self.monstro['emoji']} **{self.monstro['nome']}** te derrotou! +5 XP", color=discord.Color.red())
            return await interaction.response.edit_message(embed=embed, view=self)

        embed = discord.Embed(
            title=f"⚔️ Batalha: {self.monstro['emoji']} {self.monstro['nome']}",
            description=(
                f"{'💥 CRÍTICO! ' if crit else ''}Você causou **{dano_jogador}** de dano!\n"
                f"O monstro causou **{dano_monstro}** de dano!\n\n"
                f"🧑 Sua vida: {self.barra_hp(self.hp_jogador, self.hp_max)} ({max(0,self.hp_jogador)}/{self.hp_max})\n"
                f"{self.monstro['emoji']} Monstro: {self.barra_hp(max(0,self.monstro['hp']), 100)}"
            ),
            color=discord.Color.orange()
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🛡️ Defender", style=discord.ButtonStyle.primary)
    async def defender(self, interaction: discord.Interaction, btn: discord.ui.Button):
        if str(interaction.user.id) != str(self.user_id): return
        dano_monstro = random.randint(1, max(1, self.monstro["atk"] - 5))
        self.hp_jogador -= dano_monstro
        cura = random.randint(3, 8)
        self.hp_jogador = min(self.hp_max, self.hp_jogador + cura)
        embed = discord.Embed(
            title="🛡️ Defesa!",
            description=f"Você curou **{cura}** HP e levou **{dano_monstro}** de dano!\n🧑 Vida: {self.barra_hp(self.hp_jogador, self.hp_max)}",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🏃 Fugir", style=discord.ButtonStyle.secondary)
    async def fugir(self, interaction: discord.Interaction, btn: discord.ui.Button):
        if str(interaction.user.id) != str(self.user_id): return
        self.clear_items()
        await self.bot.add_xp_jogo(self.user_id, 3)
        await interaction.response.edit_message(embed=discord.Embed(title="🏃 Fuga!", description="Você fugiu da batalha! +3 XP", color=discord.Color.greyple()), view=self)

# ==========================================
# 3. FAZENDINHA
# ==========================================
PLANTAS = {
    "trigo": {"emoji": "🌾", "tempo": 60, "moedas": 20, "xp": 5},
    "cenoura": {"emoji": "🥕", "tempo": 120, "moedas": 35, "xp": 10},
    "morango": {"emoji": "🍓", "tempo": 180, "moedas": 50, "xp": 15},
    "girassol": {"emoji": "🌻", "tempo": 300, "moedas": 80, "xp": 20},
    "melancia": {"emoji": "🍉", "tempo": 600, "moedas": 150, "xp": 35},
}

# ==========================================
# 4. UNO
# ==========================================
CORES_UNO = ["🔴", "🟢", "🔵", "🟡"]
NUMEROS_UNO = ["0","1","2","3","4","5","6","7","8","9","⏭️","🔄","+2"]
CARTAS_ESPECIAIS = ["🌈 Curinga", "🌈+4"]

class UNOJogo:
    def __init__(self):
        self.jogadores = {}
        self.mesa = None
        self.turno = 0
        self.ativo = False

    def criar_baralho(self):
        baralho = []
        for cor in CORES_UNO:
            for num in NUMEROS_UNO:
                baralho.append(f"{cor} {num}")
                if num != "0": baralho.append(f"{cor} {num}")
        for _ in range(4): baralho.extend(CARTAS_ESPECIAIS)
        random.shuffle(baralho)
        return baralho

class UNOEntrarView(discord.ui.View):
    def __init__(self, bot, criador_id, canal_id):
        super().__init__(timeout=60)
        self.bot = bot
        self.criador_id = criador_id
        self.canal_id = canal_id

    @discord.ui.button(label="Entrar no Jogo", style=discord.ButtonStyle.success, emoji="🃏")
    async def entrar(self, interaction: discord.Interaction, btn: discord.ui.Button):
        uid = str(interaction.user.id)
        cid = str(self.canal_id)
        jogo = self.bot.uno_jogos.get(cid)
        if not jogo: return
        if uid in jogo.jogadores: return await interaction.response.send_message("❌ Você já está no jogo!", ephemeral=True)
        if len(jogo.jogadores) >= 4: return await interaction.response.send_message("❌ Sala cheia (máx 4)!", ephemeral=True)
        jogo.jogadores[uid] = {"nome": interaction.user.display_name, "cartas": []}
        await interaction.response.send_message(f"✅ {interaction.user.mention} entrou no jogo! ({len(jogo.jogadores)}/4)", ephemeral=True)

    @discord.ui.button(label="🚀 Começar!", style=discord.ButtonStyle.primary, emoji="🚀")
    async def comecar(self, interaction: discord.Interaction, btn: discord.ui.Button):
        if str(interaction.user.id) != str(self.criador_id):
            return await interaction.response.send_message("❌ Só o criador pode começar!", ephemeral=True)
        cid = str(self.canal_id)
        jogo = self.bot.uno_jogos.get(cid)
        if not jogo or len(jogo.jogadores) < 2:
            return await interaction.response.send_message("❌ Precisa de pelo menos 2 jogadores!", ephemeral=True)
        self.clear_items()
        baralho = jogo.criar_baralho()
        for uid in jogo.jogadores:
            jogo.jogadores[uid]["cartas"] = [baralho.pop() for _ in range(7)]
        jogo.mesa = baralho.pop()
        jogo.ativo = True
        primeiro = list(jogo.jogadores.keys())[0]
        embed = discord.Embed(
            title="🃏 UNO - Iniciado!",
            description=f"📋 Mesa: **{jogo.mesa}**\n🎯 Vez de: **{jogo.jogadores[primeiro]['nome']}**\n\nUse `hbl mao` para ver cartas e `hbl jogar <número>` para jogar!",
            color=discord.Color.red()
        )
        await interaction.response.edit_message(content=None, embed=embed, view=self)

# ==========================================
# 5. TRIVIA HABBO
# ==========================================
TRIVIA_PERGUNTAS = [
    {"p": "Em que ano o Habbo Hotel foi criado?", "op": ["1999", "2000", "2001", "2003"], "r": 1},
    {"p": "Qual empresa criou o Habbo?", "op": ["Zynga", "Sulake", "Rovio", "EA"], "r": 1},
    {"p": "Qual a moeda premium do Habbo?", "op": ["Duckets", "Créditos", "Diamonds", "Coins"], "r": 2},
    {"p": "O que é 'Bobba' no Habbo?", "op": ["Um pet", "Um filtro de palavrão", "Uma dança", "Um quarto"], "r": 1},
    {"p": "Qual país é a sede do Habbo?", "op": ["Suécia", "Noruega", "Finlândia", "Dinamarca"], "r": 2},
]

class TriviaView(discord.ui.View):
    def __init__(self, bot, pergunta, user_id):
        super().__init__(timeout=15)
        self.bot = bot
        self.pergunta = pergunta
        self.user_id = user_id
        self.respondido = False

    async def responder(self, interaction: discord.Interaction, idx: int):
        if str(interaction.user.id) != str(self.user_id): return
        if self.respondido: return
        self.respondido = True
        self.clear_items()
        if idx == self.pergunta["r"]:
            self.bot.add_saldo(self.user_id, 50)
            await self.bot.add_xp_jogo(self.user_id, 15)
            msg, cor = "✅ **Correto!** +50 moedas +15 XP", discord.Color.green()
        else:
            await self.bot.add_xp_jogo(self.user_id, 3)
            msg, cor = f"❌ **Errado!** Resposta: **{self.pergunta['op'][self.pergunta['r']]}**. +3 XP", discord.Color.red()
        embed = discord.Embed(title="❓ Trivia", description=f"{self.pergunta['p']}\n\n{msg}", color=cor)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="A", style=discord.ButtonStyle.primary)
    async def a(self, i, b): await self.responder(i, 0)
    @discord.ui.button(label="B", style=discord.ButtonStyle.primary)
    async def b(self, i, b): await self.responder(i, 1)
    @discord.ui.button(label="C", style=discord.ButtonStyle.primary)
    async def c(self, i, b): await self.responder(i, 2)
    @discord.ui.button(label="D", style=discord.ButtonStyle.primary)
    async def d(self, i, b): await self.responder(i, 3)

# ==========================================
# COG PRINCIPAL DE JOGOS
# ==========================================
class Jogos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["ppt"])
    async def rps(self, ctx):
        """Joga Pedra, Papel, Tesoura contra o bot"""
        embed = discord.Embed(title="✂️ Pedra, Papel, Tesoura", description="Escolha sua jogada nos botões abaixo!", color=discord.Color.purple())
        await ctx.send(embed=embed, view=RPSView(self.bot, ctx.author.id))

    @commands.command()
    async def rpg(self, ctx):
        """Inicia uma batalha RPG contra um monstro aleatório"""
        monstro = random.choice(MONSTROS)
        embed = discord.Embed(title=f"⚔️ Um {monstro['emoji']} {monstro['nome']} apareceu!", description="Escolha sua ação!", color=discord.Color.red())
        await ctx.send(embed=embed, view=RPGView(self.bot, ctx.author.id, monstro, 100))

    @commands.command()
    async def plantar(self, ctx, planta: str = None):
        """Planta uma semente na fazendinha"""
        if not planta or planta.lower() not in PLANTAS:
            lista = "\n".join(f"{d['emoji']} **{nome}** — ⏱️ {d['tempo']}s | 💰 {d['moedas']} moedas" for nome, d in PLANTAS.items())
            embed = discord.Embed(title="🌱 Sementes Disponíveis", description=lista, color=discord.Color.green())
            embed.set_footer(text="Use: hbl plantar <nome>")
            return await ctx.send(embed=embed)
        
        planta = planta.lower()
        dados = PLANTAS[planta]
        uid = str(ctx.author.id)
        if "fazenda" not in self.bot.config: self.bot.config["fazenda"] = {}
        if "planta" in self.bot.config["fazenda"].get(uid, {}):
            return await ctx.send("❌ Você já tem algo plantado! Use `hbl colher` quando estiver pronto.")
        
        self.bot.config["fazenda"][uid] = {
            "planta": planta, "emoji": dados["emoji"], "plantado_em": datetime.now().timestamp(),
            "tempo": dados["tempo"], "moedas": dados["moedas"], "xp": dados["xp"], "regado": False
        }
        self.bot.salvar_config()
        await ctx.send(f"🌱 Você plantou {dados['emoji']} **{planta}**! Tempo: **{dados['tempo']}s** (use `hbl regar` para acelerar)")

    @commands.command()
    async def regar(self, ctx):
        """Rega sua planta para diminuir o tempo pela metade"""
        uid = str(ctx.author.id)
        f = self.bot.config.get("fazenda", {}).get(uid)
        if not f or "planta" not in f: return await ctx.send("❌ Você não tem nada plantado! Use `hbl plantar`.")
        if f.get("regado"): return await ctx.send("💧 Sua planta já foi regada!")
        
        self.bot.config["fazenda"][uid]["regado"] = True
        self.bot.config["fazenda"][uid]["tempo"] = max(10, f["tempo"] // 2)
        self.bot.salvar_config()
        await ctx.send(f"💧 Você regou {f['emoji']} **{f['planta']}**! O tempo caiu pela metade!")

    @commands.command()
    async def colher(self, ctx):
        """Colhe sua planta quando estiver pronta"""
        uid = str(ctx.author.id)
        f = self.bot.config.get("fazenda", {}).get(uid)
        if not f or "planta" not in f: return await ctx.send("❌ Você não tem nada plantado!")
        passado = datetime.now().timestamp() - f["plantado_em"]
        if passado < f["tempo"]:
            return await ctx.send(f"⏳ {f['emoji']} ainda não cresceu! Faltam **{int(f['tempo'] - passado)}s**.")
        
        moedas, xp = f["moedas"], f["xp"]
        self.bot.add_saldo(uid, moedas)
        await self.bot.add_xp_jogo(uid, xp)
        del self.bot.config["fazenda"][uid]
        self.bot.salvar_config()
        await ctx.send(f"🎉 Colheu {f['emoji']} **{f['planta']}**! 💰 +{moedas} moedas | ⭐ +{xp} XP")

    @commands.command()
    async def fazenda(self, ctx):
        """Mostra o status da sua fazendinha"""
        uid = str(ctx.author.id)
        f = self.bot.config.get("fazenda", {}).get(uid)
        if not f or "planta" not in f: return await ctx.send("🌾 Sua fazendinha está vazia! Use `hbl plantar`.")
        passado = datetime.now().timestamp() - f["plantado_em"]
        restante = max(0, int(f["tempo"] - passado))
        status = "✅ Pronto para colher!" if restante == 0 else f"⏳ Faltam {restante}s"
        embed = discord.Embed(title="🌾 Sua Fazendinha", description=f"{f['emoji']} **{f['planta'].capitalize()}**\nStatus: {status}\n💧 Regado: {'Sim' if f.get('regado') else 'Não'}", color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.command()
    async def uno(self, ctx):
        """Abre uma sala para jogar UNO"""
        cid = str(ctx.channel.id)
        if cid in self.bot.uno_jogos and self.bot.uno_jogos[cid].ativo: 
            return await ctx.send("❌ Já tem uma partida de UNO ativa neste canal!")
        
        jogo = UNOJogo()
        jogo.jogadores[str(ctx.author.id)] = {"nome": ctx.author.display_name, "cartas": []}
        self.bot.uno_jogos[cid] = jogo
        
        embed = discord.Embed(
            title="🃏 UNO - Sala de Espera", 
            description=f"Criador: **{ctx.author.display_name}**\n\nClique em **Entrar no Jogo** para participar (2 a 4 jogadores)!", 
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed, view=UNOEntrarView(self.bot, ctx.author.id, ctx.channel.id))

    @commands.command()
    async def mao(self, ctx):
        """Recebe suas cartas do UNO na mensagem privada"""
        cid = str(ctx.channel.id)
        jogo = self.bot.uno_jogos.get(cid)
        if not jogo or not jogo.ativo: return await ctx.send("❌ Nenhum jogo de UNO ativo neste canal!")
        uid = str(ctx.author.id)
        if uid not in jogo.jogadores: return await ctx.send("❌ Você não está na partida!")
        cartas = "\n".join(f"`{i+1}.` {c}" for i, c in enumerate(jogo.jogadores[uid]["cartas"]))
        try:
            await ctx.author.send(embed=discord.Embed(title="🃏 Suas Cartas do UNO", description=f"📋 Carta na Mesa: **{jogo.mesa}**\n\n{cartas}", color=discord.Color.blue()))
            await ctx.send(f"📩 {ctx.author.mention}, enviadas no seu privado!")
        except: 
            await ctx.send("❌ Não consegui enviar no privado! Libere suas DMs.")

    @commands.command()
    async def jogar(self, ctx, carta: str = None):
        """Joga uma carta no UNO pelo número"""
        cid = str(ctx.channel.id)
        jogo = self.bot.uno_jogos.get(cid)
        if not jogo or not jogo.ativo: return await ctx.send("❌ Nenhum jogo de UNO ativo aqui!")
        uid = str(ctx.author.id)
        jogadores = list(jogo.jogadores.keys())
        
        if uid != jogadores[jogo.turno % len(jogadores)]: 
            return await ctx.send("❌ Não é a sua vez!")
        if not carta or not carta.isdigit(): 
            return await ctx.send("❌ Use `hbl jogar <número>` (veja suas cartas com `hbl mao`)")
        
        idx = int(carta) - 1
        mao_j = jogo.jogadores[uid]["cartas"]
        if idx < 0 or idx >= len(mao_j): 
            return await ctx.send("❌ Número de carta inválido!")
        
        c_escolhida = mao_j.pop(idx)
        jogo.mesa = c_escolhida
        
        if len(mao_j) == 0:
            jogo.ativo = False
            self.bot.add_saldo(uid, 100)
            await self.bot.add_xp_jogo(uid, 50)
            del self.bot.uno_jogos[cid]
            return await ctx.send(f"🏆 **{ctx.author.display_name} VENCEU A PARTIDA DE UNO!** 💰 +100 moedas | ⭐ +50 XP")
        
        if len(mao_j) == 1: 
            await ctx.send(f"🚨 **UNO!** {ctx.author.display_name} está com apenas 1 carta!")
        
        jogo.turno += 1
        prox = jogadores[jogo.turno % len(jogadores)]
        await ctx.send(f"✅ {ctx.author.display_name} jogou **{c_escolhida}**!\n📋 Mesa: **{jogo.mesa}**\n🎯 Vez de: **{jogo.jogadores[prox]['nome']}**")

    @commands.command()
    async def trivia(self, ctx):
        """Inicia um Quiz de 5 perguntas sobre Habbo"""
        perguntas = random.sample(TRIVIA_PERGUNTAS, min(5, len(TRIVIA_PERGUNTAS)))
        await ctx.send(f"❓ {ctx.author.mention}, o Trivia Habbo vai começar! São 5 perguntas com 15 segundos cada.")
        await asyncio.sleep(2)
        for i, p in enumerate(perguntas, 1):
            op = "\n".join(f"**{chr(65+j)}.** {o}" for j, o in enumerate(p["op"]))
            embed = discord.Embed(title=f"❓ Trivia ({i}/5)", description=f"{p['p']}\n\n{op}", color=discord.Color.blue())
            await ctx.send(embed=embed, view=TriviaView(self.bot, p, ctx.author.id))
            await asyncio.sleep(16)
        await ctx.send(f"🏁 Trivia finalizado para {ctx.author.mention}!")

    @commands.command()
    async def criajogos(self, ctx, senha: str = None):
        """Cria a categoria e os canais de jogos no servidor"""
        if not self.bot.verificar_autorizacao(ctx, senha): return
        msg = await ctx.send("🎮 Criando estrutura de canais de jogos...")
        try:
            cat = await ctx.guild.create_category("━━━「JOGOS E ECONOMIA」━━━")
        except Exception as e: 
            return await msg.edit(content=f"❌ Erro ao criar categoria: {e}")
        
        canais = [
            ("💰・banco", "hbl daily, hbl saldo, hbl pagar"),
            ("✂️・rps", "hbl rps"),
            ("⚔️・rpg", "hbl rpg"),
            ("🌾・fazendinha", "hbl plantar, hbl regar, hbl colher"),
            ("🃏・uno", "hbl uno, hbl mao, hbl jogar"),
            ("❓・trivia", "hbl trivia"),
            ("🏆・ranking-moedas", "hbl top"),
        ]
        for nome, topico in canais:
            try: 
                await ctx.guild.create_text_channel(name=nome, category=cat, topic=topico)
            except: 
                pass
        await msg.edit(content="✅ Categoria e canais de jogos criados com sucesso!")

async def setup(bot):
    await bot.add_cog(Jogos(bot))
