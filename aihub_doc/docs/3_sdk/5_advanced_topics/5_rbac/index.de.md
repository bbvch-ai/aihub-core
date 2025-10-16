---
title: RBAC-Implementierungsleitfaden
index: 5
source_sha: "dac23d6b3179b18601a36689af9607dc30eaea3252e03f01a19315bae2b11810"
---

# RBAC-Implementierungsleitfaden :shield: :gear:

::: info **Übersicht für SDK-Entwickler**
Dieser Leitfaden behandelt die Implementierung von rollenbasierter Zugriffskontrolle (RBAC) in Ihren AI-Hub-Anwendungen,
einschließlich des Schutzes von API-Endpunkten, Zugriffskontrollen für Agenten und benutzerdefinierter
Berechtigungsprüfung. Erfahren Sie, wie Sie das ausgeklügelte Berechtigungssystem des AI-Hubs nutzen können, um Ihre
benutzerdefinierten Agenten, Prozesse und Services zu sichern.
:::

## Zugriffsschutz auf Controller-Ebene

### Grundlegender Endpunktschutz

Der AI-Hub bietet ein umfassendes Framework zum Schutz von API-Endpunkten mittels der Basisklasse `Controller` und
ihrer Berechtigungsprüfungsmechanismen.

**Einfache Berechtigungsprüfung:**

```python
from aihub_lib.routes.Controller import Controller
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from fastapi import Security
from typing import Annotated

class MyController(Controller):
    def __init__(self, *, auth: AuthHandler, route: str = "/my-service"):
        super().__init__(auth=auth, route=route)

    def protected_endpoint(self, route: str = "/protected") -> "MyController":
        @self.router.get(route, tags=self.tags)
        async def protected_endpoint(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.service.my_service"))]
        ) -> dict:
            """Nur Benutzer mit Zugriff auf my_service können auf diesen Endpunkt zugreifen."""
            return {"message": "Access granted", "user_id": user.id}
        return self
```

### Dynamische Berechtigungsauflösung

Der AI-Hub unterstützt die dynamische Berechtigungsprüfung, bei der Pfadparameter automatisch in Berechtigungsvorlagen
eingesetzt werden:

**Pfadparameter-Integration:**

```python
def agent_specific_endpoint(self, route: str = "/{agent_class}/{agent_id}") -> "MyController":
    @self.router.get(route, tags=self.tags)
    async def agent_specific_endpoint(
        agent_class: str,
        agent_id: str,
        user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.agent.{agent_class}.{agent_id}"))]
    ) -> dict:
        """Die Berechtigung wird dynamisch als aihub.user.agent.customer_service.chatbot_v1 konstruiert"""
        return {
            "message": "Access granted to specific agent",
            "agent_class": agent_class,
            "agent_id": agent_id,
            "user": user.email
        }
    return self
```

### Mehrstufige Berechtigungsprüfung

Das Controller-Framework implementiert eine dreistufige Autorisierung, die an Ihre spezifischen Anforderungen
angepasst werden kann:

**Zugriffskontrolle auf Service-Ebene:**

```python
class SecureController(Controller):
    def __init__(self, *, auth: AuthHandler, route: str = "/secure",
                 additionally_required_permission: str | None = None):
        # Die additionally_required_permission fügt eine zusätzliche Sicherheitsebene hinzu
        super().__init__(
            auth=auth,
            route=route,
            additionally_required_permission="aihub.admin.special_access"
        )

    def admin_only_endpoint(self, route: str = "/admin") -> "SecureController":
        @self.router.post(route, tags=self.tags)
        async def admin_only_endpoint(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.service.secure"))]
        ) -> dict:
            """
            Benutzer benötigen beides:
            1. aihub.admin.special_access (von additionally_required_permission)
            2. aihub.admin.service.secure (von der Endpunktberechtigung)
            """
            return {"message": "Admin access granted"}
        return self
```

## Implementierung der Zugriffskontrolle auf Service-Ebene

### Benutzerdefinierte Service-Integration

Beim Erstellen benutzerdefinierter Services, die in den AI-Hub integriert werden, implementieren Sie eine
ordnungsgemäße Zugriffskontrolle über die etablierten Muster:

**Service-Klassenimplementierung:**

```python
from aihub_lib.auth.access.AccessChecker import AccessChecker
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from fastapi import HTTPException

class MyCustomService:
    @staticmethod
    async def get_user_data(user: UserIdentity, resource_id: str) -> dict:
        """Service-Methode mit integrierter Zugriffsprüfung."""
        access_checker = AccessChecker.from_user(user)

        # Prüfen, ob der Benutzer Zugriff auf diese spezifische Ressource hat
        if not access_checker.has_access(f"aihub.user.service.my_custom.{resource_id}"):
            raise HTTPException(
                status_code=403,
                detail=f"Access denied to resource {resource_id}"
            )

        # Mit der Geschäftslogik fortfahren
        return await fetch_user_specific_data(user.id, resource_id)

    @staticmethod
    async def get_admin_overview(user: UserIdentity) -> dict:
        """Administrative Funktion mit Zugriffsebenenprüfung."""
        access_checker = AccessChecker.from_user(user)

        # Prüfen auf Administratorzugriff
        access_level = access_checker.access_level("aihub.admin.service.my_custom")
        if access_level == AccessLevel.ACCESS_DENIED:
            raise HTTPException(status_code=403, detail="Administrative access required")

        # Unterschiedliche Daten je nach Zugriffsebene zurückgeben
        if access_level == AccessLevel.ACCESS_ADMIN:
            return await fetch_comprehensive_admin_data()
        else:
            return await fetch_limited_admin_data()
```

### Dynamische Zugriffsprüfung

Implementieren Sie eine dynamische Zugriffsprüfung für Szenarien, in denen Berechtigungen basierend auf
Laufzeitbedingungen ausgewertet werden müssen:

**Laufzeit-Berechtigungsprüfung:**

```python
from aihub_lib.auth.access.AccessChecker import AccessChecker
from aihub_lib.auth.access.AccessLevel import AccessLevel

class DynamicAccessService:
    @staticmethod
    async def get_agent_list(user: UserIdentity, agent_type: str | None = None) -> list[dict]:
        """Gibt eine gefilterte Agentenliste basierend auf Benutzerberechtigungen zurück."""
        access_checker = AccessChecker.from_user(user)
        available_agents = await fetch_all_agents()

        filtered_agents = []
        for agent in available_agents:
            # Zugriff auf jeden Agenten einzeln prüfen
            if access_checker.has_access_to_agent(agent.agent_class, agent.agent_id):
                # Zugriffsebeneninformationen hinzufügen
                access_level = access_checker.access_level_for_agent(
                    agent.agent_class, agent.agent_id
                )
                filtered_agents.append({
                    "agent_id": agent.agent_id,
                    "agent_class": agent.agent_class,
                    "access_level": access_level.value,
                    "can_configure": access_level == AccessLevel.ACCESS_ADMIN
                })

        return filtered_agents

    @staticmethod
    async def check_bulk_permissions(user: UserIdentity, resources: list[str]) -> dict[str, bool]:
        """Überprüft effizient Berechtigungen für mehrere Ressourcen."""
        access_checker = AccessChecker.from_user(user)
        results = {}

        for resource in resources:
            results[resource] = access_checker.has_access(resource)

        return results
```

## Implementierung der Agenten-Zugriffskontrolle

### Agentenspezifische Berechtigungsprüfung

Beim Erstellen benutzerdefinierter Agenten implementieren Sie geeignete Zugriffskontrollen, um sicherzustellen, dass
nur autorisierte Benutzer mit Ihren Agenten interagieren können:

**Agenten-Zugriffsintegration:**

```python
from aihub_lib.auth.access.AccessChecker import AccessChecker
from aihub_lib.auth.identity.UserIdentity import UserIdentity

class CustomAgent:
    def __init__(self, agent_class: str, agent_id: str):
        self.agent_class = agent_class
        self.agent_id = agent_id

    async def process_user_request(self, user: UserIdentity, request: str) -> str:
        """Verarbeitet Anfragen mit geeigneter Zugriffskontrolle."""
        access_checker = AccessChecker.from_user(user)

        # Überprüfen, ob der Benutzer Zugriff auf diesen spezifischen Agenten hat
        if not access_checker.has_access_to_agent(self.agent_class, self.agent_id):
            raise HTTPException(
                status_code=403,
                detail=f"Access denied to agent {self.agent_class}/{self.agent_id}"
            )

        # Zugriffsebene prüfen, um die Detailtiefe der Antwort zu bestimmen
        access_level = access_checker.access_level_for_agent(self.agent_class, self.agent_id)

        if access_level == AccessLevel.ACCESS_ADMIN:
            # Detaillierte Antwort für Administratoren bereitstellen
            return await self.process_admin_request(request, user)
        else:
            # Standard-Benutzerantwort
            return await self.process_user_request_internal(request, user)

    async def get_agent_configuration(self, user: UserIdentity) -> dict:
        """Gibt die Agentenkonfiguration basierend auf der Benutzerzugriffsebene zurück."""
        access_checker = AccessChecker.from_user(user)
        access_level = access_checker.access_level_for_agent(self.agent_class, self.agent_id)

        if access_level == AccessLevel.ACCESS_DENIED:
            raise HTTPException(status_code=403, detail="Agent access denied")
        elif access_level == AccessLevel.ACCESS_ADMIN:
            return await self.get_full_configuration()
        else:
            return await self.get_user_configuration()
```

### Agenten-Entdeckung mit Zugriffskontrolle

Implementieren Sie eine Agenten-Entdeckung, die Benutzerberechtigungen berücksichtigt:

**Gefilterte Agenten-Entdeckung:**

```python
class AgentDiscoveryService:
    @staticmethod
    async def discover_available_agents(user: UserIdentity) -> list[dict]:
        """Gibt nur Agenten zurück, auf die der Benutzer Zugriff hat."""
        access_checker = AccessChecker.from_user(user)
        all_agents = await fetch_registered_agents()

        accessible_agents = []
        for agent_info in all_agents:
            if access_checker.has_access_to_agent(
                agent_info.agent_class,
                agent_info.agent_id
            ):
                # Zugriffsebene in die Antwort aufnehmen
                access_level = access_checker.access_level_for_agent(
                    agent_info.agent_class,
                    agent_info.agent_id
                )

                accessible_agents.append({
                    "agent_class": agent_info.agent_class,
                    "agent_id": agent_info.agent_id,
                    "display_name": agent_info.display_name,
                    "description": agent_info.description,
                    "access_level": access_level.value,
                    "can_configure": access_level == AccessLevel.ACCESS_ADMIN
                })

        return accessible_agents

    @staticmethod
    async def check_agent_access(user: UserIdentity, agent_class: str, agent_id: str) -> dict:
        """Überprüft den Zugriff auf einen spezifischen Agenten mit detaillierten Informationen."""
        access_checker = AccessChecker.from_user(user)

        return {
            "has_access": access_checker.has_access_to_agent(agent_class, agent_id),
            "access_level": access_checker.access_level_for_agent(agent_class, agent_id).value,
            "can_view": access_checker.has_access_to_agent(agent_class, agent_id),
            "can_configure": access_checker.access_level_for_agent(agent_class, agent_id) == AccessLevel.ACCESS_ADMIN,
            "has_class_access": access_checker.has_access_to_agent_class(agent_class)
        }
```

## Implementierung der Prozess-Zugriffskontrolle

### Berechtigungsverwaltung auf Prozessebene

Beim Implementieren benutzerdefinierter Prozesse integrieren Sie geeignete Zugriffskontrollen, um eine sichere
Prozessausführung zu gewährleisten:

**Prozess-Zugriffsintegration:**

```python
from aihub_lib.auth.access.AccessChecker import AccessChecker

class CustomProcess:
    def __init__(self, process_class: str, process_id: str):
        self.process_class = process_class
        self.process_id = process_id

    async def start_process(self, user: UserIdentity, process_data: dict) -> str:
        """Startet den Prozess mit geeigneter Zugriffsprüfung."""
        access_checker = AccessChecker.from_user(user)

        # Prüfen, ob der Benutzer diesen spezifischen Prozess starten kann
        if not access_checker.has_access_to_process(self.process_class, self.process_id):
            raise HTTPException(
                status_code=403,
                detail=f"Access denied to process {self.process_class}/{self.process_id}"
            )

        # Zugriffsebene für die Prozesskonfiguration prüfen
        access_level = access_checker.access_level_for_process(self.process_class, self.process_id)

        if access_level == AccessLevel.ACCESS_ADMIN:
            # Admin-Benutzer können Standard-Prozesseinstellungen überschreiben
            return await self.start_process_with_overrides(process_data, user)
        else:
            # Standard-Benutzer verwenden die Standard-Prozesskonfiguration
            return await self.start_standard_process(process_data, user)

    async def get_process_status(self, user: UserIdentity, execution_id: str) -> dict:
        """Ruft den Prozessstatus mit entsprechendem Detaillierungsgrad ab."""
        access_checker = AccessChecker.from_user(user)

        # Zugriff auf den Prozesstyp überprüfen
        if not access_checker.has_access_to_process(self.process_class, self.process_id):
            raise HTTPException(status_code=403, detail="Process access denied")

        execution_info = await fetch_execution_info(execution_id)

        # Prüfen, ob der Benutzer die Ausführungen anderer Benutzer anzeigen kann
        if execution_info.user_id != user.id:
            access_level = access_checker.access_level_for_process(self.process_class, self.process_id)
            if access_level != AccessLevel.ACCESS_ADMIN:
                raise HTTPException(status_code=403, detail="Cannot view other users' process executions")

        return await build_process_status_response(execution_info, user)
```

## Erweiterte Berechtigungsmuster

### Implementierung von Wildcard-Berechtigungen

Verstehen und implementieren Sie die Wildcard-Berechtigungsprüfung für eine flexible Zugriffskontrolle:

**Verwendung von Wildcard-Mustern:**

```python
class AdvancedAccessService:
    @staticmethod
    async def check_wildcard_access(user: UserIdentity) -> dict:
        """Demonstriert verschiedene Wildcard-Berechtigungsmuster."""
        access_checker = AccessChecker.from_user(user)

        return {
            # Spezifischer Ressourcenzugriff
            "specific_agent": access_checker.has_access("aihub.user.agent.customer_service.chatbot_v1"),

            # Ein-Ebenen-Wildcard (jede Instanz von customer_service Agenten)
            "customer_service_agents": access_checker.has_access("aihub.user.agent.customer_service.*"),

            # Mehr-Ebenen-Wildcard (jeder Agent)
            "any_agent": access_checker.has_access("aihub.user.agent.>"),

            # Wildcards zur Überprüfung von Fähigkeiten
            "has_agent_access": access_checker.has_access("aihub.user.agent.?*"),
            "has_service_access": access_checker.has_access("aihub.user.service.?>"),

            # Überprüfung von Administratorrechten
            "admin_any_service": access_checker.has_access("aihub.admin.service.?>"),
            "admin_specific": access_checker.has_access("aihub.admin.service.roles")
        }

    @staticmethod
    async def get_accessible_resources(user: UserIdentity, resource_type: str) -> list[str]:
        """Gibt eine Liste von Ressourcen zurück, auf die der Benutzer basierend auf Wildcard-Mustern Zugriff hat."""
        access_checker = AccessChecker.from_user(user)
        all_resources = await fetch_resources_by_type(resource_type)

        accessible_resources = []
        for resource in all_resources:
            resource_permission = f"aihub.user.{resource_type}.{resource.category}.{resource.id}"
            if access_checker.has_access(resource_permission):
                accessible_resources.append(resource.id)

        return accessible_resources
```

### Benutzerdefinierte Berechtigungsvalidierung

Implementieren Sie eine benutzerdefinierte Berechtigungsvalidierungslogik für komplexe Szenarien:

**Benutzerdefinierte Validierungslogik:**

```python
class CustomPermissionValidator:
    @staticmethod
    async def validate_complex_access(user: UserIdentity, request_data: dict) -> bool:
        """Implementiert komplexe Berechtigungslogik, die mehrere Prüfungen kombiniert."""
        access_checker = AccessChecker.from_user(user)

        # Mehrere Berechtigungsanforderungen
        required_permissions = [
            "aihub.user.service.data_processing",
            f"aihub.user.knowledge.{request_data.get('knowledge_base')}",
            f"aihub.user.agent.{request_data.get('agent_type')}.?*"
        ]

        # Alle Berechtigungen müssen erfüllt sein
        for permission in required_permissions:
            if not access_checker.has_access(permission):
                return False

        # Zusätzliche Geschäftslogik-Prüfungen
        if request_data.get('sensitive_data', False):
            # Sensible Daten erfordern Administratorzugriff
            if access_checker.access_level("aihub.admin.service.data_processing") == AccessLevel.ACCESS_DENIED:
                return False

        return True

    @staticmethod
    async def get_permission_summary(user: UserIdentity) -> dict:
        """Erzeugt eine umfassende Berechtigungsübersicht für den Benutzer."""
        access_checker = AccessChecker.from_user(user)

        return {
            "user_info": {
                "id": user.id,
                "email": user.email,
                "roles": user.roles
            },
            "access_summary": {
                "total_rules": len(access_checker.access_rules),
                "admin_rules": len(access_checker.admin_access_rules),
                "user_rules": len(access_checker.user_access_rules)
            },
            "capabilities": {
                "can_access_agents": access_checker.has_access("aihub.user.agent.?*"),
                "can_access_processes": access_checker.has_access("aihub.user.process.?*"),
                "can_access_services": access_checker.has_access("aihub.user.service.?*"),
                "has_admin_access": access_checker.has_access("aihub.admin.?>")
            },
            "specific_access": {
                "role_management": access_checker.access_level("aihub.admin.service.roles").value,
                "experiment_service": access_checker.access_level("aihub.user.service.experiments").value
            }
        }
```

## Testen der RBAC-Implementierung

### Unit-Testing der Berechtigungslogik

Implementieren Sie umfassende Tests für Ihre RBAC-Integration:

**Berechtigungs-Testframework:**

```python
import pytest
from aihub_lib.auth.access.AccessChecker import AccessChecker
from aihub_lib.auth.access.AccessLevel import AccessLevel
from aihub_lib.auth.identity.UserIdentity import UserIdentity

class TestRBACImplementation:
    @pytest.fixture
    def test_user(self) -> UserIdentity:
        """Erstellt einen Testbenutzer mit spezifischen Rollen."""
        return UserIdentity(
            id="test_user_123",
            email="test@example.com",
            name="Test User",
            roles=["agent_user", "process_participant"]
        )

    @pytest.fixture
    def admin_user(self) -> UserIdentity:
        """Erstellt einen Admin-Testbenutzer."""
        return UserIdentity(
            id="admin_user_123",
            email="admin@example.com",
            name="Admin User",
            roles=["ai_admin"]
        )

    def test_user_agent_access(self, test_user):
        """Testet den Agenten-Zugriff auf Benutzerebene."""
        access_checker = AccessChecker.from_user(test_user)

        # Spezifischen Agenten-Zugriff testen
        assert access_checker.has_access_to_agent("customer_service", "chatbot_v1")
        assert not access_checker.has_access_to_agent("admin_tools", "user_manager")

        # Zugriffsebenen testen
        access_level = access_checker.access_level_for_agent("customer_service", "chatbot_v1")
        assert access_level == AccessLevel.ACCESS_USER

    def test_admin_privileges(self, admin_user):
        """Testet administrative Zugriffsfähigkeiten."""
        access_checker = AccessChecker.from_user(admin_user)

        # Admin sollte Zugriff auf Verwaltungsdienste haben
        assert access_checker.has_access("aihub.admin.service.roles")
        assert access_checker.access_level("aihub.admin.service.roles") == AccessLevel.ACCESS_ADMIN

        # Admin sollte Benutzerberechtigungen erben
        assert access_checker.has_access("aihub.user.agent.customer_service.chatbot_v1")

    def test_wildcard_permissions(self, test_user):
        """Testet Wildcard-Berechtigungsmuster."""
        access_checker = AccessChecker.from_user(test_user)

        # Verschiedene Wildcard-Muster testen
        assert access_checker.has_access("aihub.user.agent.customer_service.*")
        assert access_checker.has_access("aihub.user.agent.?>")
        assert not access_checker.has_access("aihub.admin.?>")

    @pytest.mark.asyncio
    async def test_service_integration(self, test_user):
        """Testet die Integration des Zugriffs auf Service-Ebene."""
        # Service-Aufruf mit Berechtigungsprüfung simulieren
        service = MyCustomService()

        # Sollte für autorisierte Ressource erfolgreich sein
        result = await service.get_user_data(test_user, "allowed_resource")
        assert result is not None

        # Sollte für nicht autorisierte Ressource fehlschlagen
        with pytest.raises(HTTPException) as exc_info:
            await service.get_user_data(test_user, "forbidden_resource")
        assert exc_info.value.status_code == 403
```

### Integrationstests

Testen Sie die RBAC-Integration mit Ihren API-Endpunkten:

**API-Integrationstests:**

```python
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

class TestRBACAPIIntegration:
    @pytest.fixture
    async def authenticated_client(self):
        """Erstellt einen authentifizierten Test-Client."""
        # Test-Client mit korrekter Authentifizierung einrichten
        auth = TestAuthHandler()  # Ihr Test-Auth-Handler
        runner = ApiTestRunner()
        runner.mount(MyController(auth=auth))

        async with AsyncClient(app=runner.create_app()) as client:
            yield client

    @pytest.mark.asyncio
    async def test_protected_endpoint_access(self, authenticated_client):
        """Testet den Zugriff auf geschützte Endpunkte."""
        # Erfolgreichen Zugriff mit korrekten Berechtigungen testen
        response = await authenticated_client.get("/my-service/protected")
        assert response.status_code == 200

        # Verweigerten Zugriff ohne Berechtigungen testen
        response = await authenticated_client.get("/my-service/admin-only")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_dynamic_permission_resolution(self, authenticated_client):
        """Testet die dynamische Berechtigungsprüfung mit Pfadparametern."""
        # Zugriff auf spezifischen Agenten testen
        response = await authenticated_client.get("/agents/customer_service/chatbot_v1")
        assert response.status_code == 200

        # Verweigerten Zugriff auf eingeschränkten Agenten testen
        response = await authenticated_client.get("/agents/admin_tools/user_manager")
        assert response.status_code == 403
```

## Best Practices für die RBAC-Implementierung

### Sicherheitsaspekte

**Fail-Safe-Standards**: Verweigern Sie den Zugriff immer standardmäßig, wenn Berechtigungsprüfungen unklar sind oder
fehlschlagen.

**Umfassende Protokollierung**: Protokollieren Sie alle Berechtigungsprüfungen und Zugriffsentscheidungen für
Audit- und Sicherheitsüberwachung.

**Konsistente Fehlerbehandlung**: Verwenden Sie konsistente HTTP-Statuscodes und Fehlermeldungen für
Zugriffsverweigerungen.

**Berechtigungsvalidierung**: Validieren Sie Berechtigungsvorlagen und Zugriffsregeln, um Sicherheitslücken zu
verhindern.

### Leistungsoptimierung

**Caching-Strategien**: Implementieren Sie geeignetes Caching für Berechtigungsprüfungen, um die Leistung zu
optimieren.

**Batch-Berechtigungsprüfung**: Verwenden Sie bei der Prüfung mehrerer Berechtigungen nach Möglichkeit
Batch-Operationen.

**Lazy Evaluation**: Führen Sie Berechtigungsprüfungen nur bei Bedarf durch, um die Auswirkungen auf die Leistung zu
minimieren.

### Entwicklungsrichtlinien

**Klare Berechtigungsbenennung**: Verwenden Sie beschreibende und konsistente Konventionen für die Benennung von
Berechtigungen.

**Dokumentation**: Dokumentieren Sie die Berechtigungsanforderungen für alle Endpunkte und Services.

**Testabdeckung**: Stellen Sie eine umfassende Testabdeckung für alle Berechtigungsszenarien sicher.

**Regelmäßige Überprüfungen**: Führen Sie regelmäßige Überprüfungen der Berechtigungsstrukturen und
Zugriffsmuster durch.

Dieser Implementierungsleitfaden bildet die Grundlage für die Integration von RBAC in Ihre AI-Hub-Anwendungen unter
Beibehaltung von Sicherheit, Leistung und Wartbarkeit.
