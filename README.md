# CIVIQ — National Public Grievance Portal

Poora runnable Django project — `manage.py` ke saath. Extract karo aur seedha
migrations + runserver chala sakte ho.

## Setup (Termux) — ek baar ka setup, phir baar-baar export nahi karna

```bash
cd civiq_portal

# 1. Dependencies install karo
pip install -r requirements.txt --break-system-packages

# 2. .env file banao (sirf ek baar) — isme Gmail credentials daal do
cp .env.example .env
# ab .env file ko Acode mein kholo aur CIVIQ_GMAIL_USER /
# CIVIQ_GMAIL_APP_PASSWORD ki real values bhar do

# 3. Migrations
python manage.py makemigrations civiq
python manage.py migrate

# 4. Superadmin banao
python manage.py createsuperuser

# 5. Server chalao — ab koi export command nahi chahiye
python manage.py runserver 0.0.0.0:8000
```

`.env` file `.gitignore` mein hai — GitHub pe kabhi push nahi hogi, safe hai.
Ab jab bhi terminal band-khol karoge, `settings.py` khud `.env` se values utha
lega — bas ek baar bharna hai.

## Live Deploy (Render — tumhara wahi purana RiBhay portfolio wala setup)

Render pe `.env` file nahi chalti — wahan environment variables seedhe
**dashboard mein** set karte ho, aur wo hamesha ke liye set rehte hain (kabhi
export nahi karna padta):

1. GitHub pe is project ko push karo (jaisa tum RiBhay portfolio ke liye
   karte ho — Termux se `git add`, `git commit`, `git push`).

2. Render pe naya **Web Service** banao, apna GitHub repo connect karo.

3. **Build Command:**
   ```
   pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
   ```

4. **Start Command:**
   ```
   gunicorn civiq_portal.wsgi:application
   ```

5. Render dashboard mein **Environment → Add Environment Variable** karke
   ye sab ek-ek baar daal do (hamesha ke liye save rahenge):

   | Key | Value |
   |---|---|
   | `CIVIQ_GMAIL_USER` | tumhara Gmail address |
   | `CIVIQ_GMAIL_APP_PASSWORD` | wahi 16-digit App Password |
   | `DJANGO_SECRET_KEY` | koi bhi lamba random string |
   | `DJANGO_DEBUG` | `False` |
   | `DJANGO_ALLOWED_HOSTS` | `yourapp.onrender.com` |

6. Deploy karo — bas. Ab har complaint pe email automatically jaati rahegi,
   bina kisi terminal command ke.

**Zaroori warning:** Render ke **free tier** ka disk *ephemeral* hota hai —
matlab `db.sqlite3` (saari complaints) aur uploaded photos har redeploy/restart
pe **delete ho jaate hain**. Testing/demo ke liye theek hai, lekin real
citizens se live complaints lene ke liye ya to Render ka free **PostgreSQL**
add-on use karna hoga ya paid plan ka persistent disk — bata dena, main wo
bhi wire kar dunga.

## Django Admin mein ab sirf ye baaki bacha hai (Sectors/Departments auto-seeded hain)

1. **OfficerProfile** — kisi existing User (pehle Django Admin mein User banao)
   ko officer bana ke department assign karo.

2. **TeamMember** — apna aur Riya ka entry `is_ribhay_credit=True` ke saath
   daalo taaki "Engineering Credits" section pe RiBhay Studio dikhe.

3. **StaticPage** — Citizen Charter, FAQs, Privacy Policy, About Us
   (`/page/<slug>/` pe accessible, footer mein bhi auto-list ho jaayenge).

## Pre-Loaded Categories & Government Contacts (Auto-Seeded)

Tumhe manually kuch nahi daalna — `migrate` chalate hi ye sab automatically
database mein aa jaayega:

**13 Categories (Sectors):** Potholes & Road Damage, Garbage Collection,
Street Lighting, Stray Animals, Illegal Encroachment, Water Supply,
Sewage & Drainage, Power Outage & Faults, Electricity Billing, Traffic
Signal Fault, Illegal Parking, Mosquito & Disease Control, Hospital
Sanitation.

**5 Departments**, har ek real publicly-listed Lucknow government contact
ke saath:

| Department | Email | Helpline |
|---|---|---|
| Nagar Nigam Lucknow | nnlko@nic.in | 1533 |
| Jal Sansthan / Jalkal Vibhag | nnlko@nic.in (Nagar Nigam ka hi wing) | 8177054003 |
| MVVNL (Power/Discom) | cccmvvnl1912@gmail.com | 1912 |
| Traffic Directorate, UP Police | dirtraffic-up@nic.in | 1073 |
| CMO Lucknow (Public Health) | cmolko@gmail.com | 0522-2622080 |

**Zaroori disclaimer:** Ye contacts publicly-listed official sources se
liye gaye hain (Nagar Nigam/UP Police/MVVNL ki apni websites), lekin
government contacts time ke saath badalte rehte hain. Real complaints
bhejne se pehle Django Admin mein jaake har Department ka `contact_email`
ek baar khud verify/confirm kar lena — especially Jal Sansthan ka, jiska
koi alag public email nahi mila (isliye Nagar Nigam ka hi email daala hai).
Agar tumhe koi department ka zyada accurate/current email pata ho, Admin
mein jaake update kar dena — baaki sab kaam automatic rahega.



Jab citizen complaint lodge karta hai aur NLP engine se department detect ho
jaata hai, to us **Department.contact_email** pe automatically ek email chali
jaati hai — sector, priority, citizen details, location, aur photo evidence
(attachment ke saath).

Ye chalane ke liye Gmail App Password chahiye (2-Step Verification account
mein on hona zaroori hai): https://myaccount.google.com/apppasswords

```bash
export CIVIQ_GMAIL_USER="yourteam@gmail.com"
export CIVIQ_GMAIL_APP_PASSWORD="xxxxxxxxxxxxxxxx"   # 16-char app password, spaces hata dena
python manage.py runserver 0.0.0.0:8000
```

Ye env variables set nahi karoge to emails console mein hi print hongi (crash
nahi honge) — taaki bina Gmail set kiye bhi form test kar sako.

**Zaroori:** Django Admin mein har **Department** ka `contact_email` field
bharo — jis department ka email khaali hoga, uske liye mail skip ho jaayegi
(citizen ki submission fir bhi safal rahegi, sirf log mein warning aayega).



```
civiq_portal/
├── manage.py
├── requirements.txt
├── civiq_portal/          # project package (settings, root urls)
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── civiq/                 # the app
    ├── models.py
    ├── admin.py
    ├── views.py
    ├── urls.py
    ├── apps.py
    ├── context_processors.py
    ├── utils/nlp_engine.py
    ├── migrations/
    ├── templates/
    └── static/
```

## Notes

- SQLite database (`db.sqlite3`) use ho raha hai — zero extra setup, Termux-friendly.
  Migrate karte hi wo file auto-create ho jaayegi.
- Photo uploads (evidence, resolution proof, officer/team photos) ke liye Pillow
  zaroori hai — `requirements.txt` mein already hai.
- Termux FUSE `flock()` fix `settings.py` ke end mein already merged hai — agar
  `/sdcard` par project rakhoge to upload crash nahi hoga.
- NLP engine dependency-free hai — koi extra pip install nahi chahiye.
- Officer dashboard sirf un complaints ko dikhata hai jo `assigned_officer`
  field mein explicitly assign hain. Abhi auto-assignment sirf department set
  karta hai, officer nahi — agar chaho to lodge_complaint view mein department
  ke first active officer ko bhi auto-assign karwa sakta hoon, bata dena.
- Production deploy (Render, etc.) ke liye `settings.py` mein `SECRET_KEY`,
  `DEBUG=False`, `ALLOWED_HOSTS`, aur WhiteNoise add karna hoga — abhi ye
  local-dev-ready config hai.
