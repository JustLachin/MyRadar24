# MyRadar24 - Quick Start Guide

## 🚀 Installation in 3 Steps

### Step 1: Install Python
Make sure you have Python 3.8 or higher installed:
```bash
python --version
```

### Step 2: Install Dependencies
Double-click `setup.bat` or run:
```bash
pip install -r requirements.txt
```

### Step 3: Run Application
Double-click `start.bat` or run:
```bash
python myradar24.py
```

## 🎯 First Use - Track a Flight in 60 Seconds

1. **Launch the app** → See the main window with empty table
2. **Click "Add Flight"** → Search dialog opens
3. **Type flight number** → e.g., "THY123" or "TK1983"
4. **Click "Search"** → Results appear
5. **Select a flight** → Click on it
6. **Click "Add"** → Flight added to tracking table
7. **Wait for updates** → Auto-refresh every 5-30 seconds
8. **Get notifications** → 🔊 Sound when takeoff/landing

## 📊 What You'll See

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ✈  MyRadar24 - Flight Tracker                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  [Add Flight]  [Remove Flight]  [Refresh All]                              │
├────────┬────────┬────────┬──────────┬──────────┬──────────┬────────┬───────┤
│ Flight │  From  │   To   │ Aircraft │ Departure│ Arrival  │ Status │  ETA  │
├────────┼────────┼────────┼──────────┼──────────┼──────────┼────────┼───────┤
│ THY123 │  IST   │  JFK   │ B77W     │  14:30   │  18:45   │ Flight │ 2h15m │
│ PC2103 │  SAW   │  AYT   │ B738     │  15:00   │    -     │Not Dep │   -   │
│ LH400  │  FRA   │  JFK   │ A388     │  10:15   │  13:30   │ Landed │   -   │
└────────┴────────┴────────┴──────────┴──────────┴──────────┴────────┴───────┘
```

## 🔔 Notifications You'll Get

### When Flight Takes Off
```
┌─────────────────────────────┐
│  🛫 Takeoff                 │
│  Flight THY123 has         │
│  departed!                  │
│  [OK]                       │
└─────────────────────────────┘
+ 🔊 Celebration sound
```

### When Flight Lands
```
┌─────────────────────────────┐
│  🛬 Landing                 │
│  Flight THY123 has         │
│  landed!                    │
│  [OK]                       │
└─────────────────────────────┘
+ 🔊 Notification sound
```

## 🌍 Change Language

1. Click **"Language"** menu
2. Select **"English"** or **"Türkçe"**
3. UI updates instantly

## 💡 Pro Tips

### Tip 1: Track Multiple Flights
- Add as many flights as you want
- No limit!

### Tip 2: Try Different Formats
If search doesn't work, try:
- `THY123` vs `TK123`
- `Turkish 123`
- Callsign vs Flight Number

### Tip 3: Best Time to Add Flights
- Add flights 30-60 minutes before departure
- Too early? Flight might not be active yet

### Tip 4: Remove Completed Flights
- Click on landed flight row
- Click "Remove Flight"
- Keeps your list clean

## 📱 Example Flights to Try

### Turkish Airlines
```
THY1, TK1983, Turkish 123
```

### Pegasus Airlines
```
PGT123, PC2103
```

### Popular International
```
LH400 (Frankfurt → New York)
EK202 (Dubai → New York)
BA117 (London → New York)
AA100 (Los Angeles → New York)
```

## ❓ Troubleshooting

### "Flight not found"
- ✅ Check spelling
- ✅ Try different format (TK vs THY)
- ✅ Try closer to departure time

### "No sound"
- ✅ Check Windows volume
- ✅ Check sound files exist in `sound/` folder
- ✅ Restart application

### "Application won't start"
- ✅ Run `setup.bat` again
- ✅ Check Python version (3.8+)
- ✅ Check internet connection

## 📖 More Information

- **Detailed Features**: See `FEATURES.md`
- **Complete Guide**: See `USAGE_GUIDE.md`
- **Technical Details**: See `PROJECT_STRUCTURE.md`
- **Installation**: See `README.md` or `README.tr.md`

## 🎊 You're Ready!

That's it! You now know how to:
- ✅ Install and run MyRadar24
- ✅ Add flights to tracking
- ✅ Understand the status
- ✅ Get notifications
- ✅ Change language

**Enjoy tracking your flights! 🛫**

---

# Türkçe Hızlı Başlangıç

## 🚀 3 Adımda Kurulum

### Adım 1: Python Kurulu mu?
Python 3.8 veya üstü gerekli:
```bash
python --version
```

### Adım 2: Bağımlılıkları Kur
`setup.bat`'a çift tıklayın veya:
```bash
pip install -r requirements.txt
```

### Adım 3: Uygulamayı Çalıştır
`start.bat`'a çift tıklayın veya:
```bash
python myradar24.py
```

## 🎯 İlk Kullanım - 60 Saniyede Uçuş Takibi

1. **Uygulamayı başlat** → Boş tablo ile ana pencere açılır
2. **"Uçuş Ekle"ye tıkla** → Arama penceresi açılır
3. **Uçuş numarası yaz** → örn: "THY123" veya "TK1983"
4. **"Ara"ya tıkla** → Sonuçlar görünür
5. **Bir uçuş seç** → Üzerine tıkla
6. **"Ekle"ye tıkla** → Uçuş tabloya eklenir
7. **Güncellemeleri bekle** → Her 5-30 saniyede otomatik
8. **Bildirimleri al** → 🔊 Kalkış/iniş sesli bildirim

## 💡 İpuçları

- Sınırsız uçuş ekleyebilirsiniz
- Farklı formatlar deneyin (THY vs TK)
- Kalkıştan 30-60 dk önce ekleyin
- Dil değiştirmek için menüden seçin

**İyi takipler! 🛫**
