export type FlagType = 'unauthorized_access' | 'suspicious_query' | 'data_exfiltration' | 'none';

export interface SecurityLog {
  id: string;
  userId: string;
  userName: string;
  action: string;
  resource: string;
  timestamp: string;
  ipAddress: string;
  flagType: FlagType;
  details: string;
}
