#!/bin/bash

# Скрипт для анализа админпанели с помощью DPy инструмента
# Создает структурированную папку с результатами анализа по дате

set -e  # Остановить выполнение при ошибке

# Получаем текущую дату и время в формате YYYY-MM-DD_HH-MM-SS
CURRENT_DATE=$(date +"%Y-%m-%d")
CURRENT_TIME=$(date +"%H-%M-%S")
CURRENT_DATETIME="${CURRENT_DATE}_${CURRENT_TIME}"

# Создаем основную папку с датой
ANALYSIS_BASE_DIR="analysis_results/${CURRENT_DATE}"

# Создаем уникальную подпапку для этого анализа
ANALYSIS_DIR="${ANALYSIS_BASE_DIR}/${CURRENT_DATETIME}"
echo "Создание директории анализа: ${ANALYSIS_DIR}"

# Создаем структуру папок для разных типов анализа
mkdir -p "${ANALYSIS_DIR}/architecture_smells"
mkdir -p "${ANALYSIS_DIR}/design_smells"
mkdir -p "${ANALYSIS_DIR}/implementation_smells"
mkdir -p "${ANALYSIS_DIR}/metrics"
mkdir -p "${ANALYSIS_DIR}/logs"

echo "Структура папок создана:"
echo "  ├── architecture_smells/"
echo "  ├── design_smells/"
echo "  ├── implementation_smells/"
echo "  ├── metrics/"
echo "  └── logs/"

# Временная папка для результатов анализа
TEMP_RESULTS_DIR="${ANALYSIS_DIR}/temp_results"
mkdir -p "${TEMP_RESULTS_DIR}"

echo "Запуск анализа админпанели..."

# Запускаем анализ с выводом во временную папку
if ./admin_panel/DPy analyze -i admin_panel/ -o "${TEMP_RESULTS_DIR}/"; then
    echo "✅ Анализ завершен успешно"

    # Перемещаем и переименовываем файлы результатов в соответствующую структуру
    if [ -f "${TEMP_RESULTS_DIR}/admin_panel_arch_smells.json" ]; then
        mv "${TEMP_RESULTS_DIR}/admin_panel_arch_smells.json" "${ANALYSIS_DIR}/architecture_smells/"
        echo "📁 Архитектурные проблемы перемещены"
    fi

    if [ -f "${TEMP_RESULTS_DIR}/admin_panel_design_smells.json" ]; then
        mv "${TEMP_RESULTS_DIR}/admin_panel_design_smells.json" "${ANALYSIS_DIR}/design_smells/"
        echo "📁 Проблемы проектирования перемещены"
    fi

    if [ -f "${TEMP_RESULTS_DIR}/admin_panel_implementation_smells.json" ]; then
        mv "${TEMP_RESULTS_DIR}/admin_panel_implementation_smells.json" "${ANALYSIS_BASE_DIR}/implementation_smells/"
        echo "📁 Проблемы реализации перемещены"
    fi

    # Перемещаем метрики
    if [ -f "${TEMP_RESULTS_DIR}/admin_panel_class_module_metrics.json" ]; then
        mv "${TEMP_RESULTS_DIR}/admin_panel_class_module_metrics.json" "${ANALYSIS_DIR}/metrics/"
        echo "📊 Метрики классов и модулей перемещены"
    fi

    if [ -f "${TEMP_RESULTS_DIR}/admin_panel_function_metrics.json" ]; then
        mv "${TEMP_RESULTS_DIR}/admin_panel_function_metrics.json" "${ANALYSIS_BASE_DIR}/metrics/"
        echo "📊 Метрики функций перемещены"
    fi

    # Перемещаем логи если они есть
    if ls "${TEMP_RESULTS_DIR}"/*.log 1> /dev/null 2>&1; then
        mv "${TEMP_RESULTS_DIR}"/*.log "${ANALYSIS_DIR}/logs/"
        echo "📋 Логи перемещены"
    fi

    # Удаляем временную папку
    rm -rf "${TEMP_RESULTS_DIR}"

    echo ""
    echo "🎉 Анализ завершен! Результаты сохранены в: ${ANALYSIS_DIR}"
    echo ""
    echo "Структура результатов:"
    find "${ANALYSIS_DIR}" -type f -name "*.json" | sort

else
    echo "❌ Ошибка при выполнении анализа"
    exit 1
fi