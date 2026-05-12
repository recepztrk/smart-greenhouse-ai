# Test Senaryoları

Bu doküman, **Akıllı Sera Yönetim ve Karar Destek Sistemi** için hazırlanan temel test senaryolarını açıklar.

Amaç, fuzzy karar motorunun farklı sera koşullarında beklenen davranışı üretip üretmediğini kontrol etmektir. Testler yalnızca gözlem amaçlı değildir; `scripts/run_test_scenarios.py` dosyası her senaryo için sayısal kabul kriterleri uygular ve senaryonun geçip geçmediğini terminalde gösterir.

---

## Kullanılan Giriş Değişkenleri

- Sıcaklık
- Hava nemi
- Toprak nemi
- Işık seviyesi
- Su tankı seviyesi

## Üretilen Kontrol Çıktıları

- Sulama seviyesi
- Havalandırma / fan seviyesi
- Gölgeleme seviyesi
- Alarm seviyesi

Tüm kontrol çıktıları 0-100 aralığında değerlendirilir.

---

## Senaryo Özeti ve Kabul Kriterleri

| No | Senaryo | Beklenen Ana Davranış | Sayısal Kabul Kriteri |
|---:|---|---|---|
| 1 | Normal sera koşulları | Gereksiz müdahale yapılmamalı | Sulama ≤ 10, fan ≤ 15, gölgeleme ≤ 20, alarm ≤ 10 |
| 2 | Toprak kuru, su yeterli | Sulama yüksek olmalı | Sulama ≥ 70, alarm ≤ 20 |
| 3 | Toprak kuru, su tankı düşük | Sulama sınırlanmalı, alarm yükselmeli | Sulama ≤ 40, alarm ≥ 80 |
| 4 | Sıcaklık yüksek | Fan yüksek çalışmalı | Fan ≥ 60 |
| 5 | Sıcaklık ve ışık yüksek | Fan ve gölgeleme yüksek olmalı | Fan ≥ 60, gölgeleme ≥ 70 |
| 6 | Hava nemi ve toprak nemi yüksek | Sulama kapalı, hastalık riski uyarısı | Sulama ≤ 10, alarm ≥ 50 |
| 7 | Su tankı kritik düşük | Alarm yüksek olmalı | Alarm ≥ 80 |
| 8 | Kritik bitki stresi | Alarm kritik, fan/gölgeleme yüksek, sulama sınırlı | Alarm ≥ 90, fan ≥ 60, gölgeleme ≥ 70, sulama ≤ 40 |
| 9 | Işık düşük | Gölgeleme kapalı olmalı | Gölgeleme ≤ 10, alarm ≤ 10 |
| 10 | Düşük sıcaklık | Fan kapalı olmalı | Fan ≤ 10, alarm ≤ 20 |

---

## Senaryo 1: Normal Sera Koşulları

### Giriş Değerleri

| Değişken | Değer |
|---|---:|
| Sıcaklık | 25 °C |
| Hava nemi | %55 |
| Toprak nemi | %55 |
| Işık seviyesi | %55 |
| Su tankı seviyesi | %80 |

### Beklenen Davranış

Sera ortamı dengeli olduğu için sistem gereksiz müdahale üretmemelidir. Sulama, fan ve alarm düşük/kapalı kalmalı; gölgeleme en fazla düşük seviyede olmalıdır.

---

## Senaryo 2: Toprak Kuru, Su Yeterli

### Giriş Değerleri

| Değişken | Değer |
|---|---:|
| Sıcaklık | 28 °C |
| Hava nemi | %50 |
| Toprak nemi | %20 |
| Işık seviyesi | %60 |
| Su tankı seviyesi | %80 |

### Beklenen Davranış

Toprak nemi düşük olduğu için sistem belirgin sulama kararı üretmelidir. Su tankı yeterli olduğundan alarm düşük veya kapalı kalmalıdır.

---

## Senaryo 3: Toprak Kuru, Su Tankı Düşük

### Giriş Değerleri

| Değişken | Değer |
|---|---:|
| Sıcaklık | 30 °C |
| Hava nemi | %45 |
| Toprak nemi | %18 |
| Işık seviyesi | %65 |
| Su tankı seviyesi | %15 |

### Beklenen Davranış

Toprak kuru olduğu için sulama ihtiyacı vardır. Ancak su tankı düşük olduğu için sulama sınırsız yapılmamalı; sistem alarm üretmelidir.

---

## Senaryo 4: Sıcaklık Yüksek

### Giriş Değerleri

| Değişken | Değer |
|---|---:|
| Sıcaklık | 37 °C |
| Hava nemi | %50 |
| Toprak nemi | %50 |
| Işık seviyesi | %65 |
| Su tankı seviyesi | %75 |

### Beklenen Davranış

Bu senaryo sıcaklık stresini temsil eder. Sistem fan/havalandırma kararını belirgin şekilde artırmalıdır.

---

## Senaryo 5: Sıcaklık ve Işık Yüksek

### Giriş Değerleri

| Değişken | Değer |
|---|---:|
| Sıcaklık | 36 °C |
| Hava nemi | %40 |
| Toprak nemi | %45 |
| Işık seviyesi | %90 |
| Su tankı seviyesi | %70 |

### Beklenen Davranış

Yüksek sıcaklık ve yüksek ışık birlikte ısı/ışık stresi oluşturur. Sistem hem fan hem gölgeleme aksiyonunu yüksek seviyeye çıkarmalıdır.

---

## Senaryo 6: Hava Nemi ve Toprak Nemi Yüksek

### Giriş Değerleri

| Değişken | Değer |
|---|---:|
| Sıcaklık | 24 °C |
| Hava nemi | %85 |
| Toprak nemi | %82 |
| Işık seviyesi | %50 |
| Su tankı seviyesi | %75 |

### Beklenen Davranış

Toprak zaten ıslak olduğu için sulama kapalı kalmalıdır. Hava nemi ve toprak nemi birlikte yüksek olduğundan hastalık riski alarmı üretilebilir.

---

## Senaryo 7: Su Tankı Kritik Düşük

### Giriş Değerleri

| Değişken | Değer |
|---|---:|
| Sıcaklık | 26 °C |
| Hava nemi | %50 |
| Toprak nemi | %50 |
| Işık seviyesi | %55 |
| Su tankı seviyesi | %10 |

### Beklenen Davranış

Bu senaryo sistemin kaynak farkındalığını test eder. Su tankı kritik seviyede olduğu için alarm yüksek olmalıdır.

---

## Senaryo 8: Kritik Bitki Stresi

### Giriş Değerleri

| Değişken | Değer |
|---|---:|
| Sıcaklık | 38 °C |
| Hava nemi | %25 |
| Toprak nemi | %15 |
| Işık seviyesi | %88 |
| Su tankı seviyesi | %20 |

### Beklenen Davranış

Birden fazla risk aynı anda vardır: yüksek sıcaklık, düşük hava nemi, kuru toprak, yüksek ışık ve düşük su tankı. Alarm kritik olmalı; fan ve gölgeleme yüksek çalışmalı; sulama ise su tankı nedeniyle sınırlanmalıdır.

---

## Senaryo 9: Işık Düşük

### Giriş Değerleri

| Değişken | Değer |
|---|---:|
| Sıcaklık | 22 °C |
| Hava nemi | %60 |
| Toprak nemi | %50 |
| Işık seviyesi | %20 |
| Su tankı seviyesi | %80 |

### Beklenen Davranış

Işık düşük olduğu için gölgeleme yapılmamalıdır. Bu koşul tek başına alarm üretmemelidir.

---

## Senaryo 10: Düşük Sıcaklık

### Giriş Değerleri

| Değişken | Değer |
|---|---:|
| Sıcaklık | 14 °C |
| Hava nemi | %55 |
| Toprak nemi | %55 |
| Işık seviyesi | %45 |
| Su tankı seviyesi | %80 |

### Beklenen Davranış

Sıcaklık düşükken fan çalıştırmak sera koşullarını daha da kötüleştirebilir. Bu nedenle havalandırma kapalı tutulmalıdır.

---

## Otomatik Test Komutu

Test senaryolarını çalıştırmak için:

```bash
python scripts/run_test_scenarios.py
```

Başarılı bir çalıştırmada terminal çıktısının sonunda aşağıdaki gibi bir özet görülmelidir:

```text
Test özeti: 10/10 senaryo geçti, 0 senaryo kaldı.
```
