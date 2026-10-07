/**
 * FLL BIOGLOW Intelligence Dashboard - Symbolic Client-side Access Gatekeeper
 * 
 * Provides sleek frosted-glass access control with customizable password,
 * session persistence, and lock/logout capability.
 */
(function() {
  // Configurable acceptable passwords (case-insensitive for convenience)
  const VALID_PASSWORDS = ["fll2026", "bioglow", "fll", "8888"];
  const STORAGE_KEY = "fll_bioglow_auth_pass_v1";

  // Prevent flash of unauthenticated content by injecting critical overlay CSS immediately
  const styleEl = document.createElement("style");
  styleEl.id = "fll-auth-styles";
  styleEl.textContent = `
    .fll-auth-overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background: rgba(6, 8, 16, 0.94);
      backdrop-filter: blur(24px);
      -webkit-backdrop-filter: blur(24px);
      z-index: 999999;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: 'Outfit', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      transition: opacity 0.35s cubic-bezier(0.16, 1, 0.3, 1), visibility 0.35s;
    }
    .fll-auth-overlay.hidden {
      opacity: 0;
      visibility: hidden;
      pointer-events: none;
    }
    .fll-auth-card {
      background: linear-gradient(145deg, rgba(18, 24, 44, 0.95), rgba(10, 14, 28, 0.98));
      border: 1px solid rgba(0, 242, 254, 0.3);
      box-shadow: 0 25px 60px rgba(0, 0, 0, 0.8), 0 0 40px rgba(0, 242, 254, 0.2);
      border-radius: 20px;
      padding: 36px 32px;
      width: 90%;
      max-width: 420px;
      text-align: center;
      position: relative;
      animation: fllAuthPop 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    @keyframes fllAuthPop {
      0% { transform: scale(0.92); opacity: 0; }
      100% { transform: scale(1); opacity: 1; }
    }
    .fll-auth-icon {
      width: 64px;
      height: 64px;
      margin: 0 auto 16px;
      border-radius: 18px;
      background: linear-gradient(135deg, rgba(0, 242, 254, 0.2), rgba(168, 85, 247, 0.2));
      border: 1px solid rgba(0, 242, 254, 0.4);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 28px;
      box-shadow: 0 0 25px rgba(0, 242, 254, 0.35);
    }
    .fll-auth-title {
      font-size: 1.35rem;
      font-weight: 700;
      color: #fff;
      margin-bottom: 8px;
      letter-spacing: -0.01em;
    }
    .fll-auth-desc {
      font-size: 0.85rem;
      color: #94a3b8;
      margin-bottom: 24px;
      line-height: 1.5;
    }
    .fll-auth-form {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .fll-auth-input-wrap {
      position: relative;
      width: 100%;
    }
    .fll-auth-input {
      width: 100%;
      box-sizing: border-box;
      background: rgba(10, 14, 26, 0.85);
      border: 1px solid rgba(148, 163, 184, 0.25);
      border-radius: 12px;
      padding: 13px 44px 13px 16px;
      font-size: 0.95rem;
      color: #f8fafc;
      outline: none;
      transition: all 0.2s ease;
      font-family: inherit;
    }
    .fll-auth-input:focus {
      border-color: #00f2fe;
      box-shadow: 0 0 15px rgba(0, 242, 254, 0.3);
      background: rgba(15, 23, 42, 0.95);
    }
    .fll-auth-input.error {
      border-color: #ef4444 !important;
      box-shadow: 0 0 15px rgba(239, 68, 68, 0.4) !important;
      animation: fllShake 0.4s ease;
    }
    @keyframes fllShake {
      0%, 100% { transform: translateX(0); }
      20%, 60% { transform: translateX(-8px); }
      40%, 80% { transform: translateX(8px); }
    }
    .fll-auth-toggle-pwd {
      position: absolute;
      right: 14px;
      top: 50%;
      transform: translateY(-50%);
      background: none;
      border: none;
      color: #94a3b8;
      cursor: pointer;
      font-size: 1rem;
      padding: 4px;
    }
    .fll-auth-toggle-pwd:hover {
      color: #00f2fe;
    }
    .fll-auth-options {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.8rem;
      color: #94a3b8;
      padding: 0 2px;
    }
    .fll-auth-remember {
      display: flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      user-select: none;
    }
    .fll-auth-remember input {
      accent-color: #00f2fe;
      cursor: pointer;
    }
    .fll-auth-hint {
      color: #64748b;
      font-size: 0.78rem;
    }
    .fll-auth-btn {
      width: 100%;
      background: linear-gradient(135deg, #00f2fe, #4facfe);
      border: none;
      border-radius: 12px;
      padding: 13px;
      font-size: 0.95rem;
      font-weight: 700;
      color: #060810;
      cursor: pointer;
      transition: all 0.25s ease;
      box-shadow: 0 4px 15px rgba(0, 242, 254, 0.4);
    }
    .fll-auth-btn:hover {
      transform: translateY(-1px);
      box-shadow: 0 6px 22px rgba(0, 242, 254, 0.6);
      filter: brightness(1.08);
    }
    .fll-auth-btn:active {
      transform: translateY(1px);
    }
    .fll-auth-msg {
      font-size: 0.82rem;
      color: #ef4444;
      min-height: 18px;
      margin-top: -6px;
    }
    /* Lock / Logout Button in Header */
    .fll-nav-lock-btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.15);
      color: #94a3b8;
      font-size: 0.82rem;
      padding: 6px 12px;
      border-radius: 999px;
      cursor: pointer;
      transition: all 0.2s ease;
      text-decoration: none;
      margin-left: auto;
    }
    .fll-nav-lock-btn:hover {
      background: rgba(239, 68, 68, 0.15);
      border-color: rgba(239, 68, 68, 0.4);
      color: #fca5a5;
    }
  `;
  document.head.appendChild(styleEl);

  function isAuthorized() {
    return (
      sessionStorage.getItem(STORAGE_KEY) === "authorized" ||
      localStorage.getItem(STORAGE_KEY) === "authorized"
    );
  }

  function setAuthorized(remember) {
    sessionStorage.setItem(STORAGE_KEY, "authorized");
    if (remember) {
      localStorage.setItem(STORAGE_KEY, "authorized");
    }
  }

  function clearAuthorized() {
    sessionStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(STORAGE_KEY);
  }

  function renderLockModal() {
    let overlay = document.getElementById("fllAuthOverlay");
    if (overlay) return overlay;

    overlay = document.createElement("div");
    overlay.id = "fllAuthOverlay";
    overlay.className = "fll-auth-overlay";
    overlay.innerHTML = `
      <div class="fll-auth-card">
        <div class="fll-auth-icon">🔐</div>
        <div class="fll-auth-title">NorCal FLL BIOGLOW</div>
        <div class="fll-auth-desc">
          战队竞技情报与合规审查系统<br>
          <span style="color: #64748b; font-size: 0.8rem;">受保护的内部看板 · 请验证访问密码</span>
        </div>
        <form class="fll-auth-form" id="fllAuthForm" onsubmit="return false;">
          <div class="fll-auth-input-wrap">
            <input 
              type="password" 
              id="fllAuthInput" 
              class="fll-auth-input" 
              placeholder="请输入系统密码..." 
              autocomplete="current-password" 
              required
            />
            <button type="button" class="fll-auth-toggle-pwd" id="fllAuthTogglePwd" title="显示/隐藏密码">👁</button>
          </div>
          <div class="fll-auth-msg" id="fllAuthMsg"></div>
          <div class="fll-auth-options">
            <label class="fll-auth-remember">
              <input type="checkbox" id="fllAuthRemember" checked />
              <span>记住登录 (本机免密)</span>
            </label>
            <span class="fll-auth-hint" title="默认系统预设密码">默认: fll2026</span>
          </div>
          <button type="submit" class="fll-auth-btn" id="fllAuthSubmit">解锁进入看板 ⚡</button>
        </form>
      </div>
    `;

    document.body.appendChild(overlay);

    // Bind interaction events
    const input = overlay.querySelector("#fllAuthInput");
    const toggleBtn = overlay.querySelector("#fllAuthTogglePwd");
    const form = overlay.querySelector("#fllAuthForm");
    const msgEl = overlay.querySelector("#fllAuthMsg");
    const rememberBox = overlay.querySelector("#fllAuthRemember");

    toggleBtn.addEventListener("click", () => {
      if (input.type === "password") {
        input.type = "text";
        toggleBtn.textContent = "🔒";
      } else {
        input.type = "password";
        toggleBtn.textContent = "👁";
      }
    });

    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const val = (input.value || "").trim().toLowerCase();
      if (VALID_PASSWORDS.includes(val)) {
        msgEl.textContent = "";
        input.classList.remove("error");
        setAuthorized(rememberBox.checked);
        overlay.classList.add("hidden");
        setTimeout(() => {
          overlay.remove();
        }, 360);
      } else {
        input.classList.add("error");
        msgEl.textContent = "密码错误，请重试（提示：默认密码 fll2026）";
        input.focus();
        setTimeout(() => {
          input.classList.remove("error");
        }, 600);
      }
    });

    setTimeout(() => input.focus(), 100);
    return overlay;
  }

  function injectLockOutButton() {
    // Look for header nav container
    const navBar = document.querySelector(".header-inner, .app-header, .header-right, nav");
    if (!navBar || document.getElementById("fllLogoutBtn")) return;

    const lockBtn = document.createElement("button");
    lockBtn.id = "fllLogoutBtn";
    lockBtn.className = "fll-nav-lock-btn";
    lockBtn.title = "锁定看板并清除本地登录凭证";
    lockBtn.innerHTML = `<span>🔒</span><span>锁定系统</span>`;
    lockBtn.onclick = () => {
      clearAuthorized();
      location.reload();
    };

    // Append into appropriate container
    const navTabs = document.querySelector(".nav-tabs, .header-right");
    if (navTabs) {
      navTabs.appendChild(lockBtn);
    } else {
      navBar.appendChild(lockBtn);
    }
  }

  // Initialization check
  function init() {
    if (!isAuthorized()) {
      renderLockModal();
    }
    injectLockOutButton();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
