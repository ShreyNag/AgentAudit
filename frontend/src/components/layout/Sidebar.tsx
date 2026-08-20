import {
  BarChart3,
  Beaker,
  ChevronLeft,
  ChevronRight,
  LayoutDashboard,
  ListChecks,
  Radio,
} from "lucide-react";
import { NavLink } from "react-router-dom";

import { useSidebar } from "@/context/useSidebar";
import { cn } from "@/lib/cn";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/benchmarks", label: "Benchmarks", icon: Beaker },
  { to: "/independent-agents", label: "Independent Agents", icon: Radio },
  { to: "/runs", label: "Runs", icon: ListChecks },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
];

/** Primary navigation (PROJECT_SPEC_4 SS10), state persists across page transitions. */
export function Sidebar() {
  const { collapsed, toggle } = useSidebar();

  return (
    <aside
      className={cn(
        "flex h-full flex-col border-r border-gray-200 bg-white transition-all dark:border-gray-800 dark:bg-gray-900",
        collapsed ? "w-16" : "w-56",
      )}
    >
      <div className="flex h-14 items-center justify-between px-4">
        {!collapsed && <span className="text-sm font-bold tracking-tight">AgentAudit</span>}
        <button
          onClick={toggle}
          className="rounded p-1 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>
      <nav className="flex-1 space-y-1 px-2" aria-label="Primary">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary-100 text-primary-700 dark:bg-primary-600/20 dark:text-primary-500"
                  : "text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800",
              )
            }
          >
            <item.icon className="h-4 w-4 shrink-0" aria-hidden="true" />
            {!collapsed && <span>{item.label}</span>}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
