"""
title: LCDM Hub GTO Instance Manager
author: Noah Hermann
version: 0.1.0
"""

from typing import Optional, Callable, Any, List, Dict, Type

import requests
from pydantic import BaseModel, Field, create_model, ValidationError


class Tools:
    class Valves(BaseModel):
        LCDM_HUB_BASE_URL: str = Field(
            default="https://dev.swisslcdmhub.bbv.ch/restapi/1.0/gto/",
            description="URL for accessing LCDM Hub API endpoints.",
        )
        LCDM_HUB_TOKEN: str = Field(
            default="",
            description="Token to authenticate requests to the LCDM Hub API.",
        )
        timeout_seconds: int = Field(default=30, description="Request timeout in seconds")

    def __init__(self):
        self.valves = self.Valves()
        self._schema_cache = {}  # Cache for GTO schemas to avoid repeated requests

    async def validate_and_store_gto_instances(
        self,
        gto_schema_id: int,
        instances: List[Dict],
        __event_emitter__: Optional[Callable[[dict], Any]] = None,
    ) -> str:
        """
        Validates GTO instances against their schema and stores them in the LCDM Hub.

        This tool performs the following steps:
        1. Fetches the GTO schema definition from the LCDM Hub using the provided schema ID
        2. Creates a dynamic Pydantic model based on the schema's attribute definitions
        3. Validates each provided instance against this dynamic model
        4. Stores all valid instances to the LCDM Hub via the aihub-data endpoint

        Use this tool when you need to:
        - Validate structured data extracted from documents against a specific GTO schema
        - Store multiple instances of a GTO type at once
        - Ensure data quality before inserting into the LCDM Hub system

        The tool expects instances to be provided as a list of dictionaries where:
        - Each dictionary represents one instance of the GTO
        - Keys should match the attribute keys defined in the GTO schema
        - Values should match the expected data types (string, int, float, bool)

        Example usage scenarios:
        - Processing invoice data: schema_id=101, instances=[{"invoice_number": "INV-001", "amount": 1500.50, "date": "2024-01-15"}]
        - Building inventory: schema_id=205, instances=[{"door_material": "Wood", "room_number": "A101", "size": 15}]
        - Equipment tracking: schema_id=303, instances=[{"equipment_type": "Laptop", "serial_number": "SN12345", "status": "Active"}]

        :param gto_schema_id: The unique identifier of the GTO schema to validate against
        :param instances: List of dictionaries representing GTO instances to validate and store
        :return: Success message with validation and storage results, or error details
        """

        if not self.valves.LCDM_HUB_TOKEN:
            error_msg = "LCDM Hub Token ist nicht konfiguriert. Bitte in den Einstellungen hinterlegen."
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": error_msg, "done": True}})
            return f"Error: {error_msg}"

        if not instances:
            error_msg = "Keine Instanzen zum Validieren und Speichern bereitgestellt."
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": error_msg, "done": True}})
            return f"Error: {error_msg}"

        try:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Lade GTO Schema mit ID {gto_schema_id}...",
                            "done": False,
                        },
                    }
                )

            schema_definition = await self._fetch_gto_schema(gto_schema_id)

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Schema '{schema_definition.get('name', 'Unknown')}' erfolgreich geladen.",
                            "done": False,
                        },
                    }
                )

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Erstelle dynamisches Validierungsmodell...",
                            "done": False,
                        },
                    }
                )

            dynamic_model = self._create_dynamic_model(schema_definition)

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Validiere {len(instances)} Instanz(en)...",
                            "done": False,
                        },
                    }
                )

            validated_instances = []
            validation_errors = []

            for i, instance in enumerate(instances):
                try:
                    validated_instance = dynamic_model(**instance)
                    validated_instances.append(validated_instance.model_dump())
                except ValidationError as e:
                    validation_errors.append(f"Instanz {i+1}: {str(e)}")

            if validation_errors:
                error_msg = f"Validierung fehlgeschlagen:\n" + "\n".join(validation_errors)
                if __event_emitter__:
                    await __event_emitter__(
                        {"type": "status", "data": {"description": "Validierungsfehler aufgetreten", "done": True}}
                    )
                return f"Validation Error: {error_msg}"

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Alle {len(validated_instances)} Instanzen erfolgreich validiert.",
                            "done": False,
                        },
                    }
                )

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Speichere Instanzen im LCDM Hub...",
                            "done": False,
                        },
                    }
                )

            success_count = 0
            storage_errors = []

            for i, instance in enumerate(validated_instances):
                try:
                    await self._store_instance(gto_schema_id, instance)
                    success_count += 1

                    if __event_emitter__:
                        await __event_emitter__(
                            {
                                "type": "status",
                                "data": {
                                    "description": f"Instanz {i+1}/{len(validated_instances)} gespeichert",
                                    "done": False,
                                },
                            }
                        )
                except Exception as e:
                    storage_errors.append(f"Instanz {i+1}: {str(e)}")

            if storage_errors:
                result_msg = (
                    f"Teilweise erfolgreich: {success_count}/{len(validated_instances)} Instanzen gespeichert.\nFehler:\n"
                    + "\n".join(storage_errors)
                )
            else:
                result_msg = (
                    f"Vollständig erfolgreich: Alle {success_count} Instanzen validiert und im LCDM Hub gespeichert."
                )

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {"description": "Vorgang abgeschlossen", "done": True},
                    }
                )

                await __event_emitter__(
                    {
                        "type": "message",
                        "data": {"content": f"✅ **Ergebnis:** {result_msg}"},
                    }
                )

            return f"Success: {result_msg}"

        except Exception as e:
            error_msg = f"Unerwarteter Fehler: {str(e)}"
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": error_msg, "done": True}})
            return f"Error: {error_msg}"

    async def _fetch_gto_schema(self, gto_schema_id: int) -> Dict:
        """Fetch GTO schema definition from the LCDM Hub."""
        if gto_schema_id in self._schema_cache:
            return self._schema_cache[gto_schema_id]

        headers = {
            "Authorization": f"Bearer {self.valves.LCDM_HUB_TOKEN}",
            "Accept": "application/json",
        }

        response = requests.get(
            f"{self.valves.LCDM_HUB_BASE_URL}{gto_schema_id}",
            headers=headers,
            timeout=self.valves.timeout_seconds,
        )

        if response.status_code != 200:
            raise Exception(f"Fehler beim Laden des GTO Schemas: {response.status_code} - {response.text}")

        schema_data = response.json()

        self._schema_cache[gto_schema_id] = schema_data

        return schema_data

    def _create_dynamic_model(self, schema_definition: Dict) -> Type[BaseModel]:
        """Create a dynamic Pydantic model based on GTO schema definition."""

        gto_name = schema_definition.get("name", "DynamicGTO")
        attribute_definitions = schema_definition.get("gtoAttributeDefinitions", {})

        field_definitions = {}

        for attr_key, attr_def in attribute_definitions.items():
            field_name = attr_def.get("key", attr_key)
            value_type = attr_def.get("valueType", "string")
            mandatory = attr_def.get("mandatory", False)
            unit = attr_def.get("unitOfMeasurement", "")

            python_type = self._map_value_type_to_python(value_type)

            description = f"GTO attribute: {field_name}"
            if unit:
                description += f" (Unit: {unit})"

            if mandatory:
                field_definitions[field_name] = (python_type, Field(..., description=description))
            else:
                field_definitions[field_name] = (Optional[python_type], Field(None, description=description))

        dynamic_model = create_model(f"{gto_name}Instance", **field_definitions)

        return dynamic_model

    def _map_value_type_to_python(self, value_type: str) -> Type:
        """Map GTO value types to Python types."""
        type_mapping = {
            "string": str,
            "String": str,
            "int": int,
            "integer": int,
            "float": float,
            "double": float,
            "boolean": bool,
            "bool": bool,
            "datetime": str,
            "date": str,
        }

        return type_mapping.get(value_type.lower(), str)

    async def _store_instance(self, gto_schema_id: int, instance: Dict) -> None:
        """Store a single GTO instance via the aihub-data endpoint."""
        headers = {
            "Authorization": f"Bearer {self.valves.LCDM_HUB_TOKEN}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        response = requests.post(
            f"{self.valves.LCDM_HUB_BASE_URL}{gto_schema_id}/aihub-data",
            json=instance,
            headers=headers,
            timeout=self.valves.timeout_seconds,
        )

        if response.status_code not in [200, 201]:
            raise Exception(f"Speichern fehlgeschlagen: {response.status_code} - {response.text}")


[
    {
        "id": 0,  # default, 0 for new values
        "gtoTyp": "Test GTO",  # GTO name, already created so should be known
        "objId": "150006",  # block number, data in GTOs are stored into blocks, should be something like id or another identifier of data
        "keyId": "TEST Attribute",  # the attribute which you are storing data, already defined in the GTO structure
        "sourceValue": "",  # the value of source column, the value you actually get from the unstructured data about this attribute
        "targetValue": "",  # the value of target column, the value you write (in most cases it should be blank because adaptors do write)
        "manualValue": "",  # manual value, any correction you manually make in the source value (probably will be the same as source)
        "gtoId": 7223392,  # the id of the GTO
        "manuallyModified": False,  # default, changes when you enter manual value through the app
        "released": False,  # default, changes when you release the value through adaptor execution in the app
        "gtoTransferType": "NOTRANSMISSION",  # default, changes when you release the value through adaptor execution in the app
        "gtoAttributeDefinitionsKey": "0005",  # the gto attribute key you get from the GTO definition (should match, else you get blocked)
        "issuedUpdatedByAdaptorId": 0,  # default, changes when you release the value through adaptor execution in the app
        "gtoRelationStatus": "NONE",  # default, change only if necessary from GTO attribute definition (GTO specs)
        "gtoBlockJoining": "",  # default, change only if necessary from GTO attribute definition (GTO specs)
        "qccValidationMessages": [],  # default, change only if necessary from GTO attribute definition (GTO specs)
        "metaDataFields": {},  # default, change only if necessary from GTO attribute definition (GTO specs)
        "sensitiveData": False,  # default, change only if there is a special role required for this data to be visible (eg medical data)
        "failedQualityRuleTypes": [],  # default, change only if necessary from GTO attribute definition (GTO specs)
        "participantMandatory": False,  # default
    }
]
