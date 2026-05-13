# Create various broken/encoding-mixed JSON files for testing

# Case 1: UTF-8 file with GBK bytes inside a string value
with open('tests/data/mixed_enc_utf8_gbk.json', 'wb') as f:
    f.write(b'{"name": "Alice", "msg": "')
    f.write(b'\xd6\xd0\xce\xc4\xb2\xe2\xca\xd4')  # GBK encoded Chinese
    f.write(b'"}')

# Case 2: UTF-8 file with invalid bytes
with open('tests/data/bad_bytes_utf8.json', 'wb') as f:
    f.write(b'{"name": "Alice", "msg": "')
    f.write(b'\xff\xfe')  # invalid UTF-8 bytes
    f.write(b'"}')

# Case 3: GBK content with fake UTF-8 BOM
with open('tests/data/gbk_with_fake_bom.json', 'wb') as f:
    f.write(b'\xef\xbb\xbf')  # UTF-8 BOM
    f.write(b'{"name": "')
    f.write(b'\xd6\xd0\xce\xc4')  # GBK bytes
    f.write(b'"}')

# Case 4: Valid UTF-8 but bad JSON syntax (trailing comma)
with open('tests/data/bad_json_syntax.json', 'w', encoding='utf-8') as f:
    f.write('{"name": "Alice", "value": 123,}')

# Case 5: Null byte in the middle
with open('tests/data/null_byte_json.json', 'wb') as f:
    f.write(b'{"name": "Ali')
    f.write(b'\x00')
    f.write(b'ce"}')

print('Created 5 broken JSON test files')
