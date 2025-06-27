Feature: Parent Summary Node Retrieval
  In order to enhance retrieval with contextual summary information,
  As a user of the ParentSummaryPostProcessor,
  I want to fetch parent summary nodes based on hierarchical relationships.

  Background:
    Given these nodes:
      | id      | text                   | type    |
      | node1   | "Content of node1"     | content |
      | node2   | "Content of node2"     | content |
      | summary1| "Summary for node1"    | summary |
      | summary2| "Parent summary"       | summary |
    And the following parent relationships:
      | node_id | parent_id |
      | node1   | summary1  |
      | summary1| summary2  |
    And a valid vector store with all nodes

  Scenario: Retrieve Direct Parent Summary
    Given starting nodes are:
      | node_id |
      | node1   |
    When I postprocess nodes using the ParentSummaryPostProcessor with max_levels set to 1
    Then the resulting nodes should include:
      | node_id  |
      | node1    |
      | summary1 |

  Scenario: Retrieve Multiple Levels of Parent Summaries
    Given starting nodes are:
      | node_id |
      | node1   |
    When I postprocess nodes using the ParentSummaryPostProcessor with max_levels set to 3
    Then the resulting nodes should include:
      | node_id  |
      | node1    |
      | summary1 |
      | summary2 |

  Scenario: No Parent Summaries Available
    Given starting nodes are:
      | node_id |
      | node2   |
    When I postprocess nodes using the ParentSummaryPostProcessor with max_levels set to 3
    Then the resulting nodes should include:
      | node_id |
      | node2   |

  Scenario: Multiple Starting Nodes
    Given starting nodes are:
      | node_id |
      | node1   |
      | node2   |
    When I postprocess nodes using the ParentSummaryPostProcessor with max_levels set to 3
    Then the resulting nodes should include:
      | node_id  |
      | node1    |
      | node2    |
      | summary1 |
      | summary2 |

  Scenario: Summary Nodes Should Also Fetch Additional Parents
    Given starting nodes are:
      | node_id  |
      | summary1 |
    When I postprocess nodes using the ParentSummaryPostProcessor with max_levels set to 3
    Then the resulting nodes should include:
      | node_id  |
      | summary1 |
      | summary2 |