Feature: Milvus Vector Store Factory Configuration
  As a developer, I want to create Milvus vector stores with manual partitioning
  So that I can achieve memory-efficient namespace isolation

  Background:
    Given a Milvus server is running at "http://localhost:19530"
    And the embedding dimension is 3072

  Scenario: Create collection with manual partitions and correct schema
    Given I want to create a collection named "test_manual_partitions"
    When I create a vector store with 1024 partitions
    Then the collection should exist in Milvus
    And the collection should have 1024 physical partitions
    And the collection schema should have these fields:
      | field_name       | data_type            | is_primary | is_partition_key |
      | id               | VARCHAR              | true       | false            |
      | document_id      | VARCHAR              | false      | false            |
      | namespace        | VARCHAR              | false      | false            |
      | embedding        | FLOAT_VECTOR         | false      | false            |
      | sparse_embedding | SPARSE_FLOAT_VECTOR  | false      | false            |
      | text             | VARCHAR              | false      | false            |
    And the vector store should have sparse embeddings enabled
    And the collection should have a BM25 function defined

  Scenario: Namespace-based partition routing works correctly
    Given I want to create a collection named "test_partition_routing"
    And I create a vector store with 1024 partitions
    When I insert 3 nodes with namespace "sales_team"
    And I insert 7 nodes with namespace "engineering_team"
    And I flush and load the collection
    Then querying for namespace "sales_team" should return 3 nodes
    And querying for namespace "engineering_team" should return 7 nodes
    And all returned nodes should have their correct namespace
