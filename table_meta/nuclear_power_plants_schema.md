# nuclear_power_plants

**Table**: nuclear_power_plants

**Schema**:

| Column Name | Data Type | Nullable | Description |
|------------|-----------|----------|-------------|
| Name | VARCHAR(255) | YES | Name/title of the nuclear power plant |
| Latitude | INT | YES | Geographic latitude coordinate |
| Longitude | INT | YES | Geographic longitude coordinate |
| CountryCode | VARCHAR(255) | YES | ISO 3166-1 alpha-2 country code |
| StatusId | INT | YES | Current lifecycle status (FK to nuclear_power_plant_status_type) |
| ReactorTypeId | INT | YES | Technology classification (FK to nuclear_reactor_type) |
| ReactorModel | VARCHAR(255) | YES | Specific reactor model/variant |
| ConstructionStartAt | DATETIME | YES | Date when construction began |
| OperationalFrom | DATETIME | YES | Date when plant began commercial operation |
| OperationalTo | DATETIME | YES | Date when plant ceased operation (NULL if still operating) |
| Capacity | INT | YES | Net electrical capacity in megawatts (MW) |
| Source | VARCHAR(255) | YES | Data source reference |
| LastUpdatedAt | DATETIME | YES | Timestamp of last data update |
| Id | INT | YES | Unique identifier for nuclear power plants |
