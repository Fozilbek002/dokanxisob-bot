# 🏪 Do'kon hisob-kitob Telegram boti

Ombor, sotuv, chiqim, kassa va hisobotlarni yurituvchi Telegram bot.

## Imkoniyatlar

- 📦 **Ombor** — mahsulot nomi, tannarxi va miqdorini kiritish
- 💰 **Sotish** — ombordan mahsulot tanlab sotish (qoldiq avtomatik kamayadi)
- 💸 **Chiqim** — xarajatlarni yozib borish (ijara, transport va h.k.)
- 💵 **Kassa** — kassani ochish / yopish, boshlang'ich va yakuniy summa
- 📊 **Hisobot** — kunlik / haftalik / oylik / yillik yoki ixtiyoriy sana oralig'i
- 📄 **PDF** — oxirgi ko'rilgan hisobotni PDF fayl qilib yuklab olish
- 📊 **Excel** — oxirgi hisobotni Excel (.xlsx) fayl qilib yuklab olish (Sotuvlar, Chiqimlar, Xulosa varaqlari bilan)
- 📈 **Grafiklar** — kunlik foyda/zarar ustunli diagrammasi
- 🤖 **AI tahlili** — Anthropic API orqali hisobot bo'yicha qisqa AI xulosa (ixtiyoriy, API kalit kerak)
- 🌐 **Til** — O'zbek (lotin/kirill), Rus, Ingliz (hozircha faqat lotin tili to'liq tarjima qilingan)

## O'rnatish

```bash
pip install -r requirements.txt
```

## Sozlash

1. Telegram'da **@BotFather** ga yozib yangi bot yarating, tokenni oling.
2. `bot.py` faylida:
   ```python
   BOT_TOKEN = "SIZNING_TOKEN_BU_YERGA"
   ```
   qatoriga o'z tokeningizni qo'ying.
3. (Ixtiyoriy) AI tahlili ishlashi uchun terminalda:
   ```bash
   export ANTHROPIC_API_KEY="sizning_api_kalitingiz"
   ```

## Ishga tushirish

```bash
python bot.py
```

## Fayllar tuzilishi

```
hisobot_bot/
├── bot.py           # Asosiy bot va barcha buyruqlar
├── database.py       # SQLite bilan ishlash (ombor, sotuv, chiqim, kassa)
├── language.py        # Ko'p tillilik lug'ati
├── keyboards.py        # Menyu va tugmalar
├── reports.py           # Excel / PDF / Grafik yaratish
├── requirements.txt
└── README.md
```

Ma'lumotlar `hisobot_bot.db` nomli SQLite faylida saqlanadi — bot papkasida avtomatik yaratiladi.

## Qanday ishlaydi (foyda/zarar hisobi)

- Har bir sotuvda mahsulotning **o'sha paytdagi tannarxi** saqlanadi, shu sababli keyinchalik tannarx o'zgarsa ham eski sotuvlar foyda hisobi to'g'ri qoladi.
- **Sof foyda** = (sotuvlardan sof foyda) − (chiqimlar)
- Natija manfiy bo'lsa, bot buni **"SOF ZARAR"** deb ko'rsatadi.

## Kengaytirish g'oyalari

- Kirill/Rus/Ingliz tarjimalarini `language.py` faylida to'ldirish
- Foydalanuvchilarga ruxsat (faqat administrator botdan foydalansin) qo'shish
- Bir nechta do'kon/filial uchun alohida hisob yuritish
- Excel/PDF fayllarni Google Drive'ga avtomatik yuklash
