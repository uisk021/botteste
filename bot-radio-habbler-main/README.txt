PATINHO BOT - PACOTE PARA BOT-HOSTING

ARQUIVOS
- bot.py: aplicação principal (Flask + Discord)
- cogs/musica.py: cog de música/radio atualizado
- templates/ e static/: site
- requirements.txt: dependências Python
- start.sh: instala dependências em /tmp e inicia o bot

CONFIGURAÇÃO NA HOSPEDAGEM
1. Envie e extraia o ZIP na raiz do servidor (/home/container).
2. Configure estas variáveis na aba Ambiente/Environment:
   DISCORD_TOKEN = token do bot (secreto)
   MONGO_URI = URI do MongoDB Atlas (secreta)
3. Defina o comando de inicialização como:
   bash /home/container/start.sh
4. Inicie e confira o console.

O start.sh instala cada inicialização em /tmp/patinho-packages para evitar
permissão de escrita em /home/container/.local. O diretório /tmp pode ser
apagado ao reiniciar, então o script reinstala as dependências a cada start.

IMPORTANTE
- Não inclua token nem URI em arquivos enviados/repositório.
- A senha do MongoDB que apareceu no arquivo compartilhado deve ser trocada;
  depois atualize MONGO_URI nas variáveis da hospedagem.
- O bot.py espera COGS adicionais (geral, moderacao, jogos, economia,
  verificacao, tickets, interacoes, site e decoracao). Esses arquivos não
  estavam entre os anexos recebidos. Sem eles, os respectivos comandos não
  carregam; cogs.musica está incluído.
- A configuração do domínio/porta do site pode depender do suporte do host.
