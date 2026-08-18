# HolyWay Data Engineering Pipeline

## 1. What is this project?
A complete, local ETL (Extract, Transform, Load) data-engineering pipeline built around real church-domain data used by the **HolyWay** mobile application.

## 2. Why was it built?
To demonstrate how unstructured, nested NoSQL mobile app data can be reliably extracted, transformed, and loaded into a structured relational database for rigorous SQL analytics and business intelligence, all while maintaining data quality and a reproducible pipeline.

## 3. What is the data source?
The operational NoSQL database for the HolyWay app: **Firebase Firestore** (Project: `holy-way-9800e`, Collection: `churches`).

## 4. What does the pipeline do?
It extracts the raw JSON documents from Firestore, transforms and flattens them using Python and Pandas, validates the data integrity, loads the records into a relational SQLite database, and runs SQL analytical queries against the structured data.

## 5. What technologies are actually used?
*   **Node.js / Firebase Admin SDK**: Read-only extraction.
*   **Python 3 / Pandas**: Data transformation, flattening nested structures, and orchestration.
*   **SQLite / SQL**: Relational storage and data analytics.
*   **Git**: Version control.

---

## Conceptual Architecture

```text
Firebase Firestore (holy-way-9800e)
        ↓
Node.js Extraction
        ↓
     Raw JSON
        ↓
 Python + Pandas
        ↓
Transform + Validate
        ↓
  Processed CSV
        ↓
      SQLite
        ↓
  SQL Analytics
```

### 6. What data transformations occur?
Python/Pandas cleans text formatting, handles missing values gracefully, and most importantly, "flattens" or "explodes" the deeply nested NoSQL `massTimings` dictionaries into a tabular format where each service time becomes its own row.

### 7. What relational model is created? (See below)
The processed datasets are loaded into a SQLite relational database containing normalized `churches` and `services` tables.

### 8. What SQL analytics are performed?
SQL queries perform aggregations (e.g., counting churches by denomination), filtering, joins (e.g., finding churches with the highest number of services), and data-quality analysis (e.g., finding service rows missing a language).

---

## Relational Model

The SQLite database uses a simple relational model to allow for robust analytics.

┌────────────────────┐
│      churches      │
├────────────────────┤
│ church_id (PK)     │
│ name               │
│ denomination       │
│ city               │
│ ...                │
└─────────┬──────────┘
          │
          │ 1
          │
          │ N
          ▼
┌────────────────────┐
│      services      │
├────────────────────┤
│ service_id (PK)    │
│ church_id (FK)     │
│ day                │
│ time               │
│ language           │
│ note               │
└────────────────────┘

*   **Primary Key (PK)**: `church_id` uniquely identifies each church.
*   **Foreign Key (FK)**: `church_id` in the `services` table links each service back to its parent church.
*   **One-to-Many Relationship**: One church can have many services (1:N). Flattening the nested Firestore `massTimings` structure into this relational format makes it easy to run SQL queries and perform analytics across the entire dataset.

---

## 10. How do I run it? (Setup & Execution)

### Prerequisites

- [Node.js](https://nodejs.org/) ≥ 18 (for extraction)
- [Python](https://python.org/) ≥ 3.10 (for transformation and pipeline execution)
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

# Python dependencies (for transformation and analytics)
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example environment file and fill in your Firebase Web SDK values:

```bash
cp .env.example .env
```

> **Important:** Never commit `.env`. It is excluded by `.gitignore`.

### 4. Run the Pipeline

The entire ETL pipeline is automated via a single orchestrator script. It extracts data, transforms it, loads it into SQLite, validates it, and runs SQL analytics.

```bash
python scripts/run_pipeline.py
```

---

## 11. What are the current results? (Current Dataset Metrics)

The pipeline performs automated data-quality validation on every run. **Missing values are reported (as INFO or WARNING) rather than fabricated or silently discarded.**

Actual findings from the current dataset include:

*   **Source records**: 101
*   **Processed churches**: 101
*   **Service records**: 259
*   **Orphan service records**: 0
*   **Missing coordinates**: 71 churches
*   **Churches without recorded services**: 4
*   **Service rows missing time**: 1
*   **Service rows missing language**: 4

### 9. What data-quality issues were discovered?
As seen in the metrics above, the primary data quality issues are missing geographical coordinates and occasional missing service details. The pipeline successfully catches these without dropping the valid portions of the records.

---

## Project Structure

```
holyway-etl-pipeline/
│
├── scripts/
│   ├── etl/
│   │   ├── extractFirestore.mjs
│   │   ├── transform.py
│   │   ├── validate.py
│   │   └── load_sqlite.py
│   │
│   ├── analytics/
│   │   └── run_queries.py
│   │
│   └── run_pipeline.py            ← Main orchestrator
│
├── sql/
│   └── analytics.sql              ← Analytical SQL queries
│
├── docs/
│   └── interview_notes.md         ← Project FAQ & Interview Prep
│
├── raw/                           ← (Git-ignored)
│   └── firestore/
│       └── churches.json          ← Extracted raw snapshot
│
├── processed/                     ← (Git-ignored)
│   ├── churches.csv               ← Transformed church data
│   ├── services.csv               ← Transformed service data
│   └── data_quality_report.json   ← Validation report
│
├── database/                      ← (Git-ignored)
│   └── holyway.db                 ← Generated SQLite database
│
├── README.md
├── requirements.txt
├── package.json
└── .env.example
```

---

## 12. What would the future AWS architecture look like? (Future Cloud Architecture)

The current implementation is local and does not deploy the pipeline to AWS.

**Not implemented in the current version.**

A future cloud deployment could use:

```
Firebase Firestore
        ↓
  Amazon S3
        ↓
  AWS Glue Data Catalog
        ↓
  Amazon Athena
        ↓
  SQL Analytics
```

---

## License

MIT
