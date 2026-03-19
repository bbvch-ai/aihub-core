---
title: Datenaufnahme-Pipeline
source_sha: "10a19882b20e760462998d8c57529586ec4b290c135d9f34775a90240bb44f0a"
---

# Datenaufnahme-Pipeline

Das Swiss AI Hub Pipeline SDK bietet vorgefertigte, produktionsreife Pipeline-Definitionen, die Sie mit minimaler Konfiguration verwenden können. Diese **Factories** kapseln Best Practices für die Aufnahme von Dokumenten und deren Vorbereitung für RAG-Anwendungen.

## Die zweistufige Aufnahme-Architektur

Unser Aufnahme-Prozess ist in zwei separate Stufen unterteilt, die jeweils von einer eigenen Pipeline-Definitions-Factory behandelt werden. Dies fördert Modularität und Wiederverwendbarkeit.

1.  **Stufe 1: Quelle zu Data Lake** (Optional): Diese Pipeline verbindet sich mit einer externen Quelle (wie SharePoint) und synchronisiert deren Dateien mit einem zentralen S3 Data Lake.
2.  **Stufe 2: Data Lake zu Vector Store**: Diese Pipeline überwacht den S3 Data Lake, verarbeitet die Dokumente und speichert die resultierenden Embeddings in einem Vector Store.

```mermaid
graph TD
    subgraph "Source Systems"
        A[SharePoint Sites]
        B[Confluence Wiki]
        C[Jira Projects]
        D[Manual Uploads]
        E[File Systems]
        F[Other Sources]
    end
    
    subgraph "Pipeline"
        G(Data Lake)
        H[Document Parsing]
        I(Document Store)
        J[Vector Embedding]
        K(Vector Store)
    end
    
    subgraph "Consumption"
        L(RAG Agents)
    end
    
    A --> G
    B --> G
    C --> G
    D --> G
    E --> G
    F --> G
    
    G --> H
    H --> I
    I --> J
    J --> K
    K --> L
    
    style G fill:#3a5ccc
    style I fill:#7e4cc9
    style K fill:#299764
```

## 1. Die Rclone Universal Source zu Data Lake Pipeline

Verwenden Sie die `default_rclone_to_datalake_definitions`-Factory, um Dokumente von **jedem Cloud-Speicheranbieter** mit Ihrem S3 Data Lake zu synchronisieren. Dies ist der empfohlene Ansatz für die meisten Anwendungsfälle, da er über 70 Speicher-Backends mit einer einzigen, vereinheitlichten Implementierung unterstützt.

-   **Was sie tut**: Überwacht jedes von Rclone unterstützte Remote, lädt neue oder aktualisierte Dateien herunter und bereinigt Dateien im Data Lake, die aus der Quelle gelöscht wurden.
-   **Wichtige Assets**: `observable_rclone`, `data_lake_files`, `removed_data_lake_files`.
-   **Unterstützte Quellen**: SharePoint, OneDrive, Google Drive, AWS S3, Azure Blob, SFTP, lokales Dateisystem und [70+ weitere](https://rclone.org/overview/).

### Schnellstart mit Templates

Swiss AI Hub bietet vorkonfigurierte Templates für gängige Unternehmensquellen. Jedes Template enthält Umgebungsvariablen, Pipeline-Code und Einrichtungsanweisungen.

| Template         | Anwendungsfall                                | Umgebungsvariablen-Präfix    |
| ---------------- | --------------------------------------- | --------------------- |
| **SharePoint**   | Microsoft 365 Dokumentbibliotheken        | `RCLONE_SHAREPOINT_*` |
| **OneDrive**     | Microsoft 365 privater/geschäftlicher Speicher | `RCLONE_ONEDRIVE_*`   |
| **Google Drive** | Google Workspace Organisationen          | `RCLONE_GDRIVE_*`     |
| **S3**           | AWS S3, MinIO, S3-kompatibler Speicher    | `RCLONE_S3_*`         |
| **Azure Blob**   | Azure Blob Storage                      | `RCLONE_AZUREBLOB_*`  |
| **SFTP**         | Legacy-Systeme, sichere Dateiübertragungen   | `RCLONE_SFTP_*`       |
| **Local FS**     | Gemountete Netzwerkfreigaben (NFS, SMB)       | Direkter Pfad           |

Templates befinden sich unter `packages/pipeline/templates/sources/`.

### Anwendungsbeispiel: SharePoint

**1. Umgebungsvariablen konfigurieren** (aus `templates/sources/sharepoint/.env.template` kopieren):

```bash
RCLONE_SHAREPOINT_NAME=sharepoint
RCLONE_SHAREPOINT_TYPE=onedrive
RCLONE_SHAREPOINT_CLIENT_ID=your-client-id
RCLONE_SHAREPOINT_CLIENT_SECRET=your-secret
RCLONE_SHAREPOINT_TENANT=your-tenant-id
RCLONE_SHAREPOINT_SITE_URL=https://your-tenant.sharepoint.com/sites/your-site
RCLONE_SHAREPOINT_DRIVE_TYPE=documentLibrary
```

**2. Erstellen Sie Ihre Pipeline**:

```python
from swiss_ai_hub.core.infrastructure.rclone.rclone_source_factory import sharepoint_source
from swiss_ai_hub.pipeline.util.definitions_util import default_rclone_to_datalake_definitions

# Load config from SHAREPOINT_* environment variables
sharepoint = sharepoint_source()

# Create pipeline
defs = default_rclone_to_datalake_definitions(
    datalake_container_name="my-company-docs",
    source_remote=f"{sharepoint.name}:",
    rclone_config=sharepoint,
    include_patterns=["*.pdf", "*.docx"],
    exclude_patterns=["**/archive/**"],
)
```

### Anwendungsbeispiel: Google Drive

```python
from swiss_ai_hub.core.infrastructure.rclone.rclone_source_factory import google_drive_source
from swiss_ai_hub.pipeline.util.definitions_util import default_rclone_to_datalake_definitions

gdrive = google_drive_source()

defs = default_rclone_to_datalake_definitions(
    datalake_container_name="gdrive-docs",
    source_remote=f"{gdrive.name}:Shared Documents",
    rclone_config=gdrive,
)
```

### Anwendungsbeispiel: Lokales Dateisystem / Gemountete Freigaben

Für lokale Pfade oder gemountete Netzwerkfreigaben (NFS, SMB, Azure Files) ist keine Rclone-Konfiguration erforderlich:

```python
from swiss_ai_hub.pipeline.util.definitions_util import default_rclone_to_datalake_definitions

defs = default_rclone_to_datalake_definitions(
    datalake_container_name="local-docs",
    source_remote="/mnt/shared-drive/documents",
)
```

### Verfügbare Quell-Helferfunktionen

Die `RcloneSourceFactory` bietet Komfortfunktionen, die aus Umgebungsvariablen lesen:

```python
from swiss_ai_hub.core.infrastructure.rclone.rclone_source_factory import (
    sharepoint_source,    # Reads RCLONE_SHAREPOINT_* env vars
    onedrive_source,      # Reads RCLONE_ONEDRIVE_* env vars
    google_drive_source,  # Reads RCLONE_GDRIVE_* env vars
    s3_source,            # Reads RCLONE_S3_* env vars
    azure_blob_source,    # Reads RCLONE_AZUREBLOB_* env vars
    sftp_source,          # Reads RCLONE_SFTP_* env vars
    local_fs_source,      # Reads RCLONE_LOCAL_FS_* env vars
)
```

### Umgebungsvariablen-Muster

Alle Quellkonfigurationen folgen einem konsistenten Muster mit dem Präfix `RCLONE_`:

```bash
RCLONE_<SOURCE>_NAME=remote-name       # Rclone remote name
RCLONE_<SOURCE>_TYPE=backend-type      # Rclone backend (onedrive, drive, s3, etc.)
RCLONE_<SOURCE>_CLIENT_ID=...          # OAuth client ID (if applicable)
RCLONE_<SOURCE>_CLIENT_SECRET=...      # OAuth client secret (if applicable)
RCLONE_<SOURCE>_TENANT=...             # Azure AD tenant (Microsoft sources)
RCLONE_<SOURCE>_<OPTION>=value         # Additional rclone options
```

Zusätzliche Optionen werden direkt an Rclone als Backend-spezifische Parameter übergeben:

```bash
RCLONE_S3_REGION=eu-west-1
RCLONE_S3_ENDPOINT=https://minio.example.com
RCLONE_SFTP_HOST=sftp.example.com
RCLONE_SFTP_PORT=22
```

### Rclone Service-Authentifizierung

In Produktionsumgebungen erfordert der Rclone Service eine Authentifizierung über die Umgebungsvariablen `RCLONE_RC_USER` und `RCLONE_RC_PASS`.

> **Sicherheitswarnung**: Die Standard-Zugangsdaten (`admin`/`changeme`) sind nur für Entwicklungszwecke vorgesehen. **Ändern Sie diese Zugangsdaten in Produktions-Deployments immer**, um unbefugten Zugriff auf Ihre Datenquellen zu verhindern.

```bash
# Production environment - set strong, unique credentials
RCLONE_RC_USER=your-secure-username
RCLONE_RC_PASS=your-strong-password
```

## 2. Die Data Lake zu Vector Store Pipeline

Dies ist die Kern-RAG-Pipeline. Verwenden Sie die `default_definitions`-Factory, um Dokumente aus Ihrem S3 Data Lake in einen Vector Store zu verarbeiten.

-   **Was sie tut**: Überwacht einen S3-Bucket, parst Dokumente, zerlegt sie in Nodes, erstellt optional Summary-Nodes und speichert die Embeddings in Milvus. Sie handhabt auch das Löschen von Dokumenten.
-   **Wichtige Assets**: `observable_data_lake`, `documents`, `nodes`, `summary_nodes`, `removed_documents`.

### Anwendungsbeispiel

```python
from swiss_ai_hub.pipeline.util.definitions_util import default_definitions

defs = default_definitions(
    datalake_container_name="my-company-docs",
    embedding_model_name="azure/text-embedding-3-large", # Configure the embedding model
    llm_model_name="azure/gpt-4o-mini",                 # Configure the LLM for summaries
    with_summary_nodes=True                             # Enable summary node generation
)
```

## Standard-Datenmapping

Das SDK verwendet eine konsistente Namenskonvention, um Ihre Data Lake-Struktur den zugrunde liegenden Speicher-Backends (Document Store und Vector Store) zuzuordnen.

### Container/Bucket → Datenbank/Collection

Der Name des Top-Level S3-Buckets wird als primärer Identifier für Ihre Speicherressourcen verwendet und bietet eine starke Datenisolation.

**Beispiel:**

-   **Data Lake Bucket**: `s3://hr-documents/`
-   **Document Store DB**: `hr-documents`
-   **Vector Store Collection**: `hr-documents`

### Verzeichnis → Namespace

Innerhalb eines Buckets können Sie Verzeichnisse verwenden, um logische Trennungen zu erstellen, die auf **Namespaces** innerhalb des Vector Store abgebildet werden. Dies ermöglicht Multi-Tenancy oder eine logische Gruppierung innerhalb einer einzigen Collection.

**Beispiel:**

-   **Data Lake-Pfad**: `s3://hr-documents/onboarding/`
-   **Vector Store Namespace**: `onboarding`

## Ausführen und Kombinieren von Pipelines

Um eine Pipeline auszuführen, speichern Sie Ihren Definitions-Code (z.B. `my_pipeline.py`) und verwenden Sie die Dagster CLI.

```bash
# Start the Dagster UI and development server
dagster dev -f my_pipeline.py
```
