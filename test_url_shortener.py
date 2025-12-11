from shared_url_shortener import URLShortener, URLParams, EncodingStrategy, TrackingURLDecoder

# Создаем тестовые параметры как в примере
test_params = URLParams(
    cid='9061',
    sub1='telegram_bot_start',
    sub2='telegram',
    sub3='callback_offer',
    sub4='test_user',
    sub5='premium_offer'
)

print('=== ТЕСТИРОВАНИЕ ВСЕХ СТРАТЕГИЙ КОДИРОВАНИЯ ===')
print(f'Оригинальные параметры: {test_params.to_dict()}')
print()

shortener = URLShortener()

strategies = [
    (EncodingStrategy.SEQUENTIAL, "SEQUENTIAL"),
    (EncodingStrategy.COMPRESSED, "COMPRESSED"),
    (EncodingStrategy.HYBRID, "HYBRID"),
    (EncodingStrategy.SMART, "SMART")
]

for strategy, name in strategies:
    print(f'--- {name} STRATEGY ---')

    # Кодируем
    encoded = shortener.encode(test_params, strategy)
    print(f'Закодированный код: {encoded} (длина: {len(encoded)})')
    print(f'Стратегия: {shortener.get_strategy_info(encoded)}')

    # Декодируем через shortener
    decoded_by_shortener = shortener.decode(encoded)
    if decoded_by_shortener:
        match = decoded_by_shortener.to_dict() == test_params.to_dict()
        print(f'Shortener decode: {"✓" if match else "✗"}')
    else:
        print('Shortener decode: ✗')

    # Экспортируем маппинги для декодера
    mappings = shortener.export_mappings()

    # Декодируем через TrackingURLDecoder
    decoder = TrackingURLDecoder(mappings)
    decoded_by_decoder = decoder.decode(encoded)
    if decoded_by_decoder:
        decoder_dict = decoded_by_decoder.to_dict()
        # Конвертируем для сравнения: campaign_id -> cid
        if 'campaign_id' in decoder_dict:
            decoder_dict['cid'] = decoder_dict.pop('campaign_id')
        match = decoder_dict == test_params.to_dict()
        print(f'TrackingURLDecoder: {"✓" if match else "✗"}')
    else:
        print('TrackingURLDecoder: ✗')

    print()

print('=== СТАТИСТИКА ===')
stats = shortener.get_stats()
for key, val in stats.items():
    print(f'  {key}: {val}')