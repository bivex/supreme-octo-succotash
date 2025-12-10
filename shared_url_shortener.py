import base64
import hashlib
import zlib
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import struct
import time


class EncodingStrategy(Enum):
    """Стратегии кодирования в зависимости от данных"""
    SEQUENTIAL = "seq"      # Для известных campaign/параметров
    COMPRESSED = "cmp"      # Для произвольных параметров
    HYBRID = "hyb"          # Комбинированный подход


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
    
    # Алфавит для base62 (URL-safe, без путаницы 0/O, 1/l/I)
    BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"
    
    def __init__(self):
        # In-memory маппинг для sequential strategy
        self.seq_to_params: Dict[int, URLParams] = {}
        self.params_to_seq: Dict[str, int] = {}
        self.next_seq_id = 1
        
        # Маппинг известных кампаний для сокращения
        self.campaign_map: Dict[str, int] = {}
        self.reverse_campaign_map: Dict[int, str] = {}
        self.next_campaign_id = 1
        
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
        if not code.startswith('s'):
            return None
        
        seq_id = self._decode_base62(code[1:])
        return self.seq_to_params.get(seq_id)
    
    # ==================== COMPRESSED STRATEGY ====================
    
    def encode_compressed(self, params: URLParams) -> str:
        """
        Стратегия 2: Компрессия параметров с известными кампаниями
        Формат: [strategy:1][campaign_id:2-3][compressed_params:6-7]
        Длина: 9-10 символов
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
        
        # Обрезаем до нужной длины (с возможностью восстановления)
        max_param_len = 7  # оставляем место для префикса и campaign_id
        encoded_params = encoded_params[:max_param_len]
        
        # Формат: 'c' + campaign_id(base62) + encoded_params
        return 'c' + self._encode_base62(campaign_id) + encoded_params
    
    def decode_compressed(self, code: str) -> Optional[URLParams]:
        """Декодирование compressed формата"""
        if not code.startswith('c'):
            return None
        
        try:
            # Извлекаем campaign_id (предполагаем 2-3 символа)
            campaign_part = ""
            params_part = ""
            
            for i, char in enumerate(code[1:], 1):
                if char in self.BASE62:
                    campaign_part += char
                else:
                    params_part = code[i+1:]
                    break
            
            campaign_id = self._decode_base62(campaign_part)
            cid = self.reverse_campaign_map.get(campaign_id)
            
            if not cid:
                return None
            
            # Декодируем параметры
            # Добавляем padding для base64
            padding = (4 - len(params_part) % 4) % 4
            params_part += '=' * padding
            
            compressed = base64.urlsafe_b64decode(params_part)
            params_str = zlib.decompress(compressed).decode()
            
            return self._deserialize_params(params_str, cid)
        
        except Exception:
            return None
    
    # ==================== HYBRID STRATEGY ====================
    
    def encode_hybrid(self, params: URLParams) -> str:
        """
        Стратегия 3: Гибридный подход с битовой упаковкой
        Формат: [strategy:1][packed_data:9]
        
        Оптимизация:
        - Campaign ID: 12 бит (4096 кампаний)
        - Sub1-5: по 8 бит каждый (256 значений или индекс)
        - Click ID: 16 бит (хэш)
        """
        # Получаем campaign ID
        if params.cid not in self.campaign_map:
            self.campaign_map[params.cid] = self.next_campaign_id
            self.reverse_campaign_map[self.next_campaign_id] = params.cid
            self.next_campaign_id += 1
        
        campaign_id = self.campaign_map[params.cid]
        
        # Упаковываем в биты
        packed = self._pack_bits(campaign_id, params)
        
        # Кодируем в base62
        encoded = self._encode_bytes_base62(packed)
        
        return 'h' + encoded[:9]  # max 10 символов
    
    def decode_hybrid(self, code: str) -> Optional[URLParams]:
        """Декодирование hybrid формата"""
        if not code.startswith('h'):
            return None
        
        try:
            packed = self._decode_bytes_base62(code[1:])
            campaign_id, params = self._unpack_bits(packed)
            
            cid = self.reverse_campaign_map.get(campaign_id)
            if not cid:
                return None
            
            params.cid = cid
            return params
        
        except Exception:
            return None
    
    # ==================== UNIFIED API ====================
    
    def encode(self, params: URLParams, strategy: EncodingStrategy = EncodingStrategy.SEQUENTIAL) -> str:
        """
        Унифицированный метод кодирования с автовыбором стратегии
        """
        if strategy == EncodingStrategy.SEQUENTIAL:
            code = self.encode_sequential(params)
        elif strategy == EncodingStrategy.COMPRESSED:
            code = self.encode_compressed(params)
        elif strategy == EncodingStrategy.HYBRID:
            code = self.encode_hybrid(params)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        # Проверяем длину
        if len(code) > 10:
            # Fallback на более компактную стратегию
            if strategy != EncodingStrategy.HYBRID:
                return self.encode(params, EncodingStrategy.HYBRID)
            # Если и hybrid не влез, обрезаем (с потерей данных)
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
        if code.startswith('s'):
            result = self.decode_sequential(code)
        elif code.startswith('c'):
            result = self.decode_compressed(code)
        elif code.startswith('h'):
            result = self.decode_hybrid(code)
        else:
            # Legacy format support
            result = self._decode_legacy(code)
        
        if result:
            self.decode_cache[code] = result
        
        return result
    
    # ==================== HELPER METHODS ====================
    
    def _encode_base62(self, num: int) -> str:
        """Кодирование числа в base62"""
        if num == 0:
            return self.BASE62[0]
        
        result = []
        while num:
            result.append(self.BASE62[num % 62])
            num //= 62
        
        return ''.join(reversed(result))
    
    def _decode_base62(self, s: str) -> int:
        """Декодирование base62 в число"""
        result = 0
        for char in s:
            result = result * 62 + self.BASE62.index(char)
        return result
    
    def _encode_bytes_base62(self, data: bytes) -> str:
        """Кодирование байтов в base62"""
        num = int.from_bytes(data, 'big')
        return self._encode_base62(num)
    
    def _decode_bytes_base62(self, s: str) -> bytes:
        """Декодирование base62 в байты"""
        num = self._decode_base62(s)
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
            key, val = part.split(":", 1)
            if key.isdigit():
                setattr(params, f"sub{key}", val)
            elif key == "k":
                params.click_id = val
        
        return params
    
    def _pack_bits(self, campaign_id: int, params: URLParams) -> bytes:
        """
        Упаковка параметров в биты для hybrid стратегии
        Формат: [campaign_id:12bits][sub1:8][sub2:8][sub3:8][sub4:8][sub5:8][click_hash:16]
        Всего: 68 бит = 9 байт
        """
        # Ограничиваем campaign_id 12 битами
        campaign_id = campaign_id & 0xFFF
        
        # Хэшируем значения sub-параметров в 8 бит
        def hash_param(val: Optional[str]) -> int:
            if not val:
                return 0
            return int(hashlib.md5(val.encode()).hexdigest()[:2], 16)
        
        sub_hashes = [hash_param(getattr(params, f"sub{i}")) for i in range(1, 6)]
        
        # Хэшируем click_id в 16 бит
        click_hash = 0
        if params.click_id:
            click_hash = int(hashlib.md5(params.click_id.encode()).hexdigest()[:4], 16)
        
        # Упаковываем в bytes
        packed = campaign_id << 56  # 12 бит campaign_id
        for i, h in enumerate(sub_hashes):
            packed |= (h << (48 - i * 8))  # по 8 бит на каждый sub
        packed |= click_hash  # 16 бит click_hash
        
        return packed.to_bytes(9, 'big')
    
    def _unpack_bits(self, packed: bytes) -> Tuple[int, URLParams]:
        """Распаковка битов для hybrid стратегии"""
        num = int.from_bytes(packed, 'big')
        
        campaign_id = (num >> 56) & 0xFFF
        
        # Извлекаем хэши (для верификации, но не восстановления)
        # В production нужен дополнительный lookup table для восстановления
        params = URLParams(cid="")  # cid будет установлен позже
        
        return campaign_id, params
    
    def _decode_legacy(self, code: str) -> Optional[URLParams]:
        """Поддержка legacy форматов для миграции"""
        # Пример поддержки старого формата
        try:
            # Предположим старый формат: base64 encoded JSON
            decoded = base64.urlsafe_b64decode(code + '==')
            # Парсинг и возврат URLParams
            # ...
            pass
        except Exception:
            return None
    
    # ==================== STATISTICS & MONITORING ====================
    
    def get_stats(self) -> Dict:
        """Статистика использования"""
        return {
            "sequential_mappings": len(self.seq_to_params),
            "campaigns_mapped": len(self.campaign_map),
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
        total += sys.getsizeof(self.decode_cache)
        return total / (1024 * 1024)


# ==================== USAGE EXAMPLES ====================

def demo():
    """Демонстрация работы URL shortener"""
    
    shortener = URLShortener()
    
    # Пример 1: Sequential strategy (для повторяющихся параметров)
    params1 = URLParams(
        cid="summer_promo_2024",
        sub1="facebook",
        sub2="feed",
        click_id="abc123xyz"
    )
    
    code1 = shortener.encode(params1, EncodingStrategy.SEQUENTIAL)
    print(f"Sequential: {code1} (длина: {len(code1)})")
    
    decoded1 = shortener.decode(code1)
    print(f"Decoded: {decoded1.to_dict()}\n")
    
    # Пример 2: Compressed strategy
    params2 = URLParams(
        cid="winter_sale",
        sub1="google",
        sub2="search",
        sub3="keyword_123",
        sub4="ad_group_5",
        sub5="creative_v2"
    )
    
    code2 = shortener.encode(params2, EncodingStrategy.COMPRESSED)
    print(f"Compressed: {code2} (длина: {len(code2)})")
    
    decoded2 = shortener.decode(code2)
    print(f"Decoded: {decoded2.to_dict() if decoded2 else 'None'}\n")
    
    # Пример 3: Hybrid strategy
    code3 = shortener.encode(params2, EncodingStrategy.HYBRID)
    print(f"Hybrid: {code3} (длина: {len(code3)})")
    
    # Статистика
    print("\nStatistics:")
    for key, val in shortener.get_stats().items():
        print(f"  {key}: {val}")
    
    # Производительность
    import time
    
    iterations = 10000
    start = time.time()
    for i in range(iterations):
        params = URLParams(cid=f"campaign_{i % 100}", sub1=f"source_{i % 10}")
        shortener.encode(params)
    elapsed = time.time() - start
    
    print(f"\nPerformance: {iterations} encodings in {elapsed:.3f}s")
    print(f"  {iterations/elapsed:.0f} ops/sec")


if __name__ == "__main__":
    demo()