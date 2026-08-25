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

from homeassistant.helpers.selector import TimeSelector

from .const import (
    CONF_NOTIFY_TARGETS,
    CONF_NOTIFY_UNASSIGNED_ALL,
    CONF_SUMMARY_ENABLED,
    CONF_SUMMARY_PERSISTENT,
    CONF_SUMMARY_TIME,
    DEFAULT_FEATURES,
    DEFAULT_SUMMARY_TIME,
    DOMAIN,
    NOTIFY_NONE,
)


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
    """Options: feature toggles and reminder notifications."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self.async_show_menu(
            step_id="init", menu_options=["features", "notifications"]
        )

    async def async_step_features(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                data={**dict(self.config_entry.options), **user_input}
            )
        options = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Required(
                    key, default=bool(options.get(key, default))
                ): bool
                for key, default in DEFAULT_FEATURES.items()
            }
        )
        return self.async_show_form(step_id="features", data_schema=schema)

    async def async_step_notifications(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        persons = sorted(
            self.hass.states.async_all("person"),
            key=lambda s: (s.name or s.entity_id).casefold(),
        )
        if user_input is not None:
            targets = {
                entity_id: service
                for entity_id, service in user_input.items()
                if entity_id.startswith("person.") and service != NOTIFY_NONE
            }
            return self.async_create_entry(
                data={
                    **dict(self.config_entry.options),
                    CONF_NOTIFY_TARGETS: targets,
                    CONF_NOTIFY_UNASSIGNED_ALL: bool(
                        user_input.get(CONF_NOTIFY_UNASSIGNED_ALL)
                    ),
                    CONF_SUMMARY_ENABLED: bool(user_input.get(CONF_SUMMARY_ENABLED)),
                    CONF_SUMMARY_TIME: user_input.get(
                        CONF_SUMMARY_TIME, DEFAULT_SUMMARY_TIME
                    ),
                    CONF_SUMMARY_PERSISTENT: bool(
                        user_input.get(CONF_SUMMARY_PERSISTENT)
                    ),
                }
            )
        options = self.config_entry.options
        services = sorted(self.hass.services.async_services().get("notify", {}))
        current = options.get(CONF_NOTIFY_TARGETS) or {}
        schema_dict: dict[Any, Any] = {
            vol.Optional(
                state.entity_id,
                default=current.get(state.entity_id, NOTIFY_NONE),
            ): vol.In([NOTIFY_NONE, *services])
            for state in persons
        }
        schema_dict[
            vol.Optional(
                CONF_NOTIFY_UNASSIGNED_ALL,
                default=bool(options.get(CONF_NOTIFY_UNASSIGNED_ALL)),
            )
        ] = bool
        schema_dict[
            vol.Optional(
                CONF_SUMMARY_ENABLED,
                default=bool(options.get(CONF_SUMMARY_ENABLED)),
            )
        ] = bool
        schema_dict[
            vol.Optional(
                CONF_SUMMARY_TIME,
                default=options.get(CONF_SUMMARY_TIME, DEFAULT_SUMMARY_TIME),
            )
        ] = TimeSelector()
        schema_dict[
            vol.Optional(
                CONF_SUMMARY_PERSISTENT,
                default=bool(options.get(CONF_SUMMARY_PERSISTENT)),
            )
        ] = bool
        return self.async_show_form(
            step_id="notifications", data_schema=vol.Schema(schema_dict)
        )
