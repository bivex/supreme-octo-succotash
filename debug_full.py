# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:12:16
# Last Updated: 2025-12-18T12:45:18
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
import base64
import zlib

from shared_url_shortener import URLShortener, URLParams

# Recreate the exact encoding process
params = URLParams(
    cid='9061',
    sub1='telegram_bot_start',
    sub2='telegram',
    sub3='callback_offer',
    sub4='aaa_4441',
    sub5='premium_offer'
)

print('=== ENCODING PROCESS ===')
print('Params:', params.to_dict())

shortener = URLShortener()

# Step 1: Get campaign ID
cid = params.cid
if cid not in shortener.campaign_map:
    shortener.campaign_map[cid] = shortener.next_campaign_id
    shortener.reverse_campaign_map[shortener.next_campaign_id] = cid
    shortener.next_campaign_id += 1

campaign_id = shortener.campaign_map[cid]
print(f'Campaign ID: {campaign_id}')

# Step 2: Build params string
params_parts = []
for i in range(1, 6):
    val = getattr(params, f'sub{i}')
    if val:
        params_parts.append(f'{i}:{val}')
params_str = '|'.join(params_parts)
print(f'Params string: {repr(params_str)}')

# Step 3: Compress
compressed = zlib.compress(params_str.encode(), level=9)
print(f'Compressed: {compressed}')

# Step 4: Base64 encode
encoded_params = base64.urlsafe_b64encode(compressed).decode().rstrip('=')
print(f'Base64 encoded: {repr(encoded_params)}')

# Step 5: Build final code
campaign_code = shortener._encode_base62(campaign_id).zfill(2)[:2]
result = f'c{campaign_code}{encoded_params}'
print(f'Final code: {repr(result)}')

print('\n=== DECODING PROCESS ===')

# Extract parts
campaign_part = result[1:3]
params_part = result[3:]
print(f'Campaign part: {repr(campaign_part)}')
print(f'Params part: {repr(params_part)}')

# Decode campaign
campaign_id_num = shortener._decode_base62(campaign_part)
print(f'Campaign ID num: {campaign_id_num}')

# Try to decode params
try:
    # Add padding
    padding = (4 - len(params_part) % 4) % 4
    params_part_padded = params_part + '=' * padding
    print(f'Padded params: {repr(params_part_padded)}')

    # Decode base64
    compressed_data = base64.urlsafe_b64decode(params_part_padded)
    print(f'Compressed data: {compressed_data}')

    # Decompress
    decompressed = zlib.decompress(compressed_data)
    final_params = decompressed.decode()
    print(f'Decompressed params: {repr(final_params)}')

except Exception as e:
    print(f'Decoding failed: {e}')
