"""
Phoenix observability integration for co-scientist framework.
"""

import os
import logging

# Import Phoenix
from phoenix.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_phoenix_tracing(endpoint: str = "http://localhost:6006/v1/traces") -> None:
    """
    Set up Phoenix tracing for LangChain.

    Parameters
    ----------
    endpoint : str
        Phoenix endpoint URL. Default is http://localhost:6006/v1/traces
    """
    try:
        # Register Phoenix as the tracer
        tracer_provider = register(endpoint=endpoint)

        # Instrument LangChain
        LangChainInstrumentor().instrument(tracer_provider=tracer_provider)

        logger.info(f"Phoenix tracing enabled. View traces at http://localhost:6006")
    except Exception as e:
        logger.warning(f"Failed to setup Phoenix tracing: {e}")
        logger.warning("Continuing without tracing...")
