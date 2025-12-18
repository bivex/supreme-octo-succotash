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

import requests
import os

print("🔄 Сбрасываем данные через API...")
response = requests.post('http://127.0.0.1:5000/v1/reset')
print(f"Сброс данных: {response.status_code}")

print("📊 Проверяем размер файла после сброса...")
if os.path.exists('stress_test.db'):
    size = os.path.getsize('stress_test.db')
    print(f"Размер файла после сброса: {size} байт")

    # Проверим, остались ли данные
    import sqlite3
    conn = sqlite3.connect('stress_test.db')
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM campaigns WHERE is_deleted = 0")
    campaigns_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM clicks")
    clicks_count = cursor.fetchone()[0]

    conn.close()

    print(f"Кампаний в базе: {campaigns_count}")
    print(f"Кликов в базе: {clicks_count}")

    if campaigns_count > 0 or clicks_count > 0:
        print("✅ Данные остались в файле после сброса!")
    else:
        print("ℹ️  Данные были удалены, но файл сохранился")
else:
    print("❌ Файл базы данных исчез!")

print("✨ Проверка завершена!")
