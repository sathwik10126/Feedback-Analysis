// ── Login / Signup Page JS ──────────────────────────────────────

let selectedRole = "student";
let authMode = "login";

// Role tab switching (shared between login & signup)
document.querySelectorAll(".role-tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".role-tab").forEach(t => t.classList.remove("active"));
    tab.classList.add("active");
    selectedRole = tab.dataset.role;
  });
});

// Switch between Sign In / Create Account
function switchAuthMode(mode) {
  authMode = mode;
  const isLogin = mode === "login";

  document.getElementById("tabLogin").classList.toggle("active", isLogin);
  document.getElementById("tabSignup").classList.toggle("active", !isLogin);

  document.getElementById("loginForm").classList.toggle("hidden", !isLogin);
  document.getElementById("signupForm").classList.toggle("hidden", isLogin);

  document.getElementById("formTitle").textContent = isLogin ? "Sign In" : "Create Account";
  document.getElementById("formSub").textContent = isLogin
    ? "Select your role to continue"
    : "Register a new account to get started";

  document.getElementById("hintText").classList.toggle("hidden", !isLogin);

  document.getElementById("loginError").classList.add("hidden");
  document.getElementById("signupError").classList.add("hidden");
}

// ── LOGIN ─────────────────────────────────────────────────────
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

// ── SIGNUP ────────────────────────────────────────────────────
document.getElementById("signupForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const username = document.getElementById("suUsername").value.trim();
  const password = document.getElementById("suPassword").value;
  const confirm  = document.getElementById("suConfirm").value;
  const btn      = document.getElementById("signupBtn");
  const spinner  = document.getElementById("signupSpinner");
  const errEl    = document.getElementById("signupError");

  errEl.classList.add("hidden");

  if (password !== confirm) {
    errEl.textContent = "Passwords do not match.";
    errEl.classList.remove("hidden");
    return;
  }

  btn.disabled = true;
  spinner.classList.remove("hidden");

  try {
    const res  = await fetch("/api/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password, role: selectedRole })
    });
    const data = await res.json();

    if (data.success) {
      window.location.href = "/dashboard";
    } else {
      errEl.textContent = data.message || "Signup failed. Try again.";
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

function togglePwd(id) {
  const inp = document.getElementById(id);
  inp.type = inp.type === "password" ? "text" : "password";
}
