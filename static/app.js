const form = document.getElementById("analyze-form");
const resultsEl = document.getElementById("results");
const loadingEl = document.getElementById("loading");
const loadingText = document.getElementById("loading-text");
const summaryEl = document.getElementById("summary");
const flagsWrap = document.getElementById("flags-wrap");
const letterCard = document.getElementById("letter-card");
const letterText = document.getElementById("letter-text");
const submitBtn = document.getElementById("submit-btn");

const dropzones = [
  { id: "bill-drop", input: "bill", filenameEl: "bill-filename" },
  { id: "eob-drop", input: "eob", filenameEl: "eob-filename" },
];

function updateSubmitState() {
  const billInput = document.getElementById("bill");
  submitBtn.disabled = !billInput.files.length;
}

dropzones.forEach(({ id, input, filenameEl }) => {
  const zone = document.getElementById(id);
  const fileInput = document.getElementById(input);
  const nameEl = document.getElementById(filenameEl);

  const showFile = (file) => {
    if (file) {
      zone.classList.add("has-file");
      nameEl.textContent = file.name;
    } else {
      zone.classList.remove("has-file");
      nameEl.textContent = "";
    }
  };

  fileInput.addEventListener("change", () => {
    showFile(fileInput.files[0]);
    updateSubmitState();
  });

  ["dragenter", "dragover"].forEach((evt) =>
    zone.addEventListener(evt, (e) => {
      e.preventDefault();
      zone.classList.add("drag-over");
    })
  );
  ["dragleave", "drop"].forEach((evt) =>
    zone.addEventListener(evt, (e) => {
      e.preventDefault();
      zone.classList.remove("drag-over");
    })
  );
  zone.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files[0];
    if (file) {
      fileInput.files = e.dataTransfer.files;
      showFile(file);
      updateSubmitState();
    }
  });
});

const LOADING_STEPS = [
  "Extracting line items…",
  "Checking for duplicate charges…",
  "Cross-referencing your EOB…",
  "Drafting your dispute letter…",
];

let loadingInterval;

function cycleLoadingText() {
  let i = 0;
  loadingText.textContent = LOADING_STEPS[0];
  loadingInterval = setInterval(() => {
    i = (i + 1) % LOADING_STEPS.length;
    loadingText.textContent = LOADING_STEPS[i];
  }, 1400);
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  resultsEl.classList.add("hidden");
  loadingEl.classList.remove("hidden");
  submitBtn.disabled = true;
  cycleLoadingText();

  const formData = new FormData(form);
  try {
    const res = await fetch("/api/analyze", { method: "POST", body: formData });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Analysis failed");
    renderResults(data);
  } catch (err) {
    summaryEl.innerHTML = `<div class="error-banner">${escapeHtml(err.message)}</div>`;
    flagsWrap.innerHTML = "";
    letterCard.classList.add("hidden");
    resultsEl.classList.remove("hidden");
  } finally {
    clearInterval(loadingInterval);
    loadingEl.classList.add("hidden");
    updateSubmitState();
  }
});

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function money(n) {
  return `$${n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function renderResults(data) {
  const total = data.bill_items.reduce((s, i) => s + i.amount, 0);

  summaryEl.innerHTML = `
    <h2>Billing Health Report</h2>
    <div class="summary-stats">
      <div class="stat-box">
        <div class="stat-label">Total Billed</div>
        <div class="stat-value">${money(total)}</div>
      </div>
      <div class="stat-box flagged">
        <div class="stat-label">Flagged for Review</div>
        <div class="stat-value">${money(data.total_flagged_amount)}</div>
      </div>
    </div>
    <p class="summary-note">${data.flags.length} issue(s) found across ${data.bill_items.length} line item(s).</p>
  `;

  flagsWrap.innerHTML = "";
  if (data.flags.length === 0) {
    flagsWrap.innerHTML = `<div class="card clean-state">No issues found in this bill.</div>`;
  } else {
    const heading = document.createElement("div");
    heading.className = "flags-heading";
    heading.textContent = "Flagged Line Items";
    flagsWrap.appendChild(heading);

    data.flags.forEach((f) => {
      const div = document.createElement("div");
      div.className = "flag-card";
      const amount = f.overcharge_amount ? money(f.overcharge_amount) : "";
      div.innerHTML = `
        <div class="flag-top">
          <span class="flag-type">${escapeHtml(f.type.replace(/_/g, " "))}</span>
          ${amount ? `<span class="flag-amount">${amount}</span>` : ""}
        </div>
        <p class="flag-explanation">${escapeHtml(f.explanation)}</p>
        <div class="flag-meta">CPT ${escapeHtml(f.code)} · ${escapeHtml(f.date)} · ${escapeHtml(f.confidence)} confidence</div>
      `;
      flagsWrap.appendChild(div);
    });
  }

  if (data.dispute_letter) {
    letterText.value = data.dispute_letter;
    letterCard.classList.remove("hidden");
  } else {
    letterCard.classList.add("hidden");
  }

  resultsEl.classList.remove("hidden");
}

document.getElementById("copy-btn")?.addEventListener("click", (e) => {
  navigator.clipboard.writeText(letterText.value);
  const btn = e.currentTarget;
  const original = btn.textContent;
  btn.textContent = "Copied!";
  setTimeout(() => (btn.textContent = original), 1200);
});

document.getElementById("fax-btn")?.addEventListener("click", async () => {
  const res = await fetch("/api/send-fax", { method: "POST" });
  const data = await res.json();
  alert(data.message);
});
