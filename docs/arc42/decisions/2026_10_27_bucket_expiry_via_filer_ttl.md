# Bucket Expiry via SeaweedFS Filer TTL Rules

## Context

Four storage locations hold data that must expire on its own: `dagster` (op intermediates, 1 day), `parse-cache` (parsed
documents, 7 days), `sandbox-files/.deleted/` (files moved aside by the sandbox mirror, 7 days) and `agent-files` (files
uploaded to agents, 7 days). Up to SeaweedFS 4.01, `seaweedfs-init` and the API set them as S3 lifecycle configurations,
which SeaweedFS turned into a TTL rule in the filer's `filer.conf`. Every object written below the prefix carried that
TTL, and the volume server dropped whole volumes once they expired.

SeaweedFS 4.32 changed what a lifecycle configuration means. Rules are now enforced by a lifecycle job that an admin
server schedules on a worker, two services the platform does not run. Writing the TTL at write time became an opt-in per
bucket (the "fast path"). And from 4.24, applying or deleting a lifecycle configuration deletes the `filer.conf` TTL
rules 4.01 created for that bucket, a one-way migration. Because `seaweedfs-init` re-applies its lifecycle configurations on every
`docker compose up`, the upgrade deploy itself would have stopped expiry for every object written afterwards, with no
error anywhere. On a fresh install nothing would ever have expired, including user uploads promised to last 7 days.

## Decision Drivers

- *Same behaviour as before the upgrade*: every write path (single PUT, multipart upload, server-side copy) expires.
- *No new long-running services* to deploy, secure, monitor and replicate in Kubernetes.
- *Fixed retention*: the data is caches, intermediates, a soft-delete area and temporary uploads; nobody edits the rules
  at run time, and none of these buckets is versioned.
- *Visible, not blocking*: a deploy whose rules did not land must show it, but must not keep unrelated services down.

## Decision

- **Expiry is a filer TTL rule per path prefix**, written with `weed shell` `fs.configure -locationPrefix=… -ttl=…`
  (without `-collection`, which SeaweedFS rejects for bucket paths). The upstream wiki recommends this for "high-churn,
  non-versioned data with a fixed retention".
- **A one-shot `seaweedfs-ttl-init` service** (SeaweedFS image, `storage` network) applies the four rules on every run
  and exits 1 unless `filer.conf` holds each of them afterwards. `seaweedfs-init` depends on it with `service_started`,
  so every start of the bucket initialisation applies the rules too, without waiting for them to succeed: ClickHouse
  waits for `seaweedfs-init`, and a missing TTL rule must not keep ClickHouse and Langfuse down (Compose has no
  condition for "completed with any exit code"). The two run side by side, which is safe because a rule is a path prefix
  and needs no bucket. A failed run shows as `Exited (1)` with the missing rule in its log. A rule is a prefix, so it
  can be set before its bucket exists.
- **No S3 lifecycle configuration** on these buckets, neither in `seaweedfs-init` nor in the API. On existing
  deployments the rules 4.01 created are kept: the image change alone does not touch them, and the new init writes the
  same rules instead of re-applying a lifecycle configuration.

Rejected alternatives:

- *Admin + worker services*, upstream's default: per-object deletes that honour the current policy, S3-standard
  configuration and richer rules, but two more services, expiry up to a day late, space freed only by vacuum, and a
  subsystem that was redesigned repeatedly between 4.24 and 4.50.
- *The per-bucket fast path*: keeps the lifecycle configuration, but covers single PUTs only. Multipart uploads and
  server-side copies were written without a TTL in our tests, while 4.01 expired them.

## Consequences

- Expiry is fixed per object at write time. Changing a retention affects new objects only.
- On a fresh install the S3 lifecycle API reports `NoSuchLifecycleConfiguration` for these buckets. On a deployment
  upgraded from 4.01 it still returns the configuration 4.01 stored, which 4.51 does not enforce. Either way the rules
  that apply are the ones in `filer.conf` and in the `seaweedfs-ttl-init` log.
- Applying a lifecycle configuration to one of these buckets can delete its rule. The init script, the API and the
  deployment guide say so.
- Kubernetes deployments need the equivalent step.
- Switching to admin + worker later stays possible: add the services, re-apply lifecycle configurations, and remove the
  filer TTL rules deliberately.
