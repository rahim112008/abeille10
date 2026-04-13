"""
ApiTrack Pro – Application de gestion apicole professionnelle
Streamlit + Python + SQLite
VERSION 4.0 - AMÉLIORATIONS COMPLÈTES
- Changement de région dans Météo & Cartographie
- Inspection vocale fonctionnelle (navigateur via JS)
- Réponses IA entièrement en Français
- Carte satellite interactive avec sélection de point
- Chargement/Sauvegarde de données SQLite
- Suppression de ruches
- Système multi-utilisateurs avec comptes séparés
"""

import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import hashlib
import json
import os
import datetime
import base64
import tempfile
import urllib.request
import urllib.error
import re
import math
import io

import plotly.express as px
import plotly.graph_objects as go

try:
    import folium
    from streamlit_folium import st_folium
    FOLIUM_OK = True
except ImportError:
    FOLIUM_OK = False

try:
    import anthropic
    ANTHROPIC_OK = True
except ImportError:
    ANTHROPIC_OK = False

try:
    import networkx as nx
    NETWORKX_OK = True
except ImportError:
    NETWORKX_OK = False

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

try:
    from streamlit_drawable_canvas import st_canvas
    CANVAS_OK = True
except ImportError:
    CANVAS_OK = False

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
        --gold:#F5A623;--gold-light:#FFD07A;--gold-dark:#C8820A;
        --bg-app:#0F1117;--bg-main:#161B27;--bg-card:#1E2535;--bg-card2:#252D40;
        --bg-input:#1A2030;--border:#2E3A52;--border-light:#3A4A66;
        --text-primary:#F0F4FF;--text-second:#A8B4CC;--text-muted:#6B7A99;
        --green:#34D399;--green-bg:#0D2A1F;--green-border:#1A5C3A;
        --yellow:#FBD147;--red:#F87171;--red-bg:#2A0D0D;--blue:#60A5FA;
    }
    .stApp{background-color:var(--bg-app)!important;color:var(--text-primary)!important;font-family:'Inter',sans-serif!important}
    .main .block-container{padding:1.5rem 2rem;max-width:1400px;background:var(--bg-main)!important}
    .stApp p,.stApp span,.stApp div,.stApp label,.stMarkdown,.stMarkdown p{color:var(--text-primary)!important}
    [data-testid="stSidebar"]{background:#080C14!important;border-right:1px solid var(--border)!important}
    [data-testid="stSidebar"] *{color:#C8D8F0!important}
    [data-testid="stSidebar"] button{background:transparent!important;color:#A8B4CC!important;border:none!important;
        text-align:left!important;font-size:0.875rem!important;padding:8px 12px!important;border-radius:6px!important}
    [data-testid="stSidebar"] button:hover{background:rgba(245,166,35,0.12)!important;color:var(--gold-light)!important}
    h1,h2,h3,h4,h5,h6,[data-testid="stMarkdownContainer"] h1,[data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3{color:var(--text-primary)!important;font-family:'Inter',sans-serif!important;font-weight:600!important}
    h2{font-size:1.4rem!important;border-bottom:1px solid var(--border);padding-bottom:10px;margin-bottom:16px}
    h3{font-size:1.05rem!important;color:var(--gold-light)!important}
    [data-testid="metric-container"]{background:var(--bg-card)!important;border:1px solid var(--border)!important;
        border-top:3px solid var(--gold)!important;border-radius:10px!important;padding:16px!important}
    [data-testid="stMetricValue"]{color:var(--gold-light)!important;font-size:2rem!important;font-weight:700!important}
    [data-testid="stMetricLabel"]{color:var(--text-second)!important;font-size:0.75rem!important;text-transform:uppercase!important;letter-spacing:0.06em!important}
    [data-testid="stMetricDelta"]{color:var(--green)!important}
    .stButton > button{background:var(--gold-dark)!important;color:#FFFFFF!important;border:none!important;
        border-radius:8px!important;font-weight:600!important;font-size:0.875rem!important;padding:8px 18px!important;transition:all 0.15s!important}
    .stButton > button:hover{background:var(--gold)!important;transform:translateY(-1px)!important;box-shadow:0 4px 12px rgba(245,166,35,0.3)!important}
    .stTextInput input,.stNumberInput input,.stTextArea textarea{background:var(--bg-input)!important;
        color:var(--text-primary)!important;border:1.5px solid var(--border-light)!important;border-radius:8px!important}
    .stTextInput input:focus,.stNumberInput input:focus,.stTextArea textarea:focus{border-color:var(--gold)!important;box-shadow:0 0 0 2px rgba(245,166,35,0.2)!important}
    [data-testid="stSelectbox"]>div>div{background:var(--bg-input)!important;color:var(--text-primary)!important;border:1.5px solid var(--border-light)!important;border-radius:8px!important}
    [data-testid="stSelectbox"] span,[data-testid="stSelectbox"] p{color:var(--text-primary)!important}
    .stDataFrame{border:1px solid var(--border)!important;border-radius:8px!important;overflow:hidden!important}
    .stDataFrame table{background:var(--bg-card)!important;color:var(--text-primary)!important}
    .stDataFrame thead th{background:var(--bg-card2)!important;color:var(--gold-light)!important;font-weight:600!important;font-size:0.78rem!important;text-transform:uppercase!important;border-bottom:1px solid var(--border)!important}
    .stDataFrame tbody td{color:var(--text-primary)!important;background:var(--bg-card)!important;border-bottom:1px solid var(--border)!important}
    [data-testid="stTabs"] [role="tablist"]{background:var(--bg-card)!important;border-bottom:1px solid var(--border)!important;border-radius:8px 8px 0 0!important}
    [data-testid="stTabs"] button[role="tab"]{color:var(--text-second)!important;font-weight:500!important;background:transparent!important;border:none!important;border-bottom:2px solid transparent!important}
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"]{color:var(--gold)!important;border-bottom:2px solid var(--gold)!important;font-weight:600!important}
    [data-testid="stTabsContent"]{background:var(--bg-card)!important;border:1px solid var(--border)!important;border-top:none!important;border-radius:0 0 8px 8px!important;padding:16px!important}
    [data-testid="stExpander"]{background:var(--bg-card)!important;border:1px solid var(--border)!important;border-radius:8px!important}
    [data-testid="stExpander"] summary{color:var(--text-primary)!important;font-weight:500!important;background:var(--bg-card)!important}
    [data-testid="stFileUploader"]{background:var(--bg-input)!important;border:1.5px dashed var(--border-light)!important;border-radius:8px!important}
    [data-testid="stDownloadButton"] button{background:var(--bg-card2)!important;color:var(--gold-light)!important;border:1px solid var(--gold-dark)!important;border-radius:8px!important}
    [data-testid="stFormSubmitButton"] button{background:var(--gold-dark)!important;color:#FFFFFF!important;font-weight:600!important;border-radius:8px!important;width:100%!important}
    hr{border-color:var(--border)!important}
    a{color:var(--gold-light)!important}
    code{background:var(--bg-card2)!important;color:var(--gold-light)!important;padding:1px 6px!important;border-radius:4px!important;font-family:'JetBrains Mono',monospace!important}
    ::-webkit-scrollbar{width:8px;height:8px}
    ::-webkit-scrollbar-track{background:var(--bg-app)}
    ::-webkit-scrollbar-thumb{background:var(--border-light);border-radius:4px}
    .api-footer{text-align:center;font-size:0.72rem;color:var(--text-muted);padding:12px;border-top:1px solid var(--border);margin-top:2rem;font-family:'JetBrains Mono',monospace;background:var(--bg-card);border-radius:0 0 8px 8px}
    .badge-ok{background:#0D2A1F;color:#6EE7B7;border:1px solid #1A5C3A;padding:3px 10px;border-radius:20px;font-size:0.72rem;font-weight:600}
    .badge-warn{background:#2A200A;color:#FDE68A;border:1px solid #4A3A10;padding:3px 10px;border-radius:20px;font-size:0.72rem;font-weight:600}
    .badge-crit{background:#2A0D0D;color:#FCA5A5;border:1px solid #5C1A1A;padding:3px 10px;border-radius:20px;font-size:0.72rem;font-weight:600}
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
        role TEXT DEFAULT 'apiculteur',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS ruches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
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
        user_id INTEGER REFERENCES users(id),
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
        user_id INTEGER NOT NULL,
        key TEXT NOT NULL,
        value TEXT,
        PRIMARY KEY (user_id, key)
    );
    CREATE TABLE IF NOT EXISTS pedigree (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reine_fille_id INTEGER REFERENCES ruches(id),
        reine_mere_id INTEGER REFERENCES ruches(id),
        ruche_pere_id INTEGER REFERENCES ruches(id),
        date_naissance TEXT,
        methode_fecondation TEXT DEFAULT 'naturelle',
        notes TEXT
    );
    CREATE TABLE IF NOT EXISTS voice_inspections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ruche_id INTEGER REFERENCES ruches(id),
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        transcription TEXT,
        actions_extraites TEXT
    );
    CREATE TABLE IF NOT EXISTS male_stocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ruche_id INTEGER UNIQUE REFERENCES ruches(id),
        race_male TEXT,
        score_vsh INTEGER,
        disponibilite BOOLEAN DEFAULT 1,
        rayon_km INTEGER DEFAULT 5,
        contact_prefere TEXT,
        date_mise_a_jour TEXT
    );
    CREATE TABLE IF NOT EXISTS transhumance_predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        zone_id INTEGER REFERENCES zones(id),
        date_prediction TEXT,
        potentiel_miel REAL,
        recommandation TEXT,
        meteo_json TEXT
    );
    """)

    # Créer les comptes par défaut
    comptes = [
        ("admin", "admin1234", "admin@apitrack.pro", "admin"),
        ("ami1",  "ami11234",  "ami1@apitrack.pro",  "apiculteur"),
        ("ami2",  "ami21234",  "ami2@apitrack.pro",  "apiculteur"),
        ("ami3",  "ami31234",  "ami3@apitrack.pro",  "apiculteur"),
    ]
    for username, pwd, email, role in comptes:
        h = hashlib.sha256(pwd.encode()).hexdigest()
        c.execute("INSERT OR IGNORE INTO users (username,password_hash,email,role) VALUES (?,?,?,?)",
                  (username, h, email, role))

    conn.commit()
    # Insérer les données démo pour admin
    admin = conn.execute("SELECT id FROM users WHERE username='admin'").fetchone()
    if admin:
        _insert_demo_data(c, admin[0])
    conn.commit()
    conn.close()


def _insert_demo_data(c, user_id):
    existing = c.execute("SELECT COUNT(*) FROM ruches WHERE user_id=?", (user_id,)).fetchone()[0]
    if existing > 0:
        return
    ruches_demo = [
        ("Zitoun A","intermissa","2023-03-15","Zone Atlas Nord",34.88,1.32,"actif"),
        ("Sahara B","sahariensis","2023-04-01","Zone Jujubiers",34.85,1.35,"actif"),
        ("Atlas C","hybride","2022-05-20","Zone Cèdres",34.90,1.28,"actif"),
        ("Cedre D","intermissa","2023-02-10","Zone Atlas Sud",34.82,1.31,"actif"),
        ("Cedre E","intermissa","2024-03-01","Zone Atlas Nord",34.89,1.33,"actif"),
        ("Oued F","intermissa","2024-04-15","Bord Oued",34.87,1.30,"actif"),
    ]
    ids = []
    for r in ruches_demo:
        c.execute("INSERT INTO ruches (user_id,nom,race,date_installation,localisation,latitude,longitude,statut) VALUES (?,?,?,?,?,?,?,?)",
                  (user_id,)+r)
        ids.append(c.lastrowid)

    today = datetime.date.today()
    inspections_demo = [
        (ids[0],str(today),28.4,12,0.8,1,"calme","Excellent couvain"),
        (ids[1],str(today-datetime.timedelta(days=1)),25.6,10,1.2,1,"calme","RAS"),
        (ids[2],str(today-datetime.timedelta(days=2)),22.1,9,2.4,0,"nerveuse","Reine introuvable"),
        (ids[3],str(today-datetime.timedelta(days=3)),26.9,11,1.1,1,"très calme","Top productrice"),
        (ids[5],str(today-datetime.timedelta(days=1)),19.2,7,3.8,1,"agressive","Traitement urgent"),
    ]
    for i in inspections_demo:
        c.execute("INSERT INTO inspections (ruche_id,date_inspection,poids_kg,nb_cadres,varroa_pct,reine_vue,comportement,notes) VALUES (?,?,?,?,?,?,?,?)", i)

    recoltes_demo = [
        (ids[0],"2025-03-01","miel",48.0,17.2,3.8,None,"A"),
        (ids[1],"2025-03-01","miel",32.0,17.8,3.9,None,"A"),
        (ids[0],"2025-01-15","pollen",4.5,None,None,None,"A"),
        (ids[3],"2025-03-15","gelée royale",0.6,None,None,2.1,"A+"),
        (ids[0],"2024-09-01","miel",62.0,17.0,3.7,None,"A"),
    ]
    for r in recoltes_demo:
        c.execute("INSERT INTO recoltes (ruche_id,date_recolte,type_produit,quantite_kg,humidite_pct,ph,hda_pct,qualite) VALUES (?,?,?,?,?,?,?,?)", r)

    zones_demo = [
        ("Forêt chênes-lièges","nectar+pollen",34.88,1.31,120.0,"Quercus suber",0.72,"élevé"),
        ("Jujubiers Est","nectar",34.86,1.34,45.0,"Ziziphus lotus",0.65,"élevé"),
        ("Lavande Sud","pollen",34.83,1.30,18.0,"Lavandula stoechas",0.58,"modéré"),
    ]
    for z in zones_demo:
        c.execute("INSERT INTO zones (user_id,nom,type_zone,latitude,longitude,superficie_ha,flore_principale,ndvi,potentiel) VALUES (?,?,?,?,?,?,?,?,?)",
                  (user_id,)+z)

    c.execute("INSERT OR IGNORE INTO settings VALUES (?,?,?)", (user_id,"rucher_nom","Rucher de l'Atlas"))
    c.execute("INSERT OR IGNORE INTO settings VALUES (?,?,?)", (user_id,"localisation","Tlemcen, Algérie"))
    c.execute("INSERT OR IGNORE INTO settings VALUES (?,?,?)", (user_id,"region_lat","34.88"))
    c.execute("INSERT OR IGNORE INTO settings VALUES (?,?,?)", (user_id,"region_lon","1.32"))
    c.execute("INSERT OR IGNORE INTO settings VALUES (?,?,?)", (user_id,"version","4.0.0"))


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
    col1, col2, col3 = st.columns([1,1.2,1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style='text-align:center;margin-bottom:24px'>
            <div style='font-size:3rem'>🐝</div>
            <h1 style='color:#F0F4FF;font-size:2rem;margin:8px 0 4px'>ApiTrack Pro</h1>
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
                st.session_state.user_id = user["id"]
                st.session_state.user_role = user["role"]
                log_action("Connexion", f"Utilisateur {username} connecté")
                st.rerun()
            else:
                st.error("Identifiants incorrects.")
        st.markdown("""
        <div style='background:#1E2535;border:1px solid #2E3A52;border-radius:8px;padding:12px;margin-top:16px;font-size:.8rem;color:#A8B4CC'>
        <b>Comptes disponibles :</b><br>
        admin / admin1234<br>
        ami1 / ami11234 · ami2 / ami21234 · ami3 / ami31234
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# UTILITAIRES
# ════════════════════════════════════════════════════════════════════════════
def get_user_id():
    return st.session_state.get("user_id", 1)

def log_action(action, details="", user=None):
    u = user or st.session_state.get("username","système")
    conn = get_db()
    conn.execute("INSERT INTO journal (action,details,utilisateur) VALUES (?,?,?)", (action,details,u))
    conn.commit()
    conn.close()

def status_badge(varroa):
    if varroa is None: return "N/A"
    if varroa >= 3.0: return "🔴 Critique"
    elif varroa >= 2.0: return "🟡 Surveiller"
    return "🟢 Bon"

def get_setting(key, default=""):
    uid = get_user_id()
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE user_id=? AND key=?", (uid,key)).fetchone()
    conn.close()
    return row[0] if row else default

def set_setting(key, value):
    uid = get_user_id()
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO settings VALUES (?,?,?)", (uid,key,value))
    conn.commit()
    conn.close()

def get_user_ruches():
    """Retourne uniquement les ruches de l'utilisateur connecté"""
    uid = get_user_id()
    conn = get_db()
    ruches = conn.execute("SELECT id, nom FROM ruches WHERE user_id=? AND statut='actif'", (uid,)).fetchall()
    conn.close()
    return {r[1]: r[0] for r in ruches}

# ════════════════════════════════════════════════════════════════════════════
# RÉGIONS PRÉDÉFINIES
# ════════════════════════════════════════════════════════════════════════════
REGIONS = {
    "Tlemcen, Algérie": (34.88, 1.32),
    "Alger, Algérie": (36.73, 3.08),
    "Oran, Algérie": (35.69, 0.64),
    "Constantine, Algérie": (36.36, 6.61),
    "Annaba, Algérie": (36.90, 7.76),
    "Béjaïa, Algérie": (36.75, 5.06),
    "Sétif, Algérie": (36.19, 5.40),
    "Biskra, Algérie": (34.85, 5.73),
    "Ghardaïa, Algérie": (32.49, 3.67),
    "Tamanrasset, Algérie": (22.78, 5.52),
    "Tunis, Tunisie": (36.81, 10.18),
    "Sfax, Tunisie": (34.74, 10.76),
    "Casablanca, Maroc": (33.59, -7.62),
    "Marrakech, Maroc": (31.63, -8.01),
    "Fès, Maroc": (34.03, -5.00),
    "Rabat, Maroc": (34.02, -6.83),
    "Tripoli, Libye": (32.90, 13.18),
    "Le Caire, Égypte": (30.04, 31.24),
    "Paris, France": (48.85, 2.35),
    "Lyon, France": (45.75, 4.83),
    "Marseille, France": (43.30, 5.37),
    "Bruxelles, Belgique": (50.85, 4.35),
    "Personnalisée": (None, None),
}

# ════════════════════════════════════════════════════════════════════════════
# MOTEUR IA MULTI-FOURNISSEURS
# ════════════════════════════════════════════════════════════════════════════
IA_PROVIDERS = {
    "🤖 Claude (Anthropic)": {
        "key":"anthropic_api_key","env":"ANTHROPIC_API_KEY",
        "url":"https://console.anthropic.com","prefix":"sk-ant-",
        "models":["claude-3-5-sonnet-20241022","claude-3-haiku-20240307"],
        "default":"claude-3-5-sonnet-20241022","quota":"~5$ crédits offerts",
        "vision":True,"type":"anthropic",
    },
    "🌟 Gemini (Google)": {
        "key":"google_api_key","env":"GOOGLE_API_KEY",
        "url":"https://aistudio.google.com/app/apikey","prefix":"AIzaSy",
        "models":["gemini-2.0-flash","gemini-1.5-flash"],
        "default":"gemini-2.0-flash","quota":"Gratuit · 1500 req/jour",
        "vision":True,"type":"google",
    },
    "⚡ Groq (Ultra-rapide)": {
        "key":"groq_api_key","env":"GROQ_API_KEY",
        "url":"https://console.groq.com/keys","prefix":"gsk_",
        "models":["llama-3.3-70b-versatile","llama-3.1-8b-instant"],
        "default":"llama-3.3-70b-versatile","quota":"Gratuit · 30 RPM",
        "vision":False,"type":"openai_compat","base_url":"https://api.groq.com/openai/v1",
    },
    "🔀 OpenRouter (Multi-modèles)": {
        "key":"openrouter_api_key","env":"OPENROUTER_API_KEY",
        "url":"https://openrouter.ai/keys","prefix":"sk-or-",
        "models":["meta-llama/llama-4-maverick:free","deepseek/deepseek-r1:free"],
        "default":"meta-llama/llama-4-maverick:free","quota":"Gratuit · ~50 req/jour",
        "vision":False,"type":"openai_compat","base_url":"https://openrouter.ai/api/v1",
    },
    "🌍 Mistral AI (GDPR)": {
        "key":"mistral_api_key","env":"MISTRAL_API_KEY",
        "url":"https://console.mistral.ai/api-keys","prefix":"",
        "models":["mistral-large-latest","mistral-small-latest"],
        "default":"mistral-large-latest","quota":"Gratuit · 1 req/s",
        "vision":False,"type":"openai_compat","base_url":"https://api.mistral.ai/v1",
    },
}

def get_active_provider():
    return get_setting("ia_provider", list(IA_PROVIDERS.keys())[0])

def get_active_model():
    provider = get_active_provider()
    saved = get_setting("ia_model","")
    if saved and saved in IA_PROVIDERS.get(provider,{}).get("models",[]):
        return saved
    return IA_PROVIDERS.get(provider,{}).get("default","")

def get_api_key_for_provider(provider_name):
    cfg = IA_PROVIDERS.get(provider_name,{})
    key = get_setting(cfg.get("key",""),"")
    if not key:
        key = os.environ.get(cfg.get("env",""),"")
    return key

SYSTEM_PROMPT_FR = """Tu es un expert apicole francophone. Tu réponds TOUJOURS en français, avec un vocabulaire apicole professionnel.
Tes réponses sont précises, structurées et adaptées au contexte nord-africain et méditerranéen.
Ne réponds jamais en anglais."""

def ia_call(prompt_text, image_bytes=None, json_mode=False):
    provider_name = get_active_provider()
    model = get_active_model()
    api_key = get_api_key_for_provider(provider_name)
    cfg = IA_PROVIDERS.get(provider_name,{})
    ptype = cfg.get("type","")
    if not api_key:
        return None
    # Forcer le français dans le prompt
    prompt_with_fr = f"{SYSTEM_PROMPT_FR}\n\n{prompt_text}"
    try:
        if ptype == "anthropic" and ANTHROPIC_OK:
            client = anthropic.Anthropic(api_key=api_key)
            content = []
            if image_bytes and cfg.get("vision"):
                content.append({"type":"image","source":{"type":"base64","media_type":"image/jpeg","data":base64.b64encode(image_bytes).decode()}})
            content.append({"type":"text","text":prompt_with_fr})
            resp = client.messages.create(model=model,max_tokens=2000,messages=[{"role":"user","content":content}])
            return resp.content[0].text

        elif ptype == "google":
            parts = []
            if image_bytes and cfg.get("vision"):
                parts.append({"inline_data":{"mime_type":"image/jpeg","data":base64.b64encode(image_bytes).decode()}})
            parts.append({"text":prompt_with_fr})
            payload = json.dumps({"contents":[{"parts":parts}],"systemInstruction":{"parts":[{"text":SYSTEM_PROMPT_FR}]}}).encode()
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            req = urllib.request.Request(url,data=payload,headers={"Content-Type":"application/json"})
            with urllib.request.urlopen(req,timeout=60) as r:
                data = json.loads(r.read())
            return data["candidates"][0]["content"]["parts"][0]["text"]

        elif ptype == "openai_compat":
            base_url = cfg.get("base_url","")
            messages = [{"role":"system","content":SYSTEM_PROMPT_FR}]
            if image_bytes and cfg.get("vision"):
                messages.append({"role":"user","content":[
                    {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode()}"}},
                    {"type":"text","text":prompt_text}
                ]})
            else:
                messages.append({"role":"user","content":prompt_text})
            body = {"model":model,"messages":messages,"max_tokens":2000,"temperature":0.3}
            if json_mode:
                body["response_format"] = {"type":"json_object"}
            payload = json.dumps(body).encode()
            headers = {"Content-Type":"application/json","Authorization":f"Bearer {api_key}"}
            if "openrouter" in base_url:
                headers["HTTP-Referer"] = "https://apitrack.pro"
                headers["X-Title"] = "ApiTrack Pro"
            req = urllib.request.Request(f"{base_url}/chat/completions",data=payload,headers=headers)
            with urllib.request.urlopen(req,timeout=90) as r:
                data = json.loads(r.read())
            return data["choices"][0]["message"]["content"]
        return None
    except Exception as e:
        return f"❌ Erreur {provider_name} : {e}"

def ia_call_json(prompt_text, image_bytes=None):
    result = ia_call(prompt_text, image_bytes, json_mode=True)
    if not result or result.startswith("❌"):
        return {"error": result or "Pas de réponse"}
    text = result.strip()
    if "```" in text:
        parts = text.split("```")
        for p in parts:
            if p.startswith("json"):
                text = p[4:].strip(); break
            elif p.strip().startswith("{"):
                text = p.strip(); break
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m:
            try: return json.loads(m.group())
            except: pass
        return {"error": f"JSON invalide : {text[:200]}"}

def afficher_resultat_ia(texte, titre="🤖 Analyse IA"):
    provider = get_active_provider()
    model = get_active_model()
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#161B27,#1E2535);border:1px solid #C8820A;border-left:4px solid #C8820A;border-radius:10px;padding:20px;margin:16px 0'>
        <div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:12px'>
            <div style='font-size:1rem;font-weight:600;color:#F5A623'>🤖 {titre}</div>
            <div style='font-size:.7rem;background:#1E2010;color:#A8B4CC;border:1px solid #2E3A52;border-radius:20px;padding:2px 10px'>{provider} · {model}</div>
        </div>
        <div style='font-size:.88rem;color:#F0F4FF;line-height:1.7'>
    """, unsafe_allow_html=True)
    st.markdown(texte)
    st.markdown("</div></div>", unsafe_allow_html=True)

def widget_cle_api():
    provider_names = list(IA_PROVIDERS.keys())
    current = get_active_provider()
    idx = provider_names.index(current) if current in provider_names else 0
    with st.expander("🤖 Choisir le fournisseur IA", expanded=False):
        col1, col2 = st.columns([1.5,1])
        with col1:
            sel = st.selectbox("Fournisseur IA", provider_names, index=idx, key="ia_provider_select")
        cfg = IA_PROVIDERS[sel]
        with col2:
            models = cfg["models"]
            current_model = get_setting("ia_model", cfg["default"])
            idx_m = models.index(current_model) if current_model in models else 0
            sel_model = st.selectbox("Modèle", models, index=idx_m, key="ia_model_select")
        st.markdown(f"<div style='font-size:.78rem;color:#A8B4CC;background:#0F1117;border-radius:6px;padding:8px 12px;margin:6px 0;line-height:1.6'>📊 <b>Quota :</b> {cfg['quota']}<br>🖼️ <b>Vision :</b> {'✅ Oui' if cfg['vision'] else '❌ Non'}<br>🔑 <a href='{cfg['url']}' target='_blank'>Obtenir la clé</a></div>", unsafe_allow_html=True)
        api_key = get_api_key_for_provider(sel)
        new_key = st.text_input(f"Clé API", value=api_key, type="password", placeholder=cfg.get("prefix","")+"...", key=f"key_input_{sel}")
        col_s1, col_s2 = st.columns(2)
        if col_s1.button("💾 Sauvegarder & Activer", key="save_ia_provider"):
            conn = get_db()
            uid = get_user_id()
            if new_key:
                conn.execute("INSERT OR REPLACE INTO settings VALUES (?,?,?)", (uid,cfg["key"],new_key))
            conn.execute("INSERT OR REPLACE INTO settings VALUES (?,?,?)", (uid,"ia_provider",sel))
            conn.execute("INSERT OR REPLACE INTO settings VALUES (?,?,?)", (uid,"ia_model",sel_model))
            conn.commit(); conn.close()
            st.success(f"✅ {sel} activé")
            st.rerun()
        if col_s2.button("🔬 Tester", key="test_ia_provider"):
            conn = get_db(); uid = get_user_id()
            if new_key:
                conn.execute("INSERT OR REPLACE INTO settings VALUES (?,?,?)", (uid,cfg["key"],new_key))
            conn.execute("INSERT OR REPLACE INTO settings VALUES (?,?,?)", (uid,"ia_provider",sel))
            conn.execute("INSERT OR REPLACE INTO settings VALUES (?,?,?)", (uid,"ia_model",sel_model))
            conn.commit(); conn.close()
            with st.spinner("Test..."):
                r = ia_call("Réponds uniquement : 'ApiTrack Pro IA opérationnel' en français.")
            if r and "opérationnel" in r.lower(): st.success(f"✅ {r.strip()}")
            elif r: st.warning(f"Réponse : {r[:200]}")
            else: st.error("❌ Pas de réponse")
    api_key = get_api_key_for_provider(get_active_provider())
    if api_key:
        st.markdown(f"<div style='font-size:.75rem;color:#6EE7B7;margin-bottom:8px'>✅ IA active : <b>{get_active_provider()}</b> · <code>{get_active_model()}</code></div>", unsafe_allow_html=True)
        return True
    else:
        st.warning(f"⚠️ Configurez une clé API pour **{get_active_provider()}**.")
        return False


# ════════════════════════════════════════════════════════════════════════════
# FONCTIONS IA MÉTIER (en français)
# ════════════════════════════════════════════════════════════════════════════
def ia_analyser_morphometrie(aile, largeur, cubital, glossa, tomentum, pigmentation, race_algo, confiance, image_bytes=None):
    prompt = f"""IMPORTANT : Réponds UNIQUEMENT en français.

Tu es expert apicole et morphométriste spécialisé dans la classification des races d'abeilles selon Ruttner (1988).

Mesures morphométriques relevées :
- Longueur aile antérieure : {aile} mm
- Largeur aile : {largeur} mm
- Indice cubital : {cubital}
- Longueur glossa : {glossa} mm
- Tomentum (densité poils thorax 0-3) : {tomentum}
- Pigmentation scutellum : {pigmentation}

Classification algorithmique : **{race_algo}** avec {confiance}% de confiance.

Effectue une analyse morphométrique complète en français :

## 1. Validation de la classification
- Confirme ou nuance la race {race_algo} selon les valeurs Ruttner 1988
- Ton niveau de confiance personnel (0-100%)
- Comparaison avec A.m. intermissa, sahariensis, ligustica, carnica

## 2. Scores de production (note /5 ⭐)
- 🍯 **Miel** : X/5 — justification
- 🌼 **Pollen** : X/5 — justification
- 🟤 **Propolis** : X/5 — justification
- 👑 **Gelée royale** : X/5 — justification

## 3. Caractéristiques comportementales
Douceur, essaimage, économie hivernale, résistance varroa

## 4. Recommandations stratégiques (3 actions)

## 5. Compatibilité avec l'environnement nord-africain (Algérie/Maroc/Tunisie)"""
    return ia_call(prompt, image_bytes)


def ia_analyser_environnement(description_env, latitude=None, longitude=None, saison="printemps", image_bytes=None):
    coords_str = f"Coordonnées : {latitude:.4f}°N, {longitude:.4f}°E" if latitude else ""
    prompt = f"""IMPORTANT : Réponds UNIQUEMENT en français.

Tu es expert apicole senior, botaniste et écologue spécialisé dans l'analyse des environnements mellifères méditerranéens et nord-africains.

Zone à analyser :
{coords_str}
Saison : {saison}
Description : {description_env}

Effectue une analyse environnementale mellifère COMPLÈTE en français :

## 🌿 1. Flore identifiée et potentiel mellifère
Pour chaque espèce : Source (Nectar/Pollen/Résine/Mixte) | Période | Qualité

## 📊 2. Scores de production (note /5 ⭐)
- 🍯 **MIEL** : X/5 — (type floral, saveur probable, rendement estimé kg/ruche/an)
- 🌼 **POLLEN** : X/5 — (diversité, richesse protéique %)
- 🟤 **PROPOLIS** : X/5 — (espèces résineuses, qualité antibactérienne estimée)
- 👑 **GELÉE ROYALE** : X/5 — (disponibilité protéines+sucres, taux 10-HDA estimé)

## 🌡️ 3. Analyse microclimatique
Exposition, altitude, humidité, vent, eau, risques

## 🎯 4. Verdict global
- Potentiel global : [Faible/Modéré/Élevé/Exceptionnel]
- Indice mellifère : X/10
- Production principale recommandée
- Capacité de charge : X ruches/100 ha

## 🐝 5. Plan d'action (5 recommandations)
Données chiffrées obligatoires. Références botaniques nord-africaines."""
    return ia_call(prompt, image_bytes)


def ia_analyser_zone_carto(nom_zone, flore, superficie, ndvi, potentiel, type_zone, latitude=None, longitude=None):
    coords_str = f"à {latitude:.4f}°N, {longitude:.4f}°E" if latitude else ""
    prompt = f"""IMPORTANT : Réponds UNIQUEMENT en français avec un objet JSON valide.
Tu es expert apicole. Analyse cette zone mellifère.

Zone : {nom_zone} {coords_str}
Type : {type_zone} | Flore : {flore} | Superficie : {superficie} ha
NDVI : {ndvi} | Potentiel : {potentiel}

Réponds UNIQUEMENT avec un objet JSON valide (pas de texte avant/après) :
{{
  "diagnostic": {{"potentiel_global":"Élevé","indice_mellifere":8,"capacite_ruches":12,"saison_pic":"Avril-Juin"}},
  "scores": {{
    "miel":{{"note":4,"etoiles":"⭐⭐⭐⭐","detail":"Nectar abondant"}},
    "pollen":{{"note":3,"etoiles":"⭐⭐⭐","detail":"Diversité florale correcte"}},
    "propolis":{{"note":2,"etoiles":"⭐⭐","detail":"Quelques résines"}},
    "gelee_royale":{{"note":3,"etoiles":"⭐⭐⭐","detail":"Protéines disponibles"}}
  }},
  "flore_identifiee":[{{"espece":"Ziziphus lotus","nectar":true,"pollen":true,"resine":false,"periode":"Avr-Juin","qualite":"Excellente"}}],
  "risques":["Sécheresse estivale"],
  "recommandations":["Installer 8-12 ruches en mars","Récolter en juin"],
  "race_adaptee":"intermissa",
  "resume":"Zone mellifère de haute valeur — potentiel miel exceptionnel au printemps."
}}"""
    return ia_call_json(prompt)


def ia_analyser_point_carte(lat, lon):
    """Analyse IA d'un point sélectionné sur la carte"""
    prompt = f"""IMPORTANT : Réponds UNIQUEMENT en français.

Tu es expert apicole, botaniste et écologue spécialisé en Afrique du Nord et en zone méditerranéenne.

Un apiculteur a sélectionné ce point sur une carte satellite :
- Latitude : {lat:.5f}°N
- Longitude : {lon:.5f}°E

En te basant sur tes connaissances géographiques et botaniques de cette région :

## 🌍 1. Identification de la zone
- Région/Wilaya/Pays probable
- Altitude approximative et type de terrain
- Végétation typique de cette zone géographique

## 🌿 2. Potentiel mellifère estimé
- Flore mellifère probable selon la géographie
- Saisons de miellée principales
- Espèces mellifères dominantes attendues

## 📊 3. Scores de production estimés (note /5 ⭐)
- 🍯 **Miel** : X/5 — type et saveur probable
- 🌼 **Pollen** : X/5
- 🟤 **Propolis** : X/5
- 👑 **Gelée royale** : X/5

## ⚠️ 4. Risques et contraintes
- Risques climatiques (sécheresse, chaleur, gel)
- Pesticides agricoles probables
- Pression foncière

## 🎯 5. Verdict et recommandations
- Potentiel global : [Faible/Modéré/Élevé/Exceptionnel]
- Indice mellifère : X/10
- Race d'abeille recommandée pour cette zone
- Nombre de ruches conseillé par hectare
- Mois optimal d'installation

Sois précis et concis. Base-toi sur la géographie réelle de cette localisation."""
    return ia_call(prompt)


# ════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════════════
def sidebar():
    with st.sidebar:
        st.markdown("""
        <div style='padding:8px 0 16px;border-bottom:1px solid #3d2a0e;margin-bottom:12px'>
            <div style='font-size:1.6rem;margin-bottom:4px'>🐝</div>
            <div style='color:#F5A623;font-size:1.1rem;font-weight:600'>ApiTrack Pro</div>
            <div style='font-size:.65rem;color:#8899BB;text-transform:uppercase;letter-spacing:.1em'>Gestion Apicole v4.0</div>
        </div>
        """, unsafe_allow_html=True)

        rucher_nom = get_setting("rucher_nom","Mon Rucher")
        username = st.session_state.get("username","")
        st.markdown(f"<div style='font-size:.75rem;color:#6B7A99;margin-bottom:12px'>📍 {rucher_nom}<br>👤 {username}</div>", unsafe_allow_html=True)

        pages = {
            "🏠 Dashboard": "dashboard",
            "🐝 Mes ruches": "ruches",
            "🔍 Inspections": "inspections",
            "💊 Traitements": "traitements",
            "🍯 Productions": "productions",
            "🧬 Morphométrie IA": "morpho",
            "🗺️ Cartographie": "carto",
            "☀️ Météo & Miellée": "meteo",
            "📊 Génétique": "genetique",
            "🌿 Flore mellifère": "flore",
            "⚠️ Alertes": "alertes",
            "📋 Journal": "journal",
            "🎤 Inspection Vocale": "voice_inspection",
            "🧬 Pedigree & Sélection": "pedigree",
            "🤝 Bourse aux Mâles": "male_market",
            "📸 Scanner Cadre": "cadre_scanner",
            "🚚 Prédiction Transhumance": "transhumance",
            "⚙️ Administration": "admin",
        }

        if "page" not in st.session_state:
            st.session_state.page = "dashboard"

        for label, key in pages.items():
            if st.sidebar.button(label, key=f"nav_{key}", use_container_width=True):
                st.session_state.page = key
                st.rerun()

        st.sidebar.markdown("<hr style='border-color:#2E3A52;margin:12px 0'>", unsafe_allow_html=True)
        if st.sidebar.button("🚪 Déconnexion", use_container_width=True):
            log_action("Déconnexion", f"Utilisateur {st.session_state.get('username')} déconnecté")
            for k in ["logged_in","username","user_id","user_role","page"]:
                st.session_state.pop(k, None)
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# PAGE : DASHBOARD
# ════════════════════════════════════════════════════════════════════════════
def page_dashboard():
    st.markdown("## 🏠 Tableau de bord")
    rucher = get_setting("rucher_nom","Mon Rucher")
    localisation = get_setting("localisation","")
    st.markdown(f"<p style='color:#A8B4CC;margin-top:-10px'>{rucher} · {localisation}</p>", unsafe_allow_html=True)

    uid = get_user_id()
    conn = get_db()
    nb_ruches = conn.execute("SELECT COUNT(*) FROM ruches WHERE user_id=? AND statut='actif'",(uid,)).fetchone()[0]
    total_miel = conn.execute("""
        SELECT COALESCE(SUM(rec.quantite_kg),0) FROM recoltes rec
        JOIN ruches r ON r.id=rec.ruche_id WHERE r.user_id=? AND rec.type_produit='miel'
    """,(uid,)).fetchone()[0]
    nb_insp = conn.execute("""
        SELECT COUNT(*) FROM inspections i JOIN ruches r ON r.id=i.ruche_id
        WHERE r.user_id=? AND i.date_inspection >= date('now','-30 days')
    """,(uid,)).fetchone()[0]
    critiques = conn.execute("""
        SELECT COUNT(*) FROM inspections i JOIN ruches r ON r.id=i.ruche_id
        WHERE r.user_id=? AND i.varroa_pct >= 3.0 AND i.date_inspection >= date('now','-7 days')
    """,(uid,)).fetchone()[0]

    col1,col2,col3,col4 = st.columns(4)
    col1.metric("🐝 Ruches actives", nb_ruches)
    col2.metric("🍯 Miel récolté (kg)", f"{total_miel:.0f}")
    col3.metric("🔍 Inspections (30j)", nb_insp)
    col4.metric("⚠️ Varroa critique", critiques, delta_color="inverse")

    st.markdown("<br>", unsafe_allow_html=True)
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("### 📈 Production mensuelle (kg)")
        df_prod = pd.read_sql("""
            SELECT strftime('%Y-%m', rec.date_recolte) as mois, rec.type_produit, SUM(rec.quantite_kg) as total
            FROM recoltes rec JOIN ruches r ON r.id=rec.ruche_id WHERE r.user_id=?
            GROUP BY mois, rec.type_produit ORDER BY mois
        """, conn, params=(uid,))
        if not df_prod.empty:
            fig = px.bar(df_prod, x="mois", y="total", color="type_produit",
                         color_discrete_map={"miel":"#C8820A","pollen":"#F5C842","gelée royale":"#8B7355"},
                         template="plotly_white")
            fig.update_layout(height=280, margin=dict(t=10,b=10,l=0,r=0),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=True)
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown("### 🐝 État des ruches")
        df_ruches = pd.read_sql("""
            SELECT r.nom, r.race, COALESCE(i.varroa_pct,0) as varroa,
                   COALESCE(i.nb_cadres,0) as cadres, COALESCE(i.poids_kg,0) as poids
            FROM ruches r
            LEFT JOIN inspections i ON i.ruche_id=r.id
                AND i.date_inspection=(SELECT MAX(ii.date_inspection) FROM inspections ii WHERE ii.ruche_id=r.id)
            WHERE r.user_id=? AND r.statut='actif' ORDER BY varroa DESC LIMIT 6
        """, conn, params=(uid,))
        if not df_ruches.empty:
            df_ruches["Statut"] = df_ruches["varroa"].apply(status_badge)
            df_ruches.columns = ["Ruche","Race","Varroa%","Cadres","Poids(kg)","Statut"]
            st.dataframe(df_ruches, use_container_width=True, hide_index=True)

    st.markdown("### ⚠️ Alertes actives")
    df_alertes = pd.read_sql("""
        SELECT r.nom, i.varroa_pct, i.date_inspection, i.notes
        FROM inspections i JOIN ruches r ON r.id=i.ruche_id
        WHERE r.user_id=? AND i.varroa_pct >= 2.0 AND i.date_inspection >= date('now','-7 days')
        ORDER BY i.varroa_pct DESC
    """, conn, params=(uid,))
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
    uid = get_user_id()
    conn = get_db()

    df = pd.read_sql("""
        SELECT r.id, r.nom, r.race, r.date_installation, r.localisation, r.statut,
               COALESCE(i.varroa_pct,'-') as derniere_varroa,
               COALESCE(i.nb_cadres,'-') as cadres,
               COALESCE(i.poids_kg,'-') as poids_kg,
               i.date_inspection as derniere_inspection
        FROM ruches r
        LEFT JOIN inspections i ON i.ruche_id=r.id
            AND i.date_inspection=(SELECT MAX(ii.date_inspection) FROM inspections ii WHERE ii.ruche_id=r.id)
        WHERE r.user_id=? ORDER BY r.id
    """, conn, params=(uid,))

    tab1, tab2, tab3 = st.tabs(["📋 Liste des ruches", "➕ Ajouter une ruche", "🗑️ Supprimer une ruche"])

    with tab1:
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Exporter CSV", csv, "ruches.csv", "text/csv")
        else:
            st.info("Aucune ruche enregistrée. Ajoutez votre première ruche !")

    with tab2:
        with st.form("add_ruche"):
            st.markdown("**Nouvelle ruche**")
            col1, col2 = st.columns(2)
            nom = col1.text_input("Nom / Identifiant*")
            race = col2.selectbox("Race", ["intermissa","sahariensis","ligustica","carnica","hybride"])
            date_inst = col1.date_input("Date d'installation", datetime.date.today())
            localisation = col2.text_input("Localisation")
            col3, col4 = st.columns(2)
            lat = col3.number_input("Latitude", value=float(get_setting("region_lat","34.88")), format="%.4f")
            lon = col4.number_input("Longitude", value=float(get_setting("region_lon","1.32")), format="%.4f")
            notes = st.text_area("Notes")
            submitted = st.form_submit_button("✅ Ajouter la ruche")
        if submitted and nom:
            conn.execute("INSERT INTO ruches (user_id,nom,race,date_installation,localisation,latitude,longitude,notes) VALUES (?,?,?,?,?,?,?,?)",
                         (uid,nom,race,str(date_inst),localisation,lat,lon,notes))
            conn.commit()
            log_action("Ajout ruche", f"Ruche '{nom}' ({race}) ajoutée")
            st.success(f"✅ Ruche '{nom}' ajoutée.")
            st.rerun()

    with tab3:
        st.markdown("### 🗑️ Supprimer une ruche")
        st.warning("⚠️ **Attention** : La suppression est irréversible. Toutes les inspections, récoltes et traitements associés seront supprimés.")
        ruche_ids = conn.execute("SELECT id, nom FROM ruches WHERE user_id=?", (uid,)).fetchall()
        if ruche_ids:
            options = {f"#{r[0]} — {r[1]}": r[0] for r in ruche_ids}
            selected = st.selectbox("Choisir la ruche à supprimer", options.keys())
            confirmation = st.text_input("Tapez 'SUPPRIMER' pour confirmer")
            if st.button("🗑️ Supprimer définitivement", type="secondary"):
                if confirmation == "SUPPRIMER":
                    rid = options[selected]
                    conn.execute("DELETE FROM ruches WHERE id=? AND user_id=?", (rid, uid))
                    conn.commit()
                    log_action("Suppression ruche", f"Ruche {selected} supprimée")
                    st.success(f"Ruche {selected} supprimée.")
                    st.rerun()
                else:
                    st.error("Tapez exactement 'SUPPRIMER' pour confirmer.")
        else:
            st.info("Aucune ruche à supprimer.")

    conn.close()


# ════════════════════════════════════════════════════════════════════════════
# PAGE : INSPECTIONS
# ════════════════════════════════════════════════════════════════════════════
def page_inspections():
    st.markdown("## 🔍 Inspections")
    uid = get_user_id()
    conn = get_db()

    tab1, tab2 = st.tabs(["📋 Historique", "➕ Nouvelle inspection"])

    with tab1:
        df = pd.read_sql("""
            SELECT i.id, r.nom as ruche, i.date_inspection, i.poids_kg, i.nb_cadres,
                   i.varroa_pct, i.reine_vue, i.comportement, i.notes
            FROM inspections i JOIN ruches r ON r.id=i.ruche_id
            WHERE r.user_id=? ORDER BY i.date_inspection DESC
        """, conn, params=(uid,))
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
            WHERE r.user_id=? AND i.varroa_pct IS NOT NULL ORDER BY i.date_inspection
        """, conn, params=(uid,))
        if not df_v.empty:
            fig = px.line(df_v, x="date_inspection", y="varroa_pct", color="nom", template="plotly_white", markers=True)
            fig.add_hline(y=2.0, line_dash="dash", line_color="orange", annotation_text="Seuil alerte (2%)")
            fig.add_hline(y=3.0, line_dash="dash", line_color="red", annotation_text="Seuil critique (3%)")
            fig.update_layout(height=300, margin=dict(t=10,b=10,l=0,r=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        opts = get_user_ruches()
        if not opts:
            st.warning("Ajoutez d'abord une ruche.")
        else:
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
                comportement = col7.selectbox("Comportement", ["calme","nerveuse","agressive","très calme"])
                notes = st.text_area("Notes / Observations")
                submitted = st.form_submit_button("✅ Enregistrer l'inspection")
            if submitted:
                rid = opts[ruche_sel]
                conn.execute("INSERT INTO inspections (ruche_id,date_inspection,poids_kg,nb_cadres,varroa_pct,reine_vue,comportement,notes) VALUES (?,?,?,?,?,?,?,?)",
                             (rid,str(date_insp),poids,cadres,varroa,int(reine),comportement,notes))
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
    uid = get_user_id()
    conn = get_db()

    tab1, tab2 = st.tabs(["📋 En cours & historique", "➕ Nouveau traitement"])

    with tab1:
        df = pd.read_sql("""
            SELECT t.id, r.nom as ruche, t.date_debut, t.date_fin, t.produit,
                   t.pathologie, t.dose, t.duree_jours, t.statut, t.notes
            FROM traitements t JOIN ruches r ON r.id=t.ruche_id
            WHERE r.user_id=? ORDER BY t.date_debut DESC
        """, conn, params=(uid,))
        if not df.empty:
            for _, row in df.iterrows():
                if row["statut"] == "en_cours":
                    debut = datetime.date.fromisoformat(row["date_debut"])
                    jours_ecoules = (datetime.date.today()-debut).days
                    duree = row["duree_jours"] or 21
                    progress = min(jours_ecoules/duree, 1.0)
                    with st.container():
                        col1, col2 = st.columns([3,1])
                        col1.markdown(f"**{row['ruche']}** — {row['produit']} ({row['pathologie']}) · Dose : {row['dose']}")
                        col1.progress(progress, text=f"Jour {jours_ecoules}/{duree}")
                        col2.markdown("<span class='badge-warn'>En cours</span>", unsafe_allow_html=True)
                    st.markdown("---")
            st.dataframe(df, use_container_width=True, hide_index=True)

    with tab2:
        opts = get_user_ruches()
        if not opts:
            st.warning("Ajoutez d'abord une ruche.")
        else:
            with st.form("add_traitement"):
                col1, col2 = st.columns(2)
                ruche_sel = col1.selectbox("Ruche", opts.keys())
                produit = col2.text_input("Produit", placeholder="Acide oxalique")
                col3, col4 = st.columns(2)
                pathologie = col3.selectbox("Pathologie", ["Varroa","Loque américaine","Nosémose","Foulbrood","Autre"])
                dose = col4.text_input("Dose", placeholder="50 ml")
                col5, col6 = st.columns(2)
                date_debut = col5.date_input("Date début", datetime.date.today())
                duree = col6.number_input("Durée (jours)", 1, 90, 21)
                notes = st.text_area("Notes")
                submitted = st.form_submit_button("✅ Enregistrer le traitement")
            if submitted and produit:
                date_fin = date_debut + datetime.timedelta(days=duree)
                conn.execute("INSERT INTO traitements (ruche_id,date_debut,date_fin,produit,pathologie,dose,duree_jours,statut,notes) VALUES (?,?,?,?,?,?,?,'en_cours',?)",
                             (opts[ruche_sel],str(date_debut),str(date_fin),produit,pathologie,dose,duree,notes))
                conn.commit()
                log_action("Traitement débuté", f"Ruche {ruche_sel} — {produit}")
                st.success("✅ Traitement enregistré.")
                st.rerun()
    conn.close()


# ════════════════════════════════════════════════════════════════════════════
# PAGE : PRODUCTIONS
# ════════════════════════════════════════════════════════════════════════════
def page_productions():
    st.markdown("## 🍯 Productions")
    uid = get_user_id()
    conn = get_db()

    total_miel = conn.execute("SELECT COALESCE(SUM(rec.quantite_kg),0) FROM recoltes rec JOIN ruches r ON r.id=rec.ruche_id WHERE r.user_id=? AND rec.type_produit='miel'",(uid,)).fetchone()[0]
    total_pollen = conn.execute("SELECT COALESCE(SUM(rec.quantite_kg),0) FROM recoltes rec JOIN ruches r ON r.id=rec.ruche_id WHERE r.user_id=? AND rec.type_produit='pollen'",(uid,)).fetchone()[0]
    total_gr = conn.execute("SELECT COALESCE(SUM(rec.quantite_kg),0) FROM recoltes rec JOIN ruches r ON r.id=rec.ruche_id WHERE r.user_id=? AND rec.type_produit='gelée royale'",(uid,)).fetchone()[0]

    col1,col2,col3 = st.columns(3)
    col1.metric("🍯 Miel total (kg)", f"{total_miel:.1f}")
    col2.metric("🌼 Pollen (kg)", f"{total_pollen:.1f}")
    col3.metric("👑 Gelée royale (kg)", f"{total_gr:.2f}")

    tab1, tab2, tab3 = st.tabs(["🍯 Récoltes", "📊 Graphiques", "➕ Nouvelle récolte"])

    with tab1:
        df = pd.read_sql("""
            SELECT rec.id, r.nom as ruche, rec.date_recolte, rec.type_produit,
                   rec.quantite_kg, rec.humidite_pct, rec.ph, rec.hda_pct, rec.qualite, rec.notes
            FROM recoltes rec JOIN ruches r ON r.id=rec.ruche_id
            WHERE r.user_id=? ORDER BY rec.date_recolte DESC
        """, conn, params=(uid,))
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Exporter CSV", csv, "recoltes.csv", "text/csv")

    with tab2:
        df_g = pd.read_sql("""
            SELECT strftime('%Y-%m', rec.date_recolte) as mois, rec.type_produit, SUM(rec.quantite_kg) as total
            FROM recoltes rec JOIN ruches r ON r.id=rec.ruche_id WHERE r.user_id=?
            GROUP BY mois, rec.type_produit ORDER BY mois
        """, conn, params=(uid,))
        if not df_g.empty:
            fig = px.area(df_g, x="mois", y="total", color="type_produit",
                          color_discrete_map={"miel":"#C8820A","pollen":"#F5C842","gelée royale":"#8B7355"},
                          template="plotly_white")
            fig.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=10,b=10,l=0,r=0))
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        opts = get_user_ruches()
        if not opts:
            st.warning("Ajoutez d'abord une ruche.")
        else:
            with st.form("add_recolte"):
                col1,col2,col3 = st.columns(3)
                ruche_sel = col1.selectbox("Ruche", opts.keys())
                type_prod = col2.selectbox("Produit", ["miel","pollen","gelée royale","propolis"])
                date_rec = col3.date_input("Date récolte", datetime.date.today())
                col4,col5 = st.columns(2)
                quantite = col4.number_input("Quantité (kg)", 0.0, 500.0, 10.0, 0.1)
                qualite = col5.selectbox("Qualité", ["A+","A","B","C"])
                col6,col7,col8 = st.columns(3)
                humidite = col6.number_input("Humidité (%)", 0.0, 30.0, 17.5, 0.1)
                ph = col7.number_input("pH", 2.0, 7.0, 3.9, 0.1)
                hda = col8.number_input("10-HDA (%)", 0.0, 5.0, 0.0, 0.1)
                notes = st.text_area("Notes")
                submitted = st.form_submit_button("✅ Enregistrer la récolte")
            if submitted:
                conn.execute("INSERT INTO recoltes (ruche_id,date_recolte,type_produit,quantite_kg,humidite_pct,ph,hda_pct,qualite,notes) VALUES (?,?,?,?,?,?,?,?,?)",
                             (opts[ruche_sel],str(date_rec),type_prod,quantite,
                              humidite if humidite>0 else None,
                              ph if ph>0 else None,
                              hda if hda>0 else None, qualite, notes))
                conn.commit()
                log_action("Récolte enregistrée", f"{quantite} kg de {type_prod} — ruche {ruche_sel}")
                st.success(f"✅ {quantite} kg de {type_prod} enregistrés.")
                st.rerun()
    conn.close()


# ════════════════════════════════════════════════════════════════════════════
# PAGE : MÉTÉO & MIELLÉE — AVEC CHANGEMENT DE RÉGION
# ════════════════════════════════════════════════════════════════════════════
def page_meteo():
    st.markdown("## ☀️ Météo & Miellée — Prévisions 7 jours")

    # --- Sélection de région ---
    st.markdown("### 📍 Choisir la région")
    col_reg1, col_reg2 = st.columns([2,1])
    with col_reg1:
        region_names = list(REGIONS.keys())
        current_loc = get_setting("localisation","Tlemcen, Algérie")
        # Trouver l'index par défaut
        default_idx = 0
        for i, rname in enumerate(region_names):
            if rname in current_loc or current_loc in rname:
                default_idx = i
                break
        region_sel = st.selectbox("Région prédéfinie", region_names, index=default_idx, key="meteo_region")
    with col_reg2:
        if st.button("💾 Sauvegarder comme région par défaut", key="save_meteo_region"):
            lat, lon = REGIONS[region_sel]
            if lat is not None:
                set_setting("localisation", region_sel)
                set_setting("region_lat", str(lat))
                set_setting("region_lon", str(lon))
                st.success(f"✅ Région '{region_sel}' sauvegardée.")
                st.rerun()

    lat_r, lon_r = REGIONS[region_sel]
    if region_sel == "Personnalisée" or lat_r is None:
        col_c1, col_c2 = st.columns(2)
        lat_r = col_c1.number_input("Latitude personnalisée", -90.0, 90.0, float(get_setting("region_lat","34.88")), format="%.4f", key="meteo_lat_custom")
        lon_r = col_c2.number_input("Longitude personnalisée", -180.0, 180.0, float(get_setting("region_lon","1.32")), format="%.4f", key="meteo_lon_custom")

    st.markdown(f"<p style='color:#A8B4CC'>📍 {region_sel} — Lat: {lat_r:.2f}°, Lon: {lon_r:.2f}° · Données simulées (7 jours)</p>", unsafe_allow_html=True)
    st.markdown("---")

    today = datetime.date.today()
    previsions = [
        {"jour":(today+datetime.timedelta(days=i)).strftime("%a %d/%m"),"temp":t,"icon":ic,"butinage":b,"pluie":p}
        for i,(t,ic,b,p) in enumerate([
            (22,"☀️","Élevé",0),(19,"⛅","Élevé",5),(21,"🌤️","Élevé",10),
            (14,"🌧️","Faible",80),(17,"⛅","Moyen",30),(24,"☀️","Élevé",0),(26,"☀️","Élevé",0),
        ])
    ]

    cols = st.columns(7)
    couleur_butinage = {"Élevé":"#2E7D32","Moyen":"#F57F17","Faible":"#C62828"}
    bg_butinage = {"Élevé":"#E8F5E9","Moyen":"#FFF8E1","Faible":"#FFEBEE"}
    for col, p in zip(cols, previsions):
        with col:
            st.markdown(f"""
            <div style='background:#1E2535;border:1px solid #2E3A52;border-radius:8px;padding:10px 6px;text-align:center'>
                <div style='font-size:.65rem;text-transform:uppercase;letter-spacing:.06em;color:#A8B4CC;font-weight:500'>{p['jour']}</div>
                <div style='font-size:1.4rem;margin:4px 0'>{p['icon']}</div>
                <div style='font-size:.85rem;font-weight:500;color:#F0F4FF'>{p['temp']}°C</div>
                <div style='font-size:.65rem;margin-top:4px;padding:2px 4px;border-radius:4px;background:{bg_butinage[p["butinage"]]};color:{couleur_butinage[p["butinage"]]}'>{p['butinage']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📈 Indice de butinage prévisionnel")
        df_but = pd.DataFrame(previsions)
        indice = {"Élevé":90,"Moyen":55,"Faible":15}
        df_but["indice"] = df_but["butinage"].map(indice)
        fig = px.bar(df_but, x="jour", y="indice", template="plotly_white", color_discrete_sequence=["#C8820A"])
        fig.update_layout(height=220, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=0,b=0,l=0,r=0), yaxis=dict(range=[0,100]))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("### 💡 Conseils de la semaine")
        st.success("☀️ **Lundi–Mercredi** : Conditions excellentes. Idéal pour les inspections.")
        st.warning("🌧️ **Jeudi** : Pluie prévue. Éviter toute intervention.")
        st.info("🍯 **Vendredi–Dimanche** : Conditions de butinage favorables. Vérifiez les hausses.")

    # Analyse IA de la région météo
    st.markdown("---")
    st.markdown("### 🤖 Analyse IA du potentiel mellifère de cette région")
    ia_active = widget_cle_api()
    if st.button("🌿 Analyser le potentiel mellifère de cette région", disabled=not ia_active):
        with st.spinner("L'IA analyse la région..."):
            prompt = f"""IMPORTANT : Réponds UNIQUEMENT en français.

Analyse le potentiel mellifère de la région suivante pour les apiculteurs :
- Région : {region_sel}
- Coordonnées : {lat_r:.4f}°N, {lon_r:.4f}°E

Fournis :
1. **Climat et végétation typique** de cette région
2. **Calendrier de miellée** (quels mois sont les meilleurs)
3. **Plantes mellifères dominantes** dans cette zone géographique
4. **Conseils pratiques** pour les apiculteurs de cette région
5. **Score global** : Potentiel mellifère /10

Sois précis et adapté à la réalité géographique de cette région."""
            resultat = ia_call(prompt)
        if resultat and not resultat.startswith("❌"):
            afficher_resultat_ia(resultat, f"Analyse mellifère — {region_sel}")
        elif resultat:
            st.error(resultat)


# ════════════════════════════════════════════════════════════════════════════
# PAGE : INSPECTION VOCALE — FONCTIONNELLE VIA NAVIGATEUR
# ════════════════════════════════════════════════════════════════════════════
def page_voice_inspection():
    st.markdown("## 🎤 Assistant Vocal d'Inspection")
    st.markdown("<p style='color:#A8B4CC'>Utilisez votre microphone pour dicter vos observations. L'IA extrait automatiquement les données.</p>", unsafe_allow_html=True)

    ia_active = widget_cle_api()
    opts = get_user_ruches()
    conn = get_db()

    if not opts:
        st.warning("Ajoutez d'abord une ruche.")
        conn.close()
        return

    ruche_sel = st.selectbox("Choisir la ruche à inspecter", opts.keys(), key="voice_ruche")

    tab1, tab2 = st.tabs(["🎙️ Enregistrement vocal (navigateur)", "📝 Saisie texte manuelle"])

    with tab1:
        st.markdown("### 🎙️ Reconnaissance vocale via votre navigateur")
        st.info("🌐 Cette fonctionnalité utilise l'API de reconnaissance vocale de votre navigateur (Chrome/Edge recommandé). Aucune installation requise !")

        st.markdown("""
        <div style='background:#0D2A1F;border:1px solid #1A5C3A;border-radius:8px;padding:14px;margin-bottom:16px;font-size:.84rem;color:#F0F4FF'>
        <b>🎤 Instructions :</b><br>
        1. Cliquez sur <b>"🎙️ Démarrer l'enregistrement"</b><br>
        2. Autorisez l'accès au microphone si demandé<br>
        3. Parlez clairement en français (ex: "varroa deux virgule cinq pourcent, neuf cadres")<br>
        4. Cliquez sur <b>"⏹️ Arrêter"</b> quand vous avez terminé<br>
        5. Le texte apparaîtra automatiquement dans le champ ci-dessous
        </div>
        """, unsafe_allow_html=True)

        # Composant HTML/JS pour la reconnaissance vocale
        voice_html = """
        <div style="font-family:'Inter',sans-serif;padding:10px 0">
            <div style="display:flex;gap:10px;margin-bottom:12px;flex-wrap:wrap">
                <button id="startBtn" onclick="startRecording()" style="
                    background:#C8820A;color:white;border:none;border-radius:8px;
                    padding:10px 20px;font-size:14px;font-weight:600;cursor:pointer;
                    display:flex;align-items:center;gap:8px">
                    🎙️ Démarrer l'enregistrement
                </button>
                <button id="stopBtn" onclick="stopRecording()" disabled style="
                    background:#2E3A52;color:#A8B4CC;border:none;border-radius:8px;
                    padding:10px 20px;font-size:14px;font-weight:600;cursor:pointer">
                    ⏹️ Arrêter
                </button>
                <button onclick="clearText()" style="
                    background:#1E2535;color:#A8B4CC;border:1px solid #2E3A52;
                    border-radius:8px;padding:10px 20px;font-size:14px;cursor:pointer">
                    🗑️ Effacer
                </button>
            </div>
            <div id="status" style="font-size:13px;color:#A8B4CC;margin-bottom:8px;padding:6px 10px;background:#1E2535;border-radius:6px">
                ℹ️ Prêt à enregistrer
            </div>
            <textarea id="transcript" rows="6" placeholder="Le texte dicté apparaîtra ici..." style="
                width:100%;padding:12px;background:#1A2030;color:#F0F4FF;
                border:1.5px solid #3A4A66;border-radius:8px;font-size:14px;
                font-family:'Inter',sans-serif;resize:vertical;box-sizing:border-box">
            </textarea>
            <div style="margin-top:10px">
                <button onclick="copyToClipboard()" style="
                    background:#1E2535;color:#FFD07A;border:1px solid #C8820A;
                    border-radius:8px;padding:8px 16px;font-size:13px;cursor:pointer">
                    📋 Copier le texte
                </button>
            </div>
        </div>

        <script>
        let recognition = null;
        let isRecording = false;
        let finalTranscript = '';

        function startRecording() {
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                document.getElementById('status').innerHTML = '❌ Reconnaissance vocale non supportée. Utilisez Chrome ou Edge.';
                document.getElementById('status').style.color = '#F87171';
                return;
            }
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.lang = 'fr-FR';
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.maxAlternatives = 1;
            finalTranscript = document.getElementById('transcript').value;

            recognition.onstart = function() {
                isRecording = true;
                document.getElementById('status').innerHTML = '🔴 Enregistrement en cours... Parlez maintenant';
                document.getElementById('status').style.color = '#F87171';
                document.getElementById('startBtn').disabled = true;
                document.getElementById('startBtn').style.background = '#6B7A99';
                document.getElementById('stopBtn').disabled = false;
                document.getElementById('stopBtn').style.background = '#C8820A';
            };

            recognition.onresult = function(event) {
                let interimTranscript = '';
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    if (event.results[i].isFinal) {
                        finalTranscript += event.results[i][0].transcript + ' ';
                    } else {
                        interimTranscript += event.results[i][0].transcript;
                    }
                }
                document.getElementById('transcript').value = finalTranscript + interimTranscript;
            };

            recognition.onerror = function(event) {
                let msg = '❌ Erreur : ' + event.error;
                if (event.error === 'not-allowed') msg = '❌ Accès au microphone refusé. Autorisez-le dans les paramètres du navigateur.';
                else if (event.error === 'no-speech') msg = '⚠️ Aucune parole détectée. Réessayez.';
                document.getElementById('status').innerHTML = msg;
                document.getElementById('status').style.color = '#F87171';
                stopRecording();
            };

            recognition.onend = function() {
                if (isRecording) recognition.start();
            };

            try {
                recognition.start();
            } catch(e) {
                document.getElementById('status').innerHTML = '❌ Impossible de démarrer : ' + e.message;
            }
        }

        function stopRecording() {
            isRecording = false;
            if (recognition) {
                recognition.stop();
                recognition = null;
            }
            document.getElementById('status').innerHTML = '✅ Enregistrement terminé. Copiez le texte et collez-le dans le champ Streamlit ci-dessous.';
            document.getElementById('status').style.color = '#34D399';
            document.getElementById('startBtn').disabled = false;
            document.getElementById('startBtn').style.background = '#C8820A';
            document.getElementById('stopBtn').disabled = true;
            document.getElementById('stopBtn').style.background = '#2E3A52';
        }

        function clearText() {
            finalTranscript = '';
            document.getElementById('transcript').value = '';
            document.getElementById('status').innerHTML = 'ℹ️ Prêt à enregistrer';
            document.getElementById('status').style.color = '#A8B4CC';
        }

        function copyToClipboard() {
            const text = document.getElementById('transcript').value;
            if (navigator.clipboard) {
                navigator.clipboard.writeText(text).then(() => {
                    document.getElementById('status').innerHTML = '✅ Texte copié ! Collez-le dans le champ Streamlit ci-dessous.';
                    document.getElementById('status').style.color = '#34D399';
                });
            }
        }
        </script>
        """
        st.components.v1.html(voice_html, height=320, scrolling=False)

        st.markdown("---")
        st.markdown("**📝 Collez ici le texte dicté (ou tapez directement) :**")
        transcription = st.text_area(
            "Texte de l'inspection",
            placeholder='Ex: "varroa deux virgule cinq pourcent, neuf cadres de couvain, reine vue, comportement calme, poids vingt-huit kilos"',
            height=100,
            key="voice_transcript_input"
        )

        col_guide1, col_guide2 = st.columns(2)
        with col_guide1:
            st.markdown("""
            **🗣️ Exemples de phrases :**
            - "varroa deux virgule cinq pourcent"
            - "neuf cadres de couvain"
            - "reine vue" / "reine non vue"
            - "comportement calme / agressive"
            - "poids vingt-huit kilos"
            - "traitement acide oxalique requis"
            """)
        with col_guide2:
            st.markdown("""
            **💡 Conseils :**
            - Parlez clairement et lentement
            - Dictez les chiffres en lettres
            - Chrome et Edge sont recommandés
            - Bonne connexion internet requise
            """)

        if transcription and st.button("🤖 Extraire les données avec l'IA", disabled=not ia_active, use_container_width=True):
            with st.spinner("L'IA analyse votre compte-rendu vocal..."):
                prompt = f"""IMPORTANT : Réponds UNIQUEMENT en JSON valide, sans texte avant ou après.
Tu es un assistant apicole expert. Extrait du texte d'inspection suivant les informations structurées.

Texte : "{transcription}"

Format JSON strict :
{{
    "varroa_pct": float ou null,
    "nb_cadres": int ou null,
    "poids_kg": float ou null,
    "reine_vue": true ou false,
    "comportement": "calme" ou "nerveuse" ou "agressive" ou "très calme",
    "notes": "résumé en français des observations",
    "alertes": ["liste des problèmes détectés"]
}}

Interprète intelligemment : "deux virgule cinq" = 2.5, "vingt-huit" = 28, "reine non vue" = false, etc."""
                result_json = ia_call_json(prompt)
                if result_json and "error" not in result_json:
                    st.success("✅ Données extraites avec succès !")
                    st.json(result_json)
                    st.session_state.voice_extracted_data = result_json
                    st.session_state.voice_transcript = transcription
                    if result_json.get("alertes"):
                        for alerte in result_json["alertes"]:
                            st.warning(f"⚠️ {alerte}")
                else:
                    st.error(f"Échec de l'extraction : {result_json.get('error','Erreur inconnue')}")

        if "voice_extracted_data" in st.session_state:
            data = st.session_state.voice_extracted_data
            st.markdown("---")
            st.markdown("**✏️ Vérifiez et modifiez si nécessaire :**")
            col1, col2, col3 = st.columns(3)
            varroa_v = col1.number_input("Varroa (%)", value=float(data.get("varroa_pct") or 0), min_value=0.0, max_value=20.0, step=0.1, key="v_varroa")
            cadres_v = col2.number_input("Nb cadres", value=int(data.get("nb_cadres") or 0), min_value=0, max_value=20, key="v_cadres")
            poids_v = col3.number_input("Poids (kg)", value=float(data.get("poids_kg") or 0), min_value=0.0, max_value=80.0, step=0.1, key="v_poids")
            reine_v = st.checkbox("Reine vue", value=bool(data.get("reine_vue", True)), key="v_reine")
            comp_opts = ["calme","nerveuse","agressive","très calme"]
            comp_val = data.get("comportement","calme")
            comp_idx = comp_opts.index(comp_val) if comp_val in comp_opts else 0
            comp_v = st.selectbox("Comportement", comp_opts, index=comp_idx, key="v_comp")
            notes_v = st.text_area("Notes", value=data.get("notes",""), key="v_notes")

            if st.button("✅ Valider et enregistrer l'inspection", use_container_width=True):
                rid = opts[ruche_sel]
                conn.execute("""
                    INSERT INTO inspections (ruche_id,date_inspection,poids_kg,nb_cadres,varroa_pct,reine_vue,comportement,notes)
                    VALUES (?,date('now'),?,?,?,?,?,?)
                """, (rid, poids_v or None, cadres_v or None, varroa_v or None, int(reine_v), comp_v, notes_v))
                conn.execute("""
                    INSERT INTO voice_inspections (ruche_id,transcription,actions_extraites)
                    VALUES (?,?,?)
                """, (rid, st.session_state.get("voice_transcript",""), json.dumps(data)))
                conn.commit()
                log_action("Inspection vocale", f"Ruche {ruche_sel} via assistant vocal")
                if varroa_v >= 3.0:
                    st.error(f"⚠️ ALERTE CRITIQUE : Varroa {varroa_v}% !")
                elif varroa_v >= 2.0:
                    st.warning(f"⚠️ Varroa {varroa_v}% — Surveillance renforcée.")
                else:
                    st.success("✅ Inspection vocale enregistrée avec succès !")
                del st.session_state.voice_extracted_data
                st.session_state.pop("voice_transcript", None)
                st.rerun()

    with tab2:
        st.markdown("### 📝 Saisie manuelle rapide")
        opts2 = get_user_ruches()
        with st.form("manual_quick_insp"):
            col1, col2 = st.columns(2)
            r_sel = col1.selectbox("Ruche", opts2.keys() if opts2 else ["Aucune ruche"])
            date_v = col2.date_input("Date", datetime.date.today())
            col3, col4, col5 = st.columns(3)
            varroa_m = col3.number_input("Varroa (%)", 0.0, 20.0, 1.0, 0.1)
            cadres_m = col4.number_input("Nb cadres", 0, 20, 10)
            poids_m = col5.number_input("Poids (kg)", 0.0, 80.0, 25.0, 0.1)
            col6, col7 = st.columns(2)
            reine_m = col6.checkbox("Reine vue", value=True)
            comp_m = col7.selectbox("Comportement", ["calme","nerveuse","agressive","très calme"])
            notes_m = st.text_area("Notes")
            submitted_m = st.form_submit_button("✅ Enregistrer")
        if submitted_m and opts2:
            rid = opts2[r_sel]
            conn.execute("INSERT INTO inspections (ruche_id,date_inspection,poids_kg,nb_cadres,varroa_pct,reine_vue,comportement,notes) VALUES (?,?,?,?,?,?,?,?)",
                         (rid,str(date_v),poids_m,cadres_m,varroa_m,int(reine_m),comp_m,notes_m))
            conn.commit()
            log_action("Inspection manuelle rapide", f"Ruche {r_sel}")
            st.success("✅ Inspection enregistrée.")
            st.rerun()

    st.markdown("---")
    st.markdown("### 📜 Historique des inspections vocales")
    uid = get_user_id()
    df_voice = pd.read_sql("""
        SELECT v.id, r.nom, v.timestamp, v.transcription, v.actions_extraites
        FROM voice_inspections v JOIN ruches r ON v.ruche_id=r.id
        WHERE r.user_id=? ORDER BY v.timestamp DESC LIMIT 20
    """, conn, params=(uid,))
    if not df_voice.empty:
        st.dataframe(df_voice, use_container_width=True, hide_index=True)
    else:
        st.info("Aucune inspection vocale enregistrée.")
    conn.close()


# ════════════════════════════════════════════════════════════════════════════
# PAGE : CARTOGRAPHIE — AVEC SÉLECTION DE POINT SUR CARTE + ANALYSE IA
# ════════════════════════════════════════════════════════════════════════════
def page_carto():
    st.markdown("## 🗺️ Cartographie — Zones mellifères + Analyse IA")

    ia_active = widget_cle_api()

    # --- Sélection de région ---
    st.markdown("### 📍 Région de la carte")
    col_reg1, col_reg2, col_reg3 = st.columns([2,1,1])
    with col_reg1:
        region_names = list(REGIONS.keys())
        current_loc = get_setting("localisation","Tlemcen, Algérie")
        default_idx = 0
        for i, rname in enumerate(region_names):
            if rname in current_loc or current_loc in rname:
                default_idx = i
                break
        region_sel = st.selectbox("Région", region_names, index=default_idx, key="carto_region")
    lat_r, lon_r = REGIONS[region_sel]
    if lat_r is None:
        with col_reg2:
            lat_r = st.number_input("Latitude", value=float(get_setting("region_lat","34.88")), format="%.4f", key="carto_lat_c")
        with col_reg3:
            lon_r = st.number_input("Longitude", value=float(get_setting("region_lon","1.32")), format="%.4f", key="carto_lon_c")
    else:
        with col_reg2:
            st.metric("Latitude", f"{lat_r:.4f}°")
        with col_reg3:
            st.metric("Longitude", f"{lon_r:.4f}°")

    if st.button("💾 Définir comme région par défaut", key="carto_save_region"):
        set_setting("localisation", region_sel)
        set_setting("region_lat", str(lat_r))
        set_setting("region_lon", str(lon_r))
        st.success(f"✅ Région '{region_sel}' définie par défaut.")

    uid = get_user_id()
    conn = get_db()

    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Carte & Zones", "📡 Analyse d'un point (clic carte)", "🌿 Analyse environnement IA", "➕ Ajouter une zone"])

    with tab1:
        df_zones = pd.read_sql("SELECT * FROM zones WHERE user_id=?", conn, params=(uid,))
        df_ruches = pd.read_sql("SELECT * FROM ruches WHERE user_id=? AND statut='actif' AND latitude IS NOT NULL", conn, params=(uid,))

        if FOLIUM_OK:
            center_lat = lat_r
            center_lon = lon_r
            m = folium.Map(location=[center_lat,center_lon], zoom_start=11,
                           tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}", attr="Google Satellite")
            couleurs_pot = {"élevé":"green","modéré":"orange","faible":"red","exceptionnel":"darkgreen","modere":"orange"}
            for _, r in df_ruches.iterrows():
                folium.Marker([r["latitude"],r["longitude"]],
                              popup=f"<b>{r['nom']}</b><br>{r['race']}<br>{r['localisation']}",
                              icon=folium.Icon(color="orange",icon="home",prefix="fa")).add_to(m)
            for _, z in df_zones.iterrows():
                if z["latitude"] and z["longitude"]:
                    col_m = couleurs_pot.get(str(z["potentiel"]).lower(),"blue")
                    folium.CircleMarker([z["latitude"],z["longitude"]], radius=14,
                                        popup=folium.Popup(f"<b>{z['nom']}</b><br>Flore : {z['flore_principale']}<br>NDVI : {z['ndvi']}<br>Potentiel : {z['potentiel']}", max_width=200),
                                        color=col_m, fill=True, fill_color=col_m, fill_opacity=0.55).add_to(m)
            map_data = st_folium(m, width="100%", height=450, key="main_map")
        else:
            st.warning("Installez `folium` et `streamlit-folium` pour la carte interactive.")
            map_data = None

        st.markdown("### 📋 Zones enregistrées")
        if not df_zones.empty:
            for _, z in df_zones.iterrows():
                with st.expander(f"📍 {z['nom']} — {z['flore_principale']} · {z['potentiel']}"):
                    col_z1, col_z2, col_z3, col_z4 = st.columns(4)
                    col_z1.metric("Surface", f"{z['superficie_ha']} ha")
                    col_z2.metric("NDVI", f"{z['ndvi']:.2f}")
                    col_z3.metric("Type", z["type_zone"])
                    col_z4.metric("Potentiel", z["potentiel"])
                    if st.button(f"🤖 Analyser '{z['nom']}' avec l'IA", key=f"ia_zone_{z['id']}", disabled=not ia_active):
                        with st.spinner("Analyse IA..."):
                            result = ia_analyser_zone_carto(z["nom"],z["flore_principale"],z["superficie_ha"],z["ndvi"],z["potentiel"],z["type_zone"],z["latitude"],z["longitude"])
                        if result and "error" not in result:
                            _afficher_diagnostic_zone(result, z["nom"])
                        else:
                            st.error(f"Erreur IA : {result.get('error','')}")

    with tab2:
        st.markdown("### 📡 Analyser n'importe quel point de la carte")
        st.info("🗺️ Cliquez sur un point de la carte satellite, ou entrez les coordonnées manuellement. L'IA analysera le potentiel apicole de cet endroit précis.")

        st.markdown("#### 🖱️ Cliquer sur la carte pour analyser un point")

        if FOLIUM_OK:
            m2 = folium.Map(location=[lat_r,lon_r], zoom_start=10,
                            tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}", attr="Google Satellite")
            folium.Marker([lat_r,lon_r], popup="Centre de la région", icon=folium.Icon(color="blue",icon="info-sign")).add_to(m2)
            st.markdown("<p style='color:#A8B4CC;font-size:.83rem'>💡 Cliquez sur la carte pour sélectionner un point, puis entrez ses coordonnées dans les champs ci-dessous.</p>", unsafe_allow_html=True)
            map_click_data = st_folium(m2, width="100%", height=400, key="click_map")

            # Récupérer les coordonnées du clic
            clicked_lat, clicked_lon = lat_r, lon_r
            if map_click_data and map_click_data.get("last_clicked"):
                clicked_lat = map_click_data["last_clicked"]["lat"]
                clicked_lon = map_click_data["last_clicked"]["lng"]
                st.success(f"📍 Point sélectionné : **{clicked_lat:.5f}°N, {clicked_lon:.5f}°E**")
        else:
            st.warning("Installez folium pour la carte interactive.")
            clicked_lat, clicked_lon = lat_r, lon_r

        st.markdown("#### 📐 Coordonnées du point à analyser")
        col_p1, col_p2 = st.columns(2)
        point_lat = col_p1.number_input("Latitude du point", -90.0, 90.0, float(clicked_lat if FOLIUM_OK else lat_r), format="%.5f", key="point_lat_ia")
        point_lon = col_p2.number_input("Longitude du point", -180.0, 180.0, float(clicked_lon if FOLIUM_OK else lon_r), format="%.5f", key="point_lon_ia")

        info_supp = st.text_area(
            "Informations supplémentaires (optionnel)",
            placeholder="Ex: Zone agricole avec oliviers, altitude ~800m, bord de rivière, garrigue...",
            height=80,
            key="point_info_supp"
        )

        if st.button("🤖 Analyser ce point avec l'IA satellite", disabled=not ia_active, use_container_width=True):
            with st.spinner("🛰️ L'IA analyse les caractéristiques géographiques de ce point..."):
                prompt_point = f"""IMPORTANT : Réponds UNIQUEMENT en français.

Tu es expert apicole, botaniste et écologue spécialisé en Afrique du Nord et en zone méditerranéenne.

Un apiculteur a sélectionné ce point précis sur une carte satellite :
- Latitude : {point_lat:.5f}°N
- Longitude : {point_lon:.5f}°E
{f'- Informations supplémentaires : {info_supp}' if info_supp else ''}

En te basant sur tes connaissances géographiques et botaniques :

## 🌍 1. Identification de la zone
- Région/Pays identifié
- Type de terrain (montagne, plaine, côte, désert...)
- Altitude approximative et exposition

## 🌿 2. Végétation et flore mellifère probable
- Espèces végétales typiques de cette localisation
- Flore mellifère dominante à cette latitude/longitude
- Saisonnalité des floraisons

## 📊 3. Scores de production estimés (/5 ⭐)
- 🍯 **Miel** : X/5 — type floral probable, rendement estimé kg/ruche/an
- 🌼 **Pollen** : X/5 — diversité et richesse protéique
- 🟤 **Propolis** : X/5 — espèces résineuses disponibles
- 👑 **Gelée royale** : X/5 — disponibilité protéines et sucres

## ⚠️ 4. Risques et contraintes
- Risques climatiques spécifiques à cette zone
- Pesticides agricoles probables
- Compétition avec d'autres pollinisateurs
- Prédateurs locaux

## 🎯 5. Verdict final
- **Potentiel global** : [Faible/Modéré/Élevé/Exceptionnel]
- **Indice mellifère** : X/10
- **Race d'abeille recommandée** : (nom de la race adaptée)
- **Nombre optimal de ruches** : X ruches/100 ha
- **Meilleur mois d'installation** : (mois)
- **Période de miellée principale** : (période)

Utilise des données chiffrées précises. Sois concis mais complet."""
                resultat_point = ia_call(prompt_point)

            if resultat_point and not resultat_point.startswith("❌"):
                st.markdown(f"---")
                st.markdown(f"### 📍 Résultats pour le point ({point_lat:.4f}°N, {point_lon:.4f}°E)")
                afficher_resultat_ia(resultat_point, f"Analyse du point ({point_lat:.4f}°N, {point_lon:.4f}°E)")
                log_action("Analyse point carte", f"Lat {point_lat:.4f}, Lon {point_lon:.4f}")

                st.markdown("---")
                st.markdown("**💾 Sauvegarder ce point comme zone mellifère ?**")
                with st.form("save_point_zone"):
                    nom_pz = st.text_input("Nom de la zone", f"Zone ({point_lat:.3f}, {point_lon:.3f})")
                    type_pz = st.selectbox("Type", ["nectar","pollen","nectar+pollen","propolis","mixte"])
                    surf_pz = st.number_input("Superficie estimée (ha)", 0.0, 5000.0, 10.0)
                    pot_pz = st.selectbox("Potentiel", ["faible","modéré","élevé","exceptionnel"])
                    if st.form_submit_button("💾 Sauvegarder"):
                        conn.execute("INSERT INTO zones (user_id,nom,type_zone,latitude,longitude,superficie_ha,potentiel,notes) VALUES (?,?,?,?,?,?,?,?)",
                                     (uid,nom_pz,type_pz,point_lat,point_lon,surf_pz,pot_pz,f"[Analyse IA] {info_supp}"))
                        conn.commit()
                        st.success(f"✅ Zone '{nom_pz}' sauvegardée !")
            elif resultat_point:
                st.error(resultat_point)

    with tab3:
        st.markdown("### 🌿 Analyse IA d'un environnement")
        mode_analyse = st.radio("Mode d'analyse", ["📝 Description textuelle", "📷 Analyse de photo"], horizontal=True)

        if mode_analyse == "📝 Description textuelle":
            col_env1, col_env2 = st.columns([1.2,1])
            with col_env1:
                description = st.text_area("Description de l'environnement *", placeholder="Ex : Zone de garrigue méditerranéenne avec chênes-lièges...", height=140)
                saison = st.selectbox("Saison actuelle", ["Printemps","Été","Automne","Hiver"])
                col_lat, col_lon = st.columns(2)
                env_lat = col_lat.number_input("Latitude", -90.0, 90.0, lat_r, format="%.4f")
                env_lon = col_lon.number_input("Longitude", -180.0, 180.0, lon_r, format="%.4f")
            with col_env2:
                env_img = st.file_uploader("Photo paysage (optionnel)", type=["jpg","jpeg","png","webp"])
                if env_img: st.image(env_img, use_container_width=True)

            if st.button("🤖 Lancer l'analyse", use_container_width=True, disabled=not ia_active):
                if not description.strip():
                    st.warning("Décrivez l'environnement.")
                else:
                    img_bytes = env_img.read() if env_img else None
                    with st.spinner("Analyse en cours..."):
                        resultat = ia_analyser_environnement(description, env_lat, env_lon, saison, img_bytes)
                    if resultat and not resultat.startswith("❌"):
                        afficher_resultat_ia(resultat, "Analyse environnementale mellifère")
                        log_action("Analyse IA environnement", f"Zone {env_lat:.2f},{env_lon:.2f}")
                        with st.form("save_env_zone"):
                            nom_z = st.text_input("Nom de la zone", "Zone analysée IA")
                            type_z = st.selectbox("Type", ["nectar","pollen","nectar+pollen","propolis","mixte"])
                            surf_z = st.number_input("Superficie (ha)", 0.0, 5000.0, 10.0)
                            if st.form_submit_button("💾 Sauvegarder"):
                                conn.execute("INSERT INTO zones (user_id,nom,type_zone,latitude,longitude,superficie_ha,flore_principale,potentiel,notes) VALUES (?,?,?,?,?,?,?,?,?)",
                                             (uid,nom_z,type_z,env_lat,env_lon,surf_z,description[:100],"élevé","[IA] "+description[:200]))
                                conn.commit()
                                st.success(f"✅ Zone '{nom_z}' sauvegardée !")

        else:
            st.markdown("#### 📷 Analyse par photo uniquement")
            col_p1, col_p2 = st.columns([1,1])
            with col_p1:
                env_img_only = st.file_uploader("Photo du paysage *", type=["jpg","jpeg","png","webp"])
                if env_img_only: st.image(env_img_only, use_container_width=True)
            with col_p2:
                lat_photo = st.number_input("Latitude", value=lat_r, format="%.4f")
                lon_photo = st.number_input("Longitude", value=lon_r, format="%.4f")
                saison_photo = st.selectbox("Saison", ["Printemps","Été","Automne","Hiver"])

            if st.button("🤖 Analyser la photo", disabled=not ia_active, use_container_width=True):
                if not env_img_only:
                    st.warning("Téléversez une photo.")
                else:
                    img_bytes = env_img_only.getvalue()
                    prompt_photo = f"""IMPORTANT : Réponds UNIQUEMENT en français.
Tu es expert en botanique méditerranéenne et apicole. Analyse cette photo de paysage.
Localisation : lat {lat_photo}, lon {lon_photo}. Saison : {saison_photo}.

Identifie les espèces végétales visibles et évalue le potentiel mellifère.
Structure ta réponse avec :
1. **Flore identifiée** (liste des espèces visibles)
2. **Potentiel global** : Faible/Modéré/Élevé/Exceptionnel
3. **Scores /5** pour Miel, Pollen, Propolis, Gelée royale
4. **Recommandations** (nombre de ruches, période de miellée)
5. **Risques** identifiés sur la photo

Sois précis sur ce que tu vois réellement dans la photo."""
                    with st.spinner("L'IA examine la photo..."):
                        resultat_photo = ia_call(prompt_photo, image_bytes=img_bytes)
                    if resultat_photo and not resultat_photo.startswith("❌"):
                        afficher_resultat_ia(resultat_photo, "Analyse de la photo — Vision IA")
                        log_action("Analyse photo environnement", f"Lat {lat_photo}, Lon {lon_photo}")
                    else:
                        st.error(resultat_photo or "Erreur inconnue")

    with tab4:
        with st.form("add_zone"):
            col1, col2 = st.columns(2)
            nom = col1.text_input("Nom de la zone*")
            type_zone = col2.selectbox("Type", ["nectar","pollen","nectar+pollen","propolis","mixte"])
            col3, col4 = st.columns(2)
            z_lat = col3.number_input("Latitude", value=lat_r, format="%.4f")
            z_lon = col4.number_input("Longitude", value=lon_r, format="%.4f")
            col5, col6, col7 = st.columns(3)
            superficie = col5.number_input("Superficie (ha)", 0.0, 5000.0, 10.0)
            flore = col6.text_input("Flore principale")
            ndvi = col7.number_input("NDVI", 0.0, 1.0, 0.65, 0.01)
            potentiel = st.selectbox("Potentiel mellifère", ["faible","modéré","élevé","exceptionnel"])
            notes = st.text_area("Notes")
            submitted = st.form_submit_button("✅ Ajouter la zone")
        if submitted and nom:
            conn.execute("INSERT INTO zones (user_id,nom,type_zone,latitude,longitude,superficie_ha,flore_principale,ndvi,potentiel,notes) VALUES (?,?,?,?,?,?,?,?,?,?)",
                         (uid,nom,type_zone,z_lat,z_lon,superficie,flore,ndvi,potentiel,notes))
            conn.commit()
            log_action("Zone ajoutée", f"Zone '{nom}' — {flore}")
            st.success(f"✅ Zone '{nom}' ajoutée.")
            st.rerun()

    conn.close()


def _afficher_diagnostic_zone(result, nom_zone):
    d = result.get("diagnostic",{})
    scores = result.get("scores",{})
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#161B27,#1E2535);border:1px solid #2E7D32;border-left:4px solid #2E7D32;border-radius:10px;padding:16px;margin:8px 0'>
        <div style='font-size:.95rem;font-weight:600;color:#6EE7B7;margin-bottom:10px'>🤖 Diagnostic IA — {nom_zone}</div>
        <div style='display:flex;gap:20px;flex-wrap:wrap'>
            <span>🌿 <b>{d.get('potentiel_global','—')}</b></span>
            <span>📊 Indice : <b>{d.get('indice_mellifere','—')}/10</b></span>
            <span>🐝 Capacité : <b>{d.get('capacite_ruches','—')} ruches</b></span>
            <span>📅 Pic : <b>{d.get('saison_pic','—')}</b></span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if scores:
        cols_sc = st.columns(4)
        icons = {"miel":"🍯","pollen":"🌼","propolis":"🟤","gelee_royale":"👑"}
        labels = {"miel":"Miel","pollen":"Pollen","propolis":"Propolis","gelee_royale":"Gelée royale"}
        for col, key in zip(cols_sc, ["miel","pollen","propolis","gelee_royale"]):
            s = scores.get(key,{})
            with col:
                st.markdown(f"""<div style='text-align:center;background:#1E2535;border:1px solid #2E3A52;border-radius:8px;padding:10px'>
                    <div>{icons[key]}</div><div style='font-size:.75rem;color:#A8B4CC'>{labels[key]}</div>
                    <div>{s.get('etoiles','—')}</div><div style='font-size:.7rem;color:#A8B4CC'>{str(s.get('detail',''))[:50]}</div>
                </div>""", unsafe_allow_html=True)
    flore_list = result.get("flore_identifiee",[])
    if flore_list:
        st.dataframe(pd.DataFrame(flore_list), use_container_width=True, hide_index=True)
    recs = result.get("recommandations",[])
    if recs:
        for r in recs: st.markdown(f"- {r}")
    if result.get("resume"): st.info(f"📝 {result['resume']}")


# ════════════════════════════════════════════════════════════════════════════
# PAGE : ADMINISTRATION — AVEC SAUVEGARDE/CHARGEMENT ET MULTI-UTILISATEURS
# ════════════════════════════════════════════════════════════════════════════
def page_admin():
    st.markdown("## ⚙️ Administration")
    uid = get_user_id()
    role = st.session_state.get("user_role","apiculteur")
    conn = get_db()

    tabs_list = ["🏠 Profil rucher", "🤖 Clé API IA", "🔐 Mot de passe", "💾 Base de données"]
    if role == "admin":
        tabs_list.append("👥 Gestion utilisateurs")

    tabs = st.tabs(tabs_list)

    with tabs[0]:
        rucher_nom = get_setting("rucher_nom","Mon Rucher")
        localisation = get_setting("localisation","")
        with st.form("settings_form"):
            new_nom = st.text_input("Nom du rucher", rucher_nom)
            new_loc = st.text_input("Localisation", localisation)
            col_l1, col_l2 = st.columns(2)
            new_lat = col_l1.number_input("Latitude par défaut", value=float(get_setting("region_lat","34.88")), format="%.4f")
            new_lon = col_l2.number_input("Longitude par défaut", value=float(get_setting("region_lon","1.32")), format="%.4f")
            submitted = st.form_submit_button("💾 Sauvegarder")
        if submitted:
            set_setting("rucher_nom", new_nom)
            set_setting("localisation", new_loc)
            set_setting("region_lat", str(new_lat))
            set_setting("region_lon", str(new_lon))
            log_action("Paramètres modifiés", f"Nom: {new_nom}")
            st.success("✅ Paramètres sauvegardés.")

    with tabs[1]:
        st.markdown("### 🤖 Gestion des fournisseurs IA")
        rows = []
        for pname, cfg in IA_PROVIDERS.items():
            key = get_api_key_for_provider(pname)
            rows.append({"Fournisseur":pname,"Modèle":cfg["default"],"Quota":cfg["quota"],"Vision":"✅" if cfg["vision"] else "❌","Statut":"✅ Configuré" if key else "❌ Manquant"})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        prov_sel = st.selectbox("Fournisseur à configurer", list(IA_PROVIDERS.keys()), key="admin_prov_sel")
        cfg_sel = IA_PROVIDERS[prov_sel]
        key_actuelle = get_api_key_for_provider(prov_sel)

        with st.form(f"key_form_{prov_sel}"):
            new_key = st.text_input(f"Clé API", value=key_actuelle, type="password", placeholder=cfg_sel.get("prefix","")+"votre-clé")
            sel_model_admin = st.selectbox("Modèle", cfg_sel["models"])
            col_a, col_b = st.columns(2)
            save = col_a.form_submit_button("💾 Sauvegarder & Activer")
            delete = col_b.form_submit_button("🗑️ Supprimer la clé")

        if save:
            if new_key.strip():
                conn.execute("INSERT OR REPLACE INTO settings VALUES (?,?,?)", (uid,cfg_sel["key"],new_key.strip()))
            conn.execute("INSERT OR REPLACE INTO settings VALUES (?,?,?)", (uid,"ia_provider",prov_sel))
            conn.execute("INSERT OR REPLACE INTO settings VALUES (?,?,?)", (uid,"ia_model",sel_model_admin))
            conn.commit()
            log_action("Fournisseur IA configuré", f"{prov_sel}")
            st.success(f"✅ {prov_sel} configuré.")
            st.rerun()
        if delete:
            conn.execute("DELETE FROM settings WHERE user_id=? AND key=?", (uid,cfg_sel["key"]))
            conn.commit()
            st.success("✅ Clé supprimée.")
            st.rerun()

    with tabs[2]:
        with st.form("pwd_form"):
            old_pwd = st.text_input("Mot de passe actuel", type="password")
            new_pwd = st.text_input("Nouveau mot de passe", type="password")
            new_pwd2 = st.text_input("Confirmer le nouveau mot de passe", type="password")
            submitted = st.form_submit_button("🔐 Changer le mot de passe")
        if submitted:
            user = check_login(st.session_state.username, old_pwd)
            if not user: st.error("Mot de passe actuel incorrect.")
            elif new_pwd != new_pwd2: st.error("Les nouveaux mots de passe ne correspondent pas.")
            elif len(new_pwd) < 6: st.error("Le mot de passe doit faire au moins 6 caractères.")
            else:
                new_hash = hashlib.sha256(new_pwd.encode()).hexdigest()
                conn.execute("UPDATE users SET password_hash=? WHERE username=?", (new_hash, st.session_state.username))
                conn.commit()
                log_action("Changement mot de passe","Mot de passe modifié")
                st.success("✅ Mot de passe modifié.")

    with tabs[3]:
        st.markdown("### 💾 Sauvegarde et Restauration des données")

        st.markdown("#### ⬇️ Télécharger mes données")
        st.markdown("""
        <div style='background:#0D2A1F;border:1px solid #1A5C3A;border-radius:8px;padding:12px;font-size:.84rem;color:#F0F4FF;margin-bottom:12px'>
        📌 <b>Important :</b> Téléchargez régulièrement votre base de données pour ne pas perdre vos données.
        La base SQLite contient toutes vos ruches, inspections, récoltes et paramètres.
        </div>
        """, unsafe_allow_html=True)

        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            if os.path.exists(DB_PATH):
                with open(DB_PATH, "rb") as f:
                    db_bytes = f.read()
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
                st.download_button(
                    "⬇️ Télécharger la base SQLite (complète)",
                    db_bytes,
                    f"apitrack_backup_{timestamp}.db",
                    "application/octet-stream",
                    use_container_width=True
                )

        with col_dl2:
            # Export CSV de mes données personnelles
            df_my_data = pd.read_sql("""
                SELECT r.nom, r.race, r.localisation, i.date_inspection,
                       i.varroa_pct, i.nb_cadres, i.poids_kg, i.comportement, i.notes
                FROM ruches r LEFT JOIN inspections i ON i.ruche_id=r.id
                WHERE r.user_id=? ORDER BY r.nom, i.date_inspection DESC
            """, conn, params=(uid,))
            if not df_my_data.empty:
                csv_data = df_my_data.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "⬇️ Exporter mes données (CSV)",
                    csv_data,
                    f"mes_donnees_apitrack_{timestamp}.csv",
                    "text/csv",
                    use_container_width=True
                )

        st.markdown("---")
        st.markdown("#### ⬆️ Charger une sauvegarde")
        st.markdown("""
        <div style='background:#2A0D0D;border:1px solid #5C1A1A;border-radius:8px;padding:12px;font-size:.84rem;color:#F0F4FF;margin-bottom:12px'>
        ⚠️ <b>Attention :</b> Le chargement d'une base de données <b>remplace entièrement</b> les données actuelles.
        Assurez-vous d'avoir une sauvegarde récente avant de procéder.
        </div>
        """, unsafe_allow_html=True)

        uploaded_db = st.file_uploader(
            "Charger une base SQLite (.db)",
            type=["db"],
            help="Fichier .db téléchargé précédemment depuis ApiTrack Pro"
        )

        if uploaded_db is not None:
            st.warning(f"📁 Fichier sélectionné : **{uploaded_db.name}** ({len(uploaded_db.getvalue()):,} octets)")
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                confirm_restore = st.text_input("Tapez 'RESTAURER' pour confirmer", key="confirm_restore")
            with col_r2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("⬆️ Restaurer la base de données", type="secondary"):
                    if confirm_restore == "RESTAURER":
                        try:
                            # Vérifier que c'est une base SQLite valide
                            db_content = uploaded_db.getvalue()
                            if not db_content.startswith(b'SQLite format 3'):
                                st.error("❌ Ce fichier n'est pas une base SQLite valide.")
                            else:
                                # Créer une sauvegarde de l'actuelle
                                if os.path.exists(DB_PATH):
                                    backup_path = f"apitrack_before_restore_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                                    with open(backup_path, "rb") as f_old:
                                        old_data = f_old.read()
                                    with open(backup_path, "wb") as f_bak:
                                        f_bak.write(old_data)

                                # Écrire la nouvelle base
                                with open(DB_PATH, "wb") as f_new:
                                    f_new.write(db_content)

                                log_action("Base de données restaurée", f"Fichier : {uploaded_db.name}")
                                st.success("✅ Base de données restaurée avec succès ! Reconnectez-vous.")
                                st.info("💡 Une sauvegarde de l'ancienne base a été créée automatiquement.")
                                for k in ["logged_in","username","user_id","user_role","page"]:
                                    st.session_state.pop(k, None)
                                st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erreur lors de la restauration : {e}")
                    else:
                        st.error("Tapez exactement 'RESTAURER' pour confirmer.")

        st.markdown("---")
        st.markdown("### 📊 Statistiques de la base")
        tables = ["users","ruches","inspections","traitements","recoltes","morph_analyses","zones","journal"]
        stats = {}
        for t in tables:
            n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            stats[t] = n
        df_stats = pd.DataFrame({"Table":stats.keys(),"Enregistrements":stats.values()})
        st.dataframe(df_stats, use_container_width=True, hide_index=True)

        version = get_setting("version","4.0.0")
        st.markdown(f"<div class='api-footer'>ApiTrack Pro v{version} · Streamlit · SQLite · © 2025</div>", unsafe_allow_html=True)

    # Onglet admin uniquement
    if role == "admin" and len(tabs) > 4:
        with tabs[4]:
            st.markdown("### 👥 Gestion des utilisateurs")
            st.markdown("Gérez les comptes utilisateurs. Chaque utilisateur a ses propres données.")

            df_users = pd.read_sql("SELECT id, username, email, role, created_at FROM users", conn)
            st.dataframe(df_users, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown("#### ➕ Créer un nouveau compte")
            with st.form("add_user_form"):
                col1, col2 = st.columns(2)
                new_username = col1.text_input("Identifiant*")
                new_email = col2.text_input("Email")
                col3, col4 = st.columns(2)
                new_password = col3.text_input("Mot de passe*", type="password")
                new_role = col4.selectbox("Rôle", ["apiculteur","admin"])
                if st.form_submit_button("✅ Créer le compte"):
                    if new_username and new_password:
                        h = hashlib.sha256(new_password.encode()).hexdigest()
                        try:
                            conn.execute("INSERT INTO users (username,password_hash,email,role) VALUES (?,?,?,?)",
                                         (new_username,h,new_email,new_role))
                            conn.commit()
                            log_action("Création compte", f"Utilisateur {new_username} créé")
                            st.success(f"✅ Compte '{new_username}' créé avec succès.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erreur : {e} (identifiant peut-être déjà utilisé)")
                    else:
                        st.warning("Identifiant et mot de passe requis.")

            st.markdown("#### 🗑️ Supprimer un compte")
            users_list = conn.execute("SELECT id, username FROM users WHERE username != 'admin'").fetchall()
            if users_list:
                user_opts = {u[1]: u[0] for u in users_list}
                user_to_delete = st.selectbox("Compte à supprimer", user_opts.keys())
                if st.button("🗑️ Supprimer ce compte", type="secondary"):
                    conn.execute("DELETE FROM users WHERE id=?", (user_opts[user_to_delete],))
                    conn.commit()
                    st.success(f"✅ Compte '{user_to_delete}' supprimé.")
                    st.rerun()

    conn.close()


# ════════════════════════════════════════════════════════════════════════════
# PAGES RESTANTES (Génétique, Flore, Alertes, Journal, Morpho, etc.)
# ════════════════════════════════════════════════════════════════════════════
def page_genetique():
    st.markdown("## 📊 Génétique & Sélection")
    uid = get_user_id()
    conn = get_db()
    df = pd.read_sql("""
        SELECT r.nom, r.race,
               COALESCE(AVG(i.varroa_pct),0) as varroa_moy,
               COALESCE(AVG(i.nb_cadres),0) as cadres_moy,
               COALESCE(SUM(rec.quantite_kg),0) as production_totale,
               COUNT(i.id) as nb_inspections
        FROM ruches r
        LEFT JOIN inspections i ON i.ruche_id=r.id
        LEFT JOIN recoltes rec ON rec.ruche_id=r.id AND rec.type_produit='miel'
        WHERE r.user_id=? AND r.statut='actif'
        GROUP BY r.id,r.nom,r.race ORDER BY production_totale DESC
    """, conn, params=(uid,))
    conn.close()
    if not df.empty:
        df["VSH_score"] = df["varroa_moy"].apply(lambda v: max(0,min(100,100-v*20)))
        df["Score global"] = (df["production_totale"].rank(pct=True)*40 + df["VSH_score"].rank(pct=True)*35 + (1-df["varroa_moy"].rank(pct=True))*25).round(1)
        st.markdown("### 🏆 Top 3 candidates élevage")
        top3 = df.nlargest(3,"Score global")
        for i, (_, row) in enumerate(top3.iterrows()):
            medal = ["🥇","🥈","🥉"][i]
            st.success(f"{medal} **{row['nom']}** ({row['race']}) — Score : {row['Score global']:.1f}/100 · VSH {row['VSH_score']:.0f}% · Production {row['production_totale']:.1f} kg")
        df_display = df[["nom","race","varroa_moy","cadres_moy","production_totale","VSH_score","Score global"]].copy()
        df_display.columns = ["Ruche","Race","Varroa moy%","Cadres moy","Production kg","VSH%","Score/100"]
        st.dataframe(df_display.round(2), use_container_width=True, hide_index=True)
        if len(df) > 0:
            ruche_sel = st.selectbox("Profil radar", df["nom"].tolist())
            row = df[df["nom"]==ruche_sel].iloc[0]
            categories = ["Production","VSH","Douceur","Économie hivernale","Propolis"]
            values = [min(100,row["production_totale"]*2), row["VSH_score"], max(0,100-row["varroa_moy"]*15), 70, 60]
            fig = go.Figure(go.Scatterpolar(r=values+[values[0]], theta=categories+[categories[0]], fill="toself", fillcolor="rgba(200,130,10,0.2)", line_color="#C8820A"))
            fig.update_layout(polar=dict(radialaxis=dict(range=[0,100])), height=350, paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune donnée disponible. Ajoutez des ruches et des inspections.")


def page_flore():
    st.markdown("## 🌿 Flore mellifère — Calendrier")
    flore_data = [
        {"Espèce":"Romarin (Rosmarinus officinalis)","Nectar":"⭐⭐⭐","Pollen":"⭐⭐","Propolis":"-","Période":"Fév–Avr","Potentiel":"Élevé"},
        {"Espèce":"Jujubier (Ziziphus lotus)","Nectar":"⭐⭐⭐⭐","Pollen":"⭐⭐⭐","Propolis":"-","Période":"Avr–Juin","Potentiel":"Exceptionnel"},
        {"Espèce":"Chêne-liège (Quercus suber)","Nectar":"⭐","Pollen":"⭐⭐⭐⭐","Propolis":"⭐⭐","Période":"Avr–Mai","Potentiel":"Élevé"},
        {"Espèce":"Lavande (Lavandula stoechas)","Nectar":"⭐⭐⭐","Pollen":"⭐⭐","Propolis":"-","Période":"Mai–Juil","Potentiel":"Élevé"},
        {"Espèce":"Thym (Thymus algeriensis)","Nectar":"⭐⭐⭐","Pollen":"⭐⭐⭐","Propolis":"⭐","Période":"Mar–Juin","Potentiel":"Élevé"},
        {"Espèce":"Eucalyptus (E. globulus)","Nectar":"⭐⭐⭐⭐","Pollen":"⭐⭐","Propolis":"⭐","Période":"Été","Potentiel":"Élevé"},
        {"Espèce":"Caroube (Ceratonia siliqua)","Nectar":"⭐⭐","Pollen":"⭐⭐","Propolis":"-","Période":"Sep–Oct","Potentiel":"Modéré"},
    ]
    st.dataframe(pd.DataFrame(flore_data), use_container_width=True, hide_index=True)
    st.markdown("### 📅 Calendrier de miellée")
    mois = ["Jan","Fév","Mar","Avr","Mai","Juin","Juil","Aoû","Sep","Oct","Nov","Déc"]
    esp = ["Romarin","Jujubier","Chêne-liège","Lavande","Thym","Eucalyptus","Caroube"]
    activite = np.array([[0,3,3,2,0,0,0,0,0,0,0,0],[0,0,0,3,3,2,0,0,0,0,0,0],[0,0,0,3,3,0,0,0,0,0,0,0],[0,0,0,0,3,3,3,0,0,0,0,0],[0,0,3,3,3,2,0,0,0,0,0,0],[0,0,0,0,0,0,3,3,2,0,0,0],[0,0,0,0,0,0,0,0,3,3,0,0]], dtype=float)
    fig = px.imshow(activite, labels=dict(x="Mois",y="Espèce",color="Intensité"), x=mois, y=esp,
                    color_continuous_scale=[[0,"#F5EDD8"],[0.5,"#F5C842"],[1,"#C8820A"]], template="plotly_white")
    fig.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=10,b=10,l=0,r=0))
    st.plotly_chart(fig, use_container_width=True)


def page_alertes():
    st.markdown("## ⚠️ Alertes")
    uid = get_user_id()
    conn = get_db()
    df_crit = pd.read_sql("""
        SELECT r.nom, i.varroa_pct, i.date_inspection, i.notes
        FROM inspections i JOIN ruches r ON r.id=i.ruche_id
        WHERE r.user_id=? AND i.varroa_pct >= 3.0 AND i.date_inspection >= date('now','-7 days')
        ORDER BY i.varroa_pct DESC
    """, conn, params=(uid,))
    df_warn = pd.read_sql("""
        SELECT r.nom, i.varroa_pct, i.date_inspection
        FROM inspections i JOIN ruches r ON r.id=i.ruche_id
        WHERE r.user_id=? AND i.varroa_pct >= 2.0 AND i.varroa_pct < 3.0 AND i.date_inspection >= date('now','-7 days')
        ORDER BY i.varroa_pct DESC
    """, conn, params=(uid,))
    conn.close()
    if not df_crit.empty:
        st.markdown("### 🔴 Alertes critiques (Varroa ≥ 3%)")
        for _, row in df_crit.iterrows():
            st.error(f"🔴 **{row['nom']}** — Varroa **{row['varroa_pct']}%** le {row['date_inspection']} · Traitement immédiat requis !")
    if not df_warn.empty:
        st.markdown("### 🟡 Alertes attention (Varroa ≥ 2%)")
        for _, row in df_warn.iterrows():
            st.warning(f"🟡 **{row['nom']}** — Varroa **{row['varroa_pct']}%** le {row['date_inspection']} · Surveillance renforcée.")
    if df_crit.empty and df_warn.empty:
        st.success("✅ Aucune alerte active en ce moment.")


def page_journal():
    st.markdown("## 📋 Journal d'activité")
    conn = get_db()
    df = pd.read_sql("SELECT * FROM journal ORDER BY timestamp DESC LIMIT 100", conn)
    conn.close()
    if not df.empty:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Exporter CSV", csv, "journal.csv", "text/csv")
        st.dataframe(df, use_container_width=True, hide_index=True)


RUTTNER_REF = {
    "intermissa":  {"aile":(8.9,9.4),"cubital":(2.0,2.8),"glossa":(5.8,6.3)},
    "sahariensis": {"aile":(9.0,9.5),"cubital":(1.9,2.5),"glossa":(6.0,6.5)},
    "ligustica":   {"aile":(9.2,9.8),"cubital":(2.5,3.2),"glossa":(6.3,6.8)},
    "carnica":     {"aile":(9.3,9.9),"cubital":(2.2,3.0),"glossa":(6.4,7.0)},
    "hybride":     {"aile":(8.5,9.5),"cubital":(1.8,3.5),"glossa":(5.5,6.8)},
}

def classify_race(aile, cubital, glossa):
    scores = {}
    for race, ref in RUTTNER_REF.items():
        s = 0
        for val, (lo, hi) in [(aile,ref["aile"]),(cubital,ref["cubital"]),(glossa,ref["glossa"])]:
            if val is None: s += 0.5
            elif lo <= val <= hi: s += 1.0
            else: s += max(0, 1.0-min(abs(val-lo),abs(val-hi))*0.5)
        scores[race] = s
    total = sum(scores.values()) or 1
    return {r: round(v/total*100) for r, v in scores.items()}

def page_morpho():
    st.markdown("## 🧬 Morphométrie IA — Classification raciale")
    ia_active = widget_cle_api()
    uid = get_user_id()
    conn = get_db()
    opts = get_user_ruches()

    tab1, tab2 = st.tabs(["✏️ Saisie manuelle", "📜 Historique"])

    with tab1:
        col1, col2 = st.columns([1,1.2])
        with col1:
            st.markdown("### 📐 Mesures morphométriques")
            ruche_sel_man = st.selectbox("Ruche analysée", opts.keys() if opts else ["Aucune ruche"])
            aile = st.number_input("Longueur aile antérieure (mm)", 7.0, 12.0, 9.2, 0.1)
            largeur = st.number_input("Largeur aile (mm)", 2.0, 5.0, 3.1, 0.1)
            cubital = st.number_input("Indice cubital", 1.0, 5.0, 2.3, 0.1)
            glossa = st.number_input("Longueur glossa (mm)", 4.0, 8.0, 6.1, 0.1)
            tomentum = st.slider("Tomentum (0–3)", 0, 3, 2)
            pigmentation = st.selectbox("Pigmentation scutellum", ["Noir","Brun foncé","Brun clair","Jaune"])
            notes_man = st.text_area("Notes")
            img_file_man = st.file_uploader("Photo macro (optionnel)", type=["jpg","jpeg","png"])
            col_btn1, col_btn2 = st.columns(2)
            btn_local = col_btn1.button("🔬 Classifier (local)", use_container_width=True)
            btn_ia = col_btn2.button("🤖 Analyser avec l'IA", use_container_width=True, disabled=not ia_active)

        with col2:
            st.markdown("### 📊 Classification Ruttner 1988")
            scores = classify_race(aile, cubital, glossa)
            race_prob = max(scores, key=scores.get)
            confiance = scores[race_prob]
            st.markdown(f"""<div style='background:#0F1117;border:1px solid #C8820A;border-left:4px solid #C8820A;border-radius:8px;padding:12px 16px;margin-bottom:12px'>
                <div style='font-size:.95rem;font-weight:600;color:#F0F4FF'>Race probable : <span style='color:#F5A623'>Apis mellifera {race_prob}</span></div>
                <div style='font-size:.78rem;color:#A8B4CC'>Confiance {confiance}% · aile={aile}mm / cubital={cubital} / glossa={glossa}mm</div>
            </div>""", unsafe_allow_html=True)
            couleurs = {"intermissa":"#C8820A","sahariensis":"#8B7355","ligustica":"#2E7D32","carnica":"#1565C0","hybride":"#888"}
            fig = go.Figure()
            for race, pct in sorted(scores.items(), key=lambda x: -x[1]):
                fig.add_trace(go.Bar(y=[race], x=[pct], orientation="h", marker_color=couleurs.get(race,"#ccc"), text=f"{pct}%", textposition="auto", name=race))
            fig.update_layout(height=220, showlegend=False, template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=0,b=0,l=0,r=10), xaxis=dict(range=[0,100]))
            st.plotly_chart(fig, use_container_width=True)

        if btn_local and opts:
            rid = opts[ruche_sel_man]
            conf_json = json.dumps([{"race":r,"confiance":p} for r,p in scores.items()])
            conn.execute("INSERT INTO morph_analyses (ruche_id,date_analyse,longueur_aile_mm,largeur_aile_mm,indice_cubital,glossa_mm,tomentum,pigmentation,race_probable,confiance_json,notes) VALUES (?,date('now'),?,?,?,?,?,?,?,?,?)",
                         (rid,aile,largeur,cubital,glossa,tomentum,pigmentation,race_prob,conf_json,notes_man))
            conn.commit()
            log_action("Morphométrie manuelle", f"Ruche {ruche_sel_man} — {race_prob}")
            st.success(f"✅ Classification sauvegardée : **{race_prob}** ({confiance}%)")

        if btn_ia and opts:
            img_bytes = img_file_man.read() if img_file_man else None
            with st.spinner("🤖 Analyse IA en cours..."):
                resultat_ia = ia_analyser_morphometrie(aile,largeur,cubital,glossa,tomentum,pigmentation,race_prob,confiance,img_bytes)
            if resultat_ia and not resultat_ia.startswith("❌"):
                afficher_resultat_ia(resultat_ia, "Analyse morphométrique approfondie")
                rid = opts[ruche_sel_man]
                conf_json = json.dumps([{"race":r,"confiance":p} for r,p in scores.items()])
                conn.execute("INSERT INTO morph_analyses (ruche_id,date_analyse,longueur_aile_mm,largeur_aile_mm,indice_cubital,glossa_mm,tomentum,pigmentation,race_probable,confiance_json,notes) VALUES (?,date('now'),?,?,?,?,?,?,?,?,?)",
                             (rid,aile,largeur,cubital,glossa,tomentum,pigmentation,race_prob,conf_json,f"[IA] {notes_man}"))
                conn.commit()
            elif resultat_ia:
                st.error(resultat_ia)

    with tab2:
        df = pd.read_sql("""
            SELECT m.id, r.nom as ruche, m.date_analyse, m.longueur_aile_mm,
                   m.indice_cubital, m.glossa_mm, m.race_probable, m.notes
            FROM morph_analyses m JOIN ruches r ON r.id=m.ruche_id
            WHERE r.user_id=? ORDER BY m.date_analyse DESC
        """, conn, params=(uid,))
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune analyse enregistrée.")
    conn.close()


def page_pedigree():
    st.markdown("## 🧬 Pedigree & Sélection")
    uid = get_user_id()
    conn = get_db()
    opts = get_user_ruches()
    if not opts:
        st.info("Ajoutez des ruches pour utiliser cette fonctionnalité.")
        conn.close()
        return
    tab1, tab2 = st.tabs(["➕ Ajouter une parenté", "📋 Historique"])
    with tab1:
        with st.form("form_pedigree"):
            col1,col2,col3 = st.columns(3)
            fille = col1.selectbox("Reine fille", opts.keys())
            mere = col2.selectbox("Reine mère", ["Inconnue"]+list(opts.keys()))
            pere = col3.selectbox("Ruche père", ["Inconnu"]+list(opts.keys()))
            date_naiss = st.date_input("Date de naissance estimée")
            notes = st.text_area("Notes")
            if st.form_submit_button("Enregistrer la parenté"):
                rid_fille = opts[fille]
                rid_mere = opts[mere] if mere != "Inconnue" else None
                rid_pere = opts[pere] if pere != "Inconnu" else None
                conn.execute("INSERT INTO pedigree (reine_fille_id,reine_mere_id,ruche_pere_id,date_naissance,notes) VALUES (?,?,?,?,?)",
                             (rid_fille,rid_mere,rid_pere,str(date_naiss),notes))
                conn.commit()
                st.success("Parenté enregistrée.")
                st.rerun()
    with tab2:
        df_ped = pd.read_sql("""
            SELECT p.id, f.nom as fille, m.nom as mere, pe.nom as pere, p.date_naissance, p.notes
            FROM pedigree p
            LEFT JOIN ruches f ON f.id=p.reine_fille_id
            LEFT JOIN ruches m ON m.id=p.reine_mere_id
            LEFT JOIN ruches pe ON pe.id=p.ruche_pere_id
            ORDER BY p.date_naissance DESC
        """, conn)
        if not df_ped.empty:
            st.dataframe(df_ped, use_container_width=True, hide_index=True)
    conn.close()


def page_male_market():
    st.markdown("## 🤝 Bourse aux Mâles - Réseau Collaboratif")
    uid = get_user_id()
    conn = get_db()
    tab1, tab2 = st.tabs(["📋 Stocks disponibles", "📢 Déclarer mes Mâles"])
    with tab1:
        df_males = pd.read_sql("""
            SELECT m.id, r.nom, m.race_male, m.score_vsh, m.rayon_km, m.contact_prefere, m.date_mise_a_jour
            FROM male_stocks m JOIN ruches r ON m.ruche_id=r.id WHERE m.disponibilite=1
        """, conn)
        if not df_males.empty:
            st.dataframe(df_males, use_container_width=True, hide_index=True)
        else:
            st.info("Aucun stock de mâles déclaré.")
    with tab2:
        opts = get_user_ruches()
        if opts:
            with st.form("declare_male"):
                ruche_sel = st.selectbox("Ruche productrice", opts.keys())
                race_male = st.text_input("Race des mâles", "intermissa")
                vsh = st.slider("Score VSH estimé (%)", 0, 100, 75)
                rayon = st.slider("Rayon d'action estimé (km)", 1, 20, 5)
                contact = st.text_input("Contact (optionnel)")
                dispo = st.checkbox("Disponible actuellement", value=True)
                if st.form_submit_button("📢 Publier"):
                    rid = opts[ruche_sel]
                    conn.execute("INSERT OR REPLACE INTO male_stocks (ruche_id,race_male,score_vsh,rayon_km,contact_prefere,disponibilite,date_mise_a_jour) VALUES (?,?,?,?,?,?,date('now'))",
                                 (rid,race_male,vsh,rayon,contact,1 if dispo else 0))
                    conn.commit()
                    st.success("Stock de mâles publié !")
                    st.rerun()
    conn.close()


def page_cadre_scanner():
    st.markdown("## 📸 Scanner de Cadre - Détection IA de Maladies")
    ia_active = widget_cle_api()
    img_file = st.file_uploader("Photo du cadre de couvain", type=["jpg","jpeg","png"])
    if img_file:
        image = Image.open(img_file) if PIL_OK else None
        if image: st.image(image, caption="Cadre à analyser", use_container_width=True)
        if st.button("🔍 Analyser avec l'IA", disabled=not ia_active):
            with st.spinner("Analyse en cours..."):
                img_bytes = img_file.getvalue()
                prompt = """IMPORTANT : Réponds UNIQUEMENT en français.
Tu es un expert en pathologie apicole. Analyse cette photo de cadre de couvain.
Décris en français ce que tu vois : présence de loque américaine, loque européenne, couvain plâtré, varroa, ou couvain sain.
Fournis un diagnostic structuré avec :
1. **État général du cadre** observé
2. **Pathologies détectées ou suspectées** avec niveau de certitude
3. **Recommandations** de traitement en français
4. **Urgence** : [Immédiate/Surveillance/RAS]"""
                result = ia_call(prompt, img_bytes)
            if result and not result.startswith("❌"):
                afficher_resultat_ia(result, "Diagnostic du cadre — IA")
                if "loque" in result.lower():
                    st.error("⚠️ Suspicion de loque ! Isolez la ruche et contactez un vétérinaire.")
            else:
                st.warning("Impossible d'analyser. Vérifiez votre fournisseur IA.")


def page_transhumance():
    st.markdown("## 🚚 Prédiction de Transhumance")
    uid = get_user_id()
    ia_active = widget_cle_api()
    conn = get_db()
    zones = pd.read_sql("SELECT id, nom, latitude, longitude, ndvi, potentiel FROM zones WHERE user_id=?", conn, params=(uid,))
    if zones.empty:
        st.warning("Aucune zone enregistrée. Ajoutez-en dans la page Cartographie.")
        conn.close()
        return
    zone_sel = st.selectbox("Zone cible", zones['nom'].tolist())
    zone_data = zones[zones['nom']==zone_sel].iloc[0]
    col1,col2 = st.columns(2)
    col1.metric("🌿 NDVI", f"{zone_data['ndvi']:.2f}")
    col2.metric("📍 Potentiel", zone_data['potentiel'])
    if st.button("🤖 Prédire le potentiel de miellée", disabled=not ia_active):
        with st.spinner("Analyse IA..."):
            prompt = f"""IMPORTANT : Réponds UNIQUEMENT en français.
Expert apicole, analyse cette zone pour une transhumance dans 7 jours.
Zone : {zone_data['nom']} (lat {zone_data['latitude']}, lon {zone_data['longitude']})
NDVI : {zone_data['ndvi']}, Potentiel : {zone_data['potentiel']}
Fournis en français une recommandation détaillée : déplacer ou non, nombre de ruches conseillé, période de pic de miellée, précautions."""
            reponse = ia_call(prompt)
        if reponse and not reponse.startswith("❌"):
            afficher_resultat_ia(reponse, "Prédiction de transhumance")
            conn.execute("INSERT INTO transhumance_predictions (zone_id,date_prediction,potentiel_miel,recommandation) VALUES (?,date('now'),?,?)",
                         (int(zone_data['id']),8.5,reponse[:500]))
            conn.commit()
    conn.close()


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

    page = st.session_state.get("page","dashboard")
    router = {
        "dashboard": page_dashboard,
        "ruches": page_ruches,
        "inspections": page_inspections,
        "traitements": page_traitements,
        "productions": page_productions,
        "morpho": page_morpho,
        "carto": page_carto,
        "meteo": page_meteo,
        "genetique": page_genetique,
        "flore": page_flore,
        "alertes": page_alertes,
        "journal": page_journal,
        "admin": page_admin,
        "voice_inspection": page_voice_inspection,
        "pedigree": page_pedigree,
        "male_market": page_male_market,
        "cadre_scanner": page_cadre_scanner,
        "transhumance": page_transhumance,
    }
    fn = router.get(page, page_dashboard)
    fn()

    st.markdown("""
    <div class='api-footer'>
        🐝 ApiTrack Pro v4.0 · Streamlit + Python + SQLite · Multi-utilisateurs · 2025
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
