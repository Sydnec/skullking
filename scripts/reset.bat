@echo off

for /d /r %%i in (__pycache__) do (
    if exist "%%i" (
        echo Suppression de "%%i"
        rd /s /q "%%i"
    )
)

if exist db.sqlite3 (
    echo Suppression de db.sqlite3
    del /f /q db.sqlite3
)

del /q myapp\migrations\00*

python manage.py makemigrations myapp
python manage.py migrate
python manage.py loaddata users

.\scripts\run.bat
