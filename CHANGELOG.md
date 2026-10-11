# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.6] - 2026-10-11

### Added
- **Kombi Çalışma ve Durma Toleransı (PID Aralığı / Histerezis) Kontrolleri**
  - `number.cosa_combi_work_range` (`pidWindowLow`): Hedef sıcaklığın kaç derece altına inildiğinde kombinin devreye gireceği ayarı (0.0°C - 2.0°C, varsayılan 0.1°C).
  - `number.cosa_combi_stop_range` (`pidWindowHigh`): Hedef sıcaklığın kaç derece üstüne çıkıldığında kombinin devreden çıkacağı ayarı (0.0°C - 2.0°C, varsayılan 0.2°C).
  - `cosa.set_combi_range` servisi: Otomasyonlar ve scriptler üzerinden kombi çalışma ve durma toleranslarını dinamik olarak ayarlama desteği.
- **Süreli Mod Süresi Özniteliği (`timer_duration`)**:
  - Termostat (`climate`) entity'sine `timer_duration` extra state attribute'u eklendi; aktif Turbo veya Havalandırma süresini kartlar ve otomasyonlar için takip edebilme imkanı sağlandı.

### Fixed
- **Preset Sıcaklık İzolasyonu**:
  - Termostat arayüzünden manuel hedef sıcaklık değiştirildiğinde kayıtlı Evdeyim (`homeTemperature`), Dışarıdayım (`awayTemperature`) veya Uyku (`sleepTemperature`) preset değerlerinin ezilmesi engellendi; değişiklikler güvenle anlık özel sıcaklık (`customTemperature`) ve manuel moda yönlendirildi.
- API `set_combi_settings` çağrısında sunucu tarafından reddedilen parametreler temizlendi ve stabilite sağlandı.

## [1.0.2] - 2025-12-02

### Fixed
- Rapor sensörleri artık doğru veriyi gösteriyor (API response yapısı düzeltildi)
- Dış sıcaklık, dış nem ve hava durumu sensörleri düzeltildi
- get_forecast ve get_reports API metodları düzeltildi

## [1.0.1] - 2025-12-02

### Added
- **Rapor Sensörleri (Son 24 Saat İstatistikleri)**
  - Toplam Çalışma Süresi (saat)
  - Evde Modu Çalışma Süresi
  - Uyku Modu Çalışma Süresi
  - Ortalama Sıcaklık
  - Maksimum/Minimum Sıcaklık
  - Maksimum/Minimum Nem
  - Dış Ortam Ortalama Sıcaklık
  - Ağ Kalitesi
- **Çocuk Kilidi Switch** - Çocuk kilidi özelliğini açıp kapama
- **Açık Pencere Algılama Switch** - Açık pencere algılama özelliğini açıp kapama
- **Kalibrasyon Number** - Sıcaklık kalibrasyonu (-5°C ile +5°C arası)
- **Preset Sıcaklık Kontrolleri** - Evde, Dışarı, Uyku ve Manuel sıcaklıkları ayarlama
- HACS ve Hassfest GitHub Actions eklendi

### Improved
- Optimistik güncellemeler ile daha hızlı UI yanıtı
- HVAC ve preset mod değişikliklerinde anlık görsel güncelleme
- API isteklerinde daha iyi hata yönetimi

## [1.0.0] - 2024-01-01

### Added
- Initial release of COSA Home Assistant integration
- Support for COSA thermostat control
- Temperature control (5-32°C)
- Preset modes: Home, Away, Sleep, Custom
- HVAC mode control (Heat/Off)
- Humidity and temperature sensors
- Automatic updates every 10 seconds
- Config flow for easy setup
- Turkish language support for configuration
