# IMAP Agent — Manual End-to-End Test (move mail to a folder)

Reproduces the full platform flow for the **"move a mail into a folder"** capability
(issue #1508, building on the #1507 read capability): a local IMAP server, the `ImapAgent`
running against it, a profile configured in the Admin UI, triggered through the REST API, and
verified in a real webmail client.

## What this exercises

`ReadMailStartEvent → list unread → fetch first message → move it to the processed folder → stop`,
emitting a `MailMovedEvent` that records the move.

## Design facts to know before you start

These are intentional and will otherwise look like "bugs" during testing:

- **The agent is non-conversational.** It is triggered by `ReadMailStartEvent`, not a chat message.
  It does **not** appear in OpenWebUI chat, and its Admin UI page has **no "Run" button** — you trigger
  it via the REST API (Swagger).
- **It only touches _unread_ mail.** `list unread` searches `UNSEEN`. If a message has been read
  (e.g. you opened it in a webmail client — that sets the `\Seen` flag), the agent will skip it and
  stop without moving anything. This is correct behavior.
- **Move requires server support.** The move uses IMAP `MOVE` (RFC 6851), or falls back to
  `COPY` + `UID EXPUNGE` (UIDPLUS, RFC 4315). A server offering neither is refused rather than risking
  a blind `EXPUNGE`. GreenMail 2.1.x supports both.
- **The source folder is not configurable** — it is always the `Inbox Folder` the message was read
  from (IMAP UIDs are only valid within their folder). Only the **target** (`Processed Folder`) is a setting.

## Prerequisites

The dev Docker stack must be up (most of it is already, if you've been developing):
`nats`, `valkey`, `ferretdb` (+ `postgres-ferretdb`), `seaweedfs-s3`, `keycloak`.

```bash
cd <repo-root>
docker compose -f infra/docker-compose.dev.yml up -d nats valkey ferretdb postgres-ferretdb seaweedfs-s3 keycloak
```

Ports the flow uses: NATS `4222`, Redis/Valkey `6379`, S3 `9000`, API `8000`, Admin UI `3333`.

---

## Step 1 — Start a local IMAP server (GreenMail)

GreenMail is an in-memory test IMAP+SMTP server. `8080` is taken by OpenWebUI, so its API/UI is mapped
to `8025`.

```bash
docker run -d --name greenmail \
  -p 3143:3143 -p 3025:3025 -p 8025:8080 \
  -e GREENMAIL_OPTS='-Dgreenmail.setup.test.all -Dgreenmail.hostname=0.0.0.0 -Dgreenmail.auth.disabled -Dgreenmail.verbose' \
  greenmail/standalone:2.1.3
```

- IMAP (plaintext): `3143` · SMTP: `3025` · GreenMail API: `http://localhost:8025`
- `auth.disabled` → any username/password works; mailboxes auto-create.

Confirm IMAP answers:

```bash
docker logs greenmail 2>&1 | grep -i started | tail -2
```

---

## Step 2 — Seed the mailbox

Two separate concerns, kept as two scripts. Run both from `packages/agent` (`uv run python <file>`).
The IMAP **username must equal the recipient** (GreenMail keeps one mailbox per address).

> **Password ≥ 8 chars:** the config form validates a minimum length, so use `password` (not `pw`),
> even though GreenMail ignores it.

### 2a — Init: create the target folder (one-time)

Run once per fresh GreenMail container. Idempotent — safe to re-run.

Save as `init_folder.py`:

```python
from imapclient import IMAPClient

HOST, IMAP_PORT = "127.0.0.1", 3143
MAILBOX, PASSWORD, TARGET = "test@localhost", "password", "Processed"

with IMAPClient(HOST, port=IMAP_PORT, ssl=False) as c:
    c.login(MAILBOX, PASSWORD)
    if c.folder_exists(TARGET):
        print(f"{TARGET} already exists")
    else:
        c.create_folder(TARGET)
        print(f"created {TARGET}")
    print("folders:", [f[2] for f in c.list_folders()])
```

Expect the folder list to include `INBOX` and `Processed`.

### 2b — Publish a new unread message to the inbox (repeatable)

Run this each time you want a fresh unread message to move — before every trigger.

Save as `send_mail.py`:

```python
import smtplib
from email.message import EmailMessage
from imapclient import IMAPClient

HOST, IMAP_PORT, SMTP_PORT = "127.0.0.1", 3143, 3025
MAILBOX = "test@localhost"

msg = EmailMessage()
msg["From"], msg["To"], msg["Subject"] = "sender@example.com", MAILBOX, "E2E move test"
msg.set_content("This message should be moved to the Processed folder by the agent.")
with smtplib.SMTP(HOST, SMTP_PORT) as s:
    s.send_message(msg)

with IMAPClient(HOST, port=IMAP_PORT, ssl=False) as c:
    c.login(MAILBOX, "password")
    c.select_folder("INBOX", readonly=True)
    print("INBOX:", len(c.search(["ALL"])), "msgs,", len(c.search(["UNSEEN"])), "unread")
```

Expect `INBOX: 1 msgs, 1 unread` (counts grow if you run it repeatedly without triggering in between).

---

## Step 3 — Start the local services

Three processes, each in its own terminal, from the repo root:

```bash
# API (:8000) — discovery, the trigger endpoint, config RPC
cd packages/api && make run-dev

# Agent — registers the ImapAgent blueprint and processes its events
cd packages/agent && uv run python app/imap_agent/main.py

# Admin UI (:3333) — configure the profile, view run timelines
cd packages/web && pnpm dev
```

Give the API ~60s to discover the agent (or restart the API to force a discovery sweep).

---

## Step 4 — Create & configure the agent profile (Admin UI)

1. Open `http://localhost:3333`, log in with the Keycloak superuser
   (`SUPERUSER_EMAIL` / `SUPERUSER_PASSWORD` from `.env` — dev default `admin@your-company.com` / `admin`).
2. Go to **Agents** → the **IMAP Agent** blueprint → create a profile (note its `agent_id` slug).
3. In the profile's **configuration** tab set:
   - Host `127.0.0.1`, Port `3143`, **Use TLS: off**
   - Username `test@localhost`, Password `password`
   - Inbox Folder `INBOX`
   - **Move Fetched Mail: on** → the **Processed Folder** field appears → `Processed`

> The **Processed Folder** field only shows when **Move Fetched Mail** is on (conditional visibility).

---

## Step 5 — (Optional) Roundcube webmail, to watch it visually

GreenMail's REST API cannot list a specific folder (it always returns the INBOX), so use a real webmail
client to see the Processed folder.

```bash
docker run -d --name roundcube \
  --add-host host.docker.internal:host-gateway \
  -p 8026:80 \
  -e ROUNDCUBEMAIL_DEFAULT_HOST=host.docker.internal \
  -e ROUNDCUBEMAIL_DEFAULT_PORT=3143 \
  -e ROUNDCUBEMAIL_SMTP_SERVER=host.docker.internal \
  -e ROUNDCUBEMAIL_SMTP_PORT=3025 \
  -e ROUNDCUBEMAIL_DB_TYPE=sqlite \
  roundcube/roundcubemail:latest
```

Open `http://localhost:8026`, log in as `test@localhost` / `password`.

> **Do not open the message in Roundcube before triggering** — opening it sets `\Seen`, and the agent
> skips read mail. View the INBOX *list* only (it shows bold/unread). To reset a read message:
> right-click → **Mark → As unread**.

---

## Step 6 — Trigger the agent (Swagger)

1. Open Swagger: `http://localhost:8000/api/v1/docs`
2. Click **Authorize**, paste the value of `SUPERUSER_TOKEN` (from `.env`), Authorize, Close.
3. Find `POST /{tenant_id}/agents/classes/ImapAgent/instances/{agent_id}/ReadMailStartEvent`
   (use the plain one, **not** `/stream`).
4. **Try it out** →
   - `tenant_id` = `active`
   - `agent_id` = your profile slug
   - body = `{}`
5. **Execute** → **HTTP 200** with a `StopEvent` ("Process Completed") in the response = the full run
   (list → fetch → move → stop) succeeded.

curl equivalent:

```bash
curl -X POST \
  "http://localhost:8000/api/v1/active/agents/classes/ImapAgent/instances/<agent_id>/ReadMailStartEvent" \
  -H "Authorization: Bearer $SUPERUSER_TOKEN" -H "Content-Type: application/json" -d '{}'
```

---

## Step 7 — Verify

- **Roundcube:** refresh → INBOX empty, message now under **Processed**.
- **Source emptied (API):** `http://localhost:8025/api/user/test@localhost/messages` drops from 1 to 0
  (this endpoint reads the INBOX only — see gotchas).
- **Admin UI:** profile → **Threads** tab → newest run → timeline shows
  **Unread Mail Listed → Mail Fetched → Mail Moved → Finish**.
- **IMAP truth (script):**
  ```bash
  cd packages/agent && uv run python -c "
  from imapclient import IMAPClient
  with IMAPClient('127.0.0.1', port=3143, ssl=False) as c:
      c.login('test@localhost','password')
      for f in ('INBOX','Processed'):
          c.select_folder(f, readonly=True); print(f, len(c.search(['ALL'])))
  "
  ```

---

## Troubleshooting

| Symptom | Cause / fix |
| --- | --- |
| Message stays in INBOX, run stops after `UnreadMailListedEvent` | Message is read (`\Seen`) — you opened it in Roundcube. Mark it unread, or re-seed, and trigger **before** opening it. |
| Trigger hangs, no events after `ReadMailStartEvent` | Agent crashed at run start. Ensure the agent is on current code (`ReadMailStartEvent` must declare a `user` field — see below). Check the agent's console. |
| Move refused / errors | Server lacks `MOVE` and `UIDPLUS`. GreenMail 2.1.x has both; a barebones server may not. |
| GreenMail API shows the same count for every folder | Its REST API ignores the folder parameter (INBOX-only). Use Roundcube or an IMAP script to inspect other folders. |
| Swagger `/docs` 404 | The API is mounted under `/api/v1`; docs are at `http://localhost:8000/api/v1/docs`. |
| Port `8080` isn't GreenMail | That's OpenWebUI. GreenMail's API is on `8025` here. |

### Required code fix (dependency of this test)

The IMAP demonstrator's `ReadMailStartEvent` must declare a `user` field, otherwise runs triggered via the
authenticated API crash in `AgentRunTracer.trace_run_start` (`'dict' object has no attribute 'id'`):

```python
# read_mail_start_event.py
from swiss_ai_hub.core.auth import UserIdentity
...
    user: Annotated[
        UserIdentity | None,
        Field(default=None, description="User the run is executed on behalf of; populated when triggered via the API."),
    ]
```

---

## Teardown

```bash
docker rm -f greenmail roundcube
# stop the local API / agent / web processes (Ctrl-C in their terminals)
```

GreenMail and Roundcube are in-memory — removing the containers wipes all test mail.
