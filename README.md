# HolyWay Data Engineering Pipeline

A small ETL / data-engineering project built around the church-domain data used
by the **HolyWay** mobile application.

---

## What is ETL?

**ETL** stands for **Extract, Transform, Load** — a standard data-engineering
pattern:

| Stage | What it does | Status |
|---|---|---|
| **Extract** | Read raw church data from Firestore | ✅ Done |
| **Transform** | Clean, validate, and reshape into analytics-friendly datasets | ✅ Done |
| **Load** | Load processed datasets into Amazon S3 | ⬜ Next |

## Current Architecture

```
Firestore (holy-way-9800e)
        ↓
  Step 1: Node.js extraction script
        ↓
  Raw JSON snapshot (local)
        ↓
  Step 2: Python + Pandas transformation
        ↓
  Processed CSV datasets (local)
        ↓
  [Next: Amazon S3]
```

### Planned Architecture (not yet implemented)

```
Firestore → Extract → Raw JSON → Transform / Validate → Amazon S3
                                                            ↓
                                                   AWS Glue Data Catalog
                                                            ↓
                                                      Amazon Athena
                                                            ↓
                                                      SQL Analytics
```

> **Note:** Only Steps 1 (extraction) and 2 (transformation) are implemented.
> S3, Glue, Athena, and analytics are planned for future stages.

---

## Why Firestore?

The existing HolyWay application stores manually collected church data in
Firebase Firestore (project `holy-way-9800e`). This data was gathered from:

- Individual church websites
- The Archdiocese of Hyderabad website
- PDFs and Excel files
- Other publicly available sources
- Manually collected references

Firestore is the authoritative source system for the HolyWay church dataset.

## Why preserve raw data separately?

The extraction step creates a **faithful, unmodified snapshot** of the Firestore
data. No cleaning, normalization, deduplication, or field renaming is performed.
This follows the standard ETL/ELT pattern of landing raw data first so that
downstream transformations are repeatable and auditable.

## Why only the `churches` collection?

The `churches` collection contains the core church-domain data (names,
locations, mass timings, etc.) that is relevant for data engineering and
analytics. Collections such as `suggestions`, `users`, and
authentication-related data are **excluded** because they contain private or
user-generated information that is not relevant to the data pipeline.

---

## Setup

### Prerequisites

- [Node.js](https://nodejs.org/) ≥ 18 (for extraction)
- [Python](https://python.org/) ≥ 3.10 (for transformation)
- Access to the Firebase project `holy-way-9800e`

### 1. Clone the repository

```bash
git clone https://github.com/thanmaireddy-dev/holyway-etl-pipeline.git
cd holyway-etl-pipeline
```

### 2. Install dependencies

```bash
# Node.js dependencies (for extraction)
npm install

# Python dependencies (for transformation)
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example environment file and fill in your Firebase Web SDK values:

```bash
cp .env.example .env
```

Edit `.env` and provide the following values from the Firebase console:

| Variable                      | Description                          |
| ----------------------------- | ------------------------------------ |
| `FIREBASE_API_KEY`            | Firebase Web API key                 |
| `FIREBASE_AUTH_DOMAIN`        | Firebase Auth domain                 |
| `FIREBASE_PROJECT_ID`         | `holy-way-9800e`                     |
| `FIREBASE_STORAGE_BUCKET`     | Firebase Storage bucket              |
| `FIREBASE_MESSAGING_SENDER_ID`| Firebase Cloud Messaging sender ID  |
| `FIREBASE_APP_ID`             | Firebase App ID                      |

> **Important:** Never commit `.env`. It is excluded by `.gitignore`.

---

## Running the Pipeline

### Step 1 — Extract (Firestore → Raw JSON)

```bash
npm run extract
```

This reads all documents from the Firestore `churches` collection and writes
a raw JSON snapshot to `raw/firestore/churches.json`.

### Step 2 — Transform + Validate (Raw JSON → Processed CSV)

```bash
python scripts/etl/transform.py
```

This reads the raw snapshot, performs safe transformations, and produces
analytics-friendly datasets in `processed/`.

---

## Output

### Raw data (`raw/firestore/` — git-ignored)

| File                        | Contents                                      |
| --------------------------- | --------------------------------------------- |
| `churches.json`             | Array of raw church documents from Firestore   |
| `_extraction_metadata.json` | Extraction timestamp, project ID, doc count    |

### Processed data (`processed/`)

| File                        | Contents                                          |
| --------------------------- | ------------------------------------------------- |
| `churches.csv`              | One row per church — flat, analytics-friendly      |
| `services.csv`              | One row per service-language — flattened timings    |
| `data_quality_report.json`  | Validation results and data-quality metrics         |

---

## Project Structure

```
holyway-data-pipeline/
│
├── scripts/
│   └── etl/
│       ├── extractFirestore.mjs   ← Step 1: Firestore → Raw JSON
│       └── transform.py          ← Step 2: Raw JSON → Processed CSV
│
├── raw/
│   └── firestore/                 ← Raw JSON output (git-ignored)
│
├── processed/                     ← Transformed CSV datasets
│   ├── churches.csv
│   ├── services.csv
│   └── data_quality_report.json
│
├── .env.example                   ← Template for Firebase configuration
├── .gitignore
├── package.json
├── requirements.txt               ← Python dependencies (pandas)
└── README.md
```

---

## Step 1: Extraction Details

1. Loads Firebase configuration from `.env` (via `dotenv`).
2. Connects to Firestore project `holy-way-9800e`.
3. Reads **all** documents from the `churches` collection (read-only).
4. Preserves every Firestore document ID, original field name, nested object,
   and array exactly as stored.
5. Serializes Firestore timestamps (`createdAt`, `updatedAt`) to ISO 8601
   strings while retaining the original `seconds`/`nanoseconds` precision.
6. Writes the raw data to `raw/firestore/churches.json`.
7. Writes extraction metadata to `raw/firestore/_extraction_metadata.json`.

**What extraction does NOT do:**

- It does **not** create, update, or delete any Firestore documents.
- It does **not** clean, normalize, or transform the data.
- It does **not** export user data, suggestions, or private collections.
- It does **not** expose Firebase credentials in logs or output files.

## Step 2: Transformation Details

**`churches.csv`** — One row per church with flat, analytics-friendly columns:

| Column | Source |
|---|---|
| `_firestoreId` | Firestore document ID |
| `name`, `churchType`, `denomination` | Direct from source |
| `archdiocese`, `city`, `address` | Direct from source |
| `latitude`, `longitude` | Direct from source |
| `status`, `website`, `phone` | Direct from source |
| `languages` | Semicolon-joined list |
| `language_count` | Derived: count of languages |
| `service_count` | Derived: total mass timing entries |

**`services.csv`** — Flattened from the nested `massTimings` object:

| Column | Description |
|---|---|
| `church_id` | Links to `_firestoreId` in churches.csv |
| `church_name` | Church name for readability |
| `day` | Sunday, Weekday, or Saturday |
| `time` | Service time as recorded in source |
| `language` | One language per row |
| `note` | Optional note (e.g., "Children's Mass") |

Multi-language services are exploded into separate rows (one per language).

**Safe transformations applied:**

- Strip leading/trailing whitespace from text fields.
- Add deterministic derived columns (`language_count`, `service_count`).
- Capitalize day keys for readability (sunday → Sunday).

**What transformation does NOT do:**

- It does **not** modify the raw JSON snapshot.
- It does **not** rename or remove original fields.
- It does **not** perform fuzzy matching or deduplication of churches.
- It does **not** guess or invent missing data.
- It does **not** change factual church information.

---

## License

MIT
