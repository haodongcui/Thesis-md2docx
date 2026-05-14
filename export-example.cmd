@echo off
setlocal

pushd "%~dp0"

if exist ".venv\Scripts\activate.bat" (
  call ".venv\Scripts\activate.bat"
)

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 "md2docx.py" docx "example\thesis-demo.md" "example\thesis-demo.docx" --profile xju-undergraduate-thesis
) else (
  python "md2docx.py" docx "example\thesis-demo.md" "example\thesis-demo.docx" --profile xju-undergraduate-thesis
)

set STATUS=%errorlevel%
if %STATUS%==0 echo Generated: %cd%\example\thesis-demo.docx

popd
exit /b %STATUS%
