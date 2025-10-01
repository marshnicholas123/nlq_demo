# Nuclear Power Plants Table

## Table Description
The nuclear_power_plants table is the central fact table containing detailed information about every nuclear power facility worldwide. This comprehensive dataset tracks 788 nuclear plants across their entire lifecycle, from planning through operation to decommissioning, with geographic, technical, and temporal attributes.

## Business Context
- **Global Coverage**: 788 nuclear facilities across 33+ countries
- **Current Fleet**: 464 operational reactors generating electricity (59% of total)
- **Historical Data**: Tracks plants from 1957 to present, including 174 shutdown facilities
- **Future Pipeline**: 55 reactors under construction representing upcoming capacity additions
- **Capacity Range**: Individual plants range from 3 MW to 1,660 MW
- **Primary Use Cases**: Energy policy analysis, capacity forecasting, technology assessment, geographic distribution studies, safety analysis, and market intelligence

## Schema

| Column Name | Data Type | Nullable | Description |
|------------|-----------|----------|-------------|
| Id | INT | NO | Primary key, unique identifier for each nuclear plant |
| Name | VARCHAR(255) | NO | Official name of the nuclear power plant |
| Latitude | DECIMAL(10,6) | YES | Geographic latitude coordinate |
| Longitude | DECIMAL(10,6) | YES | Geographic longitude coordinate |
| CountryCode | VARCHAR(2) | NO | ISO 3166-1 alpha-2 country code (FK to countries) |
| StatusId | INT | NO | Current lifecycle status (FK to nuclear_power_plant_status_types) |
| ReactorTypeId | INT | YES | Technology classification (FK to nuclear_reactor_types) |
| ReactorModel | VARCHAR(100) | YES | Specific reactor model/variant (e.g., "KLT-40S 'Floating'") |
| ConstructionStartAt | DATE | YES | Date when construction began |
| OperationalFrom | DATE | YES | Date when plant began commercial operation |
| OperationalTo | DATE | YES | Date when plant ceased operation (NULL if still operating) |
| Capacity | INT | YES | Net electrical capacity in megawatts (MW) |
| Source | VARCHAR(50) | YES | Data source reference (typically "WNA/IAEA") |
| LastUpdatedAt | DATETIME | NO | Timestamp of last data update |

## Relationships
- Many plants belong to one country (many-to-one with countries via CountryCode)
- Many plants use one reactor type (many-to-one with nuclear_reactor_types via ReactorTypeId)
- Many plants have one status (many-to-one with nuclear_power_plant_status_types via StatusId)

## Common Business Rules

### Status-Based Definitions
1. **Active Nuclear Fleet**: StatusId = 3 (Operational)
2. **Future Capacity**: StatusId IN (1, 2) - Planned or Under Construction
3. **Retired Plants**: StatusId = 5 (Shutdown)
4. **At-Risk Plants**: StatusId = 4 (Suspended Operation)
5. **Total Operating Experience**: StatusId IN (3, 4, 5) - Ever operated

### Capacity Categories
1. **Small Reactors**: Capacity < 400 MW
2. **Medium Reactors**: Capacity 400-900 MW
3. **Large Reactors**: Capacity > 900 MW
4. **Mega Reactors**: Capacity > 1,400 MW (EPR, VVER-1200)

### Age-Based Classifications
1. **New Plants**: OperationalFrom within last 10 years
2. **Mid-Life Plants**: 10-30 years of operation
3. **Aging Fleet**: 30-40 years of operation
4. **Life Extension Candidates**: > 40 years of operation

### Geographic Groups
1. **Top 5 Nuclear Nations**: US (137), China (91), France (72), Japan (71), Russia (56)
2. **Nuclear Energy Dependent**: France, Slovakia (>50% of electricity from nuclear)
3. **Emerging Nuclear**: China, India, UAE (rapid expansion)

## Global Statistics (788 Total Plants)
- **Operational**: 464 plants (~59%)
- **Shutdown**: 174 plants (~22%)
- **Under Construction**: 55 plants (~7%)
- **Other Statuses**: 95 plants (~12%)
- **Total Global Capacity**: ~450,000 MW (operational only)
- **Average Plant Size**: ~970 MW (operational plants)

## Sample Queries and Intent

### Current global nuclear capacity
**Natural Language**: "What's the total nuclear capacity worldwide?"
**Intent**: Calculate aggregate operational capacity
**SQL**:
```sql
SELECT COUNT(*) as operational_plants,
       SUM(Capacity) as total_capacity_mw,
       ROUND(AVG(Capacity), 0) as avg_capacity_mw,
       MIN(Capacity) as smallest_plant_mw,
       MAX(Capacity) as largest_plant_mw
FROM nuclear_power_plants
WHERE StatusId = 3 AND Capacity IS NOT NULL;
```

### Country-specific analysis
**Natural Language**: "Show me all nuclear plants in China"
**Intent**: List facilities with details for specific country
**SQL**:
```sql
SELECT npp.Name, npp.Capacity,
       st.Type as Status,
       rt.Description as Reactor_Type,
       npp.OperationalFrom,
       npp.ConstructionStartAt
FROM nuclear_power_plants npp
JOIN countries c ON npp.CountryCode = c.Id
JOIN nuclear_power_plant_status_type st ON npp.StatusId = st.Id
LEFT JOIN nuclear_reactor_type rt ON npp.ReactorTypeId = rt.Id
WHERE c.Id = 'CN'
ORDER BY npp.StatusId, npp.OperationalFrom DESC;
```

### Capacity expansion forecast
**Natural Language**: "How much nuclear capacity is under construction?"
**Intent**: Analyze future capacity pipeline by country
**SQL**:
```sql
SELECT c.Name as Country,
       COUNT(npp.Id) as reactors_under_construction,
       SUM(npp.Capacity) as future_capacity_mw,
       MIN(npp.ConstructionStartAt) as earliest_start,
       MAX(npp.ConstructionStartAt) as latest_start
FROM nuclear_power_plants npp
JOIN countries c ON npp.CountryCode = c.Id
WHERE npp.StatusId = 2
GROUP BY c.Id, c.Name
ORDER BY future_capacity_mw DESC;
```

### Aging fleet analysis
**Natural Language**: "Which nuclear plants are over 40 years old?"
**Intent**: Identify plants requiring life extension or replacement
**SQL**:
```sql
SELECT npp.Name, c.Name as Country,
       npp.OperationalFrom,
       YEAR(CURDATE()) - YEAR(npp.OperationalFrom) as age_years,
       npp.Capacity,
       rt.Type as Reactor_Type
FROM nuclear_power_plants npp
JOIN countries c ON npp.CountryCode = c.Id
LEFT JOIN nuclear_reactor_type rt ON npp.ReactorTypeId = rt.Id
WHERE npp.StatusId = 3
  AND npp.OperationalFrom IS NOT NULL
  AND YEAR(CURDATE()) - YEAR(npp.OperationalFrom) >= 40
ORDER BY age_years DESC;
```

### Shutdown analysis
**Natural Language**: "How many reactors have been permanently closed?"
**Intent**: Analyze decommissioning trends
**SQL**:
```sql
SELECT c.Name as Country,
       COUNT(npp.Id) as shutdown_count,
       SUM(npp.Capacity) as lost_capacity_mw,
       MIN(YEAR(npp.OperationalTo)) as first_shutdown_year,
       MAX(YEAR(npp.OperationalTo)) as latest_shutdown_year
FROM nuclear_power_plants npp
JOIN countries c ON npp.CountryCode = c.Id
WHERE npp.StatusId = 5
  AND npp.OperationalTo IS NOT NULL
GROUP BY c.Id, c.Name
HAVING shutdown_count > 0
ORDER BY shutdown_count DESC;
```

### Plant lifetime analysis
**Natural Language**: "What's the average operational lifespan of nuclear plants?"
**Intent**: Calculate typical operating duration for shutdown plants
**SQL**:
```sql
SELECT rt.Type as Reactor_Type,
       COUNT(*) as shutdown_plants,
       ROUND(AVG(DATEDIFF(npp.OperationalTo, npp.OperationalFrom) / 365.25), 1) as avg_lifespan_years,
       MIN(DATEDIFF(npp.OperationalTo, npp.OperationalFrom) / 365.25) as min_lifespan_years,
       MAX(DATEDIFF(npp.OperationalTo, npp.OperationalFrom) / 365.25) as max_lifespan_years
FROM nuclear_power_plants npp
LEFT JOIN nuclear_reactor_type rt ON npp.ReactorTypeId = rt.Id
WHERE npp.StatusId = 5
  AND npp.OperationalFrom IS NOT NULL
  AND npp.OperationalTo IS NOT NULL
GROUP BY rt.Type
HAVING shutdown_plants >= 3
ORDER BY avg_lifespan_years DESC;
```

### Geographic distribution
**Natural Language**: "Map all operational nuclear plants worldwide"
**Intent**: Get coordinates and details for mapping visualization
**SQL**:
```sql
SELECT npp.Name, npp.Latitude, npp.Longitude,
       c.Name as Country, npp.Capacity,
       rt.Type as Reactor_Type
FROM nuclear_power_plants npp
JOIN countries c ON npp.CountryCode = c.Id
LEFT JOIN nuclear_reactor_type rt ON npp.ReactorTypeId = rt.Id
WHERE npp.StatusId = 3
  AND npp.Latitude IS NOT NULL
  AND npp.Longitude IS NOT NULL
ORDER BY c.Name, npp.Name;
```

### Construction timeline analysis
**Natural Language**: "How long does it take to build a nuclear plant?"
**Intent**: Calculate average construction duration
**SQL**:
```sql
SELECT c.Name as Country,
       rt.Type as Reactor_Type,
       COUNT(*) as plants_completed,
       ROUND(AVG(DATEDIFF(npp.OperationalFrom, npp.ConstructionStartAt) / 365.25), 1) as avg_construction_years
FROM nuclear_power_plants npp
JOIN countries c ON npp.CountryCode = c.Id
LEFT JOIN nuclear_reactor_type rt ON npp.ReactorTypeId = rt.Id
WHERE npp.ConstructionStartAt IS NOT NULL
  AND npp.OperationalFrom IS NOT NULL
  AND npp.StatusId IN (3, 4, 5)
GROUP BY c.Id, c.Name, rt.Type
HAVING plants_completed >= 5
ORDER BY avg_construction_years;
```

### Recent deployments
**Natural Language**: "Which nuclear plants came online in the last 5 years?"
**Intent**: Identify newest operational reactors
**SQL**:
```sql
SELECT npp.Name, c.Name as Country,
       npp.OperationalFrom,
       npp.Capacity,
       rt.Description as Reactor_Type
FROM nuclear_power_plants npp
JOIN countries c ON npp.CountryCode = c.Id
LEFT JOIN nuclear_reactor_type rt ON npp.ReactorTypeId = rt.Id
WHERE npp.StatusId = 3
  AND npp.OperationalFrom >= DATE_SUB(CURDATE(), INTERVAL 5 YEAR)
ORDER BY npp.OperationalFrom DESC;
```

### Technology market share
**Natural Language**: "What percentage of reactors use PWR technology?"
**Intent**: Calculate technology distribution
**SQL**:
```sql
SELECT rt.Type, rt.Description,
       COUNT(npp.Id) as reactor_count,
       ROUND(COUNT(npp.Id) * 100.0 / (SELECT COUNT(*) FROM nuclear_power_plants WHERE StatusId = 3), 2) as market_share_percent,
       SUM(npp.Capacity) as total_capacity_mw
FROM nuclear_power_plants npp
JOIN nuclear_reactor_type rt ON npp.ReactorTypeId = rt.Id
WHERE npp.StatusId = 3
GROUP BY rt.Id, rt.Type, rt.Description
ORDER BY reactor_count DESC;
```

### Capacity utilization by country
**Natural Language**: "Compare nuclear capacity across top nuclear countries"
**Intent**: Rank countries by total operational capacity
**SQL**:
```sql
SELECT c.Name as Country,
       COUNT(npp.Id) as reactor_count,
       SUM(npp.Capacity) as total_capacity_mw,
       ROUND(AVG(npp.Capacity), 0) as avg_reactor_size_mw,
       MIN(YEAR(npp.OperationalFrom)) as nuclear_program_started
FROM nuclear_power_plants npp
JOIN countries c ON npp.CountryCode = c.Id
WHERE npp.StatusId = 3 AND npp.Capacity IS NOT NULL
GROUP BY c.Id, c.Name
ORDER BY total_capacity_mw DESC
LIMIT 15;
```

## Column Value Examples and Ranges

### Name Examples
- "Ågesta" (Sweden - first shutdown plant)
- "Akademik Lomonosov-1 (Vilyuchinsk)" (Russia - floating plant)
- "Bruce-1" through "Bruce-8" (Canada - multi-unit station)
- "Fukushima Daiichi-1" (Japan - famous incident)

### Geographic Coordinates
- Latitude: -37.8° (Australia) to 71.3° (Russia Arctic)
- Longitude: -124.7° (US West Coast) to 152.5° (Russia Far East)

### Capacity Distribution
- Smallest: 3 MW (experimental/prototype reactors)
- Typical Range: 500-1,200 MW (most commercial reactors)
- Largest: 1,660 MW (modern EPR, VVER-1200 designs)

### Date Ranges
- Construction Started: 1954 to 2024
- Operational From: 1957 (Shippingport, US) to 2024
- Operational To: 1964 to present (for shutdown plants)

### ReactorModel Examples
- "KLT-40S 'Floating'" - Floating power plant
- "CP-300" - Chinese PWR variant
- "ABWR-1356" - Advanced BWR model
- NULL - Many entries rely on ReactorTypeId instead

## Important Notes

### Data Quality Considerations
- **NULL Handling**: ReactorTypeId, ReactorModel, dates may be NULL for some plants
- **Capacity**: Always check for NULL values; some historical plants lack capacity data
- **Coordinates**: Most plants have lat/long; use for geographic visualizations
- **Source Field**: Primarily "WNA/IAEA" indicating World Nuclear Association / International Atomic Energy Agency

### Query Best Practices
1. **Always filter by StatusId** when calculating current capacity
2. **Use date filters** for performance on large time-series queries
3. **LEFT JOIN for reactor types** since ReactorTypeId can be NULL
4. **Check for NULL dates** when calculating durations or lifespans
5. **Group by country** for most business intelligence queries
6. **Consider time zones** when using LastUpdatedAt timestamps

### Common Analysis Patterns
- **Capacity Analysis**: Always SUM(Capacity) with StatusId = 3 filter
- **Geographic Analysis**: Use CountryCode, Latitude, Longitude
- **Temporal Analysis**: Compare ConstructionStartAt, OperationalFrom, OperationalTo
- **Technology Analysis**: JOIN with nuclear_reactor_type on ReactorTypeId
- **Lifecycle Analysis**: JOIN with nuclear_power_plant_status_type on StatusId

### Business Intelligence Metrics
1. **Global Nuclear Capacity**: SUM(Capacity) WHERE StatusId = 3
2. **Capacity Factor**: Requires external production data (not in this table)
3. **Fleet Age**: AVG(YEAR(CURDATE()) - YEAR(OperationalFrom))
4. **Construction Pipeline**: COUNT(*) WHERE StatusId = 2
5. **Retirement Rate**: COUNT(*) WHERE StatusId = 5 AND YEAR(OperationalTo) = [specific year]
6. **Geographic Concentration**: GROUP BY CountryCode with ORDER BY COUNT(*)

## Advanced Query Scenarios

### Multi-unit nuclear stations
Nuclear plants often have multiple reactors at the same location:
```sql
SELECT 
    SUBSTRING_INDEX(Name, '-', 1) as Station_Name,
    CountryCode,
    COUNT(*) as Unit_Count,
    SUM(Capacity) as Station_Capacity_MW
FROM nuclear_power_plants
WHERE StatusId = 3 AND Name LIKE '%-%'
GROUP BY Station_Name, CountryCode
HAVING Unit_Count > 1
ORDER BY Station_Capacity_MW DESC;
```

### Capacity replacement needs (shutdowns vs new construction)
```sql
SELECT 
    YEAR(COALESCE(OperationalTo, ConstructionStartAt)) as Year,
    SUM(CASE WHEN StatusId = 5 THEN Capacity ELSE 0 END) as Retired_Capacity_MW,
    SUM(CASE WHEN StatusId = 2 THEN Capacity ELSE 0 END) as Under_Construction_MW,
    SUM(CASE WHEN StatusId = 2 THEN Capacity ELSE 0 END) - 
    SUM(CASE WHEN StatusId = 5 THEN Capacity ELSE 0 END) as Net_Capacity_Change_MW
FROM nuclear_power_plants
WHERE (StatusId = 5 OR StatusId = 2)
  AND YEAR(COALESCE(OperationalTo, ConstructionStartAt)) >= 2010
GROUP BY Year
ORDER BY Year;
```

## Conference Talk Context
This database is ideal for demonstrating Text2SQL capabilities because:
- **Complex relationships**: 4 related tables with foreign keys
- **Rich metadata**: Multiple dimensions (geography, technology, time, status)
- **Business intelligence**: Real-world energy policy and market analysis
- **Temporal analysis**: Historical trends and forecasting scenarios
- **Natural language variety**: Many ways to ask similar questions
- **Data quality challenges**: NULL values, optional fields requiring careful handling