# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:11:50
# Last Updated: 2025-12-18T12:28:32
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""Тест автоматического удаления индексов."""

from src.container import container
from src.infrastructure.upholder.postgres_auto_upholder import UpholderConfig, PostgresAutoUpholder


def test_index_deletion():
    print("🚀 Тестирование автоматического удаления индексов...")

    # Конфигурация с включенным удалением индексов в dry-run режиме
    config = UpholderConfig(
        auto_delete_unused_indexes=True,
        dry_run_mode=True,  # Только логирование, без реального удаления
        unused_index_age_days=0  # Без проверки возраста для тестирования
    )

    conn = container.get_db_connection()
    upholder = PostgresAutoUpholder(conn, config)

    try:
        # Запустим полный аудит
        report = upholder.run_full_audit()

        print("\n✅ Аудит завершен!")
        print(f"⏱️  Длительность: {report.duration_seconds:.2f} сек")
        print(f"🗑️  Удалено индексов: {len(report.indexes_deleted)}")
        print(f"🚨 Аллертов: {len(report.alerts_generated)}")

        if report.indexes_deleted:
            print("\n📋 Удаленные индексы:")
            for deleted in report.indexes_deleted:
                print(f"  - {deleted}")
        else:
            print("\nℹ️  Индексы для удаления не найдены")

        # Покажем последние алерты
        print("\n🚨 Последние алерты:")
        for i, alert in enumerate(report.alerts_generated[-5:], 1):  # Последние 5
            print(f"  {i}. {alert}")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        container.release_db_connection(conn)


if __name__ == "__main__":
    test_index_deletion()
