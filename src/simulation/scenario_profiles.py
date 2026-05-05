"""
scenario_profiles.py

Bu dosya, dashboard ve test süreçlerinde kullanılabilecek hazır sera senaryolarını içerir.

Amaç:
    - Kullanıcının dashboard üzerinde tek tek slider ayarlamak zorunda kalmadan
      hazır senaryo seçebilmesini sağlamak
    - Demo ve sunum sürecini kolaylaştırmak
    - Fuzzy karar motorunun farklı koşullarda nasıl davrandığını hızlı göstermek

Bu dosyada tanımlanan senaryolar, fiziksel ölçüm verisi değildir.
Ders projesi kapsamında karar motorunu test etmek ve göstermek için hazırlanmış
kontrollü örnek durumlardır.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from src.simulation.greenhouse_state import GreenhouseState


@dataclass
class ScenarioProfile:
    """
    Hazır sera senaryosunu temsil eden veri sınıfı.

    Alanlar:
        name:
            Dashboard üzerinde gösterilecek senaryo adı.

        description:
            Senaryonun neyi temsil ettiğini açıklayan kısa metin.

        state:
            Senaryoya ait başlangıç sera durumu.

        expected_behavior:
            Sistemden beklenen genel karar davranışı.
    """

    name: str
    description: str
    state: GreenhouseState
    expected_behavior: str


def get_scenario_profiles() -> List[ScenarioProfile]:
    """
    Dashboard ve testlerde kullanılabilecek hazır senaryo listesini döndürür.
    """

    return [
        ScenarioProfile(
            name="Normal Sera Koşulları",
            description="Sera ortamının dengeli olduğu referans durum.",
            state=GreenhouseState(
                temperature=25.0,
                air_humidity=55.0,
                soil_moisture=55.0,
                light_level=55.0,
                water_tank_level=80.0,
            ),
            expected_behavior=(
                "Sistem gereksiz müdahale üretmemeli; sulama, fan ve alarm düşük "
                "veya kapalı seviyede kalmalıdır."
            ),
        ),
        ScenarioProfile(
            name="Toprak Kuru, Su Yeterli",
            description="Toprak nemi düşük fakat su tankı yeterli seviyede.",
            state=GreenhouseState(
                temperature=28.0,
                air_humidity=50.0,
                soil_moisture=20.0,
                light_level=60.0,
                water_tank_level=80.0,
            ),
            expected_behavior=(
                "Toprak kuru olduğu için sulama yüksek seviyede olmalı; "
                "su tankı yeterli olduğu için alarm düşük kalmalıdır."
            ),
        ),
        ScenarioProfile(
            name="Toprak Kuru, Su Tankı Düşük",
            description="Sulama ihtiyacı var ancak su kaynağı yetersiz.",
            state=GreenhouseState(
                temperature=30.0,
                air_humidity=45.0,
                soil_moisture=18.0,
                light_level=65.0,
                water_tank_level=15.0,
            ),
            expected_behavior=(
                "Sulama sınırlı tutulmalı, su tankı düşük olduğu için alarm yüksek "
                "veya kritik seviyede olmalıdır."
            ),
        ),
        ScenarioProfile(
            name="Sıcaklık Yüksek",
            description="Sera içi sıcaklık yüksek seviyede.",
            state=GreenhouseState(
                temperature=37.0,
                air_humidity=50.0,
                soil_moisture=50.0,
                light_level=65.0,
                water_tank_level=75.0,
            ),
            expected_behavior=(
                "Havalandırma seviyesi yüksek olmalıdır. Sulama kararı ise daha çok "
                "toprak nemine bağlı kalmalıdır."
            ),
        ),
        ScenarioProfile(
            name="Sıcaklık ve Işık Yüksek",
            description="Isı ve ışık stresi riski olan durum.",
            state=GreenhouseState(
                temperature=36.0,
                air_humidity=40.0,
                soil_moisture=45.0,
                light_level=90.0,
                water_tank_level=70.0,
            ),
            expected_behavior=(
                "Havalandırma ve gölgeleme yüksek seviyede olmalıdır. Sistem aşırı "
                "ışık ve sıcaklık durumunu açıklamalıdır."
            ),
        ),
        ScenarioProfile(
            name="Nem ve Toprak Nemi Yüksek",
            description="Hava nemi ve toprak neminin birlikte yüksek olduğu durum.",
            state=GreenhouseState(
                temperature=24.0,
                air_humidity=85.0,
                soil_moisture=82.0,
                light_level=50.0,
                water_tank_level=75.0,
            ),
            expected_behavior=(
                "Sulama kapalı olmalı; yüksek nem nedeniyle hastalık riski uyarısı "
                "üretilebilir."
            ),
        ),
        ScenarioProfile(
            name="Su Tankı Kritik Düşük",
            description="Su tankının kritik seviyeye düştüğü durum.",
            state=GreenhouseState(
                temperature=26.0,
                air_humidity=50.0,
                soil_moisture=50.0,
                light_level=55.0,
                water_tank_level=10.0,
            ),
            expected_behavior=(
                "Alarm yüksek seviyede olmalı ve açıklamada su tankı kritik seviyesi "
                "belirtilmelidir."
            ),
        ),
        ScenarioProfile(
            name="Kritik Bitki Stresi",
            description="Yüksek sıcaklık, düşük nem, kuru toprak ve düşük su tankı birlikte.",
            state=GreenhouseState(
                temperature=38.0,
                air_humidity=25.0,
                soil_moisture=15.0,
                light_level=88.0,
                water_tank_level=20.0,
            ),
            expected_behavior=(
                "Alarm kritik olmalı; fan ve gölgeleme yüksek çalışmalı; sulama ise "
                "su tankı düşük olduğu için sınırlanabilir."
            ),
        ),
        ScenarioProfile(
            name="Işık Düşük",
            description="Işık seviyesinin düşük olduğu durum.",
            state=GreenhouseState(
                temperature=22.0,
                air_humidity=60.0,
                soil_moisture=50.0,
                light_level=20.0,
                water_tank_level=80.0,
            ),
            expected_behavior=(
                "Gölgeleme kapalı olmalıdır. Alarm beklenmez."
            ),
        ),
        ScenarioProfile(
            name="Düşük Sıcaklık",
            description="Sıcaklığın düşük olduğu ve fanın çalışmaması gereken durum.",
            state=GreenhouseState(
                temperature=14.0,
                air_humidity=55.0,
                soil_moisture=55.0,
                light_level=45.0,
                water_tank_level=80.0,
            ),
            expected_behavior=(
                "Havalandırma kapalı olmalı ve gereksiz müdahale yapılmamalıdır."
            ),
        ),
    ]


def get_scenario_by_name(name: str) -> ScenarioProfile:
    """
    Senaryo adına göre ilgili ScenarioProfile nesnesini döndürür.

    Eğer isim bulunamazsa ilk senaryo olan normal sera koşulları döndürülür.
    """

    scenarios = get_scenario_profiles()

    for scenario in scenarios:
        if scenario.name == name:
            return scenario

    return scenarios[0]