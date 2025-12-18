
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
"""
Скрипт для запуска тестов синхронизации и многопоточности.

Запускает интеграционные тесты для проверки:
- Thread safety DI контейнера
- Синхронизации в BackgroundServiceManager
- Работы с connection pool из разных потоков
"""

import sys
import os
from pathlib import Path

# Добавляем корневую директорию в путь
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

def main():
    """Запуск тестов синхронизации."""
    print("🧵 Запуск тестов синхронизации и многопоточности...")
    print("=" * 60)

    try:
        import unittest
        from tests.integration.test_threading_sync import TestThreadingSynchronization

        # Создаем test suite
        suite = unittest.TestLoader().loadTestsFromTestCase(TestThreadingSynchronization)

        # Запускаем тесты с подробным выводом
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        # Выводим результаты
        print("\n" + "=" * 60)
        if result.wasSuccessful():
            print("✅ Все тесты синхронизации пройдены успешно!")
            print(f"📊 Запущено тестов: {result.testsRun}")
            return 0
        else:
            print("❌ Некоторые тесты синхронизации провалились!")
            print(f"📊 Провалено: {len(result.failures)}")
            print(f"📊 Ошибок: {len(result.errors)}")
            return 1

    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("Убедитесь, что все зависимости установлены")
        return 1
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
