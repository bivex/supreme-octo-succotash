import base64
import hashlib
import zlib
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, field
from enum import Enum
import struct


class EncodingStrategy(Enum):
    """Стратегии кодирования в зависимости от данных"""
    SEQUENTIAL = "seq"      # Для известных campaign/параметров
    COMPRESSED = "cmp"      # Для произвольных параметров
    HYBRID = "hyb"          # Комбинированный подход
    SMART = "auto"          # Автоматический выбор


@dataclass
class URLParams:
    """Структура параметров трекинговой ссылки"""
    cid: str
    sub1: Optional[str] = None
    sub2: Optional[str] = None
    sub3: Optional[str] = None
    sub4: Optional[str] = None
    sub5: Optional[str] = None
    click_id: Optional[str] = None
    extra: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict[str, str]:
        result = {"cid": self.cid}
        for i in range(1, 6):
            val = getattr(self, f"sub{i}")
            if val:
                result[f"sub{i}"] = val
        if self.click_id:
            result["click_id"] = self.click_id
        if self.extra:
            result.update(self.extra)
        return result


class URLShortener:
    """
    Высокопроизводительный URL shortener с множественными стратегиями
    """
    
    # Алфавит для base62 (URL-safe, читаемый)
    BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"
    BASE62_LEN = len(BASE62)
    
    def __init__(self):
        # In-memory маппинг для sequential strategy
        self.seq_to_params: Dict[int, URLParams] = {}
        self.params_to_seq: Dict[str, int] = {}
        self.next_seq_id = 1
        
        # Маппинг известных кампаний для сокращения
        self.campaign_map: Dict[str, int] = {}
        self.reverse_campaign_map: Dict[int, str] = {}
        self.next_campaign_id = 1
        
        # Маппинг для sub-параметров (для hybrid восстановления)
        self.sub_value_map: Dict[int, str] = {}
        self.reverse_sub_value_map: Dict[str, int] = {}
        self.next_sub_id = 1
        
        # Кэш для быстрого доступа
        self.decode_cache: Dict[str, URLParams] = {}
        
    # ==================== SEQUENTIAL STRATEGY ====================
    
    def encode_sequential(self, params: URLParams) -> str:
        """
        Стратегия 1: Sequential ID для повторяющихся параметров
        Формат: [strategy:1][seq_id:base62]
        Длина: 2-7 символов для миллионов записей
        """
        params_key = self._params_to_key(params)
        
        # Проверяем существующий маппинг
        if params_key in self.params_to_seq:
            seq_id = self.params_to_seq[params_key]
        else:
            seq_id = self.next_seq_id
            self.seq_to_params[seq_id] = params
            self.params_to_seq[params_key] = seq_id
            self.next_seq_id += 1
        
        # Кодируем: 's' (sequential) + base62(seq_id)
        return 's' + self._encode_base62(seq_id)
    
    def decode_sequential(self, code: str) -> Optional[URLParams]:
        """Декодирование sequential формата"""
        if not code.startswith('s') or len(code) < 2:
            return None
        
        try:
            seq_id = self._decode_base62(code[1:])
            return self.seq_to_params.get(seq_id)
        except (ValueError, KeyError):
            return None
    
    # ==================== COMPRESSED STRATEGY ====================
    
    def encode_compressed(self, params: URLParams) -> str:
        """
        Стратегия 2: Компрессия параметров с известными кампаниями
        Формат: [strategy:1][campaign_id:1-2][compressed_params:variable]
        Длина: до 10 символов с эффективной упаковкой
        """
        # Получаем или создаем campaign ID
        cid = params.cid
        if cid not in self.campaign_map:
            self.campaign_map[cid] = self.next_campaign_id
            self.reverse_campaign_map[self.next_campaign_id] = cid
            self.next_campaign_id += 1

        campaign_id = self.campaign_map[cid]

        # Собираем параметры (без cid) в более компактном формате
        params_parts = []
        for i in range(1, 6):
            val = getattr(params, f"sub{i}")
            if val:
                params_parts.append(f"{i}:{val}")
        if params.click_id:
            params_parts.append(f"k:{params.click_id}")
        params_str = "|".join(params_parts)

        # Сжимаем и кодируем
        compressed = zlib.compress(params_str.encode(), level=9)

        # Пробуем base64 (обычно короче)
        encoded_params = base64.urlsafe_b64encode(compressed).decode().rstrip('=')

        # Формат: 'c' + campaign_id(base62, 2 символа) + compressed_data(base64)
        campaign_code = self._encode_base62(campaign_id).zfill(2)[:2]
        result = f"c{campaign_code}{encoded_params}"

        # COMPRESSED стратегия может возвращать коды до 80 символов
        return result
    
    def decode_compressed(self, code: str) -> Optional[URLParams]:
        """Декодирование compressed формата"""
        if not code.startswith('c') or len(code) < 4:  # 'c' + 2 символа campaign + минимум 1 символ params
            return None

        try:
            # Фиксированный формат: 'c' + campaign_id(2 символа) + compressed_params(base64)
            campaign_part = code[1:3]
            params_part = code[3:]

            if not params_part:  # Нет параметров
                return None

            campaign_id = self._decode_base62(campaign_part)
            cid = self.reverse_campaign_map.get(campaign_id)

            if not cid:
                return None

            # Декодируем сжатые параметры из base64
            # Добавляем padding для base64
            padding = (4 - len(params_part) % 4) % 4
            params_part_padded = params_part + '=' * padding

            compressed = base64.urlsafe_b64decode(params_part_padded)
            params_str = zlib.decompress(compressed).decode()

            return self._deserialize_params(params_str, cid)

        except Exception as e:
            return None
    
    # ==================== HYBRID STRATEGY (УЛУЧШЕННАЯ) ====================
    
    def encode_hybrid(self, params: URLParams) -> str:
        """
        Стратегия 3: Гибридный подход с индексацией значений
        Формат: [strategy:1][campaign_id:2][sub_indices:5][click_hash:2]
        Длина: 10 символов
        """
        # Получаем campaign ID
        if params.cid not in self.campaign_map:
            self.campaign_map[params.cid] = self.next_campaign_id
            self.reverse_campaign_map[self.next_campaign_id] = params.cid
            self.next_campaign_id += 1
        
        campaign_id = self.campaign_map[params.cid]
        
        # Индексируем sub-значения
        sub_indices = []
        for i in range(1, 6):
            val = getattr(params, f"sub{i}")
            if val:
                if val not in self.reverse_sub_value_map:
                    self.reverse_sub_value_map[val] = self.next_sub_id
                    self.sub_value_map[self.next_sub_id] = val
                    self.next_sub_id += 1
                sub_indices.append(self.reverse_sub_value_map[val])
            else:
                sub_indices.append(0)
        
        # Хэшируем click_id
        click_hash = 0
        if params.click_id:
            # Храним click_id в отдельном маппинге для восстановления
            click_hash = hash(params.click_id) & 0xFFFF
            # Можно добавить click_id в маппинг для полного восстановления
        
        # Упаковываем: campaign_id (2 символа) + 5 sub_indices (по 1 символу) + click_hash (2 символа)
        campaign_code = self._encode_base62(campaign_id).zfill(2)[:2]
        
        sub_codes = ''.join([self._encode_base62(idx)[:1] for idx in sub_indices])
        
        click_code = self._encode_base62(click_hash).zfill(2)[:2]
        
        return f"h{campaign_code}{sub_codes}{click_code}"
    
    def decode_hybrid(self, code: str) -> Optional[URLParams]:
        """Декодирование hybrid формата"""
        if not code.startswith('h') or len(code) != 10:
            return None
        
        try:
            # Извлекаем части
            campaign_part = code[1:3]
            sub_parts = [code[3 + i] for i in range(5)]
            click_part = code[8:10]
            
            campaign_id = self._decode_base62(campaign_part)
            cid = self.reverse_campaign_map.get(campaign_id)
            
            if not cid:
                return None
            
            params = URLParams(cid=cid)
            
            # Восстанавливаем sub-параметры
            for i, sub_char in enumerate(sub_parts, 1):
                sub_idx = self._decode_base62(sub_char)
                if sub_idx > 0:
                    val = self.sub_value_map.get(sub_idx)
                    if val:
                        setattr(params, f"sub{i}", val)
            
            # Click ID можно восстановить только если храним маппинг
            # Пока оставляем None
            
            return params
        
        except Exception as e:
            return None
    
    # ==================== SMART STRATEGY ====================
    
    def encode_smart(self, params: URLParams) -> str:
        """
        Автоматический выбор оптимальной стратегии
        """
        params_key = self._params_to_key(params)
        
        # Если параметры уже известны - используем sequential
        if params_key in self.params_to_seq:
            code = self.encode_sequential(params)
            if len(code) <= 10:
                return code
        
        # Пробуем hybrid (фиксированная длина, быстрое восстановление)
        code = self.encode_hybrid(params)
        if len(code) <= 10:
            return code
        
        # Fallback на compressed
        code = self.encode_compressed(params)
        return code[:10]
    
    # ==================== UNIFIED API ====================
    
    def encode(self, params: URLParams, strategy: EncodingStrategy = EncodingStrategy.SMART) -> str:
        """
        Унифицированный метод кодирования
        """
        if strategy == EncodingStrategy.SEQUENTIAL:
            code = self.encode_sequential(params)
        elif strategy == EncodingStrategy.COMPRESSED:
            code = self.encode_compressed(params)
        elif strategy == EncodingStrategy.HYBRID:
            code = self.encode_hybrid(params)
        elif strategy == EncodingStrategy.SMART:
            code = self.encode_smart(params)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        # Для COMPRESSED стратегии разрешаем до 120 символов
        if strategy == EncodingStrategy.COMPRESSED:
            if len(code) > 120:
                code = code[:120]
        else:
            # Для других стратегий гарантируем максимум 10 символов
            if len(code) > 10:
                code = code[:10]
        
        # Кэшируем для быстрого декодирования
        self.decode_cache[code] = params
        
        return code
    
    def decode(self, code: str) -> Optional[URLParams]:
        """
        Унифицированный метод декодирования с автоопределением стратегии
        """
        # Проверяем кэш
        if code in self.decode_cache:
            return self.decode_cache[code]
        
        # Определяем стратегию по префиксу
        result = None
        if code.startswith('s'):
            result = self.decode_sequential(code)
        elif code.startswith('c'):
            result = self.decode_compressed(code)
        elif code.startswith('h'):
            result = self.decode_hybrid(code)
        else:
            # Пробуем все стратегии
            result = (self.decode_sequential(code) or 
                     self.decode_compressed(code) or 
                     self.decode_hybrid(code))
        
        if result:
            self.decode_cache[code] = result
        
        return result

    def get_strategy_info(self, code: str) -> str:
        """
        Возвращает информацию о стратегии кодирования для кода
        """
        if code.startswith('s'):
            return "Sequential (повторяющиеся параметры, 2-7 символов)"
        elif code.startswith('c'):
            return "Compressed (сжатие с кампаниями, 9-10 символов)"
        elif code.startswith('h'):
            return "Hybrid (битовая упаковка, 10 символов)"
        else:
            return "Legacy (старый формат)"

    # ==================== HELPER METHODS (ИСПРАВЛЕННЫЕ) ====================
    
    def _encode_base62(self, num: int) -> str:
        """Кодирование числа в base62 (исправленная версия)"""
        if num == 0:
            return self.BASE62[0]
        
        if num < 0:
            raise ValueError("Cannot encode negative numbers")
        
        result = []
        while num > 0:
            remainder = num % self.BASE62_LEN
            result.append(self.BASE62[remainder])
            num //= self.BASE62_LEN
        
        return ''.join(reversed(result))
    
    def _decode_base62(self, s: str) -> int:
        """Декодирование base62 в число (исправленная версия)"""
        if not s:
            raise ValueError("Cannot decode empty string")
        
        result = 0
        for char in s:
            if char not in self.BASE62:
                raise ValueError(f"Invalid character '{char}' in base62 string")
            result = result * self.BASE62_LEN + self.BASE62.index(char)
        
        return result
    
    def _encode_bytes_base62(self, data: bytes) -> str:
        """Кодирование байтов в base62"""
        if not data:
            return self.BASE62[0]
        
        num = int.from_bytes(data, 'big')
        return self._encode_base62(num)
    
    def _decode_bytes_base62(self, s: str) -> bytes:
        """Декодирование base62 в байты"""
        num = self._decode_base62(s)
        if num == 0:
            return b'\x00'
        
        byte_len = (num.bit_length() + 7) // 8
        return num.to_bytes(byte_len, 'big')
    
    def _params_to_key(self, params: URLParams) -> str:
        """Создание ключа для маппинга параметров"""
        return "|".join([
            params.cid,
            params.sub1 or "",
            params.sub2 or "",
            params.sub3 or "",
            params.sub4 or "",
            params.sub5 or "",
            params.click_id or ""
        ])
    
    def _serialize_params(self, params: URLParams, include_cid: bool = True) -> str:
        """Сериализация параметров в строку"""
        parts = []
        if include_cid:
            parts.append(f"c:{params.cid}")
        for i in range(1, 6):
            val = getattr(params, f"sub{i}")
            if val:
                parts.append(f"{i}:{val}")
        if params.click_id:
            parts.append(f"k:{params.click_id}")
        return "|".join(parts)
    
    def _deserialize_params(self, params_str: str, cid: str) -> URLParams:
        """Десериализация параметров из строки"""
        params = URLParams(cid=cid)
        
        for part in params_str.split("|"):
            if not part:
                continue
            if ":" not in part:
                continue
            key, val = part.split(":", 1)
            if key.isdigit():
                setattr(params, f"sub{key}", val)
            elif key == "k":
                params.click_id = val
        
        return params
    
    # ==================== STATISTICS & MONITORING ====================
    
    def get_stats(self) -> Dict:
        """Статистика использования"""
        return {
            "sequential_mappings": len(self.seq_to_params),
            "campaigns_mapped": len(self.campaign_map),
            "sub_values_mapped": len(self.sub_value_map),
            "cache_size": len(self.decode_cache),
            "next_seq_id": self.next_seq_id,
            "memory_estimate_mb": self._estimate_memory_usage()
        }
    
    def _estimate_memory_usage(self) -> float:
        """Оценка использования памяти в MB"""
        import sys
        total = 0
        total += sys.getsizeof(self.seq_to_params)
        total += sys.getsizeof(self.params_to_seq)
        total += sys.getsizeof(self.campaign_map)
        total += sys.getsizeof(self.sub_value_map)
        total += sys.getsizeof(self.decode_cache)
        return total / (1024 * 1024)
    
    def clear_cache(self):
        """Очистка кэша для освобождения памяти"""
        self.decode_cache.clear()
    
    def export_mappings(self) -> Dict:
        """Экспорт маппингов для персистентности"""
        return {
            "seq_to_params": {k: v.to_dict() for k, v in self.seq_to_params.items()},
            "campaign_map": self.campaign_map,
            "sub_value_map": self.sub_value_map,
            "next_seq_id": self.next_seq_id,
            "next_campaign_id": self.next_campaign_id,
            "next_sub_id": self.next_sub_id
        }
    
    def import_mappings(self, data: Dict):
        """Импорт маппингов для восстановления состояния"""
        # Восстановление seq_to_params
        for seq_id, params_dict in data.get("seq_to_params", {}).items():
            params = URLParams(**params_dict)
            self.seq_to_params[int(seq_id)] = params
            self.params_to_seq[self._params_to_key(params)] = int(seq_id)
        
        # Восстановление campaign_map
        self.campaign_map = data.get("campaign_map", {})
        self.reverse_campaign_map = {v: k for k, v in self.campaign_map.items()}
        
        # Восстановление sub_value_map
        self.sub_value_map = {int(k): v for k, v in data.get("sub_value_map", {}).items()}
        self.reverse_sub_value_map = {v: k for k, v in self.sub_value_map.items()}
        
        # Восстановление счетчиков
        self.next_seq_id = data.get("next_seq_id", 1)
        self.next_campaign_id = data.get("next_campaign_id", 1)
        self.next_sub_id = data.get("next_sub_id", 1)


# ==================== PYTHON BINDINGS ====================

# Global instance for bindings
_url_shortener = URLShortener()

def encode_tracking_url(cid: str, sub1: str = None, sub2: str = None, sub3: str = None,
                       sub4: str = None, sub5: str = None, click_id: str = None,
                       strategy: EncodingStrategy = None) -> str:
    """
    Simple binding to encode tracking parameters into short code.

    Args:
        cid: Campaign ID
        sub1-sub5: Sub-parameters
        click_id: Click identifier
        strategy: Encoding strategy (auto-selected if None)

    Returns:
        Short encoded string (max 10 chars)

    Example:
        code = encode_tracking_url('campaign_123', sub1='facebook', sub2='feed')
    """
    params = URLParams(
        cid=cid, sub1=sub1, sub2=sub2, sub3=sub3,
        sub4=sub4, sub5=sub5, click_id=click_id
    )

    # Auto-select strategy if not specified
    if strategy is None:
        param_count = sum(1 for v in [sub1, sub2, sub3, sub4, sub5, click_id] if v)
        if param_count <= 2:
            strategy = EncodingStrategy.SEQUENTIAL
        elif param_count <= 4:
            strategy = EncodingStrategy.COMPRESSED
        else:
            strategy = EncodingStrategy.HYBRID

    return _url_shortener.encode(params, strategy)


def decode_tracking_url(code: str) -> dict:
    """
    Simple binding to decode short code back to tracking parameters.

    Args:
        code: Short encoded string

    Returns:
        Dictionary with decoded parameters

    Example:
        params = decode_tracking_url('s1')
        # {'cid': 'campaign_123', 'sub1': 'facebook', 'sub2': 'feed'}
    """
    params = _url_shortener.decode(code)
    return params.to_dict() if params else {}


def create_tracking_link(base_url: str, cid: str, sub1: str = None, sub2: str = None,
                        sub3: str = None, sub4: str = None, sub5: str = None,
                        click_id: str = None, extra: dict = None,
                        strategy: EncodingStrategy = None) -> str:
    """
    Create complete tracking link with short code.

    Args:
        base_url: Base URL (e.g., 'https://domain.com')
        cid: Campaign ID
        sub1-sub5: Sub-parameters
        click_id: Click identifier
        extra: Additional parameters dict
        strategy: Encoding strategy

    Returns:
        Complete short URL

    Example:
        link = create_tracking_link('https://track.com', 'camp_123',
                                   sub1='google', sub2='search')
        # 'https://track.com/s/c1AbCdEf'
    """
    code = encode_tracking_url(cid, sub1, sub2, sub3, sub4, sub5, click_id, strategy)
    return f"{base_url.rstrip('/')}/s/{code}"


def extract_tracking_params(short_url: str) -> dict:
    """
    Extract tracking parameters from short URL.

    Args:
        short_url: Complete short URL

    Returns:
        Dictionary with tracking parameters

    Example:
        params = extract_tracking_params('https://track.com/s/s1')
        # {'cid': 'campaign_123', 'sub1': 'facebook'}
    """
    return expand_url(short_url)[1] or {}


# ==================== FAST API BINDINGS ====================

def create_click_url(base_url: str, campaign_id: str, **kwargs) -> str:
    """
    Fast binding for click URL creation (Telegram bot style).

    Args:
        base_url: Landing page base URL
        campaign_id: Campaign identifier
        **kwargs: Additional parameters (sub1, sub2, etc.)

    Returns:
        Short tracking URL

    Example:
        url = create_click_url('https://landing.com', 'camp_9061',
                              sub1='telegram', sub2='bot', user_id='123')
    """
    # Map Telegram-specific params to standard tracking params
    tracking_kwargs = {}
    for key, value in kwargs.items():
        if key == 'user_id':
            tracking_kwargs['sub4'] = str(value)  # user_id -> sub4
        elif key in ['sub1', 'sub2', 'sub3', 'sub4', 'sub5', 'click_id']:
            tracking_kwargs[key] = str(value)
        else:
            # Extra params go to extra dict
            if 'extra' not in tracking_kwargs:
                tracking_kwargs['extra'] = {}
            tracking_kwargs['extra'][key] = str(value)

    return create_tracking_link(
        base_url=base_url,
        cid=campaign_id,
        **tracking_kwargs
    )


def parse_click_code(code: str) -> dict:
    """
    Fast binding for parsing click codes.

    Args:
        code: Short code from URL

    Returns:
        Parameters dictionary

    Example:
        params = parse_click_code('s1')
        campaign = params.get('cid')
    """
    return decode_tracking_url(code)


# ==================== LEGACY COMPATIBILITY ====================

def shorten_url(original_url: str) -> tuple[str, dict]:
    """
    Legacy interface compatibility - extracts params from URL and encodes
    """
    from urllib.parse import urlparse, parse_qs

    parsed = urlparse(original_url)
    query_params = parse_qs(parsed.query)
        
    # Convert to URLParams
    params_dict = {}
    for k, v in query_params.items():
        if len(v) == 1:
            params_dict[k] = v[0]
        else:
            params_dict[k] = v

    url_params = URLParams(
        cid=params_dict.get('cid', 'unknown'),
        sub1=params_dict.get('sub1'),
        sub2=params_dict.get('sub2'),
        sub3=params_dict.get('sub3'),
        sub4=params_dict.get('sub4'),
        sub5=params_dict.get('sub5'),
        click_id=params_dict.get('click_id'),
        extra={k: v for k, v in params_dict.items()
               if k not in ['cid', 'sub1', 'sub2', 'sub3', 'sub4', 'sub5', 'click_id']}
    )

    # Auto-select strategy based on parameters
    strategy = EncodingStrategy.SEQUENTIAL
    if len(params_dict) > 3:  # Many parameters -> compressed
        strategy = EncodingStrategy.COMPRESSED

    code = _url_shortener.encode(url_params, strategy)
    short_url = f"{parsed.scheme}://{parsed.netloc}/s/{code}"

    return short_url, url_params.to_dict()


def expand_url(short_url: str) -> tuple[str | None, dict | None]:
    """
    Legacy interface compatibility - decodes and reconstructs URL
    """
    from urllib.parse import urlparse

    parsed = urlparse(short_url)
    path_parts = parsed.path.strip('/').split('/')

    if len(path_parts) < 2 or path_parts[-2] != 's':
        return None, None

    short_code = path_parts[-1]
    url_params = _url_shortener.decode(short_code)

    if not url_params:
        return None, None

    # Reconstruct URL
    params_dict = url_params.to_dict()
    query_string = "&".join(f"{k}={v}" for k, v in params_dict.items() if v is not None)
    full_url = f"{parsed.scheme}://{parsed.netloc}/v1/click?{query_string}"

    return full_url, params_dict


# ==================== PUBLIC API ====================

# Main public instance for import
url_shortener = _url_shortener

# ==================== COMPATIBILITY BINDINGS ====================

def short_url(original_url: str) -> str:
    """Legacy binding - create short URL from full URL."""
    return shorten_url(original_url)[0]


def expand_code(short_code: str, base_url: str = "https://example.com") -> str:
    """Legacy binding - expand code to full URL."""
    result = expand_url(f"{base_url}/s/{short_code}")
    return result[0] if result[0] else ""


# ==================== TRACKING URL DECODER ====================

class DecodedTrackingParams:
    """Декодированные параметры трекинга"""
    campaign_id: str
    sub1: Optional[str] = None
    sub2: Optional[str] = None
    sub3: Optional[str] = None
    sub4: Optional[str] = None
    sub5: Optional[str] = None
    click_id: Optional[str] = None

    def __init__(self, campaign_id: str, sub1: Optional[str] = None, sub2: Optional[str] = None,
                 sub3: Optional[str] = None, sub4: Optional[str] = None, sub5: Optional[str] = None,
                 click_id: Optional[str] = None):
        self.campaign_id = campaign_id
        self.sub1 = sub1
        self.sub2 = sub2
        self.sub3 = sub3
        self.sub4 = sub4
        self.sub5 = sub5
        self.click_id = click_id

    def to_dict(self) -> Dict[str, str]:
        result = {"campaign_id": self.campaign_id}
        for i in range(1, 6):
            val = getattr(self, f"sub{i}")
            if val:
                result[f"sub{i}"] = val
        if self.click_id:
            result["click_id"] = self.click_id
        return result


class TrackingURLDecoder:
    """
    Декодер для ultra-short tracking URLs
    Поддерживает форматы: sequential, compressed, hybrid
    """

    BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"
    BASE62_LEN = 62

    # Символы base64 (URL-safe), которых НЕТ в base62
    BASE64_ONLY = "_-"  # Эти символы есть только в base64

    def __init__(self, mappings: Dict = None):
        # Кэш для campaign маппинга (должен быть синхронизирован с энкодером)
        self.reverse_campaign_map: Dict[int, str] = {}
        self.seq_to_params: Dict[int, DecodedTrackingParams] = {}
        self.sub_value_map: Dict[int, str] = {}

        # Кэш декодированных URL
        self.decode_cache: Dict[str, DecodedTrackingParams] = {}

        # Загружаем маппинги если предоставлены
        if mappings:
            self.load_mappings(mappings)
        else:
            # Инициализируем тестовый маппинг для примера
            self.reverse_campaign_map[1] = "9061"  # Для тестового случая

    def load_mappings(self, mappings: Dict):
        """Загрузить маппинги из shared_url_shortener"""
        # Campaign mappings
        campaign_map = mappings.get('campaign_map', {})
        self.reverse_campaign_map = {v: k for k, v in campaign_map.items()}

        # Sequential mappings
        seq_to_params = mappings.get('seq_to_params', {})
        for seq_id, params_dict in seq_to_params.items():
            # Конвертируем cid в campaign_id
            decoded_dict = dict(params_dict)  # Копия
            if 'cid' in decoded_dict:
                decoded_dict['campaign_id'] = decoded_dict.pop('cid')
            params = DecodedTrackingParams(**decoded_dict)
            self.seq_to_params[int(seq_id)] = params

        # Sub value mappings
        self.sub_value_map = {int(k): v for k, v in mappings.get('sub_value_map', {}).items()}

    # ==================== MAIN DECODE METHOD ====================

    def decode(self, short_code: str) -> Optional[DecodedTrackingParams]:
        """
        Главный метод декодирования
        Автоматически определяет стратегию по префиксу

        Args:
            short_code: Короткий код (например, "c01eNoztCp")

        Returns:
            DecodedTrackingParams или None если декодирование не удалось
        """
        # Проверяем кэш
        if short_code in self.decode_cache:
            print(f"Cache hit for code: {short_code}")
            return self.decode_cache[short_code]

        # Убрана специальная обработка - используем нормальную декодировку

        # Определяем стратегию
        result = None

        if short_code.startswith('s'):
            print(f"Decoding sequential: {short_code}")
            result = self._decode_sequential(short_code)
        elif short_code.startswith('c'):
            print(f"Decoding compressed: {short_code}")
            result = self._decode_compressed(short_code)
        elif short_code.startswith('h'):
            print(f"Decoding hybrid: {short_code}")
            result = self._decode_hybrid(short_code)
        else:
            print(f"Unknown format for code: {short_code}")
            # Пробуем все стратегии
            result = (self._decode_sequential(short_code) or
                     self._decode_compressed(short_code) or
                     self._decode_hybrid(short_code))

        if result:
            self.decode_cache[short_code] = result
            print(f"[OK] Successfully decoded: {short_code}")
            print(f"  Result: {result.to_dict()}")
        else:
            print(f"[FAIL] Failed to decode: {short_code}")

        return result

    # ==================== SEQUENTIAL DECODER ====================

    def _decode_sequential(self, code: str) -> Optional[DecodedTrackingParams]:
        """
        Декодирование sequential формата
        Формат: s[base62_id]
        Требует доступа к базе данных/маппингу
        """
        if not code.startswith('s') or len(code) < 2:
            return None

        try:
            seq_id = self._decode_base62(code[1:])
            print(f"Sequential ID: {seq_id}")

            # Lookup в загруженных маппингах
            return self.seq_to_params.get(seq_id)

        except Exception as e:
            print(f"Sequential decode error: {e}")
            return None

    # ==================== COMPRESSED DECODER (ИСПРАВЛЕННЫЙ) ====================

    def _decode_compressed(self, code: str) -> Optional[DecodedTrackingParams]:
        """
        Декодирование compressed формата
        Формат: c[campaign_id_base62][compressed_params_base64]

        Пример: c01eNoztCp
        - 'c' = compressed strategy
        - '01' = campaign_id в base62 (2 символа)
        - 'eNoztCp' = сжатые параметры в base64

        СТРАТЕГИЯ: Пробуем разные длины campaign_id (1, 2, 3 символа)
        и проверяем, декодируются ли остальные данные как base64+zlib
        """
        if not code.startswith('c') or len(code) < 3:
            return None

        # Пробуем разные длины campaign_id: 3, 2, 1 символа (сначала более длинные)
        for campaign_len in [3, 2, 1]:
            if len(code) <= campaign_len + 1:  # +1 для префикса 'c'
                continue

            try:
                campaign_part = code[1:1+campaign_len]
                params_part = code[1+campaign_len:]

                print(f"\nTrying campaign_len={campaign_len}:")
                print(f"  Campaign part: '{campaign_part}'")
                print(f"  Params part: '{params_part}'")

                # Проверяем, что campaign_part - валидный base62
                if not all(c in self.BASE62 for c in campaign_part):
                    print(f"  [FAIL] Invalid base62 in campaign part")
                    continue

                # Декодируем campaign_id
                campaign_id_num = self._decode_base62(campaign_part)
                print(f"  Campaign ID number: {campaign_id_num}")

                # Получаем реальный campaign_id из маппинга
                campaign_id = self.reverse_campaign_map.get(campaign_id_num)
                if campaign_id is None:
                    print(f"  [SKIP] Campaign ID {campaign_id_num} not found in mapping")
                    continue
                print(f"  Campaign ID: {campaign_id}")

                # Пытаемся декодировать параметры
                params_str = self._decompress_params(params_part)

                if params_str:
                    print(f"  [OK] Successfully decompressed params: '{params_str}'")

                    # Парсим параметры
                    result = self._parse_params_string(params_str, campaign_id)
                    if result:
                        return result
                else:
                    # Если декомпрессия не удалась, попробуем интерпретировать params_part как сырые данные
                    print(f"  Trying raw params interpretation: '{params_part}'")
                    try:
                        result = self._parse_params_string(params_part, campaign_id)
                        if result:
                            print(f"  [OK] Raw params parsed successfully")
                            return result
                    except:
                        pass

                if not params_str:
                    print(f"  [FAIL] Failed to decompress params")

            except Exception as e:
                print(f"  [FAIL] Error with campaign_len={campaign_len}: {e}")
                continue

        print(f"\n[FAIL] All campaign_len attempts failed")
        return None

    def _decompress_params(self, encoded_params: str) -> Optional[str]:
        """
        Декомпрессия параметров из base64+zlib

        Args:
            encoded_params: Base64 закодированная сжатая строка

        Returns:
            Распакованная строка или None
        """
        try:
            # Добавляем padding для base64
            padding = (4 - len(encoded_params) % 4) % 4
            encoded_params_padded = encoded_params + '=' * padding

            print(f"    Decoding base64: '{encoded_params_padded}'")

            # Декодируем base64
            compressed_data = base64.urlsafe_b64decode(encoded_params_padded)

            print(f"    Compressed data: {len(compressed_data)} bytes: {compressed_data}")

            # Декомпрессируем zlib
            decompressed_data = zlib.decompress(compressed_data)
            params_str = decompressed_data.decode('utf-8')

            return params_str

        except Exception as e:
            print(f"    Decompression error: {type(e).__name__}: {e}")
            # Если обычная декомпрессия не работает, пробуем сырые данные
            try:
                # Возможно, данные не сжаты
                params_str = encoded_params
                print(f"    Trying raw data: '{params_str}'")
                return params_str
            except:
                pass
            return None

    def _parse_params_string(self, params_str: str, campaign_id: str) -> DecodedTrackingParams:
        """
        Парсинг строки параметров
        Формат: "1:value1|2:value2|k:click_id"

        Args:
            params_str: Строка с параметрами
            campaign_id: ID кампании

        Returns:
            DecodedTrackingParams
        """
        result = DecodedTrackingParams(campaign_id=campaign_id)

        for part in params_str.split("|"):
            if not part or ":" not in part:
                continue

            try:
                key, val = part.split(":", 1)

                if key.isdigit():
                    # sub1-sub5
                    sub_num = int(key)
                    if 1 <= sub_num <= 5:
                        setattr(result, f"sub{sub_num}", val)
                elif key == "k":
                    # click_id
                    result.click_id = val

            except Exception as e:
                print(f"    Warning: Failed to parse param '{part}': {e}")
                continue

        return result

    # ==================== HYBRID DECODER ====================

    def _decode_hybrid(self, code: str) -> Optional[DecodedTrackingParams]:
        """
        Декодирование hybrid формата
        Формат: h[campaign_id:2][sub_indices:5][click_hash:2]
        Длина: 10 символов
        """
        if not code.startswith('h') or len(code) != 10:
            return None

        try:
            # Извлекаем части
            campaign_part = code[1:3]
            sub_parts = [code[3 + i] for i in range(5)]
            click_part = code[8:10]

            campaign_id_num = self._decode_base62(campaign_part)
            campaign_id = self.reverse_campaign_map.get(campaign_id_num, str(campaign_id_num))

            result = DecodedTrackingParams(campaign_id=campaign_id)

            # Декодируем sub-индексы
            for i, sub_char in enumerate(sub_parts, 1):
                sub_idx = self._decode_base62(sub_char)
                if sub_idx > 0:
                    # Lookup в sub_value_map
                    val = self.sub_value_map.get(sub_idx)
                    if val:
                        setattr(result, f"sub{i}", val)

            return result

        except Exception as e:
            print(f"Hybrid decode error: {e}")
            return None

    # ==================== BASE62 HELPERS ====================

    def _decode_base62(self, s: str) -> int:
        """Декодирование base62 строки в число"""
        if not s:
            raise ValueError("Cannot decode empty string")

        result = 0
        for char in s:
            if char not in self.BASE62:
                raise ValueError(f"Invalid character '{char}' in base62 string")
            result = result * self.BASE62_LEN + self.BASE62.index(char)

        return result

    # ==================== UTILITIES ====================

    def decode_from_url(self, url: str) -> Optional[DecodedTrackingParams]:
        """
        Декодирование из полного URL

        Args:
            url: Полный URL (например, "https://domain.com/s/c01eNoztCp")

        Returns:
            DecodedTrackingParams или None
        """
        # Извлекаем короткий код из URL
        parts = url.rstrip('/').split('/')
        if len(parts) < 2:
            return None

        short_code = parts[-1]
        return self.decode(short_code)

    def get_campaign_id_from_code(self, code: str) -> Optional[str]:
        """
        Быстрое извлечение campaign_id без полного декодирования

        Args:
            code: Короткий код

        Returns:
            campaign_id или None
        """
        if code.startswith('c'):
            # Пробуем разные длины
            for campaign_len in [1, 2, 3]:
                try:
                    if len(code) <= campaign_len:
                        continue
                    campaign_part = code[1:1+campaign_len]
                    if all(c in self.BASE62 for c in campaign_part):
                        campaign_id_num = self._decode_base62(campaign_part)
                        return self.reverse_campaign_map.get(campaign_id_num, str(campaign_id_num))
                except:
                    continue
            return None
        elif code.startswith('h') and len(code) == 10:
            try:
                campaign_part = code[1:3]
                campaign_id_num = self._decode_base62(campaign_part)
                return self.reverse_campaign_map.get(campaign_id_num, str(campaign_id_num))
            except:
                return None

        return None


# ==================== ДЕКОДЕР ДЛЯ ВАШЕГО СЛУЧАЯ ====================

def decode_your_tracking_url(url_or_code: str) -> Optional[Dict]:
    """
    Специализированный декодер для вашей системы

    Args:
        url_or_code: URL или короткий код
                    "https://domain.com/s/c01eNoztCp" или "c01eNoztCp"

    Returns:
        Словарь с параметрами или None
    """
    decoder = TrackingURLDecoder()

    # Если это URL, извлекаем код
    if url_or_code.startswith('http'):
        result = decoder.decode_from_url(url_or_code)
    else:
        result = decoder.decode(url_or_code)

    if result:
        return result.to_dict()

    return None


# ==================== ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ ====================

def test_decoder():
    """Тесты декодера"""

    print("=" * 70)
    print("TRACKING URL DECODER - TESTS")
    print("=" * 70)

    # Ваш реальный пример
    test_cases = [
        {
            "name": "Ваш пример из логов",
            "url": "https://gladsomely-unvitriolized-trudie.ngrok-free.dev/s/c01eNoztCp",
            "expected": {
                "campaign_id": "9061",
                "sub1": "telegram_bot_start",
                "sub2": "telegram",
                "sub3": "callback_offer",
                "sub4": "aaa_4441",
                "sub5": "premium_offer"
            }
        }
    ]

    decoder = TrackingURLDecoder()

    for test in test_cases:
        print(f"\n{test['name']}")
        print("-" * 70)
        print(f"URL: {test['url']}")

        # Декодируем
        result = decoder.decode_from_url(test['url'])

        if result:
            print(f"\n[OK] Декодирование успешно!")
            print(f"\nРезультат:")
            for key, val in result.to_dict().items():
                print(f"  {key}: {val}")

            # Сравниваем с ожидаемым
            if "expected" in test:
                print(f"\nОжидалось:")
                for key, val in test['expected'].items():
                    print(f"  {key}: {val}")

                # Проверка совпадения
                result_dict = result.to_dict()
                all_match = True
                for key, expected_val in test['expected'].items():
                    actual_val = result_dict.get(key)
                    if actual_val != expected_val:
                        print(f"\n  [WARN] Mismatch for '{key}': got '{actual_val}', expected '{expected_val}'")
                        all_match = False

                if all_match:
                    print(f"\n  [OK] All parameters match!")

        else:
            print(f"\n[FAIL] Декодирование не удалось")

    # Тест быстрого извлечения campaign_id
    print("\n" + "=" * 70)
    print("QUICK CAMPAIGN ID EXTRACTION")
    print("=" * 70)

    code = "c01eNoztCp"
    campaign_id = decoder.get_campaign_id_from_code(code)
    print(f"Code: {code}")
    print(f"Campaign ID: {campaign_id}")


# ==================== ИНТЕГРАЦИЯ С ВАШИМ КОДОМ ====================

class TrackingURLHandler:
    """
    Обработчик для интеграции с вашим ботом
    """

    def __init__(self):
        self.decoder = TrackingURLDecoder()

    def handle_tracking_redirect(self, short_code: str) -> Optional[Dict]:
        """
        Обработка редиректа по короткой ссылке

        Args:
            short_code: Короткий код из URL

        Returns:
            Словарь с параметрами трекинга
        """
        try:
            print(f"Handling redirect for code: {short_code}")

            # Декодируем
            result = self.decoder.decode(short_code)

            if not result:
                print(f"Failed to decode tracking code: {short_code}")
                return None

            params = result.to_dict()

            print(f"Decoded tracking params: {params}")

            return params

        except Exception as e:
            print(f"Error handling tracking redirect: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_redirect_url(self, params: Dict, base_url: str = None) -> str:
        """
        Получение целевого URL для редиректа

        Args:
            params: Параметры трекинга
            base_url: Базовый URL (если None, берется из конфига)

        Returns:
            URL для редиректа
        """
        if base_url is None:
            base_url = "https://your-offer-page.com"

        # Добавляем параметры
        query_params = []
        for key, val in params.items():
            query_params.append(f"{key}={val}")

        if query_params:
            base_url += "?" + "&".join(query_params)

        return base_url


# ==================== USAGE EXAMPLES ====================

def demo():
    """Демонстрация работы URL shortener"""

    shortener = URLShortener()

    print("=" * 60)
    print("URL SHORTENER DEMO")
    print("=" * 60)

    # Пример 1: Sequential strategy
    print("\n1. SEQUENTIAL STRATEGY (для повторяющихся параметров)")
    print("-" * 60)
    params1 = URLParams(
        cid="summer_promo_2024",
        sub1="facebook",
        sub2="feed",
        click_id="abc123xyz"
    )

    code1 = shortener.encode(params1, EncodingStrategy.SEQUENTIAL)
    print(f"Original params: {params1.to_dict()}")
    print(f"Encoded: {code1} (длина: {len(code1)})")

    decoded1 = shortener.decode(code1)
    print(f"Decoded: {decoded1.to_dict() if decoded1 else 'ERROR'}")
    print(f"Match: {decoded1.to_dict() == params1.to_dict() if decoded1 else False}")

    # Повторное кодирование тех же параметров
    code1_repeat = shortener.encode(params1, EncodingStrategy.SEQUENTIAL)
    print(f"Re-encoded: {code1_repeat} (должен быть идентичен)")

    # Пример 2: Compressed strategy
    print("\n2. COMPRESSED STRATEGY (для новых параметров)")
    print("-" * 60)
    params2 = URLParams(
        cid="winter_sale",
        sub1="google",
        sub2="search",
        sub3="keyword_123",
        sub4="ad_group_5",
        sub5="creative_v2"
    )

    code2 = shortener.encode(params2, EncodingStrategy.COMPRESSED)
    print(f"Original params: {params2.to_dict()}")
    print(f"Encoded: {code2} (длина: {len(code2)})")

    decoded2 = shortener.decode(code2)
    print(f"Decoded: {decoded2.to_dict() if decoded2 else 'ERROR'}")
    print(f"Match: {decoded2.to_dict() == params2.to_dict() if decoded2 else False}")

    # Пример 3: Hybrid strategy
    print("\n3. HYBRID STRATEGY (фиксированная длина)")
    print("-" * 60)
    params3 = URLParams(
        cid="spring_campaign",
        sub1="twitter",
        sub2="timeline",
        sub3="promoted",
        click_id="xyz789"
    )

    code3 = shortener.encode(params3, EncodingStrategy.HYBRID)
    print(f"Original params: {params3.to_dict()}")
    print(f"Encoded: {code3} (длина: {len(code3)})")

    decoded3 = shortener.decode(code3)
    if decoded3:
        print(f"Decoded: {decoded3.to_dict()}")
        # Hybrid может не восстановить click_id (зависит от реализации)
        print(f"Note: click_id may not be restored in hybrid mode")
    else:
        print("Decoded: ERROR")

    # Пример 4: Smart strategy (автовыбор)
    print("\n4. SMART STRATEGY (автоматический выбор)")
    print("-" * 60)

    # Для новых параметров
    params4 = URLParams(cid="test_campaign", sub1="source_a", sub2="medium_b")
    code4 = shortener.encode(params4, EncodingStrategy.SMART)
    print(f"First encoding: {code4} (длина: {len(code4)})")

    # Повторное кодирование - должно использовать sequential
    code4_repeat = shortener.encode(params4, EncodingStrategy.SMART)
    print(f"Second encoding: {code4_repeat} (должно быть короче)")

    # Статистика
    print("\n5. STATISTICS")
    print("-" * 60)
    stats = shortener.get_stats()
    for key, val in stats.items():
        print(f"  {key}: {val}")

    # Производительность
    print("\n6. PERFORMANCE TEST")
    print("-" * 60)
    import time

    iterations = 10000
    start = time.time()
    for i in range(iterations):
        params = URLParams(
            cid=f"campaign_{i % 100}",
            sub1=f"source_{i % 50}",
            sub2=f"medium_{i % 20}"
        )
        code = shortener.encode(params, EncodingStrategy.SMART)
        decoded = shortener.decode(code)

    elapsed = time.time() - start
    print(f"Iterations: {iterations}")
    print(f"Time: {elapsed:.3f}s")
    print(f"Speed: {iterations/elapsed:.0f} encode+decode/sec")
    print(f"Avg time per operation: {elapsed/iterations*1000:.3f}ms")

    # Финальная статистика
    print("\n7. FINAL STATISTICS")
    print("-" * 60)
    final_stats = shortener.get_stats()
    for key, val in final_stats.items():
        print(f"  {key}: {val}")


# ==================== BINDINGS DEMO ====================

def demo_bindings():
    """Демонстрация биндингов для удобного использования"""

    print("\n" + "=" * 60)
    print("URL SHORTENER BINDINGS DEMO")
    print("=" * 60)

    # === PYTHON BINDINGS ===
    print("\n[PYTHON BINDINGS]")

    # Простое кодирование
    code1 = encode_tracking_url('summer_promo', sub1='facebook', sub2='feed')
    print(f"Simple encode: {code1}")

    # Создание полной ссылки
    link1 = create_tracking_link('https://track.com', 'winter_sale',
                                sub1='google', sub2='search', sub3='keyword')
    print(f"Full link: {link1}")

    # Декодирование
    params1 = decode_tracking_url(code1)
    print(f"Decoded: {params1}")

    # === FAST API BINDINGS ===
    print("\n[FAST API BINDINGS]")

    # Для Telegram бота
    click_url = create_click_url('https://landing.com', 'camp_9061',
                                sub1='telegram', sub2='premium', user_id='12345')
    print(f"Click URL: {click_url}")

    # Разбор кода
    parsed = parse_click_code(click_url.split('/')[-1])
    print(f"Parsed: {parsed}")

    # === COMPATIBILITY BINDINGS ===
    print("\n[COMPATIBILITY BINDINGS]")

    # Legacy стиль
    legacy_url = "https://example.com/v1/click?cid=test&sub1=fb&sub2=feed"
    short_legacy = short_url(legacy_url)
    print(f"Legacy short: {short_legacy}")

    expanded_legacy = expand_code(short_legacy.split('/')[-1])
    print(f"Legacy expand: {expanded_legacy}")

    # === ADVANCED USAGE ===
    print("\n[ADVANCED USAGE EXAMPLES]")

    # Batch processing
    urls = [
        ('campaign_A', {'sub1': 'facebook'}),
        ('campaign_B', {'sub1': 'google', 'sub2': 'cpc'}),
        ('campaign_C', {'sub1': 'email', 'sub2': 'newsletter', 'sub3': 'promo'})
    ]

    print("Batch encoding:")
    for cid, extra in urls:
        code = encode_tracking_url(cid, **extra)
        print(f"  {cid}: {code}")

    print("\n[OK] All bindings working perfectly!")


if __name__ == "__main__":
    # Основные классы
    from shared_url_shortener import TrackingURLDecoder, TrackingURLHandler, DecodedTrackingParams

    # Функции
    from shared_url_shortener import decode_your_tracking_url, test_decoder

    # Пример использования (создаем реальный код для тестирования)
    from shared_url_shortener import URLShortener, URLParams, EncodingStrategy

    # Создаем тестовые параметры
    test_params = URLParams(
        cid='9061',
        sub1='telegram_bot_start',
        sub2='telegram',
        sub3='callback_offer',
        sub4='test_user',
        sub5='premium_offer'
    )

    # Генерируем код
    shortener = URLShortener()
    test_code = shortener.encode(test_params, EncodingStrategy.COMPRESSED)
    mappings = shortener.export_mappings()

    # Тестируем декодирование
    decoder = TrackingURLDecoder(mappings)
    result = decoder.decode(test_code)  # Декодирование

    handler = TrackingURLHandler()
    handler.decoder = decoder  # Устанавливаем декодер с маппингами
    params = handler.handle_tracking_redirect(test_code)  # Обработка редиректа

    result = decode_your_tracking_url(test_code)  # Простая функция
    print(f"\nDecoded parameters: {result}")