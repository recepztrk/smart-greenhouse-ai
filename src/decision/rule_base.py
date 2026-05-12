"""
rule_base.py

Bu dosya, fuzzy karar motorunda kullanılan uzman sistem kurallarını dokümantasyon
amaçlı merkezi bir listede tutar.

Not:
    FuzzyEngine şu anda kuralları kendi evaluate metodu içinde çalıştırmaktadır.
    Bu dosya doğrudan çıkarım motoru olarak kullanılmaz. Amacı, rapor, sunum,
    teknik dokümantasyon veya ileride yapılacak refaktör işlemleri için kural
    tabanını okunabilir biçimde göstermektir.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class RuleDescription:
    """
    Uzman sistem kuralının insan tarafından okunabilir açıklamasını temsil eder.
    """

    category: str
    condition: str
    decision: str


FUZZY_RULE_DESCRIPTIONS: List[RuleDescription] = [
    RuleDescription(
        category="Sulama",
        condition="Toprak kuru ve su tankı orta/yeterli seviyede",
        decision="Sulama yüksek seviyede çalıştırılır.",
    ),
    RuleDescription(
        category="Sulama",
        condition="Toprak kuru, sıcaklık yüksek ve su tankı orta/yeterli seviyede",
        decision="Sulama çok yüksek seviyede çalıştırılır.",
    ),
    RuleDescription(
        category="Sulama + Alarm",
        condition="Toprak kuru fakat su tankı düşük seviyede",
        decision="Sulama sınırlanır ve alarm yükseltilir.",
    ),
    RuleDescription(
        category="Sulama",
        condition="Toprak nemi uygun veya ıslak",
        decision="Sulama kapalı tutulur.",
    ),
    RuleDescription(
        category="Havalandırma",
        condition="Sıcaklık yüksek ve hava nemi yüksek",
        decision="Fan yüksek seviyede çalıştırılır.",
    ),
    RuleDescription(
        category="Havalandırma",
        condition="Sıcaklık yüksek ve hava nemi düşük/normal",
        decision="Fan orta-yüksek seviyede çalıştırılır.",
    ),
    RuleDescription(
        category="Havalandırma",
        condition="Sıcaklık normal ve hava nemi yüksek",
        decision="Fan orta seviyede çalıştırılır.",
    ),
    RuleDescription(
        category="Havalandırma",
        condition="Sıcaklık düşük",
        decision="Fan kapalı tutulur.",
    ),
    RuleDescription(
        category="Gölgeleme",
        condition="Işık yüksek ve sıcaklık yüksek",
        decision="Gölgeleme yüksek seviyede uygulanır.",
    ),
    RuleDescription(
        category="Gölgeleme",
        condition="Işık yüksek ve sıcaklık normal",
        decision="Gölgeleme orta seviyede uygulanır.",
    ),
    RuleDescription(
        category="Gölgeleme",
        condition="Işık düşük",
        decision="Gölgeleme kapalı tutulur.",
    ),
    RuleDescription(
        category="Gölgeleme",
        condition="Işık orta seviyede",
        decision="Gölgeleme düşük seviyede uygulanır.",
    ),
    RuleDescription(
        category="Alarm",
        condition="Su tankı düşük",
        decision="Alarm yüksek seviyeye çıkarılır.",
    ),
    RuleDescription(
        category="Alarm",
        condition="Su tankı düşük ve toprak kuru",
        decision="Alarm kritik seviyeye çıkarılır.",
    ),
    RuleDescription(
        category="Alarm",
        condition="Sıcaklık yüksek, toprak kuru ve hava nemi düşük",
        decision="Bitki stresi alarmı oluşturulur.",
    ),
    RuleDescription(
        category="Alarm",
        condition="Toprak ıslak ve hava nemi yüksek",
        decision="Hastalık riski alarmı oluşturulur.",
    ),
]


def get_rule_descriptions() -> List[RuleDescription]:
    """
    Fuzzy uzman sistem kurallarını okunabilir açıklama listesi olarak döndürür.
    """

    return FUZZY_RULE_DESCRIPTIONS
