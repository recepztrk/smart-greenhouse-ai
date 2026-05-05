"""
run_test_scenarios.py

Bu dosya, Akıllı Sera Yönetim ve Karar Destek Sistemi için önceden tanımlanmış
test senaryolarını çalıştırır.

Amaç:
    - Fuzzy karar motorunun farklı sera koşullarında nasıl davrandığını görmek
    - Karar açıklama modülünün doğru gerekçeler üretip üretmediğini kontrol etmek
    - Proje raporunda kullanılabilecek örnek test çıktıları elde etmek

Bu script doğrudan simülasyon döngüsü çalıştırmaz.
Bunun yerine belirli sensör değerlerini elle vererek karar motorunu test eder.

Çalıştırma:
    python scripts/run_test_scenarios.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from src.decision.actions import ControlActions
from src.decision.fuzzy_engine import FuzzyEngine, RuleActivation
from src.explanation.explanation_engine import DecisionExplanation, ExplanationEngine
from src.simulation.virtual_sensors import SensorReadings


@dataclass
class TestScenario:
    """
    Tek bir test senaryosunu temsil eden veri sınıfı.

    Her senaryoda:
        - Bir ad
        - Açıklama
        - Sensör giriş değerleri
        - Beklenen davranış özeti

    tutulur.
    """

    name: str
    description: str
    readings: SensorReadings
    expected_behavior: str


def create_test_scenarios() -> List[TestScenario]:
    """
    Proje için kullanılacak temel test senaryolarını oluşturur.

    Bu senaryolar docs/test_scenarios.md dosyasındaki senaryolarla uyumludur.
    """

    return [
        TestScenario(
            name="Senaryo 1 - Normal Sera Koşulları",
            description="Sera ortamının dengeli olduğu durum.",
            readings=SensorReadings(
                temperature=25.0,
                air_humidity=55.0,
                soil_moisture=55.0,
                light_level=55.0,
                water_tank_level=80.0,
            ),
            expected_behavior=(
                "Sulama, havalandırma ve alarm düşük/kapalı olmalı; "
                "gölgeleme düşük seviyede kalabilir."
            ),
        ),
        TestScenario(
            name="Senaryo 2 - Toprak Kuru, Su Yeterli",
            description="Toprak nemi düşük ancak su tankı yeterli.",
            readings=SensorReadings(
                temperature=28.0,
                air_humidity=50.0,
                soil_moisture=20.0,
                light_level=60.0,
                water_tank_level=80.0,
            ),
            expected_behavior=(
                "Sulama yüksek olmalı, alarm düşük veya kapalı kalmalıdır."
            ),
        ),
        TestScenario(
            name="Senaryo 3 - Toprak Kuru, Su Tankı Düşük",
            description="Sulama ihtiyacı var ancak su kaynağı yetersiz.",
            readings=SensorReadings(
                temperature=30.0,
                air_humidity=45.0,
                soil_moisture=18.0,
                light_level=65.0,
                water_tank_level=15.0,
            ),
            expected_behavior=(
                "Sulama sınırlı tutulmalı, alarm yüksek veya kritik olmalıdır."
            ),
        ),
        TestScenario(
            name="Senaryo 4 - Sıcaklık Yüksek",
            description="Sera içi sıcaklık yüksek seviyede.",
            readings=SensorReadings(
                temperature=37.0,
                air_humidity=50.0,
                soil_moisture=50.0,
                light_level=65.0,
                water_tank_level=75.0,
            ),
            expected_behavior=(
                "Havalandırma yüksek seviyede olmalıdır."
            ),
        ),
        TestScenario(
            name="Senaryo 5 - Sıcaklık ve Işık Yüksek",
            description="Sera ortamında ısı ve ışık stresi riski var.",
            readings=SensorReadings(
                temperature=36.0,
                air_humidity=40.0,
                soil_moisture=45.0,
                light_level=90.0,
                water_tank_level=70.0,
            ),
            expected_behavior=(
                "Havalandırma ve gölgeleme yüksek seviyede olmalıdır."
            ),
        ),
        TestScenario(
            name="Senaryo 6 - Hava Nemi ve Toprak Nemi Yüksek",
            description="Yüksek nem nedeniyle hastalık riski oluşabilir.",
            readings=SensorReadings(
                temperature=24.0,
                air_humidity=85.0,
                soil_moisture=82.0,
                light_level=50.0,
                water_tank_level=75.0,
            ),
            expected_behavior=(
                "Sulama kapalı olmalı, hastalık riski uyarısı üretilebilir."
            ),
        ),
        TestScenario(
            name="Senaryo 7 - Su Tankı Kritik Düşük",
            description="Su tankı seviyesi kritik düzeyde düşük.",
            readings=SensorReadings(
                temperature=26.0,
                air_humidity=50.0,
                soil_moisture=50.0,
                light_level=55.0,
                water_tank_level=10.0,
            ),
            expected_behavior=(
                "Alarm yüksek olmalı, su tankı kritik uyarısı verilmelidir."
            ),
        ),
        TestScenario(
            name="Senaryo 8 - Kritik Bitki Stresi",
            description="Birden fazla risk aynı anda mevcut.",
            readings=SensorReadings(
                temperature=38.0,
                air_humidity=25.0,
                soil_moisture=15.0,
                light_level=88.0,
                water_tank_level=20.0,
            ),
            expected_behavior=(
                "Alarm kritik olmalı; fan ve gölgeleme yüksek çalışmalı; "
                "sulama su tankı nedeniyle sınırlanabilir."
            ),
        ),
        TestScenario(
            name="Senaryo 9 - Işık Düşük",
            description="Işık seviyesi düşük, gölgeleme gereksiz.",
            readings=SensorReadings(
                temperature=22.0,
                air_humidity=60.0,
                soil_moisture=50.0,
                light_level=20.0,
                water_tank_level=80.0,
            ),
            expected_behavior=(
                "Gölgeleme kapalı olmalı, alarm üretilmemelidir."
            ),
        ),
        TestScenario(
            name="Senaryo 10 - Düşük Sıcaklık",
            description="Sıcaklık düşük olduğu için fan çalıştırılmamalıdır.",
            readings=SensorReadings(
                temperature=14.0,
                air_humidity=55.0,
                soil_moisture=55.0,
                light_level=45.0,
                water_tank_level=80.0,
            ),
            expected_behavior=(
                "Havalandırma kapalı olmalı, gereksiz müdahale yapılmamalıdır."
            ),
        ),
    ]


def format_readings(readings: SensorReadings) -> str:
    """
    Sensör değerlerini terminal çıktısı için okunabilir hale getirir.
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
    Kontrol aksiyonlarını terminal çıktısı için okunabilir hale getirir.
    """

    return (
        f"Sulama: {actions.irrigation_level:.1f}/100 | "
        f"Havalandırma: {actions.ventilation_level:.1f}/100 | "
        f"Gölgeleme: {actions.shading_level:.1f}/100 | "
        f"Alarm: {actions.alarm_level:.1f}/100"
    )


def print_top_rules(rule_activations: List[RuleActivation], limit: int = 5) -> None:
    """
    En güçlü tetiklenen fuzzy kuralları yazdırır.
    """

    if not rule_activations:
        print("Tetiklenen fuzzy kural bulunmadı.")
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
    Karar açıklamasının özet ve uyarı bölümlerini yazdırır.
    """

    print(f"Karar Özeti: {explanation.summary}")

    if explanation.warnings:
        print("Uyarılar:")
        for warning in explanation.warnings:
            print(f"  - {warning}")
    else:
        print("Uyarılar: Yok")


def run_single_scenario(
    scenario: TestScenario,
    fuzzy_engine: FuzzyEngine,
    explanation_engine: ExplanationEngine,
) -> None:
    """
    Tek bir test senaryosunu çalıştırır ve sonucunu terminale yazdırır.
    """

    print("=" * 100)
    print(scenario.name)
    print("=" * 100)

    print(f"Açıklama: {scenario.description}")
    print(f"Beklenen Davranış: {scenario.expected_behavior}")
    print("-" * 100)

    print("Giriş Sensör Değerleri:")
    print(f"  {format_readings(scenario.readings)}")

    # Fuzzy karar motoru bu senaryonun sensör değerlerini değerlendirir.
    actions = fuzzy_engine.evaluate(scenario.readings)

    print("Üretilen Kontrol Aksiyonları:")
    print(f"  {format_actions(actions)}")

    rule_activations = fuzzy_engine.get_last_rule_activations()
    print_top_rules(rule_activations)

    explanation = explanation_engine.generate(
        readings=scenario.readings,
        actions=actions,
        rule_activations=rule_activations,
    )

    print_explanation(explanation)
    print()


def main() -> None:
    """
    Tüm test senaryolarını sırayla çalıştırır.
    """

    fuzzy_engine = FuzzyEngine()
    explanation_engine = ExplanationEngine()
    scenarios = create_test_scenarios()

    print("\nAKILLI SERA KARAR MOTORU - TEST SENARYOLARI")
    print(f"Toplam senaryo sayısı: {len(scenarios)}\n")

    for scenario in scenarios:
        run_single_scenario(
            scenario=scenario,
            fuzzy_engine=fuzzy_engine,
            explanation_engine=explanation_engine,
        )

    print("=" * 100)
    print("Tüm test senaryoları tamamlandı.")
    print("=" * 100)


if __name__ == "__main__":
    main()