# Test Senaryoları

Bu dosya, Akıllı Sera Yönetim ve Karar Destek Sistemi için temel test senaryolarını içerir.

Amaç, fuzzy karar motorunun farklı sera koşullarında beklenen davranışı üretip üretmediğini kontrol etmektir.

Sistem aşağıdaki giriş değişkenlerini kullanır:

- Sıcaklık
- Hava nemi
- Toprak nemi
- Işık seviyesi
- Su tankı seviyesi

Sistem aşağıdaki kontrol kararlarını üretir:

- Sulama seviyesi
- Havalandırma seviyesi
- Gölgeleme seviyesi
- Alarm seviyesi

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

- Sulama kapalı veya çok düşük seviyede olmalıdır.
- Havalandırma kapalı veya düşük seviyede olmalıdır.
- Gölgeleme düşük seviyede olmalıdır.
- Alarm üretilmemelidir.

### Yorum

Bu senaryo sera ortamının dengeli olduğu durumu temsil eder. Sistem gereksiz müdahale üretmemelidir.

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

- Sulama yüksek seviyede olmalıdır.
- Havalandırma düşük veya orta seviyede olabilir.
- Gölgeleme düşük seviyede olabilir.
- Alarm üretilmemelidir veya düşük seviyede kalmalıdır.

### Yorum

Toprak nemi düşük olduğu için sistem sulama kararı üretmelidir. Su tankı yeterli olduğu için sulama kısıtlanmamalıdır.

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

- Sulama tamamen yüksek olmamalı, sınırlı tutulmalıdır.
- Alarm yüksek veya kritik seviyede olmalıdır.
- Sistem açıklamasında su tankı seviyesinin düşük olduğu belirtilmelidir.

### Yorum

Toprak kuru olduğu için sulama ihtiyacı vardır. Ancak su tankı düşük olduğu için sistem sınırsız sulama yapmamalı ve kullanıcıyı uyarmalıdır.

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

- Havalandırma yüksek seviyede olmalıdır.
- Sulama toprak nemine bağlı olarak düşük veya kapalı olabilir.
- Gölgeleme ışık seviyesine bağlı olarak düşük veya orta seviyede olabilir.
- Alarm düşük veya orta seviyede olabilir.

### Yorum

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

- Havalandırma yüksek seviyede olmalıdır.
- Gölgeleme yüksek seviyede olmalıdır.
- Alarm orta seviyede olabilir.
- Açıklamada yüksek sıcaklık ve yüksek ışık seviyesi vurgulanmalıdır.

### Yorum

Bu senaryoda bitki üzerinde ısı ve ışık stresi oluşabilir. Sistem hem fan hem gölgeleme aksiyonu üretmelidir.

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

- Sulama kapalı olmalıdır.
- Havalandırma orta seviyede olabilir.
- Alarm düşük veya orta seviyede olabilir.
- Açıklamada yüksek nem nedeniyle hastalık riski belirtilebilir.

### Yorum

Toprak ve hava nemi birlikte yüksek olduğunda bazı bitkiler için hastalık riski artabilir. Sistem sulamayı kapatmalı ve gerektiğinde uyarı üretmelidir.

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

- Alarm yüksek seviyede olmalıdır.
- Sulama gerekiyorsa bile sınırlı tutulmalıdır.
- Açıklamada su tankı seviyesinin kritik olduğu belirtilmelidir.

### Yorum

Bu senaryo sistemin kaynak farkındalığını test eder. Sistem yalnızca bitki ihtiyacına göre değil, mevcut su kaynağına göre de karar vermelidir.

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

- Alarm kritik seviyede olmalıdır.
- Havalandırma yüksek seviyede olmalıdır.
- Gölgeleme yüksek seviyede olmalıdır.
- Sulama ihtiyacı vardır ancak su tankı düşük olduğu için sulama sınırlanabilir.
- Açıklamada sıcaklık, toprak kuruluğu, düşük hava nemi ve düşük su tankı birlikte değerlendirilmelidir.

### Yorum

Bu senaryo sistemin en zor durumlarından biridir. Birden fazla risk aynı anda vardır. Sistem sadece tek değişkene göre karar vermemeli, bütün koşulları birlikte yorumlamalıdır.

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

- Gölgeleme kapalı olmalıdır.
- Havalandırma kapalı veya düşük seviyede olmalıdır.
- Sulama toprak nemine bağlı olarak kapalı veya düşük seviyede olabilir.
- Alarm üretilmemelidir.

### Yorum

Işık düşük olduğu için gölgeleme yapılmamalıdır. Bu senaryo gölgeleme kararının ters durumunu test eder.

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

- Havalandırma kapalı olmalıdır.
- Gölgeleme kapalı veya çok düşük seviyede olmalıdır.
- Sulama toprak nemine göre kapalı veya düşük seviyede olabilir.
- Alarm üretilmeyebilir.

### Yorum

Sıcaklık düşükken fan çalıştırmak sera koşullarını daha da kötüleştirebilir. Sistem bu durumda fanı kapalı tutmalıdır.

---

## Test Mantığı

Bu senaryolar, sistemin aşağıdaki özelliklerini kontrol etmek için kullanılacaktır:

- Kuru toprakta sulama kararı üretme
- Su azlığında sulamayı sınırlama
- Yüksek sıcaklıkta havalandırma üretme
- Yüksek ışıkta gölgeleme üretme
- Kritik durumlarda alarm üretme
- Normal koşullarda gereksiz müdahaleden kaçınma
- Karar açıklama modülünün doğru gerekçeleri üretmesi

---

## Manuel Test Komutu

Belirli senaryolar şu anda doğrudan terminal demosu üzerinden otomatik seçilememektedir.

Ancak sistem genel davranışı aşağıdaki komutla gözlemlenebilir:

```bash
python app.py --steps 5 --no-noise