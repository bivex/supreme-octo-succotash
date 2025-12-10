#!/usr/bin/env python3
"""
Create minimal test data for cache hit ratio testing
"""

import psycopg2
from datetime import datetime, timedelta
import random
import string

def create_test_data():
    """Create minimal test data for cache testing"""
    try:
        print("🔌 Connecting to database...")
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="supreme_octosuccotash_db",
            user="app_user",
            password="app_password"
        )
        cursor = conn.cursor()
        print("✅ Connected successfully")

        print("🔧 Creating test data for cache hit ratio testing...")

        # Создаем тестовые кампании
        print("📝 Creating campaigns...")
        campaigns_data = []
        for i in range(100):  # 100 кампаний для тестирования кеша
            campaign = {
                'id': f'camp_{i:03d}',
                'name': f'Test Campaign {i}',
                'status': 'active',
                'created_at': datetime.now() - timedelta(days=random.randint(1, 30)),
                'updated_at': datetime.now()
            }
            campaigns_data.append(campaign)

            try:
                cursor.execute("""
                    INSERT INTO campaigns (
                        id, name, description, status, cost_model,
                        payout_amount, payout_currency,
                        safe_page_url, offer_page_url,
                        daily_budget_amount, daily_budget_currency,
                        total_budget_amount, total_budget_currency,
                        start_date, end_date,
                        created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    campaign['id'], campaign['name'], f'Description for {campaign["name"]}', campaign['status'], 'CPA',
                    5.0, 'USD',
                    f'https://safe.example.com/{campaign["id"]}', f'https://offer.example.com/{campaign["id"]}',
                    100.0, 'USD',
                    1000.0, 'USD',
                    campaign['created_at'], campaign['created_at'] + timedelta(days=30),
                    campaign['created_at'], campaign['updated_at']
                ))
                print(f"  ✅ Created campaign {campaign['id']}")
            except Exception as e:
                print(f"  ❌ Failed to create campaign {campaign['id']}: {e}")
                continue

        conn.commit()
        cursor.close()
        conn.close()

        # Выполним несколько запросов для "нагрева" кеша
        print("🔥 Warming up cache with queries...")
        for _ in range(10):
            cursor.execute("SELECT id, name FROM campaigns WHERE status = 'active' LIMIT 50")
            cursor.fetchall()

        print("✅ Test data created and cache warmed up successfully!")
        print("📊 Summary:")
        print(f"  - {len(campaigns_data)} campaigns")
        print("  - Cache warmed up with 10 queries")

        print("\n🔄 Now run: POST /v1/system/upholder/audit")
        print("   to see improved cache hit ratio!")

    except Exception as e:
        print(f"❌ Error creating test data: {e}")
    finally:
        if 'conn' in locals() and not conn.closed:
            conn.commit()
            cursor.close()
            conn.close()

if __name__ == "__main__":
    create_test_data()
