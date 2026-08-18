# HolyWay Data Engineering Pipeline - Interview Notes

This document provides concise answers and talking points for data engineering interviews, grounded in the actual HolyWay ETL project.

## 1. What problem does this project solve?
The project transforms raw, unstructured, nested NoSQL data (Firebase Firestore) into clean, structured, analytics-ready tabular data (SQLite). It proves that data collected manually for a mobile app can be reliably processed to support downstream BI and SQL analytics.

## 2. Why was Firestore used as the source?
Firestore is the operational database for the existing HolyWay React Native mobile app. The data was manually gathered from various public sources, making Firestore the authoritative source of truth for the church dataset.

## 3. Why is the raw data preserved?
Preserving the raw JSON snapshot follows the ELT (Extract, Load, Transform) / Data Lake best practice. It creates an immutable historical record. If the transformation logic has a bug or requirements change, the pipeline can be rerun from the raw snapshot without hitting the production source system again.

## 4. Why did `massTimings` need to be flattened?
In Firestore, `massTimings` is a nested map/dictionary. SQL databases and BI tools (like Tableau or Athena) struggle to aggregate nested arrays efficiently. By "flattening" or "exploding" the data into one row per service, we unlock standard SQL grouping and counting (e.g., "count services by language").

## 5. Why was the transformed data loaded into SQLite?
SQLite provides a lightweight, local, zero-configuration relational database engine. It perfectly demonstrates the transition from NoSQL to a structured relational model and allows for immediate SQL analytics without the overhead of spinning up a full PostgreSQL server or AWS resources.

## 6. Why are there two relational tables?
To satisfy normalization principles (specifically First Normal Form). A single church has many services. Storing them in a single table would cause massive duplication of church metadata (name, address, city) for every service row. Separating them reduces redundancy and improves data integrity.

## 7. Explain the `churches → services` one-to-many relationship.
One specific church (e.g., St. Mary's Basilica) can offer multiple services (e.g., Sunday 7:00 AM English, Sunday 8:15 AM Telugu). The `churches` table holds the single church entity, while the `services` table holds all the individual mass timings.

## 8. Explain primary key and foreign key.
- **Primary Key (PK)**: `church_id` uniquely identifies a row in the `churches` table.
- **Foreign Key (FK)**: `church_id` in the `services` table links that specific service back to the parent church in the `churches` table.

## 9. Difference between NoSQL Firestore and relational SQLite.
- **Firestore (NoSQL)**: Document-oriented, schema-less, supports deep nesting. Great for rapid mobile app development, but hard to write aggregate analytics queries against.
- **SQLite (Relational)**: Table-oriented, strict schema (rows and columns). Requires flattening data, but natively supports powerful SQL aggregations (JOIN, GROUP BY).

## 10. What does ETL mean in this project?
- **Extract**: Pulling documents from Firestore via Node.js into a local JSON file.
- **Transform**: Using Python and Pandas to clean text, handle missing values, and flatten the nested mass timings into two CSV files.
- **Load**: Inserting the CSV rows into a local SQLite database and running validation checks.

## 11. Main data-quality problems discovered.
- **Missing Coordinates**: 71 out of 101 churches are missing latitude/longitude, impacting any map-based features.
- **Missing Service Data**: 4 churches have no mass timings recorded at all.
- **Incomplete Service Records**: A few individual service records are missing their time (1) or language (4).

## 12. Future AWS Architecture.
This pipeline can be easily migrated to AWS. The raw JSON and processed CSVs would be loaded into **Amazon S3** (acting as the Data Lake). **AWS Glue Data Catalog** would crawl the S3 folders to infer the schema. **Amazon Athena** would then allow us to run the exact same SQL queries directly against the files in S3 without needing an active database server like SQLite.

---

## 10 Likely Interview Questions & Short Answers

**Q1. Describe a data pipeline you built from scratch.**
A: I built an ETL pipeline extracting nested NoSQL data from Firebase, transforming it with Pandas to flatten arrays and handle missing values, and loading it into a relational SQLite database to enable SQL analytics.

**Q2. How did you handle data quality and validation?**
A: I built a data quality gate that checks for structural integrity (record counts, duplicate IDs, orphan foreign keys) which fails the pipeline if broken. I also log non-critical business data issues (missing coordinates/phones) as INFO/WARNINGs to a central JSON report.

**Q3. Why did you choose Python and Pandas for transformation?**
A: Python/Pandas is the industry standard for data manipulation. It handles JSON parsing and "exploding" nested dictionaries extremely efficiently, which was the core challenge with my Firestore data.

**Q4. What happens if the extraction step fails?**
A: I built an orchestrator script using Python `subprocess`. If any stage returns a non-zero exit code (fails), the orchestrator immediately halts the pipeline, preventing bad data from propagating downstream.

**Q5. How do you ensure your pipeline is reproducible?**
A: The orchestrator runs all steps sequentially with a single command. The SQLite load step always drops and recreates the tables, ensuring the database state is perfectly reproducible from the source CSVs.

**Q6. Did you encounter any schema evolution issues?**
A: Since NoSQL is schema-less, I had to inspect the JSON to define a strict relational schema. Some columns were missing entirely in certain documents, which I mapped to NULLs in SQLite.

**Q7. If the data volume grew to 100 GB, what would you change?**
A: I would migrate to AWS. I'd land the data in S3, use AWS Glue or EMR (Spark) for distributed transformation, and query it using Athena, rather than processing it in memory with Pandas locally.

**Q8. Explain a complex SQL query you wrote for this project.**
A: I wrote a query to find the average number of services per church by denomination. It required grouping the `churches` table by denomination and using the `ROUND(AVG())` aggregate function on the pre-calculated `service_count` column.

**Q9. How did you handle the nested `massTimings` array?**
A: I iterated through the nested dictionary structure (Day -> Array of Services) and flattened it into a list of dictionaries, which Pandas easily converted into a flat tabular DataFrame for the `services` table.

**Q10. Why not just query Firestore directly for analytics?**
A: Firestore charges per document read and lacks robust aggregation capabilities. Fetching thousands of documents just to count them by city is slow and expensive. Moving the data to a relational structure makes analytics fast and free (or very cheap in Athena).
