#!/usr/bin/env python3
"""Проверка индексов в системе."""

import sys
import os
sys.path.insert(0, 'src')

from container import container

def check_indexes():
    conn = container.get_db_connection()
    cursor = conn.cursor()

    try:
        print("📊 ПРОВЕРКА ИНДЕКСОВ В СИСТЕМЕ")
        print("=" * 50)

        # Проверим статистику использования индексов
        cursor.execute('''
            SELECT
                schemaname,
                indexrelname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch,
                pg_size_pretty(pg_relation_size(indexrelid)) as size
            FROM pg_stat_user_indexes
            WHERE schemaname = 'public'
            ORDER BY indexrelname
        ''')

        stats = cursor.fetchall()
        print("📈 СТАТИСТИКА ИСПОЛЬЗОВАНИЯ ИНДЕКСОВ:")
        unused_indexes = []

        for schema, index, scans, tup_read, tup_fetch, size in stats:
            status = '✅ Используется' if scans > 0 else '⚠️  НЕ ИСПОЛЬЗУЕТСЯ'
            print(f'  • {schema}.{index}: {status}')
            print(f'    Сканов: {scans}, прочитано кортежей: {tup_read}, размер: {size}')

            if scans == 0:
                unused_indexes.append(index)
            print()

        print(f'🎯 НЕИСПОЛЬЗУЕМЫЕ ИНДЕКСЫ: {len(unused_indexes)} шт.')
        for idx in unused_indexes:
            print(f'   - {idx}')

        # Проверим наш тестовый индекс специально
        print("\n🎯 ТЕСТОВЫЙ ИНДЕКС:")
        cursor.execute('''
            SELECT
                schemaname,
                indexrelname,
                idx_scan,
                pg_size_pretty(pg_relation_size(indexrelid)) as size,
                CASE WHEN indisprimary THEN 'PRIMARY KEY'
                     WHEN indisunique THEN 'UNIQUE'
                     ELSE 'REGULAR' END as index_type
            FROM pg_stat_user_indexes ui
            JOIN pg_index i ON ui.indexrelid = i.indexrelid
            WHERE indexrelname = 'idx_test_unused'
        ''')

        test_index = cursor.fetchone()
        if test_index:
            schema, name, scans, size, idx_type = test_index
            print(f'   Название: {schema}.{name}')
            print(f'   Тип: {idx_type}')
            print(f'   Сканов: {scans}')
            print(f'   Размер: {size}')
            if scans == 0:
                print('   Статус: 🟢 ГОТОВ К УДАЛЕНИЮ')
            else:
                print('   Статус: 🔴 ИСПОЛЬЗУЕТСЯ')
        else:
            print('   Тестовый индекс не найден')

        print("\n" + "=" * 50)
        print("💡 ЗАКЛЮЧЕНИЕ:")
        print(f"   • Всего индексов: {len(stats)}")
        print(f"   • Неиспользуемых: {len(unused_indexes)}")
        print("   • Функция авто-удаления: ОТКЛЮЧЕНА (dry_run_mode: true)")

        if unused_indexes:
            print("\n🔧 РЕКОМЕНДАЦИИ:")
            print("   • Включите auto_delete_unused_indexes: true для авто-удаления")
            print("   • Начните с dry_run_mode: true для тестирования")
            print("   • Проверьте возраст индексов (>30 дней)")

    except Exception as e:
        print(f'❌ Ошибка: {e}')
        import traceback
        traceback.print_exc()
    finally:
        container.release_db_connection(conn)

if __name__ == "__main__":
    check_indexes()
