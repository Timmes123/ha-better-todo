/* Better ToDo Card — shipped with the better_todo integration.
 * Vanilla web component, no external dependencies. Talks to the backend
 * via the better_todo/* websocket commands.
 */

const STR = {
  en: {
    today: "due today", overdue_d: (n) => `${n} d overdue`, in_d: (n) => `in ${n} d`,
    times_due: (n) => `${n}× due`, streak_w: (n) => `${n} wk streak`, streak_m: (n) => `${n} mo streak`,
    missed_w: (n) => `${n} wk missed`, missed_m: (n) => `${n} mo missed`,
    skipped: "skipped", upcoming: "upcoming", done: "Done", edit: "Edit", skip: "Skip",
    delete: "Delete", new_task: "New task", new_list: "New list", save: "Save", cancel: "Cancel",
    complete_one: "Complete 1×", complete_all: (n) => `Complete all ${n}`,
    show_done: "Show completed", show_upcoming: "Show upcoming", all_persons: "Everyone",
    me: "My tasks", title_f: "Title", list_f: "List", type_f: "Type", notes_f: "Notes",
    due_f: "Due date", first_due_f: "First / next due date", visible_from_f: "Visible from",
    every: "Every", freq_daily: "day(s)", freq_weekly: "week(s)", freq_monthly: "month(s)", freq_yearly: "year(s)",
    after_done: "after completion", lead_f: "Show days before due (empty = on due date)",
    period_f: "Period", week: "Week", month: "Month", priority_f: "Priority",
    prio_none: "None", prio_low: "Low", prio_med: "Medium", prio_high: "High",
    assigned_f: "Assigned to", nobody: "Nobody", rotation_f: "Rotate between",
    subtasks_f: "Subtasks", add_subtask: "Add subtask…", list_name_f: "List name",
    delete_list: "Delete list", delete_list_confirm: "Delete this list and all its tasks?",
    delete_task_confirm: "Delete this task?", no_lists: "No lists yet.", empty: "Nothing to do 🎉",
    type_simple: "One-time", type_scheduled: "Recurring (fixed schedule)",
    type_after: "Recurring (after completion)", type_period: "Weekly/monthly task",
    error: "Better ToDo is not reachable. Is the integration installed?",
    days_left: (n) => `${n} d left`,
  },
  de: {
    today: "heute fällig", overdue_d: (n) => `seit ${n} T überfällig`, in_d: (n) => `in ${n} T`,
    times_due: (n) => `${n}× fällig`, streak_w: (n) => `${n} Wo Serie`, streak_m: (n) => `${n} Mon Serie`,
    missed_w: (n) => `seit ${n} Wo nicht`, missed_m: (n) => `seit ${n} Mon nicht`,
    skipped: "übersprungen", upcoming: "demnächst", done: "Erledigt", edit: "Bearbeiten", skip: "Überspringen",
    delete: "Löschen", new_task: "Neue Aufgabe", new_list: "Neue Liste", save: "Speichern", cancel: "Abbrechen",
    complete_one: "1× erledigen", complete_all: (n) => `Alle ${n} erledigen`,
    show_done: "Erledigte anzeigen", show_upcoming: "Kommende anzeigen", all_persons: "Alle",
    me: "Meine Aufgaben", title_f: "Titel", list_f: "Liste", type_f: "Typ", notes_f: "Notizen",
    due_f: "Fälligkeitsdatum", first_due_f: "Erste / nächste Fälligkeit", visible_from_f: "Sichtbar ab",
    every: "Alle", freq_daily: "Tag(e)", freq_weekly: "Woche(n)", freq_monthly: "Monat(e)", freq_yearly: "Jahr(e)",
    after_done: "nach Erledigung", lead_f: "Tage vor Fälligkeit anzeigen (leer = am Stichtag)",
    period_f: "Periode", week: "Woche", month: "Monat", priority_f: "Priorität",
    prio_none: "Keine", prio_low: "Niedrig", prio_med: "Mittel", prio_high: "Hoch",
    assigned_f: "Zugewiesen an", nobody: "Niemand", rotation_f: "Rotieren zwischen",
    subtasks_f: "Unteraufgaben", add_subtask: "Unteraufgabe hinzufügen…", list_name_f: "Listenname",
    delete_list: "Liste löschen", delete_list_confirm: "Diese Liste mit allen Aufgaben löschen?",
    delete_task_confirm: "Diese Aufgabe löschen?", no_lists: "Noch keine Listen.", empty: "Nichts zu tun 🎉",
    type_simple: "Einmalig", type_scheduled: "Wiederholend (fester Plan)",
    type_after: "Wiederholend (nach Erledigung)", type_period: "Wochen-/Monatsaufgabe",
    error: "Better ToDo ist nicht erreichbar. Ist die Integration installiert?",
    days_left: (n) => `noch ${n} T`,
  },
};

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );

const STATE_RANK = {
  overdue: 0, due: 1, period_open: 2, open: 3, period_skipped: 4,
  upcoming: 5, hidden: 5, done: 6, period_done: 6,
};

class BetterTodoCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._data = null;
    this._error = null;
    this._sub = null;
    this._ui = { menu: false, expanded: null, lists: null, person: null, showDone: null, showUpcoming: null };
    this._dialog = null; // {kind: task|list|chooser, draft}
  }

  setConfig(config) {
    this._config = {
      title: null, lists: null, assigned: "all",
      show_menu: true, show_add: true, show_completed: false, show_upcoming: false,
      ...config,
    };
  }

  static getStubConfig() {
    return { show_menu: true, show_add: true };
  }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    if (first) this._connect();
  }

  connectedCallback() {
    if (this._hass && !this._sub) this._connect();
  }

  disconnectedCallback() {
    if (this._sub) { this._sub.then((u) => u()).catch(() => {}); this._sub = null; }
  }

  get t() {
    const lang = (this._hass?.locale?.language || "en").toLowerCase();
    return lang.startsWith("de") ? STR.de : STR.en;
  }

  async _connect() {
    try {
      this._data = await this._hass.callWS({ type: "better_todo/get_data" });
      this._error = null;
      this._sub = this._hass.connection.subscribeMessage(
        (data) => { this._data = data; this._render(); },
        { type: "better_todo/subscribe" }
      );
    } catch (e) {
      this._error = e;
    }
    this._render();
  }

  async _ws(msg) {
    try {
      return await this._hass.callWS(msg);
    } catch (e) {
      alert(e.message || "Error");
      throw e;
    }
  }

  // ------------------------------------------------------------- helpers

  _feature(name) { return !!this._data?.features?.[name]; }

  _person(entityId) { return (this._data?.persons || []).find((p) => p.entity_id === entityId); }

  _myPerson() {
    const uid = this._hass?.user?.id;
    return (this._data?.persons || []).find((p) => p.user_id === uid) || null;
  }

  _activeLists() {
    const all = this._data?.lists || [];
    let filtered = all;
    if (this._config.lists && this._config.lists.length) {
      filtered = all.filter((l) => this._config.lists.includes(l.id) || this._config.lists.includes(l.name));
    }
    if (this._ui.lists) filtered = filtered.filter((l) => this._ui.lists.includes(l.id));
    return filtered;
  }

  _personFilter() {
    if (this._ui.person !== null) return this._ui.person;
    const cfg = this._config.assigned || "all";
    if (cfg === "me") return this._myPerson()?.entity_id || "all";
    return cfg;
  }

  _showDone() { return this._ui.showDone ?? !!this._config.show_completed; }
  _showUpcoming() { return this._ui.showUpcoming ?? !!this._config.show_upcoming; }

  _visibleTasks(listId) {
    const personFilter = this._personFilter();
    return (this._data?.tasks || [])
      .filter((t) => t.list_id === listId)
      .filter((t) => {
        const s = t.computed?.state;
        if (s === "done") return this._showDone();
        if (s === "hidden") return this._showUpcoming();
        if (s === "upcoming") return t.computed.visible || this._showUpcoming();
        return true;
      })
      .filter((t) => personFilter === "all" || !personFilter ? true : t.assigned_to === personFilter)
      .sort((a, b) => {
        const r = (STATE_RANK[a.computed?.state] ?? 3) - (STATE_RANK[b.computed?.state] ?? 3);
        if (r !== 0) return r;
        const pa = a.priority || 99, pb = b.priority || 99;
        if (pa !== pb) return pa - pb;
        const da = a.computed?.due || "9999", db = b.computed?.due || "9999";
        if (da !== db) return da < db ? -1 : 1;
        return (a.order || 0) - (b.order || 0);
      });
  }

  // ------------------------------------------------------------- render

  _render() {
    if (this._dialog) return; // don't nuke open dialogs; re-rendered on close
    const t = this.t;
    let body;
    if (this._error) {
      body = `<div class="empty">${esc(t.error)}</div>`;
    } else if (!this._data) {
      body = `<div class="empty">…</div>`;
    } else {
      body = this._renderBody();
    }
    this.shadowRoot.innerHTML = `<style>${this._css()}</style><ha-card>${this._renderHeader()}${body}</ha-card>`;
    this.shadowRoot.addEventListener("click", (e) => this._onClick(e));
    this.shadowRoot.addEventListener("change", (e) => this._onChange(e));
  }

  _renderHeader() {
    const t = this.t;
    if (!this._data) return "";
    const title = this._config.title;
    return `<div class="head">
      <div class="head-title">${title ? esc(title) : ""}</div>
      <div class="head-actions">
        ${this._config.show_add ? `<button class="icon-btn" data-action="add" title="${esc(t.new_task)}">+</button>` : ""}
        ${this._config.show_menu ? `<button class="icon-btn ${this._ui.menu ? "active" : ""}" data-action="menu" title="Filter">☰</button>` : ""}
      </div>
    </div>${this._ui.menu ? this._renderMenu() : ""}`;
  }

  _renderMenu() {
    const t = this.t;
    const all = this._data.lists || [];
    const active = this._activeLists().map((l) => l.id);
    const personFilter = this._personFilter();
    const persons = this._data.persons || [];
    return `<div class="menu">
      <div class="chips">
        ${all.map((l) => `<button class="chip ${active.includes(l.id) ? "on" : ""}" data-action="toggle-list" data-id="${esc(l.id)}">${esc(l.name)}</button>`).join("")}
        <button class="chip ghost" data-action="add-list">+ ${esc(t.new_list)}</button>
      </div>
      ${this._feature("assignment") && persons.length ? `<div class="menu-row">
        <select data-action="person-filter">
          <option value="all" ${personFilter === "all" ? "selected" : ""}>${esc(t.all_persons)}</option>
          ${persons.map((p) => `<option value="${esc(p.entity_id)}" ${personFilter === p.entity_id ? "selected" : ""}>${esc(p.name)}</option>`).join("")}
        </select>
      </div>` : ""}
      <div class="menu-row toggles">
        <label><input type="checkbox" data-action="show-done" ${this._showDone() ? "checked" : ""}> ${esc(t.show_done)}</label>
        <label><input type="checkbox" data-action="show-upcoming" ${this._showUpcoming() ? "checked" : ""}> ${esc(t.show_upcoming)}</label>
      </div>
    </div>`;
  }

  _renderBody() {
    const t = this.t;
    const lists = this._activeLists();
    if (!(this._data.lists || []).length) {
      return `<div class="empty">${esc(t.no_lists)}<br><br><button class="btn" data-action="add-list">+ ${esc(t.new_list)}</button></div>`;
    }
    const multi = lists.length > 1;
    let html = "";
    let any = false;
    for (const list of lists) {
      const tasks = this._visibleTasks(list.id);
      if (!tasks.length && multi) continue;
      any = any || tasks.length > 0;
      html += `<div class="list-block">`;
      if (multi) html += `<div class="list-head">${esc(list.name)}</div>`;
      html += tasks.map((task) => this._renderTask(task)).join("");
      html += `</div>`;
    }
    if (!any) html += `<div class="empty">${esc(t.empty)}</div>`;
    return html;
  }

  _renderTask(task) {
    const t = this.t;
    const c = task.computed || {};
    const s = c.state;
    const doneish = s === "done" || s === "period_done";
    const expanded = this._ui.expanded === task.id;
    const badges = [];

    if (s === "overdue" && c.due_count > 1) badges.push(`<span class="badge err">${esc(t.times_due(c.due_count))}</span>`);
    if (s === "overdue") badges.push(`<span class="badge err">${esc(t.overdue_d(c.days_overdue))}</span>`);
    if (s === "due") badges.push(`<span class="badge warn">${esc(t.today)}</span>`);
    if (s === "open" && c.days_left !== undefined) {
      const cls = c.days_left <= 7 ? "warn" : "";
      badges.push(`<span class="badge ${cls}">${esc(t.days_left(c.days_left))}</span>`);
    }
    if ((s === "upcoming" || s === "hidden") && (c.due || c.visible_from)) {
      badges.push(`<span class="badge dim">${esc(t.upcoming)} · ${esc(this._fmtDate(c.due || c.visible_from))}</span>`);
    }
    if (task.type === "period") {
      const wk = (c.period || task.period) === "week";
      if (c.streak > 0) badges.push(`<span class="badge ok">🔥 ${esc(wk ? t.streak_w(c.streak) : t.streak_m(c.streak))}</span>`);
      if (c.misses > 0 && !doneish) badges.push(`<span class="badge err">${esc(wk ? t.missed_w(c.misses) : t.missed_m(c.misses))}</span>`);
      if (s === "period_skipped") badges.push(`<span class="badge dim">${esc(t.skipped)}</span>`);
    }
    if (this._feature("priorities") && task.priority) {
      const labels = { 1: t.prio_high, 2: t.prio_med, 3: t.prio_low };
      badges.push(`<span class="badge prio p${task.priority}">${esc(labels[task.priority] || "")}</span>`);
    }
    if (this._feature("subtasks") && (task.subtasks || []).length) {
      const done = task.subtasks.filter((x) => x.done).length;
      badges.push(`<span class="badge dim">☑ ${done}/${task.subtasks.length}</span>`);
    }
    if (this._feature("assignment") && task.assigned_to) {
      const p = this._person(task.assigned_to);
      if (p) badges.push(`<span class="badge person">${esc(p.name)}${task.rotation ? " ⟳" : ""}</span>`);
    }
    const recurring = task.type === "scheduled" || task.type === "after_completion";
    if (recurring) badges.push(`<span class="badge dim">🔁</span>`);

    return `<div class="task ${doneish ? "done" : ""} ${s === "overdue" ? "overdue" : ""}" data-id="${esc(task.id)}">
      <div class="row" data-action="expand" data-id="${esc(task.id)}">
        <button class="check ${doneish ? "checked" : ""}" data-action="complete" data-id="${esc(task.id)}" aria-label="${esc(t.done)}">${doneish ? "✓" : ""}</button>
        <div class="task-main">
          <div class="task-title">${esc(task.title)}</div>
          ${badges.length ? `<div class="badges">${badges.join("")}</div>` : ""}
        </div>
      </div>
      ${expanded ? this._renderDetails(task) : ""}
    </div>`;
  }

  _renderDetails(task) {
    const t = this.t;
    const subtasks = this._feature("subtasks") ? (task.subtasks || []) : [];
    const recurring = task.type !== "simple";
    return `<div class="details">
      ${task.notes ? `<div class="notes">${esc(task.notes)}</div>` : ""}
      ${subtasks.length ? `<div class="subtasks">${subtasks
        .map((st) => `<label class="subtask"><input type="checkbox" data-action="subtask" data-id="${esc(task.id)}" data-sub="${esc(st.id)}" ${st.done ? "checked" : ""}> <span class="${st.done ? "st-done" : ""}">${esc(st.title)}</span></label>`)
        .join("")}</div>` : ""}
      <div class="actions">
        <button class="btn" data-action="edit" data-id="${esc(task.id)}">${esc(t.edit)}</button>
        ${recurring ? `<button class="btn" data-action="skip" data-id="${esc(task.id)}">${esc(t.skip)}</button>` : ""}
        <button class="btn danger" data-action="del-task" data-id="${esc(task.id)}">${esc(t.delete)}</button>
      </div>
    </div>`;
  }

  _fmtDate(iso) {
    if (!iso) return "";
    try {
      return new Date(iso + "T00:00:00").toLocaleDateString(this._hass?.locale?.language || "en", { day: "numeric", month: "short" });
    } catch { return iso; }
  }

  // ------------------------------------------------------------- events

  _onClick(e) {
    const el = e.target.closest("[data-action]");
    if (!el) return;
    const action = el.dataset.action;
    const id = el.dataset.id;
    if (action === "subtask") return; // handled on change
    e.stopPropagation();
    if (action === "menu") { this._ui.menu = !this._ui.menu; this._render(); }
    else if (action === "toggle-list") this._toggleListFilter(id);
    else if (action === "add") this._openTaskDialog(null);
    else if (action === "add-list") this._openListDialog(null);
    else if (action === "expand") { this._ui.expanded = this._ui.expanded === id ? null : id; this._render(); }
    else if (action === "complete") this._complete(id);
    else if (action === "edit") this._openTaskDialog(this._task(id));
    else if (action === "skip") this._ws({ type: "better_todo/skip_task", task_id: id });
    else if (action === "del-task") {
      if (confirm(this.t.delete_task_confirm)) this._ws({ type: "better_todo/delete_task", task_id: id });
    }
  }

  _onChange(e) {
    const el = e.target.closest("[data-action]");
    if (!el) return;
    const action = el.dataset.action;
    if (action === "subtask") {
      this._ws({ type: "better_todo/toggle_subtask", task_id: el.dataset.id, subtask_id: el.dataset.sub, done: el.checked });
    } else if (action === "person-filter") { this._ui.person = el.value; this._render(); }
    else if (action === "show-done") { this._ui.showDone = el.checked; this._render(); }
    else if (action === "show-upcoming") { this._ui.showUpcoming = el.checked; this._render(); }
  }

  _toggleListFilter(id) {
    const all = (this._data.lists || []).map((l) => l.id);
    let cur = this._ui.lists || this._activeLists().map((l) => l.id);
    cur = cur.includes(id) ? cur.filter((x) => x !== id) : [...cur, id];
    this._ui.lists = cur.length ? cur : null;
    if (cur.length === all.length) this._ui.lists = null;
    this._render();
  }

  _task(id) { return (this._data?.tasks || []).find((x) => x.id === id); }

  _complete(id) {
    const task = this._task(id);
    if (!task) return;
    const s = task.computed?.state;
    if (s === "done" || s === "period_done") {
      this._ws({ type: "better_todo/uncomplete_task", task_id: id });
      return;
    }
    if (task.type === "scheduled" && (task.computed?.due_count || 0) > 1) {
      this._openChooser(task);
      return;
    }
    this._ws({ type: "better_todo/complete_task", task_id: id, all: true });
  }

  // ------------------------------------------------------------- dialogs

  _closeDialog() {
    this._dialog = null;
    this._render();
  }

  _showDialog(innerHtml, onWire) {
    // Render dialog into shadow root without touching the card markup.
    const old = this.shadowRoot.querySelector("dialog");
    if (old) old.remove();
    const dlg = document.createElement("dialog");
    dlg.innerHTML = innerHtml;
    this.shadowRoot.appendChild(dlg);
    dlg.addEventListener("close", () => { if (this._dialog) { this._dialog = null; this._render(); } });
    dlg.addEventListener("click", (e) => { if (e.target === dlg) dlg.close(); });
    onWire(dlg);
    dlg.showModal();
    return dlg;
  }

  _openChooser(task) {
    const t = this.t;
    const n = task.computed.due_count;
    this._dialog = { kind: "chooser" };
    this._showDialog(
      `<div class="dlg-title">${esc(task.title)} — ${esc(t.times_due(n))}</div>
       <div class="dlg-actions">
         <button class="btn" data-x="one">${esc(t.complete_one)}</button>
         <button class="btn primary" data-x="all">${esc(t.complete_all(n))}</button>
         <button class="btn ghost" data-x="cancel">${esc(t.cancel)}</button>
       </div>`,
      (dlg) => {
        dlg.addEventListener("click", (e) => {
          const b = e.target.closest("[data-x]");
          if (!b) return;
          if (b.dataset.x === "one") this._ws({ type: "better_todo/complete_task", task_id: task.id, all: false });
          if (b.dataset.x === "all") this._ws({ type: "better_todo/complete_task", task_id: task.id, all: true });
          dlg.close();
        });
      }
    );
  }

  _openListDialog(list) {
    const t = this.t;
    this._dialog = { kind: "list" };
    this._showDialog(
      `<div class="dlg-title">${esc(t.new_list)}</div>
       <label class="field">${esc(t.list_name_f)}<input type="text" id="lname" value="${esc(list?.name || "")}"></label>
       <div class="dlg-actions">
         <button class="btn primary" data-x="save">${esc(t.save)}</button>
         <button class="btn ghost" data-x="cancel">${esc(t.cancel)}</button>
       </div>`,
      (dlg) => {
        dlg.querySelector("#lname").focus();
        dlg.addEventListener("click", async (e) => {
          const b = e.target.closest("[data-x]");
          if (!b) return;
          if (b.dataset.x === "save") {
            const name = dlg.querySelector("#lname").value.trim();
            if (!name) return;
            await this._ws({ type: "better_todo/save_list", list: { ...(list ? { id: list.id } : {}), name } });
          }
          dlg.close();
        });
      }
    );
  }

  _openTaskDialog(task) {
    const draft = task
      ? JSON.parse(JSON.stringify(task))
      : {
          list_id: this._activeLists()[0]?.id || this._data.lists[0]?.id,
          title: "", notes: "", type: "simple", due_date: null, visible_from: null,
          lead_days: null, priority: null, subtasks: [], assigned_to: null, rotation: null,
          schedule: { freq: "monthly", interval: 1 }, interval: { unit: "weeks", value: 1 },
          period: "week",
        };
    if (!draft.schedule) draft.schedule = { freq: "monthly", interval: 1 };
    if (!draft.interval) draft.interval = { unit: "weeks", value: 1 };
    if (!draft.period) draft.period = "week";
    this._dialog = { kind: "task", draft, isNew: !task };
    this._renderTaskDialog();
  }

  _renderTaskDialog() {
    const t = this.t;
    const d = this._dialog.draft;
    const lists = this._data.lists || [];
    const persons = this._data.persons || [];
    const types = [
      ["simple", t.type_simple],
      ["scheduled", t.type_scheduled],
      ["after_completion", t.type_after],
      ...(this._feature("periods") ? [["period", t.type_period]] : []),
    ];
    const rotationOn = !!(d.rotation && d.rotation.persons && d.rotation.persons.length);

    let typeFields = "";
    if (d.type === "simple") {
      typeFields = `
        <label class="field">${esc(t.due_f)}<input type="date" data-f="due_date" value="${esc(d.due_date || "")}"></label>
        <label class="field">${esc(t.visible_from_f)}<input type="date" data-f="visible_from" value="${esc(d.visible_from || "")}"></label>`;
    } else if (d.type === "scheduled") {
      typeFields = `
        <label class="field">${esc(t.first_due_f)}<input type="date" data-f="due_date" value="${esc(d.due_date || "")}" required></label>
        <div class="field-row">
          <span>${esc(t.every)}</span>
          <input type="number" min="1" class="num" data-f="schedule.interval" value="${esc(d.schedule.interval || 1)}">
          <select data-f="schedule.freq">
            <option value="daily" ${d.schedule.freq === "daily" ? "selected" : ""}>${esc(t.freq_daily)}</option>
            <option value="weekly" ${d.schedule.freq === "weekly" ? "selected" : ""}>${esc(t.freq_weekly)}</option>
            <option value="monthly" ${d.schedule.freq === "monthly" ? "selected" : ""}>${esc(t.freq_monthly)}</option>
            <option value="yearly" ${d.schedule.freq === "yearly" ? "selected" : ""}>${esc(t.freq_yearly)}</option>
          </select>
        </div>
        <label class="field">${esc(t.lead_f)}<input type="number" min="0" data-f="lead_days" value="${d.lead_days ?? ""}"></label>`;
    } else if (d.type === "after_completion") {
      typeFields = `
        <label class="field">${esc(t.first_due_f)}<input type="date" data-f="due_date" value="${esc(d.due_date || "")}" required></label>
        <div class="field-row">
          <span>${esc(t.every)}</span>
          <input type="number" min="1" class="num" data-f="interval.value" value="${esc(d.interval.value || 1)}">
          <select data-f="interval.unit">
            <option value="days" ${d.interval.unit === "days" ? "selected" : ""}>${esc(t.freq_daily)}</option>
            <option value="weeks" ${d.interval.unit === "weeks" ? "selected" : ""}>${esc(t.freq_weekly)}</option>
            <option value="months" ${d.interval.unit === "months" ? "selected" : ""}>${esc(t.freq_monthly)}</option>
          </select>
          <span>${esc(t.after_done)}</span>
        </div>
        <label class="field">${esc(t.lead_f)}<input type="number" min="0" data-f="lead_days" value="${d.lead_days ?? ""}"></label>`;
    } else if (d.type === "period") {
      typeFields = `
        <label class="field">${esc(t.period_f)}
          <select data-f="period">
            <option value="week" ${d.period === "week" ? "selected" : ""}>${esc(t.week)}</option>
            <option value="month" ${d.period === "month" ? "selected" : ""}>${esc(t.month)}</option>
          </select>
        </label>`;
    }

    const html = `
      <div class="dlg-title">${esc(this._dialog.isNew ? t.new_task : t.edit)}</div>
      <label class="field">${esc(t.title_f)}<input type="text" data-f="title" value="${esc(d.title)}" required></label>
      <label class="field">${esc(t.list_f)}
        <select data-f="list_id">${lists.map((l) => `<option value="${esc(l.id)}" ${d.list_id === l.id ? "selected" : ""}>${esc(l.name)}</option>`).join("")}</select>
      </label>
      <label class="field">${esc(t.type_f)}
        <select data-f="type" data-rebuild="1">${types.map(([v, label]) => `<option value="${esc(v)}" ${d.type === v ? "selected" : ""}>${esc(label)}</option>`).join("")}</select>
      </label>
      ${typeFields}
      <label class="field">${esc(t.notes_f)}<textarea data-f="notes" rows="2">${esc(d.notes || "")}</textarea></label>
      ${this._feature("priorities") ? `<label class="field">${esc(t.priority_f)}
        <select data-f="priority">
          <option value="" ${!d.priority ? "selected" : ""}>${esc(t.prio_none)}</option>
          <option value="1" ${d.priority === 1 ? "selected" : ""}>${esc(t.prio_high)}</option>
          <option value="2" ${d.priority === 2 ? "selected" : ""}>${esc(t.prio_med)}</option>
          <option value="3" ${d.priority === 3 ? "selected" : ""}>${esc(t.prio_low)}</option>
        </select></label>` : ""}
      ${this._feature("assignment") && persons.length ? `<label class="field">${esc(t.assigned_f)}
        <select data-f="assigned_to" ${rotationOn ? "disabled" : ""}>
          <option value="">${esc(t.nobody)}</option>
          ${persons.map((p) => `<option value="${esc(p.entity_id)}" ${d.assigned_to === p.entity_id ? "selected" : ""}>${esc(p.name)}</option>`).join("")}
        </select></label>` : ""}
      ${this._feature("rotation") && d.type !== "simple" && persons.length ? `<div class="field">
        <span>${esc(t.rotation_f)}</span>
        <div class="rot-list">${persons.map((p) => `<label class="rot"><input type="checkbox" data-rot="${esc(p.entity_id)}" ${rotationOn && d.rotation.persons.includes(p.entity_id) ? "checked" : ""}> ${esc(p.name)}</label>`).join("")}</div>
      </div>` : ""}
      ${this._feature("subtasks") ? `<div class="field">
        <span>${esc(t.subtasks_f)}</span>
        <div class="sub-edit">${(d.subtasks || []).map((st, i) => `<div class="sub-line"><span>${esc(st.title)}</span><button class="icon-btn small" data-subdel="${i}">×</button></div>`).join("")}</div>
        <div class="sub-add"><input type="text" id="newsub" placeholder="${esc(t.add_subtask)}"><button class="btn small" data-x="addsub">+</button></div>
      </div>` : ""}
      <div class="dlg-actions">
        <button class="btn primary" data-x="save">${esc(t.save)}</button>
        <button class="btn ghost" data-x="cancel">${esc(t.cancel)}</button>
      </div>`;

    this._showDialog(html, (dlg) => this._wireTaskDialog(dlg));
  }

  _wireTaskDialog(dlg) {
    const d = this._dialog.draft;
    const setPath = (path, value) => {
      const parts = path.split(".");
      let obj = d;
      while (parts.length > 1) obj = obj[parts.shift()];
      obj[parts[0]] = value;
    };
    dlg.addEventListener("input", (e) => {
      const f = e.target.dataset.f;
      if (!f) return;
      let v = e.target.value;
      if (e.target.type === "number") v = v === "" ? null : Number(v);
      if (f === "priority") v = v === "" ? null : Number(v);
      if ((f === "due_date" || f === "visible_from") && v === "") v = null;
      if (f === "assigned_to" && v === "") v = null;
      setPath(f, v);
      if (e.target.dataset.rebuild) this._renderTaskDialog();
    });
    dlg.addEventListener("change", (e) => {
      if (e.target.dataset.rot !== undefined && e.target.dataset.rot !== "") {
        const persons = new Set(d.rotation?.persons || []);
        if (e.target.checked) persons.add(e.target.dataset.rot);
        else persons.delete(e.target.dataset.rot);
        d.rotation = persons.size ? { persons: [...persons], index: d.rotation?.index || 0 } : null;
        const sel = dlg.querySelector('[data-f="assigned_to"]');
        if (sel) sel.disabled = !!d.rotation;
      }
    });
    dlg.addEventListener("click", async (e) => {
      const subdel = e.target.closest("[data-subdel]");
      if (subdel) {
        d.subtasks.splice(Number(subdel.dataset.subdel), 1);
        this._renderTaskDialog();
        return;
      }
      const b = e.target.closest("[data-x]");
      if (!b) return;
      if (b.dataset.x === "addsub") {
        const input = dlg.querySelector("#newsub");
        const title = input.value.trim();
        if (title) {
          d.subtasks = d.subtasks || [];
          d.subtasks.push({ title, done: false });
          this._renderTaskDialog();
        }
        return;
      }
      if (b.dataset.x === "save") {
        if (!(d.title || "").trim()) return;
        if ((d.type === "scheduled" || d.type === "after_completion") && !d.due_date) return;
        await this._saveDraft();
      }
      dlg.close();
    });
    const first = dlg.querySelector('[data-f="title"]');
    if (first && this._dialog.isNew) first.focus();
  }

  async _saveDraft() {
    const d = JSON.parse(JSON.stringify(this._dialog.draft));
    if (d.type === "scheduled") {
      // Derive the recurring day-of-month from the chosen due date.
      const day = Number((d.due_date || "").slice(8, 10));
      if (d.schedule.freq === "monthly" || d.schedule.freq === "yearly") d.schedule.day = day || null;
      d.interval = null; d.period = null;
    } else if (d.type === "after_completion") {
      d.schedule = null; d.period = null;
    } else if (d.type === "period") {
      d.schedule = null; d.interval = null; d.due_date = null; d.visible_from = null;
    } else {
      d.schedule = null; d.interval = null; d.period = null;
    }
    delete d.computed;
    await this._ws({ type: "better_todo/save_task", task: d });
  }

  // ------------------------------------------------------------- styles

  _css() {
    return `
      :host { display: block; }
      ha-card { padding: 12px 16px 16px; }
      * { box-sizing: border-box; font-family: inherit; }
      .head { display: flex; align-items: center; justify-content: space-between; min-height: 32px; }
      .head-title { font-size: 1.15em; font-weight: 500; color: var(--primary-text-color); }
      .head-actions { display: flex; gap: 4px; }
      .icon-btn { background: none; border: none; cursor: pointer; font-size: 1.2em; line-height: 1;
        color: var(--secondary-text-color); padding: 6px 8px; border-radius: 8px; }
      .icon-btn:hover, .icon-btn.active { background: var(--secondary-background-color); color: var(--primary-text-color); }
      .icon-btn.small { font-size: 1em; padding: 2px 6px; }
      .menu { padding: 8px 0 4px; border-bottom: 1px solid var(--divider-color); margin-bottom: 8px; }
      .chips { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
      .chip { border: 1px solid var(--divider-color); background: none; color: var(--secondary-text-color);
        border-radius: 14px; padding: 3px 12px; cursor: pointer; font-size: 0.85em; }
      .chip.on { background: var(--primary-color); border-color: var(--primary-color); color: var(--text-primary-color, #fff); }
      .chip.ghost { border-style: dashed; }
      .menu-row { margin: 6px 0; }
      .menu-row select { width: 100%; }
      .toggles { display: flex; gap: 16px; font-size: 0.85em; color: var(--secondary-text-color); flex-wrap: wrap; }
      .toggles label { display: flex; align-items: center; gap: 4px; cursor: pointer; }
      .list-block { margin-top: 4px; }
      .list-head { font-size: 0.8em; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;
        color: var(--secondary-text-color); margin: 12px 0 4px; }
      .task { border-radius: 10px; margin: 2px -8px; }
      .task:hover { background: var(--secondary-background-color); }
      .row { display: flex; align-items: flex-start; gap: 10px; padding: 7px 8px; cursor: pointer; }
      .check { flex: none; width: 22px; height: 22px; margin-top: 1px; border-radius: 50%;
        border: 2px solid var(--secondary-text-color); background: none; cursor: pointer;
        color: var(--text-primary-color, #fff); font-size: 13px; line-height: 1; padding: 0; }
      .check:hover { border-color: var(--primary-color); }
      .check.checked { background: var(--primary-color); border-color: var(--primary-color); }
      .task.overdue .check { border-color: var(--error-color); }
      .task-main { flex: 1; min-width: 0; }
      .task-title { color: var(--primary-text-color); word-break: break-word; }
      .task.done .task-title { text-decoration: line-through; color: var(--secondary-text-color); }
      .badges { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 3px; }
      .badge { font-size: 0.72em; padding: 1px 7px; border-radius: 9px;
        background: var(--secondary-background-color); color: var(--secondary-text-color); white-space: nowrap; }
      .badge.err { background: color-mix(in srgb, var(--error-color) 18%, transparent); color: var(--error-color); }
      .badge.warn { background: color-mix(in srgb, var(--warning-color) 22%, transparent); color: var(--warning-color); }
      .badge.ok { background: color-mix(in srgb, var(--success-color, #4caf50) 18%, transparent); color: var(--success-color, #4caf50); }
      .badge.person { background: color-mix(in srgb, var(--primary-color) 15%, transparent); color: var(--primary-color); }
      .badge.prio.p1 { background: color-mix(in srgb, var(--error-color) 18%, transparent); color: var(--error-color); }
      .badge.prio.p2 { background: color-mix(in srgb, var(--warning-color) 22%, transparent); color: var(--warning-color); }
      .badge.dim { opacity: 0.75; }
      .details { padding: 0 8px 10px 40px; }
      .notes { font-size: 0.85em; color: var(--secondary-text-color); white-space: pre-wrap; margin-bottom: 6px; }
      .subtasks { display: flex; flex-direction: column; gap: 3px; margin-bottom: 8px; }
      .subtask { display: flex; align-items: center; gap: 6px; font-size: 0.9em; color: var(--primary-text-color); cursor: pointer; }
      .st-done { text-decoration: line-through; color: var(--secondary-text-color); }
      .actions { display: flex; gap: 6px; flex-wrap: wrap; }
      .btn { border: 1px solid var(--divider-color); background: none; color: var(--primary-text-color);
        border-radius: 8px; padding: 5px 14px; cursor: pointer; font-size: 0.85em; }
      .btn:hover { background: var(--secondary-background-color); }
      .btn.primary { background: var(--primary-color); border-color: var(--primary-color); color: var(--text-primary-color, #fff); }
      .btn.danger { color: var(--error-color); border-color: color-mix(in srgb, var(--error-color) 40%, transparent); }
      .btn.ghost { border: none; color: var(--secondary-text-color); }
      .btn.small { padding: 3px 10px; }
      .empty { text-align: center; color: var(--secondary-text-color); padding: 24px 8px; }
      dialog { border: none; border-radius: 14px; background: var(--card-background-color, #fff);
        color: var(--primary-text-color); padding: 20px; min-width: min(340px, 90vw); max-width: min(440px, 95vw);
        box-shadow: 0 8px 32px rgba(0,0,0,0.35); }
      dialog::backdrop { background: rgba(0,0,0,0.45); }
      .dlg-title { font-size: 1.1em; font-weight: 500; margin-bottom: 14px; }
      .field { display: flex; flex-direction: column; gap: 3px; margin-bottom: 10px; font-size: 0.85em; color: var(--secondary-text-color); }
      .field input, .field select, .field textarea, .sub-add input {
        font-size: 1rem; padding: 7px 10px; border-radius: 8px; border: 1px solid var(--divider-color);
        background: var(--secondary-background-color); color: var(--primary-text-color); width: 100%; }
      .field-row { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; font-size: 0.9em; color: var(--secondary-text-color); }
      .field-row .num { width: 64px; padding: 7px 8px; border-radius: 8px; border: 1px solid var(--divider-color);
        background: var(--secondary-background-color); color: var(--primary-text-color); }
      .field-row select { padding: 7px 8px; border-radius: 8px; border: 1px solid var(--divider-color);
        background: var(--secondary-background-color); color: var(--primary-text-color); }
      .rot-list { display: flex; flex-wrap: wrap; gap: 8px 14px; margin-top: 4px; }
      .rot { display: flex; align-items: center; gap: 4px; font-size: 0.95em; color: var(--primary-text-color); cursor: pointer; }
      .sub-edit { display: flex; flex-direction: column; gap: 2px; margin: 4px 0; }
      .sub-line { display: flex; align-items: center; justify-content: space-between; gap: 8px;
        color: var(--primary-text-color); font-size: 0.95em; padding: 2px 0; }
      .sub-add { display: flex; gap: 6px; margin-top: 4px; }
      .dlg-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }
    `;
  }

  getCardSize() {
    return 3;
  }
}

customElements.define("better-todo-card", BetterTodoCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "better-todo-card",
  name: "Better ToDo Card",
  description: "Task list card for the Better ToDo integration.",
  preview: false,
});
