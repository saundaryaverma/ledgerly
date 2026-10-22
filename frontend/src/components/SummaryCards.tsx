import { money } from "../format";
import type { Summary } from "../types";

export function SummaryCards({ s }: { s: Summary }) {
  return (
    <section className="cards" aria-label="Monthly summary">
      <div className="card">
        <span className="label">Income</span>
        <span className="value">{money(s.income)}</span>
      </div>
      <div className="card">
        <span className="label">Spending</span>
        <span className="value">{money(s.spending)}</span>
      </div>
      <div className="card">
        <span className="label">{s.net >= 0 ? "Saved" : "Overspent"}</span>
        <span className={`value ${s.net >= 0 ? "pos" : "neg"}`}>{money(Math.abs(s.net))}</span>
        {s.savings_rate !== null && (
          <span className="sub">{s.savings_rate >= 0 ? `${s.savings_rate}% of income` : `${Math.abs(s.savings_rate)}% more than income`}</span>
        )}
      </div>
    </section>
  );
}
