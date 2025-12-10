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
        Формат: [strategy:1][campaign_id:1-2][compressed_params:6-8]
        Длина: 8-10 символов
        """
        # Получаем или создаем campaign ID
        cid = params.cid
        if cid not in self.campaign_map:
            self.campaign_map[cid] = self.next_campaign_id
            self.reverse_campaign_map[self.next_campaign_id] = cid
            self.next_campaign_id += 1
        
        campaign_id = self.campaign_map[cid]
        
        # Собираем параметры (без cid)
        params_str = self._serialize_params(params, include_cid=False)
        
        # Сжимаем и кодируем
        compressed = zlib.compress(params_str.encode(), level=9)
        encoded_params = base64.urlsafe_b64encode(compressed).decode().rstrip('=')
        
        # Обрезаем до нужной длины
        max_param_len = 8  # оставляем место для префикса
        encoded_params = encoded_params[:max_param_len]
        
        # Формат: 'c' + campaign_id(base62) + '_' + encoded_params
        campaign_code = self._encode_base62(campaign_id)
        return f"c{campaign_code}{encoded_params}"[:10]
    
    def decode_compressed(self, code: str) -> Optional[URLParams]:
        """Декодирование compressed формата"""
        if not code.startswith('c') or len(code) < 3:
            return None
        
        try:
            # Найдем границу между campaign_id и параметрами
            # campaign_id кодируется в base62, params - в base64
            idx = 1
            while idx < len(code) and code[idx] in self.BASE62:
                idx += 1
            
            if idx >= len(code):
                return None
            
            campaign_part = code[1:idx]
            params_part = code[idx:]
            
            campaign_id = self._decode_base62(campaign_part)
            cid = self.reverse_campaign_map.get(campaign_id)
            
            if not cid:
                return None
            
            # Декодируем параметры
            padding = (4 - len(params_part) % 4) % 4
            params_part += '=' * padding
            
            compressed = base64.urlsafe_b64decode(params_part)
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
        
        # Гарантируем максимум 10 символов
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


if __name__ == "__main__":
    demo()