Feature: Vector Node Chain Traversal
  In order to enhance retrieval with contextual nodes,
  As a user of the VectorPrevNextPostProcessor,
  I want to fetch adjacent nodes from a vector store in forward, backward, or both directions.

  Background:
    Given these nodes:
      | id    | text               |
      | node0 | "Content of node0" |
      | node1 | "Content of node1" |
      | node2 | "Content of node2" |
    And the following relationships for "node1":
      | relationship | target_node_id |
      | next         | node2          |
      | previous     | node0          |
    And a valid vector store with all nodes
    And starting node is "node1"

  Scenario: Traverse Forward Nodes Only
    When I postprocess nodes from the starting node using the VectorPrevNextPostProcessor with mode "next" and num_nodes set to 1
    Then the resulting node chain should contain nodes in the following order:
      | node_id |
      | node1   |
      | node2   |

  Scenario: Traverse Backward Nodes Only
    When I postprocess nodes from the starting node using the VectorPrevNextPostProcessor with mode "previous" and num_nodes set to 1
    Then the resulting node chain should contain nodes in the following order:
      | node_id |
      | node0   |
      | node1   |

  Scenario: Traverse Nodes in Both Directions
    When I postprocess nodes from the starting node using the VectorPrevNextPostProcessor with mode "both" and num_nodes set to 1
    Then the resulting node chain should contain nodes in the following order:
      | node_id |
      | node0   |
      | node1   |
      | node2   |
