// ============================================
// 🐤 PATINHO — RÁDIO HABBLER
// ============================================

// ========== 📻 PLAYER ORBITAL ==========
const audio = document.getElementById("radio-audio");
const btnPlay = document.getElementById("btn-play");
const iconPlay = document.getElementById("icon-play");
const iconPause = document.getElementById("icon-pause");
const radioStatus = document.getElementById("radio-status");
const orbitalRings = document.getElementById("orbital-rings");

function toggleRadio() {
    if (audio.paused) {
        audio.play().then(function () {
            iconPlay.style.display = "none";
            iconPause.style.display = "block";
            btnPlay.classList.add("tocando");
            orbitalRings.classList.add("ativo");
            radioStatus.textContent = "Ao vivo";
        }).catch(function () {
            radioStatus.textContent = "Erro ao conectar";
        });
    } else {
        audio.pause();
        iconPlay.style.display = "block";
        iconPause.style.display = "none";
        btnPlay.classList.remove("tocando");
        orbitalRings.classList.remove("ativo");
        radioStatus.textContent = "Pausado";
    }
}

function mudarVolume(valor) {
    audio.volume = valor / 100;
}

audio.volume = 0.7;


// ========== 📊 STATUS DO BOT ==========
async function atualizarStatus() {
    try {
        const resp = await fetch("/api/status");
        const d = await resp.json();

        const badge = document.getElementById("status-badge");
        if (d.online) {
            badge.className = "status-badge online";
            badge.innerHTML = '<span class="dot"></span><span class="badge-text">Online</span>';
        } else {
            badge.className = "status-badge offline";
            badge.innerHTML = '<span class="dot"></span><span class="badge-text">Offline</span>';
        }

        document.getElementById("stat-online").textContent = d.online ? "Online" : "Offline";
        document.getElementById("stat-servidores").textContent = (d.servidores || 0).toLocaleString("pt-BR");
        document.getElementById("stat-usuarios").textContent = (d.usuarios || 0).toLocaleString("pt-BR");
        document.getElementById("stat-comandos").textContent = (d.comandos_total || 0).toLocaleString("pt-BR");
        document.getElementById("stat-ping").textContent = (d.ultimo_ping || 0) + "ms";
        document.getElementById("last-seen").textContent = "Última atualização: " + (d.last_seen || "--");
    } catch (e) {
        console.error("Erro status:", e);
    }
}
setInterval(atualizarStatus, 5000);
atualizarStatus();


// ========== 🏆 RANKING ==========
let rankingAtual = "xp";

async function carregarRanking(tipo) {
    rankingAtual = tipo;
    const tbody = document.getElementById("ranking-body");
    const colValor = document.getElementById("col-valor");

    try {
        const resp = await fetch("/api/ranking/" + tipo);
        const dados = await resp.json();

        if (!dados || dados.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" class="loading">Nenhum dado ainda 🐤</td></tr>';
            return;
        }

        colValor.textContent = tipo === "xp" ? "XP" : "Moedas";
        let html = "";

        dados.forEach(function (user, i) {
            const pos = i + 1;
            let medalha = pos;
            let cls = "";
            if (pos === 1) { medalha = "🥇"; cls = "medalha-1"; }
            else if (pos === 2) { medalha = "🥈"; cls = "medalha-2"; }
            else if (pos === 3) { medalha = "🥉"; cls = "medalha-3"; }

            const valor = tipo === "xp" ? user.xp : user.saldo;
            const avatarUrl = "https://imaging.habblet.city/avatarimage?user=" +
                encodeURIComponent(user.user_name) + "&head_direction=3&headonly=1&size=s";

            html += '<tr>' +
                '<td class="' + cls + '">' + medalha + '</td>' +
                '<td style="display:flex;align-items:center;gap:10px;">' +
                    '<img src="' + avatarUrl + '" onerror="this.style.display=\'none\'" ' +
                         'style="width:28px;height:28px;border-radius:50%;background:rgba(139,92,246,0.1);">' +
                    '<span>' + user.user_name + '</span>' +
                '</td>' +
                '<td>' + (valor || 0).toLocaleString("pt-BR") + '</td>' +
            '</tr>';
        });

        tbody.innerHTML = html;
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="3" class="loading">Erro ao carregar 😢</td></tr>';
    }
}

function mostrarRanking(event, tipo) {
    document.querySelectorAll(".tab-btn").forEach(function (b) {
        b.classList.remove("ativo");
    });
    if (event && event.currentTarget) {
        event.currentTarget.classList.add("ativo");
    }
    carregarRanking(tipo);
}

carregarRanking("xp");
setInterval(function () { carregarRanking(rankingAtual); }, 30000);


// ========== ✨ ANIMAÇÕES AO SCROLL ==========
const observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
        if (entry.isIntersecting) {
            entry.target.classList.add("visible");
        }
    });
}, { threshold: 0.1 });

document.querySelectorAll(".fade-in").forEach(function (el) {
    observer.observe(el);
});


// ========== 📱 MENU MOBILE ==========
function toggleMenu() {
    const links = document.querySelector(".nav-links");
    if (links.style.display === "flex") {
        links.style.display = "none";
    } else {
        links.style.display = "flex";
        links.style.flexDirection = "column";
        links.style.position = "absolute";
        links.style.top = "70px";
        links.style.left = "0";
        links.style.right = "0";
        links.style.background = "rgba(5,5,8,0.95)";
        links.style.padding = "20px 30px";
        links.style.gap = "16px";
        links.style.borderBottom = "1px solid rgba(139,92,246,0.12)";
    }
}
