from enum import IntEnum


class CaptchaStateEnum(IntEnum):
    STARTED = 0
    RETRIED = 1
    PASSED = 2
    FAILED = 3
