// ── Login Page JS ──────────────────────────────────────────────

let selectedRole = "student";

// Role tab switching
document.querySelectorAll(".role-tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".role-tab").forEach(t => t.classList.remove("active"));
    tab.classList.add("active");
    selectedRole = tab.dataset.role;
  });
});

// Form submit
document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;
  const btn      = document.getElementById("loginBtn");
  const spinner  = document.getElementById("loginSpinner");
  const errEl    = document.getElementById("loginError");

  errEl.classList.add("hidden");
  btn.disabled = true;
  spinner.classList.remove("hidden");

  try {
    const res  = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password, role: selectedRole })
    });
    const data = await res.json();

    if (data.success) {
      window.location.href = "/dashboard";
    } else {
      errEl.textContent = data.message || "Login failed. Try again.";
      errEl.classList.remove("hidden");
    }
  } catch {
    errEl.textContent = "Network error. Is the server running?";
    errEl.classList.remove("hidden");
  } finally {
    btn.disabled = false;
    spinner.classList.add("hidden");
  }
});

function togglePwd() {
  const inp = document.getElementById("password");
  inp.type = inp.type === "password" ? "text" : "password";
}
