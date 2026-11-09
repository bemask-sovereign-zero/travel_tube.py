import json
import hashlib
import base64
import re
import urllib.request
from datetime import datetime
import streamlit as st
import pandas as pd

# ==============================================================================
# BEMASK // ALPHA TRAVEL TUBE (SECTOR 12 STANDALONE POD — CASH & POS SHIELD)
# ==============================================================================

st.set_page_config(
    page_title="ALPHA TRAVEL TUBE // Cassa & POS Shield",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- ICONA VETTORIALE DEL TRAVEL TUBE DI SPAZIO 1999 ---
TRAVEL_TUBE_SVG = """
<svg width="96" height="58" viewBox="0 0 140 80" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="70" cy="40" r="36" fill="#0B131E" stroke="#38BDF8" stroke-width="2.5" stroke-dasharray="6 3"/>
  <rect x="14" y="24" width="112" height="32" rx="16" fill="#1E293B" stroke="#F59E0B" stroke-width="3"/>
  <rect x="30" y="30" width="22" height="14" rx="3" fill="#090D16" stroke="#38BDF8" stroke-width="1.8"/>
  <rect x="59" y="30" width="22" height="14" rx="3" fill="#090D16" stroke="#38BDF8" stroke-width="1.8"/>
  <rect x="88" y="30" width="22" height="14" rx="3" fill="#090D16" stroke="#38BDF8" stroke-width="1.8"/>
  <line x1="18" y1="49" x2="122" y2="49" stroke="#F59E0B" stroke-width="3"/>
  <circle cx="22" cy="40" r="4" fill="#10B981"/>
  <circle cx="118" cy="40" r="4" fill="#EF4444"/>
</svg>
"""

# --- DIZIONARIO SEMANTICO AUTOMATICO (TRADUTTORE CODICI BOLLE & SCONTRINI -> A-O) ---
DEFAULT_SEMANTIC_RULES = {
    "[A] CAFFETTERIA & MISCELE": ["CAFF", "MISCELA", "GRANI", "ARABICA", "ROBUSTA", "DECA", "ORZO", "GINSENG", "10001", "ILLY", "LAVAZZA", "KIMBO"],
    "[B] BEVANDE & ALCOLICI": ["APEROL", "CAMPARI", "BITTER", "GIN", "VODKA", "RUM", "WHISKY", "PROSECCO", "VINO", "BIRRA", "COCA", "FANTA", "ACQUA", "SUCCHI", "RED BULL", "AA514", "DORECA", "CL.100", "CL.70", "LT.1"],
    "[C] LATTE, FRESCHI & LIEVITATI": ["LATTE", "PANNA", "BURRO", "BRIOCHE", "CORNETT", "PASTE", "SFOGLIA", "YOGURT", "UOVA", "GRANAROLO", "MUKKI"],
    "[D] SNACK, CUCINA & SALATO": ["PANE", "TRAMEZZIN", "PROSCIUTTO", "MOZZARELLA", "FORMAGGIO", "PATATIN", "NOCCIOLIN", "OLIVE", "FOCACCIA", "PIZZA", "PECHINO", " RISO", "INVOLTIN"],
    "[E] GHIACCIO & CONSUMABILI": ["GHIACCIO", "TOVAGLIOL", "BICCHIER", "CANNUCC", "ZUCCHERO", "BUSTIN", "PALETTIN", "CARTA TERMICA", "ROTOL"],
    "[F] PULIZIA & DETERSIVI": ["DETERSIV", "SAPONE", "CANDEGGINA", "SGRASSATOR", "SPUGN", "SACCHI", "IGIENE", "BRILLANTANTE"],
    "[G] MANUTENZIONE & RICAMBI": ["IDRAULIC", "ELETTRIC", "GUARNIZION", "FILTRO", "ADDOLCITOR", "TECNICO", "RIPARAZION"],
    "[H] STAFF & COLLABORATORI": ["ACCONTO", "EXTRA", "CAMERIER", "BARISTA", "TURNO", "BUSTA", "RIMBORSO"],
    "[I] UTENZE & BOLLETTE": ["ENEL", "LUCE", "GAS", "ACQUEDOTTO", "FIBRA", "TIM", "VODAFONE", "TARI", "SIAE"],
    "[L] TASSE, BOLLI & DIRITTI": ["F24", "BOLLO", "AGENZIA", "CAMERA COMMERCIO", "INPS", "INAIL", "SUOLO PUBBLICO"],
    "[M] FORNITORI OCCASIONALI": ["SUPERMERCATO", "CONAD", "COOP", "EUROSPIN", "LIDL", "METRO", "CASH"],
    "[N] SPESE VARIE & PICCOLA CASSA": ["FARMACIA", " CANCELLERIA", "FRANCOBOLL", "MANCIA", "RESTO", "VARIE"],
    "[O] PRELIEVO TITOLARE / VERSAMENTO": ["TITOLARE", "PRELIEVO", "VERSAMENTO BANCA", "SOCIO", "ALLEGGERIMENTO"]
}

def classify_item_semantically(text_input, rules_dict):
    up_txt = str(text_input).upper()
    for conto_key, keywords in rules_dict.items():
        for kw in keywords:
            if kw.upper() in up_txt:
                return conto_key, kw.upper()
    return "[N] SPESE VARIE & PICCOLA CASSA", "DEFAULT"

# --- STATO SESSIONE IN RAM ---
def init_tube_state():
    defaults = {
        "fondo_cassa_1": 200.0,
        "fondo_cassa_2": 0.0,
        "rt_contanti": 420.0,
        "rt_elettronico": 510.0,
        "pos_1_storico": 380.0,
        "pos_2_storico": 130.0,
        "pos_satispay": 45.0,
        "contante_contato_reale": 535.0,
        "semantic_rules": DEFAULT_SEMANTIC_RULES,
        "gemini_key": "",
        "tube_ledger": [
            {"date": datetime.now().strftime("%Y-%m-%d"), "time": "08:15", "type": "BOLLA CASH", "conto": "[C] LATTE, FRESCHI & LIEVITATI", "metodo": "CONTANTI", "desc": "Fornitore Brioche & Latte Fresco (Pagato dal cassetto)", "amount": -35.00},
            {"date": datetime.now().strftime("%Y-%m-%d"), "time": "08:58", "type": "SCONTRINO", "conto": "[D] SNACK, CUCINA & SALATO", "metodo": "CARTA / POS", "desc": "Pechino Follonica (Pagato con Carta — Non tocca i contanti)", "amount": -19.80},
            {"date": datetime.now().strftime("%Y-%m-%d"), "time": "10:30", "type": "GIUSTIFICATIVO", "conto": "[O] PRELIEVO TITOLARE / VERSAMENTO", "metodo": "CONTANTI", "desc": "Prelievo Titolare per commissioni urgenti", "amount": -50.00}
        ]
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_tube_state()

# --- CSS ANTI-SCORRIMENTO ORIZZONTALE PER TELEFONINO ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;700;800;900&family=Share+Tech+Mono&display=swap');

html, body, [data-testid="stAppViewContainer"], .stApp, .main, .block-container {
    overflow-x: hidden !important;
    max-width: 100vw !important;
    box-sizing: border-box !important;
}
.stApp {
    background-color: #0D1117;
    color: #F8FAFC;
    font-family: 'Orbitron', sans-serif;
}
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 0.6rem; padding-left: 0.9rem !important; padding-right: 0.9rem !important; max-width: 98% !important; }

div[data-baseweb="input"] > div:focus-within {
    border-color: #10B981 !important;
    box-shadow: 0 0 10px rgba(16, 185, 129, 0.45) !important;
}
div.stButton > button {
    background-color: #17202A !important; color: #F8FAFC !important;
    border: 1px solid #2E4053 !important; border-radius: 3px !important;
    font-family: 'Orbitron', sans-serif !important; font-size: 11px !important;
    font-weight: 800 !important; min-height: 42px !important;
}
div.stButton > button:hover {
    border-color: #F59E0B !important; color: #F59E0B !important;
}
.tube-header {
    background: linear-gradient(90deg, #131B26 0%, #1E2D3D 50%, #131B26 100%);
    border: 2px solid #F59E0B; border-left: 6px solid #38BDF8;
    padding: 14px 18px; border-radius: 4px; margin-bottom: 12px;
    display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 12px;
}
.kpi-card {
    background-color: #141B24; border: 1px solid #2A384B; border-left: 5px solid #F59E0B;
    padding: 14px; border-radius: 4px; margin-bottom: 10px;
}
.kpi-lbl { font-size: 10px; color: #94A3B8; font-family: 'Share Tech Mono', monospace; letter-spacing: 1px; }
.kpi-val { font-size: 23px; font-weight: 900; color: #FFFFFF; margin-top: 4px; }
.kpi-sub { font-size: 11px; font-family: 'Share Tech Mono', monospace; margin-top: 5px; }
.verdict-box {
    padding: 16px; border-radius: 4px; margin-top: 8px; margin-bottom: 12px;
    font-family: 'Share Tech Mono', monospace;
}
</style>
""", unsafe_allow_html=True)

# --- HEADER CON RITORNO ALLA NAVE MADRE (ALPHA MAIN MISSION) ---
h_c1, h_c2 = st.columns([3.8, 1.2])
with h_c1:
    st.markdown(f"""
    <div class="tube-header">
        <div style="display:flex; align-items:center; gap:16px;">
            <div>{TRAVEL_TUBE_SVG}</div>
            <div>
                <div style="font-size:11px; color:#38BDF8; font-family:'Share Tech Mono'; letter-spacing:1.5px;">
                    MOONBASE ALPHA // SECTOR 12 STANDALONE POD
                </div>
                <div style="font-size:21px; font-weight:900; color:#FFFFFF; letter-spacing:1.3px;">
                    TRAVEL TUBE // SALVACULO CASSA & POS SHIELD
                </div>
                <div style="font-size:11px; color:#F59E0B; font-family:'Share Tech Mono';">
                    ALLINEAMENTO CASSETTO · COLLISIONE MULTI-POS/RT · MOTORE SEMANTICO A-O
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
with h_c2:
    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
    st.link_button("🏠 TORNA A MAIN MISSION\n(PAGINA ZERO)", "https://alpha-main-mission.streamlit.app", use_container_width=True)

# --- BARRA DI NAVIGAZIONE INTERNA DEL POD ---
tab_mode = st.radio(
    "SELEZIONA OPERAZIONE TRAVEL TUBE:",
    [
        "1. 🛡️ Pareggio Cassa & Multi-POS",
        "2. 🧠 Scanner & Semantica (A-O)",
        "3. ⚡ Giustificativo Volante 3-Sec",
        "4. 🖨️ Verbale Difesa & Ponte JSON"
    ],
    horizontal=True,
    label_visibility="collapsed"
)

df_led = pd.DataFrame(st.session_state["tube_ledger"])
uscite_contanti_cassetto = 0.0
if not df_led.empty:
    uscite_contanti_cassetto = abs(df_led[(df_led["amount"] < 0) & (df_led["metodo"] == "CONTANTI")]["amount"].sum())

# ==============================================================================
# TAB 1: SCUDO PAREGGIO CASSA, FONDO MATTINA & COLLISIONE MULTI-POS vs RT
# ==============================================================================
if tab_mode.startswith("1."):
    st.markdown("##### 🛡️ ALLINEAMENTO GIORNALIERO / SETTIMANALE: FONDO CASSA vs REGISTRATORE RT vs STORICO POS")

    col_f, col_rt, col_pos = st.columns(3)
    with col_f:
        st.markdown("###### 🪙 1. FONDO CASSA & CASSETTO REALE")
        st.session_state["fondo_cassa_1"] = st.number_input("Fondo Cassa 1 Mattina (€):", 0.0, 50000.0, st.session_state["fondo_cassa_1"], step=10.0)
        st.session_state["fondo_cassa_2"] = st.number_input("Fondo Cassa 2 / Spiccioli (€):", 0.0, 50000.0, st.session_state["fondo_cassa_2"], step=10.0)
        st.session_state["contante_contato_reale"] = st.number_input("💵 CONTANTE FISICO CONTATO ORA NEL CASSETTO (€):", 0.0, 100000.0, st.session_state["contante_contato_reale"], step=5.0)

    with col_rt:
        st.markdown("###### 🧾 2. LETTURA REGISTRATORE TELEMATICO (RT)")
        st.session_state["rt_contanti"] = st.number_input("Vendite CONTANTI battute su RT (€):", 0.0, 100000.0, st.session_state["rt_contanti"], step=10.0)
        st.session_state["rt_elettronico"] = st.number_input("Vendite ELETTRONICO battute su RT (€):", 0.0, 100000.0, st.session_state["rt_elettronico"], step=10.0)
        st.info(f"📤 **Uscite Contanti Giustificate oggi in RAM:** `- € {uscite_contanti_cassetto:.2f}`")

    with col_pos:
        st.markdown("###### 💳 3. STORICO LETTURA POS (1 O PIÙ POS)")
        st.session_state["pos_1_storico"] = st.number_input("Storico POS Principale (€):", 0.0, 100000.0, st.session_state["pos_1_storico"], step=10.0)
        st.session_state["pos_2_storico"] = st.number_input("Storico POS 2 / Mobile (€):", 0.0, 100000.0, st.session_state["pos_2_storico"], step=10.0)
        st.session_state["pos_satispay"] = st.number_input("Satispay / App / Altro POS (€):", 0.0, 100000.0, st.session_state["pos_satispay"], step=5.0)

    # --- MOTORE MATEMATICO DI RICONCILIAZIONE ---
    fondo_totale = st.session_state["fondo_cassa_1"] + st.session_state["fondo_cassa_2"]
    contante_atteso_cassetto = fondo_totale + st.session_state["rt_contanti"] - uscite_contanti_cassetto
    diff_cassetto = st.session_state["contante_contato_reale"] - contante_atteso_cassetto

    totale_storico_pos = st.session_state["pos_1_storico"] + st.session_state["pos_2_storico"] + st.session_state["pos_satispay"]
    diff_pos_vs_rt = totale_storico_pos - st.session_state["rt_elettronico"]

    # Prelievo serale per lasciare esattamente il Fondo Cassa domani mattina
    banconote_da_togliere_sera = st.session_state["contante_contato_reale"] - fondo_totale

    k1, k2, k3 = st.columns(3)
    with k1:
        col_c1 = "#10B981" if abs(diff_cassetto) < 0.50 else "#EF4444"
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color:{col_c1};">
            <div class="kpi-lbl">CONTANTE CHE DEVE ESSERCI NEL CASSETTO ORA</div>
            <div class="kpi-val">€ {contante_atteso_cassetto:.2f}</div>
            <div class="kpi-sub" style="color:{col_c1};">
                Reale contato: € {st.session_state['contante_contato_reale']:.2f} (Scarto: € {diff_cassetto:+.2f})
            </div>
        </div>
        """, unsafe_allow_html=True)

    with k2:
        col_c2 = "#10B981" if abs(diff_pos_vs_rt) < 0.50 else "#F59E0B"
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color:{col_c2};">
            <div class="kpi-lbl">CONFRONTO STORICO POS vs ELETTRONICO RT</div>
            <div class="kpi-val">POS € {totale_storico_pos:.2f}</div>
            <div class="kpi-sub" style="color:{col_c2};">
                RT Elettronico: € {st.session_state['rt_elettronico']:.2f} (Diff: € {diff_pos_vs_rt:+.2f})
            </div>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        azione_mattina = (
            f"TOGLI € {banconote_da_togliere_sera:.2f} (Versamento/Chiusura)"
            if banconote_da_togliere_sera >= 0
            else f"RIMETTI € {abs(banconote_da_togliere_sera):.2f} IN BANCONOTE!"
        )
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color:#38BDF8;">
            <div class="kpi-lbl">RIPRISTINO FONDO CASSA PER DOMANI MATTINA (€ {fondo_totale:.2f})</div>
            <div class="kpi-val" style="font-size:19px; color:#38BDF8;">{azione_mattina}</div>
            <div class="kpi-sub" style="color:#94A3B8;">Per far trovare il Fondo Cassa spaccato al centesimo</div>
        </div>
        """, unsafe_allow_html=True)

    # --- DIAGNOSI INTELLIGENTE & MANOVRE DI PAREGGIO SUGGERITE ---
    st.markdown("###### 🧠 DIAGNOSI TRAVEL TUBE & MANOVRE DI PAREGGIO CONSIGLIATE:")

    if abs(diff_cassetto) < 0.50 and abs(diff_pos_vs_rt) < 0.50:
        st.success("🟢 **ASSETTO PERFETTO AL CENTESIMO:** Il contante fisico nel cassetto coincide con `Fondo + RT Contanti - Uscite` e la somma dei POS combacia con l'Elettronico del Registratore RT!")
    else:
        if diff_cassetto < -0.50:
            mancante = abs(diff_cassetto)
            st.markdown(f"""
            <div class="verdict-box" style="background:#2A1215; border:2px solid #EF4444;">
                <b style="color:#FCA5A5;">🔴 AMMANCO CONTANTI NEL CASSETTO: Mancano € {mancante:.2f} rispetto alla lettura RT!</b><br>
                <b>Perché succede:</b> sono usciti € {mancante:.2f} dal cassetto (pagamento fornitore volante, prelievo titolare, spiccioli o scontrino battuto "Contanti" ma pagato col POS) senza essere stati registrati.<br>
                <b>👉 Soluzione 1 (Ripristino Fisico):</b> rimetti subito <b>€ {mancante:.2f}</b> in contanti nel cassetto.<br>
                <b>👉 Soluzione 2 (Regolarizzazione Contabile in 1-Click):</b> premi il bottone qui sotto per generare adesso il giustificativo di uscita cassa di <b>€ {mancante:.2f}</b> e azzerare lo scarto.
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"⚡ CREA ORA GIUSTIFICATIVO USCITA DI € {mancante:.2f} E PAREGGIA IL CASSETTO", use_container_width=True):
                st.session_state["tube_ledger"].append({
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "time": datetime.now().strftime("%H:%M"),
                    "type": "PAREGGIO CASSA",
                    "conto": "[O] PRELIEVO TITOLARE / VERSAMENTO",
                    "metodo": "CONTANTI",
                    "desc": f"Giustificativo di riallineamento contante cassetto (€ {mancante:.2f})",
                    "amount": -round(mancante, 2)
                })
                st.rerun()

        elif diff_cassetto > 0.50:
            eccedenza = diff_cassetto
            st.markdown(f"""
            <div class="verdict-box" style="background:#2B2111; border:2px solid #F59E0B;">
                <b style="color:#FDE047;">🟠 ECCEDENZA CONTANTI NEL CASSETTO: Ci sono +€ {eccedenza:.2f} in più rispetto agli scontrini RT!</b><br>
                <b>Attenzione Ispettiva:</b> avere più contanti nel cassetto rispetto a quanto battuto sul registratore RT fa scattare la presunzione di vendite non scontrinate.<br>
                <b>👉 Soluzione Immediata:</b> verifica se sono mance/fondo spiccioli extra da separare dal cassetto fiscale, oppure emetti scontrino/chiusura di riallineamento per <b>€ {eccedenza:.2f}</b>.
            </div>
            """, unsafe_allow_html=True)

        if diff_pos_vs_rt > 0.50:
            st.markdown(f"""
            <div class="verdict-box" style="background:#1E1B2E; border:2px solid #A855F7;">
                <b style="color:#D8B4FE;">🟣 COLLISIONE STORICO POS vs RT: I tuoi POS hanno incassato +€ {diff_pos_vs_rt:.2f} che NON risultano battuti come Elettronico sul Registratore RT!</b><br>
                <b>Perché succede:</b> hai strisciato la carta del cliente sul POS ma hai dimenticato di battere lo scontrino RT (oppure lo hai battuto per errore come "Contanti", creando anche un finto buco di cassa!).<br>
                <b>👉 Manovra Correttiva Prima della Chiusura Sera:</b> batti sul Registratore Telematico uno scontrino di riallineamento da <b>€ {diff_pos_vs_rt:.2f}</b> premendo il tasto <b>PAGAMENTO ELETTRONICO</b> (senza strisciare alcuna carta), oppure emetti <b>Fattura/Autofattura</b> collegata a quell'incasso POS.
            </div>
            """, unsafe_allow_html=True)

        elif diff_pos_vs_rt < -0.50:
            st.warning(f"⚠️ **RT Elettronico più alto dei POS di € {abs(diff_pos_vs_rt):.2f}:** hai battuto per errore 'Pagamento Elettronico' sulla cassa RT per un cliente che ti ha pagato in contanti!")

# ==============================================================================
# TAB 2: MOTORE SEMANTICO MERCEOLOGICO (RICONOSCIMENTO SINONIMI & CODICI BOLLE)
# ==============================================================================
elif tab_mode.startswith("2."):
    st.markdown("##### 🧠 MOTORE SEMANTICO AUTOMATICO // SMISTAMENTO CODICI FORNITORE E SCONTRINI NEI CONTI (A–O)")
    st.caption("Qualsiasi sigla o descrizione compaia sulla bolla o sullo scontrino, il motore semantico riconosce la radice della parola e la assegna al Conto Parallelo giusto.")

    sem_c1, sem_c2, sem_c3, sem_c4 = st.columns([1.8, 0.9, 1.0, 1.0])
    with sem_c1:
        raw_desc = st.text_input("📝 Scrivi o incolla la voce della Bolla / Scontrino:", value="Art. 10001 Miscela Oro Grani 1Kg")
    with sem_c2:
        raw_amount = st.number_input("💶 Importo (€):", 0.10, 50000.0, 19.80, step=0.50)
    with sem_c3:
        raw_metodo = st.selectbox("💳 Pagato con:", ["CONTANTI", "CARTA / POS", "BONIFICO / SDD"])

    conto_trovato, kw_usata = classify_item_semantically(raw_desc, st.session_state["semantic_rules"])
    with sem_c4:
        conto_scelto = st.selectbox("🎯 Conto Riconosciuto:", list(st.session_state["semantic_rules"].keys()), index=list(st.session_state["semantic_rules"].keys()).index(conto_trovato))

    st.info(f"🔍 **Analisi Semantica Live:** la voce *'{raw_desc}'* contiene la radice **`{kw_usata}`** $\rightarrow$ Assegnata automaticamente a **`{conto_scelto}`**")

    if st.button(f"⚡ REGISTRA € {raw_amount:.2f} SU {conto_scelto} ({raw_metodo})", use_container_width=True):
        st.session_state["tube_ledger"].append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M"),
            "type": "SEMANTIC-SCAN",
            "conto": conto_scelto,
            "metodo": raw_metodo,
            "desc": raw_desc,
            "amount": -round(raw_amount, 2)
        })
        st.toast(f"✅ Imputato su {conto_scelto}!")
        st.rerun()

    with st.expander("📚 Insegna nuove parole chiave o codici articolo al Dizionario Semantico (A–O)"):
        sel_cat = st.selectbox("Scegli il Conto A–O da arricchire:", list(st.session_state["semantic_rules"].keys()))
        curr_kws = ", ".join(st.session_state["semantic_rules"][sel_cat])
        new_kws = st.text_area("Parole chiave / Codici Fornitore separati da virgola:", value=curr_kws)
        if st.button("💾 AGGIORNA DIZIONARIO SEMANTICO"):
            st.session_state["semantic_rules"][sel_cat] = [x.strip().upper() for x in new_kws.split(",") if x.strip()]
            st.success(f"Dizionario aggiornato per {sel_cat}!")

# ==============================================================================
# TAB 3: GIUSTIFICATIVO VOLANTE 3-SECONDI (E AUTOFATTURA OMAGGI / AUTOCONSUMO)
# ==============================================================================
elif tab_mode.startswith("3."):
    st.markdown("##### ⚡ GIUSTIFICATIVO VOLANTE 3-SECONDI & AUTOFATTURA DI ALLINEAMENTO MAGAZZINO")
    g1, g2 = st.columns(2)
    with g1:
        imp_veloce = st.number_input("💶 Importo Contanti Uscito dal Cassetto (€):", 0.50, 10000.0, 25.0, step=1.0)
    with g2:
        nota_veloce = st.text_input("Nota rapida (Opzionale):", placeholder="Es. Ghiaccio, Acconto ragazzo, Gasolio...")

    st.caption("Tocca un pulsante per scaricare subito il contante dal cassetto fiscale con ora esatta:")
    b_cols = st.columns(3)
    quick_actions = [
        ("🥛 FRESCHI / LATTE [C]", "[C] LATTE, FRESCHI & LIEVITATI"),
        ("🧊 GHIACCIO / CONSUMABILI [E]", "[E] GHIACCIO & CONSUMABILI"),
        ("👤 ACCONTO STAFF [H]", "[H] STAFF & COLLABORATORI"),
        ("🛒 SPESA VOLANTE [M]", "[M] FORNITORI OCCASIONALI"),
        ("💶 PRELIEVO TITOLARE [O]", "[O] PRELIEVO TITOLARE / VERSAMENTO"),
        ("☕ AUTOFATTURA OMAGGI / CALO [A]", "[A] CAFFETTERIA & MISCELE")
    ]
    for idx_q, (btn_lbl, c_target) in enumerate(quick_actions):
        if b_cols[idx_q % 3].button(btn_lbl, use_container_width=True):
            desc_f = f"{btn_lbl} — {nota_veloce}" if nota_veloce.strip() else f"Registrazione rapida {btn_lbl}"
            st.session_state["tube_ledger"].append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%H:%M"),
                "type": "GIUSTIFICATIVO",
                "conto": c_target,
                "metodo": "CONTANTI",
                "desc": desc_f,
                "amount": -round(imp_veloce, 2)
            })
            st.toast(f"✅ Registrato: {btn_lbl} (-€ {imp_veloce:.2f})")
            st.rerun()

# ==============================================================================
# TAB 4: STAMPA VERBALE DIFESA CASSA (.TXT) & PONTE JSON CON MAIN MISSION
# ==============================================================================
else:
    st.markdown("##### 🖨️ PROSPETTO ORARIO DIFESA CASSA & SCAMBIO DATI CON MAIN MISSION")
    edited_led = st.data_editor(
        df_led,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="tube_ed"
    )
    if not edited_led.equals(df_led):
        st.session_state["tube_ledger"] = edited_led.to_dict("records")
        st.rerun()

    fondo_tot = st.session_state["fondo_cassa_1"] + st.session_state["fondo_cassa_2"]
    atteso_ora = fondo_tot + st.session_state["rt_contanti"] - uscite_contanti_cassetto

    verbale_txt = (
        f"==========================================================\n"
        f"PROSPETTO GIORNALIERO RICONCILIAZIONE CASSA (TRAVEL TUBE)\n"
        f"Data e Ora Rilevazione: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        f"==========================================================\n"
        f"(+) FONDO CASSA INIZIALE MATTINA:       EUR {fondo_tot:10.2f}\n"
        f"(+) CORRISPETTIVI CONTANTI RT:          EUR {st.session_state['rt_contanti']:10.2f}\n"
        f"(-) USCITE CONTANTI DOCUMENTATE:       -EUR {uscite_contanti_cassetto:10.2f}\n"
        f"----------------------------------------------------------\n"
        f"(=) CONTANTE ATTESO NEL CASSETTO:       EUR {atteso_ora:10.2f}\n"
        f"(=) CONTANTE FISICO RILEVATO:           EUR {st.session_state['contante_contato_reale']:10.2f}\n"
        f"==========================================================\n"
        f"DETTAGLIO ANALITICO MOVIMENTI E GIUSTIFICATIVI:\n"
    )
    for r in st.session_state["tube_ledger"]:
        verbale_txt += f"- [{r['time']}] {r['metodo']:10s} | {r['conto']:32s} | EUR {r['amount']:+8.2f} | {r['desc']}\n"

    d1, d2 = st.columns(2)
    with d1:
        st.download_button("🖨️ SCARICA DISTINTA DIFESA CASSA (.TXT)", verbale_txt, file_name=f"distinta_cassa_{datetime.now().strftime('%Y%m%d_%H%M')}.txt", mime="text/plain", use_container_width=True)
    with d2:
        json_bridge = json.dumps(st.session_state["tube_ledger"], indent=2, ensure_ascii=False)
        st.download_button("🔗 ESPORTA PONTE DATI PER MAIN MISSION (.JSON)", json_bridge, file_name=f"travel_tube_bridge_{datetime.now().strftime('%Y_%m')}.json", mime="application/json", use_container_width=True)
