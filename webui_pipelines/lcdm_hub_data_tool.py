"""
title: LCDM Hub GTO Manager
author: Noah Hermann
description: Comprehensive GTO management tool for LCDM Hub - handles schema creation, data retrieval/modification, instance ingestion, and definition lookup. All GTO operations in one tool.
version: 0.2.0
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Optional, Callable, Any, List, Dict, Type

import itertools
import requests
from pydantic import BaseModel, Field, create_model, ValidationError

logger = logging.getLogger(__name__)


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

    async def get_gto_data(
        self,
        gto_id: str,
        count: int = -1,
        __event_emitter__: Optional[Callable[[dict], Any]] = None,
    ) -> str:
        """
        Retrieves data from the LCDM Hub for a specific GTO.

        Args:
            gto_id (str): The GTO identifier to retrieve data for
            count (int): Number of instances to return. -1 for all instances, 1-n for specific count

        Returns:
            str: JSON formatted data for frontend display or error message
        """
        if count == 0:
            return f"Error: Count muss größer als 0 sein. Verwenden Sie -1 für alle Instanzen oder eine positive ganze Zahl."

        if not self.valves.LCDM_HUB_TOKEN:
            error_msg = "Das LCDM Hub Token ist nicht konfiguriert. Bitte hinterlegen Sie ihn in den Einstellungen."
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": error_msg, "done": True}})
            return f"Error: {error_msg}"

        try:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Lade Daten für GTO '{gto_id}'...",
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

            headers = {
                "Authorization": f"Bearer {self.valves.LCDM_HUB_TOKEN}",
                "Accept": "application/json",
            }

            data_url = f"{self.valves.LCDM_HUB_BASE_URL}data/{gto_id}"
            response = requests.get(
                data_url,
                headers=headers,
                timeout=self.valves.timeout_seconds,
            )

            if response.status_code == 200:
                raw_data = response.json()

                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": "Bereite Daten für Anzeige vor...",
                                "done": False,
                            },
                        }
                    )

                formatted_data = self._format_data_for_display(raw_data, gto_schema, count)

                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": f"Erfolgreich {len(formatted_data)} Einträge geladen.",
                                "done": True,
                            },
                        }
                    )

                return json.dumps(
                    {
                        "success": True,
                        "gto_id": gto_id,
                        "gto_name": gto_schema.get("name", gto_id),
                        "data": formatted_data,
                        "schema": self._extract_display_schema(gto_schema),
                    },
                    indent=2,
                )

            else:
                error_msg = f"Fehler beim Laden der Daten: Status {response.status_code}"
                if __event_emitter__:
                    await __event_emitter__({"type": "status", "data": {"description": error_msg, "done": True}})
                return f"Error: {error_msg} - {response.text}"

        except requests.exceptions.Timeout:
            error_msg = f"Anfrage timeout nach {self.valves.timeout_seconds} Sekunden."
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": error_msg, "done": True}})
            return f"Timeout Error: {error_msg}"

        except requests.exceptions.ConnectionError:
            error_msg = "Verbindung zur LCDM Hub API fehlgeschlagen."
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": error_msg, "done": True}})
            return f"Connection Error: {error_msg}"

        except Exception as e:
            error_msg = f"Unerwarteter Fehler: {str(e)}"
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": error_msg, "done": True}})
            return f"Error: {error_msg}"

    async def save_gto_data(
        self,
        gto_id: str,
        data: List[Dict],
        __event_emitter__: Optional[Callable[[dict], Any]] = None,
    ) -> str:
        """
        Saves modified data back to the LCDM Hub.

        Args:
            gto_id (str): The GTO identifier
            data (List[Dict]): List of modified data entries to save

        Returns:
            str: Success or error message
        """
        if not self.valves.LCDM_HUB_TOKEN:
            error_msg = "Das LCDM Hub Token ist nicht konfiguriert. Bitte hinterlegen Sie ihn in den Einstellungen."
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": error_msg, "done": True}})
            return f"Error: {error_msg}"

        if not data:
            error_msg = "Keine Daten zum Speichern bereitgestellt."
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": error_msg, "done": True}})
            return f"Error: {error_msg}"

        try:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Validiere und transformiere {len(data)} Einträge...",
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

            validation_errors = self._validate_data_against_schema(data, gto_schema)
            if validation_errors:
                error_msg = f"Validierungsfehler: {'; '.join(validation_errors)}"
                if __event_emitter__:
                    await __event_emitter__({"type": "status", "data": {"description": error_msg, "done": True}})
                return f"Validation Error: {error_msg}"

            hub_formatted_data = self._transform_data_for_hub(data, gto_schema)

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Speichere Daten im LCDM Hub...",
                            "done": False,
                        },
                    }
                )

            headers = {
                "Authorization": f"Bearer {self.valves.LCDM_HUB_TOKEN}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

            save_url = f"{self.valves.LCDM_HUB_BASE_URL}{gto_id}/aihub-data"
            response = requests.put(
                save_url,
                json=hub_formatted_data,
                headers=headers,
                timeout=self.valves.timeout_seconds,
            )

            if response.status_code in [200, 201]:
                success_msg = f"Erfolgreich {len(data)} Einträge für GTO '{gto_id}' gespeichert."
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
                error_msg = f"Speichern fehlgeschlagen: Status {response.status_code} - {response.text}"
                if __event_emitter__:
                    await __event_emitter__({"type": "status", "data": {"description": error_msg, "done": True}})
                return f"API Error: {error_msg}"

        except requests.exceptions.Timeout:
            error_msg = f"Anfrage timeout nach {self.valves.timeout_seconds} Sekunden."
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": error_msg, "done": True}})
            return f"Timeout Error: {error_msg}"

        except requests.exceptions.ConnectionError:
            error_msg = "Verbindung zur LCDM Hub API fehlgeschlagen."
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": error_msg, "done": True}})
            return f"Connection Error: {error_msg}"

        except Exception as e:
            error_msg = f"Unerwarteter Fehler beim Speichern: {str(e)}"
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

            # First, check if GTO exists in available names
            response = requests.get(
                f"{self.valves.LCDM_HUB_BASE_URL}availablenames",
                headers=headers,
                timeout=self.valves.timeout_seconds,
            )

            if response.status_code != 200:
                return None

            names = response.json()
            available_gtos = [key for key, _ in names]
            if gto_id not in available_gtos:
                return None

            # Get the schema
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

    def _format_data_for_display(self, raw_data: List[Dict], gto_schema: Dict, count: int = -1) -> Dict:
        """
        Formats raw Hub data for frontend display.
        Only includes essential fields for readability.

        Args:
            raw_data: Raw data from the Hub
            gto_schema: GTO schema definition
            count: Number of instances to return (-1 for all, 0-n for specific count)
        """
        if not raw_data:
            return []

        # First, aggregate raw data by objId
        instances_by_id = {}
        gto_type = raw_data[0].get("gtoTyp", "") if raw_data else ""

        for item in raw_data:
            if count > 0 and len(instances_by_id) > count:
                break

            obj_id = item.get("objId")
            if obj_id not in instances_by_id:
                instances_by_id[obj_id] = {}

            key_id = item.get("keyId")
            manual_value = item.get("manualValue", item.get("sourceValue", ""))
            instances_by_id[obj_id][key_id] = manual_value

        if count > 0:
            return dict(itertools.islice(instances_by_id.items(), count))

        return instances_by_id

    def _extract_display_schema(self, gto_schema: Dict) -> Dict:
        """
        Extracts essential schema information for frontend display.
        """
        attribute_definitions = gto_schema.get("gtoAttributeDefinitions", {})
        display_schema = {"gto_name": gto_schema.get("name", ""), "attributes": {}}

        for attr_key, attr_def in attribute_definitions.items():
            field_name = attr_def.get("key", attr_key)
            display_schema["attributes"][field_name] = {
                "type": attr_def.get("valueType", "string"),
                "mandatory": attr_def.get("mandatory", False),
                "unit": attr_def.get("unitOfMeasurement", ""),
            }

        return display_schema

    def _validate_data_against_schema(self, data: List[Dict], gto_schema: Dict) -> List[str]:
        """
        Validates data entries against the GTO schema.
        Returns list of validation error messages.
        """
        errors = []
        attribute_definitions = gto_schema.get("gtoAttributeDefinitions", {})

        for i, entry in enumerate(data):
            for attr_key, attr_def in attribute_definitions.items():
                field_name = attr_def.get("key", attr_key)
                is_mandatory = attr_def.get("mandatory", False)

                if is_mandatory and (field_name not in entry or not entry[field_name]):
                    errors.append(f"Eintrag {i+1}: Pflichtfeld '{field_name}' fehlt oder ist leer")

                if field_name in entry and entry[field_name]:
                    value_type = attr_def.get("valueType", "string")
                    value = entry[field_name]

                    try:
                        if value_type == "integer" and not isinstance(value, int):
                            int(value)
                        elif value_type == "float" and not isinstance(value, float):
                            float(value)
                        elif value_type == "boolean" and not isinstance(value, bool):
                            if str(value).lower() not in ["true", "false", "1", "0"]:
                                raise ValueError()
                    except (ValueError, TypeError):
                        errors.append(
                            f"Eintrag {i+1}: Feld '{field_name}' hat falschen Datentyp (erwartet: {value_type})"
                        )

        return errors

    def _transform_data_for_hub(self, data: List[Dict], gto_schema: Dict) -> List[Dict]:
        """
        Transforms display data back to Hub format for saving.
        """
        hub_data = []
        attribute_definitions = gto_schema.get("gtoAttributeDefinitions", {})
        gto_id = gto_schema.get("id")
        gto_name = gto_schema.get("name", "")

        for entry in data:
            obj_id = entry.get("objId", "")

            for attr_key, attr_def in attribute_definitions.items():
                field_name = attr_def.get("key", attr_key)
                value = entry.get(field_name, "")

                hub_entry = {
                    "id": 0,
                    "gtoTyp": gto_name,
                    "objId": obj_id,
                    "keyId": field_name,
                    "sourceValue": value,
                    "targetValue": "",
                    "manualValue": value,
                    "gtoId": gto_id,
                    "manuallyModified": True,
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

    async def save_gto_schema(
        self,
        gto_data: dict,
        __event_emitter__: Optional[Callable[[dict], Any]] = None,
    ) -> str:
        """
        Creates a GTO (Generic Transfer Object) schema and saves it to the LCDM Hub.

        Args:
            gto_data (dict): Dictionary containing GTO definition with the structure:
                {
                    "name": "ObjectTypeName",
                    "idguid": "unique-identifier-string",
                    "gtoAttributeDefinitions": {
                        "attribute_key": {
                            "key": "AttributeName",
                            "valueType": "string|int|float|boolean",
                            "unitOfMeasurement": "unit",
                            ...
                        }
                    }
                }

        Returns:
            str: Success or error message
        """
        if not self.valves.LCDM_HUB_TOKEN:
            error_msg = "Das LCDM Hub Token ist nicht konfiguriert. Bitte hinterlegen Sie ihn in den Einstellungen."
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": error_msg, "done": True}})
            return f"Error: {error_msg}"

        try:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "GTO Datenstruktur wird validiert...",
                            "done": False,
                        },
                    }
                )

            try:
                gto = self._validate_gto_schema(gto_data)
                gto = self._rekey_gto_definitions(gto)

            except Exception as validation_error:
                error_msg = f"GTO Validierung fehlgeschlagen: {str(validation_error)}"
                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {"description": error_msg, "done": True},
                        }
                    )
                return f"Validierungsfehler: {error_msg}"

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Validierung erfolgreich. Bereite API-Anfrage vor...",
                            "done": False,
                        },
                    }
                )

            headers = {
                "Authorization": f"Bearer {self.valves.LCDM_HUB_TOKEN}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Sende GTO '{gto['name']}' an den LCDM Hub...",
                            "done": False,
                        },
                    }
                )

            response = requests.post(
                self.valves.LCDM_HUB_BASE_URL,
                json=gto,
                headers=headers,
                timeout=self.valves.timeout_seconds,
            )

            if response.status_code in [200, 201]:
                success_msg = f"GTO '{gto['name']}' erfolgreich im LCDM Hub erstellt."

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
                error_msg = f"API Anfrage fehlgeschlagen mit Status {response.status_code}: {response.text}"
                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": f"Anfrage fehlgeschlagen: {response.status_code}",
                                "done": True,
                            },
                        }
                    )
                return f"API Fehler: {error_msg}"

        except requests.exceptions.Timeout:
            error_msg = f"Anfrage timeout nach {self.valves.timeout_seconds} Sekunden."
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": error_msg, "done": True}})
            return f"Timeout Fehler: {error_msg}"

        except requests.exceptions.ConnectionError:
            error_msg = "Verbindung zur LCDM Hub API fehlgeschlagen."
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": error_msg, "done": True}})
            return f"Verbindungsfehler: {error_msg}"

        except Exception as e:
            error_msg = f"Unerwarteter Fehler aufgetreten: {str(e)}"
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": error_msg, "done": True}})
            return f"Fehler: {error_msg}"

    async def ingest_gto_instances(
        self,
        gto_id: str,
        instances_data: List[Dict],
        __event_emitter__: Optional[Callable[[dict], Any]] = None,
    ) -> str:
        """
        Validates and ingests GTO instances into the LCDM Hub.

        Args:
            gto_id (str): The GTO type identifier.
            instances_data (List[Dict]): List of GTO instances to validate and ingest.

        Returns:
            str: Result message indicating success or failure.
        """
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
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {"description": error_msg, "done": True},
                        }
                    )
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
                        {
                            "type": "status",
                            "data": {
                                "description": "Validierung fehlgeschlagen",
                                "done": True,
                            },
                        }
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

            hub_data = self._transform_instances_to_hub_format(validated_instances, gto_schema, gto_id)

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Speichere {int(len(hub_data)/len(gto_schema['gtoAttributeDefinitions']))} Einträge im LCDM Hub...",
                            "done": False,
                        },
                    }
                )

            result = await self._save_instances_to_hub(hub_data, gto_id)

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

    async def get_gto_definition(
        self,
        gto_id: str,
        __event_emitter__: Optional[Callable[[dict], Any]] = None,
    ) -> str:
        """
        Retrieves a GTO definition string and returns it for use in the chat.

        Args:
            gto_id (str): The GTO type identifier.

        Returns:
            str: Result message with GTO definition or failure message.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "GTO Schema wird gesucht...",
                        "done": False,
                    },
                }
            )

        try:
            headers = {
                "Authorization": f"Bearer {self.valves.LCDM_HUB_TOKEN}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

            response = requests.get(
                f"{self.valves.LCDM_HUB_BASE_URL}availablenames",
                headers=headers,
            )

            names = response.json()
            keys = [key for key, value in names]
            if gto_id in keys:
                r = requests.get(
                    f"{self.valves.LCDM_HUB_BASE_URL}{gto_id}",
                    headers=headers,
                    timeout=10,
                )

                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": "GTO Schema gefunden!",
                                "done": True,
                            },
                        }
                    )

                return f"<GTO_DEFINITION>{r.json()}</GTO_DEFINITION>"

            else:
                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": "GTO ID ist ungültig!",
                                "done": True,
                            },
                        }
                    )

                return "GTO ID ist ungültig!"

        except Exception as e:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Ein Fehler ist aufgetreten: {e}",
                            "done": True,
                        },
                    }
                )
            return f"Ein Fehler ist aufgetreten: {e}"

    # Helper Methods for GTO Schema Creation

    def _validate_gto_schema(self, gto_data: dict) -> dict:
        """Validates GTO schema structure."""
        required_fields = ["name", "idguid", "gtoAttributeDefinitions"]
        for field in required_fields:
            if field not in gto_data:
                raise ValueError(f"Required field '{field}' missing from GTO data")

        # Set defaults
        gto_data["id"] = 0

        # Validate attributes
        for attr_key, attr_def in gto_data["gtoAttributeDefinitions"].items():
            attr_def["id"] = 0
            if "key" not in attr_def:
                raise ValueError(f"Attribute '{attr_key}' missing 'key' field")
            if "valueType" not in attr_def:
                raise ValueError(f"Attribute '{attr_key}' missing 'valueType' field")

            # Set defaults for optional fields
            attr_def.setdefault("dataType", "MANUAL_VALUE_TYPE")
            attr_def.setdefault("unitOfMeasurement", "")
            attr_def.setdefault("leadOfData", "SOURCE")
            attr_def.setdefault("reportRelevant", False)
            attr_def.setdefault("gtoAttributeDefinitionsKey", None)
            attr_def.setdefault("mandatory", False)
            attr_def.setdefault("relationFinderActive", None)
            attr_def.setdefault("relatedGtoId", 0)
            attr_def.setdefault("relatedGtoAttributeKey", None)
            attr_def.setdefault("reportFields", {})
            attr_def.setdefault("spellingValues", [])

        return gto_data

    def _rekey_gto_definitions(self, gto: dict) -> dict:
        """Rekeys GTO attribute definitions to follow the proper numbering pattern."""
        definitions = list(gto["gtoAttributeDefinitions"].values())
        new_definitions = {}

        for i, definition in enumerate(definitions):
            new_key = f"{(i + 1) * 5:04d}"  # 0005, 0010, 0015, etc.
            definition["gtoAttributeDefinitionsKey"] = new_key
            new_definitions[new_key] = definition

        gto["gtoAttributeDefinitions"] = new_definitions
        return gto

    # Helper Methods for Instance Ingestion

    def _create_dynamic_model(self, gto_schema: Dict) -> Type[BaseModel]:
        """Creates a dynamic Pydantic model from GTO schema."""
        fields = {}
        attribute_definitions = gto_schema.get("gtoAttributeDefinitions", {})

        for attr_key, attr_def in attribute_definitions.items():
            field_name = attr_def.get("key", attr_key)
            data_type = attr_def.get("dataType", "string")
            is_mandatory = attr_def.get("mandatory", False)

            if data_type == "integer" or attr_def.get("valueType") == "integer":
                python_type = int
            elif data_type == "float" or attr_def.get("valueType") == "float":
                python_type = float
            elif data_type == "boolean" or attr_def.get("valueType") == "boolean":
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
        data_string = json.dumps(instance_data, sort_keys=True) + gto_type + str(datetime.now().timestamp())
        hash_object = hashlib.md5(data_string.encode())
        return hash_object.hexdigest()[:8].upper()

    def _transform_instances_to_hub_format(
        self, validated_instances: List[BaseModel], gto_schema: Dict, gto_type: str
    ) -> List[List[Dict]]:
        """Transforms validated instances to LCDM Hub format."""
        hub_data = []
        gto_id = gto_schema.get("id")
        attribute_definitions = gto_schema.get("gtoAttributeDefinitions", {})

        for instance in validated_instances:
            instance_dict = instance.model_dump()
            obj_id = self._generate_unique_obj_id(instance_dict, gto_type)

            tmp_instances = []
            for attr_key, attr_def in attribute_definitions.items():
                field_name = attr_def.get("key")
                source_value = instance_dict.get(field_name, "")

                hub_entry = {
                    "id": 0,
                    "gtoTyp": gto_type,
                    "objId": obj_id,
                    "keyId": field_name,
                    "sourceValue": (source_value if source_value is not None else ""),
                    "targetValue": "",
                    "manualValue": (source_value if source_value is not None else ""),
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

                tmp_instances.append(hub_entry)

            hub_data.append(tmp_instances)

        return hub_data

    async def _save_instances_to_hub(self, hub_data: List[List[Dict]], gto_id: str) -> str:
        """Saves transformed instance data to LCDM Hub."""
        try:
            headers = {
                "Authorization": f"Bearer {self.valves.LCDM_HUB_TOKEN}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

            for data in hub_data:
                response = requests.post(
                    f"{self.valves.LCDM_HUB_BASE_URL}{gto_id}/aihub-data",
                    json=data,
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
