import { budgetTone, money, monthLabel, signedMoney } from "./format";

test("money formats US dollars", () => {
  expect(money(1234.5)).toBe("$1,234.50");
  expect(signedMoney(2400)).toBe("+$2,400.00");
  expect(signedMoney(-4.5)).toBe("-$4.50");
});

test("month label", () => {
  expect(monthLabel("2026-09")).toBe("September 2026");
});

test("budget tone thresholds", () => {
  expect(budgetTone(50)).toBe("ok");
  expect(budgetTone(80)).toBe("warn");
  expect(budgetTone(100.1)).toBe("over");
});
