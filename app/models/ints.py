from pydantic import conint

UINT32 = conint(ge=0, le=2**32 - 1)
UINT64 = conint(gt=0, le=2**64 - 1)

RFID_UID = UINT32
