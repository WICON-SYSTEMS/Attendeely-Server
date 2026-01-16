"""
Script to seed subscription plans in the database
Run this before testing the subscription endpoint
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).resolve().parent))

from app.core.database import SessionLocal
from app.models.subscription import SubscriptionPlan
from decimal import Decimal
from datetime import datetime

def seed_subscription_plans():
    """Seed subscription plans into the database"""
    db = SessionLocal()
    
    try:
        # Check if plans already exist
        existing_plans = db.query(SubscriptionPlan).count()
        if existing_plans > 0:
            print(f"⚠️  {existing_plans} subscription plan(s) already exist. Skipping seed.")
            return
        
        # Create subscription plans
        plans = [
            {
                "name": "Free",
                "amount": Decimal("0.00"),  # 0 XAF - Free plan
                "currency": "XAF",
                "interval": "monthly",
                "is_active": True,
                "description": "Free plan for small teams (up to 10 employees)"
            },
            {
                "name": "Standard",
                "amount": Decimal("15000.00"),  # 15000 XAF/month
                "currency": "XAF",
                "interval": "monthly",
                "is_active": True,
                "description": "Standard plan for growing businesses (up to 100 employees)"
            },
            {
                "name": "Enterprise",
                "amount": Decimal("33000.00"),  # 33000 XAF/month
                "currency": "XAF",
                "interval": "monthly",
                "is_active": True,
                "description": "Enterprise plan for large organizations (unlimited employees)"
            }
        ]
        
        for plan_data in plans:
            plan = SubscriptionPlan(**plan_data)
            db.add(plan)
        
        db.commit()
        print("✅ Successfully seeded subscription plans:")
        for plan_data in plans:
            print(f"   - {plan_data['name']}: {plan_data['amount']} {plan_data['currency']}/{plan_data['interval']}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding subscription plans: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🌱 Seeding subscription plans...")
    seed_subscription_plans()
    print("✨ Done!")
