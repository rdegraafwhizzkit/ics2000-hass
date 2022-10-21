"""Platform for light integration."""
from __future__ import annotations

import logging
from typing import Any

from ics2000.Core import Hub
from ics2000.Devices import Device
import voluptuous as vol

# Import the device class from the component that you want to support
import homeassistant.helpers.config_validation as cv
from homeassistant.components.light import SUPPORT_BRIGHTNESS, PLATFORM_SCHEMA, LightEntity
from homeassistant.const import CONF_PASSWORD, CONF_MAC, CONF_EMAIL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)

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
        config.get(CONF_PASSWORD)
    )

    # Verify that passed in configuration works
    if not hub.connected:
        _LOGGER.error("Could not connect to ICS2000 hub")
        return

    # Add devices
    add_entities(KlikAanKlikUitDevice(device) for device in hub.devices)


class KlikAanKlikUitDevice(LightEntity):
    """Representation of a KlikAanKlikUit device"""

    _attr_supported_features: int = SUPPORT_BRIGHTNESS

    def __init__(self, light: Device) -> None:
        """Initialize an AwesomeLight."""
        # self._light = light
        self._name = light.name
        self._id = light.id
        self._hub = light.hub
        self._state = None
        self._brightness = None

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
        """Instruct the light to turn on.

        You can skip the brightness part if your light does not support
        brightness control.
        """
        # self._light.brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
        # self._light.turn_on()
        self._hub.turn_on(self._id)
        self._state = True

    def turn_off(self, **kwargs: Any) -> None:
        """Instruct the light to turn off."""
        self._hub.turn_off(self._id)
        self._state = False

    def update(self) -> None:
        """Fetch new state data for this light.

        This is the only method that should fetch new data for Home Assistant.
        """
        pass
        # self._light.update()
        # self._state = self._light.is_on()
        # self._brightness = self._light.brightness
