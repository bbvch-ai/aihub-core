Feature: Combine nodes in order

  Scenario: Combine nodes with default context prompt
    Given a locale handler
    And no context prompt
    And the following context nodes:
      | document_id | source | namespace      | type    | content_type | language | version | created_at | updated_at | inserted_at | section_start_line | section_end_line | text                | score | heading_level |
      | doc1        | doc1   | research_paper | content | text         | en       | 1       | 1700000000 | 1700005000 | 1700010000  | 10                 | 20               | Doc1 line10 content | 0.9   | 1             |
      | doc1        | doc1   | research_paper | content | text         | en       | 1       | 1700000000 | 1700005000 | 1700010000  | 20                 | 25               | Doc1 line20 content | 0.8   | 1             |
      | doc2        | doc2   | legal_document | content | text         | fr       | 2       | 1690000000 | 1690005000 | 1690010000  | 15                 | 20               | Doc2 line15 content | 0.95  | 1             |
    When the combine_nodes_in_order function is called
    Then it should return:
      """
      You are provided with additional context information in the form of structured documents. Each document follows a
      consistent format, beginning with `<REFERENCE_DOCUMENT [metadata]>` and ending with `</REFERENCE_DOCUMENT>`. These documents contain
      essential details that should be utilized to accurately understand and respond to the user’s query.

      Each document includes metadata such as source, namespace, type, language, version, and timestamps. The content
      within these documents provides crucial insights relevant to the given context.

      Below are the relevant documents:

      <context_documents>
      <REFERENCE_DOCUMENT source='doc1' namespace='research_paper' type='content' content_type='text' language='en' version='1' created_at='2023-11-14T22:13:20Z' updated_at='2023-11-14T23:36:40Z' inserted_at='2023-11-15T01:00:00Z'>


      Doc1 line10 content
      Doc1 line20 content
      </REFERENCE_DOCUMENT>

      ---

      <REFERENCE_DOCUMENT source='doc2' namespace='legal_document' type='content' content_type='text' language='fr' version='2' created_at='2023-07-22T04:26:40Z' updated_at='2023-07-22T05:50:00Z' inserted_at='2023-07-22T07:13:20Z'>


      Doc2 line15 content
      </REFERENCE_DOCUMENT>

      ---

      </context_documents>

      Instruction: Using the information from the provided documents, generate a detailed and well-structured response
      to the user’s question.
      """

  @slow
  Scenario: Combine nodes with a custom context prompt
    Given a locale handler
    And a custom context prompt
    And the following context nodes:
      | document_id | source | namespace      | type    | content_type | language | version | created_at | updated_at | inserted_at | section_start_line | section_end_line | text              | score | heading_level |
      | docA        | docA   | research_paper | content | text         | en       | 1       | 1700000000 | 1700005000 | 1700010000  | 10                 | 20               | Node docA line=5  | 0.9   | 1             |
      | docA        | docA   | research_paper | content | text         | en       | 1       | 1700000000 | 1700005000 | 1700010000  | 20                 | 25               | Node docA line=10 | 0.8   | 1             |
    When the combine_nodes_in_order function is called
    Then it should return:
      """
      Custom prompt: <REFERENCE_DOCUMENT source='docA' namespace='research_paper' type='content' content_type='text' language='en' version='1' created_at='2023-11-14T22:13:20Z' updated_at='2023-11-14T23:36:40Z' inserted_at='2023-11-15T01:00:00Z'>


      Node docA line=5
      Node docA line=10
      </REFERENCE_DOCUMENT>

      ---
      """

  Scenario: Multiple docs but empty final text
    Given a locale handler
    And no context prompt
    And no context nodes
    When the combine_nodes_in_order function is called
    Then it should return:
      """
       You are provided with additional context information in the form of structured documents. Each document follows a
      consistent format, beginning with `<REFERENCE_DOCUMENT [metadata]>` and ending with `</REFERENCE_DOCUMENT>`. These documents contain
      essential details that should be utilized to accurately understand and respond to the user’s query.

      Each document includes metadata such as source, namespace, type, language, version, and timestamps. The content
      within these documents provides crucial insights relevant to the given context.

      Below are the relevant documents:

      <context_documents>

      </context_documents>

      Instruction: Using the information from the provided documents, generate a detailed and well-structured response
      to the user’s question.
      """

  Scenario: Another custom scenario with multiple sources
    Given a locale handler
    And no context prompt
    And the following context nodes:
      | document_id | source | namespace      | type    | content_type | language | version | created_at | updated_at | inserted_at | section_start_line | section_end_line | text        | score | heading_level |
      | docX        | docX   | research_paper | content | text         | en       | 1       | 1700000000 | 1700005000 | 1700010000  | 2                  | 20               | docX line=2 | 0.8   | 1             |
      | docX        | docX   | research_paper | content | text         | en       | 1       | 1700000000 | 1700005000 | 1700010000  | 1                  | 25               | docX line=1 | 0.7   | 1             |
      | docY        | docY   | legal_document | content | text         | fr       | 2       | 1690000000 | 1690005000 | 1690010000  | 5                  | 20               | docY line=5 | 0.9   | 1             |

    When the combine_nodes_in_order function is called
    Then it should return:
      """
      You are provided with additional context information in the form of structured documents. Each document follows a
      consistent format, beginning with `<REFERENCE_DOCUMENT [metadata]>` and ending with `</REFERENCE_DOCUMENT>`. These documents contain
      essential details that should be utilized to accurately understand and respond to the user’s query.

      Each document includes metadata such as source, namespace, type, language, version, and timestamps. The content
      within these documents provides crucial insights relevant to the given context.

      Below are the relevant documents:

      <context_documents>
      <REFERENCE_DOCUMENT source='docX' namespace='research_paper' type='content' content_type='text' language='en' version='1' created_at='2023-11-14T22:13:20Z' updated_at='2023-11-14T23:36:40Z' inserted_at='2023-11-15T01:00:00Z'>


      docX line=1
      docX line=2
      </REFERENCE_DOCUMENT>

      ---

      <REFERENCE_DOCUMENT source='docY' namespace='legal_document' type='content' content_type='text' language='fr' version='2' created_at='2023-07-22T04:26:40Z' updated_at='2023-07-22T05:50:00Z' inserted_at='2023-07-22T07:13:20Z'>

      docY line=5
      </REFERENCE_DOCUMENT>

      ---

      </context_documents>

      Instruction: Using the information from the provided documents, generate a detailed and well-structured response
      to the user’s question.
      """

  Scenario: Combine nodes with all metadata fields
    Given a locale handler
    And a custom context prompt
    And the following context nodes:
      | document_id | source | namespace      | type    | content_type | language | version | created_at | updated_at | inserted_at | section_start_line | section_end_line | text                | score | heading_level |
      | 1           | doc1   | research_paper | content | text         | en       | 1       | 1700000000 | 1700005000 | 1700010000  | 10                 | 20               | Doc1 line10 content | 0.9   | 1             |
      | 2           | doc1   | research_paper | content | text         | en       | 1       | 1700000000 | 1700005000 | 1700010000  | 20                 | 25               | Doc1 line20 content | 0.8   | 1             |
      | 3           | doc2   | legal_document | content | text         | fr       | 2       | 1690000000 | 1690005000 | 1690010000  | 15                 | 20               | Doc2 line15 content | 0.95  | 1             |
    When the combine_nodes_in_order function is called
    Then it should return:
      """
      Custom prompt: <REFERENCE_DOCUMENT source='doc1' namespace='research_paper' type='content' content_type='text' language='en' version='1' created_at='2023-11-14T22:13:20Z' updated_at='2023-11-14T23:36:40Z' inserted_at='2023-11-15T01:00:00Z'>

      Doc1 line10 content
      Doc1 line20 content
      </REFERENCE_DOCUMENT>

      ---

      <REFERENCE_DOCUMENT source='doc2' namespace='legal_document' type='content' content_type='text' language='fr' version='2' created_at='2023-07-22T04:26:40Z' updated_at='2023-07-22T05:50:00Z' inserted_at='2023-07-22T07:13:20Z'>

      Doc2 line15 content
      </REFERENCE_DOCUMENT>

      ---
      """
