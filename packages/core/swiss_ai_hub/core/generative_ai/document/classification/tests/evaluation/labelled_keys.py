from swiss_ai_hub.core.generative_ai.document.classification.document_type import DocumentType
from swiss_ai_hub.core.generative_ai.document.classification.document_type_catalog import DocumentTypeCatalog


class LabelledKeys:
    """The invoice keys a label states and the evaluation compares, each with the key of the text it was read from.

    Precision keys and computed attributes (parties) are left out: precision follows from the value, and parties from
    issuer and recipient, so measuring them again would only count the same error twice.
    """

    @classmethod
    def value_keys(cls) -> list[str]:
        return list(cls.raw_key_of_value_keys())

    @classmethod
    def raw_key_of_value_keys(cls) -> dict[str, str]:
        mapping: dict[str, str] = {}
        for definition in DocumentTypeCatalog.applicable(DocumentType.INVOICE):
            if definition.is_derived:
                continue
            for key in definition.stored_keys():
                if key not in (definition.raw_key, definition.precision_key):
                    mapping[key] = definition.raw_key
        return mapping
