Feature: Email Classification Agent

  Scenario: Files every unread message into the folder for its category
    Given an EmailClassificationAgent runner with three unread messages the model classifies into categories
    When the user triggers classification
    Then a MailBatchClassifiedEvent with 3 classified messages was emitted
    And each message was filed into its category folder
    And the whole batch shares one folder check
    And the summary counts 2 support_request and 1 invoice
    And a StopEvent is present
    And no ExceptionEvent is present

  Scenario: Files mail no category fits into the fallback folder
    Given an EmailClassificationAgent runner with one unread message no category fits
    When the user triggers classification
    Then a MailBatchClassifiedEvent with 1 classified messages was emitted
    And the message was filed into the fallback folder
    And the summary counts 1 message in the fallback folder
    And no ExceptionEvent is present

  Scenario: Reports a run over an empty inbox without filing anything
    Given an EmailClassificationAgent runner with an empty inbox
    When the user triggers classification
    Then a MailBatchClassifiedEvent with 0 classified messages was emitted
    And no message was filed
    And a StopEvent is present
    And no ExceptionEvent is present

  Scenario: Records the category folder it had to create
    Given an EmailClassificationAgent runner whose category folder does not exist yet
    When the user triggers classification
    Then the created folder is recorded on the classification
    And no ExceptionEvent is present

  Scenario: Archives the original message and its attachments
    Given an EmailClassificationAgent runner with three unread messages the model classifies into categories
    When the user triggers classification
    Then every classified message references its archived original and attachments

  Scenario: Never sends mail
    Given an EmailClassificationAgent runner with three unread messages the model classifies into categories
    When the user triggers classification
    Then no draft was appended and nothing was sent

  Scenario: Drafts a reply only for the categories that asked for one
    Given an EmailClassificationAgent runner where support_request is set to get a drafted reply
    When the user triggers classification
    Then a MailBatchClassifiedEvent with 3 classified messages was emitted
    And a MailBatchDraftedEvent with 2 drafts was emitted
    And only the support_request mail was drafted
    And each draft is threaded to the message it replies to
    And every appended draft carries the Draft flag and no message was sent
    And a StopEvent is present
    And no ExceptionEvent is present

  Scenario: Mail that fits no category is never drafted
    Given an EmailClassificationAgent runner where drafting is on but the mail fits no category
    When the user triggers classification
    Then the message was filed into the fallback folder
    And no draft was appended
    And a MailBatchDraftedEvent reporting 0 drafts and 1 skipped was emitted
    And a StopEvent is present
    And no ExceptionEvent is present

  Scenario: Drafting turned off stops the run right after filing
    Given an EmailClassificationAgent runner with reply drafting turned off
    When the user triggers classification
    Then a MailBatchClassifiedEvent with 1 classified messages was emitted
    And no draft was appended
    And a MailBatchDraftedEvent reporting 0 drafts and 1 skipped was emitted
    And a StopEvent is present
    And the mailbox is no longer held
    And no ExceptionEvent is present

  Scenario: Attachment text grounds the drafted reply
    Given an EmailClassificationAgent runner drafting with attachment reading on
    When the user triggers classification
    Then a MailBatchDraftedEvent with 1 drafts was emitted
    And the attachment text reached the drafting prompt
    And no ExceptionEvent is present

  Scenario: An attachment holding no text is named rather than dropped
    Given an EmailClassificationAgent runner drafting a message whose attachment holds no text
    When the user triggers classification
    Then a MailBatchDraftedEvent with 1 drafts was emitted
    And the attachment is named as holding no text and no empty text block was sent
    And no ExceptionEvent is present

  Scenario: A signature logo is not worth a document-parser round trip
    Given an EmailClassificationAgent runner drafting a message carrying only a signature logo
    When the user triggers classification
    Then a MailBatchDraftedEvent with 1 drafts was emitted
    And the signature logo was never fetched
    And no ExceptionEvent is present

  Scenario: A scheduled run drafts exactly like a manual one
    Given an EmailClassificationAgent runner where support_request is set to get a drafted reply
    When the scheduler triggers classification
    Then a MailBatchDraftedEvent with 2 drafts was emitted
    And only the support_request mail was drafted
    And a StopEvent is present
    And the mailbox is no longer held
    And no ExceptionEvent is present

  Scenario: Fails the run when no categories are configured
    Given an EmailClassificationAgent runner with no categories configured
    When the user triggers classification
    Then an ExceptionEvent is present
    And no message was filed

  Scenario: A scheduled run classifies and files exactly like a manual one
    Given an EmailClassificationAgent runner with three unread messages the model classifies into categories
    When the scheduler triggers classification
    Then a MailBatchClassifiedEvent with 3 classified messages was emitted
    And each message was filed into its category folder
    And the summary counts 2 support_request and 1 invoice
    And a StopEvent is present
    And no ExceptionEvent is present

  Scenario: A run starting while another still holds the mailbox files nothing
    Given an EmailClassificationAgent runner whose mailbox is already held by a running classification
    When the scheduler triggers classification
    Then no message was listed, fetched or filed
    And no MailBatchClassifiedEvent was emitted
    And a StopEvent is present
    And no ExceptionEvent is present

  Scenario: A finished run hands the mailbox back
    Given an EmailClassificationAgent runner with three unread messages the model classifies into categories
    When the scheduler triggers classification
    Then the mailbox is no longer held

  Scenario: A grounded category is answered from its own knowledge collection
    Given an EmailClassificationAgent runner grounding support_request in the support collection
    When the user triggers classification and the knowledge agent answers
    Then a MailBatchDraftedEvent with 1 drafts was emitted
    And the draft body is the answer the knowledge agent returned
    And retrieval was scoped to the support collection and no other
    And a StopEvent is present
    And no ExceptionEvent is present

  Scenario: Several messages each get their own grounded draft
    Given an EmailClassificationAgent runner grounding three support_request messages
    When the user triggers classification and the knowledge agent answers each message differently
    Then a MailBatchDraftedEvent with 3 drafts was emitted
    And every draft carries the answer that belongs to its own message
    And no ExceptionEvent is present

  Scenario: Retrieval that finds nothing still produces a draft
    Given an EmailClassificationAgent runner grounding support_request in the support collection
    When the user triggers classification and the knowledge agent finds nothing
    Then a MailBatchDraftedEvent with 1 drafts was emitted
    And the draft body is the configured no-information text
    And no ExceptionEvent is present

  Scenario: A knowledge lookup that failed still produces a draft
    Given an EmailClassificationAgent runner grounding support_request in the support collection
    When the user triggers classification and the knowledge lookup fails
    Then a MailBatchDraftedEvent with 1 drafts was emitted
    And the draft body is the configured lookup-failed text
    And no ExceptionEvent is present

  Scenario: Grounded and ungrounded categories converge on one drafting pass
    Given an EmailClassificationAgent runner grounding support_request but not invoice
    When the user triggers classification and the knowledge agent answers
    Then a MailBatchDraftedEvent with 2 drafts was emitted
    And only the support_request draft came from the knowledge agent
    And no ExceptionEvent is present

  Scenario: A scheduled run delegates without an initiating user
    Given an EmailClassificationAgent runner grounding support_request in the support collection
    When the scheduler triggers classification and the knowledge agent answers
    Then a MailBatchDraftedEvent with 1 drafts was emitted
    And the delegated run carried no user
    And no ExceptionEvent is present

  Scenario: A category grounded in a collection nothing holds fails before the batch is classified
    Given an EmailClassificationAgent runner grounding support_request in a collection that does not exist
    When the user triggers classification
    Then an ExceptionEvent is present
    And no message was filed

  Scenario: Grounding left configured with drafting paused does not fail the run
    Given an EmailClassificationAgent runner grounding support_request with drafting turned off
    When the user triggers classification
    Then a MailBatchClassifiedEvent with 1 classified messages was emitted
    And the knowledge catalogue was never consulted
    And a StopEvent is present
    And no ExceptionEvent is present
