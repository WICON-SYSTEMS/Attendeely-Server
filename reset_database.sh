#!/bin/bash

echo "🗄️  Attendeely Database Reset Tool"
echo "===================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please create a virtual environment first:"
    echo "  python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please create .env file from .env.example"
    exit 1
fi

echo "⚠️  WARNING: This will DELETE ALL DATA from the database!"
echo ""
echo "Options:"
echo "  1) Reset database (drop all tables and recreate)"
echo "  2) Reset database + run migrations (recommended)"
echo "  3) Cancel"
echo ""

read -p "Choose an option (1-3): " option

case $option in
    1)
        echo ""
        echo "🔄 Resetting database..."
        python reset_database.py
        ;;
    2)
        echo ""
        echo "🔄 Resetting database..."
        python reset_database.py
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "🔄 Running migrations..."
            alembic stamp head
            echo ""
            echo "✅ Database reset and migrations complete!"
            echo ""
            echo "Current migration status:"
            alembic current
        fi
        ;;
    3)
        echo ""
        echo "✅ Cancelled. No changes made."
        exit 0
        ;;
    *)
        echo ""
        echo "❌ Invalid option. Cancelled."
        exit 1
        ;;
esac
