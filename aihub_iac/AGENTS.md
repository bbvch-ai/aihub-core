# aihub_iac - Infrastructure as Code

**Purpose**: Pulumi-based Azure infrastructure definitions. Deploy AI-Hub to Azure cloud with Terraform-like approach.

## Scope Responsibility

Cloud resource provisioning (Azure). NOT application code. Defines: networks, storage, web apps, containers, managed identities.

## Folder Structure

```
aihub_iac/azure/
├── constants/                 # Resource type constants, role definitions
├── modules/                   # Infrastructure components (by service)
│   ├── agent/                 # Agent container deployment
│   ├── api/                   # API service resources
│   ├── bot/                   # Bot service resources
│   ├── dagster/               # Dagster orchestration
│   ├── nats/                  # NATS messaging
│   ├── network/               # VNet, subnets, NSGs
│   ├── phoenix/               # Phoenix observability
│   ├── stores/                # Storage (Blob, PostgreSQL, Milvus)
│   └── webui/                 # Web UI hosting
├── providers/                 # Service provider abstractions
│   ├── NetworkProvider.py    # Network resource creation
│   ├── IdentityProvider.py   # Managed identity + RBAC
│   └── ...                    # Other providers
├── resources/                 # Common resource definitions
└── settings/                  # Configuration management
    ├── ProjectSettings.py     # Project metadata (env vars)
    ├── ApiConfig.py           # API service config
    └── ...                    # Other configs
```

## Key Concepts

**Component-Based Design**:
- Each module = Pulumi `ComponentResource`
- Encapsulates internal resources, exposes inputs/outputs
- Composable into larger infrastructures

**Provider Pattern**:
- Abstracts resource creation (e.g., `NetworkProvider.create_subnet()`)
- Standardizes naming conventions, tagging
- Reduces duplication, enforces consistency

**Configuration System** (Layered):
1. **Settings**: Load env vars → typed properties (Pydantic)
2. **Config**: Compose settings → business logic, defaults, validation
3. **Module**: Consume configs → provision resources

## Architecture Patterns

**NetworkProvider**: VNets, subnets, NSGs. Central naming/tagging.
**IdentityProvider**: Managed identities, role assignments. RBAC automation.
**StorageResourceFactory**: Blob Storage, Data Lake, PostgreSQL. Consistent storage configs.
**WebAppCreator**: Azure Web Apps for APIs/services. Standard deployment pattern.

## Configuration Workflow

**Settings** (e.g., `ProjectSettings.py`):
```python
class ProjectSettings(BaseSettings):
    project_name: str = Field(alias="PROJECT_NAME")
    environment: str = Field(alias="ENVIRONMENT")

    @classmethod
    def from_env(cls) -> "ProjectSettings":
        return cls()
```

**Config** (e.g., `ApiConfig.py`):
```python
class ApiConfig(BaseModel):
    app_name: str
    image: str

    @staticmethod
    def from_env() -> "ApiConfig":
        project = ProjectSettings.from_env()
        return ApiConfig(
            app_name=f"{project.project_name}-api",
            image=f"myregistry/api:{project.environment}",
        )
```

**Module** (e.g., `modules/api/`):
```python
api_config = ApiConfig.from_env()
web_app = WebAppCreator.create(
    name=api_config.app_name,
    image=api_config.image,
    ...
)
```

## Development Workflow

1. **Define settings**: Add env vars to `settings/<Service>Settings.py`
2. **Define config**: Compose settings in `settings/<Service>Config.py`
3. **Create module**: Infrastructure in `modules/<service>/`
4. **Use providers**: Call `NetworkProvider`, `IdentityProvider`, etc.
5. **Deploy**: `pulumi up` (preview + apply)
6. **Destroy**: `pulumi destroy` (teardown)

## Pulumi Commands

**Preview**: `pulumi preview` (dry-run, shows changes)
**Deploy**: `pulumi up` (apply changes)
**Destroy**: `pulumi destroy` (delete all resources)
**Outputs**: `pulumi stack output` (get exported values)

## Common Providers

**NetworkProvider**: `create_vnet()`, `create_subnet()`, `create_nsg()`
**IdentityProvider**: `create_identity()`, `assign_role()`
**StorageResourceFactory**: `create_blob_storage()`, `create_postgresql()`
**WebAppCreator**: `create_web_app()` (API, bot, UI hosting)

## Best Practices

**Naming**: Use `NetworkProvider` naming conventions (prefix + env + resource type)
**Tagging**: Auto-tag all resources (project, environment, component)
**Secrets**: Use Azure Key Vault, NOT hardcoded
**Modularity**: One module per logical service (agent, API, bot, etc.)

## Pre-Commit

```bash
# No specific tooling
# Validate Pulumi config: pulumi preview
```

## Essential Files

- Network provider: `/home/user/aihub-core/aihub_iac/azure/providers/NetworkProvider.py`
- Identity provider: `/home/user/aihub-core/aihub_iac/azure/providers/IdentityProvider.py`
- API module: `/home/user/aihub-core/aihub_iac/azure/modules/api/`
- Settings: `/home/user/aihub-core/aihub_iac/azure/settings/`

## Quick Reference

**Create new module**:
1. Add settings: `settings/MyServiceSettings.py` (env vars)
2. Add config: `settings/MyServiceConfig.py` (compose settings)
3. Create module: `modules/my_service/__main__.py` (provision resources)
4. Use providers: `NetworkProvider`, `IdentityProvider`, etc.
5. Export outputs: `pulumi.export("my_service_url", ...)`

**Deploy module**: `pulumi up` (from module dir or root)
**Reference outputs**: `pulumi stack output my_service_url`
