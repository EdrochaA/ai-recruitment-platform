/**
 * Chatbot Widget
 * Visible and usable only by HR and Admin users.
 * Communicates with POST /chatbot/message via JWT.
 */

const Chatbot = (() => {
  let isOpen = false;
  let isSending = false;

  const ALLOWED_ROLES = ['hr', 'admin'];

  // ── DOM helpers ──────────────────────────────────────────────────────────
  const fab       = () => document.getElementById('chatbot-fab');
  const panel     = () => document.getElementById('chatbot-panel');
  const messages  = () => document.getElementById('chatbot-messages');
  const input     = () => document.getElementById('chatbot-input');
  const sendBtn   = () => document.getElementById('chatbot-send');
  const closeBtn  = () => document.getElementById('chatbot-close');

  // ── Visibility ───────────────────────────────────────────────────────────
  function isAllowed() {
    const user = authSystem.getCurrentUser();
    return user && ALLOWED_ROLES.includes(user.role);
  }

  function updateVisibility() {
    const allowed = isAllowed();
    const fabEl = fab();
    if (!fabEl) return;

    if (allowed) {
      fabEl.style.display = 'flex';
      fabEl.style.alignItems = 'center';
      fabEl.style.justifyContent = 'center';
    } else {
      fabEl.style.display = 'none';
      close();
    }
  }

  // ── Open / close ─────────────────────────────────────────────────────────
  function open() {
    if (!isAllowed()) return;
    isOpen = true;
    panel().classList.add('chatbot--open');
    fab().setAttribute('aria-expanded', 'true');
    if (messages().children.length === 0) {
      appendBotMessage(
        '¡Hola! Soy el asistente de reclutamiento. ¿En qué puedo ayudarte hoy?',
        ['Ver candidaturas', 'Ver mis ofertas', 'Ayuda con CVs']
      );
    }
    setTimeout(() => input().focus(), 50);
  }

  function close() {
    isOpen = false;
    panel().classList.remove('chatbot--open');
    const fabEl = fab();
    if (fabEl) fabEl.setAttribute('aria-expanded', 'false');
  }

  function toggle() {
    isOpen ? close() : open();
  }

  // ── Messages ─────────────────────────────────────────────────────────────
  function appendUserMessage(text) {
    const el = document.createElement('div');
    el.className = 'chatbot__bubble chatbot__bubble--user';
    el.textContent = text;
    messages().appendChild(el);
    scrollToBottom();
  }

  function appendBotMessage(text, suggestions = []) {
    const wrapper = document.createElement('div');

    const bubble = document.createElement('div');
    bubble.className = 'chatbot__bubble chatbot__bubble--bot';
    bubble.textContent = text;
    wrapper.appendChild(bubble);

    if (suggestions.length > 0) {
      const suggestionsEl = document.createElement('div');
      suggestionsEl.className = 'chatbot__suggestions';
      suggestions.forEach(s => {
        const btn = document.createElement('button');
        btn.className = 'chatbot__suggestion-btn';
        btn.textContent = s;
        btn.addEventListener('click', () => {
          if (!isSending) sendMessage(s);
        });
        suggestionsEl.appendChild(btn);
      });
      wrapper.appendChild(suggestionsEl);
    }

    messages().appendChild(wrapper);
    scrollToBottom();
  }

  function appendErrorMessage(text) {
    const el = document.createElement('div');
    el.className = 'chatbot__bubble chatbot__bubble--error';
    el.textContent = text;
    messages().appendChild(el);
    scrollToBottom();
  }

  function appendTypingIndicator() {
    const el = document.createElement('div');
    el.className = 'chatbot__typing';
    el.id = 'chatbot-typing';
    el.textContent = 'Escribiendo…';
    messages().appendChild(el);
    scrollToBottom();
    return el;
  }

  function removeTypingIndicator() {
    const el = document.getElementById('chatbot-typing');
    if (el) el.remove();
  }

  function scrollToBottom() {
    const el = messages();
    el.scrollTop = el.scrollHeight;
  }

  // ── Current page context ─────────────────────────────────────────────────
  function getCurrentPage() {
    const page = (typeof router !== 'undefined') ? router.getCurrentPage() : 'unknown';
    const pageMap = {
      'hr-dashboard':    'hr_dashboard',
      'admin-dashboard': 'hr_dashboard',
      'home':            'job_offers',
      'job-detail':      'job_detail',
      'apply':           'applications',
    };
    return pageMap[page] || 'unknown';
  }

  // ── Ranking intent detection ─────────────────────────────────────────────

  /**
   * Returns true when the message looks like a candidate ranking request.
   * Triggers on Spanish/English keywords related to ranking candidates.
   */
  function isRankingIntent(msg) {
    return /ranking|top\s*\d|mejores candidatos?|filtrar candidatos?|rank(ea|ar)|candidatos? para|rankea/i.test(msg);
  }

  /**
   * Try to extract a job offer title from the user message.
   * Priority: quoted text → "para/de/oferta … <title>" pattern.
   * Returns null when no title can be confidently extracted.
   */
  function extractJobOfferTitle(msg) {
    // Text inside single or double quotes
    const quoted = msg.match(/["'«»]([^"'«»]{3,})["'«»]/);
    if (quoted) return quoted[1].trim();

    // "para (la oferta de?) X", "de la oferta X", "oferta llamada X", etc.
    const patterns = [
      /(?:para|de)\s+(?:la\s+oferta(?:\s+de(?:\s+trabajo)?)?|la\s+posici[oó]n(?:\s+de)?)\s+(.+?)(?:\s*[,.]|$)/i,
      /oferta(?:\s+de(?:\s+trabajo)?)?\s+(?:llamad[ao]|titulad[ao])?\s+(.+?)(?:\s*[,.]|$)/i,
      /para\s+([A-Za-z0-9\s\-áéíóúüñÁÉÍÓÚÜÑ]{5,})(?:\s*[,.]|$)/i,
    ];
    for (const p of patterns) {
      const m = msg.match(p);
      if (m) return m[1].trim();
    }

    return null;
  }

  // ── Ranking response renderer ────────────────────────────────────────────

  function appendRankingResponse(data) {
    // If not found or empty, fall back to a plain bot bubble
    if (!data.found || !data.ranked_candidates || data.ranked_candidates.length === 0) {
      appendBotMessage(data.message);
      return;
    }

    const wrapper = document.createElement('div');

    // Summary bubble
    const summary = document.createElement('div');
    summary.className = 'chatbot__bubble chatbot__bubble--bot';
    summary.textContent = data.message;
    wrapper.appendChild(summary);

    // One card per ranked candidate
    data.ranked_candidates.forEach(c => {
      const card = document.createElement('div');
      card.className = 'chatbot__ranking-card';

      const skillsText = (c.skills || []).slice(0, 5).join(', ') || '–';
      const analysisLabel = c.cv_analysis_status === 'completed'
        ? '✅ Análisis completo'
        : c.cv_processing_status === 'processed'
          ? '⚡ CV procesado'
          : '⏳ Pendiente';

      card.innerHTML = `
        <div class="chatbot__ranking-badge">#${c.rank}</div>
        <div class="chatbot__ranking-info">
          <div class="chatbot__ranking-name">${c.candidate_name}</div>
          <div class="chatbot__ranking-score">
            <span class="chatbot__ranking-score-value">${c.score}<small>/100</small></span>
            <span class="chatbot__ranking-status">${analysisLabel}</span>
          </div>
          <div class="chatbot__ranking-reason">${c.ranking_reason}</div>
          <div class="chatbot__ranking-skills">🛠 ${skillsText}</div>
        </div>
      `;
      wrapper.appendChild(card);
    });

    messages().appendChild(wrapper);
    scrollToBottom();
  }

  // ── Send ─────────────────────────────────────────────────────────────────
  async function sendMessage(text) {
    const msg = (text || input().value).trim();
    if (!msg || isSending) return;

    if (!isAllowed()) {
      appendErrorMessage('No tienes permiso para usar el chatbot.');
      return;
    }

    isSending = true;
    sendBtn().disabled = true;
    input().value = '';

    appendUserMessage(msg);
    appendTypingIndicator();

    try {
      // ── Ranking intent ────────────────────────────────────────────────
      if (isRankingIntent(msg)) {
        const title = extractJobOfferTitle(msg);
        if (!title) {
          removeTypingIndicator();
          appendBotMessage(
            'Para hacer el ranking necesito saber el nombre exacto de la oferta. ' +
            'Escríbelo entre comillas, por ejemplo:\n' +
            '"Ranking para \\"Senior Frontend Developer\\""'
          );
        } else {
          const data = await apiClient.rankCandidates(title);
          removeTypingIndicator();
          appendRankingResponse(data);
        }
      } else {
        // ── Normal chatbot ──────────────────────────────────────────────
        const data = await apiClient.sendChatbotMessage(
          msg,
          getCurrentPage(),
          null,
          null
        );
        removeTypingIndicator();
        appendBotMessage(data.answer, data.suggestions || []);
      }
    } catch (err) {
      removeTypingIndicator();
      const status = err.status || 0;
      if (status === 401) {
        appendErrorMessage('Sesión expirada. Por favor, vuelve a iniciar sesión.');
      } else if (status === 403) {
        appendErrorMessage('No tienes acceso al chatbot. Solo disponible para HR y Admin.');
        close();
        updateVisibility();
      } else {
        appendErrorMessage('Error al contactar con el asistente. Inténtalo de nuevo.');
      }
    } finally {
      isSending = false;
      sendBtn().disabled = false;
      input().focus();
    }
  }

  // ── Init ─────────────────────────────────────────────────────────────────
  function init() {
    const fabEl = fab();
    if (!fabEl) return;

    fabEl.addEventListener('click', toggle);
    closeBtn().addEventListener('click', close);

    input().addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    input().addEventListener('input', () => {
      sendBtn().disabled = input().value.trim().length === 0 || isSending;
    });

    sendBtn().addEventListener('click', () => sendMessage());

    // React to auth changes (login / logout)
    window.addEventListener('authChange', updateVisibility);

    updateVisibility();
  }

  // Run after DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  return { open, close, updateVisibility };
})();

window.chatbot = Chatbot;
