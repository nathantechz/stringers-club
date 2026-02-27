# StringerS Badminton Club — Admin App

Streamlit + Supabase admin panel for managing attendance, payments, player profiles, analytics and expenditure.

## Pages
1. Mark Attendance
2. Player Profiles
3. Record Payment
4. Manage Players
5. Monthly Settlement
6. Analytics
7. Expenditure

## Local setup
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in Supabase credentials
streamlit run app.py
```

## Streamlit Cloud deployment
Add the following secrets via **App Settings → Secrets**:
```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-service-role-key"
```
