import { Moon, Sun, SunMoon } from "lucide-react";

import { useTheme } from "@/context/useTheme";

const THEME_CYCLE = ["light", "dark", "system"] as const;
const THEME_ICON = { light: Sun, dark: Moon, system: SunMoon } as const;

/** Top application chrome: page title slot plus theme toggle (PROJECT_SPEC_4 SS9/SS25). */
export function Header({ title }: { title: string }) {
  const { theme, setTheme } = useTheme();
  const Icon = THEME_ICON[theme];

  const cycleTheme = () => {
    const nextIndex = (THEME_CYCLE.indexOf(theme) + 1) % THEME_CYCLE.length;
    setTheme(THEME_CYCLE[nextIndex]);
  };

  return (
    <header className="flex h-14 items-center justify-between border-b border-gray-200 bg-white px-6 dark:border-gray-800 dark:bg-gray-900">
      <h1 className="text-base font-semibold text-gray-900 dark:text-gray-100">{title}</h1>
      <button
        onClick={cycleTheme}
        className="flex items-center gap-2 rounded-md p-2 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
        aria-label={`Current theme: ${theme}. Click to change.`}
      >
        <Icon className="h-4 w-4" aria-hidden="true" />
      </button>
    </header>
  );
}
