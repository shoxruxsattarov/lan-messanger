TEXNIK TOPSHIRIQ: LAN MESSENGER TIZIMI
1. Loyihaning vazifasi
LAN Messenger — korporativ yoki uy ichki tarmoqlari (LAN) uchun mo'ljallangan, internetga ulanishni talab qilmaydigan aloqa vositasi.
Biznes maqsad: Ma'lumotlarning tashqi serverlarga chiqib ketishini oldini olish orqali ichki xavfsizlikni ta'minlash va internet trafiki cheklangan sharoitda aloqa o'rnatish.
Foydalanuvchi maqsadi: Tarmoqdagi hamkasblar bilan tezkor fayl va xabar almashish, "Saved Messages" orqali shaxsiy eslatmalar yuritish.
2. Foydalanuvchi guruhlari
Oddiy foydalanuvchilar: Ichki tarmoqqa ulangan har qanday xodim/shaxs. Ular xabar yuborish, qabul qilish va fayllarni yuklab olish huquqiga ega.
Administratorlar (IT mutaxassislar): Dasturning loglarini kuzatish va tarmoq sozlamalarini (IP/Port) boshqarish imkoniyatiga ega foydalanuvchilar.
3. Tarkib sharhi (Funksiyalar va ssenariylar)
Ssenariy A (Avtomatik topish): Dastur yoqilishi bilan UDP Broadcast yordamida tarmoqdagi barcha faol nuqtalarni "Shaxsiy chatlar" ro'yxatiga chiqaradi.
Ssenariy B (Unicast): Foydalanuvchi ro'yxatdan bir kishini tanlaydi va u bilan TCP protokoli orqali shifrlangan, nuqtadan-nuqtaga muloqot qiladi.
Ssenariy C (Broadcast): "Umumiy" kategoriya orqali barcha foydalanuvchilarga muhim e'lonlarni bir vaqtda yuboradi.
Ssenariy D (Shaxsiy ombor): Foydalanuvchi o'ziga xabar yuborish orqali kerakli matnlarni saqlaydi (offline rejimda ham ishlaydi).
4. Boshqa komponentlar bilan o‘zaro munosabatlari
Windows OS File System: Yuborilgan va qabul qilingan fayllarni saqlash uchun tizimning fayl menejeri bilan integratsiya (Downloads papkasi).
Local Network Stack: Operatsion tizimning tarmoq drayverlari va portlari bilan to'g'ridan-to'g'ri soket darajasida muloqot qilish.
Eslatma: Tashqi API-lar (Google, Yandex) bilan integratsiya ko'zda tutilmagan (to'liq avtonomlik talabi).

5. Interfeys sharhi
Struktura: 3-panelli (3-column) zamonaviy "Dark Mode" dizayni.
Dizayn elementlari: PyQt5 "Material Design" uslubidagi komponentlar. Ko'k va quyuq kulrang ranglar gammasi.
Logotip: "LAN Messenger" yozuvi bilan yuqori chap burchakda joylashadi.
Aksent: Holat loglari uchun monoshirift (Courier New kabi) qo'llaniladi.
6. Xavfsizlik
Shifrlash: Barcha paketlar uzatilishdan oldin AES-256 (Advanced Encryption Standard) algoritmi bilan shifrlanadi.
Fayrvol (Firewall): Dastur birinchi marta ishga tushganda Windows Firewall'dan TCP/UDP portlari (56565, 55555) uchun ruxsat so'rashi kerak.
Ma'lumotlar maxfiyligi: Xabarlar tarixi faqat foydalanuvchining lokal xotirasida saqlanadi, server bazasiga yuborilmaydi.
7. Ishlab chiqish (Texnik qism)
Dasturlash tili: Python 3.10.
Kutubxonalar:
GUI: PyQt5, QtDesigner.
Network: socket, threading, select.
Security: cryptography (Fernet).
Arxitektura: Peer-to-Peer (P2P) — har bir mijoz ham server, ham mijoz rolini bajaradi.
8. Tizim muhiti
Qurilma: Desktop/Laptop kompyuterlar.
Operatsion tizim: Windows 10 yoki undan yuqori (64-bit).
Tarmoq: Ethernet yoki Wi-Fi (Lokal tarmoq izolatsiyasi bilan).
Minimal talablar: 100MB bo'sh joy, 2GB RAM.
Muddat va Bosqichlar (Xulosa)
24.03.2026: UI shablonini tayyorlash va UDP Discovery qismini yozish.
25.03.2026: TCP xabar almashish logikasini ulash.
26.03.2026: Shifrlash va Loglarni sozlash.
27.03.2026: Yakuniy test va bug-fix.













Login page


Ishchi oyna












