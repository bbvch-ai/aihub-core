Scenario: Combine nodes with default context prompt
Given a locale handler
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