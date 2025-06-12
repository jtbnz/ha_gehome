"""GE Home Switch Entities"""
import logging
from typing import Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers import entity_registry as er

from .entities import GeErdSwitch
from .const import DOMAIN
from .devices import ApplianceApi
from .update_coordinator import GeHomeUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: Callable):
    """GE Home sensors."""
    _LOGGER.debug(f'Starting async_setup_entry for GE Home switches, config_entry_id: {config_entry.entry_id}')
    coordinator: GeHomeUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    registry = er.async_get(hass)

    @callback
    def async_devices_discovered(apis: list[ApplianceApi]):
        _LOGGER.debug(f'async_devices_discovered called with {len(apis):d} appliance APIs')
        entities = []
        for api in apis:
            _LOGGER.debug(f'Processing API for appliance: {api.appliance.appliance_type} (Type: {api.appliance.appliance_type})')
            for entity in api.entities:
                if isinstance(entity, GeErdSwitch):
                    _LOGGER.debug(f'Found potential switch entity: {entity.entity_id}, ERD code: {entity.erd_code}')
                    if entity.erd_code in api.appliance._property_cache:
                        if not registry.async_is_registered(entity.entity_id):
                            _LOGGER.debug(f'Adding unregistered switch: {entity.entity_id}')
                            entities.append(entity)
                        else:
                            _LOGGER.debug(f'Switch already registered: {entity.entity_id}')
                    else:
                        _LOGGER.debug(f'ERD code {entity.erd_code} not in property cache for {entity.entity_id}')
                else:
                    _LOGGER.debug(f'Entity {entity.entity_id} is not a GeErdSwitch')
        
        _LOGGER.debug(f'Found {len(entities):d} new switches to add')
        async_add_entities(entities)

    #if we're already initialized at this point, call device
    #discovery directly, otherwise add a callback based on the
    #ready signal
    if coordinator.initialized:
        _LOGGER.debug('Coordinator already initialized, calling async_devices_discovered directly.')
        async_devices_discovered(coordinator.appliance_apis.values())
    else:    
        _LOGGER.debug('Coordinator not initialized, adding signal_ready callback.')
        # add the ready signal and register the remove callback
        coordinator.add_signal_remove_callback(
            async_dispatcher_connect(hass, coordinator.signal_ready, async_devices_discovered))
