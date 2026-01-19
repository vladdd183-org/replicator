"""DocsTranslate Data Schemas"""

from .DocsTranslateSchemas import (
    TranslatedOCRResult,
    ProcessAndTranslateImageRequest,
    ProcessAndTranslateImageResponse,
    ProcessRegionsAndTranslateRequest,
    ProcessRegionsAndTranslateResponse,
    DocsTranslateStatus,
    # Streaming schemas
    StreamingConfig,
    ProgressEventType,
    RegionDetectedEvent,
    RegionOCRCompletedEvent,
    RegionTranslatedEvent,
    RegionProcessingFailedEvent,
    ProcessingCompletedEvent,
    ProgressEvent,
    StreamingProcessAndTranslateImageRequest,
    StreamingProcessRegionsAndTranslateRequest,
)

__all__ = [
    "TranslatedOCRResult",
    "ProcessAndTranslateImageRequest",
    "ProcessAndTranslateImageResponse",
    "ProcessRegionsAndTranslateRequest",
    "ProcessRegionsAndTranslateResponse",
    "DocsTranslateStatus",
    # Streaming
    "StreamingConfig",
    "ProgressEventType",
    "RegionDetectedEvent",
    "RegionOCRCompletedEvent",
    "RegionTranslatedEvent",
    "RegionProcessingFailedEvent",
    "ProcessingCompletedEvent",
    "ProgressEvent",
    "StreamingProcessAndTranslateImageRequest",
    "StreamingProcessRegionsAndTranslateRequest",
]




