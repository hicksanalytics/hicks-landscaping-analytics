(() => {
  const script = document.currentScript;
  const endpoint = new URL('/api/ask', script.src).href;
  const style = document.createElement('style');
  style.textContent = `
    #ha-assistant-toggle {position:fixed;right:18px;bottom:18px;z-index:9998;border:0;
      border-radius:999px;background:#14532d;color:white;padding:13px 18px;font:600 15px system-ui;
      box-shadow:0 8px 28px #0004;cursor:pointer}
    #ha-assistant-panel {position:fixed;right:18px;bottom:74px;z-index:9999;width:min(390px,calc(100vw - 24px));
      height:min(570px,calc(100vh - 100px));background:#fff;color:#17231b;border-radius:16px;
      box-shadow:0 16px 50px #0005;display:none;flex-direction:column;overflow:hidden;font:14px system-ui}
    #ha-assistant-panel.open {display:flex}
    #ha-assistant-panel header {background:#14532d;color:#fff;padding:15px 18px;display:flex;justify-content:space-between;align-items:center}
    #ha-assistant-panel header button {border:0;background:transparent;color:#fff;font-size:22px;cursor:pointer}
    #ha-assistant-messages {flex:1;overflow:auto;padding:14px;display:flex;flex-direction:column;gap:12px}
    .ha-message {padding:10px 12px;border-radius:12px;white-space:pre-wrap;line-height:1.5}
    .ha-message.user {background:#eaf5ed;align-self:flex-end;max-width:90%}
    .ha-message.assistant {background:#f3f5f3;align-self:flex-start;max-width:95%}
    .ha-message details {margin-top:8px;font-size:12px}
    .ha-message pre {overflow:auto;max-height:160px;font-size:11px}
    #ha-assistant-panel form {display:flex;gap:8px;padding:12px;border-top:1px solid #ddd}
    #ha-assistant-panel input {flex:1;min-width:0;padding:9px;border:1px solid #aaa;border-radius:8px;font:inherit}
    #ha-assistant-panel form button {border:0;border-radius:8px;background:#14532d;color:#fff;padding:9px 12px;cursor:pointer}
    #ha-assistant-panel form button:disabled {opacity:.5}
    #ha-assistant-panel footer {padding:0 12px 10px;font-size:11px;color:#5a655b}
  `;
  document.head.append(style);
  const toggle = document.createElement('button');
  toggle.id = 'ha-assistant-toggle'; toggle.textContent = 'Ask the Data';
  toggle.setAttribute('aria-expanded', 'false'); toggle.setAttribute('aria-controls', 'ha-assistant-panel');
  const panel = document.createElement('section'); panel.id = 'ha-assistant-panel';
  panel.setAttribute('aria-label', 'Landscaping data assistant');
  const header = document.createElement('header');
  const title = document.createElement('strong'); title.textContent = 'Landscaping AI analyst';
  const close = document.createElement('button'); close.textContent = '×'; close.setAttribute('aria-label', 'Close assistant');
  header.append(title, close);
  const messages = document.createElement('div'); messages.id = 'ha-assistant-messages';
  const form = document.createElement('form');
  const input = document.createElement('input'); input.required = true; input.maxLength = 350;
  input.placeholder = 'Ask about crews, margins, estimates…'; input.setAttribute('aria-label', 'Your data question');
  const send = document.createElement('button'); send.type = 'submit'; send.textContent = 'Ask';
  form.append(input, send);
  const footer = document.createElement('footer');
  footer.textContent = 'Fictional data · AI-generated answers · Review data lookups';
  panel.append(header, messages, form, footer); document.body.append(panel, toggle);
  const show = open => { panel.classList.toggle('open', open); toggle.setAttribute('aria-expanded', String(open)); if (open) input.focus(); };
  toggle.addEventListener('click', () => show(!panel.classList.contains('open')));
  close.addEventListener('click', () => show(false));
  const add = (role, content, trace) => {
    const box = document.createElement('div'); box.className = `ha-message ${role}`; box.textContent = content;
    if (trace?.length) {
      const detail = document.createElement('details');
      const summary = document.createElement('summary'); summary.textContent = 'See the data lookups';
      const pre = document.createElement('pre'); pre.textContent = JSON.stringify(trace, null, 2);
      detail.append(summary, pre); box.append(detail);
    }
    messages.append(box); messages.scrollTop = messages.scrollHeight;
    return box;
  };
  add('assistant', 'Try: Which crew had the lowest gross margin in July 2026?');
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const question = input.value.trim(); if (!question) return;
    input.value = ''; add('user', question);
    send.disabled = true; const pending = add('assistant', 'Checking the demo data…');
    try {
      const response = await fetch(endpoint, { method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ question }) });
      const data = await response.json();
      pending.remove(); add('assistant', data.answer || data.error || 'No answer available.', data.trace);
    } catch {
      pending.textContent = 'The assistant is temporarily unavailable.';
    } finally { send.disabled = false; input.focus(); }
  });
})();
