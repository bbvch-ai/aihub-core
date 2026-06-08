---
title: API-Token
description: Generieren Sie ein persönliches API-Token, um REST API-Anfragen zu authentifizieren.
source_sha: f44da54f76b2cf3ec15a7674ea25cd29f509177754b46e69f9cbbc11032885ad
---

# API-Token

Der Aufruf der REST API von einem Skript, einer Integration oder der Kommandozeile erfordert ein Bearer-Token. Anstatt
das kurzlebige JWT aus Ihrer Browser-Session wiederzuverwenden, erstellen Sie ein langlebiges persönliches Token
(präfixiert mit `sk-`), das sich als Ihr eigener Benutzer authentifiziert. Diese Seite beschreibt die Generierung eines
solchen Tokens direkt im Browser mithilfe der integrierten Swagger UI.

Es gibt noch keine dedizierte Oberfläche hierfür in der Admin-Oberfläche. Daher ist die Swagger UI unter `/api/v1/docs`
der unterstützte Weg, ein Token interaktiv zu erstellen.

## Ein Session-Token abrufen

Die Token-Endpunkte sind selbst geschützt, daher müssen Sie zuerst die Anfrage authentifizieren, die Ihr `sk-`-Token
erstellt. Die einfachste Anmeldeinformation ist das Zugriffstoken, das Ihr Browser bereits nach dem Einloggen besitzt.

1. Melden Sie sich in Ihrem Browser bei der Plattform an.
2. Öffnen Sie die Entwicklertools des Browsers, wechseln Sie zum Netzwerk-Tab und klicken Sie auf eine beliebige Anfrage
   an die API.
3. Suchen Sie unter den Anfrage-Headern nach `Authorization: Bearer eyJ...` und kopieren Sie den Wert nach `Bearer `.

::: warning Kopieren Sie das Zugriffstoken, nicht das ID-Token
Die API validiert die `account`-Audience, die nur das Zugriffstoken enthält. Wenn Sie das ID-Token kopieren (zum
Beispiel aus dem Eintrag `oidc.user:...` im lokalen Speicher), schlägt die Anfrage mit `401 ... Invalid token` fehl. Der
Netzwerk-Tab zeigt immer das Zugriffstoken an, daher ist er die zuverlässigste Quelle.

Um ein Token zu überprüfen, dekodieren Sie dessen Payload und bestätigen Sie `"typ": "Bearer"` und eine `"aud"`, die
`"account"` enthält.
:::

## Das Token in Swagger erstellen

Öffnen Sie die Swagger UI für das Deployment:

```
https://<your-deployment>/api/v1/docs
```

1. Klicken Sie auf Authorize (oben rechts).

2. Fügen Sie das Zugriffstoken in das HTTPBearer-Feld ein. Geben Sie nur das Token ein, ohne das Präfix `Bearer `.

3. Klicken Sie auf Authorize, dann auf Close.

4. Suchen Sie `POST /api/v1/{tenant_id}/tokens/` (Create API Token) und klicken Sie auf Try it out.

5. Setzen Sie `tenant_id` auf `active`, was sich zu Ihrem aktiven Mandanten auflöst.

6. Geben Sie einen Anfragekörper an. Der Name muss 1 bis 100 Zeichen lang sein und das Ablaufdatum muss ein zukünftiges
   ISO-8601 Datums-/Zeitformat sein:

   ```json
   {
     "name": "my-api-token",
     "expiry_date": "2026-12-31T23:59:59Z"
   }
   ```

7. Klicken Sie auf Execute.

Eine `201`-Antwort enthält das Token:

```json
{
  "id": "...",
  "name": "my-api-token",
  "expiry_date": "2026-12-31T23:59:59Z",
  "token": "sk-..."
}
```

::: danger Kopieren Sie das Token sofort
Der `token`-Wert wird nur einmal bei der Erstellung zurückgegeben. Er wird danach nie wieder angezeigt. Wenn Sie ihn
verlieren, widerrufen Sie das Token und erstellen Sie ein neues.
:::

## Das Token verwenden

Senden Sie das `sk-`-Token als Bearer-Anmeldeinformation bei jeder API-Anfrage:

```bash
curl https://<your-deployment>/api/v1/active/agents/ \
  -H "Authorization: Bearer sk-..."
```

Im Gegensatz zum Browser-Session-Token bleibt das `sk-`-Token bis zu seinem Ablaufdatum gültig und eignet sich daher für
Skripte und langlebige Integrationen.

## Token auflisten und widerrufen

Derselbe Controller bietet den Rest des Token-Lebenszyklus an, ebenfalls aufrufbar über die Swagger UI:

| Operation | Endpoint                                       |
| --------- | ---------------------------------------------- |
| Create    | `POST /api/v1/{tenant_id}/tokens/`             |
| List      | `GET /api/v1/{tenant_id}/tokens/`              |
| Revoke    | `DELETE /api/v1/{tenant_id}/tokens/{token_id}` |

Der List-Endpunkt gibt die ID, den Namen und das Ablaufdatum jedes Tokens zurück, aber niemals den Token-Wert. Das
Widerrufen eines Tokens löscht es dauerhaft und invalidiert sofort jeden Client, der es noch verwendet.
