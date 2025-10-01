# Countries Table

## Table Description
The countries table is a reference table containing standardized country codes and names for all countries and territories worldwide. This table is used to normalize country information across the nuclear power plant database.

## Business Context
- Contains 255 countries and territories using ISO 3166-1 alpha-2 country codes
- Serves as the master reference for geographic classification of nuclear power plants
- Essential for geographic analysis and reporting by country/region
- Used for filtering and grouping nuclear facilities by nation

## Schema

| Column Name | Data Type | Nullable | Description |
|------------|-----------|----------|-------------|
| id | VARCHAR(2) | NO | Primary key, ISO 3166-1 alpha-2 country code (2 letters) |
| name | VARCHAR(255) | NO | Official country or territory name in English |

## Relationships
- Referenced by: nuclear_power_plants.country_code (foreign key)
- One country can have many nuclear power plants (one-to-many relationship)

## Common Business Rules
1. **Nuclear Power Countries**: Countries with at least one nuclear power plant (operational, under construction, or historical)
2. **Top Nuclear Nations**: Countries with the most nuclear facilities
3. **Regional Analysis**: Group countries by continent or region for geographic insights

## Country Code Examples
- **US**: United States (137 plants)
- **CN**: China (91 plants)
- **FR**: France (72 plants)
- **JP**: Japan (71 plants)
- **RU**: Russia (56 plants)
- **KR**: South Korea
- **IN**: India
- **CA**: Canada
- **GB**: United Kingdom
- **DE**: Germany

## Sample Queries and Intent

### Countries with nuclear power plants
**Natural Language**: "Which countries have nuclear power plants?"
**Intent**: List all countries that have at least one nuclear facility
**SQL**:
```sql
SELECT DISTINCT c.id, c.name, COUNT(npp.id) as plant_count
FROM countries c
JOIN nuclear_power_plants npp ON c.id = npp.country_code
GROUP BY c.id, c.name
ORDER BY plant_count DESC;
```

### Top nuclear power countries
**Natural Language**: "Which countries have the most nuclear power plants?"
**Intent**: Rank countries by number of facilities
**SQL**:
```sql
SELECT c.name, c.id, COUNT(npp.id) as total_plants,
       SUM(CASE WHEN npp.status_id = 3 THEN 1 ELSE 0 END) as operational_plants,
       SUM(npp.capacity) as total_capacity_mw
FROM countries c
JOIN nuclear_power_plants npp ON c.id = npp.country_code
GROUP BY c.id, c.name
ORDER BY total_plants DESC
LIMIT 10;
```

### Countries with operational reactors
**Natural Language**: "Show me countries with active nuclear power plants"
**Intent**: Find countries with currently operational facilities
**SQL**:
```sql
SELECT c.name, COUNT(npp.id) as operational_count
FROM countries c
JOIN nuclear_power_plants npp ON c.id = npp.country_code
WHERE npp.status_id = 3
GROUP BY c.id, c.name
HAVING operational_count > 0
ORDER BY operational_count DESC;
```

### Countries expanding nuclear capacity
**Natural Language**: "Which countries are building new nuclear plants?"
**Intent**: Identify countries with plants under construction
**SQL**:
```sql
SELECT c.name, COUNT(npp.id) as under_construction
FROM countries c
JOIN nuclear_power_plants npp ON c.id = npp.country_code
WHERE npp.status_id = 2
GROUP BY c.id, c.name
ORDER BY under_construction DESC;
```

### Geographic coverage
**Natural Language**: "How many countries have ever operated nuclear power?"
**Intent**: Count countries with nuclear experience (operational or shutdown)
**SQL**:
```sql
SELECT COUNT(DISTINCT c.id) as countries_with_nuclear_experience
FROM countries c
JOIN nuclear_power_plants npp ON c.id = npp.country_code
WHERE npp.status_id IN (3, 4, 5);
```

## Important Notes
- Use ISO 3166-1 alpha-2 codes for consistency (2-letter codes like "US", "FR", "CN")
- Country codes are always uppercase
- Some territories and islands have their own codes (e.g., "AC" for Ascension Island)
- When counting plants, specify which StatusId values to include (operational, shutdown, etc.)
- For capacity analysis, join with nuclear_power_plants and filter by status
- Country names are in English and follow official ISO naming conventions

## Data Quality Notes
- All 255 entries are valid ISO country codes
- No duplicate country codes
- Country names are standardized and regularly updated
- Historical country codes (e.g., Soviet Union) may not be present; plants are assigned to current countries