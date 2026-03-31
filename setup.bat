@echo off
REM Setup script for Aerial Image Segmentation Web Application (Windows)

echo Setting up Aerial Image Segmentation Web Application...

REM Backend setup
echo.
echo === Backend Setup ===
cd backend

REM Create virtual environment
echo Creating Python virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing Python dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Create necessary directories
echo Creating upload and mask directories...
if not exist uploads mkdir uploads
if not exist masks mkdir masks
if not exist static\images mkdir static\images
if not exist static\masks mkdir static\masks
if not exist models\weights mkdir models\weights

REM Copy environment file
if not exist .env (
    echo Creating .env file from .env.example...
    copy .env.example .env
)

cd ..

REM Frontend setup
echo.
echo === Frontend Setup ===
cd frontend

REM Install Node.js dependencies
echo Installing Node.js dependencies...
call npm install

cd ..

echo.
echo === Setup Complete ===
echo.
echo Next steps:
echo 1. Download model weights and place them in backend\models\weights\
echo 2. Update backend\.env with correct model paths
echo 3. Start backend: cd backend ^&^& venv\Scripts\activate ^&^& uvicorn api.main:app --reload
echo 4. Start frontend: cd frontend ^&^& npm run dev
echo.
pause
