"""
explanation_engine.py

Bu dosya, akıllı sera karar destek sisteminin açıklama modülünü içerir.

ExplanationEngine sınıfı; fuzzy karar motorunun ürettiği kontrol aksiyonlarını,
tetiklenen kuralları ve mevcut sensör değerlerini kullanarak kullanıcıya anlaşılır
Türkçe açıklamalar üretir.

Bu modülün amacı yalnızca "ne karar verildiğini" göstermek değildir.
Asıl amaç, sistemin "neden bu kararı verdiğini" açıklayabilmesidir.

Örneğin:
    - Sulama seviyesi neden yüksek?
    - Fan neden çalıştırıldı?
    - Alarm neden aktif edildi?
    - Hangi fuzzy kurallar bu karara katkı sağladı?

Bu açıklanabilirlik katmanı, projeyi basit bir otomasyon uygulamasından ayırır ve
uzman sistem yaklaşımıyla doğrudan ilişkilendirir.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Dict, List

from src.decision.actions import ControlActions
from src.decision.fuzzy_engine import RuleActivation
from src.simulation.virtual_sensors import SensorReadings


@dataclass
class DecisionExplanation:
    """
    Karar açıklama çıktısını temsil eden veri sınıfı.

    Alanlar:
        summary:
            Kararın genel özeti.

        action_explanations:
            Sulama, havalandırma, gölgeleme ve alarm kararlarının ayrı ayrı açıklamaları.

        active_rule_explanations:
            Tetiklenen fuzzy kuralların açıklamaları.

        warnings:
            Kullanıcıya gösterilmesi gereken kritik uyarılar.
    """

    summary: str
    action_explanations: List[str] = field(default_factory=list)
    active_rule_explanations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        """
        Açıklama nesnesini sözlük formatına dönüştürür.

        Bu çıktı ileride dashboard, JSON kayıt veya raporlama işlemlerinde kullanılabilir.
        """

        return asdict(self)


class ExplanationEngine:
    """
    Fuzzy karar motoru çıktılarını açıklayan modül.

    Bu sınıf yeni karar üretmez.
    Sadece FuzzyEngine tarafından üretilen kararları ve tetiklenen kuralları yorumlar.

    Bu ayrım önemlidir:
        - FuzzyEngine karar verir.
        - ExplanationEngine verilen kararı açıklar.
    """

    def generate(
        self,
        readings: SensorReadings,
        actions: ControlActions,
        rule_activations: List[RuleActivation],
    ) -> DecisionExplanation:
        """
        Sensör okumaları, kontrol aksiyonları ve tetiklenen kurallardan açıklama üretir.

        Args:
            readings:
                Sanal sensörlerden gelen çevresel değerler.

            actions:
                Fuzzy karar motorunun ürettiği kontrol aksiyonları.

            rule_activations:
                FuzzyEngine tarafından son değerlendirmede tetiklenen kurallar.

        Returns:
            DecisionExplanation nesnesi.
        """

        action_explanations = self._generate_action_explanations(readings, actions)
        active_rule_explanations = self._generate_rule_explanations(rule_activations)
        warnings = self._generate_warnings(readings, actions)

        summary = self._generate_summary(actions, warnings)

        return DecisionExplanation(
            summary=summary,
            action_explanations=action_explanations,
            active_rule_explanations=active_rule_explanations,
            warnings=warnings,
        )

    def _generate_summary(self, actions: ControlActions, warnings: List[str]) -> str:
        """
        Karar çıktısı için kısa bir genel özet üretir.

        Alarm varsa özet daha dikkat çekici olur.
        Alarm yoksa sistemin normal kontrol kararı verdiği belirtilir.
        """

        if actions.has_alarm():
            return "Sistem mevcut sera koşullarında risk algıladı ve kontrol aksiyonlarıyla birlikte alarm üretti."

        if actions.is_idle():
            return "Sera koşulları dengeli görünüyor. Sistem aktif bir müdahale önermedi."

        if warnings:
            return "Sistem bazı sınır durumlar tespit etti ve uygun kontrol aksiyonları önerdi."

        return "Sistem mevcut sera koşullarını değerlendirdi ve uygun kontrol aksiyonları üretti."

    def _generate_action_explanations(
        self,
        readings: SensorReadings,
        actions: ControlActions,
    ) -> List[str]:
        """
        Her kontrol aksiyonu için ayrı açıklama üretir.

        Bu açıklamalar dashboard üzerinde doğrudan kullanıcıya gösterilebilir.
        """

        explanations = [
            self._explain_irrigation(readings, actions),
            self._explain_ventilation(readings, actions),
            self._explain_shading(readings, actions),
            self._explain_alarm(readings, actions),
        ]

        # Boş açıklama oluşursa temizlemek için filtre uyguluyoruz.
        return [explanation for explanation in explanations if explanation]

    def _explain_irrigation(
        self,
        readings: SensorReadings,
        actions: ControlActions,
    ) -> str:
        """
        Sulama kararını açıklar.
        """

        level = actions.irrigation_level

        if level >= 70:
            return (
                f"Sulama seviyesi yüksek belirlendi ({level:.1f}/100). "
                f"Bunun temel nedeni toprak neminin düşük seviyede olmasıdır "
                f"(toprak nemi: %{readings.soil_moisture:.1f})."
            )

        if 30 <= level < 70:
            return (
                f"Sulama seviyesi orta düzeyde belirlendi ({level:.1f}/100). "
                f"Toprak nemi tamamen kritik olmasa da izlenmesi gereken seviyededir "
                f"(toprak nemi: %{readings.soil_moisture:.1f})."
            )

        if 0 < level < 30:
            return (
                f"Sulama seviyesi sınırlı tutuldu ({level:.1f}/100). "
                f"Bu durum genellikle su tankı seviyesinin düşük olması veya sulama kararının "
                f"riskli görülmesiyle ilişkilidir (su tankı: %{readings.water_tank_level:.1f})."
            )

        return (
            f"Sulama kapalı tutuldu ({level:.1f}/100). "
            f"Mevcut toprak nemi sulama gerektirmeyecek seviyededir "
            f"(toprak nemi: %{readings.soil_moisture:.1f})."
        )

    def _explain_ventilation(
        self,
        readings: SensorReadings,
        actions: ControlActions,
    ) -> str:
        """
        Havalandırma/fan kararını açıklar.
        """

        level = actions.ventilation_level

        if level >= 70:
            return (
                f"Havalandırma seviyesi yüksek belirlendi ({level:.1f}/100). "
                f"Sıcaklık yüksek olduğu için sera içi ısının düşürülmesi hedeflenmektedir "
                f"(sıcaklık: {readings.temperature:.1f} °C)."
            )

        if 30 <= level < 70:
            return (
                f"Havalandırma seviyesi orta düzeyde belirlendi ({level:.1f}/100). "
                f"Sıcaklık veya hava nemi izlenmesi gereken aralıktadır "
                f"(sıcaklık: {readings.temperature:.1f} °C, hava nemi: %{readings.air_humidity:.1f})."
            )

        if 0 < level < 30:
            return (
                f"Havalandırma düşük seviyede tutuldu ({level:.1f}/100). "
                f"Mevcut koşullarda güçlü fan müdahalesi gerekli görülmedi."
            )

        return (
            f"Havalandırma kapalı tutuldu ({level:.1f}/100). "
            f"Sıcaklık değeri fan müdahalesi gerektirecek seviyede değildir "
            f"(sıcaklık: {readings.temperature:.1f} °C)."
        )

    def _explain_shading(
        self,
        readings: SensorReadings,
        actions: ControlActions,
    ) -> str:
        """
        Gölgeleme kararını açıklar.
        """

        level = actions.shading_level

        if level >= 70:
            return (
                f"Gölgeleme seviyesi yüksek belirlendi ({level:.1f}/100). "
                f"Işık seviyesi yüksek olduğu için bitkinin aşırı ışık ve ısı stresinden "
                f"korunması hedeflenmektedir (ışık seviyesi: %{readings.light_level:.1f})."
            )

        if 30 <= level < 70:
            return (
                f"Gölgeleme seviyesi orta düzeyde belirlendi ({level:.1f}/100). "
                f"Işık seviyesi yüksek aralığa yaklaşmıştır "
                f"(ışık seviyesi: %{readings.light_level:.1f})."
            )

        if 0 < level < 30:
            return (
                f"Gölgeleme düşük seviyede tutuldu ({level:.1f}/100). "
                f"Işık seviyesi kontrol altında görünmektedir "
                f"(ışık seviyesi: %{readings.light_level:.1f})."
            )

        return (
            f"Gölgeleme kapalı tutuldu ({level:.1f}/100). "
            f"Mevcut ışık seviyesi gölgeleme gerektirecek düzeyde değildir "
            f"(ışık seviyesi: %{readings.light_level:.1f})."
        )

    def _explain_alarm(
        self,
        readings: SensorReadings,
        actions: ControlActions,
    ) -> str:
        """
        Alarm kararını açıklar.
        """

        level = actions.alarm_level

        if level >= 80:
            return (
                f"Alarm seviyesi kritik olarak belirlendi ({level:.1f}/100). "
                f"Su tankı seviyesi, toprak nemi veya sıcaklık-nem kombinasyonu riskli durumdadır "
                f"(su tankı: %{readings.water_tank_level:.1f}, "
                f"toprak nemi: %{readings.soil_moisture:.1f}, "
                f"sıcaklık: {readings.temperature:.1f} °C)."
            )

        if 50 <= level < 80:
            return (
                f"Alarm seviyesi uyarı düzeyindedir ({level:.1f}/100). "
                f"Sera koşullarında izlenmesi gereken bir risk oluşmuştur."
            )

        if 0 < level < 50:
            return (
                f"Alarm seviyesi düşük düzeydedir ({level:.1f}/100). "
                f"Kritik bir durum yoktur ancak bazı değerler sınır bölgelere yaklaşmaktadır."
            )

        return "Alarm üretilmedi. Mevcut koşullarda kritik bir risk tespit edilmedi."

    def _generate_rule_explanations(
        self,
        rule_activations: List[RuleActivation],
    ) -> List[str]:
        """
        Tetiklenen fuzzy kuralları açıklama metnine dönüştürür.

        Kurallar aktivasyon derecesine göre büyükten küçüğe sıralanır.
        Böylece kullanıcı en etkili kuralları önce görür.
        """

        if not rule_activations:
            return ["Bu değerlendirmede anlamlı düzeyde tetiklenen fuzzy kural bulunmadı."]

        sorted_rules = sorted(
            rule_activations,
            key=lambda rule: rule.activation,
            reverse=True,
        )

        explanations = []

        for rule in sorted_rules:
            activation_percent = rule.activation * 100

            outputs = self._format_rule_outputs(rule)

            explanations.append(
                f"'{rule.rule_name}' kuralı %{activation_percent:.1f} düzeyinde tetiklendi."
                f"{outputs}"
            )

        return explanations

    def _format_rule_outputs(self, rule: RuleActivation) -> str:
        """
        Bir fuzzy kuralının hangi çıkışlara katkı verdiğini metinleştirir.
        """

        outputs = []

        if rule.irrigation_output is not None:
            outputs.append(f"sulama={rule.irrigation_output:.1f}")

        if rule.ventilation_output is not None:
            outputs.append(f"havalandırma={rule.ventilation_output:.1f}")

        if rule.shading_output is not None:
            outputs.append(f"gölgeleme={rule.shading_output:.1f}")

        if rule.alarm_output is not None:
            outputs.append(f"alarm={rule.alarm_output:.1f}")

        if not outputs:
            return ""

        return " Önerilen çıktı: " + ", ".join(outputs) + "."

    def _generate_warnings(
        self,
        readings: SensorReadings,
        actions: ControlActions,
    ) -> List[str]:
        """
        Sensör değerleri ve karar çıktısına göre kullanıcı uyarıları üretir.

        Bu uyarılar fuzzy kararın yerine geçmez.
        Sadece kullanıcıya önemli sınır durumları daha net göstermek için kullanılır.
        """

        warnings = []

        if readings.water_tank_level < 25:
            warnings.append(
                f"Su tankı seviyesi kritik düzeydedir (%{readings.water_tank_level:.1f}). "
                "Sulama kapasitesi sınırlanabilir."
            )

        if readings.soil_moisture < 30:
            warnings.append(
                f"Toprak nemi düşük seviyededir (%{readings.soil_moisture:.1f}). "
                "Bitki su stresi yaşayabilir."
            )

        if readings.temperature > 35:
            warnings.append(
                f"Sıcaklık yüksek seviyededir ({readings.temperature:.1f} °C). "
                "Havalandırma veya gölgeleme gerekebilir."
            )

        if readings.light_level > 85:
            warnings.append(
                f"Işık seviyesi çok yüksektir (%{readings.light_level:.1f}). "
                "Aşırı ışık/ısı stresi oluşabilir."
            )

        if readings.air_humidity > 80 and readings.soil_moisture > 75:
            warnings.append(
                "Hava nemi ve toprak nemi birlikte yüksek seviyededir. "
                "Bu durum bazı bitkiler için hastalık riskini artırabilir."
            )

        if actions.has_alarm() and not warnings:
            warnings.append(
                "Alarm aktif edildi. Risk, fuzzy kural kombinasyonlarından kaynaklanmaktadır."
            )

        return warnings