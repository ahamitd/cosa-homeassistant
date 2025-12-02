# COSA Smart Thermostat - Home Assistant Entegrasyonu

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/v/release/ahamitd/cosa-homeassistant)](https://github.com/ahamitd/cosa-homeassistant/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<p align="center">
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

### 📊 Sensörler (18 adet)
- Oda sıcaklığı ve nem
- Dış hava sıcaklığı ve nem
- Hava durumu (Türkçe: Güneşli, Bulutlu, Yağmurlu vb.)
- Pil seviyesi ve voltajı
- Sinyal gücü (RSSI)
- Kombi durumu
- Firmware versiyonu
- Ve daha fazlası...

### 🔒 Ek Özellikler
- Çocuk kilidi açma/kapama
- Açık pencere algılama
- Bağlantı durumu izleme
- 10 saniyede bir otomatik güncelleme

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
           ├── sensor.py
           ├── strings.json
           └── switch.py
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
Ana termostat kontrolü - sıcaklık ayarlama, mod değiştirme, açma/kapama

### Sensörler (18 adet)

| Sensör | Açıklama | Birim |
|--------|----------|-------|
| Oda Sıcaklığı | Mevcut oda sıcaklığı | °C |
| Nem | Oda nem oranı | % |
| Hedef Sıcaklık | Ayarlanan hedef sıcaklık | °C |
| Pil Voltajı | Termostat pil voltajı | V |
| Pil Seviyesi | Pil yüzdesi | % |
| Sinyal Gücü | WiFi sinyal gücü | dBm |
| Kombi Durumu | Açık/Kapalı | - |
| Mod | Manuel/Otomatik/Haftalık | - |
| Seçenek | Evde/Uyku/Dışarı/Manuel | - |
| Dış Sıcaklık | Hava durumu sıcaklığı | °C |
| Dış Nem | Hava durumu nemi | % |
| Hava Durumu | Güneşli/Bulutlu/Yağmurlu vb. | - |
| Evde Sıcaklığı | Ev modu hedef sıcaklığı | °C |
| Dışarı Sıcaklığı | Dışarı modu hedef sıcaklığı | °C |
| Uyku Sıcaklığı | Uyku modu hedef sıcaklığı | °C |
| Manuel Sıcaklık | Manuel mod hedef sıcaklığı | °C |
| Firmware | Cihaz yazılım versiyonu | - |
| Kalibrasyon | Sıcaklık kalibrasyonu | °C |

### Binary Sensörler (4 adet)

| Sensör | Açıklama |
|--------|----------|
| Bağlantı | Cihaz çevrimiçi mi? |
| Isıtma | Kombi şu an ısıtıyor mu? |
| Açık Pencere | Pencere açık algılandı mı? |
| Çocuk Kilidi | Kilit aktif mi? |

### Switch (1 adet)

| Switch | Açıklama |
|--------|----------|
| Çocuk Kilidi | Çocuk kilidini aç/kapat |

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
Entegrasyon her **10 saniyede** bir COSA API'sinden veri çeker.

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

**Geliştirici:** [@ahamitd](https://github.com/ahamitd)

⭐ Bu projeyi beğendiyseniz yıldız vermeyi unutmayın!