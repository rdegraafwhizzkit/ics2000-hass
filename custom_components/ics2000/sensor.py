"""Platform for light integration."""
from __future__ import annotations

from abc import abstractmethod
import concurrent.futures
import logging
from typing import Any
import voluptuous as vol

from ics2000.Core import Hub
from ics2000.Devices import Device, TemperatureHumiditySensor

# Import the device class from the component that you want to support
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity, SensorDeviceClass
from homeassistant.const import CONF_PASSWORD, CONF_MAC, CONF_EMAIL, CONF_IP_ADDRESS, UnitOfTemperature, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from .device import KlikAanKlikUitDevice

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
    add_entities(
        KlikAanKlikUitHumidityDevice(
            device=device,
            tries=int(config.get('tries', 1)),
            sleep=int(config.get('sleep', 3))
        ) for device in hub.devices if isinstance(device, (TemperatureHumiditySensor))
    )

    add_entities(
        KlikAanKlikUitTemperatureDevice(
            device=device,
            tries=int(config.get('tries', 1)),
            sleep=int(config.get('sleep', 3))
        ) for device in hub.devices if isinstance(device, (TemperatureHumiditySensor))
    )


class KlikAanKlikUitSensorDevice(KlikAanKlikUitDevice, SensorEntity):
    """Representation of a KlikAanKlikUit temperature device"""

    def __init__(self, device: Device, sensorType: SensorDeviceClass, tries: int, sleep: int) -> None:
        """Initialize a KlikAanKlikUitDevice"""
        KlikAanKlikUitDevice.__init__(self, device, tries, sleep)
        self._attr_device_class = sensorType

    @abstractmethod
    def _get_value(self) -> Any:
        return -1.0

    def update(self) -> None:
        """Update state of the sensor"""
        try:
            val = self._get_value()
            if val != self._attr_native_value:
                self._attr_native_value = val
            self._attr_available = True
        except Exception as e:
            print(e)
            if self.available:  # Read current state, no need to prefix with _attr_
                _LOGGER.warning("Update failed for %s", self.entity_id)
            self._attr_available = False  # Set property value
            return


class KlikAanKlikUitHumidityDevice(KlikAanKlikUitSensorDevice):
    """Representation of a KlikAanKlikUit humidity device"""

    def __init__(self, device: Device, tries: int, sleep: int) -> None:
        """Initialize a KlikAanKlikUitHumidityDevice"""
        KlikAanKlikUitSensorDevice.__init__(self, device, SensorDeviceClass.HUMIDITY, tries, sleep)
        self._attr_native_unit_of_measurement = PERCENTAGE

    def _get_value(self):
        return self.get_humidity()

    def get_humidity(self) -> None:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(self._hub.get_humidity, self._id)
            return_value = future.result()
            print(return_value)
            return return_value


class KlikAanKlikUitTemperatureDevice(KlikAanKlikUitDevice):
    """Representation of a KlikAanKlikUit temperature device"""

    def __init__(self, device: Device, tries: int, sleep: int) -> None:
        """Initialize a KlikAanKlikUitTemperatureDevice"""
        KlikAanKlikUitSensorDevice.__init__(self, device, SensorDeviceClass.TEMPERATURE, tries, sleep)
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def _get_value(self):
        return self.get_temperature()

    def get_temperature(self) -> None:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(self._hub.get_temperature, self._id)
            return_value = future.result()
            print(return_value)
            return return_value
