#!/usr/bin/env python3
"""
Извлечение логики upholder и main файлов из объединенного источника
"""

import re

def extract_files_by_pattern(input_file, output_file, patterns):
    """
    Извлекает файлы по паттернам из объединенного файла

    Args:
        input_file (str): Путь к входному объединенному файлу
        output_file (str): Путь к выходному файлу
        patterns (list): Список паттернов для поиска файлов
    """
    extracted_content = []
    current_file_content = []
    in_target_file = False

    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            # Проверяем начало нового файла
            if line.startswith('[ ') and '==========' in line:
                # Если мы были в целевом файле, сохраняем его содержимое
                if in_target_file and current_file_content:
                    extracted_content.extend(current_file_content)
                    extracted_content.append("\n" + "="*80 + "\n\n")

                # Проверяем, является ли этот файл целевым
                file_name = line.split('==========')[1].strip()
                in_target_file = any(re.search(pattern, file_name, re.IGNORECASE) for pattern in patterns)

                if in_target_file:
                    print(f"Извлекаем: {file_name}")
                    current_file_content = [line]  # Начинаем новый файл
                else:
                    current_file_content = []

            elif in_target_file:
                current_file_content.append(line)

    # Добавляем последний файл если он был целевым
    if in_target_file and current_file_content:
        extracted_content.extend(current_file_content)

    # Записываем результат
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("UPHOLDER + MAIN LOGIC EXTRACTION\n")
        f.write("=" * 50 + "\n\n")
        f.write("Извлечена логика PostgreSQL Auto Upholder и Main приложения\n\n")
        f.write("ВКЛЮЧЕННЫЕ КОМПОНЕНТЫ:\n")
        f.write("- PostgreSQL Auto Upholder (postgres_auto_upholder.py)\n")
        f.write("- Connection Pool Monitor (postgres_connection_pool_monitor.py)\n")
        f.write("- Monitoring компоненты (cache, query, index, optimizer)\n")
        f.write("- Main приложение (main.py, main_clean.py)\n\n")
        f.write("=" * 50 + "\n\n")
        f.writelines(extracted_content)

    print(f"\n✅ Извлечено {len(extracted_content)} строк кода")
    print(f"📁 Сохранено в: {output_file}")

def main():
    """Основная функция"""
    input_file = "debug_merged_sources.txt"
    output_file = "upholder_main_logic.txt"

    # Паттерны для поиска целевых файлов
    patterns = [
        r'.*upholder.*',           # upholder файлы
        r'.*monitor.*',            # monitor файлы
        r'.*optimizer.*',          # optimizer файлы
        r'.*main\.py$',            # main.py файлы
        r'.*main_clean\.py$',      # main_clean.py
    ]

    print("🔧 Upholder + Main Logic Extractor")
    print(f"📂 Входной файл: {input_file}")
    print(f"📄 Выходной файл: {output_file}")
    print("-" * 40)

    extract_files_by_pattern(input_file, output_file, patterns)

    print("\n✅ Готово!")

if __name__ == "__main__":
    main()
