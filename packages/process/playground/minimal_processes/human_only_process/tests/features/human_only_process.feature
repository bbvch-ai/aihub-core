Feature: Human Only Process
  Test for HumanOnlyProcess interacting with HumanA and HumanB

  Scenario: Test HumanOnlyProcess workflow
    Given a HumanOnlyProcessRunner runner
    When HumanA sends work with payload "HumanA data" and HumanB responds with payload "HumanB data"
    Then HumanOnlyProcessRunner produces a CustomProcessStopEvent with payload "Please respond to <HumanA data> with a single word: -> HumanB data -> HumanOnlyProcess output"