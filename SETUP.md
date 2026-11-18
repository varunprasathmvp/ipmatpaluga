# IPMAT PALUGA — Android-friendly setup

## What's included
- `app.py`: Streamlit application
- `requirements.txt`: Python dependencies
- `supabase_schema.sql`: database tables and privacy rules

## Step 1 — Create a Supabase project
1. Open https://supabase.com and create a free account.
2. Create a new project. Save its database password somewhere safe.
3. Open **SQL Editor** in the project dashboard.
4. Paste all of `supabase_schema.sql` and run it.
5. Open **Project Settings → API** (or API Keys).
6. Copy the Project URL and the `anon` / publishable key. Never use or share the `service_role` / secret key.

## Step 2 — Put the code on GitHub using Android
1. Open https://github.com and create a free account.
2. Create a repository named `ipmat-paluga`.
3. Upload `app.py` and `requirements.txt` from this ZIP.
4. Upload `supabase_schema.sql` too, for your reference.

## Step 3 — Deploy on Streamlit
1. Open https://share.streamlit.io and sign in with GitHub.
2. Choose **Create app** and select your `ipmat-paluga` repository.
3. Set the main file path to `app.py`.
4. Before deploying, open **Advanced settings → Secrets**.
5. Add the following TOML, replacing the example values:

[supabase]
url = "https://YOUR-PROJECT-ID.supabase.co"
anon_key = "YOUR_SUPABASE_ANON_OR_PUBLISHABLE_KEY"

6. Deploy the app.

## Step 4 — Test
1. Open your app URL.
2. Create a test account with an email you control.
3. Sign in and add a sample mock.
4. Check Dashboard and Mock History.

## Important notes
- Do not put Supabase keys in `app.py` or publish them in GitHub. Only the anon/publishable key belongs in Streamlit secrets; never use the service-role key.
- Supabase Row Level Security policies in the SQL file restrict records to their owner.
- For public student use, test signup, email confirmation, password recovery, RLS and data deletion before announcing the app.
- This is an MVP. It currently supports mock entry, question records, CSV import, score trends and topic accuracy. It does not yet calculate percentile, rank, predicted admission chances, or parse proprietary mock-provider reports automatically.
- CSV upload currently imports question-level records. Excel upload and provider-specific file parsing can be added in a later version.
