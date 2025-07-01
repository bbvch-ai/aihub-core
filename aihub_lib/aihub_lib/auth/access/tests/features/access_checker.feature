Feature: User Access Control Checker
  As a developer, I want a robust access checker
  So that I can securely and correctly determine if a user has permission to perform an action or access a resource.

  Background:
    Given a user with the name "Test User" and email "test@example.com"

  Scenario Outline: Direct Permission Matching for Specific Resources
    Given the user has the role "<user_role>"
    When the access checker checks for the permission "<permission_template>"
    Then the result should be <expected_level>

    Examples:
      | user_role                           | permission_template                         | expected_level   |
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
    Given the user has the role "<user_role>"
    When the access checker checks for the permission "<permission_template>"
    Then the result should be <expected_level>

    Examples:
      | user_role                     | permission_template         | expected_level |
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

  Scenario Outline: Complex Implicit Matching with Role Wildcards
    Given the user has the role "<user_role>"
    When the access checker checks for the permission "<permission_template>"
    Then the result should be <expected_level>

    Examples:
      | user_role                     | permission_template                 | expected_level |
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
    Given the user has the role "<user_role>"
    And the user has the role "<admin_role>"
    When the access checker checks for the permission "<permission_template>"
    Then the result should be <expected_level>

    Examples:
      | user_role                     | admin_role                    | permission_template           | expected_level |
      # Both user and admin roles match; admin should win
      | aihub.user.agent.class-a.*    | aihub.admin.agent.class-a.*   | aihub.user.agent.class-a.id-1 | ACCESS_ADMIN   |
      | aihub.user.agent.>            | aihub.admin.agent.>           | aihub.user.agent.class-a.id-1 | ACCESS_ADMIN   |

      # Specific user role and general admin role match; admin should win
      | aihub.user.agent.class-a.id-1 | aihub.admin.agent.>           | aihub.user.agent.class-a.id-1 | ACCESS_ADMIN   |

      # Only admin role matches; result should be admin
      | aihub.user.process.>          | aihub.admin.agent.>           | aihub.user.agent.class-a.id-1 | ACCESS_ADMIN   |

      # Only user role matches; result should be user
      | aihub.user.agent.>            | aihub.admin.process.*         | aihub.user.agent.class-a.id-1 | ACCESS_USER    |

      # Implicit permission where both could match; admin must win
      | aihub.user.agent.class-a.*    | aihub.admin.agent.>           | aihub.user.agent.?>           | ACCESS_ADMIN   |

  Scenario Outline: Admin Role Inheritance
    Given the user has the role "<admin_role>"
    When the access checker checks for the user-level permission "<user_permission_template>"
    Then the result should be <expected_level>

    Examples:
      | admin_role                  | user_permission_template      | expected_level |
      # Direct Matching Inheritance
      | aihub.admin.agent.class-a.* | aihub.user.agent.class-a.id-1 | ACCESS_ADMIN   |
      | aihub.admin.agent.>         | aihub.user.agent.class-a.id-1 | ACCESS_ADMIN   |
      | aihub.admin.process.>       | aihub.user.agent.class-a.id-1 | ACCESS_DENIED  |

      # Implicit Matching Inheritance
      | aihub.admin.agent.class-a.* | aihub.user.agent.class-a.?*   | ACCESS_ADMIN   |
      | aihub.admin.agent.>         | aihub.user.agent.?>           | ACCESS_ADMIN   |
      | aihub.admin.agent.class-a.* | aihub.user.agent.?>           | ACCESS_ADMIN   |

  Scenario Outline: Complex Admin Role Inheritance
    Given the user has the role "<admin_role>"
    When the access checker checks for the user-level permission "<user_permission_template>"
    Then the result should be <expected_level>

    Examples:
      | admin_role                  | user_permission_template        | expected_level |
      | aihub.admin.agent.*.id-1    | aihub.user.agent.?*.id-1        | ACCESS_ADMIN   |
      | aihub.admin.agent.>         | aihub.user.agent.class-a.?*     | ACCESS_ADMIN   |
      | aihub.admin.agent.class-a.* | aihub.user.agent.?>             | ACCESS_ADMIN   |
      | aihub.admin.agent.>         | aihub.user.agent.?>             | ACCESS_ADMIN   |
      | aihub.admin.agent.>         | aihub.user.agent.class-a.?>     | ACCESS_ADMIN   |
      | aihub.admin.process.>       | aihub.user.agent.class-a.?*     | ACCESS_DENIED  |
      | aihub.admin.process.*       | aihub.user.agent.?>             | ACCESS_DENIED  |

  Scenario Outline: Invalid and Abusive Permission Templates
    Given the user has the role "aihub.user.agent.>"
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

  Scenario Outline: Malformed user roles are ignored
    Given the user has the role "<malformed_role>"
    And the user has no other roles
    When the access checker checks for the permission "aihub.user.agent.class-a.id-1"
    Then the result should be ACCESS_DENIED

    Examples:
      | malformed_role             |
      | aihub.user.>.agent         |
      | aihub.user.agent.class$a.* |
      | aihub.user.agent.          |
      | .aihub.user.agent          |
      | aihub..agent               |
      | not-aihub-prefix           |

  Scenario: User with no matching roles
    Given the user has the role "aihub.user.process.class-c.*"
    When the access checker checks for the permission "aihub.user.agent.class-a.id-1"
    Then the result should be ACCESS_DENIED

  Scenario: Filtering of non-aihub roles
    Given the user has the role "some_other_role_format"
    And the user has the role "aihub.user.agent.class-a.*"
    When the access checker checks for the permission "aihub.user.agent.class-a.id-1"
    Then the result should be ACCESS_USER