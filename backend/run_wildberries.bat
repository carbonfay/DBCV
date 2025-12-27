"@echo off
echo ============================================================
echo Wildberries Integration Test
echo ============================================================
echo.

cd /d %~dp0
python run_wildberries_test.py

echo.
echo ============================================================
echo Test completed. Press any key to exit...
pause >nul
"