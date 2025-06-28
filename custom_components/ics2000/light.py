"""Platform for light integration."""
from __future__ import annotations

import math
import logging
import time
import threading
import voluptuous as vol

from typing import Any
from ics2000.Core import Hub
from ics2000.Devices import Device, Dimmer
from enum import Enum

# Import the device class from the component that you want to support
import homeassistant.helpers.config_validation as cv
from homeassistant.components.light import ATTR_BRIGHTNESS, PLATFORM_SCHEMA, LightEntity, ColorMode
from homeassistant.const import CONF_PASSWORD, CONF_MAC, CONF_EMAIL,CONF_IP_ADDRESS
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
    vol.Optional('tries'): cv.positive_int,
    vol.Optional('sleep'): cv.positive_int,
    vol.Optional(CONF_IP_ADDRESS): cv.matches_regex(r'[1-9][0-9]{0,2}(\.(0|[1-9][0-9]{0,2})){2}\.[1-9][0-9]{0,2}'),
    vol.Optional('aes'): cv.matches_regex(r'[a-zA-Z0-9]{32}'),
    # Nieuwe optie voor zonnescherm devices
    vol.Optional('awning_devices'): vol.All(cv.ensure_list, [cv.string])  # Device IDs die zonneschermen zijn
})


def setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        add_entities: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the ICS2000 Light platform."""
    # Assign configuration variables.
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

    # Debug: Print alle devices met hun IDs
    _LOGGER.info("=== ICS2000 DEVICES FOUND ===")
    for device in hub.devices:
        _LOGGER.info(f"Device ID: {device.id}, Name: {device.name}, Type: {type(device).__name__}")
    _LOGGER.info("=== END DEVICE LIST ===")

    entities = []
    awning_device_ids = config.get('awning_devices', [])
    
    for device in hub.devices:
        if str(device.id) in awning_device_ids:
            # Voeg zonnescherm toe als twee aparte lights
            _LOGGER.info(f"Adding awning device {device.name} as two separate lights")
            entities.append(KlikAanKlikUitDevice(
                device=device,
                tries=int(config.get('tries', 1)),
                sleep=int(config.get('sleep', 3)),
                awning_direction='up'
            ))
            entities.append(KlikAanKlikUitDevice(
                device=device,
                tries=int(config.get('tries', 1)),
                sleep=int(config.get('sleep', 3)),
                awning_direction='down'
            ))
        else:
            # Normale light
            entities.append(KlikAanKlikUitDevice(
                device=device,
                tries=int(config.get('tries', 1)),
                sleep=int(config.get('sleep', 3))
            ))

    add_entities(entities)


class KlikAanKlikUitAction(Enum):
    TURN_ON = 'on'
    TURN_OFF = 'off'
    DIM = 'dim'


class KlikAanKlikUitThread(threading.Thread):

    def __init__(self, action: KlikAanKlikUitAction, device_id, target, kwargs):
        super().__init__(
            # Thread name may be 15 characters max
            name=f'kaku{action.value}{device_id}',
            target=target,
            kwargs=kwargs
        )

    @staticmethod
    def has_running_threads(device_id) -> bool:
        running_threads = [thread.name for thread in threading.enumerate() if thread.name in [
            f'kaku{KlikAanKlikUitAction.TURN_ON.value}{device_id}',
            f'kaku{KlikAanKlikUitAction.DIM.value}{device_id}',
            f'kaku{KlikAanKlikUitAction.TURN_OFF.value}{device_id}'
        ]]
        if running_threads:
            _LOGGER.info(f'Running KlikAanKlikUit threads: {",".join(running_threads)}')
            return True
        return False


class KlikAanKlikUitDevice(LightEntity):
    """Representation of a KlikAanKlikUit device"""

    def __init__(self, device: Device, tries: int, sleep: int, awning_direction: str = None) -> None:
        """Initialize a KlikAanKlikUitDevice"""
        self.tries = tries
        self.sleep = sleep
        self.awning_direction = awning_direction
        
        if awning_direction:
            # Voor zonneschermen: voeg richting toe aan naam
            self._name = f"{device.name} {awning_direction.title()}"
            self.unique_id = f'kaku-{device.id}-{awning_direction}'
        else:
            # Normale light
            self._name = device.name
            self.unique_id = f'kaku-{device.id}'
            
        self._id = device.id
        self._hub = device.hub
        self._state = None
        self._brightness = None
        
        # Bepaal color mode op basis van device type en of het een zonnescherm is
        if Dimmer == type(device) and not awning_direction:
            _LOGGER.info(f'Adding dimmer with name {self._name}')
            self._attr_color_mode = ColorMode.BRIGHTNESS
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        else:
            _LOGGER.info(f'Adding device with name {self._name}')
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
        _LOGGER.info(f'Function turn_on called for {self._name} in thread {threading.current_thread().name}')
        if KlikAanKlikUitThread.has_running_threads(self._id):
            return

        # Voor zonneschermen: bepaal welke actie uitgevoerd moet worden
        if self.awning_direction == 'up':
            # Zonnescherm omhoog
            _LOGGER.info(f'Moving awning {self._name} UP')
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
            self._state = True
            
        elif self.awning_direction == 'down':
            # Zonnescherm omlaag
            _LOGGER.info(f'Moving awning {self._name} DOWN')
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
            self._state = True
            
        else:
            # Normale light logica
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
        _LOGGER.info(f'Function turn_off called for {self._name} in thread {threading.current_thread().name}')
        
        # Voor zonnescherm devices, turn_off betekent "stop beweging"
        if self.awning_direction:
            _LOGGER.info(f'Stopping awning {self._name}')
            self._state = False
            return
            
        # Normale light logica
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
