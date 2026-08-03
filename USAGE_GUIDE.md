# MyRadar24 - Usage Guide / Kullanım Kılavuzu

## Quick Start / Hızlı Başlangıç

### Installation / Kurulum
```bash
# 1. Install dependencies / Bağımlılıkları kur
python setup.bat

# Or manually / Veya manuel
pip install -r requirements.txt

# 2. Run the application / Uygulamayı çalıştır
python myradar24.py

# Or use / Veya kullan
start.bat
```

## Step-by-Step Guide / Adım Adım Kılavuz

### 1. Adding Your First Flight / İlk Uçuşu Ekleme

**English:**
1. Click the "Add Flight" button at the top
2. Enter a flight number (e.g., "THY123" or "TK1983")
3. Click "Search" button
4. Select a flight from the results list
5. Click "Add" button
6. The flight will appear in the main table

**Türkçe:**
1. Üstteki "Uçuş Ekle" butonuna tıklayın
2. Bir uçuş numarası girin (örn: "THY123" veya "TK1983")
3. "Ara" butonuna tıklayın
4. Sonuç listesinden bir uçuş seçin
5. "Ekle" butonuna tıklayın
6. Uçuş ana tabloda görünecektir

### 2. Understanding the Table / Tabloyu Anlamak

**Columns / Sütunlar:**

| Column | What it Shows | Example |
|--------|---------------|---------|
| Flight / Uçuş | Flight number or callsign | THY123 |
| From / Nereden | Departure airport | IST |
| To / Nereye | Arrival airport | JFK |
| Aircraft / Uçak | Plane type & registration | B77W (TC-JJN) |
| Departure Time / Kalkış | When plane took off | 14:30 |
| Arrival Time / İniş | When plane will/did land | 18:45 |
| Status / Durum | Current status | In Flight |
| ETA / Tahmini | Time remaining to land | 2h 15m |
| Landed / İneli | Time since landing | 45 min |

### 3. Flight Status Examples / Uçuş Durumu Örnekleri

#### Scenario 1: Flight Not Yet Departed / Senaryo 1: Uçak Henüz Kalkmadı

```
Flight: THY123
Status: Not Departed / Kalkmadı
ETA: - (dash)
Landed: - (dash)
```
- ✅ Updates every 5 seconds / Her 5 saniyede güncellenir
- ✅ When it takes off, you'll get a sound notification / Kalktığında ses bildirimi alırsınız

#### Scenario 2: Flight In Air / Senaryo 2: Uçak Havada

```
Flight: THY123
Status: In Flight / Uçuşta
Departure Time: 14:30
ETA: 2h 15m
Landed: -
```
- ✅ ETA counts down every update / ETA her güncellemede azalır
- ✅ Updates every 30 seconds / Her 30 saniyede güncellenir

#### Scenario 3: Flight Landed / Senaryo 3: Uçak İndi

```
Flight: THY123
Status: Landed / İndi
Arrival Time: 18:45
ETA: 00:00
Landed: 25 min
```
- ✅ You received a sound notification when it landed / İndiğinde ses bildirimi aldınız
- ✅ "Landed" time increases / "İneli" süresi artar

### 4. Managing Flights / Uçuşları Yönetme

#### Remove a Flight / Uçuş Kaldırma

**English:**
1. Click on the flight row in the table
2. Click "Remove Flight" button
3. The flight will be removed immediately

**Türkçe:**
1. Tablodaki uçuş satırına tıklayın
2. "Uçuşu Kaldır" butonuna tıklayın
3. Uçuş hemen kaldırılacaktır

#### Refresh All / Hepsini Yenile

**English:**
- Click "Refresh All" button to manually update all flights
- Useful if you want immediate updates

**Türkçe:**
- Tüm uçuşları manuel olarak güncellemek için "Hepsini Yenile" butonuna tıklayın
- Anında güncelleme istediğinizde kullanışlıdır

### 5. Changing Language / Dil Değiştirme

**Method 1 / Yöntem 1:**
1. Click "Language" menu at top
2. Select "English" or "Türkçe"
3. UI updates immediately

**Method 2 / Yöntem 2:**
1. Üstteki "Dil" menüsüne tıklayın
2. "English" veya "Türkçe" seçin
3. Arayüz hemen güncellenir

### 6. Sound Notifications / Ses Bildirimleri

#### When You'll Hear Sounds / Ne Zaman Ses Duyarsınız

**Takeoff / Kalkış:**
- 🔊 When a tracked flight takes off
- 🔊 Takip edilen uçak kalktığında
- Shows popup: "Flight THY123 has departed!" / Açılır pencere: "THY123 uçuşu kalktı!"

**Landing / İniş:**
- 🔊 When ETA reaches 00:00 and plane lands
- 🔊 ETA 00:00'a ulaştığında ve uçak indiğinde
- Shows popup: "Flight THY123 has landed!" / Açılır pencere: "THY123 uçuşu indi!"

### 7. Tips & Tricks / İpuçları

**Tip 1: Multiple Flights / Çoklu Uçuş**
- You can track as many flights as you want
- İstediğiniz kadar uçak takip edebilirsiniz

**Tip 2: Search Tips / Arama İpuçları**
- Try both flight number and callsign if one doesn't work
- Biri çalışmazsa hem uçuş numarasını hem çağrı ismini deneyin
- Examples / Örnekler: "TK1983", "THY1983", "Turkish 1983"

**Tip 3: Arrival Times / Varış Saatleri**
- Arrival time shown is estimated, may change during flight
- Gösterilen varış saati tahminidir, uçuş sırasında değişebilir

**Tip 4: Not Found? / Bulunamadı mı?**
- Flight might not be active yet / Uçuş henüz aktif olmayabilir
- Try searching closer to departure time / Kalkış saatine yakın arayın
- Check if flight number is correct / Uçuş numarasının doğru olup olmadığını kontrol edin

## Common Search Examples / Yaygın Arama Örnekleri

### Turkish Airlines / Türk Hava Yolları
```
THY123, TK1983, Turkish 1
```

### Pegasus Airlines
```
PGT123, PC2103
```

### American Airlines
```
AAL123, AA100
```

### Emirates
```
UAE202, EK202
```

### Lufthansa
```
DLH400, LH400
```

## Troubleshooting / Sorun Giderme

### Problem: No flights found / Uçuş bulunamadı

**Solutions / Çözümler:**
- Check spelling / Yazımı kontrol edin
- Try different format (THY vs TK) / Farklı format deneyin
- Flight might not be active / Uçuş aktif olmayabilir
- Try again closer to departure / Kalkışa yakın tekrar deneyin

### Problem: Sound not playing / Ses çalmıyor

**Solutions / Çözümler:**
- Check Windows volume / Windows ses seviyesini kontrol edin
- Check if .wav files exist in sound folder / .wav dosyalarının sound klasöründe olup olmadığını kontrol edin
- Restart application / Uygulamayı yeniden başlatın

### Problem: Flight not updating / Uçuş güncellenmiyor

**Solutions / Çözümler:**
- Click "Refresh All" / "Hepsini Yenile"ye tıklayın
- Check internet connection / İnternet bağlantısını kontrol edin
- Flight might have ended / Uçuş bitmiş olabilir

## Keyboard Shortcuts / Klavye Kısayolları

- **Enter** in search box = Search / Arama kutusunda = Ara
- **Double-click** on result = Add flight / Sonuçta = Uçuş ekle
- **Click + Remove Flight** = Delete / Tıkla + Uçuşu Kaldır = Sil

## Support / Destek

For issues or questions:
Sorunlar veya sorular için:

- Check FEATURES.md for detailed features / Detaylı özellikler için FEATURES.md'ye bakın
- Check README.md for installation / Kurulum için README.md'ye bakın
