export type FlagType = 'unauthorized_access' | 'suspicious_query' | 'data_exfiltration' | 'none';
export type AlarmFilterType = 'keyword' | 'provider';

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

export interface AlarmEvent {
  id: string;
  userId: string;
  userEmail: string;
  conversationId: string;
  messageContent: string;
  filterType: AlarmFilterType;
  provider: string;
  reason: string | null;
  createdAt: string;
}
