import { useState } from 'react';

interface TableField {
  name: string;
  type: string;
  description?: string;
  nullable?: boolean;
  primaryKey?: boolean;
  foreignKey?: string;
}

interface TableSchema {
  name: string;
  alias: string;
  fields: TableField[];
  description?: string;
}

const SCHEMAS: TableSchema[] = [
  {
    name: 'nuclear_power_plants',
    alias: 'npp',
    description: 'Primary table containing nuclear power plant information',
    fields: [
      { name: 'Id', type: 'INTEGER', description: 'Primary key', primaryKey: true },
      { name: 'Name', type: 'TEXT', description: 'Plant/reactor name' },
      { name: 'CountryCode', type: 'TEXT', description: 'ISO 3166-1 alpha-2 code', foreignKey: 'countries.Id' },
      { name: 'StatusId', type: 'INTEGER', description: 'Plant status', foreignKey: 'nuclear_power_plant_status_type.Id' },
      { name: 'Capacity', type: 'REAL', description: 'Megawatts', nullable: true },
      { name: 'ReactorTypeId', type: 'INTEGER', description: 'Reactor technology', foreignKey: 'nuclear_reactor_type.Id', nullable: true },
      { name: 'ReactorModel', type: 'TEXT', description: 'Specific reactor variant', nullable: true },
      { name: 'OperationalFrom', type: 'TEXT', description: 'Commercial operation start date', nullable: true },
      { name: 'OperationalTo', type: 'TEXT', description: 'Permanent shutdown date (NULL if operational)', nullable: true },
      { name: 'ConstructionStartAt', type: 'TEXT', description: 'Construction start date', nullable: true },
      { name: 'Latitude', type: 'REAL', description: 'Geographic coordinate', nullable: true },
      { name: 'Longitude', type: 'REAL', description: 'Geographic coordinate', nullable: true },
      { name: 'Source', type: 'TEXT', description: 'Data source reference' },
    ],
  },
  {
    name: 'countries',
    alias: 'c',
    description: 'Country reference table',
    fields: [
      { name: 'Id', type: 'TEXT', description: 'ISO country code (US, CN, FR, etc.)', primaryKey: true },
      { name: 'Name', type: 'TEXT', description: 'Full country name' },
    ],
  },
  {
    name: 'nuclear_power_plant_status_type',
    alias: 'st',
    description: 'Plant status reference table',
    fields: [
      { name: 'Id', type: 'INTEGER', description: 'Status identifier', primaryKey: true },
      { name: 'Status', type: 'TEXT', description: 'Status name' },
    ],
  },
  {
    name: 'nuclear_reactor_type',
    alias: 'rt',
    description: 'Reactor type reference table',
    fields: [
      { name: 'Id', type: 'INTEGER', description: 'Type identifier', primaryKey: true },
      { name: 'Type', type: 'TEXT', description: 'Reactor type code (PWR, BWR, VVER, PHWR, etc.)' },
    ],
  },
];

const STATUS_VALUES = [
  { id: 1, name: 'Planned' },
  { id: 2, name: 'Under Construction' },
  { id: 3, name: 'Operational' },
  { id: 4, name: 'Suspended Operation' },
  { id: 5, name: 'Shutdown' },
  { id: 6, name: 'Unfinished' },
  { id: 7, name: 'Never Built' },
  { id: 8, name: 'Suspended Construction' },
  { id: 9, name: 'Cancelled Construction' },
];

const COMMON_REACTOR_TYPES = [
  { id: 22, type: 'PWR', description: 'Pressurized Water Reactor (~60% market share)' },
  { id: 5, type: 'BWR', description: 'Boiling Water Reactor (~20% market share)' },
  { id: 24, type: 'VVER', description: 'Russian PWR variant' },
  { id: 19, type: 'PHWR', description: 'Pressurized Heavy Water Reactor (CANDU)' },
  { type: 'ABWR', description: 'Advanced Boiling Water Reactor' },
  { type: 'APWR', description: 'Advanced Pressurized Water Reactor' },
  { type: 'APR', description: 'Advanced Power Reactor' },
  { type: 'EPR', description: 'Evolutionary Power Reactor (Generation III+)' },
  { type: 'AGR', description: 'Advanced Gas-cooled Reactor' },
  { type: 'GCR', description: 'Gas-Cooled Reactor' },
  { type: 'FBR', description: 'Fast Breeder Reactor' },
];

export default function SchemaViewer() {
  const [selectedTable, setSelectedTable] = useState<string>(SCHEMAS[0].name);

  const currentSchema = SCHEMAS.find((s) => s.name === selectedTable) || SCHEMAS[0];

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="border-b border-gray-200 p-4">
        <h2 className="text-xl font-bold text-gray-900">Database Schema</h2>
        <p className="text-sm text-gray-600 mt-1">
          Nuclear Power Database - Table structures and relationships
        </p>
      </div>

      {/* Table Selector */}
      <div className="border-b border-gray-200 bg-gray-50 p-2">
        <div className="flex flex-wrap gap-2">
          {SCHEMAS.map((schema) => (
            <button
              key={schema.name}
              onClick={() => setSelectedTable(schema.name)}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                selectedTable === schema.name
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
              }`}
            >
              {schema.name}
            </button>
          ))}
        </div>
      </div>

      {/* Schema Content */}
      <div className="p-6">
        {/* Table Info */}
        <div className="mb-6">
          <div className="flex items-baseline gap-3 mb-2">
            <h3 className="text-2xl font-bold text-gray-900">{currentSchema.name}</h3>
            <span className="text-sm text-gray-500 font-mono">alias: {currentSchema.alias}</span>
          </div>
          {currentSchema.description && (
            <p className="text-sm text-gray-600">{currentSchema.description}</p>
          )}
        </div>

        {/* Fields Table */}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Field Name
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Constraints
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Description
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {currentSchema.fields.map((field) => (
                <tr key={field.name} className="hover:bg-gray-50">
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className="font-mono text-sm font-medium text-gray-900">
                      {field.name}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className="font-mono text-sm text-blue-600">{field.type}</span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {field.primaryKey && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                          PK
                        </span>
                      )}
                      {field.foreignKey && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                          FK → {field.foreignKey}
                        </span>
                      )}
                      {field.nullable && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                          NULL
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {field.description}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Reference Data Sections */}
        {selectedTable === 'nuclear_power_plant_status_type' && (
          <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <h4 className="text-sm font-semibold text-blue-900 mb-3">Status Values</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {STATUS_VALUES.map((status) => (
                <div key={status.id} className="flex items-center gap-2 text-sm">
                  <span className="font-mono text-blue-700 font-medium">{status.id}</span>
                  <span className="text-gray-700">{status.name}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {selectedTable === 'nuclear_reactor_type' && (
          <div className="mt-6 p-4 bg-green-50 rounded-lg border border-green-200">
            <h4 className="text-sm font-semibold text-green-900 mb-3">Common Reactor Types</h4>
            <div className="space-y-2">
              {COMMON_REACTOR_TYPES.map((reactor, index) => (
                <div key={index} className="flex items-start gap-3 text-sm">
                  {reactor.id && (
                    <span className="font-mono text-green-700 font-medium min-w-[2rem]">
                      {reactor.id}
                    </span>
                  )}
                  <span className="font-mono text-gray-900 font-semibold min-w-[4rem]">
                    {reactor.type}
                  </span>
                  <span className="text-gray-600">{reactor.description}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {selectedTable === 'nuclear_power_plants' && (
          <div className="mt-6 space-y-4">
            <div className="p-4 bg-amber-50 rounded-lg border border-amber-200">
              <h4 className="text-sm font-semibold text-amber-900 mb-2">Important JOIN Patterns</h4>
              <div className="space-y-2 text-sm text-gray-700">
                <div>
                  <span className="font-mono text-amber-800 font-medium">JOIN countries c ON npp.CountryCode = c.Id</span>
                  <p className="text-xs text-gray-600 mt-1">Always join to get readable country names (not ISO codes)</p>
                </div>
                <div>
                  <span className="font-mono text-amber-800 font-medium">JOIN nuclear_power_plant_status_type st ON npp.StatusId = st.Id</span>
                  <p className="text-xs text-gray-600 mt-1">Use INNER JOIN - StatusId is never NULL</p>
                </div>
                <div>
                  <span className="font-mono text-amber-800 font-medium">LEFT JOIN nuclear_reactor_type rt ON npp.ReactorTypeId = rt.Id</span>
                  <p className="text-xs text-gray-600 mt-1">Use LEFT JOIN - ReactorTypeId can be NULL</p>
                </div>
              </div>
            </div>

            <div className="p-4 bg-red-50 rounded-lg border border-red-200">
              <h4 className="text-sm font-semibold text-red-900 mb-2">NULL Handling Requirements</h4>
              <p className="text-sm text-gray-700 mb-2">Always check for NULL before using these fields:</p>
              <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                <li><span className="font-mono text-red-800">Capacity</span> - Filter in SUM, AVG, MIN, MAX</li>
                <li><span className="font-mono text-red-800">OperationalFrom, OperationalTo, ConstructionStartAt</span> - Check before date calculations</li>
                <li><span className="font-mono text-red-800">Latitude, Longitude</span> - Validate for mapping queries</li>
                <li><span className="font-mono text-red-800">ReactorTypeId, ReactorModel</span> - May be NULL for some plants</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
