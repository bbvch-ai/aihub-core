class OpenApiSchemaService:
    """Post-processing helpers for FastAPI's auto-generated OpenAPI schema."""

    @staticmethod
    def inject_tenant_id_into_openapi(openapi_schema: dict) -> dict:
        """Inject ``tenant_id`` as a path parameter into every tenant-scoped path.

        FastAPI doesn't auto-generate a parameter entry for variables that only appear
        in the router prefix (not in endpoint function signatures). Tenant-scoped
        controllers get mounted under ``/{tenant_id}/<route>`` via the runner, so the URL
        contains ``{tenant_id}`` but no endpoint function declares it as an argument.
        Without this hook, generated SDKs would emit ``path: { ... }`` types missing
        ``tenant_id`` and runtime URLs would keep the literal ``{tenant_id}`` placeholder.
        """
        tenant_param = {
            "name": "tenant_id",
            "in": "path",
            "required": True,
            "description": "Tenant identifier: a name, ObjectId, or 'active'",
            "schema": {"type": "string", "title": "Tenant Id"},
        }

        for path_key, path_val in openapi_schema.get("paths", {}).items():
            if "{tenant_id}" not in path_key:
                continue
            for method_val in path_val.values():
                if not isinstance(method_val, dict):
                    continue
                params = method_val.setdefault("parameters", [])
                if not any(p.get("name") == "tenant_id" for p in params):
                    params.insert(0, tenant_param)

        return openapi_schema
