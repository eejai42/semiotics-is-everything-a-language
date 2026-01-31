# Effortless Rulebook

### Generated from: 

> This builds ssotme tools including those that are disabled which regenerates this file.

```
$ cd ./docs
$ ssotme -build -id
```


> CMCC rulebook generated directly from Airtable base.

**Model ID:** `appfVjSTr5bsyyaBT`

---

## Tables

### DemoVersions

> Table: DemoVersions

#### Schema

| Field | Type | Data Type | Nullable | Description |
|-------|------|-----------|----------|-------------|
| `DemoVersionId` | raw | string | No | - |
| `Name` | calculated | string | Yes | Human-readable display name combining the version number and a slug of the commit message, used for quick identification in lists and logs. |
| `Message` | raw | string | Yes | Short summary describing what changed in this version, similar to a git commit message. |
| `Notes` | raw | string | Yes | Extended details about the version changes, including migration notes, breaking changes, or additional context not captured in the message. |
| `Published` | raw | boolean | Yes | Indicates whether this version has been officially released. Unpublished versions are drafts or internal checkpoints. |
| `CommitDate` | raw | datetime | Yes | The timestamp when this version was committed, used to generate the version number and establish chronological order. |
| `VersionNumber` | calculated | string | Yes | Computed version |

**Formula for `Name`:**
```
={{VersionNumber}}
```

**Formula for `VersionNumber`:**
```
=CONCATENATE("v", SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(CommitDate, "T", "-"), "/", "-"), ":", "-"), "Z", ""))
```


#### Sample Data (1 records)

| Field | Value |
|-------|-------|
| `DemoVersionId` | v2026-01-10-19-19-30-000 |
| `Name` | v2026-01-10-19-19-30.000 |
| `Message` | Initial commit |
| `Notes` | This is the initial commit for the project. |
| `Published` | true |
| `CommitDate` | 2026-01-10T19:19:30Z |
| `VersionNumber` | v2026-01-10-19-19-30.000 |

---


## Metadata

**Summary:** Airtable export with schema-first type mapping: Schemas, Data, Relationships (FK links), Lookups (INDEX/MATCH), Aggregations (SUMIFS/COUNTIFS/Rollups), and Calculated fields (formulas) in Excel dialect. Field types are determined from Airtable's schema metadata FIRST (no coercion), with intelligent fallback to formula/data analysis only when schema is unavailable.

### Conversion Details

| Property | Value |
|----------|-------|
| Source Base ID | `appfVjSTr5bsyyaBT` |
| Table Count | 1 |
| Tool Version | 2.0.0 |
| Export Mode | schema_first_type_mapping |
| Field Type Mapping | checkbox→boolean, number→number/integer, multipleRecordLinks→relationship, multipleLookupValues→lookup, rollup→aggregation, count→aggregation, formula→calculated |

### Type Inference

- **Enabled:** true
- **Priority:** airtable_metadata (NO COERCION) → formula_analysis → reference_resolution → data_analysis (fallback only)
- **Airtable Type Mapping:** checkbox→boolean, singleLineText→string, multilineText→string, number→number/integer, datetime→datetime, singleSelect→string, email→string, url→string, phoneNumber→string
- **Data Coercion Hierarchy:** Only used as fallback when Airtable schema unavailable: datetime → number → integer → boolean → base64 → json → string
- **Nullable Support:** true
- **Error Value Handling:** #NUM!, #ERROR!, #N/A, #REF!, #DIV/0!, #VALUE!, #NAME? are treated as NULL

---

*Generated from effortless-rulebook.json*

