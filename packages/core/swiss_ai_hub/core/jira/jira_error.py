class JiraError(Exception):
    """Anything that kept a Jira read from giving a complete answer.

    Its message is shown as it is, e.g. in an agent's chat, so it never carries the token or the query string; the
    subclasses carry what a caller needs to word the failure in its user's language.
    """
