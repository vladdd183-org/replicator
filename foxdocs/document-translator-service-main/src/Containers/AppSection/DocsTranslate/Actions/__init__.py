"""DocsTranslate Actions"""

from .ProcessFullImageAction import ProcessFullImageAction
from .ProcessRegionsAction import ProcessRegionsAction
from .GetStatusAction import GetStatusAction

# Streaming actions
from .StreamingProcessFullImageAction import StreamingProcessFullImageAction
from .StreamingProcessRegionsAction import StreamingProcessRegionsAction

# Deprecated - use specific actions instead
from .ProcessDocumentAction import ProcessDocumentAction

__all__ = [
    "ProcessFullImageAction",
    "ProcessRegionsAction",
    "GetStatusAction",
    # Streaming
    "StreamingProcessFullImageAction",
    "StreamingProcessRegionsAction",
    # Deprecated
    "ProcessDocumentAction",
]




