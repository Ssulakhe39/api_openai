#!/bin/bash

# Setup script for Aerial Image Segmentation Web Application

echo "Setting up Aerial Image Segmentation Web Application..."

# Backend setup
echo ""
echo "=== Backend Setup ==="
cd backend

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "Creating upload and mask directories..."
mkdir -p uploads masks static/images static/masks models/weights

# Copy environment file
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
fi

cd ..

# Frontend setup
echo ""
echo "=== Frontend Setup ==="
cd frontend

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install

cd ..

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Download model weights and place them in backend/models/weights/"
echo "2. Update backend/.env with correct model paths"
echo "3. Start backend: cd backend && source venv/bin/activate && uvicorn api.main:app --reload"
echo "4. Start frontend: cd frontend && npm run dev"
echo ""
