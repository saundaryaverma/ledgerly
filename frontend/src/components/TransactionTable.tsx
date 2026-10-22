import { SOURCE_LABEL, signedMoney } from "../format";
import type { Transaction } from "../types";

interface Props {
  rows: Transaction[];
  categories: string[];
  onCategory: (id: number, category: string) => void;
}

export function TransactionTable({ rows, categories, onCategory }: Props) {
  if (!rows.length) return <p className="muted">No transactions this month.</p>;
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Merchant</th>
            <th className="num">Amount</th>
            <th>Category</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((t) => (
            <tr key={t.id} className={t.category === "Uncategorized" ? "needs-review" : ""}>
              <td>{t.date.slice(5)}</td>
              <td>
                <div>{t.merchant}</div>
                <div className="muted small">{t.description}</div>
              </td>
              <td className={`num ${t.amount > 0 ? "pos" : ""}`}>{signedMoney(t.amount)}</td>
              <td>
                <select aria-label={`Category for ${t.merchant} on ${t.date}`} value={t.category} onChange={(e) => onCategory(t.id, e.target.value)}>
                  {categories.map((c) => (
                    <option key={c}>{c}</option>
                  ))}
                </select>
                <span className={`tag ${t.category_source}`}>{SOURCE_LABEL[t.category_source]}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
