# HolyWay Data Engineering Pipeline

A small ETL / data-engineering project built around the church-domain data used
by the **HolyWay** mobile application.

---

## Conceptual Architecture

```
Firebase Firestore (holy-way-9800e)
        ↓
     Extract
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

### Extract
The pipeline reads 101 church documents from the HolyWay Firestore database and creates a raw JSON snapshot.

### Transform
Python/Pandas cleans formatting, validates values, and converts nested mass/service timing structures into analytics-friendly tabular records.

### Load
The processed datasets are loaded into a SQLite relational database containing `churches` and `services` tables.

### Analyze
SQL queries perform aggregation, filtering, joins, and data-quality analysis.

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

## Setup & Execution

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

## Data Quality

The pipeline performs automated data-quality validation. Actual findings from the current dataset include:

- **101** churches preserved
- **259** service records
- **0** orphan services
- **71** churches missing coordinates
- **4** churches without recorded services
- **1** service missing time
- **4** services missing language

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

## Future Cloud Architecture

The current implementation is local and does not deploy the pipeline to AWS.

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
