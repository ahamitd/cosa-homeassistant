# COSA Home Assistant Entegrasyonu

![COSA logo](custom_components/cosa/icon.png)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

COSA termostatınızı Home Assistant'a entegre edin ve akıllı ev sisteminizin bir parçası haline getirin.

## 🎯 Özellikler

- ✅ **Termostat Kontrolü**: Kombiyi açıp kapatabilirsiniz
- ✅ **Sıcaklık Ayarı**: 5-32°C arası hassas sıcaklık kontrolü
- ✅ **Preset Modları**: Ev, Dışarıda, Gece ve Özel modlar
- ✅ **Sensör Desteği**: Oda sıcaklığı ve nem sensörleri
- ✅ **Otomatik Güncelleme**: Her 60 saniyede bir otomatik veri güncelleme
- ✅ **Config Flow**: Kolay kurulum arayüzü
- ✅ **Türkçe Dil Desteği**: Tam Türkçe arayüz

## 📋 Gereksinimler

- Home Assistant 2023.1 veya üzeri
- Python 3.9 veya üzeri
- COSA uygulamasında aktif hesap
- İnternet bağlantısı

## 🚀 HACS ile Kurulum (Önerilen)

1. HACS'ı açın (Eğer yüklü değilse, [buradan](https://hacs.xyz/) yükleyin)
2. "Entegrasyonlar" sekmesine gidin
3. Sağ üstteki **⋮** menüsünden **"Özel Depolar"**ı seçin
4. Depo URL'sini ekleyin: `https://github.com/ahamitd/cosa-homeassistant`
5. Kategori olarak **"Integration"** seçin
6. **"COSA Termostat"** entegrasyonunu arayın ve yükleyin
7. Home Assistant'ı yeniden başlatın
8. Ayarlar > Cihazlar ve Hizmetler > Entegrasyon Ekle
9. **"COSA Termostat"** entegrasyonunu arayın ve ekleyin
10. COSA uygulamasındaki kullanıcı adı ve şifrenizi girin

## 📦 Manuel Kurulum

1. Home Assistant'ın `config` klasörüne `custom_components` klasörünü oluşturun (eğer yoksa)
2. Bu repository'yi klonlayın veya indirin:
   ```bash
   git clone https://github.com/ahamitd/cosa-homeassistant.git
   ```
3. `cosa` klasörünü `config/custom_components/` klasörüne kopyalayın:
   ```
   config/
   └── custom_components/
       └── cosa/
           ├── __init__.py
           ├── manifest.json
           ├── config_flow.py
           ├── climate.py
           ├── api.py
           ├── const.py
           └── strings.json
   ```
4. Home Assistant'ı yeniden başlatın
5. Ayarlar > Cihazlar ve Hizmetler > Entegrasyon Ekle
6. **"COSA Termostat"** entegrasyonunu arayın ve ekleyin
7. COSA uygulamasındaki kullanıcı adı ve şifrenizi girin
8. Endpoint ID'yi girebilirsiniz (opsiyonel - otomatik tespit edilebilir)

## 📖 Kullanım

### Termostat Kontrolü

- **Açık/Kapalı**: HVAC modunu değiştirerek kombiyi açıp kapatabilirsiniz
- **Sıcaklık Ayarı**: Hedef sıcaklığı ayarlayabilirsiniz (5-32°C arası)
- **Preset Modları**: 
  - **Ev (Home)**: Ev modu
  - **Dışarıda (Away)**: Dışarıda modu
  - **Gece (Sleep)**: Gece modu
  - **Kullanıcı (Custom)**: Özel mod

### Sensörler

Entegrasyon aşağıdaki bilgileri sağlar:

- **Mevcut Sıcaklık**: Oda sıcaklığı
- **Hedef Sıcaklık**: Ayarlanan hedef sıcaklık
- **Nem**: Oda nem oranı
- **Durum**: Kombi çalışma durumu (Açık/Kapalı)
- **Mod**: Aktif preset modu

## 🔧 Sorun Giderme

### Bağlantı Hatası

- İnternet bağlantınızı kontrol edin
- COSA API'sinin erişilebilir olduğundan emin olun (`https://kiwi-api.nuvia.com.tr`)
- Firewall ayarlarınızı kontrol edin

### Kimlik Doğrulama Hatası

- Kullanıcı adı ve şifrenizin doğru olduğundan emin olun
- COSA uygulamasında giriş yapabildiğinizi kontrol edin
- Şifrenizde özel karakterler varsa dikkatli girin

### Endpoint ID Bulunamadı

- Endpoint ID'yi manuel olarak girebilirsiniz
- COSA uygulamasından cihaz bilgilerinizi kontrol edin
- API response'unda endpoint ID'nin bulunup bulunmadığını kontrol edin

### Token Hatası

- Login başarılı oluyor ancak token alınamıyorsa, API response formatı değişmiş olabilir
- Log dosyalarını kontrol edin: `config/home-assistant.log`
- Geliştirici konsolunda hata mesajlarını kontrol edin

### Güncelleme Sorunları

- Termostat durumu güncellenmiyorsa, Home Assistant'ı yeniden başlatmayı deneyin
- API bağlantısını kontrol edin
- Log dosyalarında hata mesajlarını kontrol edin

## 📝 API Endpoint'leri

Entegrasyon aşağıdaki API endpoint'lerini kullanır:

- `POST /users/login` - Kullanıcı girişi ve token alma
- `POST /endpoints/getEndpoint` - Termostat durumu alma
- `POST /endpoints/setMode` - Mod ayarlama
- `POST /endpoints/setTargetTemperatures` - Hedef sıcaklık ayarlama

## 🛠️ Geliştirme

### Proje Yapısı

```
cosa-homeassistant/
├── custom_components/
│   └── cosa/
│       ├── __init__.py          # Entegrasyon başlatma
│       ├── manifest.json        # Entegrasyon metadata
│       ├── config_flow.py       # Config flow
│       ├── climate.py           # Climate platform
│       ├── api.py               # API client
│       ├── const.py             # Sabitler
│       └── strings.json         # Türkçe çeviriler
├── .gitignore
├── LICENSE
├── README.md
├── CHANGELOG.md
├── hacs.json
└── info.md
```

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## 🤝 Katkıda Bulunma

Katkılarınız memnuniyetle karşılanır! Lütfen:

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit edin (`git commit -m 'Add some amazing feature'`)
4. Push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

## 📞 Destek

Sorun yaşarsanız:

1. [GitHub Issues](https://github.com/ahamitd/cosa-homeassistant/issues) sayfasında hata bildirimi oluşturun
2. Home Assistant log dosyalarını kontrol edin
3. Geliştirici konsolunda hata mesajlarını kontrol edin

## ⭐ Teşekkürler

- COSA API'sini sağlayan Nuvia'ya
- Home Assistant topluluğuna
- Tüm katkıda bulunanlara

---
