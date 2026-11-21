# WoT Registry Samples

<!-- words: WoT thingdescriptiongroups thingmodelgroups fabrikam wotid derivedfrom byom contoso standardsbody maturity affordance minversion versionorigin -->
<!-- words: factoryfloor inletpressure cloudevents describedby descriptorid -->
<!-- words: thingdescription thingdescriptions affordanceselector -->
<!-- words: affordances bundleurl nonselecting planurl standalone tds -->
<!-- words: marcschier opcuawriter -->

[registry.json](registry.json) illustrates the
[WoT Registry model](../model.json): stable authored identifiers, compatible
Versions and provenance metadata.

| Group | Content |
| --- | --- |
| `Fabrikam.Lighting` | The complete dimmable lamp Thing Model, indexed by its authored `wotid`. |
| `Fabrikam.FactoryFloor.01` | Lamp #42, with an absolute `rel: "type"` link to the lamp model and its identifier in `derivedfrom`. |
| `Contoso.Pumps` | Authored pump and device Thing Models, including two compatible pump Versions. |

The pump defaults to `1.1.0` and retains `1.0.0`. Revision `1.1.0` adds
the OPTIONAL `inletPressure` affordance without adding a mandatory member.
Both models retain their authored identifiers and references; their
`maturity` is `Vendor`, without a `standardsbody` claim.

TM `versionid` values match authored `version.model`; the lamp TD's
`versionid` matches `version.instance`. The pump's `tm:minVersion: "1.0.0"`
requires a compatible device model. The publication requests omit
`versionorigin`; the registry assigns it.

[publication-closure.json](publication-closure.json) illustrates the
[closure envelope](../../../publication/design/design.md#selection-and-acceptance).
It is not a complete snapshot. Its checks validate shape, not whether the
captured dependencies reconstruct a resolved view.

## CloudEvents document provision

The [CloudEvents WoT draft][CloudEvents WoT] defines Descriptor entry shape,
class-owned metadata, selection and failure outcomes. The registry supplies
the ordinary resolved TD/TM documents under its
[document-provision rules](../spec.md#66-provisioning-documents-for-cloudevents).

[cloudevents.json](cloudevents.json) contains a standalone event example,
not a transport batch. It uses `com.fabrikam.lamp.overheated.v1` and the
agreed numeric `temperature` payload contract. `describedby` identifies the
Descriptor Version. `source` identifies the telemetry service and `subject`
labels the lamp for filtering; neither selects a document.

[descriptor-entry.json](descriptor-entry.json) shows one named entry inside
the Descriptor used by these event examples.
Its `lamp42` entry has class `thingdescription`, an ordinary TD document
URL, and the OPTIONAL plain JSON Pointer `affordanceselector` selecting
`/events/overheated`.

The entry URL serves the resolved lamp TD at Version `1.0.0`, not Registry
metadata. Removing `affordanceselector` leaves the whole Thing available
under the class's profile rules. The CE profile determines when a chosen
entry name or a unique TD entry selects it and when repeated TDs are
ambiguous. A TM entry can bind an event type and model declaration; it does
not replace a TD's instance description.

TD and TM entries require retrievable `url` values under the CE profile;
`null` is invalid. Inline-only classes omit `url` under their own profiles.
A projection plan, when supplied through `planurl`,
is provenance for the ordinary resolved document, not a replacement for it.
Bundle assembly and `bundleurl` follow the CE contract.

The stored selector is a plain RFC 6901 string. The lamp TD declares its
affordances directly, so no reconstruction is needed to select the event.
For events using both WoT and OPC UA, the same Descriptor supplies the WoT
entry and any Descriptor-based OPC UA metadata. Native identity can come
from the envelope, `source` query parameters or the selected `opcuawriter`
entry. The [OPC UA mapping][CloudEvents OPC UA] defines these rules and
allows OPC UA-only events without a Descriptor.

[CloudEvents WoT]: https://github.com/marcschier/spec/blob/6ac67d40c38e63621d32f29c9f1a0d69c2d583da/cloudevents/extensions/wot.md
[CloudEvents OPC UA]: https://github.com/marcschier/spec/blob/6ac67d40c38e63621d32f29c9f1a0d69c2d583da/cloudevents/extensions/opcua.md#wot-mapping
