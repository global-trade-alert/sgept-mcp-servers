"""Error taxonomy per design doc."""

from enum import Enum


class ErrorCode(str, Enum):
    MALFORMED_INPUT = "malformed_input"            # 400
    MISSING_API_KEY = "missing_api_key"            # 401
    INVALID_API_KEY = "invalid_api_key"            # 401
    INSUFFICIENT_TIER = "insufficient_tier"        # 403
    QUERY_NOT_FOUND = "query_not_found"            # 404
    QUERY_ARCHIVED = "query_archived"              # 410
    RATE_LIMITED = "rate_limited"                  # 429
    WORKER_DOWN = "worker_down"                    # 503
    QUORUM_FAILED = "quorum_failed"                # 503
    QUERY_TIMEOUT = "query_timeout"                # 504


HTTP_STATUS = {
    ErrorCode.MALFORMED_INPUT: 400,
    ErrorCode.MISSING_API_KEY: 401,
    ErrorCode.INVALID_API_KEY: 401,
    ErrorCode.INSUFFICIENT_TIER: 403,
    ErrorCode.QUERY_NOT_FOUND: 404,
    ErrorCode.QUERY_ARCHIVED: 410,
    ErrorCode.RATE_LIMITED: 429,
    ErrorCode.WORKER_DOWN: 503,
    ErrorCode.QUORUM_FAILED: 503,
    ErrorCode.QUERY_TIMEOUT: 504,
}


class APIError(Exception):
    def __init__(self, code: ErrorCode, message: str, **extra):
        self.code = code
        self.message = message
        self.extra = extra
        super().__init__(message)

    def to_dict(self) -> dict:
        d = {"error": self.code.value, "message": self.message}
        d.update(self.extra)
        return d

    @property
    def http_status(self) -> int:
        return HTTP_STATUS[self.code]
