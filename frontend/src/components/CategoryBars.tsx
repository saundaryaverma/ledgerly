import { money } from "../format";
import type { CategoryTotal } from "../types";

export function CategoryBars({ data }: { data: CategoryTotal[] }) {
  if (!data.length) return <p className="muted">No spending this month.</p>;
  const max = data[0].amount;
  return (
    <ul className="bars" aria-label="Spending by category">
      {data.map((c) => (
        <li key={c.category}>
          <span className="bar-label">{c.category}</span>
          <span className="bar-track">
            <span className="bar-fill" style={{ width: `${(c.amount / max) * 100}%` }} />
          </span>
          <span className="bar-value">
            {money(c.amount)} <span className="muted">· {c.share}%</span>
          </span>
        </li>
      ))}
    </ul>
  );
}
