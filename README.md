📌 SLHTON – Readme / Developer Handbook

Telegram On-Chain Demo (SLH Token) – Current System State & Roadmap
Last updated: 15/11/2025

🧩 1. מהו הפרויקט?

SLHTON הוא בוט טלגרם + API (FastAPI) המדמה מערכת טוקן פנימית:

רישום משתמשים לפי Telegram ID

יצירת ארנק דמו לכל משתמש

יתרה + העברות (Mock)

Faucet

הזמנות (Orderbook)

היסטוריית טרנזאקציות

ניהול ע"י Admin

בסיס נתונים PostgreSQL אמיתי (במקום SQLite)

המערכת היא שלב ראשוני לקראת
האקדמיה / ה־SLH Shop / ה־Gateway / ה־Token Economy המלאה.

🚀 2. מה עשינו עד עכשיו (סיכום מלא של כל הפעולות)
✔ שלב א' – בניית פרויקט SLHTON

יצירת פרויקט FastAPI תקני.

חיבור ל־python-telegram-bot v20.

בניית מבנה תיקיות מודולרי:
/app/models.py / /services/ / /telegram/handlers.py / /main.py.

✔ שלב ב' – החלפת SQLite → PostgreSQL
מה נעשה בפועל:

מחיקת database ישנה ויצירת Postgres חדש (Postgres-WXop).

חיבור מחדש עם ENV:

DATABASE_URL=postgresql://postgres:xxxx@host/railway


הוספת לוגיקה ב־app/db.py ליצירת טבלאות אוטומטית.

✔ שלב ג' – בניית המודלים מחדש

הוגדרו מחדש:

User

Wallet

Tx

Transfer

Order

כל המודלים עברו יישור מלא עם PostgreSQL:
BIGINT ל־telegram_id, Decimal ל־balance, טבלאות יחסים תקניות.

✔ שלב ד' – בניית השירותים (services)

users_service.get_or_create_user

wallet_service.get_or_create_wallet

wallet_service.deposit / faucet / send

orders_service.create_order / list_open_orders

✔ שלב ה' – חיבור טלגרם + Webhook תקינים

ה־Webhook נקבע נכון בריילווי.

הבוט מגיב לכל הפקודות.

/start, /whoami, /wallet – תקין.

✔ שלב ו' – איתור ותיקון באגים

תיקון בעיית token_symbol (הוספת attribute).

תיקון בעיית Order.is_open.

תיקון בעיית Tx שלא היה קיים.

תיקון סכימה מלאה.

✔ שלב ז' – הכנסת WALLET_MASTER_KEY

כרגע משמש ליצירת “כתובת ארנק” דמו:

SLH-<telegram_id>-SLH


בהמשך נחליף למנגנון BSC/TON אמיתי.

📌 3. המצב הנוכחי – State Snapshot (15/11/2025)
✔ FastAPI / Telegram – ONLINE

Webhook תקין.

הבוט מגיב לכל הפקודות ללא קריסת שירות.

✔ משתמשים – תקין

/start יוצר User חדש ב־Postgres.

/whoami מתפקד.

telegram_id כבר BIGINT ולא יגרום בעיה.

✔ ארנקים – עובד חלקית

יצירת ארנק: תקין.

הצגת יתרה: תקין.

⚠ Faucet – לא עובד

בגלל:

TypeError: unsupported operand type(s) for +=: 'decimal.Decimal' and 'float'


➡ צריך להמיר סכום ל־Decimal לפני פעולת deposit.

בעיה ידועה וקטנה.

✔ ה־DB – PostgreSQL תקין

בטבלאות קיימות:

users

wallets

txs

transfers

orders

הכול נוצר אוטומטית אחרי שינויי ה־init_db.

✔ החיבור בין המודלים לשירותים – תקין
❗ 4. בעיות ידועות כרגע (TODO Fixes)
1) Faucet / Deposit המטפל ב־Decimal + float

פתרון מיידי בהמשך:

from decimal import Decimal
wallet.balance += Decimal(str(amount))

2) יתרה מוצגת כ־0E-8

נגרם מסוג Decimal.
נציג בפורמט רגיל (format_decimal).

3) העברות / הזמנות – טרם נוסה באופן מלא

דורש בדיקת קונסיסטנטיות ו־commit בכל פעולה.

4) לוג שקט – אין error handlers

נוסיף בהמשך מערכת exceptions גלובלית.

🛠 5. מבנה הפרויקט (נכון לעכשיו)
/app
   /telegram
       handlers.py
   /services
       users.py
       wallet.py
       orders.py
   models.py
   db.py
   main.py

requirements.txt
Dockerfile

🔑 6. המשתנים על השרת (Railway)
חובה:
TELEGRAM_BOT_TOKEN=xxxxxxxx
WEBHOOK_URL=https://slhton-production.up.railway.app/telegram/webhook
DATABASE_URL=postgresql://postgres:xxxx@containers-us-westxx...
WALLET_MASTER_KEY=SLH_SUPER_SECRET_001

אופציונלי:
FAUCET_AMOUNT=1
TOKEN_SYMBOL=SLH

🗺 7. מפת דרכים קדימה (Roadmap)
✔ שלב 1 (מיידי) – תיקון ה־Decimal

לתקן faucet/deposit

להחזיר יתרה נורמלית (מספר רגיל)

✔ שלב 2 – העברות אמיתיות

/send עם היסטוריית Tx

שמירה בטבלת transfers

✔ שלב 3 – Orderbook מלא

/order buy|sell token amount price

מנוע התאמת עסקאות

לוגיקה של fill & partial fill

✔ שלב 4 – בניית API חיצוני

/wallet/balance

/wallet/send

/orders/open

✔ שלב 5 – חיבור ל־SLH אמיתי (BSC / TON)

הפיכת המודל מדמו → אמת

Web3 / TonClient

חתימה חמה/קרה עם Signer Service

✔ שלב 6 – Sela Wallet / Gateway / NFT Game

זה החזון הסופי:

Marketplace

Shops

Referral System

NFT Shops

Academy levels

CRM internal

Admin dashboard

App Android (APK)

אנחנו בשלבי התשתית הראשוניים.

🧭 8. איך להמשיך מכאן בשיחה הבאה?

כשאתה פותח איתי שיחה חדשה:

שלח לי רק:
SLHTON – Continue


ושם קוד הזה:

- DATABASE_URL: מוגדר
- Postgres: פעיל (Postgres-WXop)
- טבלאות: users/wallets/txs/transfers/orders קיימות
- Faucet: לא עובד (Decimal issue)
- יתרה: מוצגת כ- 0E-8


ואז:

Tasks for next session:
1. Fix Decimal in faucet/deposit
2. Format wallet balance properly
3. Test end-to-end: faucet → deposit → wallet → send
4. Validate Tx table writes


ואנחנו נמשיך מאותה נקודה בדיוק.
