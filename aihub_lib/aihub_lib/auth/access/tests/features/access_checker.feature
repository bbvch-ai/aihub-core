Feature: User Access Control Checker
  As a developer, I want a robust access checker
  So that I can securely and correctly determine if a user has permission to perform an action or access a resource.

  Background:
    Given a user with the name "Test User" and email "test@example.com"

  Scenario Outline: Direct Permission Matching for Specific Resources
    Given the user has the role "<user_role>"
    When the access checker checks for the permission "<permission_template>"
    Then the result should be <has_permission>

    Examples:
      | user_role                     | permission_template                   | has_permission |
      # Exact Matches
      | aihub.user.agent.class-a.id-1       | aihub.user.agent.class-a.id-1                     | True           |
      | aihub.user.agent.class-a.id-1       | aihub.user.agent.class-a.id-2                     | False          |
      | aihub.user.agent.class-a.id-1       | aihub.user.agent.class-a.id-2.extra               | False          |
      | aihub.user.agent.class-a.id-1.extra | aihub.user.agent.class-a.id-2                     | False          |
      | aihub.user.agent.class-a.id-1.extra | aihub.user.agent.class-a.id-1.extra               | True           |
      | aihub.user.agent.class-a.id-1.extra | aihub.user.agent.class-a.id-2.extra               | False          |

      # Single-Level Wildcard (*)
      | aihub.user.agent.class-a.*    | aihub.user.agent.class-a.id-1            | True           |
      | aihub.user.agent.*.id-1       | aihub.user.agent.class-a.id-1            | True           |
      | aihub.user.agent.*.*          | aihub.user.agent.class-a.id-1            | True           |
      | aihub.user.agent.class-a.*    | aihub.user.agent.class-b.id-1            | False          |
      | aihub.user.agent.class-a.*    | aihub.user.agent.class-a.id-1.extra      | False          |
      | aihub.user.agent.class-a.*.*  | aihub.user.agent.class-a.id-1.extra      | True           |
      | aihub.user.agent.*.*.*        | aihub.user.agent.class-a.id-1.extra      | True           |

      # Multi-Level Wildcard (>)
      | aihub.user.>                  | aihub.user.agent.class-a.id-1         | True           |
      | aihub.user.agent.>            | aihub.user.agent.class-a.id-1         | True           |
      | aihub.user.agent.class-a.>    | aihub.user.agent.class-a.id-1         | True           |
      | aihub.user.agent.class-a.>    | aihub.user.agent.class-b.id-1         | False          |
      | aihub.user.agent.class-a.>    | aihub.user.agent.class-a.id-1.extra   | True           |
      | aihub.user.process.>          | aihub.user.agent.class-a.id-1         | False          |

  Scenario Outline: Implicit Permission Matching for General Access
    Given the user has the role "<user_role>"
    When the access checker checks for the permission "<permission_template>"
    Then the result should be <has_permission>

    Examples:
      | user_role                     | permission_template         | has_permission |
      # Wildcard Token Match (?*)
      | aihub.user.agent.class-a.*    | aihub.user.agent.class-a.?* | True           |
      | aihub.user.agent.class-a.id-1 | aihub.user.agent.class-a.?* | True           |
      | aihub.user.agent.*.id-1       | aihub.user.agent.class-a.?* | True           |
      | aihub.user.agent.class-a.id-1 | aihub.user.agent.?*.?*      | True           |
      | aihub.user.agent.*.*          | aihub.user.agent.?*.?*      | True           |
      | aihub.user.agent.*.id-1       | aihub.user.agent.?*.id-1    | True           |
      | aihub.user.agent.*.id-1       | aihub.user.agent.?*.?*      | True           |
      | aihub.user.agent.*.id-1       | aihub.user.agent.?*.?*      | True           |

      # Multi-Level Wildcard Match (?>)
      | aihub.user.agent.>            | aihub.user.agent.?>         | True           |
      | aihub.user.agent.class-a.>    | aihub.user.agent.?>         | True           |
      | aihub.user.agent.class-a.id-1 | aihub.user.agent.?>         | True           |
      | aihub.user.agent.*            | aihub.user.agent.?>         | True           |

  Scenario Outline: Complex Implicit Matching with Role Wildcards
    Given the user has the role "<user_role>"
    When the access checker checks for the permission "<permission_template>"
    Then the result should be <has_permission>

    Examples:
      | user_role                     | permission_template                 | has_permission |
      # Role `*` vs Template `?*`
      | aihub.user.agent.class-a.*    | aihub.user.agent.class-a.?*         | True           |
      | aihub.user.agent.*.id-1       | aihub.user.agent.?*.id-1            | True           |
      | aihub.user.agent.class-a.*    | aihub.user.agent.class-b.?*         | False          |
      | aihub.user.agent.*            | aihub.user.agent.?*.id-1            | False          |

      # Role `>` vs Template `?*`
      | aihub.user.agent.>            | aihub.user.agent.class-a.?*         | True           |
      | aihub.user.agent.>            | aihub.user.agent.?*.id-1            | True           |
      | aihub.user.agent.>            | aihub.user.agent.?*.?*              | True           |
      | aihub.user.agent.class-a.>    | aihub.user.agent.class-a.?*         | True           |
      | aihub.user.agent.class-a.>    | aihub.user.agent.class-a.id-1.?*    | True           |
      | aihub.user.agent.class-a.>    | aihub.user.agent.class-b.?*         | False          |
      | aihub.user.agent.class-a.id-1 | aihub.user.agent.class-a.?*         | True           |

      # Role `*` vs Template `?>`
      | aihub.user.agent.class-a.*    | aihub.user.agent.?>                 | True           |
      | aihub.user.agent.*.id-1       | aihub.user.agent.?>                 | True           |
      | aihub.user.agent.class-a.*    | aihub.user.process.?>               | False          |
      | aihub.user.agent.*            | aihub.user.agent.?>                 | True           |

      # Role `>` vs Template `?>`
      | aihub.user.agent.class-a.>    | aihub.user.agent.?>                 | True           |
      | aihub.user.agent.>            | aihub.user.agent.class-a.?>         | True           |
      | aihub.user.process.>          | aihub.user.agent.?>                 | False          |
      | aihub.user.agent.class-a.id-1 | aihub.user.agent.class-a.?>         | True           |


  Scenario Outline: Admin Role Inheritance
    Given the user has the role "<admin_role>"
    When the access checker checks for the user-level permission "<user_permission_template>"
    Then the result should be <has_permission>

    Examples:
      # Direct Matching Inheritance
      | admin_role                    | user_permission_template        | has_permission |
      | aihub.admin.agent.class-a.*   | aihub.user.agent.class-a.id-1   | True           |
      | aihub.admin.agent.>           | aihub.user.agent.class-a.id-1   | True           |
      | aihub.admin.process.>         | aihub.user.agent.class-a.id-1   | False          |
      # Implicit Matching Inheritance
      | aihub.admin.agent.class-a.*   | aihub.user.agent.class-a.?*     | True           |
      | aihub.admin.agent.>           | aihub.user.agent.?>             | True           |
      | aihub.admin.agent.class-a.*   | aihub.user.agent.?>             | True           |

  Scenario Outline: Complex Admin Role Inheritance
    Given the user has the role "<admin_role>"
    When the access checker checks for the user-level permission "<user_permission_template>"
    Then the result should be <has_permission>

    Examples:
      | admin_role                    | user_permission_template            | has_permission |
      | aihub.admin.agent.*.id-1      | aihub.user.agent.?*.id-1            | True           |
      | aihub.admin.agent.>           | aihub.user.agent.class-a.?*         | True           |
      | aihub.admin.agent.class-a.*   | aihub.user.agent.?>                 | True           |
      | aihub.admin.agent.>           | aihub.user.agent.?>                 | True           |
      | aihub.admin.agent.>           | aihub.user.agent.class-a.?>         | True          |
      | aihub.admin.process.>         | aihub.user.agent.class-a.?*         | False          |
      | aihub.admin.process.*         | aihub.user.agent.?>                 | False          |


  Scenario Outline: Invalid and Abusive Permission Templates
    Given the user has the role "aihub.user.agent.>"
    When the access checker checks for the permission "<permission_template>"
    Then a ValueError should be raised

    Examples:
      | permission_template                   |
      # Invalid characters
      | aihub.user.agent.invalid?char         |
      | aihub.user.agent.{agent_id}.{class}   |
      | aihub.user.agent.class-a.?            |
      | aihub.user.agent.?.id-1               |
      | aihub.user.agent.?.?                  |

      # Invalid structure
      | aihub.user.agent.?>.extra             |
      | aihub.user.agent..id-1                |

      # Invalid prefix
      | other.user.agent.*                    |

      # Abusive wildcards at high level
      | aihub.*                               |
      | aihub.>                               |
      | aihub.user.*                          |
      | aihub.user.>                          |
      | aihub.user.*.agent                    |

      # Standalone wildcards
      | >                                     |
      | * |
      | ?                                     |

  Scenario Outline: Malformed user roles are ignored
    Given the user has the role "<malformed_role>"
    And the user has no other roles
    When the access checker checks for the permission "aihub.user.agent.class-a.id-1"
    Then the result should be False

    Examples:
      | malformed_role                |
      | aihub.user.>.agent            |
      | aihub.user.agent.class$a.*    |
      | aihub.user.agent.             |
      | .aihub.user.agent             |
      | aihub..agent                  |
      | not-aihub-prefix              |

  Scenario: User with no matching roles
    Given the user has the role "aihub.user.process.class-c.*"
    When the access checker checks for the permission "aihub.user.agent.class-a.id-1"
    Then the result should be False

  Scenario: Filtering of non-aihub roles
    Given the user has the role "some_other_role_format"
    And the user has the role "aihub.user.agent.class-a.*"
    When the access checker checks for the permission "aihub.user.agent.class-a.id-1"
    Then the result should be True