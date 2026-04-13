"""
ApiTrack Pro – Application de gestion apicole professionnelle
Streamlit + Python + SQLite
CORRECTION : Les fonctions ia_analyser_* utilisent maintenant ia_call()
             (multi-fournisseurs) au lieu de forcer Anthropic uniquement.
"""

import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import hashlib
import json
import os
import datetime
from pathlib import Path

# ── Plotly (graphiques) ──────────────────────────────────────────────────────
import plotly.express as px
import plotly.graph_objects as go

# ── Folium (cartographie) ────────────────────────────────────────────────────
try:
    import folium
    from streamlit_folium import st_folium
    FOLIUM_OK = True
except ImportError:
    FOLIUM_OK = False

# ── TensorFlow (optionnel – deep learning) ───────────────────────────────────
try:
    import tensorflow as tf
    TF_OK = True
except ImportError:
    TF_OK = False

# ── SentinelHub (optionnel) ──────────────────────────────────────────────────
try:
    from sentinelhub import SHConfig, BBox, CRS, DataCollection, SentinelHubRequest
    SH_OK = True
except ImportError:
    SH_OK = False

# ── Anthropic (IA gratuite via Claude) ───────────────────────────────────────
try:
    import anthropic
    ANTHROPIC_OK = True
except ImportError:
    ANTHROPIC_OK = False

# ── Base64 pour upload images ─────────────────────────────────────────────────
import base64

# ════════════════════════════════════════════════════════════════════════════
# CONFIGURATION STREAMLIT
# ════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="ApiTrack Pro",
    page_icon="🐝",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = "apitrack.db"

# ════════════════════════════════════════════════════════════════════════════
# CSS PERSONNALISÉ
# ════════════════════════════════════════════════════════════════════════════
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --gold:         #F5A623;
        --gold-light:   #FFD07A;
        --gold-dark:    #C8820A;
        --bg-app:       #0F1117;
        --bg-main:      #161B27;
        --bg-card:      #1E2535;
        --bg-card2:     #252D40;
        --bg-input:     #1A2030;
        --border:       #2E3A52;
        --border-light: #3A4A66;
        --text-primary: #F0F4FF;
        --text-second:  #A8B4CC;
        --text-muted:   #6B7A99;
        --text-label:   #8899BB;
        --green:        #34D399;
        --green-bg:     #0D2A1F;
        --green-border: #1A5C3A;
        --yellow:       #FBD147;
        --yellow-bg:    #2A200A;
        --yellow-border:#4A3A10;
        --red:          #F87171;
        --red-bg:       #2A0D0D;
        --red-border:   #5C1A1A;
        --blue:         #60A5FA;
        --blue-bg:      #0D1A2A;
        --blue-border:  #1A3A5C;
    }

    .stApp {
        background-color: var(--bg-app) !important;
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
    }
    .main .block-container {
        padding: 1.5rem 2rem;
        max-width: 1400px;
        background: var(--bg-main) !important;
    }
    .stApp p, .stApp span, .stApp div, .stApp label,
    .stMarkdown, .stMarkdown p {
        color: var(--text-primary) !important;
    }

    [data-testid="stSidebar"] {
        background: #080C14 !important;
        border-right: 1px solid var(--border) !important;
    }
    [data-testid="stSidebar"] * {
        color: #C8D8F0 !important;
    }
    [data-testid="stSidebar"] button {
        background: transparent !important;
        color: #A8B4CC !important;
        border: none !important;
        text-align: left !important;
        font-size: 0.875rem !important;
        padding: 8px 12px !important;
        border-radius: 6px !important;
        transition: all 0.15s !important;
    }
    [data-testid="stSidebar"] button:hover {
        background: rgba(245,166,35,0.12) !important;
        color: var(--gold-light) !important;
    }

    h1, h2, h3, h4, h5, h6,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3 {
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
    }
    h2 { font-size: 1.4rem !important; border-bottom: 1px solid var(--border); padding-bottom: 10px; margin-bottom: 16px; }
    h3 { font-size: 1.05rem !important; color: var(--gold-light) !important; }

    [data-testid="metric-container"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-top: 3px solid var(--gold) !important;
        border-radius: 10px !important;
        padding: 16px !important;
    }
    [data-testid="stMetricValue"] {
        color: var(--gold-light) !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetricLabel"] {
        color: var(--text-second) !important;
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
    }
    [data-testid="stMetricDelta"] { color: var(--green) !important; }

    .stButton > button {
        background: var(--gold-dark) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        padding: 8px 18px !important;
        letter-spacing: 0.02em !important;
        transition: all 0.15s !important;
    }
    .stButton > button:hover {
        background: var(--gold) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(245,166,35,0.3) !important;
    }

    .stTextInput input,
    .stNumberInput input,
    .stTextArea textarea,
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input {
        background: var(--bg-input) !important;
        color: var(--text-primary) !important;
        border: 1.5px solid var(--border-light) !important;
        border-radius: 8px !important;
        font-size: 0.9rem !important;
    }
    .stTextInput input:focus,
    .stNumberInput input:focus,
    .stTextArea textarea:focus {
        border-color: var(--gold) !important;
        box-shadow: 0 0 0 2px rgba(245,166,35,0.2) !important;
    }
    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {
        color: var(--text-muted) !important;
    }
    .stTextInput label, .stNumberInput label,
    .stTextArea label, .stSelectbox label,
    .stSlider label, .stCheckbox label,
    .stFileUploader label {
        color: var(--text-second) !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
    }

    [data-testid="stSelectbox"] > div > div {
        background: var(--bg-input) !important;
        color: var(--text-primary) !important;
        border: 1.5px solid var(--border-light) !important;
        border-radius: 8px !important;
    }
    [data-testid="stSelectbox"] span,
    [data-testid="stSelectbox"] p {
        color: var(--text-primary) !important;
    }

    .stDataFrame, [data-testid="stDataFrame"] {
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        overflow: hidden !important;
    }
    .stDataFrame table {
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
    }
    .stDataFrame thead th {
        background: var(--bg-card2) !important;
        color: var(--gold-light) !important;
        font-weight: 600 !important;
        font-size: 0.78rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
        border-bottom: 1px solid var(--border) !important;
        padding: 10px 12px !important;
    }
    .stDataFrame tbody td {
        color: var(--text-primary) !important;
        background: var(--bg-card) !important;
        border-bottom: 1px solid var(--border) !important;
        padding: 8px 12px !important;
        font-size: 0.875rem !important;
    }
    .stDataFrame tbody tr:hover td {
        background: var(--bg-card2) !important;
    }

    [data-testid="stAlert"],
    .stAlert {
        border-radius: 8px !important;
        border-width: 1px !important;
        padding: 12px 16px !important;
    }

    [data-testid="stTabs"] [role="tablist"] {
        background: var(--bg-card) !important;
        border-bottom: 1px solid var(--border) !important;
        border-radius: 8px 8px 0 0 !important;
        padding: 4px 8px 0 !important;
    }
    [data-testid="stTabs"] button[role="tab"] {
        color: var(--text-second) !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        background: transparent !important;
        border: none !important;
        padding: 8px 16px !important;
        border-bottom: 2px solid transparent !important;
    }
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: var(--gold) !important;
        border-bottom: 2px solid var(--gold) !important;
        font-weight: 600 !important;
    }
    [data-testid="stTabs"] button[role="tab"]:hover {
        color: var(--gold-light) !important;
        background: rgba(245,166,35,0.08) !important;
    }
    [data-testid="stTabsContent"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
        padding: 16px !important;
    }

    [data-testid="stExpander"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
    }
    [data-testid="stExpander"] summary {
        color: var(--text-primary) !important;
        font-weight: 500 !important;
        background: var(--bg-card) !important;
    }
    [data-testid="stExpander"] summary:hover {
        background: var(--bg-card2) !important;
        color: var(--gold-light) !important;
    }
    [data-testid="stExpander"] > div {
        background: var(--bg-card) !important;
    }

    [data-testid="stFileUploader"] {
        background: var(--bg-input) !important;
        border: 1.5px dashed var(--border-light) !important;
        border-radius: 8px !important;
        color: var(--text-second) !important;
    }
    [data-testid="stFileUploader"] span,
    [data-testid="stFileUploader"] p {
        color: var(--text-second) !important;
    }

    [data-testid="stDownloadButton"] button {
        background: var(--bg-card2) !important;
        color: var(--gold-light) !important;
        border: 1px solid var(--gold-dark) !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
    }
    [data-testid="stDownloadButton"] button:hover {
        background: var(--gold-dark) !important;
        color: #FFFFFF !important;
    }

    .api-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
        color: var(--text-primary);
    }
    .api-card-title {
        font-size: 1rem;
        font-weight: 600;
        color: var(--gold-light);
        margin-bottom: 10px;
        padding-bottom: 8px;
        border-bottom: 1px solid var(--border);
    }

    .badge-ok   { background:#0D2A1F; color:#6EE7B7; border:1px solid #1A5C3A; padding:3px 10px; border-radius:20px; font-size:0.72rem; font-weight:600; }
    .badge-warn { background:#2A200A; color:#FDE68A; border:1px solid #4A3A10; padding:3px 10px; border-radius:20px; font-size:0.72rem; font-weight:600; }
    .badge-crit { background:#2A0D0D; color:#FCA5A5; border:1px solid #5C1A1A; padding:3px 10px; border-radius:20px; font-size:0.72rem; font-weight:600; }

    .api-footer {
        text-align: center;
        font-size: 0.72rem;
        color: var(--text-muted);
        padding: 12px;
        border-top: 1px solid var(--border);
        margin-top: 2rem;
        font-family: 'JetBrains Mono', monospace;
        background: var(--bg-card);
        border-radius: 0 0 8px 8px;
    }

    [data-testid="stFormSubmitButton"] button {
        background: var(--gold-dark) !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        width: 100% !important;
    }
    [data-testid="stFormSubmitButton"] button:hover {
        background: var(--gold) !important;
    }

    [data-testid="stProgressBar"] > div {
        background: var(--bg-card2) !important;
    }
    [data-testid="stProgressBar"] > div > div {
        background: linear-gradient(90deg, var(--gold-dark), var(--gold)) !important;
    }

    hr { border-color: var(--border) !important; }
    a { color: var(--gold-light) !important; }
    a:hover { color: var(--gold) !important; }

    code {
        background: var(--bg-card2) !important;
        color: var(--gold-light) !important;
        padding: 1px 6px !important;
        border-radius: 4px !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85em !important;
    }

    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: var(--bg-app); }
    ::-webkit-scrollbar-thumb { background: var(--border-light); border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--gold-dark); }

    .js-plotly-plot .plotly .main-svg {
        background: transparent !important;
    }
    </style>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# BASE DE DONNÉES SQLITE
# ════════════════════════════════════════════════════════════════════════════
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        email TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS ruches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        race TEXT DEFAULT 'intermissa',
        date_installation TEXT,
        localisation TEXT,
        latitude REAL,
        longitude REAL,
        statut TEXT DEFAULT 'actif',
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS inspections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ruche_id INTEGER REFERENCES ruches(id) ON DELETE CASCADE,
        date_inspection TEXT NOT NULL,
        poids_kg REAL,
        nb_cadres INTEGER,
        varroa_pct REAL,
        reine_vue INTEGER DEFAULT 1,
        comportement TEXT DEFAULT 'calme',
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS traitements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ruche_id INTEGER REFERENCES ruches(id) ON DELETE CASCADE,
        date_debut TEXT NOT NULL,
        date_fin TEXT,
        produit TEXT,
        pathologie TEXT,
        dose TEXT,
        duree_jours INTEGER,
        statut TEXT DEFAULT 'en_cours',
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS recoltes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ruche_id INTEGER REFERENCES ruches(id) ON DELETE CASCADE,
        date_recolte TEXT NOT NULL,
        type_produit TEXT DEFAULT 'miel',
        quantite_kg REAL,
        humidite_pct REAL,
        ph REAL,
        hda_pct REAL,
        qualite TEXT DEFAULT 'A',
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS morph_analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ruche_id INTEGER REFERENCES ruches(id),
        date_analyse TEXT NOT NULL,
        longueur_aile_mm REAL,
        largeur_aile_mm REAL,
        indice_cubital REAL,
        glossa_mm REAL,
        tomentum INTEGER,
        pigmentation TEXT,
        race_probable TEXT,
        confiance_json TEXT,
        specialisation TEXT,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS zones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        type_zone TEXT DEFAULT 'nectar',
        latitude REAL,
        longitude REAL,
        superficie_ha REAL,
        flore_principale TEXT,
        ndvi REAL,
        potentiel TEXT DEFAULT 'modere',
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS journal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        action TEXT NOT NULL,
        details TEXT,
        utilisateur TEXT DEFAULT 'admin'
    );

    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    );
    """)

    pwd_hash = hashlib.sha256("admin1234".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO users (username, password_hash, email) VALUES (?, ?, ?)",
              ("admin", pwd_hash, "admin@apitrack.pro"))

    _insert_demo_data(c)

    conn.commit()
    conn.close()


def _insert_demo_data(c):
    c.execute("SELECT COUNT(*) FROM ruches")
    if c.fetchone()[0] > 0:
        return

    ruches_demo = [
        ("Zitoun A", "intermissa", "2023-03-15", "Zone Atlas Nord", 34.88, 1.32, "actif"),
        ("Sahara B", "sahariensis", "2023-04-01", "Zone Jujubiers", 34.85, 1.35, "actif"),
        ("Atlas C", "hybride", "2022-05-20", "Zone Cèdres", 34.90, 1.28, "actif"),
        ("Cedre D", "intermissa", "2023-02-10", "Zone Atlas Sud", 34.82, 1.31, "actif"),
        ("Cedre E", "intermissa", "2024-03-01", "Zone Atlas Nord", 34.89, 1.33, "actif"),
        ("Oued F", "intermissa", "2024-04-15", "Bord Oued", 34.87, 1.30, "actif"),
    ]
    for r in ruches_demo:
        c.execute("INSERT INTO ruches (nom, race, date_installation, localisation, latitude, longitude, statut) VALUES (?,?,?,?,?,?,?)", r)

    today = datetime.date.today()
    inspections_demo = [
        (1, str(today), 28.4, 12, 0.8, 1, "calme", "Excellent couvain"),
        (2, str(today - datetime.timedelta(days=1)), 25.6, 10, 1.2, 1, "calme", "RAS"),
        (3, str(today - datetime.timedelta(days=2)), 22.1, 9, 2.4, 0, "nerveuse", "Reine introuvable"),
        (4, str(today - datetime.timedelta(days=3)), 26.9, 11, 1.1, 1, "très calme", "Top productrice"),
        (6, str(today - datetime.timedelta(days=1)), 19.2, 7, 3.8, 1, "agressive", "Traitement urgent"),
    ]
    for i in inspections_demo:
        c.execute("INSERT INTO inspections (ruche_id,date_inspection,poids_kg,nb_cadres,varroa_pct,reine_vue,comportement,notes) VALUES (?,?,?,?,?,?,?,?)", i)

    recoltes_demo = [
        (1, "2025-03-01", "miel", 48.0, 17.2, 3.8, None, "A"),
        (2, "2025-03-01", "miel", 32.0, 17.8, 3.9, None, "A"),
        (1, "2025-01-15", "pollen", 4.5, None, None, None, "A"),
        (4, "2025-03-15", "gelée royale", 0.6, None, None, 2.1, "A+"),
        (1, "2024-09-01", "miel", 62.0, 17.0, 3.7, None, "A"),
    ]
    for r in recoltes_demo:
        c.execute("INSERT INTO recoltes (ruche_id,date_recolte,type_produit,quantite_kg,humidite_pct,ph,hda_pct,qualite) VALUES (?,?,?,?,?,?,?,?)", r)

    morph_demo = [
        (1, str(today), 9.2, 3.1, 2.3, 6.1, 2, "Noir", "intermissa",
         json.dumps([{"race":"intermissa","confiance":72},{"race":"sahariensis","confiance":18},{"race":"hybride","confiance":8},{"race":"ligustica","confiance":2},{"race":"carnica","confiance":0}]),
         "Production miel + propolis"),
    ]
    for m in morph_demo:
        c.execute("INSERT INTO morph_analyses (ruche_id,date_analyse,longueur_aile_mm,largeur_aile_mm,indice_cubital,glossa_mm,tomentum,pigmentation,race_probable,confiance_json,specialisation) VALUES (?,?,?,?,?,?,?,?,?,?,?)", m)

    zones_demo = [
        ("Forêt chênes-lièges", "nectar+pollen", 34.88, 1.31, 120.0, "Quercus suber", 0.72, "élevé"),
        ("Jujubiers Est", "nectar", 34.86, 1.34, 45.0, "Ziziphus lotus", 0.65, "élevé"),
        ("Lavande Sud", "pollen", 34.83, 1.30, 18.0, "Lavandula stoechas", 0.58, "modéré"),
        ("Romarin Ouest", "nectar+pollen", 34.89, 1.28, 30.0, "Rosmarinus officinalis", 0.61, "modéré"),
    ]
    for z in zones_demo:
        c.execute("INSERT INTO zones (nom,type_zone,latitude,longitude,superficie_ha,flore_principale,ndvi,potentiel) VALUES (?,?,?,?,?,?,?,?)", z)

    journal_demo = [
        ("Initialisation base de données", "Données démo insérées", "système"),
        ("Inspection R07 critique", "Varroa 3.8% — alerte générée", "admin"),
        ("Récolte enregistrée", "48 kg miel toutes fleurs, ruche R01", "admin"),
        ("Morphométrie R01", "intermissa 72% — JSON sauvegardé", "admin"),
    ]
    for j in journal_demo:
        c.execute("INSERT INTO journal (action,details,utilisateur) VALUES (?,?,?)", j)

    c.execute("INSERT OR IGNORE INTO settings VALUES ('rucher_nom','Rucher de l Atlas')")
    c.execute("INSERT OR IGNORE INTO settings VALUES ('localisation','Tlemcen, Algérie')")
    c.execute("INSERT OR IGNORE INTO settings VALUES ('version','2.0.0')")


# ════════════════════════════════════════════════════════════════════════════
# AUTHENTIFICATION
# ════════════════════════════════════════════════════════════════════════════
def check_login(username, password):
    conn = get_db()
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    user = conn.execute(
        "SELECT * FROM users WHERE username=? AND password_hash=?",
        (username, pwd_hash)
    ).fetchone()
    conn.close()
    return user


def login_page():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style='text-align:center;margin-bottom:24px'>
            <div style='font-size:3rem'>🐝</div>
            <h1 style='font-family:Playfair Display,serif;color:#F0F4FF;font-size:2rem;margin:8px 0 4px'>ApiTrack Pro</h1>
            <p style='color:#A8B4CC;font-size:.9rem'>Gestion apicole professionnelle</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Identifiant", placeholder="admin")
            password = st.text_input("Mot de passe", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Se connecter", use_container_width=True)

        if submitted:
            user = check_login(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = username
                log_action("Connexion", f"Utilisateur {username} connecté")
                st.rerun()
            else:
                st.error("Identifiants incorrects. (Démo : admin / admin1234)")

        st.markdown("<p style='text-align:center;font-size:.75rem;color:#A8B4CC;margin-top:16px'>admin / admin1234 pour la démo</p>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# UTILITAIRES
# ════════════════════════════════════════════════════════════════════════════
def log_action(action, details="", user=None):
    u = user or st.session_state.get("username", "système")
    conn = get_db()
    conn.execute("INSERT INTO journal (action,details,utilisateur) VALUES (?,?,?)", (action, details, u))
    conn.commit()
    conn.close()


def status_badge(varroa):
    if varroa is None:
        return "N/A"
    if varroa >= 3.0:
        return "🔴 Critique"
    elif varroa >= 2.0:
        return "🟡 Surveiller"
    else:
        return "🟢 Bon"


def get_setting(key, default=""):
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row[0] if row else default


# ════════════════════════════════════════════════════════════════════════════
# MOTEUR IA MULTI-FOURNISSEURS — 100% GRATUITS
# ════════════════════════════════════════════════════════════════════════════

IA_PROVIDERS = {
    "🤖 Claude (Anthropic)": {
        "key":        "anthropic_api_key",
        "env":        "ANTHROPIC_API_KEY",
        "url":        "https://console.anthropic.com",
        "prefix":     "sk-ant-",
        "models":     ["claude-opus-4-5", "claude-haiku-4-5-20251001"],
        "default":    "claude-opus-4-5",
        "quota":      "~5$ crédits offerts · ~500 analyses",
        "vision":     True,
        "type":       "anthropic",
    },
    "🌟 Gemma 4 (Google AI Studio)": {
        "key":        "google_api_key",
        "env":        "GOOGLE_API_KEY",
        "url":        "https://aistudio.google.com/app/apikey",
        "prefix":     "AIzaSy",
        "models":     ["gemini-2.0-flash", "gemma-4-31b-it", "gemma-4-27b-it", "gemini-1.5-flash"],
        "default":    "gemini-2.0-flash",
        "quota":      "Gratuit · 1 500 req/jour · 1M tokens/min",
        "vision":     True,
        "type":       "google",
    },
    "⚡ Groq (Ultra-rapide)": {
        "key":        "groq_api_key",
        "env":        "GROQ_API_KEY",
        "url":        "https://console.groq.com/keys",
        "prefix":     "gsk_",
        "models":     ["llama-3.3-70b-versatile", "llama-4-scout-17b-16e-instruct", "gemma2-9b-it"],
        "default":    "llama-3.3-70b-versatile",
        "quota":      "Gratuit · 30 RPM · 1 000 RPD · 800 tok/s",
        "vision":     False,
        "type":       "openai_compat",
        "base_url":   "https://api.groq.com/openai/v1",
    },
    "🔀 OpenRouter (Multi-modèles)": {
        "key":        "openrouter_api_key",
        "env":        "OPENROUTER_API_KEY",
        "url":        "https://openrouter.ai/keys",
        "prefix":     "sk-or-",
        "models":     ["meta-llama/llama-4-maverick:free", "deepseek/deepseek-r1:free",
                       "google/gemma-3-27b-it:free", "mistralai/mistral-7b-instruct:free",
                       "qwen/qwen3-235b-a22b:free"],
        "default":    "meta-llama/llama-4-maverick:free",
        "quota":      "Gratuit · ~50 req/jour · accès 200+ modèles",
        "vision":     False,
        "type":       "openai_compat",
        "base_url":   "https://openrouter.ai/api/v1",
    },
    "🇪🇺 Mistral AI (GDPR)": {
        "key":        "mistral_api_key",
        "env":        "MISTRAL_API_KEY",
        "url":        "https://console.mistral.ai/api-keys",
        "prefix":     "",
        "models":     ["mistral-large-latest", "mistral-small-latest", "open-mistral-7b"],
        "default":    "mistral-large-latest",
        "quota":      "Gratuit · 1 req/s · 1 milliard tok/mois",
        "vision":     False,
        "type":       "openai_compat",
        "base_url":   "https://api.mistral.ai/v1",
    },
    "🔍 Cohere (RAG/Search)": {
        "key":        "cohere_api_key",
        "env":        "COHERE_API_KEY",
        "url":        "https://dashboard.cohere.com/api-keys",
        "prefix":     "",
        "models":     ["command-r-plus", "command-r", "command-a-03-2025"],
        "default":    "command-r-plus",
        "quota":      "Gratuit · 20 RPM · 1 000 req/mois",
        "vision":     False,
        "type":       "cohere",
    },
    "🇨🇳 Zhipu AI / GLM (Gratuit illimité)": {
        "key":        "zhipu_api_key",
        "env":        "ZHIPU_API_KEY",
        "url":        "https://open.bigmodel.cn/usercenter/apikeys",
        "prefix":     "",
        "models":     ["glm-4v-flash", "glm-4-flash", "glm-4-plus"],
        "default":    "glm-4v-flash",
        "quota":      "Gratuit · Limites non documentées · Vision OK",
        "vision":     True,
        "type":       "openai_compat",
        "base_url":   "https://open.bigmodel.cn/api/paas/v4",
    },
    "🧠 Cerebras (Très rapide)": {
        "key":        "cerebras_api_key",
        "env":        "CEREBRAS_API_KEY",
        "url":        "https://cloud.cerebras.ai/platform",
        "prefix":     "csk-",
        "models":     ["llama-3.3-70b", "qwen3-235b", "llama-4-scout-17b"],
        "default":    "llama-3.3-70b",
        "quota":      "Gratuit · 30 RPM · 14 400 RPD",
        "vision":     False,
        "type":       "openai_compat",
        "base_url":   "https://api.cerebras.ai/v1",
    },
    "🤗 Hugging Face (10 000 modèles)": {
        "key":        "hf_api_key",
        "env":        "HF_API_KEY",
        "url":        "https://huggingface.co/settings/tokens",
        "prefix":     "hf_",
        "models":     ["mistralai/Mixtral-8x7B-Instruct-v0.1",
                       "meta-llama/Llama-3.3-70B-Instruct",
                       "Qwen/Qwen2.5-72B-Instruct"],
        "default":    "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "quota":      "Gratuit · Serverless Inference · modèles <10GB",
        "vision":     False,
        "type":       "huggingface",
    },
    "🐙 GitHub Models (GPT-4o gratuit)": {
        "key":        "github_api_key",
        "env":        "GITHUB_TOKEN",
        "url":        "https://github.com/settings/tokens",
        "prefix":     "github_pat_",
        "models":     ["openai/gpt-4o", "openai/gpt-4.1",
                       "meta-llama/Llama-3.3-70B-Instruct",
                       "deepseek/DeepSeek-R1", "mistral-ai/Mistral-Large-2411"],
        "default":    "openai/gpt-4o",
        "quota":      "Gratuit · 15 RPM · 150 req/jour · Fine-grained PAT",
        "vision":     True,
        "type":       "github_models",
        "base_url":   "https://models.github.ai/inference",
        "note":       "Token Fine-grained PAT avec permission models:read requis",
    },
}


def get_active_provider():
    return get_setting("ia_provider", list(IA_PROVIDERS.keys())[0])


def get_active_model():
    provider = get_active_provider()
    saved = get_setting("ia_model", "")
    if saved and saved in IA_PROVIDERS.get(provider, {}).get("models", []):
        return saved
    return IA_PROVIDERS.get(provider, {}).get("default", "")


def get_api_key_for_provider(provider_name):
    cfg = IA_PROVIDERS.get(provider_name, {})
    key = get_setting(cfg.get("key", ""), "")
    if not key:
        key = os.environ.get(cfg.get("env", ""), "")
    return key


def ia_call(prompt_text, image_bytes=None, json_mode=False):
    """
    Appel unifié vers le fournisseur IA actif.
    Supporte : Anthropic, Google, Groq, OpenRouter, Mistral, Cohere,
               Zhipu, Cerebras, HuggingFace, GitHub Models.
    """
    import urllib.error

    provider_name = get_active_provider()
    model         = get_active_model()
    api_key       = get_api_key_for_provider(provider_name)
    cfg           = IA_PROVIDERS.get(provider_name, {})
    ptype         = cfg.get("type", "")

    if not api_key:
        return None

    try:
        # ── 1. ANTHROPIC ──────────────────────────────────────────────────
        if ptype == "anthropic" and ANTHROPIC_OK:
            client = anthropic.Anthropic(api_key=api_key)
            content = []
            if image_bytes and cfg.get("vision"):
                content.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/jpeg",
                               "data": base64.b64encode(image_bytes).decode()}
                })
            content.append({"type": "text", "text": prompt_text})
            resp = client.messages.create(model=model, max_tokens=2000,
                                          messages=[{"role": "user", "content": content}])
            return resp.content[0].text

        # ── 2. GOOGLE (Gemini API) ────────────────────────────────────────
        elif ptype == "google":
            import urllib.request
            parts = []
            if image_bytes and cfg.get("vision"):
                parts.append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": base64.b64encode(image_bytes).decode()
                    }
                })
            parts.append({"text": prompt_text})
            payload = json.dumps({"contents": [{"parts": parts}]}).encode()
            url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
                   f"{model}:generateContent?key={api_key}")
            req = urllib.request.Request(url, data=payload,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read())
            return data["candidates"][0]["content"]["parts"][0]["text"]

        # ── 3. COHERE v2 ──────────────────────────────────────────────────
        elif ptype == "cohere":
            import urllib.request
            body = {
                "model":    model,
                "messages": [{"role": "user", "content": prompt_text}],
                "max_tokens": 2000,
                "temperature": 0.3,
            }
            if json_mode:
                body["response_format"] = {"type": "json_object"}
            payload = json.dumps(body).encode()
            req = urllib.request.Request(
                "https://api.cohere.com/v2/chat",
                data=payload,
                headers={
                    "Content-Type":  "application/json",
                    "Authorization": f"Bearer {api_key}",
                    "Accept":        "application/json",
                }
            )
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read())
            msg = data.get("message", {})
            content = msg.get("content", "")
            if isinstance(content, list) and content:
                return content[0].get("text", str(content))
            return str(content)

        # ── 4. HUGGING FACE ───────────────────────────────────────────────
        elif ptype == "huggingface":
            import urllib.request
            body = {
                "model":    model,
                "messages": [{"role": "user", "content": prompt_text}],
                "max_tokens": 1800,
                "temperature": 0.4,
                "stream": False,
            }
            payload = json.dumps(body).encode()
            url = "https://api-inference.huggingface.co/v1/chat/completions"
            req = urllib.request.Request(
                url, data=payload,
                headers={
                    "Content-Type":  "application/json",
                    "Authorization": f"Bearer {api_key}",
                }
            )
            with urllib.request.urlopen(req, timeout=90) as r:
                data = json.loads(r.read())
            if "choices" in data:
                return data["choices"][0]["message"]["content"]
            if isinstance(data, list):
                full = data[0].get("generated_text", "")
                if full.startswith(prompt_text):
                    return full[len(prompt_text):].strip()
                return full
            return str(data)

        # ── 5. OPENAI-COMPATIBLE (Groq, OpenRouter, Mistral, Cerebras, Zhipu) ──
        elif ptype == "openai_compat":
            import urllib.request
            base_url = cfg.get("base_url", "")
            messages = []
            if image_bytes and cfg.get("vision"):
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "image_url",
                         "image_url": {"url": f"data:image/jpeg;base64,"
                                              f"{base64.b64encode(image_bytes).decode()}"}},
                        {"type": "text", "text": prompt_text}
                    ]
                })
            else:
                messages.append({"role": "user", "content": prompt_text})
            body = {"model": model, "messages": messages,
                    "max_tokens": 2000, "temperature": 0.3}
            if json_mode:
                body["response_format"] = {"type": "json_object"}
            payload = json.dumps(body).encode()
            headers = {"Content-Type": "application/json",
                       "Authorization": f"Bearer {api_key}"}
            if "openrouter" in base_url:
                headers["HTTP-Referer"] = "https://apitrack.pro"
                headers["X-Title"] = "ApiTrack Pro"
            req = urllib.request.Request(f"{base_url}/chat/completions",
                                         data=payload, headers=headers)
            with urllib.request.urlopen(req, timeout=90) as r:
                data = json.loads(r.read())
            return data["choices"][0]["message"]["content"]

        # ── 6. GITHUB MODELS ──────────────────────────────────────────────
        elif ptype == "github_models":
            import urllib.request
            endpoint = "https://models.github.ai/inference/chat/completions"
            messages = []
            if image_bytes and cfg.get("vision"):
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "image_url",
                         "image_url": {
                             "url": f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode()}"
                         }},
                        {"type": "text", "text": prompt_text}
                    ]
                })
            else:
                messages.append({"role": "user", "content": prompt_text})
            body = {
                "model":       model,
                "messages":    messages,
                "max_tokens":  2000,
                "temperature": 0.3,
            }
            if json_mode and model.startswith("openai/"):
                body["response_format"] = {"type": "json_object"}
            payload = json.dumps(body).encode()
            headers = {
                "Content-Type":         "application/json",
                "Accept":               "application/vnd.github+json",
                "Authorization":        f"Bearer {api_key}",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            req = urllib.request.Request(endpoint, data=payload, headers=headers)
            with urllib.request.urlopen(req, timeout=90) as r:
                data = json.loads(r.read())
            return data["choices"][0]["message"]["content"]

        return None

    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode()[:400]
        except Exception:
            pass
        if e.code == 401:
            if ptype == "github_models":
                return (f"❌ GitHub Models — Authentification échouée (401).\n"
                        f"→ Utilisez un Fine-grained PAT (github_pat_...)\n"
                        f"→ Permission requise : Models → Read-only")
            return f"❌ Erreur {provider_name} : HTTP 401 — vérifiez votre clé API. {body}"
        elif e.code == 404:
            return f"❌ Erreur {provider_name} : HTTP 404 — endpoint ou modèle introuvable. {body}"
        elif e.code == 429:
            return f"❌ Erreur {provider_name} : Quota dépassé (429) — attendez quelques minutes. {body}"
        elif e.code == 422:
            return f"❌ Erreur {provider_name} : Paramètres invalides (422). {body}"
        else:
            return f"❌ Erreur {provider_name} : HTTP {e.code} {e.reason}. {body}"
    except Exception as e:
        return f"❌ Erreur {provider_name} : {e}"


def ia_call_json(prompt_text, image_bytes=None):
    """Appel IA avec retour JSON parsé."""
    result = ia_call(prompt_text, image_bytes, json_mode=True)
    if not result or result.startswith("❌"):
        return {"error": result or "Pas de réponse"}
    text = result.strip()
    if "```" in text:
        parts = text.split("```")
        for p in parts:
            if p.startswith("json"):
                text = p[4:].strip()
                break
            elif p.strip().startswith("{"):
                text = p.strip()
                break
    try:
        return json.loads(text)
    except Exception:
        import re
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except Exception:
                pass
        return {"error": f"JSON invalide : {text[:200]}"}


# ════════════════════════════════════════════════════════════════════════════
# FONCTIONS IA MÉTIER — utilisent ia_call() → tous fournisseurs supportés
# ════════════════════════════════════════════════════════════════════════════

def ia_analyser_morphometrie(aile, largeur, cubital, glossa, tomentum, pigmentation,
                              race_algo, confiance, image_bytes=None):
    """
    Analyse morphométrique via le fournisseur IA ACTIF (Gemma, Claude, Groq, etc.)
    Plus de dépendance forcée à Anthropic.
    """
    pname = get_active_provider()
    model = get_active_model()
    prompt = f"""Tu es expert apicole et morphométriste spécialisé dans la classification des races d'abeilles selon Ruttner (1988).

Voici les mesures morphométriques relevées sur une abeille :
- Longueur aile antérieure : {aile} mm
- Largeur aile : {largeur} mm
- Indice cubital : {cubital}
- Longueur glossa : {glossa} mm
- Tomentum (densité poils thorax 0-3) : {tomentum}
- Pigmentation scutellum : {pigmentation}

L'algorithme local a classifié : **{race_algo}** avec {confiance}% de confiance.
Modèle IA utilisé : {pname} / {model}

Effectue une analyse morphométrique complète en français selon ce plan :

## 1. Validation de la classification
- Confirme ou nuance la race {race_algo} selon les valeurs Ruttner 1988
- Ton niveau de confiance personnel (0-100%)
- Comparaison avec A.m. intermissa, sahariensis, ligustica, carnica

## 2. Scores de production (note /5 ⭐)
- 🍯 **Miel** : X/5 — justification (rendement kg/ruche/an estimé)
- 🌼 **Pollen** : X/5 — justification
- 🟤 **Propolis** : X/5 — justification
- 👑 **Gelée royale** : X/5 — justification (taux 10-HDA estimé)

## 3. Caractéristiques comportementales
Douceur, essaimage, économie hivernale, résistance varroa (2-3 lignes)

## 4. Recommandations stratégiques (3 actions concrètes)
- Action 1 :
- Action 2 :
- Action 3 :

## 5. Compatibilité avec l'environnement nord-africain (Algérie/Maroc/Tunisie)
Court paragraphe sur l'adaptation de cette race au climat méditerranéen/saharien.

Sois précis, concis, vocabulaire apicole professionnel."""
    return ia_call(prompt, image_bytes)


def ia_analyser_environnement(description_env, latitude=None, longitude=None,
                               saison="printemps", image_bytes=None):
    """
    Analyse environnementale mellifère via le fournisseur IA ACTIF.
    Fonctionne avec Gemma, Claude, Groq, Mistral, etc.
    """
    pname = get_active_provider()
    coords_str = f"Coordonnées : {latitude:.4f}°N, {longitude:.4f}°E" if latitude else ""
    prompt = f"""Tu es expert apicole senior, botaniste et écologue spécialisé dans l'analyse des environnements mellifères méditerranéens et nord-africains.

Zone à analyser :
{coords_str}
Saison : {saison}
Description : {description_env}
IA utilisée : {pname}

Effectue une analyse environnementale mellifère COMPLÈTE en français :

## 🌿 1. Flore identifiée et potentiel mellifère
Pour chaque espèce présente ou probable :
| Espèce | Source | Période | Qualité |
(Nectar / Pollen / Résine / Mixte — Excellente/Bonne/Moyenne/Faible)

## 📊 2. Scores de production (note /5 ⭐)
- 🍯 **MIEL** : X/5 — (type floral, saveur probable, rendement estimé kg/ruche/an, période)
- 🌼 **POLLEN** : X/5 — (diversité, richesse protéique %, couleurs)
- 🟤 **PROPOLIS** : X/5 — (espèces résineuses, qualité antibactérienne estimée)
- 👑 **GELÉE ROYALE** : X/5 — (disponibilité protéines+sucres, taux 10-HDA estimé)

## 🌡️ 3. Analyse microclimatique
- Exposition, altitude, humidité, vent, eau permanente
- Risques : pesticides, sécheresse, concurrence, prédateurs
- Points forts spécifiques à cette zone

## 🎯 4. Verdict global
- Potentiel global : [Faible/Modéré/Élevé/Exceptionnel]
- Indice mellifère : X/10
- Production principale recommandée : [Miel/Pollen/Propolis/Gelée royale/Mixte]
- Capacité de charge : X ruches/100 ha

## 🐝 5. Plan d'action (5 recommandations)
- Race d'abeille la plus adaptée à cette zone
- Mois optimal d'installation des ruches
- Période de récolte recommandée
- 3 améliorations pour maximiser la production

Données chiffrées obligatoires. Références botaniques locales nord-africaines si possible."""
    return ia_call(prompt, image_bytes)


def ia_analyser_zone_carto(nom_zone, flore, superficie, ndvi, potentiel, type_zone,
                            latitude=None, longitude=None):
    """
    Analyse JSON d'une zone cartographiée via le fournisseur IA ACTIF.
    Fonctionne avec Gemma, Claude, Groq, Mistral, etc.
    """
    coords_str = f"à {latitude:.4f}°N, {longitude:.4f}°E" if latitude else ""
    prompt = f"""Tu es expert apicole et écologue. Analyse cette zone mellifère cartographiée.

Zone : {nom_zone} {coords_str}
Type : {type_zone} | Flore : {flore} | Superficie : {superficie} ha
NDVI : {ndvi} (0=sol nu → 1=végétation dense) | Potentiel estimé : {potentiel}

Réponds UNIQUEMENT avec un objet JSON valide (pas de texte avant/après, pas de markdown) :
{{
  "diagnostic": {{"potentiel_global":"Élevé","indice_mellifere":8,"capacite_ruches":12,"saison_pic":"Avril-Juin"}},
  "scores": {{
    "miel":{{"note":4,"etoiles":"⭐⭐⭐⭐","detail":"Nectar abondant — jujubier dominant"}},
    "pollen":{{"note":3,"etoiles":"⭐⭐⭐","detail":"Diversité florale correcte"}},
    "propolis":{{"note":2,"etoiles":"⭐⭐","detail":"Quelques résines disponibles"}},
    "gelee_royale":{{"note":3,"etoiles":"⭐⭐⭐","detail":"Protéines disponibles printemps"}}
  }},
  "flore_identifiee":[
    {{"espece":"Ziziphus lotus","nectar":true,"pollen":true,"resine":false,"periode":"Avr-Juin","qualite":"Excellente"}}
  ],
  "risques":["Sécheresse estivale","Faible diversité florale en été"],
  "recommandations":["Installer 8-12 ruches en mars","Récolter miel en juin","Prévoir nourrissement été"],
  "race_adaptee":"intermissa",
  "resume":"Zone mellifère de haute valeur — potentiel miel jujubier exceptionnel au printemps."
}}"""
    return ia_call_json(prompt)


def afficher_resultat_ia(texte, titre="🤖 Analyse IA"):
    """Affiche le résultat IA dans un bloc stylisé avec badge fournisseur."""
    provider = get_active_provider()
    model    = get_active_model()
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#161B27,#1E2535);
                border:1px solid #C8820A;border-left:4px solid #C8820A;
                border-radius:10px;padding:20px;margin:16px 0;'>
        <div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:12px'>
            <div style='font-family:Playfair Display,serif;font-size:1rem;font-weight:600;color:#F5A623'>
                🤖 {titre}
            </div>
            <div style='font-size:.7rem;background:#1E2010;color:#A8B4CC;border:1px solid #2E3A52;
                        border-radius:20px;padding:2px 10px'>{provider} · {model}</div>
        </div>
        <div style='font-size:.88rem;color:#F0F4FF;line-height:1.7'>
    """, unsafe_allow_html=True)
    st.markdown(texte)
    st.markdown("</div></div>", unsafe_allow_html=True)


# Alias de compatibilité
def afficher_resultat_ia_zone(texte, titre="🤖 Analyse IA"):
    afficher_resultat_ia(texte, titre)


def widget_ia_selector():
    """
    Widget sélecteur de fournisseur IA.
    Retourne True si une clé est configurée pour le fournisseur actif.
    """
    provider_names = list(IA_PROVIDERS.keys())
    current = get_active_provider()
    idx = provider_names.index(current) if current in provider_names else 0

    with st.expander("🤖 Choisir le fournisseur IA", expanded=False):
        col1, col2 = st.columns([1.5, 1])
        with col1:
            sel = st.selectbox("Fournisseur IA gratuit", provider_names,
                                index=idx, key="ia_provider_select")
        cfg = IA_PROVIDERS[sel]
        with col2:
            models = cfg["models"]
            current_model = get_setting("ia_model", cfg["default"])
            idx_m = models.index(current_model) if current_model in models else 0
            sel_model = st.selectbox("Modèle", models, index=idx_m, key="ia_model_select")

        st.markdown(f"""
        <div style='font-size:.78rem;color:#A8B4CC;background:#0F1117;border-radius:6px;
                    padding:8px 12px;margin:6px 0;line-height:1.6'>
        📊 <b>Quota :</b> {cfg['quota']}<br>
        🖼️ <b>Vision (photo) :</b> {'✅ Oui' if cfg['vision'] else '❌ Texte seul'}<br>
        🔑 <b>Obtenir la clé :</b> <a href='{cfg['url']}' target='_blank'>{cfg['url']}</a>
        {f"<br>⚠️ <b>Note :</b> {cfg['note']}" if cfg.get('note') else ""}
        </div>
        """, unsafe_allow_html=True)

        if cfg.get("type") == "github_models":
            st.markdown("""
            <div style='background:#0D1A2A;border:1px solid #1A3A5C;border-radius:6px;
                        padding:10px 14px;font-size:.78rem;color:#F0F4FF;margin-bottom:8px'>
            <b>🐙 Comment créer le bon token GitHub :</b><br>
            1. Allez sur <a href='https://github.com/settings/personal-access-tokens/new' target='_blank'>
               github.com/settings/personal-access-tokens/new</a><br>
            2. Choisissez <b>"Fine-grained personal access token"</b><br>
            3. Dans <b>Permissions → Account permissions</b> → <b>Models</b> → <b>Read-only</b><br>
            4. Cliquez <b>Generate token</b> → copiez le token (<code>github_pat_...</code>)<br>
            5. <b>⚠️ Les tokens classiques <code>ghp_...</code> ne fonctionnent PAS</b>
            </div>
            """, unsafe_allow_html=True)

        api_key = get_api_key_for_provider(sel)
        new_key = st.text_input(
            f"Clé API {sel.split('(')[0].strip()}",
            value=api_key, type="password",
            placeholder=cfg.get("prefix", "") + "...",
            key=f"key_input_{sel}"
        )

        col_s1, col_s2 = st.columns(2)
        if col_s1.button("💾 Sauvegarder & Activer", key="save_ia_provider"):
            conn = get_db()
            if new_key:
                conn.execute("INSERT OR REPLACE INTO settings VALUES (?,?)",
                             (cfg["key"], new_key))
            conn.execute("INSERT OR REPLACE INTO settings VALUES ('ia_provider',?)", (sel,))
            conn.execute("INSERT OR REPLACE INTO settings VALUES ('ia_model',?)", (sel_model,))
            conn.commit()
            conn.close()
            log_action("Fournisseur IA changé", f"{sel} / {sel_model}")
            st.success(f"✅ {sel} activé — modèle {sel_model}")
            st.rerun()
        if col_s2.button("🔬 Tester la connexion", key="test_ia_provider"):
            conn = get_db()
            if new_key:
                conn.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (cfg["key"], new_key))
            conn.execute("INSERT OR REPLACE INTO settings VALUES ('ia_provider',?)", (sel,))
            conn.execute("INSERT OR REPLACE INTO settings VALUES ('ia_model',?)", (sel_model,))
            conn.commit()
            conn.close()
            with st.spinner("Test en cours..."):
                r = ia_call("Réponds uniquement : 'ApiTrack Pro IA OK' en français.")
            if r and "OK" in r:
                st.success(f"✅ {r.strip()}")
            elif r:
                st.warning(f"Réponse : {r[:200]}")
            else:
                st.error("❌ Pas de réponse. Vérifiez la clé API.")

    api_key = get_api_key_for_provider(get_active_provider())
    prov    = get_active_provider()
    mod     = get_active_model()
    if api_key:
        st.markdown(f"<div style='font-size:.75rem;color:#6EE7B7;margin-bottom:8px'>"
                    f"✅ IA active : <b>{prov}</b> · <code>{mod}</code></div>",
                    unsafe_allow_html=True)
        return True
    else:
        st.warning(f"⚠️ Configurez une clé API pour **{prov}** (voir le sélecteur ci-dessus).")
        return False


# Alias de compatibilité
def widget_cle_api():
    return widget_ia_selector()


# ════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════════════
def sidebar():
    with st.sidebar:
        st.markdown("""
        <div style='padding:8px 0 16px;border-bottom:1px solid #3d2a0e;margin-bottom:12px'>
            <div style='font-size:1.6rem;margin-bottom:4px'>🐝</div>
            <div style='font-family:Playfair Display,serif;color:#F5A623;font-size:1.1rem;font-weight:600'>ApiTrack Pro</div>
            <div style='font-size:.65rem;color:#8899BB;text-transform:uppercase;letter-spacing:.1em'>Gestion Apicole</div>
        </div>
        """, unsafe_allow_html=True)

        rucher_nom = get_setting("rucher_nom", "Mon Rucher")
        st.markdown(f"<div style='font-size:.75rem;color:#6B7A99;margin-bottom:12px'>📍 {rucher_nom}</div>", unsafe_allow_html=True)

        pages = {
            "🏠 Dashboard": "dashboard",
            "🐝 Mes ruches": "ruches",
            "🔍 Inspections": "inspections",
            "💊 Traitements": "traitements",
            "🍯 Productions": "productions",
            "── ANALYSE IA ──": None,
            "🧬 Morphométrie IA": "morpho",
            "🔬 Maladies (Vision IA)": "maladies_ia",
            "🌿 Environnement IA": "carto",
            "── OUTILS AVANCÉS ──": None,
            "🚁 Transhumance IA": "transhumance",
            "🧫 Bourse aux Mâles": "bourse_males",
            "🌳 Généalogie Prédictive": "genealogie",
            "🎤 Assistant Vocal": "assistant_vocal",
            "── GESTION ──": None,
            "☀️ Météo & Miellée": "meteo",
            "📊 Génétique": "genetique",
            "🌸 Flore mellifère": "flore",
            "⚠️ Alertes": "alertes",
            "📋 Journal": "journal",
            "⚙️ Administration": "admin",
        }

        if "page" not in st.session_state:
            st.session_state.page = "dashboard"

        for label, key in pages.items():
            if key is None:
                st.sidebar.markdown(
                    f"<div style='font-size:.65rem;color:#6B7A99;text-transform:uppercase;"
                    f"letter-spacing:.1em;padding:10px 4px 2px;font-weight:600'>"
                    f"{label.replace('── ','').replace(' ──','')}</div>",
                    unsafe_allow_html=True
                )
                continue
            if st.sidebar.button(label, key=f"nav_{key}", use_container_width=True):
                st.session_state.page = key
                st.rerun()

        st.sidebar.markdown("<hr style='border-color:#2E3A52;margin:12px 0'>", unsafe_allow_html=True)
        st.sidebar.markdown(f"<div style='font-size:.75rem;color:#6B7A99'>👤 {st.session_state.get('username','admin')}</div>", unsafe_allow_html=True)
        if st.sidebar.button("🚪 Déconnexion", use_container_width=True):
            log_action("Déconnexion", f"Utilisateur {st.session_state.get('username')} déconnecté")
            st.session_state.logged_in = False
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# PAGE : DASHBOARD
# ════════════════════════════════════════════════════════════════════════════
def page_dashboard():
    st.markdown("## 🏠 Tableau de bord")
    rucher = get_setting("rucher_nom", "Mon Rucher")
    localisation = get_setting("localisation", "")
    st.markdown(f"<p style='color:#A8B4CC;margin-top:-10px'>Saison printanière 2025 · {rucher} · {localisation}</p>", unsafe_allow_html=True)

    conn = get_db()
    nb_ruches = conn.execute("SELECT COUNT(*) FROM ruches WHERE statut='actif'").fetchone()[0]
    total_miel = conn.execute("SELECT COALESCE(SUM(quantite_kg),0) FROM recoltes WHERE type_produit='miel'").fetchone()[0]
    nb_insp = conn.execute("SELECT COUNT(*) FROM inspections WHERE date_inspection >= date('now','-30 days')").fetchone()[0]
    critiques = conn.execute("SELECT COUNT(*) FROM inspections WHERE varroa_pct >= 3.0 AND date_inspection >= date('now','-7 days')").fetchone()[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🐝 Ruches actives", nb_ruches, "+3 ce mois")
    col2.metric("🍯 Miel récolté (kg)", f"{total_miel:.0f}", "+18% vs 2024")
    col3.metric("🔍 Inspections (30j)", nb_insp, "Cadence correcte")
    col4.metric("⚠️ Varroa critique", critiques, "Intervention requise" if critiques else "RAS", delta_color="inverse")

    st.markdown("<br>", unsafe_allow_html=True)
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("### 📈 Production mensuelle (kg)")
        df_prod = pd.read_sql("""
            SELECT strftime('%Y-%m', date_recolte) as mois,
                   type_produit,
                   SUM(quantite_kg) as total
            FROM recoltes
            GROUP BY mois, type_produit
            ORDER BY mois
        """, conn)
        if not df_prod.empty:
            fig = px.bar(df_prod, x="mois", y="total", color="type_produit",
                         color_discrete_map={"miel":"#C8820A","pollen":"#F5C842","gelée royale":"#8B7355"},
                         template="plotly_white")
            fig.update_layout(height=280, margin=dict(t=10,b=10,l=0,r=0),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              legend_title_text="", showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune donnée de production.")

    with col_b:
        st.markdown("### 🐝 État des ruches")
        df_ruches = pd.read_sql("""
            SELECT r.nom, r.race,
                   COALESCE(i.varroa_pct, 0) as varroa,
                   COALESCE(i.nb_cadres, 0) as cadres,
                   COALESCE(i.poids_kg, 0) as poids
            FROM ruches r
            LEFT JOIN inspections i ON i.ruche_id = r.id
            AND i.date_inspection = (SELECT MAX(ii.date_inspection) FROM inspections ii WHERE ii.ruche_id = r.id)
            WHERE r.statut='actif'
            ORDER BY varroa DESC
            LIMIT 6
        """, conn)
        if not df_ruches.empty:
            df_ruches["Statut"] = df_ruches["varroa"].apply(status_badge)
            df_ruches.columns = ["Ruche","Race","Varroa%","Cadres","Poids(kg)","Statut"]
            st.dataframe(df_ruches, use_container_width=True, hide_index=True)

    st.markdown("### ⚠️ Alertes actives")
    df_alertes = pd.read_sql("""
        SELECT r.nom, i.varroa_pct, i.date_inspection, i.notes
        FROM inspections i
        JOIN ruches r ON r.id = i.ruche_id
        WHERE i.varroa_pct >= 2.0
        AND i.date_inspection >= date('now','-7 days')
        ORDER BY i.varroa_pct DESC
    """, conn)
    conn.close()

    if not df_alertes.empty:
        for _, row in df_alertes.iterrows():
            lvl = "🔴" if row["varroa_pct"] >= 3.0 else "🟡"
            seuil = "CRITIQUE (>3%)" if row["varroa_pct"] >= 3.0 else "ATTENTION (>2%)"
            st.warning(f"{lvl} **{row['nom']}** — Varroa **{row['varroa_pct']}%** — {seuil} · {row['date_inspection']}")
    else:
        st.success("✅ Aucune alerte varroa critique en cours.")


# ════════════════════════════════════════════════════════════════════════════
# PAGE : GESTION DES RUCHES
# ════════════════════════════════════════════════════════════════════════════
def page_ruches():
    st.markdown("## 🐝 Gestion des ruches")

    conn = get_db()
    df = pd.read_sql("""
        SELECT r.id, r.nom, r.race, r.date_installation, r.localisation, r.statut,
               COALESCE(i.varroa_pct, '-') as derniere_varroa,
               COALESCE(i.nb_cadres, '-') as cadres,
               COALESCE(i.poids_kg, '-') as poids_kg,
               i.date_inspection as derniere_inspection
        FROM ruches r
        LEFT JOIN inspections i ON i.ruche_id = r.id
        AND i.date_inspection = (SELECT MAX(ii.date_inspection) FROM inspections ii WHERE ii.ruche_id = r.id)
        ORDER BY r.id
    """, conn)

    tab1, tab2 = st.tabs(["📋 Liste des ruches", "➕ Ajouter une ruche"])

    with tab1:
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Exporter CSV", csv, "ruches.csv", "text/csv")

        st.markdown("### 🗑️ Supprimer une ruche")
        ruche_ids = conn.execute("SELECT id, nom FROM ruches").fetchall()
        if ruche_ids:
            options = {f"R{r[0]:02d} — {r[1]}": r[0] for r in ruche_ids}
            selected = st.selectbox("Choisir la ruche à supprimer", options.keys())
            if st.button("⚠️ Supprimer définitivement", type="secondary"):
                rid = options[selected]
                conn.execute("DELETE FROM ruches WHERE id=?", (rid,))
                conn.commit()
                log_action("Suppression ruche", f"Ruche {selected} supprimée")
                st.success(f"Ruche {selected} supprimée.")
                st.rerun()

    with tab2:
        with st.form("add_ruche"):
            st.markdown("**Nouvelle ruche**")
            col1, col2 = st.columns(2)
            nom = col1.text_input("Nom / Reine*")
            race = col2.selectbox("Race", ["intermissa", "sahariensis", "ligustica", "carnica", "hybride"])
            date_inst = col1.date_input("Date d'installation", datetime.date.today())
            localisation = col2.text_input("Localisation")
            col3, col4 = st.columns(2)
            lat = col3.number_input("Latitude", value=34.88, format="%.4f")
            lon = col4.number_input("Longitude", value=1.32, format="%.4f")
            notes = st.text_area("Notes")
            submitted = st.form_submit_button("✅ Ajouter la ruche")

        if submitted and nom:
            conn.execute("""
                INSERT INTO ruches (nom, race, date_installation, localisation, latitude, longitude, notes)
                VALUES (?,?,?,?,?,?,?)
            """, (nom, race, str(date_inst), localisation, lat, lon, notes))
            conn.commit()
            log_action("Ajout ruche", f"Ruche '{nom}' ({race}) ajoutée")
            st.success(f"✅ Ruche '{nom}' ajoutée avec succès.")
            st.rerun()

    conn.close()


# ════════════════════════════════════════════════════════════════════════════
# PAGE : INSPECTIONS
# ════════════════════════════════════════════════════════════════════════════
def page_inspections():
    st.markdown("## 🔍 Inspections")
    conn = get_db()

    tab1, tab2 = st.tabs(["📋 Historique", "➕ Nouvelle inspection"])

    with tab1:
        df = pd.read_sql("""
            SELECT i.id, r.nom as ruche, i.date_inspection, i.poids_kg, i.nb_cadres,
                   i.varroa_pct, i.reine_vue, i.comportement, i.notes
            FROM inspections i
            JOIN ruches r ON r.id = i.ruche_id
            ORDER BY i.date_inspection DESC
        """, conn)
        if not df.empty:
            df["reine_vue"] = df["reine_vue"].apply(lambda x: "✓" if x else "✗")
            df["varroa_pct"] = df["varroa_pct"].apply(lambda x: f"{x}%" if x else "-")
            st.dataframe(df, use_container_width=True, hide_index=True)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Exporter CSV", csv, "inspections.csv", "text/csv")

        st.markdown("### 📈 Évolution du varroa")
        df_v = pd.read_sql("""
            SELECT r.nom, i.date_inspection, i.varroa_pct
            FROM inspections i JOIN ruches r ON r.id=i.ruche_id
            WHERE i.varroa_pct IS NOT NULL
            ORDER BY i.date_inspection
        """, conn)
        if not df_v.empty:
            fig = px.line(df_v, x="date_inspection", y="varroa_pct", color="nom",
                          template="plotly_white", markers=True)
            fig.add_hline(y=2.0, line_dash="dash", line_color="orange", annotation_text="Seuil alerte (2%)")
            fig.add_hline(y=3.0, line_dash="dash", line_color="red", annotation_text="Seuil critique (3%)")
            fig.update_layout(height=300, margin=dict(t=10,b=10,l=0,r=0),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        ruches = conn.execute("SELECT id, nom FROM ruches WHERE statut='actif'").fetchall()
        opts = {r[1]: r[0] for r in ruches}

        with st.form("add_inspection"):
            col1, col2 = st.columns(2)
            ruche_sel = col1.selectbox("Ruche*", opts.keys())
            date_insp = col2.date_input("Date", datetime.date.today())
            col3, col4, col5 = st.columns(3)
            poids = col3.number_input("Poids (kg)", 0.0, 80.0, 25.0, 0.1)
            cadres = col4.number_input("Nb cadres", 0, 20, 10)
            varroa = col5.number_input("Varroa (%)", 0.0, 20.0, 1.0, 0.1)
            col6, col7 = st.columns(2)
            reine = col6.checkbox("Reine vue", value=True)
            comportement = col7.selectbox("Comportement", ["calme", "nerveuse", "agressive", "très calme"])
            notes = st.text_area("Notes / Observations")
            submitted = st.form_submit_button("✅ Enregistrer l'inspection")

        if submitted:
            rid = opts[ruche_sel]
            conn.execute("""
                INSERT INTO inspections (ruche_id,date_inspection,poids_kg,nb_cadres,varroa_pct,reine_vue,comportement,notes)
                VALUES (?,?,?,?,?,?,?,?)
            """, (rid, str(date_insp), poids, cadres, varroa, int(reine), comportement, notes))
            conn.commit()
            log_action("Inspection enregistrée", f"Ruche {ruche_sel} — varroa {varroa}%")
            if varroa >= 3.0:
                st.error(f"⚠️ ALERTE CRITIQUE : Varroa {varroa}% sur {ruche_sel} — Traitement immédiat requis !")
            elif varroa >= 2.0:
                st.warning(f"⚠️ Attention : Varroa {varroa}% sur {ruche_sel} — Surveillance renforcée.")
            else:
                st.success("✅ Inspection enregistrée.")
            st.rerun()

    conn.close()


# ════════════════════════════════════════════════════════════════════════════
# PAGE : TRAITEMENTS
# ════════════════════════════════════════════════════════════════════════════
def page_traitements():
    st.markdown("## 💊 Traitements vétérinaires")
    conn = get_db()

    tab1, tab2 = st.tabs(["📋 En cours & historique", "➕ Nouveau traitement"])

    with tab1:
        df = pd.read_sql("""
            SELECT t.id, r.nom as ruche, t.date_debut, t.date_fin, t.produit,
                   t.pathologie, t.dose, t.duree_jours, t.statut, t.notes
            FROM traitements t JOIN ruches r ON r.id=t.ruche_id
            ORDER BY t.date_debut DESC
        """, conn)
        if not df.empty:
            for _, row in df.iterrows():
                if row["statut"] == "en_cours":
                    debut = datetime.date.fromisoformat(row["date_debut"])
                    jours_ecoulés = (datetime.date.today() - debut).days
                    duree = row["duree_jours"] or 21
                    progress = min(jours_ecoulés / duree, 1.0)
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        col1.markdown(f"**{row['ruche']}** — {row['produit']} ({row['pathologie']}) · Dose : {row['dose']}")
                        col1.progress(progress, text=f"Jour {jours_ecoulés}/{duree}")
                        col2.markdown(f"<span class='badge-warn'>En cours</span>", unsafe_allow_html=True)
                    st.markdown("---")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Aucun traitement enregistré.")

    with tab2:
        ruches = conn.execute("SELECT id, nom FROM ruches WHERE statut='actif'").fetchall()
        opts = {r[1]: r[0] for r in ruches}
        with st.form("add_traitement"):
            col1, col2 = st.columns(2)
            ruche_sel = col1.selectbox("Ruche", opts.keys())
            produit = col2.text_input("Produit", placeholder="Acide oxalique")
            col3, col4 = st.columns(2)
            pathologie = col3.selectbox("Pathologie", ["Varroa", "Loque américaine", "Nosémose", "Foulbrood", "Autre"])
            dose = col4.text_input("Dose", placeholder="50 ml")
            col5, col6 = st.columns(2)
            date_debut = col5.date_input("Date début", datetime.date.today())
            duree = col6.number_input("Durée (jours)", 1, 90, 21)
            notes = st.text_area("Notes")
            submitted = st.form_submit_button("✅ Enregistrer le traitement")

        if submitted and produit:
            date_fin = date_debut + datetime.timedelta(days=duree)
            conn.execute("""
                INSERT INTO traitements (ruche_id,date_debut,date_fin,produit,pathologie,dose,duree_jours,statut,notes)
                VALUES (?,?,?,?,?,?,?,'en_cours',?)
            """, (opts[ruche_sel], str(date_debut), str(date_fin), produit, pathologie, dose, duree, notes))
            conn.commit()
            log_action("Traitement débuté", f"Ruche {ruche_sel} — {produit} ({pathologie})")
            st.success("✅ Traitement enregistré.")
            st.rerun()

    conn.close()


# ════════════════════════════════════════════════════════════════════════════
# PAGE : PRODUCTIONS
# ════════════════════════════════════════════════════════════════════════════
def page_productions():
    st.markdown("## 🍯 Productions")
    conn = get_db()

    total_miel = conn.execute("SELECT COALESCE(SUM(quantite_kg),0) FROM recoltes WHERE type_produit='miel'").fetchone()[0]
    total_pollen = conn.execute("SELECT COALESCE(SUM(quantite_kg),0) FROM recoltes WHERE type_produit='pollen'").fetchone()[0]
    total_gr = conn.execute("SELECT COALESCE(SUM(quantite_kg),0) FROM recoltes WHERE type_produit='gelée royale'").fetchone()[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("🍯 Miel total (kg)", f"{total_miel:.1f}", "Humidité moy. 17.2%")
    col2.metric("🌼 Pollen (kg)", f"{total_pollen:.1f}", "Qualité A")
    col3.metric("👑 Gelée royale (kg)", f"{total_gr:.2f}", "10-HDA 2.1%")

    tab1, tab2, tab3 = st.tabs(["🍯 Récoltes", "📊 Graphiques", "➕ Nouvelle récolte"])

    with tab1:
        df = pd.read_sql("""
            SELECT rec.id, r.nom as ruche, rec.date_recolte, rec.type_produit,
                   rec.quantite_kg, rec.humidite_pct, rec.ph, rec.hda_pct, rec.qualite, rec.notes
            FROM recoltes rec JOIN ruches r ON r.id=rec.ruche_id
            ORDER BY rec.date_recolte DESC
        """, conn)
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Exporter CSV", csv, "recoltes.csv", "text/csv")

    with tab2:
        df_g = pd.read_sql("""
            SELECT strftime('%Y-%m', date_recolte) as mois, type_produit, SUM(quantite_kg) as total
            FROM recoltes GROUP BY mois, type_produit ORDER BY mois
        """, conn)
        if not df_g.empty:
            fig = px.area(df_g, x="mois", y="total", color="type_produit",
                          color_discrete_map={"miel":"#C8820A","pollen":"#F5C842","gelée royale":"#8B7355"},
                          template="plotly_white")
            fig.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              margin=dict(t=10,b=10,l=0,r=0))
            st.plotly_chart(fig, use_container_width=True)

        df_r = pd.read_sql("""
            SELECT r.nom, SUM(rec.quantite_kg) as total FROM recoltes rec
            JOIN ruches r ON r.id=rec.ruche_id WHERE rec.type_produit='miel'
            GROUP BY r.nom ORDER BY total DESC
        """, conn)
        if not df_r.empty:
            fig2 = px.bar(df_r, x="nom", y="total", template="plotly_white",
                          color_discrete_sequence=["#C8820A"])
            fig2.update_layout(height=280, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                               margin=dict(t=10,b=10,l=0,r=0), title="Production de miel par ruche (kg)")
            st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        ruches = conn.execute("SELECT id, nom FROM ruches WHERE statut='actif'").fetchall()
        opts = {r[1]: r[0] for r in ruches}
        with st.form("add_recolte"):
            col1, col2, col3 = st.columns(3)
            ruche_sel = col1.selectbox("Ruche", opts.keys())
            type_prod = col2.selectbox("Produit", ["miel", "pollen", "gelée royale", "propolis"])
            date_rec = col3.date_input("Date récolte", datetime.date.today())
            col4, col5 = st.columns(2)
            quantite = col4.number_input("Quantité (kg)", 0.0, 500.0, 10.0, 0.1)
            qualite = col5.selectbox("Qualité", ["A+", "A", "B", "C"])
            col6, col7, col8 = st.columns(3)
            humidite = col6.number_input("Humidité (%)", 0.0, 30.0, 17.5, 0.1)
            ph = col7.number_input("pH", 2.0, 7.0, 3.9, 0.1)
            hda = col8.number_input("10-HDA (%)", 0.0, 5.0, 0.0, 0.1)
            notes = st.text_area("Notes")
            submitted = st.form_submit_button("✅ Enregistrer la récolte")

        if submitted:
            conn.execute("""
                INSERT INTO recoltes (ruche_id,date_recolte,type_produit,quantite_kg,humidite_pct,ph,hda_pct,qualite,notes)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (opts[ruche_sel], str(date_rec), type_prod, quantite,
                  humidite if humidite > 0 else None,
                  ph if ph > 0 else None,
                  hda if hda > 0 else None, qualite, notes))
            conn.commit()
            log_action("Récolte enregistrée", f"{quantite} kg de {type_prod} — ruche {ruche_sel}")
            st.success(f"✅ {quantite} kg de {type_prod} enregistrés.")
            st.rerun()

    conn.close()


# ════════════════════════════════════════════════════════════════════════════
# PAGE : MORPHOMÉTRIE IA
# ════════════════════════════════════════════════════════════════════════════
RUTTNER_REF = {
    "intermissa":   {"aile": (8.9, 9.4), "cubital": (2.0, 2.8), "glossa": (5.8, 6.3)},
    "sahariensis":  {"aile": (9.0, 9.5), "cubital": (1.9, 2.5), "glossa": (6.0, 6.5)},
    "ligustica":    {"aile": (9.2, 9.8), "cubital": (2.5, 3.2), "glossa": (6.3, 6.8)},
    "carnica":      {"aile": (9.3, 9.9), "cubital": (2.2, 3.0), "glossa": (6.4, 7.0)},
    "hybride":      {"aile": (8.5, 9.5), "cubital": (1.8, 3.5), "glossa": (5.5, 6.8)},
}

def classify_race(aile, cubital, glossa):
    scores = {}
    for race, ref in RUTTNER_REF.items():
        s = 0
        for val, (lo, hi) in [(aile, ref["aile"]), (cubital, ref["cubital"]), (glossa, ref["glossa"])]:
            if val is None:
                s += 0.5
            elif lo <= val <= hi:
                s += 1.0
            else:
                dist = min(abs(val - lo), abs(val - hi))
                s += max(0, 1.0 - dist * 0.5)
        scores[race] = s
    total = sum(scores.values()) or 1
    return {r: round(v / total * 100) for r, v in scores.items()}


def page_morpho():
    st.markdown("## 🧬 Morphométrie IA — Classification raciale")
    st.markdown("<p style='color:#A8B4CC'>Mesures morphométriques + analyse IA multi-fournisseurs (Ruttner 1988)</p>",
                unsafe_allow_html=True)

    ia_active = widget_cle_api()

    conn = get_db()
    ruches = conn.execute("SELECT id, nom FROM ruches WHERE statut='actif'").fetchall()
    opts = {r[1]: r[0] for r in ruches}

    specialisations = {
        "intermissa": ["Production de miel", "Propolis abondante", "Résistance chaleur", "Adaptation locale"],
        "sahariensis": ["Butinage intense", "Résistance extrême chaleur", "Économie eau"],
        "ligustica": ["Production intensive miel", "Faible propolis", "Docilité"],
        "carnica": ["Économie hivernale", "Butinage précoce", "Faible essaimage"],
        "hybride": ["Variable selon parentaux", "Évaluation approfondie requise"],
    }

    tab1, tab2 = st.tabs(["🔬 Analyse + IA", "📜 Historique"])

    with tab1:
        col1, col2 = st.columns([1, 1.2])

        with col1:
            st.markdown("### 📐 Mesures morphométriques")
            ruche_sel = st.selectbox("Ruche analysée", opts.keys())
            aile    = st.number_input("Longueur aile antérieure (mm)", 7.0, 12.0, 9.2, 0.1)
            largeur = st.number_input("Largeur aile (mm)", 2.0, 5.0, 3.1, 0.1)
            cubital = st.number_input("Indice cubital", 1.0, 5.0, 2.3, 0.1,
                                      help="Rapport distances nervures cubitales a/b ÷ b/c")
            glossa  = st.number_input("Longueur glossa (mm)", 4.0, 8.0, 6.1, 0.1)
            tomentum    = st.slider("Tomentum (densité poils thorax 0–3)", 0, 3, 2)
            pigmentation = st.selectbox("Pigmentation scutellum",
                                        ["Noir", "Brun foncé", "Brun clair", "Jaune"])
            notes = st.text_area("Notes / Observations")

            st.markdown("### 📷 Photo macro (optionnel)")
            st.markdown("<small style='color:#A8B4CC'>Photo macro de l'aile ou de l'abeille (si le fournisseur IA supporte la vision)</small>",
                        unsafe_allow_html=True)
            img_file = st.file_uploader("Photo macro abeille", type=["jpg","jpeg","png","webp"],
                                        key="morpho_img")

            col_btn1, col_btn2 = st.columns(2)
            btn_local  = col_btn1.button("🔬 Classifier (local)", use_container_width=True)
            btn_ia     = col_btn2.button("🤖 Analyser avec l'IA", use_container_width=True,
                                          disabled=not ia_active)

        with col2:
            st.markdown("### 📊 Résultats — Classification Ruttner 1988")
            scores     = classify_race(aile, cubital, glossa)
            race_prob  = max(scores, key=scores.get)
            confiance  = scores[race_prob]

            st.markdown(f"""
            <div style='background:#0F1117;border:1px solid #C8820A;border-left:4px solid #C8820A;
                        border-radius:8px;padding:12px 16px;margin-bottom:12px'>
                <div style='font-size:.95rem;font-weight:600;color:#F0F4FF'>
                    Race probable : <span style='color:#F5A623'>Apis mellifera {race_prob}</span>
                </div>
                <div style='font-size:.78rem;color:#A8B4CC;margin-top:3px'>
                    Algorithme local · Confiance {confiance}% ·
                    aile={aile}mm / cubital={cubital} / glossa={glossa}mm
                </div>
            </div>
            """, unsafe_allow_html=True)

            couleurs = {"intermissa":"#C8820A","sahariensis":"#8B7355",
                        "ligustica":"#2E7D32","carnica":"#1565C0","hybride":"#888"}
            fig = go.Figure()
            for race, pct in sorted(scores.items(), key=lambda x: -x[1]):
                fig.add_trace(go.Bar(y=[race], x=[pct], orientation="h",
                                     marker_color=couleurs.get(race,"#ccc"),
                                     text=f"{pct}%", textposition="auto", name=race))
            fig.update_layout(height=220, showlegend=False, template="plotly_white",
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              margin=dict(t=0,b=0,l=0,r=10),
                              xaxis=dict(range=[0,100], title="Confiance (%)"))
            st.plotly_chart(fig, use_container_width=True)

            prod_scores = {
                "intermissa":   {"miel":4,"pollen":3,"propolis":5,"gr":2},
                "sahariensis":  {"miel":3,"pollen":4,"propolis":3,"gr":2},
                "ligustica":    {"miel":5,"pollen":3,"propolis":1,"gr":3},
                "carnica":      {"miel":4,"pollen":4,"propolis":2,"gr":3},
                "hybride":      {"miel":3,"pollen":3,"propolis":3,"gr":2},
            }
            ps = prod_scores.get(race_prob, {"miel":3,"pollen":3,"propolis":3,"gr":2})
            st.markdown("**Potentiel de production estimé (algorithme local) :**")
            cols_s = st.columns(4)
            for col, (label, icon, key) in zip(cols_s, [
                ("Miel","🍯","miel"), ("Pollen","🌼","pollen"),
                ("Propolis","🟤","propolis"), ("Gelée R.","👑","gr")
            ]):
                note = ps[key]
                etoiles = "⭐" * note + "☆" * (5 - note)
                col.markdown(f"<div style='text-align:center;font-size:.75rem;color:#A8B4CC'>{icon} {label}</div>"
                             f"<div style='text-align:center;font-size:.85rem'>{etoiles}</div>",
                             unsafe_allow_html=True)

        if btn_local:
            rid = opts[ruche_sel]
            conf_json = json.dumps([{"race": r, "confiance": p} for r, p in scores.items()])
            spec = " / ".join(specialisations.get(race_prob, []))
            conn.execute("""
                INSERT INTO morph_analyses
                (ruche_id,date_analyse,longueur_aile_mm,largeur_aile_mm,indice_cubital,
                 glossa_mm,tomentum,pigmentation,race_probable,confiance_json,specialisation,notes)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (rid, str(datetime.date.today()), aile, largeur, cubital,
                  glossa, tomentum, pigmentation, race_prob, conf_json, spec, notes))
            conn.commit()
            log_action("Morphométrie classifiée (local)", f"Ruche {ruche_sel} — {race_prob} {confiance}%")
            result_json = {
                "id_analyse": datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
                "date": datetime.datetime.now().isoformat() + "Z",
                "ruche": ruche_sel,
                "morphometrie": {
                    "mesures": {"longueur_aile_mm": aile, "largeur_aile_mm": largeur,
                                "indice_cubital": cubital, "glossa_mm": glossa,
                                "tomentum": tomentum, "pigmentation": pigmentation},
                    "classification_raciale": [{"race": r, "confiance": p} for r, p in scores.items()],
                    "race_probable": race_prob, "specialisation": spec,
                }
            }
            st.success(f"✅ Classification locale sauvegardée : **{race_prob}** ({confiance}%)")
            st.download_button("⬇️ Télécharger JSON", json.dumps(result_json, indent=2, ensure_ascii=False),
                               f"morpho_{datetime.date.today()}.json", "application/json")

        if btn_ia:
            img_bytes = img_file.read() if img_file else None
            prov = get_active_provider()
            with st.spinner(f"🤖 {prov} analyse les données morphométriques..."):
                resultat_ia = ia_analyser_morphometrie(
                    aile, largeur, cubital, glossa, tomentum, pigmentation,
                    race_prob, confiance, img_bytes
                )
            if resultat_ia and not resultat_ia.startswith("❌"):
                afficher_resultat_ia(resultat_ia, "Analyse morphométrique approfondie — IA")
                log_action("Morphométrie IA", f"Ruche {ruche_sel} — analyse {prov} effectuée")
                rid = opts[ruche_sel]
                conf_json = json.dumps([{"race": r, "confiance": p} for r, p in scores.items()])
                spec = " / ".join(specialisations.get(race_prob, []))
                conn.execute("""
                    INSERT INTO morph_analyses
                    (ruche_id,date_analyse,longueur_aile_mm,largeur_aile_mm,indice_cubital,
                     glossa_mm,tomentum,pigmentation,race_probable,confiance_json,specialisation,notes)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                """, (rid, str(datetime.date.today()), aile, largeur, cubital,
                      glossa, tomentum, pigmentation, race_prob, conf_json, spec,
                      f"[IA] {notes}"))
                conn.commit()
            elif resultat_ia:
                st.error(resultat_ia)
            else:
                st.warning("⚠️ IA non disponible. Configurez votre clé API via le sélecteur ci-dessus.")

    with tab2:
        df = pd.read_sql("""
            SELECT m.id, r.nom as ruche, m.date_analyse, m.longueur_aile_mm,
                   m.indice_cubital, m.glossa_mm, m.race_probable, m.specialisation, m.notes
            FROM morph_analyses m JOIN ruches r ON r.id=m.ruche_id
            ORDER BY m.date_analyse DESC
        """, conn)
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Exporter CSV", csv, "morphometrie.csv", "text/csv")
        else:
            st.info("Aucune analyse morphométrique enregistrée.")

    conn.close()


# ════════════════════════════════════════════════════════════════════════════
# PAGE : CARTOGRAPHIE
# ════════════════════════════════════════════════════════════════════════════
def page_carto():
    st.markdown("## 🗺️ Cartographie — Zones mellifères + Analyse IA")

    ia_active = widget_cle_api()

    conn = get_db()
    tab1, tab2, tab3 = st.tabs(["🗺️ Carte & Zones", "🌿 Analyse environnement IA", "➕ Ajouter une zone"])

    with tab1:
        df_zones  = pd.read_sql("SELECT * FROM zones", conn)
        df_ruches = pd.read_sql("SELECT * FROM ruches WHERE statut='actif' AND latitude IS NOT NULL", conn)

        if FOLIUM_OK:
            center_lat = float(df_ruches["latitude"].mean()) if not df_ruches.empty else 34.88
            center_lon = float(df_ruches["longitude"].mean()) if not df_ruches.empty else 1.32
            m = folium.Map(location=[center_lat, center_lon], zoom_start=13,
                           tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
                           attr="Google Satellite")
            couleurs_pot = {"élevé":"green","modéré":"orange","faible":"red",
                            "exceptionnel":"darkgreen","modere":"orange"}

            for _, r in df_ruches.iterrows():
                folium.Marker(
                    [r["latitude"], r["longitude"]],
                    popup=f"<b>{r['nom']}</b><br>{r['race']}<br>{r['localisation']}",
                    icon=folium.Icon(color="orange", icon="home", prefix="fa")
                ).add_to(m)

            for _, z in df_zones.iterrows():
                if z["latitude"] and z["longitude"]:
                    col_m = couleurs_pot.get(str(z["potentiel"]).lower(), "blue")
                    popup_html = f"""
                    <b>{z['nom']}</b><br>
                    Flore : {z['flore_principale']}<br>
                    NDVI : {z['ndvi']}<br>
                    Potentiel : {z['potentiel']}<br>
                    Surface : {z['superficie_ha']} ha
                    """
                    folium.CircleMarker(
                        [z["latitude"], z["longitude"]], radius=14,
                        popup=folium.Popup(popup_html, max_width=200),
                        color=col_m, fill=True, fill_color=col_m, fill_opacity=0.55
                    ).add_to(m)

            st_folium(m, width="100%", height=420)
        else:
            st.warning("Installez `folium` et `streamlit-folium` pour la carte interactive.")

        st.markdown("### 📋 Zones enregistrées")
        if not df_zones.empty:
            for _, z in df_zones.iterrows():
                with st.expander(f"📍 {z['nom']} — {z['flore_principale']} · {z['potentiel']}"):
                    col_z1, col_z2, col_z3, col_z4 = st.columns(4)
                    col_z1.metric("Surface", f"{z['superficie_ha']} ha")
                    col_z2.metric("NDVI", f"{z['ndvi']:.2f}")
                    col_z3.metric("Type", z["type_zone"])
                    col_z4.metric("Potentiel", z["potentiel"])

                    if st.button(f"🤖 Analyser '{z['nom']}' avec l'IA",
                                  key=f"ia_zone_{z['id']}", disabled=not ia_active):
                        prov = get_active_provider()
                        with st.spinner(f"🤖 {prov} analyse la zone..."):
                            result = ia_analyser_zone_carto(
                                z["nom"], z["flore_principale"],
                                z["superficie_ha"], z["ndvi"],
                                z["potentiel"], z["type_zone"],
                                z["latitude"], z["longitude"]
                            )
                        if result and "error" not in result:
                            _afficher_diagnostic_zone(result, z["nom"])
                            log_action("Analyse IA zone", f"Zone '{z['nom']}' analysée par {prov}")
                        elif result:
                            st.error(f"Erreur IA : {result.get('error')}")
                        else:
                            st.warning("⚠️ Configurez votre clé API via le sélecteur ci-dessus.")

    with tab2:
        st.markdown("### 🌿 Analyse IA d'un environnement mellifère")
        st.markdown("""
        <div style='background:#0D2A1F;border:1px solid #1A5C3A;border-left:4px solid #34D399;
                    border-radius:8px;padding:14px 16px;font-size:.84rem;color:#6EE7B7;margin-bottom:16px'>
        <b>📸 Photo(s) ou vidéo = suffisant !</b> La description est optionnelle.<br>
        Uploadez 1 à 5 photos (ou une capture vidéo) de votre environnement.
        L'IA identifie la flore, la faune, le microclimat et évalue le potentiel
        <b>🍯 Miel · 🌼 Pollen · 🟤 Propolis · 👑 Gelée royale</b> avec des scores /5 ⭐
        </div>
        """, unsafe_allow_html=True)

        # ── Upload multiple images ──────────────────────────────────────────
        env_imgs = st.file_uploader(
            "📷 Photos ou captures vidéo de l'environnement (1 à 5 images)",
            type=["jpg","jpeg","png","webp","bmp"],
            accept_multiple_files=True,
            key="env_imgs_multi"
        )
        if env_imgs:
            cols_prev = st.columns(min(5, len(env_imgs)))
            for i, (col_p, img_f) in enumerate(zip(cols_prev, env_imgs[:5])):
                with col_p:
                    st.image(img_f, caption=f"Photo {i+1}", use_container_width=True)

        col_env1, col_env2 = st.columns([1.2, 1])
        with col_env1:
            description = st.text_area(
                "Description complémentaire (optionnelle)",
                placeholder=(
                    "Optionnel — Ex : zone de garrigue, altitude 600m, oued à 300m...\n"
                    "Sans photo : décrivez l'environnement pour obtenir l'analyse."
                ),
                height=100,
                key="env_description"
            )
            col_s1, col_s2 = st.columns(2)
            saison = col_s1.selectbox("Saison actuelle",
                                       ["Printemps","Été","Automne","Hiver"], key="env_saison")
            localisation_env = col_s2.text_input("Localisation", "Tlemcen, Algérie", key="env_loc")
            col_lat, col_lon = st.columns(2)
            env_lat = col_lat.number_input("Latitude", -90.0, 90.0, 34.88, 0.0001,
                                            format="%.4f", key="env_lat")
            env_lon = col_lon.number_input("Longitude", -180.0, 180.0, 1.32, 0.0001,
                                            format="%.4f", key="env_lon")

        with col_env2:
            st.markdown("#### Ce que l'IA va analyser :")
            items_env = [
                ("🌿 Flore visible","Identification chaque plante, famille, floraison"),
                ("🍯 Potentiel miel","Type floral, rendement kg/ruche/an estimé"),
                ("🌼 Potentiel pollen","Diversité, richesse protéique, couleurs"),
                ("🟤 Potentiel propolis","Espèces résineuses, qualité antibactérienne"),
                ("👑 Gelée royale","Disponibilité sucres+protéines, 10-HDA estimé"),
                ("🦋 Faune","Prédateurs, pollinisateurs concurrents"),
                ("🌡️ Microclimat","Exposition, eau, vent, risques"),
                ("🎯 Verdict /10","Score global + capacité de charge"),
            ]
            for icon_lbl, desc in items_env:
                st.markdown(f"""
                <div style='display:flex;gap:8px;padding:4px 8px;background:#1E2535;
                            border-radius:5px;margin-bottom:3px'>
                    <span style='color:#34D399;font-weight:600;font-size:.78rem;
                                 min-width:130px'>{icon_lbl}</span>
                    <span style='color:#A8B4CC;font-size:.75rem'>{desc}</span>
                </div>
                """, unsafe_allow_html=True)

        prov_actif = get_active_provider()
        has_input = bool(env_imgs) or bool(description.strip())
        btn_env = st.button(
            f"🌿 Analyser l'environnement avec {prov_actif.split('(')[0].strip()}",
            use_container_width=True,
            disabled=not ia_active or not has_input,
            key="btn_env_analyse"
        )

        if not ia_active:
            st.info("🔑 Configurez votre clé API (sélecteur ci-dessus) pour activer l'analyse IA.")
        elif not has_input:
            st.info("📸 Uploadez au moins une photo OU saisissez une description pour lancer l'analyse.")

        if btn_env and has_input:
            # Utilise la première image pour l'appel IA (les modèles acceptent 1 image)
            img_bytes = env_imgs[0].read() if env_imgs else None
            nb_imgs = len(env_imgs) if env_imgs else 0

            desc_ctx = description.strip() or f"Analyse visuelle de l'environnement ({nb_imgs} photo(s))"
            prompt_env = f"""Tu es expert apicole senior, botaniste et écologue spécialisé en flore mellifère méditerranéenne et nord-africaine (Algérie, Maroc, Tunisie).

{'Analyse ' + str(nb_imgs) + ' photo(s) de cet environnement apicole.' if img_bytes else ''}
Localisation : {localisation_env}
Coordonnées : {env_lat:.4f}°N, {env_lon:.4f}°E
Saison : {saison}
Contexte additionnel : {desc_ctx}

Effectue une analyse mellifère COMPLÈTE et DÉTAILLÉE. Réponds en français.

## 🌿 1. Inventaire floristique complet
Pour CHAQUE plante/végétation identifiée (visible sur photo ou probable selon la localisation) :
**[NOM COMMUN] (Nom scientifique)**
- Source : Nectar / Pollen / Résine / Mixte
- Période de floraison :
- Qualité mellifère : Exceptionnelle / Excellente / Bonne / Moyenne / Faible
- Notes :

## 📊 2. Scores de potentiel de production (/5 ⭐)

### 🍯 MIEL : X/5 ⭐
→ Type floral dominant et saveur probable
→ Rendement estimé : X à Y kg/ruche/an
→ Meilleure période de récolte :
→ Qualité commerciale attendue :

### 🌼 POLLEN : X/5 ⭐
→ Diversité pollinique (nombre d'espèces estimé) :
→ Richesse protéique estimée (%) :
→ Couleurs dominantes :
→ Mois de collecte optimaux :

### 🟤 PROPOLIS : X/5 ⭐
→ Espèces résineuses présentes :
→ Qualité antibactérienne estimée :
→ Quantité récoltable (g/ruche/an) :

### 👑 GELÉE ROYALE : X/5 ⭐
→ Disponibilité en sucres + protéines :
→ Taux 10-HDA estimé (%) :
→ Mois favorables :

## 🦋 3. Faune et biodiversité
- Pollinisateurs sauvages probables (bourdons, syrphes, etc.)
- Prédateurs potentiels (frelons, pies-grièches, etc.)
- Niveau de biodiversité général : Faible / Moyen / Riche / Exceptionnel

## 🌡️ 4. Analyse microclimatique
- Exposition et ensoleillement :
- Humidité estimée :
- Présence d'eau (ruisseau, mare, puits) :
- Protection contre le vent :
- Risques : pesticides, sécheresse, gel tardif

## 🎯 5. Verdict et recommandations

**Potentiel global : [Insuffisant / Moyen / Bon / Excellent / Exceptionnel]**
**Indice mellifère : X/10**
**Production principale recommandée : [Miel / Pollen / Propolis / Gelée royale / Mixte]**
**Capacité de charge : X ruches / 100 ha**

### ✅ Recommandations pour l'installation
1. Nombre de ruches optimal pour ce site :
2. Race d'abeille la mieux adaptée :
3. Emplacement idéal dans la zone (orientation, distance des fleurs) :
4. Mois optimal d'installation :
5. Planning de récolte sur l'année :

### ⚠️ Points d'attention
- Contraintes identifiées :
- Actions correctives si nécessaire :

Données chiffrées obligatoires. Sois très précis sur les espèces typiques du Maghreb."""

            with st.spinner(f"🌿 {prov_actif.split('(')[0]} analyse l'environnement... (15-30 secondes)"):
                resultat = ia_call(prompt_env, img_bytes)

            if resultat and not resultat.startswith("❌"):
                afficher_resultat_ia(resultat, f"Analyse environnementale mellifère — {localisation_env}")
                log_action("Analyse IA environnement",
                           f"Zone {env_lat:.2f},{env_lon:.2f} — {saison} — {nb_imgs} photos")

                st.markdown("---")
                st.markdown("**💾 Sauvegarder cette zone dans la cartographie ?**")
                with st.form("save_env_zone"):
                    nom_z = st.text_input("Nom de la zone", f"Zone analysée — {localisation_env}")
                    type_z = st.selectbox("Type", ["nectar","pollen","nectar+pollen","propolis","mixte"])
                    surf_z = st.number_input("Superficie estimée (ha)", 0.0, 5000.0, 10.0)
                    if st.form_submit_button("💾 Sauvegarder dans la cartographie"):
                        conn.execute("""
                            INSERT INTO zones (nom,type_zone,latitude,longitude,superficie_ha,
                                               flore_principale,potentiel,notes)
                            VALUES (?,?,?,?,?,?,?,?)
                        """, (nom_z, type_z, env_lat, env_lon, surf_z,
                              desc_ctx[:100], "élevé", f"[IA {nb_imgs} photos] " + desc_ctx[:200]))
                        conn.commit()
                        log_action("Zone sauvegardée depuis analyse IA", nom_z)
                        st.success(f"✅ Zone '{nom_z}' sauvegardée dans la cartographie !")
            elif resultat:
                st.error(resultat)
            else:
                st.error("❌ Aucune réponse de l'IA. Vérifiez votre clé API dans Administration.")

    with tab3:
        with st.form("add_zone"):
            col1, col2 = st.columns(2)
            nom       = col1.text_input("Nom de la zone*")
            type_zone = col2.selectbox("Type", ["nectar","pollen","nectar+pollen","propolis","mixte"])
            col3, col4 = st.columns(2)
            lat       = col3.number_input("Latitude", value=34.88, format="%.4f")
            lon       = col4.number_input("Longitude", value=1.32, format="%.4f")
            col5, col6, col7 = st.columns(3)
            superficie = col5.number_input("Superficie (ha)", 0.0, 5000.0, 10.0)
            flore      = col6.text_input("Flore principale")
            ndvi       = col7.number_input("NDVI", 0.0, 1.0, 0.65, 0.01)
            potentiel  = st.selectbox("Potentiel mellifère", ["faible","modéré","élevé","exceptionnel"])
            notes      = st.text_area("Notes")
            submitted  = st.form_submit_button("✅ Ajouter la zone")

        if submitted and nom:
            conn.execute("""
                INSERT INTO zones (nom,type_zone,latitude,longitude,superficie_ha,
                                   flore_principale,ndvi,potentiel,notes)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (nom, type_zone, lat, lon, superficie, flore, ndvi, potentiel, notes))
            conn.commit()
            log_action("Zone ajoutée", f"Zone '{nom}' — {flore} — NDVI {ndvi}")
            st.success(f"✅ Zone '{nom}' ajoutée.")
            st.rerun()

    conn.close()


def _afficher_diagnostic_zone(result, nom_zone):
    d = result.get("diagnostic", {})
    scores = result.get("scores", {})

    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#F0F9F0,#1E2535);
                border:1px solid #2E7D32;border-left:4px solid #2E7D32;
                border-radius:10px;padding:16px;margin:8px 0'>
        <div style='font-family:Playfair Display,serif;font-size:.95rem;font-weight:600;
                    color:#6EE7B7;margin-bottom:10px'>🤖 Diagnostic IA — {nom_zone}</div>
        <div style='display:flex;gap:20px;flex-wrap:wrap;margin-bottom:10px'>
            <span>🌿 Potentiel : <b>{d.get('potentiel_global','—')}</b></span>
            <span>📊 Indice mellifère : <b>{d.get('indice_mellifere','—')}/10</b></span>
            <span>🐝 Capacité : <b>{d.get('capacite_ruches','—')} ruches</b></span>
            <span>📅 Pic : <b>{d.get('saison_pic','—')}</b></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if scores:
        st.markdown("**Scores de production :**")
        cols_sc = st.columns(4)
        icons = {"miel":"🍯","pollen":"🌼","propolis":"🟤","gelee_royale":"👑"}
        labels = {"miel":"Miel","pollen":"Pollen","propolis":"Propolis","gelee_royale":"Gelée royale"}
        for col, key in zip(cols_sc, ["miel","pollen","propolis","gelee_royale"]):
            s = scores.get(key, {})
            with col:
                st.markdown(f"""
                <div style='text-align:center;background:#1E2535;border:1px solid #2E3A52;
                            border-radius:8px;padding:10px'>
                    <div style='font-size:1.2rem'>{icons[key]}</div>
                    <div style='font-size:.75rem;color:#A8B4CC;font-weight:500'>{labels[key]}</div>
                    <div style='font-size:.9rem'>{s.get('etoiles','—')}</div>
                    <div style='font-size:.7rem;color:#A8B4CC'>{s.get('detail','')[:50]}</div>
                </div>
                """, unsafe_allow_html=True)

    flore_list = result.get("flore_identifiee", [])
    if flore_list:
        st.markdown("**Flore identifiée par l'IA :**")
        df_f = pd.DataFrame(flore_list)
        st.dataframe(df_f, use_container_width=True, hide_index=True)

    recs = result.get("recommandations", [])
    if recs:
        st.markdown("**Recommandations :**")
        for r in recs:
            st.markdown(f"- {r}")

    resume = result.get("resume", "")
    if resume:
        st.info(f"📝 {resume}")


# ════════════════════════════════════════════════════════════════════════════
# PAGE : MÉTÉO & MIELLÉE
# ════════════════════════════════════════════════════════════════════════════
def page_meteo():
    st.markdown("## ☀️ Météo & Miellée — Prévisions 7 jours")
    localisation = get_setting("localisation", "Tlemcen")
    st.markdown(f"<p style='color:#A8B4CC'>Données simulées · {localisation}</p>", unsafe_allow_html=True)

    today = datetime.date.today()
    previsions = [
        {"jour": (today + datetime.timedelta(days=i)).strftime("%a %d/%m"), "temp": t, "icon": ic, "butinage": b, "pluie": p}
        for i, (t, ic, b, p) in enumerate([
            (22, "☀️", "Élevé", 0),
            (19, "⛅", "Élevé", 5),
            (21, "🌤️", "Élevé", 10),
            (14, "🌧️", "Faible", 80),
            (17, "⛅", "Moyen", 30),
            (24, "☀️", "Élevé", 0),
            (26, "☀️", "Élevé", 0),
        ])
    ]

    cols = st.columns(7)
    couleur_butinage = {"Élevé": "#2E7D32", "Moyen": "#F57F17", "Faible": "#C62828"}
    bg_butinage = {"Élevé": "#E8F5E9", "Moyen": "#FFF8E1", "Faible": "#FFEBEE"}

    for col, p in zip(cols, previsions):
        with col:
            st.markdown(f"""
            <div style='background:#1E2535;border:1px solid #2E3A52;border-radius:8px;padding:10px 6px;text-align:center'>
                <div style='font-size:.65rem;text-transform:uppercase;letter-spacing:.06em;color:#A8B4CC;font-weight:500'>{p['jour']}</div>
                <div style='font-size:1.4rem;margin:4px 0'>{p['icon']}</div>
                <div style='font-size:.85rem;font-weight:500;color:#F0F4FF'>{p['temp']}°C</div>
                <div style='font-size:.65rem;margin-top:4px;padding:2px 4px;border-radius:4px;
                    background:{bg_butinage[p["butinage"]]};color:{couleur_butinage[p["butinage"]]}'>{p['butinage']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📈 Indice de butinage prévisionnel")
        df_but = pd.DataFrame(previsions)
        indice = {"Élevé": 90, "Moyen": 55, "Faible": 15}
        df_but["indice"] = df_but["butinage"].map(indice)
        fig = px.bar(df_but, x="jour", y="indice", template="plotly_white",
                     color_discrete_sequence=["#C8820A"])
        fig.update_layout(height=220, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          margin=dict(t=0,b=0,l=0,r=0), yaxis=dict(range=[0,100]))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 💡 Conseils de la semaine")
        st.success("☀️ **Lundi–Jeudi** : Conditions excellentes. Prioriser inspections et pose de hausses sur R01, R02, R04.")
        st.warning("🌧️ **Vendredi** : Pluie prévue. Éviter toute intervention. Vérifier fermetures.")
        st.info("🍯 **Dimanche–Lundi** : Pic de miellée jujubier prévu. Planifier la récolte en début de semaine prochaine.")


# ════════════════════════════════════════════════════════════════════════════
# PAGE : GÉNÉTIQUE & SÉLECTION
# ════════════════════════════════════════════════════════════════════════════
def page_genetique():
    st.markdown("## 📊 Génétique & Sélection")
    conn = get_db()

    df = pd.read_sql("""
        SELECT r.nom, r.race,
               COALESCE(AVG(i.varroa_pct), 0) as varroa_moy,
               COALESCE(AVG(i.nb_cadres), 0) as cadres_moy,
               COALESCE(SUM(rec.quantite_kg), 0) as production_totale,
               COUNT(i.id) as nb_inspections
        FROM ruches r
        LEFT JOIN inspections i ON i.ruche_id = r.id
        LEFT JOIN recoltes rec ON rec.ruche_id = r.id AND rec.type_produit='miel'
        WHERE r.statut='actif'
        GROUP BY r.id, r.nom, r.race
        ORDER BY production_totale DESC
    """, conn)

    if not df.empty:
        df["VSH_score"] = df["varroa_moy"].apply(lambda v: max(0, min(100, 100 - v * 20)))
        df["Score global"] = (
            df["production_totale"].rank(pct=True) * 40 +
            df["VSH_score"].rank(pct=True) * 35 +
            (1 - df["varroa_moy"].rank(pct=True)) * 25
        ).round(1)

        st.markdown("### 🏆 Top 3 candidates élevage")
        top3 = df.nlargest(3, "Score global")
        for i, (_, row) in enumerate(top3.iterrows()):
            medal = ["🥇", "🥈", "🥉"][i]
            st.success(f"{medal} **{row['nom']}** ({row['race']}) — Score : {row['Score global']:.1f}/100 · VSH {row['VSH_score']:.0f}% · Production {row['production_totale']:.1f} kg")

        st.markdown("### 📋 Registre complet")
        df_display = df[["nom","race","varroa_moy","cadres_moy","production_totale","VSH_score","Score global"]].copy()
        df_display.columns = ["Ruche","Race","Varroa moy%","Cadres moy","Production kg","VSH%","Score/100"]
        df_display = df_display.round(2)
        st.dataframe(df_display, use_container_width=True, hide_index=True)

        st.markdown("### 🕸️ Profil de caractérisation")
        ruche_sel = st.selectbox("Choisir une ruche", df["nom"].tolist())
        row = df[df["nom"] == ruche_sel].iloc[0]
        categories = ["Production", "VSH", "Douceur", "Économie hivernale", "Propolis"]
        values = [
            min(100, row["production_totale"] * 2),
            row["VSH_score"],
            max(0, 100 - row["varroa_moy"] * 15),
            70, 60
        ]
        fig = go.Figure(go.Scatterpolar(
            r=values + [values[0]], theta=categories + [categories[0]],
            fill="toself", fillcolor="rgba(200,130,10,0.2)",
            line_color="#C8820A"
        ))
        fig.update_layout(polar=dict(radialaxis=dict(range=[0,100])),
                          height=350, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    conn.close()


# ════════════════════════════════════════════════════════════════════════════
# PAGE : FLORE MELLIFÈRE
# ════════════════════════════════════════════════════════════════════════════
def page_flore():
    st.markdown("## 🌿 Flore mellifère — Calendrier")
    flore_data = [
        {"Espèce": "Romarin (Rosmarinus officinalis)", "Nectar": "⭐⭐⭐", "Pollen": "⭐⭐", "Propolis": "-", "Période": "Fév–Avr", "Potentiel": "Élevé"},
        {"Espèce": "Jujubier (Ziziphus lotus)", "Nectar": "⭐⭐⭐⭐", "Pollen": "⭐⭐⭐", "Propolis": "-", "Période": "Avr–Juin", "Potentiel": "Exceptionnel"},
        {"Espèce": "Chêne-liège (Quercus suber)", "Nectar": "⭐", "Pollen": "⭐⭐⭐⭐", "Propolis": "⭐⭐", "Période": "Avr–Mai", "Potentiel": "Élevé"},
        {"Espèce": "Lavande (Lavandula stoechas)", "Nectar": "⭐⭐⭐", "Pollen": "⭐⭐", "Propolis": "-", "Période": "Mai–Juil", "Potentiel": "Élevé"},
        {"Espèce": "Thym (Thymus algeriensis)", "Nectar": "⭐⭐⭐", "Pollen": "⭐⭐⭐", "Propolis": "⭐", "Période": "Mar–Juin", "Potentiel": "Élevé"},
        {"Espèce": "Eucalyptus (E. globulus)", "Nectar": "⭐⭐⭐⭐", "Pollen": "⭐⭐", "Propolis": "⭐", "Période": "Été", "Potentiel": "Élevé"},
        {"Espèce": "Caroube (Ceratonia siliqua)", "Nectar": "⭐⭐", "Pollen": "⭐⭐", "Propolis": "-", "Période": "Sep–Oct", "Potentiel": "Modéré"},
    ]
    df_flore = pd.DataFrame(flore_data)
    st.dataframe(df_flore, use_container_width=True, hide_index=True)

    st.markdown("### 📅 Calendrier de miellée")
    mois = ["Jan","Fév","Mar","Avr","Mai","Juin","Juil","Aoû","Sep","Oct","Nov","Déc"]
    esp = ["Romarin","Jujubier","Chêne-liège","Lavande","Thym","Eucalyptus","Caroube"]
    activite = np.array([
        [0,3,3,2,0,0,0,0,0,0,0,0],
        [0,0,0,3,3,2,0,0,0,0,0,0],
        [0,0,0,3,3,0,0,0,0,0,0,0],
        [0,0,0,0,3,3,3,0,0,0,0,0],
        [0,0,3,3,3,2,0,0,0,0,0,0],
        [0,0,0,0,0,0,3,3,2,0,0,0],
        [0,0,0,0,0,0,0,0,3,3,0,0],
    ], dtype=float)

    fig = px.imshow(activite, labels=dict(x="Mois", y="Espèce", color="Intensité"),
                    x=mois, y=esp,
                    color_continuous_scale=[[0,"#F5EDD8"],[0.5,"#F5C842"],[1,"#C8820A"]],
                    template="plotly_white")
    fig.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(t=10,b=10,l=0,r=0))
    st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# PAGE : ALERTES
# ════════════════════════════════════════════════════════════════════════════
def page_alertes():
    st.markdown("## ⚠️ Alertes")
    conn = get_db()

    df_crit = pd.read_sql("""
        SELECT r.nom, i.varroa_pct, i.date_inspection, i.notes
        FROM inspections i JOIN ruches r ON r.id=i.ruche_id
        WHERE i.varroa_pct >= 3.0 AND i.date_inspection >= date('now','-7 days')
        ORDER BY i.varroa_pct DESC
    """, conn)
    df_warn = pd.read_sql("""
        SELECT r.nom, i.varroa_pct, i.date_inspection
        FROM inspections i JOIN ruches r ON r.id=i.ruche_id
        WHERE i.varroa_pct >= 2.0 AND i.varroa_pct < 3.0 AND i.date_inspection >= date('now','-7 days')
        ORDER BY i.varroa_pct DESC
    """, conn)
    df_gr = pd.read_sql("""
        SELECT r.nom, SUM(rec.quantite_kg) as total, MAX(rec.hda_pct) as hda
        FROM recoltes rec JOIN ruches r ON r.id=rec.ruche_id
        WHERE rec.type_produit='gelée royale'
        GROUP BY r.nom HAVING total > 0.3
    """, conn)

    if not df_crit.empty:
        st.markdown("### 🔴 Alertes critiques (Varroa ≥ 3%)")
        for _, row in df_crit.iterrows():
            st.error(f"🔴 **{row['nom']}** — Varroa **{row['varroa_pct']}%** le {row['date_inspection']} · Traitement immédiat requis !")

    if not df_warn.empty:
        st.markdown("### 🟡 Alertes attention (Varroa ≥ 2%)")
        for _, row in df_warn.iterrows():
            st.warning(f"🟡 **{row['nom']}** — Varroa **{row['varroa_pct']}%** le {row['date_inspection']} · Surveillance renforcée.")

    if not df_gr.empty:
        st.markdown("### 🟢 Excellentes productrices gelée royale")
        for _, row in df_gr.iterrows():
            hda_str = f" · 10-HDA {row['hda']:.1f}%" if row["hda"] else ""
            st.success(f"🟢 **{row['nom']}** — {row['total']:.2f} kg gelée royale{hda_str} → Candidate élevage sélectif")

    if df_crit.empty and df_warn.empty and df_gr.empty:
        st.info("✅ Aucune alerte active en ce moment.")

    conn.close()


# ════════════════════════════════════════════════════════════════════════════
# PAGE : JOURNAL
# ════════════════════════════════════════════════════════════════════════════
def page_journal():
    st.markdown("## 📋 Journal d'activité")
    conn = get_db()
    df = pd.read_sql("SELECT * FROM journal ORDER BY timestamp DESC LIMIT 100", conn)
    conn.close()

    if not df.empty:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Exporter CSV", csv, "journal.csv", "text/csv")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Le journal est vide.")


# ════════════════════════════════════════════════════════════════════════════
# PAGE : ADMINISTRATION
# ════════════════════════════════════════════════════════════════════════════
def page_admin():
    st.markdown("## ⚙️ Administration")
    conn = get_db()

    tab1, tab2, tab3, tab4 = st.tabs(["🏠 Profil rucher", "🤖 Clé API IA", "🔐 Mot de passe", "💾 Base de données"])

    with tab1:
        rucher_nom = get_setting("rucher_nom", "Mon Rucher")
        localisation = get_setting("localisation", "")
        with st.form("settings_form"):
            new_nom = st.text_input("Nom du rucher", rucher_nom)
            new_loc = st.text_input("Localisation", localisation)
            submitted = st.form_submit_button("💾 Sauvegarder")
        if submitted:
            conn.execute("INSERT OR REPLACE INTO settings VALUES ('rucher_nom',?)", (new_nom,))
            conn.execute("INSERT OR REPLACE INTO settings VALUES ('localisation',?)", (new_loc,))
            conn.commit()
            log_action("Paramètres modifiés", f"Nom: {new_nom}, Localisation: {new_loc}")
            st.success("✅ Paramètres sauvegardés.")

    with tab2:
        st.markdown("### 🤖 Gestion des fournisseurs IA — Tous gratuits")
        st.markdown("""
        <div style='background:#0F1117;border:1px solid #C8820A;border-radius:8px;padding:14px;
                    font-size:.84rem;color:#F0F4FF;margin-bottom:16px'>
        <b>ApiTrack Pro supporte 10 fournisseurs IA 100% gratuits.</b>
        Configurez une ou plusieurs clés — l'app utilisera le fournisseur actif sélectionné.
        <b>Gemma, Groq, Mistral, OpenRouter</b> fonctionnent tous sans restriction Anthropic.
        </div>
        """, unsafe_allow_html=True)

        rows = []
        for pname, cfg in IA_PROVIDERS.items():
            key = get_api_key_for_provider(pname)
            rows.append({
                "Fournisseur": pname,
                "Modèle par défaut": cfg["default"],
                "Quota gratuit": cfg["quota"],
                "Vision": "✅" if cfg["vision"] else "❌",
                "Statut": "✅ Configuré" if key else "❌ Manquant",
            })
        df_prov = pd.DataFrame(rows)
        st.dataframe(df_prov, use_container_width=True, hide_index=True)

        st.markdown("#### 🔑 Configurer les clés API")
        prov_sel = st.selectbox("Fournisseur à configurer",
                                 list(IA_PROVIDERS.keys()), key="admin_prov_sel")
        cfg_sel = IA_PROVIDERS[prov_sel]
        key_actuelle = get_api_key_for_provider(prov_sel)

        st.markdown(f"""
        <div style='font-size:.8rem;background:#0D2A1F;border:1px solid #1A5C3A;
                    border-radius:6px;padding:10px;margin:8px 0'>
        🔗 Obtenir la clé : <a href='{cfg_sel["url"]}' target='_blank'>{cfg_sel["url"]}</a><br>
        📊 Quota : {cfg_sel['quota']}<br>
        🖼️ Vision/Photo : {'✅ Supporté' if cfg_sel['vision'] else '❌ Texte uniquement'}
        {f"<br>⚠️ {cfg_sel['note']}" if cfg_sel.get('note') else ""}
        </div>
        """, unsafe_allow_html=True)

        with st.form(f"key_form_{prov_sel}"):
            new_key = st.text_input(
                f"Clé API pour {prov_sel.split('(')[0].strip()}",
                value=key_actuelle, type="password",
                placeholder=cfg_sel.get("prefix","") + "votre-clé-ici"
            )
            sel_model_admin = st.selectbox("Modèle à utiliser", cfg_sel["models"],
                                            index=0, key="admin_model_sel")
            col_a, col_b = st.columns(2)
            save = col_a.form_submit_button("💾 Sauvegarder & Activer")
            delete = col_b.form_submit_button("🗑️ Supprimer la clé")

        if save:
            conn = get_db()
            if new_key.strip():
                conn.execute("INSERT OR REPLACE INTO settings VALUES (?,?)",
                             (cfg_sel["key"], new_key.strip()))
            conn.execute("INSERT OR REPLACE INTO settings VALUES ('ia_provider',?)", (prov_sel,))
            conn.execute("INSERT OR REPLACE INTO settings VALUES ('ia_model',?)", (sel_model_admin,))
            conn.commit()
            conn.close()
            log_action("Fournisseur IA configuré", f"{prov_sel} / {sel_model_admin}")
            st.success(f"✅ {prov_sel} configuré et activé · Modèle : {sel_model_admin}")
            st.rerun()
        if delete:
            conn = get_db()
            conn.execute("DELETE FROM settings WHERE key=?", (cfg_sel["key"],))
            conn.commit()
            conn.close()
            st.success("✅ Clé supprimée.")
            st.rerun()

        if key_actuelle:
            if st.button("🔬 Tester la connexion", key="admin_test_ia"):
                with st.spinner("Test en cours..."):
                    r = ia_call("Réponds uniquement : 'ApiTrack Pro IA OK'")
                if r and "OK" in r:
                    st.success(f"✅ {r.strip()}")
                elif r:
                    st.info(f"Réponse : {r[:300]}")
                else:
                    st.error("❌ Pas de réponse. Vérifiez la clé.")

    with tab3:
        with st.form("pwd_form"):
            old_pwd = st.text_input("Mot de passe actuel", type="password")
            new_pwd = st.text_input("Nouveau mot de passe", type="password")
            new_pwd2 = st.text_input("Confirmer le nouveau mot de passe", type="password")
            submitted = st.form_submit_button("🔐 Changer le mot de passe")
        if submitted:
            user = check_login(st.session_state.username, old_pwd)
            if not user:
                st.error("Mot de passe actuel incorrect.")
            elif new_pwd != new_pwd2:
                st.error("Les nouveaux mots de passe ne correspondent pas.")
            elif len(new_pwd) < 6:
                st.error("Le mot de passe doit faire au moins 6 caractères.")
            else:
                new_hash = hashlib.sha256(new_pwd.encode()).hexdigest()
                conn.execute("UPDATE users SET password_hash=? WHERE username=?",
                             (new_hash, st.session_state.username))
                conn.commit()
                log_action("Changement mot de passe", "Mot de passe modifié avec succès")
                st.success("✅ Mot de passe modifié.")

    with tab4:
        st.markdown("**Sauvegarde de la base**")
        if os.path.exists(DB_PATH):
            with open(DB_PATH, "rb") as f:
                st.download_button("⬇️ Télécharger la base SQLite", f, "apitrack_backup.db", "application/octet-stream")

        st.markdown("**Statistiques**")
        tables = ["ruches", "inspections", "traitements", "recoltes", "morph_analyses", "zones", "journal"]
        stats = {}
        for t in tables:
            n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            stats[t] = n
        df_stats = pd.DataFrame({"Table": stats.keys(), "Enregistrements": stats.values()})
        st.dataframe(df_stats, use_container_width=True, hide_index=True)

        version = get_setting("version", "2.0.0")
        st.markdown(f"<div class='api-footer'>ApiTrack Pro v{version} · Streamlit · SQLite · © 2025</div>", unsafe_allow_html=True)

    conn.close()


# ════════════════════════════════════════════════════════════════════════════
# PAGE : DÉTECTION VISUELLE DE MALADIES (COMPUTER VISION IA)
# ════════════════════════════════════════════════════════════════════════════
def page_maladies_ia():
    st.markdown("## 🔬 Détection Visuelle de Maladies — Computer Vision IA")
    st.markdown("""
    <div style='background:#2A0D0D;border:1px solid #5C1A1A;border-left:4px solid #F87171;
                border-radius:8px;padding:14px;font-size:.84rem;color:#FCA5A5;margin-bottom:16px'>
    <b>🔬 Diagnostiquez vos abeilles et couvains par simple photo.</b>
    L'IA détecte les signes visuels de maladies, pathologies et parasites
    avec un protocole de traitement adapté à l'Algérie et au Maghreb.
    </div>
    """, unsafe_allow_html=True)

    ia_active = widget_cle_api()

    tab1, tab2, tab3 = st.tabs(["🐝 Abeilles adultes", "🥚 Couvain & cellules", "📊 Historique diagnostics"])

    with tab1:
        col1, col2 = st.columns([1, 1.2])
        with col1:
            imgs = st.file_uploader("📷 Photos d'abeilles (1-4 images)",
                                     type=["jpg","jpeg","png","webp"],
                                     accept_multiple_files=True, key="mal_abeilles")
            if imgs:
                cols_p = st.columns(min(2, len(imgs)))
                for i, (cp, img_f) in enumerate(zip(cols_p, imgs[:4])):
                    with cp: st.image(img_f, use_container_width=True)

            symptomes = st.multiselect("Symptômes observés", [
                "Ailes déformées / recroquevillées (DWF)",
                "Abeilles rampantes devant ruche",
                "Abdomen distendu / diarrhée",
                "Tremblements / paralysie",
                "Ailes en V (K-Wing)",
                "Varroa visible sur abeille",
                "Mortalité anormale",
                "Perte de population rapide",
                "Agressivité inhabituelle",
                "Odeur anormale dans la ruche",
            ], key="mal_symptomes")
            ruche_sel = st.selectbox("Ruche concernée",
                [f"R{r[0]:02d} — {r[1]}" for r in get_db().execute(
                    "SELECT id,nom FROM ruches WHERE statut='actif'").fetchall()],
                key="mal_ruche")
            btn_diag = st.button("🔬 Diagnostiquer", use_container_width=True,
                                  disabled=not ia_active, key="btn_diag_adult")

        with col2:
            st.markdown("#### Maladies détectables :")
            maladies = [
                ("🔴 CRITIQUE","Loque américaine (AFB)","Couvain filant, odeur putride"),
                ("🔴 CRITIQUE","Varroose","Acarien visible, ailes DWF, abeilles chétives"),
                ("🟡 ATTENTION","Loque européenne (EFB)","Larves jaunies, odeur acide"),
                ("🟡 ATTENTION","Nosémose","Abdomen distendu, dysenterie"),
                ("🟡 ATTENTION","DWF Virus","Ailes raccourcies, atrophiées"),
                ("🟡 ATTENTION","Paralysie chronique (CBPV)","Abeilles noires luisantes, tremblements"),
                ("🔵 SURVEILLER","Sacbrood","Larves en sac d'eau"),
                ("🔵 SURVEILLER","K-Wing","Ailes en position anormale"),
                ("🔵 SURVEILLER","Acarose","Abeilles rampantes (non visible directement)"),
            ]
            for niveau, nom, signe in maladies:
                color = "#FCA5A5" if "CRITIQUE" in niveau else "#FDE68A" if "ATTENTION" in niveau else "#93C5FD"
                bg = "#2A0D0D" if "CRITIQUE" in niveau else "#2A200A" if "ATTENTION" in niveau else "#0D1A2A"
                st.markdown(f"""
                <div style='padding:5px 8px;background:{bg};border-radius:5px;margin-bottom:3px'>
                    <span style='color:{color};font-weight:600;font-size:.75rem'>{niveau} · {nom}</span>
                    <div style='color:#A8B4CC;font-size:.72rem'>{signe}</div>
                </div>""", unsafe_allow_html=True)

        if btn_diag and imgs:
            img_bytes = imgs[0].read()
            symp_str = ", ".join(symptomes) if symptomes else "Aucun précisé"
            prompt = f"""Tu es vétérinaire apicole expert en pathologie des abeilles (Apis mellifera), spécialisé dans les maladies du Maghreb et de la Méditerranée.

Ruche concernée : {ruche_sel}
Symptômes signalés : {symp_str}
Nombre de photos : {len(imgs)}

Analyse cette/ces photo(s) d'abeilles et effectue un DIAGNOSTIC COMPLET.

## 🔍 1. Observations visuelles détaillées
Décris précisément tout ce que tu vois : morphologie, couleurs, déformations, parasites visibles, comportements anormaux.

## 🦠 2. Diagnostic différentiel
Pour chaque pathologie suspectée (du plus au moins probable) :
| Maladie | Probabilité % | Signes observés | Urgence |
Urgence : 🔴 Immédiate (24h) / 🟡 Cette semaine / 🔵 Surveillance

## ⚠️ 3. Niveau d'alerte global
Indique clairement : 🔴 CRITIQUE / 🟡 ATTENTION / 🟢 RAS

## 💊 4. Protocole de traitement
Pour chaque maladie identifiée :
- **Traitement 1** : nom commercial + principe actif + dosage + durée
- **Traitement alternatif** : produit homologué Algérie/Maroc si disponible
- Précautions : retrait hausses, délai d'attente avant consommation
- Coût estimé (MAD/DZD)

## 🛡️ 5. Mesures prophylactiques
- Actions préventives pour les ruches adjacentes du rucher
- Risque de contagion et vitesse de propagation
- Mesures de quarantaine si nécessaire

## 📋 6. Examens complémentaires
- Analyses de laboratoire recommandées
- Organismes à contacter (DSA, vétérinaire sanitaire apicole)
- Déclaration obligatoire ? (loque américaine = maladie légalement déclarable)

## 📊 7. Impact estimé sur la production
- Miel : impact en % sur la récolte prévue
- Durée de récupération estimée après traitement

Sois très précis. Protocoles adaptés aux conditions Algeria/Maghreb."""

            with st.spinner("🔬 Analyse pathologique en cours..."):
                result = ia_call(prompt, img_bytes)
            if result and not result.startswith("❌"):
                afficher_resultat_ia(result, f"Diagnostic pathologique — {ruche_sel}")
                log_action("Diagnostic maladie IA", f"{ruche_sel} — {symp_str[:80]}")
            elif result:
                st.error(result)

    with tab2:
        col1c, col2c = st.columns([1, 1.2])
        with col1c:
            imgs_couv = st.file_uploader("📷 Photos du couvain / cadres",
                                          type=["jpg","jpeg","png","webp"],
                                          accept_multiple_files=True, key="mal_couvain")
            if imgs_couv:
                for img_f in imgs_couv[:2]: st.image(img_f, use_container_width=True)

            anomalies = st.multiselect("Anomalies couvain observées", [
                "Couvain irrégulier / parsemé","Cellules perforées ou enfoncées",
                "Larves décolorées (jaunâtres / brunâtres)","Larves filantes",
                "Odeur putride","Odeur acide","Cellules non operculées avec larves mortes",
                "Opercules creux / affaissés","Couvain pétrifié (calcaire)","Larves en sac d'eau",
            ], key="mal_couvain_anom")
            btn_couv = st.button("🔬 Analyser le couvain", use_container_width=True,
                                  disabled=not ia_active, key="btn_diag_couv")

        with col2c:
            st.markdown("#### Maladies du couvain :")
            maladies_couv = [
                ("🔴","Loque américaine","Larves café filantes, odeur colle chaude, AFB"),
                ("🔴","Loque européenne","Larves jaunes tordues, EFB, odeur acide"),
                ("🟡","Sacbrood","Larves en sac eau, virus SBV"),
                ("🟡","Couvain calcifié","Larves calcifiées blanches/noires"),
                ("🟡","Couvain saccifié","Larves noires momifiées"),
                ("🟡","Aethina tumida","Petits coléoptères des ruches"),
                ("🔵","Couvain glacé","Larves gelées par froid"),
            ]
            for niveau, nom, desc in maladies_couv:
                color = "#FCA5A5" if niveau == "🔴" else "#FDE68A" if niveau == "🟡" else "#93C5FD"
                st.markdown(f"<div style='padding:4px 8px;background:#1E2535;border-radius:4px;margin-bottom:3px'>"
                            f"<span style='color:{color};font-weight:600;font-size:.75rem'>{niveau} {nom}</span>"
                            f"<div style='color:#A8B4CC;font-size:.7rem'>{desc}</div></div>",
                            unsafe_allow_html=True)

        if btn_couv and imgs_couv:
            img_bytes = imgs_couv[0].read()
            anom_str = ", ".join(anomalies) if anomalies else "Aucune précisée"
            prompt_couv = f"""Tu es expert en pathologie apicole du couvain. Analyse ces photos de couvain d'abeilles.

Anomalies signalées : {anom_str}

## 🔍 1. Description visuelle du couvain
État général, couleur des larves, régularité, opercules, odeur probable.

## 🦠 2. Maladies identifiées (probabilité décroissante)
| Maladie | Probabilité % | Stade affecté | Urgence |

## 💊 3. Traitement
Protocole complet pour chaque maladie identifiée, adapté Maghreb.

## ⚠️ 4. Actions immédiates
Étapes dans les 24h / 48h / semaine.

## 📋 5. Déclaration obligatoire ?
Loque américaine et européenne = déclaration légalement obligatoire en Algérie."""

            with st.spinner("🔬 Analyse couvain en cours..."):
                result = ia_call(prompt_couv, img_bytes)
            if result and not result.startswith("❌"):
                afficher_resultat_ia(result, "Diagnostic couvain — Computer Vision IA")
                log_action("Diagnostic couvain IA", f"Anomalies: {anom_str[:80]}")
            elif result:
                st.error(result)

    with tab3:
        conn = get_db()
        df_diag = pd.read_sql("""
            SELECT timestamp, action, details FROM journal
            WHERE action LIKE '%Diagnostic%' OR action LIKE '%maladie%' OR action LIKE '%patholog%'
            ORDER BY timestamp DESC LIMIT 30
        """, conn)
        conn.close()
        if not df_diag.empty:
            st.dataframe(df_diag, use_container_width=True, hide_index=True)
        else:
            st.info("Aucun diagnostic enregistré.")


# ════════════════════════════════════════════════════════════════════════════
# PAGE : TRANSHUMANCE IA (Modèle Prédictif)
# ════════════════════════════════════════════════════════════════════════════
def page_transhumance():
    st.markdown("## 🚁 Modèle Prédictif de Transhumance — IA + Climat")
    st.markdown("""
    <div style='background:#0D1A2A;border:1px solid #1A3A5C;border-left:4px solid #60A5FA;
                border-radius:8px;padding:14px;font-size:.84rem;color:#93C5FD;margin-bottom:16px'>
    <b>🚁 Optimisez vos déplacements de ruches.</b> L'IA analyse les données climatiques,
    floristiques et géographiques pour vous recommander le meilleur calendrier et itinéraire
    de transhumance afin de maximiser votre production annuelle.
    </div>
    """, unsafe_allow_html=True)

    ia_active = widget_cle_api()

    tab1, tab2, tab3 = st.tabs(["🗓️ Planification IA", "📍 Zones connues", "📊 Historique transhumances"])

    with tab1:
        st.markdown("### Planification intelligente de la transhumance")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**📍 Rucher actuel**")
            loc_actuelle = st.text_input("Localisation actuelle", "Tlemcen, 600m, Atlas tellien", key="th_loc")
            nb_ruches_th = st.number_input("Nombre de ruches à déplacer", 1, 200, 10, key="th_nb")
            race_th = st.selectbox("Race", ["intermissa","sahariensis","ligustica","carnica","hybride"], key="th_race")
            prod_cible = st.multiselect("Production(s) ciblée(s)",
                                         ["🍯 Miel","🌼 Pollen","🟤 Propolis","👑 Gelée royale"],
                                         default=["🍯 Miel"], key="th_prod")
            mois_depart = st.selectbox("Mois de départ envisagé",
                ["Janvier","Février","Mars","Avril","Mai","Juin",
                 "Juillet","Août","Septembre","Octobre","Novembre","Décembre"], key="th_mois")

        with col2:
            st.markdown("**🎯 Contraintes**")
            rayon_km = st.slider("Rayon de déplacement max (km)", 50, 500, 200, key="th_rayon")
            budget_th = st.number_input("Budget transport (DZD)", 0, 500000, 50000, 5000, key="th_budget")
            duree_max = st.slider("Durée maximale sur place (jours)", 15, 180, 60, key="th_duree")
            regions_evit = st.text_input("Régions à éviter", placeholder="Ex: zone agricole traitée, zone sèche...", key="th_evit")

            st.markdown("**📸 Photo de la zone cible (optionnel)**")
            img_th = st.file_uploader("Photo zone cible", type=["jpg","jpeg","png","webp"], key="th_img")
            if img_th: st.image(img_th, use_container_width=True)

        btn_th = st.button("🚁 Générer le plan de transhumance IA",
                            use_container_width=True, disabled=not ia_active, key="btn_th")

        if btn_th:
            img_bytes = img_th.read() if img_th else None
            prod_str = ", ".join(prod_cible)
            prompt_th = f"""Tu es consultant expert en transhumance apicole pour l'Algérie et le Maghreb,
spécialisé en optimisation de déplacements de ruchers selon les données phénologiques, climatiques et géographiques.

**Rucher actuel :** {loc_actuelle}
**Nombre de ruches :** {nb_ruches_th} | **Race :** {race_th}
**Productions ciblées :** {prod_str}
**Mois de départ envisagé :** {mois_depart}
**Rayon max :** {rayon_km} km | **Budget transport :** {budget_th} DZD
**Durée sur place :** max {duree_max} jours
**Zones à éviter :** {regions_evit or 'Aucune précisée'}

## 🗓️ 1. Calendrier de transhumance optimal (12 mois)
Pour chaque déplacement recommandé :
| Mois | Zone destination | Altitude | Floraison principale | Production attendue | Durée recommandée |

## 📍 2. Zones de destination recommandées (Top 5)
Pour chaque zone, détailler :
**[Nom de la zone / Région]**
- Localisation précise + coordonnées approximatives
- Distance depuis {loc_actuelle} (km)
- Altitude (m)
- Flore mellifère dominante
- Production principale + rendement estimé (kg/ruche)
- Fenêtre temporelle idéale
- Accessibilité (piste, route, terrain)
- Présence d'eau pour les abeilles
- Risques (météo, animaux, vol)

## 📊 3. Prévision de production annuelle
Sans transhumance vs avec le plan proposé :
| Production | Sans transhumance | Avec plan | Gain |
🍯 Miel (kg total) :
🌼 Pollen (kg total) :
🟤 Propolis (g total) :
CA estimé (DZD) :

## 💰 4. Analyse économique
- Coût total transport (aller-retour x nb déplacements) :
- Coût nourrissement si nécessaire :
- Revenu supplémentaire estimé :
- ROI du plan de transhumance :
- Seuil de rentabilité (nb kg miel minimum) :

## 🚛 5. Logistique pratique
- Type de transport recommandé (camion, remorque)
- Heure de déplacement (nuit recommandée)
- Préparation des ruches avant transport
- Documents nécessaires (certificat sanitaire, etc.)
- Contacts utiles (DSA locale, association apicole régionale)

## ⚠️ 6. Risques et mitigation
- Risques climatiques par saison
- Risques sanitaires (nouveaux pathogènes en zone destination)
- Plan B si floraison décalée

## ✅ 7. Plan d'action en 10 étapes
Checklist pratique pour la transhumance.

Adapte tes recommandations aux spécificités du terrain algérien (Atlas, Tell, steppes, Sahara).
Cite des régions réelles d'Algérie reconnues pour leur potentiel mellifère."""

            with st.spinner("🚁 Génération du plan de transhumance IA... (20-30 secondes)"):
                result = ia_call(prompt_th, img_bytes)
            if result and not result.startswith("❌"):
                afficher_resultat_ia(result, f"Plan de transhumance — {loc_actuelle} → {mois_depart}")
                log_action("Transhumance IA", f"{nb_ruches_th} ruches depuis {loc_actuelle}")

                # Sauvegarder
                with st.form("save_th"):
                    nom_plan = st.text_input("Sauvegarder ce plan", f"Transhumance {mois_depart} — {nb_ruches_th} ruches")
                    if st.form_submit_button("💾 Sauvegarder dans le journal"):
                        log_action("Plan transhumance sauvegardé", nom_plan)
                        st.success(f"✅ Plan '{nom_plan}' sauvegardé dans le journal.")
            elif result:
                st.error(result)

    with tab2:
        conn = get_db()
        df_zones = pd.read_sql("SELECT * FROM zones ORDER BY potentiel DESC", conn)
        conn.close()
        if not df_zones.empty:
            st.dataframe(df_zones, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune zone enregistrée. Ajoutez des zones via la Cartographie.")

    with tab3:
        conn = get_db()
        df_th = pd.read_sql("""
            SELECT timestamp, action, details FROM journal
            WHERE action LIKE '%transhumance%' OR action LIKE '%Transhumance%'
            ORDER BY timestamp DESC
        """, conn)
        conn.close()
        if not df_th.empty:
            st.dataframe(df_th, use_container_width=True, hide_index=True)
        else:
            st.info("Aucun plan de transhumance enregistré.")


# ════════════════════════════════════════════════════════════════════════════
# PAGE : BOURSE AUX MÂLES (Collaboratif Anonymisé)
# ════════════════════════════════════════════════════════════════════════════
def page_bourse_males():
    st.markdown("## 🧫 Bourse aux Mâles — Échange Collaboratif Anonymisé")
    st.markdown("""
    <div style='background:#1E2010;border:1px solid #4A3A10;border-left:4px solid #FBD147;
                border-radius:8px;padding:14px;font-size:.84rem;color:#FDE68A;margin-bottom:16px'>
    <b>🧫 Optimisez la génétique de votre rucher par échange de faux-bourdons.</b>
    Partagez anonymement vos données génétiques et trouvez des mâles complémentaires
    pour améliorer la diversité génétique et la productivité de vos colonies.
    </div>
    """, unsafe_allow_html=True)

    ia_active = widget_cle_api()

    tab1, tab2, tab3 = st.tabs(["📤 Publier une offre", "📥 Chercher des mâles", "🤖 Analyse IA compatibilité"])

    with tab1:
        st.markdown("### Publier une offre de mâles (anonymisée)")
        st.markdown("""
        <div style='font-size:.8rem;color:#A8B4CC;background:#1E2535;border:1px solid #2E3A52;
                    border-radius:6px;padding:10px;margin-bottom:12px'>
        ✅ Vos données sont <b>anonymisées</b> — seule la région est visible pour les autres apiculteurs.
        Votre identité, le nom de votre rucher et les coordonnées exactes ne sont jamais partagés.
        </div>
        """, unsafe_allow_html=True)

        with st.form("offre_males"):
            col1, col2 = st.columns(2)
            region = col1.selectbox("Région (visible)", [
                "Tlemcen","Oran","Alger","Constantine","Annaba","Sétif","Béjaïa",
                "Tizi Ouzou","Blida","Médéa","Batna","Biskra","Ouargla","Autre"
            ], key="bm_region")
            race = col2.selectbox("Race des mâles", [
                "A.m. intermissa","A.m. sahariensis","A.m. ligustica",
                "A.m. carnica","Hybride sélectionné","Autre"
            ], key="bm_race")
            col3, col4 = st.columns(2)
            vsh_score = col3.slider("Score VSH (%)", 0, 100, 75, key="bm_vsh")
            productivite = col4.slider("Productivité relative (%)", 0, 200, 120, key="bm_prod")
            col5, col6 = st.columns(2)
            douceur = col5.slider("Douceur (1=agressive, 5=très douce)", 1, 5, 4, key="bm_douc")
            saison_dispo = col6.multiselect("Disponibilité",
                ["Janvier","Février","Mars","Avril","Mai","Juin",
                 "Juillet","Août","Septembre","Octobre","Novembre","Décembre"],
                default=["Avril","Mai","Juin"], key="bm_saison")
            notes_offre = st.text_area("Caractéristiques supplémentaires",
                placeholder="Ex: lignée sélectionnée sur 5 générations, excellente économie hivernale, faible essaimage...",
                height=80, key="bm_notes")
            submit_offre = st.form_submit_button("📤 Publier l'offre")

        if submit_offre:
            conn = get_db()
            conn.execute("""
                INSERT INTO journal (action, details, utilisateur)
                VALUES (?, ?, ?)
            """, ("Bourse aux mâles — Offre publiée",
                  f"Race:{race} | VSH:{vsh_score}% | Prod:{productivite}% | "
                  f"Douceur:{douceur}/5 | Région:{region} | Saisons:{','.join(saison_dispo)}",
                  "anonyme"))
            conn.commit()
            conn.close()
            st.success(f"✅ Offre publiée anonymement pour la région {region} !")

    with tab2:
        st.markdown("### Rechercher des mâles complémentaires")
        col_r1, col_r2, col_r3 = st.columns(3)
        race_cible = col_r1.selectbox("Race recherchée", [
            "Toutes races","A.m. intermissa","A.m. sahariensis",
            "A.m. ligustica","A.m. carnica","Hybride"
        ], key="bm_cible")
        vsh_min = col_r2.slider("VSH minimum (%)", 0, 100, 60, key="bm_vsh_min")
        region_cible = col_r3.selectbox("Région", [
            "Toutes régions","Tlemcen","Oran","Alger","Constantine","Béjaïa","Sétif"
        ], key="bm_reg_cible")

        conn = get_db()
        df_offres = pd.read_sql("""
            SELECT timestamp, details FROM journal
            WHERE action = 'Bourse aux mâles — Offre publiée'
            ORDER BY timestamp DESC LIMIT 20
        """, conn)
        conn.close()

        if not df_offres.empty:
            st.markdown("#### Offres disponibles :")
            for _, row in df_offres.iterrows():
                details = row["details"]
                if race_cible != "Toutes races" and race_cible not in details:
                    continue
                if region_cible != "Toutes régions" and region_cible not in details:
                    continue
                st.markdown(f"""
                <div style='background:#1E2535;border:1px solid #2E3A52;border-radius:8px;
                            padding:10px 14px;margin-bottom:6px'>
                    <div style='color:#FDE68A;font-weight:600;font-size:.82rem'>{details.split('|')[0].strip()}</div>
                    <div style='color:#A8B4CC;font-size:.78rem;margin-top:2px'>{details}</div>
                    <div style='color:#6B7A99;font-size:.72rem;margin-top:2px'>Publié le {row["timestamp"][:10]}</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Aucune offre disponible pour le moment. Soyez le premier à publier !")

    with tab3:
        st.markdown("### Analyse IA de compatibilité génétique")
        if not ia_active:
            st.info("🔑 Configurez votre clé API pour utiliser l'analyse IA.")
        else:
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                st.markdown("**Votre reine actuelle**")
                race_reine = st.selectbox("Race reine", ["intermissa","sahariensis","ligustica","carnica"], key="bm_reine")
                vsh_reine = st.slider("VSH reine (%)", 0, 100, 65, key="bm_vsh_r")
                prod_reine = st.slider("Productivité reine (%)", 0, 200, 110, key="bm_prod_r")
            with col_c2:
                st.markdown("**Mâles cibles**")
                race_males = st.selectbox("Race mâles", ["intermissa","sahariensis","ligustica","carnica"], key="bm_males")
                vsh_males = st.slider("VSH mâles (%)", 0, 100, 80, key="bm_vsh_m")
                prod_males = st.slider("Productivité mâles (%)", 0, 200, 130, key="bm_prod_m")

            btn_compat = st.button("🧬 Analyser la compatibilité génétique",
                                    use_container_width=True, key="btn_compat")
            if btn_compat:
                prompt_compat = f"""Tu es généticien apicole expert en amélioration des races d'abeilles.

Analyse la compatibilité génétique entre :
**Reine :** {race_reine} | VSH: {vsh_reine}% | Productivité: {prod_reine}%
**Mâles :** {race_males} | VSH: {vsh_males}% | Productivité: {prod_males}%

## 🧬 1. Compatibilité génétique
- Niveau de compatibilité : Excellente / Bonne / Acceptable / Déconseillée / Incompatible
- Risque de consanguinité : Faible / Modéré / Élevé
- Diversité allélique attendue chez la descendance

## 📊 2. Prédiction des performances de la descendance
| Caractère | Valeur estimée | Héritabilité |
- VSH attendu (%) :
- Productivité miel (%) :
- Douceur (1-5) :
- Économie hivernale :
- Tendance à l'essaimage :
- Résistance aux maladies :

## 🌟 3. Hétérosis (vigueur hybride)
- Gain attendu par hétérosis (%) :
- Caractères bénéficiant le plus du croisement :

## ⚠️ 4. Risques génétiques
- Amplification de traits négatifs possibles
- Instabilité comportementale (agressivité F1 ?)
- Recommandation : croisement conseillé ou non ?

## ✅ 5. Recommandation finale
Score de compatibilité global : X/10
Action recommandée pour l'apiculteur."""

                with st.spinner("🧬 Analyse de compatibilité en cours..."):
                    result = ia_call(prompt_compat)
                if result and not result.startswith("❌"):
                    afficher_resultat_ia(result, f"Compatibilité génétique {race_reine} × {race_males}")
                elif result:
                    st.error(result)


# ════════════════════════════════════════════════════════════════════════════
# PAGE : GÉNÉALOGIE PRÉDICTIVE (Pedigree & Consanguinité)
# ════════════════════════════════════════════════════════════════════════════
def page_genealogie():
    st.markdown("## 🌳 Généalogie Prédictive — Pedigree & Consanguinité")
    st.markdown("""
    <div style='background:#0D2A1F;border:1px solid #1A5C3A;border-left:4px solid #34D399;
                border-radius:8px;padding:14px;font-size:.84rem;color:#6EE7B7;margin-bottom:16px'>
    <b>🌳 Gérez le pedigree de vos reines et anticipez les effets de la consanguinité.</b>
    L'IA prédit les performances des descendances et recommande les meilleurs croisements
    pour maintenir la vigueur génétique de votre rucher.
    </div>
    """, unsafe_allow_html=True)

    ia_active = widget_cle_api()

    tab1, tab2, tab3 = st.tabs(["📋 Registre des reines", "🧬 Calcul consanguinité", "🔮 Prédiction descendance"])

    with tab1:
        st.markdown("### Registre généalogique des reines")
        conn = get_db()

        with st.form("add_reine_gene"):
            st.markdown("**Ajouter une reine au registre**")
            col1, col2, col3 = st.columns(3)
            nom_reine = col1.text_input("Nom / ID reine", placeholder="Ex: R01-Q2025")
            ruche_id_g = col2.selectbox("Ruche",
                [f"R{r[0]:02d} — {r[1]}" for r in conn.execute(
                    "SELECT id,nom FROM ruches WHERE statut='actif'").fetchall()],
                key="gene_ruche")
            race_g = col3.selectbox("Race", ["intermissa","sahariensis","ligustica","carnica","hybride"], key="gene_race")
            col4, col5, col6 = st.columns(3)
            date_naiss = col4.date_input("Date naissance", datetime.date.today(), key="gene_date")
            mere_id = col5.text_input("ID mère (si connu)", placeholder="Ex: R02-Q2024")
            pere_id = col6.text_input("ID père/faux-bourdon", placeholder="Ex: MB-Oran-2024")
            col7, col8, col9 = st.columns(3)
            vsh_g = col7.slider("VSH (%)", 0, 100, 70, key="gene_vsh")
            prod_g = col8.slider("Productivité (%)", 0, 200, 100, key="gene_prod")
            douc_g = col9.slider("Douceur (1-5)", 1, 5, 4, key="gene_douc")
            notes_g = st.text_area("Notes généalogiques", height=60, key="gene_notes")
            submitted_g = st.form_submit_button("✅ Ajouter au registre")

        if submitted_g and nom_reine:
            conn.execute("""
                INSERT INTO journal (action, details, utilisateur) VALUES (?,?,?)
            """, ("Généalogie — Reine enregistrée",
                  f"ID:{nom_reine} | Race:{race_g} | Mère:{mere_id or 'Inconnue'} | "
                  f"Père:{pere_id or 'Inconnu'} | VSH:{vsh_g}% | Prod:{prod_g}% | "
                  f"Douceur:{douc_g}/5 | Naissance:{date_naiss} | Notes:{notes_g[:100]}",
                  st.session_state.get("username","admin")))
            conn.commit()
            st.success(f"✅ Reine '{nom_reine}' ajoutée au registre généalogique !")

        # Affichage du registre
        df_reines = pd.read_sql("""
            SELECT timestamp as 'Date', details as 'Données généalogiques'
            FROM journal WHERE action = 'Généalogie — Reine enregistrée'
            ORDER BY timestamp DESC
        """, conn)
        conn.close()

        if not df_reines.empty:
            st.markdown("#### Registre actuel")
            st.dataframe(df_reines, use_container_width=True, hide_index=True)
            csv = df_reines.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Exporter registre CSV", csv, "registre_genealogique.csv", "text/csv")
        else:
            st.info("Aucune reine enregistrée. Ajoutez vos reines ci-dessus.")

    with tab2:
        st.markdown("### Calcul du coefficient de consanguinité")
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            id_reine_f = st.text_input("ID Reine à évaluer", placeholder="R01-Q2025", key="cog_reine")
            gen_connues = st.slider("Générations connues", 1, 6, 3, key="cog_gen")
            notes_pedigree = st.text_area(
                "Historique du pedigree (décrivez la lignée)",
                placeholder="Ex: Génération 1: reine R01 (intermissa) × mâles Oran\n"
                            "Génération 2: fille de R01 × mâles Tlemcen\n...",
                height=120, key="cog_notes"
            )
        with col_a2:
            st.markdown("#### Indicateurs de consanguinité")
            indicateurs = [
                ("F < 5%", "✅ Excellente diversité génétique"),
                ("F 5-10%", "🟡 Diversité acceptable, surveiller"),
                ("F 10-25%", "🟠 Consanguinité modérée — renouveler les mâles"),
                ("F > 25%", "🔴 Consanguinité élevée — apport génétique extérieur urgent"),
            ]
            for niveau, desc in indicateurs:
                color = "#6EE7B7" if "✅" in desc else "#FDE68A" if "🟡" in desc else "#FCA5A5"
                st.markdown(f"""
                <div style='padding:6px 10px;background:#1E2535;border-radius:5px;margin-bottom:4px'>
                    <span style='color:{color};font-weight:600;font-size:.8rem'>{niveau}</span>
                    <span style='color:#A8B4CC;font-size:.78rem;margin-left:8px'>{desc}</span>
                </div>""", unsafe_allow_html=True)

        btn_cog = st.button("🧮 Calculer la consanguinité", use_container_width=True,
                             disabled=not ia_active or not notes_pedigree, key="btn_cog")
        if btn_cog and notes_pedigree:
            prompt_cog = f"""Tu es généticien des populations apicoles. Calcule et analyse la consanguinité.

Reine : {id_reine_f}
Générations connues : {gen_connues}
Pedigree :
{notes_pedigree}

## 📊 1. Calcul du coefficient de consanguinité (F)
- Valeur F estimée (%) :
- Niveau : Faible / Modéré / Élevé / Critique
- Méthode de calcul utilisée

## 🔬 2. Analyse de la diversité génétique
- Nombre d'allèles distincts estimés
- Hétérozygotie attendue (%)
- Points de blocage génétique identifiés

## 📉 3. Impacts sur les performances
- Dépression de consanguinité attendue sur : productivité, VSH, longévité des reines
- Risque de sexe-allèles identiques → couvain mosaïque

## ✅ 4. Plan de régénération génétique
- Urgence d'intervention : Faible / Modérée / Urgente / Critique
- Sources de mâles recommandées
- Stratégie de croisement sur 2-3 générations
- Délai avant amélioration mesurable"""

            with st.spinner("🧮 Calcul consanguinité en cours..."):
                result = ia_call(prompt_cog)
            if result and not result.startswith("❌"):
                afficher_resultat_ia(result, f"Analyse consanguinité — {id_reine_f}")
            elif result:
                st.error(result)

    with tab3:
        st.markdown("### Prédiction IA des performances de la descendance")
        if not ia_active:
            st.info("🔑 Configurez votre clé API.")
        else:
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.markdown("**Reine mère**")
                vsh_mere = st.slider("VSH mère (%)", 0, 100, 72, key="pred_vsh_m")
                prod_mere = st.slider("Productivité mère (%)", 0, 200, 115, key="pred_prod_m")
                douc_mere = st.slider("Douceur mère", 1, 5, 4, key="pred_douc_m")
                race_mere = st.selectbox("Race mère", ["intermissa","sahariensis","ligustica","carnica"], key="pred_race_m")
            with col_p2:
                st.markdown("**Faux-bourdons (pères)**")
                vsh_pere = st.slider("VSH pères (%)", 0, 100, 80, key="pred_vsh_p")
                prod_pere = st.slider("Productivité pères (%)", 0, 200, 125, key="pred_prod_p")
                douc_pere = st.slider("Douceur pères", 1, 5, 4, key="pred_douc_p")
                race_pere = st.selectbox("Race pères", ["intermissa","sahariensis","ligustica","carnica"], key="pred_race_p")

            btn_pred = st.button("🔮 Prédire les performances de la descendance",
                                  use_container_width=True, key="btn_pred")
            if btn_pred:
                prompt_pred = f"""Tu es spécialiste en génétique quantitative apicole.

**Reine mère:** {race_mere} | VSH:{vsh_mere}% | Prod:{prod_mere}% | Douceur:{douc_mere}/5
**Faux-bourdons:** {race_pere} | VSH:{vsh_pere}% | Prod:{prod_pere}% | Douceur:{douc_pere}/5

## 🔮 Prédiction des performances F1 (descendance directe)
| Caractère | Valeur prédite | IC 95% | Héritabilité h² |
- VSH (%) :
- Production miel (% relatif) :
- Douceur (1-5) :
- Économie hivernale :
- Tendance essaimage :
- Résistance nosémose :
- Longévité reine (mois) :

## 📈 Courbe de progrès génétique
Si sélection sur 3-5 générations :
| Génération | VSH attendu | Productivité | Douceur |

## 🌟 Hétérosis attendu
Gain par rapport aux valeurs parentales moyennes : +X%

## 💡 Recommandation de sélection
- Meilleurs individus à conserver pour l'élevage
- Critères de sélection prioritaires pour ce croisement
- Objectif à atteindre en 3 générations"""

                with st.spinner("🔮 Prédiction génétique en cours..."):
                    result = ia_call(prompt_pred)
                if result and not result.startswith("❌"):
                    afficher_resultat_ia(result, f"Prédiction descendance {race_mere} × {race_pere}")
                elif result:
                    st.error(result)


# ════════════════════════════════════════════════════════════════════════════
# PAGE : ASSISTANT VOCAL IA "EN RUCHE" (Hands-Free)
# ════════════════════════════════════════════════════════════════════════════
def page_assistant_vocal():
    st.markdown("## 🎤 Assistant IA 'En Ruche' — Inspection Mains Libres")
    st.markdown("""
    <div style='background:#161B27;border:1px solid #3A4A66;border-left:4px solid #F5A623;
                border-radius:8px;padding:14px;font-size:.84rem;color:#A8B4CC;margin-bottom:16px'>
    <b>🎤 Dictez vos observations pendant l'inspection sans poser vos outils.</b>
    Tapez (ou dictez) vos observations en langage naturel.
    L'IA structure automatiquement les données, remplit les formulaires et génère les alertes.
    </div>
    """, unsafe_allow_html=True)

    ia_active = widget_cle_api()

    tab1, tab2, tab3 = st.tabs(["🎙️ Saisie vocale / rapide", "📋 Rapports structurés", "💬 Chat apicole"])

    # ── TAB 1 : SAISIE VOCALE / RAPIDE ───────────────────────────────────────
    with tab1:
        st.markdown("### Inspection mains libres — Saisie en langage naturel")
        st.markdown("""
        <div style='font-size:.8rem;color:#A8B4CC;background:#1E2535;border:1px solid #2E3A52;
                    border-radius:6px;padding:10px;margin-bottom:12px'>
        <b>💡 Exemples de phrases :</b><br>
        "Ruche 3 — poids 24 kg, 9 cadres, varroa environ 1.5%, reine vue, comportement calme"<br>
        "R7 — abeilles agressives, pas de reine, varroa 4%, traitement urgent nécessaire"<br>
        "Ruche 1 — super, 12 cadres couverts, très douce, bonne réserve de miel"
        </div>
        """, unsafe_allow_html=True)

        conn = get_db()
        ruches = conn.execute("SELECT id, nom FROM ruches WHERE statut='actif'").fetchall()
        opts_ruche = {f"R{r[0]:02d} — {r[1]}": r[0] for r in ruches}

        col_v1, col_v2 = st.columns([1.5, 1])
        with col_v1:
            ruche_vocal = st.selectbox("Ruche inspectée", opts_ruche.keys(), key="vocal_ruche")
            observation = st.text_area(
                "🎙️ Vos observations (langage naturel)",
                placeholder="Ex: 'Ruche 1 poids 26 kilos, 11 cadres couverts, reine repérée dans le 4e cadre, "
                            "très douce, varroa estimé à 1%, bonne quantité de miel, pas d'anomalie...'",
                height=120,
                key="vocal_obs"
            )
            img_vocal = st.file_uploader("📷 Photo pendant l'inspection (optionnel)",
                                          type=["jpg","jpeg","png","webp"], key="vocal_img")
            if img_vocal: st.image(img_vocal, use_container_width=True, caption="Photo inspection")

            btn_vocal = st.button("🤖 Structurer + Enregistrer l'inspection",
                                   use_container_width=True,
                                   disabled=not ia_active or not observation.strip(),
                                   key="btn_vocal")

        with col_v2:
            st.markdown("#### L'IA va automatiquement :")
            actions = [
                "📊 Extraire : poids, cadres, varroa, reine",
                "⚠️ Générer des alertes si nécessaire",
                "💊 Recommander un traitement si varroa >2%",
                "📋 Créer l'enregistrement d'inspection",
                "🔮 Prédire la production selon l'état",
                "📅 Suggérer la prochaine date d'inspection",
                "📈 Comparer avec l'inspection précédente",
            ]
            for a in actions:
                st.markdown(f"""
                <div style='padding:4px 8px;background:#1E2535;border-radius:4px;margin-bottom:3px;
                            font-size:.8rem;color:#A8B4CC'>{a}</div>
                """, unsafe_allow_html=True)

        if btn_vocal and observation.strip():
            img_bytes = img_vocal.read() if img_vocal else None
            ruche_id = opts_ruche[ruche_vocal]

            # Récupère l'historique de cette ruche
            hist = conn.execute("""
                SELECT date_inspection, poids_kg, nb_cadres, varroa_pct, reine_vue, comportement, notes
                FROM inspections WHERE ruche_id=? ORDER BY date_inspection DESC LIMIT 3
            """, (ruche_id,)).fetchall()
            hist_str = "\n".join([
                f"  {h[0]}: {h[1]}kg, {h[2]} cadres, varroa {h[3]}%, reine={'vue' if h[4] else 'non vue'}"
                for h in hist
            ]) if hist else "Pas d'historique"

            prompt_vocal = f"""Tu es assistant apicole expert. Analyse cette observation d'inspection de ruche.

Ruche : {ruche_vocal}
Date : {datetime.date.today()}
Observations de l'apiculteur : "{observation}"

Historique récent de cette ruche :
{hist_str}

## 📊 1. DONNÉES STRUCTURÉES (extrait de l'observation)
Réponds avec des valeurs précises ou "non mentionné" :
- Poids estimé (kg) :
- Nombre de cadres couverts :
- Taux varroa estimé (%) :
- Reine vue : Oui / Non / Non mentionné
- Comportement : Calme / Nerveuse / Agressive / Non mentionné
- État du couvain : Bon / Irrégulier / Problème / Non mentionné
- Réserves miel : Bonnes / Insuffisantes / Non mentionné

## ⚠️ 2. ALERTES AUTOMATIQUES
Liste toutes les alertes déclenchées :
(🔴 si varroa ≥3%, reine absente confirmée | 🟡 si varroa 2-3%, comportement anormal)

## 💊 3. RECOMMANDATIONS IMMÉDIATES
Actions à faire dans les 24h / 7 jours / 30 jours.

## 📈 4. COMPARAISON AVEC HISTORIQUE
Évolution par rapport aux dernières inspections (meilleur / stable / dégradé).

## 🔮 5. PRÉDICTION PRODUCTION
Estimation production miel prochaine récolte (kg) basée sur l'état actuel.

## 📅 6. PROCHAINE INSPECTION RECOMMANDÉE
Date recommandée + points prioritaires à vérifier.

## ✅ 7. RÉSUMÉ EN 1 LIGNE
Synthèse de l'état de cette ruche aujourd'hui."""

            with st.spinner("🤖 Analyse et structuration de l'inspection..."):
                result = ia_call(prompt_vocal, img_bytes)

            if result and not result.startswith("❌"):
                afficher_resultat_ia(result, f"Inspection IA — {ruche_vocal}")

                # Auto-enregistrement de l'inspection
                import re
                poids_m = re.search(r'Poids.*?:\s*([\d.]+)', result)
                cadres_m = re.search(r'cadres.*?:\s*(\d+)', result)
                varroa_m = re.search(r'varroa.*?:\s*([\d.]+)', result, re.IGNORECASE)
                reine_m = re.search(r'Reine vue.*?:\s*(Oui|Non)', result, re.IGNORECASE)
                comport_m = re.search(r'Comportement.*?:\s*(\w+)', result)

                poids_val = float(poids_m.group(1)) if poids_m else None
                cadres_val = int(cadres_m.group(1)) if cadres_m else None
                varroa_val = float(varroa_m.group(1)) if varroa_m else None
                reine_val = 1 if reine_m and "oui" in reine_m.group(1).lower() else 0
                comport_val = comport_m.group(1).lower() if comport_m else "calme"

                if poids_val or cadres_val or varroa_val:
                    conn.execute("""
                        INSERT INTO inspections
                        (ruche_id,date_inspection,poids_kg,nb_cadres,varroa_pct,reine_vue,comportement,notes)
                        VALUES (?,?,?,?,?,?,?,?)
                    """, (ruche_id, str(datetime.date.today()), poids_val, cadres_val,
                          varroa_val, reine_val, comport_val,
                          f"[IA Vocal] {observation[:200]}"))
                    conn.commit()
                    st.success("✅ Inspection enregistrée automatiquement dans la base de données !")

                    if varroa_val and varroa_val >= 3.0:
                        st.error(f"🔴 ALERTE CRITIQUE : Varroa {varroa_val}% sur {ruche_vocal} — Traitement immédiat !")
                    elif varroa_val and varroa_val >= 2.0:
                        st.warning(f"🟡 Attention : Varroa {varroa_val}% sur {ruche_vocal}")

                log_action("Inspection vocale IA", f"{ruche_vocal}: {observation[:100]}")
            elif result:
                st.error(result)

        conn.close()

    # ── TAB 2 : RAPPORTS STRUCTURÉS ──────────────────────────────────────────
    with tab2:
        st.markdown("### Rapports d'inspection par voix / texte rapide")
        conn = get_db()
        st.markdown("**Dernières inspections enregistrées par assistant vocal :**")
        df_vocal = pd.read_sql("""
            SELECT i.date_inspection, r.nom as ruche, i.poids_kg,
                   i.nb_cadres, i.varroa_pct, i.reine_vue, i.comportement, i.notes
            FROM inspections i JOIN ruches r ON r.id=i.ruche_id
            WHERE i.notes LIKE '%[IA Vocal]%'
            ORDER BY i.date_inspection DESC LIMIT 20
        """, conn)
        conn.close()

        if not df_vocal.empty:
            df_vocal["reine_vue"] = df_vocal["reine_vue"].apply(lambda x: "✓" if x else "✗")
            st.dataframe(df_vocal, use_container_width=True, hide_index=True)
            csv = df_vocal.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Exporter CSV", csv, "inspections_vocal.csv", "text/csv")
        else:
            st.info("Aucune inspection vocale enregistrée pour le moment.")

    # ── TAB 3 : CHAT APICOLE ─────────────────────────────────────────────────
    with tab3:
        st.markdown("### 💬 Chat avec l'expert apicole IA")
        st.markdown("""
        <div style='font-size:.8rem;color:#A8B4CC;background:#1E2535;border:1px solid #2E3A52;
                    border-radius:6px;padding:10px;margin-bottom:12px'>
        Posez n'importe quelle question apicole. L'IA répond en expert adapté à votre contexte
        (Algérie, races locales, conditions climatiques méditerranéennes et sahariennes).
        </div>
        """, unsafe_allow_html=True)

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        # Afficher l'historique
        for msg in st.session_state.chat_history:
            role_color = "#F5A623" if msg["role"] == "assistant" else "#60A5FA"
            role_label = "🤖 Expert IA" if msg["role"] == "assistant" else "👤 Vous"
            st.markdown(f"""
            <div style='background:#1E2535;border:1px solid #2E3A52;border-radius:8px;
                        padding:10px 14px;margin-bottom:8px;
                        border-left:3px solid {role_color}'>
                <div style='color:{role_color};font-weight:600;font-size:.78rem;margin-bottom:4px'>{role_label}</div>
                <div style='color:#F0F4FF;font-size:.85rem'>{msg["content"]}</div>
            </div>""", unsafe_allow_html=True)

        question = st.text_input(
            "Votre question",
            placeholder="Ex: Comment traiter la varroose en été sans retirer les hausses ?",
            key="chat_question"
        )
        col_chat1, col_chat2 = st.columns([3,1])
        btn_chat = col_chat1.button("💬 Envoyer", use_container_width=True,
                                     disabled=not ia_active or not question.strip(),
                                     key="btn_chat")
        if col_chat2.button("🗑️ Effacer", use_container_width=True, key="btn_clear_chat"):
            st.session_state.chat_history = []
            st.rerun()

        if btn_chat and question.strip():
            st.session_state.chat_history.append({"role": "user", "content": question})
            hist_ctx = "\n".join([
                f"{'Apiculteur' if m['role']=='user' else 'Expert'}: {m['content']}"
                for m in st.session_state.chat_history[-6:]
            ])
            prompt_chat = f"""Tu es un expert apicole senior, passionné et pédagogue, spécialisé dans l'apiculture du Maghreb et de la Méditerranée (Algérie, Maroc, Tunisie). Tu réponds toujours en français, de manière pratique, concise et adaptée aux conditions locales.

Historique de la conversation :
{hist_ctx}

Réponds à la dernière question de manière experte, pratique et adaptée au contexte algérien/maghrébin.
Si tu donnes des traitements, précise les produits disponibles en Algérie.
Si tu parles de races, mentionne les races locales (intermissa, sahariensis) en priorité.
Sois direct et opérationnel. Maximum 300 mots."""

            with st.spinner("💬 L'expert IA réfléchit..."):
                result = ia_call(prompt_chat)

            if result and not result.startswith("❌"):
                st.session_state.chat_history.append({"role": "assistant", "content": result})
                st.rerun()
            elif result:
                st.error(result)


# ════════════════════════════════════════════════════════════════════════════
# ROUTEUR PRINCIPAL
# ════════════════════════════════════════════════════════════════════════════
def main():
    inject_css()
    init_db()

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        login_page()
        return

    sidebar()

    page = st.session_state.get("page", "dashboard")
    router = {
        "dashboard": page_dashboard,
        "ruches": page_ruches,
        "inspections": page_inspections,
        "traitements": page_traitements,
        "productions": page_productions,
        "morpho": page_morpho,
        "maladies_ia": page_maladies_ia,
        "carto": page_carto,
        "transhumance": page_transhumance,
        "bourse_males": page_bourse_males,
        "genealogie": page_genealogie,
        "assistant_vocal": page_assistant_vocal,
        "meteo": page_meteo,
        "genetique": page_genetique,
        "flore": page_flore,
        "alertes": page_alertes,
        "journal": page_journal,
        "admin": page_admin,
    }
    fn = router.get(page, page_dashboard)
    fn()

    st.markdown("""
    <div class='api-footer'>
        🐝 ApiTrack Pro v2.0 · Streamlit + Python + SQLite · Rucher de l'Atlas · 2025
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
