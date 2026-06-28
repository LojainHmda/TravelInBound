@echo off
cd /d C:\Users\user\TravelInBound-main
"C:\Users\user\.cursor\projects\empty-window\TravelInBound\.venv\Scripts\python.exe" -c "from app import create_app; app = create_app(); app.run(host='0.0.0.0', port=3000, debug=False)"
pause
