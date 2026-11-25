# WoT Registry Samples

<!-- words: WoT thingdescriptiongroups thingmodelgroups fabrikam wotid derivedfrom byom contoso standardsbody maturity affordance minversion versionorigin -->
<!-- words: factoryfloor inletpressure py -->
<!-- words: cloudevents descriptorid describedby thingdescription thingdescriptions affordances standalone affordanceselector -->
<!-- words: bundleurl nonselecting planurl tds marcschier opcuawriter -->

[registry.json](registry.json) illustrates document identity, compatible
Versions and provenance metadata using the [WoT Registry model](../model.json).
It contains the following lamp and vendor-model examples:

| Group | Content |
| --- | --- |
| `Fabrikam.Lighting` | A complete dimmable lamp Thing Model. Its authored `urn:fabrikam:lamp:v1` appears in `wotid`; its client-chosen Resource id is `urn.fabrikam.lamp.v1`. |
| `Fabrikam.FactoryFloor.01` | Lamp #42, a Thing Description with an absolute `rel: "type"` link to the lamp model. The TD's `derivedfrom` records the model's `wotid`. |
| `Contoso.Pumps` | Vendor-supplied pump and device Thing Models, including two compatible pump Versions. |

The Registry contains both the complete lamp model and its conforming Thing
Description. A Consumer holding either document's authored identifier queries
`wotid` to find the Resource.

Contoso stores its models as authored. Their `id` members and the pump's
`tm:extends` link remain unchanged. Both models have `"maturity": "Vendor"`
and omit `standardsbody`: Contoso publishes them, while `standardsbody`
records an organization that defines or endorses a document, not its author.

The pump defaults to `1.1.0` and retains `1.0.0` in its explicit `versions`
collection. Maturity and other metadata appear on each Version. The device has
one implicit Version, so those attributes appear on the Resource. Pump revision
`1.1.0` adds the OPTIONAL `inletPressure` affordance and no mandatory member.

Each TM's `versionid` matches its document's SemVer `version.model`, and its
`wotid` includes the major version. The lamp TD's `versionid` instead
matches `version.instance`. The pump's `tm:minVersion: "1.0.0"` requires a
device-model revision at or above 1.0.0. This is a proposed WoT extension,
not a member defined by the published WoT 1.1 Recommendation.

The [registry sample](registry.json) illustrates document and Version
metadata, not a series of write requests. Clients can omit `versionorigin`
from a write: the Registry assigns it under the
[versioning rules](../spec.md#13-versioning).

[publication-closure.json](publication-closure.json) separately illustrates the
[proposed closure envelope](../../../publication/design/design.md#selection-and-acceptance).
It is neither Registry content nor a complete snapshot.
[Checking the sample against the closure schema](../tests/test_wot_examples.py)
establishes its shape, not snapshot coverage or correct target selection.

## CloudEvents document provision

[cloudevents.json](cloudevents.json) contains two standalone CloudEvents as
sample data, not a transport batch. Using the
[proposed WoT profile](../spec.md#531-cloudevents-wot-source-resolution),
they identify the same lamp TD Version and optionally an event affordance.
The first event's `source` is absolute and the second event's `source` is
relative. The profile does not prescribe a URI scheme. Their `subject` values
label the Thing for filtering, not document selection. Each event's
`describedby` URL selects the exact Version of `lamp-42-temperature` or
`lamp-42`, respectively. The Descriptor examples omit other Core metadata:

```json
[
  {
    "descriptorid": "lamp-42-temperature",
    "versionid": "1",
    "entries": {
      "lamp42": {
        "class": "thingdescription",
        "url": "https://registry.example/thingdescriptiongroups/Fabrikam.FactoryFloor.01/thingdescriptions/urn.fabrikam.lamp.42/versions/1.0.0",
        "affordanceselector": "/events/overheated"
      }
    }
  },
  {
    "descriptorid": "lamp-42",
    "versionid": "1",
    "entries": {
      "lamp42": {
        "class": "thingdescription",
        "url": "https://registry.example/thingdescriptiongroups/Fabrikam.FactoryFloor.01/thingdescriptions/urn.fabrikam.lamp.42/versions/1.0.0"
      }
    }
  }
]
```

Each entry's `url` identifies the lamp TD Version's document. The first
Descriptor's plain JSON Pointer selects `/events/overheated`; the second
omits the selector for the whole Thing. The sample TD declares that event
affordance directly.

[descriptor-entry.json](descriptor-entry.json) also supplies the first
Descriptor as a separate sample. The CloudEvents profile determines when a
chosen entry name or a unique TD entry selects it and when repeated TDs are
ambiguous. A TM entry can bind an event type and model declaration; it does
not replace a TD's instance description.

TD and TM entries require retrievable `url` values under the
[CloudEvents WoT profile][CloudEvents WoT]; `null` is invalid. Inline-only
classes omit `url` under their own profiles. A projection plan supplied
through `planurl` is provenance for the ordinary resolved document, not a
replacement for it. Bundle assembly and `bundleurl` follow that contract.

For events using both WoT and OPC UA, the same Descriptor supplies the WoT
entry and any Descriptor-based OPC UA metadata. Native identity can come
from the envelope, `source` query parameters or the selected `opcuawriter`
entry. The [OPC UA mapping][CloudEvents OPC UA] defines these rules and
allows OPC UA-only events without a Descriptor.

Both events use `com.fabrikam.lamp.overheated.v1` as their `type`. Their
payload contract defines a numeric `temperature` member; the different values
and TD selection do not change that contract. The example's naming
convention uses the final `v1` for the payload contract revision, independently of the TD's
`version.instance` or Registry `versionid`. Under that convention, adding a
payload member, even one whose presence is not mandatory, would use a new
contract revision.

The samples do not claim that the proposed closure envelope can reconstruct
a composed TD or that an event version proves content integrity.

[CloudEvents WoT]: https://github.com/marcschier/spec/blob/6ac67d40c38e63621d32f29c9f1a0d69c2d583da/cloudevents/extensions/wot.md
[CloudEvents OPC UA]: https://github.com/marcschier/spec/blob/6ac67d40c38e63621d32f29c9f1a0d69c2d583da/cloudevents/extensions/opcua.md#wot-mapping
