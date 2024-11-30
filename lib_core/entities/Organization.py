from typing import List

from mongoengine import (
    BooleanField,
    Document,
    EmbeddedDocument,
    EmbeddedDocumentField,
    FloatField,
    IntField,
    StringField,
)
from mongoengine.base import DocumentMetaclass

from aihub.app.constants.features import FeatureFlag
from aihub.records.organization.OrganizationResponse import OrganizationResponse


class OrganizationLimits(EmbeddedDocument):
    monthly_spending_limit_per_orga = FloatField(required=False, default=1_000)
    monthly_spending_limit_per_user = FloatField(required=False, default=100)


class OrganizationFeaturesCheckMeta(DocumentMetaclass):
    """Metaclass to check that all fields are present and no unexpected fields are present.
    With this metaclass, the class OrganizationFeatures is forced to have all fields present in the enum FeatureFlag.
    Like this, we can ensure that when accessing FeatureFlags though the Enum that the flags are also respected in the
    OrganizationFeatures object collects the data from the database."""

    def __new__(mcs, name, bases, attrs):
        for feature in list(FeatureFlag):
            if feature.value not in attrs:
                raise TypeError(f"Missing field for feature: {feature.value}")
        for attr in attrs:
            if attr not in [feature.value for feature in list(FeatureFlag)] and not attr.startswith("_"):
                raise TypeError(f"Unexpected field: {attr}")
        return super().__new__(mcs, name, bases, attrs)


class OrganizationFeatures(EmbeddedDocument, metaclass=OrganizationFeaturesCheckMeta):
    prompt_enhance = BooleanField(required=False, default=False)
    prompt_library = BooleanField(required=False, default=False)
    voice_input = BooleanField(required=False, default=False)
    voice_output = BooleanField(required=False, default=False)
    tracing = BooleanField(required=False, default=False)
    trace_user = BooleanField(required=False, default=False)
    usage_limits = BooleanField(required=False, default=False)
    chat_export_import = BooleanField(required=False, default=False)
    save_questions = BooleanField(required=False, default=False)
    save_chat_history = BooleanField(required=False, default=False)


class Organization(Document):
    meta = {
        "collection": "organizations",
        "strict": False,
    }
    version = IntField(default=1, db_field="_version")
    name = StringField(required=True)
    shortname = StringField(required=True)
    msal_client_id = StringField(required=True)
    msal_tenant_id = StringField(required=True)
    logo_url = StringField(required=True)
    dark_logo_url = StringField(required=True)
    limits = EmbeddedDocumentField(OrganizationLimits, required=True)
    features = EmbeddedDocumentField(OrganizationFeatures, required=True)

    @staticmethod
    def by_shortname(shortname: str):
        return Organization.objects.using("default").get(shortname=shortname)

    @staticmethod
    def all_shortnames() -> List[str]:
        organizations = Organization.objects.only("shortname")
        return [org.shortname for org in organizations]

    def to_record(self):
        return OrganizationResponse(**self.to_mongo().to_dict())
