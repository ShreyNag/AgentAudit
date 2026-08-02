import React, { useMemo, useState } from "react";

import { SidebarContext } from "@/context/sidebar-context";

export function SidebarProvider({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const value = useMemo(
    () => ({ collapsed, toggle: () => setCollapsed((prev) => !prev) }),
    [collapsed],
  );
  return <SidebarContext.Provider value={value}>{children}</SidebarContext.Provider>;
}
