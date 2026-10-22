export type Source = "rule" | "ai" | "user" | "none";

export interface Transaction {
  id: number;
  date: string;
  description: string;
  merchant: string;
  amount: number;
  category: string;
  category_source: Source;
}

export interface CategoryTotal {
  category: string;
  amount: number;
  count: number;
  share: number;
}

export interface BudgetStatus {
  category: string;
  limit: number;
  spent: number;
  remaining: number;
  percent_used: number;
}

export interface Insights {
  source: "ai" | "template";
  verified: boolean;
  items: string[];
  note?: string;
}

export interface Summary {
  month: string;
  income: number;
  spending: number;
  net: number;
  savings_rate: number | null;
  by_category: CategoryTotal[];
  top_merchants: { merchant: string; amount: number }[];
  transaction_count: number;
  uncategorized: number;
  budgets: BudgetStatus[];
  insights: Insights;
}

export interface ImportResult {
  imported: number;
  skipped_duplicates: number;
  categorized_by: Record<Source, number>;
}
