"""
Интеграционный тест для проверки синхронизации и многопоточности.

Проверяет:
- Многопоточный доступ к DI контейнеру без race conditions
- Синхронизацию в BackgroundServiceManager
- Thread-safe работу с connection pool
- Общую стабильность при параллельном доступе
"""

import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock

from src.container import container
from main_clean import BackgroundServiceManager, DatabaseConnectionTester


class TestThreadingSynchronization(unittest.TestCase):
    """Тесты для проверки thread safety и синхронизации."""

    def setUp(self):
        """Подготовка к тестам."""
        self.service_manager = BackgroundServiceManager()
        self.db_tester = DatabaseConnectionTester(container)
        self.results = []
        self.errors = []

    def tearDown(self):
        """Очистка после тестов."""
        # Останавливаем все сервисы
        try:
            self.service_manager.stop_all_services()
        except Exception:
            pass  # Игнорируем ошибки при остановке

    def test_concurrent_container_access(self):
        """Тест многопоточного доступа к DI контейнеру."""
        def access_container(thread_id: int) -> Dict[str, Any]:
            """Функция для доступа к контейнеру из потока."""
            try:
                start_time = time.time()

                # Получаем различные сервисы из контейнера
                services = {
                    'pool': container.get_db_connection_pool(),
                    'upholder': container.get_postgres_upholder(),
                    'cache_monitor': container.get_postgres_cache_monitor(),
                    'campaign_repo': container.get_campaign_repository(),
                }

                end_time = time.time()
                return {
                    'thread_id': thread_id,
                    'success': True,
                    'duration': end_time - start_time,
                    'services': list(services.keys())
                }
            except Exception as e:
                return {
                    'thread_id': thread_id,
                    'success': False,
                    'error': str(e),
                    'duration': 0
                }

        # Запускаем 10 потоков одновременно
        num_threads = 10
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(access_container, i) for i in range(num_threads)]
            results = [future.result() for future in as_completed(futures)]

        # Проверяем результаты
        successful_accesses = [r for r in results if r['success']]
        failed_accesses = [r for r in results if not r['success']]

        self.assertEqual(len(successful_accesses), num_threads,
                        f"Все {num_threads} потоков должны успешно получить доступ к контейнеру")

        self.assertEqual(len(failed_accesses), 0,
                        f"Не должно быть неудачных доступов: {failed_accesses}")

        # Проверяем, что все потоки получили одинаковые сервисы
        first_services = set(successful_accesses[0]['services'])
        for result in successful_accesses[1:]:
            self.assertEqual(set(result['services']), first_services,
                           "Все потоки должны получить одинаковый набор сервисов")

    def test_service_manager_thread_safety(self):
        """Тест thread safety BackgroundServiceManager."""
        def start_services(thread_id: int) -> Dict[str, Any]:
            """Функция для запуска сервисов из потока."""
            try:
                start_time = time.time()

                # Создаем новый менеджер для каждого потока
                manager = BackgroundServiceManager()

                # Запускаем сервисы
                manager.start_postgres_upholder()
                manager.start_cache_monitor()

                # Немного ждем
                time.sleep(0.1)

                # Останавливаем сервисы
                manager.stop_all_services()

                end_time = time.time()
                return {
                    'thread_id': thread_id,
                    'success': True,
                    'duration': end_time - start_time
                }
            except Exception as e:
                return {
                    'thread_id': thread_id,
                    'success': False,
                    'error': str(e)
                }

        # Запускаем 5 потоков одновременно
        num_threads = 5
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(start_services, i) for i in range(num_threads)]
            results = [future.result() for future in as_completed(futures)]

        # Проверяем результаты
        successful_operations = [r for r in results if r['success']]
        failed_operations = [r for r in results if not r['success']]

        self.assertGreaterEqual(len(successful_operations), num_threads - 1,
                               f"Большинство потоков должны успешно управлять сервисами")

    def test_connection_pool_thread_safety(self):
        """Тест thread safety connection pool."""
        def test_connection(thread_id: int) -> Dict[str, Any]:
            """Функция для тестирования соединения из потока."""
            try:
                start_time = time.time()

                # Тестируем подключение
                is_connected, driver_info = self.db_tester.test_postgresql_connection()

                end_time = time.time()
                return {
                    'thread_id': thread_id,
                    'success': True,
                    'connected': is_connected,
                    'driver': driver_info,
                    'duration': end_time - start_time
                }
            except Exception as e:
                return {
                    'thread_id': thread_id,
                    'success': False,
                    'error': str(e)
                }

        # Запускаем 8 потоков одновременно
        num_threads = 8
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(test_connection, i) for i in range(num_threads)]
            results = [future.result() for future in as_completed(futures)]

        # Проверяем результаты
        successful_tests = [r for r in results if r['success']]
        failed_tests = [r for r in results if not r['success']]

        self.assertGreaterEqual(len(successful_tests), num_threads - 2,
                               f"Большинство потоков должны успешно протестировать соединение")

        # Проверяем, что все успешные тесты вернули одинаковый драйвер
        connected_results = [r for r in successful_tests if r['connected']]
        if connected_results:
            first_driver = connected_results[0]['driver']
            for result in connected_results[1:]:
                self.assertEqual(result['driver'], first_driver,
                               "Все тесты должны вернуть одинаковый драйвер БД")

    def test_race_condition_prevention(self):
        """Тест предотвращения race condition при одновременном доступе."""
        shared_results = []
        errors = []

        def race_condition_test(thread_id: int):
            """Тест на race condition."""
            try:
                # Быстрые последовательные операции
                for i in range(10):
                    # Получаем сервисы
                    upholder = container.get_postgres_upholder()
                    cache_monitor = container.get_postgres_cache_monitor()
                    pool = container.get_db_connection_pool()

                    # Проверяем, что объекты получены
                    self.assertIsNotNone(upholder)
                    self.assertIsNotNone(cache_monitor)
                    self.assertIsNotNone(pool)

                    # Маленькая задержка для имитации конкуренции
                    time.sleep(0.001)

                shared_results.append(f"Thread {thread_id}: OK")
            except Exception as e:
                errors.append(f"Thread {thread_id}: {str(e)}")

        # Запускаем много потоков одновременно
        threads = []
        num_threads = 20

        for i in range(num_threads):
            thread = threading.Thread(target=race_condition_test, args=(i,))
            threads.append(thread)

        # Стартуем все потоки одновременно
        for thread in threads:
            thread.start()

        # Ждем завершения
        for thread in threads:
            thread.join(timeout=10)

        # Проверяем результаты
        self.assertEqual(len(shared_results), num_threads,
                        f"Все {num_threads} потоков должны завершиться успешно")

        self.assertEqual(len(errors), 0,
                        f"Не должно быть ошибок: {errors}")

    @patch('main_clean.logger')
    def test_service_manager_lock_behavior(self, mock_logger):
        """Тест поведения блокировок в BackgroundServiceManager."""
        # Создаем primary manager для тестирования
        from main_clean import BackgroundServiceManager
        primary_manager = BackgroundServiceManager()
        # Гарантируем, что это primary manager
        primary_manager._is_primary_manager = True

        # Создаем мок-объекты без метода stop(), чтобы проверить stop_monitoring
        mock_upholder = MagicMock()
        mock_upholder.start = MagicMock()
        mock_upholder._scheduler_thread = MagicMock()
        mock_upholder._scheduler_thread.is_alive.return_value = True
        # Удаляем stop, чтобы проверить stop_monitoring
        del mock_upholder.stop

        mock_cache_monitor = MagicMock()
        mock_cache_monitor.start_monitoring = MagicMock()
        mock_cache_monitor.monitor_thread = MagicMock()
        mock_cache_monitor.monitor_thread.is_alive.return_value = True
        # Удаляем stop, чтобы проверить stop_monitoring
        del mock_cache_monitor.stop

        # Патчим методы контейнера
        with patch.object(container, 'get_postgres_upholder', return_value=mock_upholder), \
             patch.object(container, 'get_postgres_cache_monitor', return_value=mock_cache_monitor):

            # Запускаем сервисы на primary manager
            primary_manager.start_postgres_upholder()
            primary_manager.start_cache_monitor()

            # Проверяем, что методы были вызваны
            mock_upholder.start.assert_called_once()
            mock_cache_monitor.start_monitoring.assert_called_once()

            # Останавливаем сервисы
            primary_manager.stop_all_services()

            # Проверяем, что stop_monitoring была вызвана (поскольку stop() нет)
            mock_cache_monitor.stop_monitoring.assert_called_once()

    def test_performance_under_load(self):
        """Тест производительности под нагрузкой."""
        start_time = time.time()

        def load_test(thread_id: int) -> float:
            """Нагрузочный тест."""
            thread_start = time.time()

            for i in range(50):  # 50 итераций на поток
                # Получаем сервисы
                _ = container.get_postgres_upholder()
                _ = container.get_postgres_cache_monitor()
                _ = container.get_db_connection_pool()

                # Маленькая задержка
                time.sleep(0.001)

            thread_end = time.time()
            return thread_end - thread_start

        # Запускаем 10 потоков
        num_threads = 10
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(load_test, i) for i in range(num_threads)]
            execution_times = [future.result() for future in as_completed(futures)]

        total_time = time.time() - start_time

        # Проверяем, что общее время выполнения разумное (не более 60 секунд)
        self.assertLess(total_time, 60,
                       f"Тест под нагрузкой должен завершиться за разумное время, но занял {total_time:.2f} сек")

        # Проверяем, что все потоки завершились
        self.assertEqual(len(execution_times), num_threads)

        # Среднее время выполнения не должно быть слишком большим
        avg_time = sum(execution_times) / len(execution_times)
        self.assertLess(avg_time, 5,
                       f"Среднее время выполнения потока должно быть разумным: {avg_time:.2f} сек")


if __name__ == '__main__':
    # Настраиваем более подробный вывод
    unittest.main(verbosity=2, exit=False)
