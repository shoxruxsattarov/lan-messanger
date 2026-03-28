LAN Messenger Tizimi

LAN Messenger — bu korporativ yoki uy ichki tarmoqlari (LAN) uchun mo‘ljallangan, internetga ulanmasdan ishlaydigan xavfsiz aloqa tizimi. Dastur foydalanuvchilarga bir lokal tarmoq ichida tezkor xabar almashish, fayl yuborish va shaxsiy qaydlarni saqlash imkonini beradi.

Ushbu loyiha ichki xavfsizlik, mustaqillik, va tezkor lokal muloqot tamoyillari asosida ishlab chiqilgan.

Loyihaning maqsadi
Biznes maqsadi

Tashqi serverlar va internet xizmatlariga bog‘lanmagan holda, ichki tarmoqdagi ma’lumotlar almashinuvini ta’minlash. Bu orqali:

ma’lumotlarning tashqi tarmoqqa chiqib ketishi oldi olinadi;
internet trafiki cheklangan yoki mavjud bo‘lmagan muhitda ham aloqa davom etadi;
korporativ ichki kommunikatsiya xavfsizligi oshiriladi.
Foydalanuvchi maqsadi

Foydalanuvchilar bir lokal tarmoq ichida:

hamkasblari bilan tezkor yozishmalar olib borishi,
fayl almashishi,
va Saved Messages orqali o‘ziga kerakli eslatmalarni saqlashi mumkin bo‘ladi.
Asosiy imkoniyatlar
1. Avtomatik foydalanuvchilarni aniqlash

Dastur ishga tushirilganda UDP Broadcast yordamida tarmoqdagi faol qurilmalarni aniqlaydi va ularni Shaxsiy chatlar ro‘yxatida ko‘rsatadi.

2. Shaxsiy chat

Foydalanuvchi ro‘yxatdan kerakli kishini tanlab, u bilan TCP orqali shifrlangan nuqtadan-nuqtaga (peer-to-peer) muloqot qiladi.

3. Umumiy xabarlar

Umumiy bo‘limi orqali barcha online foydalanuvchilarga bir vaqtning o‘zida e’lon yoki muhim xabar yuborish mumkin.

4. Saved Messages

Foydalanuvchi o‘ziga o‘zi xabar yuborib, shaxsiy matnlar, eslatmalar yoki kerakli ma’lumotlarni saqlab borishi mumkin. Bu funksiya offline rejimda ham ishlaydi.

5. Fayl almashish

Foydalanuvchilar o‘zaro fayl yuborishi va qabul qilishi mumkin. Qabul qilingan fayllar lokal tizimda saqlanadi.

6. Lokal chat tarixi

Barcha yozishmalar va tarixlar faqat foydalanuvchining lokal xotirasida saqlanadi. Hech qanday tashqi server yoki bulut bazasiga yuborilmaydi.

7. Administrator nazorati

Administratorlar:

log yozuvlarini kuzatishi,
IP va port sozlamalarini boshqarishi,
tarmoq ishlash holatini nazorat qilishi mumkin.
Foydalanuvchi rollari
Oddiy foydalanuvchi

Ichki tarmoqqa ulangan istalgan foydalanuvchi quyidagi imkoniyatlarga ega:

xabar yuborish va qabul qilish,
shaxsiy va umumiy chatlardan foydalanish,
fayl yuborish va yuklab olish,
Saved Messages’dan foydalanish.
Administrator

IT mutaxassis yoki tizim nazoratchisi quyidagi qo‘shimcha imkoniyatlarga ega:

loglarni kuzatish,
tarmoq parametrlarini boshqarish,
port va ulanish holatini nazorat qilish.
Tizim ishlash ssenariylari
Ssenariy A — Avtomatik topish

Dastur ishga tushishi bilan UDP Broadcast orqali lokal tarmoqdagi faol foydalanuvchilar aniqlanadi va ro‘yxatda ko‘rsatiladi.

Ssenariy B — Unicast chat

Foydalanuvchi ro‘yxatdan bitta foydalanuvchini tanlaydi va u bilan TCP orqali shifrlangan shaxsiy chat boshlaydi.

Ssenariy C — Broadcast chat

Foydalanuvchi Umumiy bo‘limi orqali barcha foydalanuvchilarga umumiy xabar yuboradi.

Ssenariy D — Shaxsiy ombor

Foydalanuvchi o‘ziga yozish orqali matnli eslatmalarni saqlaydi. Bu ma’lumotlar lokal saqlanadi va internet talab qilmaydi.

Boshqa tizim komponentlari bilan integratsiya
Windows File System

Qabul qilingan va yuborilgan fayllar operatsion tizimning lokal fayl tizimida, masalan Downloads papkasida saqlanadi.

Local Network Stack

Dastur OS’ning tarmoq drayverlari va portlari bilan socket darajasida ishlaydi.

Tashqi xizmatlar

Loyiha konsepsiyasiga ko‘ra:

Google API,
Yandex API,
bulutli chat serverlari,
yoki boshqa tashqi xizmatlar

integratsiya qilinmaydi.

Bu tizimning asosiy talabi — to‘liq avtonomlik.

Interfeys tavsifi
Dizayn

Dastur 3 panelli (3-column) zamonaviy interfeysga ega bo‘ladi:

chap panel — foydalanuvchilar va kategoriyalar,
markaziy panel — aktiv chat oynasi,
o‘ng panel — qo‘shimcha ma’lumotlar, fayllar yoki loglar.
Stil

Interfeys Dark Mode asosida yaratiladi va quyidagi uslublarga tayanadi:

Material Design elementlari,
ko‘k va quyuq kulrang ranglar palitrasi,
zamonaviy yumaloq burchakli komponentlar,
soddalik va tezkor foydalanish.
Qo‘shimcha elementlar
yuqori chap burchakda LAN Messenger logotipi;
holat va diagnostika loglari uchun monoshirift (Courier New kabi);
foydalanuvchi uchun qulay, minimalist va professional ko‘rinish.
Xavfsizlik
Shifrlash

Tarmoq orqali uzatiladigan barcha xabarlar va ma’lumotlar AES-256 asosidagi shifrlash bilan himoyalanadi.

Texnik realizatsiyada cryptography kutubxonasi va Fernet mexanizmidan foydalaniladi.

Firewall

Dastur birinchi ishga tushirilganda Windows Firewall uchun quyidagi portlarga ruxsat talab qiladi:

56565 — TCP
55555 — UDP
Maxfiylik
Chat tarixi faqat lokal xotirada saqlanadi.
Hech qanday xabar tashqi serverlarga yuborilmaydi.
Tizim internetga bog‘liq emas.
Texnik qism
Dasturlash tili
Python 3.10
Asosiy kutubxonalar
GUI: PyQt5, QtDesigner
Network: socket, threading, select
Security: cryptography (Fernet)
Arxitektura

Tizim Peer-to-Peer (P2P) arxitekturasida ishlaydi. Har bir foydalanuvchi:

ham mijoz,
ham server

rolini bajaradi.

Bu esa markaziy serverga ehtiyojni yo‘q qiladi va tizimni avtonom qiladi.

Tizim muhiti
Qo‘llab-quvvatlanadigan platforma
Windows 10 yoki undan yuqori
64-bit arxitektura
Qurilmalar
Desktop kompyuterlar
Laptop qurilmalar
Tarmoq muhiti
Ethernet
Wi-Fi
Lokal tarmoq izolatsiyasi bilan ishlash
Minimal talablar
100 MB bo‘sh joy
2 GB RAM
Ishlab chiqish bosqichlari
Sana	Bosqich
24.03.2026	UI shablonini tayyorlash va UDP Discovery qismini yozish
25.03.2026	TCP asosidagi xabar almashish logikasini ulash
26.03.2026	Shifrlash va log tizimini sozlash
27.03.2026	Yakuniy test va bug-fix ishlari
Interfeys oynalari
Login page

Tizimga kirish oynasi foydalanuvchining ismi va kerakli ulanish parametrlarini kiritish uchun xizmat qiladi.

Ishchi oyna

Asosiy oynada foydalanuvchilar ro‘yxati, chat oynasi, umumiy xabarlar bo‘limi va saved messages mavjud bo‘ladi.

Loyihaning afzalliklari
internet talab qilmaydi;
tashqi serverlarsiz ishlaydi;
lokal tarmoq uchun tezkor va xavfsiz;
yozishmalar lokal saqlanadi;
peer-to-peer arxitektura sababli markaziy nuqta yo‘q;
korporativ va yopiq tarmoqlar uchun qulay.
Kelajakdagi rivojlantirish g‘oyalari
foydalanuvchi avatarlarini qo‘llab-quvvatlash;
guruhli chatlar;
chat ichida qidiruv;
yuborilgan fayllar tarixini alohida ko‘rsatish;
xabarlarni pin qilish;
audio xabar yoki ovozli aloqa funksiyasi;
lokal bazada kengaytirilgan log tahlili.
