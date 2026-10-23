# Portable Processing Samples

These fixtures show the WoT model's `wotprocessinggroups` Resources and the
processing evidence envelope defined in
[spec.md](../../spec.md#54-processing-invocation-and-evidence).

- `processing-profile-definition.json` contains the complete fixed definition
  for the bounded `resolve-definition` operation. `processing-profile.json`
  binds its digest.
- `processing-profile.json` and the configuration documents are ordinary JSON
  documents. Each configuration is root-free. The local-only configuration
  has no provider rules; the own-imported and shared configurations each name
  one exact xRegistry scope and a registry-default selection.
- `processing-resources.xreg.json` contains the separate WoT Processing Group
  and its `stableprofileuri` and `configurationuri` attributes.
- `local-evidence.json` packages a local same-document `tm:ref`, with no
  external import, policy, or resolution record. `imported-evidence.json` packages a
  shared-configuration registry-default reference with its root-bound policy
  and resolution record. `own-imported-evidence.json` selects the same authority from a
  caller-owned local configuration, without inventing registry coordinates
  for that configuration. `registry-configuration-evidence.json` selects a
  caller-owned configuration by exact registry Version.
- `local-replay-pins.json` and `imported-replay-pins.json` contain test-sidecar
  caller pins for the sample evidence. They are not evidence members or
  deployment authority. Production callers obtain expected digests from
  their own trusted state.
- The files named in each `retainedArtifacts` manifest are separate retained
  artifacts. `archivePath` values are relative archive-member names, never
  host filesystem paths. Their exact bytes, not only their manifest entries,
  are included in this directory.

The fixtures document the evidence contract; they are not a running
processor, registry resolver, trust system, or deployment integration. The
sample's fixed inline context is not a general-purpose JSON-LD context
processor.
