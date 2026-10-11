# COSA Smart Thermostat - Home Assistant Entegrasyonu

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/v/release/ahamitd/cosa-homeassistant)](https://github.com/ahamitd/cosa-homeassistant/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<p>
  <img src="custom_components/cosa/icon.png" alt="COSA Logo" width="128">
</p>

COSA akıllı termostatınızı Home Assistant üzerinden tam kontrol edin! Bu entegrasyon, COSA mobil uygulamasındaki tüm özellikleri Home Assistant'a taşır.

---

## ✨ Özellikler

### 🌡️ Termostat Kontrolü
- Sıcaklık ayarlama (0.1°C hassasiyet)
- Anlık sıcaklık ve nem gösterimi
- Kombi açık/kapalı durumu

### 🏠 6 Preset Modu
| Mod | İkon | Açıklama |
|-----|------|----------|
| Evde | 🏠 | Ev modu sıcaklığı |
| Uyku | 🛏️ | Gece/uyku modu |
| Dışarı | 🚶 | Dışarıda modu |
| Manuel | ⚙️ | Manuel sıcaklık ayarı |
| Otomatik | 🤖 | Otomatik mod |
| Haftalık | 📅 | Haftalık program |

### 📊 Sensörler (20+ adet)
- Oda sıcaklığı ve nem
- Dış hava sıcaklığı ve nem
- Hava durumu (Türkçe: Güneşli, Bulutlu, Yağmurlu vb.)
- Pil seviyesi ve voltajı
- Sinyal gücü (RSSI)
- Kombi durumu
- Firmware versiyonu
- Ve daha fazlası...

### 🔒 Ek Özellikler
- Açık pencere algılama ve bekleme süresi ayarı
- Kombi çalışma ve durma histerezis toleransları
- Bağlantı durumu izleme
- 15 saniyede bir otomatik güncelleme

---

## 🚀 Servisler (Services)

Entegrasyon, gelişmiş kontroller ve otomasyonlar için aşağıdaki servisleri sunar:

| Servis | Açıklama | Parametreler |
|--------|----------|--------------|
| `cosa.set_turbo` | Süreli ısıtma (Turbo) veya havalandırma modunu başlatır | `duration` (1-180 dk), `temperature` (5-35°C), `mode` (turbo/ventilation) |
| `cosa.set_ventilation` | Belirlenen süre boyunca havalandırma modunu etkinleştirir | `duration` (1-180 dk) |
| `cosa.cancel_timer` | Aktif süreli modu iptal eder ve önceki çalışma moduna döner | - |
| `cosa.set_combi_range` | Kombinin çalışma ve durma histerezis eşiklerini ayarlar | `work_range` (0.0-2.0°C), `stop_range` (0.0-2.0°C) |
| `cosa.set_schedule` | Termostatı haftalık program/takvim moduna geçirir | - |
| `cosa.set_auto` | Termostatı akıllı otomatik moda geçirir | - |

---

## 📦 Kurulum

### Yöntem 1: HACS ile Kurulum (Önerilen)

1. **HACS'ı açın** → Entegrasyonlar sekmesine gidin

2. **Özel depo ekleyin:**
   - Sağ üst köşedeki **⋮** (üç nokta) menüsüne tıklayın
   - **"Özel depolar"** seçin
   - Depo URL'si: `https://github.com/ahamitd/cosa-homeassistant`
   - Kategori: **Entegrasyon** seçin
   - **Ekle** butonuna tıklayın

3. **Entegrasyonu kurun:**
   - HACS'ta **"COSA Smart Thermostat"** arayın
   - **İndir** butonuna tıklayın
   - İndirme tamamlandığında **Home Assistant'ı yeniden başlatın**

4. **Entegrasyonu ekleyin:**
   - **Ayarlar** → **Cihazlar ve Hizmetler** → **+ Entegrasyon Ekle**
   - **"COSA"** arayın ve seçin
   - COSA hesap bilgilerinizi girin

### Yöntem 2: Manuel Kurulum

1. Bu depoyu indirin veya klonlayın:
   ```bash
   git clone https://github.com/ahamitd/cosa-homeassistant.git
   ```

2. `custom_components/cosa` klasörünü Home Assistant'ın `config/custom_components/` dizinine kopyalayın:
   ```
   config/
   └── custom_components/
       └── cosa/
           ├── __init__.py
           ├── api.py
           ├── binary_sensor.py
           ├── climate.py
           ├── config_flow.py
           ├── const.py
           ├── manifest.json
           ├── number.py
           ├── sensor.py
           ├── services.yaml
           ├── strings.json
           ├── switch.py
           └── translations/
               └── tr.json
   ```

3. Home Assistant'ı yeniden başlatın

4. **Ayarlar** → **Cihazlar ve Hizmetler** → **+ Entegrasyon Ekle** → "COSA" arayın

---

## ⚙️ Yapılandırma

### Giriş Bilgileri

Entegrasyonu eklerken COSA mobil uygulamasında kullandığınız bilgileri girin:

| Alan | Açıklama |
|------|----------|
| **E-posta** | COSA hesabınızın e-posta adresi |
| **Şifre** | COSA hesabınızın şifresi |

### Cihaz Seçimi

Hesabınızda birden fazla cihaz varsa, kontrol etmek istediğiniz cihazı seçmeniz istenecektir.

---

## 🎛️ Entity'ler

### Climate (1 adet)
Ana termostat kontrolü - sıcaklık ayarlama, mod değiştirme (Evde, Uyku, Dışarı, Manuel, Otomatik, Haftalık), açma/kapama

### Sayısal Varlıklar / Number (8 adet - Yapılandırma)

| Varlık | Açıklama | Aralık |
|--------|----------|--------|
| Evde Hedef Sıcaklığı | Ev modu hedef sıcaklığı | 15.0 - 28.0 °C |
| Uyku Hedef Sıcaklığı | Uyku modu hedef sıcaklığı | 15.0 - 28.0 °C |
| Dışarı Hedef Sıcaklığı | Dışarı modu hedef sıcaklığı | 5.0 - 25.0 °C |
| Manuel Hedef Sıcaklığı | Manuel mod hedef sıcaklığı | 5.0 - 35.0 °C |
| Kombi Çalışma Toleransı | Hedef sıcaklığın altına inildiğinde kombinin devreye girme eşiği | 0.0 - 2.0 °C |
| Kombi Durma Toleransı | Hedef sıcaklığın üstüne çıkıldığında kombinin devreden çıkma eşiği | 0.0 - 2.0 °C |
| Sıcaklık Kalibrasyonu | Cihaz sıcaklık ölçüm sapma düzeltmesi | -5.0 - +5.0 °C |
| Açık Pencere Süresi | Havalandırma algılandığında bekleme süresi | 15 - 90 dk |

### Switch (1 adet - Yapılandırma)

| Switch | Açıklama |
|--------|----------|
| Açık Pencere Algılama | Açık pencere korumasını aç/kapat |

*(Not: Çocuk kilidi donanım desteğine göre climate varlığının özniteliklerinde takip edilebilir)*

### Binary Sensörler (2 adet)

| Sensör | Açıklama | Kategori |
|--------|----------|----------|
| Isıtma | Kombi şu an aktif ısıtıyor mu? | - |
| Bağlantı | Cihaz bulut servisine bağlı mı? (`connectivity`) | Tanılama (Diagnostic) |

### Sensörler (20+ adet)

| Sensör | Açıklama | Birim | Kategori |
|--------|----------|-------|----------|
| Oda Sıcaklığı | Mevcut oda sıcaklığı | °C | - |
| Nem | Oda nem oranı | % | - |
| Hedef Sıcaklık | Ayarlanan hedef sıcaklık | °C | - |
| Pil Voltajı | Termostat pil voltajı | V | Tanılama |
| Pil Seviyesi | Pil yüzdesi | % | Tanılama |
| Sinyal Gücü | WiFi sinyal gücü | dBm | Tanılama |
| Kombi Durumu | Açık/Kapalı | - | - |
| Mod | Manuel/Otomatik/Haftalık | - | - |
| Seçenek | Evde/Uyku/Dışarı/Manuel | - | - |
| Dış Sıcaklık | Dış hava sıcaklığı | °C | - |
| Dış Nem | Dış hava nemi | % | - |
| Hava Durumu | Güneşli/Bulutlu/Yağmurlu vb. | - | - |
| Firmware | Cihaz yazılım versiyonu | - | Tanılama |

---

## 🔧 Sorun Giderme

### "Bağlantı Kurulamadı" Hatası
- İnternet bağlantınızı kontrol edin
- COSA uygulamasında giriş yapabildiğinizi doğrulayın
- VPN veya firewall ayarlarını kontrol edin

### "Geçersiz Kimlik Doğrulama" Hatası
- E-posta ve şifrenizin doğru olduğundan emin olun
- COSA mobil uygulamasında giriş yapabildiğinizi test edin

### Sıcaklık Güncellenmiyor
- Home Assistant'ı yeniden başlatın
- Entegrasyonu silip yeniden ekleyin
- Log dosyalarını kontrol edin

### Logo/İkon Görünmüyor
- Tarayıcı önbelleğini temizleyin (Ctrl+F5)
- Home Assistant'ı yeniden başlatın

### Güncelleme Aktif Olmadı
- Entegrasyonu **silip yeniden ekleyin**
- Veya Home Assistant'ı tamamen **yeniden başlatın**
- HACS'tan güncelleme yaptıysanız mutlaka restart gerekli

---

### Güncelleme Aralığı
Entegrasyon her **15 saniyede** bir COSA API'sinden veri çeker.

---

## 📄 Lisans

Bu proje MIT Lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

---

## ⚠️ Telif Hakkı ve İletişim

Bu entegrasyon **resmi olmayan** bir topluluk projesidir ve COSA/Nuvia tarafından desteklenmemektedir.

**Telif, ticari kullanım veya sorularınız için:**
- 📧 Telegram: [@ahamitd](https://t.me/ahamitd)
- 🐛 GitHub Issues: [https://github.com/ahamitd/cosa-homeassistant/issues](https://github.com/ahamitd/cosa-homeassistant/issues)

---

## 🤝 Katkıda Bulunma

Katkılarınızı bekliyoruz! Lütfen [CONTRIBUTING.md](CONTRIBUTING.md) dosyasını inceleyin.

---

## 🙏 Teşekkürler

- [Telegram Akıllı Evler Topluluğu](https://t.me/+hvkiQg0YIERiY2Fk)'na
- Home Assistant topluluğuna
- HACS ekibine
- Tüm katkıda bulunanlara

---

* **Geliştirici:** [@ahamitd](https://github.com/ahamitd)
* **Katkıda Bulunan:** [@bselcuk](https://github.com/bselcuk)

⭐ Bu projeyi beğendiyseniz yıldız vermeyi unutmayın!
