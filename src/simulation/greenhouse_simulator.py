"""
greenhouse_simulator.py

Bu dosya, akıllı sera projesindeki sera ortamı simülasyonunu yönetir.

GreenhouseSimulator sınıfı, GreenhouseState veri modelini kullanarak sera ortamındaki
çevresel değişkenlerin zaman içinde nasıl değiştiğini simüle eder.

İlk prototipte fiziksel donanım kullanılmadığı için sıcaklık, nem, toprak nemi,
ışık seviyesi ve su tankı seviyesi yazılım içinde modellenir.

Bu simülatör ileride:
    - Fuzzy karar motorundan gelen sulama/fan/gölgeleme kararlarını uygulamak,
    - Dashboard üzerinde canlı sera davranışı göstermek,
    - Test senaryoları üretmek,
    - Karar açıklama modülüne veri sağlamak

için kullanılacaktır.
"""

from __future__ import annotations

import random
from typing import Dict, Optional

from src.simulation.greenhouse_state import GreenhouseState, create_default_greenhouse_state


class GreenhouseSimulator:
    """
    Sera ortamının zaman içindeki davranışını simüle eden sınıf.

    Bu sınıf, gerçek sensörler yerine yazılım tabanlı bir çevre modeli kullanır.
    Her simülasyon adımında sera değişkenleri küçük miktarlarda güncellenir.

    Not:
        Bu ilk sürüm basit ve anlaşılır tutulmuştur.
        Amaç fiziksel olarak kusursuz bir sera modeli kurmak değil,
        fuzzy karar sistemini test edebileceğimiz kontrollü bir ortam oluşturmaktır.
    """

    def __init__(self, initial_state: Optional[GreenhouseState] = None) -> None:
        """
        Simülatörü başlangıç sera durumu ile oluşturur.

        Args:
            initial_state: Kullanıcı tarafından verilen başlangıç sera durumu.
                           Verilmezse varsayılan sera durumu kullanılır.
        """

        self.state = initial_state if initial_state is not None else create_default_greenhouse_state()

        # Simülasyonun kaç adım ilerlediğini takip ediyoruz.
        # Bu bilgi ileride grafiklerde ve log kayıtlarında kullanılabilir.
        self.current_step = 0

    def step(self) -> GreenhouseState:
        """
        Simülasyonu bir zaman adımı ilerletir.

        Bu metot şu anda yalnızca doğal çevresel değişimi uygular.
        Daha sonraki aşamada fuzzy karar motorundan gelen aksiyonlar da bu metoda
        dahil edilecektir.

        Returns:
            Güncellenmiş GreenhouseState nesnesi.
        """

        self.current_step += 1

        # Önce sera ortamının doğal değişimini hesaplıyoruz.
        natural_changes = self._calculate_natural_changes()

        # Hesaplanan değişimleri mevcut sera durumuna uyguluyoruz.
        self.state.update(
            temperature_delta=natural_changes["temperature_delta"],
            air_humidity_delta=natural_changes["air_humidity_delta"],
            soil_moisture_delta=natural_changes["soil_moisture_delta"],
            light_level_delta=natural_changes["light_level_delta"],
            water_tank_delta=natural_changes["water_tank_delta"],
        )

        return self.state

    def _calculate_natural_changes(self) -> Dict[str, float]:
        """
        Sera ortamında dış müdahale olmadan oluşan doğal değişimleri hesaplar.

        Buradaki değerler gerçek fiziksel model değildir; ders projesi için yeterli,
        kontrol edilebilir ve açıklanabilir bir simülasyon davranışı üretmek amacıyla
        seçilmiştir.

        Returns:
            Her çevresel değişken için delta değerlerini içeren sözlük.
        """

        # Işık seviyesi gün içinde dalgalanıyormuş gibi küçük rastgele değişim alır.
        light_delta = random.uniform(-3.0, 3.0)

        # Işık yüksekse sıcaklık artma eğilimindedir.
        # Işık düşükse sıcaklık hafif düşebilir.
        if self.state.light_level > 70:
            temperature_delta = random.uniform(0.1, 0.5)
        elif self.state.light_level < 30:
            temperature_delta = random.uniform(-0.4, -0.1)
        else:
            temperature_delta = random.uniform(-0.2, 0.2)

        # Sıcaklık arttıkça hava nemi bir miktar düşebilir.
        # Bu basitleştirilmiş ilişki, sera ortamında değişkenlerin birbirini
        # etkilediğini göstermek için eklenmiştir.
        if temperature_delta > 0:
            air_humidity_delta = random.uniform(-0.4, -0.1)
        else:
            air_humidity_delta = random.uniform(-0.1, 0.2)

        # Sulama yapılmadığı varsayımıyla toprak nemi zamanla azalır.
        # Bu, ileride fuzzy sistemin sulama kararı üretmesini gerektirecek temel etkidir.
        soil_moisture_delta = random.uniform(-0.8, -0.2)

        # Doğal çevresel değişim su tankını etkilemez.
        # Su tankı yalnızca sulama aksiyonu geldiğinde azalacaktır.
        water_tank_delta = 0.0

        return {
            "temperature_delta": temperature_delta,
            "air_humidity_delta": air_humidity_delta,
            "soil_moisture_delta": soil_moisture_delta,
            "light_level_delta": light_delta,
            "water_tank_delta": water_tank_delta,
        }

    def apply_actions(
        self,
        irrigation_level: float = 0.0,
        ventilation_level: float = 0.0,
        shading_level: float = 0.0,
    ) -> GreenhouseState:
        """
        Kontrol kararlarını sera ortamına uygular.

        Bu metot ileride fuzzy karar motorundan gelen çıktılarla beslenecektir.

        Args:
            irrigation_level: Sulama seviyesi (0-100)
            ventilation_level: Havalandırma/fan seviyesi (0-100)
            shading_level: Gölgeleme seviyesi (0-100)

        Returns:
            Aksiyonlar uygulandıktan sonraki güncel sera durumu.
        """

        # Aksiyon değerlerini güvenli aralığa çekiyoruz.
        irrigation_level = self._clamp(irrigation_level, 0.0, 100.0)
        ventilation_level = self._clamp(ventilation_level, 0.0, 100.0)
        shading_level = self._clamp(shading_level, 0.0, 100.0)

        # Sulama arttıkça toprak nemi artar.
        # Aynı zamanda su tankı seviyesi azalır.
        soil_moisture_delta = irrigation_level * 0.08
        water_tank_delta = -irrigation_level * 0.04

        # Fan/havalandırma arttıkça sıcaklık düşer.
        # Havalandırmanın hava nemi üzerinde küçük düşürücü etkisi de modellenmiştir.
        temperature_delta = -ventilation_level * 0.04
        air_humidity_delta = -ventilation_level * 0.015

        # Gölgeleme arttıkça ışık seviyesi düşer.
        light_level_delta = -shading_level * 0.06

        self.state.update(
            temperature_delta=temperature_delta,
            air_humidity_delta=air_humidity_delta,
            soil_moisture_delta=soil_moisture_delta,
            light_level_delta=light_level_delta,
            water_tank_delta=water_tank_delta,
        )

        return self.state

    def get_state(self) -> GreenhouseState:
        """
        Mevcut sera durumunu döndürür.

        Dashboard, test senaryoları ve karar motoru bu metot üzerinden
        güncel sera durumunu okuyabilir.
        """

        return self.state

    def reset(self, new_state: Optional[GreenhouseState] = None) -> GreenhouseState:
        """
        Simülasyonu başlangıç durumuna döndürür.

        Args:
            new_state: İsteğe bağlı yeni başlangıç durumu.

        Returns:
            Sıfırlanmış sera durumu.
        """

        self.state = new_state if new_state is not None else create_default_greenhouse_state()
        self.current_step = 0
        return self.state

    @staticmethod
    def _clamp(value: float, min_value: float, max_value: float) -> float:
        """
        Verilen değeri belirtilen aralıkta sınırlar.

        Bu yardımcı metot, dışarıdan gelen aksiyon değerlerinin güvenli aralıkta
        kalmasını sağlar.
        """

        return max(min_value, min(value, max_value))