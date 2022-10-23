"""Platform for light integration."""
from __future__ import annotations

import math
import logging
import time
from typing import Any

from ics2000.Core import Hub
from ics2000.Devices import Device, Dimmer
import threading

import voluptuous as vol

# Import the device class from the component that you want to support
import homeassistant.helpers.config_validation as cv
from homeassistant.components.light import ATTR_BRIGHTNESS, SUPPORT_BRIGHTNESS, PLATFORM_SCHEMA, LightEntity
from homeassistant.const import CONF_PASSWORD, CONF_MAC, CONF_EMAIL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)


def repeat(tries: int, sleep: int, callable_function, **kwargs):
    _LOGGER.info(f'Function repeat called in thread {threading.current_thread().name}')
    qualname = getattr(callable_function, '__qualname__')
    for i in range(0, tries):
        _LOGGER.info(f'Try {i + 1} of {tries} on {qualname}')
        callable_function(**kwargs)
        time.sleep(sleep if i != tries - 1 else 0)


# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_MAC): cv.string,
    vol.Required(CONF_EMAIL): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
})


def setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        add_entities: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the ICS2000 Light platform."""
    # Assign configuration variables.
    # The configuration check takes care they are present.
    # Setup connection with devices/cloud
    hub = Hub(
        config[CONF_MAC],
        config[CONF_EMAIL],
        config[CONF_PASSWORD]
    )

    # Verify that passed in configuration works
    if not hub.connected:
        _LOGGER.error("Could not connect to ICS2000 hub")
        return

    # Add devices
    add_entities(KlikAanKlikUitDevice(
        device=device,
        tries=int(config.get('tries', 3)),
        sleep=int(config.get('sleep', 3))
    ) for device in hub.devices)


class KlikAanKlikUitDevice(LightEntity):
    """Representation of a KlikAanKlikUit device"""

    def __init__(self, device: Device, tries: int, sleep: int) -> None:
        """Initialize a KlikAanKlikUitDevice"""
        self.tries = tries
        self.sleep = sleep
        self._name = device.name
        self._id = device.id
        self._hub = device.hub
        self._state = None
        self._brightness = None
        if Dimmer == type(device):
            self._attr_supported_features = SUPPORT_BRIGHTNESS
        else:
            self._attr_supported_features = 0

    @property
    def name(self) -> str:
        """Return the display name of this light."""
        return self._name

    @property
    def brightness(self):
        """Return the brightness of the light.

        This method is optional. Removing it indicates to Home Assistant
        that brightness is not supported for this light.
        """
        return self._brightness

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""
        return self._state

    def turn_on(self, **kwargs: Any) -> None:
        _LOGGER.info(f'Function turn_on called in thread {threading.current_thread().name}')
        if 'kaku_turn_off' in [thread.name for thread in threading.enumerate()]:
            _LOGGER.info(f'Thread kaku_turn_off still running')
            return

        self._brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
        if self.is_on is None or not self.is_on:
            threading.Thread(
                name='kaku_turn_on',
                target=repeat,
                kwargs={
                    'tries': self.tries,
                    'sleep': self.sleep,
                    'callable_function': self._hub.turn_on,
                    'entity': self._id
                }
            ).start()
        else:
            # KAKU brightness goes from 1 - 15
            threading.Thread(
                name='kaku_dim',
                target=repeat,
                kwargs={
                    'tries': self.tries,
                    'sleep': self.sleep,
                    'callable_function': self._hub.dim,
                    'entity': self._id,
                    'level': math.ceil(self.brightness / 17)
                }
            ).start()
        self._state = True

    def turn_off(self, **kwargs: Any) -> None:
        _LOGGER.info(f'Function turn_off called in thread {threading.current_thread().name}')
        if 'kaku_turn_on' in [thread.name for thread in threading.enumerate()]:
            _LOGGER.info(f'Thread kaku_turn_on still running')
            return

        threading.Thread(
            name='kaku_turn_off',
            target=repeat,
            kwargs={
                'tries': self.tries,
                'sleep': self.sleep,
                'callable_function': self._hub.turn_off,
                'entity': self._id
            }
        ).start()
        self._state = False

    def update(self) -> None:
        pass
