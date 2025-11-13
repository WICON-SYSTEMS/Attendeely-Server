"""
Database Reset Script
=====================
This script will DELETE ALL DATA from the database.
Use with caution! Only for development/testing.

Usage:
    python reset_database.py
"""

import sys
from sqlalchemy import text
from app.core.database import engine, Base
from app.models import User, OTP, Organization
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def confirm_reset():
    """Ask for user confirmation before wiping data"""
    print("\n" + "="*60)
    print("⚠️  WARNING: DATABASE RESET")
    print("="*60)
    print("\nThis will DELETE ALL DATA from the following tables:")
    print("  - organizations")
    print("  - otps")
    print("  - users")
    print("\n❌ This action CANNOT be undone!")
    print("="*60)
    
    response = input("\nType 'DELETE ALL DATA' to confirm: ")
    
    if response != "DELETE ALL DATA":
        print("\n✅ Reset cancelled. No data was deleted.")
        return False
    
    # Double confirmation
    response2 = input("\nAre you absolutely sure? Type 'YES' to proceed: ")
    
    if response2 != "YES":
        print("\n✅ Reset cancelled. No data was deleted.")
        return False
    
    return True


def reset_database():
    """Drop all tables and recreate them"""
    try:
        logger.info("Starting database reset...")
        
        # Drop all tables
        logger.info("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        logger.info("✅ All tables dropped successfully")
        
        # Recreate all tables
        logger.info("Recreating all tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ All tables recreated successfully")
        
        # Verify tables exist
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result]
            
            logger.info(f"\n📊 Database tables after reset:")
            for table in tables:
                logger.info(f"  ✓ {table}")
        
        print("\n" + "="*60)
        print("✅ DATABASE RESET COMPLETE")
        print("="*60)
        print("\nThe database has been wiped clean.")
        print("All tables have been recreated with no data.")
        print("\nYou can now:")
        print("  1. Start the server: ./dev.sh")
        print("  2. Create a new admin account")
        print("  3. Test the application from scratch")
        print("="*60 + "\n")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error resetting database: {str(e)}")
        return False


def main():
    """Main function"""
    print("\n🗄️  Attendeely Database Reset Tool\n")
    
    # Check if user wants to proceed
    if not confirm_reset():
        sys.exit(0)
    
    # Reset the database
    success = reset_database()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
