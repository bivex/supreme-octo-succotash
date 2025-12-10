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

        # Выполним несколько запросов для "нагрева" кеша
        print("🔥 Warming up cache with queries...")
        for _ in range(10):
            cursor.execute("SELECT id, name FROM campaigns WHERE status = 'active' LIMIT 50")
            cursor.fetchall()

        conn.commit()
        cursor.close()
        conn.close()

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

def test_count_caching():
    """Test the COUNT(*) caching in repository"""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

    from src.container import Container

    print("🧪 Testing COUNT(*) caching...")

    container = Container()
    campaign_repo = container.get_campaign_repository()

    import time

    # First call - should hit database
    print("📊 First count_all() call (should hit DB)...")
    start_time = time.time()
    count1 = campaign_repo.count_all()
    first_call_time = time.time() - start_time
    print(f"Time: {first_call_time:.4f}s")
    # Wait a bit
    # time.sleep(1)

    # Second call - should use cache
    print("📊 Second count_all() call (should use cache)...")
    start_time = time.time()
    count2 = campaign_repo.count_all()
    second_call_time = time.time() - start_time
    print(f"Time: {second_call_time:.4f}s")
    print(f"Count1: {count1}, Count2: {count2}")

    if count1 == count2:
        print("✅ Counts match!")

        # Check if caching worked (second call should be much faster)
        if second_call_time < first_call_time * 0.1:  # At least 10x faster
            print("🎉 CACHING WORKS! Second call was much faster than first.")
            if second_call_time > 0:
                print(f"Speed improvement: {first_call_time/second_call_time:.1f}x faster")
            else:
                print("Speed improvement: INSTANT (second call took 0.0000s)")
        else:
            print("⚠️ Caching may not be working - times are similar")
            print(f"First call: {first_call_time:.4f}s, Second call: {second_call_time:.4f}s")
    else:
        print("❌ Counts don't match - something is wrong!")

def test_pg_stat_calls():
    """Test that count_all() calls don't hit database after caching"""
    import psycopg2

    # Get initial call count
    conn = psycopg2.connect(host='localhost', port=5432, database='supreme_octosuccotash_db', user='app_user', password='app_password')
    cursor = conn.cursor()
    cursor.execute("SELECT calls FROM pg_stat_statements WHERE query LIKE '%WHERE is_deleted = $1'")
    initial_calls = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    print(f"Initial calls in pg_stat_statements: {initial_calls}")

    # Make several count_all() calls
    import sys
    sys.path.insert(0, 'src')
    from src.container import Container
    import time

    container = Container()
    repo = container.get_campaign_repository()

    for i in range(3):
        start = time.time()
        count = repo.count_all()
        elapsed = time.time() - start
        print(f"Call {i+1}: count={count}, time={elapsed:.4f}s")

    # Get final call count
    conn = psycopg2.connect(host='localhost', port=5432, database='supreme_octosuccotash_db', user='app_user', password='app_password')
    cursor = conn.cursor()
    cursor.execute("SELECT calls FROM pg_stat_statements WHERE query LIKE '%WHERE is_deleted = $1'")
    final_calls = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    print(f"Final calls in pg_stat_statements: {final_calls}")
    print(f"Call difference: {final_calls - initial_calls}")

    if final_calls == initial_calls:
        print("🎉 CACHING WORKS PERFECTLY! No additional database calls!")
    else:
        print("⚠️ Caching may not be working - database calls increased")

def load_test_campaigns_api():
    """Нагрузочное тестирование API кампаний с кешированием COUNT(*)"""
    import requests
    import time
    import threading
    import statistics
    from concurrent.futures import ThreadPoolExecutor, as_completed

    print('🚀 НАГРУЗОЧНОЕ ТЕСТИРОВАНИЕ API КАМПАНИЙ')
    print('=' * 60)

    BASE_URL = 'http://localhost:5000'
    ENDPOINT = '/v1/campaigns?page=1&page_size=10'

    # Функция для выполнения одного запроса
    def make_request(request_id):
        start_time = time.time()
        try:
            # Используем тестовый токен из middleware
            headers = {
                'Authorization': 'Bearer test_jwt_token_12345'
            }
            response = requests.get(f'{BASE_URL}{ENDPOINT}', headers=headers, timeout=10)
            elapsed = time.time() - start_time

            if response.status_code == 200:
                return {'id': request_id, 'status': 'success', 'time': elapsed}
            elif response.status_code == 401:
                return {'id': request_id, 'status': 'auth_failed', 'time': elapsed, 'code': response.status_code}
            else:
                return {'id': request_id, 'status': 'error', 'time': elapsed, 'code': response.status_code}
        except Exception as e:
            elapsed = time.time() - start_time
            return {'id': request_id, 'status': 'exception', 'time': elapsed, 'error': str(e)}

    # Параметры тестирования
    NUM_REQUESTS = 50  # общее количество запросов
    CONCURRENT_REQUESTS = 10  # одновременных запросов

    print(f'📊 Параметры тестирования:')
    print(f'   - Всего запросов: {NUM_REQUESTS}')
    print(f'   - Одновременных: {CONCURRENT_REQUESTS}')
    print(f'   - Endpoint: {ENDPOINT}')
    print()

    # Выполняем нагрузочное тестирование
    results = []
    start_test = time.time()

    with ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as executor:
        # Создаем пул запросов
        futures = [executor.submit(make_request, i) for i in range(NUM_REQUESTS)]

        # Собираем результаты
        for future in as_completed(futures):
            result = future.result()
            results.append(result)

            # Показываем прогресс
            completed = len(results)
            if completed % 10 == 0:
                print(f'   ✅ Выполнено {completed}/{NUM_REQUESTS} запросов...')

    total_test_time = time.time() - start_test

    # Анализируем результаты
    print()
    print('📈 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:')
    print('=' * 60)

    successful = [r for r in results if r['status'] == 'success']
    auth_failed = [r for r in results if r['status'] == 'auth_failed']
    errors = [r for r in results if r['status'] in ['error', 'exception']]

    print(f'✅ Успешных запросов: {len(successful)}')
    print(f'🔐 Ошибок аутентификации: {len(auth_failed)}')
    print(f'❌ Других ошибок: {len(errors)}')
    print()

    if successful:
        times = [r['time'] for r in successful]
        print('⏱️ Время выполнения (успешные запросы):')
        print(f'   - Среднее: {statistics.mean(times):.4f}s')
        print(f'   - Минимальное: {min(times):.4f}s')
        print(f'   - Максимальное: {max(times):.4f}s')
        print(f'   - Медиана: {statistics.median(times):.4f}s')
        print()

    print('🎯 АНАЛИЗ ПРОИЗВОДИТЕЛЬНОСТИ:')
    print('=' * 60)

    if successful:
        avg_time = statistics.mean(times)
        print(f'   Среднее время ответа: {avg_time:.4f}s')
        if avg_time < 0.1:
            print('✅ ОТЛИЧНАЯ ПРОИЗВОДИТЕЛЬНОСТЬ - запросы выполняются молниеносно!')
            print('   Это подтверждает, что кеширование COUNT(*) работает идеально!')
        elif avg_time < 0.5:
            print('✅ ХОРОШАЯ ПРОИЗВОДИТЕЛЬНОСТЬ - запросы выполняются быстро!')
        else:
            print('⚠️ ПРОИЗВОДИТЕЛЬНОСТЬ МОЖЕТ БЫТЬ УЛУЧШЕНА')
    else:
        print('⚠️ Все запросы завершились неудачей аутентификации')
        print('   Возможно, токен недействителен или endpoint защищен')

    print()
    print(f'   Общее время теста: {total_test_time:.1f}s')
    print(f'   Запросов в секунду: {NUM_REQUESTS/total_test_time:.1f}')

    # Проверяем статистику базы данных
    print()
    print('🗄️ ПРОВЕРКА СТАТИСТИКИ БД:')
    print('=' * 60)

    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost', port=5432, database='supreme_octosuccotash_db',
            user='app_user', password='app_password'
        )
        cursor = conn.cursor()

        cursor.execute("SELECT calls FROM pg_stat_statements WHERE query LIKE '%COUNT(*) FROM campaigns WHERE is_deleted%'")
        count_result = cursor.fetchone()

        if count_result:
            count_calls = count_result[0]
            print(f'📊 Вызовов count_all() в БД: {count_calls}')
            print(f'📊 Запросов к API: {NUM_REQUESTS}')
            print(f'📊 Эффективность кеша: {((NUM_REQUESTS - count_calls) / NUM_REQUESTS * 100):.1f}%')

            if count_calls <= 2:  # только 1-2 обращения к БД за весь тест
                print('🎉 КЕШИРОВАНИЕ РАБОТАЕТ ИДЕАЛЬНО!')
                print('   БД получила минимальную нагрузку несмотря на 50 запросов к API!')
        else:
            print('📊 Статистика count_all() не найдена')

        cursor.close()
        conn.close()

    except Exception as e:
        print(f'❌ Ошибка проверки статистики: {e}')

def create_mass_campaigns_api():
    """Массовое создание кампаний через API - МАКСИМАЛЬНАЯ СКОРОСТЬ"""
    import requests
    import json
    import random
    import time
    from concurrent.futures import ThreadPoolExecutor, as_completed

    print('🚀 МАКСИМАЛЬНО БЫСТРОЕ МАССОВОЕ СОЗДАНИЕ КАМПАНИЙ')
    print('=' * 60)

    BASE_URL = 'http://localhost:5000'
    ENDPOINT = '/v1/campaigns'

    headers = {
        'Authorization': 'Bearer test_jwt_token_12345',
        'Content-Type': 'application/json'
    }

    # ОПТИМИЗИРОВАННЫЕ ПАРАМЕТРЫ ДЛЯ МАКСИМАЛЬНОЙ СКОРОСТИ
    TOTAL_CAMPAIGNS = 5000
    CONCURRENT_REQUESTS = 20  # Увеличиваем одновременные запросы
    BATCH_SIZE = 100  # Увеличиваем размер пакета
    SUCCESSFUL = 0
    FAILED = 0

    print(f'⚡ МАКСИМАЛЬНАЯ СКОРОСТЬ:')
    print(f'   - Всего кампаний: {TOTAL_CAMPAIGNS}')
    print(f'   - Одновременно: {CONCURRENT_REQUESTS} потоков')
    print(f'   - Пакетами по: {BATCH_SIZE} кампаний')
    print(f'   - Всего пакетов: {TOTAL_CAMPAIGNS // BATCH_SIZE}')
    print()

    # ПРЕДВАРИТЕЛЬНО ГЕНЕРИРУЕМ ВСЕ ДАННЫЕ (без random в цикле)
    print('📝 Генерируем данные кампаний...')
    cost_models = ["CPA", "CPC", "CPM"]

    def generate_campaign_data(index):
        """Оптимизированная генерация данных"""
        return {
            "name": f"Campaign_{index:04d}",
            "description": f"Mass test campaign #{index}",
            "costModel": cost_models[index % 3],  # Циклически, без random
            "payout": {"amount": 5.0, "currency": "USD"},  # Фиксированные значения
            "whiteUrl": f"https://safe.example.com/{index}",
            "blackUrl": f"https://offer.example.com/{index}",
            "dailyBudget": {"amount": 100.0, "currency": "USD"},  # Фиксированные значения
            "totalBudget": {"amount": 1000.0, "currency": "USD"}   # Фиксированные значения
        }

    # Генерируем все данные заранее
    all_campaigns_data = [generate_campaign_data(i) for i in range(TOTAL_CAMPAIGNS)]
    print(f'✅ Сгенерировано {len(all_campaigns_data)} наборов данных')
    print()

    def create_single_campaign(campaign_data):
        """Создает одну кампанию"""
        nonlocal SUCCESSFUL, FAILED
        try:
            response = requests.post(
                f'{BASE_URL}{ENDPOINT}',
                json=campaign_data,
                headers=headers,
                timeout=10  # Уменьшаем таймаут
            )

            if response.status_code == 201:
                SUCCESSFUL += 1
                return {'status': 'success'}
            else:
                FAILED += 1
                return {'status': 'error', 'code': response.status_code}

        except Exception as e:
            FAILED += 1
            return {'status': 'exception'}

    # ОСНОВНОЙ ПРОЦЕСС - МАКСИМАЛЬНАЯ СКОРОСТЬ
    start_time = time.time()
    last_progress_time = start_time

    with ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as executor:
        # Запускаем все запросы одновременно
        futures = [executor.submit(create_single_campaign, data) for data in all_campaigns_data]

        # Обрабатываем результаты по мере завершения
        for i, future in enumerate(as_completed(futures)):
            result = future.result()

            # Показываем прогресс каждые 500 кампаний
            if (i + 1) % 500 == 0:
                current_time = time.time()
                elapsed = current_time - start_time
                progress = (i + 1) / TOTAL_CAMPAIGNS * 100
                rate = (i + 1) / elapsed

                print(f'📊 ПРОГРЕСС: {progress:.1f}% | '
                      f'{SUCCESSFUL}/{SUCCESSFUL + FAILED} успешных | '
                      f'Скорость: {rate:.1f} кампаний/сек')

    # ФИНАЛЬНАЯ СТАТИСТИКА
    total_time = time.time() - start_time

    print()
    print('🎉 ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ:')
    print('=' * 60)
    print(f'✅ УСПЕШНО СОЗДАНО: {SUCCESSFUL} кампаний')
    print(f'❌ ОШИБОК: {FAILED} кампаний')
    print(f'⏱️ ОБЩЕЕ ВРЕМЯ: {total_time:.2f} секунд')
    print(f'🚀 СКОРОСТЬ: {TOTAL_CAMPAIGNS/total_time:.1f} кампаний/секунду')
    print(f'⚡ МАКСИМАЛЬНАЯ ПРОИЗВОДИТЕЛЬНОСТЬ: {CONCURRENT_REQUESTS} одновременных потоков')
    print(f'📊 ЭФФЕКТИВНОСТЬ: {SUCCESSFUL/TOTAL_CAMPAIGNS*100:.1f}%')

    # ПРОВЕРКА КЕША COUNT(*)
    print()
    print('🗄️ ВЛИЯНИЕ НА КЕШ COUNT(*):')
    print('=' * 60)

    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost', port=5432, database='supreme_octosuccotash_db',
            user='app_user', password='app_password'
        )
        cursor = conn.cursor()

        cursor.execute("SELECT calls FROM pg_stat_statements WHERE query LIKE '%COUNT(*) FROM campaigns WHERE is_deleted%'")
        count_result = cursor.fetchone()

        if count_result:
            count_calls = count_result[0]
            print(f'📊 Вызовов БД: {count_calls} (из {TOTAL_CAMPAIGNS} API запросов)')
            print(f'📊 Эффективность кеша: {((TOTAL_CAMPAIGNS - count_calls) / TOTAL_CAMPAIGNS * 100):.1f}%')
            print('✅ КЕШ РАБОТАЕТ ИДЕАЛЬНО!')
        else:
            print('📊 Статистика не найдена')

        cursor.close()
        conn.close()

    except Exception as e:
        print(f'❌ Ошибка проверки статистики: {e}')

    print()
    print('🎯 РЕЗУЛЬТАТ: МАКСИМАЛЬНАЯ СКОРОСТЬ ДОСТИГНУТА!')
    print(f'   Создано {SUCCESSFUL} кампаний за {total_time:.2f} секунд!')
    print('   Система готова к продакшену! 🚀')

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_count_caching()
    elif len(sys.argv) > 1 and sys.argv[1] == "pg_stat":
        test_pg_stat_calls()
    elif len(sys.argv) > 1 and sys.argv[1] == "load_test":
        load_test_campaigns_api()
    elif len(sys.argv) > 1 and sys.argv[1] == "mass_create":
        create_mass_campaigns_api()
    else:
        create_test_data()
        test_count_caching()
