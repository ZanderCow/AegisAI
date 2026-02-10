import type { FlagType } from '@/types';
import { Badge } from './Badge';

interface FlagIndicatorProps {
  flagType: FlagType;
}

const flagConfig: Record<FlagType, { label: string; variant: 'default' | 'danger' | 'warning' }> = {
  none: { label: 'Clean', variant: 'default' },
  unauthorized_access: { label: 'Unauthorized Access', variant: 'danger' },
  suspicious_query: { label: 'Suspicious Query', variant: 'warning' },
  data_exfiltration: { label: 'Data Exfiltration', variant: 'danger' },
};

export function FlagIndicator({ flagType }: FlagIndicatorProps) {
  const config = flagConfig[flagType];
  return <Badge variant={config.variant}>{config.label}</Badge>;
}
