from typing import ClassVar

from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import UserMessageEvent
from swiss_ai_hub.core.generative_ai import limit_chat_history
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.jira import JiraError, JiraJql, JiraTicketSearch

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.agents.release_notes_agent.changelog_stream import ChangelogStream
from swiss_ai_hub.agent.agents.release_notes_agent.events.release_notes_written_event import ReleaseNotesWrittenEvent
from swiss_ai_hub.agent.agents.release_notes_agent.events.version_resolved_event import VersionResolvedEvent
from swiss_ai_hub.agent.agents.release_notes_agent.release_note_translator import ReleaseNoteTranslator
from swiss_ai_hub.agent.agents.release_notes_agent.release_note_writer import ReleaseNoteWriter
from swiss_ai_hub.agent.agents.release_notes_agent.release_notes_agent_config import ReleaseNotesAgentConfig
from swiss_ai_hub.agent.agents.release_notes_agent.release_notes_reply import ReleaseNotesReply
from swiss_ai_hub.agent.agents.release_notes_agent.release_version_matcher import ReleaseVersionMatcher
from swiss_ai_hub.agent.agents.release_notes_agent.version_match_outcome import VersionMatchOutcome
from swiss_ai_hub.agent.agents.release_notes_agent.version_match_reply import VersionMatchReply
from swiss_ai_hub.agent.capabilities.conversation.conversation import Conversation
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.workflow.decorators.step import step

_KEY = "agent.release_notes_agent"


class ReleaseNotesAgent(Agent):
    """Writes the release notes of a Jira fix version: a changelog by section, then the same in each further language.

    The model writes only a note per ticket, a batch at a time; the changelog around the notes is built here, so a
    release of hundreds of tickets fits models that answer at most a few thousand tokens. Tickets never travel on an
    event: they are read and written up in one step, and only the notes are handed on to be translated.
    """

    name: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path(f"{_KEY}.metadata.name")
    description: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path(f"{_KEY}.metadata.description")
    icon: ClassVar[str] = "mdi:text-box-check-outline"

    @step(
        name=AgentLocaleString.from_i18n_path(f"{_KEY}.steps.contextualize.name"),
        description=AgentLocaleString.from_i18n_path(f"{_KEY}.steps.contextualize.description"),
        icon="mage:edit",
    )
    async def contextualize_step(
        self, event: UserMessageEvent, config: ReleaseNotesAgentConfig
    ) -> Conversation.ContextualizeRequest:
        """Earlier changelogs fill the history fast, and only the questions in it matter for this turn."""
        history = limit_chat_history(chat_history=event.messages, number_of_input_tokens=config.input_budget())
        return Conversation.contextualize(history=history, message=event)

    @step(
        name=AgentLocaleString.from_i18n_path(f"{_KEY}.steps.resolve_version.name"),
        description=AgentLocaleString.from_i18n_path(f"{_KEY}.steps.resolve_version.description"),
        icon="mdi:tag-search-outline",
    )
    async def resolve_version_step(
        self,
        ctx: Conversation.Contextualized,
        config: ReleaseNotesAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> VersionResolvedEvent | Conversation.CompleteRequest:
        """The release is one of the projects' own version names, so a name Jira does not have is answered with the
        ones it does, before any ticket is read."""
        speaker = ReleaseNotesAgent.__name__
        try:
            versions = await JiraTicketSearch.find_versions(config.jira, config.projects())
        except JiraError as failure:
            return await ReleaseNotesReply.jira_failure(failure, ctx.query, displayer, t, speaker)
        match = ReleaseVersionMatcher.match(ctx.query, versions)
        if match.outcome is not VersionMatchOutcome.FOUND:
            reply = VersionMatchReply.message(match, config.projects(), t)
            return await ReleaseNotesReply.say(reply, ctx.query, displayer, speaker)
        projects = ", ".join(version.project for version in match.versions)
        await displayer.display_thought(t(f"{_KEY}.thoughts.version_found", version=match.name, projects=projects))
        return VersionResolvedEvent(versions=match.versions)

    @step(
        name=AgentLocaleString.from_i18n_path(f"{_KEY}.steps.write_release_notes.name"),
        description=AgentLocaleString.from_i18n_path(f"{_KEY}.steps.write_release_notes.description"),
        icon="mdi:text-box-edit-outline",
    )
    async def write_release_notes_step(
        self,
        resolved: VersionResolvedEvent,
        ctx: Conversation.Contextualized,
        config: ReleaseNotesAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> ReleaseNotesWrittenEvent | Conversation.CompleteRequest:
        """The title is shown as soon as the tickets are read, and each batch of notes as soon as it is written, so the
        chat never waits for the whole release."""
        speaker = ReleaseNotesAgent.__name__
        clauses = [config.extra_jql, JiraJql.fix_version_clause(resolved.versions)]
        try:
            tickets = await JiraTicketSearch.find_tickets(config.capped_jira(), config.projects(), clauses)
        except JiraError as failure:
            return await ReleaseNotesReply.jira_failure(failure, ctx.query, displayer, t, speaker)
        if not tickets:
            reply = t(f"{_KEY}.messages.no_tickets", version=resolved.name, projects=", ".join(config.projects()))
            return await ReleaseNotesReply.say(reply, ctx.query, displayer, speaker)
        await displayer.display_thought(t(f"{_KEY}.thoughts.tickets_found", count=len(tickets), version=resolved.name))
        stream = ChangelogStream(displayer, t, config.show_ticket_keys, config.llm.model_name)
        await stream.begin(config.writing_language(), resolved.name)
        async with config.llm.cost_reporting_llm(displayer, user=user) as llm:
            writer = ReleaseNoteWriter(
                llm,
                config.writing_language(),
                config.audience,
                config.tickets_per_batch,
                config.max_concurrent_calls,
                config.max_description_chars,
            )
            notes = await writer.write(tickets, stream.add)
        summarized = sum(note.fallback for note in notes)
        if summarized:
            await displayer.display_thought(t(f"{_KEY}.thoughts.notes_summarized", count=summarized, total=len(notes)))
        return ReleaseNotesWrittenEvent(version=resolved.name, notes=notes, shown=stream.text)

    @step(
        name=AgentLocaleString.from_i18n_path(f"{_KEY}.steps.translate_release_notes.name"),
        description=AgentLocaleString.from_i18n_path(f"{_KEY}.steps.translate_release_notes.description"),
        icon="mdi:translate",
    )
    async def translate_release_notes_step(
        self,
        written: ReleaseNotesWrittenEvent,
        ctx: Conversation.Contextualized,
        config: ReleaseNotesAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> Conversation.CompleteRequest:
        """Each further language follows as a block of its own; with none configured the run ends on the changelog
        as written."""
        stream = ChangelogStream(displayer, t, config.show_ticket_keys, config.llm.model_name, shown=written.shown)
        targets = config.translation_targets()
        if targets:
            async with config.llm.cost_reporting_llm(displayer, user=user) as llm:
                translator = ReleaseNoteTranslator(
                    llm,
                    config.writing_language(),
                    config.audience,
                    config.tickets_per_batch,
                    config.max_concurrent_calls,
                )
                for language in targets:
                    await stream.begin(language, written.version)
                    translated = await translator.translate(written.notes, language, stream.add)
                    kept = sum(
                        after.fallback and not before.fallback
                        for after, before in zip(translated, written.notes, strict=True)
                    )
                    if kept:
                        thought = t(f"{_KEY}.thoughts.notes_untranslated", count=kept, language=language.endonym)
                        await displayer.display_thought(thought)
        return ReleaseNotesReply.complete(ctx.query, stream.text, config.llm.model_name, answered=written.shown)
