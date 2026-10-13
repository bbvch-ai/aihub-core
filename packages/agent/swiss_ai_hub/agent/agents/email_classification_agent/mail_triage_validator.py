import logging
from collections.abc import Callable

from swiss_ai_hub.core.imap import (
    DraftEmailSettings,
    EmailClassificationSettings,
)

from swiss_ai_hub.agent.agents.email_classification_agent.configs.knowledge_delegation_config import (
    KnowledgeDelegationConfig,
)
from swiss_ai_hub.agent.imap.draft_prompt_builder import DraftPromptBuilder

logger = logging.getLogger(__name__)


class MailTriageValidator:
    """Rejects a mailbox setup that would file mail wrongly or draft into a loop, before a run spends anything."""

    @staticmethod
    def validate(
        classification: EmailClassificationSettings,
        draft: DraftEmailSettings,
        inbox_folder: str,
        token_counter: Callable[[str], list[int]],
        knowledge_delegation: KnowledgeDelegationConfig | None = None,
    ) -> None:
        """Fail the run rather than silently filing everything into the fallback folder, or drafting into the inbox.

        The drafting checks run here, before the first fetch, even though drafting happens at the very end: a run that
        classified and filed a whole batch at full model cost and only then discovered its drafts folder is
        unusable has wasted all of it.
        """
        MailTriageValidator._validate_taxonomy(classification, inbox_folder)
        MailTriageValidator._validate_drafting(classification, draft, inbox_folder, token_counter)
        MailTriageValidator._validate_grounding(classification, draft, knowledge_delegation)

    @staticmethod
    def _validate_taxonomy(classification: EmailClassificationSettings, inbox_folder: str) -> None:
        """The folders mail is filed into must be distinct from each other and from the inbox."""
        if not classification.categories:
            raise ValueError("no categories are configured — the agent has nothing to classify into")
        if not classification.fallback_folder:
            raise ValueError("fallback_folder is empty — mail the model is unsure about would have nowhere to go")
        if not classification.failure_folder:
            raise ValueError("failure_folder is empty — mail the classifier failed on would have nowhere to go")

        names = [category.category for category in classification.categories]
        folders = [category.imap_folder for category in classification.categories]
        if len(set(names)) != len(names):
            raise ValueError(f"category names must be unique, got {names}")
        if len(set(folders)) != len(folders):
            raise ValueError(f"category folders must be unique, got {folders}")
        if classification.fallback_folder in folders:
            raise ValueError(
                f"fallback_folder {classification.fallback_folder!r} is also a category folder — the run summary "
                "could not tell a categorised message from an uncategorised one"
            )
        if classification.failure_folder in folders:
            raise ValueError(
                f"failure_folder {classification.failure_folder!r} is also a category folder — a message the "
                "classifier never reached a verdict on would be indistinguishable from one it placed there"
            )
        if classification.failure_folder == classification.fallback_folder:
            raise ValueError(
                f"failure_folder {classification.failure_folder!r} equals the fallback folder — an operator could "
                "not tell mail the model deliberately declined from mail it never read, which is the whole reason "
                "the two are kept apart"
            )

        # Filing out of the inbox is the only dedup this agent has, and a target equal to the inbox defeats it.
        # On the COPY + UID EXPUNGE path the original is replaced by a fresh unread copy in the same folder, so the
        # next run classifies the copy, archives it again, and repeats without termination. Folder names are
        # admin-entered free text, so this is reachable by a typo rather than only by misuse.
        if inbox_folder in {*folders, classification.fallback_folder, classification.failure_folder}:
            raise ValueError(
                f"a target folder equals the inbox folder {inbox_folder!r} — filed mail would stay unread in the "
                "inbox and be reprocessed on every run"
            )

    @staticmethod
    def _validate_drafting(
        classification: EmailClassificationSettings,
        draft: DraftEmailSettings,
        inbox_folder: str,
        token_counter: Callable[[str], list[int]],
    ) -> None:
        """Reject a drafting setup that cannot produce a draft, before the run spends anything on classification."""
        if not draft.enable_draft:
            return

        folders = [category.imap_folder for category in classification.categories]

        # Constructing the builder is the check: it is the thing that knows whether the configured budget survives
        # the system prompt, and a budget that cannot is only discovered at drafting time otherwise — after the whole
        # batch has been classified and filed, with the drafts unrecoverable.
        DraftPromptBuilder(draft.number_of_input_tokens, token_counter, draft.draft_prompt)

        if not any(category.draft_reply for category in classification.categories):
            raise ValueError(
                "reply drafting is enabled but no category is set to get a drafted reply — either tick a category or "
                "turn drafting off, rather than paying for a drafting pass that can never produce anything"
            )

        # A draft appended into the inbox arrives unread, so the next run classifies and files the agent's own
        # draft — and drafts a reply to it. Same class of unterminating loop as an inbox-equal target folder above,
        # and reachable the same way, by a typo in a free-text folder name.
        if draft.drafts_folder == inbox_folder:
            raise ValueError(
                f"drafts_folder equals the inbox folder {inbox_folder!r} — every draft would be classified and "
                "replied to on the following run"
            )
        if draft.drafts_folder in {*folders, classification.fallback_folder, classification.failure_folder}:
            raise ValueError(
                f"drafts_folder {draft.drafts_folder!r} is also a category or fallback folder — drafts and filed "
                "mail would be indistinguishable in it"
            )

    @staticmethod
    def _validate_grounding(
        classification: EmailClassificationSettings,
        draft: DraftEmailSettings,
        knowledge_delegation: KnowledgeDelegationConfig | None,
    ) -> None:
        """Reject a grounding setup that cannot produce a grounded draft, before the run spends anything.

        Skipped entirely when drafting is off, mirroring `_validate_drafting`: `ReplyDrafting.drafting_batch` returns
        nothing in that state, so grounding cannot execute and must not be able to fail a run either. Otherwise an
        admin who configured grounding and later paused drafting would have every classification run die on a feature
        that cannot run.
        """
        if not draft.enable_draft:
            return

        # A category that is not drafted never retrieves, and the form hides its selection, so a selection left
        # behind when drafting was switched off is inert and must not fail the run.
        narrowed = [
            category
            for category in classification.categories
            if category.draft_reply and category.knowledge_namespaces is not None
        ]

        if knowledge_delegation is None:
            if narrowed:
                raise ValueError(
                    f"categories {[category.category for category in narrowed]} narrow retrieval to a knowledge "
                    "collection but no knowledge agent is configured — their replies have nothing to retrieve from"
                )
            return

        # Checked here rather than left to the form: a blank fallback would only be discovered by the message that
        # needed it, which is the one message nobody is watching for.
        if not draft.no_information_draft.strip() or not draft.grounding_failed_draft.strip():
            raise ValueError(
                "both fallback draft texts must be set when a knowledge agent is configured — a message retrieval "
                "could not answer must still get a draft, or it stays filed with no draft and is never looked at "
                "again"
            )

        # An enabled selection holding nothing is not the same as no selection: it reads as "answer from knowledge"
        # while naming none, and the delegated run would fall back to the delegate's whole scope.
        empty = [category.category for category in narrowed if not category.knowledge_namespaces]
        if empty:
            raise ValueError(
                f"categories {empty} have their collection selection switched on but name no collection — either "
                "pick the collections their replies are answered from, or switch the selection off to answer them "
                "from every collection the knowledge agent retrieves from"
            )
