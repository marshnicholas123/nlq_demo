import { ServiceConfig } from '@/types/text2sql';
import { SERVICES } from '@/api/text2sql';

interface ServiceToggleProps {
  selectedServices: string[];
  onToggle: (serviceId: string) => void;
  onToggleAll: (selected: boolean) => void;
}

export default function ServiceToggle({
  selectedServices,
  onToggle,
  onToggleAll,
}: ServiceToggleProps) {
  const allSelected = selectedServices.length === SERVICES.length;
  const someSelected = selectedServices.length > 0 && !allSelected;

  const getServiceIcon = (service: ServiceConfig) => {
    const icons: Record<string, string> = {
      simple: '📝',
      advanced: '🚀',
      chat: '💬',
      agentic: '🤖',
    };
    return icons[service.id] || '⚙️';
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-3">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-700">Select Services</h3>
        <button
          onClick={() => onToggleAll(!allSelected)}
          className="text-xs text-primary-600 hover:text-primary-700 font-medium"
        >
          {allSelected ? 'None' : 'All'}
        </button>
      </div>

      <div className="space-y-2">
        {SERVICES.map((service) => {
          const isSelected = selectedServices.includes(service.id);

          return (
            <label
              key={service.id}
              className={`
                flex items-start p-2.5 rounded-lg border-2 cursor-pointer transition-all
                ${
                  isSelected
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-gray-200 bg-white hover:border-gray-300'
                }
              `}
            >
              <input
                type="checkbox"
                checked={isSelected}
                onChange={() => onToggle(service.id)}
                className="mt-0.5 mr-2.5 h-4 w-4 text-primary-600 rounded focus:ring-primary-500 flex-shrink-0"
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5 mb-0.5">
                  <span className="text-base">{getServiceIcon(service)}</span>
                  <span className="font-medium text-sm text-gray-900">{service.name}</span>
                  {service.supportsFollowUp && (
                    <span className="text-xs px-1.5 py-0.5 bg-green-100 text-green-700 rounded-full flex-shrink-0">
                      Follow-up
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-600 leading-tight">{service.description}</p>
              </div>
            </label>
          );
        })}
      </div>

      {selectedServices.length === 0 && (
        <p className="mt-3 text-xs text-amber-600 bg-amber-50 px-2 py-1.5 rounded">
          ⚠️ Select at least one service
        </p>
      )}

      <p className="mt-3 text-xs text-gray-500">
        Selected: {selectedServices.length} / {SERVICES.length}
      </p>
    </div>
  );
}
