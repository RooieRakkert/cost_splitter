/**
 * Balance calculation and debt simplification for cost splitting.
 * Direct port of calculator.py.
 */

/**
 * Round a number to 2 decimal places.
 * @param {number} n
 * @returns {number}
 */
function roundCents(n) {
  return Math.round(n * 100) / 100;
}

/**
 * Calculate the net balance for each participant across all spendings.
 * Positive = is owed money, negative = owes money.
 * @param {Object} report
 * @param {string[]} report.participants
 * @param {Object[]} report.spendings
 * @returns {Object.<string, number>}
 */
function calculateBalances(report) {
  const balances = {};
  for (const p of report.participants) {
    balances[p] = 0;
  }

  for (const spending of report.spendings) {
    balances[spending.paidBy] += spending.amount;

    if (spending.customAmounts) {
      for (const [person, amount] of Object.entries(spending.customAmounts)) {
        balances[person] -= amount;
      }
    } else {
      const share = roundCents(spending.amount / spending.participants.length);
      for (let i = 0; i < spending.participants.length; i++) {
        const person = spending.participants[i];
        if (i === spending.participants.length - 1) {
          const remainder = roundCents(
            spending.amount - share * (spending.participants.length - 1)
          );
          balances[person] -= remainder;
        } else {
          balances[person] -= share;
        }
      }
    }
  }

  for (const p of Object.keys(balances)) {
    balances[p] = roundCents(balances[p]);
  }

  return balances;
}

/**
 * Calculate simplified settlement transfers using greedy debt matching.
 * @param {Object} report
 * @returns {{fromPerson: string, toPerson: string, amount: number}[]}
 */
function calculateSettlement(report) {
  const balances = calculateBalances(report);

  const debtors = [];
  const creditors = [];

  for (const [person, balance] of Object.entries(balances)) {
    if (balance < -0.001) {
      debtors.push({ person, amount: roundCents(-balance) });
    } else if (balance > 0.001) {
      creditors.push({ person, amount: roundCents(balance) });
    }
  }

  debtors.sort((a, b) => b.amount - a.amount);
  creditors.sort((a, b) => b.amount - a.amount);

  const transfers = [];
  let di = 0;
  let ci = 0;

  while (di < debtors.length && ci < creditors.length) {
    const debtor = debtors[di];
    const creditor = creditors[ci];
    const amount = roundCents(Math.min(debtor.amount, creditor.amount));

    if (amount > 0) {
      transfers.push({
        fromPerson: debtor.person,
        toPerson: creditor.person,
        amount,
      });
    }

    debtor.amount = roundCents(debtor.amount - amount);
    creditor.amount = roundCents(creditor.amount - amount);

    if (debtor.amount < 0.001) di++;
    if (creditor.amount < 0.001) ci++;
  }

  return transfers;
}

export { calculateBalances, calculateSettlement, roundCents };
