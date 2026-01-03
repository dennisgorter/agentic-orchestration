"""In-memory session state management."""
from typing import Dict, Optional
from app.models import AgentState
from app.logging_config import get_logger

logger = get_logger(__name__)


class SessionStore:
    """Simple in-memory store for session states."""
    
    def __init__(self):
        self._sessions: Dict[str, AgentState] = {}
    
    def get(self, session_id: str) -> Optional[AgentState]:
        """Get session state by ID."""
        return self._sessions.get(session_id)
    
    def set(self, session_id: str, state: AgentState) -> None:
        """Store or update session state."""
        logger.info(f"[{session_id}] STATE SAVE - car_identifier: {state.car_identifier}, "
                   f"selected_car: {state.selected_car.plate if state.selected_car else None}, "
                   f"intent: {state.intent}, city: {state.city}")
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
            # Preserve language from previous turn
            previous_language = state.language
            # Preserve car context (selected_car and car_identifier) across turns
            previous_selected_car = state.selected_car
            previous_car_identifier = state.car_identifier
            
            logger.info(f"[{session_id}] STATE RESTORE - Previous car_identifier: {previous_car_identifier}, "
                       f"selected_car: {previous_selected_car.plate if previous_selected_car else None}")
            
            state.message = message
            state.reply = ""
            state.pending_question = False
            state.disambiguation_options = []
            # Keep the language if it was already detected
            if not previous_language:
                previous_language = "en"
            state.language = previous_language
            # Preserve car context unless it will be explicitly overridden by new message
            state.selected_car = previous_selected_car
            state.car_identifier = previous_car_identifier
            
            logger.info(f"[{session_id}] STATE AFTER RESET - car_identifier: {state.car_identifier}, "
                       f"selected_car: {state.selected_car.plate if state.selected_car else None}, "
                       f"language: {state.language}")
            
            return state
        else:
            # Create new session
            logger.info(f"[{session_id}] Creating NEW SESSION")
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
