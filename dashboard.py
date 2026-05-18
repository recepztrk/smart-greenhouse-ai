"""dashboard.py v2 — Akıllı Sera Yönetim Sistemi (Geliştirilmiş Dashboard)"""
from __future__ import annotations
import time
from typing import Dict, List
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from src.decision.fuzzy_engine import FuzzyEngine, RuleActivation
from src.explanation.explanation_engine import DecisionExplanation, ExplanationEngine
from src.simulation.greenhouse_state import GreenhouseState
from src.simulation.greenhouse_simulator import GreenhouseSimulator
from src.simulation.virtual_sensors import SensorReadings, VirtualSensorReader
from src.simulation.scenario_profiles import get_scenario_by_name, get_scenario_profiles

st.set_page_config(page_title="Akıllı Sera Yönetim Sistemi", page_icon="🌱", layout="wide")

def inject_css():
    st.markdown("""<style>
    .stApp { background: linear-gradient(135deg,#071a10 0%,#0a1628 100%); }
    [data-testid="stSidebar"] { background: linear-gradient(180deg,#0d2137 0%,#071a10 100%); border-right:1px solid #1a4a2a; }
    h1 { background: linear-gradient(90deg,#00c896,#00a8ff); -webkit-background-clip:text; -webkit-text-fill-color:transparent; font-weight:800 !important; }
    h2,h3 { color:#a8d8b8 !important; }
    [data-testid="metric-container"] { background:rgba(0,200,150,0.07); border:1px solid rgba(0,200,150,0.2); border-radius:12px; padding:12px 16px; }
    [data-testid="stMetricValue"] { color:#00c896 !important; font-weight:700 !important; }
    [data-testid="stMetricLabel"] { color:#7ab8a0 !important; font-size:0.78rem !important; text-transform:uppercase; }
    .stButton>button { background:linear-gradient(135deg,#00c896,#009e78); color:white; border:none; border-radius:8px; font-weight:600; transition:all .3s; }
    .stButton>button:hover { box-shadow:0 6px 20px rgba(0,200,150,0.4); transform:translateY(-2px); }
    hr { border-color:rgba(0,200,150,0.2) !important; }
    .alarm-crit { background:rgba(255,50,50,0.15); border:2px solid #ff4444; border-radius:12px; padding:16px 20px; margin-bottom:16px; animation:pulse 2s infinite; }
    .alarm-warn { background:rgba(255,170,0,0.12); border:1px solid #ffaa00; border-radius:12px; padding:12px 20px; margin-bottom:12px; }
    .kpi-card { background:rgba(0,200,150,0.08); border:1px solid rgba(0,200,150,0.22); border-radius:14px; padding:18px; text-align:center; }
    .kpi-val { font-size:1.9rem; font-weight:800; color:#00c896; }
    .kpi-lbl { font-size:0.72rem; text-transform:uppercase; letter-spacing:.07em; color:#7ab8a0; margin-top:4px; }
    @keyframes pulse { 0%{box-shadow:0 0 0 0 rgba(255,68,68,.4)} 70%{box-shadow:0 0 0 10px rgba(255,68,68,0)} 100%{box-shadow:0 0 0 0 rgba(255,68,68,0)} }
    </style>""", unsafe_allow_html=True)


def gauge(value, title, unit, lo=0.0, hi=100.0, warn_hi=None, warn_lo=None, alarm_mode=False):
    pct = (value - lo) / (hi - lo) if (hi - lo) else 0
    if alarm_mode:
        color = "#ff2222" if value >= 75 else ("#ff7700" if value >= 50 else ("#ffcc00" if value > 0 else "#00c896"))
    elif warn_hi and value > warn_hi:
        color = "#ff4444"
    elif warn_lo and value < warn_lo:
        color = "#ffaa00"
    else:
        color = "#00c896"
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value,
        number={"suffix": unit, "font": {"size": 20, "color": "#e0f0e9"}, "valueformat": ".1f"},
        title={"text": title, "font": {"size": 12, "color": "#7ab8a0"}},
        gauge={
            "axis": {"range": [lo, hi], "tickfont": {"color": "#5a8a6a", "size": 9}, "tickcolor": "#3a5a4a"},
            "bar": {"color": color, "thickness": 0.35},
            "bgcolor": "#0d1f2f", "borderwidth": 1, "bordercolor": "#1a3a2a",
            "steps": [{"range": [lo, hi], "color": "#091520"}],
        }
    ))
    fig.update_layout(height=190, margin=dict(l=15, r=15, t=48, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig


def initialize_session_state(initial_state, noise_enabled):
    st.session_state.simulator = GreenhouseSimulator(initial_state=initial_state)
    st.session_state.sensors = VirtualSensorReader(noise_enabled=noise_enabled)
    st.session_state.fuzzy_engine = FuzzyEngine()
    st.session_state.explanation_engine = ExplanationEngine()
    st.session_state.history = []
    st.session_state.last_readings = None
    st.session_state.last_actions = None
    st.session_state.last_explanation = None
    st.session_state.last_rules = []
    st.session_state.step_count = 0


def ensure_initialized(initial_state, noise_enabled):
    if "simulator" not in st.session_state:
        initialize_session_state(initial_state, noise_enabled)


def run_step():
    sim = st.session_state.simulator
    sensors = st.session_state.sensors
    fe = st.session_state.fuzzy_engine
    ee = st.session_state.explanation_engine
    st.session_state.step_count += 1
    state = GreenhouseState(**sim.get_state().to_dict())
    readings = sensors.read_all(state)
    actions = fe.evaluate(readings)
    rules = fe.get_last_rule_activations()
    explanation = ee.generate(readings=readings, actions=actions, rule_activations=rules)
    sim.apply_actions(irrigation_level=actions.irrigation_level, ventilation_level=actions.ventilation_level, shading_level=actions.shading_level)
    sim.step()
    state_after = GreenhouseState(**sim.get_state().to_dict())
    st.session_state.last_readings = readings
    st.session_state.last_actions = actions
    st.session_state.last_explanation = explanation
    st.session_state.last_rules = rules
    st.session_state.history.append({
        "step": st.session_state.step_count,
        # Sera durumu (adım sonrası)
        "temperature": state_after.temperature, "air_humidity": state_after.air_humidity,
        "soil_moisture": state_after.soil_moisture, "light_level": state_after.light_level,
        "water_tank_level": state_after.water_tank_level,
        # Kontrol aksiyonları
        "irrigation_level": actions.irrigation_level, "ventilation_level": actions.ventilation_level,
        "shading_level": actions.shading_level, "alarm_level": actions.alarm_level,
        # Sensör okumaları (playback için)
        "s_temperature": readings.temperature, "s_air_humidity": readings.air_humidity,
        "s_soil_moisture": readings.soil_moisture, "s_light_level": readings.light_level,
        "s_water_tank_level": readings.water_tank_level,
    })


# Bitki profilleri: ideal aralıklar ve isim
PLANT_PROFILES = {
    "🍅 Domates":  dict(t=(18,27), ah=(50,70), sm=(50,75), ll=(55,85)),
    "🌶️ Biber":   dict(t=(20,30), ah=(50,70), sm=(45,70), ll=(55,80)),
    "🥒 Salatalık": dict(t=(20,28), ah=(60,80), sm=(55,75), ll=(45,75)),
    "🌸 Genel":    dict(t=(15,30), ah=(40,70), sm=(35,70), ll=(30,80)),
}


def sidebar_controls(noise_enabled, noise_level):
    # Bitki profili
    st.sidebar.header("🌿 Bitki Profili")
    plant = st.sidebar.selectbox("Bitki Türü", list(PLANT_PROFILES.keys()), key="plant_profile")
    profile = PLANT_PROFILES[plant]
    st.sidebar.caption(f"İdeal sıcaklık: {profile['t'][0]}-{profile['t'][1]}°C | Nem: {profile['ah'][0]}-{profile['ah'][1]}%")

    st.sidebar.divider()
    st.sidebar.header("🌿 Hazır Senaryolar")
    scenarios = get_scenario_profiles()
    names = [s.name for s in scenarios]
    sel_name = st.sidebar.selectbox("Senaryo Seç", options=names)
    sel = get_scenario_by_name(sel_name)
    st.sidebar.caption(sel.description)
    with st.sidebar.expander("Beklenen Davranış"):
        st.write(sel.expected_behavior)
    if st.sidebar.button("✅ Senaryoyu Yükle", width="stretch"):
        initialize_session_state(sel.state, noise_enabled)
        st.rerun()
    st.sidebar.divider()
    st.sidebar.header("⚙️ Manuel Başlangıç")
    t = st.sidebar.slider("🌡️ Sıcaklık (°C)", 0.0, 50.0, 25.0, 0.5)
    ah = st.sidebar.slider("💧 Hava Nemi (%)", 0.0, 100.0, 50.0, 1.0)
    sm = st.sidebar.slider("🌱 Toprak Nemi (%)", 0.0, 100.0, 45.0, 1.0)
    ll = st.sidebar.slider("☀️ Işık Seviyesi (%)", 0.0, 100.0, 60.0, 1.0)
    wt = st.sidebar.slider("🚰 Su Tankı (%)", 0.0, 100.0, 80.0, 1.0)
    return GreenhouseState(temperature=t, air_humidity=ah, soil_moisture=sm, light_level=ll, water_tank_level=wt), plant


def render_alarm_banner(actions):
    if actions is None:
        return
    a = actions.alarm_level
    if a >= 75:
        st.markdown(f'<div class="alarm-crit">🚨 <strong style="color:#ff6666;font-size:1.1rem"> KRİTİK ALARM!</strong> <span style="color:#ffaaaa"> Alarm seviyesi {a:.1f}/100 — Hemen müdahale gerekebilir!</span></div>', unsafe_allow_html=True)
    elif a >= 50:
        st.markdown(f'<div class="alarm-warn">⚠️ <strong style="color:#ffcc00"> UYARI:</strong> <span style="color:#ffe080"> Alarm seviyesi {a:.1f}/100 — Sera koşulları izleniyor.</span></div>', unsafe_allow_html=True)


def _health_score(df: "pd.DataFrame") -> float:
    """Son adımdaki sensör değerlerinden 0-100 arası sera sağlık skoru hesaplar."""
    last = df.iloc[-1]
    # Her sensör için ideal aralığa yakınlığa göre 0-1 puan
    def score_range(val, lo, hi):
        if lo <= val <= hi:
            return 1.0
        dist = min(abs(val - lo), abs(val - hi))
        span = (hi - lo) or 1
        return max(0.0, 1.0 - dist / span)

    scores = [
        score_range(last["temperature"], 18, 30),
        score_range(last["air_humidity"], 40, 70),
        score_range(last["soil_moisture"], 35, 70),
        score_range(last["light_level"], 30, 75),
        score_range(last["water_tank_level"], 30, 100),
        1.0 - last["alarm_level"] / 100.0,
    ]
    return round(sum(scores) / len(scores) * 100, 1)


def render_kpi(history):
    if not history:
        return
    df = pd.DataFrame(history)
    health = _health_score(df)
    health_color = "#00c896" if health >= 70 else ("#ffaa00" if health >= 40 else "#ff4444")
    cols = st.columns(7)
    cards = [
        (f"{health}%", "🌿 Sera Sağlığı", health_color),
        (str(len(df)), "Toplam Adım", "#00c896"),
        (f"{(df['alarm_level'] >= 50).sum()}", "Alarm Olayı", "#ff4444" if (df['alarm_level'] >= 50).sum() > 0 else "#00c896"),
        (f"{df['alarm_level'].mean():.1f}", "Ort. Alarm", "#ffaa00"),
        (f"{df['temperature'].mean():.1f}°C", "Ort. Sıcaklık", "#00a8ff"),
        (f"{df['irrigation_level'].sum():.0f}", "Top. Sulama", "#00c896"),
        (f"{df['soil_moisture'].mean():.1f}%", "Ort. Toprak", "#00c896"),
    ]
    for col, (val, lbl, color) in zip(cols, cards):
        with col:
            st.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:{color}">{val}</div><div class="kpi-lbl">{lbl}</div></div>', unsafe_allow_html=True)


def render_sensor_gauges(state, readings):
    st.markdown("### 📡 Anlık Sera Durumu")
    cols = st.columns(5)
    with cols[0]: st.plotly_chart(gauge(state.temperature, "Sıcaklık", " °C", 0, 50, warn_hi=35, warn_lo=10), width="stretch", key="g_temp")
    with cols[1]: st.plotly_chart(gauge(state.air_humidity, "Hava Nemi", "%", warn_hi=80, warn_lo=30), width="stretch", key="g_air")
    with cols[2]: st.plotly_chart(gauge(state.soil_moisture, "Toprak Nemi", "%", warn_lo=30), width="stretch", key="g_soil")
    with cols[3]: st.plotly_chart(gauge(state.light_level, "Işık", "%", warn_hi=85), width="stretch", key="g_light")
    with cols[4]: st.plotly_chart(gauge(state.water_tank_level, "Su Tankı", "%", warn_lo=25), width="stretch", key="g_water")


def render_radar(state):
    fig = go.Figure(go.Scatterpolar(
        r=[state.temperature * 2, state.air_humidity, state.soil_moisture, state.light_level, state.water_tank_level],
        theta=["Sıcaklık", "Hava Nemi", "Toprak Nemi", "Işık", "Su Tankı"],
        fill="toself", name="Sensörler",
        line=dict(color="#00c896", width=2),
        fillcolor="rgba(0,200,150,0.15)",
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100], gridcolor="#1a3a2a", tickfont=dict(color="#5a8a6a")),
                   angularaxis=dict(linecolor="#2a5a3a", gridcolor="#1a3a2a", tickfont=dict(color="#a8d8b8", size=11)),
                   bgcolor="rgba(0,0,0,0)"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=300, margin=dict(l=30, r=30, t=30, b=30),
        showlegend=False, font=dict(color="#e0f0e9"),
    )
    return fig


def render_action_gauges(actions):
    st.markdown("### 🎛️ Kontrol Aksiyonları")
    if actions is None:
        st.info("Henüz karar üretilmedi.")
        return
    cols = st.columns(4)
    with cols[0]: st.plotly_chart(gauge(actions.irrigation_level, "💧 Sulama", "/100"), width="stretch", key="g_irr")
    with cols[1]: st.plotly_chart(gauge(actions.ventilation_level, "💨 Havalandırma", "/100"), width="stretch", key="g_vent")
    with cols[2]: st.plotly_chart(gauge(actions.shading_level, "🌫️ Gölgeleme", "/100"), width="stretch", key="g_shade")
    with cols[3]: st.plotly_chart(gauge(actions.alarm_level, "🚨 Alarm", "/100", alarm_mode=True), width="stretch", key="g_alarm")


def render_membership(readings, fuzzy_engine):
    st.markdown("### 🔬 Bulanık Üyelik Dereceleri")
    snap = fuzzy_engine.get_membership_snapshot(readings)
    labels_map = {
        "temperature": ("Sıcaklık", ["Düşük", "Normal", "Yüksek"]),
        "air_humidity": ("Hava Nemi", ["Düşük", "Normal", "Yüksek"]),
        "soil_moisture": ("Toprak Nemi", ["Kuru", "Uygun", "Islak"]),
        "light_level": ("Işık", ["Düşük", "Orta", "Yüksek"]),
        "water_tank_level": ("Su Tankı", ["Düşük", "Orta", "Yeterli"]),
    }
    cols = st.columns(5)
    colors = ["#ff6b6b", "#ffd93d", "#00c896"]
    for col, (key, (title, lbls)) in zip(cols, labels_map.items()):
        vals = list(snap[key].values())
        fig = go.Figure(go.Bar(
            x=lbls, y=vals,
            marker_color=[colors[i] if v == max(vals) else "rgba(0,200,150,0.25)" for i, v in enumerate(vals)],
            text=[f"{v:.2f}" for v in vals], textposition="outside",
            textfont=dict(color="#e0f0e9", size=10),
        ))
        fig.update_layout(
            title=dict(text=title, font=dict(color="#7ab8a0", size=11)),
            yaxis=dict(range=[0, 1.15], gridcolor="#1a3a2a", tickfont=dict(color="#5a8a6a", size=9), zerolinecolor="#1a3a2a"),
            xaxis=dict(tickfont=dict(color="#a8d8b8", size=9)),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=200, margin=dict(l=8, r=8, t=35, b=8), showlegend=False,
        )
        with col:
            st.plotly_chart(fig, width="stretch", key=f"mem_{key}")


def render_rules(rules):
    st.markdown("### 📋 Tetiklenen Fuzzy Kurallar")
    if not rules:
        st.info("Henüz tetiklenen kural yok.")
        return
    sorted_rules = sorted(rules, key=lambda r: r.activation, reverse=True)
    names = [r.rule_name[:55] + "…" if len(r.rule_name) > 55 else r.rule_name for r in sorted_rules]
    vals = [r.activation * 100 for r in sorted_rules]
    bar_colors = ["#ff4444" if v >= 70 else ("#ffaa00" if v >= 40 else "#00c896") for v in vals]
    fig = go.Figure(go.Bar(
        x=vals, y=names, orientation="h",
        marker_color=bar_colors,
        text=[f"%{v:.1f}" for v in vals], textposition="outside",
        textfont=dict(color="#e0f0e9", size=10),
    ))
    fig.update_layout(
        xaxis=dict(range=[0, 115], title="Aktivasyon (%)", tickfont=dict(color="#5a8a6a"), gridcolor="#1a3a2a", zerolinecolor="#1a3a2a"),
        yaxis=dict(tickfont=dict(color="#a8d8b8", size=10), autorange="reversed"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=max(200, len(rules) * 40), margin=dict(l=10, r=60, t=10, b=10),
    )
    st.plotly_chart(fig, width="stretch", key="rules_bar")


def render_explanation(explanation):
    st.markdown("### 💬 Karar Açıklaması")
    if explanation is None:
        st.info("Henüz karar açıklaması üretilmedi.")
        return
    st.info(explanation.summary)
    if explanation.warnings:
        for w in explanation.warnings:
            st.warning(w)
    with st.expander("Aksiyon Açıklamaları"):
        for item in explanation.action_explanations:
            st.write(f"- {item}")
    with st.expander("Kural Açıklamaları"):
        for item in explanation.active_rule_explanations:
            st.write(f"- {item}")


def render_playback(history: list) -> None:
    """Geçmiş adımları kaydırıcıyla geri oynatır, adım detaylarını ve delta değişimlerini gösterir."""
    st.markdown("### ⏮️ Adım Adım Geri Oynatma")
    if len(history) < 1:
        st.info("Geri oynatma için en az 1 adım çalıştır.")
        return

    steps = [r["step"] for r in history]

    # Tek adım varsa slider gösteremeyiz (min==max → RangeError).
    # Direkt o adımın verilerini gösterip çıkıyoruz.
    if len(steps) < 2:
        rec = history[0]
        st.info(f"Adım **{steps[0]}** gösteriliyor. Birden fazla adım çalıştırınca kaydırıcı aktif olur.")
        g1, g2, g3, g4, g5 = st.columns(5)
        with g1: st.plotly_chart(gauge(rec["s_temperature"], "Sıcaklık", " °C", 0, 50, warn_hi=35), width="stretch", key="pb1_t")
        with g2: st.plotly_chart(gauge(rec["s_air_humidity"], "Hava Nemi", "%", warn_hi=80, warn_lo=30), width="stretch", key="pb1_ah")
        with g3: st.plotly_chart(gauge(rec["s_soil_moisture"], "Toprak Nemi", "%", warn_lo=30), width="stretch", key="pb1_sm")
        with g4: st.plotly_chart(gauge(rec["s_light_level"], "Işık", "%", warn_hi=85), width="stretch", key="pb1_ll")
        with g5: st.plotly_chart(gauge(rec["s_water_tank_level"], "Su Tankı", "%", warn_lo=25), width="stretch", key="pb1_wt")
        return

    # Navigasyon butonları slider'dan ÖNCE — state'i slider oluşmadan güncelliyoruz
    nav_left, nav_mid, nav_right = st.columns([1, 4, 1])

    # Mevcut seçili adımı ayrı bir state'de tutuyoruz
    if "playback_step" not in st.session_state or st.session_state.playback_step not in steps:
        st.session_state.playback_step = steps[-1]

    # Yeni adım geldiğinde: kullanıcı önceki son adımdaysa otomatik ilerle,
    # geri çekilmişse dokunma.
    prev_max = st.session_state.get("playback_last_max", steps[-1])
    if steps[-1] > prev_max:
        # Yeni adım eklendi
        if st.session_state.playback_step == prev_max:
            # Kullanıcı frontier'daydı → yeni sona atla
            st.session_state.playback_step = steps[-1]
    st.session_state.playback_last_max = steps[-1]

    current_idx = steps.index(st.session_state.playback_step)

    with nav_left:
        if st.button("◀ Önceki", key="pb_prev", width="stretch", disabled=(current_idx == 0)):
            st.session_state.playback_step = steps[current_idx - 1]
            st.rerun()

    with nav_right:
        if st.button("Sonraki ▶", key="pb_next", width="stretch", disabled=(current_idx == len(steps) - 1)):
            st.session_state.playback_step = steps[current_idx + 1]
            st.rerun()

    with nav_mid:
        # Slider kendi key'ini (playback_slider) iç cache'den okur, value= parametresini yeniden
        # render'da görmezden gelir. Bu yüzden slider OLUŞTURULMADAN ÖNCE key'i güncelliyoruz.
        # Bu Streamlit'in izin verdiği tek doğru pattern'dir.
        st.session_state["playback_slider"] = st.session_state.playback_step
        selected = st.select_slider(
            "İncelemek istediğin adımı seç:",
            options=steps,
            key="playback_slider",
            label_visibility="collapsed",
        )
        # Kullanıcı slider'ı elle hareket ettirdiyse state'i güncelle
        st.session_state.playback_step = selected

    idx = steps.index(selected)
    rec = history[idx]
    prev = history[idx - 1] if idx > 0 else None

    st.markdown(f"##### Adım **{selected}** / {steps[-1]} — Sensör Okumaları & Sera Durumu")

    col_info, col_delta = st.columns([2, 1])

    with col_info:
        g1, g2, g3, g4, g5 = st.columns(5)
        with g1: st.plotly_chart(gauge(rec["s_temperature"], "Sıcaklık", " °C", 0, 50, warn_hi=35), width="stretch", key=f"pb_t_{selected}")
        with g2: st.plotly_chart(gauge(rec["s_air_humidity"], "Hava Nemi", "%", warn_hi=80, warn_lo=30), width="stretch", key=f"pb_ah_{selected}")
        with g3: st.plotly_chart(gauge(rec["s_soil_moisture"], "Toprak Nemi", "%", warn_lo=30), width="stretch", key=f"pb_sm_{selected}")
        with g4: st.plotly_chart(gauge(rec["s_light_level"], "Işık", "%", warn_hi=85), width="stretch", key=f"pb_ll_{selected}")
        with g5: st.plotly_chart(gauge(rec["s_water_tank_level"], "Su Tankı", "%", warn_lo=25), width="stretch", key=f"pb_wt_{selected}")

        st.markdown("**Üretilen Kontrol Kararları**")
        a1, a2, a3, a4 = st.columns(4)
        with a1: st.plotly_chart(gauge(rec["irrigation_level"], "💧 Sulama", "/100"), width="stretch", key=f"pb_irr_{selected}")
        with a2: st.plotly_chart(gauge(rec["ventilation_level"], "💨 Fan", "/100"), width="stretch", key=f"pb_vent_{selected}")
        with a3: st.plotly_chart(gauge(rec["shading_level"], "🌫️ Gölge", "/100"), width="stretch", key=f"pb_shade_{selected}")
        with a4: st.plotly_chart(gauge(rec["alarm_level"], "🚨 Alarm", "/100", alarm_mode=True), width="stretch", key=f"pb_alarm_{selected}")

    with col_delta:
        st.markdown("**📊 Önceki Adıma Göre Değişim**")
        if prev is None:
            st.info("İlk adım — önceki adım yok.")
        else:
            fields = [
                ("temperature", "🌡 Sıcaklık", "°C"),
                ("air_humidity", "💧 Hava Nemi", "%"),
                ("soil_moisture", "🌱 Toprak Nemi", "%"),
                ("light_level", "☀️ Işık", "%"),
                ("water_tank_level", "🚰 Su Tankı", "%"),
                ("irrigation_level", "💧 Sulama", "/100"),
                ("ventilation_level", "💨 Fan", "/100"),
                ("shading_level", "🌫️ Gölge", "/100"),
                ("alarm_level", "🚨 Alarm", "/100"),
            ]
            rows = []
            for key, label, unit in fields:
                curr_val = rec[key]
                prev_val = prev[key]
                delta = curr_val - prev_val
                arrow = "🔺" if delta > 0.05 else ("🔻" if delta < -0.05 else "➖")
                rows.append({"Değişken": label, "Şu An": f"{curr_val:.1f}{unit}", "Değişim": f"{arrow} {delta:+.1f}"})
            df_delta = pd.DataFrame(rows)
            st.dataframe(df_delta, hide_index=True, width="stretch", key=f"delta_table_{selected}")


def render_alarm_timeline(history: list) -> None:
    """Hangi adımda alarm çıktığını renkli bar grafikle gösterir."""
    st.markdown("### 🚨 Alarm Zaman Çizelgesi")
    if not history:
        st.info("Alarm geçmişi için en az 1 adım çalıştır.")
        return
    df = pd.DataFrame(history)
    colors = ["#ff2222" if v >= 75 else ("#ffaa00" if v >= 50 else "#1a4a2a") for v in df["alarm_level"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["step"], y=df["alarm_level"],
        marker_color=colors, name="Alarm",
        text=[f"{v:.0f}" if v >= 50 else "" for v in df["alarm_level"]],
        textposition="outside", textfont=dict(color="#ffaaaa", size=10),
    ))
    fig.add_hline(y=75, line=dict(color="#ff2222", dash="dash", width=1.5), annotation_text="Kritik (75)", annotation_font_color="#ff4444")
    fig.add_hline(y=50, line=dict(color="#ffaa00", dash="dot", width=1),   annotation_text="Uyarı (50)",  annotation_font_color="#ffaa00")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(title="Adım", gridcolor="#1a3a2a", tickfont=dict(color="#5a8a6a")),
        yaxis=dict(title="Alarm Seviyesi", range=[0, 115], gridcolor="#1a3a2a", tickfont=dict(color="#5a8a6a")),
        height=250, margin=dict(l=10, r=80, t=10, b=30), showlegend=False,
    )
    st.plotly_chart(fig, width="stretch", key="alarm_timeline")
    alarm_steps = df[df["alarm_level"] >= 50]["step"].tolist()
    if alarm_steps:
        st.caption(f"⚠️ Alarm tetiklenen adımlar: {alarm_steps}")
    else:
        st.caption("✅ Hiç alarm tetiklenmedi.")


def render_fuzzy_curves(readings) -> None:
    """Her giriş değişkeni için trapezoid/üçgen üyelik fonksiyonu eğrilerini çizer."""
    import numpy as np

    st.markdown("### 📐 Bulanık Üyelik Fonksiyonu Eğrileri")
    if readings is None:
        st.info("Eğriler için en az 1 adım çalıştır.")
        return

    # (değer, [set_adı, tip, parametreler, renk], başlık, x_max)
    VAR_DEFS = {
        "temperature": {
            "title": "🌡 Sıcaklık (°C)", "value": readings.temperature, "xmax": 50,
            "sets": [
                ("Düşük",  "trap", (0,0,15,22),   "#4fc3f7"),
                ("Normal", "tri",  (18,25,32),     "#ffd93d"),
                ("Yüksek", "trap", (28,35,50,50),  "#ff6b6b"),
            ],
        },
        "air_humidity": {
            "title": "💧 Hava Nemi (%)", "value": readings.air_humidity, "xmax": 100,
            "sets": [
                ("Düşük",  "trap", (0,0,35,50),    "#4fc3f7"),
                ("Normal", "tri",  (40,55,70),      "#ffd93d"),
                ("Yüksek", "trap", (60,75,100,100), "#ff6b6b"),
            ],
        },
        "soil_moisture": {
            "title": "🌱 Toprak Nemi (%)", "value": readings.soil_moisture, "xmax": 100,
            "sets": [
                ("Kuru",   "trap", (0,0,25,40),    "#ff6b6b"),
                ("Uygun",  "tri",  (35,55,75),     "#ffd93d"),
                ("Islak",  "trap", (65,80,100,100),"#4fc3f7"),
            ],
        },
        "light_level": {
            "title": "☀️ Işık (%)", "value": readings.light_level, "xmax": 100,
            "sets": [
                ("Düşük",  "trap", (0,0,25,40),    "#4fc3f7"),
                ("Orta",   "tri",  (30,55,75),     "#ffd93d"),
                ("Yüksek", "trap", (65,80,100,100),"#ff6b6b"),
            ],
        },
        "water_tank_level": {
            "title": "🚰 Su Tankı (%)", "value": readings.water_tank_level, "xmax": 100,
            "sets": [
                ("Düşük",   "trap", (0,0,20,35),    "#ff6b6b"),
                ("Orta",    "tri",  (25,50,75),     "#ffd93d"),
                ("Yeterli", "trap", (65,80,100,100),"#00c896"),
            ],
        },
    }

    def trap(x, a, b, c, d):
        if a == b and x <= b: return 1.0
        if c == d and x >= c: return 1.0
        if x <= a or x >= d:  return 0.0
        if a < x < b: return (x - a) / (b - a)
        if b <= x <= c: return 1.0
        return (d - x) / (d - c)

    def tri(x, l, c, r):
        if x <= l or x >= r: return 0.0
        return (x - l)/(c - l) if x <= c else (r - x)/(r - c)

    def hex_to_rgba(h: str, alpha: float = 0.12) -> str:
        """'#rrggbb' → 'rgba(r,g,b,alpha)'"""
        h = h.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"

    cols = st.columns(5)
    for col, (key, vdef) in zip(cols, VAR_DEFS.items()):
        xs = np.linspace(0, vdef["xmax"], 300)
        fig = go.Figure()
        for sname, stype, sparams, scolor in vdef["sets"]:
            if stype == "trap":
                ys = [trap(x, *sparams) for x in xs]
            else:
                ys = [tri(x, *sparams) for x in xs]
            fig.add_trace(go.Scatter(
                x=list(xs), y=ys, name=sname,
                mode="lines", line=dict(color=scolor, width=2),
                fill="tozeroy", fillcolor=hex_to_rgba(scolor),
            ))
        # Sensörün şu anki değerini dikey çizgi olarak göster
        cur = vdef["value"]
        fig.add_vline(x=cur, line=dict(color="#ffffff", dash="dash", width=1.5),
                      annotation_text=f"{cur:.1f}", annotation_font_color="#ffffff",
                      annotation_position="top right")
        fig.update_layout(
            title=dict(text=vdef["title"], font=dict(color="#a8d8b8", size=11), x=0.5),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(range=[0, vdef["xmax"]], gridcolor="#1a3a2a", tickfont=dict(color="#5a8a6a"), tickfont_size=8),
            yaxis=dict(range=[0, 1.15], gridcolor="#1a3a2a", tickfont=dict(color="#5a8a6a"), tickfont_size=8),
            legend=dict(font=dict(color="#a8d8b8", size=8), bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.3),
            height=220, margin=dict(l=8, r=8, t=36, b=8), showlegend=True,
        )
        with col:
            st.plotly_chart(fig, width="stretch", key=f"fuzzy_curve_{key}")


def render_history(history):
    st.markdown("### 📈 Simülasyon Geçmişi")
    if not history:
        st.info("Grafik için en az bir adım çalıştır.")
        return
    df = pd.DataFrame(history)

    fig1 = go.Figure()
    env_cols = {"temperature": ("🌡 Sıcaklık", "#ff6b6b"), "air_humidity": ("💧 Hava Nemi", "#4ecdc4"),
                "soil_moisture": ("🌱 Toprak Nemi", "#45b7d1"), "light_level": ("☀️ Işık", "#ffd93d"),
                "water_tank_level": ("🚰 Su Tankı", "#96ceb4")}
    for col, (name, color) in env_cols.items():
        fig1.add_trace(go.Scatter(x=df["step"], y=df[col], name=name, line=dict(color=color, width=2)))
    fig1.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                       legend=dict(font=dict(color="#a8d8b8"), bgcolor="rgba(0,0,0,0)"),
                       xaxis=dict(title="Adım", gridcolor="#1a3a2a", tickfont=dict(color="#5a8a6a")),
                       yaxis=dict(gridcolor="#1a3a2a", tickfont=dict(color="#5a8a6a")),
                       height=320, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig1, width="stretch", key="hist_env")

    fig2 = go.Figure()
    act_cols = {"irrigation_level": ("💧 Sulama", "#00c896"), "ventilation_level": ("💨 Havalandırma", "#00a8ff"),
                "shading_level": ("🌫️ Gölgeleme", "#a8d8b8"), "alarm_level": ("🚨 Alarm", "#ff4444")}
    for col, (name, color) in act_cols.items():
        fig2.add_trace(go.Scatter(x=df["step"], y=df[col], name=name, line=dict(color=color, width=2)))
    fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                       legend=dict(font=dict(color="#a8d8b8"), bgcolor="rgba(0,0,0,0)"),
                       xaxis=dict(title="Adım", gridcolor="#1a3a2a", tickfont=dict(color="#5a8a6a")),
                       yaxis=dict(gridcolor="#1a3a2a", tickfont=dict(color="#5a8a6a"), range=[0, 105]),
                       height=320, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig2, width="stretch", key="hist_act")

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 CSV İndir", csv, "simulasyon_gecmisi.csv", "text/csv", width="stretch")


def main():
    inject_css()

    st.title("🌱 Akıllı Sera Yönetim ve Karar Destek Sistemi")
    st.caption("Bulanık mantık tabanlı uzman sistem | Yazılım simülasyonu")

    # --- Sidebar ---
    st.sidebar.title("🎛️ Kontrol Paneli")
    noise_enabled = st.sidebar.checkbox("📡 Sensör ölçüm hatası aktif", value=True)
    noise_level = st.sidebar.slider("📶 Gürültü Şiddeti", 0.0, 5.0, 1.0, 0.5,
                                    help="0 = gürültüsüz, 5 = çok gürültülü",
                                    disabled=not noise_enabled)
    initial_state, active_plant = sidebar_controls(noise_enabled, noise_level)

    st.sidebar.divider()
    st.sidebar.header("▶️ Simülasyon Kontrolü")

    if st.sidebar.button("🔄 Simülasyonu Sıfırla", width="stretch"):
        initialize_session_state(initial_state, noise_enabled)
        st.rerun()

    if st.sidebar.button("⏭️ Bir Adım Çalıştır", width="stretch"):
        st.session_state.sensors.noise_enabled = noise_enabled
        run_step()
        st.rerun()

    run_count = st.sidebar.number_input("Çoklu adım sayısı", 1, 100, 5, 1)
    if st.sidebar.button("⏩ Çoklu Adım Çalıştır", width="stretch"):
        st.session_state.sensors.noise_enabled = noise_enabled
        for _ in range(int(run_count)):
            run_step()
        st.rerun()

    st.sidebar.divider()
    st.sidebar.header("🤖 Otomatik Simülasyon")
    auto_mode = st.sidebar.toggle("Otomatik Mod", value=False)
    auto_interval = st.sidebar.slider("Hız (saniye)", 0.5, 5.0, 1.5, 0.5)

    ensure_initialized(initial_state, noise_enabled)
    # Gürültü şiddetini sensöre uygula
    if hasattr(st.session_state.sensors, 'noise_level'):
        st.session_state.sensors.noise_level = noise_level

    state = st.session_state.simulator.get_state()
    actions = st.session_state.last_actions
    readings = st.session_state.last_readings
    rules = st.session_state.last_rules
    explanation = st.session_state.last_explanation
    history = st.session_state.history

    # --- Alarm Banner ---
    render_alarm_banner(actions)

    # --- KPI ---
    render_kpi(history)

    st.divider()

    # --- Sensor Gauges + Radar ---
    left, right = st.columns([3, 1])
    with left:
        render_sensor_gauges(state, readings)
    with right:
        st.markdown("### 🕸️ Radar")
        st.plotly_chart(render_radar(state), width="stretch", key="radar")

    st.divider()

    # --- Control Actions ---
    render_action_gauges(actions)

    st.divider()

    # --- Fuzzy Membership (bar) + Fuzzy Curves ---
    if readings is not None:
        render_membership(readings, st.session_state.fuzzy_engine)
        st.divider()
        render_fuzzy_curves(readings)
        st.divider()

    # --- Rules ---
    render_rules(rules)

    st.divider()

    # --- Explanation ---
    render_explanation(explanation)

    st.divider()

    # --- Alarm Timeline ---
    render_alarm_timeline(history)

    st.divider()

    # --- Playback ---
    render_playback(history)

    st.divider()

    # --- History ---
    render_history(history)

    st.markdown('<div style="text-align:center;color:rgba(160,180,170,0.4);font-size:.72rem;margin-top:24px">Akıllı Sera Yönetim Sistemi v2 · Bulanık Mantık Tabanlı Karar Destek</div>', unsafe_allow_html=True)

    # --- Auto Simulation ---
    if auto_mode:
        st.session_state.sensors.noise_enabled = noise_enabled
        run_step()
        time.sleep(auto_interval)
        st.rerun()


if __name__ == "__main__":
    main()