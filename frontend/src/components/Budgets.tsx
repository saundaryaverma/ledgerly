import { useState } from "react";
import { budgetTone, money } from "../format";
import type { BudgetStatus } from "../types";

interface Props {
  budgets: BudgetStatus[];
  categories: string[];
  onSave: (category: string, limit: number) => Promise<void>;
}

export function Budgets({ budgets, categories, onSave }: Props) {
  const spendable = categories.filter((c) => c !== "Income" && c !== "Transfers");
  const [category, setCategory] = useState(spendable[0] ?? "Dining");
  const [limit, setLimit] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const n = Number(limit);
    if (!Number.isFinite(n) || n <= 0) {
      setError("Enter an amount above $0.");
      return;
    }
    setError(null);
    await onSave(category, n);
    setLimit("");
  }

  return (
    <div>
      {budgets.length === 0 && <p className="muted">No budgets yet. Set one below.</p>}
      <ul className="budgets">
        {budgets.map((b) => {
          const tone = budgetTone(b.percent_used);
          return (
            <li key={b.category} className={`budget ${tone}`}>
              <div className="budget-head">
                <span>{b.category}</span>
                <span>
                  {money(b.spent)} of {money(b.limit)}
                </span>
              </div>
              <div className="budget-track" role="progressbar" aria-valuenow={b.percent_used} aria-valuemin={0} aria-valuemax={100} aria-label={`${b.category} budget used`}>
                <div className="budget-fill" style={{ width: `${Math.min(b.percent_used, 100)}%` }} />
              </div>
              <span className="sub">{b.remaining >= 0 ? `${money(b.remaining)} left` : `${money(-b.remaining)} over`}</span>
            </li>
          );
        })}
      </ul>
      <form className="budget-form" onSubmit={submit}>
        <select aria-label="Budget category" value={category} onChange={(e) => setCategory(e.target.value)}>
          {spendable.map((c) => (
            <option key={c}>{c}</option>
          ))}
        </select>
        <input aria-label="Monthly limit" inputMode="decimal" placeholder="Monthly limit" value={limit} onChange={(e) => setLimit(e.target.value)} />
        <button type="submit">Set budget</button>
      </form>
      {error && <p className="error">{error}</p>}
    </div>
  );
}
