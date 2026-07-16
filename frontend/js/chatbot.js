/**
 * Chat Assistant (full page — /chat route)
 *
 * Renders inside #chat-page (not a floating widget).
 * Usable only by HR and Admin users. Communicates with the backend via
 * apiClient.sendChatbotMessage and apiClient.rankCandidates (JWT).
 *
 * Assistant replies are rendered as Markdown (via marked.js when available).
 */

const Chatbot = (() => {
  let isSending = false;
  let welcomed = false;

  const ALLOWED_ROLES = ['hr', 'admin'];

  // ── DOM helpers ──────────────────────────────────────────────────────────
  const messages = () => document.getElementById('chatbot-messages');
  const input    = () => document.getElementById('chatbot-input');
  const sendBtn  = () => document.getElementById('chatbot-send');

  // ── Permissions ──────────────────────────────────────────────────────────
  function isAllowed() {
    const user = authSystem.getCurrentUser();
    return user && ALLOWED_ROLES.includes(user.role);
  }

  function updateVisibility() {
    // Visibility of the /chat entry point is handled by the sidebar (app.js).
    // If the user loses access while on the page, reset the conversation state.
    if (!isAllowed()) {
      welcomed = false;
      const list = messages();
      if (list) list.innerHTML = '';
    }
  }

  // ── Markdown rendering ───────────────────────────────────────────────────
  function renderMarkdown(text) {
    if (window.marked && typeof window.marked.parse === 'function') {
      try {
        return window.marked.parse(text, { breaks: true });
      } catch (_) {
        /* fall through to escaped plain text */
      }
    }
    return escapeHtml(text).replace(/\n/g, '<br>');
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // ── Message builders ─────────────────────────────────────────────────────
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
    bubble.innerHTML = renderMarkdown(text);
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
    el.innerHTML = '<span class="spinner spinner--sm"></span> Escribiendo…';
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
    if (el) el.scrollTop = el.scrollHeight;
  }

  // ── Welcome message (shown once per session on the page) ─────────────────
  function showWelcomeIfNeeded() {
    if (welcomed) return;
    const list = messages();
    if (!list) return;
    if (list.children.length === 0) {
      appendBotMessage(
        '¡Hola! Soy el **asistente de reclutamiento**. Puedo ayudarte a:\n' +
        '- Consultar tus ofertas y candidaturas\n' +
        '- Generar un **ranking de candidatos** para una oferta\n\n' +
        '¿En qué puedo ayudarte hoy?',
        ['Ver candidaturas', 'Ver mis ofertas', 'Ayuda con CVs']
      );
    }
    welcomed = true;
  }

  // ── Current page context ─────────────────────────────────────────────────
  function getContextPage() {
    // The assistant lives on its own page; report a generic HR context.
    return 'hr_dashboard';
  }

  // ── Ranking intent detection ─────────────────────────────────────────────
  function isRankingIntent(msg) {
    return /ranking|top\s*\d|mejores candidatos?|filtrar candidatos?|rank(ea|ar)|candidatos? para|rankea/i.test(msg);
  }

  function extractJobOfferTitle(msg) {
    const quoted = msg.match(/["'«»]([^"'«»]{3,})["'«»]/);
    if (quoted) return quoted[1].trim();

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
    if (!data.found || !data.ranked_candidates || data.ranked_candidates.length === 0) {
      appendBotMessage(data.message);
      return;
    }

    const wrapper = document.createElement('div');

    const summary = document.createElement('div');
    summary.className = 'chatbot__bubble chatbot__bubble--bot';
    summary.innerHTML = renderMarkdown(data.message);
    wrapper.appendChild(summary);

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
          <div class="chatbot__ranking-name">${escapeHtml(c.candidate_name)}</div>
          <div class="chatbot__ranking-score">
            <span class="chatbot__ranking-score-value">${c.score}<small>/100</small></span>
            <span class="chatbot__ranking-status">${analysisLabel}</span>
          </div>
          <div class="chatbot__ranking-reason">${escapeHtml(c.ranking_reason || '')}</div>
          <div class="chatbot__ranking-skills">🛠 ${escapeHtml(skillsText)}</div>
        </div>
      `;
      wrapper.appendChild(card);
    });

    messages().appendChild(wrapper);
    scrollToBottom();
  }

  // ── Send ─────────────────────────────────────────────────────────────────
  async function sendMessage(text) {
    const el = input();
    const msg = (text || (el ? el.value : '')).trim();
    if (!msg || isSending) return;

    if (!isAllowed()) {
      appendErrorMessage('No tienes permiso para usar el asistente.');
      return;
    }

    isSending = true;
    if (sendBtn()) sendBtn().disabled = true;
    if (el) {
      el.value = '';
      autoResize();
    }

    appendUserMessage(msg);
    appendTypingIndicator();

    try {
      if (isRankingIntent(msg)) {
        const title = extractJobOfferTitle(msg);
        if (!title) {
          removeTypingIndicator();
          appendBotMessage(
            'Para hacer el ranking necesito saber el nombre exacto de la oferta. ' +
            'Escríbelo entre comillas, por ejemplo:\n\n' +
            '`Ranking para "Senior Frontend Developer"`'
          );
        } else {
          const data = await apiClient.rankCandidates(title);
          removeTypingIndicator();
          appendRankingResponse(data);
        }
      } else {
        const data = await apiClient.sendChatbotMessage(
          msg,
          getContextPage(),
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
        appendErrorMessage('No tienes acceso al asistente. Solo disponible para HR y Admin.');
      } else {
        appendErrorMessage('Error al contactar con el asistente. Inténtalo de nuevo.');
      }
    } finally {
      isSending = false;
      if (sendBtn()) sendBtn().disabled = (input()?.value.trim().length || 0) === 0;
      input()?.focus();
    }
  }

  // ── Auto-resizing textarea ───────────────────────────────────────────────
  function autoResize() {
    const el = input();
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 160) + 'px';
  }

  // ── Init / open (called by initChat when navigating to /chat) ────────────
  let bound = false;

  function bindEvents() {
    if (bound) return;
    const el = input();
    const btn = sendBtn();
    if (!el || !btn) return;

    el.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    el.addEventListener('input', () => {
      autoResize();
      btn.disabled = el.value.trim().length === 0 || isSending;
    });

    btn.addEventListener('click', () => sendMessage());

    window.addEventListener('authChange', updateVisibility);

    bound = true;
  }

  /**
   * Called every time the /chat page is shown.
   */
  function open() {
    if (!isAllowed()) return;
    bindEvents();
    showWelcomeIfNeeded();
    autoResize();
    if (sendBtn()) sendBtn().disabled = (input()?.value.trim().length || 0) === 0;
    setTimeout(() => input()?.focus(), 50);
  }

  return { open, updateVisibility };
})();

window.chatbot = Chatbot;
