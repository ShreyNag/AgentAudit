import { createContext } from "react";

export interface SidebarContextValue {
  collapsed: boolean;
  toggle: () => void;
}

export const SidebarContext = createContext<SidebarContextValue | undefined>(undefined);
