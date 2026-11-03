# JAVA'S RESTAURANT — Flask + PostgreSQL starter

Mobile-friendly Somali-first website and booking starter for a hospital meal service in Hyderabad.

**Business model:** each booking request is for a 30-day service covering breakfast, lunch and dinner. There is no fixed public price. After a booking is submitted, the restaurant contacts the customer by phone to agree the price and confirm details.

## Pages
Home, Services, About Us, Menu, Contact, Register, Login, Booking, Customer Account, Admin Dashboard.

## 1. Run locally (Windows PowerShell)
Install Python 3.11+ and PostgreSQL. Create a database named `javas_restaurant`.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set `DATABASE_URL`, `SECRET_KEY`, `ADMIN_EMAIL`, and `ADMIN_PASSWORD`.
Then run:

```powershell
flask --app app init-db
python app.py
```
Open http://127.0.0.1:5000

## 2. Add images
Replace files in `static/images/` with licensed images or AI-generated assets:
- hero.jpg
- meal1.jpg
- meal2.jpg
- meal3.jpg

## 3. GitHub
Create a private GitHub repository, then:

```powershell
git init
git add .
git commit -m "Initial Java's Restaurant app"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

Never commit `.env` or secrets.

## 4. Deploy
Vercel can run Python serverless functions, but this Flask app must be tested against Vercel's function limits and request lifecycle. Set the environment variables in Vercel Project Settings. Use a managed PostgreSQL provider with SSL and a serverless-compatible connection strategy. For a continuously running Flask/Gunicorn server, use a Python host such as Render or Railway instead; keep the frontend on Vercel if desired.

## 5. WhatsApp Cloud API
Create/configure a Meta WhatsApp Business app. Set `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, and `ADMIN_WHATSAPP_NUMBER` in the hosting provider's environment settings. Phone numbers must be in international format without `+` for Cloud API. Production messaging may require approved templates and user opt-in; this starter sends simple text notifications only.

## Important before real launch
- Add CSRF protection, rate limiting, email/phone verification, password reset, audit logs, backups, and stronger admin authorization.
- Use a proper production admin account and rotate all secrets.
- Validate customer consent before WhatsApp notifications.
- Do not promise a medically suitable diet. Confirm special diets, allergies, and clinical restrictions with the patient's doctor/dietitian before cooking.
- Add the negotiated 30-day package price to the booking/admin workflow, delivery fees if applicable, payment gateway integration, refund rules, and cancellation policy.
- Existing PostgreSQL databases need a schema migration after adding the `package_days` and `meals_included` booking columns. For a fresh development database, run `flask --app app init-db`.
- Payment records in this starter are manual records only; it does not process payments.
