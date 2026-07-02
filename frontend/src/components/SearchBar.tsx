"use client";

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
}

/** Filters the board's cards by company or role (client-side, FR-CRM-010). */
export default function SearchBar({ value, onChange }: SearchBarProps) {
  return (
    <input
      type="search"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder="Search by company or role…"
      className="w-full max-w-xs rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-transparent"
    />
  );
}
