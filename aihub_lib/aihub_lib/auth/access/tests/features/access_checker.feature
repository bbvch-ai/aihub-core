Feature: User Access Control Checker
  As a developer, I want a robust access checker
  So that I can securely and correctly determine if a user has permission to perform an action or access a resource.

  Scenario Outline: Direct Permission Matching for Specific Resources
    Given the access rule "<access_rule>"
    When the access checker checks for the permission "<permission_template>"
    Then the result should be <expected_level>

    Examples:
      | access_rule                           | permission_template                         | expected_level   |
      # Exact Matches
      | aihub.user.agent.class-a.id-1       | aihub.user.agent.class-a.id-1               | ACCESS_USER      |
      | aihub.user.agent.class-a.id-1       | aihub.user.agent.class-a.id-2               | ACCESS_DENIED    |
      | aihub.user.agent.class-a.id-1       | aihub.user.agent.class-a.id-2.extra         | ACCESS_DENIED    |
      | aihub.user.agent.class-a.id-1.extra | aihub.user.agent.class-a.id-2               | ACCESS_DENIED    |
      | aihub.user.agent.class-a.id-1.extra | aihub.user.agent.class-a.id-1.extra         | ACCESS_USER      |
      | aihub.user.agent.class-a.id-1.extra | aihub.user.agent.class-a.id-2.extra         | ACCESS_DENIED    |

      # Single-Level Wildcard (*)
      | aihub.user.agent.class-a.*          | aihub.user.agent.class-a.id-1               | ACCESS_USER      |
      | aihub.user.agent.*.id-1             | aihub.user.agent.class-a.id-1               | ACCESS_USER      |
      | aihub.user.agent.*.*                | aihub.user.agent.class-a.id-1               | ACCESS_USER      |
      | aihub.user.agent.class-a.*          | aihub.user.agent.class-b.id-1               | ACCESS_DENIED    |
      | aihub.user.agent.class-a.*          | aihub.user.agent.class-a.id-1.extra         | ACCESS_DENIED    |
      | aihub.user.agent.class-a.*.*        | aihub.user.agent.class-a.id-1.extra         | ACCESS_USER      |
      | aihub.user.agent.*.*.*              | aihub.user.agent.class-a.id-1.extra         | ACCESS_USER      |

      # Multi-Level Wildcard (>)
      | aihub.user.>                        | aihub.user.agent.class-a.id-1               | ACCESS_USER      |
      | aihub.user.agent.>                  | aihub.user.agent.class-a.id-1               | ACCESS_USER      |
      | aihub.user.agent.class-a.>          | aihub.user.agent.class-a.id-1               | ACCESS_USER      |
      | aihub.user.agent.class-a.>          | aihub.user.agent.class-b.id-1               | ACCESS_DENIED    |
      | aihub.user.agent.class-a.>          | aihub.user.agent.class-a.id-1.extra         | ACCESS_USER      |
      | aihub.user.process.>                | aihub.user.agent.class-a.id-1               | ACCESS_DENIED    |

  Scenario Outline: Implicit Permission Matching for General Access
    Given the access rule "<access_rule>"
    When the access checker checks for the permission "<permission_template>"
    Then the result should be <expected_level>

    Examples:
      | access_rule                     | permission_template         | expected_level |
      # Wildcard Token Match (?*)
      | aihub.user.agent.class-a.*    | aihub.user.agent.class-a.?* | ACCESS_USER    |
      | aihub.user.agent.class-a.id-1 | aihub.user.agent.class-a.?* | ACCESS_USER    |
      | aihub.user.agent.*.id-1       | aihub.user.agent.class-a.?* | ACCESS_USER    |
      | aihub.user.agent.class-a.id-1 | aihub.user.agent.?*.?*      | ACCESS_USER    |
      | aihub.user.agent.*.*          | aihub.user.agent.?*.?*      | ACCESS_USER    |
      | aihub.user.agent.*.id-1       | aihub.user.agent.?*.id-1    | ACCESS_USER    |
      | aihub.user.agent.*.id-1       | aihub.user.agent.?*.?*      | ACCESS_USER    |
      | aihub.user.agent.*.id-1       | aihub.user.agent.?*.?*      | ACCESS_USER    |

      # Multi-Level Wildcard Match (?>)
      | aihub.user.agent.>            | aihub.user.agent.?>         | ACCESS_USER    |
      | aihub.user.agent.class-a.>    | aihub.user.agent.?>         | ACCESS_USER    |
      | aihub.user.agent.class-a.id-1 | aihub.user.agent.?>         | ACCESS_USER    |
      | aihub.user.agent.*            | aihub.user.agent.?>         | ACCESS_USER    |

      # Non-matching Cases
      | aihub.user.service.>          | aihub.user.agent.?>         | ACCESS_DENIED  |
      | aihub.user.agent.class-b.>    | aihub.user.agent.class-a.?* | ACCESS_DENIED  |

  Scenario Outline: Complex Implicit Matching with access rule Wildcards
    Given the access rule "<access_rule>"
    When the access checker checks for the permission "<permission_template>"
    Then the result should be <expected_level>

    Examples:
      | access_rule                     | permission_template                 | expected_level |
      # Role `*` vs Template `?*`
      | aihub.user.agent.class-a.*    | aihub.user.agent.class-a.?*         | ACCESS_USER    |
      | aihub.user.agent.*.id-1       | aihub.user.agent.?*.id-1            | ACCESS_USER    |
      | aihub.user.agent.class-a.*    | aihub.user.agent.class-b.?*         | ACCESS_DENIED  |
      | aihub.user.agent.* | aihub.user.agent.?*.id-1                       | ACCESS_DENIED  |

      # Role `>` vs Template `?*`
      | aihub.user.agent.>            | aihub.user.agent.class-a.?*         | ACCESS_USER    |
      | aihub.user.agent.>            | aihub.user.agent.?*.id-1            | ACCESS_USER    |
      | aihub.user.agent.>            | aihub.user.agent.?*.?*              | ACCESS_USER    |
      | aihub.user.agent.class-a.>    | aihub.user.agent.class-a.?*         | ACCESS_USER    |
      | aihub.user.agent.class-a.>    | aihub.user.agent.class-a.id-1.?*    | ACCESS_USER    |
      | aihub.user.agent.class-a.>    | aihub.user.agent.class-b.?*         | ACCESS_DENIED  |
      | aihub.user.agent.class-a.id-1 | aihub.user.agent.class-a.?*         | ACCESS_USER    |

      # Role `*` vs Template `?>`
      | aihub.user.agent.class-a.*    | aihub.user.agent.?>                 | ACCESS_USER    |
      | aihub.user.agent.*.id-1       | aihub.user.agent.?>                 | ACCESS_USER    |
      | aihub.user.agent.class-a.*    | aihub.user.process.?>               | ACCESS_DENIED  |
      | aihub.user.agent.* | aihub.user.agent.?>                            | ACCESS_USER    |

      # Role `>` vs Template `?>`
      | aihub.user.agent.class-a.>    | aihub.user.agent.?>                 | ACCESS_USER    |
      | aihub.user.agent.>            | aihub.user.agent.class-a.?>         | ACCESS_USER    |
      | aihub.user.process.>          | aihub.user.agent.?>                 | ACCESS_DENIED  |
      | aihub.user.agent.class-a.id-1 | aihub.user.agent.class-a.?>         | ACCESS_USER    |

  Scenario Outline: Admin Access Priority
    Given the access rule "<user_access_rule>"
    And the access rule "<admin_access_rule>"
    When the access checker checks for the permission "<permission_template>"
    Then the result should be <expected_level>

    Examples:
      | user_access_rule                     | admin_access_rule        | permission_template           | expected_level |
      # Both user and admin access rules match; admin should win
      | aihub.user.agent.class-a.*          | aihub.admin.agent.class-a.*     | aihub.user.agent.class-a.id-1 | ACCESS_ADMIN   |
      | aihub.user.agent.>                  | aihub.admin.agent.>             | aihub.user.agent.class-a.id-1 | ACCESS_ADMIN   |

      # Specific user access rule and general admin access rule match; admin should win
      | aihub.user.agent.class-a.id-1       | aihub.admin.agent.>             | aihub.user.agent.class-a.id-1 | ACCESS_ADMIN   |

      # Only admin access rule matches; result should be admin
      | aihub.user.process.>                | aihub.admin.agent.>             | aihub.user.agent.class-a.id-1 | ACCESS_ADMIN   |

      # Only user access rule matches; result should be user
      | aihub.user.agent.>                  | aihub.admin.process.*           | aihub.user.agent.class-a.id-1 | ACCESS_USER    |

      # Implicit permission where both could match; admin must win
      | aihub.user.agent.class-a.*          | aihub.admin.agent.>             | aihub.user.agent.?>           | ACCESS_ADMIN   |
      | aihub.user.agent.>                  | aihub.admin.agent.class-a.id-1  | aihub.user.agent.class-a.id-1 | ACCESS_ADMIN   |
      | aihub.user.agent.>                  | aihub.admin.agent.class-a.*     | aihub.user.agent.class-a.id-1 | ACCESS_ADMIN   |
      | aihub.user.agent.>                  | aihub.admin.agent.*.id-1        | aihub.user.agent.class-a.id-1 | ACCESS_ADMIN   |

  Scenario Outline: Admin Role Inheritance
    Given the access rule "<access_rule>"
    When the access checker checks for the permission "<user_permission_template>"
    Then the result should be <expected_level>

    Examples:
      | access_rule                  | user_permission_template      | expected_level |
      # Direct Matching Inheritance
      | aihub.admin.agent.class-a.* | aihub.user.agent.class-a.id-1 | ACCESS_ADMIN   |
      | aihub.admin.agent.>         | aihub.user.agent.class-a.id-1 | ACCESS_ADMIN   |
      | aihub.admin.process.>       | aihub.user.agent.class-a.id-1 | ACCESS_DENIED  |

      # Implicit Matching Inheritance
      | aihub.admin.agent.class-a.* | aihub.user.agent.class-a.?*   | ACCESS_ADMIN   |
      | aihub.admin.agent.>         | aihub.user.agent.?>           | ACCESS_ADMIN   |
      | aihub.admin.agent.class-a.* | aihub.user.agent.?>           | ACCESS_ADMIN   |

  Scenario Outline: Complex Admin Role Inheritance
    Given the access rule "<access_rule>"
    When the access checker checks for the permission "<user_permission_template>"
    Then the result should be <expected_level>

    Examples:
      | access_rule                  | user_permission_template        | expected_level |
      | aihub.admin.agent.*.id-1    | aihub.user.agent.?*.id-1        | ACCESS_ADMIN   |
      | aihub.admin.agent.>         | aihub.user.agent.class-a.?*     | ACCESS_ADMIN   |
      | aihub.admin.agent.class-a.* | aihub.user.agent.?>             | ACCESS_ADMIN   |
      | aihub.admin.agent.>         | aihub.user.agent.?>             | ACCESS_ADMIN   |
      | aihub.admin.agent.>         | aihub.user.agent.class-a.?>     | ACCESS_ADMIN   |
      | aihub.admin.process.>       | aihub.user.agent.class-a.?*     | ACCESS_DENIED  |
      | aihub.admin.process.*       | aihub.user.agent.?>             | ACCESS_DENIED  |

  Scenario Outline: Invalid and Abusive Permission Templates
    Given the access rule "aihub.user.agent.>"
    When the access checker checks for the permission "<permission_template>"
    Then a ValueError should be raised

    Examples:
      | permission_template                 |
      # Invalid characters
      | aihub.user.agent.invalid?char       |
      | aihub.user.agent.{agent_id}.{class} |
      | aihub.user.agent.class-a.?          |
      | aihub.user.agent.?.id-1             |
      | aihub.user.agent.?.?                |

      # Invalid structure
      | aihub.user.agent.?>.extra           |
      | aihub.user.agent..id-1              |

      # Invalid prefix
      | other.user.agent.*                  |

      # Abusive wildcards at high level
      | aihub.*                             |
      | aihub.>                             |
      | aihub.user.*                        |
      | aihub.user.>                        |
      | aihub.user.*.agent                  |

      # Standalone wildcards
      | >                                   |
      | *                                   |
      | ?                                   |

  Scenario Outline: Malformed user access rules are ignored
    Given the access rule "<malformed_access_rule>"
    When the access checker checks for the permission "aihub.user.agent.class-a.id-1"
    Then the result should be ACCESS_DENIED

    Examples:
      | malformed_access_rule      |
      | aihub.user.>.agent         |
      | aihub.user.agent.class$a.* |
      | aihub.user.agent.          |
      | .aihub.user.agent          |
      | aihub..agent               |
      | not-aihub-prefix           |

  Scenario: User with no matching access rules
    Given the access rule "aihub.user.process.class-c.*"
    When the access checker checks for the permission "aihub.user.agent.class-a.id-1"
    Then the result should be ACCESS_DENIED

  Scenario: Filtering of non-aihub access rules
    Given the access rule "some_other_access_rule_format"
    And the access rule "aihub.user.agent.class-a.*"
    When the access checker checks for the permission "aihub.user.agent.class-a.id-1"
    Then the result should be ACCESS_USER

  Scenario Outline: Case sensitivity support for uppercase class names
    Given the access rule "<access_rule>"
    When the access checker checks for the permission "<permission_template>"
    Then the result should be <expected_level>

    Examples:
      | access_rule                                | permission_template                           | expected_level |
      # Exact match with uppercase agent class
      | aihub.user.agent.RAGAgent.rag_dev_agent   | aihub.user.agent.RAGAgent.rag_dev_agent       | ACCESS_USER    |
      | aihub.user.agent.RAGAgent.*               | aihub.user.agent.RAGAgent.rag_dev_agent       | ACCESS_USER    |
      | aihub.user.agent.RAGAgent.>               | aihub.user.agent.RAGAgent.rag_dev_agent       | ACCESS_USER    |
      # Mixed case in various components
      | aihub.user.agent.MyAgent.MyId123          | aihub.user.agent.MyAgent.MyId123              | ACCESS_USER    |
      | aihub.admin.agent.RAGAgent.*              | aihub.user.agent.RAGAgent.rag_dev_agent       | ACCESS_ADMIN   |