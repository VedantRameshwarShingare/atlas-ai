"""Asynchronous document parse/chunk/embed/store worker."""

from app.scheduler.workers.base import BaseWorker


class DocumentProcessorWorker(BaseWorker):
    capability_name = "document_processor"
