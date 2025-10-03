from pydantic import conint

UINT32 = conint(ge=0, le=2**32 - 1)
UINT64 = conint(gt=0, le=2**64 - 1)

RFID_UID = UINT32
CHIP_ID = conint(ge=0, le=2**63 - 1) # Because postgres BigInteger
