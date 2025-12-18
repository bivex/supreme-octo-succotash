
# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:12:29
# Last Updated: 2025-12-18T12:12:29
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
PostgreSQL Bulk Loading and Prepared Statements Demo
Shows efficient data loading techniques and query optimization
"""

import psycopg2
import time
import csv
import io
from datetime import datetime, timedelta
import random

class BulkLoadingDemo:
    def __init__(self):
        self.conn_params = {
            'host': 'localhost',
            'port': 5432,
            'database': 'supreme_octosuccotash_db',
            'user': 'app_user',
            'password': 'app_password'
        }

    def generate_test_data_csv(self, num_rows=10000):
        """Generate test CSV data in memory."""
        csv_data = io.StringIO()
        writer = csv.writer(csv_data)

        # Write header
        writer.writerow(['id', 'campaign_id', 'user_id', 'ip_address', 'user_agent',
                        'click_url', 'referer', 'created_at', 'is_valid'])

        # Generate test data
        campaign_ids = [f'test_campaign_{i}' for i in range(10)]
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]

        base_time = datetime.now() - timedelta(days=7)

        for i in range(num_rows):
            writer.writerow([
                f'bulk_click_{i}',
                random.choice(campaign_ids),
                f'user_{random.randint(1, 10000)}',
                f'192.168.{random.randint(0, 255)}.{random.randint(1, 255)}',
                random.choice(user_agents),
                f'https://example.com/click/{i}',
                f'https://google.com/search?q=test{i}',
                (base_time + timedelta(seconds=random.randint(0, 604800))).isoformat(),
                random.choice([True, True, True, False])  # 75% valid
            ])

        csv_data.seek(0)
        return csv_data

    def demonstrate_copy_bulk_loading(self):
        """Demonstrate bulk loading with COPY command."""
        print("📤 COPY Command Bulk Loading Demo")
        print("=" * 50)

        num_rows = 5000
        csv_data = self.generate_test_data_csv(num_rows)

        conn = psycopg2.connect(**self.conn_params)
        cursor = conn.cursor()

        print(f"Loading {num_rows} rows using COPY...")

        # Bulk load with COPY
        start_time = time.time()

        try:
            cursor.copy_expert("""
                COPY clicks (
                    id, campaign_id, user_id, ip_address, user_agent,
                    click_url, referer, created_at, is_valid
                )
                FROM STDIN WITH CSV HEADER
            """, csv_data)

            conn.commit()
            copy_time = time.time() - start_time

            print("✅ COPY loading completed"            print(".2f"            print(".0f"
        except Exception as e:
            print(f"❌ COPY failed: {e}")
            conn.rollback()
            copy_time = 0

        conn.close()
        return copy_time

    def demonstrate_individual_inserts(self, num_rows=100):
        """Demonstrate loading with individual INSERTs for comparison."""
        print(f"\n📝 Individual INSERTs Demo ({num_rows} rows)")
        print("=" * 50)

        csv_data = self.generate_test_data_csv(num_rows)
        csv_data.readline()  # Skip header
        reader = csv.reader(csv_data)

        conn = psycopg2.connect(**self.conn_params)
        cursor = conn.cursor()

        print(f"Loading {num_rows} rows using individual INSERTs...")

        start_time = time.time()
        inserts_count = 0

        try:
            for row in reader:
                if len(row) >= 9:  # Ensure we have all required columns
                    cursor.execute("""
                        INSERT INTO clicks (
                            id, campaign_id, user_id, ip_address, user_agent,
                            click_url, referer, created_at, is_valid
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, row[:9])
                    inserts_count += 1

            conn.commit()
            insert_time = time.time() - start_time

            print("✅ Individual INSERTs completed"            print(".2f"            print(".0f"
        except Exception as e:
            print(f"❌ INSERTs failed: {e}")
            conn.rollback()
            insert_time = 0
            inserts_count = 0

        conn.close()
        return insert_time, inserts_count

    def demonstrate_prepared_statements_bulk(self):
        """Demonstrate bulk operations with prepared statements."""
        print("\n🔧 Prepared Statements Bulk Operations")
        print("=" * 50)

        num_rows = 2000
        csv_data = self.generate_test_data_csv(num_rows)
        csv_data.readline()  # Skip header
        reader = csv.reader(csv_data)

        conn = psycopg2.connect(**self.conn_params)
        cursor = conn.cursor()

        # Prepare the INSERT statement
        cursor.execute("""
            PREPARE bulk_click_insert AS
            INSERT INTO clicks (
                id, campaign_id, user_id, ip_address, user_agent,
                click_url, referer, created_at, is_valid
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """)

        print(f"Loading {num_rows} rows using prepared statements...")

        start_time = time.time()
        inserts_count = 0

        try:
            # Execute prepared statement for each row
            for row in reader:
                if len(row) >= 9:
                    cursor.execute("EXECUTE bulk_click_insert (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                                 row[:9])
                    inserts_count += 1

            conn.commit()
            prep_time = time.time() - start_time

            print("✅ Prepared statements completed"            print(".2f"            print(".0f"
        except Exception as e:
            print(f"❌ Prepared statements failed: {e}")
            conn.rollback()
            prep_time = 0
            inserts_count = 0

        # Clean up prepared statement
        cursor.execute("DEALLOCATE bulk_click_insert")
        conn.close()
        return prep_time, inserts_count

    def compare_loading_methods(self):
        """Compare different loading methods performance."""
        print("\n📊 Bulk Loading Methods Comparison")
        print("=" * 50)

        methods = []

        # Test COPY method
        print("Testing COPY method...")
        copy_time = self.demonstrate_copy_bulk_loading()
        if copy_time > 0:
            methods.append(('COPY', 5000, copy_time))

        # Test Prepared Statements
        print("\nTesting Prepared Statements...")
        prep_time, prep_count = self.demonstrate_prepared_statements_bulk()
        if prep_time > 0:
            methods.append(('Prepared', prep_count, prep_time))

        # Test Individual INSERTs
        print("\nTesting Individual INSERTs...")
        insert_time, insert_count = self.demonstrate_individual_inserts(200)  # Smaller sample
        if insert_time > 0:
            # Extrapolate for fair comparison (200 inserts took insert_time, so 5000 would take ~125x)
            estimated_time = (insert_time / insert_count) * 5000
            methods.append(('Individual', 5000, estimated_time))

        # Print comparison table
        if methods:
            print("\n🏆 Performance Comparison (for 5000 rows):")
            print("Method".ljust(12), "Time".ljust(10), "Rows/sec".ljust(10), "vs COPY")
            print("-" * 55)

            # Find COPY baseline
            copy_method = next((m for m in methods if m[0] == 'COPY'), None)
            copy_time = copy_method[2] if copy_method else 1

            for method, rows, time_taken in methods:
                if time_taken > 0:
                    rows_per_sec = rows / time_taken
                    speedup = copy_time / time_taken if method != 'COPY' else 1.0
                    print("<12")

        print("\n💡 Bulk Loading Best Practices:")
        print("• Use COPY for maximum performance")
        print("• Validate data before loading")
        print("• Use transactions for consistency")
        print("• Consider temporary tables for staging")
        print("• Monitor disk I/O during loading")

    def demonstrate_error_handling(self):
        """Demonstrate error handling in bulk operations."""
        print("\n🛡️  Error Handling in Bulk Operations")
        print("=" * 50)

        # Create CSV with some invalid data
        csv_data = io.StringIO()
        writer = csv.writer(csv_data)

        writer.writerow(['id', 'campaign_id', 'user_id', 'ip_address', 'user_agent',
                        'click_url', 'referer', 'created_at', 'is_valid'])

        # Add some valid and invalid rows
        for i in range(10):
            if i == 5:  # Make one row invalid
                writer.writerow([
                    None,  # Invalid: NULL id
                    f'campaign_{i}',
                    f'user_{i}',
                    f'192.168.1.{i}',
                    'Test Agent',
                    f'https://example.com/{i}',
                    'https://referer.com',
                    datetime.now().isoformat(),
                    True
                ])
            else:
                writer.writerow([
                    f'error_test_{i}',
                    f'campaign_{i}',
                    f'user_{i}',
                    f'192.168.1.{i}',
                    'Test Agent',
                    f'https://example.com/{i}',
                    'https://referer.com',
                    datetime.now().isoformat(),
                    True
                ])

        csv_data.seek(0)

        conn = psycopg2.connect(**self.conn_params)
        cursor = conn.cursor()

        print("Testing COPY with error handling...")

        try:
            # This will fail due to NULL id constraint
            cursor.copy_expert("""
                COPY clicks (
                    id, campaign_id, user_id, ip_address, user_agent,
                    click_url, referer, created_at, is_valid
                )
                FROM STDIN WITH CSV HEADER
            """, csv_data)

            conn.commit()
            print("❌ Unexpected: COPY succeeded (should have failed)")

        except psycopg2.Error as e:
            print("✅ COPY correctly failed with error:"            print(f"   {e}")
            conn.rollback()

            print("\n🔧 Error Recovery Options:")
            print("1. Fix data and retry")
            print("2. Use ON_ERROR_STOP with COPY")
            print("3. Load to temporary table first")
            print("4. Use individual INSERTs with error handling")

        conn.close()

    def cleanup_demo_data(self):
        """Clean up demo data."""
        conn = psycopg2.connect(**self.conn_params)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM clicks WHERE id LIKE 'bulk_click_%' OR id LIKE 'error_test_%'")
        conn.commit()
        conn.close()

        print("✅ Demo data cleaned up")

    def run_bulk_loading_demo(self):
        """Run complete bulk loading demonstration."""
        print("🚀 PostgreSQL Bulk Loading Demonstration")
        print("=" * 60)
        print(f"Started: {datetime.now()}")

        try:
            self.compare_loading_methods()
            self.demonstrate_error_handling()

        except Exception as e:
            print(f"❌ Demo failed: {e}")

        finally:
            self.cleanup_demo_data()

        print(f"\n✅ Bulk loading demo completed: {datetime.now()}")

        print("\n🎯 Key Takeaways:")
        print("• COPY is 10-100x faster than individual INSERTs")
        print("• Prepared statements help with repeated operations")
        print("• Always validate data before bulk loading")
        print("• Use transactions for consistency")
        print("• Handle errors gracefully")
        print("• Consider temporary staging tables")

def main():
    demo = BulkLoadingDemo()
    demo.run_bulk_loading_demo()

if __name__ == "__main__":
    main()
