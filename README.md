# HolyWay Data Engineering Pipeline

A small ETL / data-engineering project built around the church-domain data used
by the **HolyWay** mobile application.

## Current Stage

**Step 1 — Extract** (Firestore → Raw JSON)

```
Firestore (holy-way-9800e)
        ↓
  Node.js extraction script
        ↓
  Raw JSON snapshot (local)
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

> **Note:** Only Step 1 (extraction) is implemented. S3, Glue, Athena, and
> analytics are planned for future stages.

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

- [Node.js](https://nodejs.org/) ≥ 18
- Access to the Firebase project `holy-way-9800e`

### 1. Clone the repository

```bash
git clone https://github.com/thanmaireddy-dev/holyway-etl-pipeline.git
cd holyway-etl-pipeline
```

### 2. Install dependencies

```bash
npm install
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
| `FIREBASE_PROJECT_ID`         | `holy-way-9800e`                      |
| `FIREBASE_STORAGE_BUCKET`     | Firebase Storage bucket              |
| `FIREBASE_MESSAGING_SENDER_ID`| Firebase Cloud Messaging sender ID  |
| `FIREBASE_APP_ID`             | Firebase App ID                      |

> **Important:** Never commit `.env`. It is excluded by `.gitignore`.

### 4. Run the extraction

```bash
npm run extract
```

Or directly:

```bash
node scripts/etl/extractFirestore.mjs
```

---

## Output

After a successful extraction, the following files are created in `raw/firestore/`:

| File                        | Contents                                      |
| --------------------------- | --------------------------------------------- |
| `churches.json`             | Array of raw church documents from Firestore   |
| `_extraction_metadata.json` | Extraction timestamp, project ID, doc count    |

The `raw/` directory is excluded from version control by `.gitignore`.

---

## Project Structure

```
holyway-data-pipeline/
│
├── scripts/
│   └── etl/
│       └── extractFirestore.mjs   ← Firestore extraction script
│
├── raw/
│   └── firestore/                 ← Raw JSON output (git-ignored)
│
├── .env.example                   ← Template for Firebase configuration
├── .gitignore
├── package.json
└── README.md
```

---

## What the extraction script does

1. Loads Firebase configuration from `.env` (via `dotenv`).
2. Connects to Firestore project `holy-way-9800e`.
3. Reads **all** documents from the `churches` collection (read-only).
4. Preserves every Firestore document ID, original field name, nested object,
   and array exactly as stored.
5. Serializes Firestore timestamps (`createdAt`, `updatedAt`) to ISO 8601
   strings while retaining the original `seconds`/`nanoseconds` precision.
6. Writes the raw data to `raw/firestore/churches.json`.
7. Writes extraction metadata to `raw/firestore/_extraction_metadata.json`.

### What the script does NOT do

- It does **not** create, update, or delete any Firestore documents.
- It does **not** clean, normalize, or transform the data.
- It does **not** export user data, suggestions, or private collections.
- It does **not** expose Firebase credentials in logs or output files.

---

## License

MIT
