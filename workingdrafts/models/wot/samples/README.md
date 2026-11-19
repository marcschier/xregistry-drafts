# WoT Registry Samples

<!-- words: WoT thingdescriptiongroups thingmodelgroups fabrikam wotid derivedfrom byom contoso standardsbody maturity affordance minversion versionorigin -->
<!-- words: factoryfloor inletpressure -->
<!-- words: cloudevents wotversion wotdigest topology percent affordances standalone -->
<!-- words: thingref affordanceselector quantitykind describedby marcschier descriptorgroups -->
<!-- words: descriptorid thingdescription thingdescriptions -->
<!-- words: lampmodel modelref schemaref thingmodel -->

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

[cloudevents.json](cloudevents.json) contains five standalone CloudEvents as
sample data, not a transport batch. They refer to the lamp TD's resolved view
using the routes in the
[committed CloudEvents WoT extension draft][CloudEvents WoT].
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

All five events use `com.fabrikam.lamp.overheated.v1`. Their payload contract
defines a numeric `temperature` member; the different values and TD selection
do not change that contract. The publication profile assigns the final `v1`
segment independently of the TD's `version.instance` and Registry `versionid`.
Adding a payload member, even an OPTIONAL one, requires a new contract revision.

Neither of the first two events uses `describedby` or requires a Descriptor.
These events need
only the selected TD and the agreed payload contract. Their wire schema is
not inferred from the TD's inline DataSchema; a profile requiring an external
payload schema would supply `dataschema` or a complete Descriptor.
The samples do not claim that the proposed closure envelope can reconstruct
a composed TD or that an event version proves content integrity.

[subject-descriptor.json](subject-descriptor.json) describes the same lamp
event affordance using the
[Subject Descriptor profile](../spec.md#664-subject-descriptors). Core
bookkeeping is omitted. `data.wot.subject.thingref` selects the exact name
in `references.thingdescription`; its `affordanceselector` is a nonempty
JSON Pointer string selecting one event affordance, without a leading `#`.
This example's deployment defines `quantitykind` as an absolute-URI string
identifying the measured quantity. It is an annotation, not authorization
or a universal WoT vocabulary. It appears beside the subject's selector.
Omitting the selector describes the whole Thing; subject annotations then
describe that Thing:

```json
{
  "descriptorid": "lamp-42",
  "versionid": "1",
  "description": "Lamp on the factory floor",
  "data": {
    "wot": {"subject": {"thingref": "lamp42"}}
  },
  "references": {
    "thingdescription": {
      "lamp42": {
        "url": "https://example.com/thingdescriptiongroups/Fabrikam.FactoryFloor.01/thingdescriptions/urn.fabrikam.lamp.42/versions/1.0.0"
      }
    }
  }
}
```

The third event in `cloudevents.json` selects the Subject Descriptor at an
exact Version URL without a fragment; the event envelope is unchanged.

The agreed URL binding identifies that exact Descriptor Version; spelling
`versions` in a URL alone does not establish Version identity. The Subject
Descriptor selects `/events/overheated` in the lamp TD at Version `1.0.0`.
The Consumer does not retrieve the source or use Subject Descriptor schemas
as processing inputs. Here the event and agreed payload contract supply the
remaining inputs. The [CloudEvents review](https://github.com/cloudevents/spec/pull/1406)
aligns the binding with `data.wot.subject` and `data.wot.event`;
the pinned draft uses an earlier representation.

If the event also supplies `describedby`, that Processing Descriptor remains
authoritative and MUST contain exactly one TD Reference with the same URL.
Zero matches or duplicate URLs fail correlation even though
`data.wot.subject.thingref` selects a unique local entry in the Subject
Descriptor. Only `references.thingdescription` participates in that URL
match. Reference names are unique across all type buckets. The Consumer
does not merge missing processing inputs from the
Subject Descriptor or retry another route.

The fourth event demonstrates this explicit `describedby` case. Its direct
TD subject URL matches the Descriptor's `lamp42` Reference exactly. This
Descriptor is selected for processing; its `data.wot.subject` selector
does not replace the event's direct TD pointer.

The fifth event uses that same Descriptor Version URL as `source`, omits
`describedby` and selects `lamp42#/events/overheated`. The agreed
source-Descriptor binding selects it as the Processing Descriptor. This
example intentionally identifies the Descriptor as the originating context;
it has a different source-plus-id identity scope from the actor-source
examples. The named subject selects the TD Reference, not the Descriptor's
`data.wot.subject` selector. The agreed payload contract supplies the
processing inputs; these examples need no external payload schema.

Inline profile metadata belongs in `data.<type>`, with its shape defined by
that type's profile.
`data.wot.subject.quantitykind` annotates the subject, not a selector object.
Independent `data.wot.event` binds a full event type to a TM Reference:

```json
{
  "data": {
    "wot": {
      "event": {
        "type": "com.fabrikam.lamp.overheated.v1",
        "modelref": "lampmodel",
        "affordanceselector": "/events/overheated"
      }
    }
  },
  "references": {
    "thingmodel": {"lampmodel": {"url": "https://example.com/tm/lamp/versions/1.0.0"}}
  }
}
```

Core bookkeeping is omitted. The TM declares that event. When this
Descriptor is selected for processing, CE defines the exact type check;
the profile then resolves `modelref` and its OPTIONAL declaration selector.
Presence alone does not trigger a TM fetch. Subject and event objects can
occur separately or together; neither changes `data.schema.schemaref`.

[CloudEvents WoT]: https://github.com/marcschier/spec/blob/1c4caca73c69a7e076e75fe0727f6a216c83e500/cloudevents/extensions/wot.md
