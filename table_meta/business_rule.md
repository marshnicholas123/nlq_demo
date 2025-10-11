# Nuclear Power Database - Business Rules

This document contains business rules for SQL query generation. Each rule is designed to be independently retrievable based on user query context.

---

## RULE: Operational Plants Query Pattern
**When to use**: User asks for "operational", "active", "current", "running", or "generating" plants
**Definition**: Plants currently generating electricity
**SQL Implementation**:
```sql
WHERE StatusId = 3
```
**Global context**: 464 operational plants worldwide (59% of total fleet)
**Example queries**: "Show me operational plants", "How many active reactors", "Current nuclear capacity"

---

## RULE: Under Construction Plants Query Pattern
**When to use**: User asks for "under construction", "being built", "future", "upcoming", or "expansion"
**Definition**: Plants being actively built, representing future capacity additions
**SQL Implementation**:
```sql
WHERE StatusId = 2
```
**Example queries**: "Which countries are expanding nuclear capacity?", "Plants under construction", "Future nuclear projects"

---

## RULE: Planned Capacity Query Pattern
**When to use**: User asks for "planned", "proposed", or "future beyond construction"
**Definition**: Plants in planning/proposal stage, not yet approved for construction
**SQL Implementation**:
```sql
WHERE StatusId = 1
```
**Example queries**: "What's in the planning pipeline?", "Proposed nuclear plants", "Future nuclear plans"

---

## RULE: Shutdown Plants Query Pattern
**When to use**: User asks for "shutdown", "closed", "retired", "decommissioned", or "permanently offline"
**Definition**: Permanently closed facilities, no longer generating power
**SQL Implementation**:
```sql
WHERE StatusId = 5
```
**Global context**: 174 shutdown plants worldwide (22% of total fleet)
**Example queries**: "How many plants have been shut down?", "Retired nuclear facilities", "Decommissioned reactors"

---

## RULE: Suspended Operation Query Pattern
**When to use**: User asks for "suspended", "temporarily offline", "paused", or "at risk"
**Definition**: Temporarily offline due to maintenance, safety review, or political reasons
**SQL Implementation**:
```sql
WHERE StatusId = 4
```
**Note**: These plants may return to operational status or be permanently shutdown
**Example queries**: "Plants suspended for safety", "Temporarily offline reactors"

---

## RULE: Failed Projects Query Pattern
**When to use**: User asks for "cancelled", "abandoned", "failed", or "unfinished" projects
**Definition**: Construction projects that were cancelled, never completed, or never started
**SQL Implementation**:
```sql
WHERE StatusId IN (6, 7, 8, 9)
```
**Status breakdown**:
- StatusId = 6: Unfinished (construction started but never completed)
- StatusId = 7: Never Built (planned but construction never began)
- StatusId = 8: Suspended Construction (construction paused indefinitely)
- StatusId = 9: Cancelled Construction (officially cancelled)

---

## RULE: Future Capacity Pipeline Query Pattern
**When to use**: User asks for "pipeline", "future capacity", or "expansion programs"
**Definition**: Upcoming capacity additions combining planned and under construction
**SQL Implementation**:
```sql
WHERE StatusId IN (1, 2)
```
**Example queries**: "What's in the nuclear pipeline?", "Future expansion plans", "Upcoming nuclear capacity"

---

## RULE: Ever Operated Plants Query Pattern
**When to use**: User asks for "nuclear experience", "historical capacity", or "ever operational"
**Definition**: Plants that have operated at any point (current, suspended, or shutdown)
**SQL Implementation**:
```sql
WHERE StatusId IN (3, 4, 5)
```
**Use case**: Understanding total historical nuclear deployment

---

## RULE: Current Capacity Calculation
**When to use**: User asks for "current capacity", "total capacity", or "operational capacity"
**Definition**: Total megawatts of electricity being generated now
**SQL Implementation**:
```sql
SUM(Capacity) WHERE StatusId = 3 AND Capacity IS NOT NULL
```
**Critical**: Always filter by StatusId = 3 and exclude NULL capacity values
**Example queries**: "What's the total nuclear capacity?", "Current megawatts", "Operational capacity"

---

## RULE: Future Capacity Under Construction
**When to use**: User asks for "upcoming capacity", "expansion capacity", or "future additions"
**Definition**: Megawatts being added through active construction
**SQL Implementation**:
```sql
SUM(Capacity) WHERE StatusId = 2 AND Capacity IS NOT NULL
```
**Example queries**: "How much capacity is being built?", "Future nuclear additions"

---

## RULE: Lost Capacity from Shutdowns
**When to use**: Analyzing decommissioning trends or capacity losses
**Definition**: Megawatts removed from service through permanent shutdowns
**SQL Implementation**:
```sql
SUM(Capacity) WHERE StatusId = 5 AND Capacity IS NOT NULL
```
**Example queries**: "Capacity lost to shutdowns", "Decommissioned megawatts"

---

## RULE: Average Plant Size Calculation
**When to use**: User asks about "typical reactor size", "average capacity", or plant size norms
**Definition**: Mean capacity per operational plant
**Global average**: ~970 MW for operational plants
**SQL Implementation**:
```sql
AVG(Capacity) WHERE StatusId = 3 AND Capacity IS NOT NULL
```

---

## RULE: Small Reactors Classification
**When to use**: User asks about "small reactors", "low capacity", or experimental reactors
**Definition**: Lower capacity units, often older or experimental designs
**Capacity range**: Less than 400 MW
**SQL Implementation**:
```sql
WHERE Capacity < 400 AND Capacity IS NOT NULL
```

---

## RULE: Medium Reactors Classification
**When to use**: User asks about "standard reactors", "typical size", or medium capacity
**Definition**: Standard commercial reactor size range
**Capacity range**: 400 to 900 MW
**SQL Implementation**:
```sql
WHERE Capacity BETWEEN 400 AND 900
```

---

## RULE: Large Reactors Classification
**When to use**: User asks about "large reactors", "high capacity" plants
**Definition**: High capacity modern commercial reactors
**Capacity range**: Greater than 900 MW
**SQL Implementation**:
```sql
WHERE Capacity > 900
```

---

## RULE: Mega Reactors Classification
**When to use**: User asks about "largest reactors", "very high capacity", "EPR", or Generation III+
**Definition**: Very large Generation III+ reactor designs
**Capacity range**: Greater than 1400 MW
**SQL Implementation**:
```sql
WHERE Capacity > 1400
```
**Examples**: EPR reactors (~1,600 MW), VVER-1200 (~1,200 MW)

---

## RULE: Country Name Display with JOIN
**When to use**: ANY query displaying country information
**Definition**: Always join with countries table to get readable country names
**SQL Implementation**:
```sql
JOIN countries c ON npp.CountryCode = c.Id
```
**Critical**: CountryCode stores ISO codes (US, CN, FR), not display names. Never display CountryCode without joining to countries table.

---

## RULE: ISO Country Code Format
**When to use**: Filtering by specific country
**Definition**: Use ISO 3166-1 alpha-2 codes (2 letters, uppercase)
**Examples**: US, CN, FR, JP, RU, KR, IN, CA, GB, DE
**SQL Implementation**:
```sql
WHERE CountryCode = 'US'
```
**Wrong**: 'USA', 'United States', 'America'
**Right**: 'US'

---

## RULE: Top Nuclear Nations Reference
**When to use**: User asks about "most nuclear plants", "top countries", or country rankings
**Definition**: Countries with the most nuclear facilities
**Top 5**: United States (137), China (91), France (72), Japan (71), Russia (56)
**SQL Implementation**:
```sql
GROUP BY CountryCode ORDER BY COUNT(*) DESC
```

---

## RULE: Emerging Nuclear Programs
**When to use**: User asks about "rapidly expanding", "new nuclear programs", or "emerging nuclear"
**Definition**: Countries with significant construction activity
**Primary examples**: China, India, UAE
**SQL Implementation**:
```sql
WHERE StatusId = 2
GROUP BY CountryCode
ORDER BY COUNT(*) DESC
```

---

## RULE: Geographic Mapping Data
**When to use**: User wants map visualization or location-based queries
**Definition**: Use Latitude and Longitude fields for geographic display
**SQL Implementation**:
```sql
WHERE Latitude IS NOT NULL AND Longitude IS NOT NULL
```
**Note**: Most plants have coordinates, but always filter NULL values for mapping

---

## RULE: Plant Age Calculation
**When to use**: User asks about "age", "how old", or plant vintage
**Definition**: Calculate years since commercial operation began
**SQL Implementation**:
```sql
YEAR(CURDATE()) - YEAR(OperationalFrom) AS age_years
```
**Use OperationalFrom, not ConstructionStartAt**
**Filter**: WHERE OperationalFrom IS NOT NULL

---

## RULE: New Plants Classification
**When to use**: User asks for "new", "recent", or "latest" plants
**Definition**: Recently deployed reactors in last 10 years
**SQL Implementation**:
```sql
WHERE OperationalFrom >= DATE_SUB(CURDATE(), INTERVAL 10 YEAR)
```

---

## RULE: Aging Fleet Classification
**When to use**: User asks about "old reactors", "aging fleet", or retirement candidates
**Definition**: Plants 30-40 years old approaching end of design life
**SQL Implementation**:
```sql
WHERE YEAR(CURDATE()) - YEAR(OperationalFrom) BETWEEN 30 AND 40
AND StatusId = 3
```

---

## RULE: Life Extension Candidates
**When to use**: User asks about "oldest plants", "license renewal", or retirement risk
**Definition**: Very old operational plants requiring license renewal or replacement
**Age threshold**: Greater than 40 years
**SQL Implementation**:
```sql
WHERE YEAR(CURDATE()) - YEAR(OperationalFrom) > 40
AND StatusId = 3
```

---

## RULE: Operational Lifetime for Shutdown Plants
**When to use**: User asks "how long did plants operate", "typical lifespan", or historical operation duration
**Definition**: Total years a plant operated before permanent closure
**SQL Implementation**:
```sql
DATEDIFF(OperationalTo, OperationalFrom) / 365.25 AS lifespan_years
WHERE OperationalFrom IS NOT NULL
AND OperationalTo IS NOT NULL
```
**Average**: 35-45 years for shutdown plants globally

---

## RULE: Construction Duration Analysis
**When to use**: User asks about "construction time", "build duration", or project timelines
**Definition**: Time from construction start to commercial operation
**SQL Implementation**:
```sql
DATEDIFF(OperationalFrom, ConstructionStartAt) / 365.25 AS construction_years
WHERE ConstructionStartAt IS NOT NULL
AND OperationalFrom IS NOT NULL
```
**Typical range**: 5-10 years for most plants

---

## RULE: PWR Pressurized Water Reactors
**When to use**: User asks about "PWR", "pressurized water", or most common reactor type
**Definition**: Most common reactor type worldwide (~60% market share)
**SQL Implementation**:
```sql
WHERE ReactorTypeId = 22
-- OR using join:
WHERE rt.Type = 'PWR'
```
**Characteristics**: Two separate water loops, high pressure, enriched uranium

---

## RULE: BWR Boiling Water Reactors
**When to use**: User asks about "BWR" or "boiling water reactors"
**Definition**: Second most common reactor type (~20% market share)
**SQL Implementation**:
```sql
WHERE ReactorTypeId = 5
-- OR using join:
WHERE rt.Type = 'BWR'
```
**Characteristics**: Single water loop, lower pressure than PWR

---

## RULE: VVER Russian Reactor Type
**When to use**: User asks about "VVER", "Russian reactors", or Eastern European nuclear technology
**Definition**: Russian PWR variant (Water-Water Energetic Reactor)
**Geographic distribution**: Primarily Russia, Eastern Europe, China
**SQL Implementation**:
```sql
WHERE ReactorTypeId = 24
-- OR using join:
WHERE rt.Type = 'VVER'
```

---

## RULE: PHWR CANDU Canadian Reactors
**When to use**: User asks about "CANDU", "heavy water", "Canadian reactors", or natural uranium
**Definition**: Pressurized Heavy Water Reactor (Canadian design)
**Geographic distribution**: Canada, India, Argentina, China
**SQL Implementation**:
```sql
WHERE ReactorTypeId = 19
-- OR using join:
WHERE rt.Type = 'PHWR'
```
**Characteristics**: Uses natural uranium (no enrichment), heavy water moderator

---

## RULE: Advanced Generation III Reactors
**When to use**: User asks about "advanced reactors", "Generation III", "modern designs"
**Definition**: 1990s-2010s designs with enhanced safety features
**Types**: ABWR, APWR, APR, EPR
**SQL Implementation**:
```sql
WHERE rt.Type IN ('ABWR', 'APWR', 'APR', 'EPR')
AND StatusId IN (2, 3)
```
**Characteristics**: Passive safety systems, improved efficiency

---

## RULE: EPR Generation III+ Reactors
**When to use**: User asks about "EPR", "Generation III+", "Evolutionary Power Reactor", or latest commercial designs
**Definition**: Latest generation commercial reactors (2010s+)
**SQL Implementation**:
```sql
WHERE rt.Type = 'EPR'
```
**Characteristics**: Enhanced safety, very large capacity (>1,600 MW)

---

## RULE: Fast Breeder Reactors
**When to use**: User asks about "fast breeder", "FBR", or fuel breeding technology
**Definition**: Advanced reactors that produce more fuel than they consume
**Types**: FBR, LMFBR, LFR
**SQL Implementation**:
```sql
WHERE rt.Type IN ('FBR', 'LMFBR', 'LFR')
```
**Note**: Rare but strategically important for advanced fuel cycles

---

## RULE: Gas Cooled Reactors
**When to use**: User asks about "gas cooled", "AGR", or UK reactor technology
**Definition**: Reactors using gas (CO2, helium) as coolant
**Types**: AGR, GCR, HTGR
**SQL Implementation**:
```sql
WHERE rt.Type IN ('AGR', 'GCR', 'HTGR')
```
**Geographic**: Primarily UK (AGR), historically used elsewhere

---

## RULE: Reactor Type JOIN Pattern
**When to use**: ANY query involving reactor type information
**Definition**: Use LEFT JOIN because ReactorTypeId can be NULL
**SQL Implementation**:
```sql
LEFT JOIN nuclear_reactor_type rt ON npp.ReactorTypeId = rt.Id
```
**Never use INNER JOIN** - would exclude plants with NULL ReactorTypeId

---

## RULE: Country Comparison Between Two Nations
**When to use**: User asks "compare X to Y", "X versus Y", or "difference between X and Y"
**SQL Implementation**:
```sql
WHERE CountryCode IN ('US', 'CN')
GROUP BY CountryCode, c.Name
```
**Pattern**: Use IN clause with ISO codes, group by country

---

## RULE: Top N Countries Ranking
**When to use**: User asks for "top 10 countries", "leading nations", or country rankings
**SQL Implementation**:
```sql
GROUP BY c.Id, c.Name
ORDER BY COUNT(*) DESC
LIMIT 10
```
**Common metrics**: plant_count, total_capacity, under_construction_count

---

## RULE: Year Over Year Trend Analysis
**When to use**: User asks about "historical trends", "deployment by year", or "nuclear growth over time"
**SQL Implementation**:
```sql
GROUP BY YEAR(OperationalFrom)
ORDER BY YEAR(OperationalFrom)
```
**Use with**: COUNT(*) or SUM(Capacity) for trend analysis

---

## RULE: Percentage Market Share Calculation
**When to use**: User asks "what percentage", "market share", or proportion questions
**SQL Implementation**:
```sql
COUNT(*) * 100.0 / (SELECT COUNT(*) FROM nuclear_power_plants WHERE StatusId = 3) AS percentage
```
**Note**: Ensure denominator uses same filters as appropriate for context

---

## RULE: Multi-Unit Station Aggregation
**When to use**: User asks about "stations" vs "reactors", or site-level totals
**Definition**: Some sites have multiple reactor units (e.g., "Bruce-1" through "Bruce-8")
**Pattern**: Names with "-" often indicate unit numbers
**SQL Implementation**:
```sql
SUBSTRING_INDEX(Name, '-', 1) AS station_name
GROUP BY station_name
```

---

## RULE: Count Plants Aggregation
**When to use**: User asks "how many plants", "number of reactors", or facility counts
**SQL Implementation**:
```sql
COUNT(*) AS plant_count
-- OR
COUNT(Id) AS plant_count
```
**Group by**: CountryCode, StatusId, or ReactorTypeId as appropriate

---

## RULE: Sum Total Capacity Aggregation
**When to use**: User asks for "total capacity", "total megawatts", or capacity sums
**SQL Implementation**:
```sql
SUM(Capacity) AS total_capacity_mw
WHERE Capacity IS NOT NULL
AND StatusId = [appropriate status]
```
**Critical**: Always filter NULL capacity and apply appropriate StatusId

---

## RULE: Average Capacity Calculation
**When to use**: User asks for "average capacity", "mean size", or typical plant capacity
**SQL Implementation**:
```sql
ROUND(AVG(Capacity), 0) AS avg_capacity_mw
WHERE Capacity IS NOT NULL
AND StatusId = [appropriate status]
```

---

## RULE: Capacity Range Min/Max
**When to use**: User asks about "largest plant", "smallest reactor", or capacity distribution
**SQL Implementation**:
```sql
MIN(Capacity) AS smallest_mw,
MAX(Capacity) AS largest_mw
WHERE Capacity IS NOT NULL
```

---

## RULE: Default Result Limiting
**When to use**: Non-aggregate queries returning plant lists
**SQL Implementation**:
```sql
LIMIT 100
```
**Override**: If user specifies "all" or query is aggregate, don't limit

---

## RULE: Default Sorting for Plant Lists
**When to use**: Providing plant lists without specific sort request
**Default patterns**:
- Country rankings: ORDER BY plant_count DESC
- Plant lists: ORDER BY Name ASC
- Capacity: ORDER BY Capacity DESC
- Temporal: ORDER BY OperationalFrom DESC

---

## RULE: Status Table JOIN Pattern
**When to use**: Displaying readable status names
**SQL Implementation**:
```sql
JOIN nuclear_power_plant_status_type st ON npp.StatusId = st.Id
```
**Use INNER JOIN** - StatusId is never NULL

---

## RULE: Standard Table Aliases
**When to use**: ALL queries for consistency and clarity
**Standard aliases**:
- nuclear_power_plants → npp
- countries → c
- nuclear_reactor_type → rt
- nuclear_power_plant_status_type → st

---

## RULE: NULL Date Field Handling
**When to use**: ANY query using date fields in calculations or WHERE clauses
**Fields that can be NULL**: OperationalFrom, OperationalTo, ConstructionStartAt
**SQL Implementation**:
```sql
WHERE OperationalFrom IS NOT NULL
```
**Critical**: Always check before using in DATEDIFF or date arithmetic

---

## RULE: NULL Capacity Handling
**When to use**: ANY capacity aggregation (SUM, AVG, MIN, MAX)
**SQL Implementation**:
```sql
WHERE Capacity IS NOT NULL
```
**Reason**: Some plants (especially planned or historical) lack capacity data

---

## RULE: NULL Coordinate Validation for Mapping
**When to use**: Geographic visualization or location-based analysis
**SQL Implementation**:
```sql
WHERE Latitude IS NOT NULL
AND Longitude IS NOT NULL
```

---

## RULE: Experimental Small Reactors
**When to use**: User asks about "experimental", "prototype", or very small reactors
**Definition**: Very low capacity often indicates experimental/prototype designs
**Capacity threshold**: Less than 50 MW
**SQL Implementation**:
```sql
WHERE Capacity < 50 AND Capacity IS NOT NULL
```

---

## RULE: Floating Nuclear Reactors
**When to use**: User asks about "floating reactors" or maritime nuclear power
**Definition**: Reactors mounted on floating platforms
**Example**: Akademik Lomonosov (Russia)
**SQL Implementation**:
```sql
WHERE ReactorModel LIKE '%Floating%'
```

---

## RULE: Revenue Generating Plants
**When to use**: Business/financial analysis of revenue-generating facilities
**Definition**: Only operational plants generate revenue
**SQL Implementation**:
```sql
WHERE StatusId = 3
```
**Never include**: Planned, under construction, or shutdown in revenue calculations

---

## RULE: Active Investment Projects
**When to use**: Analyzing capital investment or active construction spending
**Definition**: Projects representing active capital investment
**SQL Implementation**:
```sql
WHERE StatusId = 2
```
**Include planned for pipeline**: StatusId IN (1, 2)

---

## RULE: Regional Grouping for Asia
**When to use**: User asks about "Asian nuclear programs" or regional Asian analysis
**Countries**: China (CN), Japan (JP), South Korea (KR), India (IN)
**SQL Implementation**:
```sql
WHERE CountryCode IN ('CN', 'JP', 'KR', 'IN')
```

---

## RULE: Regional Grouping for Europe
**When to use**: User asks about "European nuclear" or Western European analysis
**Countries**: France (FR), United Kingdom (GB), Germany (DE), Spain (ES)
**SQL Implementation**:
```sql
WHERE CountryCode IN ('FR', 'GB', 'DE', 'ES')
```

---

## RULE: Regional Grouping for Eastern Europe
**When to use**: User asks about "Eastern European nuclear" or former Soviet states
**Countries**: Russia (RU), Ukraine (UA), Czech Republic (CZ), Slovakia (SK)
**SQL Implementation**:
```sql
WHERE CountryCode IN ('RU', 'UA', 'CZ', 'SK')
```

---

## RULE: Regional Grouping for North America
**When to use**: User asks about "North American nuclear programs"
**Countries**: United States (US), Canada (CA)
**SQL Implementation**:
```sql
WHERE CountryCode IN ('US', 'CA')
```

---

## RULE: Query Optimization with Indexed Fields
**When to use**: ALL queries for performance
**Indexed fields**: Id, CountryCode, StatusId, ReactorTypeId
**Pattern**: Filter on indexed columns first in WHERE clauses
**Avoid**: Functions on indexed columns like WHERE YEAR(OperationalFrom) = 2020
**Prefer**: WHERE OperationalFrom BETWEEN '2020-01-01' AND '2020-12-31'

---

## DATABASE SCHEMA: nuclear_power_plants table structure
**Primary table**: nuclear_power_plants (alias: npp)
**Key fields**:
- Id: Primary key
- Name: Plant/reactor name
- CountryCode: ISO 3166-1 alpha-2 code (join to countries.Id)
- StatusId: Plant status (join to nuclear_power_plant_status_type.Id)
- Capacity: Megawatts (can be NULL)
- ReactorTypeId: Reactor technology (join to nuclear_reactor_type.Id, can be NULL)
- ReactorModel: Specific reactor variant (can be NULL)
- OperationalFrom: Commercial operation start date (can be NULL)
- OperationalTo: Permanent shutdown date (NULL if operational)
- ConstructionStartAt: Construction start date (can be NULL)
- Latitude: Geographic coordinate (can be NULL)
- Longitude: Geographic coordinate (can be NULL)
- Source: Data source reference

---

## DATABASE SCHEMA: countries table structure
**Table**: countries (alias: c)
**Key fields**:
- Id: ISO country code (US, CN, FR, etc.)
- Name: Full country name
**JOIN pattern**: JOIN countries c ON npp.CountryCode = c.Id

---

## DATABASE SCHEMA: nuclear_power_plant_status_type table
**Table**: nuclear_power_plant_status_type (alias: st)
**Status values**:
- 1: Planned
- 2: Under Construction
- 3: Operational
- 4: Suspended Operation
- 5: Shutdown
- 6: Unfinished
- 7: Never Built
- 8: Suspended Construction
- 9: Cancelled Construction
**JOIN pattern**: JOIN nuclear_power_plant_status_type st ON npp.StatusId = st.Id

---

## DATABASE SCHEMA: nuclear_reactor_type table
**Table**: nuclear_reactor_type (alias: rt)
**Common types**: PWR, BWR, VVER, PHWR, AGR, EPR, ABWR, FBR
**Key fields**:
- Id: Primary key
- Type: Reactor type code
**JOIN pattern**: LEFT JOIN nuclear_reactor_type rt ON npp.ReactorTypeId = rt.Id
**Use LEFT JOIN** - ReactorTypeId can be NULL
