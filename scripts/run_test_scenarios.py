"""
run_test_scenarios.py

Bu dosya, Akıllı Sera Yönetim ve Karar Destek Sistemi için önceden tanımlanmış
test senaryolarını çalıştırır ve üretilen kararları beklenen davranışlara göre doğrular.

Amaç:
    - Fuzzy karar motorunun farklı sera koşullarında nasıl davrandığını görmek
    - Üretilen aksiyonları sayısal kabul kriterleriyle kontrol etmek
    - Karar açıklama modülünün ürettiği gerekçeleri terminal çıktısında göstermek
    - Proje raporunda kullanılabilecek test sonuçları elde etmek

Bu script doğrudan simülasyon döngüsü çalıştırmaz.
Bunun yerine belirli sensör değerlerini elle vererek karar motorunu test eder.

Çalıştırma:
    python scripts/run_test_scenarios.py
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

# Script doğrudan `python scripts/run_test_scenarios.py` komutuyla çalıştırıldığında
# Python, proje kökünü otomatik olarak import path içine almayabilir.
# Bu blok, `src` paketinin her ortamda bulunmasını garanti eder.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.decision.actions import ControlActions
from src.decision.fuzzy_engine import FuzzyEngine, RuleActivation
from src.explanation.explanation_engine import DecisionExplanation, ExplanationEngine
from src.simulation.virtual_sensors import SensorReadings


@dataclass
class ExpectedCheck:
    """
    Bir senaryo için sayısal doğrulama kriterini temsil eder.

    metric:
        ControlActions içindeki kontrol çıktısı adı.
        Örnek: irrigation_level, ventilation_level, shading_level, alarm_level

    min_value / max_value:
        İlgili aksiyonun kabul edilebilir alt ve üst sınırları.
        Yalnızca gerekli olan sınır doldurulabilir.
    """

    description: str
    metric: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None

    def evaluate(self, actions: ControlActions) -> "CheckResult":
        """
        Verilen ControlActions çıktısına göre kriterin geçip geçmediğini hesaplar.
        """

        actual_value = getattr(actions, self.metric)
        passed = True

        if self.min_value is not None and actual_value < self.min_value:
            passed = False

        if self.max_value is not None and actual_value > self.max_value:
            passed = False

        return CheckResult(
            description=self.description,
            metric=self.metric,
            actual_value=actual_value,
            min_value=self.min_value,
            max_value=self.max_value,
            passed=passed,
        )


@dataclass
class CheckResult:
    """
    Bir doğrulama kriterinin sonucunu temsil eder.
    """

    description: str
    metric: str
    actual_value: float
    min_value: Optional[float]
    max_value: Optional[float]
    passed: bool

    def expected_range_text(self) -> str:
        """
        Beklenen aralığı terminal için okunabilir metne dönüştürür.
        """

        if self.min_value is not None and self.max_value is not None:
            return f"{self.min_value:.1f} <= değer <= {self.max_value:.1f}"

        if self.min_value is not None:
            return f"değer >= {self.min_value:.1f}"

        if self.max_value is not None:
            return f"değer <= {self.max_value:.1f}"

        return "sayısal sınır yok"


@dataclass
class TestScenario:
    """
    Tek bir test senaryosunu temsil eden veri sınıfı.
    """

    name: str
    description: str
    readings: SensorReadings
    expected_behavior: str
    expected_checks: List[ExpectedCheck]


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
            expected_checks=[
                ExpectedCheck("Normal koşulda sulama düşük kalmalı", "irrigation_level", max_value=10.0),
                ExpectedCheck("Normal koşulda fan düşük kalmalı", "ventilation_level", max_value=15.0),
                ExpectedCheck("Normal koşulda gölgeleme düşük kalmalı", "shading_level", max_value=20.0),
                ExpectedCheck("Normal koşulda alarm üretilmemeli", "alarm_level", max_value=10.0),
            ],
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
            expected_behavior="Sulama yüksek olmalı, alarm düşük veya kapalı kalmalıdır.",
            expected_checks=[
                ExpectedCheck("Kuru toprakta sulama yüksek olmalı", "irrigation_level", min_value=70.0),
                ExpectedCheck("Su yeterliyken alarm düşük kalmalı", "alarm_level", max_value=20.0),
            ],
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
            expected_behavior="Sulama sınırlı tutulmalı, alarm yüksek veya kritik olmalıdır.",
            expected_checks=[
                ExpectedCheck("Su azlığında sulama sınırlanmalı", "irrigation_level", max_value=40.0),
                ExpectedCheck("Su azlığında alarm yüksek olmalı", "alarm_level", min_value=80.0),
            ],
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
            expected_behavior="Havalandırma yüksek seviyede olmalıdır.",
            expected_checks=[
                ExpectedCheck("Yüksek sıcaklıkta fan yüksek olmalı", "ventilation_level", min_value=60.0),
            ],
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
            expected_behavior="Havalandırma ve gölgeleme yüksek seviyede olmalıdır.",
            expected_checks=[
                ExpectedCheck("Yüksek sıcaklıkta fan yüksek olmalı", "ventilation_level", min_value=60.0),
                ExpectedCheck("Yüksek ışıkta gölgeleme yüksek olmalı", "shading_level", min_value=70.0),
            ],
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
            expected_behavior="Sulama kapalı olmalı, hastalık riski uyarısı üretilebilir.",
            expected_checks=[
                ExpectedCheck("Islak toprakta sulama kapalı kalmalı", "irrigation_level", max_value=10.0),
                ExpectedCheck("Yüksek nem ve ıslak toprakta risk alarmı oluşmalı", "alarm_level", min_value=50.0),
            ],
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
            expected_behavior="Alarm yüksek olmalı, su tankı kritik uyarısı verilmelidir.",
            expected_checks=[
                ExpectedCheck("Kritik düşük su tankında alarm yüksek olmalı", "alarm_level", min_value=80.0),
            ],
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
            expected_checks=[
                ExpectedCheck("Kritik streste alarm kritik olmalı", "alarm_level", min_value=90.0),
                ExpectedCheck("Kritik streste fan yüksek olmalı", "ventilation_level", min_value=60.0),
                ExpectedCheck("Kritik streste gölgeleme yüksek olmalı", "shading_level", min_value=70.0),
                ExpectedCheck("Düşük su tankında sulama sınırlanmalı", "irrigation_level", max_value=40.0),
            ],
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
            expected_behavior="Gölgeleme kapalı olmalı, alarm üretilmemelidir.",
            expected_checks=[
                ExpectedCheck("Düşük ışıkta gölgeleme kapalı kalmalı", "shading_level", max_value=10.0),
                ExpectedCheck("Düşük ışık tek başına alarm üretmemeli", "alarm_level", max_value=10.0),
            ],
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
            expected_behavior="Havalandırma kapalı olmalı, gereksiz müdahale yapılmamalıdır.",
            expected_checks=[
                ExpectedCheck("Düşük sıcaklıkta fan kapalı kalmalı", "ventilation_level", max_value=10.0),
                ExpectedCheck("Düşük sıcaklık tek başına alarm üretmemeli", "alarm_level", max_value=20.0),
            ],
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


def print_check_results(results: List[CheckResult]) -> bool:
    """
    Doğrulama sonuçlarını terminale yazar.

    Returns:
        Tüm kriterler geçtiyse True, aksi halde False.
    """

    print("Doğrulama Sonuçları:")

    all_passed = True

    for result in results:
        status = "GEÇTİ" if result.passed else "KALDI"
        if not result.passed:
            all_passed = False

        print(
            f"  [{status}] {result.description} | "
            f"Gerçek: {result.actual_value:.1f} | "
            f"Beklenen: {result.expected_range_text()}"
        )

    return all_passed


def run_single_scenario(
    scenario: TestScenario,
    fuzzy_engine: FuzzyEngine,
    explanation_engine: ExplanationEngine,
) -> bool:
    """
    Tek bir test senaryosunu çalıştırır, doğrular ve sonucunu terminale yazdırır.

    Returns:
        Senaryodaki tüm doğrulama kriterleri geçtiyse True döner.
    """

    print("=" * 100)
    print(scenario.name)
    print("=" * 100)

    print(f"Açıklama: {scenario.description}")
    print(f"Beklenen Davranış: {scenario.expected_behavior}")
    print("-" * 100)

    print("Giriş Sensör Değerleri:")
    print(f"  {format_readings(scenario.readings)}")

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

    check_results = [check.evaluate(actions) for check in scenario.expected_checks]
    scenario_passed = print_check_results(check_results)

    print()
    return scenario_passed


def main() -> None:
    """
    Tüm test senaryolarını sırayla çalıştırır.
    """

    fuzzy_engine = FuzzyEngine()
    explanation_engine = ExplanationEngine()
    scenarios = create_test_scenarios()

    print("\nAKILLI SERA KARAR MOTORU - TEST SENARYOLARI")
    print(f"Toplam senaryo sayısı: {len(scenarios)}\n")

    passed_count = 0

    for scenario in scenarios:
        scenario_passed = run_single_scenario(
            scenario=scenario,
            fuzzy_engine=fuzzy_engine,
            explanation_engine=explanation_engine,
        )

        if scenario_passed:
            passed_count += 1

    failed_count = len(scenarios) - passed_count

    print("=" * 100)
    print(f"Test özeti: {passed_count}/{len(scenarios)} senaryo geçti, {failed_count} senaryo kaldı.")
    print("=" * 100)

    if failed_count > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
