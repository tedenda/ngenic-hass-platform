import logging
from datetime import timedelta

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.const import (
    CONF_TOKEN
)

from .const import DOMAIN
from .errors import AlreadyConfigured, NoTunes

from ngenicpy import Ngenic
from ngenicpy.exceptions import ClientException

_LOGGER = logging.getLogger(__name__)

@callback
def configured_instances(hass):
    """Return a set of configured Ngenic instances."""
    return set(
        entry.data[CONF_TOKEN] for entry in hass.config_entries.async_entries(DOMAIN)
    )

@config_entries.HANDLERS.register(DOMAIN)
class FlowHandler(config_entries.ConfigFlow):
    
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_PUSH

    async def async_step_import(self, import_config):
        """Import a config entry from configuration.yaml."""
        return await self.async_step_user(import_config)

    async def async_step_user(self, user_input=None):
        """Handle the start of the config flow."""
        
        errors = {}

        if user_input is not None:
            try:
                if user_input[CONF_TOKEN] in configured_instances(self.hass):
                    raise AlreadyConfigured

                ngenic = Ngenic(
                    token=user_input[CONF_TOKEN]
                )

                tune_name = None
                
                for tune in ngenic.tunes():
                    tune_name = tune["tuneName"]
        
                if tune_name is None:
                    raise NoTunes

                return self.async_create_entry(
                    title=tune_name, data=user_input
                )

            except ClientException:
                errors["base"] = "bad_token"

            except AlreadyConfigured:
                errors["base"] = "already_configured"
            
            except NoTunes:
                errors["base"] = "no_tune"

        
        return self.async_show_form(
            step_id='user',
            data_schema=vol.Schema({
                vol.Required(CONF_TOKEN): str
            }),
            errors=errors
        )

        