import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import { Budgets } from "./components/Budgets";
import { CategoryBars } from "./components/CategoryBars";
import { InsightsPanel } from "./components/InsightsPanel";
import { SummaryCards } from "./components/SummaryCards";
import { TransactionTable } from "./components/TransactionTable";
import { monthLabel } from "./format";
import type { Summary, Transaction } from "./types";

export default function App() {
  const [months, setMonths] = useState<string[]>([]);
  const [month, setMonth] = useState<string | null>(null);
  const [categories, setCategories] = useState<string[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [rows, setRows] = useState<Transaction[]>([]);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadMonths = useCallback(async () => {
    const ms = await api.months();
    setMonths(ms);
    setMonth((current) => (current && ms.includes(current) ? current : ms[0] ?? null));
  }, []);

  const loadMonth = useCallback(async (m: string) => {
    const [s, t] = await Promise.all([api.summary(m), api.transactions(m)]);
    setSummary(s);
    setRows(t);
  }, []);

  useEffect(() => {
    api.categories().then(setCategories).catch((e) => setError(e.message));
    loadMonths().catch((e) => setError(e.message));
  }, [loadMonths]);

  useEffect(() => {
    if (month) loadMonth(month).catch((e) => setError(e.message));
  }, [month, loadMonth]);

  async function onUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setError(null);
    try {
      const r = await api.importCsv(file);
      const review = r.categorized_by.none;
      setStatus(`Imported ${r.imported} transactions${r.skipped_duplicates ? `, skipped ${r.skipped_duplicates} duplicates` : ""}${review ? `. ${review} need a category from you.` : "."}`);
      await loadMonths();
      if (month) await loadMonth(month);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function onCategory(id: number, category: string) {
    try {
      const r = await api.setCategory(id, category);
      setStatus(`Got it. Updated ${r.updated} transaction${r.updated === 1 ? "" : "s"} from this merchant, and Ledgerly will remember next time.`);
      if (month) await loadMonth(month);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function onBudget(category: string, limit: number) {
    try {
      await api.setBudget(category, limit);
      if (month) await loadMonth(month);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div className="app">
      <header>
        <h1>Ledgerly</h1>
        <div className="header-actions">
          {months.length > 0 && (
            <select aria-label="Month" value={month ?? ""} onChange={(e) => setMonth(e.target.value)}>
              {months.map((m) => (
                <option key={m} value={m}>
                  {monthLabel(m)}
                </option>
              ))}
            </select>
          )}
          <label className="upload">
            Import bank CSV
            <input type="file" accept=".csv,text/csv" onChange={onUpload} />
          </label>
        </div>
      </header>

      {status && <p className="status" role="status">{status}</p>}
      {error && <p className="error" role="alert">{error}</p>}

      {!months.length && !error && (
        <section className="empty">
          <h2>Start with a bank export</h2>
          <p>Download a CSV from your bank and import it. Ledgerly sorts every transaction and explains where your money went.</p>
        </section>
      )}

      {summary && (
        <main>
          <SummaryCards s={summary} />
          <div className="grid">
            <section className="panel">
              <h2>Where it went</h2>
              <CategoryBars data={summary.by_category} />
            </section>
            <section className="panel">
              <h2>What stood out</h2>
              <InsightsPanel insights={summary.insights} />
            </section>
            <section className="panel">
              <h2>Budgets</h2>
              <Budgets budgets={summary.budgets} categories={categories} onSave={onBudget} />
            </section>
          </div>
          <section className="panel">
            <h2>
              Transactions <span className="muted small">{summary.uncategorized ? `${summary.uncategorized} ${summary.uncategorized === 1 ? "needs" : "need"} review` : "all categorized"}</span>
            </h2>
            <TransactionTable rows={rows} categories={categories} onCategory={onCategory} />
          </section>
        </main>
      )}
    </div>
  );
}
