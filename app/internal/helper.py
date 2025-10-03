import struct

import bcrypt


def hash_password(pw: str) -> bytes:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt())

def check_password(pw: str, pw_h: bytes):
    return bcrypt.checkpw(pw.encode(), pw_h)

def rfid_uids_to_little_endian_bytes(uids: list[int]) -> bytes:
    return b''.join(struct.pack('<I', uid) for uid in uids)
