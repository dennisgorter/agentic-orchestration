"""Structured logging configuration for traceability."""
import logging
import sys
from contextvars import ContextVar
from datetime import datetime
from typing import Optional

# Context variable to store trace_id across async calls
trace_id_var: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)


class TraceFormatter(logging.Formatter):
    """Custom formatter that includes trace_id in log messages."""
    
    def format(self, record):
        trace_id = trace_id_var.get()
        if trace_id:
            record.trace_id = trace_id
        else:
            record.trace_id = "no-trace"
        
        return super().format(record)


def setup_logging():
    """Configure structured logging for the application."""
    
    # Create formatter with trace_id
    formatter = TraceFormatter(
        '%(asctime)s | %(trace_id)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Set levels for specific loggers
    logging.getLogger('uvicorn').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    return logging.getLogger(name)


def set_trace_id(trace_id: str):
    """Set trace_id for current context."""
    trace_id_var.set(trace_id)


def get_trace_id() -> Optional[str]:
    """Get trace_id from current context."""
    return trace_id_var.get()
