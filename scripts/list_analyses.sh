#!/bin/bash

# Скрипт для просмотра истории всех анализов админпанели

set -e

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}📊 ИСТОРИЯ АНАЛИЗОВ АДМИНПАНЕЛИ${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

if [ -d "analysis_results" ]; then
    # Находим все уникальные анализы (только папки с форматом YYYY-MM-DD_HH-MM-SS)
    ANALYSES=$(find analysis_results -mindepth 2 -maxdepth 2 -type d | grep -E "[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}-[0-9]{2}-[0-9]{2}$" | xargs ls -td)

    if [ -z "$ANALYSES" ]; then
        echo -e "${YELLOW}⚠️  Уникальных анализов не найдено${NC}"
        echo -e "${GREEN}💡 Запустите: ./scripts/analyze_admin_panel.sh${NC}"
        exit 0
    fi

    COUNTER=1
    echo "$ANALYSES" | while read -r analysis_dir; do
        # Извлекаем дату и время из пути
        date_part=$(basename "$(dirname "$analysis_dir")")
        time_part=$(basename "$analysis_dir")

        # Подсчитываем проблемы в этом анализе
        arch_file="$analysis_dir/architecture_smells/admin_panel_arch_smells.json"
        design_file="$analysis_dir/design_smells/admin_panel_design_smells.json"
        impl_file="$analysis_dir/implementation_smells/admin_panel_implementation_smells.json"

        arch_count=$(jq '. | length' "$arch_file" 2>/dev/null || echo "0")
        design_count=$(jq '. | length' "$design_file" 2>/dev/null || echo "0")
        impl_count=$(jq '. | length' "$impl_file" 2>/dev/null || echo "0")

        total=$((arch_count + design_count + impl_count))

        # Определяем маркер для текущего анализа
        if [ $COUNTER -eq 1 ]; then
            marker="${GREEN}🆕${NC}"
        else
            marker="   "
        fi

        echo -e "$marker $COUNTER. $date_part $time_part"
        echo -e "      📁 Архитектура: $arch_count  🎯 Проектирование: $design_count  💻 Реализация: $impl_count  📊 Всего: $total"

        # Показываем детали для первых 3 анализов
        if [ $COUNTER -le 3 ]; then
            echo -e "      Путь: $analysis_dir"
        fi

        echo ""
        COUNTER=$((COUNTER + 1))
    done

    # Показываем общее количество анализов
    TOTAL_ANALYSES=$(echo "$ANALYSES" | wc -l)
    echo -e "${BLUE}Всего анализов: $TOTAL_ANALYSES${NC}"

else
    echo -e "${YELLOW}⚠️  Директория analysis_results не найдена${NC}"
fi