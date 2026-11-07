# Publication Closure Fixtures

<!-- words: jsonld py pytest readme workingdrafts xml nodeset nodesets -->
<!-- words: autocrlf gitattributes sha opcua semver tds tms vendoring -->

The [closure corpus](closure-corpus/) is one byte-pinned set of captured
publications for the [schema closure](../profiles/schema-closure.md) and
[composite closure](../profiles/composite-closure.md) profiles. Each case is a
publication package with its manifest, captured Registry JSON, documents and
closure descriptors, plus the expected result. Other repositories that
implement the same contract, such as the OPC UA WoT Binding, vendor a copy
and run their own checker against it.

## Layout

| Path | Contents |
| --- | --- |
| `cases.json` | Each case: its package, a description and the expected package, domain and runtime results. |
| `corpus-manifest.json` | Size and SHA-256 of every other file, and the corpus digest. |
| `packages/` | Publication package contexts, one for each case. |
| `manifests/` | Snapshot manifests. Some cases share one. |
| `registries/` | Captured Registry JSON for each profile and Registry variant. |
| `documents/` | Captured TDs, TMs, schemas, JSON-LD contexts and NodeSets. |
| `descriptors/` | Closure descriptors for the composite, schema, WoT and example OPC UA members. |

The OPC UA member in the corpus is the stand-in extension
`urn:example:opcua-materialization`, not the OPC UA WoT Binding's
materialization extension. All URIs use reserved example domains.

## Byte Pinning

`corpus-manifest.json` lists each file with its size and SHA-256, sorted by
path, and excludes itself. The corpus digest is the SHA-256 of one ASCII line
per listed file, in the same order:

```text
<sha256 hex>  <path>\n
```

`<path>` is relative to `closure-corpus/` and uses `/`. The repository's
`.gitattributes` marks the corpus `-text`, so Git does not convert line
endings on checkout, whatever `core.autocrlf` is set to. The files use LF.

## Commands

Run these from the repository root:

```text
python -B -m workingdrafts.publication.tools.build_closure_corpus --check
python -B -m workingdrafts.publication.tools.closure_checker
python -B -m pytest workingdrafts/publication/tools -q
```

The first command compares the corpus with the output of
[build_closure_corpus.py](../tools/build_closure_corpus.py). The second runs
the [reference checker](../tools/closure_checker.py) on every case and
compares its results with `cases.json`. The tests also check single
conditions on in-memory variants of the corpus.

The corpus is generated. To change it, edit the builder and run it without
`--check`; it rewrites the corpus and the manifest. Do not edit corpus files
by hand.

## Vendoring

A repository that vendors the corpus records the source repository, the
commit and the corpus digest. It copies the files byte for byte, keeps them
out of line-ending conversion, and verifies each file's SHA-256 and the corpus
digest against `corpus-manifest.json` before it runs any case. A changed
corpus digest is a new corpus version and needs a new pin.
