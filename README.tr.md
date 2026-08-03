# MyRadar24 - Uçuş Takip Masaüstü Uygulaması

FlightRadar24 API'sini kullanarak uçuşları gerçek zamanlı takip eden kapsamlı bir masaüstü uygulaması.

## Özellikler

- **Canlı Uçuş Takibi**: Birden fazla uçağı aynı anda gerçek zamanlı takip edin
- **Kalkış ve İniş Saatleri**: Planlanan ve gerçek kalkış/iniş saatlerini gösterir
- **Tahmini İniş Süresi (ETA)**: Uçuştaki uçaklar için inişe kalan süreyi gösterir
- **İniş Zamanı**: Uçağın ne kadar süre önce indiğini takip eder
- **Akıllı Güncelleme**: 
  - Kalkmayan uçaklar: Her 5 saniyede bir güncellenir
  - Tüm takip edilen uçaklar: Her 30 saniyede bir güncellenir
- **Sesli Bildirimler**: 
  - Takip edilen uçak kalktığında ses bildirimi
  - Takip edilen uçak indiğinde ses bildirimi
- **Çoklu Dil Desteği**: İngilizce ve Türkçe dil seçenekleri
- **Kullanıcı Dostu Arayüz**: Sıralanabilir tablolarla temiz PyQt6 tabanlı arayüz

## Gereksinimler

- Python 3.8 veya üzeri
- PyQt6
- FlightRadar24 SDK (SDK klasöründe dahildir)

## Kurulum

1. Bu depoyu klonlayın veya indirin

2. Gerekli bağımlılıkları kurun:
```bash
pip install -r requirements.txt
```

3. SDK klasörünün uygulama ile aynı dizinde olduğundan emin olun

## Kullanım

Uygulamayı çalıştırın:
```bash
python myradar24.py
```

### Uçuş Ekleme

1. "Uçuş Ekle" butonuna tıklayın
2. Uçuş numarasını veya çağrı ismini girin (örn: THY123, TK1983)
3. "Ara" butonuna tıklayın
4. Sonuçlardan bir uçuş seçin
5. Takibi başlatmak için "Ekle"ye tıklayın

### Uçuş Kaldırma

1. Tablodaki bir uçuşu seçin
2. "Uçuşu Kaldır" butonuna tıklayın

### Dil Değiştirme

1. Dil menüsüne gidin
2. "English" veya "Türkçe" seçin

## Ses Efektleri

Uygulama SND01-sine-sound-pack ses efektlerini kullanır:
- **Kalkış**: Uçak kalktığında kutlama sesi
- **İniş**: Uçak indiğinde bildirim sesi

## Tablo Sütunları

- **Uçuş**: Uçuş numarası/çağrı ismi
- **Nereden**: Kalkış havalimanı (IATA kodu)
- **Nereye**: İniş havalimanı (IATA kodu)
- **Uçak**: Uçak tipi ve kayıt numarası
- **Kalkış Saati**: Gerçek veya planlanan kalkış saati
- **İniş Saati**: Gerçek veya planlanan iniş saati
- **Durum**: Kalkmadı / Uçuşta / İndi
- **Tahmini**: Kalan tahmini süre (sadece uçuştakiler için)
- **İneli**: İnişten bu yana geçen süre

## Lisans

Bu proje FlightRadar24 SDK'sını kullanmaktadır. Lütfen FlightRadar24'ün kullanım şartlarına bakın.
