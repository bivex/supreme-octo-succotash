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

        # Улучшенные паттерны mock данных
        self.mock_patterns = [
            # Базовые mock паттерны
            r'mock.*response',
            r'fake.*data',
            r'dummy.*result',
            r'test.*response',
            r'hardcoded.*data',
            r'static.*response',

            # JSON структуры с hardcoded данными
            r'"status":\s*"success"',
            r'"status":\s*"ok"',
            r'"status":\s*"error"',
            r'"message":\s*"[^*]*successfully[^"]*"',
            r'"message":\s*"[^*]*success[^"]*"',

            # Метрики с фиксированными числами
            r'"average_ltv":\s*\d+\.\d+',
            r'"total_customers":\s*\d+',
            r'"conversion_rate":\s*\d+\.\d+',
            r'"clicks":\s*\d+',
            r'"impressions":\s*\d+',

            # Массивы с тестовыми данными
            r'"campaigns":\s*\[',
            r'"leads":\s*\[',
            r'"clicks":\s*\[',
            r'"events":\s*\[',

            # Идентификаторы с тестовыми значениями
            r'"lead_id":\s*".*"',
            r'"campaign_id":\s*".*"',
            r'"click_id":\s*".*"',

            # Специфические домены
            r'retention.*campaigns.*mock',
            r'welcome.*back.*campaign',
            r'personalized.*message.*segment',

            # Общие mock ответы
            r'return\s*\{[^}]*"status":\s*"success"[^}]*\}',
            r'return\s*\{[^}]*"message":\s*"[^"]*success[^"]*"[^}]*\}',

            # Empty implementations
            r'return\s*\{\s*\}',
            r'return\s*None',
            r'pass\s*$',
        ]

        # Улучшенные паттерны реальной реализации
        self.real_implementation_patterns = [
            # Репозиторийные операции
            r'\.save\(',
            r'\.find_by_',
            r'\.get_by_',
            r'\.find_all\(',
            r'\.count_by_',
            r'\.delete\(',
            r'\.update\(',
            r'\.create\(',

            # Сервисные операции
            r'\.calculate_',
            r'\.validate_',
            r'\.process_',
            r'\.analyze_',
            r'\.generate_',
            r'\.enrich_',
            r'\.filter_',
            r'\.aggregate_',

            # Бизнес-логика паттерны
            r'repository\.',
            r'service\.',
            r'handler\.',
            r'factory\.',
            r'manager\.',

            # Асинхронные операции
            r'await\s+\w+\.',
            r'async\s+def',

            # Комплексные выражения
            r'if\s+.*repository',
            r'for\s+.*in\s+.*repository',
            r'with\s+.*repository',

            # Валидация и обработка ошибок
            r'try:',
            r'except\s+\w+:',
            r'raise\s+\w+',

            # Работа с данными
            r'json\.dumps',
            r'json\.loads',
            r'\.to_dict\(\)',
            r'\.from_dict\(',
            r'\.serialize',
            r'\.deserialize',

            # HTTP клиенты и внешние API
            r'requests\.',
            r'httpx\.',
            r'aiohttp\.',

            # База данных
            r'\.execute\(',
            r'\.commit\(\)',
            r'\.rollback\(\)',
            r'SELECT\s+.*FROM',
            r'INSERT\s+INTO',
            r'UPDATE\s+.*SET',
            r'DELETE\s+FROM',

            # Специфические паттерны нашей архитектуры
            r'CampaignRepository',
            r'AnalyticsRepository',
            r'EventRepository',
            r'ConversionRepository',
            r'LandingPageRepository',
            r'OfferRepository',
            r'CampaignService',
            r'AnalyticsService',
            r'EventService',

            # CQRS паттерны
            r'Query\(',
            r'Command\(',
            r'Handler\(',
            r'QueryHandler',
            r'CommandHandler',
            r'GetCampaignQuery',
            r'GetCampaignAnalyticsQuery',
            r'GetCampaignLandingPagesQuery',
            r'GetCampaignOffersQuery',

            # Dependency Injection паттерны
            r'container\.',
            r'_container\.',
            r'get_campaign_repository',
            r'get_analytics_repository',
            r'get_event_repository',
            r'get_campaign_handler',
            r'get_analytics_handler',

            # Middleware паттерны
            r'middleware\.',
            r'validate_request',
            r'add_security_headers',

            # Pagination паттерны
            r'page\s*=',
            r'pageSize\s*=',
            r'limit\s*=',
            r'offset\s*=',
            r'pagination',
            r'total_count',
            r'total_pages',

            # Domain паттерны
            r'Campaign\(',
            r'CampaignId\(',
            r'Event\(',
            r'Conversion\(',
            r'Money\(',
            r'DateRange\(',
            r'Analytics\(',

            # Logger паттерны
            r'logger\.',
            r'logger\.error',
            r'logger\.info',
            r'logger\.debug',
            r'traceback\.',

            # Специфические утилиты
            r'money_to_dict',
            r'datetime\.',
            r'date\.',
        ]

    def analyze_business_logic(self) -> BusinessLogicReport:
        """Основной метод анализа бизнес логики с улучшенными алгоритмами."""
        print("🔍 Начинаем комплексный анализ бизнес логики API...")
        print("=" * 60)

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

        # Предварительный анализ - проверяем актуальность OpenAPI
        spec_freshness = self._analyze_openapi_freshness(openapi_spec, route_files)
        if spec_freshness['issues']:
            print(f"⚠️  Проблемы с актуальностью OpenAPI: {len(spec_freshness['issues'])}")

        # Детальный анализ каждого эндпоинта
        print("\n🔎 Анализируем endpoints...")
        analyzed_endpoints = []
        processed_count = 0

        for endpoint in endpoints:
            analyzed_endpoint = self._analyze_endpoint(endpoint, route_files)
            analyzed_endpoints.append(analyzed_endpoint)

            processed_count += 1
            if processed_count % 10 == 0:
                print(f"  ✓ Обработано {processed_count}/{len(endpoints)} endpoints")

        print(f"✅ Анализ завершен: {len(analyzed_endpoints)} endpoints")

        # Генерируем расширенный отчет
        report = self._generate_report(analyzed_endpoints)

        # Добавляем дополнительную аналитику
        report = self._enhance_report_with_advanced_analytics(report, analyzed_endpoints, spec_freshness)

        return report

    def _analyze_openapi_freshness(self, spec: Dict, route_files: Dict[str, Path]) -> Dict[str, List[str]]:
        """Анализирует актуальность OpenAPI спецификации."""
        issues = []

        # Проверяем, есть ли новые route файлы, не отраженные в спецификации
        spec_paths = set()
        if 'paths' in spec:
            spec_paths = set(spec['paths'].keys())

        route_paths = set()
        for route_file, file_path in route_files.items():
            content = self._read_file_content(file_path)
            if content:
                # Ищем все пути в route файле
                path_patterns = [
                    r"app\.\w+\(\s*['\"]([^'\"]+)['\"]",
                    r"app\.\w+\(\s*f?['\"]([^'\"]+)['\"]"
                ]

                for pattern in path_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        route_paths.add(match)

        # Находим новые пути
        new_paths = route_paths - spec_paths
        if new_paths:
            issues.append(f"Найдено {len(new_paths)} новых путей не отраженных в OpenAPI")

        return {'issues': issues, 'new_paths': list(new_paths)}

    def _enhance_report_with_advanced_analytics(self, report: BusinessLogicReport, endpoints: List[EndpointAnalysis], spec_freshness: Dict) -> BusinessLogicReport:
        """Добавляет расширенную аналитику в отчет."""
        # Добавляем информацию о свежести спецификации
        if spec_freshness['issues']:
            report.critical_missing_features.extend([
                f"OpenAPI Spec Issue: {issue}" for issue in spec_freshness['issues']
            ])

        # Добавляем метрики качества
        quality_metrics = self._calculate_quality_metrics(endpoints)
        if quality_metrics:
            report.recommendations.extend([
                f"📊 Качество: {metric}" for metric in quality_metrics
            ])

        return report

    def _calculate_quality_metrics(self, endpoints: List[EndpointAnalysis]) -> List[str]:
        """Вычисляет метрики качества реализации."""
        metrics = []

        implemented_endpoints = [e for e in endpoints if e.status == ImplementationStatus.FULLY_IMPLEMENTED]

        if implemented_endpoints:
            # Среднее количество компонентов на endpoint
            avg_components = sum(len(e.implementation_notes) for e in implemented_endpoints) / len(implemented_endpoints)
            metrics.append(f"Среднее кол-во компонентов: {avg_components:.1f}")

            # Процент endpoints с error handling
            with_error_handling = sum(1 for e in implemented_endpoints
                                    if any('error' in note.lower() for note in e.implementation_notes))
            error_handling_pct = (with_error_handling / len(implemented_endpoints)) * 100
            metrics.append(f"Error handling coverage: {error_handling_pct:.1f}%")

            # Процент endpoints с валидацией
            with_validation = sum(1 for e in implemented_endpoints
                                if any('valid' in note.lower() for note in e.implementation_notes))
            validation_pct = (with_validation / len(implemented_endpoints)) * 100
            metrics.append(f"Validation coverage: {validation_pct:.1f}%")

        return metrics

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
        """Находит соответствующий route файл для эндпоинта с улучшенным алгоритмом."""
        path = endpoint['path'].lower()
        method = endpoint['method'].lower()

        # Улучшенное сопоставление по ключевым словам пути
        path_mappings = {
            # Основные домены
            'campaign': 'campaign_routes',
            'campaigns': 'campaign_routes',
            'click': 'click_routes',
            'clicks': 'click_routes',
            'analytics': 'analytics_routes',
            'fraud': 'fraud_routes',
            'webhook': 'webhook_routes',
            'webhooks': 'webhook_routes',
            'event': 'event_routes',
            'events': 'event_routes',
            'conversion': 'conversion_routes',
            'conversions': 'conversion_routes',
            'postback': 'postback_routes',
            'postbacks': 'postback_routes',
            'goal': 'goal_routes',
            'goals': 'goal_routes',
            'journey': 'journey_routes',
            'journeys': 'journey_routes',
            'ltv': 'ltv_routes',
            'retention': 'retention_routes',
            'form': 'form_routes',
            'forms': 'form_routes',
            'bulk': 'bulk_operations_routes',
            'system': 'system_routes',
            'cache': 'system_routes',
            'health': 'system_routes',
            'status': 'system_routes',
        }

        # Проверяем точные совпадения в пути
        for keyword, route_file in path_mappings.items():
            if keyword in path and route_file in route_files:
                return route_file

        # Анализируем структуру пути для более точного сопоставления
        path_parts = [part for part in path.strip('/').split('/') if part and not part.startswith('{')]
        path_keywords = set()

        for part in path_parts:
            # Разбиваем составные слова
            words = re.findall(r'[a-zA-Z]+', part.lower())
            path_keywords.update(words)

        # Исключаем общие слова
        exclude_words = {'v1', 'api', 'id', 'ids', 'list', 'get', 'create', 'update', 'delete'}
        path_keywords -= exclude_words

        if not path_keywords:
            return None

        # Оцениваем каждый route файл
        best_match = None
        best_score = 0
        best_confidence = 0

        for route_name in route_files.keys():
            # Извлекаем ключевые слова из имени route файла
            route_keywords = set()
            route_base = route_name.replace('_routes', '')

            # Разбиваем на отдельные слова
            words = re.findall(r'[a-zA-Z]+', route_base.lower())
            route_keywords.update(words)

            # Вычисляем оценку совпадения
            common_keywords = path_keywords & route_keywords
            score = len(common_keywords)

            # Бонус за точное совпадение первого ключевого слова
            if path_keywords and route_keywords and list(path_keywords)[0] in route_keywords:
                score += 2

            # Штраф за нерелевантные совпадения
            if 'system' in route_keywords and not any(word in path for word in ['health', 'cache', 'status']):
                score -= 1

            # Confidence - процент совпадения
            total_keywords = len(path_keywords | route_keywords)
            confidence = score / max(total_keywords, 1) if total_keywords > 0 else 0

            # Выбираем лучший результат
            if score > best_score or (score == best_score and confidence > best_confidence):
                best_score = score
                best_confidence = confidence
                best_match = route_name

        # Возвращаем результат только если уверенность достаточно высока
        return best_match if best_confidence > 0.2 and best_score > 0 else None

    def _read_file_content(self, file_path: Path) -> Optional[str]:
        """Читает содержимое файла."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"❌ Ошибка чтения файла {file_path}: {e}")
            return None

    def _find_handler_function(self, endpoint: Dict, route_content: str) -> Optional[str]:
        """Находит функцию-обработчик для эндпоинта с улучшенным алгоритмом."""
        method = endpoint['method'].lower()
        path = endpoint['path']

        # Экранируем специальные символы в пути
        escaped_path = re.escape(path)

        # Более гибкие паттерны для поиска регистрации маршрутов
        patterns = [
            # Стандартный формат: app.method('path', handler)
            rf"app\.{method}\(\s*['\"]{escaped_path}['\"]\s*,\s*(\w+)\s*\)",

            # С переменными в пути: app.method('path' + var, handler)
            rf"app\.{method}\(\s*['\"]{escaped_path}\s*\+\s*[^,]+,\s*(\w+)\s*\)",

            # С форматированием строк: app.method(f'path', handler)
            rf"app\.{method}\(\s*f?['\"]{escaped_path}['\"],\s*(\w+)\s*\)",

            # С дополнительными параметрами: app.method('path', handler, ...)
            rf"app\.{method}\(\s*['\"]{escaped_path}['\"]\s*,\s*(\w+)\s*[,)]",

            # Многострочный формат
            rf"app\.{method}\(\s*['\"]{escaped_path}['\"]\s*,\s*\n?\s*(\w+)\s*\)",
        ]

        # Ищем по всем паттернам
        for pattern in patterns:
            match = re.search(pattern, route_content, re.MULTILINE | re.DOTALL)
            if match:
                function_name = match.group(1)
                # Проверяем, что это действительно имя функции (не переменная)
                if self._is_function_name(function_name, route_content):
                    return function_name

        # Fallback: ищем функции, которые могут обрабатывать этот путь
        # на основе комментариев или имен
        return self._find_handler_by_context(endpoint, route_content)

    def _is_function_name(self, name: str, content: str) -> bool:
        """Проверяет, является ли строка именем функции."""
        # Проверяем, что это не ключевое слово или переменная
        if name in ['None', 'True', 'False', 'self']:
            return False

        # Ищем определение функции с этим именем
        function_pattern = rf"def\s+{re.escape(name)}\s*\("
        return bool(re.search(function_pattern, content))

    def _find_handler_by_context(self, endpoint: Dict, route_content: str) -> Optional[str]:
        """Ищет обработчик по контексту (комментарии, имена функций)."""
        path = endpoint['path'].lower()
        method = endpoint['method'].lower()

        # Извлекаем ключевые слова из пути
        path_keywords = re.findall(r'[a-zA-Z]+', path)
        path_keywords = [kw.lower() for kw in path_keywords if len(kw) > 2 and kw not in ['api', 'v1']]

        # Ищем функции, которые могут обрабатывать этот endpoint
        function_pattern = r"def\s+(\w+)\s*\("
        functions = re.findall(function_pattern, route_content)

        best_match = None
        best_score = 0

        for func_name in functions:
            score = 0

            # Проверяем имя функции
            func_lower = func_name.lower()
            if any(keyword in func_lower for keyword in path_keywords):
                score += 2

            # Проверяем комментарии перед функцией
            func_start = route_content.find(f"def {func_name}")
            if func_start > 0:
                # Ищем комментарии в предыдущих 5 строках
                lines_before = route_content[:func_start].split('\n')[-5:]
                comment_text = '\n'.join(lines_before).lower()

                if any(keyword in comment_text for keyword in path_keywords):
                    score += 1

                if method in comment_text:
                    score += 1

            if score > best_score:
                best_score = score
                best_match = func_name

        return best_match if best_score > 1 else None

    def _analyze_handler_implementation(self, handler_function: str, route_content: str) -> Tuple[ImplementationStatus, List[str], List[str], List[str]]:
        """Анализирует реализацию функции-обработчика с улучшенным алгоритмом."""
        # Извлекаем функцию из кода с учетом отступов
        function_pattern = rf"def\s+{re.escape(handler_function)}\s*\([^)]*\):(.*?)(?=\n\S|\n\s*def|\n\s*@|\n\s*class|\Z)"
        match = re.search(function_pattern, route_content, re.DOTALL)

        if not match:
            return ImplementationStatus.NOT_IMPLEMENTED, [], ["Function definition not found"], []

        function_body = match.group(1)

        # Очищаем тело функции от комментариев и пустых строк для лучшего анализа
        cleaned_body = self._clean_function_body(function_body)

        # Расширенный анализ
        analysis_result = self._comprehensive_implementation_analysis(cleaned_body)

        return analysis_result

    def _clean_function_body(self, body: str) -> str:
        """Очищает тело функции для анализа."""
        # Удаляем комментарии
        body = re.sub(r'#.*$', '', body, flags=re.MULTILINE)
        # Удаляем пустые строки
        body = re.sub(r'\n\s*\n', '\n', body)
        # Удаляем лишние пробелы
        body = body.strip()
        return body

    def _comprehensive_implementation_analysis(self, function_body: str) -> Tuple[ImplementationStatus, List[str], List[str], List[str]]:
        """Комплексный анализ реализации функции."""
        mock_patterns_found = []
        real_patterns_found = []
        missing_components = []
        notes = []

        # Анализируем по категориям
        has_business_logic = False
        has_data_access = False
        has_error_handling = False
        has_validation = False
        has_external_calls = False

        # 1. Проверяем на mock паттерны
        for pattern in self.mock_patterns:
            if re.search(pattern, function_body, re.IGNORECASE | re.DOTALL):
                mock_patterns_found.append(pattern)

        # 2. Проверяем на паттерны реальной реализации
        for pattern in self.real_implementation_patterns:
            if re.search(pattern, function_body, re.DOTALL):
                real_patterns_found.append(pattern)
                # Определяем категории реализации
                if any(word in pattern for word in ['repository', 'save', 'find_by', 'get_by', 'delete', 'update']):
                    has_data_access = True
                if any(word in pattern for word in ['service', 'handler', 'calculate', 'process', 'validate']):
                    has_business_logic = True
                if any(word in pattern for word in ['try:', 'except', 'raise']):
                    has_error_handling = True
                if any(word in pattern for word in ['requests', 'httpx', 'aiohttp']):
                    has_external_calls = True

        # 3. Анализируем структуру кода
        lines = [line.strip() for line in function_body.split('\n') if line.strip()]

        # Проверяем на наличие валидации
        if any('validate' in line.lower() or 'check' in line.lower() for line in lines):
            has_validation = True

        # Проверяем на пустую реализацию
        if not lines or all(line in ['pass', '...', 'return None', 'return {}'] for line in lines):
            return ImplementationStatus.NOT_IMPLEMENTED, [], ["Empty or trivial implementation"], []

        # 4. Определяем статус реализации на основе комплексного анализа
        if mock_patterns_found and not real_patterns_found:
            # Только mock данные
            status = ImplementationStatus.MOCK_IMPLEMENTED
            notes.append("Contains only mock/stub data")
            missing_components.append("Replace mock data with real business logic")

        elif real_patterns_found and not mock_patterns_found:
            # Только реальная реализация
            if has_business_logic and has_data_access:
                status = ImplementationStatus.FULLY_IMPLEMENTED
                notes.append("Complete business logic implementation")
                if has_error_handling:
                    notes.append("Includes error handling")
                if has_validation:
                    notes.append("Includes input validation")
                if has_external_calls:
                    notes.append("Includes external API calls")
            elif has_business_logic or has_data_access:
                status = ImplementationStatus.FULLY_IMPLEMENTED
                notes.append("Basic business logic implementation")
            else:
                status = ImplementationStatus.PARTIALLY_IMPLEMENTED
                notes.append("Contains some real patterns but incomplete")

        elif real_patterns_found and mock_patterns_found:
            # Смешанная реализация
            status = ImplementationStatus.PARTIALLY_IMPLEMENTED
            notes.append("Mixed mock and real implementation")
            notes.append(f"Found {len(real_patterns_found)} real patterns, {len(mock_patterns_found)} mock patterns")

            if has_business_logic and has_data_access:
                notes.append("Has core business logic components")
            else:
                missing_components.append("Core business logic components missing")

        else:
            # Нет четких паттернов
            status = ImplementationStatus.PARTIALLY_IMPLEMENTED
            missing_components.append("No clear implementation patterns detected")
            notes.append("Requires manual review")

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
        """Генерирует улучшенные рекомендации по улучшению."""
        recommendations = []

        # Анализ по статусам
        status_counts = {}
        for endpoint in endpoints:
            status_counts[endpoint.status] = status_counts.get(endpoint.status, 0) + 1

        # Рекомендации по mock данным
        mock_count = status_counts.get(ImplementationStatus.MOCK_IMPLEMENTED, 0)
        if mock_count > 0:
            recommendations.append(f"🔄 Заменить mock данные в {mock_count} эндпоинтах реальной бизнес логикой")

        # Рекомендации по нереализованным endpoint'ам
        not_implemented_count = status_counts.get(ImplementationStatus.NOT_IMPLEMENTED, 0)
        if not_implemented_count > 0:
            recommendations.append(f"📝 Реализовать {not_implemented_count} отсутствующих эндпоинтов")

        # Рекомендации по частично реализованным
        partial_count = status_counts.get(ImplementationStatus.PARTIALLY_IMPLEMENTED, 0)
        if partial_count > 0:
            recommendations.append(f"⚡ Завершить реализацию {partial_count} частично реализованных эндпоинтов")

        # Анализ покрытия доменов
        domain_coverage = self._analyze_domain_coverage(endpoints)
        if domain_coverage['missing']:
            recommendations.append(f"🌟 Добавить недостающие домены: {', '.join(domain_coverage['missing'])}")

        # Анализ качества реализации
        quality_issues = self._analyze_implementation_quality(endpoints)
        recommendations.extend(quality_issues)

        # Приоритизация по бизнес-ценности
        priority_recs = self._prioritize_by_business_value(endpoints)
        recommendations.extend(priority_recs)

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

    def _analyze_domain_coverage(self, endpoints: List[EndpointAnalysis]) -> Dict[str, List[str]]:
        """Анализирует покрытие бизнес-доменов."""
        # Собираем все теги
        all_tags = set()
        for endpoint in endpoints:
            all_tags.update(endpoint.tags)

        # Определяем ожидаемые домены
        expected_domains = {
            'campaigns': ['campaign', 'campaigns'],
            'analytics': ['analytics'],
            'click_tracking': ['click', 'clicks'],
            'fraud_detection': ['fraud'],
            'webhooks': ['webhook', 'webhooks'],
            'events': ['event', 'events'],
            'conversions': ['conversion', 'conversions'],
            'postbacks': ['postback', 'postbacks'],
            'goals': ['goal', 'goals'],
            'journeys': ['journey', 'journeys'],
            'ltv': ['ltv'],
            'retention': ['retention'],
            'forms': ['form', 'forms'],
            'system': ['system', 'health', 'cache']
        }

        missing_domains = []
        for domain, tags in expected_domains.items():
            if not any(tag in all_tags for tag in tags):
                # Преобразуем в читаемые названия
                domain_names = {
                    'campaigns': 'Campaign Management',
                    'analytics': 'Analytics & Reporting',
                    'click_tracking': 'Click Tracking',
                    'fraud_detection': 'Fraud Detection',
                    'webhooks': 'Webhooks',
                    'events': 'Event Tracking',
                    'conversions': 'Conversion Tracking',
                    'postbacks': 'Postback System',
                    'goals': 'Goal Management',
                    'journeys': 'User Journey Analytics',
                    'ltv': 'LTV Analysis',
                    'retention': 'Retention Campaigns',
                    'forms': 'Lead Forms',
                    'system': 'System Management'
                }
                missing_domains.append(domain_names.get(domain, domain))

        return {'present': list(all_tags), 'missing': missing_domains}

    def _analyze_implementation_quality(self, endpoints: List[EndpointAnalysis]) -> List[str]:
        """Анализирует качество реализации."""
        issues = []

        # Проверяем наличие error handling
        endpoints_with_error_handling = 0
        endpoints_with_validation = 0

        for endpoint in endpoints:
            if endpoint.status in [ImplementationStatus.FULLY_IMPLEMENTED, ImplementationStatus.PARTIALLY_IMPLEMENTED]:
                # Проверяем implementation_notes на наличие error handling и validation
                notes_text = ' '.join(endpoint.implementation_notes).lower()
                if 'error' in notes_text or 'exception' in notes_text:
                    endpoints_with_error_handling += 1
                if 'valid' in notes_text or 'check' in notes_text:
                    endpoints_with_validation += 1

        total_implemented = sum(1 for e in endpoints if e.status in [ImplementationStatus.FULLY_IMPLEMENTED, ImplementationStatus.PARTIALLY_IMPLEMENTED])

        if total_implemented > 0:
            error_handling_coverage = (endpoints_with_error_handling / total_implemented) * 100
            validation_coverage = (endpoints_with_validation / total_implemented) * 100

            if error_handling_coverage < 70:
                issues.append(f"⚠️  Повысить покрытие error handling: {error_handling_coverage:.1f}% (рекомендуется >70%)")

            if validation_coverage < 60:
                issues.append(f"🔍 Добавить input validation: {validation_coverage:.1f}% (рекомендуется >60%)")

        return issues

    def _prioritize_by_business_value(self, endpoints: List[EndpointAnalysis]) -> List[str]:
        """Приоритизирует задачи по бизнес-ценности."""
        priorities = []

        # Критически важные endpoints без реализации
        critical_endpoints = [
            e for e in endpoints
            if e.status != ImplementationStatus.FULLY_IMPLEMENTED and
            any(tag in ['campaign', 'analytics', 'fraud', 'security'] for tag in e.tags)
        ]

        if critical_endpoints:
            priorities.append(f"🚨 Приоритет: Реализовать {len(critical_endpoints)} критичных для бизнеса endpoints")

        # Endpoints с высоким трафиком (предполагаем на основе пути)
        high_traffic_patterns = ['/campaigns', '/click', '/analytics', '/health']
        high_traffic_endpoints = [
            e for e in endpoints
            if any(pattern in e.path for pattern in high_traffic_patterns) and
            e.status != ImplementationStatus.FULLY_IMPLEMENTED
        ]

        if high_traffic_endpoints:
            priorities.append(f"⚡ Оптимизация: Улучшить {len(high_traffic_endpoints)} высоконагруженных endpoints")

        return priorities


def print_report(report: BusinessLogicReport):
    """Выводит расширенный отчет в консоль."""
    print("\n" + "="*90)
    print("📊 КОМПЛЕКСНЫЙ ОТЧЕТ О РЕАЛИЗАЦИИ БИЗНЕС ЛОГИКИ API")
    print("="*90)

    # Основная статистика с прогресс-баром
    print(f"\n📈 ОБЩАЯ СТАТИСТИКА:")
    print(f"  Всего эндпоинтов: {report.total_endpoints}")

    # Создаем прогресс-бар
    implemented_pct = (report.implemented_endpoints / report.total_endpoints) * 100 if report.total_endpoints > 0 else 0
    mock_pct = (report.mock_endpoints / report.total_endpoints) * 100 if report.total_endpoints > 0 else 0
    partial_pct = (report.partially_implemented_endpoints / report.total_endpoints) * 100 if report.total_endpoints > 0 else 0
    not_impl_pct = (report.not_implemented_endpoints / report.total_endpoints) * 100 if report.total_endpoints > 0 else 0

    print(f"  ✅ Полностью реализовано: {report.implemented_endpoints} ({implemented_pct:.1f}%)")
    print(f"  ⚠️  Mock данные: {report.mock_endpoints} ({mock_pct:.1f}%)")
    print(f"  🔄 Частично реализовано: {report.partially_implemented_endpoints} ({partial_pct:.1f}%)")
    print(f"  ❌ Не реализовано: {report.not_implemented_endpoints} ({not_impl_pct:.1f}%)")

    # Статус проекта
    if implemented_pct >= 95:
        print(f"\n🎉 СТАТУС ПРОЕКТА: ПОЛНОСТЬЮ ГОТОВ К ПРОДАКШЕНУ!")
    elif implemented_pct >= 80:
        print(f"\n⚡ СТАТУС ПРОЕКТА: ГОТОВ К ТЕСТИРОВАНИЮ")
    else:
        print(f"\n🚧 СТАТУС ПРОЕКТА: ТРЕБУЕТ ДОРАБОТКИ")

    if report.endpoints_by_status:
        print(f"\n🔍 ПОДРОБНЫЙ АНАЛИЗ ПО СТАТУСУ:")

        for status in ['fully_implemented', 'partially_implemented', 'mock_implemented', 'not_implemented']:
            if status in report.endpoints_by_status:
                endpoints = report.endpoints_by_status[status]
                status_name = {
                    'fully_implemented': '✅ Полностью реализовано',
                    'mock_implemented': '⚠️  Mock данные',
                    'partially_implemented': '🔄 Частично реализовано',
                    'not_implemented': '❌ Не реализовано'
                }.get(status, status)

                print(f"\n  {status_name} ({len(endpoints)} эндпоинтов):")

                # Группируем по тегам для лучшего обзора
                tag_groups = {}
                for endpoint in endpoints:
                    primary_tag = endpoint.tags[0] if endpoint.tags else 'other'
                    if primary_tag not in tag_groups:
                        tag_groups[primary_tag] = []
                    tag_groups[primary_tag].append(endpoint)

                for tag, tag_endpoints in tag_groups.items():
                    print(f"    📁 {tag.title()}: {len(tag_endpoints)} endpoints")
                    for endpoint in tag_endpoints[:3]:  # Показываем первые 3 из каждой группы
                        print(f"      • {endpoint.method} {endpoint.path}")
                        if endpoint.missing_components and status != 'fully_implemented':
                            print(f"        ⚠️  {endpoint.missing_components[0]}")

                if len(endpoints) > 5:
                    print(f"    ... и ещё {len(endpoints) - 5} эндпоинтов")

    if report.endpoints_by_tag:
        print(f"\n🏷️  ПОКРЫТИЕ ДОМЕНОВ:")
        for tag, endpoints in sorted(report.endpoints_by_tag.items()):
            implemented_in_tag = sum(1 for e in endpoints if e.status == ImplementationStatus.FULLY_IMPLEMENTED)
            total_in_tag = len(endpoints)
            coverage = (implemented_in_tag / total_in_tag) * 100 if total_in_tag > 0 else 0

            status_icon = "✅" if coverage == 100 else "⚠️" if coverage >= 50 else "❌"
            print(f"  {status_icon} {tag.title()}: {implemented_in_tag}/{total_in_tag} ({coverage:.1f}%)")

    if report.critical_missing_features:
        print(f"\n🚨 КРИТИЧЕСКИ ВАЖНЫЕ ПРОБЛЕМЫ:")
        for feature in report.critical_missing_features:
            print(f"  • {feature}")

    if report.recommendations:
        print(f"\n💡 РЕКОМЕНДАЦИИ И ПРИОРИТЕТЫ:")
        for rec in report.recommendations:
            print(f"  • {rec}")

    print(f"\n" + "="*90)
    print("🔍 Анализ завершен. Для детального просмотра см. business_logic_report.json")


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
