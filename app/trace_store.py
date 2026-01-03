"""In-memory trace storage for workflow execution tracking."""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
from app.logging_config import get_logger

logger = get_logger(__name__)


class TraceStep(BaseModel):
    """A single step in the workflow execution."""
    step_number: int
    node_name: str
    timestamp: datetime
    input_state: Dict[str, Any]
    output_state: Dict[str, Any]
    duration_ms: float


class WorkflowTrace(BaseModel):
    """Complete trace of a workflow execution."""
    trace_id: str
    session_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_duration_ms: Optional[float] = None
    steps: List[TraceStep] = []
    final_reply: Optional[str] = None
    success: bool = True
    error: Optional[str] = None


class TraceStore:
    """In-memory store for execution traces."""
    
    def __init__(self, max_traces: int = 1000):
        self._traces: Dict[str, WorkflowTrace] = {}
        self._max_traces = max_traces
    
    def create_trace(self, trace_id: str, session_id: str) -> WorkflowTrace:
        """Create a new trace."""
        trace = WorkflowTrace(
            trace_id=trace_id,
            session_id=session_id,
            started_at=datetime.now()
        )
        
        # Clean up old traces if we exceed max
        if len(self._traces) >= self._max_traces:
            # Remove oldest trace
            oldest_id = min(self._traces.keys(), 
                          key=lambda k: self._traces[k].started_at)
            del self._traces[oldest_id]
            logger.info(f"Removed oldest trace: {oldest_id}")
        
        self._traces[trace_id] = trace
        logger.info(f"Created trace: {trace_id}")
        return trace
    
    def add_step(self, trace_id: str, node_name: str, 
                 input_state: Dict[str, Any], output_state: Dict[str, Any],
                 duration_ms: float):
        """Add a step to an existing trace."""
        if trace_id not in self._traces:
            logger.warning(f"Trace not found: {trace_id}")
            return
        
        trace = self._traces[trace_id]
        step = TraceStep(
            step_number=len(trace.steps) + 1,
            node_name=node_name,
            timestamp=datetime.now(),
            input_state=self._sanitize_state(input_state),
            output_state=self._sanitize_state(output_state),
            duration_ms=duration_ms
        )
        trace.steps.append(step)
        logger.debug(f"Added step {step.step_number} ({node_name}) to trace {trace_id}")
    
    def complete_trace(self, trace_id: str, final_reply: Optional[str] = None,
                      success: bool = True, error: Optional[str] = None):
        """Mark a trace as complete."""
        if trace_id not in self._traces:
            logger.warning(f"Trace not found: {trace_id}")
            return
        
        trace = self._traces[trace_id]
        trace.completed_at = datetime.now()
        trace.total_duration_ms = (trace.completed_at - trace.started_at).total_seconds() * 1000
        trace.final_reply = final_reply
        trace.success = success
        trace.error = error
        logger.info(f"Completed trace: {trace_id} (success={success}, steps={len(trace.steps)})")
    
    def get_trace(self, trace_id: str) -> Optional[WorkflowTrace]:
        """Get a trace by ID."""
        return self._traces.get(trace_id)
    
    def _sanitize_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize state for storage (remove large objects, convert types)."""
        sanitized = {}
        for key, value in state.items():
            # Skip internal fields
            if key.startswith('_'):
                continue
            
            # Convert pydantic models to dict
            if hasattr(value, 'model_dump'):
                sanitized[key] = value.model_dump()
            elif isinstance(value, list) and value and hasattr(value[0], 'model_dump'):
                sanitized[key] = [item.model_dump() for item in value]
            elif isinstance(value, (str, int, float, bool, type(None))):
                sanitized[key] = value
            elif isinstance(value, list):
                # Limit list length to prevent huge traces
                sanitized[key] = value[:10] if len(value) > 10 else value
            else:
                sanitized[key] = str(value)
        
        return sanitized


# Global trace store instance
_trace_store: Optional[TraceStore] = None


def get_trace_store() -> TraceStore:
    """Get or create global trace store."""
    global _trace_store
    if _trace_store is None:
        _trace_store = TraceStore()
    return _trace_store
