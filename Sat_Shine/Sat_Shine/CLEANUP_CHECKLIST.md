# Repository Cleanup Checklist

## Files to Keep (Essential):
- `manage.py`
- `requirements.txt`
- `Procfile`
- `railway.json`
- `gunicorn.conf.py`
- `Sat_Shine/` (Django project folder)
- `authe/` (Authentication app)
- `main/` (Main app)
- `.env.example`
- `.env.production`
- `README.md`
- `.gitignore`

## Files to Remove:
- `env/` - Virtual environment
- `env_new/` - Additional virtual environment
- `staticfiles/` - Generated static files
- `db.sqlite3` - Local database
- `*.log` - Log files
- `osgeo4w-setup.exe` - OSGeo installer
- `__pycache__/` - Python cache
- `.env` - Local environment file

## Commands to Run:
```bash
# 1. Run the cleanup script
update_repo.bat

# 2. Or manually:
git rm -r --cached .
git add .gitignore
git add .
git commit -m "Clean repository structure"
git push origin main
```

## Repository Structure After Cleanup:
```
Sat_shine/
├── authe/                    # Authentication app
├── main/                     # Main app  
├── Sat_Shine/               # Django project
├── .env.example             # Environment template
├── .env.production          # Production env template
├── .gitignore              # Git ignore rules
├── gunicorn.conf.py        # Gunicorn config
├── manage.py               # Django management
├── Procfile                # Deployment config
├── railway.json            # Railway config
├── README.md               # Documentation
└── requirements.txt        # Dependencies
```