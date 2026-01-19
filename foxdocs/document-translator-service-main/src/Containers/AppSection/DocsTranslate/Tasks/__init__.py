"""DocsTranslate Tasks"""

from .ProcessAndTranslateImageTask import ProcessAndTranslateImageTask
from .ProcessRegionsAndTranslateTask import ProcessRegionsAndTranslateTask
from .GetDocsTranslateStatusTask import GetDocsTranslateStatusTask

# Streaming tasks
from .StreamingProcessAndTranslateTask import StreamingProcessAndTranslateTask
from .StreamingProcessRegionsAndTranslateTask import StreamingProcessRegionsAndTranslateTask

__all__ = [
    "ProcessAndTranslateImageTask",
    "ProcessRegionsAndTranslateTask", 
    "GetDocsTranslateStatusTask",
    # Streaming
    "StreamingProcessAndTranslateTask",
    "StreamingProcessRegionsAndTranslateTask",
]




