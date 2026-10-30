# Uncategorised Mail Kept in the Inbox Is Tracked by an Inbox UID Watermark

## Context

The email classification agent reads the unread mail in a profile's inbox on every run and files each message into a
folder: its category's, the fallback folder for mail that fits none, or the failure folder. Moving a message out of the
inbox is also its only dedup: the next run's unread listing cannot see a message that has left.

A customer starting with a single category wants everything else to stay in the inbox, unread, instead of moving to the
fallback folder. A message left there unread would be listed, archived and classified again on every run, at full model
cost, and old mail would crowd new mail out of every batch. Something other than the move has to mark it as processed,
without marking it read.

The obvious marker is a custom IMAP keyword on the message, which `ImapAgent` already uses for its drafting dedup
(`$AiHubDrafted`). Microsoft 365, which this customer uses, does not accept one: a writable `SELECT INBOX` on
`outlook.office365.com` returns `PERMANENTFLAGS (\Seen \Answered \Flagged \Deleted \Draft $MDNSent $Forwarded)`, with no
`\*`.

## Decision Drivers

- The marker must work on Microsoft 365, Gmail and Dovecot alike.
- The message must stay exactly as the person reading the mailbox left it: unread, with no flag that means something to
  them.
- New mail must still be found, and a message dragged back into the inbox must still be retried.
- Default behaviour is unchanged for every existing profile.

## Decision

- A new setting, `EmailClassificationSettings.keep_uncategorised_in_inbox`, off by default. With it on, a decline stays
  in the inbox; categorised mail still moves and a failure still goes to the failure folder.
- **The record is an inbox UID watermark held in Valkey.** `InboxWatermark` stores, per profile, the highest inbox UID a
  run has classified, together with the inbox's UIDVALIDITY and the mailbox it describes, next to `MailboxRunLease`.
- **Listing starts above the watermark, lowest UID first** (`ImapClient.list_unread_above`): `UNSEEN UID n+1:*`,
  filtered client-side because `UID n:*` always names the highest UID, even one below `n`. Lowest UID first rather than
  oldest sent, because advancing the watermark to the batch's highest UID is only sound when every unread UID below it
  was in the batch.
- **The watermark advances after filing succeeds and before drafting.** A run that fails mid-batch leaves it where it
  was, so the next run re-lists what was not finished. Once filing is done the batch sits below the watermark, so a
  concurrent run cannot pick it up while this run drafts, which keeps `MailboxRunLease.reacquire` sound.
- A UIDVALIDITY or mailbox mismatch counts as no watermark: the whole unread inbox is listed again rather than skipped.

## Considered Alternatives

- **Custom IMAP keyword** (`$AiHubClassified`): self-contained in the mailbox, but rejected by Microsoft 365.
- **A system flag** (`\Answered`, `\Flagged`, `$MDNSent`, `$Forwarded`): accepted everywhere, but each one tells the
  reader something false (replied, flagged, read receipt sent, forwarded) and some clients act on it.
- **A stored set of processed UIDs or Message-IDs**: grows without bound in a mailbox that keeps most of its mail, and
  excluding it server-side means an ever longer `SEARCH`.

## Consequences

- Losing the Valkey key, or the server renumbering the inbox, costs one more classification of the unread mail kept in
  the inbox. It never skips a message.
- A message the user marks unread again after it was classified is not classified again: it is below the watermark.
- Moving a message back into the inbox gives it a new, higher UID, so it is classified again. That stays the way to
  retry a failure.
- Mail is classified in arrival order rather than sent order while the setting is on. In an inbox the two agree almost
  everywhere.
- `UnreadMailListedEvent` carries the listing's UIDVALIDITY (`uid_validity`, `None` for a plain listing), so the run
  advances the watermark in the UID space it listed from.
