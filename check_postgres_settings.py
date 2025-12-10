#!/usr/bin/env python3
"""
Check PostgreSQL settings and database state
"""

import psycopg2

def check_postgres_settings():
    """Check PostgreSQL settings and database state"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="supreme_octosuccotash_db",
            user="app_user",
            password="app_password"
        )
        cursor = conn.cursor()

        print("🔍 PostgreSQL Cache Hit Ratio Analysis")
        print("=" * 50)

        # Размер базы данных
        cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database())) as db_size")
        db_size = cursor.fetchone()[0]
        print(f"📊 Database size: {db_size}")

        # Количество записей в основных таблицах
        tables = ['campaigns', 'clicks', 'events', 'conversions', 'landing_pages', 'offers']
        total_records = 0
        print("\n📋 Table records:")
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                total_records += count
                print(f"  {table}: {count} records")
            except Exception as e:
                print(f"  {table}: error - {e}")

        print(f"\n📈 Total records: {total_records}")

        # Текущие настройки PostgreSQL
        cursor.execute("""
            SELECT name, setting, unit
            FROM pg_settings
            WHERE name IN ('shared_buffers', 'work_mem', 'maintenance_work_mem', 'effective_cache_size', 'shared_preload_libraries')
            ORDER BY name
        """)
        settings = cursor.fetchall()

        print("\n⚙️ PostgreSQL Cache Settings:")
        for name, setting, unit in settings:
            unit_str = f" {unit}" if unit else ""
            print(f"  {name}: {setting}{unit_str}")

        # Проверка расширения pg_buffercache
        cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'pg_buffercache'")
        has_buffercache = cursor.fetchone()

        if has_buffercache:
            print("\n✅ pg_buffercache extension: INSTALLED")
        else:
            print("\n❌ pg_buffercache extension: NOT INSTALLED")
            print("   This may cause inaccurate cache hit ratio measurements")

        # Проверка расширения pg_stat_statements
        cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'")
        has_stat_statements = cursor.fetchone()

        if has_stat_statements:
            print("✅ pg_stat_statements extension: INSTALLED")
        else:
            print("❌ pg_stat_statements extension: NOT INSTALLED")
            print("   This may cause missing query performance data")

        # Диагностика cache hit ratio = 0%
        print("\n🔬 DIAGNOSIS:")
        if total_records == 0:
            print("❌ ПРОБЛЕМА: База данных пустая (0 записей)")
            print("   Решение: Загрузите тестовые данные для тестирования кеша")

        if db_size.endswith('kB') and int(db_size[:-2]) < 10000:
            print("❌ ПРОБЛЕМА: База данных слишком маленькая для эффективного кеширования")
            print(f"   Текущий размер: {db_size}")
            print("   Решение: Увеличьте объем данных")

        # Проверяем shared_buffers
        cursor.execute("SELECT setting::bigint FROM pg_settings WHERE name = 'shared_buffers'")
        shared_buffers_kb = cursor.fetchone()[0]

        if shared_buffers_kb < 128 * 1024:  # меньше 128MB
            print("❌ ПРОБЛЕМА: shared_buffers слишком маленький")
            print(f"   Текущий: {shared_buffers_kb // 1024} MB")
            print("   Рекомендация: 25-40% от оперативной памяти")

        print("\n💡 РЕКОМЕНДАЦИИ:")
        print("1. Загрузите тестовые данные: python load_test_db.py --small")
        print("2. Увеличьте shared_buffers в postgresql.conf")
        print("3. Установите pg_buffercache для точных измерений")
        print("4. Проведите нагрузочное тестирование")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_postgres_settings()
