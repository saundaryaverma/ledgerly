import type { ImportResult, Summary, Transaction } from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* keep statusText */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  categories: () => request<string[]>("/api/categories"),
  months: () => request<string[]>("/api/months"),
  summary: (month: string) => request<Summary>(`/api/summary?month=${month}`),
  transactions: (month: string) => request<Transaction[]>(`/api/transactions?month=${month}`),
  setCategory: (id: number, category: string) =>
    request<{ updated: number }>(`/api/transactions/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ category }),
    }),
  setBudget: (category: string, monthly_limit: number) =>
    request(`/api/budgets/${encodeURIComponent(category)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ monthly_limit }),
    }),
  importCsv: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<ImportResult>("/api/import", { method: "POST", body: form });
  },
};
