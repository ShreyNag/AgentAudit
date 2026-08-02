import { clsx, type ClassValue } from "clsx";

/** Tiny class-name joiner, used throughout the shared component library. */
export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}
