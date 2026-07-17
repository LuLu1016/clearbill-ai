const form = document.getElementById("analyze-form");
const resultsEl = document.getElementById("results");
const loadingEl = document.getElementById("loading");
const summaryEl = document.getElementById("summary");
const flagsEl = document.getElementById("flags");
const letterCard = document.getElementById("letter-card");
const letterText = document.getElementById("letter-text");
const submitBtn = document.getElementById("submit-btn");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  resultsEl.classList.add("hidden");
  loadingEl.classList.remove("hidden");
  submitBtn.disabled = true;

  const formData = new FormData(form);
  try {
    const res = await fetch("/api/analyze", { method: "POST", body: formData });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Analysis failed");
    renderResults(data);
  } catch (err) {
    summaryEl.innerHTML = `<p style="color:#b91c1c">${err.message}</p>`;
    resultsEl.classList.remove("hidden");
  } finally {
    loadingEl.classList.add("hidden");
    submitBtn.disabled = false;
  }
});

function renderResults(data) {
  const total = data.bill_items.reduce((s, i) => s + i.amount, 0);
  summaryEl.innerHTML = `
    <h2>Billing Health Report</h2>
    <p>Total billed: <strong>$${total.toLocaleString(undefined, { minimumFractionDigits: 2 })}</strong></p>
    <p>Flagged for review: <span class="big-number">$${data.total_flagged_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span></p>
    <p>${data.flags.length} issue(s) found across ${data.bill_items.length} line item(s).</p>
  `;

  flagsEl.innerHTML = "";
  data.flags.forEach((f) => {
    const div = document.createElement("div");
    div.className = "flag-card";
    div.innerHTML = `
      <div class="flag-type">${f.type.replace(/_/g, " ")} · ${f.confidence} confidence</div>
      <p>${f.explanation}</p>
      <p><strong>CPT ${f.code}</strong> on ${f.date}${f.overcharge_amount ? ` — $${f.overcharge_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })} flagged` : ""}</p>
    `;
    flagsEl.appendChild(div);
  });

  if (data.dispute_letter) {
    letterText.value = data.dispute_letter;
    letterCard.classList.remove("hidden");
  } else {
    letterCard.classList.add("hidden");
  }

  resultsEl.classList.remove("hidden");
}

document.getElementById("copy-btn")?.addEventListener("click", () => {
  navigator.clipboard.writeText(letterText.value);
});

document.getElementById("fax-btn")?.addEventListener("click", async () => {
  const res = await fetch("/api/send-fax", { method: "POST" });
  const data = await res.json();
  alert(data.message);
});
