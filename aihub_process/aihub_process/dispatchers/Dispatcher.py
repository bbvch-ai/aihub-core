import asyncio
from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Any, Type, Callable

from bson import ObjectId

from aihub_api.routes.process.AgenticProcess import AgenticProcess
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.persistence.process.AgentProcessStepInstanceEntity import AgentProcessStepInstanceEntity
from aihub_lib.persistence.process.HumanProcessStepInstanceEntity import HumanProcessStepInstanceEntity
from aihub_lib.persistence.process.ProcessStepInstanceEntity import ProcessStepInstanceEntity
from aihub_lib.persistence.process.ProgramProcessStepInstanceEntity import ProgramProcessStepInstanceEntity
from aihub_process.process.entities.BaseProcessEntity import BaseProcessEntity as DecoratorBaseProcessEntity
from aihub_process.process.entities.agent.Agent import Agent as DecoratorAgent
from aihub_process.process.entities.human.Human import Human as DecoratorHuman
from aihub_process.process.entities.program.Program import Program as DecoratorProgram
from aihub_process.process.entities.terminal.Terminal import Terminal as DecoratorTerminal
from aihub_process.process.io.Work import Work
from aihub_process.process.io.WorkRequest import WorkRequest

from aihub_process.process.io.agent.AgentWorkRequest import AgentWorkRequest
from aihub_process.process.io.human.HumanWorkRequest import HumanWorkRequest
from aihub_process.process.io.program.ProgramWorkRequest import ProgramWorkRequest


@dataclass
class DecoratorMetadata:
    input_from_config: DecoratorBaseProcessEntity.In
    delegate_to_config: DecoratorBaseProcessEntity.Out
    step_def_name: str
    display_icon: str
    display_name_ls: LocaleString
    display_description_ls: LocaleString

def get_decorator_metadata(step_method: Callable) -> DecoratorMetadata:
    return DecoratorMetadata(
        input_from_config=getattr(step_method, "_input_from_config", None),
        delegate_to_config=getattr(step_method, "_delegate_to_config", None),
        step_def_name=getattr(step_method, "_python_method_name", step_method.__name__),
        display_icon=getattr(step_method, "_step_icon", None),
        display_name_ls=getattr(step_method, "_step_name", None),
        display_description_ls=getattr(step_method, "_step_description", None),
    )


class ProcessDispatcher:
    def __init__(self, process: Type[AgenticProcess]): # AgenticProcess class
        self.process = process

    async def _delegate_to_agent(self, process_instance_id: str, db_step_doc: AgentProcessStepInstanceEntity, work_request: AgentWorkRequest):
        print(f"[{process_instance_id}] Delegating to Agent: {work_request.agent_class}/{work_request.agent_id}, StartEvent: {work_request.start_event.event_id}")
        persisted_start_event_id = "fake_persisted_event_id_" + work_request.start_event.event_id # Placeholder
        db_step_doc.work_request_start_event_id = persisted_start_event_id
        await asyncio.sleep(0.1)
        print(f"[{process_instance_id}] Published StartEvent to NATS for Agent.")

    async def _delegate_to_human(self, process_instance_id: str, db_step_doc: HumanProcessStepInstanceEntity, work_request: HumanWorkRequest):
        print(f"[{process_instance_id}] Delegating to Human: Task Schema {db_step_doc.work_request_task_schema_name}")
        # Complex logic for populating possible_choices deferred
        db_step_doc.work_request_possible_choices = []
        await asyncio.sleep(0.1)
        print(f"[{process_instance_id}] Notified Human users.")

    async def _delegate_to_program(self, process_instance_id: str, db_step_doc: ProgramProcessStepInstanceEntity, work_request: ProgramWorkRequest):
        print(f"[{process_instance_id}] Delegating to Program: Schema {db_step_doc.work_request_schema_name}")
        await asyncio.sleep(0.1)
        print(f"[{process_instance_id}] Made HTTP call to Program.")


    async def execute_step_method(
            self,
            process_instance_id: str,
            step_method_to_execute: Callable,
            input_work_obj: Work
    ):
        print(f"[{process_instance_id}] Executing step method: {step_method_to_execute.__name__}")

        metadata = get_decorator_metadata(step_method_to_execute)
        decorator_input_from_config: DecoratorBaseProcessEntity.In = metadata.input_from_config
        decorator_delegate_to_config: DecoratorBaseProcessEntity.Out = metadata.delegate_to_config

        if not decorator_delegate_to_config:
            raise ValueError(f"Step method {metadata.step_def_name} is missing delegation configuration.")

        process_instance_obj = self.process()
        output_work_request_obj: WorkRequest = await step_method_to_execute(process_instance_obj, input_work_obj)

        if output_work_request_obj is None and not isinstance(decorator_delegate_to_config, DecoratorTerminal.Out):
            print(f"Warning: Step {metadata.step_def_name} returned None but was not DecoratorTerminal.Out. Assuming terminal.")
            decorator_delegate_to_config = DecoratorTerminal.Out() # Use instance of Terminal.Out

        db_input_config = decorator_input_from_config.to_persisted()
        db_delegation_config = decorator_delegate_to_config.to_persisted()

        StepDocClass = decorator_delegate_to_config.get_step_doc_type()

        current_step_doc: ProcessStepInstanceEntity = StepDocClass(
            process_class_name=self.process.__name__,
            process_instance_id=process_instance_id,
            step_definition_name=metadata.step_def_name,
            display_name=metadata.display_name_ls.model_dump() if metadata.display_name_ls else {"en": metadata.step_def_name},
            display_icon=metadata.display_icon,
            display_description=metadata.display_description_ls.model_dump() if metadata.display_description_ls else None,
            input_from_config=db_input_config,
            delegate_to_config=db_delegation_config,
            initiated_at=datetime.now(UTC),
        )

        # Populate type-specific WorkRequest fields before saving
        if isinstance(decorator_delegate_to_config, DecoratorHuman.Out):
            current_step_doc.work_request_task_schema_name = output_work_request_obj.__class__.__name__
        elif isinstance(decorator_delegate_to_config, DecoratorProgram.Out):
            current_step_doc.work_request_schema_name = output_work_request_obj.__class__.__name__
            current_step_doc.work_request_payload = output_work_request_obj.model_dump()
        # Agent's work_request_start_event_id is set during its delegate method

        if isinstance(decorator_delegate_to_config, DecoratorTerminal.Out):
            current_step_doc.status = "COMPLETED"
            current_step_doc.completed_at = datetime.now(UTC)
            print(f"[{process_instance_id}] Step {metadata.step_def_name} is terminal. Marked as COMPLETED.")
        else:
            current_step_doc.status = "AWAITING_RESPONSE"

        current_step_doc.save()
        print(f"[{process_instance_id}] Saved new step doc {current_step_doc.id} for {metadata.step_def_name} with status {current_step_doc.status}")

        delegation_successful = True
        if not isinstance(decorator_delegate_to_config, DecoratorTerminal.Out):
            try:
                # Polymorphic call to the delegate method
                await decorator_delegate_to_config.delegate(
                    self, process_instance_id, current_step_doc, output_work_request_obj
                )
            except Exception as e:
                delegation_successful = False
                print(f"[{process_instance_id}] Delegation failed for step {metadata.step_def_name}: {e}")
                current_step_doc.status = "FAILED"
                current_step_doc.error_details = {"type": e.__class__.__name__, "message": str(e)}
                current_step_doc.completed_at = datetime.now(UTC)

        current_step_doc.save() # Save again to reflect delegation changes
        print(f"[{process_instance_id}] Updated step doc {current_step_doc.id} after delegation attempt with status {current_step_doc.status}")

        if not delegation_successful:
            pass # Handle process failure

    async def handle_initial_trigger(
            self,
            process_class_name: str,
            initial_work_obj: Any, # Pydantic 'Work' model (e.g. SubmittedCV)
            start_step_method: Callable # The @process_start decorated method
    ):
        process_instance_id = str(ObjectId())
        print(f"[{process_instance_id}] Handling initial trigger for {process_class_name}")

        metadata = get_decorator_metadata(start_step_method)
        decorator_input_from_config: DecoratorBaseProcessEntity.In = metadata.input_from_config

        db_input_config = decorator_input_from_config.to_persisted()

        # Determine the DB Step Doc type for the trigger step based on its input_from config
        TriggerStepDocClass: Type[ProcessStepInstanceEntity]
        if isinstance(decorator_input_from_config, DecoratorProgram.In):
            TriggerStepDocClass = ProgramProcessStepInstanceEntity
        elif isinstance(decorator_input_from_config, DecoratorAgent.In):
            TriggerStepDocClass = AgentProcessStepInstanceEntity
        elif isinstance(decorator_input_from_config, DecoratorHuman.In):
            TriggerStepDocClass = HumanProcessStepInstanceEntity
        else:
            raise ValueError(f"Unsupported initial trigger input type: {type(decorator_input_from_config)}")

        trigger_step_doc: ProcessStepInstanceEntity = TriggerStepDocClass(
            process_class_name=process_class_name,
            process_instance_id=process_instance_id,
            step_definition_name=metadata.step_def_name,
            display_name=metadata.display_name_ls.model_dump() if metadata.display_name_ls else {"en": metadata.step_def_name},
            display_icon=metadata.display_icon,
            display_description=metadata.display_description_ls.model_dump() if metadata.display_description_ls else None,
            input_from_config=db_input_config,
            delegate_to_config=DecoratorTerminal.Out().to_persisted(), # Trigger step is terminal
            status="COMPLETED",
            initiated_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )

        # Populate the 'work_response' fields of the trigger step with the initial_work_obj data
        if isinstance(trigger_step_doc, ProgramProcessStepInstanceEntity):
            trigger_step_doc.work_response_schema_name = initial_work_obj.__class__.__name__
            trigger_step_doc.work_response_payload = initial_work_obj.model_dump()
        elif isinstance(trigger_step_doc, AgentProcessStepInstanceEntity):
            trigger_step_doc.work_response_stop_event_id = "fake_initial_agent_event_id" # Placeholder
        elif isinstance(trigger_step_doc, HumanProcessStepInstanceEntity):
            trigger_step_doc.work_response_chosen_action_name = "initial_trigger" # Or derive if possible
            trigger_step_doc.work_response_chosen_action_schema_name = initial_work_obj.__class__.__name__
            trigger_step_doc.work_response_chosen_action_payload = initial_work_obj.model_dump()

        trigger_step_doc.save()
        print(f"[{process_instance_id}] Saved initial trigger step doc {trigger_step_doc.id}")

        await self.execute_step_method(
            process_instance_id=process_instance_id,
            step_method_to_execute=start_step_method,
            input_work_obj=initial_work_obj
        )

    async def handle_subsequent_work(
            self,
            process_instance_id: str,
            next_step_method_to_execute: Callable,
            received_work_obj: Any, # Pydantic 'Work' model instance
            # DB doc of the step that was 'AWAITING_RESPONSE' and just got this work
            active_step_doc_being_completed: ProcessStepInstanceEntity
    ):
        print(f"[{process_instance_id}] Handling subsequent work for step def {active_step_doc_being_completed.step_definition_name}, to trigger {next_step_method_to_execute.__name__}")

        active_step_doc_being_completed.status = "COMPLETED"
        active_step_doc_being_completed.completed_at = datetime.now(UTC)

        # Populate the 'work_response' fields based on the type of step and received_work_obj
        if isinstance(active_step_doc_being_completed, AgentProcessStepInstanceEntity):
            active_step_doc_being_completed.work_response_stop_event_id = "fake_received_agent_event_id" # Placeholder
        elif isinstance(active_step_doc_being_completed, HumanProcessStepInstanceEntity):
            action_name = "unknown_action" # Placeholder - this needs to be passed in or derived
            active_step_doc_being_completed.work_response_chosen_action_name = action_name
            active_step_doc_being_completed.work_response_chosen_action_schema_name = received_work_obj.__class__.__name__
            active_step_doc_being_completed.work_response_chosen_action_payload = received_work_obj.model_dump()
        elif isinstance(active_step_doc_being_completed, ProgramProcessStepInstanceEntity):
            active_step_doc_being_completed.work_response_schema_name = received_work_obj.__class__.__name__
            active_step_doc_being_completed.work_response_payload = received_work_obj.model_dump()

        active_step_doc_being_completed.save()
        print(f"[{process_instance_id}] Marked step doc {active_step_doc_being_completed.id} as COMPLETED.")

        await self.execute_step_method(
            process_instance_id=process_instance_id,
            step_method_to_execute=next_step_method_to_execute,
            input_work_obj=received_work_obj
        )