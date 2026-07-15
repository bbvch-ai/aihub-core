Feature: IMAP Agent

  Scenario: Lists unread mail and fetches the first message with attachments
    Given an ImapAgent runner with a mocked IMAP inbox
    When the user asks to read mail
    Then an UnreadMailListedEvent was emitted
    And a MailFetchedEvent was emitted
    And a StopEvent is present
    And no ExceptionEvent is present

  Scenario: Stops gracefully when the inbox has no unread mail
    Given an ImapAgent runner with an empty IMAP inbox
    When the user asks to read mail
    Then an UnreadMailListedEvent was emitted
    And no MailFetchedEvent was emitted
    And a StopEvent is present
