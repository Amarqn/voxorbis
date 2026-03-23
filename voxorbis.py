# -*- coding: utf-8 -*-
"""
VoxOrbis - Atlas interactif des langues du monde
Projet universitaire, Amar C.C
Paul-Valéry Montpellier, 2025

Streamlit app avec Plotly pour les cartes, CSS custom pour le design dark/glass.
"""

# TODO: ajouter les langues autochtones d'Australie (Pitjantjatjara, Warlpiri...)
# TODO: fix le scroll qui saute quand on ouvre le panel stats sur mobile
# TODO: rajouter un mode sombre/clair ? (pour l'instant on garde full dark)
# TODO: intégrer les données UNESCO 2024 quand elles sortent
# TODO: page "a propos" avec les sources et la methodo
# TODO: exporter les fiches en PDF (demandé par M. Dupont)
# TODO: tester perf sur les ordis de la fac (ils sont lents...)
# FIXME: le réseau Kamada-Kawai freeze sur les machines < 4Go RAM
# NOTE: les données locuteurs sont des estimations (Ethnologue 26e + Glottolog 4.8)

import streamlit as st
import pandas as pd
import math
import base64
import os

st.set_page_config(
    page_title="VoxOrbis | Atlas des Langues",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# background.gif en base64 (on lit le fichier brut, pas de PIL pour garder les frames)
_bg_css_val = "linear-gradient(135deg, #1a0a2e 0%, #2d1b4e 40%, #1a1040 100%)"
_bg_gif = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "background.gif")
if os.path.exists(_bg_gif):
    try:
        with open(_bg_gif, "rb") as _f:
            _b64 = base64.b64encode(_f.read()).decode()
        _bg_css_val = f'url("data:image/gif;base64,{_b64}") center center / cover no-repeat fixed'
    except Exception:
        pass

# mute toggle (son activé par defaut)
if "muted" not in st.session_state:
    st.session_state.muted = False
_is_muted = st.session_state.muted

# theme toujours dark (on a retiré le light mode)
_is_light = False

# variables CSS (dark only)
_tv = {
    "bg": "rgba(255,255,255,0.07)", "border": "rgba(167,139,250,0.25)", "border_h": "rgba(167,139,250,0.5)",
    "text": "#f1f0ff", "text_s": "#c4b5fd", "text_m": "#8b7ac9",
    "app_bg": _bg_css_val, "app_overlay": "rgba(15,8,30,0.62)",
    "card_bg": "rgba(255,255,255,0.07)", "card_shadow": "0 4px 16px rgba(0,0,0,0.25)",
    "input_bg": "rgba(255,255,255,0.07)", "metric_val": "#a78bfa",
    "land": "#1e1035", "ocean": "#0d0820", "coast": "rgba(167,139,250,0.25)",
}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=Fraunces:ital,wght@0,300;0,600;0,700;1,300;1,400&display=swap');

:root {{
  --violet:    #7c3aed;
  --violet-l:  #a78bfa;
  --violet-ll: #ddd6fe;
  --violet-d:  #5b21b6;
  --rose:      #ec4899;
  --teal:      #14b8a6;
  --amber:     #f59e0b;
  --sky:       #38bdf8;
  --bg:        {_tv['bg']};
  --border:    {_tv['border']};
  --border-h:  {_tv['border_h']};
  --text:      {_tv['text']};
  --text-s:    {_tv['text_s']};
  --text-m:    {_tv['text_m']};
  --shadow:    0 8px 32px rgba(0,0,0,{'0.12' if _is_light else '0.35'});
  --shadow-sm: {_tv['card_shadow']};
  --glow:      0 0 20px rgba(124,58,237,{'0.15' if _is_light else '0.35'});
  --r:         18px;
  --r-sm:      12px;
  --blur:      blur(20px) saturate(180%);
  --blur-sm:   blur(12px) saturate(160%);
}}

@keyframes fadeUp  {{ from {{ opacity:0; transform:translateY(24px); }} to {{ opacity:1; transform:translateY(0); }} }}
@keyframes fadeIn  {{ from {{ opacity:0; }} to {{ opacity:1; }} }}
@keyframes float   {{ 0%,100% {{ transform:translateY(0); }} 50% {{ transform:translateY(-8px); }} }}
@keyframes pulse-dot {{ 0%,100% {{ transform:scale(1); opacity:1; }} 50% {{ transform:scale(1.5); opacity:0.7; }} }}
@keyframes bar-grow {{ from {{ width:0; }} to {{ width:var(--bar-w); }} }}
@keyframes slideIn {{ from {{ opacity:0; transform:translateX(30px); }} to {{ opacity:1; transform:translateX(0); }} }}
@keyframes glow-pulse {{ 0%,100% {{ box-shadow: 0 0 20px rgba(124,58,237,0.4); }} 50% {{ box-shadow: 0 0 40px rgba(124,58,237,0.8), 0 0 60px rgba(236,72,153,0.3); }} }}
@keyframes rotate-slow {{ from {{ transform:rotate(0deg); }} to {{ transform:rotate(360deg); }} }}
@keyframes shimmer-text {{
  0%   {{ background-position: -200% center; }}
  100% {{ background-position:  200% center; }}
}}



html, body {{ font-family:'Outfit', sans-serif !important; }}

/* ── CURSEUR CUSTOM ── */
*, *::before, *::after {{
  cursor: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24'%3E%3Cdefs%3E%3CradialGradient id='g' cx='30%25' cy='30%25'%3E%3Cstop offset='0%25' stop-color='%23a78bfa'/%3E%3Cstop offset='100%25' stop-color='%237c3aed'/%3E%3C/radialGradient%3E%3Cfilter id='f'%3E%3CfeDropShadow dx='0' dy='0' stdDeviation='1.5' flood-color='%237c3aed' flood-opacity='0.8'/%3E%3C/filter%3E%3C/defs%3E%3Cpath d='M4 2 L4 18 L8.5 13.5 L12 20 L14 19 L10.5 12.5 L17 12.5 Z' fill='url(%23g)' stroke='%23ddd6fe' stroke-width='0.8' stroke-linejoin='round' filter='url(%23f)'/%3E%3C/svg%3E") 4 2, auto !important;
}}

a, button, [role="button"],
.stButton > button,
.home-nav-card,
select, [data-baseweb="select"],
input[type="range"],
label {{
  cursor: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='28' height='28' viewBox='0 0 28 28'%3E%3Cdefs%3E%3CradialGradient id='g' cx='35%25' cy='35%25'%3E%3Cstop offset='0%25' stop-color='%2322d3ee'/%3E%3Cstop offset='100%25' stop-color='%230e7490'/%3E%3C/radialGradient%3E%3Cfilter id='f'%3E%3CfeDropShadow dx='0' dy='0' stdDeviation='2' flood-color='%2322d3ee' flood-opacity='0.9'/%3E%3C/filter%3E%3C/defs%3E%3Ccircle cx='14' cy='14' r='6' fill='url(%23g)' filter='url(%23f)' opacity='0.95'/%3E%3Ccircle cx='14' cy='14' r='9' fill='none' stroke='%2322d3ee' stroke-width='1.2' opacity='0.5'/%3E%3Ccircle cx='14' cy='14' r='1.8' fill='%23f0fdfa'/%3E%3C/svg%3E") 14 14, pointer !important;
}}

input[type="text"], input[type="number"], textarea {{
  cursor: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='24' viewBox='0 0 20 24'%3E%3Cdefs%3E%3Cfilter id='f'%3E%3CfeDropShadow dx='0' dy='0' stdDeviation='1.5' flood-color='%23a78bfa' flood-opacity='0.8'/%3E%3C/filter%3E%3C/defs%3E%3Crect x='9' y='0' width='2' height='6' rx='1' fill='%23a78bfa' filter='url(%23f)'/%3E%3Crect x='9' y='18' width='2' height='6' rx='1' fill='%23a78bfa' filter='url(%23f)'/%3E%3Crect x='5' y='5' width='10' height='14' rx='1' fill='none' stroke='%23a78bfa' stroke-width='1.5' filter='url(%23f)'/%3E%3C/svg%3E") 10 12, text !important;
}}

/* ── BACKGROUND ── */
.stApp {{
  background: {_tv['app_bg']} !important;
  min-height: 100vh !important;
}}
.stApp::before {{
  content:''; position:fixed; inset:0; z-index:0; pointer-events:none;
  background: {'rgba(255,255,255,0.3)' if _is_light else f"""
    radial-gradient(ellipse 55% 45% at 15% 20%, rgba(124,58,237,0.28) 0%, transparent 60%),
    radial-gradient(ellipse 45% 40% at 85% 75%, rgba(236,72,153,0.18) 0%, transparent 60%),
    radial-gradient(ellipse 35% 30% at 75% 10%, rgba(20,184,166,0.12) 0%, transparent 55%),
    {_tv['app_overlay']}"""};
}}
.stApp > div, .stMainBlockContainer, .stMain, .main {{ position:relative; z-index:1; }}

/* ── RESET ── */
[data-testid="stSidebar"] {{ display:none !important; }}
[data-testid="stHeader"]  {{ display:none !important; }}
#MainMenu, footer, header {{ visibility:hidden !important; }}
.main .block-container {{
  padding: 0 !important; max-width: 100% !important;
  background: transparent !important; box-shadow: none !important;
  border: none !important;
}}

/* ══════════════════════════════════
   back button (glassmorphism style)
   ══════════════════════════════════ */
.back-btn-wrap .stButton > button {{
  font-family:'Outfit',sans-serif !important;
  font-weight:800 !important;
  font-size:0.78rem !important;
  letter-spacing:0.06em !important;
  background: linear-gradient(135deg, rgba(124,58,237,0.22), rgba(236,72,153,0.12)) !important;
  backdrop-filter: blur(20px) saturate(200%) !important;
  -webkit-backdrop-filter: blur(20px) saturate(200%) !important;
  color: #e9d5ff !important;
  border: 1.5px solid rgba(167,139,250,0.4) !important;
  border-radius: 60px !important;
  padding: 0.55rem 1.4rem 0.55rem 1rem !important;
  transition: all 0.3s cubic-bezier(.34,1.56,.64,1) !important;
  box-shadow: 0 6px 24px rgba(0,0,0,0.4),
              0 0 0 1px rgba(167,139,250,0.1),
              inset 0 1px 0 rgba(255,255,255,0.12) !important;
  text-transform: uppercase !important;
}}
.back-btn-wrap .stButton > button:hover {{
  background: linear-gradient(135deg, rgba(124,58,237,0.45), rgba(236,72,153,0.25)) !important;
  border-color: #c4b5fd !important;
  color: #ffffff !important;
  transform: translateX(-4px) scale(1.06) !important;
  box-shadow: 0 8px 32px rgba(0,0,0,0.5),
              0 0 28px rgba(124,58,237,0.5),
              0 0 56px rgba(236,72,153,0.2),
              inset 0 1px 0 rgba(255,255,255,0.15) !important;
}}
.back-btn-wrap .stButton > button:active {{
  transform: translateX(-2px) scale(0.97) !important;
  box-shadow: 0 4px 16px rgba(0,0,0,0.5), 0 0 12px rgba(124,58,237,0.4) !important;
}}

/* ── GLOBAL BUTTONS ── */
.stButton > button {{
  font-family:'Outfit',sans-serif !important; font-weight:600 !important;
  font-size:0.85rem !important; letter-spacing:0.03em !important;
  background: rgba(124,58,237,0.18) !important;
  color: var(--violet-ll) !important;
  border: 1px solid rgba(167,139,250,0.35) !important;
  border-radius: 50px !important; padding: 0.5rem 1.4rem !important;
  transition: all 0.2s cubic-bezier(.34,1.56,.64,1) !important;
  box-shadow: var(--shadow-sm), inset 0 1px 0 rgba(255,255,255,0.08) !important;
  backdrop-filter: var(--blur-sm) !important;
}}
.stButton > button:hover {{
  background: rgba(124,58,237,0.35) !important;
  border-color: var(--violet-l) !important;
  transform: translateY(-2px) scale(1.03) !important;
  box-shadow: var(--shadow), var(--glow) !important;
  color: white !important;
}}
.stButton > button:active {{ transform: scale(0.97) !important; }}

/* ── HOME NAV CARDS ── */
.home-nav-card {{
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(167,139,250,0.15);
  border-radius: 24px;
  padding: 2rem 1.6rem 1.6rem;
  text-align: center;
  cursor: default;
  transition: transform 0.28s cubic-bezier(.34,1.56,.64,1), box-shadow 0.28s, border-color 0.28s, background 0.28s;
  animation: fadeUp 0.45s ease both;
  position: relative; overflow: hidden;
}}
.home-nav-card::before {{
  content:''; position:absolute; inset:0; border-radius:24px;
  background: linear-gradient(135deg, rgba(255,255,255,0.04) 0%, transparent 60%);
  pointer-events:none;
}}
.home-nav-card:hover {{
  transform: translateY(-8px);
  box-shadow: 0 24px 60px rgba(0,0,0,0.55), var(--glow);
  border-color: rgba(167,139,250,0.35);
  background: rgba(124,58,237,0.1);
}}

/* ── CARD ── */
.lm-card {{
  background: var(--bg); backdrop-filter: var(--blur-sm);
  -webkit-backdrop-filter: var(--blur-sm);
  border: 1px solid var(--border); border-radius: var(--r);
  padding: 1.1rem 1.3rem; margin-bottom: 0.7rem;
  box-shadow: var(--shadow-sm), inset 0 1px 0 rgba(255,255,255,0.06);
  transition: transform 0.22s cubic-bezier(.34,1.56,.64,1), box-shadow 0.22s, border-color 0.22s;
  animation: fadeUp 0.4s ease both;
}}
.lm-card:hover {{
  transform: translateY(-4px);
  box-shadow: var(--shadow), var(--glow);
  border-color: var(--border-h);
}}

/* ── METRICS ── */
[data-testid="stMetric"] {{
  background: var(--bg) !important; backdrop-filter: var(--blur-sm) !important;
  border: 1px solid var(--border) !important; border-radius: var(--r-sm) !important;
  padding: 1rem 1.2rem !important; box-shadow: var(--shadow-sm) !important;
  transition: all 0.22s !important; animation: fadeUp 0.5s ease both !important;
}}
[data-testid="stMetric"]:hover {{ box-shadow: var(--shadow), var(--glow) !important; border-color: var(--border-h) !important; }}
[data-testid="stMetricValue"] {{ font-family:'Outfit',sans-serif !important; color: {_tv['metric_val']} !important; font-size:1.9rem !important; font-weight:800 !important; }}
[data-testid="stMetricLabel"] {{ font-family:'Outfit',sans-serif !important; color: var(--text-m) !important; font-size:0.78rem !important; text-transform:uppercase; letter-spacing:0.06em; }}

/* ── INPUTS ── */
[data-baseweb="select"] > div, .stTextInput input {{
  background: rgba(255,255,255,0.07) !important;
  border: 1px solid var(--border) !important; border-radius: var(--r-sm) !important;
  color: var(--text) !important; backdrop-filter: var(--blur-sm) !important;
  font-family: 'Outfit', sans-serif !important;
}}
[data-baseweb="select"] * {{ color: var(--text) !important; }}

/* ── DROPDOWN ── */
[data-baseweb="popover"],
[data-baseweb="popover"] > div,
[data-baseweb="menu"],
[data-baseweb="menu"] > div,
[role="listbox"],
[role="listbox"] > div,
ul[role="listbox"],
ul[role="listbox"] > li {{
  background: #130826 !important;
  background-color: #130826 !important;
}}
[data-baseweb="popover"] {{
  border: 1px solid rgba(167,139,250,0.3) !important;
  border-radius: 12px !important;
  box-shadow: 0 16px 48px rgba(0,0,0,0.7), 0 0 0 1px rgba(124,58,237,0.2) !important;
  overflow: hidden !important;
}}
[data-baseweb="menu"] ul,
[data-baseweb="menu"] li,
[role="option"],
[role="option"] > div,
[role="option"] span {{
  background: transparent !important;
  background-color: transparent !important;
  color: #d4c8f5 !important;
  font-family: 'Outfit', sans-serif !important;
  font-size: 0.87rem !important;
}}
[role="option"]:hover > div,
[role="option"]:hover,
[aria-selected="true"] > div,
[aria-selected="true"] {{
  background: rgba(124,58,237,0.28) !important;
  background-color: rgba(124,58,237,0.28) !important;
  color: #f1f0ff !important;
  border-radius: 8px !important;
}}
[data-baseweb="select"] span,
[data-baseweb="select"] div {{
  color: var(--text) !important;
}}
.stMultiSelect [data-baseweb="tag"] {{ background: rgba(124,58,237,0.25) !important; border: 1px solid rgba(167,139,250,0.4) !important; border-radius: 20px !important; color: var(--violet-ll) !important; }}
input::placeholder {{ color: var(--text-m) !important; }}
p, span, label, li {{ color: var(--text) !important; font-family:'Outfit',sans-serif !important; }}
.stMarkdown p {{ color: var(--text) !important; }}

/* ── DATAFRAME ── */
[data-testid="stDataFrame"] {{ border: 1px solid var(--border) !important; border-radius: var(--r-sm) !important; background: rgba(255,255,255,0.04) !important; }}
[data-testid="stDataFrame"] th {{ background: rgba(124,58,237,0.15) !important; color: var(--violet-l) !important; font-family:'Outfit',sans-serif !important; font-weight:600 !important; }}
[data-testid="stDataFrame"] td {{ color: var(--text-s) !important; }}

/* ── ALERTS ── */
[data-testid="stAlert"] {{ background: rgba(124,58,237,0.1) !important; border: 1px solid rgba(167,139,250,0.3) !important; border-left: 3px solid var(--violet) !important; border-radius: var(--r-sm) !important; }}

/* ── CORR CARD ── */
.corr-card {{
  background: var(--bg); backdrop-filter: var(--blur-sm);
  border: 1px solid var(--border); border-left: 3px solid var(--violet);
  border-radius: var(--r-sm); padding:1rem 1.2rem; text-align:center;
  box-shadow: var(--shadow-sm); min-width:160px; transition: all 0.22s;
}}
.corr-card:hover {{ box-shadow: var(--shadow), var(--glow); border-color: var(--border-h); }}

/* ── BAR CHART ── */
.stat-bar-wrap {{ margin-bottom: 0.6rem; animation: fadeUp 0.4s ease both; }}
.stat-bar-label {{ display:flex; justify-content:space-between; margin-bottom:3px; font-size:0.8rem; font-family:'Outfit',sans-serif; }}
.stat-bar-track {{ height:10px; background:rgba(255,255,255,0.07); border-radius:5px; overflow:hidden; }}
.stat-bar-fill {{ height:100%; border-radius:5px; animation: bar-grow 1s cubic-bezier(.34,1.2,.64,1) both; animation-delay: var(--delay, 0s); }}

/* ── BADGES ── */
.badge {{
  display:inline-block; padding:0.18rem 0.65rem; border-radius:20px;
  font-size:0.72rem; font-family:'Outfit',sans-serif; font-weight:600;
  letter-spacing:0.03em; border:1px solid; margin:2px; white-space:nowrap;
}}
.b-safe     {{ background:rgba(20,184,166,0.15); color:#5eead4; border-color:rgba(20,184,166,0.35); }}
.b-vuln     {{ background:rgba(245,158,11,0.15); color:#fcd34d; border-color:rgba(245,158,11,0.35); }}
.b-danger   {{ background:rgba(249,115,22,0.15); color:#fdba74; border-color:rgba(249,115,22,0.35); }}
.b-critical {{ background:rgba(239,68,68,0.15);  color:#fca5a5; border-color:rgba(239,68,68,0.35); }}
.b-dialect  {{ background:rgba(56,189,248,0.15); color:#7dd3fc; border-color:rgba(56,189,248,0.35); }}

/* ── CHIP ── */
.chip {{
  display:inline-block; background:rgba(255,255,255,0.07); border:1px solid rgba(167,139,250,0.2);
  border-radius:20px; padding:0.12rem 0.55rem; font-size:0.78rem;
  font-family:'Outfit',sans-serif; color:var(--text-s); margin:2px; white-space:nowrap;
}}

/* ── SCROLLBAR ── */
::-webkit-scrollbar {{ width:5px; }}
::-webkit-scrollbar-track {{ background: rgba(255,255,255,0.03); }}
::-webkit-scrollbar-thumb {{ background: rgba(124,58,237,0.4); border-radius:3px; }}
::-webkit-scrollbar-thumb:hover {{ background: var(--violet); }}

/* ── PAGE ── */
@keyframes slideIn {{ from {{ opacity:0; transform:translateX(30px); }} to {{ opacity:1; transform:translateX(0); }} }}
.page-wrap {{ padding-bottom: 2rem; animation: slideIn 0.3s cubic-bezier(0.25,0.46,0.45,0.94) both; }}

/* ── PROGRESS BAR (jeu) ── */
[data-testid="stProgress"] > div > div {{
  background: rgba(34,211,238,0.15) !important;
  border-radius: 8px !important;
  height: 8px !important;
}}
[data-testid="stProgress"] > div > div > div {{
  background: linear-gradient(90deg, #22d3ee, #7c3aed) !important;
  border-radius: 8px !important;
  box-shadow: 0 0 12px rgba(34,211,238,0.5) !important;
}}
[data-testid="stProgress"] p {{
  font-family: 'Outfit', sans-serif !important;
  font-size: 0.7rem !important;
  color: #4a3870 !important;
  letter-spacing: 0.04em !important;
}}

/* ── FOLIUM MAP CONTAINER ── */
iframe[title="st_folium.st_folium"] {{
  border-radius: 16px !important;
  border: 2px solid rgba(34,211,238,0.3) !important;
  box-shadow: 0 8px 32px rgba(0,0,0,0.4), 0 0 20px rgba(34,211,238,0.15) !important;
}}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# DONNÉES
# liste construite à la main à partir de Glottolog, Ethnologue et Wikipedia
# j'ai ajouté les dialectes arabes et occitans parce que c'est le sujet du mémoire
# ══════════════════════════════════════════════
LANGUES_RAW = [
    ("Mandarin standard",   "Sino-tibétaine",    "langue",  920,  35.0,  105.0, "Chine",           "Asie de l'Est",   "safe",    True,  "Sinogrammes",  "Langue la plus parlée au monde (L1+L2)"),
    ("Espagnol",            "Indo-européenne",   "langue",  475,  40.4,   -3.7, "Espagne",          "Europe",          "safe",    True,  "Latin",        "Officielle dans 21 pays"),
    ("Anglais",             "Indo-européenne",   "langue",  373,  51.5,   -0.1, "Royaume-Uni",      "Europe",          "safe",    True,  "Latin",        "Lingua franca mondiale"),
    ("Hindi",               "Indo-européenne",   "langue",  344,  28.6,   77.2, "Inde",             "Asie du Sud",     "safe",    True,  "Devanagari",   "Co-officielle avec l'anglais"),
    ("Bengali",             "Indo-européenne",   "langue",  234,  23.7,   90.4, "Bangladesh",       "Asie du Sud",     "safe",    True,  "Bengali",      "7ème langue par nombre de locuteurs"),
    ("Portugais",           "Indo-européenne",   "langue",  232,  38.7,   -9.1, "Portugal",         "Europe",          "safe",    True,  "Latin",        "Parlé sur 4 continents"),
    ("Russe",               "Indo-européenne",   "langue",  154,  55.7,   37.6, "Russie",           "Europe",          "safe",    True,  "Cyrillique",   "Langue slave la plus parlée"),
    ("Japonais",            "Japonique",         "langue",  125,  35.7,  139.7, "Japon",            "Asie de l'Est",   "safe",    True,  "Mixte",        "3 systèmes d'écriture coexistants"),
    ("Arabe standard",      "Afro-asiatique",    "langue",   70,  24.7,   46.7, "Arabie Saoudite",  "Moyen-Orient",    "safe",    True,  "Arabe",        "Officielle dans 22 pays"),
    ("Coréen",              "Koreanique",        "langue",   77,  37.6,  127.0, "Corée du Sud",     "Asie de l'Est",   "safe",    True,  "Hangul",       "Hangul inventé en 1443 par Sejong"),
    ("Français",            "Indo-européenne",   "langue",   80,  48.9,    2.3, "France",           "Europe",          "safe",    True,  "Latin",        "Officiel dans 29 pays, 5 continents"),
    ("Allemand",            "Indo-européenne",   "langue",   76,  52.5,   13.4, "Allemagne",        "Europe",          "safe",    True,  "Latin",        "Langue la plus parlée en UE"),
    ("Swahili",             "Niger-Congo",       "langue",   71,  -6.2,   35.7, "Tanzanie",         "Afrique",         "safe",    True,  "Latin",        "Lingua franca de l'Afrique de l'Est"),
    ("Ukrainien",           "Indo-européenne",   "langue",   40,  50.4,   30.5, "Ukraine",          "Europe",          "safe",    True,  "Cyrillique",   "Langue slave orientale"),
    ("Polonais",            "Indo-européenne",   "langue",   45,  52.2,   21.0, "Pologne",          "Europe",          "safe",    True,  "Latin",        "7 cas grammaticaux"),
    ("Persan (Farsi)",      "Indo-européenne",   "langue",   70,  35.7,   51.4, "Iran",             "Moyen-Orient",    "safe",    True,  "Arabe-Persan", "Langue de Rumi et Hafez"),
    ("Ourdou",              "Indo-européenne",   "langue",   70,  33.7,   73.1, "Pakistan",         "Asie du Sud",     "safe",    True,  "Nastaliq",     "Mutuellement intelligible avec le hindi"),
    ("Indonésien (Bahasa)", "Austronésienne",    "langue",  199,  -6.2,  106.8, "Indonésie",        "Asie du SE",      "safe",    True,  "Latin",        "Lingua franca de 270 M de personnes"),
    ("Thaï",                "Kadaï",             "langue",   61,  13.7,  100.5, "Thaïlande",        "Asie du SE",      "safe",    True,  "Thaï",         "5 tons phonémiques"),
    ("Vietnamien",          "Austro-asiatique",  "langue",   77,  21.0,  105.8, "Vietnam",          "Asie du SE",      "safe",    True,  "Latin",        "6 tons, écriture latinisée au XVIIe s."),
    ("Turc",                "Turco-mongole",     "langue",   76,  39.9,   32.9, "Turquie",          "Moyen-Orient",    "safe",    True,  "Latin",        "Langue agglutinante, réforme graphique 1928"),
    ("Cantonais (Yue)",     "Sino-tibétaine",    "dialecte", 84,  23.1,  113.3, "Chine",            "Asie de l'Est",   "safe",    False, "Sinogrammes",  "Dialecte de Hong Kong et Guangdong"),
    ("Wu (Shanghainien)",   "Sino-tibétaine",    "dialecte", 74,  31.2,  121.5, "Chine",            "Asie de l'Est",   "safe",    False, "Sinogrammes",  "Famille de dialectes sino-tibétains"),
    ("Minnan (Hokkien)",    "Sino-tibétaine",    "dialecte", 46,  24.4,  118.1, "Chine",            "Asie de l'Est",   "safe",    False, "Sinogrammes",  "Dialecte du Fujian, Taïwan, diaspora mondiale"),
    ("Hakka",               "Sino-tibétaine",    "dialecte", 44,  24.8,  116.1, "Chine",            "Asie de l'Est",   "safe",    False, "Sinogrammes",  "Communauté diasporique très active"),
    ("Darija (Algérie)",    "Afro-asiatique",    "dialecte", 35,  36.7,    3.1, "Algérie",          "Afrique du N.",   "safe",    False, "Arabe/Latin",  "Mélange d'arabe, berbère, français et espagnol"),
    ("Darija (Maroc)",      "Afro-asiatique",    "dialecte", 30,  33.9,   -6.9, "Maroc",            "Afrique du N.",   "safe",    False, "Arabe/Latin",  "~50 % de lexique berbère et français"),
    ("Darija (Tunisie)",    "Afro-asiatique",    "dialecte", 11,  36.8,   10.2, "Tunisie",          "Afrique du N.",   "safe",    False, "Arabe/Latin",  "Forte influence italienne et française"),
    ("Égyptien (Masri)",    "Afro-asiatique",    "dialecte", 68,  30.0,   31.2, "Égypte",           "Moyen-Orient",    "safe",    False, "Arabe",        "Dialecte le plus compris grâce au cinéma"),
    ("Levantin",            "Afro-asiatique",    "dialecte", 35,  33.9,   35.5, "Liban/Syrie",      "Moyen-Orient",    "safe",    False, "Arabe",        "Liban, Syrie, Palestine, Jordanie"),
    ("Golfe (Khaliji)",     "Afro-asiatique",    "dialecte", 15,  24.5,   54.4, "Émirats",          "Moyen-Orient",    "safe",    False, "Arabe",        "Dialecte du Golfe Persique"),
    ("Hassaniya",           "Afro-asiatique",    "dialecte",  3,  20.0,  -10.0, "Mauritanie",       "Afrique",         "vulnerable", True, "Arabe",       "Dialecte arabe du Sahara occidental"),
    ("Tamazight kabyle",    "Afro-asiatique",    "dialecte",  5,  36.7,    4.0, "Algérie",          "Afrique du N.",   "safe",    True,  "Tifinagh/Latin","Principale variété berbère d'Algérie"),
    ("Tachelhit (Maroc)",   "Afro-asiatique",    "dialecte",  8,  30.9,   -8.0, "Maroc",            "Afrique du N.",   "safe",    True,  "Tifinagh/Latin","Berbère du sud marocain"),
    ("Tarifit (Rif)",       "Afro-asiatique",    "dialecte",  4,  35.2,   -4.0, "Maroc",            "Afrique du N.",   "vulnerable", False,"Tifinagh",    "Berbère du nord du Maroc"),
    ("Tamahaq (Touareg)",   "Afro-asiatique",    "dialecte",  1,  20.0,    5.0, "Niger/Mali",       "Afrique",         "vulnerable", False,"Tifinagh",    "Langue des Touaregs du Sahara"),
    ("Hausa",               "Afro-asiatique",    "langue",   63,  12.0,    8.5, "Nigeria",          "Afrique",         "safe",    True,  "Latin/Ajami",  "Lingua franca d'Afrique de l'Ouest"),
    ("Amharique",           "Afro-asiatique",    "langue",   32,   9.0,   38.7, "Éthiopie",         "Afrique",         "safe",    True,  "Guèze",        "Écriture syllabique guèze"),
    ("Yoruba",              "Niger-Congo",       "langue",   43,   7.4,    3.9, "Nigeria",          "Afrique",         "safe",    False, "Latin",        "3 tons, riche tradition orale"),
    ("Igbo",                "Niger-Congo",       "langue",   27,   6.4,    7.5, "Nigeria",          "Afrique",         "safe",    False, "Latin",        "Delta du Niger"),
    ("Zulu",                "Niger-Congo",       "langue",   13, -29.0,   31.0, "Afrique du Sud",   "Afrique",         "safe",    True,  "Latin",        "Clicks phonémiques bantoues"),
    ("Wolof",               "Niger-Congo",       "langue",   12,  14.7,  -17.4, "Sénégal",          "Afrique",         "safe",    False, "Latin/Arabe",  "Lingua franca au Sénégal"),
    ("Lingala",             "Niger-Congo",       "langue",   15,  -4.3,   15.3, "Congo",            "Afrique",         "safe",    False, "Latin",        "Lingua franca de la RDC et Congo-Brazza"),
    ("Somali",              "Afro-asiatique",    "langue",   21,   2.0,   45.3, "Somalie",          "Afrique",         "safe",    True,  "Latin",        "Langue couchitique de la Corne de l'Afrique"),
    ("Tigrigna",            "Afro-asiatique",    "dialecte",  7,  15.3,   38.9, "Érythrée",         "Afrique",         "safe",    True,  "Guèze",        "Langue sémitique d'Érythrée"),
    ("Grec",                "Indo-européenne",   "langue",   13,  37.9,   23.7, "Grèce",            "Europe",          "safe",    True,  "Grec",         "Plus de 3 000 ans d'histoire écrite"),
    ("Hébreu moderne",      "Afro-asiatique",    "langue",    9,  31.8,   35.2, "Israël",           "Moyen-Orient",    "safe",    True,  "Hébreu",       "Seule langue morte ressuscitée avec succès"),
    ("Néerlandais",         "Indo-européenne",   "langue",   24,  52.4,    4.9, "Pays-Bas",         "Europe",          "safe",    True,  "Latin",        "Langue germanique occidentale"),
    ("Flamand",             "Indo-européenne",   "dialecte",  6,  51.0,    4.0, "Belgique",         "Europe",          "safe",    True,  "Latin",        "Variété néerlandaise de Belgique"),
    ("Catalan",             "Indo-européenne",   "langue",    9,  41.4,    2.2, "Espagne",          "Europe",          "safe",    True,  "Latin",        "10 M de locuteurs, langue romane"),
    ("Gallois",             "Indo-européenne",   "langue",  0.88, 52.1,   -3.8, "Pays de Galles",   "Europe",          "safe",    True,  "Latin",        "Revitalisé grâce aux politiques linguistiques"),
    ("Basque",              "Isolat",            "langue",  0.75, 43.3,   -1.9, "Espagne/France",   "Europe",          "safe",    True,  "Latin",        "Langue sans famille connue"),
    ("Gaélique irlandais",  "Indo-européenne",   "langue",   1.8, 53.3,   -7.8, "Irlande",          "Europe",          "vulnerable", True,"Latin",       "1ère langue officielle d'Irlande"),
    ("Gaélique écossais",   "Indo-européenne",   "langue", 0.057, 57.5,   -4.5, "Royaume-Uni",      "Europe",          "endangered", False,"Latin",      "57 000 locuteurs"),
    ("Breton",              "Indo-européenne",   "langue",  0.21, 48.2,   -2.9, "France",           "Europe",          "vulnerable", False,"Latin",      "Langue celtique de Bretagne"),
    ("Cornique",            "Indo-européenne",   "langue", 0.003, 50.1,   -5.3, "Royaume-Uni",      "Europe",          "endangered", False,"Latin",      "Ressuscité depuis 1900"),
    ("Islandais",           "Indo-européenne",   "langue",  0.37, 64.1,  -21.9, "Islande",          "Europe",          "safe",    True,  "Latin",        "Très proche du vieux norrois"),
    ("Maltais",             "Afro-asiatique",    "langue",  0.52, 35.9,   14.5, "Malte",            "Europe",          "safe",    True,  "Latin",        "Seule langue sémitique officielle en UE"),
    ("Finnois",             "Ouralienne",        "langue",   5.0, 60.2,   25.0, "Finlande",         "Europe",          "safe",    True,  "Latin",        "15 cas grammaticaux"),
    ("Hongrois",            "Ouralienne",        "langue",   13,  47.5,   19.0, "Hongrie",          "Europe",          "safe",    True,  "Latin",        "18 cas grammaticaux"),
    ("Géorgien",            "Kartvélienne",      "langue",   3.7, 41.7,   44.8, "Géorgie",          "Europe",          "safe",    True,  "Mkhédrouri",   "Alphabet unique créé au Ve siècle"),
    ("Arménien",            "Indo-européenne",   "langue",   6.7, 40.2,   44.5, "Arménie",          "Europe",          "safe",    True,  "Arménien",     "Branche propre de l'indo-européen"),
    ("Romani",              "Indo-européenne",   "dialecte", 3.5, 45.0,   20.0, "Europe centrale",  "Europe",          "vulnerable", False,"Latin",      "Forte variation dialectale"),
    ("Yiddish",             "Indo-européenne",   "langue",   1.5, 52.0,   19.0, "Diaspore",         "Europe",          "endangered", False,"Hébreu",     "Langue des communautés ashkénazes"),
    ("Ladino",              "Indo-européenne",   "langue",  0.06, 41.0,   29.0, "Turquie",          "Europe",          "critically_endangered", False,"Latin/Hébreu","Espagnol médiéval des Séfarades"),
    ("Sami du Nord",        "Ouralienne",        "langue", 0.025, 69.0,   26.0, "Norvège",          "Europe",          "endangered", False,"Latin",      "Langue des Samis de Scandinavie"),
    ("Occitan",             "Indo-européenne",   "langue",   0.5, 43.6,    3.9, "France",           "Occitanie",       "vulnerable", False,"Latin",      "Langue d'oc, 6 dialectes, parlée du Moyen Age au XIXe s."),
    ("Languedocien",        "Indo-européenne",   "dialecte", 0.15,43.6,    3.9, "France",           "Occitanie",       "vulnerable", False,"Latin",      "Dialecte occitan central, historiquement parlé à Montpellier"),
    ("Gascon",              "Indo-européenne",   "dialecte", 0.15,43.9,   -0.6, "France",           "Occitanie",       "vulnerable", False,"Latin",      "Dialecte gallo-roman, inclut le béarnais"),
    ("Provençal",           "Indo-européenne",   "dialecte", 0.12,43.8,    4.6, "France",           "Occitanie",       "vulnerable", False,"Latin",      "Langue de Frédéric Mistral, Prix Nobel 1904"),
    ("Nissard",             "Indo-européenne",   "dialecte", 0.03,43.7,    7.3, "France",           "Occitanie",       "endangered", False,"Latin",      "Dialecte occitan niçois"),
    ("Aranese",             "Indo-européenne",   "dialecte",0.004,42.7,    0.9, "Espagne (Aran)",   "Occitanie",       "vulnerable", True, "Latin",      "Gascon officiel en Val d'Aran"),
    ("Catalan nord (Roussillon)","Indo-européenne","dialecte",0.17,42.7,   2.9, "France",           "Occitanie",       "vulnerable", False,"Latin",      "Catalan de Catalogne du Nord, à 80 km de Montpellier"),
    ("Tibétain",            "Sino-tibétaine",    "langue",   1.2, 29.6,   91.1, "Chine",            "Asie du Sud",     "vulnerable", False,"Tibétain",   "Langue du plateau tibétain"),
    ("Ouïghour",            "Turco-mongole",     "langue",   10,  43.8,   87.6, "Chine",            "Asie centrale",   "endangered", False,"Arabe-Ouïg.","Langue turcique du Xinjiang"),
    ("Kazakh",              "Turco-mongole",     "langue",   13,  51.2,   71.4, "Kazakhstan",       "Asie centrale",   "safe",    True,  "Latin",        "Passage au latin en 2020"),
    ("Mongol",              "Turco-mongole",     "langue",    6,  47.9,  106.9, "Mongolie",         "Asie de l'Est",   "safe",    True,  "Cyrillique",   "Écriture verticale traditionnelle"),
    ("Tamoul",              "Dravidienne",       "langue",   78,  11.1,   79.0, "Inde",             "Asie du Sud",     "safe",    True,  "Tamoul",       "Langue classique, +2000 ans"),
    ("Télougou",            "Dravidienne",       "langue",   83,  17.4,   78.5, "Inde",             "Asie du Sud",     "safe",    True,  "Télougou",     "Officielle d'Andhra Pradesh"),
    ("Kannada",             "Dravidienne",       "langue",   44,  15.3,   75.7, "Inde",             "Asie du Sud",     "safe",    True,  "Kannada",      "Officielle du Karnataka"),
    ("Maori",               "Austronésienne",    "langue", 0.185,-40.9,  174.9, "Nouvelle-Zélande", "Océanie",         "vulnerable", True,"Latin",       "Revitalisé via kura kaupapa"),
    ("Hawaïen",             "Austronésienne",    "langue", 0.024, 21.3, -157.8, "États-Unis",       "Océanie",         "endangered", True,"Latin",       "Revitalisé grâce aux écoles Punana Leo"),
    ("Tahitien",            "Austronésienne",    "langue", 0.068,-17.5, -149.6, "France",           "Océanie",         "vulnerable", True,"Latin",       "Langue officielle de Polynésie française"),
    ("Nahuatl",             "Uto-aztèque",       "langue",   1.7, 19.4,  -99.1, "Mexique",          "Amériques",       "vulnerable", False,"Latin",      "Langue des Aztèques"),
    ("Quechua",             "Quechuan",          "langue",    8, -13.5,  -72.0, "Pérou",            "Amériques",       "vulnerable", True,"Latin",       "Langue de l'Empire Inca"),
    ("Guaraní",             "Tupian",            "langue",    6, -25.3,  -57.6, "Paraguay",         "Amériques",       "safe",    True,  "Latin",        "Co-officielle au Paraguay"),
    ("Navajo",              "Na-Déné",           "langue",  0.17, 36.1, -108.7, "États-Unis",       "Amériques",       "vulnerable", False,"Latin",      "Code talkers de la WWII"),
    ("Cherokee",            "Iroquoienne",       "langue", 0.002, 35.5,  -83.3, "États-Unis",       "Amériques",       "critically_endangered", False,"Syllabaire","Syllabaire inventé par Sequoyah en 1821"),
    ("Inuktitut",           "Esquimau-aléoute",  "langue",  0.04, 63.7,  -68.5, "Canada",           "Amériques",       "vulnerable", True,"Syllabique",  "Officielle au Nunavut"),
    ("Aymara",              "Aymaran",           "langue",    2, -16.5,  -68.2, "Bolivie",          "Amériques",       "vulnerable", True,"Latin",       "Autour du lac Titicaca"),
    ("Aïnou",               "Isolat",            "langue", 0.002, 43.1,  141.4, "Japon",            "Asie de l'Est",   "critically_endangered", False,"Latin","Sans famille connue, Hokkaido"),
    ("Abkhaze",             "Caucasique du N.",  "langue",  0.19, 43.0,   41.0, "Abkhazie",         "Europe",          "vulnerable", True,"Cyrillique",  "65 consonnes"),
    ("Tchétchène",          "Caucasique du N.",  "langue",   1.4, 43.3,   45.7, "Russie",           "Europe",          "vulnerable", False,"Cyrillique", "Langue nakh-daghestanienne"),
    ("Shona",               "Niger-Congo",       "langue",   15,  -18.0,  31.0, "Zimbabwe",         "Afrique",         "safe",    True,  "Latin",        "Langue bantoue du Zimbabwe"),
    ("Xhosa",               "Niger-Congo",       "langue",    8,  -32.0,  27.0, "Afrique du Sud",   "Afrique",         "safe",    True,  "Latin",        "Clicks consonantiques, Nelson Mandela"),
    ("Kinyarwanda",         "Niger-Congo",       "langue",   12,  -1.9,   29.9, "Rwanda",           "Afrique",         "safe",    True,  "Latin",        "Langue nationale du Rwanda"),
    ("Kirundi",             "Niger-Congo",       "langue",    9,  -3.4,   29.9, "Burundi",          "Afrique",         "safe",    True,  "Latin",        "Dialecte proche du kinyarwanda"),
    ("Luganda",             "Niger-Congo",       "langue",    5,   0.3,   32.6, "Ouganda",          "Afrique",         "safe",    False, "Latin",        "Langue bantoue d'Ouganda"),
    ("Dioula",              "Niger-Congo",       "langue",   12,  12.3,   -8.0, "Côte d'Ivoire",    "Afrique",         "safe",    False, "Latin",        "Langue de commerce mandé"),
    ("Peul (Fulfulde)",     "Niger-Congo",       "langue",   40,  11.0,   -3.0, "Sahel",            "Afrique",         "safe",    False, "Latin/Arabe",  "Couvre 20 pays du Sahel"),
    ("Bambara",             "Niger-Congo",       "langue",   14,  12.7,   -8.0, "Mali",             "Afrique",         "safe",    False, "Latin",        "Langue véhiculaire du Mali"),
    ("Twi",                 "Niger-Congo",       "langue",    9,   6.7,   -1.6, "Ghana",            "Afrique",         "safe",    False, "Latin",        "Famille akan, Ghana"),
    ("Oromo",               "Afro-asiatique",    "langue",   40,   8.0,   38.0, "Éthiopie",         "Afrique",         "safe",    True,  "Latin",        "Langue couchitique la plus parlée"),
    ("Sidamo",              "Afro-asiatique",    "langue",    4,   6.8,   38.4, "Éthiopie",         "Afrique",         "vulnerable", False,"Latin",      "Langue omotique d'Éthiopie"),
    ("Afrikaans",           "Indo-européenne",   "langue",    7, -30.0,   25.0, "Afrique du Sud",   "Afrique",         "safe",    True,  "Latin",        "Créole du néerlandais, 17e siècle"),
    ("Malagasy",            "Austronésienne",    "langue",   25, -19.0,   46.0, "Madagascar",       "Afrique",         "safe",    True,  "Latin",        "Seule langue austronésienne d'Afrique"),
    ("Tsonga",              "Niger-Congo",       "langue",    3, -24.0,   32.0, "Mozambique",       "Afrique",         "safe",    True,  "Latin",        "Langue bantoue du sud-est"),
    ("Setswana",            "Niger-Congo",       "langue",    5, -22.0,   24.0, "Botswana",         "Afrique",         "safe",    True,  "Latin",        "Langue officielle du Botswana"),
    ("Sesotho",             "Niger-Congo",       "langue",    5, -29.3,   27.5, "Lesotho",          "Afrique",         "safe",    True,  "Latin",        "Langue du Lesotho et d'Afrique du Sud"),
    ("Amazigh (Maroc)",     "Afro-asiatique",    "langue",    8,  31.0,   -5.0, "Maroc",            "Afrique du N.",   "vulnerable", True,"Tifinagh",    "Officielle au Maroc depuis 2011"),
    ("Tigré",               "Afro-asiatique",    "dialecte",  1,  16.0,   38.0, "Érythrée",         "Afrique",         "vulnerable", False,"Guèze",      "Langue sémitique nord-éthiopienne"),
    ("Nuer",                "Nilo-saharienne",   "langue",    2,   7.5,   31.0, "Soudan du Sud",    "Afrique",         "vulnerable", False,"Latin",      "Langue nilotique du Nil"),
    ("Dinka",               "Nilo-saharienne",   "langue",    4,   8.0,   30.0, "Soudan du Sud",    "Afrique",         "vulnerable", False,"Latin",      "Langue la plus parlée au Soudan du Sud"),
    ("Zarma",               "Nilo-saharienne",   "langue",    5,  13.5,    2.0, "Niger",            "Afrique",         "safe",    False, "Latin",        "Langue songhaï du Niger"),
    ("Kanuri",              "Nilo-saharienne",   "langue",    4,  13.0,   13.0, "Nigeria/Niger",    "Afrique",         "vulnerable", False,"Latin/Arabe", "Ancien empire du Kanem-Bornou"),
    ("Kikuyu",              "Niger-Congo",       "langue",    8,  -1.0,   37.0, "Kenya",            "Afrique",         "safe",    False, "Latin",        "Langue bantoue la plus parlée au Kenya"),
    ("Luo",                 "Nilo-saharienne",   "langue",    4,  -0.5,   34.5, "Kenya",            "Afrique",         "safe",    False, "Latin",        "Langue nilotique du Kenya"),
    ("Chichewa",            "Niger-Congo",       "langue",   12, -13.0,   34.0, "Malawi",           "Afrique",         "safe",    True,  "Latin",        "Langue nationale du Malawi"),
    ("Ndebele",             "Niger-Congo",       "langue",    2, -20.0,   29.0, "Zimbabwe",         "Afrique",         "safe",    True,  "Latin",        "Langue nguni du Zimbabwe"),
    ("Marathi",             "Indo-européenne",   "langue",   83,  19.0,   76.0, "Inde",             "Asie du Sud",     "safe",    True,  "Devanagari",   "Officielle du Maharashtra"),
    ("Gujarati",            "Indo-européenne",   "langue",   56,  23.0,   72.0, "Inde",             "Asie du Sud",     "safe",    True,  "Gujarati",     "Langue de Gandhi, diaspora mondiale"),
    ("Punjabi",             "Indo-européenne",   "langue",  125,  31.0,   75.0, "Inde/Pakistan",    "Asie du Sud",     "safe",    True,  "Gurmukhi",     "Langue des Sikhs"),
    ("Malayalam",           "Dravidienne",       "langue",   38,  10.5,   76.5, "Inde",             "Asie du Sud",     "safe",    True,  "Malayalam",    "Kerala, taux d'alphabétisation 96%"),
    ("Odia",                "Indo-européenne",   "langue",   33,  20.0,   84.0, "Inde",             "Asie du Sud",     "safe",    True,  "Odia",         "Une des 6 langues classiques de l'Inde"),
    ("Assamese",            "Indo-européenne",   "langue",   23,  26.0,   92.0, "Inde",             "Asie du Sud",     "safe",    True,  "Bengalais",    "Langue d'Assam, nord-est de l'Inde"),
    ("Maithili",            "Indo-européenne",   "langue",   34,  26.5,   86.0, "Inde/Népal",       "Asie du Sud",     "vulnerable", False,"Devanagari",  "Reconnue comme langue officielle en 2003"),
    ("Népalais",            "Indo-européenne",   "langue",   16,  28.0,   84.0, "Népal",            "Asie du Sud",     "safe",    True,  "Devanagari",   "Langue nationale du Népal"),
    ("Cingalais",           "Indo-européenne",   "langue",   17,   7.0,   81.0, "Sri Lanka",        "Asie du Sud",     "safe",    True,  "Cingalais",    "Script spiralé unique"),
    ("Pashto",              "Indo-européenne",   "langue",   60,  34.0,   65.0, "Afghanistan",      "Asie du Sud",     "safe",    True,  "Arabe-Persan", "Co-officielle en Afghanistan"),
    ("Dari",                "Indo-européenne",   "langue",   28,  34.5,   67.0, "Afghanistan",      "Asie du Sud",     "safe",    True,  "Arabe-Persan", "Farsi afghan, langue administrative"),
    ("Dzongkha",            "Sino-tibétaine",    "langue",  0.17, 27.5,   90.0, "Bhoutan",          "Asie du Sud",     "safe",    True,  "Tibétain",     "Langue nationale du Bhoutan"),
    ("Birman",              "Sino-tibétaine",    "langue",   33,  19.7,   96.1, "Myanmar",          "Asie du SE",      "safe",    True,  "Birman",       "Script circulaire bouddhiste"),
    ("Khmer",               "Austro-asiatique",  "langue",   16,  12.5,  105.0, "Cambodge",         "Asie du SE",      "safe",    True,  "Khmer",        "Plus vieux alphabet d'Asie du SE"),
    ("Lao",                 "Kadaï",             "langue",    7,  18.0,  103.0, "Laos",             "Asie du SE",      "safe",    True,  "Lao",          "Étroitement apparenté au thaï"),
    ("Filipino (Tagalog)",  "Austronésienne",    "langue",   90,  14.6,  121.0, "Philippines",      "Asie du SE",      "safe",    True,  "Latin",        "Basé sur le tagalog de Manille"),
    ("Cebuano",             "Austronésienne",    "dialecte", 21,  10.3,  123.9, "Philippines",      "Asie du SE",      "safe",    False, "Latin",        "2e langue des Philippines"),
    ("Javanais",            "Austronésienne",    "dialecte", 98,  -7.5,  110.0, "Indonésie",        "Asie du SE",      "safe",    False, "Latin",        "Langue la plus parlée d'Indonésie"),
    ("Soundanais",          "Austronésienne",    "dialecte", 40,  -7.0,  107.0, "Indonésie",        "Asie du SE",      "safe",    False, "Latin",        "Java occidental"),
    ("Minangkabau",         "Austronésienne",    "dialecte", 10,  -0.9,  100.4, "Indonésie",        "Asie du SE",      "safe",    False, "Latin",        "Société matrilinéaire de Sumatra"),
    ("Balinais",            "Austronésienne",    "dialecte",  3,  -8.4,  115.0, "Indonésie",        "Asie du SE",      "vulnerable", False,"Balinais",   "Script balinais millénaire"),
    ("Malais",              "Austronésienne",    "langue",   33,   3.0,  110.0, "Malaisie",         "Asie du SE",      "safe",    True,  "Latin/Jawi",   "Base de l'indonésien"),
    ("Tétum",               "Austronésienne",    "langue",   0.8,  -8.9,  125.6, "Timor oriental",  "Asie du SE",      "vulnerable", True,"Latin",       "Co-officielle au Timor oriental"),
    ("Fidjien",             "Austronésienne",    "langue",   0.3, -18.0,  178.0, "Fidji",            "Océanie",         "vulnerable", True,"Latin",       "Langue mélanésienne des Fidji"),
    ("Samoan",              "Austronésienne",    "langue",   0.5, -13.7, -172.0, "Samoa",            "Océanie",         "safe",    True,  "Latin",        "Langue polynésienne du Pacifique"),
    ("Tongien",             "Austronésienne",    "langue",  0.09, -21.1, -175.2, "Tonga",            "Océanie",         "safe",    True,  "Latin",        "Unique monarchie du Pacifique"),
    ("Azerbaïdjanais",      "Turco-mongole",     "langue",   32,  40.4,   49.9, "Azerbaïdjan",      "Asie centrale",   "safe",    True,  "Latin",        "Passage au latin en 1991"),
    ("Ouzbek",              "Turco-mongole",     "langue",   44,  41.3,   64.4, "Ouzbékistan",      "Asie centrale",   "safe",    True,  "Latin",        "Langue de Samarcande"),
    ("Turkmène",            "Turco-mongole",     "langue",    8,  38.0,   58.0, "Turkménistan",     "Asie centrale",   "safe",    True,  "Latin",        "Passage au latin en 1993"),
    ("Kirghiz",             "Turco-mongole",     "langue",    5,  41.2,   74.8, "Kirghizistan",     "Asie centrale",   "safe",    True,  "Cyrillique",   "Épopée de Manas, 500 000 vers"),
    ("Tadjik",              "Indo-européenne",   "langue",    8,  38.6,   68.8, "Tadjikistan",      "Asie centrale",   "safe",    True,  "Cyrillique",   "Dialecte persan, en cyrillique"),
    ("Kurde (Kurmandji)",   "Indo-européenne",   "langue",   20,  37.0,   43.0, "Turquie/Irak",     "Moyen-Orient",    "vulnerable", False,"Latin/Arabe", "Langue indo-iranienne sans état"),
    ("Kurde (Sorani)",      "Indo-européenne",   "dialecte",  7,  36.2,   44.0, "Irak/Iran",        "Moyen-Orient",    "vulnerable", True,"Arabe",       "Officiel en région kurdistanaise d'Irak"),
    ("Syriaque",            "Afro-asiatique",    "langue",  0.45, 37.0,   42.0, "Irak/Syrie",       "Moyen-Orient",    "endangered", False,"Syriaque",   "Aramée, langue du Christ"),
    ("Araméen moderne",     "Afro-asiatique",    "dialecte",0.23, 37.5,   43.0, "Irak",             "Moyen-Orient",    "critically_endangered", False,"Syriaque","Survirait dans quelques villages"),
    ("Pachto méridional",   "Indo-européenne",   "dialecte", 10,  31.6,   65.7, "Pakistan",         "Asie du Sud",     "safe",    False, "Arabe-Persan", "Dialecte du sud de l'Afghanistan"),
    ("Baloutchi",           "Indo-européenne",   "langue",    9,  27.0,   63.0, "Pakistan/Iran",    "Asie du Sud",     "vulnerable", False,"Arabe-Persan","Langue des Baloutches"),
    ("Sindhi",              "Indo-européenne",   "langue",   33,  25.0,   68.0, "Pakistan",         "Asie du Sud",     "safe",    True,  "Arabe-Sindhi", "Civilisation de l'Indus"),
    ("Néwar",               "Sino-tibétaine",    "langue",  0.85, 27.7,   85.3, "Népal",            "Asie du Sud",     "vulnerable", False,"Devanagari", "Langue de la vallée de Katmandou"),
    ("Serbe",               "Indo-européenne",   "langue",   12,  44.0,   21.0, "Serbie",           "Europe",          "safe",    True,  "Cyrillique",   "Bicéphalique : latin et cyrillique"),
    ("Croate",              "Indo-européenne",   "langue",    7,  45.8,   16.0, "Croatie",          "Europe",          "safe",    True,  "Latin",        "Mutuellement intelligible avec le serbe"),
    ("Slovène",             "Indo-européenne",   "langue",   2.5, 46.0,   14.5, "Slovénie",         "Europe",          "safe",    True,  "Latin",        "Langue slave méridionale"),
    ("Bulgare",             "Indo-européenne",   "langue",    9,  42.7,   25.5, "Bulgarie",         "Europe",          "safe",    True,  "Cyrillique",   "Père du cyrillique moderne"),
    ("Macédonien",          "Indo-européenne",   "langue",   1.4, 41.6,   21.7, "Macédoine du N.",  "Europe",          "safe",    True,  "Cyrillique",   "Standardisé en 1944"),
    ("Roumain",             "Indo-européenne",   "langue",   26,  45.9,   24.9, "Roumanie",         "Europe",          "safe",    True,  "Latin",        "Seule langue latine de l'Est"),
    ("Tchèque",             "Indo-européenne",   "langue",   10,  50.1,   14.4, "Tchéquie",         "Europe",          "safe",    True,  "Latin",        "Diacritiques créés par Jan Hus"),
    ("Slovaque",            "Indo-européenne",   "langue",    5,  48.7,   19.7, "Slovaquie",        "Europe",          "safe",    True,  "Latin",        "Très proche du tchèque"),
    ("Lituanien",           "Indo-européenne",   "langue",    3,  55.2,   24.0, "Lituanie",         "Europe",          "safe",    True,  "Latin",        "Langue la plus archaïque en vie"),
    ("Letton",              "Indo-européenne",   "langue",   1.5, 56.9,   24.1, "Lettonie",         "Europe",          "safe",    True,  "Latin",        "Proche du lituanien"),
    ("Estonien",            "Ouralienne",        "langue",   1.1, 59.4,   24.7, "Estonie",          "Europe",          "safe",    True,  "Latin",        "Proche du finnois"),
    ("Albanais",            "Indo-européenne",   "langue",    8,  41.3,   20.0, "Albanie",          "Europe",          "safe",    True,  "Latin",        "Branche isolée indo-européenne"),
    ("Biélorusse",          "Indo-européenne",   "langue",   10,  53.9,   27.6, "Biélorussie",      "Europe",          "vulnerable", True,"Cyrillique",  "Coexiste avec le russe"),
    ("Moldave",             "Indo-européenne",   "dialecte",  3,  47.0,   28.9, "Moldavie",         "Europe",          "safe",    True,  "Latin",        "Dialecte du roumain"),
    ("Monténégrin",         "Indo-européenne",   "dialecte", 0.23, 42.8,  19.4, "Monténégro",       "Europe",          "safe",    True,  "Latin/Cyr.",   "Standardisé en 2007"),
    ("Bosnien",             "Indo-européenne",   "dialecte",  2,  44.0,   17.5, "Bosnie",           "Europe",          "safe",    True,  "Latin",        "Mutuellement intelligible serbe-croate"),
    ("Luxembourgeois",      "Indo-européenne",   "langue",  0.38, 49.8,    6.1, "Luxembourg",       "Europe",          "safe",    True,  "Latin",        "Langue mosellane officielle"),
    ("Romanche",            "Indo-européenne",   "langue",  0.04, 46.7,    9.5, "Suisse",           "Europe",          "endangered", True,"Latin",       "4e langue officielle de Suisse"),
    ("Frioulan",            "Indo-européenne",   "dialecte", 0.6, 46.1,   13.2, "Italie",           "Europe",          "vulnerable", False,"Latin",      "Langue rhéto-romane du Frioul"),
    ("Asturien",            "Indo-européenne",   "dialecte", 0.45, 43.4,  -5.9, "Espagne",          "Europe",          "vulnerable", False,"Latin",      "Langue astur-léonaise du Nord"),
    ("Galicien",            "Indo-européenne",   "langue",   2.4, 42.8,   -8.5, "Espagne",          "Europe",          "safe",    True,  "Latin",        "Proche du portugais"),
    ("Sarde",               "Indo-européenne",   "dialecte", 1.2, 40.0,    9.0, "Italie",           "Europe",          "vulnerable", False,"Latin",      "Latin insulaire le plus conservateur"),
    ("Sicilien",            "Indo-européenne",   "dialecte", 4.7, 37.6,   14.0, "Italie",           "Europe",          "vulnerable", False,"Latin",      "Arabe, normand et espagnol mêlés"),
    ("Vénitien",            "Indo-européenne",   "dialecte", 3.8, 45.4,   12.3, "Italie",           "Europe",          "vulnerable", False,"Latin",      "Langue de la Sérénissime République"),
    ("Napolitain",          "Indo-européenne",   "dialecte", 5.7, 40.8,   14.2, "Italie",           "Europe",          "vulnerable", False,"Latin",      "Dialecte italo-roman du Sud"),
    ("Norvégien (Bokmål)",  "Indo-européenne",   "dialecte", 4.5, 59.9,   10.7, "Norvège",          "Europe",          "safe",    True,  "Latin",        "Standard dominant en Norvège"),
    ("Suédois",             "Indo-européenne",   "langue",   10,  59.3,   18.1, "Suède",            "Europe",          "safe",    True,  "Latin",        "Officielle en Suède et Finlande"),
    ("Danois",              "Indo-européenne",   "langue",    6,  55.7,   12.6, "Danemark",         "Europe",          "safe",    True,  "Latin",        "Intelligible avec le norvégien"),
    ("Féroïen",             "Indo-européenne",   "langue",  0.07, 62.0,   -7.0, "Îles Féroé",       "Europe",          "safe",    True,  "Latin",        "Norrois préservé aux Féroé"),
    ("Mapuche",             "Isolat",            "langue",   0.3, -38.7,  -72.4, "Chili",            "Amériques",       "endangered", False,"Latin",      "Seul peuple amérindien non conquis"),
    ("Wayuu",               "Arawak",            "langue",   0.4,  11.5,  -72.5, "Colombie/Vénéz.", "Amériques",       "vulnerable", False,"Latin",      "Langue arawak du Guajiro"),
    ("Mixtec",              "Oto-mangue",        "langue",   0.5,  17.5,  -97.5, "Mexique",          "Amériques",       "vulnerable", False,"Latin",      "Civilization mixtèque précolombienne"),
    ("Zapotèque",           "Oto-mangue",        "dialecte", 0.45, 17.0,  -96.7, "Mexique",          "Amériques",       "vulnerable", False,"Latin",      "Première écriture des Amériques"),
    ("Quiché (K'iche')",    "Maya",              "langue",   1.0,  15.0,  -91.0, "Guatemala",        "Amériques",       "vulnerable", False,"Latin",      "Langue du Popol Vuh maya"),
    ("Mam",                 "Maya",              "langue",   0.5,  15.5,  -91.7, "Guatemala",        "Amériques",       "vulnerable", False,"Latin",      "Langue maya des hautes terres"),
    ("Aymara bolivien",     "Aymaran",           "dialecte", 1.5, -17.0,  -67.0, "Bolivie",          "Amériques",       "vulnerable", True,"Latin",       "Co-officielle en Bolivie"),
    ("Créole haïtien",      "Créole",            "langue",   12,  18.9,  -72.3, "Haïti",            "Amériques",       "safe",    True,  "Latin",        "Créole à base française"),
    ("Papiamento",          "Créole",            "dialecte", 0.33, 12.2,  -69.0, "Aruba/Curaçao",    "Amériques",       "safe",    True,  "Latin",        "Créole ibéro-africain des Antilles"),
    ("Garifuna",            "Arawak",            "langue",   0.17, 15.8,  -88.8, "Honduras",         "Amériques",       "vulnerable", False,"Latin",      "Mélange d'arawak et de caribéen"),
    ("Créole mauricien",    "Créole",            "dialecte", 1.3, -20.3,   57.6, "Maurice",          "Afrique",         "safe",    False, "Latin",        "Créole à base française de l'Océan Indien"),
    ("Créole réunionnais",  "Créole",            "dialecte", 0.6, -21.1,   55.5, "La Réunion",       "Afrique",         "safe",    False, "Latin",        "Créole bourbonnais"),
    ("Seychellois",         "Créole",            "dialecte", 0.08, -4.6,   55.5, "Seychelles",       "Afrique",         "safe",    True,  "Latin",        "Créole seselwa, officiel aux Seychelles"),
    ("Tok Pisin",           "Créole",            "langue",    4,  -6.3,  147.0, "Papouasie-NG",     "Océanie",         "safe",    True,  "Latin",        "Anglais pidgin mélanésien"),
    ("Bislama",             "Créole",            "langue",   0.21, -17.7, 168.3, "Vanuatu",          "Océanie",         "safe",    True,  "Latin",        "Pidgin officiel de Vanuatu"),
    ("Hiri Motu",           "Austronésienne",    "dialecte", 0.12, -9.4,  147.2, "Papouasie-NG",     "Océanie",         "vulnerable", True,"Latin",       "Pidgin policier de Papouasie"),
    ("Wenzhounais",         "Sino-tibétaine",    "dialecte",  2,  28.0,  120.7, "Chine",            "Asie de l'Est",   "safe",    False, "Sinogrammes",  "Dialecte wu le plus divergent"),
    ("Taïwanais (Min du S.)","Sino-tibétaine",   "dialecte", 15,  23.5,  121.0, "Taïwan",           "Asie de l'Est",   "vulnerable", False,"Sinogrammes","Hokkien de Taïwan"),
    ("Xiang (Hunnanais)",   "Sino-tibétaine",    "dialecte", 38,  28.2,  112.0, "Chine",            "Asie de l'Est",   "safe",    False, "Sinogrammes",  "Dialecte du Hunan"),
    ("Gan",                 "Sino-tibétaine",    "dialecte", 21,  28.7,  115.9, "Chine",            "Asie de l'Est",   "safe",    False, "Sinogrammes",  "Dialecte du Jiangxi"),
    ("Ryukyu (Okinawaïen)", "Japonique",         "dialecte", 0.9, 26.2,  127.7, "Japon",            "Asie de l'Est",   "endangered", False,"Latin/Kan.", "Langue des îles Ryukyu"),
    ("Jejueo",              "Koreanique",        "dialecte", 0.06, 33.5, 126.5, "Corée du Sud",     "Asie de l'Est",   "critically_endangered", False,"Hangul","2 locuteurs natifs en 2023"),
    ("Zhuang",              "Kadaï",             "langue",   16,  23.9,  108.4, "Chine",            "Asie de l'Est",   "vulnerable", True,"Latin/Chuang","Langue thaï-kadaï officielle"),
    ("Yi",                  "Sino-tibétaine",    "langue",    2,  26.0,  103.0, "Chine",            "Asie de l'Est",   "vulnerable", True,"Yi",           "Syllabaire yi de 819 symboles"),
    ("Miao (Hmong)",        "Hmong-Mien",        "langue",    9,  26.0,  107.0, "Chine/SE-Asie",    "Asie du SE",      "vulnerable", False,"Latin",      "Dispersé entre 9 pays"),
    ("Yao",                 "Hmong-Mien",        "langue",    3,  24.0,  110.0, "Chine",            "Asie de l'Est",   "vulnerable", False,"Latin",      "Famille hmong-mien du Sud"),
    ("Ganda",               "Niger-Congo",       "langue",    5,   0.3,   32.6, "Ouganda",          "Afrique",         "safe",    False, "Latin",        "Langue bantoue principale d'Ouganda"),
    ("Luba-Kasai",          "Niger-Congo",       "langue",    6,  -5.5,   23.0, "RD Congo",         "Afrique",         "safe",    False, "Latin",        "Langue bantoue du Kasai"),
    ("Tshiluba",            "Niger-Congo",       "dialecte",  8,  -6.0,   23.5, "RD Congo",         "Afrique",         "safe",    True,  "Latin",        "Nationale de la RDC"),
    ("Kituba",              "Créole",            "dialecte",  5,  -4.5,   15.0, "Congo/RDC",        "Afrique",         "safe",    True,  "Latin",        "Créole bantoue du Congo"),
    ("Sango",               "Créole",            "langue",   0.5,   5.0,   19.0, "Centrafrique",     "Afrique",         "safe",    True,  "Latin",        "Lingua franca centrafricaine"),
    ("Manding",             "Niger-Congo",       "langue",   11,  12.0,   -9.5, "Guinée",           "Afrique",         "safe",    False, "Latin/Arabe",  "Famille mandé, empire du Mali"),
    ("Éwé",                 "Niger-Congo",       "langue",    7,   6.4,    0.8, "Togo/Ghana",       "Afrique",         "safe",    False, "Latin",        "Langue gbe du golfe du Bénin"),
    ("Fon",                 "Niger-Congo",       "langue",    2,   6.4,    2.3, "Bénin",            "Afrique",         "safe",    False, "Latin",        "Langue vodoun du Bénin"),
    ("Krio",                "Créole",            "langue",  0.47,   8.5,  -13.2, "Sierra Leone",     "Afrique",         "safe",    False, "Latin",        "Créole anglais, lingua franca"),
    ("Kabiyè",              "Niger-Congo",       "langue",   0.9,  10.0,    1.0, "Togo",             "Afrique",         "safe",    True,  "Latin",        "Co-officielle au Togo"),
]
LANGUES_RAW = [x for x in LANGUES_RAW if x is not None]

COLS = ["nom","famille","type","locuteurs_M","lat","lon","pays","region",
        "statut","officielle","script","notes"]
df = pd.DataFrame(LANGUES_RAW, columns=COLS)

STATUT_LABEL = {"safe":"Vivante","vulnerable":"Vulnérable","endangered":"En danger","critically_endangered":"Critique"}
STATUT_COLOR = {"safe":"#14b8a6","vulnerable":"#f59e0b","endangered":"#f97316","critically_endangered":"#ef4444"}
STATUT_BADGE = {"safe":"b-safe","vulnerable":"b-vuln","endangered":"b-danger","critically_endangered":"b-critical"}
FAMILLE_COLORS = {
    "Indo-européenne":"#a78bfa","Sino-tibétaine":"#f9a8d4","Afro-asiatique":"#6ee7b7",
    "Niger-Congo":"#7dd3fc","Austronésienne":"#fde68a","Dravidienne":"#fdba74",
    "Turco-mongole":"#86efac","Austro-asiatique":"#fca5a5","Ouralienne":"#c4b5fd",
    "Koreanique":"#f0abfc","Japonique":"#d8b4fe","Kadaï":"#99f6e4",
    "Caucasique du N.":"#fcd34d","Kartvélienne":"#67e8f9","Isolat":"#f9a8d4",
    "Iroquoienne":"#a5f3fc","Na-Déné":"#bfdbfe","Uto-aztèque":"#fed7aa",
    "Quechuan":"#bbf7d0","Aymaran":"#bae6fd","Tupian":"#d9f99d","Esquimau-aléoute":"#e9d5ff",
    "Nilo-saharienne":"#fda4af","Créole":"#fb923c","Hmong-Mien":"#4ade80",
    "Maya":"#34d399","Oto-mangue":"#2dd4bf","Arawak":"#38bdf8",
}

df["statut_label"] = df["statut"].map(STATUT_LABEL)
df["couleur"]      = df["statut"].map(STATUT_COLOR)
all_familles = sorted(df["famille"].unique().tolist())

# ══════════════════════════════════════════════
# NAVIGATION
# systeme simple avec session_state, pas besoin de router externe
# on garde un historique pour le bouton retour
# ══════════════════════════════════════════════
if "page"    not in st.session_state: st.session_state.page    = "home"
if "history" not in st.session_state: st.session_state.history = ["home"]
page = st.session_state.page

def go(p):
    if p != st.session_state.page:
        st.session_state.history.append(p)
    st.session_state.page = p
    st.rerun()

def go_back():
    h = st.session_state.history
    if len(h) > 1: h.pop(); st.session_state.page = h[-1]
    else: st.session_state.page = "home"; st.session_state.history = ["home"]
    st.rerun()

# ══════════════════════════════════════════════
# SYSTÈME AUDIO
# les fichiers mp3 sont dans /audio, si ils existent pas c'est pas grave
# ça crashe pas, ça joue juste rien
# ══════════════════════════════════════════════
def _audio_b64(filename):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio", filename)
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

_snd = {k: _audio_b64(v) for k, v in {
    "hover": "hover.mp3",
    "click": "click.mp3",
    "music": "music.mp3",
    "game":  "game.mp3",
}.items()}

_bg_music_key  = "game" if page == "jeu" else "music"
_bg_music_b64  = _snd[_bg_music_key]
_hover_b64     = _snd["hover"]
_click_b64     = _snd["click"]

def _src(b64, mime="audio/mpeg"):
    return f"data:{mime};base64,{b64}" if b64 else ""

_audio_html = f"""<!DOCTYPE html><html><head></head><body style="margin:0;padding:0;overflow:hidden">
<audio id="vox_music" loop preload="auto">
  <source src="{_src(_bg_music_b64)}" type="audio/mpeg">
</audio>
<audio id="vox_hover" preload="auto">
  <source src="{_src(_hover_b64)}" type="audio/mpeg">
</audio>
<audio id="vox_click" preload="auto">
  <source src="{_src(_click_b64)}" type="audio/mpeg">
</audio>
<script>
(function() {{
  var music = document.getElementById('vox_music');
  var hover = document.getElementById('vox_hover');
  var click = document.getElementById('vox_click');
  var MUTED = {'true' if _is_muted else 'false'};
  if (music) music.volume = MUTED ? 0 : 0.30;
  if (hover) hover.volume = MUTED ? 0 : 0.55;
  if (click) click.volume = MUTED ? 0 : 0.70;
  function startMusic() {{
    if (MUTED) return;
    if (!music || !music.querySelector('source[src]').src.startsWith('data:')) return;
    music.play().catch(function(){{}});
  }}
  if (!MUTED) startMusic();
  if (MUTED && music) {{ music.pause(); }}
  window.parent.document.addEventListener('click', function _unlock() {{
    if (!MUTED) startMusic();
    window.parent.document.removeEventListener('click', _unlock);
  }}, {{once: true}});
  function playSound(el) {{
    if (MUTED) return;
    if (!el) return;
    var src = el.querySelector('source');
    if (!src || !src.getAttribute('src').startsWith('data:')) return;
    el.currentTime = 0;
    el.play().catch(function(){{}});
  }}
  function attachSounds(btn) {{
    if (btn._voxBound) return;
    btn._voxBound = true;
    btn.addEventListener('mouseenter', function() {{ playSound(hover); }});
    btn.addEventListener('mousedown',  function() {{ playSound(click); }});
  }}
  try {{
    var parentDoc = window.parent.document;
    parentDoc.querySelectorAll('button').forEach(attachSounds);
    new MutationObserver(function() {{
      parentDoc.querySelectorAll('button').forEach(attachSounds);
    }}).observe(parentDoc.body, {{childList: true, subtree: true}});
  }} catch(e) {{}}
}})();
</script>
</body></html>"""

st.components.v1.html(_audio_html, height=0, scrolling=False)

# -------------------------------------------------------
# bouton retour (pas sur la home) + toggle theme
# -------------------------------------------------------
if page != "home":
    st.markdown('<div style="padding:1.2rem 2rem 0">', unsafe_allow_html=True)
    back_col, _, theme_col = st.columns([1, 5, 1])
    with back_col:
        st.markdown('<div class="back-btn-wrap">', unsafe_allow_html=True)
        if st.button("◂ ACCUEIL", key="global_back"):
            go_back()
        st.markdown('</div>', unsafe_allow_html=True)
    with theme_col:
        _m_icon = "🔇  Muet" if not _is_muted else "🔊  Son"
        if st.button(_m_icon, key="mute_toggle_sub"):
            st.session_state.muted = not _is_muted
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# carte plotly (utilisee sur la home et dans le jeu)
def _build_map(df_src, height=480, zoom=2, center=(20,10)):
    try:
        import plotly.graph_objects as go

        sizes = [max(6, min(55, math.sqrt(float(v)+1)*5.5)) for v in df_src["locuteurs_M"]]
        colors = [FAMILLE_COLORS.get(f, "#a78bfa") for f in df_src["famille"]]

        hover_text = [
            f"<b>{r['nom']}</b><br>"
            f"<span style='color:#8b5cf6'>{r['famille']}</span> · {r['type']}<br>"
            f"👥 {r['locuteurs_M']}M locuteurs<br>"
            f"🏳 {r['pays']} · ✍ {r['script']}<br>"
            f"<i>{r['statut_label']}</i><br>"
            f"<span style='font-size:0.85em;color:#6b7280'>{r['notes']}</span>"
            for _, r in df_src.iterrows()
        ]

        fig = go.Figure(go.Scattergeo(
            lat=df_src["lat"], lon=df_src["lon"], mode="markers",
            marker=dict(size=sizes, color=colors, opacity=0.85,
                        line=dict(width=1.2, color="rgba(255,255,255,0.6)"), sizemode="diameter"),
            hovertext=hover_text, hoverinfo="text",
            hoverlabel=dict(bgcolor="#1a0a2e", bordercolor="#a78bfa",
                            font=dict(family="Outfit, sans-serif", size=12, color="#f1f0ff")),
        ))
        fig.update_geos(
            projection_type="natural earth",
            showland=True, landcolor=_tv['land'], showocean=True, oceancolor=_tv['ocean'],
            showcoastlines=True, coastlinecolor=_tv['coast'],
            showframe=False, showcountries=True, countrycolor="rgba(167,139,250,0.15)",
            showlakes=False, bgcolor="rgba(0,0,0,0)", lataxis_range=[-65, 85],
        )
        fig.update_layout(height=height, margin=dict(l=0, r=0, t=0, b=0),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          geo=dict(bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        return True
    except ImportError:
        st.info("Installe `plotly` pour afficher la carte.")
        return False

# -------------------------------------------------------
# PAGE : HOME
# -------------------------------------------------------
if page == "home":
    st.markdown('<div class="page-wrap">', unsafe_allow_html=True)

    # toggle mute en haut a droite
    _, _mcol = st.columns([6, 1])
    with _mcol:
        _m_icon_h = "🔇  Muet" if not _is_muted else "🔊  Son"
        if st.button(_m_icon_h, key="mute_toggle_home"):
            st.session_state.muted = not _is_muted
            st.rerun()

    # hero section
    st.markdown("""
<div style="position:relative;overflow:hidden;padding:3.5rem 3rem 2rem">

  <!-- orbes décoratifs -->
  <div style="position:absolute;top:-80px;right:-100px;width:500px;height:500px;
    background:radial-gradient(circle,rgba(124,58,237,0.22) 0%,transparent 65%);
    border-radius:50%;pointer-events:none;animation:float 8s ease-in-out infinite"></div>
  <div style="position:absolute;bottom:-120px;left:-80px;width:400px;height:400px;
    background:radial-gradient(circle,rgba(236,72,153,0.12) 0%,transparent 65%);
    border-radius:50%;pointer-events:none;animation:float 10s ease-in-out infinite reverse"></div>

  <!-- badge tag -->
  <div style="display:inline-flex;align-items:center;gap:7px;
    background:rgba(167,139,250,0.1);border:1px solid rgba(167,139,250,0.3);
    border-radius:20px;padding:4px 14px;margin-bottom:1.4rem;animation:fadeUp 0.4s ease both">
    <span style="width:6px;height:6px;background:#a78bfa;border-radius:50%;
      box-shadow:0 0 8px #a78bfa;display:inline-block;animation:pulse-dot 2s infinite"></span>
    <span style="font-size:0.63rem;font-weight:700;letter-spacing:0.14em;color:#a78bfa;font-family:'Outfit',sans-serif">VOXORBIS · ATLAS DES LANGUES · 2025</span>
  </div>

  <!-- TITRE principal -->
  <h1 style="font-family:Outfit,sans-serif;font-size:clamp(3.5rem,7vw,6.5rem);
    font-weight:900;line-height:0.88;margin:0 0 1rem;letter-spacing:-0.03em;
    background:linear-gradient(135deg,#ffffff 0%,#c4b5fd 40%,#ec4899 80%,#f59e0b 100%);
    background-size:200% auto;
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
    animation:fadeUp 0.5s ease 0.05s both,shimmer-text 6s linear infinite">
    VOX<br>ORBIS
  </h1>

  <!-- sous-titre -->
  <p style="font-family:'Fraunces',serif;font-size:1.05rem;color:#c4b5fd;
    max-width:420px;line-height:1.7;margin:0 0 0.5rem;font-style:italic;
    animation:fadeUp 0.5s ease 0.1s both">
    200+ langues &amp; dialectes, de l'occitan languedocien au darija algérien,
    du cherokee au tibétain.
  </p>
</div>
""", unsafe_allow_html=True)

    # stats row (clickable boxes)
    n_langues   = int((df["type"] == "langue").sum())
    n_dialectes = int((df["type"] == "dialecte").sum())
    n_familles  = int(df["famille"].nunique())
    n_danger    = int(df[df["statut"].isin(["endangered","critically_endangered"])].shape[0])
    n_safe      = int(df[df["statut"] == "safe"].shape[0])

    if "stat_panel" not in st.session_state:
        st.session_state.stat_panel = None

    def _lang_rows(mask, sort_col="locuteurs_M", max_items=120):
        sub = df[mask].sort_values(sort_col, ascending=False)
        rows = []
        for _, r in sub.head(max_items).iterrows():
            c = STATUT_COLOR.get(r["statut"], "#a78bfa")
            rows.append(
                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'padding:5px 0;border-bottom:1px solid rgba(255,255,255,0.06)">'
                f'<span style="font-size:0.78rem;color:#f1f0ff">{r["nom"]}</span>'
                f'<span style="font-size:0.68rem;color:{c};background:{c}22;'
                f'border-radius:6px;padding:1px 8px;white-space:nowrap">{r["statut_label"]}</span></div>')
        return "".join(rows)

    def _fam_rows():
        rows = []
        for fam in sorted(df["famille"].unique()):
            n = int((df["famille"] == fam).sum())
            color = FAMILLE_COLORS.get(fam, "#a78bfa")
            rows.append(
                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'padding:5px 0;border-bottom:1px solid rgba(255,255,255,0.06)">'
                f'<span style="font-size:0.78rem;color:#f1f0ff">{fam}</span>'
                f'<span style="font-size:0.68rem;color:{color};background:{color}22;'
                f'border-radius:6px;padding:1px 8px">{n} langue{"s" if n>1 else ""}</span></div>')
        return "".join(rows)

    panel_data = {
        "langues":   ("Langues du monde",  "#a78bfa", _lang_rows(df["type"] == "langue")),
        "dialectes": ("Dialectes",          "#ec4899", _lang_rows(df["type"] == "dialecte")),
        "familles":  ("Familles linguistiques",           "#38bdf8", _fam_rows()),
        "danger":    ("En danger",          "#f97316", _lang_rows(df["statut"].isin(["endangered","critically_endangered"]))),
        "safe":      ("Vivantes",            "#14b8a6", _lang_rows(df["statut"] == "safe")),
    }

    stat_defs = [
        ("langues",   n_langues,   "#a78bfa", "rgba(167,139,250,0.12)", "rgba(167,139,250,0.35)", "LANGUES"),
        ("dialectes", n_dialectes, "#ec4899", "rgba(236,72,153,0.12)",  "rgba(236,72,153,0.35)",  "DIALECTES"),
        ("familles",  n_familles,  "#38bdf8", "rgba(56,189,248,0.12)",  "rgba(56,189,248,0.35)",  "FAMILLES"),
        ("danger",    n_danger,    "#f97316", "rgba(249,115,22,0.12)",  "rgba(249,115,22,0.35)",  "EN DANGER"),
        ("safe",      n_safe,      "#14b8a6", "rgba(20,184,166,0.12)",  "rgba(20,184,166,0.3)",   "VIVANTES"),
    ]

    # CSS pour transformer les boutons en stat boxes
    st.markdown("""
<style>
.stat-box-row .stButton > button {
  background: var(--stat-bg) !important;
  border: 1px solid var(--stat-border) !important;
  border-radius: 14px !important;
  padding: 0.8rem 0.4rem 0.6rem !important;
  width: 100% !important;
  text-align: center !important;
  min-height: 80px !important;
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 2px !important;
  transition: transform .18s, box-shadow .18s !important;
  backdrop-filter: blur(12px) !important;
}
.stat-box-row .stButton > button:hover {
  transform: translateY(-5px) scale(1.05) !important;
  box-shadow: 0 12px 32px rgba(0,0,0,0.4), 0 0 20px var(--stat-glow) !important;
}
.stat-box-row .stButton > button p {
  margin: 0 !important;
  line-height: 1.1 !important;
}
</style>""", unsafe_allow_html=True)

    st.markdown('<div class="stat-box-row" style="padding:0 2rem;margin-bottom:0.3rem">', unsafe_allow_html=True)
    box_cols = st.columns(5, gap="small")
    for i, (key, val, color, bg, border, label) in enumerate(stat_defs):
        with box_cols[i]:
            is_active = st.session_state.stat_panel == key
            active_style = f"box-shadow:0 0 0 2px {color}, 0 12px 32px rgba(0,0,0,0.4);" if is_active else ""
            st.markdown(f'<style>div[data-testid="column"]:nth-child({i+1}) .stat-box-row .stButton > button,'
                        f'div[data-testid="stVerticalBlock"] > div:nth-child(1) div[data-testid="column"]:nth-child({i+1}) .stButton > button'
                        f'{{ --stat-bg: {bg}; --stat-border: {border}; --stat-glow: {color}55; {active_style} }}</style>', unsafe_allow_html=True)
            btn_label = f"**{val}**\n\n{label}"
            if st.button(f"{val}\n{label}", key=f"sbox_{key}", use_container_width=True):
                st.session_state.stat_panel = None if is_active else key
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Style override pour les stat box buttons text
    for i, (key, val, color, bg, border, label) in enumerate(stat_defs):
        st.markdown(f"""<style>
button[data-testid="stBaseButton-secondary"][key="sbox_{key}"],
button[kind="secondary"]:has(> div > p) {{}}
div[data-testid="stVerticalBlock"] button[key="sbox_{key}"] {{
  --stat-bg: {bg} !important; --stat-border: {border} !important;
}}
</style>""", unsafe_allow_html=True)

    # Panel déroulant
    pk = st.session_state.stat_panel
    if pk and pk in panel_data:
        title, color, content = panel_data[pk]
        st.markdown(f"""
<div style="background:rgba(13,8,32,0.92);border:1px solid {color}44;
  border-left:3px solid {color};border-radius:16px;
  padding:1rem 1.4rem;margin:0 2rem 0.8rem;animation:fadeUp 0.2s ease">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.7rem">
    <span style="font-family:'Outfit',sans-serif;font-size:0.9rem;font-weight:800;color:{color}">{title}</span>
    <span style="font-family:'Outfit',sans-serif;font-size:0.6rem;color:#4a3870">
      Clique à nouveau sur la box pour fermer</span>
  </div>
  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:4px;
    max-height:260px;overflow-y:auto;scrollbar-width:thin;scrollbar-color:{color}44 transparent">
    {content}
  </div>
</div>""", unsafe_allow_html=True)

    # separateur carte
    st.markdown("""
<div style="display:flex;align-items:center;gap:12px;padding:1.5rem 3rem 0.6rem">
  <div style="flex:1;height:1px;background:linear-gradient(90deg,rgba(124,58,237,0.4),transparent)"></div>
  <span style="font-family:'Outfit',sans-serif;font-size:0.6rem;font-weight:700;
    letter-spacing:0.14em;color:#4a3870;text-transform:uppercase">CARTE MONDIALE INTERACTIVE</span>
  <div style="flex:1;height:1px;background:linear-gradient(90deg,transparent,rgba(124,58,237,0.4))"></div>
</div>""", unsafe_allow_html=True)

    # carte avec cadre lumineux
    st.markdown("""
<style>
@keyframes border-spin {
  0%   { background-position: 0% 50%; }
  50%  { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
@keyframes glow-breathe {
  0%,100% { box-shadow: 0 0 18px rgba(124,58,237,0.35), 0 0 40px rgba(124,58,237,0.15), inset 0 0 20px rgba(0,0,0,0.4); }
  50%      { box-shadow: 0 0 32px rgba(167,139,250,0.55), 0 0 70px rgba(236,72,153,0.22), 0 0 100px rgba(124,58,237,0.18), inset 0 0 20px rgba(0,0,0,0.4); }
}
.map-frame-outer {
  position: relative; padding: 3px; border-radius: 22px; margin: 0 2rem;
  background: linear-gradient(270deg, #7c3aed, #ec4899, #14b8a6, #a78bfa, #7c3aed);
  background-size: 300% 300%;
  animation: border-spin 5s ease infinite, glow-breathe 3s ease-in-out infinite;
  touch-action: none;
}
.map-frame-inner {
  border-radius: 20px; overflow: hidden; background: #0d0820; position: relative;
}
.map-frame-inner::before {
  content: ''; position: absolute; inset: 0; border-radius: 20px;
  background: linear-gradient(180deg, rgba(124,58,237,0.08) 0%, transparent 30%, transparent 70%, rgba(124,58,237,0.06) 100%);
  pointer-events: none; z-index: 1;
}
.map-corner {
  position: absolute; width: 18px; height: 18px;
  border-color: #a78bfa; border-style: solid; z-index: 2; opacity: 0.9;
}
.map-corner.tl { top:6px;  left:6px;  border-width: 2px 0 0 2px; border-radius: 4px 0 0 0; }
.map-corner.tr { top:6px;  right:6px; border-width: 2px 2px 0 0; border-radius: 0 4px 0 0; }
.map-corner.bl { bottom:6px; left:6px;  border-width: 0 0 2px 2px; border-radius: 0 0 0 4px; }
.map-corner.br { bottom:6px; right:6px; border-width: 0 2px 2px 0; border-radius: 0 0 4px 0; }
</style>
<div class="map-frame-outer">
  <div class="map-frame-inner" id="map-container">
    <div class="map-corner tl"></div><div class="map-corner tr"></div>
    <div class="map-corner bl"></div><div class="map-corner br"></div>
""", unsafe_allow_html=True)

    _build_map(df, height=440)

    st.markdown("</div></div>", unsafe_allow_html=True)

    # separateur "explorer l'atlas"
    st.markdown("""
<div style="display:flex;align-items:center;gap:12px;padding:1.8rem 3rem 1.2rem">
  <div style="flex:1;height:1px;background:linear-gradient(90deg,rgba(124,58,237,0.4),transparent)"></div>
  <span style="font-family:'Outfit',sans-serif;font-size:0.6rem;font-weight:700;
    letter-spacing:0.14em;color:#4a3870;text-transform:uppercase">EXPLORER L'ATLAS</span>
  <div style="flex:1;height:1px;background:linear-gradient(90deg,transparent,rgba(124,58,237,0.4))"></div>
</div>""", unsafe_allow_html=True)

    # nav cards (3 colonnes)
    st.markdown('<div style="padding:0 2.5rem 1.5rem">', unsafe_allow_html=True)
    nc1, nc2, nc3 = st.columns(3, gap="large")

    card_defs = [
        (nc1, "fiches", "#ec4899", "📚", "Fiches Langues",
         "Explorez les 200+ fiches détaillées : famille, script, statut, locuteurs.",
         "0s", "Parcourir les langues"),
        (nc2, "stats", "#14b8a6", "📊", "Statistiques",
         "K-Means, régression OLS, Shannon, distributions. Tout from scratch.",
         "0.08s", "Décrypter les données"),
        (nc3, "occitanie", "#f59e0b", "✨", "Occitanie",
         "Les langues du territoire montpelliérain, du languedocien au darija.",
         "0.16s", "Partir en territoire"),
    ]

    st.markdown("""
<style>
div[data-testid="column"]:nth-child(1) .stButton > button {
  border-color: rgba(236,72,153,0.4) !important; color: #f9a8d4 !important;
}
div[data-testid="column"]:nth-child(1) .stButton > button:hover {
  background: rgba(236,72,153,0.28) !important; border-color: #ec4899 !important;
  box-shadow: 0 8px 28px rgba(236,72,153,0.35), 0 0 0 1px rgba(236,72,153,0.4) !important;
  color: #fff !important; transform: translateY(-3px) scale(1.04) !important;
}
div[data-testid="column"]:nth-child(2) .stButton > button {
  border-color: rgba(20,184,166,0.4) !important; color: #5eead4 !important;
}
div[data-testid="column"]:nth-child(2) .stButton > button:hover {
  background: rgba(20,184,166,0.25) !important; border-color: #14b8a6 !important;
  box-shadow: 0 8px 28px rgba(20,184,166,0.35), 0 0 0 1px rgba(20,184,166,0.4) !important;
  color: #fff !important; transform: translateY(-3px) scale(1.04) !important;
}
div[data-testid="column"]:nth-child(3) .stButton > button {
  border-color: rgba(245,158,11,0.4) !important; color: #fcd34d !important;
}
div[data-testid="column"]:nth-child(3) .stButton > button:hover {
  background: rgba(245,158,11,0.22) !important; border-color: #f59e0b !important;
  box-shadow: 0 8px 28px rgba(245,158,11,0.35), 0 0 0 1px rgba(245,158,11,0.4) !important;
  color: #fff !important; transform: translateY(-3px) scale(1.04) !important;
}
</style>""", unsafe_allow_html=True)

    for col, pid, color, icon, title, desc, delay, btn_label in card_defs:
        with col:
            st.markdown(f"""
<div class="home-nav-card" style="border-top:3px solid {color};animation-delay:{delay}">
  <div style="width:56px;height:56px;border-radius:16px;margin:0 auto 1.1rem;
    background:linear-gradient(135deg,{color}33,{color}11);border:1px solid {color}44;
    display:flex;align-items:center;justify-content:center;font-size:1.8rem;
    box-shadow:0 8px 24px {color}33,inset 0 1px 0 rgba(255,255,255,0.1)">{icon}</div>
  <p style="font-family:'Outfit',sans-serif;font-size:1.05rem;font-weight:800;
    color:#f1f0ff;margin:0 0 0.5rem;letter-spacing:-0.01em">{title}</p>
  <p style="font-family:'Fraunces',serif;font-size:0.83rem;color:#8b7ac9;
    margin:0 0 1.4rem;font-style:italic;line-height:1.6">{desc}</p>
  <div style="height:2px;width:32px;margin:0 auto 1.1rem;
    background:linear-gradient(90deg,{color},{color}44);border-radius:2px"></div>
</div>""", unsafe_allow_html=True)
            if st.button(btn_label, key=f"home_{pid}", use_container_width=True):
                go(pid)

    st.markdown('</div>', unsafe_allow_html=True)

    # navigation cards : carte HTML + petit bouton fleche a droite
    _mini_cards = [
        ("reseau",     "#6366f1", "🕸️", "Réseau",       "Graphe force-directed des clusters.", "⚠ Feature gourmande (CPU)", "#fbbf24"),
        ("jeu",        "#22d3ee", "🌍", "Place-moi !",   "Localise chaque langue sur la carte.", "10 manches, score final.", "#6b5fa8"),
        ("timeline",   "#f97316", "🕰️", "Timeline",     "5000 ans d'histoire linguistique.", "Frise interactive filtrable.", "#6b5fa8"),
        ("comparateur","#8b5cf6", "⚖️", "Comparateur",  "Mets 2 ou 3 langues cote a cote.", "Compare tous leurs attributs.", "#6b5fa8"),
        ("quiz",       "#10b981", "✍️", "Quiz Script",  "Devine la langue derriere l ecriture.", "10 questions, 4 choix.", "#6b5fa8"),
        ("about",      "#64748b", "📄", "A propos",      "Methodologie, sources et credits.", "Stack technique et limites.", "#6b5fa8"),
    ]

    # CSS : bouton fleche petit et rond + centrage vertical
    _arrow_css = """
/* centrage vertical de la colonne fleche */
div[data-testid="stHorizontalBlock"] > div:last-child {
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}
"""
    for pid, color, *_ in _mini_cards:
        _arrow_css += f"""
div[data-testid="stVerticalBlock"] button[key="go_{pid}"] {{
  background: {color}18 !important;
  border: 1.5px solid {color}44 !important;
  border-radius: 50% !important;
  width: 44px !important; height: 44px !important;
  min-height: 44px !important; max-width: 44px !important;
  padding: 0 !important;
  display: flex !important; align-items: center !important; justify-content: center !important;
  transition: all 0.25s cubic-bezier(.34,1.56,.64,1) !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2) !important;
  flex-shrink: 0 !important;
  margin: 0 auto !important;
}}
div[data-testid="stVerticalBlock"] button[key="go_{pid}"] p {{
  color: {color} !important; font-size: 1.1rem !important; margin: 0 !important;
  line-height: 1 !important;
}}
div[data-testid="stVerticalBlock"] button[key="go_{pid}"]:hover {{
  background: {color}35 !important;
  border-color: {color} !important;
  transform: scale(1.15) translateX(3px) !important;
  box-shadow: 0 4px 16px {color}44, 0 0 12px {color}33 !important;
}}
div[data-testid="stVerticalBlock"] button[key="go_{pid}"]:hover p {{
  color: #fff !important;
}}
"""
    st.markdown(f"<style>{_arrow_css}</style>", unsafe_allow_html=True)

    # grille 2 colonnes : [card HTML + fleche bouton]
    for row_start in range(0, len(_mini_cards), 2):
        cols = st.columns(2, gap="medium")
        for col_idx in range(2):
            card_idx = row_start + col_idx
            if card_idx >= len(_mini_cards):
                break
            pid, color, icon, title, desc, sub, sub_color = _mini_cards[card_idx]
            with cols[col_idx]:
                card_col, arrow_col = st.columns([5.5, 1])
                with card_col:
                    st.markdown(f"""
<div style="background:rgba(255,255,255,0.04);border:1px solid {color}33;border-left:3px solid {color};
  border-radius:16px;padding:0.9rem 1.2rem;backdrop-filter:blur(12px);
  box-shadow:0 4px 16px rgba(0,0,0,0.2);
  display:flex;align-items:center;gap:0.9rem;
  transition:all 0.2s"
  onmouseenter="this.style.background='{color}0a';this.style.borderColor='{color}55'"
  onmouseleave="this.style.background='rgba(255,255,255,0.04)';this.style.borderColor='{color}33'">
  <div style="width:42px;height:42px;border-radius:12px;flex-shrink:0;
    background:linear-gradient(135deg,{color}22,{color}08);border:1px solid {color}44;
    display:flex;align-items:center;justify-content:center;font-size:1.25rem;
    box-shadow:0 4px 12px {color}22">{icon}</div>
  <div style="flex:1;min-width:0">
    <p style="font-family:Outfit,sans-serif;font-size:0.92rem;font-weight:800;color:#f1f0ff;margin:0 0 0.1rem">{title}</p>
    <p style="font-family:Fraunces,serif;font-size:0.74rem;color:#c4b5fd;margin:0;font-style:italic;line-height:1.3">{desc}</p>
    <p style="margin:0.12rem 0 0;font-family:Outfit,sans-serif;font-size:0.68rem;font-weight:600;color:{sub_color}">{sub}</p>
  </div>
</div>""", unsafe_allow_html=True)
                with arrow_col:
                    if st.button("➛", key=f"go_{pid}"):
                        go(pid)

    st.markdown('</div>', unsafe_allow_html=True)  # page-wrap

# PAGE : PLACE-MOI (mini-jeu geographique)
# le joueur clique sur la carte plotly pour deviner ou se parle une langue
# on utilise haversine pour calculer la distance en km
# le score depend de la distance : < 200km = 1000pts, > 4000km = 50pts
elif page == "jeu":
    import plotly.graph_objects as _go
    import json as _json

    _SCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".voxorbis_best.json")

    def _load_best():
        try:
            with open(_SCORE_FILE) as f:
                d = _json.load(f)
                return int(d.get("best", 0)), str(d.get("date", ""))
        except Exception:
            return 0, ""

    def _save_best(score):
        import datetime
        try:
            with open(_SCORE_FILE, "w") as f:
                _json.dump({"best": score, "date": datetime.date.today().strftime("%d/%m/%Y")}, f)
        except Exception:
            pass

    if "jeu_best" not in st.session_state:
        st.session_state.jeu_best, st.session_state.jeu_best_date = _load_best()

    if "jeu_round"   not in st.session_state: st.session_state.jeu_round   = 0
    if "jeu_score"   not in st.session_state: st.session_state.jeu_score   = 0
    if "jeu_order"   not in st.session_state:
        import random as _rnd
        _pool = df[df["statut"].isin(["safe","vulnerable"])].copy()
        _idx  = list(_pool.index)
        _rnd.shuffle(_idx)
        st.session_state.jeu_order   = _idx[:10]
        st.session_state.jeu_guesses = []
        st.session_state.jeu_waiting = False
        st.session_state.jeu_click   = None

    ROUNDS_TOTAL = 10

    def _jeu_reset():
        import random as _rnd
        _pool = df[df["statut"].isin(["safe","vulnerable"])].copy()
        _idx  = list(_pool.index)
        _rnd.shuffle(_idx)
        st.session_state.jeu_round   = 0
        st.session_state.jeu_score   = 0
        st.session_state.jeu_order   = _idx[:10]
        st.session_state.jeu_guesses = []
        st.session_state.jeu_waiting = False
        st.session_state.jeu_click   = None

    def _haversine(lat1, lon1, lat2, lon2):
        R = 6371
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlam = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    def _dist_to_pts(km):
        if km < 200:   return 1000
        if km < 500:   return 800
        if km < 1000:  return 600
        if km < 2000:  return 400
        if km < 4000:  return 200
        return 50

    st.markdown('<div class="page-wrap" style="padding:0.5rem 2vw 2rem">', unsafe_allow_html=True)

    rnd   = st.session_state.jeu_round
    score = st.session_state.jeu_score

    # fin de partie
    if rnd >= ROUNDS_TOTAL:
        pct = score / (ROUNDS_TOTAL * 1000) * 100
        if pct >= 80:   medal, msg = "🏆", "Cartographe d'élite !"
        elif pct >= 55: medal, msg = "🥈", "Bon sens de l'orientation !"
        elif pct >= 35: medal, msg = "🥉", "En route pour la maîtrise…"
        else:           medal, msg = "🌐", "Le monde est vaste, réessaie !"

        is_new_record = score > st.session_state.jeu_best
        if is_new_record:
            st.session_state.jeu_best = score
            _save_best(score)
            import datetime
            st.session_state.jeu_best_date = datetime.date.today().strftime("%d/%m/%Y")

        if is_new_record and score > 0:
            st.markdown(f"""
<div style="text-align:center;animation:fadeUp 0.4s ease;margin-bottom:0.5rem">
  <div style="display:inline-flex;align-items:center;gap:10px;
    background:linear-gradient(135deg,rgba(251,191,36,0.18),rgba(245,158,11,0.08));
    border:1.5px solid rgba(251,191,36,0.6);border-radius:50px;padding:0.5rem 1.6rem;
    box-shadow:0 0 24px rgba(251,191,36,0.25)">
    <span style="font-size:1.3rem">⭐</span>
    <span style="font-family:'Outfit',sans-serif;font-size:0.9rem;font-weight:800;
      color:#fbbf24;letter-spacing:0.05em;text-transform:uppercase">Nouveau Record Personnel !</span>
    <span style="font-size:1.3rem">⭐</span>
  </div>
</div>""", unsafe_allow_html=True)

        best_score = st.session_state.jeu_best
        best_date  = st.session_state.jeu_best_date

        st.markdown(f"""
<div style="text-align:center;padding:2rem 2rem 1rem;animation:fadeUp 0.5s ease">
  <div style="font-size:4rem;margin-bottom:0.5rem">{medal}</div>
  <h2 style="font-family:'Outfit',sans-serif;font-size:2rem;font-weight:900;color:#f1f0ff;margin:0 0 0.4rem">{msg}</h2>
  <p style="font-family:'Outfit',sans-serif;font-size:1rem;color:#a78bfa;margin:0 0 1.2rem">
    Score final : <b style="color:#22d3ee;font-size:1.4rem">{score}</b> / {ROUNDS_TOTAL*1000} pts
    &nbsp;·&nbsp; <b style="color:#f1f0ff">{round(pct)}%</b></p>
  <div style="display:inline-flex;align-items:center;gap:12px;
    background:rgba(251,191,36,0.08);border:1px solid rgba(251,191,36,0.25);
    border-radius:14px;padding:0.6rem 1.4rem;margin-bottom:1.5rem">
    <span style="font-size:1.2rem">🏆</span>
    <div style="text-align:left">
      <p style="font-family:'Outfit',sans-serif;font-size:0.6rem;font-weight:700;color:#92400e;text-transform:uppercase;letter-spacing:.08em;margin:0">Record all-time</p>
      <p style="font-family:'Outfit',sans-serif;font-size:1.2rem;font-weight:900;color:#fbbf24;margin:0">{best_score} <span style="font-size:0.75rem;color:#78350f;font-weight:600">/ {ROUNDS_TOTAL*1000}</span></p>
      {"" if not best_date else f'<p style="font-family:\'Outfit\',sans-serif;font-size:0.62rem;color:#78350f;margin:0">{best_date}</p>'}
    </div>
  </div>
</div>""", unsafe_allow_html=True)

        # Résumé des manches
        st.markdown("""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:0.8rem">
  <div style="flex:1;height:1px;background:linear-gradient(90deg,rgba(34,211,238,0.4),transparent)"></div>
  <span style="font-family:'Outfit',sans-serif;font-size:0.6rem;font-weight:700;
    letter-spacing:0.14em;color:#164e63;text-transform:uppercase">DÉTAIL DES MANCHES</span>
  <div style="flex:1;height:1px;background:linear-gradient(90deg,transparent,rgba(34,211,238,0.4))"></div>
</div>""", unsafe_allow_html=True)

        recap_html = '<div style="display:flex;flex-direction:column;gap:0.4rem;margin-bottom:2rem">'
        for i, (nom, dist, pts, glat, glon) in enumerate(st.session_state.jeu_guesses):
            bar_w = int(pts / 10)
            color = "#22d3ee" if pts >= 800 else "#a78bfa" if pts >= 500 else "#f59e0b" if pts >= 200 else "#ef4444"
            recap_html += f"""
<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(34,211,238,0.15);
  border-radius:10px;padding:0.55rem 1rem;display:flex;align-items:center;gap:1rem">
  <span style="font-family:'Outfit',sans-serif;font-size:0.72rem;color:#4a5568;min-width:20px">#{i+1}</span>
  <span style="font-family:'Outfit',sans-serif;font-size:0.9rem;font-weight:700;color:#f1f0ff;min-width:140px">{nom}</span>
  <div style="flex:1;height:6px;background:rgba(255,255,255,0.07);border-radius:3px;overflow:hidden">
    <div style="width:{bar_w}%;height:100%;background:{color};border-radius:3px;box-shadow:0 0 8px {color}88"></div>
  </div>
  <span style="font-family:'Outfit',sans-serif;font-size:0.8rem;color:#8b7ac9;min-width:70px;text-align:right">{int(dist):,} km</span>
  <span style="font-family:'Outfit',sans-serif;font-size:0.88rem;font-weight:700;color:{color};min-width:55px;text-align:right">{pts} pts</span>
</div>"""
        st.markdown(recap_html + "</div>", unsafe_allow_html=True)

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            if st.button("Rejouer", key="jeu_restart", use_container_width=True):
                _jeu_reset(); st.rerun()
        with col_r2:
            if st.button("Retour accueil", key="jeu_home", use_container_width=True):
                go("home")

    else:
        # en cours
        lang_idx = st.session_state.jeu_order[rnd]
        lang_row = df.iloc[lang_idx]
        true_lat, true_lon = float(lang_row["lat"]), float(lang_row["lon"])

        # header + barre de progression
        progress_text = f"{rnd}/{ROUNDS_TOTAL}"
        progress_bar_pct = int(rnd / ROUNDS_TOTAL * 100)

        best_score = st.session_state.jeu_best
        best_date  = st.session_state.jeu_best_date
        best_chip = ""
        if best_score > 0:
            best_date_span = f'<span style="font-family:Outfit,sans-serif;font-size:0.6rem;color:#78350f;display:block">{best_date}</span>' if best_date else ""
            best_chip = (
                f'<div style="background:rgba(251,191,36,0.1);border:1px solid rgba(251,191,36,0.35);'
                f'border-radius:12px;padding:0.4rem 0.8rem;text-align:center;min-width:80px">'
                f'<span style="font-size:0.6rem;font-family:Outfit,sans-serif;color:#92400e;'
                f'text-transform:uppercase;letter-spacing:.05em;display:block">🏆 Record</span>'
                f'<span style="font-family:Outfit,sans-serif;font-size:1.1rem;font-weight:800;color:#fbbf24">{best_score}</span>'
                f'{best_date_span}</div>')

        st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem;margin-bottom:0.8rem">
  <div style="display:flex;align-items:center;gap:12px">
    <span style="font-size:1.6rem">🌍</span>
    <div>
      <h2 style="font-family:Outfit,sans-serif;font-size:1.3rem;font-weight:800;color:#f1f0ff;margin:0">Place-moi sur la carte !</h2>
      <p style="font-family:Fraunces,serif;font-size:0.78rem;color:#8b7ac9;margin:0;font-style:italic">
        Manche {rnd+1} / {ROUNDS_TOTAL} · Clique sur la carte puis valide</p>
    </div>
  </div>
  <div style="display:flex;gap:0.8rem;align-items:center">
    <div style="background:rgba(34,211,238,0.1);border:1px solid rgba(34,211,238,0.3);
      border-radius:12px;padding:0.4rem 1rem;text-align:center">
      <span style="font-family:Outfit,sans-serif;font-size:1.3rem;font-weight:800;color:#22d3ee">{score}</span>
      <span style="font-family:Outfit,sans-serif;font-size:0.65rem;color:#164e63;display:block;text-transform:uppercase;letter-spacing:.05em">pts</span>
    </div>
    {best_chip}
  </div>
</div>""", unsafe_allow_html=True)

        # Progress bar as native Streamlit
        st.progress(rnd / ROUNDS_TOTAL, text=f"Progression : {rnd} / {ROUNDS_TOTAL} manches")

        # Carte langue à deviner
        fam_color = FAMILLE_COLORS.get(lang_row['famille'], '#a78bfa')
        st.markdown(f"""
<div style="background:linear-gradient(135deg,rgba(34,211,238,0.08),rgba(124,58,237,0.06));
  border:1px solid rgba(34,211,238,0.25);border-radius:16px;
  padding:1.2rem 2rem;margin-bottom:1rem;text-align:center;
  box-shadow:0 0 30px rgba(34,211,238,0.08)">
  <p style="font-family:Outfit,sans-serif;font-size:0.65rem;font-weight:700;
    letter-spacing:0.14em;text-transform:uppercase;color:#164e63;margin:0 0 0.3rem">Langue à placer</p>
  <h1 style="font-family:Outfit,sans-serif;font-size:2.5rem;font-weight:900;
    color:#f1f0ff;margin:0 0 0.4rem;letter-spacing:-0.02em">{lang_row['nom']}</h1>
  <div style="display:flex;justify-content:center;gap:1.5rem;flex-wrap:wrap">
    <span style="font-family:Outfit,sans-serif;font-size:0.82rem;color:#8b7ac9">👥 {lang_row['locuteurs_M']}M locuteurs</span>
    <span style="font-family:Outfit,sans-serif;font-size:0.82rem;color:#8b7ac9">✍ {lang_row['script']}</span>
    <span style="font-family:Outfit,sans-serif;font-size:0.82rem;color:{fam_color}">{lang_row['famille']}</span>
  </div>
</div>""", unsafe_allow_html=True)

        waiting = st.session_state.jeu_waiting
        click   = st.session_state.jeu_click

        if not waiting:
            import plotly.graph_objects as _go_jeu

            st.markdown("""
<div style="display:flex;align-items:center;gap:8px;
  background:rgba(34,211,238,0.06);border:1px solid rgba(34,211,238,0.2);
  border-radius:10px;padding:0.45rem 1rem;margin-bottom:0.6rem">
  <span style="font-size:0.85rem;flex-shrink:0">🖱️</span>
  <p style="font-family:Outfit,sans-serif;font-size:0.75rem;color:#67e8f9;margin:0;line-height:1.4">
    <b style="color:#22d3ee">Clique directement sur la carte</b> pour placer ton marqueur, puis valide ta position.
  </p>
</div>""", unsafe_allow_html=True)

            # Clé de persistance pour cette manche
            click_key = f"jeu_click_pos_{rnd}"
            if click_key not in st.session_state:
                st.session_state[click_key] = None

            # Construire la carte Plotly avec une grille de points invisibles cliquables
            # Grille de 37x73 = ~2700 points couvrant le globe
            grid_lats = []
            grid_lons = []
            for lat_i in range(-85, 90, 5):
                for lon_i in range(-180, 181, 5):
                    grid_lats.append(lat_i)
                    grid_lons.append(lon_i)

            fig_click = _go_jeu.Figure()

            # Grille cliquable (points transparents)
            fig_click.add_trace(_go_jeu.Scattergeo(
                lat=grid_lats, lon=grid_lons,
                mode="markers",
                marker=dict(size=8, color="rgba(0,0,0,0)", opacity=0),
                hoverinfo="text",
                hovertext=[f"{la}°N, {lo}°E" for la, lo in zip(grid_lats, grid_lons)],
                hoverlabel=dict(
                    bgcolor="#0d0820", bordercolor="#22d3ee",
                    font=dict(family="Outfit, sans-serif", size=11, color="#22d3ee")),
                showlegend=False,
            ))

            # Afficher le marker si on a déjà cliqué
            if st.session_state[click_key]:
                prev = st.session_state[click_key]
                fig_click.add_trace(_go_jeu.Scattergeo(
                    lat=[prev["lat"]], lon=[prev["lng"]],
                    mode="markers",
                    marker=dict(size=18, color="#22d3ee", opacity=0.95,
                                line=dict(width=3, color="white"),
                                symbol="circle"),
                    hoverinfo="text",
                    hovertext=[f"📍 {prev['lat']}°N · {prev['lng']}°E"],
                    showlegend=False,
                ))

            fig_click.update_geos(
                projection_type="natural earth",
                showland=True, landcolor="#1e1035",
                showocean=True, oceancolor="#0d0820",
                showcoastlines=True, coastlinecolor="rgba(34,211,238,0.2)",
                showcountries=True, countrycolor="rgba(34,211,238,0.12)",
                showframe=False, showlakes=False,
                bgcolor="rgba(0,0,0,0)",
                lataxis_range=[-65, 85],
            )
            fig_click.update_layout(
                height=480,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                geo=dict(bgcolor="rgba(0,0,0,0)"),
                dragmode=False,
                clickmode="event",
            )

            # Cadre animé autour de la carte
            st.markdown("""
<div class="map-frame-outer" style="margin:0 0 0.5rem">
  <div class="map-frame-inner">
    <div class="map-corner tl"></div><div class="map-corner tr"></div>
    <div class="map-corner bl"></div><div class="map-corner br"></div>
""", unsafe_allow_html=True)

            # on_select capture le clic sur un point de la grille
            event = st.plotly_chart(
                fig_click, use_container_width=True,
                config={"displayModeBar": False, "scrollZoom": False,
                        "doubleClick": False, "staticPlot": False},
                on_select="rerun",
                selection_mode="points",
                key=f"jeu_plotly_{rnd}",
            )

            st.markdown("</div></div>", unsafe_allow_html=True)

            # Récupérer le clic depuis l'event Plotly
            if event and event.selection and event.selection.points:
                pt = event.selection.points[0]
                st.session_state[click_key] = {
                    "lat": round(pt["lat"], 1),
                    "lng": round(pt["lon"], 1),
                }

            pos = st.session_state[click_key]

            if pos:
                g_lat, g_lon = pos["lat"], pos["lng"]
                st.markdown(f"""
<div style="text-align:center;margin:0.5rem 0">
  <span style="font-family:Outfit,sans-serif;font-size:1.05rem;font-weight:700;color:#22d3ee">
    📍 {g_lat:.1f}°N · {g_lon:.1f}°E
  </span>
</div>""", unsafe_allow_html=True)
                if st.button("Valider cette position", key=f"jeu_submit_{rnd}",
                             use_container_width=True):
                    st.session_state.jeu_click   = (g_lat, g_lon)
                    st.session_state.jeu_waiting = True
                    st.rerun()
            else:
                st.markdown("""
<div style="text-align:center;margin:0.6rem 0">
  <span style="font-family:Outfit,sans-serif;font-size:0.85rem;color:#4a3870;font-style:italic">
    Clique sur la carte pour placer ton marqueur…
  </span>
</div>""", unsafe_allow_html=True)

        else:
            # resultat
            g_lat, g_lon = click
            dist_km = _haversine(true_lat, true_lon, g_lat, g_lon)
            pts     = _dist_to_pts(dist_km)

            if dist_km < 500:    res_color, res_emoji, res_msg = "#22d3ee", "🎯", "Excellent !"
            elif dist_km < 1500: res_color, res_emoji, res_msg = "#a78bfa", "✅", "Bien joué !"
            elif dist_km < 3000: res_color, res_emoji, res_msg = "#f59e0b", "🟡", "Pas mal…"
            else:                res_color, res_emoji, res_msg = "#ef4444", "❌", "Raté !"

            fig_res = _go.Figure()
            fig_res.add_trace(_go.Scattergeo(
                lat=[g_lat, true_lat], lon=[g_lon, true_lon], mode="lines",
                line=dict(width=2, color=res_color, dash="dot"), opacity=0.7,
                hoverinfo="none", showlegend=False))
            fig_res.add_trace(_go.Scattergeo(
                lat=[g_lat], lon=[g_lon], mode="markers+text",
                marker=dict(size=14, color=res_color, opacity=0.9, symbol="x",
                            line=dict(width=2, color="white")),
                text=["Ta réponse"], textposition="top center",
                textfont=dict(family="Outfit", size=11, color=res_color),
                hoverinfo="none", showlegend=False))
            fig_res.add_trace(_go.Scattergeo(
                lat=[true_lat], lon=[true_lon], mode="markers+text",
                marker=dict(size=16, color="#22d3ee", opacity=1.0, symbol="star",
                            line=dict(width=1.5, color="white")),
                text=[lang_row["nom"]], textposition="top center",
                textfont=dict(family="Outfit", size=12, color="#22d3ee"),
                hoverinfo="none", showlegend=False))
            fig_res.update_geos(
                projection_type="natural earth",
                showland=True, landcolor="#1e1035", showocean=True, oceancolor="#0d0820",
                showcoastlines=True, coastlinecolor="rgba(34,211,238,0.2)",
                showcountries=True, countrycolor="rgba(34,211,238,0.1)",
                showframe=False, bgcolor="rgba(0,0,0,0)", lataxis_range=[-65, 85])
            fig_res.update_layout(
                height=400, margin=dict(l=0,r=0,t=0,b=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                geo=dict(bgcolor="rgba(0,0,0,0)"))

            st.markdown("""
<div class="map-frame-outer" style="margin:0 0 0.8rem">
  <div class="map-frame-inner">
    <div class="map-corner tl"></div><div class="map-corner tr"></div>
    <div class="map-corner bl"></div><div class="map-corner br"></div>
""", unsafe_allow_html=True)
            st.plotly_chart(fig_res, use_container_width=True,
                            config={"displayModeBar": False}, key=f"jeu_res_{rnd}")
            st.markdown("</div></div>", unsafe_allow_html=True)

            st.markdown(f"""
<div style="background:rgba(255,255,255,0.04);border:1px solid {res_color}44;
  border-left:4px solid {res_color};border-radius:14px;
  padding:1rem 1.5rem;margin-bottom:1rem;
  display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem">
  <div>
    <p style="font-family:'Outfit',sans-serif;font-size:1.1rem;font-weight:800;color:{res_color};margin:0">{res_emoji} {res_msg}</p>
    <p style="font-family:'Fraunces',serif;font-size:0.85rem;color:#8b7ac9;margin:0.2rem 0 0;font-style:italic">
      {lang_row['nom']} se parle en <b style="color:#f1f0ff">{lang_row['pays']}</b> · {lang_row['region']}</p>
    <p style="font-family:'Outfit',sans-serif;font-size:0.78rem;color:#6b5fa8;margin:0.3rem 0 0">{lang_row['notes']}</p>
  </div>
  <div style="text-align:right">
    <p style="font-family:'Outfit',sans-serif;font-size:0.72rem;color:#6b5fa8;margin:0;text-transform:uppercase;letter-spacing:.05em">Distance</p>
    <p style="font-family:'Outfit',sans-serif;font-size:1.5rem;font-weight:800;color:{res_color};margin:0">{int(dist_km):,} km</p>
    <p style="font-family:'Outfit',sans-serif;font-size:1rem;font-weight:700;color:#f1f0ff;margin:0">+{pts} pts</p>
  </div>
</div>""", unsafe_allow_html=True)

            next_label = "Manche suivante ➛" if rnd < ROUNDS_TOTAL - 1 else "🏆 Voir mes résultats"
            if st.button(next_label, key=f"jeu_next_{rnd}", use_container_width=True):
                st.session_state.jeu_score  += pts
                st.session_state.jeu_guesses.append(
                    (lang_row["nom"], dist_km, pts, g_lat, g_lon))
                st.session_state.jeu_round   += 1
                st.session_state.jeu_waiting = False
                st.session_state.jeu_click   = None
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
# PAGE : RÉSEAU DE SIMILARITÉS
# layout Kamada-Kawai codé from scratch (pas de networkx)
# c'est O(n³) donc ça rame au dessus de 120 noeuds, j'ai pas trouvé mieux
# ══════════════════════════════════════════════
elif page == "reseau":

    ctrl1, ctrl2, ctrl3 = st.columns([2, 2, 2])
    with ctrl1:
        familles_dispo = ["Toutes"] + sorted(df["famille"].unique().tolist())
        fam_filter = st.selectbox("Famille", familles_dispo, key="reseau_fam")
    with ctrl2:
        regions_dispo = ["Toutes"] + sorted(df["region"].unique().tolist())
        reg_filter = st.selectbox("Région", regions_dispo, key="reseau_reg")
    with ctrl3:
        seuil = st.slider("Seuil de similarité", 0.1, 0.9, 0.30, 0.05, key="reseau_seuil",
                          help="0.55 = même famille uniquement · 0.75 = famille + script")

    df_net = df.copy()
    if fam_filter != "Toutes":
        df_net = df_net[df_net["famille"] == fam_filter]
    if reg_filter != "Toutes":
        df_net = df_net[df_net["region"] == reg_filter]
    df_net = df_net.nlargest(120, "locuteurs_M").reset_index(drop=True)
    rows_net = df_net.to_dict("records")
    n_net = len(rows_net)

    local_scores = {}
    for i in range(n_net):
        for j in range(i+1, n_net):
            a, b = rows_net[i], rows_net[j]
            s = 0.0
            if a["famille"] == b["famille"]: s += 0.70
            sa = set(a["script"].replace(" ","").split("/"))
            sb = set(b["script"].replace(" ","").split("/"))
            if sa & sb: s += 0.30
            if s >= seuil:
                local_scores[(i, j)] = round(min(s, 1.0), 3)

    n_edges  = len(local_scores)
    avg_deg  = round(2 * n_edges / max(n_net, 1), 1)

    st.markdown(f"""
<div style="display:flex;gap:1rem;margin-bottom:1rem;flex-wrap:wrap">
  <div style="background:rgba(99,102,241,0.12);border:1px solid rgba(99,102,241,0.3);border-radius:12px;padding:0.5rem 1rem">
    <span style="font-size:1.4rem;font-weight:800;color:#818cf8;font-family:'Outfit',sans-serif">{n_net}</span>
    <span style="font-size:0.72rem;color:#6b5fa8;margin-left:6px;text-transform:uppercase;letter-spacing:.05em;font-family:'Outfit',sans-serif">nœuds</span>
  </div>
  <div style="background:rgba(236,72,153,0.12);border:1px solid rgba(236,72,153,0.3);border-radius:12px;padding:0.5rem 1rem">
    <span style="font-size:1.4rem;font-weight:800;color:#f472b6;font-family:'Outfit',sans-serif">{n_edges}</span>
    <span style="font-size:0.72rem;color:#6b5fa8;margin-left:6px;text-transform:uppercase;letter-spacing:.05em;font-family:'Outfit',sans-serif">arêtes</span>
  </div>
  <div style="background:rgba(20,184,166,0.12);border:1px solid rgba(20,184,166,0.3);border-radius:12px;padding:0.5rem 1rem">
    <span style="font-size:1.4rem;font-weight:800;color:#2dd4bf;font-family:'Outfit',sans-serif">{avg_deg}</span>
    <span style="font-size:0.72rem;color:#6b5fa8;margin-left:6px;text-transform:uppercase;letter-spacing:.05em;font-family:'Outfit',sans-serif">degré moyen</span>
  </div>
  <div style="background:rgba(245,158,11,0.12);border:1px solid rgba(245,158,11,0.3);border-radius:12px;padding:0.5rem 1rem">
    <span style="font-size:1.4rem;font-weight:800;color:#fbbf24;font-family:'Outfit',sans-serif">{df_net['famille'].nunique()}</span>
    <span style="font-size:0.72rem;color:#6b5fa8;margin-left:6px;text-transform:uppercase;letter-spacing:.05em;font-family:'Outfit',sans-serif">familles</span>
  </div>
</div>""", unsafe_allow_html=True)

    def kamada_kawai_layout(n, edges):
        import random
        random.seed(42)
        adj = [[0.0]*n for _ in range(n)]
        for (i,j), w in edges.items():
            adj[i][j] = w; adj[j][i] = w
        INF = float("inf")
        dist_graph = [[INF]*n for _ in range(n)]
        for i in range(n): dist_graph[i][i] = 0.0
        for (i,j), w in edges.items():
            d = 1.0 / (w + 1e-9)
            dist_graph[i][j] = d; dist_graph[j][i] = d
        for k in range(n):
            for i in range(n):
                for j in range(n):
                    if dist_graph[i][k] + dist_graph[k][j] < dist_graph[i][j]:
                        dist_graph[i][j] = dist_graph[i][k] + dist_graph[k][j]
        max_d = max(dist_graph[i][j] for i in range(n) for j in range(n) if dist_graph[i][j] < INF) or 1.0
        L = 1.0
        pos = {}
        for i in range(n):
            a = 2 * math.pi * i / max(n, 1)
            pos[i] = [math.cos(a)*2 + random.uniform(-0.05,0.05), math.sin(a)*2 + random.uniform(-0.05,0.05)]
        K_strength = 1.0
        for _iter in range(200):
            max_delta = -1; best_m = 0
            for m in range(n):
                dEx = dEy = 0.0
                for i in range(n):
                    if i == m: continue
                    d_mi = dist_graph[m][i]
                    if d_mi == INF: continue
                    l_mi = L * d_mi / max_d
                    k_mi = K_strength / (d_mi**2 + 1e-9)
                    dx = pos[m][0] - pos[i][0]; dy = pos[m][1] - pos[i][1]
                    dist_euc = math.sqrt(dx*dx + dy*dy) + 1e-9
                    coeff = k_mi * (1 - l_mi/dist_euc)
                    dEx += coeff * dx; dEy += coeff * dy
                delta = math.sqrt(dEx*dEx + dEy*dEy)
                if delta > max_delta: max_delta = delta; best_m = m
            m = best_m
            for _inner in range(50):
                dEx = dEy = d2Ex = d2Ey = dExy = 0.0
                for i in range(n):
                    if i == m: continue
                    d_mi = dist_graph[m][i]
                    if d_mi == INF: continue
                    l_mi = L * d_mi / max_d; k_mi = K_strength / (d_mi**2 + 1e-9)
                    dx = pos[m][0] - pos[i][0]; dy = pos[m][1] - pos[i][1]
                    dist_euc = math.sqrt(dx*dx + dy*dy) + 1e-9
                    dist3 = dist_euc**3; coeff = k_mi * (1 - l_mi/dist_euc)
                    dEx += coeff * dx; dEy += coeff * dy
                    d2Ex += k_mi * (1 - l_mi*dy*dy/dist3)
                    d2Ey += k_mi * (1 - l_mi*dx*dx/dist3)
                    dExy += k_mi * l_mi*dx*dy/dist3
                det = d2Ex*d2Ey - dExy*dExy
                if abs(det) < 1e-12: break
                dx_step = (dExy*dEy - d2Ey*dEx) / det
                dy_step = (dExy*dEx - d2Ex*dEy) / det
                pos[m][0] += dx_step; pos[m][1] += dy_step
                if math.sqrt(dx_step**2+dy_step**2) < 1e-4: break
            if max_delta < 1e-3: break
        connected = set()
        for (i,j) in edges: connected.add(i); connected.add(j)
        outer_r = 3.5; outer_isolated = [i for i in range(n) if i not in connected]
        for k, i in enumerate(outer_isolated):
            a = 2 * math.pi * k / max(len(outer_isolated), 1)
            pos[i] = [outer_r*math.cos(a), outer_r*math.sin(a)]
        return pos

    if n_net == 0:
        st.warning("Aucune langue pour ces filtres.")
    else:
        with st.spinner("Calcul Kamada-Kawai…"):
            pos = kamada_kawai_layout(n_net, local_scores)

        import plotly.graph_objects as go_px

        edge_traces = []
        score_vals = list(local_scores.values()) or [0, 1]
        s_min, s_max = min(score_vals), max(score_vals)
        for (i, j), w in local_scores.items():
            x0, y0 = pos[i]; x1, y1 = pos[j]
            norm = (w - s_min) / (s_max - s_min + 1e-9)
            opacity = 0.10 + norm * 0.55; width = 0.4 + norm * 3.0
            fa, fb = rows_net[i]["famille"], rows_net[j]["famille"]
            edge_color = FAMILLE_COLORS.get(fa, "#a78bfa") if fa == fb else "#6366f1"
            edge_traces.append(go_px.Scatter(
                x=[x0, x1, None], y=[y0, y1, None], mode="lines",
                line=dict(width=width, color=edge_color), opacity=opacity,
                hoverinfo="none", showlegend=False))

        degrees = [0]*n_net
        for (i, j) in local_scores: degrees[i] += 1; degrees[j] += 1

        node_x = [pos[i][0] for i in range(n_net)]
        node_y = [pos[i][1] for i in range(n_net)]
        node_colors = [FAMILLE_COLORS.get(r["famille"],"#a78bfa") for r in rows_net]
        node_sizes = [max(8, min(52, math.sqrt(float(r["locuteurs_M"])+1)*6.2)) for r in rows_net]
        node_border_colors = [
            "rgba(255,255,255,0.8)" if r["statut"]=="safe"
            else "#fbbf24" if r["statut"]=="vulnerable"
            else "#f97316" if r["statut"]=="endangered"
            else "#ef4444" for r in rows_net]
        hover_node = [
            "<b>{}</b><br><span style='color:{}'>{}</span><br>👥 {}M · {}<br>✍ {}<br>{}<br>🔗 {} connexions".format(
                r["nom"], FAMILLE_COLORS.get(r["famille"],"#a78bfa"), r["famille"],
                r["locuteurs_M"], r["region"], r["script"], r["statut_label"], degrees[i])
            for i, r in enumerate(rows_net)]
        node_labels = [r["nom"] if r["locuteurs_M"] >= 10 else "" for r in rows_net]

        node_trace = go_px.Scatter(
            x=node_x, y=node_y, mode="markers+text",
            marker=dict(size=node_sizes, color=node_colors, opacity=0.93,
                        line=dict(width=2.0, color=node_border_colors), sizemode="diameter"),
            text=node_labels, textposition="top center",
            textfont=dict(family="Outfit, sans-serif", size=9, color="rgba(230,220,255,0.9)"),
            hovertext=hover_node, hoverinfo="text",
            hoverlabel=dict(bgcolor="#0a0318", bordercolor="#a78bfa",
                            font=dict(family="Outfit, sans-serif", size=12, color="#f1f0ff"), namelength=0),
            showlegend=False)

        pad = 0.6
        x_range = [min(node_x)-pad, max(node_x)+pad] if node_x else [-4, 4]
        y_range = [min(node_y)-pad, max(node_y)+pad] if node_y else [-4, 4]

        fig_net = go_px.Figure(data=edge_traces + [node_trace])
        fig_net.update_layout(
            height=680, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(5,1,15,0.95)",
            margin=dict(l=8, r=8, t=8, b=8),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, showline=False, range=x_range),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, showline=False, scaleanchor="x", range=y_range),
            hovermode="closest", dragmode="pan")

        st.markdown("""
<div class="map-frame-outer" style="margin:0 0 1.2rem">
  <div class="map-frame-inner">
    <div class="map-corner tl"></div><div class="map-corner tr"></div>
    <div class="map-corner bl"></div><div class="map-corner br"></div>
""", unsafe_allow_html=True)
        st.plotly_chart(fig_net, use_container_width=True,
                        config={"displayModeBar": True, "modeBarButtonsToRemove": ["toImage","select2d","lasso2d"],
                                "displaylogo": False, "scrollZoom": True})
        st.markdown("</div></div>", unsafe_allow_html=True)

        familles_presentes = sorted(df_net["famille"].unique().tolist())
        legend_html = '<div style="display:flex;flex-wrap:wrap;gap:0.5rem;margin-bottom:1.2rem">'
        for fam in familles_presentes:
            c = FAMILLE_COLORS.get(fam, "#a78bfa"); n_fam = len(df_net[df_net["famille"]==fam])
            legend_html += (
                f'<div style="display:inline-flex;align-items:center;gap:6px;'
                f'background:rgba(255,255,255,0.05);border:1px solid {c}44;border-radius:20px;padding:3px 10px">'
                f'<div style="width:9px;height:9px;border-radius:50%;background:{c};box-shadow:0 0 6px {c}88"></div>'
                f'<span style="font-family:\'Outfit\',sans-serif;font-size:0.72rem;color:{c};font-weight:600">{fam}</span>'
                f'<span style="font-family:\'Outfit\',sans-serif;font-size:0.65rem;color:#4a3870">({n_fam})</span></div>')
        st.markdown(legend_html + "</div>", unsafe_allow_html=True)

        st.markdown("""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:0.8rem">
  <div style="flex:1;height:1px;background:linear-gradient(90deg,rgba(99,102,241,0.4),transparent)"></div>
  <span style="font-family:'Outfit',sans-serif;font-size:0.6rem;font-weight:700;
    letter-spacing:0.14em;color:#4a3870;text-transform:uppercase">TOP NŒUDS · CENTRALITÉ DE DEGRÉ</span>
  <div style="flex:1;height:1px;background:linear-gradient(90deg,transparent,rgba(99,102,241,0.4))"></div>
</div>""", unsafe_allow_html=True)

        top_nodes = sorted(range(n_net), key=lambda i: degrees[i], reverse=True)[:8]
        medal_icons = ["🥇","🥈","🥉","④","⑤","⑥","⑦","⑧"]
        top_html = '<div style="display:flex;flex-wrap:wrap;gap:0.6rem">'
        for rank, idx in enumerate(top_nodes):
            r = rows_net[idx]; c = FAMILLE_COLORS.get(r["famille"],"#a78bfa")
            top_html += (
                f'<div style="background:rgba(255,255,255,0.05);border:1px solid {c}33;'
                f'border-left:3px solid {c};border-radius:12px;padding:0.6rem 0.9rem;min-width:140px">'
                f'<div style="font-size:0.7rem;color:#4a3870">{medal_icons[rank]}</div>'
                f'<div style="font-family:\'Outfit\',sans-serif;font-size:0.88rem;font-weight:700;color:#f1f0ff">{r["nom"]}</div>'
                f'<div style="font-family:\'Outfit\',sans-serif;font-size:0.7rem;color:{c}">{r["famille"]}</div>'
                f'<div style="font-family:\'Outfit\',sans-serif;font-size:0.78rem;color:#a78bfa;margin-top:3px">🔗 {degrees[idx]} liens</div></div>')
        st.markdown(top_html + "</div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------
# PAGE : FICHES
# -------------------------------------------------------
elif page == "fiches":
    st.markdown('<div class="page-wrap" style="padding:0.5rem 3vw 2rem">', unsafe_allow_html=True)

    st.markdown("""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:1.2rem;animation:fadeUp 0.4s ease">
  <span style="font-size:1.8rem">📚</span>
  <h2 style="font-family:'Outfit',sans-serif;font-size:1.5rem;font-weight:800;color:#f1f0ff;margin:0">Fiches Langues</h2>
</div>""", unsafe_allow_html=True)

    sc1, sc2 = st.columns([3, 1])
    with sc1:
        search = st.text_input("", placeholder="🔍  Rechercher… ex : Darija, Occitan, Aïnou")
    with sc2:
        sort_by = st.selectbox("Trier", ["Locuteurs ↓", "Nom A-Z", "Statut"])

    results = df.copy()
    if search:
        results = results[results["nom"].str.contains(search, case=False, na=False)]
    order_map = {"safe":0,"vulnerable":1,"endangered":2,"critically_endangered":3}
    if sort_by == "Locuteurs ↓":  results = results.sort_values("locuteurs_M", ascending=False)
    elif sort_by == "Nom A-Z":    results = results.sort_values("nom")
    else:                          results = results.sort_values("statut", key=lambda x: x.map(order_map))

    st.markdown(f'<p style="color:#8b7ac9;font-size:0.8rem;font-family:Outfit,sans-serif">{len(results)} entrée(s) · {len(results[results["type"]=="dialecte"])} dialectes</p>', unsafe_allow_html=True)

    it = results.iterrows(); done = False; delay = 0
    while not done:
        cols3 = st.columns(3)
        for ci in range(3):
            try:
                _, row = next(it)
                bs = STATUT_BADGE.get(row["statut"], "b-safe")
                fc = FAMILLE_COLORS.get(row["famille"], "#a78bfa")
                dialect_badge = '<span class="badge b-dialect">dialecte</span>' if row["type"] == "dialecte" else ""
                with cols3[ci]:
                    st.markdown(f"""
<div class="lm-card" style="border-top:3px solid {fc};animation-delay:{delay*0.04}s">
  <p style="font-family:'Outfit',sans-serif;font-size:0.95rem;font-weight:700;margin:0 0 0.5rem;color:#f1f0ff">{row['nom']}</p>
  <div style="margin-bottom:0.5rem"><span class="badge {bs}">{row['statut_label']}</span>{dialect_badge}</div>
  <div style="display:flex;flex-wrap:wrap;gap:3px;margin-bottom:0.4rem">
    <span class="chip" style="color:{fc}">🌿 {row['famille']}</span>
    <span class="chip">👥 {row['locuteurs_M']}M</span>
    <span class="chip">✍ {row['script']}</span>
  </div>
  <p style="font-size:0.8rem;color:#8b7ac9;margin:0.1rem 0">🏳 {row['pays']}</p>
  <p style="font-size:0.8rem;font-style:italic;color:#6b5f9e;margin:0.5rem 0 0;
     border-top:1px solid rgba(167,139,250,0.15);padding-top:0.4rem;
     line-height:1.55;font-family:'Fraunces',serif">{row['notes']}</p>
</div>""", unsafe_allow_html=True)
                delay += 1
            except StopIteration:
                done = True; break
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
# PAGE : STATS
# tout calculé from scratch sans numpy/sklearn (montre qu'on comprend les maths)
# descriptives, distribution, k-means, regression OLS, shannon
# ══════════════════════════════════════════════
elif page == "stats":
    st.markdown('<div class="page-wrap" style="padding:0.5rem 3vw 2rem">', unsafe_allow_html=True)

    st.markdown("""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:1.2rem;animation:fadeUp 0.4s ease">
  <span style="font-size:1.8rem">📊</span>
  <h2 style="font-family:'Outfit',sans-serif;font-size:1.5rem;font-weight:800;color:#f1f0ff;margin:0">Statistiques et Analyse</h2>
</div>""", unsafe_allow_html=True)

    m1,m2,m3,m4,m5 = st.columns(5)
    with m1: st.metric("Langues", str(len(df[df["type"]=="langue"])))
    with m2: st.metric("Dialectes", str(len(df[df["type"]=="dialecte"])))
    with m3: st.metric("Locuteurs", f"{df['locuteurs_M'].sum():.0f} M")
    with m4: st.metric("Familles", str(df["famille"].nunique()))
    with m5: st.metric("En danger", str(len(df[df["statut"].isin(["endangered","critically_endangered"])])))

    st.markdown('<div style="height:1.5rem"></div>', unsafe_allow_html=True)

    ga, gb = st.columns(2)
    with ga:
        st.markdown("""<p style="font-family:'Outfit',sans-serif;font-size:0.9rem;font-weight:700;
          color:#a78bfa;margin:0 0 1rem;text-transform:uppercase;letter-spacing:0.06em">Top familles par locuteurs (M)</p>""", unsafe_allow_html=True)
        fam_sum = df.groupby("famille")["locuteurs_M"].sum().sort_values(ascending=False).head(10)
        max_val = fam_sum.max()
        gradient_pairs = [
            ("#7c3aed","#a78bfa"),("#ec4899","#f9a8d4"),("#14b8a6","#99f6e4"),
            ("#f59e0b","#fde68a"),("#38bdf8","#bae6fd"),("#8b5cf6","#c4b5fd"),
            ("#10b981","#6ee7b7"),("#f97316","#fdba74"),("#06b6d4","#a5f3fc"),("#6366f1","#a5b4fc")]
        bars_html = ""
        for i,(fam,val) in enumerate(fam_sum.items()):
            pct = val/max_val*100; c1,c2 = gradient_pairs[i % len(gradient_pairs)]
            bars_html += f"""
<div class="stat-bar-wrap" style="animation-delay:{i*0.06}s">
  <div class="stat-bar-label">
    <span style="color:#c4b5fd;font-weight:500">{fam}</span>
    <span style="color:#a78bfa;font-weight:700">{val:.0f}M</span>
  </div>
  <div class="stat-bar-track">
    <div class="stat-bar-fill" style="width:{pct:.1f}%;background:linear-gradient(90deg,{c1},{c2});--bar-w:{pct:.1f}%;--delay:{i*0.08}s"></div>
  </div>
</div>"""
        st.markdown(bars_html, unsafe_allow_html=True)

    with gb:
        st.markdown("""<p style="font-family:'Outfit',sans-serif;font-size:0.9rem;font-weight:700;
          color:#ec4899;margin:0 0 1rem;text-transform:uppercase;letter-spacing:0.06em">Statut de vitalité</p>""", unsafe_allow_html=True)
        stat_counts = df["statut"].value_counts(); total = len(df)
        statut_info = [
            ("safe","Vivante","#14b8a6","#99f6e4"),("vulnerable","Vulnérable","#f59e0b","#fde68a"),
            ("endangered","En danger","#f97316","#fdba74"),("critically_endangered","Critique","#ef4444","#fca5a5")]
        donut_html = '<div style="display:flex;flex-direction:column;gap:0.8rem">'
        for idx,(sk,sl,c1,c2) in enumerate(statut_info):
            n = stat_counts.get(sk, 0); pct = n / total * 100
            donut_html += f"""
<div style="display:flex;align-items:center;gap:10px">
  <div style="width:42px;height:42px;border-radius:50%;flex-shrink:0;
    background:conic-gradient({c1} 0% {pct:.1f}%, rgba(255,255,255,0.07) {pct:.1f}% 100%);
    display:flex;align-items:center;justify-content:center">
    <div style="width:28px;height:28px;border-radius:50%;background:rgba(15,8,30,0.9)"></div>
  </div>
  <div style="flex:1">
    <div style="display:flex;justify-content:space-between;margin-bottom:3px">
      <span style="font-family:'Outfit',sans-serif;font-size:0.82rem;font-weight:600;color:{c1}">{sl}</span>
      <span style="font-family:'Outfit',sans-serif;font-size:0.82rem;color:#8b7ac9">{n} ({pct:.0f}%)</span>
    </div>
    <div style="height:6px;background:rgba(255,255,255,0.07);border-radius:3px;overflow:hidden">
      <div style="height:100%;width:{pct:.1f}%;background:linear-gradient(90deg,{c1},{c2});
        border-radius:3px;animation:bar-grow 1s cubic-bezier(.34,1.2,.64,1) both;
        animation-delay:{0.1+idx*0.12}s;--bar-w:{pct:.1f}%"></div>
    </div>
  </div>
</div>"""
        st.markdown(donut_html + "</div>", unsafe_allow_html=True)

    st.markdown('<div style="height:1.5rem"></div>', unsafe_allow_html=True)

    st.markdown("""<p style="font-family:'Outfit',sans-serif;font-size:0.9rem;font-weight:700;
      color:#38bdf8;margin:0 0 1rem;text-transform:uppercase;letter-spacing:0.06em">Top 10 locuteurs (millions)</p>""", unsafe_allow_html=True)

    top10 = df.nlargest(10,"locuteurs_M"); max_loc = top10["locuteurs_M"].max()
    medal_t = ["🥇","🥈","🥉"] + [f"{i}." for i in range(4,11)]
    grad_top = [("#7c3aed","#ec4899"),("#5b21b6","#a78bfa"),("#14b8a6","#38bdf8"),
                ("#ec4899","#f59e0b"),("#8b5cf6","#14b8a6"),("#f59e0b","#f97316"),
                ("#38bdf8","#6366f1"),("#6366f1","#ec4899"),("#14b8a6","#22d3ee"),("#f97316","#fbbf24")]
    top10_html = ""
    for i,(_,row) in enumerate(top10.iterrows()):
        pct = row["locuteurs_M"]/max_loc*100; c1,c2 = grad_top[i]
        top10_html += f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:0.55rem;animation:fadeUp 0.4s ease {i*0.05}s both">
  <span style="font-size:1rem;width:28px;text-align:center;flex-shrink:0">{medal_t[i]}</span>
  <span style="font-family:'Outfit',sans-serif;font-size:0.85rem;font-weight:600;color:#f1f0ff;
    width:160px;flex-shrink:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{row['nom']}</span>
  <div style="flex:1;height:20px;background:rgba(255,255,255,0.07);border-radius:10px;overflow:hidden">
    <div style="height:100%;width:{pct:.1f}%;background:linear-gradient(90deg,{c1},{c2});border-radius:10px;
      animation:bar-grow 1.2s cubic-bezier(.34,1.2,.64,1) {i*0.06}s both;--bar-w:{pct:.1f}%"></div>
  </div>
  <span style="font-family:'Outfit',sans-serif;font-size:0.82rem;font-weight:700;color:#a78bfa;width:60px;text-align:right;flex-shrink:0">{row['locuteurs_M']:.0f}M</span>
</div>"""
    st.markdown(top10_html, unsafe_allow_html=True)

    st.markdown('<div style="height:1.5rem"></div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════
    # ANALYSE AVANCÉE : stats descriptives, distribution, clustering, regression
    # tout calculé from scratch sans sklearn/scipy (montre qu'on sait ce qu'on fait)
    # ══════════════════════════════════════════════

    st.markdown("""<p style="font-family:'Outfit',sans-serif;font-size:0.9rem;font-weight:700;
      color:#c4b5fd;margin:0 0 0.8rem;text-transform:uppercase;letter-spacing:0.06em">Analyse statistique avancée</p>""", unsafe_allow_html=True)

    # --- Statistiques descriptives étendues ---
    loc_vals = sorted(df["locuteurs_M"].tolist())
    n_obs = len(loc_vals)
    mean_v = sum(loc_vals) / n_obs
    median_v = loc_vals[n_obs // 2] if n_obs % 2 else (loc_vals[n_obs//2 - 1] + loc_vals[n_obs//2]) / 2
    variance_v = sum((x - mean_v)**2 for x in loc_vals) / n_obs
    std_v = math.sqrt(variance_v)
    # skewness (asymétrie) et kurtosis (aplatissement) calculés à la main
    skew_v = sum(((x - mean_v) / std_v)**3 for x in loc_vals) / n_obs if std_v > 0 else 0
    kurt_v = sum(((x - mean_v) / std_v)**4 for x in loc_vals) / n_obs - 3 if std_v > 0 else 0
    # coefficient de variation
    cv_v = (std_v / mean_v * 100) if mean_v > 0 else 0
    # quartiles (méthode inclusive)
    q1_v = loc_vals[n_obs // 4]
    q3_v = loc_vals[3 * n_obs // 4]
    iqr_v = q3_v - q1_v

    st.markdown("""<p style="font-family:'Outfit',sans-serif;font-size:0.82rem;font-weight:600;
      color:#a78bfa;margin:0 0 0.6rem">Distribution des locuteurs (M)</p>""", unsafe_allow_html=True)

    desc_cols = st.columns(4)
    with desc_cols[0]:
        st.metric("Moyenne", f"{mean_v:.1f} M")
        st.metric("Médiane", f"{median_v:.1f} M")
    with desc_cols[1]:
        st.metric("Écart-type (σ)", f"{std_v:.1f}")
        st.metric("CV", f"{cv_v:.0f}%")
    with desc_cols[2]:
        st.metric("Skewness (γ₁)", f"{skew_v:.2f}")
        st.metric("Kurtosis (γ₂)", f"{kurt_v:.2f}")
    with desc_cols[3]:
        st.metric("IQR (Q3-Q1)", f"{iqr_v:.1f}")
        st.metric("Min / Max", f"{loc_vals[0]:.2f} / {loc_vals[-1]:.0f}")

    # interpretation skewness/kurtosis
    skew_label = "symétrique" if abs(skew_v) < 0.5 else ("asymétrie positive (queue droite)" if skew_v > 0 else "asymétrie négative (queue gauche)")
    kurt_label = "mésokurtique (normale)" if abs(kurt_v) < 1 else ("leptokurtique (pics)" if kurt_v > 0 else "platykurtique (plat)")
    st.markdown(f"""
<div class="lm-card" style="border-left:3px solid #a78bfa;margin:0.5rem 0 1.2rem">
  <p style="font-family:'Outfit',sans-serif;font-size:0.78rem;color:#c4b5fd;margin:0;line-height:1.7">
    <b style="color:#a78bfa">Interprétation :</b> La distribution est <b style="color:#ec4899">{skew_label}</b>
    (γ₁ = {skew_v:.2f}) et <b style="color:#14b8a6">{kurt_label}</b>
    (γ₂ = {kurt_v:.2f}). Le coefficient de variation de {cv_v:.0f}% indique une
    <b style="color:#f59e0b">{"forte" if cv_v > 100 else "modérée" if cv_v > 50 else "faible"} dispersion</b>
    des effectifs entre langues.
  </p>
  <hr style="border:none;border-top:1px solid rgba(167,139,250,0.15);margin:0.6rem 0"/>
  <p style="font-family:'Outfit',sans-serif;font-size:0.75rem;color:#8b7ac9;margin:0;line-height:1.7">
    <b style="color:#6b5fa8">En clair :</b> La plupart des langues ont très peu de locuteurs, et quelques-unes en ont énormément (comme le mandarin ou l'espagnol). C'est ce que montre le skewness : les données ne sont pas réparties de manière égale, elles "penchent" d'un côté.
    La médiane ({median_v:.1f}M) est bien plus basse que la moyenne ({mean_v:.1f}M), ce qui confirme que quelques géants tirent la moyenne vers le haut.
  </p>
</div>""", unsafe_allow_html=True)

    # --- Histogramme de distribution ---
    st.markdown("""<p style="font-family:'Outfit',sans-serif;font-size:0.82rem;font-weight:600;
      color:#ec4899;margin:0 0 0.6rem">Histogramme des locuteurs (classes log)</p>""", unsafe_allow_html=True)

    # bins logarithmiques (plus pertinent pour des données power-law)
    log_bins = [0, 0.1, 1, 5, 10, 50, 100, 500, 1000]
    bin_labels = ["<0.1M", "0.1-1M", "1-5M", "5-10M", "10-50M", "50-100M", "100-500M", "500M+"]
    bin_counts = [0] * len(bin_labels)
    for v in loc_vals:
        for b_idx in range(len(log_bins) - 1):
            if log_bins[b_idx] <= v < log_bins[b_idx + 1]:
                bin_counts[b_idx] += 1
                break
        else:
            bin_counts[-1] += 1

    max_bc = max(bin_counts) if bin_counts else 1
    hist_colors = ["#7c3aed","#a78bfa","#ec4899","#f9a8d4","#14b8a6","#f59e0b","#38bdf8","#ef4444"]
    hist_html = ""
    for i, (lbl, cnt) in enumerate(zip(bin_labels, bin_counts)):
        pct = cnt / max_bc * 100
        c = hist_colors[i % len(hist_colors)]
        hist_html += f"""
<div class="stat-bar-wrap" style="animation-delay:{i*0.06}s">
  <div class="stat-bar-label">
    <span style="color:#c4b5fd;font-weight:500">{lbl}</span>
    <span style="color:{c};font-weight:700">{cnt} langues</span>
  </div>
  <div class="stat-bar-track">
    <div class="stat-bar-fill" style="width:{pct:.1f}%;background:{c};--bar-w:{pct:.1f}%;--delay:{i*0.08}s"></div>
  </div>
</div>"""
    st.markdown(hist_html, unsafe_allow_html=True)

    st.markdown("""
<div class="lm-card" style="border-left:3px solid #ec4899;margin:0.5rem 0 0.8rem">
  <p style="font-family:'Outfit',sans-serif;font-size:0.75rem;color:#8b7ac9;margin:0;line-height:1.7">
    <b style="color:#6b5fa8">En clair :</b> Ce graphique montre combien de langues tombent dans chaque tranche de taille.
    On voit que la grande majorité des langues ont moins de 50 millions de locuteurs,
    et très peu dépassent les 100 millions. C'est un schéma classique en linguistique :
    beaucoup de "petites" langues, très peu de "géantes".
  </p>
</div>""", unsafe_allow_html=True)
    st.markdown("""<p style="font-family:'Outfit',sans-serif;font-size:0.82rem;font-weight:600;
      color:#14b8a6;margin:0 0 0.6rem">K-Means Clustering (k=4, from scratch)</p>
    <p style="font-family:'Fraunces',serif;font-size:0.82rem;color:#8b7ac9;font-style:italic;margin:0 0 0.8rem">
      Regroupement des langues par coordonnées géographiques (lat, lon) en 4 clusters.
      Algorithme implémenté sans bibliothèque externe.
    </p>""", unsafe_allow_html=True)

    # K-Means from scratch (convergence en ~20 itérations)
    import random as _km_rnd
    _km_rnd.seed(42)

    k_clusters = 4
    points = [(float(r["lat"]), float(r["lon"])) for _, r in df.iterrows()]
    n_pts = len(points)

    # init : choisir k centroides au hasard parmi les points
    centroids = [points[i] for i in _km_rnd.sample(range(n_pts), k_clusters)]
    labels = [0] * n_pts

    for _iteration in range(30):
        # assignation : chaque point au centroide le plus proche (distance euclidienne)
        new_labels = []
        for (px, py) in points:
            dists = [math.sqrt((px - cx)**2 + (py - cy)**2) for (cx, cy) in centroids]
            new_labels.append(dists.index(min(dists)))
        # convergence ?
        if new_labels == labels:
            break
        labels = new_labels
        # mise a jour des centroides
        for c in range(k_clusters):
            members = [(points[i][0], points[i][1]) for i in range(n_pts) if labels[i] == c]
            if members:
                centroids[c] = (
                    sum(m[0] for m in members) / len(members),
                    sum(m[1] for m in members) / len(members),
                )

    # inertie (WCSS) pour évaluer la qualité
    wcss = sum(
        (points[i][0] - centroids[labels[i]][0])**2 +
        (points[i][1] - centroids[labels[i]][1])**2
        for i in range(n_pts)
    )

    cluster_colors = ["#a78bfa", "#ec4899", "#14b8a6", "#f59e0b"]
    cluster_names = ["Cluster A", "Cluster B", "Cluster C", "Cluster D"]

    # stats par cluster
    cl_html = '<div style="display:flex;gap:0.7rem;flex-wrap:wrap;margin-bottom:0.8rem">'
    for c in range(k_clusters):
        members_df = df.iloc[[i for i in range(n_pts) if labels[i] == c]]
        n_c = len(members_df)
        avg_loc = members_df["locuteurs_M"].mean() if n_c > 0 else 0
        top_lang = members_df.nlargest(1, "locuteurs_M")["nom"].values[0] if n_c > 0 else "-"
        cc = cluster_colors[c]
        cl_html += f"""
<div class="corr-card" style="border-left-color:{cc};flex:1;min-width:140px">
  <p style="font-family:'Outfit',sans-serif;font-size:0.72rem;font-weight:700;color:{cc};margin:0;text-transform:uppercase;letter-spacing:.05em">{cluster_names[c]}</p>
  <p style="font-family:'Outfit',sans-serif;font-size:1.6rem;font-weight:800;color:#f1f0ff;margin:0.2rem 0">{n_c}</p>
  <p style="font-size:0.7rem;color:#8b7ac9;margin:0">moy. {avg_loc:.0f}M loc.</p>
  <p style="font-size:0.68rem;color:#6b5fa8;margin:0.2rem 0 0;font-style:italic">{top_lang}</p>
</div>"""
    cl_html += '</div>'
    st.markdown(cl_html, unsafe_allow_html=True)

    st.markdown(f"""
<div style="font-family:'Outfit',sans-serif;font-size:0.75rem;color:#4a3870;margin-bottom:0.8rem">
  WCSS (inertie intra-cluster) = <b style="color:#14b8a6">{wcss:.0f}</b> · {_iteration+1} itérations · k = {k_clusters}
</div>""", unsafe_allow_html=True)

    # scatter chart des clusters
    df_clust = df[["lat", "lon", "nom", "famille"]].copy()
    df_clust["Cluster"] = [cluster_names[l] for l in labels]
    try:
        st.scatter_chart(df_clust, x="lon", y="lat", color="Cluster", height=300, use_container_width=True)
    except Exception:
        pass

    st.markdown("""
<div class="lm-card" style="border-left:3px solid #14b8a6;margin:0.5rem 0 1rem">
  <p style="font-family:'Outfit',sans-serif;font-size:0.75rem;color:#8b7ac9;margin:0;line-height:1.7">
    <b style="color:#6b5fa8">En clair :</b> L'algorithme K-Means regroupe automatiquement les langues
    en 4 "familles géographiques" selon leur position sur le globe. C'est comme demander à un ordinateur
    de tracer des frontières naturelles entre zones linguistiques, sans lui dire à l'avance où elles sont.
    Le chiffre WCSS mesure la qualité du regroupement : plus il est bas, mieux les langues d'un même
    groupe sont proches les unes des autres.
  </p>
</div>"""  , unsafe_allow_html=True)

    # --- Régression linéaire simple (from scratch) ---
    st.markdown("""<p style="font-family:'Outfit',sans-serif;font-size:0.82rem;font-weight:600;
      color:#38bdf8;margin:0 0 0.6rem">Régression linéaire (moindres carrés ordinaires)</p>
    <p style="font-family:'Fraunces',serif;font-size:0.82rem;color:#8b7ac9;font-style:italic;margin:0 0 0.8rem">
      Prédiction du nombre de locuteurs en fonction de la latitude.
      Coefficients calculés par la méthode OLS sans bibliothèque.
    </p>""", unsafe_allow_html=True)

    xs_reg = df["lat"].tolist()
    ys_reg = df["locuteurs_M"].tolist()
    n_reg = len(xs_reg)
    mx_r = sum(xs_reg) / n_reg
    my_r = sum(ys_reg) / n_reg
    ss_xy = sum((xs_reg[i] - mx_r) * (ys_reg[i] - my_r) for i in range(n_reg))
    ss_xx = sum((xs_reg[i] - mx_r)**2 for i in range(n_reg))
    beta_1 = ss_xy / ss_xx if ss_xx != 0 else 0
    beta_0 = my_r - beta_1 * mx_r
    # R² (coefficient de détermination)
    ss_res = sum((ys_reg[i] - (beta_0 + beta_1 * xs_reg[i]))**2 for i in range(n_reg))
    ss_tot = sum((ys_reg[i] - my_r)**2 for i in range(n_reg))
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    # erreur standard des résidus
    se = math.sqrt(ss_res / max(n_reg - 2, 1))

    rc1, rc2 = st.columns([1, 2])
    with rc1:
        r2_color = "#14b8a6" if r_squared > 0.3 else "#f59e0b" if r_squared > 0.1 else "#ef4444"
        st.markdown(f"""
<div class="corr-card" style="border-left-color:#38bdf8">
  <p style="font-family:'Outfit',sans-serif;font-size:0.7rem;color:#4a3870;margin:0;text-transform:uppercase;letter-spacing:.05em">Modèle OLS</p>
  <p style="font-family:'Outfit',sans-serif;font-size:0.85rem;color:#c4b5fd;margin:0.4rem 0 0.2rem">
    ŷ = {beta_0:.1f} + ({beta_1:.2f}) · lat</p>
  <p style="font-family:'Outfit',sans-serif;font-size:2rem;font-weight:800;color:{r2_color};margin:0.2rem 0;text-shadow:0 0 20px {r2_color}55">
    R² = {r_squared:.4f}</p>
  <p style="font-size:0.75rem;color:#8b7ac9;margin:0">SE résidus = {se:.1f}</p>
  <p style="font-size:0.75rem;color:#8b7ac9;margin:0">n = {n_reg} obs.</p>
</div>""", unsafe_allow_html=True)
    with rc2:
        reg_df = df[["lat", "locuteurs_M", "famille"]].copy()
        reg_df.columns = ["Latitude", "Locuteurs (M)", "Famille"]
        try:
            st.scatter_chart(reg_df, x="Latitude", y="Locuteurs (M)", color="Famille",
                             height=280, use_container_width=True)
        except Exception:
            pass

    st.markdown(f"""
<div class="lm-card" style="border-left:3px solid #38bdf8;margin:0.5rem 0 1.2rem;max-width:600px">
  <p style="font-family:'Outfit',sans-serif;font-size:0.78rem;color:#c4b5fd;margin:0;line-height:1.7">
    <b style="color:#38bdf8">Interprétation :</b> Le R² de {r_squared:.4f} signifie que la latitude
    n'explique que <b style="color:#f59e0b">{r_squared*100:.1f}%</b> de la variance du nombre de locuteurs.
    Le coefficient β₁ = {beta_1:.2f} {"(négatif : les langues proches de l'équateur tendent à avoir plus de locuteurs)" if beta_1 < 0 else "(positif : tendance vers les hautes latitudes)"}.
    Ce faible pouvoir prédictif confirme que la géographie seule ne détermine pas la vitalité d'une langue.
  </p>
  <hr style="border:none;border-top:1px solid rgba(56,189,248,0.15);margin:0.6rem 0"/>
  <p style="font-family:'Outfit',sans-serif;font-size:0.75rem;color:#8b7ac9;margin:0;line-height:1.7">
    <b style="color:#6b5fa8">En clair :</b> On a essayé de prédire combien de gens parlent une langue
    juste en regardant si elle est parlée au nord ou au sud du globe. Résultat : ça ne marche quasiment pas.
    Le R² proche de 0 veut dire que savoir qu'une langue est parlée à telle latitude ne nous dit presque rien
    sur son nombre de locuteurs. La géographie n'est pas le facteur principal, c'est plutôt l'histoire,
    la politique et la démographie qui comptent.
  </p>
</div>""", unsafe_allow_html=True)

    def shannon(counts):
        total = sum(counts)
        if not total: return 0
        return round(-sum((c/total)*math.log(c/total) for c in counts if c>0), 3)
    h = shannon(df["famille"].value_counts().tolist())
    h_max = round(math.log(max(len(all_familles),1)), 2)
    h_pct = h/h_max*100 if h_max else 0
    st.markdown(f"""
<div class="lm-card" style="border-left:3px solid #a78bfa;max-width:480px;margin-top:1.2rem">
  <p style="font-family:'Outfit',sans-serif;font-size:0.8rem;font-weight:700;color:#a78bfa;margin:0 0 0.3rem;text-transform:uppercase;letter-spacing:0.06em">Indice de diversité de Shannon</p>
  <p style="font-family:'Outfit',sans-serif;font-size:3rem;font-weight:800;color:#f1f0ff;margin:0;text-shadow:0 0 30px rgba(167,139,250,0.5)">H = {h}</p>
  <p style="font-size:0.82rem;color:#8b7ac9;margin:0.3rem 0 0.6rem;font-family:'Fraunces',serif;font-style:italic">H max théorique ({len(all_familles)} familles) : {h_max}</p>
  <div style="height:8px;background:rgba(255,255,255,0.07);border-radius:4px;overflow:hidden">
    <div style="height:100%;width:{h_pct:.1f}%;background:linear-gradient(90deg,#7c3aed,#a78bfa,#ec4899);border-radius:4px;animation:bar-grow 1.5s cubic-bezier(.34,1.2,.64,1) both;--bar-w:{h_pct:.1f}%"></div>
  </div>
</div>
<div class="lm-card" style="border-left:3px solid #a78bfa;max-width:480px;margin-top:0.5rem">
  <p style="font-family:'Outfit',sans-serif;font-size:0.75rem;color:#8b7ac9;margin:0;line-height:1.7">
    <b style="color:#6b5fa8">En clair :</b> L'indice de Shannon mesure la diversité comme en écologie.
    Plus il est élevé, plus les langues sont réparties entre beaucoup de familles différentes.
    La barre montre le ratio entre la diversité réelle et la diversité maximale théorique
    (si chaque famille avait exactement le même nombre de langues).
  </p>
</div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------
# PAGE : OCCITANIE
# -------------------------------------------------------
elif page == "occitanie":
    st.markdown('<div class="page-wrap" style="padding:0.5rem 3vw 2rem">', unsafe_allow_html=True)

    st.markdown("""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:1rem;animation:fadeUp 0.4s ease">
  <span style="font-size:1.8rem;animation:float 4s ease-in-out infinite">✨</span>
  <h2 style="font-family:'Outfit',sans-serif;font-size:1.5rem;font-weight:800;color:#f1f0ff;margin:0">Occitanie et Montpellier</h2>
</div>""", unsafe_allow_html=True)

    st.markdown("""
<div style="background:rgba(167,139,250,0.1);backdrop-filter:blur(14px);
  border:1px solid rgba(167,139,250,0.25);border-left:4px solid #a78bfa;
  border-radius:18px;padding:1.2rem 1.5rem;margin-bottom:1.2rem;animation:fadeUp 0.5s ease 0.1s both">
  <p style="font-family:'Outfit',sans-serif;font-size:1rem;font-weight:700;color:#f1f0ff;margin:0 0 0.5rem">Montpellier, carrefour linguistique du Midi</p>
  <p style="font-family:'Fraunces',serif;font-size:0.92rem;line-height:1.8;margin:0;color:#c4b5fd;font-style:italic">
    Montpellier se situe au coeur d'un territoire a l'histoire linguistique exceptionnelle.
    L'<b style="color:#a78bfa">Université Paul-Valéry Montpellier</b> abrite un département
    de linguistique reconnu pour ses recherches sur les <b style="color:#a78bfa">langues romanes</b>,
    l'<b style="color:#ec4899">occitan languedocien</b>, le <b style="color:#38bdf8">catalan</b>
    et les <b style="color:#14b8a6">langues en contact méditerranéen</b>.
  </p>
</div>""", unsafe_allow_html=True)

    df_occ = df[df["region"] == "Occitanie"].copy()

    try:
        import plotly.graph_objects as go

        sizes_occ = [max(10, min(40, float(r["locuteurs_M"])*25+10)) for _, r in df_occ.iterrows()]
        hover_occ = [
            f"<b>{r['nom']}</b><br>{r['type']}<br>👥 {r['locuteurs_M']}M · {r['statut_label']}<br><i style='font-size:0.85em'>{r['notes']}</i>"
            for _, r in df_occ.iterrows()]

        fig2 = go.Figure()
        fig2.add_trace(go.Scattergeo(
            lat=df_occ["lat"], lon=df_occ["lon"], mode="markers+text",
            text=df_occ["nom"], textposition="top center",
            textfont=dict(family="Outfit, sans-serif", size=10, color="#e9d5ff"),
            marker=dict(size=sizes_occ, color="#7c3aed", opacity=0.75,
                        line=dict(width=1.5, color="rgba(255,255,255,0.7)")),
            hovertext=hover_occ, hoverinfo="text",
            hoverlabel=dict(bgcolor="#1a0a2e", bordercolor="#a78bfa",
                            font=dict(family="Outfit, sans-serif", size=12, color="#f1f0ff")),
            name="Variétés occitanes"))
        fig2.add_trace(go.Scattergeo(
            lat=[43.6117], lon=[3.8767], mode="markers+text",
            text=["★ Montpellier"], textposition="top right",
            textfont=dict(family="Outfit, sans-serif", size=11, color="#ec4899"),
            marker=dict(size=14, color="#ec4899", symbol="star",
                        line=dict(width=1.5, color="white")),
            hovertext=["Montpellier · Univ. Paul-Valéry Montpellier"],
            hoverinfo="text", name="Montpellier"))
        fig2.update_geos(
            projection_type="mercator",
            showland=True, landcolor="#1e1035", showocean=True, oceancolor="#0d0820",
            showcoastlines=True, coastlinecolor="rgba(167,139,250,0.3)",
            showcountries=True, countrycolor="rgba(167,139,250,0.2)",
            showframe=False, showlakes=False, bgcolor="rgba(0,0,0,0)",
            lonaxis_range=[-3.5, 9.5], lataxis_range=[41.5, 46.5])
        fig2.update_layout(height=380, margin=dict(l=0, r=0, t=0, b=0),
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           showlegend=False)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
    except ImportError:
        pass

    st.markdown("##### Variétés occitanes du territoire")
    c_occ = st.columns(3)
    for idx,(_,row) in enumerate(df_occ.iterrows()):
        b = STATUT_BADGE.get(row["statut"], "b-vuln")
        with c_occ[idx % 3]:
            st.markdown(f"""
<div class="lm-card" style="border-top:3px solid #a78bfa;animation-delay:{idx*0.05}s">
  <p style="font-family:'Outfit',sans-serif;font-size:0.93rem;font-weight:700;margin:0 0 0.4rem;color:#f1f0ff">{row['nom']}</p>
  <div style="margin-bottom:0.4rem"><span class="badge {b}">{row['statut_label']}</span><span class="badge b-dialect">{row['type']}</span></div>
  <p style="font-size:0.8rem;color:#8b7ac9;margin:0.1rem 0">👥 {row['locuteurs_M']}M · 🏳 {row['pays']}</p>
  <p style="font-size:0.8rem;font-style:italic;color:#6b5f9e;margin:0.5rem 0 0;
     border-top:1px solid rgba(167,139,250,0.15);padding-top:0.4rem;
     line-height:1.55;font-family:'Fraunces',serif">{row['notes']}</p>
</div>""", unsafe_allow_html=True)

    st.markdown("##### Langues de la communauté montpelliéraine")
    extras = [
        ("Darija (Algérie)", "Dialecte arabe majoritaire dans la diaspora algérienne de Montpellier.", "b-dialect", "#38bdf8"),
        ("Darija (Maroc)", "Parlé par la communauté marocaine de l'Hérault.", "b-dialect", "#38bdf8"),
        ("Tamazight kabyle", "Langue berbère vivante dans la diaspora kabyle d'Occitanie.", "b-vuln", "#f59e0b"),
        ("Catalan nord (Roussillon)", "Parlé à 80 km, en Catalogne du Nord (Perpignan).", "b-vuln", "#a78bfa"),
        ("Arabe standard", "Arabe littéraire, enseigné et pratiqué dans la ville.", "b-safe", "#14b8a6"),
        ("Languedocien", "Occitan historiquement parlé dans les rues de Montpellier.", "b-vuln", "#ec4899")]
    mc = st.columns(3)
    for idx,(nom, desc, badge, accent) in enumerate(extras):
        with mc[idx%3]:
            st.markdown(f"""
<div class="lm-card" style="border-top:3px solid {accent};animation-delay:{idx*0.05}s">
  <span class="badge {badge}">{nom}</span>
  <p style="font-size:0.82rem;color:#8b7ac9;margin:0.5rem 0 0;line-height:1.6;font-family:'Fraunces',serif;font-style:italic">{desc}</p>
</div>""", unsafe_allow_html=True)

    st.markdown("""
<div class="lm-card" style="border-left:3px solid #a78bfa;margin-top:1rem">
  <p style="font-family:'Outfit',sans-serif;font-size:0.85rem;font-weight:700;color:#a78bfa;margin:0 0 0.4rem;text-transform:uppercase;letter-spacing:0.04em">Université Paul-Valéry Montpellier</p>
  <p style="font-family:'Fraunces',serif;font-size:0.9rem;color:#c4b5fd;line-height:1.8;margin:0;font-style:italic">
    Fondée en 1970, héritière d'une faculté des Lettres dont les racines remontent à <b style="color:#a78bfa">1289</b>.
    Son département de linguistique mène des recherches actives sur les langues romanes,
    l'occitan, le catalan, les langues en contact méditerranéen et la sociolinguistique.
  </p>
</div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
# PAGE : TIMELINE
# frise chronologique des langues, codée en HTML/CSS pur
# les dates sont approximatives (sources : Glottolog, Wikipedia, UNESCO)
# ══════════════════════════════════════════════
elif page == "timeline":
    st.markdown('<div class="page-wrap" style="padding:0.5rem 3vw 2rem">', unsafe_allow_html=True)

    st.markdown("""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:1.2rem;animation:fadeUp 0.4s ease">
  <span style="font-size:1.8rem">🕰️</span>
  <div>
    <h2 style="font-family:'Outfit',sans-serif;font-size:1.5rem;font-weight:800;color:var(--text);margin:0">Frise historique des langues</h2>
    <p style="font-family:'Fraunces',serif;font-size:0.82rem;color:var(--text-m);margin:0;font-style:italic">
      Grandes dates de l'histoire linguistique mondiale</p>
  </div>
</div>""", unsafe_allow_html=True)

    # donnees de la frise (date, titre, description, couleur, categorie)
    timeline_events = [
        (-3200, "Sumérien cunéiforme", "Premier système d'écriture connu, Mésopotamie", "#f59e0b", "Écriture"),
        (-3000, "Hiéroglyphes égyptiens", "Développement de l'écriture sacrée en Égypte ancienne", "#f59e0b", "Écriture"),
        (-1500, "Proto-indo-européen", "Dispersion estimée de la famille linguistique la plus large au monde", "#a78bfa", "Famille"),
        (-1200, "Alphabet phénicien", "Ancêtre de presque tous les alphabets modernes (grec, latin, arabe, hébreu)", "#f59e0b", "Écriture"),
        (-500,  "Sanskrit classique", "Grammaire de Panini, première description linguistique formelle", "#14b8a6", "Étude"),
        (-300,  "Expansion bantou", "Migration des peuples bantoues depuis l'Afrique de l'Ouest, diffusion de 500+ langues", "#ec4899", "Migration"),
        (100,   "Expansion du latin", "Le latin devient lingua franca de l'Empire romain, ancêtre des langues romanes", "#a78bfa", "Famille"),
        (609,   "Révélation du Coran", "L'arabe classique se fixe et se diffuse dans tout le monde musulman", "#38bdf8", "Diffusion"),
        (800,   "Vieux norrois", "Les Vikings diffusent le norrois en Europe du Nord, ancêtre du suédois, norvégien, islandais", "#a78bfa", "Famille"),
        (1000,  "Apogée de l'occitan", "La langue d'oc domine la poésie des troubadours en Europe médiévale", "#ec4899", "Culture"),
        (1190,  "Troubadours occitans", "Montpellier, Toulouse et la Provence brillent dans la littérature en langue d'oc", "#ec4899", "Culture"),
        (1443,  "Invention du Hangul", "Le roi Sejong crée l'alphabet coréen pour le peuple", "#f59e0b", "Écriture"),
        (1492,  "Grammaire de Nebrija", "Première grammaire d'une langue européenne moderne (espagnol)", "#14b8a6", "Étude"),
        (1539,  "Ordonnance de Villers-Cotterêts", "Le français remplace le latin dans l'administration en France", "#6366f1", "Politique"),
        (1600,  "Colonisation et diffusion", "L'espagnol, le portugais, l'anglais et le français se mondialisent", "#38bdf8", "Diffusion"),
        (1786,  "Découverte de l'indo-européen", "William Jones identifie les liens entre sanskrit, grec et latin", "#14b8a6", "Étude"),
        (1821,  "Syllabaire Cherokee", "Sequoyah invente un système d'écriture pour la langue Cherokee", "#f59e0b", "Écriture"),
        (1880,  "Volapük puis Espéranto", "Premières langues construites pour la communication internationale", "#6366f1", "Politique"),
        (1904,  "Prix Nobel de Mistral", "Frédéric Mistral reçoit le Nobel pour son oeuvre en provençal, l'occitan brille", "#ec4899", "Culture"),
        (1928,  "Réforme turque", "Atatürk remplace l'alphabet arabe par le latin en Turquie", "#6366f1", "Politique"),
        (1948,  "Déclaration universelle", "L'ONU publie la DUDH, traduite en 500+ langues", "#6366f1", "Politique"),
        (1950,  "Mort du dalmate", "Dernière langue romane des Balkans, Tuone Udaina (dernier locuteur) mort en 1898", "#ef4444", "Disparition"),
        (1953,  "Code talkers reconnus", "Les Navajos ayant utilisé leur langue comme code durant WWII sont honorés", "#38bdf8", "Culture"),
        (1992,  "Charte européenne", "Charte européenne des langues régionales ou minoritaires", "#6366f1", "Politique"),
        (1996,  "Atlas UNESCO", "L'UNESCO publie le premier Atlas des langues en danger dans le monde", "#ef4444", "Disparition"),
        (2003,  "Convention UNESCO", "Convention pour la sauvegarde du patrimoine culturel immatériel", "#6366f1", "Politique"),
        (2008,  "Mort de l'eyak", "Marie Smith Jones, dernière locutrice de l'eyak (Alaska), décède", "#ef4444", "Disparition"),
        (2011,  "Amazigh officiel au Maroc", "Le berbère (tifinagh) devient langue officielle du Maroc", "#14b8a6", "Revitalisation"),
        (2019,  "Année int. langues autochtones", "L'ONU déclare 2019 année internationale des langues autochtones", "#14b8a6", "Revitalisation"),
        (2023,  "Jejueo : 2 locuteurs", "Le dialecte de l'île de Jeju en Corée n'a plus que 2 locuteurs natifs", "#ef4444", "Disparition"),
        (2024,  "Décennie des langues", "L'UNESCO lance la Décennie internationale des langues autochtones (2022-2032)", "#14b8a6", "Revitalisation"),
    ]

    # filtre par catégorie
    categories = sorted(set(e[4] for e in timeline_events))
    cat_filter = st.multiselect("Filtrer par catégorie", categories, default=categories, key="tl_cat")

    filtered = [e for e in timeline_events if e[4] in cat_filter]

    # légende des catégories
    cat_colors = {"Écriture": "#f59e0b", "Famille": "#a78bfa", "Étude": "#14b8a6",
                  "Migration": "#ec4899", "Culture": "#ec4899", "Diffusion": "#38bdf8",
                  "Politique": "#6366f1", "Disparition": "#ef4444", "Revitalisation": "#14b8a6"}
    legend = '<div style="display:flex;flex-wrap:wrap;gap:0.5rem;margin-bottom:1.5rem">'
    for cat in categories:
        if cat not in cat_filter:
            continue
        c = cat_colors.get(cat, "#a78bfa")
        legend += (f'<div style="display:inline-flex;align-items:center;gap:5px;'
                   f'background:rgba(255,255,255,0.05);border:1px solid {c}44;'
                   f'border-radius:20px;padding:3px 10px">'
                   f'<div style="width:8px;height:8px;border-radius:50%;background:{c}"></div>'
                   f'<span style="font-family:Outfit,sans-serif;font-size:0.7rem;color:{c};font-weight:600">{cat}</span></div>')
    st.markdown(legend + '</div>', unsafe_allow_html=True)

    # construction de la frise verticale
    tl_html = '<div style="position:relative;padding-left:40px;border-left:2px solid rgba(167,139,250,0.2);margin-left:20px">'
    for i, (year, title, desc, color, cat) in enumerate(filtered):
        year_display = f"{abs(year)} av. J.-C." if year < 0 else f"{year}"
        delay = i * 0.04
        tl_html += f"""
<div style="position:relative;margin-bottom:1.8rem;animation:fadeUp 0.4s ease {delay}s both">
  <!-- point sur la ligne -->
  <div style="position:absolute;left:-47px;top:4px;width:14px;height:14px;border-radius:50%;
    background:{color};border:3px solid {'#f8f6ff' if _is_light else '#0d0820'};
    box-shadow:0 0 10px {color}88;z-index:2"></div>
  <!-- contenu -->
  <div style="background:var(--bg);backdrop-filter:var(--blur-sm);
    border:1px solid var(--border);border-left:3px solid {color};
    border-radius:14px;padding:0.9rem 1.2rem;
    box-shadow:var(--shadow-sm);transition:transform 0.2s,box-shadow 0.2s"
    onmouseenter="this.style.transform='translateX(6px)';this.style.boxShadow='0 8px 28px rgba(0,0,0,0.3),0 0 16px {color}33'"
    onmouseleave="this.style.transform='';this.style.boxShadow=''">
    <div style="display:flex;align-items:center;gap:0.8rem;margin-bottom:0.3rem">
      <span style="font-family:'Outfit',sans-serif;font-size:0.68rem;font-weight:700;
        color:{color};background:{color}18;border:1px solid {color}33;
        border-radius:6px;padding:2px 8px;white-space:nowrap">{year_display}</span>
      <span style="font-family:'Outfit',sans-serif;font-size:0.62rem;color:var(--text-m);
        text-transform:uppercase;letter-spacing:.08em">{cat}</span>
    </div>
    <p style="font-family:'Outfit',sans-serif;font-size:0.92rem;font-weight:700;
      color:var(--text);margin:0 0 0.2rem">{title}</p>
    <p style="font-family:'Fraunces',serif;font-size:0.8rem;color:var(--text-m);
      margin:0;font-style:italic;line-height:1.5">{desc}</p>
  </div>
</div>"""

    tl_html += '</div>'
    st.markdown(tl_html, unsafe_allow_html=True)

    # stats de la frise
    n_events = len(filtered)
    earliest = min(e[0] for e in filtered) if filtered else 0
    latest = max(e[0] for e in filtered) if filtered else 2024
    span_years = latest - earliest
    n_disparition = sum(1 for e in filtered if e[4] == "Disparition")
    n_revit = sum(1 for e in filtered if e[4] == "Revitalisation")

    st.markdown(f"""
<div style="display:flex;gap:1rem;flex-wrap:wrap;margin-top:1rem">
  <div style="background:var(--bg);border:1px solid var(--border);border-radius:12px;padding:0.5rem 1rem">
    <span style="font-family:'Outfit',sans-serif;font-size:1.2rem;font-weight:800;color:var(--text)">{n_events}</span>
    <span style="font-family:'Outfit',sans-serif;font-size:0.68rem;color:var(--text-m);margin-left:6px">événements</span>
  </div>
  <div style="background:var(--bg);border:1px solid var(--border);border-radius:12px;padding:0.5rem 1rem">
    <span style="font-family:'Outfit',sans-serif;font-size:1.2rem;font-weight:800;color:var(--text)">{span_years:,}</span>
    <span style="font-family:'Outfit',sans-serif;font-size:0.68rem;color:var(--text-m);margin-left:6px">ans couverts</span>
  </div>
  <div style="background:var(--bg);border:1px solid var(--border);border-radius:12px;padding:0.5rem 1rem">
    <span style="font-family:'Outfit',sans-serif;font-size:1.2rem;font-weight:800;color:#ef4444">{n_disparition}</span>
    <span style="font-family:'Outfit',sans-serif;font-size:0.68rem;color:var(--text-m);margin-left:6px">disparitions</span>
  </div>
  <div style="background:var(--bg);border:1px solid var(--border);border-radius:12px;padding:0.5rem 1rem">
    <span style="font-family:'Outfit',sans-serif;font-size:1.2rem;font-weight:800;color:#14b8a6">{n_revit}</span>
    <span style="font-family:'Outfit',sans-serif;font-size:0.68rem;color:var(--text-m);margin-left:6px">revitalisations</span>
  </div>
</div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
# PAGE : COMPARATEUR
# compare 2-3 langues cote a cote
# ══════════════════════════════════════════════
elif page == "comparateur":
    st.markdown('<div class="page-wrap" style="padding:0.5rem 3vw 2rem">', unsafe_allow_html=True)

    st.markdown("""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:1.2rem;animation:fadeUp 0.4s ease">
  <span style="font-size:1.8rem">⚖️</span>
  <div>
    <h2 style="font-family:'Outfit',sans-serif;font-size:1.5rem;font-weight:800;color:var(--text);margin:0">Comparateur de langues</h2>
    <p style="font-family:'Fraunces',serif;font-size:0.82rem;color:var(--text-m);margin:0;font-style:italic">
      Selectionne 2 ou 3 langues pour les comparer visuellement</p>
  </div>
</div>""", unsafe_allow_html=True)

    all_names = sorted(df["nom"].tolist())
    comp_cols = st.columns(3)
    selections = []
    for i, col in enumerate(comp_cols):
        with col:
            default_idx = min(i, len(all_names)-1)
            defaults = ["Français", "Arabe standard", "Japonais"]
            def_val = defaults[i] if defaults[i] in all_names else all_names[default_idx]
            sel = st.selectbox(f"Langue {i+1}", ["(aucune)"] + all_names,
                               index=all_names.index(def_val)+1 if def_val in all_names else 0,
                               key=f"comp_{i}")
            if sel != "(aucune)":
                selections.append(sel)

    if len(selections) >= 2:
        comp_df = df[df["nom"].isin(selections)].copy()
        comp_colors = ["#a78bfa", "#ec4899", "#14b8a6"]

        # tableau comparatif
        fields = [
            ("Famille", "famille"), ("Type", "type"), ("Locuteurs", "locuteurs_M"),
            ("Pays", "pays"), ("Region", "region"), ("Script", "script"),
            ("Statut", "statut_label"), ("Officielle", "officielle"),
        ]

        for fname, fkey in fields:
            row_html = f'<div style="display:flex;gap:0;margin-bottom:2px">'
            row_html += (f'<div style="width:120px;flex-shrink:0;padding:8px 12px;'
                         f'background:rgba(124,58,237,0.08);border-radius:8px 0 0 8px;'
                         f'font-family:Outfit,sans-serif;font-size:0.72rem;font-weight:700;'
                         f'color:var(--text-m);display:flex;align-items:center">{fname}</div>')
            for j, (_, r) in enumerate(comp_df.iterrows()):
                val = r[fkey]
                if fkey == "locuteurs_M":
                    val = f"{val}M"
                elif fkey == "officielle":
                    val = "Oui" if val else "Non"
                c = comp_colors[j % 3]
                row_html += (f'<div style="flex:1;padding:8px 12px;'
                             f'background:rgba(255,255,255,0.03);border:1px solid var(--border);'
                             f'font-family:Outfit,sans-serif;font-size:0.82rem;color:var(--text);'
                             f'{"border-radius:0 8px 8px 0;" if j == len(comp_df)-1 else ""}'
                             f'display:flex;align-items:center">{val}</div>')
            row_html += '</div>'
            st.markdown(row_html, unsafe_allow_html=True)

        # barres comparatives locuteurs
        st.markdown('<div style="height:1.2rem"></div>', unsafe_allow_html=True)
        st.markdown("""<p style="font-family:'Outfit',sans-serif;font-size:0.82rem;font-weight:600;
          color:var(--text-s);margin:0 0 0.6rem">Comparaison des locuteurs</p>""", unsafe_allow_html=True)
        max_loc = comp_df["locuteurs_M"].max()
        for j, (_, r) in enumerate(comp_df.iterrows()):
            pct = r["locuteurs_M"] / max_loc * 100 if max_loc > 0 else 0
            c = comp_colors[j % 3]
            st.markdown(f"""
<div class="stat-bar-wrap">
  <div class="stat-bar-label">
    <span style="color:var(--text);font-weight:600">{r['nom']}</span>
    <span style="color:{c};font-weight:700">{r['locuteurs_M']}M</span>
  </div>
  <div class="stat-bar-track">
    <div class="stat-bar-fill" style="width:{pct:.1f}%;background:{c};--bar-w:{pct:.1f}%;--delay:0s"></div>
  </div>
</div>""", unsafe_allow_html=True)

        # notes
        st.markdown('<div style="height:0.8rem"></div>', unsafe_allow_html=True)
        for j, (_, r) in enumerate(comp_df.iterrows()):
            c = comp_colors[j % 3]
            st.markdown(f"""
<div class="lm-card" style="border-left:3px solid {c};padding:0.7rem 1rem;margin-bottom:0.4rem">
  <p style="font-family:'Outfit',sans-serif;font-size:0.85rem;font-weight:700;color:{c};margin:0 0 0.2rem">{r['nom']}</p>
  <p style="font-family:'Fraunces',serif;font-size:0.8rem;color:var(--text-m);margin:0;font-style:italic;line-height:1.5">{r['notes']}</p>
</div>""", unsafe_allow_html=True)

    elif len(selections) == 1:
        st.markdown("""<p style="font-family:'Outfit',sans-serif;font-size:0.85rem;color:var(--text-m);
          font-style:italic;margin-top:1rem">Selectionne au moins une deuxieme langue pour comparer.</p>""", unsafe_allow_html=True)
    else:
        st.markdown("""<p style="font-family:'Outfit',sans-serif;font-size:0.85rem;color:var(--text-m);
          font-style:italic;margin-top:1rem">Selectionne 2 ou 3 langues ci-dessus pour lancer la comparaison.</p>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
# PAGE : QUIZ SCRIPT
# on montre un mot ecrit dans un script et le joueur doit deviner la langue
# ══════════════════════════════════════════════
elif page == "quiz":
    import random as _qrnd

    st.markdown('<div class="page-wrap" style="padding:0.5rem 3vw 2rem">', unsafe_allow_html=True)

    st.markdown("""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:1.2rem;animation:fadeUp 0.4s ease">
  <span style="font-size:1.8rem">✍️</span>
  <div>
    <h2 style="font-family:'Outfit',sans-serif;font-size:1.5rem;font-weight:800;color:var(--text);margin:0">Quiz Script</h2>
    <p style="font-family:'Fraunces',serif;font-size:0.82rem;color:var(--text-m);margin:0;font-style:italic">
      Reconnais l'ecriture, devine la langue</p>
  </div>
</div>""", unsafe_allow_html=True)

    # banque de mots (mot, langue, script)
    _quiz_bank = [
        ("مرحبا", "Arabe standard", "Arabe", "Bonjour"),
        ("こんにちは", "Japonais", "Mixte", "Bonjour"),
        ("안녕하세요", "Coréen", "Hangul", "Bonjour"),
        ("नमस्ते", "Hindi", "Devanagari", "Bonjour"),
        ("你好", "Mandarin standard", "Sinogrammes", "Bonjour"),
        ("สวัสดี", "Thaï", "Thaï", "Bonjour"),
        ("Привет", "Russe", "Cyrillique", "Salut"),
        ("Γεια σου", "Grec", "Grec", "Salut"),
        ("שלום", "Hébreu moderne", "Hébreu", "Paix/Bonjour"),
        ("ສະບາຍດີ", "Lao", "Lao", "Bonjour"),
        ("မင်္ဂလာပါ", "Birman", "Birman", "Bonjour"),
        ("ជំរាបសួរ", "Khmer", "Khmer", "Bonjour"),
        ("வணக்கம்", "Tamoul", "Tamoul", "Bonjour"),
        ("ಹಲೋ", "Kannada", "Kannada", "Bonjour"),
        ("សួស្តី", "Khmer", "Khmer", "Bonjour"),
        ("ᐊᐃᓐᖓᐃ", "Inuktitut", "Syllabique", "Bonjour"),
        ("Merhaba", "Turc", "Latin", "Bonjour"),
        ("Xin chào", "Vietnamien", "Latin", "Bonjour"),
        ("Bom dia", "Portugais", "Latin", "Bonjour"),
        ("Cześć", "Polonais", "Latin", "Salut"),
        ("Сайн байна уу", "Mongol", "Cyrillique", "Bonjour"),
        ("Გამარჯობა", "Géorgien", "Mkhédrouri", "Bonjour"),
        ("Բարև", "Arménien", "Arménien", "Bonjour"),
        ("ⵜⴰⵏⵎⵎⵉⵔⵜ", "Tamazight kabyle", "Tifinagh/Latin", "Merci"),
        ("ありがとう", "Japonais", "Mixte", "Merci"),
        ("감사합니다", "Coréen", "Hangul", "Merci"),
        ("ధన్యవాదాలు", "Télougou", "Télougou", "Merci"),
        ("ขอบคุณ", "Thaï", "Thaï", "Merci"),
    ]

    # init quiz state
    if "quiz_round" not in st.session_state:
        st.session_state.quiz_round = 0
        st.session_state.quiz_score = 0
        st.session_state.quiz_total = 0
        _qrnd.seed()
        st.session_state.quiz_order = _qrnd.sample(range(len(_quiz_bank)), min(10, len(_quiz_bank)))
        st.session_state.quiz_answered = False
        st.session_state.quiz_last_correct = None

    qr = st.session_state.quiz_round
    QUIZ_TOTAL = len(st.session_state.quiz_order)

    def _quiz_reset():
        _qrnd.seed()
        st.session_state.quiz_round = 0
        st.session_state.quiz_score = 0
        st.session_state.quiz_total = 0
        st.session_state.quiz_order = _qrnd.sample(range(len(_quiz_bank)), min(10, len(_quiz_bank)))
        st.session_state.quiz_answered = False
        st.session_state.quiz_last_correct = None

    # progression
    st.progress(qr / QUIZ_TOTAL, text=f"Question {min(qr+1, QUIZ_TOTAL)} / {QUIZ_TOTAL}")

    if qr >= QUIZ_TOTAL:
        # fin du quiz
        sc = st.session_state.quiz_score
        pct = sc / QUIZ_TOTAL * 100
        if pct >= 80: medal, msg = "🏆", "Expert en ecritures !"
        elif pct >= 50: medal, msg = "🥈", "Bon oeil !"
        else: medal, msg = "🌐", "Continue a explorer !"

        st.markdown(f"""
<div style="text-align:center;padding:2rem;animation:fadeUp 0.5s ease">
  <div style="font-size:4rem;margin-bottom:0.5rem">{medal}</div>
  <h2 style="font-family:'Outfit',sans-serif;font-size:2rem;font-weight:900;color:var(--text);margin:0 0 0.4rem">{msg}</h2>
  <p style="font-family:'Outfit',sans-serif;font-size:1.2rem;color:#a78bfa;margin:0">
    {sc} / {QUIZ_TOTAL} bonnes reponses ({pct:.0f}%)</p>
</div>""", unsafe_allow_html=True)
        if st.button("Rejouer le quiz", key="quiz_restart", use_container_width=True):
            _quiz_reset(); st.rerun()
    else:
        idx = st.session_state.quiz_order[qr]
        word, correct_lang, script_name, meaning = _quiz_bank[idx]

        # afficher le mot
        st.markdown(f"""
<div style="text-align:center;padding:2.5rem 2rem;margin-bottom:1.2rem;
  background:var(--bg);border:1px solid var(--border);border-radius:20px;
  box-shadow:var(--shadow-sm)">
  <p style="font-family:'Outfit',sans-serif;font-size:0.65rem;font-weight:700;
    letter-spacing:0.14em;text-transform:uppercase;color:var(--text-m);margin:0 0 0.8rem">Quel langue utilise cette ecriture ?</p>
  <p style="font-size:3.5rem;margin:0 0 0.6rem;line-height:1.2;color:var(--text)">{word}</p>
  <p style="font-family:'Fraunces',serif;font-size:0.85rem;color:var(--text-m);margin:0;font-style:italic">
    Signification : "{meaning}" · Script : {script_name}</p>
</div>""", unsafe_allow_html=True)

        if not st.session_state.quiz_answered:
            # generer 4 choix (1 correct + 3 faux)
            all_langs_quiz = list(set(q[1] for q in _quiz_bank))
            wrong = [l for l in all_langs_quiz if l != correct_lang]
            _qrnd.shuffle(wrong)
            choices = [correct_lang] + wrong[:3]
            _qrnd.shuffle(choices)

            # stocker les choix pour pas qu'ils changent au rerun
            if f"quiz_choices_{qr}" not in st.session_state:
                st.session_state[f"quiz_choices_{qr}"] = choices
            choices = st.session_state[f"quiz_choices_{qr}"]

            ch_cols = st.columns(2)
            for ci, choice in enumerate(choices):
                with ch_cols[ci % 2]:
                    if st.button(choice, key=f"quiz_choice_{qr}_{ci}", use_container_width=True):
                        st.session_state.quiz_answered = True
                        if choice == correct_lang:
                            st.session_state.quiz_score += 1
                            st.session_state.quiz_last_correct = True
                        else:
                            st.session_state.quiz_last_correct = False
                        st.rerun()
        else:
            # feedback
            is_correct = st.session_state.quiz_last_correct
            if is_correct:
                st.markdown(f"""
<div style="background:rgba(20,184,166,0.1);border:1px solid rgba(20,184,166,0.3);
  border-left:4px solid #14b8a6;border-radius:12px;padding:1rem 1.5rem;margin-bottom:1rem">
  <p style="font-family:'Outfit',sans-serif;font-size:1rem;font-weight:800;color:#14b8a6;margin:0">
    Bonne reponse !</p>
  <p style="font-family:'Fraunces',serif;font-size:0.85rem;color:var(--text-m);margin:0.2rem 0 0;font-style:italic">
    C'est bien du {correct_lang} ({script_name}).</p>
</div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
<div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);
  border-left:4px solid #ef4444;border-radius:12px;padding:1rem 1.5rem;margin-bottom:1rem">
  <p style="font-family:'Outfit',sans-serif;font-size:1rem;font-weight:800;color:#ef4444;margin:0">
    Rate !</p>
  <p style="font-family:'Fraunces',serif;font-size:0.85rem;color:var(--text-m);margin:0.2rem 0 0;font-style:italic">
    La bonne reponse etait <b style="color:var(--text)">{correct_lang}</b> ({script_name}).</p>
</div>""", unsafe_allow_html=True)

            if st.button("Question suivante", key=f"quiz_next_{qr}", use_container_width=True):
                st.session_state.quiz_round += 1
                st.session_state.quiz_answered = False
                st.session_state.quiz_last_correct = None
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
# PAGE : A PROPOS
# methodologie, sources, credits
# ══════════════════════════════════════════════
elif page == "about":
    st.markdown('<div class="page-wrap" style="padding:0.5rem 3vw 2rem">', unsafe_allow_html=True)

    st.markdown("""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:1.5rem;animation:fadeUp 0.4s ease">
  <span style="font-size:1.8rem">📄</span>
  <div>
    <h2 style="font-family:'Outfit',sans-serif;font-size:1.5rem;font-weight:800;color:var(--text);margin:0">A propos de VoxOrbis</h2>
    <p style="font-family:'Fraunces',serif;font-size:0.82rem;color:var(--text-m);margin:0;font-style:italic">
      Methodologie, sources et credits</p>
  </div>
</div>""", unsafe_allow_html=True)

    about_sections = [
        ("Le projet", "#a78bfa", """
            VoxOrbis est un atlas interactif des langues du monde. Il recense plus de 200 langues
            et dialectes avec leurs caractéristiques linguistiques, géographiques et sociolinguistiques.
            L'objectif est double : offrir un outil de visualisation pour l'exploration des données
            linguistiques, et démontrer des compétences en data science appliquée (statistiques
            descriptives, clustering, régression, visualisation interactive).
        """),
        ("Methodologie", "#ec4899", """
            Les données ont été compilées manuellement à partir de plusieurs sources de référence.
            Chaque langue est caractérisée par : nom, famille linguistique, type (langue/dialecte),
            nombre de locuteurs (estimation), coordonnées géographiques du foyer principal, pays,
            région, statut de vitalité (UNESCO), officialité, système d'écriture, et une note descriptive.
            Les analyses statistiques (skewness, kurtosis, K-Means, OLS, Shannon) sont toutes
            implémentées from scratch sans bibliothèque externe (ni numpy, ni sklearn, ni scipy),
            en utilisant uniquement le module math de Python.
        """),
        ("Sources des données", "#14b8a6", """
            <b>Glottolog 4.8</b> (Max Planck Institute) pour la classification des familles linguistiques.
            <b>Ethnologue 26e édition</b> (SIL International) pour les estimations de locuteurs.
            <b>UNESCO Atlas of the World's Languages in Danger</b> pour les statuts de vitalité.
            <b>Wikipedia</b> et littérature académique pour les notes descriptives et historiques.
            Les chiffres de locuteurs sont des estimations et peuvent varier selon les sources.
        """),
        ("Stack technique", "#38bdf8", """
            <b>Python 3</b> + <b>Streamlit</b> pour l'application web.
            <b>Plotly</b> pour les cartes interactives et les graphes du réseau.
            <b>HTML/CSS</b> custom pour le design glassmorphism dark.
            <b>Pandas</b> pour la manipulation des données.
            Tout le code statistique (Pearson, K-Means, OLS, Shannon, Haversine) est écrit à la main.
            L'algorithme Kamada-Kawai pour le layout du graphe est aussi from scratch.
        """),
        ("Limites connues", "#f59e0b", """
            Les estimations de locuteurs sont approximatives et varient fortement selon les sources
            (L1 vs L1+L2, comptages officiels vs estimations linguistiques).
            La classification langue/dialecte est souvent politique autant que linguistique.
            Le réseau Kamada-Kawai est limité à 120 nœuds pour des raisons de performance (O(n³)).
            Les coordonnées géographiques représentent un point central approximatif, pas l'aire
            réelle de diffusion d'une langue.
        """),
    ]

    for title, color, content in about_sections:
        st.markdown(f"""
<div class="lm-card" style="border-left:3px solid {color};margin-bottom:0.8rem">
  <p style="font-family:'Outfit',sans-serif;font-size:0.9rem;font-weight:700;color:{color};
    margin:0 0 0.5rem;text-transform:uppercase;letter-spacing:0.04em">{title}</p>
  <p style="font-family:'Fraunces',serif;font-size:0.88rem;color:var(--text-s);
    margin:0;line-height:1.8;font-style:italic">{content.strip()}</p>
</div>""", unsafe_allow_html=True)

    # compteurs du dataset
    st.markdown(f"""
<div style="display:flex;gap:1rem;flex-wrap:wrap;margin-top:1rem">
  <div style="background:var(--bg);border:1px solid var(--border);border-radius:12px;padding:0.6rem 1.2rem">
    <span style="font-family:'Outfit',sans-serif;font-size:1.4rem;font-weight:800;color:#a78bfa">{len(df)}</span>
    <span style="font-family:'Outfit',sans-serif;font-size:0.7rem;color:var(--text-m);margin-left:6px">entrées totales</span>
  </div>
  <div style="background:var(--bg);border:1px solid var(--border);border-radius:12px;padding:0.6rem 1.2rem">
    <span style="font-family:'Outfit',sans-serif;font-size:1.4rem;font-weight:800;color:#ec4899">{df['famille'].nunique()}</span>
    <span style="font-family:'Outfit',sans-serif;font-size:0.7rem;color:var(--text-m);margin-left:6px">familles</span>
  </div>
  <div style="background:var(--bg);border:1px solid var(--border);border-radius:12px;padding:0.6rem 1.2rem">
    <span style="font-family:'Outfit',sans-serif;font-size:1.4rem;font-weight:800;color:#14b8a6">{df['region'].nunique()}</span>
    <span style="font-family:'Outfit',sans-serif;font-size:0.7rem;color:var(--text-m);margin-left:6px">regions</span>
  </div>
  <div style="background:var(--bg);border:1px solid var(--border);border-radius:12px;padding:0.6rem 1.2rem">
    <span style="font-family:'Outfit',sans-serif;font-size:1.4rem;font-weight:800;color:#f59e0b">{df['script'].nunique()}</span>
    <span style="font-family:'Outfit',sans-serif;font-size:0.7rem;color:var(--text-m);margin-left:6px">systemes d'ecriture</span>
  </div>
</div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# auteur + footer
# on charge owl.gif pour l'avatar (meme technique que le background)
_owl_b64_src = ""
_owl_gif = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "owl.gif")
if os.path.exists(_owl_gif):
    try:
        with open(_owl_gif, "rb") as _f:
            _owl_b64_src = f"data:image/gif;base64,{base64.b64encode(_f.read()).decode()}"
    except Exception:
        pass

# si owl.gif existe on affiche le gif, sinon on fallback sur une lettre
if _owl_b64_src:
    _avatar_html = (
        f'<img src="{_owl_b64_src}" style="width:38px;height:38px;border-radius:50%;'
        f'object-fit:cover;box-shadow:0 0 16px rgba(124,58,237,0.5);'
        f'border:2px solid rgba(167,139,250,0.4)" />'
    )
else:
    _avatar_html = (
        '<div style="width:38px;height:38px;border-radius:50%;flex-shrink:0;'
        'background:linear-gradient(135deg,#7c3aed,#ec4899);'
        'display:flex;align-items:center;justify-content:center;'
        'font-weight:800;font-size:0.85rem;color:white;'
        'box-shadow:0 0 16px rgba(124,58,237,0.5)">A</div>'
    )

st.markdown(f"""
<div style="display:flex;flex-direction:column;align-items:center;gap:1rem;padding:2rem 1rem 0.5rem">
  <div style="display:inline-flex;align-items:center;gap:12px;
    background:rgba(255,255,255,0.05);border:1px solid rgba(167,139,250,0.15);
    border-radius:16px;padding:0.7rem 1.4rem">
    {_avatar_html}
    <div>
      <p style="font-size:0.82rem;font-weight:700;color:#f1f0ff;margin:0;font-family:'Outfit',sans-serif">Amar C.C</p>
      <p style="font-family:'Fraunces',serif;font-size:0.7rem;color:#6b5fa8;margin:0;font-style:italic">Data Science &amp; Visualisation</p>
    </div>
  </div>
  <div style="text-align:center;font-family:'Outfit',sans-serif;font-size:0.7rem;
    color:#4a3870;letter-spacing:0.08em;margin-bottom:75px;text-transform:uppercase">
    VoxOrbis · Amar C.C · 2025<br>
    <span style="font-family:'Fraunces',serif;font-style:italic;font-size:0.76rem;letter-spacing:0;color:#3a2860;text-transform:none">
      Glottolog 4.8 · Ethnologue 26e · UNESCO Atlas · SIL International
    </span>
  </div>
</div>
""", unsafe_allow_html=True)