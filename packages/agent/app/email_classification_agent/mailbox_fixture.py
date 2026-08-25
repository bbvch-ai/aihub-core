"""Seed and verify a GreenMail mailbox for the end-to-end drafting run.

Turns the manual e2e into two commands. `seed` posts a fixture set over SMTP; `verify` reads the mailbox back over
IMAP and asserts where every message ended up, that each opted-in message has exactly one threaded draft, and — the
part no mock can prove — that no mailbox exists for an outside recipient, i.e. the agent sent no mail.

Bring GreenMail up first:

    docker run -d --name greenmail -p 3025:3025 -p 3143:3143 -p 8081:8080 \
      -e GREENMAIL_OPTS='-Dgreenmail.setup.test.all -Dgreenmail.hostname=0.0.0.0 \
                         -Dgreenmail.users=user:password@localhost -Dgreenmail.verbose' \
      greenmail/standalone:2.1.5

Two details in that command are not optional. Without `greenmail.hostname=0.0.0.0` GreenMail binds its listeners to
the container's own loopback and the published ports connect to nothing. And its API listens on 8080 inside the
container, which is OpenWebUI's port on the dev stack — hence the 8081 mapping, and `--api-port` if you move it again.

Then:

    uv run --package swiss-ai-hub-agent python -m app.email_classification_agent.mailbox_fixture seed
    IMAP_HOST=127.0.0.1 IMAP_PORT=3143 IMAP_TLS=0 IMAP_USER=user IMAP_PASS=password \
    IMAP_ENABLE_DRAFT=1 IMAP_DRAFTS=Drafts IMAP_INCLUDE_ATTACHMENTS=1 \
        uv run --package swiss-ai-hub-agent python -m app.email_classification_agent.trigger
    uv run --package swiss-ai-hub-agent python -m app.email_classification_agent.mailbox_fixture verify

Recreate the container before each full pass rather than seeding twice. The fixtures use fixed `Message-ID`s so that
`verify` can match a draft to the mail it answers, which means a second seeding produces a second set of drafts
carrying the same ids — indistinguishable from the duplicate-draft bug the checks are looking for.

`--delimiter` is the separator in the *configured* category folder names, which defaults to `/` to match the trigger.
It is not necessarily the server's own delimiter: GreenMail's is `.`, so a configured `Triage/Support` is created there
as one flat folder literally called `Triage/Support` rather than as a tree, while Gmail builds a real label tree from
the same name (see the IMAP ADR). Either way the checks look for the name that was configured.
"""

import argparse
import json
import smtplib
import sys
import urllib.request
from email.message import EmailMessage
from email.policy import default as default_policy

from pydantic import BaseModel, Field

_HOST = "127.0.0.1"
_SMTP_PORT = 3025
_IMAP_PORT = 3143
_DEFAULT_API_PORT = 8081
_MAILBOX = "user@localhost"
_SENDER = "customer@example.com"
# The IMAP login and the address mail is sent to are different strings for the same mailbox, and the GREENMAIL_OPTS
# format is what ties them together: `user:password@localhost` means login `user`, password `password`, address
# `user@localhost`. Get that wrong and GreenMail auto-creates a second mailbox for the recipient, leaving the one you
# log into empty — at which point every check here passes for the wrong reason.
_LOGIN = "user"
_PASSWORD = "password"

# A signature logo is only ever judged on its size, so fake bytes are honest here — nothing will try to parse it.
_PNG_3KB = b"\x89PNG\r\n\x1a\n" + b"\x00" * 3000


def _real_jpeg_without_text() -> bytes:
    """A genuine JPEG holding no writing — the photo case.

    It has to be a real image, not padded bytes: the parser has to *succeed* and come back with nothing, which is the
    outcome under test. Fake bytes make it fail to decode instead, which exercises a different path entirely and
    quietly proves nothing about textless attachments.
    """
    from io import BytesIO

    from PIL import Image, ImageDraw

    image = Image.new("RGB", (1400, 900), (96, 132, 88))
    draw = ImageDraw.Draw(image)
    for offset in range(0, 1400, 37):
        draw.ellipse((offset, offset // 2, offset + 120, offset // 2 + 90), fill=(140, 96, 64))
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=92)
    return buffer.getvalue()


def _real_office_document() -> bytes:
    """A genuine Office file, so the MarkItDown branch is actually exercised.

    An `.xlsx` rather than a `.docx` only because the workspace can already write one; both route to the same loader,
    which is the point being tested. Comfortably over the size floor.
    """
    from io import BytesIO

    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Delivery"
    sheet.append(["Order", "Depot", "Status"])
    sheet.append([4711, "Bern", "delivered to the wrong depot"])
    for index in range(400):
        sheet.append([4712 + index, "Basel", "delivered as ordered"])
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


class Fixture(BaseModel):
    """One seeded message and what the run is expected to do with it."""

    key: str
    subject: str
    body: str
    expected_category: str | None
    expects_draft: bool
    attachments: list[tuple[str, str, str, bytes]] = Field(default_factory=list)
    omit_date: bool = False


_FIXTURES = [
    Fixture(
        key="information",
        subject="What are your opening hours?",
        body="Could you tell me when your office is open on Saturdays? Many thanks.",
        expected_category="information_request",
        expects_draft=True,
    ),
    Fixture(
        key="support",
        subject="Portal login is broken",
        body="I cannot log in to the portal since this morning. It returns a 500 error. Please fix it.",
        expected_category="support_request",
        expects_draft=True,
    ),
    Fixture(
        key="invoice_pdf",
        subject="Invoice 2026-0042",
        body="Please find our invoice attached, payable within 30 days.",
        expected_category="invoice",
        expects_draft=False,
        attachments=[("invoice.pdf", "application", "pdf", b"%PDF-1.4 Invoice 2026-0042 total CHF 1240.00")],
    ),
    Fixture(
        key="support_office",
        # The MarkItDown branch: MinerU never sees an Office file, so a run that only routed PDFs proves nothing
        # about it. The file is generated for real, or the loader fails to open it and the branch is never reached.
        subject="Wrong depot for order 4711",
        body="See the attached order confirmation — it went to the wrong depot.",
        expected_category="support_request",
        expects_draft=True,
        attachments=[
            (
                "order.xlsx",
                "application",
                "vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                _real_office_document(),
            )
        ],
    ),
    Fixture(
        key="thanks",
        subject="Thank you!",
        body="Just wanted to say the new release is lovely. No reply needed.",
        expected_category=None,
        expects_draft=False,
    ),
    Fixture(
        key="no_date",
        # GreenMail advertises SORT but sorts Date-less mail last instead of falling back to INTERNALDATE, so this
        # is the fixture that exercises the ordering branch rather than assuming it.
        subject="Undated question about pricing",
        body="How much does the enterprise plan cost?",
        expected_category="information_request",
        expects_draft=True,
        omit_date=True,
    ),
    Fixture(
        key="cat_photo",
        # The textless-image case: MinerU answers with empty markdown, which must read as "no text", not as an error.
        subject="Is this damage covered?",
        body="Photo attached of the damaged parcel.",
        expected_category="support_request",
        expects_draft=True,
        attachments=[("cat.jpg", "image", "jpeg", _real_jpeg_without_text())],
    ),
    Fixture(
        key="signature_logo",
        # A routine business mail. The 3 KB inline logo must never cost a document-parser round trip.
        subject="Quick question about the contract",
        body="Does the contract auto-renew? Thanks.\n\n-- \nBest regards\nSales",
        expected_category="information_request",
        expects_draft=True,
        attachments=[("logo.png", "image", "png", _PNG_3KB)],
    ),
    Fixture(
        key="long_thread",
        # A long body, plus a PDF that is deliberately *not* a valid one. Two things under test: that a parser
        # failure costs the attachment and not the draft, and that a long thread still produces a usable reply.
        # Swap in a real multi-page PDF to exercise MinerU's success path — the workspace cannot generate one.
        subject="Escalation: repeated delivery failures",
        body=(
            "Our shipments have failed four times. Please confirm a fixed delivery date.\n\n"
            + "\n".join(f"> On an earlier date, agent {index} promised a callback." for index in range(400))
        ),
        expected_category="support_request",
        expects_draft=True,
        attachments=[("history.pdf", "application", "pdf", b"%PDF-1.4 " + b"delivery log entry. " * 4000)],
    ),
]


class MailboxFixture:
    """Seeds the fixture mailbox and checks what a run did to it."""

    @staticmethod
    def seed(api_port: int) -> None:
        """Post every fixture over SMTP, oldest first, and show which mailboxes exist before the run."""
        with smtplib.SMTP(_HOST, _SMTP_PORT) as smtp:
            for fixture in _FIXTURES:
                smtp.send_message(MailboxFixture._build(fixture))
                print(f"[seed] sent {fixture.key}: {fixture.subject!r}")

        mailboxes = MailboxFixture._mailboxes(api_port)
        print(f"[seed] {len(_FIXTURES)} message(s) seeded; mailboxes on the server: {sorted(mailboxes or [])}")
        print("[seed] `verify` asserts no mailbox for an outside recipient appears — that is the no-send check")

    @staticmethod
    def verify(delimiter: str, drafts_folder: str, api_port: int) -> int:
        """Assert filing, drafting and threading, and that nothing was sent. Returns the number of failures."""
        from imapclient import IMAPClient

        failures: list[str] = []
        with IMAPClient(_HOST, port=_IMAP_PORT, ssl=False) as client:
            client.login(_LOGIN, _PASSWORD)
            folders = {name for _flags, _delim, name in client.list_folders()}
            print(f"[verify] folders on the server: {sorted(folders)}")

            drafts = MailboxFixture._drafts(client, drafts_folder, folders)
            failures += MailboxFixture._check_the_mailbox_is_the_seeded_one(client, delimiter, folders)
            failures += MailboxFixture._check_filing(client, delimiter, folders)
            failures += MailboxFixture._check_drafts(drafts)
            failures += MailboxFixture._check_inbox_is_drained(client)

        failures += MailboxFixture._check_nothing_was_sent(api_port)

        for failure in failures:
            print(f"[verify] FAIL {failure}")
        print(f"[verify] {'PASS — every check held' if not failures else f'{len(failures)} check(s) failed'}")
        return len(failures)

    @staticmethod
    def _build(fixture: Fixture) -> EmailMessage:
        message = EmailMessage(policy=default_policy)
        message["From"] = _SENDER
        message["To"] = _MAILBOX
        message["Subject"] = fixture.subject
        message["Message-ID"] = f"<{fixture.key}@example.com>"
        if not fixture.omit_date:
            message["Date"] = "Tue, 25 Aug 2026 09:00:00 +0000"
        message.set_content(fixture.body)
        for filename, maintype, subtype, content in fixture.attachments:
            message.add_attachment(content, maintype=maintype, subtype=subtype, filename=filename)
        return message

    @staticmethod
    def _folder_for(category: str | None, delimiter: str) -> str:
        """The folder a category files into, with the server's own delimiter substituted in.

        Mirrors the trigger's category configuration; keep the two in step or every filing check fails at once.
        """
        folders = {
            "information_request": "Triage/Information",
            "support_request": "Triage/Support",
            "invoice": "Triage/Invoices",
            None: "Triage/Uncategorised",
        }
        return folders[category].replace("/", delimiter)

    @staticmethod
    def _check_filing(client, delimiter: str, folders: set[str]) -> list[str]:
        failures = []
        for fixture in _FIXTURES:
            expected = MailboxFixture._folder_for(fixture.expected_category, delimiter)
            if expected not in folders:
                failures.append(f"{fixture.key}: folder {expected!r} does not exist")
                continue
            subjects = MailboxFixture._subjects_in(client, expected)
            if fixture.subject not in subjects:
                failures.append(f"{fixture.key}: expected in {expected!r}, found {sorted(subjects)}")
            else:
                print(f"[verify] {fixture.key} filed into {expected!r}")
        return failures

    @staticmethod
    def _drafts(client, drafts_folder: str, folders: set[str]) -> list[EmailMessage]:
        if drafts_folder not in folders:
            print(f"[verify] the drafts folder {drafts_folder!r} does not exist — no drafts to read")
            return []
        client.select_folder(drafts_folder, readonly=True)
        uids = client.search(["ALL"])
        fetched = client.fetch(uids, ["BODY.PEEK[]", "FLAGS"]) if uids else {}
        drafts = []
        for uid in uids:
            import email as email_module

            raw = fetched[uid][b"BODY[]"]
            message = email_module.message_from_bytes(raw, policy=default_policy)
            message["X-Fixture-Flags"] = " ".join(flag.decode() for flag in fetched[uid].get(b"FLAGS", ()))
            drafts.append(message)
        return drafts

    @staticmethod
    def _check_drafts(drafts: list[EmailMessage]) -> list[str]:
        failures = []
        by_in_reply_to = {message.get("In-Reply-To"): message for message in drafts}
        for fixture in _FIXTURES:
            expected_id = f"<{fixture.key}@example.com>"
            draft = by_in_reply_to.get(expected_id)
            if fixture.expects_draft and draft is None:
                failures.append(f"{fixture.key}: expected a draft threaded to {expected_id}, found none")
                continue
            if not fixture.expects_draft:
                if draft is not None:
                    failures.append(f"{fixture.key}: its category is not opted in, yet a draft was written")
                else:
                    print(f"[verify] {fixture.key} correctly got no draft")
                continue

            problems = MailboxFixture._draft_problems(fixture, draft)
            failures += problems
            if not problems:
                print(f"[verify] {fixture.key} has a threaded draft addressed to the sender")

        extra = len(drafts) - sum(1 for fixture in _FIXTURES if fixture.expects_draft)
        if extra > 0:
            failures.append(f"{extra} draft(s) more than expected — a re-run may have drafted twice")
        return failures

    @staticmethod
    def _draft_problems(fixture: Fixture, draft: EmailMessage) -> list[str]:
        """Everything a correctly threaded draft must show. `Re:` and `In-Reply-To` are what make a mail client file
        it under the original conversation rather than as a stray new message."""
        problems = []
        if draft.get("Subject") != f"Re: {fixture.subject}":
            problems.append(f"{fixture.key}: draft subject is {draft.get('Subject')!r}")
        if _SENDER not in (draft.get("To") or ""):
            problems.append(f"{fixture.key}: draft is addressed to {draft.get('To')!r}, not the sender")
        if "\\Draft" not in (draft.get("X-Fixture-Flags") or ""):
            problems.append(f"{fixture.key}: the appended message is not flagged \\Draft")
        return problems

    @staticmethod
    def _check_the_mailbox_is_the_seeded_one(client, delimiter: str, folders: set[str]) -> list[str]:
        """Refuse to report success against a mailbox that never held the fixtures.

        Every other check here is satisfied by an *empty* mailbox: nothing is misfiled, nothing is left unread, and no
        mail was sent. Logging into the wrong account therefore looked like a clean pass. This counts the messages the
        run should have accounted for and fails when they are simply not there.
        """
        reachable = {*folders, "INBOX"}
        found = sum(len(MailboxFixture._subjects_in(client, folder)) for folder in sorted(reachable))
        if found >= len(_FIXTURES):
            print(f"[verify] {found} message(s) across {len(reachable)} folder(s) — the seeded mail is here")
            return []
        return [
            f"only {found} of {len(_FIXTURES)} seeded message(s) are anywhere in this mailbox — seed it, or check "
            f"that the login matches the address the mail was sent to"
        ]

    @staticmethod
    def _check_inbox_is_drained(client) -> list[str]:
        """Filing is the only dedup, so anything left unread in the inbox would be reprocessed forever."""
        client.select_folder("INBOX", readonly=True)
        remaining = client.search(["UNSEEN"])
        if remaining:
            return [f"{len(remaining)} message(s) still unread in INBOX — the next run would reprocess them"]
        print("[verify] the inbox is drained")
        return []

    @staticmethod
    def _check_nothing_was_sent(api_port: int) -> list[str]:
        """The strongest available proof of the no-SMTP-path invariant.

        GreenMail is configured to accept mail for any address and creates a mailbox for each *recipient* it delivers
        to. The seeded mail is addressed to the shared mailbox, so that is the only mailbox that should ever exist. A
        reply the agent had actually sent would have been delivered to the customer's address, and a mailbox for it
        would be sitting right here. Its absence is the assertion.
        """
        mailboxes = MailboxFixture._mailboxes(api_port)
        if mailboxes is None:
            return ["could not read GreenMail's API — the no-send check did not run"]

        delivered_to_outsiders = sorted(box for box in mailboxes if box and box != _MAILBOX)
        if delivered_to_outsiders:
            return [f"GreenMail delivered mail to {delivered_to_outsiders} — the agent sent something"]
        print(f"[verify] {sorted(mailboxes)} is still the only mailbox — nothing was sent")
        return []

    @staticmethod
    def _mailboxes(api_port: int = _DEFAULT_API_PORT) -> set[str] | None:
        """Every address GreenMail has a mailbox for. `/api/mail` does not exist in 2.1.5; `/api/user` does."""
        try:
            with urllib.request.urlopen(f"http://{_HOST}:{api_port}/api/user", timeout=5) as response:
                payload = json.loads(response.read())
        except Exception as error:  # noqa: BLE001 - a probe, not a workflow step
            print(f"[verify] GreenMail API unreachable ({error})")
            return None
        return {entry.get("email", "") for entry in payload}

    @staticmethod
    def _subjects_in(client, folder: str) -> set[str]:
        client.select_folder(folder, readonly=True)
        uids = client.search(["ALL"])
        if not uids:
            return set()
        fetched = client.fetch(uids, ["ENVELOPE"])
        return {
            data[b"ENVELOPE"].subject.decode(errors="replace")
            for data in fetched.values()
            if data.get(b"ENVELOPE") and data[b"ENVELOPE"].subject
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["seed", "verify"])
    parser.add_argument("--delimiter", default="/", help="separator used in the configured category folder names")
    parser.add_argument("--drafts-folder", default="Drafts")
    parser.add_argument(
        "--api-port", type=int, default=_DEFAULT_API_PORT, help="host port GreenMail's API is mapped to"
    )
    args = parser.parse_args()

    if args.action == "seed":
        MailboxFixture.seed(args.api_port)
        return 0
    return 1 if MailboxFixture.verify(args.delimiter, args.drafts_folder, args.api_port) else 0


if __name__ == "__main__":
    sys.exit(main())
