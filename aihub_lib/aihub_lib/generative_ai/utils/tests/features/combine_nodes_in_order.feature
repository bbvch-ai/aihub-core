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
      You are provided with additional context information in the form of structured documents. Each document follows a
      consistent format, beginning with `<DOCUMENT [metadata]>` and ending with `</DOCUMENT>`. These documents contain
      essential details that should be utilized to accurately understand and respond to the user’s query.

      Each document includes metadata such as source, namespace, type, language, version, and timestamps. The content
      within these documents provides crucial insights relevant to the given context.

      Below are the relevant documents:

      <context_documents>
      <DOCUMENT source='doc1'>

      Doc1 line10 content

      Doc1 line20 content

      </DOCUMENT>

      ---
      <DOCUMENT source='doc2'>

      Doc2 line15 content

      </DOCUMENT>

      ---

      </context_documents>

      Instruction: Using the information from the provided documents, generate a detailed and well-structured response
      to the user’s question.
      """

  Scenario: Combine nodes with a custom context prompt
    Given a locale handler
    And a custom context prompt
    And the following context nodes:
      | source | section_start_line | text              | score |
      | docA   | 5                  | Node docA line=5  | 1.0   |
      | docA   | 10                 | Node docA line=10 | 1.0   |
    When the combine_nodes_in_order function is called
    Then it should return:
      """
      Custom prompt: <DOCUMENT source='docA'>

      Node docA line=5

      Node docA line=10

      </DOCUMENT>

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
       You are provided with additional context information in the form of structured documents. Each document follows a
      consistent format, beginning with `<DOCUMENT [metadata]>` and ending with `</DOCUMENT>`. These documents contain
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
      | source | section_start_line | text        | score |
      | docX   | 2                  | docX line=2 | 0.8   |
      | docX   | 1                  | docX line=1 | 0.7   |
      | docY   | 5                  | docY line=5 | 0.9   |
    When the combine_nodes_in_order function is called
    Then it should return:
      """
      You are provided with additional context information in the form of structured documents. Each document follows a
      consistent format, beginning with `<DOCUMENT [metadata]>` and ending with `</DOCUMENT>`. These documents contain
      essential details that should be utilized to accurately understand and respond to the user’s query.

      Each document includes metadata such as source, namespace, type, language, version, and timestamps. The content
      within these documents provides crucial insights relevant to the given context.

      Below are the relevant documents:

      <context_documents>
      <DOCUMENT source='docX'>

      docX line=1

      docX line=2

      </DOCUMENT>

      ---
      <DOCUMENT source='docY'>

      docY line=5

      </DOCUMENT>

      ---

      </context_documents>

      Instruction: Using the information from the provided documents, generate a detailed and well-structured response
      to the user’s question.
      """

  Scenario: Combine nodes with all metadata fields
    Given a locale handler
    And a custom context prompt
    And the following context nodes:
      | source | namespace      | type     | language | version | created_at | updated_at | inserted_at | section_start_line | text                | score |
      | doc1   | research_paper | report   | en       | 1.2     | 1700000000 | 1700005000 | 1700010000  | 10                 | Doc1 line10 content | 0.9   |
      | doc1   | research_paper | report   | en       | 1.2     | 1700000000 | 1700005000 | 1700010000  | 20                 | Doc1 line20 content | 0.8   |
      | doc2   | legal_document | contract | fr       | 2.0     | 1690000000 | 1690005000 | 1690010000  | 15                 | Doc2 line15 content | 0.95  |
    When the combine_nodes_in_order function is called
    Then it should return:
      """
      Custom prompt: <DOCUMENT source='doc1' namespace='research_paper' type='report' language='en' version='1.2' created_at='14.11.2023' updated_at='14.11.2023' inserted_at='15.11.2023'>

      Doc1 line10 content

      Doc1 line20 content

      </DOCUMENT>

      ---
      <DOCUMENT source='doc2' namespace='legal_document' type='contract' language='fr' version='2.0' created_at='22.07.2023' updated_at='22.07.2023' inserted_at='22.07.2023'>

      Doc2 line15 content

      </DOCUMENT>

      ---
      """
