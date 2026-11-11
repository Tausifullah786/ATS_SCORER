# ATS_SCORER

Run the API from the project root in PowerShell:

```powershell
cd D:\ATS_SCORER
.\backend\venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

Configuration is loaded from the project-root `.env` and `backend/.env`.
Existing environment variables take precedence, followed by project-root values.
Set `SUPABASE_URL` and `SUPABASE_ANON_KEY` for your Supabase project. If your
project uses legacy HS256 user tokens, also set `SUPABASE_JWT_SECRET`.

Start the Streamlit frontend from the project root in a separate terminal:

```powershell
.\run_frontend.ps1
```

If your terminal is already in `D:\ATS_SCORER\frontend`, run
`..\run_frontend.ps1` instead. The launcher uses `backend/venv` explicitly and
loads the frontend's Streamlit configuration. Additional Streamlit options can
be passed through, for example `.\run_frontend.ps1 --server.port 8502`.

If you see `ModuleNotFoundError: No module named 'supabase'` after using the bare
`streamlit run` command, Streamlit may be running in a different Python
environment (such as Anaconda). Use the launcher above. If dependencies are
missing from the project environment, install them from the project root:

```powershell
.\backend\venv\Scripts\python.exe -m pip install -r requirements.txt
```

The frontend also reads the project-root `.env` and `backend/.env`, with the
same precedence. Restart Streamlit after changing these files because auth
settings are read when its auth module is first imported. For hosted Streamlit,
configure `SUPABASE_URL` and `SUPABASE_ANON_KEY` under a `[supabase]` section in
Streamlit secrets; your local `backend/.env` is not available on the hosted app.

Resume and job-description extraction use Groq. Set `GROQ_API_KEY` and choose
a chat model available to that key in `backend/.env`:

```dotenv
GROQ_MODEL=openai/gpt-oss-20b
```

The model defaults to `openai/gpt-oss-20b`. If Groq returns `model_not_found`,
check the models available to your account and update `GROQ_MODEL`. Restart
the API after editing `.env` so the new settings take effect.

Resume uploads are detected from PDF content or DOCX package structure; no
`python-magic` or native `libmagic` installation is required. Legacy `.doc`
files must be converted to PDF or DOCX.

## PDF setup on Windows

PDF exports use WeasyPrint. Its Python package also requires native Pango
libraries; `pip install` alone does not install them on Windows.

1. Install [MSYS2](https://www.msys2.org/) in its default location, `C:\msys64`.
2. Open **MSYS2 UCRT64** and run:

   ```sh
   pacman -S --needed mingw-w64-ucrt-x86_64-pango
   ```

3. Restart the backend. The PDF exporter detects the default MSYS2 runtime.

If MSYS2 is installed elsewhere, set `WEASYPRINT_DLL_DIRECTORIES` in
`backend/.env` to its `ucrt64/bin` directory before restarting the backend.
For example:

```dotenv
WEASYPRINT_DLL_DIRECTORIES=C:/msys64/ucrt64/bin
```

See the [WeasyPrint installation guide](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows)
for other operating systems. A missing renderer returns HTTP 503 with setup
instructions; it does not prevent the API from starting.

## Testing authenticated endpoints in Swagger

1. Open http://127.0.0.1:8000/docs.
2. Obtain the `access_token` from a signed-in Supabase user session.
3. Click **Authorize** and paste only the token, without `Bearer `.
4. Click **Authorize**, close the dialog, and retry **POST /api/v1/analyze-resume**.

For an existing email/password Supabase account, you can obtain a session token
by starting Python from the project root. It prompts for your password without
echoing it and prints the access token locally; do not share that token.

```powershell
.\backend\venv\Scripts\python.exe
```

Run the following in that Python session (paste each block separated by a blank
line, and press Enter to finish each block):

```python
from getpass import getpass
import httpx
from backend.core.config import SUPABASE_URL, SUPABASE_ANON_KEY

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise SystemExit("Set SUPABASE_URL and SUPABASE_ANON_KEY in backend/.env first.")

email = input("Supabase user email: ").strip()
password = getpass("Password: ")
response = httpx.post(
    f"{SUPABASE_URL.rstrip('/')}/auth/v1/token",
    params={"grant_type": "password"},
    headers={"apikey": SUPABASE_ANON_KEY},
    json={"email": email, "password": password},
    timeout=30,
)
if response.is_error:
    raise SystemExit(f"Sign-in failed (HTTP {response.status_code}). Check your account credentials and Supabase configuration.")

print(response.json()["access_token"])
```

The API expects `Authorization: Bearer <access_token>`. Project anon keys and
service-role keys are not substitutes for a user session token. A missing,
invalid, or expired token produces HTTP 401 before resume processing begins.
Sign in again to obtain a fresh token when it expires. The health endpoint at
http://127.0.0.1:8000/api/v1/health does not require authentication.
