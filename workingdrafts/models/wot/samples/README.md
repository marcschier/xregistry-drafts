# WoT Registry Samples

<!-- words: WoT thingdescriptiongroups thingmodelgroups schemagroups messagegroups fabrikam lamp smartlamp -->
<!-- words: wotid derivedfrom byom contoso standardsbody maturity -->
<!-- words: wotprocessinggroups processingprofiles processingconfigurations -->

The sample documents illustrate the WoT Registry model in
[../model.json](../model.json):

- [lamp-tm.xreg.json](lamp-tm.xreg.json) — a minimal `thingmodelgroups`
  document with one Thing Model for a generic dimmable lamp. The authored
  identifier `urn:fabrikam:lamp` appears in `wotid`; the client chose
  `urn.fabrikam.lamp` as the Resource id. A Consumer holding the authored
  identifier finds the Resource by querying `wotid`.
- [lamp-td.xreg.json](lamp-td.xreg.json) — a `thingdescriptiongroups` document
  with a Thing Description (`urn:fabrikam:lamp:42`) that conforms to the lamp
  Thing Model. Its `links[].rel = "type"` entry uses the absolute document-view
  URL; `derivedfrom` records the TM's authored `wotid`.
- [byom-pump-tm.xreg.json](byom-pump-tm.xreg.json) — a bring-your-own-model
  example. It stores two vendor-supplied Thing Models as authored, preserving
  their `id` members and the `tm:extends` link. Their authored identifiers
  appear in `wotid` and `derivedfrom`. Both models are marked
  `"maturity": "Vendor"` and omit `standardsbody`: Contoso publishes them, but
  does not define them as a standards body would. The pump has two Versions;
  `2` is the default and `.../versions/1` retrieves the earlier one. Because
  the pump has an explicit `versions` collection, its attributes—including
  provenance—appear on each Version. The device has one implicit Version, so
  its attributes appear on the Resource. The sample shows both forms; a
  `versions` collection is needed only when a Resource has multiple Versions.

- [smartlamp-wot.xreg.json](smartlamp-wot.xreg.json) — an end-to-end scenario
  with a Thing Model and a conforming Thing Description in one registry
  document. The instance records `derivedfrom` and a `links[].rel = "type"`
  reference to the Thing Model Resource.
- [resolution-evidence.xreg.json](resolution-evidence.xreg.json) — a Thing
  Model with nonnumeric Core Version IDs, a sticky default, optional policy
  and record attachments on each Version, and a separate resolution fixture.
  The record captures Version `7` while the later default is `8`; replay uses
  the retained Version-7 artifact, not the current default. This evidence
  illustrates the contract; it is not a running resolver.
- [processing](processing/README.md) — portable processing profile and
  configuration documents, a WoT Processing Group, and local and imported
  invocation evidence. Each invocation selects one configuration; the samples
  do not merge configurations or authorize deployment.
