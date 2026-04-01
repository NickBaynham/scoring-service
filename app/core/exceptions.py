"""Domain and service exceptions."""


class ScoringServiceError(Exception):
    """Base exception for the scoring service."""

    def __init__(self, message: str, code: str = "internal_error") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class NotFoundError(ScoringServiceError):
    """Resource was not found."""

    def __init__(self, message: str = "Not found") -> None:
        super().__init__(message, code="not_found")


class DomainValidationError(ScoringServiceError):
    """Invalid input or state."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="validation_error")


class LLMError(ScoringServiceError):
    """LLM provider or parsing failure."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="llm_error")


class StorageError(ScoringServiceError):
    """Object storage failure."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="storage_error")


class UnauthorizedError(ScoringServiceError):
    """Missing or invalid credentials."""

    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(message, code="unauthorized")
