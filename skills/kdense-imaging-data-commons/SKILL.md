---
name: imaging-data-commons
description: Query and download public cancer imaging data from NCI Imaging Data Commons using idc-index. Use for accessing large-scale radiology (CT, MR, PET) and pathology datasets for AI training or research. No authentication required. Query by metadata, visualize in browser, check licenses.
license: This skill is provided under the MIT License. IDC data itself has individual licensing (mostly CC-BY, some CC-NC) that must be respected when using the data.
metadata:
  version: "1.3"
  source-skill-version: 1.4.0
  skill-author: Andrey Fedorov, @fedorov
  idc-index: 0.11.14
  idc-data-version: v23
  repository: https://github.com/ImagingDataCommons/idc-claude-skill
---

# Imaging Data Commons

## Overview

Use the `idc-index` Python package to query and download public cancer imaging data from the National Cancer Institute Imaging Data Commons (IDC). No authentication required for data access.

**Current IDC Data Version: v23** (always verify with `IDCClient().get_idc_version()`)

**Primary tool:** `idc-index` ([GitHub](https://github.com/imagingdatacommons/idc-index))

**CRITICAL - Check package version before anything else (run this FIRST):**

This block only *reports*. It never installs. If the version is too old, show the user the
suggested command and wait for them to approve it — do not run an install on their behalf.

```python
import idc_index

REQUIRED_VERSION = "0.11.14"  # Must match metadata.idc-index in this file
installed = idc_index.__version__

def _parts(version):
    # Compare numerically: "0.9.0" < "0.11.14" is False as a string comparison.
    return tuple(int(p) if p.isdigit() else 0 for p in version.split(".")[:3])

if _parts(installed) < _parts(REQUIRED_VERSION):
    print(f"idc-index {installed} is older than the tested {REQUIRED_VERSION}.")
    print("Ask the user before installing. Suggested command, in a virtual environment:")
    print(f"    uv pip install 'idc-index=={REQUIRED_VERSION}'")
else:
    print(f"idc-index {installed} meets requirement ({REQUIRED_VERSION})")
```

**Never** install into a system-managed Python with `--break-system-packages`. That flag exists to
override a protection the distribution put there deliberately, and a skill has no business
switching it off unattended. Install into a virtual environment, and pin the version you tested
against so a later IDC release cannot silently change query results underneath a saved analysis.

**Verify IDC data version and check current data scale:**

```python
from idc_index import IDCClient
client = IDCClient()

# Verify IDC data version (should be "v23")
print(f"IDC data version: {client.get_idc_version()}")

# Get collection count and total series
stats = client.sql_query("""
    SELECT
        COUNT(DISTINCT collection_id) as collections,
        COUNT(DISTINCT analysis_result_id) as analysis_results,
        COUNT(DISTINCT PatientID) as patients,
        COUNT(DISTINCT StudyInstanceUID) as studies,
        COUNT(DISTINCT SeriesInstanceUID) as series,
        SUM(instanceCount) as instances,
        SUM(series_size_MB)/1000000 as size_TB
    FROM index
""")
print(stats)
```

**Core workflow:**
1. Query metadata → `client.sql_query()`
2. Download DICOM files → `client.download_from_selection()`
3. Visualize in browser → `client.get_viewer_URL(seriesInstanceUID=...)`

## When to Use This Skill

- Finding publicly available radiology (CT, MR, PET) or pathology (slide microscopy) images
- Selecting image subsets by cancer type, modality, anatomical site, or other metadata
- Downloading DICOM data from IDC
- Checking data licenses before use in research or commercial applications
- Visualizing medical images in a browser without local DICOM viewer software

## Quick Navigation

**Core Sections (inline):**
- IDC Data Model - Collection and analysis result hierarchy
- Index Tables - Available tables and joining patterns
- Installation - Package setup and version verification
- Core Capabilities - Essential API patterns (query, download, visualize, license, citations, batch)
- Best Practices - Usage guidelines
- Troubleshooting - Common issues and solutions

**Reference Guides (load on demand):**

| Guide | When to Load |
|-------|--------------|
| `index_tables_guide.md` | Complex JOINs, schema discovery, DataFrame access |
| `use_cases.md` | End-to-end workflow examples (training datasets, batch downloads) |
| `sql_patterns.md` | Quick SQL patterns for filter discovery, annotations, size estimation |
| `clinical_data_guide.md` | Clinical/tabular data, imaging+clinical joins, value mapping |
| `cloud_storage_guide.md` | Direct S3/GCS access, versioning, UUID mapping |
| `dicomweb_guide.md` | DICOMweb endpoints, PACS integration |
| `digital_pathology_guide.md` | Slide microscopy (SM), annotations (ANN), pathology workflows |
| `bigquery_guide.md` | Full DICOM metadata, private elements (requires GCP) |
| `cli_guide.md` | Command-line tools (`idc download`, manifest files) |
| `parquet_access_guide.md` | Direct Parquet queries via GCS (no idc-index install needed) |

## IDC Data Model

IDC adds two grouping levels above the standard DICOM hierarchy (Patient → Study → Series → Instance):

- **collection_id**: Groups patients by disease, modality, or research focus (e.g., `tcga_luad`, `nlst`). A patient belongs to exactly one collection.
- **analysis_result_id**: Identifies derived objects (segmentations, annotations, radiomics features) across one or more original collections.

Use `collection_id` to find original imaging data, may include annotations deposited along with the images; use `analysis_result_id` to find AI-generated or expert annotations.

**Key identifiers for queries:**
| Identifier | Scope | Use for |
|------------|-------|---------|
| `collection_id` | Dataset grouping | Filtering by project/study |
| `PatientID` | Patient | Grouping images by patient |
| `StudyInstanceUID` | DICOM study | Grouping of related series, visualization |
| `SeriesInstanceUID` | DICOM series | Grouping of related series, visualization |

## Index Tables

The `idc-index` package provides multiple metadata index tables, accessible via SQL or as pandas DataFrames.

**Complete index table documentation:** Use https://idc-index.readthedocs.io/en/latest/indices_reference.html for quick check of available tables and columns without executing any code.

**Important:** Use `client.indices_overview` to get current table descriptions and column schemas. This is the authoritative source for available columns and their types — always query it when writing SQL or exploring data structure.

### Available Tables

| Table | Row Granularity | Loaded | Description |
|-------|-----------------|--------|-------------|
| `index` | 1 row = 1 DICOM series | Auto | Primary metadata for all current IDC data |
| `prior_versions_index` | 1 row = 1 DICOM series | Auto | Series from previous IDC releases; for downloading deprecated data |
| `collections_index` | 1 row = 1 collection | fetch_index() | Collection-level metadata and descriptions |
| `analysis_results_index` | 1 row = 1 analysis result collection | fetch_index() | Metadata about derived datasets (annotations, segmentations) |
| `clinical_index` | 1 row = 1 clinical data column | fetch_index() | Dictionary mapping clinical table columns to collections |
| `sm_index` | 1 row = 1 slide microscopy series | fetch_index() | Slide Microscopy (pathology) series metadata |
| `sm_instance_index` | 1 row = 1 slide microscopy instance | fetch_index() | Instance-level (SOPInstanceUID) metadata for slide microscopy |
| `seg_index` | 1 row = 1 DICOM Segmentation series | fetch_index() | Segmentation metadata: algorithm, segment count, reference to source image series |
| `ann_index` | 1 row = 1 DICOM ANN series | fetch_index() | Microscopy Bulk Simple Annotations series metadata; references annotated image series |
| `ann_group_index` | 1 row = 1 annotation group | fetch_index() | Detailed annotation group metadata: graphic type, annotation count, property codes, algorithm |
| `contrast_index` | 1 row = 1 series with contrast info | fetch_index() | Contrast agent metadata: agent name, ingredient, administration route (CT, MR, PT, XA, RF) |
| `volume_geometry_index` | 1 row = 1 CT/MR/PT series | fetch_index() | 3D volume geometry validation for single-frame CT, MR, and PT series; boolean checks for orientation, spacing, dimensions, and slice positions; composite `regularly_spaced_3d_volume` flag |
| `rtstruct_index` | 1 row = 1 RTSTRUCT series | fetch_index() | RT Structure Set metadata: total ROI count, ROI names, generation algorithms, interpreted types, and the referenced image series UID |

**Auto** = loaded automatically when `IDCClient()` is instantiated
**fetch_index()** = requires `client.fetch_index("table_name")` to load

### Joining Tables

**Key columns are not explicitly labeled, the following is a subset that can be used in joins.**

| Join Column | Tables | Use Case |
|-------------|--------|----------|
| `collection_id` | index, prior_versions_index, collections_index, clinical_index | Link series to collection metadata or clinical data |
| `SeriesInstanceUID` | index, prior_versions_index, sm_index, sm_instance_index | Link series across tables; connect to slide microscopy details |
| `StudyInstanceUID` | index, prior_versions_index | Link studies across current and historical data |
| `PatientID` | index, prior_versions_index | Link patients across current and historical data |
| `analysis_result_id` | index, analysis_results_index | Link series to analysis result metadata (annotations, segmentations) |
| `source_DOI` | index, analysis_results_index | Link by publication DOI |
| `crdc_series_uuid` | index, prior_versions_index | Link by CRDC unique identifier |
| `Modality` | index, prior_versions_index | Filter by imaging modality |
| `SeriesInstanceUID` | index, seg_index, ann_index, ann_group_index, contrast_index | Link segmentation/annotation/contrast series to its index metadata |
| `segmented_SeriesInstanceUID` | seg_index → index | Link segmentation to its source image series (join seg_index.segmented_SeriesInstanceUID = index.SeriesInstanceUID) |
| `referenced_SeriesInstanceUID` | ann_index → index | Link annotation to its source image series (join ann_index.referenced_SeriesInstanceUID = index.SeriesInstanceUID) |
| `SeriesInstanceUID` | index, volume_geometry_index | Link series to its 3D geometry validation result (join index.SeriesInstanceUID = volume_geometry_index.SeriesInstanceUID) |
| `SeriesInstanceUID` / `referenced_SeriesInstanceUID` | index, rtstruct_index | Join RTSTRUCT series to its metadata (index.SeriesInstanceUID = rtstruct_index.SeriesInstanceUID); use rtstruct_index.referenced_SeriesInstanceUID to find the source image series |

**Note:** `Subjects`, `Updated`, and `Description` appear in multiple tables but have different meanings (counts vs identifiers, different update contexts).

For detailed join examples, schema discovery patterns, key columns reference, and DataFrame access, see `references/index_tables_guide.md`.

### Clinical Data Access

```python
# Fetch clinical index (also downloads clinical data tables)
client.fetch_index("clinical_index")

# Query clinical index to find available tables and their columns
tables = client.sql_query("SELECT DISTINCT table_name, column_label FROM clinical_index")

# Load a specific clinical table as DataFrame
clinical_df = client.get_clinical_table("table_name")
```

See `references/clinical_data_guide.md` for detailed workflows including value mapping patterns and joining clinical data with imaging.

## Data Access Options

| Method | Auth Required | Best For |
|--------|---------------|----------|
| `idc-index` | No | Key queries and downloads (recommended) |
| Direct Parquet (GCS) | No | Quick queries without installing idc-index; always uses latest data |
| IDC Portal | No | Interactive exploration, manual selection, browser-based download |
| BigQuery | Yes (GCP account) | Complex queries, full DICOM metadata |
| DICOMweb proxy | No | Tool integration via DICOMweb API |
| Cloud storage (S3/GCS) | No | Direct file access, bulk downloads, custom pipelines |

**Cloud storage organization**

IDC maintains all DICOM files in public cloud storage buckets mirrored between AWS S3 and Google Cloud Storage. Files are organized by CRDC UUIDs (not DICOM UIDs) to support versioning.

| Bucket (AWS / GCS) | License | Content |
|--------------------|---------|---------|
| `idc-open-data` / `idc-open-data` | No commercial restriction | >90% of IDC data |
| `idc-open-data-two` / `idc-open-idc1` | No commercial restriction | Collections with potential head scans |
| `idc-open-data-cr` / `idc-open-cr` | Commercial use restricted (CC BY-NC) | ~4% of data |

Files are stored as `<crdc_series_uuid>/<crdc_instance_uuid>.dcm`. Access is free (no egress fees) via AWS CLI, gsutil, or s5cmd with anonymous access. Use `series_aws_url` column from the index for S3 URLs; GCS uses the same path structure.

See `references/cloud_storage_guide.md` for bucket details, access commands, UUID mapping, and versioning.

**DICOMweb access**

IDC data is available via DICOMweb interface (Google Cloud Healthcare API implementation) for integration with PACS systems and DICOMweb-compatible tools.

| Endpoint | Auth | Use Case |
|----------|------|----------|
| Public proxy | No | Testing, moderate queries, daily quota |
| Google Healthcare | Yes (GCP) | Production use, higher quotas |

See `references/dicomweb_guide.md` for endpoint URLs, code examples, supported operations, and implementation details.

**Direct Parquet access**

All idc-index metadata tables are published as Parquet files to a public GCS bucket (`idc-index-data-artifacts`) with unrestricted CORS. This enables DuckDB or pandas queries without installing idc-index, including cross-table joins and queries against `volume_geometry_index` and `rtstruct_index`.

See `references/parquet_access_guide.md` for URL patterns, available files, and DuckDB query examples.

## Installation and Setup

**Required (for basic access):** install into a virtual environment, pinned to the tested release:
```bash
uv pip install 'idc-index==0.11.14'
```

**Important:** every new IDC data release ships a new `idc-index`. Moving to a newer version
changes which data your queries see, so treat it as a deliberate step: check the release notes,
then pin the new version here. An unpinned `--upgrade` makes the data version a moving target and
silently breaks reproducibility of an analysis you ran last month.

**IMPORTANT:** IDC data version v23 is current. Always verify your version:
```python
print(client.get_idc_version())  # Should return "v23"
```
If it returns an older version, tell the user which version they have and which one this skill was
tested against, and let them decide whether to upgrade.

**Tested with:** idc-index 0.11.14 (IDC data version v23)

**Optional (for data analysis):**
```bash
uv pip install pandas numpy pydicom
```

## Core Capabilities

Nine capability areas, each with worked code, are documented in
[references/core_capabilities.md](references/core_capabilities.md):

1. **Data discovery and exploration** — summary statistics, and enumerating the actual
   `Modality` and `BodyPartExamined` values before filtering on them.
2. **Querying metadata with SQL** — against `index`, `collections_index`, and
   `analysis_results_index`, returning pandas DataFrames.
3. **Downloading DICOM files** — Python and CLI, by collection, series UID, or manifest,
   with control over directory hierarchy (full, simplified, or flat).
4. **Visualizing IDC images** — single series or a whole study in the OHIF viewer.
5. **Licenses and citations** — per-collection license checks, and citations in APA or
   BibTeX.
6. **Batch processing and filtering** — scanner- and protocol-level filters, manifests,
   and batched downloads that avoid timeouts.
7. **Advanced BigQuery queries** — for joins and aggregations beyond the index API.
8. **Tool selection guide** — which access path fits which task.
9. **Integration with analysis pipelines** — reading series with pydicom, processing with
   SimpleITK, and converting to NIfTI.

Always explore the real column values first: filtering on a guessed `Modality` or
`BodyPartExamined` string is the most common cause of an empty result set.

## Common Use Cases

See `references/use_cases.md` for complete end-to-end workflow examples including:
- Building deep learning training datasets from lung CT scans
- Comparing image quality across scanner manufacturers
- Previewing data in browser before downloading
- License-aware batch downloads for commercial use

## Best Practices

- **Verify IDC version before generating responses** - Always call `client.get_idc_version()` at the start of a session to confirm you're using the expected data version (currently v23). If using an older version, report it and let the user decide whether to install a newer pinned release; never install on their behalf
- **Check licenses before use** - Always query the `license_short_name` field and respect licensing terms (CC BY vs CC BY-NC)
- **Generate citations for attribution** - Use `citations_from_selection()` to get properly formatted citations from `source_DOI` values; include these in publications
- **Start with small queries** - Use `LIMIT` clause when exploring to avoid long downloads and understand data structure
- **Use mini-index for simple queries** - Only use BigQuery when you need comprehensive metadata or complex JOINs
- **Organize downloads with dirTemplate** - Use meaningful directory structures like `%collection_id/%PatientID/%Modality`
- **Cache query results** - Save DataFrames to CSV files to avoid re-querying and ensure reproducibility
- **Estimate size first** - Check collection size before downloading - some collection sizes are in terabytes!
- **Save manifests** - Always save query results with Series UIDs for reproducibility and data provenance
- **Read documentation** - IDC data structure and metadata fields are documented at https://learn.canceridc.dev/
- **Use IDC forum** - Search for questions/answers and ask your questions to the IDC maintainers and users at https://discourse.canceridc.dev/

## Troubleshooting

**Issue: `ModuleNotFoundError: No module named 'idc_index'`**
- **Cause:** idc-index package not installed
- **Solution:** with the user's agreement, `uv pip install 'idc-index==0.11.14'` in a virtual environment

**Issue: Download fails with connection timeout**
- **Cause:** Network instability or large download size
- **Solution:**
  - Download smaller batches (e.g., 10-20 series at a time)
  - Check network connection
  - Use `dirTemplate` to organize downloads by batch
  - Implement retry logic with delays

**Issue: `BigQuery quota exceeded` or billing errors**
- **Cause:** BigQuery requires billing-enabled GCP project
- **Solution:** Use idc-index mini-index for simple queries (no billing required), or see `references/bigquery_guide.md` for cost optimization tips

**Issue: Series UID not found or no data returned**
- **Cause:** Typo in UID, data not in current IDC version, or wrong field name
- **Solution:**
  - Check if data is in current IDC version (some old data may be deprecated)
  - Use `LIMIT 5` to test query first
  - Check field names against metadata schema documentation

**Issue: Downloaded DICOM files won't open**
- **Cause:** Corrupted download or incompatible viewer
- **Solution:**
  - Check DICOM object type (Modality and SOPClassUID attributes) - some object types require specialized tools
  - Verify file integrity (check file sizes)
  - Use pydicom to validate: `pydicom.dcmread(file, force=True)`
  - Try different DICOM viewer (3D Slicer, Horos, RadiAnt, QuPath)
  - Re-download the series

## Common SQL Query Patterns

See `references/sql_patterns.md` for quick-reference SQL patterns including:
- Filter value discovery (modalities, body parts, manufacturers)
- Annotation and segmentation queries (including seg_index, ann_index joins)
- Slide microscopy queries (sm_index patterns)
- Download size estimation
- Clinical data linking

For segmentation and annotation details, also see `references/digital_pathology_guide.md`.

## Related Skills

The following skills complement IDC workflows for downstream analysis and visualization:

### DICOM Processing
- **pydicom** - Read, write, and manipulate downloaded DICOM files. Use for extracting pixel data, reading metadata, anonymization, and format conversion. Essential for working with IDC radiology data (CT, MR, PET).

### Pathology and Slide Microscopy
See `references/digital_pathology_guide.md` for DICOM-compatible tools (highdicom, wsidicom, TIA-Toolbox, Slim viewer).

### Metadata Visualization
- **matplotlib** - Low-level plotting for full customization. Use for creating static figures summarizing IDC query results (bar charts of modalities, histograms of series counts, etc.).
- **seaborn** - Statistical visualization with pandas integration. Use for quick exploration of IDC metadata distributions, relationships between variables, and categorical comparisons with attractive defaults.
- **plotly** - Interactive visualization. Use when you need hover info, zoom, and pan for exploring IDC metadata, or for creating web-embeddable dashboards of collection statistics.

### Data Exploration
- **exploratory-data-analysis** - Comprehensive EDA on scientific data files. Use after downloading IDC data to understand file structure, quality, and characteristics before analysis.

## Resources

### Schema Reference (Primary Source)

**Always use `client.indices_overview` for current column schemas.** This ensures accuracy with the installed idc-index version:

```python
# Get all column names and types for any table
schema = client.indices_overview["index"]["schema"]
columns = [(c['name'], c['type'], c.get('description', '')) for c in schema['columns']]
```

### Reference Documentation

See the Quick Navigation section at the top for the full list of reference guides with decision triggers.

- **[indices_reference](https://idc-index.readthedocs.io/en/latest/indices_reference.html)** - External documentation for index tables (may be ahead of the installed version)

### External Links

- **IDC Portal**: https://portal.imaging.datacommons.cancer.gov/explore/
- **Documentation**: https://learn.canceridc.dev/
- **Tutorials**: https://github.com/ImagingDataCommons/IDC-Tutorials
- **User Forum**: https://discourse.canceridc.dev/
- **idc-index GitHub**: https://github.com/ImagingDataCommons/idc-index
- **Citation**: Fedorov, A., et al. "National Cancer Institute Imaging Data Commons: Toward Transparency, Reproducibility, and Scalability in Imaging Artificial Intelligence." RadioGraphics 43.12 (2023). https://doi.org/10.1148/rg.230180

### Skill Updates

This skill version is available in skill metadata. To check for updates:
- Visit the [releases page](https://github.com/ImagingDataCommons/idc-claude-skill/releases)
- Watch the repository on GitHub (Watch → Custom → Releases)
