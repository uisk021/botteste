import discord
from discord.ext import commands, tasks
import os
import json
import asyncio
import threading
import certifi
from dotenv import load_dotenv
from datetime import datetime
from pymongo import MongoClient
from flask import Flask, render_template, jsonify, request

# ==========================================
# CONFIGURAÇÕES GLOBAIS
# ==========================================
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
CONFIG_FILE = "config.json"

SITE_URL = "https://radiohabbler.com.br"
CANAL_NOTICIAS_ID = 1554620684208963645

COGS = [
    "cogs.geral",
    "cogs.musica",
    "cogs.moderacao",
    "cogs.jogos",
    "cogs.economia",
    "cogs.verificacao",
    "cogs.tickets",
    "cogs.interacoes",
    "cogs.site",
    "cogs.decoracao",
]

# Memória compartilhada
spam_tracker = {}
music_queues = {}
player_tasks = {}
ultimo_locutor = None
codigos_pendentes = {}
xp_cooldown = {}
uno_jogos = {}

# ==========================================
# CONEXÃO MONGODB
# ==========================================
mongo_client = None
if not MONGO_URI:
    print("⚠️ MONGO_URI não configurada; funções de banco ficarão indisponíveis.", flush=True)
    db = None
else:
    try:
        ca = certifi.where()
        mongo_client = MongoClient(
            MONGO_URI,
            tlsCAFile=ca,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000
        )
        db = mongo_client["radio_habbler"]
        col_usuarios = db["usuarios"]
        col_status = db["bot_status"]
        col_logs = db["comandos_log"]
        col_site_cmds = db["mensagens_site"]
        # Força a verificação da conexão agora, em vez de apenas criar o cliente.
        mongo_client.admin.command("ping")
        print("🍃 Conectado com sucesso ao MongoDB Atlas!", flush=True)
    except Exception as e:
        print(f"❌ Erro ao conectar no MongoDB: {e}", flush=True)
        db = None

# ==========================================
# CONFIG JSON LOCAL
# ==========================================
def carregar_config():
    defaults = {
        "staff": {}, "palavras_proibidas": [], "links_proibidos": [],
        "log_channel": None, "warns": {}, "radio_favorites": {},
        "ultima_noticia_url": None, "cargo_verificado": None,
        "verificados": {}, "tickets": {}, "xp": {}, "aniversarios": {},
        "economia": {}, "daily_cooldown": {}, "fazenda": {}
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                defaults.update(json.load(f))
        except Exception:
            pass
    return defaults

def salvar_config():
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Erro ao salvar config.json: {e}", flush=True)

config = carregar_config()

# ==========================================
# FUNÇÕES DE BANCO DE DADOS (MONGODB)
# ==========================================
def get_saldo(user_id):
    uid = str(user_id)
    if db is not None:
        doc = col_usuarios.find_one({"user_id": uid})
        if doc and "saldo" in doc:
            return doc["saldo"]
    return config.get("economia", {}).get(uid, 0)

def add_saldo(user_id, valor, user_name=None):
    uid = str(user_id)
    if "economia" not in config: config["economia"] = {}
    config["economia"][uid] = max(0, config["economia"].get(uid, 0) + valor)
    salvar_config()
    
    if db is not None:
        update_data = {
            "$inc": {"saldo": valor},
            "$set": {"ultima_atualizacao": datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
        }
        if user_name:
            update_data["$set"]["user_name"] = user_name
            
        col_usuarios.update_one({"user_id": uid}, update_data, upsert=True)

async def add_xp_jogo(user_id, amount, user_name=None):
    uid = str(user_id)
    if "xp" not in config: config["xp"] = {}
    config["xp"][uid] = config["xp"].get(uid, 0) + amount
    salvar_config()
    
    if db is not None:
        update_data = {
            "$inc": {"xp": amount},
            "$set": {"ultima_atualizacao": datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
        }
        if user_name:
            update_data["$set"]["user_name"] = user_name
            
        col_usuarios.update_one({"user_id": uid}, update_data, upsert=True)

def migrar_dados_iniciais():
    if db is None: return
    try:
        xp_data = config.get("xp", {})
        eco_data = config.get("economia", {})
        verificados = config.get("verificados", {})
        todos = set(list(xp_data.keys()) + list(eco_data.keys()))
        
        for uid in todos:
            nick = verificados.get(uid, f"Habbler #{uid[-4:]}")
            col_usuarios.update_one(
                {"user_id": uid},
                {
                    "$setOnInsert": {
                        "xp": xp_data.get(uid, 0),
                        "saldo": eco_data.get(uid, 0),
                        "user_name": nick,
                        "ultima_atualizacao": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    }
                },
                upsert=True
            )
    except Exception as e:
        print(f"Erro na migração inicial: {e}", flush=True)

# ==========================================
# SERVIDOR FLASK (PORTAL WEB)
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

app_flask = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

@app_flask.route("/")
def index():
    return render_template("index.html")

@app_flask.route("/api/status")
def api_status():
    try:
        if db is not None:
            doc = col_status.find_one({"_id": "status"})
            if doc:
                doc.pop("_id", None)
                return jsonify(doc)
    except Exception as e:
        return jsonify({"online": 0, "erro": str(e)})
    return jsonify({"online": 0})

@app_flask.route("/api/ranking/xp")
def api_ranking_xp():
    try:
        if db is not None:
            docs = list(col_usuarios.find({}, {"_id": 0, "user_name": 1, "xp": 1, "saldo": 1}).sort("xp", -1).limit(20))
            return jsonify(docs)
    except Exception:
        pass
    return jsonify([])

@app_flask.route("/api/ranking/saldo")
def api_ranking_saldo():
    try:
        if db is not None:
            docs = list(col_usuarios.find({}, {"_id": 0, "user_name": 1, "xp": 1, "saldo": 1}).sort("saldo", -1).limit(20))
            return jsonify(docs)
    except Exception:
        pass
    return jsonify([])

@app_flask.route("/api/logs")
def api_logs():
    try:
        if db is not None:
            docs = list(col_logs.find({}, {"_id": 0}).sort("timestamp", -1).limit(15))
            return jsonify(docs)
    except Exception:
        pass
    return jsonify([])

@app_flask.route("/api/comando", methods=["POST"])
def api_comando():
    dados = request.get_json() or {}
    tipo = dados.get("tipo", "anuncio")
    conteudo = dados.get("conteudo", "")

    if not conteudo:
        return jsonify({"sucesso": False, "erro": "Mensagem vazia!"})

    try:
        if db is not None:
            col_site_cmds.insert_one({
                "tipo": tipo,
                "conteudo": conteudo,
                "lido": False,
                "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            })
            return jsonify({"sucesso": True, "mensagem": "Comando enviado para o Patinho! 🐥"})
    except Exception as e:
        return jsonify({"sucesso": False, "erro": str(e)})
    return jsonify({"sucesso": False, "erro": "Banco offline"})

def rodar_servidor():
    porta = int(os.environ.get("PORT", 8080))
    app_flask.run(host="0.0.0.0", port=porta, debug=False, use_reloader=False)

threading.Thread(target=rodar_servidor, daemon=True).start()

# ==========================================
# BOT INIT
# ==========================================
class PatinhoBot(commands.Bot):
    async def setup_hook(self):
        print("📦 Carregando Cogs...", flush=True)
        for cog in COGS:
            try:
                await self.load_extension(cog)
                print(f"  ✅ Cog carregado: {cog}", flush=True)
            except Exception as e:
                print(f"  ⚠️ Erro ao carregar {cog}: {e}", flush=True)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = PatinhoBot(
    command_prefix=["hbl ", "Hbl ", "HBL ", "hbl", "Hbl", "HBL"],
    intents=intents,
    case_insensitive=True
)

bot.music_queues = music_queues
bot.player_tasks = player_tasks
bot.config = config
bot.salvar_config = salvar_config
bot.get_saldo = get_saldo
bot.add_saldo = add_saldo
bot.add_xp_jogo = add_xp_jogo
bot.db = db

# ==========================================
# TAREFAS EM SEGUNDO PLANO
# ==========================================
@tasks.loop(seconds=15)
async def atualizar_status_no_banco():
    if not bot.is_ready() or db is None: return
    try:
        servidores = len(bot.guilds)
        usuarios = sum(g.member_count for g in bot.guilds if g.member_count)
        ping = round(bot.latency * 1000) if bot.latency else 0
        
        col_status.update_one(
            {"_id": "status"},
            {
                "$set": {
                    "online": 1,
                    "servidores": servidores,
                    "usuarios": usuarios,
                    "ultimo_ping": ping,
                    "last_seen": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                },
                "$setOnInsert": {
                    "comandos_total": 0,
                    "comandos_hoje": 0
                }
            },
            upsert=True
        )
    except Exception as e:
        print(f"Erro ao salvar status no Mongo: {e}", flush=True)

@tasks.loop(seconds=5)
async def checar_comandos_do_site():
    if not bot.is_ready() or db is None: return
    try:
        mensagens = list(col_site_cmds.find({"lido": False}))
        for msg in mensagens:
            if msg.get("tipo") == "anuncio":
                canal = bot.get_channel(CANAL_NOTICIAS_ID)
                if canal:
                    embed = discord.Embed(
                        title="📢 Comunicado da Rádio Habbler",
                        description=msg.get("conteudo"),
                        color=discord.Color.gold(),
                        timestamp=datetime.utcnow()
                    )
                    embed.set_footer(text="Enviado via Painel Web")
                    await canal.send(embed=embed)
            
            col_site_cmds.update_one({"_id": msg["_id"]}, {"$set": {"lido": True}})
    except Exception as e:
        print(f"Erro comandos site Mongo: {e}", flush=True)

# ==========================================
# EVENTOS DO BOT
# ==========================================
@bot.event
async def on_ready():
    print(f"✅ Patinho online como {bot.user}", flush=True)
    migrar_dados_iniciais()
    
    if not atualizar_status_no_banco.is_running():
        atualizar_status_no_banco.start()
    if not checar_comandos_do_site.is_running():
        checar_comandos_do_site.start()

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        await bot.process_commands(message)
        return
    
    uid = str(message.author.id)
    agora = asyncio.get_event_loop().time()
    
    if uid not in xp_cooldown or agora - xp_cooldown[uid] > 60:
        xp_cooldown[uid] = agora
        nick = config.get("verificados", {}).get(uid, message.author.display_name)
        await add_xp_jogo(message.author.id, 15, user_name=nick)
        
    cl = message.content.strip().lower()
    if cl in ["hbl", "hbl "]:
        await message.channel.send(f"👋 {message.author.mention} Prefixo: `hbl ` | `hbl ajuda`")
        return
        
    if str(message.author.id) in config["staff"] or message.author == message.guild.owner:
        await bot.process_commands(message)
        return
        
    for p in config["palavras_proibidas"]:
        if p.lower() in cl:
            await message.delete()
            return
            
    if any(x in cl for x in ["http://", "https://", "www.", "discord.gg"]):
        bl = not config["links_proibidos"] or any(k.lower() in cl for k in config["links_proibidos"])
        if bl:
            await message.delete()
            return
            
    if len(message.mentions) >= 5 or "@everyone" in message.content:
        await message.delete()
        return
        
    await bot.process_commands(message)

@bot.event
async def on_command(ctx):
    try:
        if db is not None:
            col_logs.insert_one({
                "comando": ctx.command.name,
                "usuario": str(ctx.author),
                "servidor": str(ctx.guild),
                "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "timestamp": datetime.utcnow()
            })
            col_status.update_one(
                {"_id": "status"},
                {"$inc": {"comandos_total": 1, "comandos_hoje": 1}},
                upsert=True
            )
    except Exception as e:
        print(f"Erro logs Mongo: {e}", flush=True)

@bot.event
async def on_command_error(ctx, error):
    import difflib
    if isinstance(error, commands.CommandNotFound):
        p = ctx.message.content.split()
        t = p[1].lower() if len(p) > 1 else ""
        cmds = [c.name for c in bot.commands]
        for c in bot.commands: cmds.extend(c.aliases)
        s = difflib.get_close_matches(t, cmds, n=1, cutoff=0.3)
        await ctx.send(f"❓ `hbl {t}` não existe!" + (f"\n💡 Quis dizer **`hbl {s[0]}`**?" if s else "\n📋 `hbl ajuda`"))
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"⚠️ Use: `hbl {ctx.command.name} {error.param.name}`")
    else: 
        print(f"Erro comando: {error}", flush=True)

@bot.event
async def on_disconnect():
    try:
        if db is not None:
            col_status.update_one({"_id": "status"}, {"$set": {"online": 0}})
    except Exception:
        pass

# ==========================================
# RUN
# ==========================================
if not TOKEN:
    print("❌ DISCORD_TOKEN não encontrado! Configure-o nas variáveis de ambiente da hospedagem.", flush=True)
else:
    bot.run(TOKEN)
