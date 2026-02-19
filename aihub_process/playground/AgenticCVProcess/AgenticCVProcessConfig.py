from typing import Annotated, Self

from aihub_lib.agents.AgentRef import AgentRef
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.elements.AgentSelector import AgentSelector
from aihub_lib.processes.ProcessConfig import ProcessConfig
from pydantic import Field


class AgenticCVProcessConfig(ProcessConfig):
    """
    Configuration for the AgenticCVProcess demo.

    Adds an agent selector so the user can choose which agent
    instance performs the CV analysis step.
    """

    cv_analysis_agent: Annotated[
        AgentRef | AgentSelector,
        Field(description="The agent instance that analyzes submitted CVs."),
    ]

    @classmethod
    def as_form(cls) -> Self:
        base = ProcessConfig.as_form()
        return cls(
            process_id=base.process_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            cv_analysis_agent=AgentSelector(
                label=LocaleString(
                    en="CV Analysis Agent",
                    de="CV-Analyse-Agent",
                    fr="Agent d'analyse CV",
                    it="Agente analisi CV",
                ),
                help=LocaleString(
                    en="Select the agent that will analyze submitted CVs",
                    de="Wählen Sie den Agenten, der eingereichte CVs analysiert",
                    fr="Sélectionnez l'agent qui analysera les CV soumis",
                    it="Seleziona l'agente che analizzerà i CV inviati",
                ),
            ),
        )
