from typing import Callable, Dict, Optional
from contextvars import ContextVar


class EmitterManager:
    def __init__(self) -> None:
        self._emit_ctx: ContextVar[Optional[Callable[[str], None]]] = ContextVar("emit_ctx", default=None)
        self._session_ctx: ContextVar[str] = ContextVar("session_ctx", default="default")
        self._session_emitters: Dict[str, Callable[[str], None]] = {}

    # Session context
    def set_session(self, session_id: str):
        return self._session_ctx.set(session_id)

    def reset_session(self, token) -> None:
        self._session_ctx.reset(token)

    def current_session(self) -> str:
        return self._session_ctx.get()

    # Emitters
    def set_emitter(self, emitter: Callable[[str], None]):
        return self._emit_ctx.set(emitter)

    def reset_emitter(self, token) -> None:
        self._emit_ctx.reset(token)

    def register_session_emitter(self, session_id: str, emitter: Callable[[str], None]) -> None:
        self._session_emitters[session_id] = emitter

    def unregister_session_emitter(self, session_id: str) -> None:
        self._session_emitters.pop(session_id, None)

    def get_emitter(self) -> Optional[Callable[[str], None]]:
        # Prefer session-scoped emitter, fall back to context emitter
        session_id = self.current_session()
        return self._session_emitters.get(session_id) or self._emit_ctx.get()


