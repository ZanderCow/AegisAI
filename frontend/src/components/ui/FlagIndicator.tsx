/**
 * Defines the possible types of security flags that can be indicated.
 */
export type FlagType = 'none' | 'unauthorized_access' | 'suspicious_query' | 'data_exfiltration';
import { Badge } from './Badge';

/**
 * Props for the FlagIndicator component.
 */
interface FlagIndicatorProps {
  /** The type of flag to display, which determines its visual styling and label. */
  flagType: FlagType;
}

const flagConfig: Record<FlagType, { label: string; variant: 'default' | 'danger' | 'warning' }> = {
  none: { label: 'Clean', variant: 'default' },
  unauthorized_access: { label: 'Unauthorized Access', variant: 'danger' },
  suspicious_query: { label: 'Suspicious Query', variant: 'warning' },
  data_exfiltration: { label: 'Data Exfiltration', variant: 'danger' },
};

/**
 * Renders a visual badge indicating a specific security flag or status.
 *
 * @param props - The FlagIndicator properties.
 * @returns The rendered FlagIndicator component.
 */
export function FlagIndicator({ flagType }: FlagIndicatorProps) {
  const config = flagConfig[flagType];
  return <Badge variant={config.variant}>{config.label}</Badge>;
}
