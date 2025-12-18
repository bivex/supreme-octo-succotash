
# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:11:47
# Last Updated: 2025-12-18T12:28:32
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
Быстрая проверка синхронизации - запускает тест на многопоточность.

Использование: python test_sync_quick.py
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor

from src.container import container

def quick_sync_test():
    """Быстрая проверка синхронизации."""
    print("🧵 Быстрая проверка синхронизации...")

    errors = []
    success_count = 0

    def test_thread(thread_id):
        nonlocal success_count, errors
        try:
            # Быстрый тест доступа к контейнеру
            for i in range(5):
                upholder = container.get_postgres_upholder()
                cache_monitor = container.get_postgres_cache_monitor()
                pool = container.get_db_connection_pool()

                assert upholder is not None
                assert cache_monitor is not None
                assert pool is not None

            success_count += 1
            print(f"✅ Поток {thread_id}: OK")
        except Exception as e:
            errors.append(f"Поток {thread_id}: {e}")
            print(f"❌ Поток {thread_id}: {e}")

    # Запускаем 10 потоков
    num_threads = 10
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(test_thread, i) for i in range(num_threads)]

        # Ждем завершения
        for future in futures:
            future.result(timeout=30)

    # Результаты
    print(f"\n📊 Результаты:")
    print(f"✅ Успешных потоков: {success_count}/{num_threads}")
    print(f"❌ Ошибок: {len(errors)}")

    if errors:
        print(f"Ошибки: {errors}")
        return False
    else:
        print("🎉 Синхронизация работает корректно!")
        return True

if __name__ == "__main__":
    success = quick_sync_test()
    exit(0 if success else 1)
