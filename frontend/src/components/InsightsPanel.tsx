import type { Insights } from "../types";

export function InsightsPanel({ insights }: { insights: Insights }) {
  return (
    <div>
      <ul className="insights">
        {insights.items.map((text) => (
          <li key={text}>{text}</li>
        ))}
      </ul>
      <p className="verified" title="Every dollar amount and percentage is checked against your transactions before it's shown.">
        ✓ Every number checked against your transactions
        {insights.source === "ai" ? " · written with AI" : ""}
      </p>
      {insights.note && <p className="muted small">{insights.note}</p>}
    </div>
  );
}
