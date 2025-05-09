Feature: Token Budget Manager
  In order to allocate context tokens efficiently,
  As a RAG system developer,
  I want to manage token budgets for different types of nodes.

  Background:
    Given a token budget with:
      | max_tokens        | 1000 |
      | summary_allocation | 0.25 |
      | content_allocation | 0.65 |
      | parent_allocation  | 0.10 |
    And these nodes:
      | id      | text                                                    | token_count | type    |
      | sum1    | "This is a summary node with an estimated 30 tokens"    | 30          | summary |
      | sum2    | "This is another summary node with 40 tokens"           | 40          | summary |
      | content1| "This is a content node with about 50 tokens"           | 50          | content |
      | content2| "This is a larger content node with about 200 tokens"   | 200         | content |
      | parent1 | "This is a parent node with about 25 tokens"            | 25          | parent  |
      | parent2 | "This is another parent node with 30 tokens"            | 30          | parent  |
      | large   | "This is a very large node that exceeds all budgets"    | 1000        | content |

  Scenario: Add Nodes Within Budgets
    When I add "sum1" as a summary node
    And I add "content1" as a content node
    And I add "parent1" as a parent node
    Then all nodes should be accepted
    And the budget usage stats should be:
      | summary_tokens | 30  |
      | content_tokens | 50  |
      | parent_tokens  | 25  |
      | total_tokens   | 105 |

  Scenario: Exceeding Summary Budget
    When I add "sum1" as a summary node
    And I add "sum2" as a summary node
    And I add "sum1" again as a summary node
    And I add a large summary node of 300 tokens
    Then 2 nodes should be accepted
    And the budget usage stats should include:
      | summary_tokens | 70  |
      | summary_budget | 250 |
    And the selected nodes should contain:
      | node_id |
      | sum1    |
      | sum2    |

  Scenario: Exceeding Content Budget
    When I add "content1" as a content node
    And I add "content2" as a content node
    And I add "large" as a content node
    Then 2 nodes should be accepted
    And the budget usage stats should include:
      | content_tokens | 250 |
      | content_budget | 650 |
    And the selected nodes should contain:
      | node_id   |
      | content1  |
      | content2  |

  Scenario: Exceeding Parent Budget
    When I add "parent1" as a parent node
    And I add "parent2" as a parent node
    And I add a large parent node of 150 tokens
    Then 2 nodes should be accepted
    And the budget usage stats should include:
      | parent_tokens | 55  |
      | parent_budget | 100 |
    And the selected nodes should contain:
      | node_id  |
      | parent1  |
      | parent2  |

  Scenario: Duplicate Node IDs Are Rejected
    When I add "sum1" as a summary node
    And I add "sum1" as a content node
    Then 1 node should be accepted
    And the budget usage stats should include:
      | summary_tokens | 30 |
      | content_tokens | 0  |
    And the selected nodes should contain:
      | node_id |
      | sum1    |

  Scenario: Budget Utilization Calculation
    When I add "sum1" as a summary node
    And I add "content1" as a content node
    And I add "parent1" as a parent node
    Then the budget utilization should be:
      | summary | 0.12 |
      | content | 0.077 |
      | parent  | 0.25 |

  Scenario: Custom Budget Allocation
    Given a token budget with:
      | max_tokens        | 2000 |
      | summary_allocation | 0.5  |
      | content_allocation | 0.3  |
      | parent_allocation  | 0.2  |
    When I add "sum1" as a summary node
    And I add "content1" as a content node
    And I add "parent1" as a parent node
    Then the budget usage stats should include:
      | summary_budget | 1000 |
      | content_budget | 600  |
      | parent_budget  | 400  |
    And the budget utilization should be:
      | summary | 0.03  |
      | content | 0.083 |
      | parent  | 0.063 |