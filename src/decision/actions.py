"""
actions.py

Bu dosya, akıllı sera sisteminde karar motoru tarafından üretilecek kontrol
aksiyonlarını temsil eder.

Fuzzy karar motoru; sulama, havalandırma, gölgeleme ve alarm gibi çıktılar üretir.
Bu çıktıları dağınık değişkenler halinde taşımak yerine ControlActions sınıfı altında
toplamak daha temiz ve sürdürülebilir bir mimari sağlar.

Bu dosya ileride:
    - FuzzyEngine çıktısını standartlaştırmak,
    - Simülasyon motoruna uygulanacak aksiyonları taşımak,
    - Dashboard üzerinde kararları göstermek,
    - Açıklama modülüne karar bilgisini aktarmak

için kullanılacaktır.
"""

from dataclasses import dataclass, asdict
from typing import Dict


@dataclass
class ControlActions:
    """
    Sera kontrol sisteminin ürettiği aksiyonları temsil eden veri sınıfı.

    Değerler:
        irrigation_level:
            Sulama seviyesi (0-100)

        ventilation_level:
            Havalandırma/fan seviyesi (0-100)

        shading_level:
            Gölgeleme seviyesi (0-100)

        alarm_level:
            Alarm seviyesi (0-100)

    Not:
        Alarmı yalnızca True/False yapmak yerine 0-100 aralığında tutuyoruz.
        Böylece ileride "uyarı", "riskli", "kritik" gibi seviyeli alarm yapısı
        kurmak daha kolay olur.
    """

    irrigation_level: float = 0.0
    ventilation_level: float = 0.0
    shading_level: float = 0.0
    alarm_level: float = 0.0

    def __post_init__(self) -> None:
        """
        Nesne oluşturulduktan sonra tüm aksiyon değerlerini güvenli aralığa çeker.

        Fuzzy motor veya başka bir modül yanlışlıkla 0-100 dışı değer üretirse,
        sistemin geri kalanına hatalı kontrol çıktısı gitmesini engelleriz.
        """

        self.clamp_values()

    def clamp_values(self) -> None:
        """
        Tüm kontrol aksiyonlarını 0-100 aralığında sınırlar.
        """

        self.irrigation_level = self._clamp(self.irrigation_level, 0.0, 100.0)
        self.ventilation_level = self._clamp(self.ventilation_level, 0.0, 100.0)
        self.shading_level = self._clamp(self.shading_level, 0.0, 100.0)
        self.alarm_level = self._clamp(self.alarm_level, 0.0, 100.0)

    def to_dict(self) -> Dict[str, float]:
        """
        Kontrol aksiyonlarını sözlük formatına dönüştürür.

        Bu çıktı dashboard, loglama ve açıklama modüllerinde kullanılacaktır.
        """

        return asdict(self)

    def has_alarm(self, threshold: float = 50.0) -> bool:
        """
        Alarm seviyesinin belirli bir eşik üzerinde olup olmadığını döndürür.

        Args:
            threshold:
                Alarmın aktif kabul edileceği minimum seviye.

        Returns:
            Alarm aktifse True, değilse False.
        """

        return self.alarm_level >= threshold

    def is_idle(self) -> bool:
        """
        Sistemin herhangi bir aktif kontrol aksiyonu üretip üretmediğini kontrol eder.

        Returns:
            Tüm aksiyon seviyeleri 0 ise True döner.
        """

        return (
            self.irrigation_level == 0.0
            and self.ventilation_level == 0.0
            and self.shading_level == 0.0
            and self.alarm_level == 0.0
        )

    @staticmethod
    def _clamp(value: float, min_value: float, max_value: float) -> float:
        """
        Verilen değeri belirtilen aralıkta sınırlar.
        """

        return max(min_value, min(value, max_value))


def create_no_action() -> ControlActions:
    """
    Hiçbir kontrol aksiyonunun aktif olmadığı varsayılan karar nesnesi oluşturur.

    Bu fonksiyon özellikle testlerde ve sistemin başlangıç durumunda kullanılabilir.
    """

    return ControlActions(
        irrigation_level=0.0,
        ventilation_level=0.0,
        shading_level=0.0,
        alarm_level=0.0,
    )