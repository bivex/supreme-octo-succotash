#!/usr/bin/env python3
"""
Python source files merger - объединяет все .py файлы в один txt файл
"""

import os
import sys
from pathlib import Path

def merge_python_files(root_dir=".", output_file="merged_python_sources.txt"):
    """
    Объединяет все .py файлы из указанного каталога в один txt файл

    Args:
        root_dir (str): Корневой каталог для поиска файлов
        output_file (str): Имя выходного файла
    """
    root_path = Path(root_dir)

    if not root_path.exists():
        print(f"Ошибка: Каталог {root_dir} не существует")
        return False

    # Директории и файлы для исключения
    skip_dirs = {
        "__pycache__", ".venv", "venv", ".env", "node_modules",
        ".git", ".cursor", ".vscode", ".idea",
        "build", "dist", ".pytest_cache", ".mypy_cache",
        ".tox", ".coverage", "htmlcov", "docs", ".git",
        ".cursor", "scripts", "tests", "migrations"
    }

    skip_files = {
        "merge_python_files.py",  # Сам скрипт слияния
        "setup.py", "conftest.py"
    }

    # Собираем все .py файлы
    python_files = []
    for py_file in root_path.rglob("*.py"):
        # Пропускаем ненужные директории (проверяем только непосредственных родителей)
        skip_file = False
        for part in py_file.parts:
            if part in skip_dirs:
                skip_file = True
                break

        if skip_file:
            continue

        # Пропускаем ненужные файлы
        if py_file.name in skip_files:
            continue

        # Пропускаем файлы с расширениями .pyc
        if py_file.suffix == '.pyc':
            continue

        # Пропускаем временные файлы и бэкапы
        if py_file.name.startswith('.') or py_file.name.endswith(('.bak', '.tmp', '.log')):
            continue

        python_files.append(py_file)

    if not python_files:
        print("Не найдено ни одного .py файла")
        return False

    print(f"Найдено {len(python_files)} Python файлов")

    # Отладка: покажем первые 10 файлов
    print("Первые 10 найденных файлов:")
    for i, f in enumerate(python_files[:10]):
        print(f"  {i+1}. {f}")
    print()

    # Сортируем файлы по пути для консистентности
    python_files.sort()

    try:
        with open(output_file, 'w', encoding='utf-8') as outfile:
            outfile.write("PYTHON SOURCE FILES MERGER\n")
            outfile.write("=" * 50 + "\n\n")
            outfile.write(f"Объединено файлов: {len(python_files)}\n")
            outfile.write(f"Корневой каталог: {root_path.absolute()}\n")
            outfile.write(f"Сгенерировано: {Path(output_file).absolute()}\n\n")
            outfile.write("ИСКЛЮЧЕННЫЕ ДИРЕКТОРИИ:\n")
            outfile.write("- __pycache__, .venv, venv, .env, node_modules\n")
            outfile.write("- .git, .cursor, .vscode, .idea\n")
            outfile.write("- build, dist, .pytest_cache, .mypy_cache, .tox\n")
            outfile.write("- .coverage, htmlcov, docs, scripts, tests, migrations\n\n")
            outfile.write("ИСКЛЮЧЕННЫЕ ФАЙЛЫ:\n")
            outfile.write("- merge_python_files.py, setup.py, conftest.py\n")
            outfile.write("- *.pyc, *.bak, *.tmp, *.log, файлы начинающиеся с .\n\n")
            outfile.write("=" * 50 + "\n\n")

            for i, py_file in enumerate(python_files, 1):
                relative_path = py_file.relative_to(root_path)

                outfile.write(f"[{i:3d}] {'='*10} {relative_path} {'='*10}\n")
                outfile.write(f"Полный путь: {py_file.absolute()}\n")
                outfile.write(f"Размер: {py_file.stat().st_size} байт\n\n")

                try:
                    with open(py_file, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                        outfile.write(content)
                        outfile.write("\n\n")
                except UnicodeDecodeError:
                    # Если файл не в UTF-8, пробуем другие кодировки
                    try:
                        with open(py_file, 'r', encoding='cp1251') as infile:
                            content = infile.read()
                            outfile.write(f"--- Файл прочитан в кодировке CP1251 ---\n")
                            outfile.write(content)
                            outfile.write("\n\n")
                    except UnicodeDecodeError:
                        outfile.write(f"--- ОШИБКА: Не удалось прочитать файл в кодировках UTF-8 и CP1251 ---\n\n")
                except Exception as e:
                    outfile.write(f"--- ОШИБКА чтения файла: {e} ---\n\n")

                outfile.write(f"{'='*20} КОНЕЦ ФАЙЛА {relative_path} {'='*20}\n\n\n")

        print(f"✅ Успешно объединено {len(python_files)} файлов в {output_file}")
        print(f"📁 Выходной файл: {Path(output_file).absolute()}")
        return True

    except Exception as e:
        print(f"❌ Ошибка при создании файла: {e}")
        return False

def main():
    """Основная функция"""
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = "."

    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = "merged_python_sources.txt"

    print("🔧 Python Source Files Merger")
    print(f"📂 Каталог: {root_dir}")
    print(f"📄 Выходной файл: {output_file}")
    print("-" * 40)

    success = merge_python_files(root_dir, output_file)

    if success:
        print("\n✅ Готово!")
    else:
        print("\n❌ Произошла ошибка")
        sys.exit(1)

if __name__ == "__main__":
    main()
