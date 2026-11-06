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
    EntitySelector,
    EntitySelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TimeSelector,
)

from .const import (
    CONF_EXCLUDED_PERSONS,
    CONF_LLM_AREA_LISTS,
    CONF_LLM_DEFAULT_LIST,
    CONF_LLM_PERSON_LISTS,
    CONF_NOTIFY_TARGETS,
    CONF_NOTIFY_UNASSIGNED_ALL,
    CONF_PRIORITY_LEVELS,
    CONF_SUMMARY_ENABLED,
    CONF_SUMMARY_PERSISTENT,
    CONF_SUMMARY_TIME,
    CONF_TIME_FORMAT,
    DEFAULT_FEATURES,
    DEFAULT_PRIORITY_LEVELS,
    DEFAULT_SUMMARY_TIME,
    DEFAULT_TIME_FORMAT,
    DOMAIN,
    NOTIFY_NONE,
    PRIORITY_LEVEL_CHOICES,
    TIME_FORMAT_CHOICES,
)

# Task titles listed in the "remove from tasks?" warning.
CONFIRM_MAX_TITLES = 10


def _active_persons(hass: HomeAssistant, options) -> list:
    """Person states that are not excluded, sorted by name."""
    excluded = set(options.get(CONF_EXCLUDED_PERSONS) or [])
    return sorted(
        (s for s in hass.states.async_all("person") if s.entity_id not in excluded),
        key=lambda s: (s.name or s.entity_id).casefold(),
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
            step_id="init",
            menu_options=["features", "persons", "notifications", "voice"],
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
        persons = _active_persons(self.hass, self.config_entry.options)
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
                    CONF_TIME_FORMAT: user_input.get(
                        CONF_TIME_FORMAT, DEFAULT_TIME_FORMAT
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
        time_format = options.get(CONF_TIME_FORMAT, DEFAULT_TIME_FORMAT)
        if time_format not in TIME_FORMAT_CHOICES:
            time_format = DEFAULT_TIME_FORMAT
        schema_dict[vol.Optional(CONF_TIME_FORMAT, default=time_format)] = (
            SelectSelector(
                SelectSelectorConfig(
                    options=TIME_FORMAT_CHOICES,
                    mode=SelectSelectorMode.DROPDOWN,
                    translation_key=CONF_TIME_FORMAT,
                )
            )
        )
        return self.async_show_form(
            step_id="notifications", data_schema=vol.Schema(schema_dict)
        )

    async def async_step_persons(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Persons that cannot be assigned. If any of them still appears in
        tasks, a confirmation step warns that they will be removed there."""
        manager = self.hass.data.get(DOMAIN)
        if user_input is not None:
            self._excluded = sorted(set(user_input.get(CONF_EXCLUDED_PERSONS) or []))
            if manager and manager.persons_in_tasks(self._excluded):
                return await self.async_step_persons_confirm()
            return self._save_excluded()
        current = [
            p for p in (self.config_entry.options.get(CONF_EXCLUDED_PERSONS) or [])
            if self.hass.states.get(p) is not None
        ]
        schema = vol.Schema(
            {
                vol.Optional(CONF_EXCLUDED_PERSONS, default=current): EntitySelector(
                    EntitySelectorConfig(domain="person", multiple=True)
                )
            }
        )
        return self.async_show_form(step_id="persons", data_schema=schema)

    async def async_step_persons_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        manager = self.hass.data.get(DOMAIN)
        if user_input is not None:
            if manager:
                manager.remove_persons(self._excluded)
                await manager.async_save_now()
            return self._save_excluded()
        used = manager.persons_in_tasks(self._excluded) if manager else []
        tasks = manager.tasks_with_persons(self._excluded) if manager else []
        names = []
        for person_id in used:
            state = self.hass.states.get(person_id)
            names.append(state.name if state and state.name else person_id)
        titles = [f"- {t.get('title') or '?'}" for t in tasks[:CONFIRM_MAX_TITLES]]
        if len(tasks) > CONFIRM_MAX_TITLES:
            titles.append(f"- … (+{len(tasks) - CONFIRM_MAX_TITLES})")
        return self.async_show_form(
            step_id="persons_confirm",
            data_schema=vol.Schema({}),
            description_placeholders={
                "persons": ", ".join(names),
                "count": str(len(tasks)),
                "tasks": "\n".join(titles),
            },
        )

    def _save_excluded(self) -> ConfigFlowResult:
        """Store the exclusion and drop the per-person settings of the
        excluded persons (notify target, voice list rule)."""
        excluded = set(self._excluded)
        options = dict(self.config_entry.options)
        options[CONF_EXCLUDED_PERSONS] = list(self._excluded)
        for key in (CONF_NOTIFY_TARGETS, CONF_LLM_PERSON_LISTS):
            per_person = options.get(key)
            if isinstance(per_person, dict):
                options[key] = {
                    k: v for k, v in per_person.items() if k not in excluded
                }
        return self.async_create_entry(data=options)

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
        for state in _active_persons(self.hass, options):
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
