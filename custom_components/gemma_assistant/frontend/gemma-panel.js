/* Gemma Assistant — sidebar chat panel.
 * Custom element loaded by Home Assistant as a "custom" built-in panel.
 * HA sets `hass`, `panel` and `narrow` properties on the element; the chat
 * itself goes through the authenticated WebSocket command
 * "gemma_assistant/chat".
 */
class GemmaPanel extends HTMLElement {
  constructor() {
    super();
    this._hass = null;
    this._booted = false;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._booted) {
      this._booted = true;
      this._render();
    }
  }

  _render() {
    const root = this.attachShadow({ mode: "open" });
    root.innerHTML = `
      <style>
        :host { display: block; height: 100%; }
        .wrap {
          box-sizing: border-box;
          display: flex; flex-direction: column;
          height: 100%; max-width: 760px; margin: 0 auto;
          padding: 16px;
        }
        .msgs {
          flex: 1; overflow-y: auto;
          display: flex; flex-direction: column; gap: 8px;
          padding-bottom: 8px;
        }
        .msg {
          max-width: 85%;
          padding: 10px 14px;
          border-radius: 16px;
          line-height: 1.45;
          white-space: pre-wrap;
          word-wrap: break-word;
        }
        .msg.user {
          align-self: flex-end;
          background: var(--primary-color);
          color: var(--text-primary-color, #fff);
          border-bottom-right-radius: 4px;
        }
        .msg.assistant {
          align-self: flex-start;
          background: var(--card-background-color, #1c1c1c);
          color: var(--primary-text-color);
          border: 1px solid var(--divider-color, #333);
          border-bottom-left-radius: 4px;
        }
        .msg.typing { opacity: 0.55; font-style: italic; }
        .bar {
          display: flex; gap: 8px; padding-top: 8px;
          border-top: 1px solid var(--divider-color, #333);
        }
        input {
          flex: 1; padding: 12px 14px; font-size: 16px;
          color: var(--primary-text-color);
          background: var(--card-background-color, #1c1c1c);
          border: 1px solid var(--divider-color, #444);
          border-radius: 24px; outline: none;
        }
        input:focus { border-color: var(--primary-color); }
        button {
          padding: 0 20px; border: none; border-radius: 24px;
          background: var(--primary-color);
          color: var(--text-primary-color, #fff);
          font-size: 15px; font-weight: 500; cursor: pointer;
        }
        button.icon { padding: 0 14px; background: transparent;
          color: var(--secondary-text-color); font-size: 20px; }
        button:disabled { opacity: 0.5; cursor: default; }
      </style>
      <div class="wrap">
        <div id="msgs" class="msgs"></div>
        <div class="bar">
          <input id="in" type="text"
                 placeholder="Demande quelque chose à Gemma…"
                 autocomplete="off" />
          <button id="clear" class="icon" title="Effacer la conversation">🗑</button>
          <button id="send">Envoyer</button>
        </div>
      </div>`;

    this.$msgs = root.getElementById("msgs");
    this.$in = root.getElementById("in");
    this.$send = root.getElementById("send");

    this.$send.addEventListener("click", () => this._send());
    this.$in.addEventListener("keydown", (e) => {
      if (e.key === "Enter") this._send();
    });
    root.getElementById("clear").addEventListener("click", () => {
      this.$msgs.innerHTML = "";
      this._greet();
    });

    this._greet();
  }

  _greet() {
    this._addMsg(
      "assistant",
      "Salut, je suis Gemma — ton assistant local (Ollama + recherche web). " +
        "Pose-moi une question, contrôle ta maison, ou demande-moi les dernières actualités."
    );
  }

  _addMsg(who, text) {
    const d = document.createElement("div");
    d.className = `msg ${who}`;
    d.textContent = text;
    this.$msgs.appendChild(d);
    this.$msgs.scrollTop = this.$msgs.scrollHeight;
    return d;
  }

  async _send() {
    const text = this.$in.value.trim();
    if (!text || !this._hass) return;
    this.$in.value = "";
    this._addMsg("user", text);
    const typing = this._addMsg("assistant typing", "Gemma réfléchit…");
    this.$send.disabled = true;
    try {
      const res = await this._hass.connection.sendMessagePromise({
        type: "gemma_assistant/chat",
        text,
      });
      typing.classList.remove("typing");
      typing.textContent = (res && res.response) || "(réponse vide)";
    } catch (err) {
      typing.classList.remove("typing");
      typing.textContent = `Erreur : ${(err && err.message) || err}`;
    }
    this.$send.disabled = false;
    this.$in.focus();
  }
}

customElements.define("gemma-panel", GemmaPanel);
