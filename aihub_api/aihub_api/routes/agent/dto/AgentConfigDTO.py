from typing import Annotated

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.discovery.agent.AgentConfigSpecs import AgentConfigSpecs
from aihub_lib.nats.events.discovery.agent.AgentConfigSpecsEntity import AgentConfigSpecsEntity
from aihub_lib.nats.events.form import ALL_FORM_OPTIONS, Checkbox, InputNumber, InputText, Slider
from aihub_lib.nats.events.form.base.FormkitElement import FormkitElement
from pydantic import BaseModel, Field


class AgentConfigDTO(BaseModel):
    model_config = {
        "use_enum_values": True,
        # Ensure nested models serialize by alias
        "populate_by_name": True,
    }

    agent_id: Annotated[str, Field(description="The id of the agent.")]
    name: Annotated[str, Field(description="The name of the agent.")]
    description: Annotated[str, Field(description="The description of the agent.")]
    icon: Annotated[str, Field(description="The icon representing the agent.")] = "meteor-icons:robot"
    form: Annotated[
        list[ALL_FORM_OPTIONS] | None,
        Field(description="Dynamic form configuration for agent runtime settings."),
    ] = None

    @classmethod
    def from_agent_config_specs(cls, agent_config_specs: AgentConfigSpecs, t: LocaleHandler) -> "AgentConfigDTO":
        form = [form.in_locale(t) for form in agent_config_specs.form]
        return cls(
            agent_id=agent_config_specs.agent_id,
            name=t.extract(agent_config_specs.name),
            description=t.extract(agent_config_specs.description),
            icon=agent_config_specs.icon,
            form=form,
        )

    @classmethod
    def from_agent_config_entity_specs(
        cls, agent_config_specs_entity: AgentConfigSpecsEntity | None, t: LocaleHandler
    ) -> "AgentConfigDTO | None":
        """
        Create an AgentConfigDTO from a persisted AgentConfigSpecsEntity.
        Returns None if agent_config_specs_entity is None (for backwards compatibility with
        agents that were stored before agent_config_specs was added to AgentEntity).
        """
        if agent_config_specs_entity is None:
            return None

        # Use form_elements property to deserialize dicts back to typed Pydantic models
        form_elements = agent_config_specs_entity.form_elements
        form = [form_element.in_locale(t) for form_element in form_elements]
        return cls(
            agent_id=agent_config_specs_entity.agent_id,
            name=t.extract(agent_config_specs_entity.to_locale_string_name()),
            description=t.extract(agent_config_specs_entity.to_locale_string_description()),
            icon=agent_config_specs_entity.icon,
            form=form,
        )

    @staticmethod
    def _generate_mock_form(t: LocaleHandler) -> list[FormkitElement]:
        """
        Generate mock form data for testing the agent configuration UI.
        This simulates what agent_config.to_formkit_form() will eventually provide.
        """
        return [
            InputText(
                name="api_endpoint",
                label=LocaleString(
                    de="API-Endpunkt",
                    en="API Endpoint",
                    fr="Point de terminaison API",
                    it="Endpoint API",
                ),
                help=LocaleString(
                    de="Die URL des API-Endpunkts für diesen Agenten",
                    en="The URL of the API endpoint for this agent",
                    fr="L'URL du point de terminaison API pour cet agent",
                    it="L'URL dell'endpoint API per questo agente",
                ),
                placeholder=LocaleString(
                    de="https://api.example.com",
                    en="https://api.example.com",
                    fr="https://api.example.com",
                    it="https://api.example.com",
                ),
                required=True,
            ).in_locale(t),
            InputNumber(
                name="max_retries",
                label=LocaleString(
                    de="Maximale Wiederholungsversuche",
                    en="Maximum Retries",
                    fr="Nombre maximum de tentatives",
                    it="Tentativi massimi",
                ),
                help=LocaleString(
                    de="Anzahl der Wiederholungsversuche bei Fehlern",
                    en="Number of retry attempts on failures",
                    fr="Nombre de tentatives de nouvelle tentative en cas d'échec",
                    it="Numero di tentativi in caso di errori",
                ),
                min=0,
                max=10,
                step=1,
                show_buttons=True,
                required=True,
            ).in_locale(t),
            Slider(
                name="temperature",
                label=LocaleString(
                    de="Temperatur",
                    en="Temperature",
                    fr="Température",
                    it="Temperatura",
                ),
                help=LocaleString(
                    de="Steuert die Zufälligkeit der LLM-Ausgabe (0.0 = deterministisch, 1.0 = kreativ)",
                    en="Controls the randomness of LLM output (0.0 = deterministic, 1.0 = creative)",
                    fr="Contrôle le caractère aléatoire de la sortie LLM (0.0 = déterministe, 1.0 = créatif)",
                    it="Controlla la casualità dell'output LLM (0.0 = deterministico, 1.0 = creativo)",
                ),
                min=0.0,
                max=2.0,
                step=0.1,
            ).in_locale(t),
            Checkbox(
                name="enable_caching",
                label=LocaleString(
                    de="Caching aktivieren",
                    en="Enable Caching",
                    fr="Activer la mise en cache",
                    it="Abilita cache",
                ),
                help=LocaleString(
                    de="Aktiviert das Caching von API-Antworten zur Leistungsverbesserung",
                    en="Enables caching of API responses for performance improvement",
                    fr="Active la mise en cache des réponses API pour améliorer les performances",
                    it="Abilita la cache delle risposte API per migliorare le prestazioni",
                ),
                binary=True,
            ).in_locale(t),
            Checkbox(
                name="verbose_logging",
                label=LocaleString(
                    de="Ausführliche Protokollierung",
                    en="Verbose Logging",
                    fr="Journalisation détaillée",
                    it="Logging dettagliato",
                ),
                help=LocaleString(
                    de="Aktiviert detaillierte Logging-Ausgaben für Debugging",
                    en="Enables detailed logging output for debugging",
                    fr="Active la sortie de journalisation détaillée pour le débogage",
                    it="Abilita l'output di logging dettagliato per il debug",
                ),
                binary=True,
            ).in_locale(t),
        ]
