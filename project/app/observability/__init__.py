"""Phoenix observability setup for LangChain/LangGraph tracing."""

import logging

logger = logging.getLogger(__name__)
_tracer_initialized = False


def setup_phoenix_tracing() -> bool:
    """Initialize Phoenix tracing for LangChain/LangGraph.

    This function sets up OpenTelemetry with the OpenInference
    LangChain instrumentation to automatically trace all LLM calls.

    Returns:
        True if tracing was initialized successfully, False otherwise.
    """
    global _tracer_initialized

    if _tracer_initialized:
        logger.debug("Phoenix tracing already initialized")
        return True

    from project.config import get_settings

    settings = get_settings()

    if not settings.phoenix_enabled:
        logger.info("Phoenix tracing disabled (PHOENIX_ENABLED=false)")
        return False

    try:
        from openinference.instrumentation.langchain import LangChainInstrumentor
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create(
            {
                "service.name": settings.phoenix_project_name,
                "service.version": "0.1.0",
            }
        )

        tracer_provider = TracerProvider(resource=resource)
        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.phoenix_collector_endpoint,
            insecure=True,
        )
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        trace.set_tracer_provider(tracer_provider)

        LangChainInstrumentor().instrument()

        _tracer_initialized = True
        logger.info(
            "Phoenix tracing initialized: %s", settings.phoenix_collector_endpoint
        )
        return True

    except ImportError as e:
        logger.warning("Phoenix dependencies not installed: %s", e)
        return False
    except Exception as e:
        logger.error("Failed to initialize Phoenix tracing: %s", e)
        return False


def is_tracing_enabled() -> bool:
    """Check if Phoenix tracing is currently enabled and initialized."""
    return _tracer_initialized
