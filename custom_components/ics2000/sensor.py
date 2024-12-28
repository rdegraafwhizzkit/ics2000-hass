"""Platform for light integration."""
from __future__ import annotations

import concurrent.futures
import math
import logging
import time
import threading
import voluptuous as vol

from typing import Any
from ics2000.Core import Hub
from ics2000.Devices import Device, TemperatureHumiditySensor
from .threader import KlikAanKlikUitAction, KlikAanKlikUitThread, single_result

# Import the device class from the component that you want to support
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorEntity,
    SensorDeviceClass,
)
from homeassistant.const import CONF_PASSWORD, CONF_MAC, CONF_EMAIL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_MAC): cv.string,
        vol.Required(CONF_EMAIL): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional("tries"): cv.positive_int,
        vol.Optional("sleep"): cv.positive_int,
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the ICS2000 Light platform."""
    # Assign configuration variables.
    # The configuration check takes care they are present.
    # Setup connection with devices/cloud
    hub = Hub(config[CONF_MAC], config[CONF_EMAIL], config[CONF_PASSWORD])

    # Verify that passed in configuration works
    if not hub.connected:
        _LOGGER.error("Could not connect to ICS2000 hub")
        return

    # Add devices
    add_entities(
        KlikAanKlikUitDevice(device=device, sensorType=SensorDeviceClass.HUMIDITY)
        for device in hub.devices
        if type(device) == TemperatureHumiditySensor
    )

    add_entities(
        KlikAanKlikUitDevice(device=device, sensorType=SensorDeviceClass.TEMPERATURE)
        for device in hub.devices
        if type(device) == TemperatureHumiditySensor
    )


class KlikAanKlikUitDevice(SensorEntity):
    """Representation of a KlikAanKlikUit device"""

    def __init__(self, device: Device, sensorType: SensorDeviceClass) -> None:
        """Initialize a KlikAanKlikUitDevice"""
        self._name = device.name
        self._id = device.id
        self._hub = device.hub
        self._state = None
        self._attr_device_class = sensorType

    @property
    def name(self) -> str:
        """Return the display name of this sensor."""
        return self._name

    def get_humidity(self) -> None:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(self._hub.get_humidity, self._id)
            return_value = future.result()
            print(return_value)
            return return_value

    def get_temperature(self) -> None:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(self._hub.get_temperature, self._id)
            return_value = future.result()
            print(return_value)
            return return_value

    def update(self) -> None:
        """Update state of the sensor"""
        try:
            val = -1.0
            if SensorDeviceClass.HUMIDITY == self._attr_device_class:
                val = self.get_humidity()
            elif SensorDeviceClass.TEMPERATURE == self._attr_device_class:
                val = self.get_temperature()

            if val != self._attr_native_value:
                self._attr_native_value = val
            self._attr_available = True
        except Exception as e:
            print(e)
            if self.available:  # Read current state, no need to prefix with _attr_
                _LOGGER.warning("Update failed for %s", self.entity_id)
            self._attr_available = False  # Set property value
            return
