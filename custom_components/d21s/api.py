"""Wrapper for DT API."""

import collections.abc

import disruptive


class D21sAPI:
    """Handle D21S object creation and authentication."""

    def __init__(self, email: str, key_id: str, secret: str) -> None:
        """Initialize D21S API."""
        self._auth = disruptive.Auth.service_account(key_id, secret, email)

    def get_project(self, project_id: str) -> disruptive.Project:
        """Get project details by ID."""
        return disruptive.Project.get_project(project_id, auth=self._auth)

    def get_devices(self, project_id: str):
        """Get all devices in a project."""
        return disruptive.Device.list_devices(project_id, auth=self._auth)

    def stream_events(
        self, project_id: str
    ) -> collections.abc.Generator[disruptive.events.Event]:
        """Stream events from all devices in a project."""
        stream = disruptive.Stream.event_stream(
            project_id, request_attempts=0, auth=self._auth
        )
        yield from stream
