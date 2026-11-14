# WoT Registry Samples

<!-- words: WoT thingdescriptiongroups thingmodelgroups fabrikam wotid derivedfrom byom contoso standardsbody maturity affordance minversion versionorigin -->
<!-- words: factoryfloor inletpressure -->
<!-- words: cloudevents wotversion wotdigest topology percent affordances standalone -->

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

[cloudevents.json](cloudevents.json) contains two standalone CloudEvents as
sample data, not a transport batch. They refer to the lamp TD's resolved view
using the direct TD subject route in the
[committed CloudEvents WoT profile draft][CloudEvents WoT].
The [Registry-side publication rules](../spec.md#531-cloudevents-wot-source-resolution)
require the selected document to contain that resolved view. The first
`source` identifies a factory line; the second identifies an actor. Neither
source is a TD retrieval instruction or carries WoT lookup parameters.

The first subject identifies the lamp TD's document-view URL at Version
`1.0.0`, matching its `version.instance` and Registry `versionid`, followed
by `#/events/overheated`. The Consumer retrieves the fragment-free URL and
applies the pointer to the resolved TD. This sample's TD declares its
affordances directly, so that pointer selects the locally declared event.
The second subject identifies the same Resource without a Version and uses
`#` for the whole resolved TD. It selects the current default, which can
change after publication. The publication profile defines the second
event's payload as a temperature report concerning the whole Thing.

Both events use `com.fabrikam.lamp.overheated.v1`. Their payload contract
defines a numeric `temperature` member; the different values and TD selection
do not change that contract. The publication profile assigns the final `v1`
segment independently of the TD's `version.instance` and Registry `versionid`.
Adding a payload member, even an OPTIONAL one, requires a new contract revision.

Neither event uses `describedby` or requires a Descriptor. These events need
only the selected TD and the agreed payload contract. Their wire schema is
not inferred from the TD's inline DataSchema; a profile requiring an external
payload schema would supply `dataschema` or a complete Descriptor.
The samples do not claim that the proposed closure envelope can reconstruct
a composed TD or that an event version proves content integrity.

[CloudEvents WoT]: https://github.com/marcschier/spec/blob/2b122bb9ea420b24ffccb53c6e0a05c20082ac7a/cloudevents/extensions/wot.md
