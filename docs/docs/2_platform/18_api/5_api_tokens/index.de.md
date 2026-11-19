---
title: API-Token
description: Generieren, prüfen und widerrufen Sie persönliche API-Token, um REST API-Anfragen zu authentifizieren.
source_sha: 256681263ce528de0f4fb12e0f24f1cf3a6b75e2cd913f62ae2fa78b248b42b8
---

# API-Token

Der Aufruf der REST API von einem Skript, einer Integration oder der Kommandozeile erfordert ein Bearer-Token. Anstatt
das kurzlebige JWT aus Ihrer Browser-Session wiederzuverwenden, erstellen Sie ein langlebiges persönliches Token
(präfixiert mit `sk-`), das sich als Ihr eigener Benutzer mit Ihren eigenen Berechtigungen authentifiziert. Ein Token
gilt in allen Mandanten, denen Sie angehören, bis es abläuft oder Sie es widerrufen.

## Token in der Admin-Oberfläche verwalten

Öffnen Sie **API-Token** im Service-Menü der Admin-Oberfläche. Die Seite listet Ihre Token auf, die neuesten zuerst,
einschliesslich abgelaufener:

| Spalte            | Bedeutung                                                                                                   |
| ----------------- | ----------------------------------------------------------------------------------------------------------- |
| Name              | Der Name, den Sie dem Token beim Generieren gegeben haben.                                                  |
| Erstellt          | Wann das Token generiert wurde.                                                                             |
| Läuft ab          | Das Ablaufdatum, markiert als Aktiv, Läuft bald ab (innerhalb von sieben Tagen) oder Abgelaufen.            |
| Zuletzt verwendet | Wann das Token zuletzt eine Anfrage authentifiziert hat, auf etwa fünf Minuten genau, oder «Nie verwendet». |

### Ein Token generieren

1. Klicken Sie auf **Token generieren**.
2. Geben Sie einen Namen ein, an dem Sie später erkennen, was das Token verwendet, zum Beispiel das Skript oder die
   Integration.
3. Wählen Sie, wie lange das Token gültig bleibt: 30 Tage, 90 Tage, 6 Monate, 1 Jahr oder ein eigenes Datum.
4. Klicken Sie auf **Generieren**.

::: danger Kopieren Sie das Token sofort
Der Token-Wert wird nur einmal angezeigt, im Dialog, der sich nach dem Generieren öffnet, und keine Seite und kein
Endpunkt gibt ihn je wieder zurück. Kopieren Sie ihn, bevor Sie den Dialog schliessen. Wenn Sie ihn verlieren,
widerrufen Sie das Token und generieren Sie ein neues.
:::

### Ein Token widerrufen

Klicken Sie auf das Papierkorb-Symbol in der Zeile des Tokens und bestätigen Sie. Das Widerrufen löscht das Token
dauerhaft und invalidiert sofort jeden Client, der es noch verwendet. Widerrufen Sie ein Token, sobald Sie vermuten,
dass es offengelegt wurde, und widerrufen Sie Token, die Sie nicht mehr verwenden.

## Das Token verwenden

Senden Sie das `sk-`-Token als Bearer-Anmeldeinformation bei jeder API-Anfrage:

```bash
curl https://<your-deployment>/api/v1/active/agents/instances \
  -H "Authorization: Bearer sk-..."
```

`active` im Pfad löst sich zu Ihrem aktiven Mandanten auf. Um in einem anderen Mandanten zu handeln, dem Sie angehören,
setzen Sie stattdessen dessen ID ein.

## Token über die API verwalten

Die obige Seite ist ein Client derselben Endpunkte, die Skripte direkt aufrufen können. Das Erstellen eines Tokens über
die API erfordert bereits eine Anmeldeinformation, daher generieren Sie das erste am einfachsten in der
Admin-Oberfläche.

| Operation | Endpoint                                       |
| --------- | ---------------------------------------------- |
| Create    | `POST /api/v1/{tenant_id}/tokens/`             |
| List      | `GET /api/v1/{tenant_id}/tokens/`              |
| Revoke    | `DELETE /api/v1/{tenant_id}/tokens/{token_id}` |

Der Create-Endpunkt erwartet einen Namen mit 1 bis 100 Zeichen und ein Ablaufdatum, das ein zukünftiges ISO-8601
Datums-/Zeitformat sein muss:

```json
{
  "name": "my-api-token",
  "expiry_date": "2027-12-31T23:59:59Z"
}
```

Eine `201`-Antwort enthält den Token-Wert, als einzige Antwort überhaupt:

```json
{
  "id": "...",
  "name": "my-api-token",
  "expiry_date": "2027-12-31T23:59:59Z",
  "token": "sk-..."
}
```

Der List-Endpunkt gibt für jedes Token `id`, `name`, `created_at`, `expiry_date` und `last_used_at` zurück, aber niemals
den Token-Wert. Das Widerrufen eines Tokens, das nicht existiert oder jemand anderem gehört, beantwortet die API mit
`404`.

::: details Ein Token ohne die Admin-Oberfläche in der Swagger UI erstellen
Die Swagger UI unter `https://<your-deployment>/api/v1/docs` akzeptiert das Zugriffstoken, das Ihr Browser nach dem
Einloggen besitzt.

1. Öffnen Sie die Entwicklertools des Browsers, wechseln Sie zum Netzwerk-Tab und klicken Sie auf eine beliebige Anfrage
   an die API.
2. Suchen Sie unter den Anfrage-Headern nach `Authorization: Bearer eyJ...` und kopieren Sie den Wert nach `Bearer `.
3. Klicken Sie in der Swagger UI auf Authorize, fügen Sie den Wert ohne das Präfix `Bearer ` in das HTTPBearer-Feld ein
   und klicken Sie auf Authorize, dann auf Close.
4. Suchen Sie `POST /api/v1/{tenant_id}/tokens/` (Create API Token), klicken Sie auf Try it out, setzen Sie `tenant_id`
   auf `active`, geben Sie den obigen Anfragekörper an und klicken Sie auf Execute.

Kopieren Sie das Zugriffstoken, nicht das ID-Token. Die API validiert die `account`-Audience, die nur das Zugriffstoken
enthält; ein ID-Token (zum Beispiel aus dem Eintrag `oidc.user:...` im lokalen Speicher) schlägt mit
`401 ... Invalid token` fehl.
:::
