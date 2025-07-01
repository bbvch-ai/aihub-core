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
      | aihub.user.agent.class-a.id-1 | aihub.user.agent.class-a.id-1         | True           |
      | aihub.user.agent.class-a.id-1 | aihub.user.agent.class-a.id-2         | False          |

      # Single-Level Wildcard (*)
      | aihub.user.agent.class-a.*    | aihub.user.agent.class-a.id-1         | True           |
      | aihub.user.agent.*.id-1       | aihub.user.agent.class-a.id-1         | True           |
      | aihub.user.agent.class-a.*    | aihub.user.agent.class-b.id-1         | False          |
      | aihub.user.agent.class-a.*    | aihub.user.agent.class-a.id-1.extra   | False          |

      # Multi-Level Wildcard (>)
      | aihub.user.agent.>            | aihub.user.agent.class-a.id-1         | True           |
      | aihub.user.agent.class-a.>    | aihub.user.agent.class-a.id-1         | True           |
      | aihub.user.agent.class-a.>    | aihub.user.agent.class-a.id-1.thread1 | True           |
      | aihub.user.process.>          | aihub.user.agent.class-a.id-1         | False          |

  Scenario Outline: Implicit Permission Matching for General Access
    Given the user has the role "<user_role>"
    When the access checker checks for the permission "<permission_template>"
    Then the result should be <has_permission>

    Examples:
      | user_role                  | permission_template        | has_permission |

      # Single Token Match (?)
      | aihub.user.agent.class-a.id-1 | aihub.user.agent.class-a.? | True           |
      | aihub.user.agent.class-a.id-1 | aihub.user.agent.?.id-1    | True           |
      | aihub.user.agent.class-a.id-1 | aihub.user.agent.?.?       | True           |
      | aihub.user.agent.class-a.id-1 | aihub.user.agent.class-b.? | False          |

      # Wildcard Token Match (?*)
      | aihub.user.agent.class-a.*    | aihub.user.agent.class-a.?*| True           |
      | aihub.user.agent.class-a.id-1 | aihub.user.agent.class-a.?*| False          |
      | aihub.user.agent.*.id-1       | aihub.user.agent.?*.id-1   | True           |

      # Multi-Level Wildcard Match (?>)
      | aihub.user.agent.>            | aihub.user.agent.?>        | True           |
      | aihub.user.agent.class-a.>    | aihub.user.agent.?>        | True           |
      | aihub.user.agent.class-a.id-1 | aihub.user.agent.?>        | False          |
      | aihub.user.agent.*            | aihub.user.agent.?>        | False          |


  Scenario Outline: Admin Role Inheritance
    Given the user has the role "<admin_role>"
    When the access checker checks for the user-level permission "<user_permission_template>"
    Then the result should be <has_permission>

    Examples:
      # Direct Matching Inheritance
      | admin_role                 | user_permission_template        | has_permission |
      | aihub.admin.agent.class-a.*| aihub.user.agent.class-a.id-1   | True           |
      | aihub.admin.agent.>        | aihub.user.agent.class-a.id-1   | True           |
      | aihub.admin.process.>      | aihub.user.agent.class-a.id-1   | False          |

      # Implicit Matching Inheritance
      | admin_role                 | user_permission_template        | has_permission |
      | aihub.admin.agent.class-a.*| aihub.user.agent.class-a.?* | True           |
      | aihub.admin.agent.>        | aihub.user.agent.?>             | True           |
      | aihub.admin.agent.class-a.*| aihub.user.agent.?>             | True           |


  Scenario Outline: Invalid Role and Permission Formats
    Given the user has the role "<user_role>"
    When the access checker checks for the permission "<permission_template>"
    Then a ValueError should be raised

    Examples:
      | user_role                  | permission_template                   |
      | aihub.user.agent.>         | aihub.user.agent.?>.extra             |
      | aihub.user.agent.>         | aihub.user.agent.invalid?char         |
      | aihub.user.agent.>         | aihub.user.agent.{agent_id}.{class}   |
      | aihub.user.agent.>         | other.user.agent.* |

  Scenario: User with no matching roles
    Given the user has the role "aihub.user.process.class-c.*"
    When the access checker checks for the permission "aihub.user.agent.class-a.id-1"
    Then the result should be False

  Scenario: Filtering of non-aihub roles
    Given the user has the role "some_other_role_format"
    And the user has the role "aihub.user.agent.class-a.*"
    When the access checker checks for the permission "aihub.user.agent.class-a.id-1"
    Then the result should be True

