"""
title: LCDM Hub GTO Ingestion Tool
author: Noah Hermann
version: 0.1.0
"""

import hashlib
import json
from datetime import datetime
from typing import Optional, Callable, Any, List, Dict, Type

import requests
from pydantic import BaseModel, Field, create_model, ValidationError


class Tools:
    class Valves(BaseModel):
        LCDM_HUB_BASE_URL: str = Field(
            default="https://dev.swisslcdmhub.bbv.ch/restapi/1.0/gto/",
            description="Base URL for accessing LCDM Hub API endpoints.",
        )
        LCDM_HUB_TOKEN: str = Field(
            default="",
            description="Token to authenticate requests to the LCDM Hub API.",
        )
        timeout_seconds: int = Field(default=30, description="Request timeout in seconds")

    def __init__(self):
        self.valves = self.Valves()

    async def ingest_gto_instances(
        self,
        gto_id: str,
        instances_data: List[Dict],
        __event_emitter__: Optional[Callable[[dict], Any]] = None,
    ) -> str:
        """Validates and ingests GTO instances into the LCDM Hub."""

        if not self.valves.LCDM_HUB_TOKEN:
            error_msg = "Das LCDM Hub Token ist nicht konfiguriert. Bitte hinterlegen Sie ihn in den Einstellungen."
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": error_msg, "done": True}})
            return f"Error: {error_msg}"

        if not instances_data:
            error_msg = "Keine GTO Instanzen zum Verarbeiten bereitgestellt."
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": error_msg, "done": True}})
            return f"Error: {error_msg}"

        try:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Lade GTO Schema für '{gto_id}'...",
                            "done": False,
                        },
                    }
                )

            gto_schema = await self._fetch_gto_schema(gto_id)
            if not gto_schema:
                error_msg = f"GTO Schema für '{gto_id}' nicht gefunden."
                if __event_emitter__:
                    await __event_emitter__({"type": "status", "data": {"description": error_msg, "done": True}})
                return f"Error: {error_msg}"

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

            validation_model = self._create_dynamic_model(gto_schema)

            # Step 3: Validate instances
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Validiere {len(instances_data)} GTO Instanzen...",
                            "done": False,
                        },
                    }
                )

            validation_errors = []
            validated_instances = []

            for i, instance_data in enumerate(instances_data):
                try:
                    validated_instance = validation_model.model_validate(instance_data)
                    validated_instances.append(validated_instance)
                except ValidationError as e:
                    validation_errors.append(f"Instanz {i+1}: {str(e)}")

            if validation_errors:
                error_msg = f"Validierungsfehler gefunden:\n" + "\n".join(validation_errors)
                if __event_emitter__:
                    await __event_emitter__(
                        {"type": "status", "data": {"description": "Validierung fehlgeschlagen", "done": True}}
                    )
                return f"Validation Error: {error_msg}"

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Transformiere Daten für LCDM Hub...",
                            "done": False,
                        },
                    }
                )

            hub_data = self._transform_to_hub_format(validated_instances, gto_schema, gto_id)

            # Step 5: Save to LCDM Hub
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Speichere {len(hub_data)} Einträge im LCDM Hub...",
                            "done": False,
                        },
                    }
                )

            result = await self._save_to_hub(hub_data, gto_id)

            if result.startswith("Success"):
                success_msg = f"Erfolgreich {len(validated_instances)} GTO Instanzen vom Typ '{gto_id}' gespeichert."
                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {"description": success_msg, "done": True},
                        }
                    )
                    await __event_emitter__(
                        {
                            "type": "message",
                            "data": {"content": f"✅ **Erfolg!** {success_msg}"},
                        }
                    )
                return f"Success: {success_msg}"
            else:
                return result

        except Exception as e:
            error_msg = f"Unerwarteter Fehler beim Verarbeiten der GTO Instanzen: {str(e)}"
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": error_msg, "done": True}})
            return f"Error: {error_msg}"

    async def _fetch_gto_schema(self, gto_id: str) -> Optional[Dict]:
        """Fetches GTO schema from the LCDM Hub API."""
        try:
            headers = {
                "Authorization": f"Bearer {self.valves.LCDM_HUB_TOKEN}",
                "Accept": "application/json",
            }

            # First, get available GTOs to find the ID for the given type
            response = requests.get(
                f"{self.valves.LCDM_HUB_BASE_URL}availablenames",
                headers=headers,
                timeout=self.valves.timeout_seconds,
            )

            if response.status_code != 200:
                return None

            names = response.text
            names_list = eval(names)
            if gto_id not in [key for key, _ in names_list]:
                return None

            schema_response = requests.get(
                f"{self.valves.LCDM_HUB_BASE_URL}{gto_id}",
                headers=headers,
                timeout=self.valves.timeout_seconds,
            )

            if schema_response.status_code == 200:
                return schema_response.json()

            return None

        except Exception:
            return None

    def _create_dynamic_model(self, gto_schema: Dict) -> Type[BaseModel]:
        """Creates a dynamic Pydantic model from GTO schema."""
        fields = {}

        attribute_definitions = gto_schema.get("gtoAttributeDefinitions", {})

        for attr_key, attr_def in attribute_definitions.items():
            field_name = attr_def.get("key", attr_key)
            data_type = attr_def.get("dataType", "string")
            is_mandatory = attr_def.get("mandatory", False)

            if data_type == "int" or attr_def.get("valueType") == "int":
                python_type = int
            elif data_type == "float" or attr_def.get("valueType") == "float":
                python_type = float
            elif data_type == "bool" or attr_def.get("valueType") == "bool":
                python_type = bool
            else:
                python_type = str

            # Make field optional if not mandatory
            if not is_mandatory:
                python_type = Optional[python_type]
                fields[field_name] = (python_type, Field(default=None))
            else:
                fields[field_name] = (python_type, Field(...))

        # Create dynamic model
        DynamicGTOModel = create_model("DynamicGTOModel", **fields)
        return DynamicGTOModel

    def _generate_unique_obj_id(self, instance_data: Dict, gto_type: str) -> str:
        """Generates a unique objId based on GTO data."""
        # Create a hash from the instance data and timestamp
        data_string = json.dumps(instance_data, sort_keys=True) + gto_type + str(datetime.now().timestamp())
        hash_object = hashlib.md5(data_string.encode())
        return hash_object.hexdigest()[:8].upper()

    def _transform_to_hub_format(
        self, validated_instances: List[BaseModel], gto_schema: Dict, gto_type: str
    ) -> List[Dict]:
        """Transforms validated instances to LCDM Hub format."""
        hub_data = []
        gto_id = gto_schema.get("id")
        attribute_definitions = gto_schema.get("gtoAttributeDefinitions", {})

        for instance in validated_instances:
            instance_dict = instance.model_dump()
            obj_id = self._generate_unique_obj_id(instance_dict, gto_type)

            # Create hub entry for each attribute
            for attr_key, attr_def in attribute_definitions.items():
                field_name = attr_def.get("key")
                source_value = instance_dict.get(field_name, "")

                hub_entry = {
                    "id": 0,
                    "gtoTyp": gto_type,
                    "objId": obj_id,
                    "keyId": field_name,
                    "sourceValue": str(source_value) if source_value is not None else "",
                    "targetValue": "",
                    "manualValue": "",
                    "gtoId": gto_id,
                    "manuallyModified": False,
                    "released": False,
                    "gtoTransferType": "NOTRANSMISSION",
                    "gtoAttributeDefinitionsKey": attr_key,
                    "issuedUpdatedByAdaptorId": 0,
                    "gtoRelationStatus": "NONE",
                    "gtoBlockJoining": "",
                    "qccValidationMessages": [],
                    "metaDataFields": {},
                    "sensitiveData": False,
                    "failedQualityRuleTypes": [],
                    "participantMandatory": False,
                }

                hub_data.append(hub_entry)

        return hub_data

    async def _save_to_hub(self, hub_data: List[Dict], gto_id: str) -> str:
        """Saves transformed data to LCDM Hub."""
        try:
            headers = {
                "Authorization": f"Bearer {self.valves.LCDM_HUB_TOKEN}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

            # Assuming there's an endpoint for batch saving GTO instances
            # You may need to adjust this endpoint based on your actual API
            response = requests.post(
                f"{self.valves.LCDM_HUB_BASE_URL}{gto_id}/aihub-data",
                json=hub_data,
                headers=headers,
                timeout=self.valves.timeout_seconds,
            )

            if response.status_code in [200, 201]:
                return f"Success: Daten erfolgreich gespeichert."
            else:
                return f"API Error: Anfrage fehlgeschlagen mit Status {response.status_code}: {response.text}"

        except requests.exceptions.Timeout:
            return f"Timeout Error: Anfrage timeout nach {self.valves.timeout_seconds} Sekunden."
        except requests.exceptions.ConnectionError:
            return f"Connection Error: Verbindung zur LCDM Hub API fehlgeschlagen."
        except Exception as e:
            return f"Error: Unerwarteter Fehler beim Speichern: {str(e)}"
