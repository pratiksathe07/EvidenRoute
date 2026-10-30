import { LucideIcon } from 'lucide-react';

export interface NavItem {
  id: string;
  label: string;
  path: string;
  icon: LucideIcon;
  badge?: string;
}

export type SystemStatus = 'operational' | 'degraded' | 'offline';
