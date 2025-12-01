# COSA Smart Thermostat - Home Assistant Entegrasyonu

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/v/release/ahamitd/cosa-homeassistant)](https://github.com/ahamitd/cosa-homeassistant/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<p align="center">
  <img src="custom_components/cosa/icon.png" alt="COSA Logo" width="128">
</p>

COSA akıllı termostatınızı Home Assistant üzerinden kontrol edin!

## ✨ Özellikler

- 🌡️ **Termostat Kontrolü** - Sıcaklık ayarlama (0.1°C hassasiyet)
- 🏠 **6 Preset Modu** - Evde, Uyku, Dışarı, Manuel, Otomatik, Haftalık
- 📊 **18 Sensör** - Sıcaklık, nem, pil, sinyal gücü ve daha fazlası
- 🔥 **Anlık Durum** - Kombi ısıtma durumu gösterimi
- 🌤️ **Hava Durumu** - Dış sıcaklık ve nem bilgisi
- 🔒 **Çocuk Kilidi** - Uzaktan kontrol
- ⚡ **Hızlı Güncelleme** - 10 saniyede bir senkronizasyon

## 📦 Kurulum

### HACS ile Kurulum (Önerilen)

1. HACS > Entegrasyonlar > ⋮ > Özel depolar
2. URL: `https://github.com/ahamitd/cosa-homeassistant`
3. Kategori: Entegrasyon
4. COSA Smart Thermostat'ı kurun
5. Home Assistant'ı yeniden başlatın

### Manuel Kurulum

`custom_components/cosa` klasörünü Home Assistant `config/custom_components/` dizinine kopyalayın.

## ⚙️ Yapılandırma

1. **Ayarlar** > **Cihazlar ve Hizmetler** > **+ Entegrasyon Ekle**
2. "COSA" arayın
3. COSA hesap bilgilerinizi girin

## 🎛️ Entity'ler

| Tip | Adet | Örnekler |
|-----|------|----------|
| Climate | 1 | Termostat kontrolü |
| Sensor | 18 | Sıcaklık, nem, pil, hava durumu |
| Binary Sensor | 4 | Bağlantı, ısıtma, pencere, kilit |
| Switch | 1 | Çocuk kilidi |

## 🔥 Preset Modları

| Mod | İkon | Açıklama |
|-----|------|----------|
| Evde | 🏠 | Ev modu |
| Uyku | 🛏️ | Gece modu |
| Dışarı | 🚶 | Dışarıda modu |
| Manuel | ⚙️ | Manuel ayar |
| Otomatik | 🤖 | Otomatik mod |
| Haftalık | 📅 | Haftalık program |

## 📸 Ekran Görüntüleri

<p align="center">
  <img src="docs/screenshot1.png" alt="Termostat Kartı" width="300">
</p>

## 📄 Lisans

MIT License - [LICENSE](LICENSE)

## 💬 Destek

- [GitHub Issues](https://github.com/ahamitd/cosa-homeassistant/issues)
- Telegram: [@ahamitd](https://t.me/ahamitd)

---

**Geliştirici:** [@ahamitd](https://github.com/ahamitd)
