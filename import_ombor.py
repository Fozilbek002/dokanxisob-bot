"""
import_ombor.py — Ombor ro'yxatini botning bazasiga (qayta) qo'shadi.

QANDAY ISHLATISH:
1. Bu faylni bot.py, database.py bilan BIR XIL papkaga qo'ying
   (chunki u database.py dagi funksiyalardan foydalanadi).
2. Agar botni ishga tushirishda DB_PATH muhit o'zgaruvchisi ishlatgan
   bo'lsangiz, shu skriptni ham xuddi shunday ishga tushiring, masalan:
       DB_PATH=hisobot_bot.db python3 import_ombor.py
   Aks holda oddiy:
       python3 import_ombor.py
3. Skript ishlab bo'lgach, botni ochib "📦 Ombor" tugmasini bosib
   tekshiring — 87 ta mahsulot ko'rinishi kerak.

DIQQAT: bu skript mahsulotlarni YANGI qator sifatida QO'SHADI.
Agar botda ayni shu mahsulotlar allaqachon bor bo'lsa, ular
IKKILANIB (dublikat) qo'shilib qoladi. Faqat bo'sh/o'chib ketgan
ombor uchun bir marta ishlating.
"""

import database as db

OWNER_ID = 7558203366  # sizning Telegram ID'ingiz

ITEMS = [
    ("Almaz gisk oq", 1050000, 5, "dona"),
    ("Almaz gisk qora", 1050000, 5, "dona"),
    ("Alumen chelak", 474500, 2, "dona"),
    ("Antibrik", 171000, 20, "dona"),
    ("Balon katta", 189800, 6, "dona"),
    ("Balon kichik", 189800, 6, "dona"),
    ("Barboros bittalik moyli", 5000000, 60, "dona"),
    ("Bibiron 3L", 52000, 65, "dona"),
    ("Bibiron 4L", 71500, 10, "dona"),
    ("Bolustavatil M", 475000, 10, "dona"),
    ("Chelak 8L", 127400, 70, "dona"),
    ("Chelak klapn 8", 45000, 40, "dona"),
    ("Chelak soska", 40000, 50, "dona"),
    ("Chisalka 100 sm Xitoy", 5850000, 2, "dona"),
    ("Chisalka 60 sm Xitoy", 5213000, 2, "dona"),
    ("Chisalka Melasty", 8500000, 5, "dona"),
    ("Chotka kalta", 35100, 25, "dona"),
    ("Cho'tka uzun", 35100, 25, "dona"),
    ("Chupachups Barba K", 45000, 50, "dona"),
    ("Chupachups Melasty K", 45000, 50, "dona"),
    ("Chupachups kurtsan", 45000, 30, "dona"),
    ("Damkrat", 2500000, 2, "dona"),
    ("Do doyka kanstr", 24500, 520, "litr"),
    ("Droja", 39000, 50, "kg"),
    ("Flaga Nerjaviyka 40L", 1600000, 2, "dona"),
    ("Gilza Nerjaviyka", 156000, 20, "dona"),
    ("Gilza ftulka", 45000, 25, "dona"),
    ("Gulishitel moyli", 195000, 3, "dona"),
    ("Gulshtl suxvoy", 195000, 2, "dona"),
    ("Karo'tki shlang", 10000, 100, "dona"),
    ("Katta kirishka barba", 98000, 10, "dona"),
    ("Katta krishka rezinasi", 78000, 20, "dona"),
    ("Kichik kirishka 2 teshik", 89000, 25, "dona"),
    ("Kichik kirishka 3 teshik", 89000, 25, "dona"),
    ("Kichik kirishka rezinasi", 78000, 25, "dona"),
    ("Kislota", 425000, 8, "dona"),
    ("Kollektor Melasty [240]", 201500, 20, "dona"),
    ("Kollektor borba [240]", 169000, 20, "dona"),
    ("Kollektor kanplekt borba", 845000, 4, "dona"),
    ("Kollektor kurtsan", 410000, 10, "dona"),
    ("Ko'mir 4.90x43x70", 325000, 10, "dona"),
    ("Ko'mir 4.90x43x80", 325000, 10, "dona"),
    ("Ko'mir 4.90x43x85", 325000, 10, "dona"),
    ("Ko'mir 6x46x70", 325000, 10, "dona"),
    ("Magnit bolyus", 29811, 200, "dona"),
    ("Manametr kichik borbo", 130000, 10, "dona"),
    ("Manametr kichik oddiy", 130000, 15, "dona"),
    ("Melasty Junyor moyli", 5811000, 25, "dona"),
    ("Melasty ikkitalik moyli", 7020000, 15, "dona"),
    ("Melasty ikkitalik suxvoy", 6760000, 5, "dona"),
    ("Minbrana kanplekt", 46800, 50, "dona"),
    ("Minbrana kichik oq", 10000, 150, "dona"),
    ("Moy 1L", 29900, 40, "dona"),
    ("Moy 20L kanstr", 32500, 40, "litr"),
    ("Moy bacho'k tagi", 125000, 10, "dona"),
    ("Nasos klapn rezina", 210000, 5, "dona"),
    ("Nasos klapn temrli", 240000, 5, "dona"),
    ("Posli doyka yo'd 1L", 55000, 24, "litr"),
    ("Posli stakan", 51000, 48, "dona"),
    ("Poslidoyka xlor 1L", 55000, 24, "litr"),
    ("Poslidoyka yod kanstr", 35750, 40, "litr"),
    ("Pulsator borba", 170000, 25, "dona"),
    ("Pulsator shlang", 52000, 50, "metr"),
    ("Regulyato'r Melasty", 110000, 15, "dona"),
    ("Rigulyator barba", 110000, 10, "dona"),
    ("Separator", 1800000, 5, "dona"),
    ("Sho'lch", 425000, 8, "dona"),
    ("Soda", 7200, 500, "kg"),
    ("Soska (17) Melasty", 35300, 100, "dona"),
    ("Soska (22) Melasty", 48400, 100, "dona"),
    ("Soska (27) Melasty", 40625, 160, "dona"),
    ("Soska (27) Melasty katta teshik", 40625, 80, "dona"),
    ("Soska (27) barba", 40625, 160, "dona"),
    ("Sovun", 100000, 8, "dona"),
    ("Sut shlang", 52000, 50, "metr"),
    ("Tal Xitoy", 1500000, 5, "dona"),
    ("Tekstalit 4,90x43x70", 390000, 10, "dona"),
    ("Tekstalit 6x46x70", 390000, 5, "dona"),
    ("Vakum bachok barboros", 676000, 2, "dona"),
    ("Vakum bachok krishka", 33800, 10, "dona"),
    ("Vakum bachok salnigi", 39000, 10, "dona"),
    ("Vilofoss (083)", 24000, 250, "kg"),
    ("Vilofoss (084)", 22000, 1000, "kg"),
    ("Vilofoss (085)", 23000, 300, "kg"),
    ("Vilofoss (115)", 22500, 1125, "kg"),
    ("Vilofoss (179)", 24000, 250, "kg"),
    ("Vilofoss (259)", 20000, 1000, "kg"),
]

def main():
    db.init_db()
    added = 0
    for name, price, qty, unit in ITEMS:
        db.add_item(OWNER_ID, name, price, qty, unit)
        added += 1
        print(f"✅ {name} — {qty} {unit} x {price:,.0f} so'm".replace(",", " "))
    print(f"\nJami {added} ta mahsulot bazaga qo'shildi (owner_id={OWNER_ID}).")

if __name__ == "__main__":
    main()
