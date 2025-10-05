# Nuclear Power Plant Status Types Table

## Table Description
The nuclear_power_plant_status_types table is a reference lookup table that defines all possible lifecycle states of a nuclear power plant, from planning through operation to decommissioning. This table standardizes status classification across the entire database.

## Business Context
- Tracks the complete lifecycle of nuclear facilities from conception to closure
- Essential for analyzing active nuclear capacity versus planned expansion
- Used for safety and regulatory reporting
- Critical for understanding global nuclear energy trends and capacity forecasting

## Schema

| Column Name | Data Type | Nullable | Description |
|------------|-----------|----------|-------------|
| Id | INT | NO | Primary key, unique numeric identifier for each status |
| Type | VARCHAR(50) | NO | Descriptive name of the lifecycle status |

## Relationships
- Referenced by: nuclear_power_plants.StatusId (foreign key)
- One status type can apply to many plants (one-to-many relationship)

## Complete Status Types

| Id | Status Type | Description |
|----|-------------|-------------|
| 0 | Unknown | Status information not available or uncertain |
| 1 | Planned | Facility is in planning/proposal stage, not yet approved |
| 2 | Under Construction | Construction actively underway, site work in progress |
| 3 | Operational | Plant is currently generating electricity |
| 4 | Suspended Operation | Temporarily offline (maintenance, safety review, political) |
| 5 | Shutdown | Permanently ceased operations, may be undergoing decommissioning |
| 6 | Unfinished | Construction started but never completed |
| 7 | Never Built | Planned but construction never began, project abandoned |
| 8 | Suspended Construction | Construction paused indefinitely |
| 9 | Cancelled Construction | Construction officially cancelled, will not resume |

## Common Business Rules
1. **Active Fleet**: StatusId = 3 (Operational)
2. **Future Capacity**: StatusId IN (1, 2) - Planned or Under Construction
3. **Retired Fleet**: StatusId = 5 (Shutdown)
4. **At Risk**: StatusId = 4 (Suspended Operation) - may return to service or be shutdown
5. **Failed Projects**: StatusId IN (6, 7, 8, 9) - Projects that didn't reach operation
6. **Total Nuclear Experience**: StatusId IN (3, 4, 5) - Plants that operated at some point

## Status Distribution (Global)
Based on 788 total nuclear facilities:
- **Operational (3)**: 464 plants (~59%)
- **Shutdown (5)**: 174 plants (~22%)
- **Under Construction (2)**: 55 plants (~7%)
- **Other statuses**: ~12%

## Sample Queries and Intent

### Current operational capacity
**Natural Language**: "How many nuclear plants are currently operating worldwide?"
**Intent**: Count active nuclear facilities
**SQL**:
```sql
SELECT COUNT(*) as operational_plants,
       SUM(npp.capacity) as total_capacity_mw
FROM nuclear_power_plants npp
WHERE npp.status_id = 3;
```

### Future capacity pipeline
**Natural Language**: "What nuclear capacity is under construction?"
**Intent**: Analyze upcoming nuclear capacity additions
**SQL**:
```sql
SELECT st.type, COUNT(npp.id) as plant_count,
       SUM(npp.capacity) as total_capacity_mw
FROM nuclear_power_plants npp
JOIN nuclear_power_plant_status_types st ON npp.status_id = st.id
WHERE st.id IN (1, 2)
GROUP BY st.id, st.type
ORDER BY st.id;
```

### Status breakdown by country
**Natural Language**: "Show me the status of nuclear plants in the United States"
**Intent**: Analyze plant lifecycle distribution for specific country
**SQL**:
```sql
SELECT st.type, COUNT(npp.id) as plant_count
FROM nuclear_power_plants npp
JOIN nuclear_power_plant_status_types st ON npp.status_id = st.id
WHERE npp.country_code = 'US'
GROUP BY st.id, st.type
ORDER BY plant_count DESC;
```

### Historical shutdown analysis
**Natural Language**: "How many nuclear plants have been permanently shut down?"
**Intent**: Count retired nuclear facilities
**SQL**:
```sql
SELECT COUNT(*) as shutdown_plants,
       AVG(YEAR(npp.operational_to) - YEAR(npp.operational_from)) as avg_operational_years
FROM nuclear_power_plants npp
WHERE npp.status_id = 5
  AND npp.operational_from IS NOT NULL
  AND npp.operational_to IS NOT NULL;
```

### Failed construction projects
**Natural Language**: "Which nuclear projects were cancelled or never completed?"
**Intent**: Identify unsuccessful nuclear construction attempts
**SQL**:
```sql
SELECT npp.name, c.name as Country, st.type as Status,
       npp.construction_start_at
FROM nuclear_power_plants npp
JOIN countries c ON npp.country_code = c.id
JOIN nuclear_power_plant_status_types st ON npp.status_id = st.id
WHERE st.id IN (6, 7, 8, 9)
ORDER BY npp.construction_start_at DESC;
```

### Plants at risk of closure
**Natural Language**: "Which nuclear plants are currently suspended?"
**Intent**: Identify plants with uncertain future
**SQL**:
```sql
SELECT npp.name, c.name as Country, npp.capacity,
       DATEDIFF(CURDATE(), npp.operational_to) as days_suspended
FROM nuclear_power_plants npp
JOIN countries c ON npp.country_code = c.id
WHERE npp.status_id = 4
ORDER BY days_suspended DESC;
```

### Capacity by lifecycle stage
**Natural Language**: "Compare operational versus planned nuclear capacity"
**Intent**: Analyze capacity distribution across lifecycle stages
**SQL**:
```sql
SELECT 
    CASE 
        WHEN st.id = 3 THEN 'Current Operational'
        WHEN st.id IN (1, 2) THEN 'Future Pipeline'
        WHEN st.id = 5 THEN 'Retired'
        ELSE 'Other'
    END as capacity_category,
    COUNT(npp.id) as plant_count,
    SUM(npp.capacity) as total_mw,
    ROUND(AVG(npp.capacity), 0) as avg_mw_per_plant
FROM nuclear_power_plants npp
JOIN nuclear_power_plant_status_types st ON npp.status_id = st.id
GROUP BY capacity_category
ORDER BY total_mw DESC;
```

## Important Notes
- **StatusId = 3 (Operational)** is the most important for current capacity calculations
- **StatusId IN (1, 2)** represents future capacity pipeline
- **StatusId = 4 (Suspended)** plants may return to operational status or be shutdown
- When calculating "ever operated" plants, use StatusId IN (3, 4, 5)
- Failed projects (6, 7, 8, 9) represent sunk investment but no capacity contribution
- Always filter by StatusId when calculating capacity metrics
- StatusId = 0 (Unknown) should be investigated for data quality issues

## Business Intelligence Applications
- **Capacity Planning**: Use StatusId 1, 2 for future capacity forecasting
- **Decommissioning Analysis**: Track StatusId 5 trends over time
- **Success Rate**: Calculate ratio of operational plants to total started projects
- **Investment Risk**: Monitor StatusId 4, 8, 9 for market confidence indicators