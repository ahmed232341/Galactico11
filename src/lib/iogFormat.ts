export function normalizeIoG(value: unknown): number | null {
  if (value === null || value === undefined || value === "") return null;

  const numeric = typeof value === "number" ? value : Number(String(value).trim());
  if (!Number.isFinite(numeric)) return null;

  const scaled = Math.abs(numeric) > 10 ? numeric / 10 : numeric;
  const capped = Math.min(9.9, Math.max(0, scaled));

  return Math.round(capped * 10) / 10;
}

export function formatIoG(value: unknown): string {
  const normalized = normalizeIoG(value);
  return normalized === null ? "-" : normalized.toFixed(1);
}
