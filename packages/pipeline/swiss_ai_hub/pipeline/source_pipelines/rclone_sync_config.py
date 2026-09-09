from typing import Annotated, Any, Self

from pydantic import Field, field_validator
from swiss_ai_hub.core.form import ChipsInput, InputNumber, InputText, Password, Select
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure.rclone import RcloneBackendType, RcloneSourceConfig
from swiss_ai_hub.core.source_pipelines import SourcePipelineConfig

_I18N = "lib.source_pipelines.rclone.config"
_BACKEND_REF = "rclone_backend_type"


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


def _choice(backend: RcloneBackendType, key: str, values: list[str]) -> Select:
    return Select(
        label=LocaleString.from_i18n_path(f"{_I18N}.{backend.value}.{key}.label"),
        help=LocaleString.from_i18n_path(f"{_I18N}.{backend.value}.{key}.help"),
        options=values,
        condition_if=_when(backend),
    )


class OneDriveOptions(Form):
    """rclone ``onedrive``; a SharePoint document library is OneDrive with ``drive_type=documentLibrary``."""

    client_id: Annotated[str | InputText, Field(description="Entra ID application (client) id.")] = ""
    client_secret: Annotated[str | Password, Field(description="Entra ID client secret.")] = ""
    tenant: Annotated[str | InputText, Field(description="Entra ID tenant id.")] = ""
    drive_id: Annotated[str | InputText, Field(description="Drive id of the site or user to sync.")] = ""
    drive_type: Annotated[str | Select, Field(description="personal, business or documentLibrary.")] = "business"
    region: Annotated[str | Select, Field(description="Microsoft cloud region.")] = "global"
    token: Annotated[
        str | Password, Field(description="Pre-obtained OAuth token JSON, instead of client credentials.")
    ] = ""

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


class GoogleDriveOptions(Form):
    client_id: Annotated[str | InputText, Field(description="OAuth client id.")] = ""
    client_secret: Annotated[str | Password, Field(description="OAuth client secret.")] = ""
    token: Annotated[str | Password, Field(description="Pre-obtained OAuth token JSON.")] = ""
    service_account_credentials: Annotated[
        str | Password, Field(description="Service account JSON, instead of an OAuth token.")
    ] = ""
    root_folder_id: Annotated[str | InputText, Field(description="Folder id to treat as the root.")] = ""

    @classmethod
    def as_form(cls) -> Self:
        backend = RcloneBackendType.DRIVE
        return cls(
            client_id=_text(backend, "client_id"),
            client_secret=_secret(backend, "client_secret"),
            token=_secret(backend, "token"),
            service_account_credentials=_secret(backend, "service_account_credentials"),
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
    """rclone ``local`` has no credentials; ``root_path`` is a path inside the rclone container."""

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
    def as_form(cls) -> Self:
        return cls(
            backend_type=Select(
                label=LocaleString.from_i18n_path(f"{_I18N}.backend_type.label"),
                help=LocaleString.from_i18n_path(f"{_I18N}.backend_type.help"),
                options=[backend.value for backend in RcloneBackendType],
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
        if self.backend is RcloneBackendType.ONEDRIVE and "token" not in options:
            options["client_credentials"] = "true"
        if self.backend is RcloneBackendType.DRIVE:
            options.setdefault("scope", "drive.readonly")
        return RcloneSourceConfig(name=remote_name, backend_type=self.backend, options=options)

    def remote_fs(self, remote_name: str) -> str:
        root = self.root_path if self.backend is RcloneBackendType.LOCAL else self.root_path.strip("/")
        return f"{remote_name}:{root}"

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
