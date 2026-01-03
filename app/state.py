"""In-memory session state management."""
from typing import Dict, Optional
from app.models import AgentState


class SessionStore:
    """Simple in-memory store for session states."""
    
    def __init__(self):
        self._sessions: Dict[str, AgentState] = {}
    
    def get(self, session_id: str) -> Optional[AgentState]:
        """Get session state by ID."""
        return self._sessions.get(session_id)
    
    def set(self, session_id: str, state: AgentState) -> None:
        """Store or update session state."""
        self._sessions[session_id] = state
    
    def delete(self, session_id: str) -> None:
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
    
    def create_or_get(self, session_id: str, message: str = "") -> AgentState:
        """Get existing session or create new one."""
        if session_id in self._sessions:
            # Update message and reset for new turn
            state = self._sessions[session_id]
            state.message = message
            state.reply = ""
            state.pending_question = False
            state.disambiguation_options = []
            return state
        else:
            # Create new session
            state = AgentState(session_id=session_id, message=message)
            self._sessions[session_id] = state
            return state


# Global session store instance
_session_store: Optional[SessionStore] = None


def get_session_store() -> SessionStore:
    """Get or create global session store."""
    global _session_store
    if _session_store is None:
        _session_store = SessionStore()
    return _session_store
