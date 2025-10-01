# Nuclear Reactor Types Table

## Table Description
The nuclear_reactor_types table is a comprehensive reference table cataloging all nuclear reactor technologies used in power generation worldwide. It includes both legacy designs and advanced modern reactor types, providing technical classification for nuclear facilities.

## Business Context
- Essential for analyzing reactor technology distribution and evolution
- Different reactor types have varying efficiency, safety profiles, and fuel requirements
- Used for technology trend analysis and future reactor selection
- Critical for understanding regional technology preferences and capabilities
- Important for safety analysis and regulatory compliance

## Schema

| Column Name | Data Type | Nullable | Description |
|------------|-----------|----------|-------------|
| Id | INT | NO | Primary key, unique numeric identifier |
| Type | VARCHAR(20) | NO | Short acronym/code for reactor type |
| Description | VARCHAR(255) | NO | Full descriptive name of the reactor technology |

## Relationships
- Referenced by: nuclear_power_plants.ReactorTypeId (foreign key)
- One reactor type can be used in many plants (one-to-many relationship)

## Major Reactor Technology Families

### Water-Cooled Reactors (Most Common)
| Id | Type | Description | Generation |
|----|------|-------------|------------|
| 5 | BWR | Boiling Water Reactor | Gen II |
| 1 | ABWR | Advanced Boiling Water Reactor | Gen III |
| 22 | PWR | Pressurised Water Reactor | Gen II |
| 24 | VVER | Water-Water Energetic Reactor | Gen II (Soviet) |
| 3 | APWR | Advanced Pressurised Water Reactor | Gen III |
| 2 | APR | Advanced Power Reactor | Gen III |
| 6 | EPR | Evolutionary Power Reactor | Gen III+ |

### Gas-Cooled Reactors
| Id | Type | Description |
|----|------|-------------|
| 4 | AGR | Advanced Gas-cooled Reactor |
| 8 | GCR | Gas-Cooled Reactor |
| 9 | HTGR | High-Temperature Gas-cooled Reactor |
| 11 | HWGCR | Heavy Water Gas Cooled Reactor |

### Heavy Water Reactors
| Id | Type | Description |
|----|------|-------------|
| 19 | PHWR | Pressurised Heavy Water Reactor (CANDU) |
| 12 | HWLWR | Heavy Water Light Water Reactor |
| 13 | HWOCR | Heavy Water Organic Cooled Reactor |

### Fast Breeder and Advanced Reactors
| Id | Type | Description |
|----|------|-------------|
| 7 | FBR | Fast Breeder Reactor |
| 15 | LMFBR | Liquid Metal Fast Breeder Reactor |
| 14 | LFR | Lead-cooled Fast Reactor |
| 16 | LWGR | Light Water Graphite Reactor |

### Next Generation Technologies
| Id | Type | Description |
|----|------|-------------|
| 10 | HTR-PM | High Temperature Reactor - Pebble Module |
| 23 | SCWR | Supercritical Water Reactor |
| 18 | PBMR | Pebble Bed Modular Reactor |

## Common Business Rules
1. **Generation Classification**:
   - Gen II: BWR, PWR, VVER, PHWR (1960s-1990s designs)
   - Gen III/III+: ABWR, APWR, APR, EPR (1990s-2010s)
   - Gen IV: FBR, HTR-PM, SCWR (Future/experimental)

2. **Technology Dominance**:
   - PWR/VVER: Most common worldwide (~60% of reactors)
   - BWR: Second most common (~20%)
   - PHWR: Popular in Canada, India
   - Others: Specialized or regional use

3. **Safety Evolution**:
   - Advanced reactors (ABWR, APWR, EPR) have enhanced safety features
   - Gen III+ designs include passive safety systems
   - Fast breeders require more complex safety considerations

## Sample Queries and Intent

### Most common reactor types
**Natural Language**: "What are the most popular nuclear reactor technologies?"
**Intent**: Rank reactor types by deployment count
**SQL**:
```sql
SELECT rt.Type, rt.Description,
       COUNT(npp.Id) as plant_count,
       SUM(npp.Capacity) as total_capacity_mw
FROM nuclear_reactor_type rt
JOIN nuclear_power_plants npp ON rt.Id = npp.ReactorTypeId
WHERE npp.StatusId = 3
GROUP BY rt.Id, rt.Type, rt.Description
ORDER BY plant_count DESC
LIMIT 10;
```

### Advanced reactor deployment
**Natural Language**: "How many Generation III+ reactors are operational?"
**Intent**: Count modern advanced reactors
**SQL**:
```sql
SELECT rt.Type, rt.Description, COUNT(npp.Id) as operational_count
FROM nuclear_reactor_type rt
JOIN nuclear_power_plants npp ON rt.Id = npp.ReactorTypeId
WHERE rt.Type IN ('ABWR', 'APWR', 'APR', 'EPR')
  AND npp.StatusId = 3
GROUP BY rt.Id, rt.Type, rt.Description
ORDER BY operational_count DESC;
```

### Reactor technology by country
**Natural Language**: "What reactor types does France use?"
**Intent**: Identify technology portfolio for specific country
**SQL**:
```sql
SELECT rt.Type, rt.Description,
       COUNT(npp.Id) as reactor_count,
       SUM(npp.Capacity) as total_capacity_mw
FROM nuclear_power_plants npp
JOIN nuclear_reactor_type rt ON npp.ReactorTypeId = rt.Id
JOIN countries c ON npp.CountryCode = c.Id
WHERE c.Id = 'FR' AND npp.StatusId = 3
GROUP BY rt.Id, rt.Type, rt.Description
ORDER BY reactor_count DESC;
```

### Fast breeder reactor analysis
**Natural Language**: "Which countries operate fast breeder reactors?"
**Intent**: Find countries with advanced breeding technology
**SQL**:
```sql
SELECT c.Name as Country, npp.Name as Plant_Name,
       rt.Description as Reactor_Type, npp.Capacity
FROM nuclear_power_plants npp
JOIN countries c ON npp.CountryCode = c.Id
JOIN nuclear_reactor_type rt ON npp.ReactorTypeId = rt.Id
WHERE rt.Type IN ('FBR', 'LMFBR', 'LFR')
  AND npp.StatusId IN (2, 3)
ORDER BY c.Name, npp.Name;
```

### Average capacity by reactor type
**Natural Language**: "What's the typical size of different reactor types?"
**Intent**: Compare capacity characteristics across technologies
**SQL**:
```sql
SELECT rt.Type, rt.Description,
       COUNT(npp.Id) as reactor_count,
       ROUND(AVG(npp.Capacity), 0) as avg_capacity_mw,
       MIN(npp.Capacity) as min_capacity_mw,
       MAX(npp.Capacity) as max_capacity_mw
FROM nuclear_reactor_type rt
JOIN nuclear_power_plants npp ON rt.Id = npp.ReactorTypeId
WHERE npp.StatusId = 3 AND npp.Capacity IS NOT NULL
GROUP BY rt.Id, rt.Type, rt.Description
HAVING reactor_count >= 5
ORDER BY avg_capacity_mw DESC;
```

### Technology evolution timeline
**Natural Language**: "When were different reactor types first deployed?"
**Intent**: Analyze technology development chronology
**SQL**:
```sql
SELECT rt.Type, rt.Description,
       MIN(YEAR(npp.OperationalFrom)) as first_deployment,
       MAX(YEAR(npp.OperationalFrom)) as latest_deployment,
       COUNT(*) as total_built
FROM nuclear_reactor_type rt
JOIN nuclear_power_plants npp ON rt.Id = npp.ReactorTypeId
WHERE npp.OperationalFrom IS NOT NULL
GROUP BY rt.Id, rt.Type, rt.Description
ORDER BY first_deployment, rt.Type;
```

### Future reactor technology trends
**Natural Language**: "What reactor types are being built now?"
**Intent**: Identify current construction technology choices
**SQL**:
```sql
SELECT rt.Type, rt.Description,
       COUNT(npp.Id) as under_construction,
       SUM(npp.Capacity) as future_capacity_mw,
       COUNT(DISTINCT npp.CountryCode) as countries_building
FROM nuclear_reactor_type rt
JOIN nuclear_power_plants npp ON rt.Id = npp.ReactorTypeId
WHERE npp.StatusId = 2
GROUP BY rt.Id, rt.Type, rt.Description
ORDER BY under_construction DESC;
```

## Technology Notes

### PWR (Pressurised Water Reactor)
- Most widely deployed design globally
- Uses enriched uranium fuel
- Two separate water loops (primary and secondary)
- High pressure primary coolant (~155 bar)

### BWR (Boiling Water Reactor)
- Second most common design
- Single water loop (water boils in reactor core)
- Slightly simpler design than PWR
- Lower operating pressure than PWR

### VVER (Water-Water Energetic Reactor)
- Soviet/Russian PWR variant
- Used throughout former Soviet Union and Eastern Europe
- Horizontal steam generators (vs vertical in Western PWRs)

### PHWR/CANDU
- Uses natural uranium (no enrichment needed)
- Heavy water moderator and coolant
- Online refueling capability
- Popular in Canada, India, Argentina

### EPR (Evolutionary Power Reactor)
- Gen III+ design by France/Germany
- Enhanced safety features
- Very large capacity (typically 1,600+ MW)
- Higher construction costs

## Important Notes
- ReactorTypeId links plants to specific technology families
- Some plants may have ReactorTypeId = NULL (verify with ReactorModel field)
- Reactor type influences capacity, efficiency, fuel requirements, and safety profile
- When analyzing by technology, consider both Type acronym and full Description
- Advanced reactors (ABWR, APR, EPR) typically have larger capacity
- Fast breeders are rare but strategically important for fuel cycles
- Some reactor types are obsolete (no longer being built)
- Regional preferences exist (VVER in Russia/Eastern Europe, PHWR in Canada/India)