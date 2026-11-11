$ErrorActionPreference = 'Stop'

# Use the project's Python even when Anaconda or another Python is on PATH.
$projectPython = Join-Path $PSScriptRoot 'backend\venv\Scripts\python.exe'
$frontendDirectory = Join-Path $PSScriptRoot 'frontend'

if (-not (Test-Path -LiteralPath $projectPython -PathType Leaf)) {
    throw 'Project environment not found. From the project root, run: python -m venv backend/venv, then .\backend\venv\Scripts\python.exe -m pip install -r requirements.txt'
}

# Streamlit reads .streamlit/config.toml relative to the working directory.
Push-Location -LiteralPath $frontendDirectory
try {
    & $projectPython -m streamlit run streamlit_app.py @args
    if ($LASTEXITCODE -ne 0) {
        throw "Streamlit exited with code $LASTEXITCODE. See the error above for details."
    }
}
finally {
    Pop-Location
}
