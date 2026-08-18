# HolyWay Data Engineering Pipeline - Interview Notes

This document provides concise answers and talking points for data engineering interviews, grounded in the actual HolyWay ETL project. It strictly distinguishes between what was **ACTUALLY IMPLEMENTED** locally and what is **CONCEPTUALLY UNDERSTOOD** for future cloud deployment.

---

## Part 1: Actually Implemented (Local ETL Pipeline)

**1. Explain your project in 60 seconds.**
I built a local end-to-end ETL pipeline to process data for the HolyWay mobile app. I extracted 101 unstructured NoSQL documents from Firebase Firestore using Node.js, transformed and flattened the nested arrays using Python and Pandas, and loaded the cleaned data into a relational SQLite database. I then wrote SQL queries to analyze the data and built an automated validation gate to ensure data quality.

**2. What is ETL?**
ETL stands for Extract, Transform, and Load. In this project:
*   **Extract**: Node.js pulls raw data from Firestore to a local JSON file.
*   **Transform**: Python/Pandas cleans missing values and flattens nested arrays.
*   **Load**: Python inserts the tabular data into a local SQLite database.

**3. Why did you choose Firestore as the source?**
Firestore is the actual operational database for the HolyWay React Native mobile app. It serves as the authoritative source of truth for the church dataset.

**4. Why did you preserve raw JSON?**
Preserving the raw JSON snapshot follows the ELT/Data Lake best practice of maintaining an immutable historical record. If the transformation logic has a bug, the pipeline can be rerun from the raw snapshot without hitting the production source system again.

**5. What transformations did you perform?**
I used Python and Pandas to clean text fields, handle missing phone numbers and coordinates, calculate the total number of services per church, and most importantly, flatten the deeply nested `massTimings` dictionary into individual service rows.

**6. Why did you flatten massTimings?**
In Firestore, `massTimings` is a nested dictionary. Relational SQL databases and BI tools cannot aggregate nested structures efficiently. By "flattening" or "exploding" the data into one row per service, we unlock standard SQL grouping and counting.

**7. Why did you create churches and services tables?**
To satisfy database normalization (First Normal Form). Storing everything in a single table would cause massive duplication of church metadata (name, address) for every service. Separating them reduces redundancy and improves data integrity.

**8. What is the primary key?**
The primary key (PK) is `church_id`. It uniquely identifies a single row in the `churches` table.

**9. What is the foreign key?**
The foreign key (FK) is also `church_id` in the `services` table. It links a specific service back to its parent church in the `churches` table.

**10. What is the relationship between churches and services?**
It is a **one-to-many (1:N)** relationship. One specific church can offer multiple services, but each service belongs to exactly one church.

**11. Why SQLite?**
SQLite provides a lightweight, local, zero-configuration relational database engine. It perfectly demonstrates the transition from NoSQL to a structured relational model and allows for immediate SQL analytics without the overhead of spinning up a full database server.

**12. How did you validate that no records were lost?**
I built a Python validation script (`validate.py`) that counts the records at each stage. It explicitly asserts that the 101 raw documents extracted from Firestore match exactly the 101 records loaded into the `churches` SQLite table, failing the pipeline if they differ.

**13. What data-quality issues did you find?**
Out of 101 records:
*   71 churches are missing latitude/longitude coordinates.
*   4 churches have no recorded services at all.
*   1 service row is missing a time, and 4 are missing a language.

**14. Why are missing coordinates not automatically errors?**
Because a church still exists and holds services even if we haven't mapped its exact GPS location yet. Dropping the whole record would destroy valuable service data. Therefore, missing coordinates are flagged as `INFO` rather than pipeline-failing `ERROR`s.

**15. What SQL queries did you implement?**
I implemented 10 analytical queries, including:
*   Counting churches by denomination (using `GROUP BY`).
*   Finding churches with the most services (using `JOIN` and `ORDER BY`).
*   Finding orphan records or missing data (using `WHERE ... IS NULL`).

**16. What happens if the Firestore schema changes?**
Because Firestore is schema-less, new fields might appear or old ones might disappear. The Pandas transformation script maps missing fields to `NULL` (NaN) gracefully, and ignores unrecognized new fields until the Python script is explicitly updated to handle them.

**17. What would happen if the dataset grew from 101 records to 10 million?**
The current local Python/Pandas approach would run out of memory (OOM). We would need to move to a distributed cloud architecture (like AWS) and use tools like Apache Spark (EMR or Glue) that can process data in parallel across multiple machines.

---

## Part 2: Conceptually Understood (Future Cloud Architecture)

*Note: The following AWS services were NOT implemented in the current project, but represent the future roadmap for scaling.*

**18. How would you move this architecture to AWS?**
I would replace the local file system with Amazon S3. The Node.js extractor would drop the raw JSON into an S3 raw bucket. A serverless AWS Glue job (PySpark) would perform the Pandas transformations and save the CSV/Parquet files to an S3 processed bucket. Finally, Amazon Athena would replace SQLite for querying the data.

**19. Why would S3 be used?**
Amazon Simple Storage Service (S3) would act as our Data Lake. It provides infinitely scalable, cheap, and durable storage for both the raw JSON snapshots and the processed tabular datasets.

**20. What would AWS Glue do?**
AWS Glue provides two things:
1.  **Glue ETL**: A serverless Spark environment to run our Python transformation code at massive scale.
2.  **Glue Data Catalog**: A crawler that inspects the files in S3 and infers their schema, acting as a central metadata repository.

**21. What would Athena do?**
Amazon Athena is a serverless interactive query service. Instead of loading the processed data into a traditional database like SQLite or PostgreSQL, Athena allows us to write standard SQL queries *directly* against the CSV/Parquet files sitting in S3.
