Feature: Combine nodes in order

  @slow
  Scenario: Combine nodes with default context prompt
    Given a locale handler
    And no context prompt
    And the following context nodes:
      | document_id | source | document_title | namespace      | type    | content_type | h1                  | language | version | created_at | updated_at | inserted_at | section_start_line | text                |
      | doc1        | doc1   | Doc 1 Title    | research_paper | content | text         | Main Title 1        | en       | 1       | 1704880800 | 1704967200 | 1705053600  | 10                 | Doc1 line10 content |
      | doc1        | doc1   | Doc 1 Title    | research_paper | content | text         | Main Title 1        | en       | 1       | 1704880800 | 1704967200 | 1705053600  | 20                 | Doc1 line20 content |
      | doc2        | doc2   | Doc 2 Title    | legal_document | content | text         | Legal Doc Main      | fr       | 2       | 1707987600 | 1708074000 | 1708160400  | 15                 | Doc2 line15 content |
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
      <REFERENCE_DOCUMENT source='doc1' document_title='Doc 1 Title' language='en' version='1' created_at='2024-01-10T10:00:00Z' updated_at='2024-01-11T10:00:00Z' inserted_at='2024-01-12T10:00:00Z'>

      <h1>Main Title 1</h1>

      <content>Doc1 line10 content</content>

      <content>Doc1 line20 content</content>

      </REFERENCE_DOCUMENT>

      ---

      <REFERENCE_DOCUMENT source='doc2' document_title='Doc 2 Title' language='fr' version='2' created_at='2024-02-15T09:00:00Z' updated_at='2024-02-16T09:00:00Z' inserted_at='2024-02-17T09:00:00Z'>

      <h1>Legal Doc Main</h1>

      <content>Doc2 line15 content</content>

      </REFERENCE_DOCUMENT>

      ---

      </context_documents>
      Instruction: Using the information from the provided documents, generate a detailed and well-structured response
      to the user’s question.
      """

  @slow
  Scenario: Combine nodes with summaries in hierarchical order
    Given a locale handler
    And no context prompt
    And the following context nodes:
      | document_id | source | namespace | document_title | type    | h1              | h2               | created_at | updated_at | inserted_at | section_start_line | text                                         | heading_level |
      | doc1        | doc1   | testing   | Hierarchical   | summary |                 |                  | 1709283600 | 1709287200 | 1709290800  | 0                  | This is the overall summary of the document. | 0             |
      | doc1        | doc1   | testing   | Hierarchical   | summary | Main Section    |                  | 1709283600 | 1709287200 | 1709290800  | 5                  | This is the summary of the main section.     | 1             |
      | doc1        | doc1   | testing   | Hierarchical   | content | Main Section    |                  | 1709283600 | 1709287200 | 1709290800  | 5                  | Content of the main section.                 | 1             |
      | doc1        | doc1   | testing   | Hierarchical   | summary | Main Section    | Sub Section 1.1  | 1709283600 | 1709287200 | 1709290800  | 20                 | Summary of subsection 1.1.                   | 2             |
      | doc1        | doc1   | testing   | Hierarchical   | content | Main Section    | Sub Section 1.1  | 1709283600 | 1709287200 | 1709290800  | 20                 | Content of subsection 1.1.                   | 2             |
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
      <REFERENCE_DOCUMENT source='doc1' document_title='Hierarchical' language='de' version='1' created_at='2024-03-01T09:00:00Z' updated_at='2024-03-01T10:00:00Z' inserted_at='2024-03-01T11:00:00Z'>

      <summary>This is the overall summary of the document.</summary>

      <h1>Main Section</h1>

      <summary>This is the summary of the main section.</summary>

      <content>Content of the main section.</content>

      <h2>Sub Section 1.1</h2>

      <summary>Summary of subsection 1.1.</summary>

      <content>Content of subsection 1.1.</content>

      </REFERENCE_DOCUMENT>

      ---

      </context_documents>
      Instruction: Using the information from the provided documents, generate a detailed and well-structured response
      to the user’s question.
      """

  @slow
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

  @slow
  Scenario: Combine nodes with all metadata fields
    Given a locale handler
    And a custom context prompt
    And the following context nodes:
      | document_id | source | document_title      | namespace      | type    | content_type | language | version | created_at | updated_at | inserted_at | section_start_line | section_end_line | text                | score | heading_level |
      | 1           | doc1   | research_paper.docx | research_paper | content | text         | en       | 1       | 1700000000 | 1700005000 | 1700010000  | 10                 | 20               | Doc1 line10 content | 0.9   | 1             |
      | 2           | doc1   | research_paper.docx | research_paper | content | text         | en       | 1       | 1700000000 | 1700005000 | 1700010000  | 20                 | 25               | Doc1 line20 content | 0.8   | 1             |
      | 3           | doc2   | legal_document.docx | legal_document | content | text         | fr       | 2       | 1690000000 | 1690005000 | 1690010000  | 15                 | 20               | Doc2 line15 content | 0.95  | 1             |
    When the combine_nodes_in_order function is called
    Then it should return:
      """
      Custom prompt: <REFERENCE_DOCUMENT source='doc1' document_title='research_paper.docx' language='en' version='1' created_at='2023-11-14T22:13:20Z' updated_at='2023-11-14T23:36:40Z' inserted_at='2023-11-15T01:00:00Z'>

      <content>Doc1 line10 content</content>

      <content>Doc1 line20 content</content>

      </REFERENCE_DOCUMENT>

      ---

      <REFERENCE_DOCUMENT source='doc2' document_title='legal_document.docx' language='fr' version='2' created_at='2023-07-22T04:26:40Z' updated_at='2023-07-22T05:50:00Z' inserted_at='2023-07-22T07:13:20Z'>

      <content>Doc2 line15 content</content>

      </REFERENCE_DOCUMENT>

      ---
      """


  @slow
  Scenario: Combine nodes with a custom context prompt
    Given a locale handler
    And a custom context prompt
    And the following context nodes:
      | document_id | source | document_title | namespace      | type    | content_type | language | version | created_at | updated_at | inserted_at | section_start_line | section_end_line | text              | score | heading_level |
      | docA        | docA   | research_paper | research_paper | content | text         | en       | 1       | 1700000000 | 1700005000 | 1700010000  | 10                 | 20               | Node docA line=5  | 0.9   | 1             |
      | docA        | docA   | research_paper | research_paper | content | text         | en       | 1       | 1700000000 | 1700005000 | 1700010000  | 20                 | 25               | Node docA line=10 | 0.8   | 1             |
    When the combine_nodes_in_order function is called
    Then it should return:
      """
      Custom prompt: <REFERENCE_DOCUMENT source='docA' document_title='research_paper' language='en' version='1' created_at='2023-11-14T22:13:20Z' updated_at='2023-11-14T23:36:40Z' inserted_at='2023-11-15T01:00:00Z'>

      <content>Node docA line=5</content>

      <content>Node docA line=10</content>

      </REFERENCE_DOCUMENT>

      ---
      """

  @slow
  Scenario: Handles special characters, whitespace, and empty content
    Given a locale handler
    And no context prompt
    And the following context nodes:
      | document_id | source | namespace | document_title | type    | h1                            | h2 | created_at | updated_at | inserted_at | section_start_line | text                          |
      | doc3        | doc3   | edge_case | Special Chars  | content | <HTML> & 'Tags'               |    | 1709292000 | 1709292000 | 1709292000  | 1                  | This content has an & ampersand. |
      | doc3        | doc3   | edge_case | Special Chars  | content |    Whitespace Heading         |    | 1709292000 | 1709292000 | 1709292000  | 5                  | Some more text.               |
      | doc3        | doc3   | edge_case | Special Chars  | content |    Whitespace Heading         |    | 1709292000 | 1709292000 | 1709292000  | 10                 |                               |
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
      <REFERENCE_DOCUMENT source='doc3' document_title='Special Chars' language='de' version='1' created_at='2024-03-01T11:20:00Z' updated_at='2024-03-01T11:20:00Z' inserted_at='2024-03-01T11:20:00Z'>

      <h1>&lt;HTML&gt; &amp; 'Tags'</h1>

      <content>This content has an &amp; ampersand.</content>

      <h1>Whitespace Heading</h1>

      <content>Some more text.</content>

      <content></content>

      </REFERENCE_DOCUMENT>

      ---

      </context_documents>
      Instruction: Using the information from the provided documents, generate a detailed and well-structured response
      to the user’s question.
      """

  @slow
  Scenario: Handles skipped heading levels and missing node position
    Given a locale handler
    And no context prompt
    And the following context nodes:
      | document_id | source | namespace | document_title | type    | h1          | h2 | h3          | created_at | updated_at | inserted_at | section_start_line | text                |
      | doc4        | doc4   | edge_case | Skipped Levels | summary |             |    |             | 1709292100 | 1709292100 | 1709292100  |                    | Summary with no position. |
      | doc4        | doc4   | edge_case | Skipped Levels | content |             |    |             | 1709292100 | 1709292100 | 1709292100  |                    | Content with no position. |
      | doc4        | doc4   | edge_case | Skipped Levels | content | Section 1   |    |             | 1709292100 | 1709292100 | 1709292100  | 10                 | Content for S1.     |
      | doc4        | doc4   | edge_case | Skipped Levels | content | Section 1   |    | Sub-sub 1.1 | 1709292100 | 1709292100 | 1709292100  | 20                 | Content for S1.1.1. |
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
      <REFERENCE_DOCUMENT source='doc4' document_title='Skipped Levels' language='de' version='1' created_at='2024-03-01T11:21:40Z' updated_at='2024-03-01T11:21:40Z' inserted_at='2024-03-01T11:21:40Z'>

      <summary>Summary with no position.</summary>

      <content>Content with no position.</content>

      <h1>Section 1</h1>

      <content>Content for S1.</content>

      <h3>Sub-sub 1.1</h3>

      <content>Content for S1.1.1.</content>

      </REFERENCE_DOCUMENT>

      ---

      </context_documents>
      Instruction: Using the information from the provided documents, generate a detailed and well-structured response
      to the user’s question.
      """