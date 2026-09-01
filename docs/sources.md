# Sources and Provenance

Cognivia grounds its primary workflow in a repository-local knowledge base
under `data/knowledge_base/`.

## Supported source formats

The current loader recursively reads:

- Markdown files;
- PDF files.

Loaded documents are split into token-aware chunks. Source paths, headings, and
other available metadata are retained so retrieval results can carry
provenance into the application graph.

## Index integrity

The local Qdrant index records a source manifest containing:

- source path;
- file size; and
- file modification time.

The stored metadata also records the index schema version and embedding
identity: provider, model, and base URL. These checks detect manifest, schema,
and embedding-identity changes before reuse. They do not hash source contents
or provide byte-level corpus-integrity verification.

## Evidence limits

Repository inspection verifies the loading, metadata, and manifest mechanisms.
It does not establish that every source is accurate, current, or suitable for
every learner decision. Response-level citation quality and corpus coverage are
**PENDING evaluation**.

Third-party redistribution status is documented in
[`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md). The public tree retains
only the Stanford AI Index PDF under its embedded CC BY-ND 4.0 notice. Sources
without established redistribution permission remain represented by external
links and owner-written summaries rather than copied binaries.

See [Architecture](architecture.md) for the retrieval path and
[Evaluation](evaluation.md) for the proposed evidence process.
