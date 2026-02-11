import time
from google.adk.sessions import InMemorySessionService, Session


class AutoCreateSessionService(InMemorySessionService):
    """Session service that automatically creates sessions on first access."""

    async def get_session(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str,
        config=None,
    ):
        """Get existing session or auto-create a new one."""
        existing = await super().get_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            config=config,
        )

        if existing:
            return existing

        # Auto-create session
        if app_name not in self.sessions:
            self.sessions[app_name] = {}
        if user_id not in self.sessions[app_name]:
            self.sessions[app_name][user_id] = {}

        new_session = Session(
            app_name=app_name,
            user_id=user_id,
            id=session_id,
            state={},
            last_update_time=time.time(),
        )

        self.sessions[app_name][user_id][session_id] = new_session
        return new_session
