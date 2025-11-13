# SLHTON – Telegram TON Trade Demo (Enterprise-Ready Skeleton)

זהו פרויקט SLHTON נקי ומודרני, מוכן לפריסה על Railway, שמחבר:
- בוט טלגרם (Webhook)
- API מבוסס FastAPI
- מנגנון ארנק והזמנות (Orderbook) פנימי (In-Memory/SQLite)

## מבנה הפרויקט

```text
.
├── app
│   ├── __init__.py
│   ├── main.py              # FastAPI app + /health + /meta + /telegram/webhook
│   ├── config.py            # טעינת משתני סביבה
│   ├── db.py                # SQLAlchemy + SQLite
│   ├── models.py            # User, Wallet, Order, Tx
│   ├── services
│   │   ├── __init__.py
│   │   ├── users.py
│   │   ├── wallet.py
│   │   └── orders.py
│   └── telegram
│       ├── __init__.py
│       ├── bot.py           # יצירת Application + Handlers
│       └── handlers.py      # פקודות טלגרם
├── init_webhook.py          # קובץ הרצה ראשי ל-Railway (סט Webhook + מפעיל Uvicorn)
├── requirements.txt
├── runtime.txt
├── Dockerfile
├── .env.example
└── README.md
```

## הרצה מקומית

```bash
python -m venv .venv
source .venv/bin/activate  # ב-Windows: .venv\Scripts\activate
pip install -r requirements.txt

# צור קובץ .env מקומי
copy .env.example .env  # ב-Windows
# או:
cp .env.example .env    # בלינוקס/מק

# הרצת המערכת (סט Webhook + API)
python init_webhook.py
```

לאחר ההרצה, גש ל:
- http://127.0.0.1:5000/health – בדיקת בריאות
- http://127.0.0.1:5000/meta – מטא-דאטה

## פריסה ב-Railway

1. העלה את כל קבצי הפרויקט ל-GitHub בריפו שמחובר ל-Railway (לדוגמה: osifeu-prog/SLHTON).
2. ב-Railway, ודא:
   - Root Directory ריק (כלומר: הפרויקט בשורש הריפו).
   - Start Command: python init_webhook.py
   - Target port: 5000
3. הגדר את משתני הסביבה (Variables) לפי .env.example.
4. בצע Deploy חדש.

## שימוש בפקודות טלגרם

הפקודות הנתמכות כרגע:
- /start – ברכת פתיחה, יצירת משתמש בבסיס הנתונים
- /whoami – פרטי המשתמש
- /wallet – יצירת ארנק והצגת יתרה
- /deposit <amount> – הפקדת טוקנים דמו לארנק
- /order <buy|sell> <token> <amount> <price> – יצירת הזמנה
- /orders – צפייה בהזמנות פתוחות
- /faucet – קבלת טוקנים חינמיים
- /adminpanel – לפקודות אדמין (ID חייב להיות ב-ADMIN_OWNER_IDS)

> שים לב: בשלב זה החיבור לבלוקצ'יין TON הוא לוגי/דמו בלבד. ניתן להחליף את המימוש ב-`services/wallet.py`
> בחיבור אמיתי ל-SDK של TON.
