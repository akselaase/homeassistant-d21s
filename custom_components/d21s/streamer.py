"""Implements sensor event streaming and dispatches events."""

import asyncio
import logging
import threading

import disruptive
import requests

from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .api import D21sAPI
from .const import SENSOR_EVENT

LOGGER = logging.getLogger(__name__)


class Streamer:
    """Handles sensor event stream."""

    def __init__(self, hass: HomeAssistant, api: D21sAPI) -> None:
        """Initialize event streamer."""
        self._hass = hass
        self._api = api
        self._stop_event = threading.Event()

    async def stream_forever(self, project_id: str):
        """Continuously stream events until unload."""
        while not self._stop_event.is_set():
            try:
                await self._hass.async_add_executor_job(self._stream_once, project_id)
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                LOGGER.debug("Stream cancelled")
                self._stop_event.set()
            except Exception:
                LOGGER.exception("Unhandled exception")

    def _stream_once(self, project_id: str):
        try:
            stream = self._api.stream_events(project_id)
            for event in stream:
                self._dispatch(event)
                if self._stop_event.is_set():
                    break
        except disruptive.errors.DTApiError:
            LOGGER.exception("Stream error")
        except requests.exceptions.RequestException:
            LOGGER.exception("Request error")

    def _dispatch(self, event: disruptive.events.Event) -> None:
        LOGGER.debug(
            "Dispatching event: device_id=%s, event_type=%s, data=%s",
            event.device_id,
            event.event_type,
            event.data,
        )
        self._hass.add_job(
            async_dispatcher_send,
            self._hass,
            SENSOR_EVENT,
            event.device_id,
            event.event_type,
            event.data.timestamp,
            event.data,
        )
