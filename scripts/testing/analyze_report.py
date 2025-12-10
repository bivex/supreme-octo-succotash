import json

# Загружаем отчет
with open('business_logic_report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

print("⚠️  ЭНДПОИНТЫ С MOCK ДАННЫМИ:")
print("=" * 50)

for endpoint in report['endpoints_by_status']['mock_implemented']:
    print(f"• {endpoint['method']} {endpoint['path']}")
    if endpoint['mock_patterns']:
        print(f"  📋 Mock паттерны ({len(endpoint['mock_patterns'])}):")
        for pattern in endpoint['mock_patterns'][:3]:  # Показываем первые 3
            print(f"    - {pattern}")
    print()

print("🔄 ЧАСТИЧНО РЕАЛИЗОВАННЫЕ ЭНДПОИНТЫ:")
print("=" * 50)

for endpoint in report['endpoints_by_status']['partially_implemented']:
    print(f"• {endpoint['method']} {endpoint['path']}")
    if endpoint['missing_components']:
        print(f"  ⚠️  Проблемы: {', '.join(endpoint['missing_components'])}")
    print()

print("📊 СТАТИСТИКА:")
print(f"Всего эндпоинтов: {report['total_endpoints']}")
print(f"✅ Полностью реализовано: {report['implemented_endpoints']}")
print(f"⚠️  Mock данные: {report['mock_endpoints']}")
print(f"🔄 Частично: {report['partially_implemented_endpoints']}")
print(f"❌ Не реализовано: {report['not_implemented_endpoints']}")

print("\n💡 РЕКОМЕНДАЦИИ:")
for rec in report['recommendations']:
    print(f"• {rec}")
