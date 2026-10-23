# WoT Registry Samples

<!-- words: WoT thingdescriptiongroups thingmodelgroups schemagroups messagegroups fabrikam lamp smartlamp -->
<!-- words: wotid derivedfrom byom contoso standardsbody maturity -->
<!-- words: wotprocessinggroups processingprofiles processingconfigurations -->

This directory contains illustrative sample documents that exercise the
WoT Registry model defined in [../model.json](../model.json):

- [lamp-tm.xreg.json](lamp-tm.xreg.json) — a minimal `thingmodelgroups`
  document containing a single Thing Model for a generic dimmable lamp. Its
  authored identifier `urn:fabrikam:lamp` is carried in `wotid`, while
  `urn.fabrikam.lamp` is the Resource id the client chose for it; a Consumer
  holding the authored identifier finds the Resource by querying `wotid`.
- [lamp-td.xreg.json](lamp-td.xreg.json) — a `thingdescriptiongroups` document
  containing a Thing Description (`urn:fabrikam:lamp:42`) that conforms to the
  lamp Thing Model above. Its `links[].rel = "type"` entry references the TM
  by absolute document-view URL, and its `derivedfrom` attribute records the
  TM's authored `wotid`.
- [byom-pump-tm.xreg.json](byom-pump-tm.xreg.json) — a bring-your-own-model
  example. Two vendor-supplied Thing Models are stored exactly as authored:
  their `id` members and the `tm:extends` link between them are untouched, and
  the authored identifiers are carried alongside the documents in `wotid` and
  `derivedfrom`. Both are marked `"maturity": "Vendor"` and carry no
  `standardsbody`, because Contoso publishes them itself; a `standardsbody` is
  a claim about who defines a document, not about who wrote it. The pump has
  two Versions, with `2` as the default, so retrieving the Resource yields the
  default while `.../versions/1` yields the earlier one. Because the pump
  supplies an explicit `versions` collection, its attributes — including the
  provenance attributes an agent uses to prefer an official model — are
  carried on each Version rather than on the Resource; the device, which has a
  single implicit Version, carries them on the Resource directly. Showing both
  shapes in one file is deliberate: the `versions` collection is only needed
  when a Resource has more than one Version.

- [smartlamp-wot.xreg.json](smartlamp-wot.xreg.json) — an end-to-end scenario
  combining a Thing Model and a Thing Description that conforms to it in a
  single registry document, showing how `thingmodelgroups` and
  `thingdescriptiongroups` compose: the instance carries `derivedfrom` and a
  `links[].rel = "type"` reference to the Thing Model Resource.
- [resolution-evidence.xreg.json](resolution-evidence.xreg.json) — a Thing
  Model with nonnumeric Core Version IDs, a sticky default, per-Version
  optional policy/record attachments, and a separately stored resolution
  fixture. The record captures Version `7` while the later default is `8`;
  replay is pinned to the retained Version-7 artifact, not the current
  default. This is illustrative evidence, not a running resolver.
- [processing](processing/README.md) — portable processing profile and
  configuration documents, a WoT Processing Group, and local/imported
  invocation evidence packages. Configurations are selected individually;
  the samples do not merge them or authorize deployment.
