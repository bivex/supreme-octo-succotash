import sqlite3
import os

# Проверим, существует ли файл
if os.path.exists('stress_test.db'):
    print('✅ Файл stress_test.db существует!')
    print(f'📏 Размер файла: {os.path.getsize("stress_test.db")} байт')

    # Попробуем подключиться и посмотреть таблицы
    conn = sqlite3.connect('stress_test.db')
    cursor = conn.cursor()

    # Получить список таблиц
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f'🗂️  Найдено таблиц: {len(tables)}')
    for table in tables:
        print(f'  📋 {table[0]}')

        # Посчитать записи в каждой таблице
        cursor.execute(f'SELECT COUNT(*) FROM {table[0]}')
        count = cursor.fetchone()[0]
        print(f'    📊 Записей: {count}')

        if count > 0:
            # Показать структуру таблицы
            cursor.execute(f'PRAGMA table_info({table[0]})')
            columns = cursor.fetchall()
            print(f'    📝 Колонки: {len(columns)}')
            for col in columns[:3]:  # Покажем первые 3 колонки
                print(f'      • {col[1]} ({col[2]})')

    conn.close()
else:
    print('❌ Файл stress_test.db НЕ существует')

print("\n🔍 Проверка завершена!")
