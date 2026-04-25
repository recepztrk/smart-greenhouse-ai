"""
fuzzy_engine.py

Bu dosya, akıllı sera yönetim sisteminin bulanık mantık tabanlı karar motorunu içerir.

FuzzyEngine sınıfı, sanal sensörlerden gelen çevresel değerleri alır ve bu değerleri
bulanık üyelik fonksiyonları üzerinden değerlendirerek kontrol aksiyonları üretir.

Girişler:
    - Sıcaklık
    - Hava nemi
    - Toprak nemi
    - Işık seviyesi
    - Su tankı seviyesi

Çıkışlar:
    - Sulama seviyesi
    - Havalandırma / fan seviyesi
    - Gölgeleme seviyesi
    - Alarm seviyesi

Bu ilk prototipte basitleştirilmiş Sugeno-benzeri bir yaklaşım kullanılmıştır:
    - Giriş değerleri bulanık kümelere dönüştürülür.
    - Kurallar min/max operatörleriyle tetiklenir.
    - Her kural belirli bir sabit çıkış değeri önerir.
    - Son karar, kural aktivasyonlarına göre ağırlıklı ortalama ile üretilir.

Bu yapı hem ders kapsamında anlatılabilir düzeydedir hem de ileride daha gelişmiş
Mamdani tipi çıkarım veya scikit-fuzzy entegrasyonu için genişletilebilir.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

from src.decision.actions import ControlActions
from src.simulation.virtual_sensors import SensorReadings


@dataclass
class RuleActivation:
    """
    Tetiklenen fuzzy kuralların izini tutmak için kullanılan veri sınıfı.

    Bu yapı ileride karar açıklama modülünde kullanılacaktır.
    Örneğin kullanıcıya:
        "Sulama kararı verildi çünkü toprak nemi kuru ve sıcaklık yüksek."
    şeklinde açıklama üretmek için hangi kuralların ne kadar tetiklendiğini bilmemiz gerekir.
    """

    rule_name: str
    activation: float
    irrigation_output: Optional[float] = None
    ventilation_output: Optional[float] = None
    shading_output: Optional[float] = None
    alarm_output: Optional[float] = None

    def to_dict(self) -> Dict[str, Optional[float]]:
        """
        Kural aktivasyon bilgisini sözlük formatına dönüştürür.
        """

        return asdict(self)


class FuzzyEngine:
    """
    Bulanık mantık tabanlı sera karar motoru.

    Bu sınıf, sensör okumalarını alır ve uzman kurallara göre kontrol aksiyonları üretir.
    """

    def __init__(self) -> None:
        """
        Fuzzy karar motorunu oluşturur.

        last_rule_activations:
            Son değerlendirmede tetiklenen kuralları saklar.
            Bu bilgi doğrudan karar açıklama modülünde kullanılacaktır.
        """

        self.last_rule_activations: List[RuleActivation] = []

    def evaluate(self, readings: SensorReadings) -> ControlActions:
        """
        Sensör okumalarını değerlendirerek kontrol aksiyonları üretir.

        Args:
            readings:
                Sanal sensör katmanından gelen çevresel ölçüm değerleri.

        Returns:
            ControlActions nesnesi.
        """

        # Her değerlendirme öncesi eski kural izlerini temizliyoruz.
        self.last_rule_activations = []

        # 1. Adım: Kesin sensör değerlerini bulanık üyelik derecelerine dönüştür.
        memberships = self._fuzzify(readings)

        # Her çıkış için (aktivasyon, önerilen çıkış değeri) çiftlerini tutuyoruz.
        irrigation_rules: List[Tuple[float, float]] = []
        ventilation_rules: List[Tuple[float, float]] = []
        shading_rules: List[Tuple[float, float]] = []
        alarm_rules: List[Tuple[float, float]] = []

        def add_rule(
            rule_name: str,
            activation: float,
            irrigation_output: Optional[float] = None,
            ventilation_output: Optional[float] = None,
            shading_output: Optional[float] = None,
            alarm_output: Optional[float] = None,
        ) -> None:
            """
            Bir fuzzy kuralının sonucunu ilgili çıkış listelerine ekler.

            activation:
                Kuralın ne kadar tetiklendiğini gösterir.
                0 ise kural hiç etkili değildir.
                1 ise kural tam olarak aktiftir.

            output değerleri:
                Kuralın ilgili kontrol çıktısı için önerdiği sabit seviyedir.
            """

            # Negatif veya 1 üstü aktivasyon oluşmasını engelliyoruz.
            activation = self._clamp(activation, 0.0, 1.0)

            # Aktivasyonu 0 olan kuralları iz listesine eklemiyoruz.
            # Böylece açıklama modülü yalnızca gerçekten etkili kuralları görebilir.
            if activation <= 0.0:
                return

            rule_activation = RuleActivation(
                rule_name=rule_name,
                activation=activation,
                irrigation_output=irrigation_output,
                ventilation_output=ventilation_output,
                shading_output=shading_output,
                alarm_output=alarm_output,
            )

            self.last_rule_activations.append(rule_activation)

            if irrigation_output is not None:
                irrigation_rules.append((activation, irrigation_output))

            if ventilation_output is not None:
                ventilation_rules.append((activation, ventilation_output))

            if shading_output is not None:
                shading_rules.append((activation, shading_output))

            if alarm_output is not None:
                alarm_rules.append((activation, alarm_output))

        # Okunabilirlik için üyelik derecelerini kısa değişkenlere alıyoruz.
        temp = memberships["temperature"]
        air = memberships["air_humidity"]
        soil = memberships["soil_moisture"]
        light = memberships["light_level"]
        water = memberships["water_tank_level"]

        # ---------------------------------------------------------------------
        # SULAMA KURALLARI
        # ---------------------------------------------------------------------

        add_rule(
            rule_name="Toprak kuru ve su yeterli ise sulama yüksek olmalı",
            activation=self._and(soil["dry"], self._or(water["medium"], water["sufficient"])),
            irrigation_output=80.0,
        )

        add_rule(
            rule_name="Toprak kuru, sıcaklık yüksek ve su yeterli ise sulama çok yüksek olmalı",
            activation=self._and(
                soil["dry"],
                temp["high"],
                self._or(water["medium"], water["sufficient"]),
            ),
            irrigation_output=90.0,
        )

        add_rule(
            rule_name="Toprak kuru fakat su tankı düşük ise sulama sınırlı olmalı ve alarm yükselmeli",
            activation=self._and(soil["dry"], water["low"]),
            irrigation_output=25.0,
            alarm_output=90.0,
        )

        add_rule(
            rule_name="Toprak nemi uygun ise sulama kapalı olmalı",
            activation=soil["optimal"],
            irrigation_output=0.0,
        )

        add_rule(
            rule_name="Toprak ıslak ise sulama kapalı olmalı",
            activation=soil["wet"],
            irrigation_output=0.0,
        )

        # ---------------------------------------------------------------------
        # HAVALANDIRMA / FAN KURALLARI
        # ---------------------------------------------------------------------

        add_rule(
            rule_name="Sıcaklık yüksek ve hava nemi yüksek ise fan yüksek çalışmalı",
            activation=self._and(temp["high"], air["high"]),
            ventilation_output=85.0,
        )

        add_rule(
            rule_name="Sıcaklık yüksek ise fan orta-yüksek çalışmalı",
            activation=self._and(temp["high"], self._or(air["low"], air["normal"])),
            ventilation_output=70.0,
        )

        add_rule(
            rule_name="Sıcaklık normal ve hava nemi yüksek ise fan orta seviyede çalışmalı",
            activation=self._and(temp["normal"], air["high"]),
            ventilation_output=35.0,
        )

        add_rule(
            rule_name="Sıcaklık düşük ise fan kapalı olmalı",
            activation=temp["low"],
            ventilation_output=0.0,
        )

        # ---------------------------------------------------------------------
        # GÖLGELEME KURALLARI
        # ---------------------------------------------------------------------

        add_rule(
            rule_name="Işık fazla ve sıcaklık yüksek ise gölgeleme yüksek olmalı",
            activation=self._and(light["high"], temp["high"]),
            shading_output=85.0,
        )

        add_rule(
            rule_name="Işık fazla ve sıcaklık normal ise gölgeleme orta olmalı",
            activation=self._and(light["high"], temp["normal"]),
            shading_output=55.0,
        )

        add_rule(
            rule_name="Işık düşük ise gölgeleme kapalı olmalı",
            activation=light["low"],
            shading_output=0.0,
        )

        add_rule(
            rule_name="Işık orta seviyede ise gölgeleme düşük olmalı",
            activation=light["medium"],
            shading_output=10.0,
        )

        # ---------------------------------------------------------------------
        # ALARM KURALLARI
        # ---------------------------------------------------------------------

        add_rule(
            rule_name="Su tankı düşük ise alarm yüksek olmalı",
            activation=water["low"],
            alarm_output=90.0,
        )

        add_rule(
            rule_name="Su tankı düşük ve toprak kuru ise alarm kritik olmalı",
            activation=self._and(water["low"], soil["dry"]),
            alarm_output=100.0,
        )

        add_rule(
            rule_name="Sıcaklık yüksek, toprak kuru ve hava nemi düşük ise bitki stresi alarmı oluşmalı",
            activation=self._and(temp["high"], soil["dry"], air["low"]),
            alarm_output=75.0,
        )

        add_rule(
            rule_name="Toprak ıslak ve hava nemi yüksek ise hastalık riski alarmı oluşmalı",
            activation=self._and(soil["wet"], air["high"]),
            alarm_output=60.0,
        )

        # 2. Adım: Kural çıktılarından nihai kontrol kararlarını üret.
        irrigation_level = self._weighted_average(irrigation_rules)
        ventilation_level = self._weighted_average(ventilation_rules)
        shading_level = self._weighted_average(shading_rules)

        # Alarm için daha korumacı davranıyoruz.
        # Birden fazla alarm kuralı varsa en güçlü alarm etkisini esas alıyoruz.
        alarm_level = self._max_activated_output(alarm_rules)

        return ControlActions(
            irrigation_level=irrigation_level,
            ventilation_level=ventilation_level,
            shading_level=shading_level,
            alarm_level=alarm_level,
        )

    def get_last_rule_activations(self) -> List[RuleActivation]:
        """
        Son değerlendirmede tetiklenen kuralları döndürür.

        Bu metot, açıklama modülünün hangi kararın neden üretildiğini anlaması için
        kullanılacaktır.
        """

        return self.last_rule_activations

    def get_membership_snapshot(self, readings: SensorReadings) -> Dict[str, Dict[str, float]]:
        """
        Verilen sensör değerleri için bulanık üyelik derecelerini döndürür.

        Bu metot özellikle debug, raporlama ve dashboard üzerinde üyelik derecelerini
        göstermek için faydalıdır.
        """

        return self._fuzzify(readings)

    def _fuzzify(self, readings: SensorReadings) -> Dict[str, Dict[str, float]]:
        """
        Kesin sensör okumalarını bulanık üyelik derecelerine dönüştürür.

        Her değişken için düşük/normal/yüksek veya kuru/uygun/ıslak gibi
        dilsel kümeler tanımlanmıştır.
        """

        return {
            "temperature": {
                "low": self._trapezoidal(readings.temperature, 0.0, 0.0, 15.0, 22.0),
                "normal": self._triangular(readings.temperature, 18.0, 25.0, 32.0),
                "high": self._trapezoidal(readings.temperature, 28.0, 35.0, 50.0, 50.0),
            },
            "air_humidity": {
                "low": self._trapezoidal(readings.air_humidity, 0.0, 0.0, 35.0, 50.0),
                "normal": self._triangular(readings.air_humidity, 40.0, 55.0, 70.0),
                "high": self._trapezoidal(readings.air_humidity, 60.0, 75.0, 100.0, 100.0),
            },
            "soil_moisture": {
                "dry": self._trapezoidal(readings.soil_moisture, 0.0, 0.0, 25.0, 40.0),
                "optimal": self._triangular(readings.soil_moisture, 35.0, 55.0, 75.0),
                "wet": self._trapezoidal(readings.soil_moisture, 65.0, 80.0, 100.0, 100.0),
            },
            "light_level": {
                "low": self._trapezoidal(readings.light_level, 0.0, 0.0, 25.0, 40.0),
                "medium": self._triangular(readings.light_level, 30.0, 55.0, 75.0),
                "high": self._trapezoidal(readings.light_level, 65.0, 80.0, 100.0, 100.0),
            },
            "water_tank_level": {
                "low": self._trapezoidal(readings.water_tank_level, 0.0, 0.0, 20.0, 35.0),
                "medium": self._triangular(readings.water_tank_level, 25.0, 50.0, 75.0),
                "sufficient": self._trapezoidal(readings.water_tank_level, 65.0, 80.0, 100.0, 100.0),
            },
        }

    @staticmethod
    def _triangular(value: float, left: float, center: float, right: float) -> float:
        """
        Üçgensel üyelik fonksiyonunu hesaplar.

        left:
            Üyeliğin başladığı nokta.

        center:
            Üyeliğin 1 olduğu tepe noktası.

        right:
            Üyeliğin tekrar 0 olduğu nokta.
        """

        if value <= left or value >= right:
            return 0.0

        if value == center:
            return 1.0

        if left < value < center:
            return (value - left) / (center - left)

        return (right - value) / (right - center)

    @staticmethod
    def _trapezoidal(value: float, a: float, b: float, c: float, d: float) -> float:
        """
        Yamuksal üyelik fonksiyonunu hesaplar.

        a-b arası yükselen kenar,
        b-c arası tam üyelik bölgesi,
        c-d arası azalan kenardır.

        a == b veya c == d durumları omuz tipi üyelik fonksiyonları için kullanılır.
        Örneğin:
            düşük sıcaklık: 0-15 arası tam düşük kabul edilebilir.
            yüksek sıcaklık: 35-50 arası tam yüksek kabul edilebilir.
        """

        # Sol omuz: a == b ise b noktasına kadar üyelik tam kabul edilir.
        if a == b and value <= b:
            return 1.0

        # Sağ omuz: c == d ise c noktasından sonra üyelik tam kabul edilir.
        if c == d and value >= c:
            return 1.0

        if value <= a or value >= d:
            return 0.0

        if a < value < b:
            return (value - a) / (b - a)

        if b <= value <= c:
            return 1.0

        if c < value < d:
            return (d - value) / (d - c)

        return 0.0

    @staticmethod
    def _and(*values: float) -> float:
        """
        Bulanık AND işlemi.

        Mamdani tipi sistemlerde yaygın olarak minimum operatörü kullanılır.
        """

        return min(values)

    @staticmethod
    def _or(*values: float) -> float:
        """
        Bulanık OR işlemi.

        Mamdani tipi sistemlerde yaygın olarak maksimum operatörü kullanılır.
        """

        return max(values)

    @staticmethod
    def _weighted_average(rule_outputs: List[Tuple[float, float]]) -> float:
        """
        Kural aktivasyonlarına göre ağırlıklı ortalama çıkış üretir.

        Her eleman:
            (aktivasyon, önerilen_çıkış_değeri)

        Eğer hiçbir kural tetiklenmemişse 0 döner.
        """

        if not rule_outputs:
            return 0.0

        total_activation = sum(activation for activation, _ in rule_outputs)

        if total_activation == 0.0:
            return 0.0

        weighted_sum = sum(activation * output for activation, output in rule_outputs)

        return weighted_sum / total_activation

    @staticmethod
    def _max_activated_output(rule_outputs: List[Tuple[float, float]]) -> float:
        """
        Alarm gibi kritik çıktılar için en güçlü aktive edilmiş çıkışı seçer.

        Burada output doğrudan alınmaz.
        Aktivasyon derecesi ile çarpılır.

        Örnek:
            alarm_output = 100
            activation = 0.60

            gerçek alarm etkisi = 60
        """

        if not rule_outputs:
            return 0.0

        return max(activation * output for activation, output in rule_outputs)

    @staticmethod
    def _clamp(value: float, min_value: float, max_value: float) -> float:
        """
        Değeri belirtilen aralıkta sınırlar.
        """

        return max(min_value, min(value, max_value))