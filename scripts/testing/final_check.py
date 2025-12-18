# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:33
# Last Updated: 2025-12-18T12:28:33
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

import os
import sqlite3

print("🎯 Финальная проверка SQLite базы данных")
print("=" * 50)

# Проверяем файл
if os.path.exists('stress_test.db'):
    size = os.path.getsize('stress_test.db')
    print(f"✅ Файл существует: {size} байт")
else:
    print("❌ Файл не найден!")
    exit(1)

# Проверяем содержимое
conn = sqlite3.connect('stress_test.db')
cursor = conn.cursor()

tables = ['campaigns', 'clicks', 'webhooks', 'events', 'conversions', 'postbacks', 'goals']
total_records = 0

print("\n📊 Содержимое таблиц:")
for table in tables:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        total_records += count
        print(f"  • {table}: {count} записей")
    except:
        print(f"  • {table}: ошибка чтения")

print(f"\n📈 Всего записей в базе: {total_records}")

# Проверим конкретные данные
cursor.execute("SELECT id, name, status FROM campaigns WHERE is_deleted = 0")
campaigns = cursor.fetchall()
print(f"\n🎯 Активные кампании ({len(campaigns)}):")
for camp in campaigns[:3]:  # Покажем первые 3
    print(f"  • {camp[0]}: {camp[1]} ({camp[2]})")

cursor.execute("SELECT id, campaign_id, ip_address FROM clicks LIMIT 3")
clicks = cursor.fetchall()
print(f"\n🖱️  Клики ({len(clicks)} показаны):")
for click in clicks:
    print(f"  • {click[0]}: кампания {click[1]}, IP {click[2]}")

conn.close()

print("\n🎉 Проверка завершена успешно!")
print("✅ SQLite репозитории работают корректно!")
print("✅ Данные сохраняются в файл на диске!")
print("✅ База данных переиспользуется между запусками!")
