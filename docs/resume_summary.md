# HolyWay Data Engineering Pipeline - Resume Summary

**Project Title**: HolyWay Mobile Data ETL Pipeline
**One-Line Description**: An end-to-end local ETL pipeline that transforms unstructured NoSQL mobile app data into a structured relational database for SQL analytics.
**Technology Stack**: Python, Pandas, SQLite, SQL, Node.js, Firebase/Firestore, Git

## Resume Bullets

*   Architected and implemented an end-to-end ETL pipeline in Python to extract unstructured NoSQL data from a production Firebase Firestore database.
*   Engineered data transformation scripts using Pandas to flatten deeply nested JSON arrays, resulting in a normalized relational schema with 100% data preservation.
*   Developed a rigorous automated data-quality gate that identifies and logs missing geographical and categorical fields without failing the broader pipeline.
*   Loaded cleaned datasets into a local SQLite database and wrote complex SQL aggregations to analyze church and service metrics, proving the viability of migrating the mobile app's data to a structured format.

## Measurable Results

*   Successfully processed 101 raw NoSQL documents into 101 normalized church records and 259 distinct service records.
*   Identified 71 records missing critical geographical coordinates and 4 churches missing service schedules through automated data-quality checks.
*   Maintained 0 orphan foreign-key relationships through strict relational modeling.
*   Achieved 100% local pipeline reproducibility via a centralized orchestration script.

*(Note: If discussing AWS during an interview, clearly state that S3, Glue, and Athena represent the designed future cloud architecture for scaling this local pipeline, not the currently deployed state).*
