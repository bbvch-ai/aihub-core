import logging
from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from langfuse import Evaluation, get_client
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.prompts import ChatPromptTemplate, PromptTemplate, RichPromptTemplate
from nats.aio.client import Client as NATS

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.generative_ai.evaluation.JudgeOutput import JudgeOutput
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.infrastructure.langfuse.LangfuseSettings import LangfuseSettings
from aihub_lib.nats.distributor.ExternalAgentEventDistributor import ExternalAgentEventDistributor
from aihub_lib.routes.chat.ChatService import ChatContent, ChatService, JsonResources

logger = logging.getLogger(__name__)


class LangfuseExperimentEvaluator:
    """
    Orchestrates evaluations of agents using Langfuse experiments.

    ### Why this Evaluator?
    It bridges the gap between our agent interaction mechanism (ChatService via NATS)
    and the Langfuse evaluation framework. It standardizes how we:
    1.  Run agents against test datasets.
    2.  Evaluate their responses using LLM-based judges.
    3.  Log these results back to Langfuse for analysis.

    It uses a "Judge LLM" with structured prompts and few-shot examples (loaded via i18n)
    to provide consistent, automated evaluations on dimensions like correctness,
    completeness, and conciseness.
    """

    def __init__(
        self,
        nats_client: NATS,
        external_agent_event_distributor: ExternalAgentEventDistributor,
        judge: LLMConfig,
        authenticated_user: UserIdentity,
        t: LocaleHandler,
    ):
        """
        Initializes the evaluator.
        """
        # Validate settings are configured - will raise if not
        _ = LangfuseSettings()
        self.langfuse_client = get_client()
        self.langfuse_client.auth_check()  # Verify credentials are valid
        self.nats_client = nats_client
        self.external_agent_event_distributor = external_agent_event_distributor
        self.user = authenticated_user
        self.judge = judge
        self.t = t
        self.llm_judge_kwargs = {"temperature": 0.0}

    async def _agent_interaction_task(
        self,
        example_input: dict[str, Any],
        agent_class: str,
        agent_id: str,
    ) -> dict[str, Any]:
        """
        Task function for Langfuse: sends a question to the agent and returns its response.
        Encapsulates the complex NATS-based communication, needed to interact with our agents,
        handling event streams and responses.
        """
        question = example_input.get("question")
        if not question:
            raise ValueError("Question not found in example input.")

        messages = [ChatMessage(role=MessageRole.USER, content=question)]

        thread_id = ObjectId()
        display_id = ObjectId()

        json_resources: JsonResources = await ChatService.start_json_chat_interaction(
            user=self.user,
            agent_class=agent_class,
            agent_id=agent_id,
            messages=messages,
            nc=self.nats_client,
            external_agent_event_distributor=self.external_agent_event_distributor,
            thread_id=thread_id,
            display_id=display_id,
            locale=self.t.locale,
        )
        await json_resources.stop_signal.wait()

        if json_resources.stop_event and json_resources.stop_event.is_exception_event:
            logger.error(f"Agent interaction error for question '{question}': {json_resources.stop_event.message}")
            return {
                "agent_response": "",
                "error": json_resources.stop_event.message,
                "thread_id": str(thread_id),
                "display_id": str(display_id),
            }

        chat_content: ChatContent = ChatService.build_json_response_content(
            json_resources.chunk_events, json_resources.stop_event
        )
        return {
            "agent_response": chat_content.content,
            "thread_id": str(thread_id),
            "display_id": str(display_id),
        }

    def _build_judge_prompt_template(self, evaluator_type: str, user_input_structure: str) -> RichPromptTemplate:
        """
        Constructs the RichPromptTemplate for the LLM judge using i18n strings.
        """
        system_base = self.t("lib.evaluation.judge.system_base")
        system_addon = self.t(f"lib.evaluation.judge.{evaluator_type}.system_addon")
        examples = self.t.t_object(f"lib.evaluation.judge.{evaluator_type}.examples")

        system_message = f"{system_base}\n{system_addon}"

        chat_messages = [ChatMessage.from_str(system_message, role="system")]

        for example in examples:
            chat_messages.append(ChatMessage.from_str(example["user"], role="user"))
            chat_messages.append(ChatMessage.from_str(example["assistant"], role="assistant"))

        chat_messages.append(ChatMessage.from_str(user_input_structure, role="user"))

        return ChatPromptTemplate(message_templates=chat_messages)

    async def _evaluate_with_judge(
        self, prompt_template: ChatPromptTemplate, prompt_vars: dict[str, Any]
    ) -> JudgeOutput:
        """
        Calls the judge LLM with a constructed prompt and parses the structured output.
        Uses LlamaIndex's structured prediction with tool calls to enforce the JudgeOutput schema.
        """
        llm, _ = self.judge.to_llama_index()
        return await llm.astructured_predict(
            output_cls=JudgeOutput, prompt=prompt_template, llm_kwargs=self.llm_judge_kwargs, **prompt_vars
        )

    async def _run_single_evaluation(
        self, evaluator_type: str, task_output: dict[str, Any], **kwargs: Any
    ) -> Evaluation:
        """
        Generic function to run a single evaluation type (Correctness, Completeness, etc.).
        Returns a Langfuse Evaluation object.
        """
        agent_response = task_output.get("agent_response", "")

        prompt_vars = {"agent_response": agent_response, **kwargs}
        user_structure_template = self.t(f"lib.evaluation.judge.{evaluator_type}.user_structure")
        user_input_structure = PromptTemplate(user_structure_template).format(**prompt_vars)

        prompt_template = self._build_judge_prompt_template(evaluator_type, user_input_structure)
        judge_output = await self._evaluate_with_judge(prompt_template, prompt_vars)

        return Evaluation(
            name=evaluator_type.capitalize(),
            value=judge_output.score,
            comment=judge_output.reasoning,
        )

    async def run_evaluation_experiment(
        self,
        agent_class: str,
        agent_id: str,
        dataset_id: str,
        experiment_name: str | None = None,
        experiment_description: str | None = None,
        experiment_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Runs a full evaluation experiment using Langfuse.

        It fetches the dataset, sets up the agent interaction task, defines
        evaluators using our LLM judge functions, and runs the
        Langfuse experiment, logging all results.

        Returns a dictionary with the experiment results.
        """
        # Fetch the dataset from Langfuse
        try:
            dataset = self.langfuse_client.get_dataset(dataset_id)
        except Exception as e:
            logger.exception(f"CRITICAL: Failed to load dataset ID '{dataset_id}' from Langfuse: {e}")
            raise ValueError(f"Failed to load dataset ID '{dataset_id}': {e}") from e

        if not dataset or not dataset.items:
            message = f"Dataset ID '{dataset_id}' not found or is empty in Langfuse."
            logger.error(message)
            raise ValueError(message)

        final_experiment_name = experiment_name or (
            f"Eval_{agent_class}_{agent_id}_on_{dataset_id}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
        )

        final_metadata = {
            "agent_class": agent_class,
            "agent_id": agent_id,
            "experiment_name": final_experiment_name,
            "experiment_description": experiment_description,
            "locale": self.t.locale,
            **(experiment_metadata or {}),
        }

        # Define the task function for Langfuse experiment runner
        async def task_for_langfuse(*, item: Any, **kwargs: Any) -> str:
            """Task that runs agent interaction and returns the response."""
            input_data = item.input if hasattr(item, "input") else item.get("input", {})
            result = await self._agent_interaction_task(
                example_input=input_data,
                agent_class=agent_class,
                agent_id=agent_id,
            )
            return result.get("agent_response", "")

        # Define evaluators for Langfuse
        async def correctness_evaluator(
            *, input: Any, output: Any, expected_output: Any, metadata: Any, **kwargs: Any
        ) -> Evaluation:
            """Evaluates correctness and returns a Langfuse Evaluation."""
            input_data = input if isinstance(input, dict) else {}
            expected_data = expected_output if isinstance(expected_output, dict) else {}
            reference_answer = expected_data.get("answer")
            return await self._run_single_evaluation(
                "correctness",
                {"agent_response": output},
                question=input_data.get("question"),
                reference_answer=reference_answer,
            )

        async def completeness_evaluator(
            *, input: Any, output: Any, expected_output: Any, metadata: Any, **kwargs: Any
        ) -> Evaluation:
            """Evaluates completeness and returns a Langfuse Evaluation."""
            input_data = input if isinstance(input, dict) else {}
            return await self._run_single_evaluation(
                "completeness",
                {"agent_response": output},
                question=input_data.get("question"),
            )

        async def conciseness_evaluator(
            *, input: Any, output: Any, expected_output: Any, metadata: Any, **kwargs: Any
        ) -> Evaluation:
            """Evaluates conciseness and returns a Langfuse Evaluation."""
            input_data = input if isinstance(input, dict) else {}
            return await self._run_single_evaluation(
                "conciseness",
                {"agent_response": output},
                question=input_data.get("question"),
            )

        logger.info(f"Starting Langfuse experiment: {final_experiment_name}")

        # Run the experiment using Langfuse's experiment runner
        # Note: run_experiment blocks until completion and stores results in Langfuse
        self.langfuse_client.run_experiment(
            name=final_experiment_name,
            description=experiment_description,
            data=dataset,
            task=task_for_langfuse,
            evaluators=[correctness_evaluator, completeness_evaluator, conciseness_evaluator],
            metadata=final_metadata,
        )

        logger.info(f"Langfuse experiment '{final_experiment_name}' completed.")

        # Return experiment metadata for API response
        return {
            "experiment_id": final_experiment_name,
            "dataset_id": dataset_id,
            "metadata": final_metadata,
        }
