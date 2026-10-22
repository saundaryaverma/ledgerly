import { fireEvent, render, screen } from "@testing-library/react";
import { Budgets } from "./Budgets";
import { InsightsPanel } from "./InsightsPanel";
import { TransactionTable } from "./TransactionTable";

const cats = ["Income", "Dining", "Shopping", "Transfers", "Uncategorized"];

test("transaction table flags rows that need review and reports category changes", () => {
  const onCategory = vi.fn();
  render(
    <TransactionTable
      categories={cats}
      onCategory={onCategory}
      rows={[{ id: 7, date: "2026-09-03", description: "KINOKUNIYA BOOKSTORE NY", merchant: "Kinokuniya Bookstore", amount: -22, category: "Uncategorized", category_source: "none" }]}
    />,
  );
  expect(screen.getByText("Needs review")).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText(/Category for Kinokuniya/), { target: { value: "Shopping" } });
  expect(onCategory).toHaveBeenCalledWith(7, "Shopping");
});

test("budget shows over-budget state and rejects bad input", async () => {
  const onSave = vi.fn().mockResolvedValue(undefined);
  render(<Budgets categories={cats} onSave={onSave} budgets={[{ category: "Dining", limit: 100, spent: 130, remaining: -30, percent_used: 130 }]} />);
  expect(screen.getByText("$30.00 over")).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("Monthly limit"), { target: { value: "-5" } });
  fireEvent.click(screen.getByText("Set budget"));
  expect(await screen.findByText("Enter an amount above $0.")).toBeInTheDocument();
  expect(onSave).not.toHaveBeenCalled();
  // Income and Transfers aren't budgetable
  expect(screen.queryByRole("option", { name: "Income" })).toBeNull();
});

test("insights always show the verification note", () => {
  render(<InsightsPanel insights={{ source: "template", verified: true, items: ["You saved $300.00, 12.5% of your income."] }} />);
  expect(screen.getByText(/Every number checked/)).toBeInTheDocument();
});
