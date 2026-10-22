const usd = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

export function money(n: number): string {
  return usd.format(n);
}

export function signedMoney(n: number): string {
  return n > 0 ? `+${usd.format(n)}` : usd.format(n);
}

export function monthLabel(month: string): string {
  const [y, m] = month.split("-").map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString("en-US", { month: "long", year: "numeric" });
}

export function budgetTone(percentUsed: number): "ok" | "warn" | "over" {
  if (percentUsed > 100) return "over";
  if (percentUsed >= 80) return "warn";
  return "ok";
}

export const SOURCE_LABEL: Record<string, string> = {
  rule: "Auto",
  ai: "AI",
  user: "You",
  none: "Needs review",
};
