# Secret Masks Carry an Identity Handle

## Context

Secret configuration fields are encrypted at rest and replaced with a mask in API responses. A client that
resubmits the mask unchanged means "keep the stored secret", so the server has to work out which stored
secret a given mask stands for.

The first implementation matched them by position: the nth mask in the submission took the nth stored
secret. That holds only while submission and storage list the same secrets in the same order. An announced
form turns any `list[Form]` field into a repeated section, and a repeated section offers the user controls
to reorder, delete and insert rows. Moving a row therefore handed its credential to a different row,
silently, with the masked response identical before and after.

## Decision Drivers

- **Correctness under editing** Reordering, deleting or inserting a row must not move a secret between rows.
- **Fail closed** An unresolvable mask must raise, never fall back to a guess or to an empty value.
- **No new stored state** The round trip must not require a server-side table of issued masks.
- **Nothing leaks** A mask must reveal neither the secret nor its ciphertext, including for rows that still
  hold plaintext from before encryption existed.

## Decision

A mask is `<mask>:<handle>`, where the handle is an HMAC-SHA256 of the stored value under a key derived
from the encryption key, truncated to 16 hex characters. Restoring a submission builds a handle-to-secret
map from the stored document and resolves each mask through it, so position carries no meaning.

The HMAC is keyed rather than a plain digest because `decrypt` passes plaintext through unchanged, so rows
written before encryption still hold plaintext passwords. Publishing an unkeyed digest of one would be an
offline dictionary attack on a low-entropy secret. Handles are looked up in a dict rather than compared
with `hmac.compare_digest`: the server is not verifying an attacker-supplied MAC against a computed one,
and forging a handle would only move a credential between rows of a document the caller can already edit.

`SecretMasker` merged into `SecretEncryptionService`. Masking now needs the key, and the service already
depended on the masker for the mask constant, so keeping them apart would have closed an import cycle.

## Consequences

Clients must treat the mask as a **prefix** and the remainder as opaque, matching with "starts with" rather
than equality, and returning it verbatim. This is the contract the frontend work in #1588 and #1722 builds
against.

Masking and restoring have to be handed the same representation of the stored document, normally the
encrypted one straight from the database. Masking one representation and restoring against another makes
every handle miss, which fails closed but is easy to misdiagnose.

Rotating the encryption key changes both the ciphertext and the handles, so any form open in a browser at
rotation time fails on save and has to be reloaded. Two rows holding the same secret produce the same
handle; they restore correctly, and the only disclosure is that the two rows share a credential.

Whether a secret field absent from a submission means "unchanged" or "delete" is still undefined, and
belongs to the layer that writes to the database rather than here.
