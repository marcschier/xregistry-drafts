# Portable Processing Samples

These fixtures demonstrate the WoT model's `wotprocessinggroups` resources and
the processing evidence envelope defined in
[spec.md](../../spec.md#54-processing-invocation-and-evidence).

- `processing-profile-definition.json` is the complete fixed definition for
  the bounded `resolve-definition` operation. Its digest is bound by
  `processing-profile.json`.
- `processing-profile.json` and the configuration documents are ordinary JSON
  documents. Every configuration is root-free; the local-only configuration
  has no provider rules, while the own-imported and shared configurations
  authorize one exact xRegistry scope and a registry-default selection.
- `processing-resources.xreg.json` shows the separate WoT Processing Group
  and its `stableprofileuri` and `configurationuri` identity attributes.
- `local-evidence.json` packages a local same-document `tm:ref`, with no
  external import, policy, or lock. `imported-evidence.json` packages a
  shared-configuration registry-default reference with its root-bound policy
  and lock. `own-imported-evidence.json` demonstrates the same exact authority
  selected from a caller-owned local configuration; it has no fabricated
  registry coordinates for that configuration. `registry-configuration-evidence.json`
  demonstrates the caller-owned configuration selected as an exact registry
  Version.
- `local-replay-pins.json` and `imported-replay-pins.json` are test-sidecar
  caller pins for the sample evidence. They are not evidence members and are
  not authority in a deployment; production callers obtain expected digests
  from their own trusted state.
- The files named in each `retainedArtifacts` manifest are separate retained
  artifacts. `archivePath` values are relative archive-member names, never
  host filesystem paths. Their exact bytes, not only their manifest entries,
  are included in this directory.

The fixtures are illustrative contract evidence, not a running processor,
registry resolver, trust system, or deployment integration. In particular,
the sample's fixed inline context is not a general-purpose JSON-LD context
processor.
