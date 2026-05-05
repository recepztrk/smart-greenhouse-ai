"""
logger.py

Bu dosya, akıllı sera simülasyonunda oluşan adım adım verileri CSV formatında
kaydetmek için kullanılır.

SimulationLogger sınıfı; sera durumu, sensör okumaları, fuzzy karar çıktıları,
tetiklenen kurallar ve açıklama özetlerini tek bir kayıt satırı halinde dosyaya yazar.

Bu modül özellikle şu amaçlar için önemlidir:
    - Simülasyonun geçmişini incelemek
    - Dashboard üzerinde grafik üretmek
    - Proje raporunda örnek çıktı göstermek
    - Fuzzy karar motorunun davranışını test etmek
    - Sistem geliştikçe kararların tutarlılığını analiz etmek

Not:
    data/simulation_logs.csv dosyası otomatik oluşturulur.
    Bu dosya .gitignore içinde tutulduğu için GitHub'a gönderilmez.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.decision.actions import ControlActions
from src.decision.fuzzy_engine import RuleActivation
from src.explanation.explanation_engine import DecisionExplanation
from src.simulation.greenhouse_state import GreenhouseState
from src.simulation.virtual_sensors import SensorReadings


class SimulationLogger:
    """
    Simülasyon adımlarını CSV dosyasına kaydeden sınıf.

    Her log satırı, sistemin belirli bir andaki durumunu temsil eder.
    """

    def __init__(self, log_file_path: str = "data/simulation_logs.csv") -> None:
        """
        Logger nesnesini oluşturur.

        Args:
            log_file_path:
                Log kayıtlarının yazılacağı CSV dosyasının yolu.
        """

        self.log_file_path = Path(log_file_path)

        # data/ klasörü yoksa otomatik oluşturulur.
        # Böylece kullanıcı manuel klasör oluşturmayı unutsa bile logger çalışır.
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)

        self.fieldnames = [
            "timestamp",
            "step",

            # Aksiyon öncesi sera durumu
            "state_before_temperature",
            "state_before_air_humidity",
            "state_before_soil_moisture",
            "state_before_light_level",
            "state_before_water_tank_level",

            # Sensör okumaları
            "sensor_temperature",
            "sensor_air_humidity",
            "sensor_soil_moisture",
            "sensor_light_level",
            "sensor_water_tank_level",

            # Fuzzy karar çıktıları
            "irrigation_level",
            "ventilation_level",
            "shading_level",
            "alarm_level",

            # Aksiyon sonrası sera durumu
            "state_after_temperature",
            "state_after_air_humidity",
            "state_after_soil_moisture",
            "state_after_light_level",
            "state_after_water_tank_level",

            # Açıklama ve kural bilgileri
            "summary",
            "warnings",
            "active_rule_count",
            "top_rules",
        ]

        self._ensure_file_has_header()

    def log_step(
        self,
        step: int,
        state_before: GreenhouseState,
        readings: SensorReadings,
        actions: ControlActions,
        explanation: DecisionExplanation,
        rule_activations: List[RuleActivation],
        state_after: Optional[GreenhouseState] = None,
    ) -> None:
        """
        Tek bir simülasyon adımını CSV dosyasına kaydeder.

        Args:
            step:
                Simülasyon adım numarası.

            state_before:
                Aksiyon uygulanmadan önceki sera durumu.

            readings:
                Sanal sensörlerden okunan değerler.

            actions:
                Fuzzy karar motorunun ürettiği kontrol aksiyonları.

            explanation:
                Açıklama modülünün ürettiği karar açıklaması.

            rule_activations:
                FuzzyEngine tarafından tetiklenen kurallar.

            state_after:
                Aksiyonlar ve doğal değişim uygulandıktan sonraki sera durumu.
        """

        top_rules = self._format_top_rules(rule_activations)
        warnings = self._format_warnings(explanation.warnings)

        row = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "step": step,

            "state_before_temperature": state_before.temperature,
            "state_before_air_humidity": state_before.air_humidity,
            "state_before_soil_moisture": state_before.soil_moisture,
            "state_before_light_level": state_before.light_level,
            "state_before_water_tank_level": state_before.water_tank_level,

            "sensor_temperature": readings.temperature,
            "sensor_air_humidity": readings.air_humidity,
            "sensor_soil_moisture": readings.soil_moisture,
            "sensor_light_level": readings.light_level,
            "sensor_water_tank_level": readings.water_tank_level,

            "irrigation_level": actions.irrigation_level,
            "ventilation_level": actions.ventilation_level,
            "shading_level": actions.shading_level,
            "alarm_level": actions.alarm_level,

            "state_after_temperature": state_after.temperature if state_after else "",
            "state_after_air_humidity": state_after.air_humidity if state_after else "",
            "state_after_soil_moisture": state_after.soil_moisture if state_after else "",
            "state_after_light_level": state_after.light_level if state_after else "",
            "state_after_water_tank_level": state_after.water_tank_level if state_after else "",

            "summary": explanation.summary,
            "warnings": warnings,
            "active_rule_count": len(rule_activations),
            "top_rules": top_rules,
        }

        self._append_row(row)

    def clear_logs(self) -> None:
        """
        Mevcut log dosyasını temizler ve yalnızca başlık satırını yeniden oluşturur.

        Bu metot özellikle yeni bir demo çalıştırmadan önce temiz kayıt almak için
        kullanılabilir.
        """

        with self.log_file_path.open(mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=self.fieldnames)
            writer.writeheader()

    def _ensure_file_has_header(self) -> None:
        """
        Log dosyası yoksa veya boşsa CSV başlık satırını oluşturur.
        """

        if not self.log_file_path.exists() or self.log_file_path.stat().st_size == 0:
            with self.log_file_path.open(mode="w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                writer.writeheader()

    def _append_row(self, row: Dict[str, object]) -> None:
        """
        Verilen satırı CSV dosyasına ekler.
        """

        with self.log_file_path.open(mode="a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=self.fieldnames)
            writer.writerow(row)

    @staticmethod
    def _format_top_rules(
        rule_activations: List[RuleActivation],
        limit: int = 3,
    ) -> str:
        """
        En güçlü tetiklenen kuralları tek satırlık metne dönüştürür.

        CSV içinde liste saklamak yerine okunabilir bir string formatı kullanıyoruz.
        """

        if not rule_activations:
            return ""

        sorted_rules = sorted(
            rule_activations,
            key=lambda rule: rule.activation,
            reverse=True,
        )

        top_rules = []

        for rule in sorted_rules[:limit]:
            top_rules.append(f"{rule.rule_name} (%{rule.activation * 100:.1f})")

        return " | ".join(top_rules)

    @staticmethod
    def _format_warnings(warnings: List[str]) -> str:
        """
        Uyarı listesini CSV içinde saklanabilir tek satırlık metne dönüştürür.
        """

        if not warnings:
            return ""

        return " | ".join(warnings)