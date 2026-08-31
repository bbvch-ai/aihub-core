Feature: IMAP Agent

  Scenario: Lists unread and fetches the first message, then finishes when moving is off
    Given an ImapAgent runner with a mocked IMAP inbox
    When the user triggers reading mail
    Then an UnreadMailListedEvent was emitted
    And a MailFetchedEvent was emitted
    And no MailMovedEvent was emitted
    And a StopEvent is present
    And no ExceptionEvent is present

  Scenario: Moves the fetched message when moving is enabled
    Given an ImapAgent runner with moving enabled and a mocked IMAP inbox
    When the user triggers reading mail
    Then a MailFetchedEvent was emitted
    And a MailMovedEvent that moved the message was emitted
    And a StopEvent is present
    And no ExceptionEvent is present

  Scenario: Creates the target folder when it does not exist yet
    Given an ImapAgent runner with moving enabled and a missing target folder
    When the user triggers reading mail
    Then a MailMovedEvent that records the created folder was emitted
    And a StopEvent is present
    And no ExceptionEvent is present

  Scenario: Stops gracefully when the inbox has no unread mail
    Given an ImapAgent runner with an empty IMAP inbox
    When the user triggers reading mail
    Then an UnreadMailListedEvent was emitted
    And no MailFetchedEvent was emitted
    And a StopEvent is present

  Scenario: Drafts replies for a batch of undrafted messages
    Given an ImapAgent runner with drafting enabled and undrafted mail in the source folder
    When the user triggers drafting
    Then a MailBatchDraftedEvent with 2 drafts was emitted
    And a StopEvent is present
    And no ExceptionEvent is present

  Scenario: Drafts nothing when there are no undrafted messages
    Given an ImapAgent runner with drafting enabled and no undrafted mail
    When the user triggers drafting
    Then a MailBatchDraftedEvent with 0 drafts was emitted
    And a StopEvent is present

  Scenario: Does not draft when drafting is disabled
    Given an ImapAgent runner with drafting disabled
    When the user triggers drafting
    Then no MailBatchDraftedEvent was emitted
    And a StopEvent is present
