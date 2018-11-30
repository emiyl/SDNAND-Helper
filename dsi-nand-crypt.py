#!/usr/bin/env python3

print("Created by Ian Burgwin (ihaveamac)\nhttps://github.com/ihaveamac")

from argparse import ArgumentParser
from hashlib import sha1
from struct import pack
from sys import exit

from Cryptodome.Cipher import AES
from Cryptodome.Util import Counter

TWLN_OFFSET = 0x10EE00
TWLN_SIZE = 0xCDF1200

TWLP_OFFSET = 0xCF09A00
TWLP_SIZE = 0x20B6600

parser = ArgumentParser(description='Decrypts Nintendo DSi NAND images, using the nocash footer.')
parser.add_argument('nand', help='NAND image')

a = parser.parse_args()

# used from http://www.falatic.com/index.php/108/python-and-bitwise-rotation
# converted to def because pycodestyle complained to me
def rol(val: int, r_bits: int, max_bits: int) -> int:
    return (val << r_bits % max_bits) & (2 ** max_bits - 1) |\
           ((val & (2 ** max_bits - 1)) >> (max_bits - (r_bits % max_bits)))


def keygen_twl(x: int, y: int):
    return rol((x ^ y) + 0xFFFEFB4E295902582A680F5F1A4F3E79, 42, 128).to_bytes(0x10, 'big')


class TWLCryptoWrapper:
    def __init__(self, key: bytes, ctr: int):
        self._cipher = AES.new(key, AES.MODE_CTR, counter=Counter.new(128, initial_value=ctr))

    def crypt(self, data: bytes) -> bytes:
        data_len = len(data)
        data_rev = bytearray(data_len)
        for i in range(0, data_len, 0x10):
            data_rev[i:i + 0x10] = data[i:i + 0x10][::-1]

        data_out = bytearray(self._cipher.encrypt(bytes(data_rev)))

        for i in range(0, data_len, 0x10):
            data_out[i:i + 0x10] = data_out[i:i + 0x10][::-1]
        return bytes(data_out[0:data_len])


with open(a.nand, 'rb+') as f:
    nand_size = f.seek(0, 2)
    if nand_size < 0xF000000:
        exit(f'NAND is too small (expected >= 0xF000000, got {nand_size:#X}')

    if not nand_size & 0x40 == 0x40:
        exit('Nocash block not found.')

    f.seek(nand_size - 0x40)
    nocash_blk = f.read(0x40)
    if nocash_blk[0:0x10] != b'DSi eMMC CID/CPU':
        exit('Could not find magic in nocash block. "DSi eMMC CID/CPU"')

    cid = int.from_bytes(sha1(nocash_blk[0x10:0x20]).digest()[0:16], 'little')
    consoleid = nocash_blk[0x20:0x28][::-1]

    twl_consoleid_list = (int.from_bytes(consoleid[4:8], 'big'), int.from_bytes(consoleid[0:4], 'big'))

    key_x_list = [twl_consoleid_list[0],
                  twl_consoleid_list[0] ^ 0x24EE6906,
                  twl_consoleid_list[1] ^ 0xE65B601D,
                  twl_consoleid_list[1]]

    key = keygen_twl(int.from_bytes(pack('<4I', *key_x_list), 'little'), 0xE1A00005202DDD1DBD4DC4D30AB9DC76)

    f.seek(0)

    # assuming the offset/sizes for twln/twlp, since they should never change
    # (anything different would not work on a real DSi anyway, I think)

    # decrypt header
    print('Decrypting header...')
    header = TWLCryptoWrapper(key, cid).crypt(f.read(0x200))
    f.seek(0)
    f.write(header)

    # decrypt twln
    print('Decrypting twln...')
    f.seek(TWLN_OFFSET)
    cipher_twln = TWLCryptoWrapper(key, cid + (TWLN_OFFSET >> 4))
    left = TWLN_SIZE
    while left > 0:
        to_read = min(0x10000, left)
        data = cipher_twln.crypt(f.read(to_read))
        f.seek(-to_read, 1)
        f.write(data)
        left -= to_read
        print(f'{TWLN_SIZE - left:#010x} / {TWLN_SIZE:#010x}', end='\r')
    print()

    # decrypt twlp
    print('Decrypting twlp...')
    f.seek(TWLP_OFFSET)
    cipher_twln = TWLCryptoWrapper(key, cid + (TWLP_OFFSET >> 4))
    left = TWLP_SIZE
    while left > 0:
        to_read = min(0x10000, left)
        data = cipher_twln.crypt(f.read(to_read))
        f.seek(-to_read, 1)
        f.write(data)
        left -= to_read
        print(f'{TWLP_SIZE - left:#010x} / {TWLP_SIZE:#010x}', end='\r')
    print()
