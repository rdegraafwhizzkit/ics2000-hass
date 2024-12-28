"""Platform for light integration."""
from __future__ import annotations

import math
import logging
import time
import threading
import voluptuous as vol

from typing import Any
from ics2000.Core import Hub
from ics2000.Devices import Device, Light, Dimmer
from .threader import KlikAanKlikUitThread, repeat

# Import the device class from the component that you want to support
import homeassistant.helpers.config_validation as cv
from homeassistant.components.light import ATTR_BRIGHTNESS, PLATFORM_SCHEMA, LightEntity, ColorMode
from homeassistant.const import CONF_PASSWORD, CONF_MAC, CONF_EMAIL,CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_MAC): cv.string,
    vol.Required(CONF_EMAIL): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional('tries'): cv.positive_int,
    vol.Optional('sleep'): cv.positive_int,
    vol.Optional(CONF_IP_ADDRESS): cv.matches_regex(r'[1-9][0-9]{0,2}(\.(0|[1-9][0-9]{0,2})){2}\.[1-9][0-9]{0,2}'),
    vol.Optional('aes'): cv.matches_regex(r'[a-zA-Z0-9]{32}')
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
        tries=int(config.get('tries', 1)),
        sleep=int(config.get('sleep', 3))
    ) for device in hub.devices if type(device) == Light or type(device) == Dimmer)


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
            _LOGGER.info(f'Adding dimmer with name {device.name}')
            self._attr_color_mode = ColorMode.BRIGHTNESS
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        else:
            _LOGGER.info(f'Adding device with name {device.name}')
            self._attr_color_mode = ColorMode.ONOFF
            self._attr_supported_color_modes = {ColorMode.ONOFF}

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
        if KlikAanKlikUitThread.has_running_threads(self._id):
            return

        self._brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
        if self.is_on is None or not self.is_on:
            KlikAanKlikUitThread(
                action=KlikAanKlikUitAction.TURN_ON,
                device_id=self._id,
                target=repeat,
                kwargs={
                    'tries': self.tries,
                    'sleep': self.sleep,
                    'callable_function': self._hub.turn_on,
                    'entity': self._id
                }
            ).start()
        else:
            # KlikAanKlikUit brightness goes from 1 to 15 so divide by 17
            KlikAanKlikUitThread(
                action=KlikAanKlikUitAction.DIM,
                device_id=self._id,
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
        if KlikAanKlikUitThread.has_running_threads(self._id):
            return

        KlikAanKlikUitThread(
            action=KlikAanKlikUitAction.TURN_OFF,
            device_id=self._id,
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
