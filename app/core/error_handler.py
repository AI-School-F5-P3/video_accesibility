from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

class ErrorType(Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    VIDEO_PROCESSING_ERROR = "VIDEO_PROCESSING_ERROR"
    AUDIO_PROCESSING_ERROR = "AUDIO_PROCESSING_ERROR"
    AI_SERVICE_ERROR = "AI_SERVICE_ERROR"
    RESOURCE_ERROR = "RESOURCE_ERROR"
    SYSTEM_ERROR = "SYSTEM_ERROR"

@dataclass
class ErrorDetails:
    component: str
    message: str
    code: str
    suggestion: Optional[str] = None
    retry_count: int = 0

class ProcessingError(Exception):
    def __init__(
        self,
        error_type: ErrorType,
        details: ErrorDetails
    ):
        self.error_type = error_type
        self.details = details
        super().__init__(f"{error_type.value}: {details.message}")
        
        logger.error(
            "Error: %s - Component: %s - Message: %s",
            error_type.value,
            details.component,
            details.message
        )

    def should_retry(self) -> bool:
        retryable_errors = {
            ErrorType.AI_SERVICE_ERROR,
            ErrorType.RESOURCE_ERROR
        }
        return (
            self.error_type in retryable_errors and 
            self.details.retry_count < 3
        )

    def increment_retry(self):
        self.details.retry_count += 1