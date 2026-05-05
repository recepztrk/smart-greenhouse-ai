# Akıllı Sera Yönetim ve Karar Destek Sistemi

Bu proje, **Yapay Zekâ ve Uzman Sistemler** dersi kapsamında geliştirilen yazılım tabanlı bir akıllı sera yönetim ve karar destek sistemi prototipidir.

Projenin amacı; sera ortamını yazılım içinde simüle eden, sanal sensörlerden çevresel veriler alan, bu verileri bulanık mantık tabanlı uzman sistem yaklaşımıyla değerlendiren ve uygun kontrol kararları üreten açıklanabilir bir karar destek sistemi geliştirmektir.

Bu dönem kapsamında fiziksel donanım, gerçek sensör entegrasyonu veya gömülü sistem geliştirme hedeflenmemektedir. Ana hedef; çalışan, test edilebilir, açıklanabilir ve geliştirilebilir bir yazılım prototipi ortaya koymaktır.

---

## Proje Kapsamı

Sistem aşağıdaki çevresel değişkenleri dikkate alır:

- Sıcaklık
- Hava nemi
- Toprak nemi
- Işık seviyesi
- Su tankı seviyesi

Bu değişkenlere göre aşağıdaki kontrol kararları üretilir:

- Sulama seviyesi
- Havalandırma / fan seviyesi
- Gölgeleme seviyesi
- Alarm seviyesi

---

## Temel Özellikler

- Yazılım tabanlı sera ortamı simülasyonu
- Sanal sensör okuma katmanı
- Bulanık mantık tabanlı karar motoru
- Uzman sistem mantığıyla kural tabanlı karar üretimi
- Karar açıklama modülü
- Terminal üzerinden çalışan uçtan uca demo
- Gelecekte dashboard ve fiziksel sistem entegrasyonuna uygun modüler yapı

---

## Proje Mimarisi

Genel veri akışı aşağıdaki gibidir:

```text
GreenhouseState
    ↓
GreenhouseSimulator
    ↓
VirtualSensorReader
    ↓
SensorReadings
    ↓
FuzzyEngine
    ↓
ControlActions
    ↓
ExplanationEngine
    ↓
DecisionExplanation
```

---

## Test Senaryolarını Çalıştırma

Önceden tanımlanmış fuzzy karar motoru test senaryolarını çalıştırmak için:

```bash
python scripts/run_test_scenarios.py 
```

---

## Dashboard'u Çalıştırma

Dashboard üzerinde hazır test senaryoları da seçilebilir. Bu senaryolar sayesinde sistemin normal koşullar, kuru toprak, düşük su tankı, yüksek sıcaklık ve kritik bitki stresi gibi durumlarda nasıl karar verdiği hızlıca gözlemlenebilir.

Streamlit tabanlı görsel dashboard'u çalıştırmak için:

```bash
streamlit run dashboard.py
