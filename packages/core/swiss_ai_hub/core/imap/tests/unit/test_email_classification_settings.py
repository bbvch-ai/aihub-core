from swiss_ai_hub.core.form.elements.toggle_switch import ToggleSwitch
from swiss_ai_hub.core.imap.email_classification_settings import EmailClassificationSettings


def test_uncategorised_mail_leaves_the_inbox_unless_the_admin_keeps_it():
    assert EmailClassificationSettings().keep_uncategorised_in_inbox is False


def test_the_fallback_folder_is_hidden_while_uncategorised_mail_is_kept_in_the_inbox():
    form = EmailClassificationSettings.as_form()

    assert isinstance(form.keep_uncategorised_in_inbox, ToggleSwitch)
    assert form.fallback_folder.condition_if == f"$get({form.keep_uncategorised_in_inbox.ref}).value !== true"
