Feature: Expert Asking Agent
  Tests for the ExpertAskingAgent which asks questions to experts via bot channels
  and processes their responses until a sufficient answer is obtained.

  Scenario: Expert provides sufficient answer on first response
    Given an ExpertAskingAgent runner
    When a question is asked and the expert provides a sufficient answer
    Then a BotInTheLoopRequestEvent is present
    And a BotInTheLoopResponseEvent is present
    And an AnswerStopEvent is present with the expert answer

  Scenario: Expert provides insufficient answer then sufficient answer
    Given an ExpertAskingAgent runner
    When a question is asked and the expert first provides an insufficient answer then a sufficient answer
    Then multiple BotInTheLoopRequestEvents are present
    And an AnswerStopEvent is present with the expert answer

  Scenario: Expert provides insufficient answers until max loops reached
    Given an ExpertAskingAgent runner
    When a question is asked and the expert consistently provides insufficient answers
    Then a NoAnswerStopEvent is present
