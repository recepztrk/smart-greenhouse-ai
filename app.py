"""
app.py

Bu dosya, Akıllı Sera Yönetim ve Karar Destek Sistemi projesinin ilk uçtan uca
terminal demosunu çalıştırır.

Bu aşamada henüz Streamlit dashboard kullanılmamaktadır. Amaç, sistemin temel
çekirdeğinin doğru çalıştığını terminal üzerinden doğrulamaktır.

Demo akışı:
    1. Sera simülasyonu başlatılır.
    2. Sanal sensörler mevcut sera durumunu okur.
    3. Fuzzy karar motoru sensör verilerini değerlendirir.
    4. Sulama, havalandırma, gölgeleme ve alarm kararları üretilir.
    5. Açıklama modülü kararların nedenlerini üretir.
    6. Kontrol aksiyonları simülasyon ortamına uygulanır.
    7. Simülasyon bir zaman adımı ilerletilir.

Bu dosya, dashboard geliştirilmeden önce sistemin mantıksal olarak çalıştığını
kanıtlayan ilk ana çalıştırma dosyasıdır.
"""

from __future__ import annotations

import argparse
import time
from typing import List

from src.decision.actions import ControlActions
from src.decision.fuzzy_engine import FuzzyEngine, RuleActivation
from src.explanation.explanation_engine import DecisionExplanation, ExplanationEngine
from src.simulation.greenhouse_state import GreenhouseState
from src.simulation.greenhouse_simulator import GreenhouseSimulator
from src.simulation.virtual_sensors import SensorReadings, VirtualSensorReader
from src.utils.logger import SimulationLogger

def format_state(state: GreenhouseState) -> str:
    """
    Sera durumunu terminalde okunabilir tek satırlık metne dönüştürür.
    """

    return (
        f"Sıcaklık: {state.temperature:.1f} °C | "
        f"Hava Nemi: %{state.air_humidity:.1f} | "
        f"Toprak Nemi: %{state.soil_moisture:.1f} | "
        f"Işık: %{state.light_level:.1f} | "
        f"Su Tankı: %{state.water_tank_level:.1f}"
    )


def format_readings(readings: SensorReadings) -> str:
    """
    Sanal sensör okumalarını terminalde okunabilir tek satırlık metne dönüştürür.

    Not:
        Noise aktifse bu değerler GreenhouseState ile birebir aynı olmayabilir.
        Bu fark gerçek sensörlerdeki küçük ölçüm sapmalarını temsil eder.
    """

    return (
        f"Sıcaklık: {readings.temperature:.1f} °C | "
        f"Hava Nemi: %{readings.air_humidity:.1f} | "
        f"Toprak Nemi: %{readings.soil_moisture:.1f} | "
        f"Işık: %{readings.light_level:.1f} | "
        f"Su Tankı: %{readings.water_tank_level:.1f}"
    )


def format_actions(actions: ControlActions) -> str:
    """
    Fuzzy karar motorunun ürettiği kontrol aksiyonlarını okunabilir hale getirir.
    """

    return (
        f"Sulama: {actions.irrigation_level:.1f}/100 | "
        f"Havalandırma: {actions.ventilation_level:.1f}/100 | "
        f"Gölgeleme: {actions.shading_level:.1f}/100 | "
        f"Alarm: {actions.alarm_level:.1f}/100"
    )


def print_top_rules(rule_activations: List[RuleActivation], limit: int = 3) -> None:
    """
    En güçlü tetiklenen fuzzy kuralları terminale yazdırır.

    Çok fazla kural tetiklenirse terminal çıktısı kalabalıklaşabilir.
    Bu nedenle varsayılan olarak en etkili ilk 3 kural gösterilir.
    """

    if not rule_activations:
        print("Tetiklenen Kural: Yok")
        return

    sorted_rules = sorted(
        rule_activations,
        key=lambda rule: rule.activation,
        reverse=True,
    )

    print("En Etkili Kurallar:")

    for index, rule in enumerate(sorted_rules[:limit], start=1):
        print(f"  {index}. {rule.rule_name} | Aktivasyon: %{rule.activation * 100:.1f}")


def print_explanation(explanation: DecisionExplanation) -> None:
    """
    Açıklama modülünden gelen özet ve uyarıları terminale yazdırır.

    Terminal demosunda tüm aksiyon açıklamalarını ve tüm kuralları basmak yerine
    çıktıyı okunabilir tutmak için özet + uyarılar gösterilir.
    Detaylı açıklamalar daha sonra dashboard üzerinde daha geniş gösterilebilir.
    """

    print(f"Özet: {explanation.summary}")

    if explanation.warnings:
        print("Uyarılar:")
        for warning in explanation.warnings:
            print(f"  - {warning}")


def run_demo(steps: int, delay: float, noise_enabled: bool) -> None:
    """
    Akıllı sera sisteminin uçtan uca terminal demosunu çalıştırır.

    Args:
        steps:
            Simülasyonun kaç adım çalışacağı.

        delay:
            Her adım arasında kaç saniye beklenileceği.

        noise_enabled:
            Sanal sensörlerde ölçüm hatası/noise kullanılıp kullanılmayacağı.
    """

    simulator = GreenhouseSimulator()
    sensors = VirtualSensorReader(noise_enabled=noise_enabled)
    fuzzy_engine = FuzzyEngine()
    explanation_engine = ExplanationEngine()

    # Her demo çalışmasında temiz bir log dosyası oluşturuyoruz.
    logger = SimulationLogger()
    logger.clear_logs()

    print("=" * 80)
    print("AKILLI SERA YÖNETİM VE KARAR DESTEK SİSTEMİ - TERMİNAL DEMO")
    print("=" * 80)
    print(f"Simülasyon adım sayısı: {steps}")
    print(f"Sensör noise durumu: {'Aktif' if noise_enabled else 'Kapalı'}")
    print("=" * 80)

    for step_index in range(1, steps + 1):
        print(f"\nADIM {step_index}")
        print("-" * 80)

        # 1. Mevcut simülasyon durumunu alıyoruz.
        current_state = simulator.get_state()
        # Mevcut sera durumunun kopyasını alıyoruz.
        # Çünkü birazdan aksiyonlar uygulanınca simulator içindeki state değişecek.
        state_before_snapshot = GreenhouseState(**current_state.to_dict())
        print("Mevcut Sera Durumu:")
        print(f"  {format_state(current_state)}")

        # 2. Sanal sensörler mevcut sera durumunu okuyor.
        readings = sensors.read_all(current_state)
        print("Sanal Sensör Okumaları:")
        print(f"  {format_readings(readings)}")

        # 3. Fuzzy karar motoru sensör verilerine göre aksiyon üretiyor.
        actions = fuzzy_engine.evaluate(readings)
        print("Üretilen Kontrol Aksiyonları:")
        print(f"  {format_actions(actions)}")

        # 4. Fuzzy motorun tetiklediği kuralları alıyoruz.
        rule_activations = fuzzy_engine.get_last_rule_activations()
        print_top_rules(rule_activations)

        # 5. Açıklama motoru kararların nedenini açıklıyor.
        explanation = explanation_engine.generate(
            readings=readings,
            actions=actions,
            rule_activations=rule_activations,
        )
        print_explanation(explanation)

        # 6. Üretilen aksiyonları sera simülasyonuna uyguluyoruz.
        simulator.apply_actions(
            irrigation_level=actions.irrigation_level,
            ventilation_level=actions.ventilation_level,
            shading_level=actions.shading_level,
        )

        # 7. Doğal çevresel değişimi uygulayarak simülasyonu bir adım ilerletiyoruz.
        simulator.step()

        # Aksiyon ve doğal değişim sonrası oluşan yeni durumu kaydediyoruz.
        state_after_snapshot = GreenhouseState(**simulator.get_state().to_dict())

        # 8. Bu adımda oluşan tüm önemli verileri CSV log dosyasına yazıyoruz.
        logger.log_step(
            step=step_index,
            state_before=state_before_snapshot,
            readings=readings,
            actions=actions,
            explanation=explanation,
            rule_activations=rule_activations,
            state_after=state_after_snapshot,
        )

        print("Adım Sonrası Sera Durumu:")
        print(f"  {format_state(simulator.get_state())}")

        # Terminal çıktısının daha rahat takip edilmesi için isteğe bağlı bekleme.
        if delay > 0:
            time.sleep(delay)

    print("\n" + "=" * 80)
    print("Demo tamamlandı.")
    print("Log dosyası oluşturuldu: data/simulation_logs.csv")
    print("=" * 80)


def parse_args() -> argparse.Namespace:
    """
    Terminal argümanlarını okur.

    Kullanım örnekleri:
        python app.py
        python app.py --steps 20
        python app.py --steps 20 --delay 0.5
        python app.py --no-noise
    """

    parser = argparse.ArgumentParser(
        description="Akıllı Sera Yönetim ve Karar Destek Sistemi terminal demosu."
    )

    parser.add_argument(
        "--steps",
        type=int,
        default=10,
        help="Simülasyonun kaç adım çalışacağı. Varsayılan: 10",
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Her simülasyon adımı arasında beklenecek saniye. Varsayılan: 0",
    )

    parser.add_argument(
        "--no-noise",
        action="store_true",
        help="Sanal sensörlerdeki rastgele ölçüm hatasını kapatır.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    run_demo(
        steps=args.steps,
        delay=args.delay,
        noise_enabled=not args.no_noise,
    )