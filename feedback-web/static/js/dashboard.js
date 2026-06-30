// ── Dashboard JS ─────────────────────────────────────────────────

// ── Navigation ────────────────────────────────────────────────────
function showView(viewId) {
  document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));

  const view = document.getElementById("view-" + viewId);
  if (view) view.classList.add("active");

  const navItem = document.querySelector(`[data-view="${viewId}"]`);
  if (navItem) navItem.classList.add("active");

  const titles = {
    courses: "Courses", "my-feedback": "My Submissions",
    overview: "Overview", "feedback-list": "Feedback",
    analytics: "Analytics", "all-feedback": "All Feedback"
  };
  document.getElementById("topbarTitle").textContent = titles[viewId] || "Dashboard";

  closeSidebar();
}

function toggleSidebar() {
  document.getElementById("sidebar").classList.toggle("open");
}
function closeSidebar() {
  document.getElementById("sidebar").classList.remove("open");
}

// ── Logout ────────────────────────────────────────────────────────
async function logout() {
  await fetch("/api/logout", { method: "POST" });
  window.location.href = "/";
}

// ── Fetch helper ──────────────────────────────────────────────────
async function api(url) {
  const res = await fetch(url);
  if (!res.ok) { window.location.href = "/"; throw new Error("Auth"); }
  return res.json();
}

// ════════════════════════════════════════════════════════════════
// STUDENT
// ════════════════════════════════════════════════════════════════
const EMOJIS = { "NLP": "🤖", "Smart Farming": "🌱", "Data Structures": "🧩" };

let selectedCourse = null;
let currentRating  = 3;

async function loadCourses() {
  if (ROLE !== "student") return;
  const courses = await api("/api/courses");
  const grid = document.getElementById("coursesGrid");
  grid.innerHTML = "";

  courses.forEach(c => {
    const emoji = EMOJIS[c.course] || "📚";
    const card = document.createElement("div");
    card.className = "course-card";
    card.innerHTML = `
      <span class="course-emoji">${emoji}</span>
      <div class="course-name">${c.course}</div>
      <div class="course-faculty">👨‍🏫 ${c.faculty}</div>
      <button class="course-btn" onclick="openFeedbackModal('${c.faculty}','${c.course}')">
        Give Feedback →
      </button>
    `;
    grid.appendChild(card);
  });
}

function openFeedbackModal(faculty, course) {
  selectedCourse = { faculty, course };
  currentRating  = 3;

  document.getElementById("modalTitle").textContent = course;
  document.getElementById("modalSub").textContent   = `Feedback for ${faculty}`;
  document.getElementById("fbText").value           = "";
  document.getElementById("fbError").classList.add("hidden");

  updateStars(3);
  document.getElementById("feedbackModal").classList.remove("hidden");
}

function closeModal() {
  document.getElementById("feedbackModal").classList.add("hidden");
}

// Stars
document.addEventListener("DOMContentLoaded", () => {
  if (ROLE !== "student") return;

  const stars = document.querySelectorAll(".star");
  stars.forEach(star => {
    star.addEventListener("click", () => {
      currentRating = parseInt(star.dataset.val);
      updateStars(currentRating);
    });
    star.addEventListener("mouseenter", () => highlightStars(parseInt(star.dataset.val)));
    star.addEventListener("mouseleave", () => updateStars(currentRating));
  });
});

function updateStars(val) {
  document.getElementById("ratingVal").textContent = val;
  document.querySelectorAll(".star").forEach(s => {
    s.classList.toggle("active", parseInt(s.dataset.val) <= val);
    s.classList.remove("hovered");
  });
}
function highlightStars(val) {
  document.querySelectorAll(".star").forEach(s => {
    s.classList.toggle("hovered", parseInt(s.dataset.val) <= val);
  });
}

async function submitFeedback() {
  const text  = document.getElementById("fbText").value.trim();
  const errEl = document.getElementById("fbError");
  errEl.classList.add("hidden");

  if (!text) {
    errEl.textContent = "Please write your feedback before submitting.";
    errEl.classList.remove("hidden");
    return;
  }

  const res = await fetch("/api/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ faculty: selectedCourse.faculty, course: selectedCourse.course, feedback: text, rating: currentRating })
  });
  const data = await res.json();

  if (!data.success) {
    errEl.textContent = data.message || "Submission failed.";
    errEl.classList.remove("hidden");
    return;
  }

  closeModal();
  showSuccess(data.sentiment);
}

function showSuccess(sentiment) {
  const icons = { "Good 😊": "🎉", "Bad 😠": "😞", "Neutral 😐": "😐" };
  const msgs  = {
    "Good 😊": "Your positive feedback has been recorded. Thank you!",
    "Bad 😠":  "Your feedback has been recorded. We'll work on improving.",
    "Neutral 😐": "Your feedback has been recorded. Thank you!"
  };

  document.getElementById("successIcon").textContent = icons[sentiment] || "✅";
  document.getElementById("successTitle").textContent = "Feedback Submitted!";
  document.getElementById("successMsg").textContent   = `Sentiment detected: ${sentiment}. ${msgs[sentiment] || ""}`;
  document.getElementById("successOverlay").classList.remove("hidden");
}

function closeSuccess() {
  document.getElementById("successOverlay").classList.add("hidden");
}

// ════════════════════════════════════════════════════════════════
// FACULTY
// ════════════════════════════════════════════════════════════════
async function loadTeacherData() {
  if (ROLE !== "faculty") return;
  const data = await api("/api/teacher/feedback");

  // Metrics
  const avg = data.length ? (data.reduce((s,r) => s + r.rating, 0) / data.length).toFixed(2) : 0;
  const pos = data.filter(r => r.sentiment === "Positive").length;
  document.getElementById("teacherMetrics").innerHTML = `
    <div class="metric-card"><div class="metric-icon">📝</div><div class="metric-val">${data.length}</div><div class="metric-lbl">Total Feedback</div></div>
    <div class="metric-card"><div class="metric-icon">⭐</div><div class="metric-val">${avg}</div><div class="metric-lbl">Avg Rating</div></div>
    <div class="metric-card"><div class="metric-icon">😊</div><div class="metric-val">${pos}</div><div class="metric-lbl">Positive</div></div>
  `;

  // Charts
  const ratings   = [1,2,3,4,5].map(v => data.filter(r => r.rating === v).length);
  const sentCount = { Positive: 0, Negative: 0, Neutral: 0 };
  data.forEach(r => sentCount[r.sentiment] = (sentCount[r.sentiment]||0) + 1);

  renderBar("ratingChart", ["1★","2★","3★","4★","5★"], ratings, "#3b6dd4");
  renderDoughnut("sentimentChart",
    Object.keys(sentCount), Object.values(sentCount),
    ["#22c55e","#ef4444","#f59e0b"]
  );

  // Feedback list
  const list = document.getElementById("teacherFeedbackList");
  list.innerHTML = data.length ? "" : emptyState("No feedback received yet.");
  data.forEach(r => list.appendChild(buildFbCard(r)));
}

// ════════════════════════════════════════════════════════════════
// ADMIN
// ════════════════════════════════════════════════════════════════
let allFeedback = [];

async function loadAdminData() {
  if (ROLE !== "admin") return;
  const [stats, feedback] = await Promise.all([api("/api/admin/stats"), api("/api/admin/feedback")]);

  allFeedback = feedback;

  // Metrics
  document.getElementById("adminMetrics").innerHTML = `
    <div class="metric-card"><div class="metric-icon">📋</div><div class="metric-val">${stats.total}</div><div class="metric-lbl">Total Feedback</div></div>
    <div class="metric-card"><div class="metric-icon">⭐</div><div class="metric-val">${stats.avg_rating}</div><div class="metric-lbl">Avg Rating</div></div>
    <div class="metric-card"><div class="metric-icon">👨‍🏫</div><div class="metric-val">${stats.faculty.length}</div><div class="metric-lbl">Faculty</div></div>
  `;

  // Sentiment chart
  const sLabels = stats.sentiment.map(s => s.sentiment);
  const sCounts = stats.sentiment.map(s => s.c);
  const sColors = sLabels.map(l => ({ Positive:"#22c55e", Negative:"#ef4444", Neutral:"#f59e0b" }[l] || "#93b4f5"));
  renderDoughnut("sentimentChart", sLabels, sCounts, sColors);

  // Ratings chart
  const rLabels = stats.ratings.map(r => r.rating + "★");
  const rCounts = stats.ratings.map(r => r.c);
  renderBar("ratingChart", rLabels, rCounts, "#3b6dd4");

  // Faculty chart
  const fLabels = stats.faculty.map(f => f.faculty);
  const fVals   = stats.faculty.map(f => f.avg);
  renderBar("facultyChart", fLabels, fVals, "#f0a500", 5);

  // Table
  renderTable(feedback);
}

function renderTable(data) {
  const tbody = document.getElementById("feedbackTableBody");
  tbody.innerHTML = "";
  if (!data.length) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:40px;color:#94a3b8">No feedback found</td></tr>`;
    return;
  }
  data.forEach(r => {
    const tr = document.createElement("tr");
    const chipClass = { Positive:"chip-positive", Negative:"chip-negative", Neutral:"chip-neutral" }[r.sentiment] || "";
    const date = r.created_at ? new Date(r.created_at).toLocaleDateString() : "—";
    tr.innerHTML = `
      <td>${r.student}</td><td>${r.faculty}</td><td>${r.course}</td>
      <td style="max-width:200px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="${r.feedback}">${r.feedback}</td>
      <td><span class="chip ${chipClass}">${r.sentiment}</span></td>
      <td>${"★".repeat(r.rating)}</td>
      <td>${date}</td>
    `;
    tbody.appendChild(tr);
  });
}

function filterTable() {
  const q = document.getElementById("searchInput").value.toLowerCase();
  const filtered = allFeedback.filter(r =>
    r.feedback.toLowerCase().includes(q) ||
    r.student.toLowerCase().includes(q) ||
    r.faculty.toLowerCase().includes(q) ||
    r.course.toLowerCase().includes(q)
  );
  renderTable(filtered);
}

function downloadCSV() {
  const headers = ["ID","Student","Faculty","Course","Feedback","Sentiment","Rating","Date"];
  const rows = allFeedback.map(r =>
    [r.id, r.student, r.faculty, r.course, `"${r.feedback.replace(/"/g,'""')}"`, r.sentiment, r.rating, r.created_at || ""].join(",")
  );
  const csv  = [headers.join(","), ...rows].join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const a    = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "feedback_data.csv";
  a.click();
}

// ════════════════════════════════════════════════════════════════
// Chart helpers
// ════════════════════════════════════════════════════════════════
function renderBar(id, labels, data, color, max) {
  const ctx = document.getElementById(id);
  if (!ctx) return;
  if (ctx._chart) ctx._chart.destroy();
  ctx._chart = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{ data, backgroundColor: color + "cc", borderColor: color, borderWidth: 2, borderRadius: 6 }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, max, grid: { color: "#f1f5f9" }, ticks: { color: "#94a3b8" } },
        x: { grid: { display: false }, ticks: { color: "#475569" } }
      }
    }
  });
}

function renderDoughnut(id, labels, data, colors) {
  const ctx = document.getElementById(id);
  if (!ctx) return;
  if (ctx._chart) ctx._chart.destroy();
  ctx._chart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{ data, backgroundColor: colors, borderWidth: 3, borderColor: "#fff" }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: "bottom", labels: { color: "#475569", font: { size: 12 }, padding: 16 } }
      },
      cutout: "65%"
    }
  });
}

// ── Shared helpers ────────────────────────────────────────────────
function buildFbCard(r) {
  const sentKey = { Positive: "positive", Negative: "negative", Neutral: "neutral" }[r.sentiment] || "neutral";
  const chipCls = { Positive: "chip-positive", Negative: "chip-negative", Neutral: "chip-neutral" }[r.sentiment] || "";
  const date    = r.created_at ? new Date(r.created_at).toLocaleDateString() : "";
  const div = document.createElement("div");
  div.className = `fb-card ${sentKey}`;
  div.innerHTML = `
    <div class="fb-header">
      <span class="fb-course">📘 ${r.course}</span>
      <span class="fb-meta">${r.student ? "👤 " + r.student + " · " : ""}${date}</span>
    </div>
    <p class="fb-text">${r.feedback}</p>
    <div class="fb-footer">
      <span class="chip ${chipCls}">${r.sentiment}</span>
      <span class="chip chip-rating">⭐ ${r.rating}/5</span>
    </div>
  `;
  return div;
}

function emptyState(msg) {
  return `<div class="empty-state"><span class="empty-icon">📭</span><p>${msg}</p></div>`;
}

// ── Init ──────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  if (ROLE === "student")  loadCourses();
  if (ROLE === "faculty")  loadTeacherData();
  if (ROLE === "admin")    loadAdminData();
});