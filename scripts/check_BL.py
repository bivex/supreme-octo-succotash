#!/usr/bin/env python3
"""
Business Logic Implementation Checker

Анализирует API эндпоинты и проверяет статус реализации бизнес логики.
Сравнивает OpenAPI спецификацию с существующей реализацией, выявляет
mock данные и недостающую функциональность.
"""

import os
import re
import ast
import yaml
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class ImplementationStatus(Enum):
    """Статус реализации эндпоинта."""
    NOT_IMPLEMENTED = "not_implemented"
    MOCK_IMPLEMENTED = "mock_implemented"
    PARTIALLY_IMPLEMENTED = "partially_implemented"
    FULLY_IMPLEMENTED = "fully_implemented"


@dataclass
class EndpointAnalysis:
    """Анализ отдельного эндпоинта."""
    path: str
    method: str
    operation_id: Optional[str]
    summary: Optional[str]
    tags: List[str] = field(default_factory=list)
    status: ImplementationStatus = ImplementationStatus.NOT_IMPLEMENTED
    route_file: Optional[str] = None
    handler_function: Optional[str] = None
    mock_patterns: List[str] = field(default_factory=list)
    missing_components: List[str] = field(default_factory=list)
    implementation_notes: List[str] = field(default_factory=list)


@dataclass
class BusinessLogicReport:
    """Общий отчет о бизнес логике."""
    total_endpoints: int = 0
    implemented_endpoints: int = 0
    mock_endpoints: int = 0
    not_implemented_endpoints: int = 0
    partially_implemented_endpoints: int = 0

    endpoints_by_status: Dict[str, List[EndpointAnalysis]] = field(default_factory=dict)
    endpoints_by_tag: Dict[str, List[EndpointAnalysis]] = field(default_factory=dict)

    critical_missing_features: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class BusinessLogicChecker:
    """Проверяет статус реализации бизнес логики API."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.openapi_path = project_root / "openapi.yaml"
        self.routes_dir = project_root / "src" / "presentation" / "routes"

        # Паттерны mock данных
        self.mock_patterns = [
            r'mock.*response',
            r'fake.*data',
            r'dummy.*result',
            r'test.*response',
            r'hardcoded.*data',
            r'static.*response',
            r'"status":\s*"success"',
            r'"average_ltv":\s*\d+\.\d+',
            r'"total_customers":\s*\d+',
            r'"campaigns":\s*\[',
            r'"lead_id":\s*".*"',
            r'"message":\s*"Form submitted successfully"',
            r'retention.*campaigns.*mock',
            r'welcome.*back.*campaign',
            r'personalized.*message.*segment'
        ]

        # Паттерны реальной реализации
        self.real_implementation_patterns = [
            r'\.save\(',
            r'\.find_by_',
            r'\.get_by_',
            r'\.calculate_',
            r'\.validate_',
            r'\.process_',
            r'\.analyze_',
            r'repository\.',
            r'service\.',
            r'handler\.',
            r'\.create_',
            r'\.update_',
            r'\.delete_'
        ]

    def analyze_business_logic(self) -> BusinessLogicReport:
        """Основной метод анализа бизнес логики."""
        print("🔍 Начинаем анализ бизнес логики API...")

        # Загружаем OpenAPI спецификацию
        openapi_spec = self._load_openapi_spec()
        if not openapi_spec:
            print("❌ Не удалось загрузить OpenAPI спецификацию")
            return BusinessLogicReport()

        # Анализируем эндпоинты
        endpoints = self._extract_endpoints_from_openapi(openapi_spec)
        print(f"📋 Найдено {len(endpoints)} эндпоинтов в OpenAPI спецификации")

        # Анализируем существующие routes
        route_files = self._find_route_files()
        print(f"📁 Найдено {len(route_files)} route файлов")

        # Анализируем каждый эндпоинт
        analyzed_endpoints = []
        for endpoint in endpoints:
            analyzed_endpoint = self._analyze_endpoint(endpoint, route_files)
            analyzed_endpoints.append(analyzed_endpoint)

        # Генерируем отчет
        report = self._generate_report(analyzed_endpoints)

        return report

    def _load_openapi_spec(self) -> Optional[Dict]:
        """Загружает OpenAPI спецификацию."""
        try:
            with open(self.openapi_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"❌ Ошибка загрузки OpenAPI спецификации: {e}")
            return None

    def _extract_endpoints_from_openapi(self, spec: Dict) -> List[Dict]:
        """Извлекает эндпоинты из OpenAPI спецификации."""
        endpoints = []

        if 'paths' not in spec:
            return endpoints

        for path, path_item in spec['paths'].items():
            for method, operation in path_item.items():
                if method.upper() not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    continue

                endpoint = {
                    'path': path,
                    'method': method.upper(),
                    'operation_id': operation.get('operationId'),
                    'summary': operation.get('summary'),
                    'description': operation.get('description'),
                    'tags': operation.get('tags', []),
                    'responses': operation.get('responses', {})
                }
                endpoints.append(endpoint)

        return endpoints

    def _find_route_files(self) -> Dict[str, Path]:
        """Находит все route файлы."""
        route_files = {}
        if not self.routes_dir.exists():
            return route_files

        for file_path in self.routes_dir.glob("*.py"):
            if file_path.name != "__init__.py":
                route_files[file_path.stem] = file_path

        return route_files

    def _analyze_endpoint(self, endpoint: Dict, route_files: Dict[str, Path]) -> EndpointAnalysis:
        """Анализирует отдельный эндпоинт."""
        analysis = EndpointAnalysis(
            path=endpoint['path'],
            method=endpoint['method'],
            operation_id=endpoint.get('operation_id'),
            summary=endpoint.get('summary'),
            tags=endpoint.get('tags', [])
        )

        # Определяем соответствующий route файл
        route_file = self._find_matching_route_file(endpoint, route_files)
        if not route_file:
            analysis.status = ImplementationStatus.NOT_IMPLEMENTED
            analysis.missing_components.append("Route file not found")
            return analysis

        analysis.route_file = route_file

        # Анализируем содержимое route файла
        route_content = self._read_file_content(route_files[route_file])
        if not route_content:
            analysis.status = ImplementationStatus.NOT_IMPLEMENTED
            analysis.missing_components.append("Route file content not readable")
            return analysis

        # Ищем функцию-обработчик
        handler_function = self._find_handler_function(endpoint, route_content)
        analysis.handler_function = handler_function

        if handler_function:
            # Анализируем реализацию обработчика
            status, mock_patterns, missing_components, notes = self._analyze_handler_implementation(
                handler_function, route_content
            )
            analysis.status = status
            analysis.mock_patterns = mock_patterns
            analysis.missing_components = missing_components
            analysis.implementation_notes = notes
        else:
            # Если функция не найдена, проверяем весь файл на mock паттерны
            status, mock_patterns, missing_components, notes = self._analyze_file_implementation(route_content)
            analysis.status = status
            analysis.mock_patterns = mock_patterns
            analysis.missing_components = missing_components + ["Handler function not found"]
            analysis.implementation_notes = notes

        analysis.status = status
        analysis.mock_patterns = mock_patterns
        analysis.missing_components = missing_components
        analysis.implementation_notes = notes

        return analysis

    def _find_matching_route_file(self, endpoint: Dict, route_files: Dict[str, Path]) -> Optional[str]:
        """Находит соответствующий route файл для эндпоинта."""
        path = endpoint['path'].lower()

        # Прямое сопоставление по ключевым словам пути
        path_mappings = {
            'campaign': 'campaign_routes',
            'click': 'click_routes',
            'analytics': 'analytics_routes',
            'fraud': 'fraud_routes',
            'webhook': 'webhook_routes',
            'event': 'event_routes',
            'conversion': 'conversion_routes',
            'postback': 'postback_routes',
            'goal': 'goal_routes',
            'journey': 'journey_routes',
            'ltv': 'ltv_routes',
            'retention': 'retention_routes',
            'form': 'form_routes',
            'bulk': 'bulk_operations_routes',
            'system': 'system_routes',
            'cache': 'system_routes',
            'health': 'system_routes'
        }

        # Ищем совпадения в пути
        for keyword, route_file in path_mappings.items():
            if keyword in path and route_file in route_files:
                return route_file

        # Если прямое сопоставление не сработало, используем fallback логику
        path_parts = endpoint['path'].strip('/').split('/')
        path_keywords = [part.lower() for part in path_parts if not part.startswith('{') and part not in ['v1', 'api']]

        best_match = None
        best_score = 0

        for route_name in route_files.keys():
            score = 0
            route_keywords = route_name.replace('_routes', '').split('_')

            for keyword in path_keywords:
                if keyword in route_keywords:
                    score += 1

            if score > best_score:
                best_score = score
                best_match = route_name

        return best_match if best_score > 0 else None

    def _read_file_content(self, file_path: Path) -> Optional[str]:
        """Читает содержимое файла."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"❌ Ошибка чтения файла {file_path}: {e}")
            return None

    def _find_handler_function(self, endpoint: Dict, route_content: str) -> Optional[str]:
        """Находит функцию-обработчик для эндпоинта."""
        # Ищем паттерны регистрации маршрутов
        method = endpoint['method'].lower()
        path = endpoint['path']

        # Ищем строки вида app.get('/path', handler_function)
        patterns = [
            rf"app\.{method}\(\s*['\"]{re.escape(path)}['\"],\s*(\w+)\s*\)",
            rf"app\.{method}\(\s*['\"]{re.escape(path)}\s*\+\s*[^,]+,\s*(\w+)\s*\)",
        ]

        for pattern in patterns:
            match = re.search(pattern, route_content, re.MULTILINE)
            if match:
                return match.group(1)

        return None

    def _analyze_handler_implementation(self, handler_function: str, route_content: str) -> Tuple[ImplementationStatus, List[str], List[str], List[str]]:
        """Анализирует реализацию функции-обработчика."""
        # Извлекаем функцию из кода
        function_pattern = rf"def\s+{handler_function}\s*\([^)]*\):(.*?)(?=\n\s*def|\n\s*@|\n\s*class|\Z)"
        match = re.search(function_pattern, route_content, re.DOTALL)

        if not match:
            return ImplementationStatus.NOT_IMPLEMENTED, [], ["Function definition not found"], []

        function_body = match.group(1)

        # Анализируем тело функции
        mock_patterns_found = []
        real_patterns_found = []
        missing_components = []
        notes = []

        # Проверяем на mock паттерны
        for pattern in self.mock_patterns:
            if re.search(pattern, function_body, re.IGNORECASE | re.DOTALL):
                mock_patterns_found.append(pattern)

        # Проверяем на паттерны реальной реализации
        for pattern in self.real_implementation_patterns:
            if re.search(pattern, function_body, re.DOTALL):
                real_patterns_found.append(pattern)

        # Определяем статус реализации
        if not function_body.strip() or "pass" in function_body.lower():
            status = ImplementationStatus.NOT_IMPLEMENTED
            missing_components.append("Empty function body")
        elif mock_patterns_found and not real_patterns_found:
            status = ImplementationStatus.MOCK_IMPLEMENTED
            notes.append("Contains only mock data patterns")
        elif real_patterns_found and mock_patterns_found:
            status = ImplementationStatus.PARTIALLY_IMPLEMENTED
            notes.append("Mixed mock and real implementation")
        elif real_patterns_found:
            status = ImplementationStatus.FULLY_IMPLEMENTED
            notes.append("Contains real business logic patterns")
        else:
            status = ImplementationStatus.PARTIALLY_IMPLEMENTED
            missing_components.append("No clear implementation patterns detected")

        return status, mock_patterns_found, missing_components, notes

    def _analyze_file_implementation(self, file_content: str) -> Tuple[ImplementationStatus, List[str], List[str], List[str]]:
        """Анализирует реализацию всего файла."""
        mock_patterns_found = []
        real_patterns_found = []
        missing_components = []
        notes = []

        # Проверяем на mock паттерны во всем файле
        for pattern in self.mock_patterns:
            if re.search(pattern, file_content, re.IGNORECASE | re.DOTALL):
                mock_patterns_found.append(pattern)

        # Проверяем на паттерны реальной реализации
        for pattern in self.real_implementation_patterns:
            if re.search(pattern, file_content, re.DOTALL):
                real_patterns_found.append(pattern)

        # Определяем статус реализации
        if mock_patterns_found and not real_patterns_found:
            status = ImplementationStatus.MOCK_IMPLEMENTED
            notes.append("File contains mock data patterns")
        elif real_patterns_found:
            status = ImplementationStatus.FULLY_IMPLEMENTED
            notes.append("File contains real business logic")
        else:
            status = ImplementationStatus.NOT_IMPLEMENTED
            missing_components.append("No implementation patterns detected")

        return status, mock_patterns_found, missing_components, notes

    def _generate_report(self, endpoints: List[EndpointAnalysis]) -> BusinessLogicReport:
        """Генерирует отчет о статусе реализации."""
        report = BusinessLogicReport()
        report.total_endpoints = len(endpoints)

        # Группируем по статусу
        status_groups = {}
        tag_groups = {}

        for endpoint in endpoints:
            # По статусу
            status_key = endpoint.status.value
            if status_key not in status_groups:
                status_groups[status_key] = []
            status_groups[status_key].append(endpoint)

            # По тегам
            for tag in endpoint.tags:
                if tag not in tag_groups:
                    tag_groups[tag] = []
                tag_groups[tag].append(endpoint)

        report.endpoints_by_status = status_groups
        report.endpoints_by_tag = tag_groups

        # Подсчитываем статистики
        for status, endpoints_list in status_groups.items():
            count = len(endpoints_list)
            if status == ImplementationStatus.FULLY_IMPLEMENTED.value:
                report.implemented_endpoints = count
            elif status == ImplementationStatus.MOCK_IMPLEMENTED.value:
                report.mock_endpoints = count
            elif status == ImplementationStatus.NOT_IMPLEMENTED.value:
                report.not_implemented_endpoints = count
            elif status == ImplementationStatus.PARTIALLY_IMPLEMENTED.value:
                report.partially_implemented_endpoints = count

        # Генерируем рекомендации
        report.recommendations = self._generate_recommendations(endpoints)
        report.critical_missing_features = self._identify_critical_missing_features(endpoints)

        return report

    def _generate_recommendations(self, endpoints: List[EndpointAnalysis]) -> List[str]:
        """Генерирует рекомендации по улучшению."""
        recommendations = []

        mock_endpoints = [e for e in endpoints if e.status == ImplementationStatus.MOCK_IMPLEMENTED]
        if mock_endpoints:
            recommendations.append(f"Заменить mock данные в {len(mock_endpoints)} эндпоинтах реальной бизнес логикой")

        not_implemented = [e for e in endpoints if e.status == ImplementationStatus.NOT_IMPLEMENTED]
        if not_implemented:
            recommendations.append(f"Реализовать {len(not_implemented)} отсутствующих эндпоинтов")

        # Проверяем наличие основных доменов
        tags = set()
        for endpoint in endpoints:
            tags.update(endpoint.tags)

        missing_domains = []
        if 'ltv' not in tags:
            missing_domains.append('LTV analysis')
        if 'retention' not in tags:
            missing_domains.append('Retention campaigns')
        if 'forms' not in tags:
            missing_domains.append('Lead forms')

        if missing_domains:
            recommendations.append(f"Добавить домены: {', '.join(missing_domains)}")

        return recommendations

    def _identify_critical_missing_features(self, endpoints: List[EndpointAnalysis]) -> List[str]:
        """Идентифицирует критически важные отсутствующие функции."""
        critical_features = []

        # Проверяем наличие основных бизнес-функций
        has_campaign_management = any('campaign' in e.tags for e in endpoints)
        has_click_tracking = any('click' in e.tags for e in endpoints)
        has_analytics = any('analytics' in e.tags for e in endpoints)

        if not has_campaign_management:
            critical_features.append("Campaign management endpoints")
        if not has_click_tracking:
            critical_features.append("Click tracking functionality")
        if not has_analytics:
            critical_features.append("Analytics and reporting")

        # Проверяем на mock реализации в критичных областях
        critical_mock = [
            e for e in endpoints
            if e.status == ImplementationStatus.MOCK_IMPLEMENTED and
            any(tag in ['campaign', 'analytics', 'security'] for tag in e.tags)
        ]

        if critical_mock:
            critical_features.append(f"Mock реализации в критичных областях: {len(critical_mock)} эндпоинтов")

        return critical_features


def print_report(report: BusinessLogicReport):
    """Выводит отчет в консоль."""
    print("\n" + "="*80)
    print("📊 ОТЧЕТ О РЕАЛИЗАЦИИ БИЗНЕС ЛОГИКИ API")
    print("="*80)

    print(f"\n📈 ОБЩАЯ СТАТИСТИКА:")
    print(f"  Всего эндпоинтов: {report.total_endpoints}")
    print(f"  Полностью реализовано: {report.implemented_endpoints}")
    print(f"  Mock данные: {report.mock_endpoints}")
    print(f"  Частично реализовано: {report.partially_implemented_endpoints}")
    print(f"  Не реализовано: {report.not_implemented_endpoints}")

    if report.endpoints_by_status:
        print(f"\n🔍 ПОДРОБНЫЙ АНАЛИЗ ПО СТАТУСУ:")

        for status, endpoints in report.endpoints_by_status.items():
            status_name = {
                'fully_implemented': '✅ Полностью реализовано',
                'mock_implemented': '⚠️  Mock данные',
                'partially_implemented': '🔄 Частично реализовано',
                'not_implemented': '❌ Не реализовано'
            }.get(status, status)

            print(f"\n  {status_name} ({len(endpoints)} эндпоинтов):")
            for endpoint in endpoints[:5]:  # Показываем первые 5
                tags = ', '.join(endpoint.tags) if endpoint.tags else 'без тегов'
                print(f"    • {endpoint.method} {endpoint.path} ({tags})")
                if endpoint.mock_patterns:
                    print(f"      Mock паттерны: {len(endpoint.mock_patterns)}")
                if endpoint.missing_components:
                    print(f"      Проблемы: {', '.join(endpoint.missing_components)}")

            if len(endpoints) > 5:
                print(f"    ... и ещё {len(endpoints) - 5} эндпоинтов")

    if report.critical_missing_features:
        print(f"\n🚨 КРИТИЧЕСКИ ВАЖНЫЕ ПРОБЛЕМЫ:")
        for feature in report.critical_missing_features:
            print(f"  • {feature}")

    if report.recommendations:
        print(f"\n💡 РЕКОМЕНДАЦИИ:")
        for rec in report.recommendations:
            print(f"  • {rec}")

    print(f"\n" + "="*80)


def main():
    """Основная функция."""
    project_root = Path(__file__).parent.parent

    checker = BusinessLogicChecker(project_root)
    report = checker.analyze_business_logic()

    print_report(report)

    # Сохраняем отчет в JSON
    report_data = {
        'total_endpoints': report.total_endpoints,
        'implemented_endpoints': report.implemented_endpoints,
        'mock_endpoints': report.mock_endpoints,
        'not_implemented_endpoints': report.not_implemented_endpoints,
        'partially_implemented_endpoints': report.partially_implemented_endpoints,
        'critical_missing_features': report.critical_missing_features,
        'recommendations': report.recommendations,
        'endpoints_by_status': {
            status: [
                {
                    'path': e.path,
                    'method': e.method,
                    'tags': e.tags,
                    'route_file': e.route_file,
                    'mock_patterns': e.mock_patterns,
                    'missing_components': e.missing_components
                } for e in endpoints
            ] for status, endpoints in report.endpoints_by_status.items()
        }
    }

    with open(project_root / 'business_logic_report.json', 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    print("💾 Отчет сохранен в business_logic_report.json")


if __name__ == "__main__":
    main()
