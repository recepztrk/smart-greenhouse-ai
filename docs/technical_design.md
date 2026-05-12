# Teknik Tasarım Dokümanı

## Hibrit Akıllı Sera Yönetim ve Karar Destek Sistemi

Bu doküman, **Yapay Zekâ ve Uzman Sistemler** dersi kapsamında geliştirilen Akıllı Sera Yönetim ve Karar Destek Sistemi projesinin teknik tasarımını açıklamak amacıyla hazırlanmıştır.

Proje; sera ortamını yazılım tabanlı olarak simüle eden, sanal sensörlerden çevresel veri alan, bu verileri bulanık mantık tabanlı uzman sistem yaklaşımıyla yorumlayan ve sulama, havalandırma, gölgeleme ve alarm kararları üreten açıklanabilir bir karar destek sistemi olarak tasarlanmıştır.

---

## 1. Projenin Teknik Amacı

Bu projenin temel teknik amacı, fiziksel donanım kullanılmadan sera ortamının yazılım içinde modellenmesi ve bu ortam üzerinde çalışan karar destek sisteminin geliştirilmesidir.

Sistem aşağıdaki hedefleri karşılayacak şekilde tasarlanmıştır:

- Sera ortamının anlık durumunu temsil etmek
- Sanal sensörler aracılığıyla çevresel değerleri okumak
- Bulanık mantık tabanlı karar üretmek
- Uzman sistem yaklaşımıyla kural tabanlı kontrol sağlamak
- Üretilen kararların gerekçelerini açıklamak
- Terminal ve dashboard üzerinden sistem davranışını göstermek
- Gelecekte gerçek sensör ve gömülü sistem entegrasyonuna uygun modüler yapı sunmak

Bu dönemki proje kapsamı fiziksel sera kurulumu değil, çalışan ve açıklanabilir bir yazılım prototipi geliştirmektir.

---

## 2. Genel Sistem Mimarisi

Sistem modüler bir mimariyle tasarlanmıştır. Her modül belirli bir sorumluluğa sahiptir. Bu yaklaşım, kodun okunabilirliğini artırır ve ileride yapılacak geliştirmeleri kolaylaştırır.

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

Bu akışta önce sera ortamı simüle edilir, ardından sanal sensörler bu ortamdan veri okur. Okunan değerler fuzzy karar motoruna gönderilir. Karar motoru kontrol aksiyonları üretir. Açıklama modülü ise bu kararların neden üretildiğini kullanıcıya açıklar.

---

## 3. Proje Dizin Yapısı

Proje dizin yapısı aşağıdaki gibi düzenlenmiştir:

```text
smart-greenhouse-ai/
│
├── app.py
├── dashboard.py
├── README.md
├── requirements.txt
│
├── src/
│   ├── simulation/
│   │   ├── greenhouse_state.py
│   │   ├── greenhouse_simulator.py
│   │   ├── scenario_profiles.py
│   │   └── virtual_sensors.py
│   │
│   ├── decision/
│   │   ├── actions.py
│   │   ├── fuzzy_engine.py
│   │   └── rule_base.py
│   │
│   ├── explanation/
│   │   └── explanation_engine.py
│   │
│   └── utils/
│       └── logger.py
│
├── scripts/
│   └── run_test_scenarios.py
│
├── docs/
│   ├── test_scenarios.md
│   └── technical_design.md
│
├── data/
│
└── outputs/
```

Bu yapı, simülasyon, karar verme, açıklama üretme, loglama, test ve arayüz katmanlarını birbirinden ayırır.

---

## 4. Temel Modüller

### 4.1. GreenhouseState

Dosya:

```text
src/simulation/greenhouse_state.py
```

`GreenhouseState`, sera ortamının anlık durumunu temsil eden temel veri modelidir.

Tutulan değişkenler:

- Sıcaklık
- Hava nemi
- Toprak nemi
- Işık seviyesi
- Su tankı seviyesi

Bu sınıfın temel görevi, sera ortamına ait çevresel değerleri tek bir veri yapısı altında toplamaktır.

Ayrıca değerlerin fiziksel olarak anlamlı sınırlar içinde kalması sağlanır. Örneğin nem değerleri 0–100 aralığında, sıcaklık ise ilk prototipte 0–50 °C aralığında tutulur.

Bu yapı, sistemin diğer modülleri tarafından ortak veri modeli olarak kullanılır.

---

### 4.2. GreenhouseSimulator

Dosya:

```text
src/simulation/greenhouse_simulator.py
```

`GreenhouseSimulator`, sera ortamının zaman içindeki davranışını simüle eder.

Bu modül iki temel işlev yürütür:

1. Doğal çevresel değişimleri uygulamak
2. Kontrol aksiyonlarının sera ortamına etkisini simüle etmek

Örnek davranışlar:

- Sulama yapılmazsa toprak nemi zamanla azalır.
- Sulama yapılırsa toprak nemi artar.
- Sulama yapılınca su tankı seviyesi azalır.
- Fan çalışırsa sıcaklık düşer.
- Gölgeleme uygulanırsa ışık seviyesi azalır.
- Işık seviyesi yüksek olduğunda sıcaklık artma eğilimi gösterir.

Bu simülatör gerçek fiziksel sera modelinin birebir karşılığı değildir. Amaç, fuzzy karar sistemini test edebilecek kontrollü ve anlaşılır bir ortam oluşturmaktır.

---

### 4.3. VirtualSensorReader

Dosya:

```text
src/simulation/virtual_sensors.py
```

`VirtualSensorReader`, simülasyon ortamındaki sera durumundan sanal sensör okumaları üretir.

Bu katman, karar motorunun doğrudan simülasyonun iç durumuna bağımlı olmasını engeller. Böylece sistem daha gerçekçi ve genişletilebilir hale gelir.

Şu anda sensör değerleri `GreenhouseState` üzerinden okunmaktadır. İsteğe bağlı olarak küçük rastgele ölçüm hataları eklenebilir. Bu durum, gerçek sensörlerde görülebilecek küçük sapmaları temsil eder.

Gelecekte gerçek sensörler kullanılmak istenirse, sistemin tamamını değiştirmek yerine yalnızca bu katman güncellenebilir.

---

### 4.4. SensorReadings

Dosya:

```text
src/simulation/virtual_sensors.py
```

`SensorReadings`, sanal sensörlerden okunan değerleri taşıyan veri modelidir.

Bu yapı, `GreenhouseState` ile benzer alanlara sahiptir. Ancak kavramsal olarak farklıdır.

- `GreenhouseState`: Simülasyonun gerçek iç durumunu temsil eder.
- `SensorReadings`: Karar motoruna sunulan ölçüm değerlerini temsil eder.

Bu ayrım, sistemin ileride gerçek donanıma taşınması açısından önemlidir.

---

### 4.5. ControlActions

Dosya:

```text
src/decision/actions.py
```

`ControlActions`, fuzzy karar motorunun ürettiği kontrol aksiyonlarını temsil eder.

İçerdiği karar çıktıları:

- Sulama seviyesi
- Havalandırma seviyesi
- Gölgeleme seviyesi
- Alarm seviyesi

Tüm değerler 0–100 aralığında tutulur.

Alarm değeri yalnızca `True/False` olarak değil, 0–100 aralığında seviyeli olarak tasarlanmıştır. Böylece sistem düşük uyarı, orta risk ve kritik alarm gibi farklı seviyelerde çıktı üretebilir.

---

## 5. Fuzzy Karar Motoru

Dosya:

```text
src/decision/fuzzy_engine.py
```

`FuzzyEngine`, sistemin temel karar üretim modülüdür.

Bu modül, sanal sensörlerden gelen değerleri bulanık üyelik fonksiyonlarıyla değerlendirir ve uzman kurallar üzerinden kontrol aksiyonları üretir.

Kullanılan giriş değişkenleri:

- Sıcaklık
- Hava nemi
- Toprak nemi
- Işık seviyesi
- Su tankı seviyesi

Üretilen çıkış değişkenleri:

- Sulama seviyesi
- Havalandırma seviyesi
- Gölgeleme seviyesi
- Alarm seviyesi

---

## 6. Bulanık Üyelik Yapısı

Sistem içinde her giriş değişkeni belirli dilsel kümelere ayrılmıştır.

Örnek:

### Sıcaklık

- Düşük
- Normal
- Yüksek

### Hava Nemi

- Düşük
- Normal
- Yüksek

### Toprak Nemi

- Kuru
- Uygun
- Islak

### Işık Seviyesi

- Düşük
- Orta
- Yüksek

### Su Tankı Seviyesi

- Düşük
- Orta
- Yeterli

Üyelik hesaplamalarında üçgensel ve yamuksal üyelik fonksiyonları kullanılmıştır.

Bu yapı, kesin sensör değerlerinin insan benzeri dilsel ifadelere dönüştürülmesini sağlar.

Örneğin:

```text
Toprak nemi = %22
```

Bu değer sistem tarafından “kuru” kümesine yüksek üyelik derecesiyle dahil edilebilir.

---

## 7. Fuzzy Kural Tabanı

Fuzzy karar motorunda uzman sistem yaklaşımına uygun şekilde kural tabanlı karar üretimi yapılır.

Örnek kurallar:

```text
Eğer toprak kuru ve su tankı yeterli ise sulama yüksek olmalı.
```

```text
Eğer toprak kuru fakat su tankı düşük ise sulama sınırlı olmalı ve alarm yükselmeli.
```

```text
Eğer sıcaklık yüksek ise fan orta-yüksek çalışmalı.
```

```text
Eğer ışık fazla ve sıcaklık yüksek ise gölgeleme yüksek olmalı.
```

```text
Eğer su tankı düşük ise alarm yüksek olmalı.
```

Kuralların tetiklenme dereceleri fuzzy AND/OR işlemleriyle hesaplanır.

- AND işlemi için minimum operatörü kullanılır.
- OR işlemi için maksimum operatörü kullanılır.

Bu yapı, klasik eşik tabanlı sistemlerden farklı olarak kademeli karar üretimi sağlar.

---

## 8. Karar Üretim Yaklaşımı

Bu prototipte basitleştirilmiş Sugeno-benzeri bir yaklaşım kullanılmıştır.

Süreç şu şekildedir:

1. Sensör değerleri alınır.
2. Her değer için bulanık üyelik dereceleri hesaplanır.
3. Fuzzy kuralların aktivasyon dereceleri belirlenir.
4. Her kural ilgili çıkış için sabit bir değer önerir.
5. Sulama, havalandırma ve gölgeleme kararları ağırlıklı ortalama ile üretilir.
6. Alarm kararı daha korumacı şekilde en güçlü alarm etkisi üzerinden belirlenir.

Bu yöntem ilk prototip için yeterince açıklanabilir ve kontrol edilebilir bir yapı sağlar.

---

## 9. Açıklama Modülü

Dosya:

```text
src/explanation/explanation_engine.py
```

`ExplanationEngine`, fuzzy karar motoru tarafından üretilen kararları kullanıcıya açıklamak için geliştirilmiştir.

Bu modül yeni karar üretmez. Sadece mevcut kararları ve tetiklenen kuralları yorumlar.

Ürettiği bilgiler:

- Genel karar özeti
- Sulama kararının açıklaması
- Havalandırma kararının açıklaması
- Gölgeleme kararının açıklaması
- Alarm kararının açıklaması
- Tetiklenen fuzzy kurallar
- Kritik uyarılar

Örnek açıklama:

```text
Sulama seviyesi sınırlı tutuldu. Bu durum genellikle su tankı seviyesinin düşük olması veya sulama kararının riskli görülmesiyle ilişkilidir.
```

Bu modül, projeyi yalnızca otomatik kontrol sistemi olmaktan çıkarır ve açıklanabilir karar destek sistemi haline getirir.

---

## 10. Terminal Demo

Dosya:

```text
app.py
```

`app.py`, sistemin terminal üzerinden uçtan uca çalıştırılmasını sağlar.

Demo akışı:

1. Sera simülasyonu başlatılır.
2. Sanal sensörler mevcut sera durumunu okur.
3. Fuzzy karar motoru sensör verilerini değerlendirir.
4. Kontrol aksiyonları üretilir.
5. Açıklama motoru kararların nedenini açıklar.
6. Aksiyonlar sera simülasyonuna uygulanır.
7. Doğal çevresel değişim uygulanır.
8. Yeni sera durumu terminalde gösterilir.

Çalıştırma komutu:

```bash
python app.py
```

Belirli adım sayısıyla çalıştırmak için:

```bash
python app.py --steps 5
```

Sensör ölçüm hatasını kapatmak için:

```bash
python app.py --steps 5 --no-noise
```

---

## 11. Streamlit Dashboard

Dosya:

```text
dashboard.py
```

Dashboard, sistemin görsel arayüzünü sağlar.

Dashboard üzerinden kullanıcı:

- Başlangıç sera değerlerini ayarlayabilir.
- Hazır sera senaryolarını seçebilir.
- Simülasyonu tek adım çalıştırabilir.
- Simülasyonu çoklu adım çalıştırabilir.
- Anlık sera durumunu görebilir.
- Sanal sensör okumalarını izleyebilir.
- Fuzzy karar motorunun ürettiği aksiyonları görebilir.
- Karar açıklamalarını inceleyebilir.
- Tetiklenen fuzzy kuralları tablo halinde görüntüleyebilir.
- Simülasyon geçmişini grafiklerle takip edebilir.

Çalıştırma komutu:

```bash
streamlit run dashboard.py
```

Dashboard, projenin sunum ve demo aşaması için en önemli bileşenlerden biridir.

---

## 12. Simülasyon Loglama Sistemi

Dosya:

```text
src/utils/logger.py
```

`SimulationLogger`, simülasyon sırasında oluşan verileri CSV dosyasına kaydeder.

Kaydedilen bilgiler:

- Zaman damgası
- Simülasyon adımı
- Aksiyon öncesi sera durumu
- Sensör okumaları
- Kontrol aksiyonları
- Aksiyon sonrası sera durumu
- Karar özeti
- Uyarılar
- Tetiklenen kural sayısı
- En etkili kurallar

Varsayılan log dosyası:

```text
data/simulation_logs.csv
```

Bu dosya `.gitignore` içinde tutulduğu için GitHub’a gönderilmez.

Loglama sistemi ileride dashboard grafikleri, test çıktıları ve proje raporu için kullanılabilir.

---

## 13. Test Senaryoları

Doküman:

```text
docs/test_scenarios.md
```

Script:

```text
scripts/run_test_scenarios.py
```

Test senaryoları, fuzzy karar motorunun farklı sera koşullarında nasıl davrandığını görmek için hazırlanmıştır.

Örnek senaryolar:

- Normal sera koşulları
- Toprak kuru, su yeterli
- Toprak kuru, su tankı düşük
- Sıcaklık yüksek
- Sıcaklık ve ışık yüksek
- Hava nemi ve toprak nemi yüksek
- Su tankı kritik düşük
- Kritik bitki stresi
- Işık düşük
- Düşük sıcaklık

Test scriptini çalıştırmak için:

```bash
python scripts/run_test_scenarios.py
```

Test scripti, her senaryo için üretilen aksiyonları sayısal kabul kriterlerine göre otomatik doğrular.

Örnek kabul kriterleri:

- Kuru toprak ve yeterli su tankında sulama seviyesi yüksek olmalıdır.
- Su tankı kritik düşükken alarm seviyesi yüksek olmalıdır.
- Yüksek sıcaklıkta fan seviyesi yüksek olmalıdır.
- Düşük ışıkta gölgeleme kapalı kalmalıdır.

Başarılı çalıştırmada terminal çıktısının sonunda aşağıdaki özet beklenir:

```text
Test özeti: 10/10 senaryo geçti, 0 senaryo kaldı.
```

---

## 14. Veri Akışı Detayı

Sistemin çalışma mantığı adım adım aşağıdaki gibidir:

```text
1. GreenhouseSimulator mevcut sera durumunu tutar.
2. VirtualSensorReader bu durumdan sanal sensör değerleri üretir.
3. FuzzyEngine sensör değerlerini bulanık kümelere dönüştürür.
4. Fuzzy kurallar tetiklenir.
5. ControlActions nesnesi oluşturulur.
6. ExplanationEngine kararların nedenini açıklar.
7. GreenhouseSimulator üretilen aksiyonları uygular.
8. Simülasyon bir sonraki adıma geçer.
9. İsteğe bağlı olarak tüm adım CSV dosyasına kaydedilir.
```

Bu akış, hem terminal demosunda hem de dashboard üzerinde aynı temel mantıkla çalışır.

---

## 15. Mevcut Sistem Sınırları

Bu prototip bilinçli olarak sınırlı tutulmuştur.

Mevcut sınırlılıklar:

- Gerçek sensör kullanılmamaktadır.
- Fiziksel pompa, fan veya gölgeleme sistemi kontrol edilmemektedir.
- Simülasyon modeli gerçek sera fiziğini birebir temsil etmez.
- Bitki türüne özel optimum değerler henüz tanımlanmamıştır.
- Fuzzy kurallar ilk prototip seviyesindedir.
- Planning/search modülü henüz uygulanmamıştır.

Bu sınırlılıklar projenin zayıflığı değil, dönem kapsamının kontrollü tutulması için yapılan bilinçli tercihlerdir.

---

## 16. Güçlü Yönler

Projenin mevcut güçlü yönleri:

- Modüler mimari
- Açıklanabilir karar üretimi
- Fuzzy uzman sistem yaklaşımı
- Simülasyon tabanlı test edilebilir yapı
- Terminal ve dashboard üzerinden çalışabilir prototip
- Gelecekte gerçek donanıma genişletilebilir yapı
- Türkçe dokümantasyon
- Sayısal kabul kriterleriyle otomatik test senaryoları
- Dashboard üzerinde hazır senaryo seçimi
- Test senaryoları ile davranış kontrolü

Bu yönleriyle proje yalnızca basit bir otomasyon demosu değil, karar destek sistemi mantığını gösteren akademik bir prototiptir.

---

## 17. Gelecek Geliştirmeler

İlerleyen aşamalarda sisteme aşağıdaki geliştirmeler eklenebilir:

### Kısa Vadeli Geliştirmeler

- Simülasyon loglarının dashboard’da CSV olarak indirilmesi
- Fuzzy üyelik derecelerinin grafiksel gösterimi
- Kural tabanının iyileştirilmesi
- Basit bir planning/search modülü

### Orta Vadeli Geliştirmeler

- Bitki türüne göre optimum değer profilleri
- Gün/gece döngüsü simülasyonu
- Dış ortam sıcaklığı ve ışık etkisi
- Kaynak tüketimi analizi
- Sulama stratejisi karşılaştırması

### Uzun Vadeli Geliştirmeler

- Gerçek sensör entegrasyonu
- ESP32 veya STM32 tabanlı gömülü sistem
- Fiziksel pompa, fan ve gölgeleme kontrolü
- IoT tabanlı uzaktan izleme
- Mobil uygulama
- Gerçek sera ortamında test

---

## 18. Sonuç

Bu teknik tasarım kapsamında geliştirilen sistem, sera ortamını yazılım içinde simüle eden ve fuzzy uzman sistem yaklaşımıyla açıklanabilir kontrol kararları üreten bir karar destek prototipidir.

Proje; simülasyon, sanal sensör, fuzzy karar motoru, açıklama modülü, loglama sistemi, test senaryoları ve dashboard bileşenlerinden oluşmaktadır.

Mevcut haliyle sistem, ders kapsamında gösterilebilir ve geliştirilebilir bir yapıya sahiptir. Uzun vadede ise gerçek sensörler ve gömülü sistemlerle desteklenerek fiziksel sera ortamına taşınabilecek bir altyapı sunmaktadır.