const resultsEl = document.getElementById("results");
const loadingEl = document.getElementById("loading");
const loadingText = document.getElementById("loading-text");
const summaryEl = document.getElementById("summary");
const flagsWrap = document.getElementById("flags-wrap");
const letterCard = document.getElementById("letter-card");
const letterText = document.getElementById("letter-text");
const submitBtn = document.getElementById("submit-btn");

let toastTimer;
function showToast(msg) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("show"), 2600);
}

const dropzones = [
  { id: "bill-drop", input: "bill", filenameEl: "bill-filename", clearBtn: "bill-clear" },
  { id: "eob-drop", input: "eob", filenameEl: "eob-filename", clearBtn: "eob-clear" },
];

function updateSubmitState() {
  submitBtn.disabled = !document.getElementById("bill").files.length;
}

function setDropzoneFile(dz, file) {
  const zone = document.getElementById(dz.id);
  const fileInput = document.getElementById(dz.input);
  const nameEl = document.getElementById(dz.filenameEl);

  if (file) {
    const dt = new DataTransfer();
    dt.items.add(file);
    fileInput.files = dt.files;
    zone.classList.add("has-file");
    nameEl.textContent = file.name;
  } else {
    fileInput.value = "";
    zone.classList.remove("has-file");
    nameEl.textContent = "";
  }
  updateSubmitState();
}

dropzones.forEach((dz) => {
  const zone = document.getElementById(dz.id);
  const fileInput = document.getElementById(dz.input);
  const clearEl = document.getElementById(dz.clearBtn);

  fileInput.addEventListener("change", () => setDropzoneFile(dz, fileInput.files[0] || null));

  clearEl.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDropzoneFile(dz, null);
  });

  ["dragenter", "dragover"].forEach((evt) =>
    zone.addEventListener(evt, (e) => { e.preventDefault(); zone.classList.add("drag-over"); })
  );
  ["dragleave", "drop"].forEach((evt) =>
    zone.addEventListener(evt, (e) => { e.preventDefault(); zone.classList.remove("drag-over"); })
  );
  zone.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files[0];
    if (file) setDropzoneFile(dz, file);
  });
});

document.getElementById("load-sample-btn").addEventListener("click", async (e) => {
  const btn = e.currentTarget;
  const original = btn.textContent;
  btn.textContent = "Loading…";
  btn.disabled = true;
  try {
    const [billBlob, eobBlob] = await Promise.all([
      fetch("/demo_assets/sample_itemized_bill.pdf").then((r) => r.blob()),
      fetch("/demo_assets/sample_eob.pdf").then((r) => r.blob()),
    ]);
    setDropzoneFile(dropzones[0], new File([billBlob], "sample_itemized_bill.pdf", { type: "application/pdf" }));
    setDropzoneFile(dropzones[1], new File([eobBlob], "sample_eob.pdf", { type: "application/pdf" }));
    showToast("Sample bill and EOB loaded");
  } catch (err) {
    showToast("Couldn't load the sample files -- check the server console");
  } finally {
    btn.textContent = original;
    btn.disabled = false;
  }
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

submitBtn.addEventListener("click", async () => {
  const billInput = document.getElementById("bill");
  const eobInput = document.getElementById("eob");
  if (!billInput.files.length) return;

  resultsEl.classList.add("hidden");
  loadingEl.classList.remove("hidden");
  loadingEl.scrollIntoView({ behavior: "smooth", block: "center" });
  submitBtn.disabled = true;
  cycleLoadingText();

  const formData = new FormData();
  formData.append("bill", billInput.files[0]);
  if (eobInput.files.length) formData.append("eob", eobInput.files[0]);

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
        <div class="flag-meta">CPT ${escapeHtml(f.code)} &middot; ${escapeHtml(f.date)} &middot; ${escapeHtml(f.confidence)} confidence</div>
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

document.getElementById("copy-btn")?.addEventListener("click", () => {
  navigator.clipboard.writeText(letterText.value);
  showToast("Letter copied to clipboard");
});

<<<<<<< HEAD
document.getElementById("fax-btn")?.addEventListener("click", async () => {
  const res = await fetch("/api/send-fax", { method: "POST" });
  const data = await res.json();
  showToast(data.message);
});

document.getElementById("reset-btn")?.addEventListener("click", () => {
  resultsEl.classList.add("hidden");
  dropzones.forEach((dz) => setDropzoneFile(dz, null));
  window.scrollTo({ top: 0, behavior: "smooth" });
=======
document.getElementById("fax-btn")?.addEventListener("click", async (e) => {
  const faxNumber = prompt(
    "Fax number for the hospital's billing department (e.g. +16505551234).\n" +
      "Never use a real hospital's number for testing."
  );
  if (!faxNumber) return;

  const btn = e.currentTarget;
  const original = btn.textContent;
  btn.disabled = true;
  btn.textContent = "Sending…";
  try {
    const res = await fetch("/api/send-fax", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ letter: letterText.value, fax_number: faxNumber }),
    });
    const data = await res.json();
    alert(data.message);
  } catch (err) {
    alert(`Fax request failed: ${err}`);
  } finally {
    btn.disabled = false;
    btn.textContent = original;
  }
>>>>>>> 64fe36f (update)
});
