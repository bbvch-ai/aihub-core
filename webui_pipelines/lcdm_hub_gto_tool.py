"""
title: LCDM Hub GTO Manager
author: Noah Hermann
version: 0.1.0
"""

import os
import requests
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Callable, Any, List, Dict


class GtoAttributeDefinition(BaseModel):
    id: int = Field(..., description="Unique identifier of the GTO attribute")
    key: str = Field(..., description="The name of the GTO attribute")
    dataType: Optional[str] = Field(
        None, description="The datatype for the attributes value"
    )
    valueType: str = Field(..., description="")
    unitOfMeasurement: Optional[str] = Field(
        None, description="Mostly used for integers"
    )
    leadOfData: Optional[str] = Field(None, description="")
    reportRelevant: Optional[bool] = Field(None, description="")
    gtoAttributeDefinitionsKey: Optional[str] = Field(None, description="")
    mandatory: Optional[bool] = Field(None, description="")
    relationFinderActive: Optional[bool] = Field(None, description="")
    relatedGtoId: Optional[int] = Field(None, description="")
    relatedGtoAttributeKey: Optional[str] = Field(None, description="")
    reportFields: Optional[Dict] = Field(None, description="")
    spellingValues: Optional[List] = Field(None, description="")


class GTO(BaseModel):
    id: int = Field(..., description="Unique identifier of the GTO")
    name: str = Field(..., description="Name of the GTO")
    idguid: str = Field(..., description="")
    gtoAttributeDefinitions: Dict[str, GtoAttributeDefinition] = Field(
        ..., description="All the attributes of the GTO"
    )

    class Config:
        schema_extra = {
            "example": {
                "id": 7220792,
                "name": "Door",
                "idguid": "string",
                "gtoAttributeDefinitions": {
                    "0010": {
                        "id": 7221698,
                        "key": "Material",
                        "dataType": "MANUAL_VALUE_TYPE",
                        "valueType": "string",
                        "unitOfMeasurement": "",
                        "leadOfData": "SOURCE",
                        "reportRelevant": False,
                        "gtoAttributeDefinitionsKey": "string",
                        "mandatory": False,
                        "relationFinderActive": None,
                        "relatedGtoId": 0,
                        "relatedGtoAttributeKey": None,
                        "reportFields": {},
                        "spellingValues": [],
                    }
                },
            }
        }


class Tools:
    class Valves(BaseModel):
        LCDM_HUB_BASE_URL: str = Field(
            default="https://dev.swisslcdmhub.bbv.ch/restapi/1.0/gto",
            description="URL for accessing LCDM Hub API endpoints.",
        )
        LCDM_HUB_TOKEN: str = Field(
            default="",
            description="Token to authenticate requests to the LCDM Hub API.",
        )
        timeout_seconds: int = Field(
            default=30, description="Request timeout in seconds"
        )

    def __init__(self):
        self.valves = self.Valves()

    async def create_GTO(
        self,
        gto_data: dict,
        __event_emitter__: Optional[Callable[[dict], Any]] = None,
    ) -> str:
        """
        Erstellt ein GTO mit Attributen und speichert dieses im LCDM Hub.

        :param gto_data: Dictionary welches GTO Definitionen enthält mit required fields (id, name, idguid, gtoAttributeDefinitions)
        :return: Erfolg-/Fehlermeldung mit Details
        """

        if not self.valves.LCDM_HUB_TOKEN:
            error_msg = "Das LCDM Hub Token ist nicht konfiguriert. Bitte hinterlegen Sie ihn in den Einstellungen."
            if __event_emitter__:
                await __event_emitter__(
                    {"type": "status", "data": {"description": error_msg, "done": True}}
                )
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
                gto = GTO.model_validate(gto_data)
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
                            "description": f"Sende GTO '{gto.name}' an den LCDM Hub...",
                            "done": False,
                        },
                    }
                )

            response = requests.post(
                self.valves.LCDM_HUB_BASE_URL,
                json=gto.model_dump(),
                headers=headers,
                timeout=self.valves.timeout_seconds,
            )

            if response.status_code == 200 or response.status_code == 201:
                success_msg = (
                    f"GTO '{gto.name}' (ID: {gto.id}) erfolgreich im LCDM Hub erstellt."
                )

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
                            "data": {
                                "content": f"✅ **Erfolg!** {success_msg}\n\n**Antwort:** {response.text if response.text else 'Erfolgreich erstellt.'}"
                            },
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
                await __event_emitter__(
                    {"type": "status", "data": {"description": error_msg, "done": True}}
                )
            return f"Timeout Fehler: {error_msg}"

        except requests.exceptions.ConnectionError:
            error_msg = "Verbindung zur LCDM Hub API fehlgeschlagen."
            if __event_emitter__:
                await __event_emitter__(
                    {"type": "status", "data": {"description": error_msg, "done": True}}
                )
            return f"Verbindungsfehler: {error_msg}"

        except Exception as e:
            error_msg = f"Unerwarteter Fehler aufgetreten: {str(e)}"
            if __event_emitter__:
                await __event_emitter__(
                    {"type": "status", "data": {"description": error_msg, "done": True}}
                )
            return f"Fehler: {error_msg}"
