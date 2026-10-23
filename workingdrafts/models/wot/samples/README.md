# WoT Registry Samples

<!-- words: WoT thinggroups things schemagroups messagegroups fabrikam lamp smartlamp -->
<!-- words: ThingDescription ThingModel ThingProjection -->
<!-- words: wotid derivedfrom byom contoso standardsbody maturity -->

This directory contains illustrative sample documents that exercise the
WoT Registry model defined in [../model.json](../model.json). Every sample
uses the same `thinggroups` / `things` layout and the `thing` document
attribute. `kind` is registry metadata beside the document, not part of its
JSON-LD contents:

- [lamp-tm.xreg.json](lamp-tm.xreg.json) — a minimal `thinggroups`
  document containing a single `kind=ThingModel` document for a generic dimmable lamp. Its
  authored identifier `urn:fabrikam:lamp` is carried in `wotid`, while
  `urn.fabrikam.lamp` is the Resource id the client chose for it; a Consumer
  holding the authored identifier finds the Resource by querying `wotid`.
- [lamp-td.xreg.json](lamp-td.xreg.json) — a `thinggroups` document
  containing a `kind=ThingDescription` document (`urn:fabrikam:lamp:42`) that conforms to the
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
  latest while `.../versions/1` yields the earlier one. Because the pump
  supplies an explicit `versions` collection, its attributes — including the
  provenance attributes an agent uses to prefer an official model — are
  carried on each Version rather than on the Resource. This includes
  `kind=ThingModel` on both Versions. The device, which has a
  single implicit Version, carries them on the Resource directly. Showing both
  shapes in one file is deliberate: the `versions` collection is only needed
  when a Resource has more than one Version.

- [smartlamp-wot.xreg.json](smartlamp-wot.xreg.json) — an end-to-end scenario
  combining a Thing Model, a Thing Description that conforms to it, and a
  provisional Thing Projection in
  the same `Fabrikam.Lighting` Group and `things` collection. Their different
  `kind` values distinguish them; the instance carries `derivedfrom` and a
  `links[].rel = "type"` reference to the Thing Model Resource. The TD and TP
  intentionally share a `wotid` under distinct Resource ids, illustrating
  `(kind, wotid)` lookup without declaring TP lineage.

- [lamp-tp.xreg.json](lamp-tp.xreg.json) — a minimal provisional
  `kind=ThingProjection` envelope with `application/json` and JSON-LD 1.1.
  It illustrates registry storage and filtering only, not a standardized TP
  vocabulary or lineage contract.

For example, against the smart-lamp registry:

```http
GET /thinggroups/Fabrikam.Lighting/things?filter=kind=ThingModel
GET /?filter=thinggroups.things.kind=ThingDescription&inline=thinggroups.things
GET /thinggroups/Fabrikam.Lighting/things/urn.fabrikam.lamp?filter=kind=ThingModel
```

The first query returns only the model metadata; the second returns the
instance metadata under its Group. The third returns the model document.
Changing the third query's kind to `ThingProjection` returns `404 Not Found`,
not the model. See [kind-filtered access](../spec.md#531-kind-filtered-discovery-and-access)
for combined filters, pinned Versions, and pagination.
