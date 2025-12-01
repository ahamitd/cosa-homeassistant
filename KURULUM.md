# COSA Home Assistant Entegrasyonu - Kurulum Kılavuzu

## Gereksinimler

- Home Assistant 2023.1 veya üzeri
- Python 3.9 veya üzeri
- COSA uygulamasında aktif hesap

## Kurulum Adımları

### 1. Dosyaları Kopyalama

Home Assistant'ın `config` klasörüne `custom_components` klasörünü kopyalayın:

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

**Önemli:** `custom_components` klasörü yoksa oluşturun.

### 2. Home Assistant'ı Yeniden Başlatma

Home Assistant'ı tamamen yeniden başlatın (sadece reload değil).

### 3. Entegrasyonu Ekleme

1. Home Assistant arayüzünde **Ayarlar** > **Cihazlar ve Hizmetler**'e gidin
2. Sağ alttaki **+ Entegrasyon Ekle** butonuna tıklayın
3. Arama kutusuna **"COSA"** yazın
4. **COSA Termostat** entegrasyonunu seçin

### 4. Giriş Bilgilerini Girme

1. **Kullanıcı Adı:** COSA uygulamasında kullandığınız kullanıcı adı veya e-posta
2. **Şifre:** COSA uygulamasında kullandığınız şifre
3. **Endpoint ID (Opsiyonel):** Eğer otomatik tespit edilmezse, COSA uygulamasından cihaz ID'nizi girebilirsiniz

### 5. Doğrulama

Entegrasyon başarıyla kurulduktan sonra:

1. **Ayarlar** > **Cihazlar ve Hizmetler**'de **COSA Termostat** görünmeli
2. Ana sayfada termostat cihazınız görünmeli
3. Termostat kontrolü yapabilmelisiniz

## Kullanım

### Termostat Kontrolü

- **Açık/Kapalı:** HVAC modunu değiştirerek kombiyi açıp kapatabilirsiniz
- **Sıcaklık Ayarı:** Hedef sıcaklığı ayarlayabilirsiniz (5-32°C arası)
- **Preset Modları:**
  - **Ev (Home):** Ev modu
  - **Dışarıda (Away):** Dışarıda modu
  - **Gece (Sleep):** Gece modu
  - **Kullanıcı (Custom):** Özel mod

### Sensörler

Entegrasyon aşağıdaki bilgileri sağlar:

- **Mevcut Sıcaklık:** Oda sıcaklığı
- **Hedef Sıcaklık:** Ayarlanan hedef sıcaklık
- **Nem:** Oda nem oranı
- **Durum:** Kombi çalışma durumu (Açık/Kapalı)
- **Mod:** Aktif preset modu

## Sorun Giderme

### "Bağlanılamadı" Hatası

- İnternet bağlantınızı kontrol edin
- COSA API'sinin erişilebilir olduğundan emin olun (`https://kiwi-api.nuvia.com.tr`)
- Firewall ayarlarınızı kontrol edin

### "Geçersiz Kimlik Doğrulama" Hatası

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

## API Endpoint'leri

Entegrasyon aşağıdaki API endpoint'lerini kullanır:

- `POST /users/login` - Kullanıcı girişi ve token alma
- `POST /endpoints/getEndpoint` - Termostat durumu alma
- `POST /endpoints/setMode` - Mod ayarlama
- `POST /endpoints/setTargetTemperatures` - Hedef sıcaklık ayarlama

## Geliştirme Notları

### Login Endpoint Alternatifleri

Entegrasyon farklı login endpoint formatlarını deneyerek çalışır:
- `/users/login`
- `/auth/login`
- `/login`

### Token Formatları

Entegrasyon aşağıdaki token formatlarını destekler:
- `token`
- `authtoken`
- `access_token`
- `accessToken`
- `data.token`
- `data.authtoken`

### Endpoint ID Tespiti

Login sırasında endpoint ID otomatik olarak tespit edilmeye çalışılır. Eğer bulunamazsa, kullanıcıdan manuel olarak istenir.

## Destek

Sorun yaşarsanız:

1. Home Assistant log dosyalarını kontrol edin
2. Geliştirici konsolunda hata mesajlarını kontrol edin
3. API response'larını inceleyin
4. GitHub issues'da benzer sorunları arayın

## Lisans

Bu entegrasyon ahamitd tarafından geliştirilmiştir ve açık kaynaklıdır.
Herhangi bir telif ve sorularınız için https://t.me/ahamitd iletişime geçebilirsiniz.

