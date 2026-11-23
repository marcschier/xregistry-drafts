# WoT Registry Samples

<!-- words: WoT thingdescriptiongroups thingmodelgroups fabrikam wotid derivedfrom byom contoso standardsbody maturity affordance minversion versionorigin -->
<!-- words: factoryfloor inletpressure -->
<!-- words: cloudevents descriptorid describedby thingdescription thingdescriptions affordances standalone affordanceselector -->
<!-- words: bundleurl nonselecting planurl tds marcschier opcuawriter -->

[registry.json](registry.json) illustrates document identity, compatible
Versions and provenance metadata using the [WoT Registry model](../model.json).
It contains the following lamp and vendor-model examples:

| Group | Content |
| --- | --- |
| `Fabrikam.Lighting` | A complete dimmable lamp Thing Model. Its authored `urn:fabrikam:lamp:v1` appears in `wotid`; its client-chosen Resource id is `urn.fabrikam.lamp.v1`. |
| `Fabrikam.FactoryFloor.01` | Lamp #42, a Thing Description with an absolute `rel: "type"` link to the lamp model and its authored identifier in `derivedfrom`. |
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
identifier includes the major version. The lamp TD's `versionid` instead
matches `version.instance`. The pump's `tm:minVersion: "1.0.0"` requires a
device-model revision at or above 1.0.0. This is a proposed WoT extension,
not a member defined by the published WoT 1.1 Recommendation.

The publication requests omit `versionorigin` because the model initializes
it to `authored`. The registry remains responsible for assignment.

[publication-closure.json](publication-closure.json) separately illustrates the
[proposed closure envelope](../../../publication/design/design.md#selection-and-acceptance).
It is neither Registry content nor a complete snapshot. Its checks validate
shape only.

## CloudEvents document provision

[cloudevents.json](cloudevents.json) contains two standalone CloudEvents as
sample data, not a transport batch. They refer to the lamp TD's resolved view
using the [proposed WoT profile](../spec.md#531-cloudevents-wot-source-resolution).
The absolute first `source` and relative second `source` illustrate that the
profile does not prescribe a URI scheme. Their `subject` values label the Thing
for filtering, not document selection. Each event's `describedby` selects one
of these Descriptor Versions; other Core metadata is omitted:

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

Both events use `com.fabrikam.lamp.overheated.v1`. Their payload contract
defines a numeric `temperature` member; the different values and TD selection
do not change that contract. The publication profile assigns the final `v1`
segment independently of the TD's `version.instance` and Registry `versionid`.
Adding a payload member, even an OPTIONAL one, requires a new contract revision.

The samples do not claim that the proposed closure envelope can reconstruct
a composed TD or that an event version proves content integrity.

[CloudEvents WoT]: https://github.com/marcschier/spec/blob/6ac67d40c38e63621d32f29c9f1a0d69c2d583da/cloudevents/extensions/wot.md
[CloudEvents OPC UA]: https://github.com/marcschier/spec/blob/6ac67d40c38e63621d32f29c9f1a0d69c2d583da/cloudevents/extensions/opcua.md#wot-mapping
