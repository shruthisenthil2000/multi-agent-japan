"""Premium travel UI design system — Streamlit CSS injection."""

PREMIUM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
  --bg: #070B14;
  --surface: #111827;
  --card: #1A2335;
  --card-hover: #1f2a40;
  --accent: #3B82F6;
  --accent-soft: rgba(59, 130, 246, 0.15);
  --success: #22C55E;
  --text: #F1F5F9;
  --muted: #94A3B8;
  --border: rgba(148, 163, 184, 0.12);
  --glass: rgba(17, 24, 39, 0.72);
  --shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
  --radius: 20px;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header[data-testid="stHeader"] {visibility: hidden; height: 0;}
.stDeployButton, [data-testid="stToolbar"] {display: none !important;}
.stApp {
  background: var(--bg);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  color: var(--text);
}
.block-container {
  padding: 0.75rem 1rem 1rem;
  max-width: 100%;
}
section[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border);
  min-width: 280px !important;
  max-width: 280px !important;
}
section[data-testid="stSidebar"] > div {
  background: var(--surface) !important;
}
h1, h2, h3, h4, p, label, span { color: var(--text) !important; }

/* Layout regions */
.trip-profile-title {
  font-size: 0.7rem; font-weight: 600; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--muted) !important; margin-bottom: 0.5rem;
}
.profile-bar {
  height: 6px; background: var(--card); border-radius: 99px; overflow: hidden; margin: 0.75rem 0 1rem;
}
.profile-bar-fill {
  height: 100%; background: linear-gradient(90deg, var(--accent), #60a5fa);
  border-radius: 99px; transition: width 0.3s ease;
}
.profile-row {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.45rem 0; font-size: 0.88rem; color: var(--muted) !important;
}
.profile-row.done { color: var(--text) !important; }
.profile-row .icon { width: 1.25rem; }

/* Chat */
.chat-header {
  font-size: 1.35rem; font-weight: 700; margin-bottom: 0.25rem;
  background: linear-gradient(135deg, #fff 0%, #94a3b8 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.chat-sub { font-size: 0.85rem; color: var(--muted) !important; margin-bottom: 1rem; }
.chat-scroll {
  max-width: 850px; margin: 0 auto; min-height: 52vh; max-height: 58vh;
  overflow-y: auto; padding: 0.5rem 0.25rem 1rem;
  scrollbar-width: thin; scrollbar-color: var(--card) transparent;
}
.msg-row { display: flex; margin-bottom: 1rem; max-width: 850px; margin-left: auto; margin-right: auto; }
.msg-row.user { justify-content: flex-end; }
.msg-assistant {
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--radius); border-top-left-radius: 6px;
  padding: 1rem 1.15rem; max-width: 85%; line-height: 1.55;
  box-shadow: var(--shadow); backdrop-filter: blur(12px);
}
.msg-user {
  background: linear-gradient(135deg, #2563eb, var(--accent));
  color: #fff !important; border-radius: var(--radius); border-top-right-radius: 6px;
  padding: 0.85rem 1.15rem; max-width: 78%; line-height: 1.5;
  box-shadow: 0 4px 20px rgba(59, 130, 246, 0.35);
}
.msg-user * { color: #fff !important; }
.typing-dots span {
  display: inline-block; width: 7px; height: 7px; margin: 0 3px;
  background: var(--muted); border-radius: 50%;
  animation: bounce 1.2s infinite;
}
.typing-dots span:nth-child(2) { animation-delay: 0.15s; }
.typing-dots span:nth-child(3) { animation-delay: 0.3s; }
@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-6px); opacity: 1; }
}

/* Composer */
.composer-wrap {
  max-width: 850px; margin: 0 auto; padding: 0.5rem 0 0.25rem;
  position: sticky; bottom: 0; z-index: 10;
}
.composer-shell {
  background: var(--glass); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 0.65rem 0.85rem;
  box-shadow: var(--shadow); backdrop-filter: blur(16px);
}
div[data-testid="stForm"] {
  border: none !important; padding: 0 !important;
  background: transparent !important;
}
div[data-testid="stForm"] textarea {
  background: transparent !important; border: none !important;
  color: var(--text) !important; font-size: 1rem !important;
  min-height: 52px !important; box-shadow: none !important;
}
div[data-testid="stForm"] textarea:focus {
  box-shadow: none !important; outline: none !important;
}
.composer-actions button {
  background: var(--accent-soft) !important; border: 1px solid var(--border) !important;
  border-radius: 14px !important; color: var(--text) !important;
  min-height: 42px !important; transition: all 0.2s;
}
.composer-actions button:hover {
  background: var(--accent) !important; border-color: var(--accent) !important;
}
.composer-actions button[kind="primary"] {
  background: var(--accent) !important; border-color: var(--accent) !important;
}

/* Itinerary panel */
.itin-panel {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 1.15rem;
  box-shadow: var(--shadow); max-height: 92vh; overflow-y: auto;
  position: sticky; top: 0.5rem;
}
.itin-title { font-size: 1.1rem; font-weight: 700; margin-bottom: 0.75rem; }
.itin-empty {
  text-align: center; padding: 2.5rem 1rem; color: var(--muted) !important;
  font-size: 0.9rem; line-height: 1.6;
}
.day-block {
  margin-bottom: 1.5rem; padding-bottom: 1.25rem;
  border-bottom: 1px solid var(--border);
}
.day-header {
  font-size: 1rem; font-weight: 700; margin-bottom: 0.15rem;
}
.day-city { font-size: 0.8rem; color: var(--muted) !important; margin-bottom: 0.85rem; }
.day-divider {
  height: 2px; background: linear-gradient(90deg, var(--accent), transparent);
  margin-bottom: 0.85rem; border-radius: 2px;
}
.slot-label {
  font-size: 0.72rem; font-weight: 600; letter-spacing: 0.06em;
  color: var(--muted) !important; margin: 0.65rem 0 0.4rem;
}
.activity-card-premium {
  background: var(--card); border: 1px solid var(--border);
  border-radius: 16px; padding: 0.9rem 1rem; margin-bottom: 0.55rem;
  transition: background 0.2s, transform 0.2s;
}
.activity-card-premium:hover {
  background: var(--card-hover); transform: translateY(-1px);
}
.act-title { font-weight: 600; font-size: 0.95rem; margin-bottom: 0.25rem; }
.act-meta { font-size: 0.75rem; color: var(--muted) !important; }
.act-notes { font-size: 0.82rem; color: #cbd5e1 !important; margin-top: 0.4rem; line-height: 1.45; }

/* Travel pills */
.pill-row { display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 0.75rem 0; }
.pill-row button {
  border-radius: 999px !important; font-size: 0.78rem !important;
  padding: 0.35rem 0.85rem !important; background: var(--card) !important;
  border: 1px solid var(--border) !important; color: var(--text) !important;
}
.pill-row button:hover {
  background: var(--accent-soft) !important; border-color: var(--accent) !important;
}

/* Modals */
.ui-overlay {
  position: fixed; inset: 0; z-index: 9999;
  background: rgba(7, 11, 20, 0.82); backdrop-filter: blur(8px);
  display: flex; align-items: center; justify-content: center;
}
.ui-modal {
  background: var(--card); border: 1px solid var(--border);
  border-radius: 24px; padding: 2.5rem 2rem; text-align: center;
  min-width: 320px; max-width: 420px; box-shadow: 0 24px 80px rgba(0,0,0,0.5);
}
.ui-modal-icon { font-size: 2.5rem; margin-bottom: 0.75rem; }
.ui-modal-title { font-size: 1.15rem; font-weight: 600; margin-bottom: 0.5rem; }
.ui-modal-sub { font-size: 0.88rem; color: var(--muted) !important; line-height: 1.5; }
.pulse-ring {
  width: 72px; height: 72px; margin: 0 auto 1rem; border-radius: 50%;
  border: 3px solid var(--accent);
  animation: pulse-ring 1.5s ease-out infinite;
}
@keyframes pulse-ring {
  0% { transform: scale(0.9); opacity: 1; }
  100% { transform: scale(1.35); opacity: 0; }
}
.loader-spin {
  width: 40px; height: 40px; margin: 0 auto 1rem;
  border: 3px solid var(--border); border-top-color: var(--accent);
  border-radius: 50%; animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Hide default widgets in main */
.stTextInput > label, .stTextArea > label { display: none !important; }
[data-testid="stMetric"] { display: none !important; }
div[data-testid="column"] .stDownloadButton button {
  font-size: 0.75rem !important; border-radius: 12px !important;
  background: var(--card) !important; border: 1px solid var(--border) !important;
}
</style>
"""

CHAT_SCROLL_JS = """
<script>
(function() {
  const el = window.parent.document.querySelector('.chat-scroll');
  if (el) el.scrollTop = el.scrollHeight;
})();
</script>
"""
