# COSA Home Assistant Entegrasyonu - Kurulum Kılavuzu

## 🏠 Genel Bakış

COSA Smart Thermostat entegrasyonu, COSA termostatınızı Home Assistant üzerinden kontrol etmenizi sağlar.

### Özellikler

- 🌡️ **Termostat Kontrolü:** Sıcaklık ayarlama, mod değiştirme
- 📊 **18 Sensör:** Sıcaklık, nem, pil durumu, dış hava ve daha fazlası
- 🔒 **Çocuk Kilidi:** Açma/kapama kontrolü
- 🏠 **6 Preset Modu:** Evde, Uyku, Dışarı, Manuel, Otomatik, Haftalık
- 🔥 **Anlık Durum:** Kombi ısıtma durumu gösterimi
- 🌤️ **Hava Durumu:** Dış sıcaklık ve nem bilgisi

## 📋 Gereksinimler

- Home Assistant 2024.1 veya üzeri
- COSA mobil uygulamasında aktif hesap
- İnternet bağlantısı

## �� Kurulum

### Yöntem 1: HACS ile Kurulum (Önerilen)

1. HACS > Entegrasyonlar'a gidin
2. Sağ üst köşedeki **⋮** menüsüne tıklayın
3. **Özel depolar** seçin
4. Depo URL'si: `https://github.com/ahamitd/cosa-homeassistant`
5. Kategori: **Entegrasyon** seçin
6. **Ekle** butonuna tıklayın
7. COSA Smart Thermostat'ı bulun ve kurun
8. Home Assistant'ı yeniden başlatın

### Yöntem 2: Manuel Kurulum

1. Bu depoyu indirin veya klonlayın
2. `custom_components/cosa` klasörünü Home Assistant'ın `config/custom_components/` klasörüne kopyalayın
3. Home Assistant'ı yeniden başlatın

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
        ├── switch.py
        └── icons/
            └── icon.png
```

## ⚙️ Entegrasyonu Ekleme

1. **Ayarlar** > **Cihazlar ve Hizmetler**'e gidin
2. **+ Entegrasyon Ekle** butonuna tıklayın
3. **"COSA"** yazarak arayın
4. **COSA Smart Thermostat** seçin
5. COSA hesap bilgilerinizi girin:
   - **E-posta:** COSA uygulamasındaki e-posta adresiniz
   - **Şifre:** COSA uygulamasındaki şifreniz
6. Cihazınızı seçin (birden fazla varsa)

## 🎛️ Kullanım

### Termostat Kartı

Entegrasyon kurulduktan sonra termostat kartında şunları göreceksiniz:

| Özellik | Açıklama |
|---------|----------|
| 🌡️ Mevcut Sıcaklık | Oda sıcaklığı |
| 💧 Nem | Oda nem oranı |
| 🎯 Hedef Sıcaklık | Ayarlanan sıcaklık (0.1°C hassasiyet) |
| 🔥 Isıtma Durumu | Kombi aktif/pasif |

### Preset Modları

| Mod | İkon | Açıklama |
|-----|------|----------|
| 🏠 Evde | `mdi:home` | Ev modu |
| 🛏️ Uyku | `mdi:bed` | Gece/uyku modu |
| 🚶 Dışarı | `mdi:walk` | Dışarıda modu |
| ⚙️ Manuel | `mdi:tune` | Manuel ayar |
| 🤖 Otomatik | `mdi:thermostat-auto` | Otomatik mod |
| 📅 Haftalık | `mdi:calendar-clock` | Haftalık program |

### Entity'ler

#### Climate (1 adet)
- `climate.evim` - Ana termostat kontrolü

#### Sensörler (18 adet)
| Entity | Açıklama |
|--------|----------|
| Oda Sıcaklığı | Mevcut oda sıcaklığı |
| Nem | Oda nem oranı |
| Hedef Sıcaklık | Ayarlanan hedef |
| Pil Voltajı | Termostat pil voltajı |
| Pil Seviyesi | Pil yüzdesi |
| Sinyal Gücü | WiFi sinyal gücü |
| Kombi Durumu | Açık/Kapalı |
| Mod | Aktif mod |
| Seçenek | Aktif preset |
| Dış Sıcaklık | Hava durumu sıcaklığı |
| Dış Nem | Hava durumu nemi |
| Hava Durumu | Hava durumu ikonu |
| Evde Sıcaklığı | Ev modu sıcaklığı |
| Dışarıda Sıcaklığı | Dışarı modu sıcaklığı |
| Uyku Sıcaklığı | Uyku modu sıcaklığı |
| Özel Sıcaklık | Manuel mod sıcaklığı |
| Firmware | Cihaz yazılım versiyonu |
| Kalibrasyon | Sıcaklık kalibrasyonu |

#### Binary Sensörler (4 adet)
| Entity | Açıklama |
|--------|----------|
| Bağlantı | Cihaz bağlantı durumu |
| Isıtma | Kombi aktif mi? |
| Açık Pencere | Pencere açık algılama |
| Çocuk Kilidi Durumu | Kilit durumu |

#### Switch (1 adet)
| Entity | Açıklama |
|--------|----------|
| Çocuk Kilidi | Çocuk kilidini aç/kapat |

## 🔧 Sorun Giderme

### "Bağlantı Kurulamadı" Hatası

- İnternet bağlantınızı kontrol edin
- COSA API'sinin erişilebilir olduğunu doğrulayın
- Firewall/VPN ayarlarını kontrol edin

### "Geçersiz Kimlik Doğrulama" Hatası

- E-posta ve şifrenizin doğru olduğundan emin olun
- COSA mobil uygulamasında giriş yapabildiğinizi test edin
- Şifrenizde özel karakter varsa dikkatli girin

### Sıcaklık Değişikliği Gecikmesi

- Entegrasyon her 10 saniyede bir güncellenir
- API isteği sırasında kısa gecikme normaldir

### Ikon Görünmüyor

- Home Assistant'ı yeniden başlatın
- Tarayıcı önbelleğini temizleyin (Ctrl+F5)

## 📡 API Bilgisi

Entegrasyon aşağıdaki COSA API endpoint'lerini kullanır:

| Endpoint | Açıklama |
|----------|----------|
| `/api/users/login` | Kullanıcı girişi |
| `/api/endpoints/getEndpoints` | Cihaz listesi |
| `/api/endpoints/getEndpoint` | Cihaz detayları |
| `/api/endpoints/setMode` | Mod değiştirme |
| `/api/endpoints/setTargetTemperatures` | Sıcaklık ayarlama |
| `/api/endpoints/setCombiSettings` | Kombi ayarları |
| `/api/places/getForecast` | Hava durumu |

## 📄 Lisans

MIT License - Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## 💬 Destek

- GitHub Issues: [https://github.com/ahamitd/cosa-homeassistant/issues](https://github.com/ahamitd/cosa-homeassistant/issues)
- Telegram: [@ahamitd](https://t.me/ahamitd)

---

**Geliştirici:** [@ahamitd](https://github.com/ahamitd)
