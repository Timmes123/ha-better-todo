"""Config flow for the Better ToDo integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
    OptionsFlowWithReload,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import (
    area_registry as ar,
    device_registry as dr,
    entity_registry as er,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TimeSelector,
)

from .const import (
    CONF_LLM_AREA_LISTS,
    CONF_LLM_DEFAULT_LIST,
    CONF_LLM_PERSON_LISTS,
    CONF_NOTIFY_TARGETS,
    CONF_NOTIFY_UNASSIGNED_ALL,
    CONF_PRIORITY_LEVELS,
    CONF_SUMMARY_ENABLED,
    CONF_SUMMARY_PERSISTENT,
    CONF_SUMMARY_TIME,
    DEFAULT_FEATURES,
    DEFAULT_PRIORITY_LEVELS,
    DEFAULT_SUMMARY_TIME,
    DOMAIN,
    NOTIFY_NONE,
    PRIORITY_LEVEL_CHOICES,
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


class BetterTodoOptionsFlow(OptionsFlowWithReload):
    """Options: feature toggles and reminder notifications.

    OptionsFlowWithReload reloads the entry automatically after a change, so
    feature toggles (incl. platforms) take effect without an update listener.
    """

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self.async_show_menu(
            step_id="init", menu_options=["features", "notifications", "voice"]
        )

    async def async_step_features(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            user_input[CONF_PRIORITY_LEVELS] = int(user_input[CONF_PRIORITY_LEVELS])
            return self.async_create_entry(
                data={**dict(self.config_entry.options), **user_input}
            )
        options = self.config_entry.options
        schema_dict: dict[Any, Any] = {
            vol.Required(key, default=bool(options.get(key, default))): bool
            for key, default in DEFAULT_FEATURES.items()
        }
        levels = options.get(CONF_PRIORITY_LEVELS, DEFAULT_PRIORITY_LEVELS)
        if levels not in PRIORITY_LEVEL_CHOICES:
            levels = DEFAULT_PRIORITY_LEVELS
        schema_dict[vol.Required(CONF_PRIORITY_LEVELS, default=str(levels))] = (
            SelectSelector(
                SelectSelectorConfig(
                    options=[str(x) for x in PRIORITY_LEVEL_CHOICES],
                    mode=SelectSelectorMode.DROPDOWN,
                    translation_key=CONF_PRIORITY_LEVELS,
                )
            )
        )
        return self.async_show_form(
            step_id="features", data_schema=vol.Schema(schema_dict)
        )

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

    async def async_step_voice(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """LLM API scope: default list, and per person / per satellite area
        the lists an assistant may use (nothing selected = all lists)."""
        options = self.config_entry.options
        manager = self.hass.data.get(DOMAIN)
        lists = sorted(
            (manager.data["lists"] if manager else []), key=lambda l: l.get("order", 0)
        )
        list_choices = {lst["id"]: lst["name"] for lst in lists}
        if user_input is not None:
            person_rules: dict[str, list[str]] = {}
            area_rules: dict[str, list[str]] = {}
            for key, value in user_input.items():
                if key == CONF_LLM_DEFAULT_LIST or not value:
                    continue
                if key.startswith("person."):
                    person_rules[key] = list(value)
                else:
                    area_rules[key] = list(value)
            return self.async_create_entry(
                data={
                    **dict(options),
                    CONF_LLM_DEFAULT_LIST: user_input.get(CONF_LLM_DEFAULT_LIST) or None,
                    CONF_LLM_PERSON_LISTS: person_rules,
                    CONF_LLM_AREA_LISTS: area_rules,
                }
            )
        person_rules = options.get(CONF_LLM_PERSON_LISTS) or {}
        area_rules = options.get(CONF_LLM_AREA_LISTS) or {}
        default = options.get(CONF_LLM_DEFAULT_LIST) or ""
        if default not in list_choices:
            default = ""
        schema_dict: dict[Any, Any] = {
            vol.Optional(CONF_LLM_DEFAULT_LIST, default=default): vol.In(
                {"": NOTIFY_NONE, **list_choices}
            )
        }
        persons = sorted(
            self.hass.states.async_all("person"),
            key=lambda s: (s.name or s.entity_id).casefold(),
        )
        for state in persons:
            current = [i for i in person_rules.get(state.entity_id, []) if i in list_choices]
            schema_dict[vol.Optional(state.entity_id, default=current)] = cv.multi_select(
                list_choices
            )
        areas = _satellite_areas(self.hass, set(area_rules))
        for area_id, _name in areas:
            current = [i for i in area_rules.get(area_id, []) if i in list_choices]
            schema_dict[vol.Optional(area_id, default=current)] = cv.multi_select(
                list_choices
            )
        return self.async_show_form(step_id="voice", data_schema=vol.Schema(schema_dict))


def _satellite_areas(hass: HomeAssistant, extra: set[str]) -> list[tuple[str, str]]:
    """Areas that contain an Assist satellite (plus ``extra`` ids that
    already have a rule), as (area_id, name) sorted by name."""
    ent_reg = er.async_get(hass)
    dev_reg = dr.async_get(hass)
    area_reg = ar.async_get(hass)
    area_ids = set(extra)
    for entry in ent_reg.entities.values():
        if entry.domain != "assist_satellite":
            continue
        area_id = entry.area_id
        if not area_id and entry.device_id:
            device = dev_reg.async_get(entry.device_id)
            area_id = device.area_id if device else None
        if area_id:
            area_ids.add(area_id)
    result = []
    for area_id in area_ids:
        area = area_reg.async_get_area(area_id)
        result.append((area_id, area.name if area else area_id))
    return sorted(result, key=lambda item: item[1].casefold())
