"""Config flow for the Better ToDo integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback

from .const import DEFAULT_FEATURES, DOMAIN


class BetterTodoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Better ToDo."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if user_input is not None:
            return self.async_create_entry(title="Better ToDo", data={})
        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return BetterTodoOptionsFlow()


class BetterTodoOptionsFlow(OptionsFlow):
    """Feature toggles for Better ToDo."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        options = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Required(
                    key, default=bool(options.get(key, default))
                ): bool
                for key, default in DEFAULT_FEATURES.items()
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
