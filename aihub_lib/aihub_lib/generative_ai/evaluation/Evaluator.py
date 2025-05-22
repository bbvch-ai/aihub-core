from typing import Annotated
from pydantic import BaseModel, Field

import phoenix as px
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, UTC

from nats.aio.client import Client as NATS
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.prompts import RichPromptTemplate
from phoenix.experiments import run_experiment
from phoenix.experiments.types import Example as PhoenixExample, Dataset as PhoenixDataset, RanExperiment, EvaluationResult as PhoenixEvaluationResult
from phoenix.experiments.evaluators import create_evaluator

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.generative_ai.resources.models.llm.chat.ChatLLMConfig import ChatLLMConfig
from aihub_lib.nats.distributor.ExternalEventDistributor import ExternalEventDistributor
from aihub_lib.routes.chat.ChatService import ChatService, JsonResources, ChatContent # Adjust path

class JudgeOutput(BaseModel):
    score: Annotated[float, Field(description="The evaluation score, typically between 0.0 and 1.0.")]
    reasoning: Annotated[str, Field(description="A brief explanation for the assigned score.")]
    error: Annotated[Optional[bool], Field(description="Flag indicating if the judge encountered an issue evaluating.", default=False)] = False


logger = logging.getLogger(__name__)

class PhoenixExperimentEvaluator:
    """
    Orchestrates evaluations of agents using Arize Phoenix experiments.
    This evaluator defines a task to interact with an agent via ChatService
    and provides custom LLM-based evaluators for correctness, completeness,
    and conciseness using structured outputs and few-shot prompting.
    """

    def __init__(
            self,
            nats_client: NATS,
            external_event_distributor: ExternalEventDistributor,
            judge: ChatLLMConfig,
            authenticated_user: AuthenticatedUser,
    ):
        """
        Initializes the PhoenixExperimentEvaluator.
        The Phoenix client is created internally. ChatService methods are called statically.
        """
        self.phoenix_client = px.Client(warn_if_server_not_running=False)
        self.nats_client = nats_client
        self.external_event_distributor = external_event_distributor
        self.user = authenticated_user
        self.llm_judge_kwargs = {"temperature": 0.0}
        self.judge = judge

    async def _agent_interaction_task(
            self,
            example_input: Dict[str, Any],
            agent_class: str,
            agent_id: str,
    ) -> Dict[str, Any]:
        """
        Task function for Phoenix experiment: sends a question to the agent and returns its response.
        """
        question = example_input.get("question")
        if not question:
            logger.warning(f"Task input missing 'question': {example_input}")
            return {"agent_response": "", "error": "Missing 'question' in input"}

        messages = [
            ChatMessage(role=MessageRole.USER, content=question),
        ]

        try:
            json_resources: JsonResources = await ChatService.start_json_chat_interaction(
                user=self.user,
                agent_class=agent_class,
                agent_id=agent_id,
                messages=messages,
                nc=self.nats_client,
                external_event_distributor=self.external_event_distributor,
            )
            await json_resources.stop_signal.wait()

            if json_resources.stop_event and json_resources.stop_event.is_exception_event:
                logger.error(f"Agent interaction error for question '{question}': {json_resources.stop_event.message}")
                return {"agent_response": "", "error": json_resources.stop_event.message}

            chat_content: ChatContent = ChatService.build_json_response_content(
                json_resources.chunk_events, json_resources.stop_event
            )
            return {"agent_response": chat_content.content}
        except Exception as e:
            logger.exception(f"Task exception for question '{question}': {e}")
            return {"agent_response": "", "error": str(e)}

    def _create_judge_prompt_template(self, system_message: str, few_shot_examples: List[Dict[str, str]], user_inputstructure: str) -> RichPromptTemplate:
        """
        Helper to create a RichPromptTemplate for the LLM judge with few-shot examples.
        """
        template_str = f"""{{% chat role="system" %}}
{system_message}
You MUST output your evaluation as a JSON object matching the specified Pydantic model: {{{{output_schema}}}}.
{{% endchat %}}"""

        for example in few_shot_examples:
            template_str += f"""
{{% chat role="user" %}}
{example['user']}
{{% endchat %}}
{{% chat role="assistant" %}}
{example['assistant']}
{{% endchat %}}"""

        template_str += f"""
{{% chat role="user" %}}
{user_inputstructure}
{{% endchat %}}"""
        return RichPromptTemplate(template_str)


    async def _evaluate_with_judge(
            self,
            prompt_template: RichPromptTemplate,
            prompt_vars: Dict[str, Any]
    ) -> JudgeOutput:
        """
        Helper method to call the judge LLM with a RichPromptTemplate and structured output.
        """
        llm, _ = self.judge.to_llama_index()
        return await llm.astructured_predict(
            output_cls=JudgeOutput,
            prompt=prompt_template,
            llm_kwargs=self.llm_judge_kwargs,
            **prompt_vars
        )


    async def _correctness_evaluator_func(
            self, task_output: Dict[str, Any], reference: Dict[str, Any], inputdata: Dict[str, Any]
    ) -> PhoenixEvaluationResult: # Return type changed
        """
        Evaluates correctness and returns a PhoenixEvaluationResult.
        """
        agent_response = task_output.get("agent_response", "")
        reference_answer = reference.get("answer")
        question = inputdata.get("question")

        if reference_answer is None:
            return PhoenixEvaluationResult(label="error", explanation="Reference answer missing in dataset.", metadata={"error_flag": True})
        if not agent_response and task_output.get("error"):
            return PhoenixEvaluationResult(label="error", explanation=f"Agent failed to respond: {task_output.get('error')}", metadata={"error_flag": True})

        system_message = "You are an impartial judge. Evaluate the AGENT_RESPONSE for its correctness based on the REFERENCE_ANSWER to the given QUESTION. A correct response accurately addresses the question and aligns with the reference answer."
        few_shot_examples = [
            {"user": "<inputDATA>\n<QUESTION>What is the capital of France?</QUESTION>\n<REFERENCE_ANSWER>Paris</REFERENCE_ANSWER>\n<AGENT_RESPONSE>The capital of France is Paris.</AGENT_RESPONSE>\n</inputDATA>",
             "assistant": '{"score": 1.0, "reasoning": "The agent correctly identified Paris as the capital of France, matching the reference answer.", "error": false}'},
            {"user": "<inputDATA>\n<QUESTION>What is 2+2?</QUESTION>\n<REFERENCE_ANSWER>4</REFERENCE_ANSWER>\n<AGENT_RESPONSE>It is five.</AGENT_RESPONSE>\n</inputDATA>",
             "assistant": '{"score": 0.0, "reasoning": "The agent provided an incorrect answer. The reference answer is 4, but the agent said 5.", "error": false}'}
        ]
        user_inputstructure = f"<inputDATA>\n<QUESTION>{question}</QUESTION>\n<REFERENCE_ANSWER>{reference_answer}</REFERENCE_ANSWER>\n<AGENT_RESPONSE>{agent_response}</AGENT_RESPONSE>\n</inputDATA>"
        prompt_template = self._create_judge_prompt_template(system_message, few_shot_examples, user_inputstructure)
        prompt_vars = {"question": question, "reference_answer": reference_answer, "agent_response": agent_response}

        judge_output_model = await self._evaluate_with_judge(prompt_template, prompt_vars)

        return PhoenixEvaluationResult(
            score=judge_output_model.score,
            explanation=judge_output_model.reasoning,
            # Optionally derive a label or include full judge output in metadata
            # label="pass" if judge_output_model.score >= 0.7 else "fail", # Example label
            metadata={"judge_had_error": judge_output_model.error}
        )

    async def _completeness_evaluator_func(
            self, task_output: Dict[str, Any], inputdata: Dict[str, Any]
    ) -> PhoenixEvaluationResult: # Return type changed
        """
        Evaluates completeness and returns a PhoenixEvaluationResult.
        """
        agent_response = task_output.get("agent_response", "")
        question = inputdata.get("question")

        if not agent_response and task_output.get("error"):
            return PhoenixEvaluationResult(label="error", explanation=f"Agent failed to respond: {task_output.get('error')}", metadata={"error_flag": True})

        system_message = "You are an impartial judge. Evaluate if the AGENT_RESPONSE fully addresses all aspects of the QUESTION, both explicit and implicit parts."
        few_shot_examples = [
            {"user": "<inputDATA>\n<QUESTION>Tell me about the benefits and drawbacks of solar power.</QUESTION>\n<AGENT_RESPONSE>Solar power is great because it's renewable and reduces carbon emissions.</AGENT_RESPONSE>\n</inputDATA>",
             "assistant": '{"score": 0.5, "reasoning": "The agent mentioned benefits but did not cover any drawbacks, so the answer is incomplete.", "error": false}'},
            {"user": "<inputDATA>\n<QUESTION>What is photosynthesis?</QUESTION>\n<AGENT_RESPONSE>Photosynthesis is the process used by plants, algae and certain bacteria to harness energy from sunlight and turn it into chemical energy.</AGENT_RESPONSE>\n</inputDATA>",
             "assistant": '{"score": 1.0, "reasoning": "The agent provided a concise and accurate definition covering the main aspects of photosynthesis.", "error": false}'}
        ]
        user_inputstructure = f"<inputDATA>\n<QUESTION>{question}</QUESTION>\n<AGENT_RESPONSE>{agent_response}</AGENT_RESPONSE>\n</inputDATA>"
        prompt_template = self._create_judge_prompt_template(system_message, few_shot_examples, user_inputstructure)
        prompt_vars = {"question": question, "agent_response": agent_response}

        judge_output_model = await self._evaluate_with_judge(prompt_template, prompt_vars)

        return PhoenixEvaluationResult(
            score=judge_output_model.score,
            explanation=judge_output_model.reasoning,
            metadata={"judge_had_error": judge_output_model.error}
        )

    async def _conciseness_evaluator_func(
            self, task_output: Dict[str, Any], inputdata: Dict[str, Any]
    ) -> PhoenixEvaluationResult: # Return type changed
        """
        Evaluates conciseness and returns a PhoenixEvaluationResult.
        """
        agent_response = task_output.get("agent_response", "")
        question = inputdata.get("question")

        if not agent_response and task_output.get("error"):
            return PhoenixEvaluationResult(label="error", explanation=f"Agent failed to respond: {task_output.get('error')}", metadata={"error_flag": True})

        system_message = "You are an impartial judge. Evaluate if the AGENT_RESPONSE is concise and to the point, avoiding unnecessary verbosity or irrelevant details for the given QUESTION."
        few_shot_examples = [
            {"user": "<inputDATA>\n<QUESTION>What time is it?</QUESTION>\n<AGENT_RESPONSE>It is currently 3:00 PM. By the way, the weather today is sunny and I also had a great lunch. Did you know that time is a fascinating concept studied in physics?</AGENT_RESPONSE>\n</inputDATA>",
             "assistant": '{"score": 0.2, "reasoning": "The agent answered the question but included a lot of irrelevant information, making it not concise.", "error": false}'},
            {"user": "<inputDATA>\n<QUESTION>Is Paris the capital of France?</QUESTION>\n<AGENT_RESPONSE>Yes.</AGENT_RESPONSE>\n</inputDATA>",
             "assistant": '{"score": 1.0, "reasoning": "The agent provided a direct and concise answer.", "error": false}'}
        ]
        user_inputstructure = f"<inputDATA>\n<QUESTION>{question}</QUESTION>\n<AGENT_RESPONSE>{agent_response}</AGENT_RESPONSE>\n</inputDATA>"
        prompt_template = self._create_judge_prompt_template(system_message, few_shot_examples, user_inputstructure)
        prompt_vars = {"question": question, "agent_response": agent_response}

        judge_output_model = await self._evaluate_with_judge(prompt_template, prompt_vars)

        return PhoenixEvaluationResult(
            score=judge_output_model.score,
            explanation=judge_output_model.reasoning,
            metadata={"judge_had_error": judge_output_model.error}
        )


    async def run_evaluation_experiment(
            self,
            agent_class: str,
            agent_id: str,
            dataset_id: str,
            experiment_name: Optional[str] = None,
            experiment_description: Optional[str] = None,
            experiment_metadata: Optional[Dict[str, Any]] = None,
    ) -> RanExperiment:
        """
        Runs a full evaluation experiment using Arize Phoenix.
        """
        try:
            dataset: PhoenixDataset = self.phoenix_client.get_dataset(id=dataset_id)
        except Exception as e:
            logger.exception(f"Failed to load dataset with ID '{dataset_id}' from Phoenix: {e}")
            raise

        if not dataset or not dataset.examples:
            message = f"Dataset ID '{dataset_id}' not found or is empty in Phoenix."
            logger.error(message)
            raise ValueError(message)

        async def task_for_phoenix(example: PhoenixExample) -> Dict[str, Any]:
            return await self._agent_interaction_task(
                example_input=example.input,
                agent_class=agent_class,
                agent_id=agent_id,
            )

        @create_evaluator(name="Correctness", kind="LLM")
        async def correctness_phoenix_eval(output: Dict[str, Any], reference: Dict[str, Any], input: Dict[str, Any]) -> PhoenixEvaluationResult:
            return await self._correctness_evaluator_func(task_output=output, reference=reference, inputdata=input)

        @create_evaluator(name="Completeness", kind="LLM")
        async def completeness_phoenix_eval(output: Dict[str, Any], input: Dict[str, Any]) -> PhoenixEvaluationResult:
            return await self._completeness_evaluator_func(task_output=output, inputdata=input)

        @create_evaluator(name="Conciseness", kind="LLM")
        async def conciseness_phoenix_eval(output: Dict[str, Any], input: Dict[str, Any]) -> PhoenixEvaluationResult:
            return await self._conciseness_evaluator_func(task_output=output, inputdata=input)

        evaluators_list = [
            correctness_phoenix_eval,
            completeness_phoenix_eval,
            conciseness_phoenix_eval,
        ]

        final_experiment_name = experiment_name
        if not final_experiment_name:
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            final_experiment_name = f"Eval_{agent_class}_{agent_id}_on_Dataset_{dataset_id}_{timestamp}"

        logger.info(f"Starting Phoenix experiment: {final_experiment_name}")
        experiment_result: RanExperiment = run_experiment(
            dataset=dataset,
            task=task_for_phoenix,
            evaluators=evaluators_list,
            experiment_name=final_experiment_name,
            experiment_description=experiment_description,
            experiment_metadata={
                "agent_class": agent_class,
                "agent_id": agent_id,
                "experiment_name": experiment_name,
                "experiment_description": experiment_description,
                **(experiment_metadata or {}),
            }
        )
        logger.info(f"Phoenix experiment '{final_experiment_name}' completed. View at: {experiment_result.url if hasattr(experiment_result, 'url') else 'URL not available'}")

        return experiment_result