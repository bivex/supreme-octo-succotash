# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:12:16
# Last Updated: 2025-12-18T12:28:32
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
import base64
import zlib

# Test what happens with the encoded data
encoded = 'eNoztCp'
print('Encoded data:', repr(encoded))

# Try different paddings
for padding in ['', '=', '==', '===']:
    try:
        test_data = encoded + padding
        print(f'Trying with padding "{padding}": {repr(test_data)}')

        compressed = base64.urlsafe_b64decode(test_data)
        print(f'Compressed bytes: {compressed}')

        decompressed = zlib.decompress(compressed)
        params_str = decompressed.decode()
        print(f'SUCCESS! Decompressed: {repr(params_str)}')
        break
    except Exception as e:
        print(f'Failed: {e}')
