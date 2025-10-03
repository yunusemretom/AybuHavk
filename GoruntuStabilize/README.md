# 🎥 Görüntü Stabilizasyon Projesi

Bu klasör, video görüntülerindeki titreme ve sarsıntıları düzeltmek için geliştirilmiş görüntü stabilizasyon algoritmalarını içerir. Proje, hem basit hem de gelişmiş stabilizasyon tekniklerini kullanarak farklı yaklaşımlar sunar.

## 📁 Dosya Yapısı

```
GoruntuStabilize/
├── 📄 README.md                    # Bu dosya
├── 🎬 deneme.mp4                   # Test videosu
├── 🐍 video_stabilization.py       # Ana stabilizasyon kodu
└── 🧪 deneme.py                    # Gelişmiş stabilizasyon denemesi
```

## 🚀 Özellikler

### 📹 `video_stabilization.py` - Ana Stabilizasyon Kodu
- ✅ **Optik Akış Tabanlı Stabilizasyon**: Lucas-Kanade algoritması kullanır
- ✅ **Özellik Noktası Tespiti**: Harris köşe tespiti ile güvenilir noktalar
- ✅ **Affine Transformasyon**: Dönüş, öteleme ve ölçekleme düzeltmeleri
- ✅ **Yumuşatma Filtresi**: Hareketli ortalama ile titreşim azaltma
- ✅ **Kenar Düzeltme**: Sınır artefaktlarını giderme
- ✅ **Yan Yana Karşılaştırma**: Orijinal ve stabilize edilmiş görüntü

### 🧪 `deneme.py` - Gelişmiş Stabilizasyon Denemesi
- 🔬 **Kalman Filtresi**: Gelişmiş hareket tahmini ve düzeltme
- 🎛️ **Gerçek Zamanlı Kontrol**: Stabilizasyonu açma/kapama
- 📊 **Performans İzleme**: FPS ve hareket büyüklüğü takibi
- 🎮 **İnteraktif Kontroller**: Klavye ile parametre ayarlama
- 📈 **İstatistiksel Analiz**: Hareket geçmişi ve performans metrikleri

## 🛠️ Kurulum ve Gereksinimler

### Gerekli Kütüphaneler
```bash
pip install opencv-python numpy
```

### Sistem Gereksinimleri
- 🐍 Python 3.6+
- 📹 OpenCV 4.0+
- 🔢 NumPy
- 🖥️ Webcam (opsiyonel)

## 🎯 Kullanım

### 1. Basit Video Stabilizasyonu
```bash
python video_stabilization.py
```

**Özellikler:**
- 📁 Sabit video dosyası yolu (`deneme.mp4`)
- 🎬 Otomatik işleme ve çıktı oluşturma
- 📊 İşlem ilerlemesi gösterimi
- 💾 `video_out.mp4` olarak kaydetme

### 2. Gelişmiş Stabilizasyon Sistemi
```bash
python deneme.py
```

**Kontroller:**
- `[SPACE]` - Stabilizasyonu aç/kapat
- `[R]` - Stabilizatörü sıfırla
- `[+/-]` - Yumuşatma faktörünü ayarla
- `[Q/ESC]` - Çıkış

## ⚙️ Parametreler

### `video_stabilization.py`
```python
SMOOTHING_RADIUS = 50  # Yumuşatma yarıçapı (daha büyük = daha stabil)
```

### `deneme.py`
```python
smoothing_factor = 0.8        # Yumuşatma faktörü (0.0-1.0)
process_noise = 0.01          # Kalman süreç gürültüsü
measurement_noise = 0.1       # Kalman ölçüm gürültüsü
maxCorners = 200              # Maksimum özellik noktası sayısı
qualityLevel = 0.01           # Özellik kalite seviyesi
```

## 🔧 Algoritma Detayları

### 1. Özellik Tespiti
- **Harris Köşe Tespiti**: Güvenilir özellik noktaları bulma
- **Kalite Filtreleme**: Düşük kaliteli noktaları eleme
- **Mesafe Kontrolü**: Yakın noktaları temizleme

### 2. Optik Akış
- **Lucas-Kanade**: Pyramidal optik akış hesaplama
- **Durum Filtreleme**: Başarısız takipleri eleme
- **Hata Analizi**: Güvenilir eşleşmeleri seçme

### 3. Transformasyon
- **Affine Matris**: Dönüş, öteleme ve ölçekleme
- **RANSAC**: Aykırı değerleri temizleme
- **Kümülatif Hesaplama**: Toplam hareket birikimi

### 4. Yumuşatma
- **Hareketli Ortalama**: Basit filtreleme
- **Kalman Filtresi**: Gelişmiş tahmin ve düzeltme
- **Adaptif Parametreler**: Dinamik ayarlama

## 📊 Performans Metrikleri

### İzlenen Parametreler
- 🎯 **FPS**: İşleme hızı
- 📏 **Hareket Büyüklüğü**: Piksel cinsinden hareket
- 🎛️ **Stabilizasyon Etkinliği**: Düzeltme oranı
- 📈 **Özellik Noktası Sayısı**: Tespit edilen noktalar

### Optimizasyon İpuçları
- 🔧 Düşük çözünürlük = Yüksek FPS
- 🎯 Daha az özellik noktası = Daha hızlı işleme
- ⚖️ Yumuşatma faktörü = Stabilite vs. Responsivite dengesi

## 🐛 Bilinen Sorunlar

### `deneme.py` Durumu
> ⚠️ **Not**: `deneme.py` dosyası şu anda düzgün çalışmıyor. Geliştirme aşamasında.

### Yaygın Sorunlar
- 📹 **Kamera Erişimi**: Webcam indeksi değişebilir
- 💾 **Bellek Kullanımı**: Uzun videolar için yüksek RAM
- 🎬 **Format Uyumluluğu**: Bazı video codec'leri desteklenmeyebilir

## 🔮 Gelecek Geliştirmeler

- [ ] 🧠 **Makine Öğrenmesi**: Derin öğrenme tabanlı stabilizasyon
- [ ] 🌐 **Web Arayüzü**: Tarayıcı tabanlı kullanım
- [ ] 📱 **Mobil Optimizasyon**: Android/iOS desteği
- [ ] 🎨 **Gelişmiş Filtreler**: Daha sofistike yumuşatma algoritmaları
- [ ] 📊 **Detaylı Analiz**: Hareket analizi ve raporlama

## 🤝 Katkıda Bulunma

1. 🍴 Fork yapın
2. 🌿 Yeni branch oluşturun (`git checkout -b feature/amazing-feature`)
3. 💾 Değişikliklerinizi commit edin (`git commit -m 'Add amazing feature'`)
4. 📤 Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. 🔄 Pull Request oluşturun

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakın.


---

*🎥 Daha stabil videolar için geliştirilmiştir!*
