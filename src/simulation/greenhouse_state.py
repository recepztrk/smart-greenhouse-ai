"""
greenhouse_state.py

Bu dosya, akıllı sera simülasyonunda kullanılan anlık sera durumunu temsil eder.

GreenhouseState sınıfı; sıcaklık, hava nemi, toprak nemi, ışık seviyesi ve su tankı
seviyesi gibi temel çevresel değişkenleri tek bir veri modeli altında toplar.

Bu yapı projenin temel veri taşıyıcısıdır. Simülasyon motoru, sanal sensörler,
fuzzy karar motoru ve dashboard bu veri modelini kullanarak çalışacaktır.
"""

from dataclasses import dataclass, asdict


@dataclass
class GreenhouseState:
    """
    Sera ortamının anlık durumunu temsil eden veri sınıfı.

    Değerler:
        temperature: Ortam sıcaklığı (°C)
        air_humidity: Hava nemi (%)
        soil_moisture: Toprak nemi (%)
        light_level: Işık seviyesi (%)
        water_tank_level: Su tankı seviyesi (%)
    """

    temperature: float = 25.0
    air_humidity: float = 50.0
    soil_moisture: float = 50.0
    light_level: float = 50.0
    water_tank_level: float = 80.0

    def __post_init__(self) -> None:
        """
        Nesne oluşturulduktan sonra değerleri güvenli aralıklara çeker.

        Simülasyon sırasında bazı değerler negatif olabilir veya 100'ü aşabilir.
        Örneğin sulama yapılınca toprak nemi 100 üstüne çıkabilir.
        Bu nedenle fiziksel olarak anlamlı aralığın dışına çıkılmasını engelliyoruz.
        """

        self.clamp_values()

    def clamp_values(self) -> None:
        """
        Sera değişkenlerini mantıklı fiziksel sınırlar içinde tutar.

        Yüzdesel değerler 0-100 aralığında tutulur.
        Sıcaklık için bu ilk prototipte 0-50 °C aralığı yeterli kabul edilmiştir.
        """

        self.temperature = self._clamp(self.temperature, 0.0, 50.0)
        self.air_humidity = self._clamp(self.air_humidity, 0.0, 100.0)
        self.soil_moisture = self._clamp(self.soil_moisture, 0.0, 100.0)
        self.light_level = self._clamp(self.light_level, 0.0, 100.0)
        self.water_tank_level = self._clamp(self.water_tank_level, 0.0, 100.0)

    def to_dict(self) -> dict:
        """
        Sera durumunu sözlük formatına dönüştürür.

        Bu metot ileride dashboard, loglama ve CSV/JSON kayıt işlemlerinde
        doğrudan kullanılacaktır.
        """

        return asdict(self)

    def update(
        self,
        temperature_delta: float = 0.0,
        air_humidity_delta: float = 0.0,
        soil_moisture_delta: float = 0.0,
        light_level_delta: float = 0.0,
        water_tank_delta: float = 0.0,
    ) -> None:
        """
        Sera durumunu verilen değişim miktarlarına göre günceller.

        Bu metot simülasyon motorunda kullanılacaktır.
        Örneğin:
            - Fan çalışırsa sıcaklık düşebilir.
            - Sulama yapılırsa toprak nemi artar.
            - Sulama yapılırsa su tankı seviyesi azalır.
        """

        self.temperature += temperature_delta
        self.air_humidity += air_humidity_delta
        self.soil_moisture += soil_moisture_delta
        self.light_level += light_level_delta
        self.water_tank_level += water_tank_delta

        # Her güncellemeden sonra değerleri tekrar güvenli aralığa çekiyoruz.
        self.clamp_values()

    @staticmethod
    def _clamp(value: float, min_value: float, max_value: float) -> float:
        """
        Verilen değeri min_value ile max_value arasında sınırlar.

        Bu yardımcı metot, simülasyonun fiziksel olarak anlamsız değerlere
        gitmesini engeller.
        """

        return max(min_value, min(value, max_value))


def create_default_greenhouse_state() -> GreenhouseState:
    """
    Varsayılan başlangıç sera durumunu oluşturur.

    Projenin ilk aşamasında simülasyonu bu başlangıç değerleriyle başlatacağız.
    Daha sonra dashboard üzerinden kullanıcı bu değerleri değiştirebilir.
    """

    return GreenhouseState(
        temperature=25.0,
        air_humidity=50.0,
        soil_moisture=45.0,
        light_level=60.0,
        water_tank_level=80.0,
    )