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

  Scenario: Fails the run when no categories are configured
    Given an EmailClassificationAgent runner with no categories configured
    When the user triggers classification
    Then an ExceptionEvent is present
    And no message was filed
