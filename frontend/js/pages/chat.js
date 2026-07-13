/**
 * Chat page controller (/chat route)
 *
 * The router calls window.initChat when navigating to the chat page.
 * All chat logic lives in js/chatbot.js; this just opens/focuses it.
 */
function initChat() {
  if (window.chatbot && typeof window.chatbot.open === 'function') {
    window.chatbot.open();
  }
}

window.initChat = initChat;
