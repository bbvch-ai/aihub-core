import json
import posixpath
from pathlib import PurePosixPath
from typing import Annotated, Any, Self
from urllib.parse import quote

from pydantic import Field, field_validator, model_validator
from swiss_ai_hub.core.form import ChipsInput, InputNumber, InputText, Password, SecretFileInput, Select
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure.rclone import (
    RcloneBackendType,
    RclonePipelineSettings,
    RcloneSettings,
    RcloneSourceConfig,
)
from swiss_ai_hub.core.network import PublicHostGuard
from swiss_ai_hub.core.source_pipelines import SourcePipelineConfig

_I18N = "lib.source_pipelines.rclone.config"
_BACKEND_REF = "rclone_backend_type"
_TESTED_BACKENDS = (RcloneBackendType.S3, RcloneBackendType.DRIVE, RcloneBackendType.ONEDRIVE)
_KEY_FILE_MAX_BYTES = 65536
_GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
_GOOGLE_TOKEN_URIS = {_GOOGLE_TOKEN_URI, "https://accounts.google.com/o/oauth2/token"}
# Providers rclone 1.71 addresses in path style on a custom endpoint, so every request goes to the endpoint host
# (checked against the real image). AWS and many others put the bucket into the host name instead.
_PATH_STYLE_S3_PROVIDERS = frozenset(
    {
        "ArvanCloud",
        "Ceph",
        "ChinaMobile",
        "Cloudflare",
        "Exaba",
        "FlashBlade",
        "IBMCOS",
        "IDrive",
        "IONOS",
        "Liara",
        "Magalu",
        "Mega",
        "Minio",
        "Other",
        "Outscale",
        "Qiniu",
        "Rclone",
        "SeaweedFS",
        "StackPath",
    }
)
_LOCAL_DISABLED = "rclone backend 'local' is disabled on this deployment: RCLONE_LOCAL_SOURCE_ROOT is unset."
# rclone's own OneDrive ``authEndpoint`` per region. The token endpoint is always one of these Microsoft hosts, so no
# form field can send a stored token anywhere else.
_ONEDRIVE_LOGIN_HOSTS = {
    "global": "https://login.microsoftonline.com",
    "us": "https://login.microsoftonline.us",
    "de": "https://login.microsoftonline.de",
    "cn": "https://login.chinacloudapi.cn",
}
_ONEDRIVE_TOKEN_SHAPE = 'The OneDrive token must be the JSON object `rclone authorize "onedrive"` prints.'
_REFRESHABLE_TOKEN_BACKENDS = (RcloneBackendType.ONEDRIVE, RcloneBackendType.DRIVE)


def _when(backend: RcloneBackendType) -> str:
    return f"$get({_BACKEND_REF}).value === '{backend.value}'"


def _text(backend: RcloneBackendType, key: str, *, placeholder: str | None = None) -> InputText:
    return InputText(
        label=LocaleString.from_i18n_path(f"{_I18N}.{backend.value}.{key}.label"),
        help=LocaleString.from_i18n_path(f"{_I18N}.{backend.value}.{key}.help"),
        placeholder=placeholder,
        condition_if=_when(backend),
    )


def _secret(backend: RcloneBackendType, key: str) -> Password:
    return Password(
        label=LocaleString.from_i18n_path(f"{_I18N}.{backend.value}.{key}.label"),
        help=LocaleString.from_i18n_path(f"{_I18N}.{backend.value}.{key}.help"),
        feedback=False,
        toggle_mask=True,
        condition_if=_when(backend),
    )


def _secret_file(backend: RcloneBackendType, key: str, accept: str) -> SecretFileInput:
    return SecretFileInput(
        label=LocaleString.from_i18n_path(f"{_I18N}.{backend.value}.{key}.label"),
        help=LocaleString.from_i18n_path(f"{_I18N}.{backend.value}.{key}.help"),
        accept=accept,
        max_size_bytes=_KEY_FILE_MAX_BYTES,
        condition_if=_when(backend),
    )


def _onedrive_setup_answers(drive_id: str) -> dict[str, str]:
    """rclone's OneDrive setup asks how to find the drive even when ``drive_id`` is given. Answering with that ID
    makes rclone check the drive against Microsoft Graph while the remote is created, so a wrong ID or a missing
    permission fails before anything is listed. rclone never stores ``config_*`` answers in the remote."""
    return {
        "config_type": "driveid",
        "config_driveid_fixed": drive_id,
        "config_driveid": drive_id,
        "config_drive_ok": "true",
    }


def _choice(backend: RcloneBackendType, key: str, values: list[str]) -> Select:
    return Select(
        label=LocaleString.from_i18n_path(f"{_I18N}.{backend.value}.{key}.label"),
        help=LocaleString.from_i18n_path(f"{_I18N}.{backend.value}.{key}.help"),
        options=values,
        condition_if=_when(backend),
    )


class OneDriveOptions(Form):
    """rclone ``onedrive``; a SharePoint document library is OneDrive with ``drive_type=documentLibrary``. rclone
    replaces ``drive_type`` with what Microsoft Graph reports for the drive when the remote is created."""

    client_id: Annotated[str | InputText, Field(description="Entra ID application (client) id.")] = ""
    client_secret: Annotated[str | Password, Field(description="Entra ID client secret.")] = ""
    tenant: Annotated[str | InputText, Field(description="Entra ID tenant id.")] = ""
    drive_id: Annotated[str | InputText, Field(description="Drive id of the site or user to sync.")] = ""
    drive_type: Annotated[str | Select, Field(description="personal, business or documentLibrary.")] = "business"
    region: Annotated[str | Select, Field(description="Microsoft cloud region.")] = "global"
    token: Annotated[
        str | Password, Field(description="Pre-obtained OAuth token JSON, instead of client credentials.")
    ] = ""

    @field_validator("token", mode="after")
    @classmethod
    def _token_is_a_json_object(cls, value: str | Password) -> str | Password:
        """The observation reads the token's refresh_token before creating the remote, so a token that is not the JSON
        object rclone printed is refused here with the field named, not later with a bare JSON parse error."""
        if not isinstance(value, str) or not value.strip():
            return value
        try:
            parsed = json.loads(value)
        except ValueError as error:
            raise ValueError(_ONEDRIVE_TOKEN_SHAPE) from error
        if not isinstance(parsed, dict):
            raise ValueError(_ONEDRIVE_TOKEN_SHAPE)
        return value

    @classmethod
    def as_form(cls) -> Self:
        backend = RcloneBackendType.ONEDRIVE
        return cls(
            client_id=_text(backend, "client_id"),
            client_secret=_secret(backend, "client_secret"),
            tenant=_text(backend, "tenant"),
            drive_id=_text(backend, "drive_id"),
            drive_type=_choice(backend, "drive_type", ["business", "documentLibrary", "personal"]),
            region=_choice(backend, "region", ["global", "us", "de", "cn"]),
            token=_secret(backend, "token"),
        )

    def token_url(self) -> str:
        """Where rclone refreshes a pasted token. rclone's OneDrive setup checks the drive with a client that has no
        token URL of its own (``onedrive.go:612``, v1.71.2), so without this an expired access token fails the
        remote's creation with ``Post "": unsupported protocol scheme``. Built the way rclone's ``makeOauthConfig``
        builds it: the region's login host, then the tenant (``common`` for a token from rclone's own app)."""
        region = self.region or "global"
        if region not in _ONEDRIVE_LOGIN_HOSTS:
            raise ValueError(f"Unknown OneDrive region '{region}'.")
        return f"{_ONEDRIVE_LOGIN_HOSTS[region]}/{quote(self.tenant or 'common', safe='')}/oauth2/v2.0/token"


class GoogleDriveOptions(Form):
    client_id: Annotated[str | InputText, Field(description="OAuth client id.")] = ""
    client_secret: Annotated[str | Password, Field(description="OAuth client secret.")] = ""
    token: Annotated[str | Password, Field(description="Pre-obtained OAuth token JSON.")] = ""
    service_account_credentials: Annotated[
        str | SecretFileInput, Field(description="Service account key file JSON, instead of an OAuth token.")
    ] = ""
    root_folder_id: Annotated[str | InputText, Field(description="Folder id to treat as the root.")] = ""

    @field_validator("token", "service_account_credentials", mode="after")
    @classmethod
    def _single_line_json(cls, value: str | Password | SecretFileInput) -> str | Password | SecretFileInput:
        """rclone's config store refuses values with line breaks, and Google hands out pretty-printed key files:
        re-serialize the blob on one line so what the user pasted is what rclone accepts."""
        if not isinstance(value, str) or not value.strip():
            return value
        try:
            return json.dumps(json.loads(value), separators=(",", ":"))
        except ValueError as error:
            raise ValueError("Google Drive credentials must be the JSON blob from the downloaded key file.") from error

    @field_validator("service_account_credentials", mode="after")
    @classmethod
    def _google_token_endpoint(cls, value: str | SecretFileInput) -> str | SecretFileInput:
        """rclone posts the signed assertion to the key file's own `token_uri`, so any other host is one the submitter
        picked; checked without a name lookup. Go reads JSON keys ignoring case (the Kelvin sign included) and keeps
        the last match, so every key that folds to `token_uri` must name Google."""
        if not isinstance(value, str) or not value.strip():
            return value
        key = json.loads(value)
        if not isinstance(key, dict):
            return value
        token_uris = [uri for name, uri in key.items() if name.casefold() == "token_uri"]
        if any(not isinstance(uri, str) or uri not in _GOOGLE_TOKEN_URIS for uri in token_uris):
            raise ValueError("The service account key file must use Google's token_uri.")
        return value

    @classmethod
    def as_form(cls) -> Self:
        backend = RcloneBackendType.DRIVE
        return cls(
            client_id=_text(backend, "client_id"),
            client_secret=_secret(backend, "client_secret"),
            token=_secret(backend, "token"),
            service_account_credentials=_secret_file(backend, "service_account_credentials", accept=".json"),
            root_folder_id=_text(backend, "root_folder_id"),
        )


class S3Options(Form):
    provider: Annotated[str | InputText, Field(description="rclone S3 provider name, e.g. AWS or Minio.")] = "AWS"
    access_key_id: Annotated[str | InputText, Field(description="Access key id.")] = ""
    secret_access_key: Annotated[str | Password, Field(description="Secret access key.")] = ""
    region: Annotated[str | InputText, Field(description="Region.")] = ""
    endpoint: Annotated[str | InputText, Field(description="Endpoint URL for non-AWS providers.")] = ""

    @classmethod
    def as_form(cls) -> Self:
        backend = RcloneBackendType.S3
        return cls(
            provider=_text(backend, "provider", placeholder="AWS"),
            access_key_id=_text(backend, "access_key_id"),
            secret_access_key=_secret(backend, "secret_access_key"),
            region=_text(backend, "region"),
            endpoint=_text(backend, "endpoint"),
        )


class AzureBlobOptions(Form):
    account: Annotated[str | InputText, Field(description="Storage account name.")] = ""
    key: Annotated[str | Password, Field(description="Storage account key.")] = ""
    sas_url: Annotated[str | Password, Field(description="SAS URL, instead of an account key.")] = ""
    endpoint: Annotated[str | InputText, Field(description="Endpoint for sovereign clouds.")] = ""

    @classmethod
    def as_form(cls) -> Self:
        backend = RcloneBackendType.AZUREBLOB
        return cls(
            account=_text(backend, "account"),
            key=_secret(backend, "key"),
            sas_url=_secret(backend, "sas_url"),
            endpoint=_text(backend, "endpoint"),
        )


class SftpOptions(Form):
    host: Annotated[str | InputText, Field(description="Host name.")] = ""
    port: Annotated[int | InputNumber, Field(description="Port.")] = 22
    user: Annotated[str | InputText, Field(description="User name.")] = ""
    password: Annotated[str | Password, Field(description="Password, instead of a key.")] = ""
    key_pem: Annotated[str | Password, Field(description="PEM-encoded private key, instead of a password.")] = ""

    @field_validator("key_pem", mode="after")
    @classmethod
    def _escape_line_breaks(cls, value: str | Password) -> str | Password:
        """rclone wants a PEM key on one line with literal ``\\n`` between the lines; a pasted key has real ones."""
        if not isinstance(value, str):
            return value
        return value.strip().replace("\r\n", "\n").replace("\n", "\\n")

    @classmethod
    def as_form(cls) -> Self:
        backend = RcloneBackendType.SFTP
        return cls(
            host=_text(backend, "host"),
            port=InputNumber(
                label=LocaleString.from_i18n_path(f"{_I18N}.sftp.port.label"),
                min=1,
                max=65535,
                use_grouping=False,
                condition_if=_when(backend),
            ),
            user=_text(backend, "user"),
            password=_secret(backend, "password"),
            key_pem=_secret(backend, "key_pem"),
        )


class LocalOptions(Form):
    """rclone ``local`` has no credentials; ``root_path`` is a path inside the rclone container, and only below
    ``RCLONE_LOCAL_SOURCE_ROOT``: without that setting the backend is neither offered nor run."""

    @classmethod
    def as_form(cls) -> Self:
        return cls()


_RCLONE_KEYS = {"password": "pass"}


class RcloneSyncConfig(SourcePipelineConfig):
    """
    What a knowledge database filled by the rclone source pipeline is configured with.

    One class covers every backend: ``backend_type`` selects which option group is shown, the groups themselves
    are plain nested forms with primitive defaults so a hidden group submits nothing and validates as its
    defaults. Announced through the pipeline's registration record, stored per database as
    ``BucketEntity.source_configuration`` with the ``Password`` fields encrypted, and read back per run to build
    the database's rclone remote.
    """

    backend_type: Annotated[str | Select, Field(description="rclone backend the source is reached with.")]
    root_path: Annotated[
        str | InputText,
        Field(description="Folder inside the remote whose top-level folders become the database's namespaces."),
    ] = ""
    # Nullable because an untouched chips input submits nothing, which the normaliser turns into None.
    include_patterns: Annotated[list[str] | ChipsInput | None, Field(description="rclone glob rules to include.")] = (
        None
    )
    exclude_patterns: Annotated[list[str] | ChipsInput | None, Field(description="rclone glob rules to exclude.")] = (
        None
    )
    onedrive: Annotated[OneDriveOptions, Field(description="OneDrive / SharePoint options.")] = Field(
        default_factory=OneDriveOptions
    )
    drive: Annotated[GoogleDriveOptions, Field(description="Google Drive options.")] = Field(
        default_factory=GoogleDriveOptions
    )
    s3: Annotated[S3Options, Field(description="S3 options.")] = Field(default_factory=S3Options)
    azureblob: Annotated[AzureBlobOptions, Field(description="Azure Blob options.")] = Field(
        default_factory=AzureBlobOptions
    )
    sftp: Annotated[SftpOptions, Field(description="SFTP options.")] = Field(default_factory=SftpOptions)
    local: Annotated[LocalOptions, Field(description="Local filesystem options.")] = Field(default_factory=LocalOptions)

    @classmethod
    def offered_backends(cls) -> list[RcloneBackendType]:
        """Only the backends verified end to end, plus ``local`` where the deployment names a directory the daemon
        may serve from. Nothing else is synced either, whatever a stored configuration names."""
        allowed_root = RcloneSettings().LOCAL_SOURCE_ROOT
        return [
            backend
            for backend in RcloneBackendType
            if backend in _TESTED_BACKENDS or (backend is RcloneBackendType.LOCAL and allowed_root)
        ]

    @classmethod
    def as_form(cls) -> Self:
        return cls(
            backend_type=Select(
                label=LocaleString.from_i18n_path(f"{_I18N}.backend_type.label"),
                help=LocaleString.from_i18n_path(f"{_I18N}.backend_type.help"),
                options=[
                    {
                        "label": LocaleString.from_i18n_path(f"{_I18N}.backend_type.options.{backend.value}"),
                        "value": backend.value,
                    }
                    for backend in cls.offered_backends()
                ],
                option_label="label",
                option_value="value",
                ref=_BACKEND_REF,
                required=True,
            ),
            root_path=InputText(
                label=LocaleString.from_i18n_path(f"{_I18N}.root_path.label"),
                help=LocaleString.from_i18n_path(f"{_I18N}.root_path.help"),
            ),
            include_patterns=ChipsInput(
                label=LocaleString.from_i18n_path(f"{_I18N}.include_patterns.label"),
                help=LocaleString.from_i18n_path(f"{_I18N}.include_patterns.help"),
                placeholder="*.pdf",
            ),
            exclude_patterns=ChipsInput(
                label=LocaleString.from_i18n_path(f"{_I18N}.exclude_patterns.label"),
                help=LocaleString.from_i18n_path(f"{_I18N}.exclude_patterns.help"),
                placeholder="**/~$*",
            ),
            onedrive=OneDriveOptions.as_form(),
            drive=GoogleDriveOptions.as_form(),
            s3=S3Options.as_form(),
            azureblob=AzureBlobOptions.as_form(),
            sftp=SftpOptions.as_form(),
            local=LocalOptions.as_form(),
        )

    @model_validator(mode="after")
    def _only_offered_backends(self) -> Self:
        """The dialog's choice is not enforced by the API, which validates against the announced schema only."""
        if not isinstance(self.backend_type, str) or self.backend in self.offered_backends():
            return self
        if self.backend is RcloneBackendType.LOCAL:
            raise ValueError(_LOCAL_DISABLED)
        offered = ", ".join(backend.value for backend in self.offered_backends())
        raise ValueError(f"rclone backend '{self.backend_type}' is not offered on this deployment ({offered}).")

    @model_validator(mode="after")
    def _no_access_point_behind_an_endpoint(self) -> Self:
        """An access point ARN as the bucket makes the S3 client derive its own host from the ARN instead of using the
        checked endpoint; rclone fails on it in path style anyway, so the reason is given here."""
        if not isinstance(self.backend_type, str) or self.backend is not RcloneBackendType.S3 or not self.s3.endpoint:
            return self
        if self.root_path.strip("/").split("/")[0].lower().startswith("arn:"):
            raise ValueError("An S3 access point ARN cannot be the root path of a source with a custom endpoint.")
        return self

    @field_validator("include_patterns", "exclude_patterns", mode="before")
    @classmethod
    def _blank_patterns_mean_none(cls, value: object) -> object:
        """An untouched chips input may arrive as an empty string rather than a list."""
        return None if value == "" else value

    @property
    def backend(self) -> RcloneBackendType:
        return RcloneBackendType(self.backend_type)

    def to_rclone_source_config(self, remote_name: str) -> RcloneSourceConfig:
        """The remote definition for the selected backend only; empty options are dropped so rclone applies its
        own defaults, and the one field rclone spells differently is renamed on the way out."""
        options = {
            _RCLONE_KEYS.get(key, key): value
            for key, value in getattr(self, self.backend.value).model_dump().items()
            if value not in ("", None) and not key.startswith("_")
        }
        self._require(options)
        if self.backend is RcloneBackendType.ONEDRIVE:
            options |= _onedrive_setup_answers(options["drive_id"])
            if "token" in options:
                options["token_url"] = self.onedrive.token_url()
            else:
                options["client_credentials"] = "true"
        if self.backend is RcloneBackendType.DRIVE:
            options.setdefault("scope", "drive.readonly")
        if self.backend is RcloneBackendType.S3 and "endpoint" in options:
            options["provider"] = self._path_style_provider(options.get("provider"))
        return RcloneSourceConfig(name=remote_name, backend_type=self.backend, options=options)

    @staticmethod
    def _path_style_provider(provider: str | None) -> str:
        """In virtual-hosted style rclone contacts ``<bucket>.<endpoint host>``, a name whoever owns the endpoint's
        domain can point inside the platform, and only the endpoint host is checked. A provider that keeps the bucket
        in the path is kept for its other quirks; any other is sent as ``Other``. The stored provider is untouched."""
        return provider if provider in _PATH_STYLE_S3_PROVIDERS else "Other"

    def outbound_urls(self) -> list[str]:
        """Every host the selected backend was told to connect to, as a URL. OneDrive and Drive name none: rclone
        reaches Microsoft Graph and Google on its own."""
        match self.backend:
            case RcloneBackendType.S3:
                endpoints = [self.s3.endpoint]
            case RcloneBackendType.AZUREBLOB:
                endpoints = [self.azureblob.endpoint]
            case RcloneBackendType.SFTP:
                endpoints = [f"sftp://{self.sftp.host}:{self.sftp.port}"]
            case _:
                endpoints = []
        return [endpoint if "://" in endpoint else f"https://{endpoint}" for endpoint in endpoints if endpoint]

    def require_public_hosts(self) -> None:
        """Run before any remote is created from this configuration: a knowledge administrator names these hosts and
        the daemon sits on the platform's own networks."""
        allowed_hosts = RclonePipelineSettings().private_host_allow_list()
        for url in self.outbound_urls():
            PublicHostGuard.require_public(url, allowed_hosts, "RCLONE_PIPELINE_ALLOWED_PRIVATE_HOSTS")

    def refreshable_token_path(self) -> str | None:
        """Dotted path of the pasted OAuth token rclone refreshes for this source, or None when the source holds
        none: client credentials and service accounts fetch a fresh token on every run and keep no refresh token."""
        if self.backend not in _REFRESHABLE_TOKEN_BACKENDS or not getattr(self, self.backend.value).token:
            return None
        return f"{self.backend.value}.token"

    def remote_fs(self, remote_name: str) -> str:
        if self.backend is RcloneBackendType.LOCAL:
            return f"{remote_name}:{self._local_root_within_allowed_directory()}"
        return f"{remote_name}:{self.root_path.strip('/')}"

    def _local_root_within_allowed_directory(self) -> str:
        """The form is advisory: a stored configuration is re-checked on every run against the deployment's
        ``RCLONE_LOCAL_SOURCE_ROOT``, so a `local` source can never leave that directory or run where the
        setting is absent."""
        allowed_root = RcloneSettings().LOCAL_SOURCE_ROOT
        if not allowed_root:
            raise ValueError(_LOCAL_DISABLED)
        allowed = PurePosixPath(posixpath.normpath(allowed_root))
        requested = PurePosixPath(posixpath.normpath(self.root_path)) if self.root_path.strip() else allowed
        if requested != allowed and allowed not in requested.parents:
            raise ValueError(f"rclone backend 'local' may only read below '{allowed}', not '{requested}'.")
        return str(requested)

    def _require(self, options: dict[str, Any]) -> None:
        alternatives: dict[RcloneBackendType, list[set[str]]] = {
            RcloneBackendType.ONEDRIVE: [{"drive_id", "token"}, {"drive_id", "client_id", "client_secret", "tenant"}],
            RcloneBackendType.DRIVE: [{"token"}, {"service_account_credentials"}],
            RcloneBackendType.S3: [{"access_key_id", "secret_access_key"}],
            RcloneBackendType.AZUREBLOB: [{"account", "key"}, {"sas_url"}],
            RcloneBackendType.SFTP: [{"host", "user", "pass"}, {"host", "user", "key_pem"}],
            RcloneBackendType.LOCAL: [set()],
        }
        if not any(required <= options.keys() for required in alternatives[self.backend]):
            wanted = " or ".join("+".join(sorted(required)) for required in alternatives[self.backend])
            raise ValueError(f"rclone backend '{self.backend.value}' needs {wanted}.")
