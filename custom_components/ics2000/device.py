"""Representation of a KlikAanKlikUit device in Home Assistant"""

from __future__ import annotations
import logging

from homeassistant.helpers.entity import Entity
from ics2000.Devices import Device

_LOGGER = logging.getLogger(__name__)

class KlikAanKlikUitDevice(Entity):
    """Representation of a KlikAanKlikUit device"""

    def __init__(self, device: Device, tries: int, sleep: int) -> None:
        """Initialize a KlikAanKlikUitDevice"""
        self.tries = tries
        self.sleep = sleep
        self._name = device.name
        self._id = device.id
        self._attr_unique_id = device.id
        self._hub = device.hub
        self._state = None
        _LOGGER.info('Adding device (%s) with name %s', device.__class__.__name__, device.name)

    @property
    def name(self) -> str:
        """Return the display name of this device."""
        return self._name
