# Legacy Reference Extraction

This file extracts only the reusable value from the legacy project.

## Legacy Sources Reviewed

- legacy crawler application directory (`网络数据爬取`)
- legacy v3 crawler application directory (`网络数据爬取_v3`)
- related design docs, ER diagrams, flow charts, and requirement notes

## Valuable Ideas Worth Keeping

### 1. Historical data asset mindset

The strongest legacy idea is not the crawler itself, but the decision to store job data in a database for long-term retrieval and evolution analysis.

This should remain a first-class principle in the new system.

### 2. Business loop is already clear

The legacy project already identified the useful loop:

- create crawl task
- acquire website data
- store structured records
- search and filter
- export
- analyze trends

This loop should be preserved, but rebuilt with cleaner boundaries.

### 3. Multi-role system is necessary

The distinction between normal users and admins is valid and should remain.

In the new system, this evolves into:

- core system permissions
- workspace permissions
- proposal/review permissions

### 4. Search and analytics are core, not accessory

The old system correctly treated search, export, and analytics as part of the main product rather than add-ons.

### 5. Template extensibility is the real future

The old project already showed that hardcoded support for only a few websites will hit a ceiling quickly.

The new system should turn this into a formal template and onboarding architecture.

## Legacy Problems To Avoid Repeating

### 1. Single-file backend

Do not rebuild another all-in-one application file.

### 2. Web and crawling tightly coupled

Crawl execution must be async and independent from the request lifecycle.

### 3. Old and new versions mixed in one root

New work must stay in this clean project root only.

### 4. Weak version discipline

Templates, workflows, schema changes, and generated artifacts must all be versioned.

### 5. Unstructured analysis fields

Salary, publish date, experience, and normalized tags should be stored in analysis-friendly fields.

## Legacy Materials Worth Consulting Later

- old requirement notes for real user pain points
- old database design for entity boundaries
- old crawler code for site-specific extraction logic
- old templates for useful interaction ideas

## Migration Rule

Nothing should be copied into the new system unless it meets one of these conditions:

1. It contains reusable domain knowledge.
2. It contains reusable extraction logic.
3. It is needed as an archived reference.

Otherwise, rebuild cleanly.
