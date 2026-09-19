# Architecture

```text
CSV source files
      |
      v
   raw schema
      |
      v
staging models
(stg_*)
      |
      v
intermediate models
(int_*)
      |
      v
business marts
(fct_*, mart_*)
      |
      +--------------------+
      |                    |
      v                    v
BI dashboard          AI analytics layer
```

## Why this architecture

The project intentionally separates raw source data from business logic.

- **Raw** preserves the original source shape.
- **Staging** standardizes types and names.
- **Intermediate** calculates reusable operational logic.
- **Marts** expose business-ready tables for Power BI, Tableau, Qlik, or an AI assistant.

This pattern makes the project easier to test, document, and expand when a real client connects Jobber, LMN, Aspire, QuickBooks, or other systems.
