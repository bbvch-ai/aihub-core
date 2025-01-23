async def explain_guard_reject_prompt(
        llm: LLM,
        t: LocaleHandler,
        user_query: str,
        guardResult: GuardResult,
) -> string:
    prompt = PromptTemplate(t("lib.guards.agent_description_guard"))
    history = "".join(
        [
            (
                PromptTemplate(t("lib.guards.agent_description_guard.user_message")).format(user=message.content)
                if message.role == MessageRole.USER
                else PromptTemplate(t("lib.guards.agent_description_guard.agent_message")).format(agent=message.content)
            )
            for message in messages
        ]
    )

    result = await llm.structured_predict(
        guard_result_factory(t),
        prompt,
        agent_description=agent_description.in_locale(t.locale),
        user_query=user_query,
        history=history,
    )

    guard_result_class = guard_result_factory(t)
    return guard_result_class.model_validate(result)
