"""
dashboard.py

Bu dosya, Akıllı Sera Yönetim ve Karar Destek Sistemi için Streamlit tabanlı
görsel kullanıcı arayüzünü içerir.

Dashboard'un amacı:
    - Sera ortamının anlık durumunu göstermek
    - Sanal sensör okumalarını göstermek
    - Fuzzy karar motorunun ürettiği kontrol aksiyonlarını göstermek
    - Karar açıklamalarını kullanıcıya sunmak
    - Tetiklenen fuzzy kuralları görüntülemek
    - Simülasyon geçmişini tablo ve grafiklerle izlemek

Bu dosya projenin terminal demosundan sonraki ilk görsel arayüz aşamasıdır.
Fiziksel donanım kullanılmadan, tamamen yazılım tabanlı sera simülasyonu üzerinden
çalışır.
"""

from __future__ import annotations

from typing import Dict, List

import pandas as pd
import streamlit as st

from src.decision.fuzzy_engine import FuzzyEngine, RuleActivation
from src.explanation.explanation_engine import DecisionExplanation, ExplanationEngine
from src.simulation.greenhouse_state import GreenhouseState
from src.simulation.greenhouse_simulator import GreenhouseSimulator
from src.simulation.virtual_sensors import SensorReadings, VirtualSensorReader
from src.simulation.scenario_profiles import get_scenario_by_name, get_scenario_profiles


# -----------------------------------------------------------------------------
# Sayfa ayarları
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="Akıllı Sera Yönetim Sistemi",
    page_icon="🌱",
    layout="wide",
)


def create_initial_state_from_sidebar() -> GreenhouseState:
    """
    Sidebar üzerindeki kullanıcı ayarlarından başlangıç sera durumunu oluşturur.

    Bu fonksiyon, kullanıcının farklı başlangıç koşullarıyla simülasyon başlatmasını
    sağlar. Böylece dashboard üzerinden farklı sera senaryoları test edilebilir.
    """

    st.sidebar.header("Başlangıç Değerleri")

    temperature = st.sidebar.slider(
        "Sıcaklık (°C)",
        min_value=0.0,
        max_value=50.0,
        value=25.0,
        step=0.5,
    )

    air_humidity = st.sidebar.slider(
        "Hava Nemi (%)",
        min_value=0.0,
        max_value=100.0,
        value=50.0,
        step=1.0,
    )

    soil_moisture = st.sidebar.slider(
        "Toprak Nemi (%)",
        min_value=0.0,
        max_value=100.0,
        value=45.0,
        step=1.0,
    )

    light_level = st.sidebar.slider(
        "Işık Seviyesi (%)",
        min_value=0.0,
        max_value=100.0,
        value=60.0,
        step=1.0,
    )

    water_tank_level = st.sidebar.slider(
        "Su Tankı Seviyesi (%)",
        min_value=0.0,
        max_value=100.0,
        value=80.0,
        step=1.0,
    )

    return GreenhouseState(
        temperature=temperature,
        air_humidity=air_humidity,
        soil_moisture=soil_moisture,
        light_level=light_level,
        water_tank_level=water_tank_level,
    )


def initialize_session_state(initial_state: GreenhouseState, noise_enabled: bool) -> None:
    """
    Streamlit session_state içinde sistem bileşenlerini başlatır.

    Streamlit her kullanıcı etkileşiminde dosyayı yeniden çalıştırır.
    Bu nedenle simülasyon nesnelerini doğrudan global değişkende tutmak yerine
    session_state içinde saklıyoruz.
    """

    st.session_state.simulator = GreenhouseSimulator(initial_state=initial_state)
    st.session_state.sensors = VirtualSensorReader(noise_enabled=noise_enabled)
    st.session_state.fuzzy_engine = FuzzyEngine()
    st.session_state.explanation_engine = ExplanationEngine()

    # Simülasyon geçmişi dashboard grafikleri için bellekte tutulur.
    st.session_state.history = []

    # Son üretilen karar ve açıklama başlangıçta yoktur.
    st.session_state.last_readings = None
    st.session_state.last_actions = None
    st.session_state.last_explanation = None
    st.session_state.last_rules = []
    st.session_state.step_count = 0


def ensure_system_initialized(initial_state: GreenhouseState, noise_enabled: bool) -> None:
    """
    Sistem daha önce başlatılmadıysa session_state içine gerekli nesneleri oluşturur.
    """

    if "simulator" not in st.session_state:
        initialize_session_state(
            initial_state=initial_state,
            noise_enabled=noise_enabled,
        )


def run_one_simulation_step() -> None:
    """
    Simülasyonu bir adım çalıştırır.

    Akış:
        1. Mevcut sera durumu alınır.
        2. Sanal sensörler okunur.
        3. Fuzzy karar motoru aksiyon üretir.
        4. Açıklama motoru karar gerekçesi üretir.
        5. Aksiyonlar simülasyon ortamına uygulanır.
        6. Doğal çevresel değişim uygulanır.
        7. Tüm sonuçlar history listesine eklenir.
    """

    simulator: GreenhouseSimulator = st.session_state.simulator
    sensors: VirtualSensorReader = st.session_state.sensors
    fuzzy_engine: FuzzyEngine = st.session_state.fuzzy_engine
    explanation_engine: ExplanationEngine = st.session_state.explanation_engine

    st.session_state.step_count += 1

    # Aksiyon öncesi sera durumunu kopyalıyoruz.
    # Çünkü apply_actions ve step çağrıları mevcut state'i değiştirecek.
    state_before = GreenhouseState(**simulator.get_state().to_dict())

    readings = sensors.read_all(state_before)

    actions = fuzzy_engine.evaluate(readings)
    rules = fuzzy_engine.get_last_rule_activations()

    explanation = explanation_engine.generate(
        readings=readings,
        actions=actions,
        rule_activations=rules,
    )

    simulator.apply_actions(
        irrigation_level=actions.irrigation_level,
        ventilation_level=actions.ventilation_level,
        shading_level=actions.shading_level,
    )

    simulator.step()

    state_after = GreenhouseState(**simulator.get_state().to_dict())

    # Son değerleri session_state içinde saklıyoruz.
    st.session_state.last_readings = readings
    st.session_state.last_actions = actions
    st.session_state.last_explanation = explanation
    st.session_state.last_rules = rules

    # Grafik ve tablo için geçmişe kayıt ekliyoruz.
    st.session_state.history.append(
        {
            "step": st.session_state.step_count,
            "temperature": state_after.temperature,
            "air_humidity": state_after.air_humidity,
            "soil_moisture": state_after.soil_moisture,
            "light_level": state_after.light_level,
            "water_tank_level": state_after.water_tank_level,
            "irrigation_level": actions.irrigation_level,
            "ventilation_level": actions.ventilation_level,
            "shading_level": actions.shading_level,
            "alarm_level": actions.alarm_level,
        }
    )


def state_to_metric_columns(state: GreenhouseState) -> None:
    """
    Güncel sera durumunu Streamlit metric bileşenleriyle gösterir.
    """

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Sıcaklık", f"{state.temperature:.1f} °C")
    col2.metric("Hava Nemi", f"%{state.air_humidity:.1f}")
    col3.metric("Toprak Nemi", f"%{state.soil_moisture:.1f}")
    col4.metric("Işık", f"%{state.light_level:.1f}")
    col5.metric("Su Tankı", f"%{state.water_tank_level:.1f}")


def render_sensor_readings(readings: SensorReadings | None) -> None:
    """
    Son sanal sensör okumalarını gösterir.
    """

    st.subheader("Sanal Sensör Okumaları")

    if readings is None:
        st.info("Henüz sensör okuması yapılmadı. Simülasyonu bir adım çalıştır.")
        return

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Sensör Sıcaklık", f"{readings.temperature:.1f} °C")
    col2.metric("Sensör Hava Nemi", f"%{readings.air_humidity:.1f}")
    col3.metric("Sensör Toprak Nemi", f"%{readings.soil_moisture:.1f}")
    col4.metric("Sensör Işık", f"%{readings.light_level:.1f}")
    col5.metric("Sensör Su Tankı", f"%{readings.water_tank_level:.1f}")


def render_control_actions(actions) -> None:
    """
    Fuzzy karar motorunun ürettiği kontrol aksiyonlarını gösterir.
    """

    st.subheader("Üretilen Kontrol Aksiyonları")

    if actions is None:
        st.info("Henüz kontrol kararı üretilmedi.")
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Sulama", f"{actions.irrigation_level:.1f}/100")
        st.progress(int(actions.irrigation_level))

    with col2:
        st.metric("Havalandırma", f"{actions.ventilation_level:.1f}/100")
        st.progress(int(actions.ventilation_level))

    with col3:
        st.metric("Gölgeleme", f"{actions.shading_level:.1f}/100")
        st.progress(int(actions.shading_level))

    with col4:
        st.metric("Alarm", f"{actions.alarm_level:.1f}/100")
        st.progress(int(actions.alarm_level))


def render_explanation(explanation: DecisionExplanation | None) -> None:
    """
    Karar açıklama modülünün ürettiği açıklamaları gösterir.
    """

    st.subheader("Karar Açıklaması")

    if explanation is None:
        st.info("Henüz karar açıklaması üretilmedi.")
        return

    st.write(explanation.summary)

    if explanation.warnings:
        st.warning("Sistem uyarı üretti:")
        for warning in explanation.warnings:
            st.write(f"- {warning}")

    with st.expander("Aksiyon Açıklamaları"):
        for item in explanation.action_explanations:
            st.write(f"- {item}")

    with st.expander("Tetiklenen Kural Açıklamaları"):
        for item in explanation.active_rule_explanations:
            st.write(f"- {item}")


def rules_to_dataframe(rules: List[RuleActivation]) -> pd.DataFrame:
    """
    Tetiklenen fuzzy kuralları pandas DataFrame formatına dönüştürür.
    """

    rows = []

    for rule in rules:
        rows.append(
            {
                "Kural": rule.rule_name,
                "Aktivasyon (%)": round(rule.activation * 100, 2),
                "Sulama Çıktısı": rule.irrigation_output,
                "Havalandırma Çıktısı": rule.ventilation_output,
                "Gölgeleme Çıktısı": rule.shading_output,
                "Alarm Çıktısı": rule.alarm_output,
            }
        )

    return pd.DataFrame(rows)


def render_active_rules(rules: List[RuleActivation]) -> None:
    """
    Tetiklenen fuzzy kuralları tablo halinde gösterir.
    """

    st.subheader("Tetiklenen Fuzzy Kurallar")

    if not rules:
        st.info("Henüz tetiklenen kural yok.")
        return

    df = rules_to_dataframe(rules)
    df = df.sort_values(by="Aktivasyon (%)", ascending=False)

    st.dataframe(df, use_container_width=True)


def render_history_charts(history: List[Dict[str, float]]) -> None:
    """
    Simülasyon geçmişini grafik ve tablo olarak gösterir.
    """

    st.subheader("Simülasyon Geçmişi")

    if not history:
        st.info("Grafik oluşturmak için en az bir simülasyon adımı çalıştır.")
        return

    df = pd.DataFrame(history)

    st.write("Çevresel değişkenler:")
    st.line_chart(
        df.set_index("step")[
            [
                "temperature",
                "air_humidity",
                "soil_moisture",
                "light_level",
                "water_tank_level",
            ]
        ]
    )

    st.write("Kontrol aksiyonları:")
    st.line_chart(
        df.set_index("step")[
            [
                "irrigation_level",
                "ventilation_level",
                "shading_level",
                "alarm_level",
            ]
        ]
    )

    with st.expander("Ham Simülasyon Geçmişi"):
        st.dataframe(df, use_container_width=True)


def main() -> None:
    """
    Dashboard ana çalıştırma fonksiyonu.
    """

    st.title("🌱 Akıllı Sera Yönetim ve Karar Destek Sistemi")

    st.write(
        "Bu dashboard, sera ortamını yazılım tabanlı olarak simüle eder; "
        "sanal sensör verilerini fuzzy uzman sistem ile değerlendirir ve "
        "sulama, havalandırma, gölgeleme ve alarm kararları üretir."
    )

    st.sidebar.title("Kontrol Paneli")

    noise_enabled = st.sidebar.checkbox(
        "Sensör ölçüm hatası aktif",
        value=True,
        help="Aktif olduğunda sanal sensör değerlerine küçük rastgele sapmalar eklenir.",
    )

    st.sidebar.header("Hazır Senaryolar")

    scenario_profiles = get_scenario_profiles()
    scenario_names = [scenario.name for scenario in scenario_profiles]

    selected_scenario_name = st.sidebar.selectbox(
        "Senaryo Seç",
        options=scenario_names,
        help="Hazır senaryolar, fuzzy karar motorunun davranışını hızlı test etmek için kullanılır.",
    )

    selected_scenario = get_scenario_by_name(selected_scenario_name)

    st.sidebar.caption(selected_scenario.description)

    with st.sidebar.expander("Beklenen Davranış"):
        st.write(selected_scenario.expected_behavior)

    if st.sidebar.button("Seçili Senaryoyu Yükle", use_container_width=True):
        initialize_session_state(
            initial_state=selected_scenario.state,
            noise_enabled=noise_enabled,
        )
        st.rerun()

    initial_state = create_initial_state_from_sidebar()

    ensure_system_initialized(
        initial_state=initial_state,
        noise_enabled=noise_enabled,
    )

    st.sidebar.divider()

    if st.sidebar.button("Simülasyonu Sıfırla", use_container_width=True):
        initialize_session_state(
            initial_state=initial_state,
            noise_enabled=noise_enabled,
        )
        st.rerun()

    if st.sidebar.button("Bir Adım Çalıştır", use_container_width=True):
        # Noise ayarı kullanıcı tarafından değiştirildiyse sensör okuyucuyu güncelliyoruz.
        st.session_state.sensors.noise_enabled = noise_enabled
        run_one_simulation_step()
        st.rerun()

    run_count = st.sidebar.number_input(
        "Çoklu adım sayısı",
        min_value=1,
        max_value=100,
        value=5,
        step=1,
    )

    if st.sidebar.button("Çoklu Adım Çalıştır", use_container_width=True):
        st.session_state.sensors.noise_enabled = noise_enabled

        for _ in range(int(run_count)):
            run_one_simulation_step()

        st.rerun()

    current_state = st.session_state.simulator.get_state()

    st.header("Anlık Sera Durumu")
    state_to_metric_columns(current_state)

    st.divider()

    render_sensor_readings(st.session_state.last_readings)

    st.divider()

    render_control_actions(st.session_state.last_actions)

    st.divider()

    render_explanation(st.session_state.last_explanation)

    st.divider()

    render_active_rules(st.session_state.last_rules)

    st.divider()

    render_history_charts(st.session_state.history)


if __name__ == "__main__":
    main()