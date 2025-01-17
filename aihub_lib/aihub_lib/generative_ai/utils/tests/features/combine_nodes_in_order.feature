Feature: Combine nodes in order

  Scenario: Combine nodes with default context prompt
    Given a locale handler
    And no context prompt
    And the following context nodes:
      | source | section_start_line | text                | score |
      | doc1   | 10                 | Doc1 line10 content | 0.9   |
      | doc1   | 20                 | Doc1 line20 content | 0.8   |
      | doc2   | 15                 | Doc2 line15 content | 0.95  |
    When the combine_nodes_in_order function is called
    Then it should return:
      """
      Default prompt: <DOC START: doc1>

      Doc1 line10 content

      Doc1 line20 content

      <DOC END: doc1>

      ---
      <DOC START: doc2>

      Doc2 line15 content

      <DOC END: doc2>

      ---
      """

  Scenario: Combine nodes with a custom context prompt
    Given a locale handler
    And a custom context prompt
    And the following context nodes:
      | source | section_start_line | text                 | score |
      | docA   | 5                  | Node docA line=5     | 1.0   |
      | docA   | 10                 | Node docA line=10    | 1.0   |
    When the combine_nodes_in_order function is called
    Then it should return:
      """
      Custom prompt: <DOC START: docA>

      Node docA line=5

      Node docA line=10

      <DOC END: docA>

      ---
      """

  Scenario: Missing source in metadata
    Given a locale handler
    And no context prompt
    And the following context nodes:
      | source | section_start_line | text                    | score |
      |        | 0                  | Document missing source | 0.7   |
    When the combine_nodes_in_order function is called
    Then a ValueError is raised

  Scenario: Multiple docs but empty final text
    Given a locale handler
    And no context prompt
    And no context nodes
    When the combine_nodes_in_order function is called
    Then it should return:
      """
      Default prompt:
      """

  Scenario: Another custom scenario with multiple sources
    Given a locale handler
    And no context prompt
    And the following context nodes:
      | source | section_start_line | text               | score |
      | docX   | 2                  | docX line=2        | 0.8   |
      | docX   | 1                  | docX line=1        | 0.7   |
      | docY   | 5                  | docY line=5        | 0.9   |
    When the combine_nodes_in_order function is called
    Then it should return:
      """
      Default prompt: <DOC START: docX>

      docX line=1

      docX line=2

      <DOC END: docX>

      ---
      <DOC START: docY>

      docY line=5

      <DOC END: docY>

      ---
      """
