/**
 * Cost Splitter — single-page web application.
 * Handles UI rendering, event handling, and state management.
 */

import { calculateBalances, calculateSettlement, roundCents } from "./calculator.js";
import {
  saveReport,
  loadReport,
  listReports,
  deleteReport,
  createReport,
  createSpending,
} from "./storage.js";

let currentReport = null;

// --- Navigation ---

function showView(id) {
  document.querySelectorAll(".view").forEach((v) => v.classList.add("hidden"));
  document.getElementById(id).classList.remove("hidden");
}

window.goHome = function () {
  currentReport = null;
  showView("view-home");
  renderHome();
};

// --- Home Screen ---

function renderHome() {
  const slugs = listReports();
  const list = document.getElementById("report-list");

  if (slugs.length === 0) {
    list.innerHTML = '<p class="muted">No reports yet. Create one to get started.</p>';
    return;
  }

  list.innerHTML = slugs
    .map((slug) => {
      const r = loadReport(slug);
      return `
      <div class="report-card">
        <div class="report-card-info" onclick="openReport('${slug}')">
          <div class="name">${esc(r.name)}</div>
          <div class="meta">${r.participants.length} participants, ${r.spendings.length} spendings</div>
        </div>
        <button class="btn btn-danger btn-sm" onclick="event.stopPropagation(); deleteReportFromHome('${slug}')">Delete</button>
      </div>`;
    })
    .join("");
}

window.openReport = function (slug) {
  currentReport = loadReport(slug);
  showView("view-report");
  renderReport();
};

window.deleteReportFromHome = function (slug) {
  const r = loadReport(slug);
  if (confirm(`Delete report '${r.name}' and all its spendings?`)) {
    deleteReport(slug);
    renderHome();
  }
};

// --- New Report ---

window.showNewReportForm = function () {
  document.getElementById("new-report-form").classList.remove("hidden");
  document.getElementById("new-report-name").focus();
};

window.hideNewReportForm = function () {
  document.getElementById("new-report-form").classList.add("hidden");
  document.getElementById("new-report-error").classList.add("hidden");
  document.getElementById("new-report-name").value = "";
  document.getElementById("new-report-participants").value = "";
};

window.createNewReport = function () {
  const name = document.getElementById("new-report-name").value.trim();
  const rawParticipants = document.getElementById("new-report-participants").value;
  const participants = rawParticipants
    .split(",")
    .map((p) => p.trim())
    .filter(Boolean);

  const errEl = document.getElementById("new-report-error");

  if (!name) {
    errEl.textContent = "Report name is required.";
    errEl.classList.remove("hidden");
    return;
  }
  if (participants.length === 0) {
    errEl.textContent = "At least one participant is required.";
    errEl.classList.remove("hidden");
    return;
  }
  if (new Set(participants).size !== participants.length) {
    errEl.textContent = "Participant names must be unique.";
    errEl.classList.remove("hidden");
    return;
  }

  const report = createReport(name, participants);
  saveReport(report);
  hideNewReportForm();
  openReport(report.slug);
};

// --- Report View ---

function renderReport() {
  document.getElementById("report-title").textContent = currentReport.name;
  document.getElementById("participants-list").textContent =
    "Participants: " + currentReport.participants.join(", ");

  renderSpendingsTable();
  renderSummaries();
}

function renderSpendingsTable() {
  const body = document.getElementById("spendings-body");
  const noSpend = document.getElementById("no-spendings");

  if (currentReport.spendings.length === 0) {
    body.innerHTML = "";
    noSpend.classList.remove("hidden");
    document.getElementById("summaries-section").classList.add("hidden");
    return;
  }

  noSpend.classList.add("hidden");

  body.innerHTML = currentReport.spendings
    .map((s, i) => {
      let eachOwes;
      if (s.customAmounts) {
        eachOwes = Object.entries(s.customAmounts)
          .map(([p, a]) => `${esc(p)}: ${a.toFixed(2)}`)
          .join(", ");
      } else {
        eachOwes = roundCents(s.amount / s.participants.length).toFixed(2);
      }
      return `<tr>
        <td>${i + 1}</td>
        <td>${esc(s.description)}</td>
        <td class="num">${s.amount.toFixed(2)}</td>
        <td>${esc(s.paidBy)}</td>
        <td>${s.participants.map(esc).join(", ")}</td>
        <td class="num">${eachOwes}</td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="editSpending(${i})">Edit</button>
          <button class="btn btn-danger btn-sm" onclick="removeSpending(${i})">Del</button>
        </td>
      </tr>`;
    })
    .join("");
}

function renderSummaries() {
  if (currentReport.spendings.length === 0) {
    document.getElementById("summaries-section").classList.add("hidden");
    return;
  }

  document.getElementById("summaries-section").classList.remove("hidden");

  const paid = {};
  const owed = {};
  for (const p of currentReport.participants) {
    paid[p] = 0;
    owed[p] = 0;
  }

  let total = 0;
  for (const s of currentReport.spendings) {
    paid[s.paidBy] += s.amount;
    total += s.amount;
    if (s.customAmounts) {
      for (const [person, amount] of Object.entries(s.customAmounts)) {
        owed[person] += amount;
      }
    } else {
      const share = roundCents(s.amount / s.participants.length);
      for (const person of s.participants) {
        owed[person] += share;
      }
    }
  }

  document.getElementById("spending-summary-body").innerHTML = currentReport.participants
    .map((p) => `<tr><td>${esc(p)}</td><td class="num">${roundCents(paid[p]).toFixed(2)}</td></tr>`)
    .join("");

  document.getElementById("spending-summary-foot").innerHTML =
    `<tr><td><strong>Total</strong></td><td class="num"><strong>${roundCents(total).toFixed(2)}</strong></td></tr>`;

  document.getElementById("individual-summary-body").innerHTML = currentReport.participants
    .map((p) => `<tr><td>${esc(p)}</td><td class="num">${roundCents(owed[p]).toFixed(2)}</td></tr>`)
    .join("");
}

// --- Add Participant ---

window.showAddParticipant = function () {
  document.getElementById("add-participant-form").classList.remove("hidden");
  document.getElementById("new-participant-name").focus();
};

window.hideAddParticipant = function () {
  document.getElementById("add-participant-form").classList.add("hidden");
  document.getElementById("new-participant-name").value = "";
};

window.addParticipant = function () {
  const name = document.getElementById("new-participant-name").value.trim();
  if (!name) return;
  if (currentReport.participants.includes(name)) {
    alert(`'${name}' is already a participant.`);
    return;
  }
  currentReport.participants.push(name);
  saveReport(currentReport);
  hideAddParticipant();
  renderReport();
};

// --- Spending Form ---

window.showSpendingForm = function (editIndex = -1) {
  const form = document.getElementById("spending-form");
  const title = document.getElementById("spending-form-title");
  document.getElementById("spending-edit-index").value = editIndex;

  const paidBySelect = document.getElementById("spending-paid-by");
  paidBySelect.innerHTML = currentReport.participants
    .map((p) => `<option value="${esc(p)}">${esc(p)}</option>`)
    .join("");

  const checksDiv = document.getElementById("spending-participants-checks");
  checksDiv.innerHTML = currentReport.participants
    .map(
      (p) =>
        `<div class="check-item"><label><input type="checkbox" value="${esc(p)}" checked> ${esc(p)}</label></div>`
    )
    .join("");

  document.querySelector('input[name="split-type"][value="equal"]').checked = true;
  document.getElementById("custom-amounts-section").classList.add("hidden");
  document.getElementById("split-error").classList.add("hidden");

  if (editIndex >= 0) {
    title.textContent = "Edit Spending";
    const s = currentReport.spendings[editIndex];
    document.getElementById("spending-description").value = s.description;
    document.getElementById("spending-amount").value = s.amount;
    paidBySelect.value = s.paidBy;

    checksDiv.querySelectorAll("input[type=checkbox]").forEach((cb) => {
      cb.checked = s.participants.includes(cb.value);
    });

    if (s.customAmounts) {
      document.querySelector('input[name="split-type"][value="custom"]').checked = true;
      onSplitTypeChange();
      for (const [person, amount] of Object.entries(s.customAmounts)) {
        const input = document.getElementById("custom-" + person);
        if (input) input.value = amount;
      }
    }
  } else {
    title.textContent = "Add Spending";
    document.getElementById("spending-description").value = "";
    document.getElementById("spending-amount").value = "";
  }

  form.classList.remove("hidden");
  document.getElementById("spending-description").focus();
};

window.editSpending = function (index) {
  showSpendingForm(index);
};

window.hideSpendingForm = function () {
  document.getElementById("spending-form").classList.add("hidden");
};

window.onSplitTypeChange = function () {
  const splitType = document.querySelector('input[name="split-type"]:checked').value;
  const section = document.getElementById("custom-amounts-section");
  const errEl = document.getElementById("split-error");
  errEl.classList.add("hidden");

  if (splitType === "equal") {
    section.classList.add("hidden");
    return;
  }

  section.classList.remove("hidden");
  const checked = getCheckedParticipants();
  const label = splitType === "percentage" ? "%" : "Amount";

  document.getElementById("custom-amounts-inputs").innerHTML = checked
    .map(
      (p) =>
        `<div class="custom-amount-row">
          <label for="custom-${esc(p)}">${esc(p)}</label>
          <input type="number" id="custom-${esc(p)}" step="0.01" placeholder="${label}">
        </div>`
    )
    .join("");
};

function getCheckedParticipants() {
  return Array.from(
    document.querySelectorAll("#spending-participants-checks input:checked")
  ).map((cb) => cb.value);
}

window.saveSpending = function () {
  const description = document.getElementById("spending-description").value.trim();
  const amount = parseFloat(document.getElementById("spending-amount").value);
  const paidBy = document.getElementById("spending-paid-by").value;
  const participants = getCheckedParticipants();
  const splitType = document.querySelector('input[name="split-type"]:checked').value;
  const editIndex = parseInt(document.getElementById("spending-edit-index").value);
  const errEl = document.getElementById("split-error");
  errEl.classList.add("hidden");

  if (!description) { errEl.textContent = "Description required."; errEl.classList.remove("hidden"); return; }
  if (!amount || amount <= 0) { errEl.textContent = "Amount must be positive."; errEl.classList.remove("hidden"); return; }
  if (participants.length === 0) { errEl.textContent = "Select at least one participant."; errEl.classList.remove("hidden"); return; }

  let customAmounts = null;

  if (splitType === "custom") {
    customAmounts = {};
    for (const p of participants) {
      const val = parseFloat(document.getElementById("custom-" + p)?.value);
      if (isNaN(val)) { errEl.textContent = `Enter an amount for ${p}.`; errEl.classList.remove("hidden"); return; }
      customAmounts[p] = roundCents(val);
    }
    const total = roundCents(Object.values(customAmounts).reduce((a, b) => a + b, 0));
    if (Math.abs(total - amount) > 0.01) {
      errEl.textContent = `Amounts must sum to ${amount.toFixed(2)}, got ${total.toFixed(2)}.`;
      errEl.classList.remove("hidden");
      return;
    }
  } else if (splitType === "percentage") {
    const pcts = {};
    for (const p of participants) {
      const val = parseFloat(document.getElementById("custom-" + p)?.value);
      if (isNaN(val)) { errEl.textContent = `Enter a percentage for ${p}.`; errEl.classList.remove("hidden"); return; }
      pcts[p] = val;
    }
    const totalPct = roundCents(Object.values(pcts).reduce((a, b) => a + b, 0));
    if (Math.abs(totalPct - 100) > 0.01) {
      errEl.textContent = `Percentages must sum to 100%, got ${totalPct}%.`;
      errEl.classList.remove("hidden");
      return;
    }
    customAmounts = {};
    for (const [p, pct] of Object.entries(pcts)) {
      customAmounts[p] = roundCents((amount * pct) / 100);
    }
  }

  const spending = createSpending(description, roundCents(amount), paidBy, participants, customAmounts);

  if (editIndex >= 0) {
    currentReport.spendings[editIndex] = spending;
  } else {
    currentReport.spendings.push(spending);
  }

  saveReport(currentReport);
  hideSpendingForm();
  renderReport();
};

window.removeSpending = function (index) {
  const s = currentReport.spendings[index];
  if (confirm(`Delete spending '${s.description}'?`)) {
    currentReport.spendings.splice(index, 1);
    saveReport(currentReport);
    renderReport();
  }
};

// --- Settlement ---

window.showSettlement = function () {
  const transfers = calculateSettlement(currentReport);
  const balances = calculateBalances(currentReport);
  const content = document.getElementById("settlement-content");

  if (transfers.length === 0) {
    content.innerHTML = '<div class="all-settled">Everyone is settled up!</div>';
  } else {
    let html = '<div class="settlement-panel">';
    for (const t of transfers) {
      html += `<div class="transfer-line">${esc(t.fromPerson)} &rarr; ${esc(t.toPerson)}: <strong>${t.amount.toFixed(2)}</strong></div>`;
    }

    const settled = Object.entries(balances)
      .filter(([, b]) => Math.abs(b) < 0.01)
      .map(([p]) => p);

    if (settled.length > 0) {
      html += "<hr>";
      for (const p of settled) {
        html += `<div class="settled-line">${esc(p)}: settled (no action needed)</div>`;
      }
    }
    html += "</div>";
    content.innerHTML = html;
  }

  showView("view-settlement");
};

window.hideSettlement = function () {
  showView("view-report");
};

// --- Delete Report ---

window.deleteCurrentReport = function () {
  if (confirm(`Delete report '${currentReport.name}' and all its spendings?`)) {
    deleteReport(currentReport.slug);
    goHome();
  }
};

// --- Helpers ---

function esc(str) {
  const d = document.createElement("div");
  d.textContent = str;
  return d.innerHTML;
}

// --- Init ---

renderHome();
