# Akıllı Sera Yönetim ve Karar Destek Sistemi

Bu proje, **Yapay Zekâ ve Uzman Sistemler** dersi kapsamında geliştirilen yazılım tabanlı bir akıllı sera yönetim ve karar destek sistemi prototipidir.

Projenin amacı; sera ortamını yazılım içinde simüle eden, sanal sensörlerden çevresel veriler alan, bu verileri bulanık mantık tabanlı uzman sistem yaklaşımıyla değerlendiren ve uygun kontrol kararları üreten açıklanabilir bir karar destek sistemi geliştirmektir.

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
- Sanal sensör okuma katmanı (ayarlanabilir gürültü şiddeti)
- Bulanık mantık tabanlı karar motoru (Sugeno tipi)
- Uzman sistem mantığıyla kural tabanlı karar üretimi
- Karar açıklama modülü
- Sayısal kabul kriterleri olan test senaryoları
- Terminal üzerinden çalışan uçtan uca demo
- Streamlit tabanlı gelişmiş görsel dashboard (v2)
- Gelecekte fiziksel sistem entegrasyonuna uygun modüler yapı

---

## Proje Mimarisi

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

## Kurulum

```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
# .\venv\Scripts\Activate.ps1  # Windows PowerShell
pip install -r requirements.txt
```

---

## Terminal Demosunu Çalıştırma

```bash
python app.py                        # varsayılan demo
python app.py --steps 5              # belirli adım sayısı
python app.py --steps 5 --no-noise  # gürültüsüz çalıştırma
```

---

## Test Senaryolarını Çalıştırma

```bash
python scripts/run_test_scenarios.py
```

Her senaryoda üretilen sulama, havalandırma, gölgeleme ve alarm değerleri beklenen sayısal kriterlere göre kontrol edilir. Tüm senaryolar başarıyla geçerse terminalde test özeti görüntülenir.

---

## Dashboard'u Çalıştırma

```bash
streamlit run dashboard.py
```

---

## Dashboard v2 — Özellikler

| Bölüm | Açıklama |
|---|---|
| 🌿 **Sera Sağlık Skoru** | Tüm sensörleri birleştiren 0–100 anlık skor (KPI kartı) |
| 📡 **Sensör Gauge'ları** | 5 sensör için renk kodlu yarım daire göstergeler |
| 🕸️ **Radar Chart** | 5 değişkeni tek pentagon grafikte görselleştirme |
| 🎛️ **Kontrol Aksiyonları** | Sulama / fan / gölge / alarm gauge'ları |
| 🔬 **Fuzzy Üyelik Bar'ları** | Her değişken için dilsel küme aktivasyon dereceleri |
| 📐 **Fuzzy Üyelik Eğrileri** | Trapezoid/üçgen şekiller + sensörün anlık konumu (dikey çizgi) |
| 📊 **Kural Aktivasyon Grafiği** | Tetiklenen fuzzy kuralları yatay bar chart |
| 🚨 **Alarm Zaman Çizelgesi** | Hangi adımda alarm oluştuğunu renkli bar grafik + eşik çizgileri |
| ⏮️ **Adım Adım Geri Oynatma** | Slider + butonlarla her adımı ayrı incele, delta tablosu ile değişimleri gör |
| 📈 **Simülasyon Geçmişi** | Etkileşimli Plotly line chart (sensörler + aksiyonlar) |
| 📥 **CSV Dışa Aktarma** | Tüm simülasyon geçmişi indirilebilir |
| 🤖 **Otomatik Simülasyon** | Toggle + hız slider (0.5–5 sn) ile kendi kendine çalışır |
| 🌿 **Bitki Profili** | Domates / Biber / Salatalık / Genel — seçilebilir ideal aralıklar |
| 📶 **Gürültü Şiddeti** | Sensör gürültüsünü 0–5 arası slider ile ayarla |
| 🚨 **Alarm Banner** | Kritik alarm → kırmızı animasyon, uyarı → sarı banner |

---

## Sunum İçin Önerilen Demo Akışı

1. **"Kuru Toprak" senaryosunu yükle** → sulama kararının fuzzy motor tarafından nasıl devreye girdiğini göster
2. **"Kritik Bitki Stresi" senaryosunu yükle** → alarm banner'ının kırmızı yanmasını göster
3. **Fuzzy üyelik eğrilerini göster** → "sensörün hangi kümeye ne kadar üye olduğunu anlık görüyoruz" de
4. **Adım adım playback** → "her kararı geriye dönük inceleyebiliyoruz, delta tablosunda ne değiştiği görünüyor" de
5. **Radar chart** → "5 boyutlu sera durumu tek bakışta" de
6. **Otomatik simülasyon modunu aç** → sistemin kendi kendine çalışmasını canlı göster
