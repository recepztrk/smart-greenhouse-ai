"""
virtual_sensors.py

Bu dosya, akıllı sera simülasyonunda kullanılan sanal sensör katmanını içerir.

Gerçek fiziksel sensörler bu dönem kapsamına dahil olmadığı için sistem,
sera ortamındaki değerleri GreenhouseState nesnesinden okuyarak sanal sensör
verisi üretir.

Bu katman özellikle önemlidir çünkü karar motorunun doğrudan simülasyonun iç
durumuna bağımlı olmasını engeller. Böylece ileride gerçek sensör entegrasyonu
yapılmak istenirse yalnızca bu katman değiştirilerek sistem genişletilebilir.

Örneğin:
    - Şu anda sıcaklık değeri simülasyondan okunur.
    - Gelecekte aynı değer DHT22, SHT31 veya benzeri fiziksel sensörden okunabilir.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, asdict
from typing import Dict

from src.simulation.greenhouse_state import GreenhouseState


@dataclass
class SensorReadings:
    """
    Sanal sensörlerden okunan çevresel değerleri temsil eden veri sınıfı.

    Bu sınıf, GreenhouseState ile benzer alanlara sahiptir.
    Fakat kavramsal olarak farklıdır:

        GreenhouseState:
            Simülasyonun gerçek iç durumudur.

        SensorReadings:
            Sensörlerin karar motoruna sunduğu ölçüm değerleridir.

    Gerçek dünyada sensör verileri her zaman kusursuz değildir.
    Bu nedenle bu sınıf ileride ölçüm hatası, gecikme veya eksik veri gibi
    durumları modellemek için de genişletilebilir.
    """

    temperature: float
    air_humidity: float
    soil_moisture: float
    light_level: float
    water_tank_level: float

    def to_dict(self) -> Dict[str, float]:
        """
        Sensör okumalarını sözlük formatına dönüştürür.

        Bu çıktı fuzzy karar motoru, dashboard ve loglama modülleri tarafından
        kolayca kullanılabilir.
        """

        return asdict(self)


class VirtualSensorReader:
    """
    Sera durumundan sanal sensör verileri üreten sınıf.

    Bu sınıf, simülatör ile karar motoru arasında bir ara katman görevi görür.
    Böylece sistem daha modüler ve gerçek donanıma geçiş için daha uygun hale gelir.
    """

    def __init__(self, noise_enabled: bool = True) -> None:
        """
        Sanal sensör okuyucusunu oluşturur.

        Args:
            noise_enabled:
                True ise sensör okumalarına küçük rastgele ölçüm hataları eklenir.
                False ise değerler GreenhouseState içinden aynen okunur.
        """

        self.noise_enabled = noise_enabled

    def read_all(self, state: GreenhouseState) -> SensorReadings:
        """
        Tüm sanal sensörleri okuyarak tek bir SensorReadings nesnesi döndürür.

        Args:
            state:
                Simülatörden gelen mevcut sera durumu.

        Returns:
            Sanal sensör okumalarını içeren SensorReadings nesnesi.
        """

        return SensorReadings(
            temperature=self.read_temperature(state),
            air_humidity=self.read_air_humidity(state),
            soil_moisture=self.read_soil_moisture(state),
            light_level=self.read_light_level(state),
            water_tank_level=self.read_water_tank_level(state),
        )

    def read_temperature(self, state: GreenhouseState) -> float:
        """
        Sıcaklık sensörü okuması üretir.

        İlk prototipte sıcaklık 0-50 °C aralığında tutulmaktadır.
        Ölçüm hatası aktifse küçük bir rastgele sapma eklenir.
        """

        value = state.temperature

        if self.noise_enabled:
            value = self._add_noise(value, min_noise=-0.3, max_noise=0.3)

        return self._clamp(value, 0.0, 50.0)

    def read_air_humidity(self, state: GreenhouseState) -> float:
        """
        Hava nemi sensörü okuması üretir.

        Hava nemi yüzdesel bir değerdir ve 0-100 aralığında tutulur.
        """

        value = state.air_humidity

        if self.noise_enabled:
            value = self._add_noise(value, min_noise=-1.0, max_noise=1.0)

        return self._clamp(value, 0.0, 100.0)

    def read_soil_moisture(self, state: GreenhouseState) -> float:
        """
        Toprak nemi sensörü okuması üretir.

        Toprak nemi, sulama kararının en kritik girdilerinden biridir.
        Bu nedenle fuzzy karar motorunda doğrudan kullanılacaktır.
        """

        value = state.soil_moisture

        if self.noise_enabled:
            value = self._add_noise(value, min_noise=-1.5, max_noise=1.5)

        return self._clamp(value, 0.0, 100.0)

    def read_light_level(self, state: GreenhouseState) -> float:
        """
        Işık seviyesi sensörü okuması üretir.

        Işık seviyesi, gölgeleme kararı ve sıcaklık davranışı açısından önemlidir.
        """

        value = state.light_level

        if self.noise_enabled:
            value = self._add_noise(value, min_noise=-2.0, max_noise=2.0)

        return self._clamp(value, 0.0, 100.0)

    def read_water_tank_level(self, state: GreenhouseState) -> float:
        """
        Su tankı seviyesi sensörü okuması üretir.

        Bu değer özellikle alarm kararında kullanılacaktır.
        Su tankı seviyesi düşükse sistem sulama kararını sınırlayabilir veya
        kullanıcıya uyarı verebilir.
        """

        value = state.water_tank_level

        if self.noise_enabled:
            value = self._add_noise(value, min_noise=-1.0, max_noise=1.0)

        return self._clamp(value, 0.0, 100.0)

    @staticmethod
    def _add_noise(value: float, min_noise: float, max_noise: float) -> float:
        """
        Verilen değere rastgele ölçüm hatası ekler.

        Bu, gerçek sensörlerde görülebilecek küçük ölçüm sapmalarını temsil eder.
        Amaç sistemi gereksiz karmaşık yapmak değil, daha gerçekçi test ortamı
        oluşturmaktır.
        """

        return value + random.uniform(min_noise, max_noise)

    @staticmethod
    def _clamp(value: float, min_value: float, max_value: float) -> float:
        """
        Verilen değeri belirtilen minimum ve maksimum aralıkta sınırlar.

        Noise eklendikten sonra değerlerin fiziksel olarak anlamsız aralıklara
        çıkmasını engeller.
        """

        return max(min_value, min(value, max_value))