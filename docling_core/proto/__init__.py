"""Protocol buffer definitions for DoclingDocument (gRPC/document API)."""

from docling_core.proto.gen.ai.docling.core.v1 import (
    docling_document_pb2 as docling_document_pb2,
)
from docling_core.utils.conversion import (
    docling_document_to_proto as docling_document_to_proto,
)
from docling_core.utils.conversion import (
    proto_to_docling_document as proto_to_docling_document,
)
