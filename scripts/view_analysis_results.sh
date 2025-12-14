#!/bin/bash

# Скрипт для просмотра результатов анализа админпанели
# Показывает сводку по найденным проблемам

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для отображения заголовка
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Функция для подсчета проблем в JSON файле
count_smells() {
    local file="$1"
    if [ -f "$file" ]; then
        local count=$(jq '. | length' "$file" 2>/dev/null || echo "0")
        echo "$count"
    else
        echo "0"
    fi
}

# Получаем последнюю папку анализа (самый свежий по времени)
if [ -d "analysis_results" ]; then
    # Находим все подпапки с временными метками (глубина 2), сортируем по времени модификации
    LATEST_ANALYSIS=$(find analysis_results -mindepth 2 -maxdepth 2 -type d -name "*_*" | xargs ls -td | head -1)
    ANALYSIS_DIR="${LATEST_ANALYSIS}"

    if [ -d "$ANALYSIS_DIR" ]; then
        # Извлекаем дату из пути (YYYY-MM-DD из YYYY-MM-DD/HH-MM-SS)
        ANALYSIS_DATE=$(basename "$(dirname "$ANALYSIS_DIR")")
        ANALYSIS_TIME=$(basename "$ANALYSIS_DIR")
        echo -e "${GREEN}📊 Найден последний анализ от: ${ANALYSIS_DATE} ${ANALYSIS_TIME}${NC}"
        echo ""

        # Архитектурные проблемы
        # Архитектурные проблемы
        ARCH_FILE="${ANALYSIS_DIR}/architecture_smells/admin_panel_arch_smells.json"
        ARCH_COUNT=$(count_smells "$ARCH_FILE")

        # Проблемы проектирования
        DESIGN_FILE="${ANALYSIS_DIR}/design_smells/admin_panel_design_smells.json"
        DESIGN_COUNT=$(count_smells "$DESIGN_FILE")

        # Проблемы реализации
        IMPL_FILE="${ANALYSIS_DIR}/implementation_smells/admin_panel_implementation_smells.json"
        IMPL_COUNT=$(count_smells "$IMPL_FILE")

        print_header "АНАЛИЗ АДМИНПАНЕЛИ - СВОДКА"

        echo -e "${YELLOW}📁 Архитектурные проблемы:${NC} ${RED}${ARCH_COUNT}${NC}"
        if [ "$ARCH_COUNT" -gt 0 ]; then
            echo "   Расположение: ${ARCH_FILE}"
        fi
        echo ""

        echo -e "${YELLOW}🎯 Проблемы проектирования:${NC} ${RED}${DESIGN_COUNT}${NC}"
        if [ "$DESIGN_COUNT" -gt 0 ]; then
            echo "   Расположение: ${DESIGN_FILE}"
        fi
        echo ""

        echo -e "${YELLOW}💻 Проблемы реализации:${NC} ${RED}${IMPL_COUNT}${NC}"
        if [ "$IMPL_COUNT" -gt 0 ]; then
            echo "   Расположение: ${IMPL_FILE}"
        fi
        echo ""

        # Показываем метрики
        METRICS_DIR="${ANALYSIS_DIR}/metrics"
        if [ -d "$METRICS_DIR" ]; then
            echo -e "${BLUE}📊 Метрики кода:${NC}"
            ls -1 "${METRICS_DIR}"/*.json 2>/dev/null | while read -r file; do
                echo "   $(basename "$file")"
            done
            echo ""
        fi

        # Общая статистика
        TOTAL_SMELLS=$((ARCH_COUNT + DESIGN_COUNT + IMPL_COUNT))

        if [ "$TOTAL_SMELLS" -eq 0 ]; then
            echo -e "${GREEN}✅ Поздравляем! Критических проблем не найдено.${NC}"
        else
            echo -e "${YELLOW}⚠️  Всего обнаружено проблем: ${RED}${TOTAL_SMELLS}${NC}"
            echo ""
            echo -e "${BLUE}Для детального просмотра используйте:${NC}"
            echo "  cat '${ARCH_FILE}' | jq ."
            echo "  cat '${DESIGN_FILE}' | jq ."
            echo "  cat '${IMPL_FILE}' | jq ."
        fi

    else
        echo -e "${RED}❌ Папка анализа не найдена: ${ANALYSIS_DIR}${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ Директория analysis_results не найдена${NC}"
    echo -e "${YELLOW}💡 Сначала запустите: ./scripts/analyze_admin_panel.sh${NC}"
    exit 1
fi