"use strict";

// ROLE et CONFIGURED sont injectés par FlasK dans terminal.html

// --- Variables Globales (Sync + Carte) ---
let syncVersion = -1;
let knownErrorCount = 0;
let aliceLastState = false;

let distBobMap = 10;
let distEveMap = 20;
let mapInitialized = false;

// Suivi de l'état "simulation terminée" côté serveur
let lastServerVersion = -1;

function init() {

    // Bouton retour > deconnexion
    window.history.pushState(null, "", window.location.href);
    window.addEventListener('popstate', function() {
        window.location.href = "/logout";
    });

    if (ROLE === "alice") {
        initAlice();
    }
    if (ROLE === "bob" || ROLE === "eve") {
        initReceiver();
    }
    syncLoop();
}

// ── GESTION DU POPUP TACTIQUE

function openTacticalModal() {
    const overlay = document.getElementById("tactical-modal-overlay");
    if (overlay) {
        overlay.style.display = "flex";
        // On attend 50ms pour laisser au navigateur le temps d'afficher la fenêtre
        // avant de calculer les positions de la carte
        setTimeout(() => {
            initMap();
        }, 50);
    }
}

function closeTacticalModal() {
    const overlay = document.getElementById("tactical-modal-overlay");
    if (overlay) overlay.style.display = "none";
}

function validateTacticalModal() {
    setLocked(true); // Déclenche l'avertissement "CANAL NON INITIALISÉ"
    closeTacticalModal(); // Ferme le popup
}

function setLocked(locked) {
    const banner = document.getElementById("locked-banner");
    const txForm = document.getElementById("tx-form");
    const statusMsg = document.getElementById("cfg-status");

    if (banner) banner.style.display = locked ? "" : "none";
    if (txForm) txForm.style.display = locked ? "none" : "";

    if (locked) {
        resetImageInput();
        if (statusMsg) {
            statusMsg.textContent = ""; // Efface
            statusMsg.className = "status-msg"; // Retire les couleurs de succès
        }
    }
}
// ════════════════════════════════════════════════════════════
// BOUCLE DE SYNCHRONISATION (une seule définition)
// ════════════════════════════════════════════════════════════
async function syncLoop() {
    while (true) {
        try {
            const res = await fetch(`/api/sync?version=${syncVersion}`);
            if (!res.ok) {
                await sleep(5000);
                continue;
            }

            const data = await res.json();

            if (data.version !== syncVersion) {
                syncVersion = data.version;

                // Bob/Eve : rafraîchir dès que la version change ET qu'une simulation vient de se terminer
                // On détecte : alice était ready, maintenant elle ne l'est plus → simulation achevée
                const aliceReady = data.alice?.ready ?? false;
                if (aliceLastState === true && aliceReady === false) {
                    if (ROLE === "bob" || ROLE === "eve") {

                            // Alice vient de terminer → récupérer le résultat
                            fetchRX();
                        }
                    if (ROLE === "alice") {
                        const btnStats = document.getElementById("btn-stats");
                        if (btnStats) btnStats.style.display = "block"; // Apparaît à la fin !
                    }
                }

                aliceLastState = aliceReady;
                // Erreurs
                const count = data.errors?.count ?? 0;
                if (count !== knownErrorCount) {
                    knownErrorCount = count;
                    if (count > 0) {
                        renderErrorPopup(data.errors.list);
                        openErrorPopup();
                    } else {
                        closeErrorPopup();
                    }
                }
            }

        } catch (e) {
            // réseau coupé, on attend
            await sleep(1500);
        }
    }
}


// ════════════════════════════════════════════════════════════
// ALICE : CARTE TACTIQUE
// ════════════════════════════════════════════════════════════

// Calcul physique — identique à distance_to_params() dans app.py
// p(d) = 0.5 * (d / D_MAX)²   →  p=0 à d=0, p=0.5 à d=D_MAX  (loi en 1/d²)
// SNR(d) = 20 - 20*log10(d)   →  décroissance 20 dB/décade
const D_MAX_GLOBAL = 100.0;

function calcParamsFromDist(dist_m) {
    const d   = Math.min(Math.max(dist_m, 0.1), D_MAX_GLOBAL);
    const p   = 0.5 * Math.pow(d / D_MAX_GLOBAL, 2);
    const snr = 20.0 - 20.0 * Math.log10(d);
    return {
        snr: parseFloat(snr.toFixed(1)),
        p:   parseFloat(p.toFixed(4))
    };
}

function initMap() {
    if (mapInitialized) return;

    const map = document.getElementById('tactical-map');
    if (!map) return;

    const nodes = {
        alice: document.getElementById('node-alice'),
        bob: document.getElementById('node-bob'),
        eve: document.getElementById('node-eve')
    };
    const lines = {
        ab: document.getElementById('line-ab'),
        ae: document.getElementById('line-ae')
    };
    let activeNode = null;

    const D_MAX_CARTE = 100.0;

    function getPos(node) {
        return {
            x: node.offsetLeft,
            y: node.offsetTop
        };
    }

    function drawLine(line, p1, p2) {
        if (!line) return;
        const dx = p2.x - p1.x;
        const dy = p2.y - p1.y;
        const len = Math.hypot(dx, dy);
        const angle = Math.atan2(dy, dx) * 180 / Math.PI;
        line.style.width = len + 'px';
        line.style.left = p1.x + 'px';
        line.style.top = p1.y + 'px';
        line.style.transform = `rotate(${angle}deg)`;
    }

    function updateVisuals() {
        const pA = getPos(nodes.alice);
        const pB = getPos(nodes.bob);
        const pE = getPos(nodes.eve);

        const distAB_px = Math.hypot(pB.x - pA.x, pB.y - pA.y);
        const distAE_px = Math.hypot(pE.x - pA.x, pE.y - pA.y);

        const zoneAlice = document.getElementById('zone-alice');
        if (zoneAlice) {
            zoneAlice.style.width = (distAB_px * 2) + 'px';
            zoneAlice.style.height = (distAB_px * 2) + 'px';
            zoneAlice.style.left = pA.x + 'px';
            zoneAlice.style.top = pA.y + 'px';
        }

        const diag = Math.hypot(map.offsetWidth || 800, map.offsetHeight || 400);
        distBobMap = (distAB_px / diag) * D_MAX_CARTE;
        distEveMap = (distAE_px / diag) * D_MAX_CARTE;

        const dispAB = document.getElementById('display-ab');
        const dispAE = document.getElementById('display-ae');
        if (dispAB) dispAB.textContent = distBobMap.toFixed(0);
        if (dispAE) dispAE.textContent = distEveMap.toFixed(0);

        const resB = calcParamsFromDist(distBobMap);
        const resE = calcParamsFromDist(distEveMap);

        const fieldSNRBob = document.getElementById('input-snr-bob');
        const fieldSNREve = document.getElementById('input-snr-eve');
        const fieldPBob   = document.getElementById('input-p-bob');
        const fieldPEve   = document.getElementById('input-p-eve');

        if (fieldSNRBob) fieldSNRBob.value = resB.snr;
        if (fieldSNREve) fieldSNREve.value = resE.snr;
        if (fieldPBob)   fieldPBob.value   = resB.p;
        if (fieldPEve)   fieldPEve.value   = resE.p;

        drawLine(lines.ab, pA, pB);
        drawLine(lines.ae, pA, pE);
    }

// Petite fonction magique pour récupérer la position (Doigt ou Souris)
    function getEventPos(e) {
        if (e.type.includes('touch')) {
            return {
                clientX: e.touches[0].clientX || e.changedTouches[0].clientX,
                clientY: e.touches[0].clientY || e.changedTouches[0].clientY
            };
        }
        return { clientX: e.clientX, clientY: e.clientY };
    }

    // 1. Initialisation du drag (Souris + Tactile)
    Object.values(nodes).forEach(node => {
        if (node) {
            node.addEventListener('mousedown', (e) => {
                activeNode = node;
                e.preventDefault();
            });
            node.addEventListener('touchstart', (e) => {
                activeNode = node;
                e.preventDefault(); // Empêche le scroll quand on attrape le nœud
            }, { passive: false });
        }
    });

    // 2. Logique de déplacement unifiée
    function handleMove(e) {
        if (!activeNode) return;
        
        // Empêche l'écran du téléphone de défiler quand on glisse le nœud
        if (e.type === 'touchmove') e.preventDefault(); 

        const pos = getEventPos(e);
        const rect = map.getBoundingClientRect();
        
        let x = pos.clientX - rect.left;
        let y = pos.clientY - rect.top;

        x = Math.max(20, Math.min(x, rect.width - 20));
        y = Math.max(20, Math.min(y, rect.height - 20));

        // ── Logique de collision (Eve reste hors du cercle) ──
        const pA = activeNode === nodes.alice ? {x, y} : getPos(nodes.alice);
        const pB = activeNode === nodes.bob   ? {x, y} : getPos(nodes.bob);
        const pE = activeNode === nodes.eve   ? {x, y} : getPos(nodes.eve);

        const distAB = Math.hypot(pB.x - pA.x, pB.y - pA.y);
        const distAE = Math.hypot(pE.x - pA.x, pE.y - pA.y);

        if (distAE < distAB) {
            if (activeNode === nodes.eve) {
                const angle = Math.atan2(pE.y - pA.y, pE.x - pA.x);
                x = pA.x + Math.cos(angle) * distAB;
                y = pA.y + Math.sin(angle) * distAB;
            } else if (activeNode === nodes.bob) {
                const angle = Math.atan2(pB.y - pA.y, pB.x - pA.x);
                x = pA.x + Math.cos(angle) * distAE;
                y = pA.y + Math.sin(angle) * distAE;
            } else if (activeNode === nodes.alice) {
                const angle = Math.atan2(pE.y - pA.y, pE.x - pA.x);
                let eveX = pA.x + Math.cos(angle) * distAB;
                let eveY = pA.y + Math.sin(angle) * distAB;
                
                eveX = Math.max(20, Math.min(eveX, rect.width - 20));
                eveY = Math.max(20, Math.min(eveY, rect.height - 20));
                
                nodes.eve.style.left = eveX + 'px';
                nodes.eve.style.top  = eveY + 'px';
            }
            x = Math.max(20, Math.min(x, rect.width - 20));
            y = Math.max(20, Math.min(y, rect.height - 20));
        }

        activeNode.style.left = x + 'px';
        activeNode.style.top  = y + 'px';

        updateVisuals();
    }

    // 3. Écoute du déplacement (Souris + Tactile)
    document.addEventListener('mousemove', handleMove);
    document.addEventListener('touchmove', handleMove, { passive: false });

    // 4. Arrêt du déplacement (Souris + Tactile)
    document.addEventListener('mouseup', () => { activeNode = null; });
    document.addEventListener('touchend', () => { activeNode = null; });
    document.addEventListener('touchcancel', () => { activeNode = null; });

    updateVisuals();
    mapInitialized = true;
}

// ════════════════════════════════════════════════════════════
// ALICE : CONTRÔLES ET CONFIGURATION
// ════════════════════════════════════════════════════════════

function initAlice() {
    updateStatusBadge();
    toggleCanalFields();
    toggleLiaisonMode();

    document.getElementById('conn-toggle')?.addEventListener('change', () => {
        setLocked(true);
        updateStatusBadge();
        toggleLiaisonMode();
    });

    document.querySelectorAll('input[name="conn"], input[name="canal"], [name="N"], [name="K"]')
        .forEach(el => el.addEventListener("change", () => {
            setLocked(true);
            updateStatusBadge();
            toggleCanalFields();
        }));
}

function updateStatusBadge() {
    const toggle = document.getElementById('conn-toggle');
    if (!toggle) return;
    const offline = toggle.checked; // true si coché (HORS LIGNE)
    const badge = document.getElementById("status-badge");
    if (!badge) return;
    badge.textContent = "● " + (offline ? "SIMULATION" : "EN LIGNE");
    badge.className   = "status-badge " + (offline ? "status-offline" : "status-online");
}

function toggleCanalFields() {
    const toggle = document.getElementById('canal-toggle');
    if (!toggle) return;
    
    const isBSC = toggle.checked; // true si BSC, false si AWGN

    // Mise à jour visuelle des labels du Switch
    const lblAWGN = document.getElementById('lbl-awgn');
    const lblBSC = document.getElementById('lbl-bsc');
    if (isBSC) {
        if(lblAWGN) lblAWGN.classList.remove('active-online'); 
        if(lblBSC) lblBSC.classList.add('active-offline'); 
    } else {
        if(lblAWGN) lblAWGN.classList.add('active-online');
        if(lblBSC) lblBSC.classList.remove('active-offline');
    }

    // Affichage des blocs
    const awgnB = document.getElementById("awgn-fields-bob");
    const awgnE = document.getElementById("awgn-fields-eve");
    const bscB  = document.getElementById("bsc-fields-bob");
    const bscE  = document.getElementById("bsc-fields-eve");

    if (awgnB) awgnB.style.display = isBSC ? "none" : "flex";
    if (awgnE) awgnE.style.display = isBSC ? "none" : "flex";
    if (bscB)  bscB.style.display  = isBSC ? "flex" : "none";
    if (bscE)  bscE.style.display  = isBSC ? "flex" : "none";

    // Si le radar est affiché, forcer une redessin pour mettre à jour les couleurs (vert/cyan)
    if (typeof drawConcentricCircles === "function" && mapInitialized) {
        drawConcentricCircles();
    }
}

function toggleLiaisonMode() {
    const toggle = document.getElementById('conn-toggle');
    if (!toggle) return;
    
    const offline = toggle.checked;
    
    // Gérer l'affichage du bouton de déploiement
    const configContainer = document.getElementById('btn-config-container');
    if (configContainer) {
        configContainer.style.display = offline ? "block" : "none";
    }

    // Mettre à jour le style
    const lblOnline = document.getElementById('lbl-online');
    const lblOffline = document.getElementById('lbl-offline');
    if (offline) {
        lblOnline.classList.remove('active-online');
        lblOffline.classList.add('active-offline');
    } else {
        lblOnline.classList.add('active-online');
        lblOffline.classList.remove('active-offline');
    }
}

let selectedImageFilename = null;

function resetImageInput() {
    selectedImageFilename = null;
    const label = document.getElementById("upload-label");
    if (label) label.textContent = "📂 Cliquer pour choisir une image";
    const hint = document.getElementById("upload-hint");
    if (hint) hint.textContent = "";
}

function openGalleryModal() {
    const overlay = document.getElementById("gallery-modal-overlay");
    if (overlay) overlay.style.display = "flex";
}

function closeGalleryModal() {
    const overlay = document.getElementById("gallery-modal-overlay");
    if (overlay) overlay.style.display = "none";
}

function selectImage(filename) {
    selectedImageFilename = filename;
    
    const label = document.getElementById("upload-label");
    if (label) label.textContent = "📎 " + filename;
    
    const hint = document.getElementById("upload-hint");
    if (hint) hint.textContent = "Image prête pour la transmission.";

    closeGalleryModal();
}

function onImageSelected(input) {
    const hint  = document.getElementById("upload-hint");
    const label = document.getElementById("upload-label");
    if (input.files[0]) {
        label.textContent = "📎 " + input.files[0].name;
        if (hint) hint.textContent = "Image prête à être envoyée.";
    }
}

async function configure() {
    const checked = name => document.querySelector(`input[name="${name}"]:checked`)?.value;
    const val     = name => document.querySelector(`[name="${name}"]`)?.value;
    const status  = document.getElementById("cfg-status");

    setStatus(status, "Enregistrement...", "pending");

    const fd = new FormData();
    const isOffline = document.getElementById('conn-toggle').checked; // Lecture du toggle
    const isBSC = document.getElementById('canal-toggle')?.checked;
    
    fd.append("mode",       "WIRETAP");
    fd.append("conn_mode",  isOffline ? "HORS LIGNE" : "EN LIGNE");
    fd.append("N",          val("N"));
    fd.append("K",          val("K"));
    fd.append("type_canal", isBSC ? "BSC" : "AWGN");

    // Distances calculées depuis la carte — pas de saisie manuelle
    fd.append("dist_ab", distBobMap);
    fd.append("dist_ae", distEveMap);

    const res  = await fetch("/configure", { method: "POST", body: fd });
    const data = await res.json();

    if (data.ok) {
        setStatus(status, "✓ Configuration appliquée", "ok");
        setLocked(false);
        updateStatusBadge();
        closeTacticalModal();
    } else {
        setStatus(status, "✗ " + data.error, "error");
    }
}

async function sendMessage() {
    const message  = document.getElementById("msg-input")?.value || "";
    //const imgFile  = document.getElementById("img-file")?.files[0];
    const status   = document.getElementById("send-status");
    const errorBox = document.getElementById("send-error");

    if (!message.trim() && !selectedImageFilename) {
        setStatus(status, "✗ Message vide.", "error");
        return;
    }

    if (errorBox) errorBox.style.display = "none";
    setStatus(status, "Transmission en cours...", "pending");
    document.getElementById("btn-send").disabled = true;

    const fd = new FormData();
    fd.append("message", message);
    if (selectedImageFilename) {
        fd.append("image_filename", selectedImageFilename);
    }
    const res  = await fetch("/send", { method: "POST", body: fd });
    const data = await res.json();
    document.getElementById("btn-send").disabled = false;

    if (data.ok) {
        setStatus(status, "✓ Transmis — type : " + data.type, "ok");
        document.getElementById("msg-input").value = "";
        resetImageInput();
    } else {
        setStatus(status, "✗ Échec.", "error");
        if (errorBox) {
            errorBox.textContent   = data.error;
            errorBox.style.display = "";
        }
    }
}


// ════════════════════════════════════════════════════════════
// BOB / EVE
// ════════════════════════════════════════════════════════════

function initReceiver() {
    // Chargement initial du dernier résultat disponible
    fetchRX();
}

async function fetchRX() {
    const target = ROLE === "bob" ? "bob" : "eve";
    try {
        const res  = await fetch("/rx?target=" + target);
        const data = await res.json();
        renderRX(data);
    } catch (e) {
        // Réseau coupé, on ignore
    }
}

function renderRX(data) {
    setBadge("● EN ATTENTE", "status-wait");

    if (!data || !data.ready) return;

    flashNewMessage();

    const isEve   = ROLE === "eve";
    const metaEl  = document.getElementById("rx-meta");
    const content = document.getElementById("rx-content");

    if (metaEl) {
        metaEl.style.display = "";
        metaEl.innerHTML = `
            <span class="type-badge ${isEve ? 'type-badge-eve' : ''}">${data.type}</span>
            <span class="rx-time">Reçu à ${data.time}</span>
        `;
    }

    if (!isEve && data.error_count > 0) {
        const alert = document.getElementById("bob-alert");
        if (alert) {
            alert.style.display = "";
            alert.textContent   = "⚠ ALERTE INTÉGRITÉ — " + data.error_count + " erreur(s) détectée(s).";
        }
    }

    const cardClass = "terminal-card" + (isEve ? " terminal-card-eve" : "");

    if (data.image) {
        if (content) {
            content.className = "";
            // On force une largeur plus grande (ex: 256px ou 100%) et on garde les pixels nets
            content.innerHTML = `<img src="data:image/png;base64,${data.content}"
                style="width: 100%; max-width: 300px; height: auto; image-rendering: auto; border-radius: 8px; border: 1px solid var(--color-border);" 
                alt="Signal reçu">`;
        }  
    } else if (data.image_error) {
        if (content) {
            content.className   = cardClass;
            content.textContent = "FLUX IMAGE CORROMPU — canal trop dégradé.";
        }
    } else {
        if (content) {
            content.className   = cardClass;
            content.textContent = data.content || "—";
        }
    }
}


// ════════════════════════════════════════════════════════════
// UTILITAIRES ET ERREURS
// ════════════════════════════════════════════════════════════

/**
 * Empêche les valeurs aberrantes en forçant un minimum et un maximum.
 * Appelée via onchange .
 */
function clampValue(inputEl, min, max) {
    let val = parseFloat(inputEl.value);
    
    // Si ce n'est pas un nombre, ou si c'est inférieur au min
    if (isNaN(val) || val <= min) {
        val = min;
    } 
    // Si c'est supérieur au max
    else if (val > max) {
        val = max;
    }

    inputEl.value = val; // Force la valeur dans le champ
    
    // Déclenche manuellement la mise à jour du radar avec la valeur corrigée
    inputEl.dispatchEvent(new Event('input'));
}

function setStatus(el, msg, type) {
    if (!el) return;
    el.textContent = msg;
    el.className   = "status-msg" + (type ? " status-" + type : "");
}

function flashNewMessage() {
    setBadge("● NOUVEAU MESSAGE", "status-online");
    setTimeout(() => {
        setBadge("● EN ATTENTE", "status-wait");
    }, 3000);
}

function setBadge(text, className) {
    const badge = document.getElementById("status-badge");
    if (badge) {
        badge.textContent = text;
        badge.className   = "status-badge " + className;
    }
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function openStatsModal() {
    const overlay = document.getElementById("stats-modal-overlay");
    if (overlay) overlay.style.display = "flex";
    fetchSecurityStats();
}

function closeStatsModal() {
    const overlay = document.getElementById("stats-modal-overlay");
    if (overlay) overlay.style.display = "none";
}

async function fetchSecurityStats() {
    const body = document.getElementById("stats-body");
    try {
        const res = await fetch("/api/security-stats");
        const data = await res.json();
        
        if (data.error) {
            body.innerHTML = `<div style="color: #ff4444;">ERREUR : ${data.error}</div>`;
            return;
        }

        // On récupère les deux sous-objets
        const th = data.theorique;
        const em = data.empirique;

        // Logique de validation pour Cs (Capacité Secrète)
        let msgCs = "";
        if (th.Cs_capacite > 0) {
            msgCs = `<span style="color: var(--color-online);">✓ Transmission sécurisée possible</span>`;
        } else {
            msgCs = `<span style="color: #ff4444;">✗ Aucune capacité secrète !</span>`;
        }

        // Logique de validation pour l'Avantage de Bob
        let msgAvantage = "";
        if (em.avantage_bob > 0.05) {
            msgAvantage = `<span style="color: var(--color-online);">✓ Bob est significativement avantagé</span>`;
        } else if (em.avantage_bob > 0) {
            msgAvantage = `<span style="color: #ffaa00;">~ Avantage faible</span>`;
        } else {
            msgAvantage = `<span style="color: #ff4444;">✗ Aucun avantage détecté (Eve aussi bien informée que Bob)</span>`;
        }

        let html = `
<div style="white-space: pre; color: #8c9baf; line-height: 1.5; font-size: 18px; overflow-x: auto;">
============================================================
  <span style="color: var(--color-alice); font-weight: bold; font-size: 1.2em;">BILAN DE SÉCURITÉ — Canal BSC</span>
============================================================
  p_bob = <span style="color: #fff;">${th.p_bob}</span>   |   p_eve = <span style="color: #fff;">${th.p_eve}</span>

  <span style="color: var(--color-alice);">── Capacités théoriques ──────────────────────────</span>
  C_Bob          = <span style="color: #fff;">${th.C_bob.toFixed(4)}</span> bit/usage
  C_eve          = <span style="color: #fff;">${th.C_eve.toFixed(4)}</span> bit/usage
  Cs (secrète)   = <span style="color: #fff;">${th.Cs_capacite.toFixed(4)}</span> bit/usage   ${msgCs}

  <span style="color: var(--color-alice);">── Résultats empiriques ──────────────────────────</span>
  TEB Bob         = <span style="color: #fff;">${em.teb_bob_pct.toFixed(3)}</span> %
  TEB Eve         = <span style="color: #fff;">${em.teb_eve_pct.toFixed(3)}</span> %

  I(Source ; Bob) = <span style="color: #fff;">${em.mi_source_bob.toFixed(4)}</span> bit
  I(Source ; Eve) = <span style="color: #fff;">${em.mi_source_eve.toFixed(4)}</span> bit
  I(Bob ; Eve)    = <span style="color: #fff;">${em.mi_bob_eve.toFixed(4)}</span> bit  <span style="color: #666;">← corrélation entre récepteurs</span>

  Avantage Bob    = <span style="color: #fff;">${em.avantage_bob.toFixed(4)}</span> bit   ${msgAvantage}
</div>`;

        body.innerHTML = html;
        
    } catch (e) {
        body.innerHTML = `<div style="color: #ff4444;">ÉCHEC DE LA LECTURE DES STATISTIQUES</div>`;
    }
}
// ── Erreurs

function renderErrorPopup(erreurs) {
    const body = document.getElementById("error-popup-body");
    if (!body) return;
    body.innerHTML = "";

    erreurs.forEach(prog => {
        const block = document.createElement("div");
        block.className = "error-entry";

        const title = document.createElement("div");
        title.className   = "error-entry-prog";
        title.textContent = prog.nom_programme;
        block.appendChild(title);

        prog.erreurs.forEach(e => {
            const msg = document.createElement("div");
            msg.className   = "error-entry-msg";
            msg.textContent = e.message;
            block.appendChild(msg);
        });

        body.appendChild(block);
    });
}

function openErrorPopup() {
    const overlay = document.getElementById("error-overlay");
    if (overlay) overlay.style.display = "flex";
}

function closeErrorPopup() {
    const overlay = document.getElementById("error-overlay");
    if (overlay) overlay.style.display = "none";
}

async function clearErrors() {
    await fetch("/errors/clear", { method: "POST" });
    knownErrorCount = 0;
    closeErrorPopup();
}

const errorOverlay = document.getElementById("error-overlay");
if (errorOverlay) {
    errorOverlay.addEventListener("click", e => {
        if (e.target === e.currentTarget) closeErrorPopup();
    });
}

// ── Synchronisation Roles (Page Login)

async function loginSyncLoop() {
    while (true) {
        try {
            const res = await fetch(`/api/roles?version=${syncVersion}`);
            if (!res.ok) {
                await sleep(5000);
                continue;
            }
            const data = await res.json();

            if (data.version !== syncVersion) {
                syncVersion = data.version;

                for (const role of ["alice", "bob", "eve"]) {
                    const btn = document.querySelector(`.role-${role}`);
                    if (!btn) continue;

                    const online = data[role] ?? false;
                    btn.disabled = online;
                    const descEl = btn.querySelector(".role-desc");
                    if (descEl) {
                        descEl.textContent = online ? "Connecté(e)" : btn.dataset.desc;
                    }
                }
            }
        } 

        catch (e) {
            await sleep(1500);
        }
    }
}