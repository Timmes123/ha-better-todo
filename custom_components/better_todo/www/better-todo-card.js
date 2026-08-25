/* Better ToDo Card — shipped with the better_todo integration.
 * Vanilla web component, no external dependencies. Talks to the backend
 * via the better_todo/* websocket commands.
 */

const WD_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

const STR = {
  en: {
    wd: WD_EN,
    today: "due today", overdue_d: (n) => `${n} d overdue`, days_left: (n) => `${n} d left`,
    times_due: (n) => `${n}× due`, streak_w: (n) => `${n} wk streak`, streak_m: (n) => `${n} mo streak`,
    missed_w: (n) => `${n} wk missed`, missed_m: (n) => `${n} mo missed`,
    skipped: "skipped", upcoming: "upcoming", done: "Done", edit: "Edit", skip: "Skip",
    delete: "Delete", new_task: "New task", new_list: "New list", save: "Save", cancel: "Cancel",
    complete_one: "Complete 1×", complete_all: (n) => `Complete all ${n}`,
    show_done: "Show completed", show_upcoming: "Show upcoming", all_persons: "Everyone",
    title_f: "Title", list_f: "List", type_f: "Type", notes_f: "Notes",
    due_f: "Due date", first_due_f: "First / next due date", visible_from_f: "Visible from",
    time_f: "Time", every: "Every", freq_daily: "day(s)", freq_weekly: "week(s)",
    freq_monthly: "month(s)", freq_yearly: "year(s)", after_done: "after completion",
    lead_f: "Show days before due (empty = on due date)",
    period_f: "Period", week: "Week", month: "Month", priority_f: "Priority",
    prio_none: "None", prio_low: "Low", prio_med: "Medium", prio_high: "High",
    assigned_f: "Assigned to", nobody: "Nobody", rotate_f: "Rotate", rotate_start_f: "Start with",
    rec: (n, u) => n === 1 ? ({ d: "daily", w: "weekly", m: "monthly", y: "yearly" })[u] : `every ${n} ${({ d: "days", w: "weeks", m: "months", y: "years" })[u]}`,
    rec_in: (n, u) => `${n} ${({ d: "d", w: "wk", m: "mo", y: "yr" })[u]}`,
    subtasks_f: "Subtasks", add_subtask: "Add subtask…", list_name_f: "List name",
    delete_task_confirm: "Delete this task?", no_lists: "No lists yet.", empty: "Nothing to do 🎉",
    edit_list: "Edit list", delete_list_confirm: "Delete this list and all its tasks?",
    show_filters: "Show filters", manage_lists: "Edit lists",
    clear_done: "Clear completed", clear_done_confirm: "Delete all completed tasks?",
    reset_filters: "Reset filters",
    type_simple: "One-time", type_scheduled: "Recurring (fixed schedule)",
    type_after: "Recurring (after completion)", type_period: "Weekly/monthly task",
    error: "Better ToDo is not reachable. Is the integration installed?",
    tags_f: "Tags", tags_ph: "comma,separated", reminders_f: "Reminders",
    rem_0: "at due time", rem_min: (n) => `${n} min before`, rem_h: (n) => `${n} h before`,
    rem_d: (n) => `${n} d before`, add_reminder: "+ reminder",
    sort_f: "Sort", sort_smart: "Smart", sort_manual: "Manual", sort_due: "Due date",
    sort_prio: "Priority", sort_title: "Title", sort_person: "Person",
    due_soon: (n) => `Due soon (${n} d)`, end_f: "End (optional)",
    until_f: "Until date", max_occ_f: "Max. repetitions",
    monthly_day: (d) => `on day ${d}`, monthly_last: "on the last day",
    monthly_nth: (n, wd) => `on the ${n}. ${wd}`, monthly_nth_last: (wd) => `on the last ${wd}`,
    confirm_done: (t) => `Complete "${t}"?`,
    logged_in: "Logged-in user", mode_day: "on a fixed day", mode_last: "on the last day of the month",
    mode_nth: "on the nth weekday", day_f: "Day (1–31)", month_f: "Month", nth_last: "last",
    auto_hint: "empty = automatic from rule",
  },
  de: {
    wd: ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"],
    today: "heute fällig", overdue_d: (n) => `seit ${n} T überfällig`, days_left: (n) => `noch ${n} T`,
    times_due: (n) => `${n}× fällig`, streak_w: (n) => `${n} Wo Serie`, streak_m: (n) => `${n} Mon Serie`,
    missed_w: (n) => `seit ${n} Wo nicht`, missed_m: (n) => `seit ${n} Mon nicht`,
    skipped: "übersprungen", upcoming: "demnächst", done: "Erledigt", edit: "Bearbeiten", skip: "Überspringen",
    delete: "Löschen", new_task: "Neue Aufgabe", new_list: "Neue Liste", save: "Speichern", cancel: "Abbrechen",
    complete_one: "1× erledigen", complete_all: (n) => `Alle ${n} erledigen`,
    show_done: "Erledigte anzeigen", show_upcoming: "Kommende anzeigen", all_persons: "Alle",
    title_f: "Titel", list_f: "Liste", type_f: "Typ", notes_f: "Notizen",
    due_f: "Fälligkeitsdatum", first_due_f: "Erste / nächste Fälligkeit", visible_from_f: "Sichtbar ab",
    time_f: "Uhrzeit", every: "Alle", freq_daily: "Tag(e)", freq_weekly: "Woche(n)",
    freq_monthly: "Monat(e)", freq_yearly: "Jahr(e)", after_done: "nach Erledigung",
    lead_f: "Tage vor Fälligkeit anzeigen (leer = am Stichtag)",
    period_f: "Periode", week: "Woche", month: "Monat", priority_f: "Priorität",
    prio_none: "Keine", prio_low: "Niedrig", prio_med: "Mittel", prio_high: "Hoch",
    assigned_f: "Zugewiesen an", nobody: "Niemand", rotate_f: "Rotieren", rotate_start_f: "Beginnen mit",
    rec: (n, u) => n === 1 ? ({ d: "täglich", w: "wöchentlich", m: "monatlich", y: "jährlich" })[u] : `alle ${n} ${({ d: "Tage", w: "Wochen", m: "Monate", y: "Jahre" })[u]}`,
    rec_in: (n, u) => `${n} ${({ d: "T", w: "Wo", m: "Mon", y: "J" })[u]}`,
    subtasks_f: "Unteraufgaben", add_subtask: "Unteraufgabe hinzufügen…", list_name_f: "Listenname",
    delete_task_confirm: "Diese Aufgabe löschen?", no_lists: "Noch keine Listen.", empty: "Nichts zu tun 🎉",
    edit_list: "Liste bearbeiten", delete_list_confirm: "Diese Liste und alle ihre Aufgaben löschen?",
    show_filters: "Filter anzeigen", manage_lists: "Listen bearbeiten",
    clear_done: "Erledigte aufräumen", clear_done_confirm: "Alle erledigten Aufgaben löschen?",
    reset_filters: "Filter zurücksetzen",
    type_simple: "Einmalig", type_scheduled: "Wiederholend (fester Plan)",
    type_after: "Wiederholend (nach Erledigung)", type_period: "Wochen-/Monatsaufgabe",
    error: "Better ToDo ist nicht erreichbar. Ist die Integration installiert?",
    tags_f: "Tags", tags_ph: "komma,getrennt", reminders_f: "Erinnerungen",
    rem_0: "zur Fälligkeit", rem_min: (n) => `${n} Min vorher`, rem_h: (n) => `${n} Std vorher`,
    rem_d: (n) => `${n} T vorher`, add_reminder: "+ Erinnerung",
    sort_f: "Sortierung", sort_smart: "Automatisch", sort_manual: "Manuell", sort_due: "Fälligkeit",
    sort_prio: "Priorität", sort_title: "Titel", sort_person: "Person",
    due_soon: (n) => `Bald fällig (${n} T)`, end_f: "Ende (optional)",
    until_f: "Enddatum", max_occ_f: "Max. Wiederholungen",
    monthly_day: (d) => `am ${d}. Tag`, monthly_last: "am letzten Tag",
    monthly_nth: (n, wd) => `am ${n}. ${wd}`, monthly_nth_last: (wd) => `am letzten ${wd}`,
    confirm_done: (t) => `„${t}" erledigen?`,
    logged_in: "Angemeldeter Benutzer", mode_day: "an festem Tag", mode_last: "am letzten Tag des Monats",
    mode_nth: "am N-ten Wochentag", day_f: "Tag (1–31)", month_f: "Monat", nth_last: "letzter",
    auto_hint: "leer = automatisch aus der Regel",
  },
  fr: {
    wd: ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"],
    today: "pour aujourd'hui", overdue_d: (n) => `${n} j de retard`, days_left: (n) => `${n} j restants`,
    times_due: (n) => `${n}× dû`, streak_w: (n) => `série de ${n} sem`, streak_m: (n) => `série de ${n} mois`,
    missed_w: (n) => `${n} sem manquées`, missed_m: (n) => `${n} mois manqués`,
    skipped: "ignoré", upcoming: "à venir", done: "Terminé", edit: "Modifier", skip: "Ignorer",
    delete: "Supprimer", new_task: "Nouvelle tâche", new_list: "Nouvelle liste", save: "Enregistrer", cancel: "Annuler",
    complete_one: "Terminer 1×", complete_all: (n) => `Tout terminer (${n})`,
    show_done: "Afficher terminées", show_upcoming: "Afficher à venir", all_persons: "Tous",
    title_f: "Titre", list_f: "Liste", type_f: "Type", notes_f: "Notes",
    due_f: "Date d'échéance", first_due_f: "Première / prochaine échéance", visible_from_f: "Visible à partir de",
    time_f: "Heure", every: "Tous les", freq_daily: "jour(s)", freq_weekly: "semaine(s)",
    freq_monthly: "mois", freq_yearly: "an(s)", after_done: "après achèvement",
    lead_f: "Afficher x jours avant l'échéance (vide = le jour même)",
    period_f: "Période", week: "Semaine", month: "Mois", priority_f: "Priorité",
    prio_none: "Aucune", prio_low: "Basse", prio_med: "Moyenne", prio_high: "Haute",
    assigned_f: "Assignée à", nobody: "Personne", rotate_f: "Alterner", rotate_start_f: "Commencer par",
    rec: (n, u) => n === 1 ? ({ d: "quotidien", w: "hebdomadaire", m: "mensuel", y: "annuel" })[u] : (u === "w" ? `toutes les ${n} semaines` : `tous les ${n} ${({ d: "jours", m: "mois", y: "ans" })[u]}`),
    rec_in: (n, u) => u === "y" ? `${n} an${n > 1 ? "s" : ""}` : `${n} ${({ d: "j", w: "sem", m: "mois" })[u]}`,
    subtasks_f: "Sous-tâches", add_subtask: "Ajouter une sous-tâche…", list_name_f: "Nom de la liste",
    delete_task_confirm: "Supprimer cette tâche ?", no_lists: "Pas encore de listes.", empty: "Rien à faire 🎉",
    edit_list: "Modifier la liste", delete_list_confirm: "Supprimer cette liste et toutes ses tâches ?",
    show_filters: "Afficher les filtres", manage_lists: "Modifier les listes",
    clear_done: "Effacer les terminées", clear_done_confirm: "Supprimer toutes les tâches terminées ?",
    reset_filters: "Réinitialiser les filtres",
    type_simple: "Unique", type_scheduled: "Récurrente (plan fixe)",
    type_after: "Récurrente (après achèvement)", type_period: "Tâche hebdo/mensuelle",
    error: "Better ToDo est injoignable. L'intégration est-elle installée ?",
    tags_f: "Tags", tags_ph: "séparés,par,virgules", reminders_f: "Rappels",
    rem_0: "à l'échéance", rem_min: (n) => `${n} min avant`, rem_h: (n) => `${n} h avant`,
    rem_d: (n) => `${n} j avant`, add_reminder: "+ rappel",
    sort_f: "Tri", sort_smart: "Automatique", sort_manual: "Manuel", sort_due: "Échéance",
    sort_prio: "Priorité", sort_title: "Titre", sort_person: "Personne",
    due_soon: (n) => `Bientôt dû (${n} j)`, end_f: "Fin (optionnel)",
    until_f: "Date de fin", max_occ_f: "Répétitions max.",
    monthly_day: (d) => `le ${d}`, monthly_last: "le dernier jour",
    monthly_nth: (n, wd) => `le ${n}e ${wd}`, monthly_nth_last: (wd) => `le dernier ${wd}`,
    confirm_done: (t) => `Terminer « ${t} » ?`,
    logged_in: "Utilisateur connecté", mode_day: "à jour fixe", mode_last: "le dernier jour du mois",
    mode_nth: "le n-ième jour de semaine", day_f: "Jour (1–31)", month_f: "Mois", nth_last: "dernier",
    auto_hint: "vide = automatique selon la règle",
  },
  es: {
    wd: ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"],
    today: "vence hoy", overdue_d: (n) => `${n} d de retraso`, days_left: (n) => `quedan ${n} d`,
    times_due: (n) => `${n}× pendiente`, streak_w: (n) => `racha de ${n} sem`, streak_m: (n) => `racha de ${n} meses`,
    missed_w: (n) => `${n} sem sin hacer`, missed_m: (n) => `${n} meses sin hacer`,
    skipped: "omitida", upcoming: "próxima", done: "Hecho", edit: "Editar", skip: "Omitir",
    delete: "Eliminar", new_task: "Nueva tarea", new_list: "Nueva lista", save: "Guardar", cancel: "Cancelar",
    complete_one: "Completar 1×", complete_all: (n) => `Completar todas (${n})`,
    show_done: "Mostrar completadas", show_upcoming: "Mostrar próximas", all_persons: "Todos",
    title_f: "Título", list_f: "Lista", type_f: "Tipo", notes_f: "Notas",
    due_f: "Fecha límite", first_due_f: "Primera / próxima fecha", visible_from_f: "Visible desde",
    time_f: "Hora", every: "Cada", freq_daily: "día(s)", freq_weekly: "semana(s)",
    freq_monthly: "mes(es)", freq_yearly: "año(s)", after_done: "tras completar",
    lead_f: "Mostrar días antes del vencimiento (vacío = el mismo día)",
    period_f: "Período", week: "Semana", month: "Mes", priority_f: "Prioridad",
    prio_none: "Ninguna", prio_low: "Baja", prio_med: "Media", prio_high: "Alta",
    assigned_f: "Asignada a", nobody: "Nadie", rotate_f: "Rotar", rotate_start_f: "Empezar con",
    rec: (n, u) => n === 1 ? ({ d: "diaria", w: "semanal", m: "mensual", y: "anual" })[u] : `cada ${n} ${({ d: "días", w: "semanas", m: "meses", y: "años" })[u]}`,
    rec_in: (n, u) => `${n} ${({ d: "d", w: "sem", m: n > 1 ? "meses" : "mes", y: n > 1 ? "años" : "año" })[u]}`,
    subtasks_f: "Subtareas", add_subtask: "Añadir subtarea…", list_name_f: "Nombre de la lista",
    delete_task_confirm: "¿Eliminar esta tarea?", no_lists: "Aún no hay listas.", empty: "Nada que hacer 🎉",
    edit_list: "Editar lista", delete_list_confirm: "¿Eliminar esta lista y todas sus tareas?",
    show_filters: "Mostrar filtros", manage_lists: "Editar listas",
    clear_done: "Borrar completadas", clear_done_confirm: "¿Eliminar todas las tareas completadas?",
    reset_filters: "Restablecer filtros",
    type_simple: "Única", type_scheduled: "Recurrente (plan fijo)",
    type_after: "Recurrente (tras completar)", type_period: "Tarea semanal/mensual",
    error: "Better ToDo no responde. ¿Está instalada la integración?",
    tags_f: "Etiquetas", tags_ph: "separadas,por,comas", reminders_f: "Recordatorios",
    rem_0: "al vencer", rem_min: (n) => `${n} min antes`, rem_h: (n) => `${n} h antes`,
    rem_d: (n) => `${n} d antes`, add_reminder: "+ recordatorio",
    sort_f: "Orden", sort_smart: "Automático", sort_manual: "Manual", sort_due: "Vencimiento",
    sort_prio: "Prioridad", sort_title: "Título", sort_person: "Persona",
    due_soon: (n) => `Próximas (${n} d)`, end_f: "Fin (opcional)",
    until_f: "Fecha final", max_occ_f: "Repeticiones máx.",
    monthly_day: (d) => `el día ${d}`, monthly_last: "el último día",
    monthly_nth: (n, wd) => `el ${n}º ${wd}`, monthly_nth_last: (wd) => `el último ${wd}`,
    confirm_done: (t) => `¿Completar "${t}"?`,
    logged_in: "Usuario conectado", mode_day: "en un día fijo", mode_last: "el último día del mes",
    mode_nth: "el n-ésimo día de la semana", day_f: "Día (1–31)", month_f: "Mes", nth_last: "último",
    auto_hint: "vacío = automático según la regla",
  },
  it: {
    wd: ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"],
    today: "scade oggi", overdue_d: (n) => `${n} g di ritardo`, days_left: (n) => `${n} g rimasti`,
    times_due: (n) => `${n}× in scadenza`, streak_w: (n) => `serie di ${n} sett`, streak_m: (n) => `serie di ${n} mesi`,
    missed_w: (n) => `${n} sett saltate`, missed_m: (n) => `${n} mesi saltati`,
    skipped: "saltata", upcoming: "in arrivo", done: "Fatto", edit: "Modifica", skip: "Salta",
    delete: "Elimina", new_task: "Nuova attività", new_list: "Nuova lista", save: "Salva", cancel: "Annulla",
    complete_one: "Completa 1×", complete_all: (n) => `Completa tutte (${n})`,
    show_done: "Mostra completate", show_upcoming: "Mostra future", all_persons: "Tutti",
    title_f: "Titolo", list_f: "Lista", type_f: "Tipo", notes_f: "Note",
    due_f: "Scadenza", first_due_f: "Prima / prossima scadenza", visible_from_f: "Visibile dal",
    time_f: "Ora", every: "Ogni", freq_daily: "giorno/i", freq_weekly: "settimana/e",
    freq_monthly: "mese/i", freq_yearly: "anno/i", after_done: "dopo il completamento",
    lead_f: "Mostra giorni prima della scadenza (vuoto = il giorno stesso)",
    period_f: "Periodo", week: "Settimana", month: "Mese", priority_f: "Priorità",
    prio_none: "Nessuna", prio_low: "Bassa", prio_med: "Media", prio_high: "Alta",
    assigned_f: "Assegnata a", nobody: "Nessuno", rotate_f: "Ruota", rotate_start_f: "Inizia con",
    rec: (n, u) => n === 1 ? ({ d: "giornaliera", w: "settimanale", m: "mensile", y: "annuale" })[u] : `ogni ${n} ${({ d: "giorni", w: "settimane", m: "mesi", y: "anni" })[u]}`,
    rec_in: (n, u) => `${n} ${({ d: "g", w: "sett", m: n > 1 ? "mesi" : "mese", y: n > 1 ? "anni" : "anno" })[u]}`,
    subtasks_f: "Sottoattività", add_subtask: "Aggiungi sottoattività…", list_name_f: "Nome lista",
    delete_task_confirm: "Eliminare questa attività?", no_lists: "Ancora nessuna lista.", empty: "Niente da fare 🎉",
    edit_list: "Modifica lista", delete_list_confirm: "Eliminare questa lista e tutte le sue attività?",
    show_filters: "Mostra filtri", manage_lists: "Modifica liste",
    clear_done: "Rimuovi completate", clear_done_confirm: "Eliminare tutte le attività completate?",
    reset_filters: "Reimposta filtri",
    type_simple: "Singola", type_scheduled: "Ricorrente (piano fisso)",
    type_after: "Ricorrente (dopo completamento)", type_period: "Attività settimanale/mensile",
    error: "Better ToDo non raggiungibile. L'integrazione è installata?",
    tags_f: "Tag", tags_ph: "separati,da,virgole", reminders_f: "Promemoria",
    rem_0: "alla scadenza", rem_min: (n) => `${n} min prima`, rem_h: (n) => `${n} h prima`,
    rem_d: (n) => `${n} g prima`, add_reminder: "+ promemoria",
    sort_f: "Ordinamento", sort_smart: "Automatico", sort_manual: "Manuale", sort_due: "Scadenza",
    sort_prio: "Priorità", sort_title: "Titolo", sort_person: "Persona",
    due_soon: (n) => `In scadenza (${n} g)`, end_f: "Fine (opzionale)",
    until_f: "Data finale", max_occ_f: "Ripetizioni max",
    monthly_day: (d) => `il giorno ${d}`, monthly_last: "l'ultimo giorno",
    monthly_nth: (n, wd) => `il ${n}º ${wd}`, monthly_nth_last: (wd) => `l'ultimo ${wd}`,
    confirm_done: (t) => `Completare "${t}"?`,
    logged_in: "Utente connesso", mode_day: "in un giorno fisso", mode_last: "l'ultimo giorno del mese",
    mode_nth: "l'n-esimo giorno della settimana", day_f: "Giorno (1–31)", month_f: "Mese", nth_last: "ultimo",
    auto_hint: "vuoto = automatico dalla regola",
  },
  nl: {
    wd: ["Ma", "Di", "Wo", "Do", "Vr", "Za", "Zo"],
    today: "vandaag", overdue_d: (n) => `${n} d te laat`, days_left: (n) => `nog ${n} d`,
    times_due: (n) => `${n}× verschuldigd`, streak_w: (n) => `reeks van ${n} wk`, streak_m: (n) => `reeks van ${n} mnd`,
    missed_w: (n) => `${n} wk gemist`, missed_m: (n) => `${n} mnd gemist`,
    skipped: "overgeslagen", upcoming: "binnenkort", done: "Klaar", edit: "Bewerken", skip: "Overslaan",
    delete: "Verwijderen", new_task: "Nieuwe taak", new_list: "Nieuwe lijst", save: "Opslaan", cancel: "Annuleren",
    complete_one: "1× afronden", complete_all: (n) => `Alle ${n} afronden`,
    show_done: "Voltooide tonen", show_upcoming: "Komende tonen", all_persons: "Iedereen",
    title_f: "Titel", list_f: "Lijst", type_f: "Type", notes_f: "Notities",
    due_f: "Vervaldatum", first_due_f: "Eerste / volgende vervaldatum", visible_from_f: "Zichtbaar vanaf",
    time_f: "Tijd", every: "Elke", freq_daily: "dag(en)", freq_weekly: "week/weken",
    freq_monthly: "maand(en)", freq_yearly: "jaar/jaren", after_done: "na afronden",
    lead_f: "Dagen vóór vervaldatum tonen (leeg = op de dag zelf)",
    period_f: "Periode", week: "Week", month: "Maand", priority_f: "Prioriteit",
    prio_none: "Geen", prio_low: "Laag", prio_med: "Middel", prio_high: "Hoog",
    assigned_f: "Toegewezen aan", nobody: "Niemand", rotate_f: "Rouleren", rotate_start_f: "Beginnen met",
    rec: (n, u) => n === 1 ? ({ d: "dagelijks", w: "wekelijks", m: "maandelijks", y: "jaarlijks" })[u] : `elke ${n} ${({ d: "dagen", w: "weken", m: "maanden", y: "jaar" })[u]}`,
    rec_in: (n, u) => `${n} ${({ d: "d", w: "wk", m: "mnd", y: "jr" })[u]}`,
    subtasks_f: "Subtaken", add_subtask: "Subtaak toevoegen…", list_name_f: "Lijstnaam",
    delete_task_confirm: "Deze taak verwijderen?", no_lists: "Nog geen lijsten.", empty: "Niets te doen 🎉",
    edit_list: "Lijst bewerken", delete_list_confirm: "Deze lijst en al haar taken verwijderen?",
    show_filters: "Filters tonen", manage_lists: "Lijsten bewerken",
    clear_done: "Voltooide opruimen", clear_done_confirm: "Alle voltooide taken verwijderen?",
    reset_filters: "Filters herstellen",
    type_simple: "Eenmalig", type_scheduled: "Terugkerend (vast schema)",
    type_after: "Terugkerend (na afronden)", type_period: "Week-/maandtaak",
    error: "Better ToDo is niet bereikbaar. Is de integratie geïnstalleerd?",
    tags_f: "Tags", tags_ph: "komma,gescheiden", reminders_f: "Herinneringen",
    rem_0: "op vervalmoment", rem_min: (n) => `${n} min eerder`, rem_h: (n) => `${n} u eerder`,
    rem_d: (n) => `${n} d eerder`, add_reminder: "+ herinnering",
    sort_f: "Sortering", sort_smart: "Automatisch", sort_manual: "Handmatig", sort_due: "Vervaldatum",
    sort_prio: "Prioriteit", sort_title: "Titel", sort_person: "Persoon",
    due_soon: (n) => `Binnenkort (${n} d)`, end_f: "Einde (optioneel)",
    until_f: "Einddatum", max_occ_f: "Max. herhalingen",
    monthly_day: (d) => `op dag ${d}`, monthly_last: "op de laatste dag",
    monthly_nth: (n, wd) => `op de ${n}e ${wd}`, monthly_nth_last: (wd) => `op de laatste ${wd}`,
    confirm_done: (t) => `"${t}" afronden?`,
    logged_in: "Ingelogde gebruiker", mode_day: "op een vaste dag", mode_last: "op de laatste dag van de maand",
    mode_nth: "op de n-de weekdag", day_f: "Dag (1–31)", month_f: "Maand", nth_last: "laatste",
    auto_hint: "leeg = automatisch volgens regel",
  },
  pl: {
    wd: ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Nd"],
    today: "termin dziś", overdue_d: (n) => `${n} dni po terminie`, days_left: (n) => `zostało ${n} dni`,
    times_due: (n) => `${n}× zaległe`, streak_w: (n) => `seria ${n} tyg`, streak_m: (n) => `seria ${n} mies`,
    missed_w: (n) => `${n} tyg pominięte`, missed_m: (n) => `${n} mies pominięte`,
    skipped: "pominięte", upcoming: "nadchodzące", done: "Gotowe", edit: "Edytuj", skip: "Pomiń",
    delete: "Usuń", new_task: "Nowe zadanie", new_list: "Nowa lista", save: "Zapisz", cancel: "Anuluj",
    complete_one: "Ukończ 1×", complete_all: (n) => `Ukończ wszystkie (${n})`,
    show_done: "Pokaż ukończone", show_upcoming: "Pokaż nadchodzące", all_persons: "Wszyscy",
    title_f: "Tytuł", list_f: "Lista", type_f: "Typ", notes_f: "Notatki",
    due_f: "Termin", first_due_f: "Pierwszy / następny termin", visible_from_f: "Widoczne od",
    time_f: "Godzina", every: "Co", freq_daily: "dzień/dni", freq_weekly: "tydzień/tygodnie",
    freq_monthly: "miesiąc(e)", freq_yearly: "rok/lata", after_done: "po ukończeniu",
    lead_f: "Pokaż dni przed terminem (puste = w dniu terminu)",
    period_f: "Okres", week: "Tydzień", month: "Miesiąc", priority_f: "Priorytet",
    prio_none: "Brak", prio_low: "Niski", prio_med: "Średni", prio_high: "Wysoki",
    assigned_f: "Przypisane do", nobody: "Nikt", rotate_f: "Rotacja", rotate_start_f: "Zacznij od",
    rec: (n, u) => n === 1 ? ({ d: "codziennie", w: "co tydzień", m: "co miesiąc", y: "co rok" })[u] : `co ${n} ${({ d: "dni", w: "tyg.", m: "mies.", y: "lat" })[u]}`,
    rec_in: (n, u) => `${n} ${({ d: "dni", w: "tyg.", m: "mies.", y: "lat" })[u]}`,
    subtasks_f: "Podzadania", add_subtask: "Dodaj podzadanie…", list_name_f: "Nazwa listy",
    delete_task_confirm: "Usunąć to zadanie?", no_lists: "Brak list.", empty: "Nic do zrobienia 🎉",
    edit_list: "Edytuj listę", delete_list_confirm: "Usunąć tę listę i wszystkie jej zadania?",
    show_filters: "Pokaż filtry", manage_lists: "Edytuj listy",
    clear_done: "Wyczyść ukończone", clear_done_confirm: "Usunąć wszystkie ukończone zadania?",
    reset_filters: "Resetuj filtry",
    type_simple: "Jednorazowe", type_scheduled: "Cykliczne (stały plan)",
    type_after: "Cykliczne (po ukończeniu)", type_period: "Zadanie tygodniowe/miesięczne",
    error: "Better ToDo jest niedostępne. Czy integracja jest zainstalowana?",
    tags_f: "Tagi", tags_ph: "oddzielone,przecinkami", reminders_f: "Przypomnienia",
    rem_0: "w terminie", rem_min: (n) => `${n} min przed`, rem_h: (n) => `${n} godz przed`,
    rem_d: (n) => `${n} dni przed`, add_reminder: "+ przypomnienie",
    sort_f: "Sortowanie", sort_smart: "Automatyczne", sort_manual: "Ręczne", sort_due: "Termin",
    sort_prio: "Priorytet", sort_title: "Tytuł", sort_person: "Osoba",
    due_soon: (n) => `Wkrótce (${n} dni)`, end_f: "Koniec (opcjonalnie)",
    until_f: "Data końcowa", max_occ_f: "Maks. powtórzeń",
    monthly_day: (d) => `${d}. dnia`, monthly_last: "ostatniego dnia",
    monthly_nth: (n, wd) => `${n}. ${wd}`, monthly_nth_last: (wd) => `ostatni ${wd}`,
    confirm_done: (t) => `Ukończyć „${t}"?`,
    logged_in: "Zalogowany użytkownik", mode_day: "w stały dzień", mode_last: "ostatniego dnia miesiąca",
    mode_nth: "w n-ty dzień tygodnia", day_f: "Dzień (1–31)", month_f: "Miesiąc", nth_last: "ostatni",
    auto_hint: "puste = automatycznie z reguły",
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

const REMINDER_PRESETS = [0, 30, 60, 120, 1440, 2880, 10080];

function remLabel(t, minutes) {
  if (minutes === 0) return t.rem_0;
  if (minutes < 60) return t.rem_min(minutes);
  if (minutes < 1440) return t.rem_h(Math.round(minutes / 60));
  return t.rem_d(Math.round(minutes / 1440));
}

const toIso = (d) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

function nextRuleDate(s) {
  // First occurrence (>= today) matching a schedule rule — mirrors engine.py.
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const clampDay = (y, m, day) => {
    const last = new Date(y, m + 1, 0).getDate();
    return new Date(y, m, Math.min(day, last));
  };
  const nthDate = (y, m, n, wd) => {
    if (n === -1) {
      const last = new Date(y, m + 1, 0);
      const diff = (((last.getDay() + 6) % 7) - wd + 7) % 7;
      return new Date(y, m, last.getDate() - diff);
    }
    const first = new Date(y, m, 1);
    const off = (wd - ((first.getDay() + 6) % 7) + 7) % 7;
    return new Date(y, m, 1 + off + (n - 1) * 7);
  };
  if (s.freq === "weekly") {
    const wds = s.weekdays && s.weekdays.length ? s.weekdays : [(today.getDay() + 6) % 7];
    for (let i = 0; i < 14; i++) {
      const d = new Date(today);
      d.setDate(d.getDate() + i);
      if (wds.includes((d.getDay() + 6) % 7)) return d;
    }
  }
  if (s.freq === "monthly") {
    for (let k = 0; k < 24; k++) {
      const probe = new Date(today.getFullYear(), today.getMonth() + k, 1);
      const y = probe.getFullYear();
      const m = probe.getMonth();
      let d;
      if (s.nth) d = nthDate(y, m, s.nth.n, s.nth.weekday);
      else if (s.day === "last") d = new Date(y, m + 1, 0);
      else d = clampDay(y, m, Number(s.day) || 1);
      if (d >= today) return d;
    }
  }
  if (s.freq === "yearly") {
    for (let k = 0; k < 3; k++) {
      const y = today.getFullYear() + k;
      const m = (Number(s.month) || today.getMonth() + 1) - 1;
      const d = s.day === "last" ? new Date(y, m + 1, 0) : clampDay(y, m, Number(s.day) || 1);
      if (d >= today) return d;
    }
  }
  return today;
}

function pickLang(hass) {
  const lang = (hass?.locale?.language || "en").toLowerCase().slice(0, 2);
  return STR[lang] || STR.en;
}

class BetterTodoCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._data = null;
    this._error = null;
    this._sub = null;
    this._ui = {
      menu: false, dropdown: false, expanded: null, lists: null, person: null,
      showDone: null, showUpcoming: null, tags: null, dueSoon: false, sort: null,
    };
    this._dialog = null;
    this._dialogEl = null;
    this._drag = null;
    // Delegated listeners are attached ONCE here — the shadow root element
    // survives innerHTML swaps, so attaching them per render would stack
    // duplicate handlers and eventually freeze the page.
    this.shadowRoot.addEventListener("click", (e) => this._onClick(e));
    this.shadowRoot.addEventListener("change", (e) => this._onChange(e));
    this.shadowRoot.addEventListener("dragstart", (e) => this._onDragStart(e));
    this.shadowRoot.addEventListener("dragover", (e) => this._onDragOver(e));
    this.shadowRoot.addEventListener("drop", (e) => this._onDrop(e));
  }

  setConfig(config) {
    this._config = {
      title: null, lists: null, assigned: "all", sort: "smart",
      show_menu: true, show_add: true, show_completed: false, show_upcoming: false,
      compact: false, max_height: null, confirm_complete: false, due_soon_days: 7,
      ...config,
    };
  }

  static getStubConfig() {
    return { show_menu: true, show_add: true };
  }

  static getConfigElement() {
    return document.createElement("better-todo-card-editor");
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

  get t() { return pickLang(this._hass); }

  async _connect() {
    if (this._connecting) return;
    this._connecting = true;
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
    this._connecting = false;
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
  _sortMode() { return this._ui.sort ?? this._config.sort ?? "smart"; }

  _recurLabel(task) {
    const t = this.t;
    if (task.type === "scheduled") {
      const s = task.schedule || {};
      const u = { daily: "d", weekly: "w", monthly: "m", yearly: "y" }[s.freq] || "m";
      return t.rec(Number(s.interval) || 1, u);
    }
    const iv = task.interval || {};
    const u = { days: "d", weeks: "w", months: "m", years: "y" }[iv.unit] || "w";
    return `${t.rec_in(Number(iv.value) || 1, u)} ${t.after_done}`;
  }

  _knownTags() {
    // Every tag in the data set, regardless of visibility — used to offer
    // existing tags for reuse in the task dialog.
    const tags = new Set();
    for (const task of this._data?.tasks || []) (task.tags || []).forEach((x) => tags.add(x));
    return [...tags].sort();
  }

  _filtersActive() {
    const u = this._ui;
    return !!(u.lists || u.person !== null || (u.tags && u.tags.length)
      || u.dueSoon || u.sort || u.showDone !== null || u.showUpcoming !== null);
  }

  _allTags() {
    // Same visibility rules as _visibleTasks, minus the tag filter itself:
    // chips only offer tags the current view can actually match. Selected
    // tags stay listed so they can be deselected.
    const personFilter = this._personFilter();
    const activeIds = this._activeLists().map((l) => l.id);
    const tags = new Set(this._ui.tags || []);
    for (const task of this._data?.tasks || []) {
      if (!activeIds.includes(task.list_id)) continue;
      const s = task.computed?.state;
      if (s === "done" && !this._showDone()) continue;
      if (s === "hidden" && !this._showUpcoming()) continue;
      if (s === "upcoming" && !(task.computed.visible || this._showUpcoming())) continue;
      if (personFilter && personFilter !== "all" && !(task.assigned_to || []).includes(personFilter)) continue;
      if (this._ui.dueSoon && !this._dueWithin(task, this._config.due_soon_days ?? 7)) continue;
      (task.tags || []).forEach((x) => tags.add(x));
    }
    return [...tags].sort();
  }

  _dueWithin(task, days) {
    const c = task.computed || {};
    if (["overdue", "due", "period_open"].includes(c.state)) return true;
    if (!c.due) return false;
    const diff = (new Date(c.due + "T00:00:00") - new Date(new Date().toDateString())) / 86400000;
    return diff <= days;
  }

  _visibleTasks(listId) {
    const personFilter = this._personFilter();
    const tagFilter = this._ui.tags;
    const sort = this._sortMode();
    let tasks = (this._data?.tasks || [])
      .filter((t) => t.list_id === listId)
      .filter((t) => {
        const s = t.computed?.state;
        if (s === "done") return this._showDone();
        if (s === "hidden") return this._showUpcoming();
        if (s === "upcoming") return t.computed.visible || this._showUpcoming();
        return true;
      })
      .filter((t) => personFilter === "all" || !personFilter ? true : (t.assigned_to || []).includes(personFilter));
    if (tagFilter && tagFilter.length) {
      tasks = tasks.filter((t) => (t.tags || []).some((x) => tagFilter.includes(x)));
    }
    if (this._ui.dueSoon) {
      tasks = tasks.filter((t) => this._dueWithin(t, this._config.due_soon_days ?? 7));
    }
    const doneRank = (t) => (["done", "period_done"].includes(t.computed?.state) ? 1 : 0);
    return tasks.sort((a, b) => {
      const dr = doneRank(a) - doneRank(b);
      if (dr !== 0) return dr;
      if (sort === "manual") return (a.order || 0) - (b.order || 0);
      if (sort === "due") return (a.computed?.due || "9999") < (b.computed?.due || "9999") ? -1 : 1;
      if (sort === "priority") return (a.priority || 99) - (b.priority || 99);
      if (sort === "title") return a.title.localeCompare(b.title);
      if (sort === "person") {
        const pa = this._person((a.assigned_to || [])[0])?.name || "zzz";
        const pb = this._person((b.assigned_to || [])[0])?.name || "zzz";
        return pa.localeCompare(pb);
      }
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
    if (this._dialog) return;
    const t = this.t;
    let body;
    if (this._error) {
      body = `<div class="empty">${esc(t.error)}</div>`;
    } else if (!this._data) {
      body = `<div class="empty">…</div>`;
    } else {
      body = this._renderBody();
    }
    const maxH = this._config.max_height ? `style="max-height:${Number(this._config.max_height)}px;overflow-y:auto"` : "";
    this.shadowRoot.innerHTML = `<style>${this._css()}</style>
      <ha-card class="${this._config.compact ? "compact" : ""}">
        ${this._renderHeader()}
        <div class="body" ${maxH}>${body}</div>
      </ha-card>`;
  }

  _renderHeader() {
    const t = this.t;
    if (!this._data) return "";
    const title = this._config.title;
    if (!title && !this._config.show_add && !this._config.show_menu) return "";
    return `<div class="head">
      <div class="head-title">${title ? esc(title) : ""}</div>
      <div class="head-actions">
        ${this._config.show_add ? `<button class="icon-btn" data-action="add" title="${esc(t.new_task)}">+</button>` : ""}
        ${this._config.show_menu ? `<div class="menu-anchor">
          <button class="icon-btn ${this._ui.dropdown ? "active" : ""}" data-action="menu" title="Menu">☰</button>
          ${this._ui.dropdown ? `<div class="dropdown">
            <button class="dd-item" data-action="dd-filters">${this._ui.menu ? "✓ " : ""}${esc(t.show_filters)}</button>
            <button class="dd-item" data-action="dd-lists">${esc(t.manage_lists)}</button>
            <button class="dd-item" data-action="dd-clear">${esc(t.clear_done)}</button>
            ${this._filtersActive() ? `<button class="dd-item" data-action="dd-reset">${esc(t.reset_filters)}</button>` : ""}
          </div>` : ""}
        </div>` : ""}
      </div>
    </div>${this._ui.menu ? this._renderMenu() : ""}`;
  }

  _renderMenu() {
    const t = this.t;
    const all = this._data.lists || [];
    const active = this._activeLists().map((l) => l.id);
    const personFilter = this._personFilter();
    const persons = this._data.persons || [];
    const tags = this._feature("tags") ? this._allTags() : [];
    const selTags = this._ui.tags || [];
    const sort = this._sortMode();
    return `<div class="menu">
      <div class="chips">
        ${all.map((l) => `<button class="chip ${active.includes(l.id) ? "on" : ""}" data-action="toggle-list" data-id="${esc(l.id)}">${esc(l.name)}</button>`).join("")}
        <button class="chip ghost" data-action="add-list">+ ${esc(t.new_list)}</button>
      </div>
      ${tags.length ? `<div class="chips">
        ${tags.map((x) => `<button class="chip tagchip ${selTags.includes(x) ? "on" : ""}" data-action="toggle-tag" data-id="${esc(x)}">#${esc(x)}</button>`).join("")}
      </div>` : ""}
      <div class="menu-row selects">
        ${this._feature("assignment") && persons.length ? `<select data-action="person-filter">
          <option value="all" ${personFilter === "all" ? "selected" : ""}>${esc(t.all_persons)}</option>
          ${persons.map((p) => `<option value="${esc(p.entity_id)}" ${personFilter === p.entity_id ? "selected" : ""}>${esc(p.name)}</option>`).join("")}
        </select>` : ""}
        <select data-action="sort">
          ${[["smart", t.sort_smart], ["manual", t.sort_manual], ["due", t.sort_due], ["priority", t.sort_prio], ["title", t.sort_title], ["person", t.sort_person]]
            .map(([v, label]) => `<option value="${v}" ${sort === v ? "selected" : ""}>${esc(t.sort_f)}: ${esc(label)}</option>`).join("")}
        </select>
      </div>
      <div class="menu-row toggles">
        <label><input type="checkbox" data-action="show-done" ${this._showDone() ? "checked" : ""}> ${esc(t.show_done)}</label>
        <label><input type="checkbox" data-action="show-upcoming" ${this._showUpcoming() ? "checked" : ""}> ${esc(t.show_upcoming)}</label>
        <label><input type="checkbox" data-action="due-soon" ${this._ui.dueSoon ? "checked" : ""}> ${esc(t.due_soon(this._config.due_soon_days ?? 7))}</label>
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
      html += `<div class="list-block" data-list="${esc(list.id)}">`;
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
    const timeSuffix = task.due_time ? ` · ${esc(task.due_time)}` : "";

    if (s === "overdue" && c.due_count > 1) badges.push(`<span class="badge err">${esc(t.times_due(c.due_count))}</span>`);
    if (s === "overdue") badges.push(`<span class="badge err">${esc(t.overdue_d(c.days_overdue))}</span>`);
    if (s === "due") badges.push(`<span class="badge warn">${esc(t.today)}${timeSuffix}</span>`);
    if (s === "open" && c.days_left !== undefined) {
      const cls = c.days_left <= 7 ? "warn" : "";
      badges.push(`<span class="badge ${cls}">${esc(t.days_left(c.days_left))}${timeSuffix}</span>`);
    }
    if ((s === "upcoming" || s === "hidden") && (c.due || c.visible_from)) {
      badges.push(`<span class="badge dim">${esc(t.upcoming)} · ${esc(this._fmtDate(c.due || c.visible_from))}${timeSuffix}</span>`);
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
    if (this._feature("tags")) {
      for (const tag of task.tags || []) badges.push(`<span class="badge tag">#${esc(tag)}</span>`);
    }
    if (this._feature("assignment")) {
      for (const pid of task.assigned_to || []) {
        const p = this._person(pid);
        if (p) badges.push(`<span class="badge person">${esc(p.name)}${task.rotation ? " ⟳" : ""}</span>`);
      }
    }
    if ((task.reminders || []).length) badges.push(`<span class="badge dim">🔔</span>`);
    const recurring = task.type === "scheduled" || task.type === "after_completion";
    if (recurring) badges.push(`<span class="badge dim">🔁 ${esc(this._recurLabel(task))}</span>`);

    const draggable = this._sortMode() === "manual" && !doneish;
    return `<div class="task ${doneish ? "done" : ""} ${s === "overdue" ? "overdue" : ""}" data-id="${esc(task.id)}" data-list="${esc(task.list_id)}" ${draggable ? 'draggable="true"' : ""}>
      <div class="row" data-action="expand" data-id="${esc(task.id)}">
        ${draggable ? `<span class="grip">⋮⋮</span>` : ""}
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
    if (this._ui.dropdown && !e.target.closest(".menu-anchor")) {
      this._ui.dropdown = false;
      this._render();
    }
    if (!el) return;
    const action = el.dataset.action;
    const id = el.dataset.id;
    if (action === "subtask") return;
    e.stopPropagation();
    if (action === "menu") { this._ui.dropdown = !this._ui.dropdown; this._render(); }
    else if (action === "dd-filters") { this._ui.menu = !this._ui.menu; this._ui.dropdown = false; this._render(); }
    else if (action === "dd-lists") { this._ui.dropdown = false; this._render(); this._openManageLists(); }
    else if (action === "dd-clear") {
      this._ui.dropdown = false;
      this._render();
      if (confirm(this.t.clear_done_confirm)) {
        this._ws({ type: "better_todo/clear_completed", list_ids: this._activeLists().map((l) => l.id) });
      }
    }
    else if (action === "dd-reset") {
      Object.assign(this._ui, {
        lists: null, person: null, tags: null, dueSoon: false, sort: null,
        showDone: null, showUpcoming: null, dropdown: false,
      });
      this._render();
    }
    else if (action === "toggle-list") this._toggleListFilter(id);
    else if (action === "toggle-tag") this._toggleTagFilter(id);
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
    else if (action === "sort") { this._ui.sort = el.value; this._render(); }
    else if (action === "show-done") { this._ui.showDone = el.checked; this._render(); }
    else if (action === "show-upcoming") { this._ui.showUpcoming = el.checked; this._render(); }
    else if (action === "due-soon") { this._ui.dueSoon = el.checked; this._render(); }
  }

  _onDragStart(e) {
    const row = e.target.closest?.(".task[draggable]");
    if (!row) return;
    this._drag = { id: row.dataset.id, listId: row.dataset.list };
    e.dataTransfer.effectAllowed = "move";
  }

  _onDragOver(e) {
    if (!this._drag) return;
    const row = e.target.closest?.(".task");
    if (row && row.dataset.list === this._drag.listId) e.preventDefault();
  }

  _onDrop(e) {
    if (!this._drag) return;
    const row = e.target.closest?.(".task");
    const drag = this._drag;
    this._drag = null;
    if (!row || row.dataset.list !== drag.listId || row.dataset.id === drag.id) return;
    e.preventDefault();
    const visible = this._visibleTasks(drag.listId).map((x) => x.id);
    const from = visible.indexOf(drag.id);
    const to = visible.indexOf(row.dataset.id);
    if (from < 0 || to < 0) return;
    visible.splice(to, 0, visible.splice(from, 1)[0]);
    const rest = (this._data.tasks || [])
      .filter((x) => x.list_id === drag.listId && !visible.includes(x.id))
      .sort((a, b) => (a.order || 0) - (b.order || 0))
      .map((x) => x.id);
    this._ws({ type: "better_todo/reorder", list_id: drag.listId, task_ids: [...visible, ...rest] });
  }

  _toggleListFilter(id) {
    const all = (this._data.lists || []).map((l) => l.id);
    let cur = this._ui.lists || this._activeLists().map((l) => l.id);
    cur = cur.includes(id) ? cur.filter((x) => x !== id) : [...cur, id];
    this._ui.lists = cur.length ? cur : null;
    if (cur.length === all.length) this._ui.lists = null;
    this._render();
  }

  _toggleTagFilter(tag) {
    let cur = this._ui.tags || [];
    cur = cur.includes(tag) ? cur.filter((x) => x !== tag) : [...cur, tag];
    this._ui.tags = cur.length ? cur : null;
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
    if (this._config.confirm_complete && !confirm(this.t.confirm_done(task.title))) return;
    this._ws({ type: "better_todo/complete_task", task_id: id, all: true });
  }

  // ------------------------------------------------------------- dialogs

  _showDialog(innerHtml, onWire) {
    const old = this.shadowRoot.querySelector("dialog");
    if (old) old.remove();
    const dlg = document.createElement("dialog");
    dlg.innerHTML = innerHtml;
    this.shadowRoot.appendChild(dlg);
    this._dialogEl = dlg;
    // No backdrop-click close: dialogs only close via their buttons, so a
    // stray click next to the dialog cannot discard unsaved edits.
    // The close event fires async; ignore it if another dialog has been
    // opened in the meantime (close → immediately open follow-up dialog).
    dlg.addEventListener("close", () => {
      if (this._dialogEl !== dlg) return;
      this._dialogEl = null;
      if (this._dialog) { this._dialog = null; this._render(); }
    });
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
      `<div class="dlg-title">${esc(list ? t.edit_list : t.new_list)}</div>
       <label class="field">${esc(t.list_name_f)}<input type="text" id="lname" value="${esc(list?.name || "")}"></label>
       <div class="dlg-actions">
         <button class="btn primary" data-x="save">${esc(t.save)}</button>
         ${list ? `<button class="btn danger" data-x="delete">${esc(t.delete)}</button>` : ""}
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
          } else if (b.dataset.x === "delete") {
            if (!confirm(t.delete_list_confirm)) return;
            await this._ws({ type: "better_todo/delete_list", list_id: list.id });
          }
          dlg.close();
        });
      }
    );
  }

  _openManageLists() {
    const t = this.t;
    this._dialog = { kind: "lists" };
    const lists = this._data?.lists || [];
    this._showDialog(
      `<div class="dlg-title">${esc(t.manage_lists)}</div>
       <div class="list-manage">
         ${lists.map((l) => `<button class="btn list-row" data-x="edit" data-id="${esc(l.id)}"><span>${esc(l.name)}</span><span class="row-edit">✎</span></button>`).join("")}
       </div>
       <div class="dlg-actions">
         <button class="btn" data-x="new">+ ${esc(t.new_list)}</button>
         <button class="btn ghost" data-x="cancel">${esc(t.cancel)}</button>
       </div>`,
      (dlg) => {
        dlg.addEventListener("click", (e) => {
          const b = e.target.closest("[data-x]");
          if (!b) return;
          if (b.dataset.x === "edit") {
            const list = (this._data?.lists || []).find((l) => l.id === b.dataset.id);
            dlg.close();
            this._openListDialog(list);
          } else if (b.dataset.x === "new") {
            dlg.close();
            this._openListDialog(null);
          } else {
            dlg.close();
          }
        });
      }
    );
  }

  _openTaskDialog(task) {
    const draft = task
      ? JSON.parse(JSON.stringify(task))
      : {
          list_id: this._activeLists()[0]?.id || this._data.lists[0]?.id,
          title: "", notes: "", type: "simple", due_date: null, due_time: null,
          visible_from: null, lead_days: null, priority: null, subtasks: [],
          assigned_to: [], rotation: null, tags: [], reminders: [],
          schedule: { freq: "monthly", interval: 1 }, interval: { unit: "weeks", value: 1 },
          period: "week",
        };
    if (!Array.isArray(draft.assigned_to)) draft.assigned_to = draft.assigned_to ? [draft.assigned_to] : [];
    // Working state for the assignment UI: _persons is the selected pool
    // (with rotation, assigned_to holds only the current person).
    draft._persons = draft.rotation?.persons ? [...draft.rotation.persons] : [...draft.assigned_to];
    draft._rotate = !!(draft.rotation && (draft.rotation.persons || []).length);
    draft._rotate_start = draft._rotate
      ? draft.rotation.persons[draft.rotation.index || 0] || draft._persons[0]
      : null;
    if (!draft.schedule) draft.schedule = { freq: "monthly", interval: 1 };
    if (!draft.interval) draft.interval = { unit: "weeks", value: 1 };
    if (!draft.period) draft.period = "week";
    // Editable rule fields, prefilled from an existing schedule.
    const s = draft.schedule;
    const now = new Date();
    draft._mMode = s.nth ? "nth" : (s.day === "last" ? "last" : "day");
    draft._mDay = s.day && s.day !== "last" ? Number(s.day) : now.getDate();
    draft._mNthN = s.nth ? Number(s.nth.n) : 1;
    draft._mNthWd = s.nth ? Number(s.nth.weekday) : (now.getDay() + 6) % 7;
    draft._yMonth = Number(s.month) || now.getMonth() + 1;
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
    const hasDue = d.type !== "period";

    let typeFields = "";
    if (d.type === "simple") {
      typeFields = `
        <div class="field-row2">
          <label class="field grow">${esc(t.due_f)}<input type="date" data-f="due_date" value="${esc(d.due_date || "")}"></label>
          <label class="field">${esc(t.time_f)}<input type="time" data-f="due_time" value="${esc(d.due_time || "")}"></label>
        </div>
        <label class="field">${esc(t.visible_from_f)}<input type="date" data-f="visible_from" value="${esc(d.visible_from || "")}"></label>`;
    } else if (d.type === "scheduled") {
      const freq = d.schedule.freq;
      const weekdaysSel = d.schedule.weekdays || [];
      const lang = this._hass?.locale?.language || "en";
      const monthName = (m) => new Date(2000, m - 1, 1).toLocaleDateString(lang, { month: "long" });
      let ruleFields = "";
      if (freq === "weekly") {
        ruleFields = `<div class="field"><div class="wd-row">${t.wd.map((label, i) =>
          `<label class="wd"><input type="checkbox" data-wd="${i}" ${weekdaysSel.includes(i) ? "checked" : ""}>${esc(label)}</label>`).join("")}</div></div>`;
      } else if (freq === "monthly") {
        ruleFields = `
          <div class="field-row">
            <select data-f="_mMode" data-rebuild="1">
              <option value="day" ${d._mMode === "day" ? "selected" : ""}>${esc(t.mode_day)}</option>
              <option value="last" ${d._mMode === "last" ? "selected" : ""}>${esc(t.mode_last)}</option>
              <option value="nth" ${d._mMode === "nth" ? "selected" : ""}>${esc(t.mode_nth)}</option>
            </select>
            ${d._mMode === "day" ? `<input type="number" min="1" max="31" class="num" data-f="_mDay" value="${esc(d._mDay)}" title="${esc(t.day_f)}">` : ""}
            ${d._mMode === "nth" ? `
              <select data-f="_mNthN">
                ${[1, 2, 3, 4].map((n) => `<option value="${n}" ${d._mNthN === n ? "selected" : ""}>${n}.</option>`).join("")}
                <option value="-1" ${d._mNthN === -1 ? "selected" : ""}>${esc(t.nth_last)}</option>
              </select>
              <select data-f="_mNthWd">
                ${t.wd.map((label, i) => `<option value="${i}" ${d._mNthWd === i ? "selected" : ""}>${esc(label)}</option>`).join("")}
              </select>` : ""}
          </div>`;
      } else if (freq === "yearly") {
        ruleFields = `
          <div class="field-row">
            <span>${esc(t.day_f)}</span>
            <input type="number" min="1" max="31" class="num" data-f="_mDay" value="${esc(d._mDay)}">
            <select data-f="_yMonth">
              ${Array.from({ length: 12 }, (_, i) => i + 1).map((m) =>
                `<option value="${m}" ${d._yMonth === m ? "selected" : ""}>${esc(monthName(m))}</option>`).join("")}
            </select>
          </div>`;
      }
      typeFields = `
        <div class="field-row">
          <span>${esc(t.every)}</span>
          <input type="number" min="1" class="num" data-f="schedule.interval" value="${esc(d.schedule.interval || 1)}">
          <select data-f="schedule.freq" data-rebuild="1">
            <option value="daily" ${freq === "daily" ? "selected" : ""}>${esc(t.freq_daily)}</option>
            <option value="weekly" ${freq === "weekly" ? "selected" : ""}>${esc(t.freq_weekly)}</option>
            <option value="monthly" ${freq === "monthly" ? "selected" : ""}>${esc(t.freq_monthly)}</option>
            <option value="yearly" ${freq === "yearly" ? "selected" : ""}>${esc(t.freq_yearly)}</option>
          </select>
        </div>
        ${ruleFields}
        <div class="field-row2">
          <label class="field grow">${esc(t.first_due_f)} <span class="hint">(${esc(t.auto_hint)})</span><input type="date" data-f="due_date" value="${esc(d.due_date || "")}"></label>
          <label class="field">${esc(t.time_f)}<input type="time" data-f="due_time" value="${esc(d.due_time || "")}"></label>
        </div>
        <label class="field">${esc(t.lead_f)}<input type="number" min="0" data-f="lead_days" value="${d.lead_days ?? ""}"></label>
        <details class="endblock" ${d.schedule.until || d.schedule.max_occurrences ? "open" : ""}>
          <summary>${esc(t.end_f)}</summary>
          <div class="field-row2">
            <label class="field grow">${esc(t.until_f)}<input type="date" data-f="schedule.until" value="${esc(d.schedule.until || "")}"></label>
            <label class="field">${esc(t.max_occ_f)}<input type="number" min="1" data-f="schedule.max_occurrences" value="${d.schedule.max_occurrences ?? ""}"></label>
          </div>
        </details>`;
    } else if (d.type === "after_completion") {
      typeFields = `
        <div class="field-row2">
          <label class="field grow">${esc(t.first_due_f)}<input type="date" data-f="due_date" value="${esc(d.due_date || "")}" required></label>
          <label class="field">${esc(t.time_f)}<input type="time" data-f="due_time" value="${esc(d.due_time || "")}"></label>
        </div>
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
      ${hasDue ? `<div class="field">
        <span>${esc(t.reminders_f)}</span>
        <div class="chips">${(d.reminders || []).map((m, i) => `<button class="chip on" data-remdel="${i}">🔔 ${esc(remLabel(t, m))} ×</button>`).join("")}
          ${(d.reminders || []).length < 5 ? `<select class="chip-select" data-x="addrem">
            <option value="">${esc(t.add_reminder)}</option>
            ${REMINDER_PRESETS.filter((m) => !(d.reminders || []).includes(m)).map((m) => `<option value="${m}">${esc(remLabel(t, m))}</option>`).join("")}
          </select>` : ""}
        </div>
      </div>` : ""}
      <label class="field">${esc(t.notes_f)}<textarea data-f="notes" rows="2">${esc(d.notes || "")}</textarea></label>
      ${this._feature("tags") ? (() => {
        const known = this._knownTags();
        return `<label class="field">${esc(t.tags_f)}<input type="text" data-f="_tags" placeholder="${esc(t.tags_ph)}" value="${esc((d.tags || []).join(", "))}"></label>
        ${known.length ? `<div class="chips tagpick">${known.map((x) => `<button type="button" class="chip tagchip ${(d.tags || []).includes(x) ? "on" : ""}" data-tagpick="${esc(x)}">#${esc(x)}</button>`).join("")}</div>` : ""}`;
      })() : ""}
      ${this._feature("priorities") ? `<label class="field">${esc(t.priority_f)}
        <select data-f="priority">
          <option value="" ${!d.priority ? "selected" : ""}>${esc(t.prio_none)}</option>
          <option value="1" ${d.priority === 1 ? "selected" : ""}>${esc(t.prio_high)}</option>
          <option value="2" ${d.priority === 2 ? "selected" : ""}>${esc(t.prio_med)}</option>
          <option value="3" ${d.priority === 3 ? "selected" : ""}>${esc(t.prio_low)}</option>
        </select></label>` : ""}
      ${this._feature("assignment") && persons.length ? `<div class="field">
        <span>${esc(t.assigned_f)}</span>
        <div class="chips tagpick">${persons.map((p) => `<button type="button" class="chip tagchip ${(d._persons || []).includes(p.entity_id) ? "on" : ""}" data-personpick="${esc(p.entity_id)}">${esc(p.name)}</button>`).join("")}</div>
      </div>` : ""}
      ${this._feature("rotation") && d.type !== "simple" && (d._persons || []).length >= 2 ? `<div class="field">
        <label class="rot"><input type="checkbox" data-x="rotate" ${d._rotate ? "checked" : ""}> ${esc(t.rotate_f)}</label>
        ${d._rotate ? `<label class="field">${esc(t.rotate_start_f)}
          <select data-f="_rotate_start">
            ${d._persons.map((pid) => `<option value="${esc(pid)}" ${(d._rotate_start || d._persons[0]) === pid ? "selected" : ""}>${esc(this._person(pid)?.name || pid)}</option>`).join("")}
          </select></label>` : ""}
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
      if (["due_date", "visible_from", "due_time", "schedule.until"].includes(f) && v === "") v = null;
      if (f === "_tags") {
        d.tags = v.split(",").map((x) => x.trim()).filter(Boolean);
        return;
      }
      setPath(f, v);
      if (e.target.dataset.rebuild) this._renderTaskDialog();
    });
    dlg.addEventListener("change", (e) => {
      if (e.target.dataset.x === "rotate") {
        d._rotate = e.target.checked;
        if (d._rotate && !d._rotate_start) d._rotate_start = d._persons[0];
        this._renderTaskDialog();
      }
      if (e.target.dataset.wd !== undefined) {
        const wds = new Set(d.schedule.weekdays || []);
        const wd = Number(e.target.dataset.wd);
        if (e.target.checked) wds.add(wd); else wds.delete(wd);
        d.schedule.weekdays = [...wds].sort((a, b) => a - b);
      }
      if (e.target.dataset.x === "addrem" && e.target.value !== "") {
        d.reminders = [...(d.reminders || []), Number(e.target.value)].sort((a, b) => a - b);
        this._renderTaskDialog();
      }
    });
    // Editing must not be lost to an accidental Esc press.
    dlg.addEventListener("cancel", (e) => e.preventDefault());
    dlg.addEventListener("click", async (e) => {
      const tagpick = e.target.closest("[data-tagpick]");
      if (tagpick) {
        const tag = tagpick.dataset.tagpick;
        const cur = new Set(d.tags || []);
        if (cur.has(tag)) cur.delete(tag); else cur.add(tag);
        d.tags = [...cur];
        this._renderTaskDialog();
        return;
      }
      const personpick = e.target.closest("[data-personpick]");
      if (personpick) {
        const pid = personpick.dataset.personpick;
        const cur = new Set(d._persons || []);
        if (cur.has(pid)) cur.delete(pid); else cur.add(pid);
        d._persons = [...cur];
        if (d._persons.length < 2) d._rotate = false;
        if (d._rotate_start && !d._persons.includes(d._rotate_start)) d._rotate_start = d._persons[0] || null;
        this._renderTaskDialog();
        return;
      }
      const remdel = e.target.closest("[data-remdel]");
      if (remdel) {
        d.reminders.splice(Number(remdel.dataset.remdel), 1);
        this._renderTaskDialog();
        return;
      }
      const subdel = e.target.closest("[data-subdel]");
      if (subdel) {
        d.subtasks.splice(Number(subdel.dataset.subdel), 1);
        this._renderTaskDialog();
        return;
      }
      const b = e.target.closest("[data-x]");
      if (!b || b.dataset.x === "addrem") return;
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
        if (d.type === "after_completion" && !d.due_date) return;
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
      // Build the rule from the explicit inputs (cron-style, independent of
      // the optional first-due date).
      const s = d.schedule;
      s.day = null; s.nth = null; s.month = null;
      if (s.freq === "monthly") {
        if (d._mMode === "last") s.day = "last";
        else if (d._mMode === "nth") s.nth = { n: Number(d._mNthN), weekday: Number(d._mNthWd) };
        else s.day = Math.min(31, Math.max(1, Number(d._mDay) || 1));
      } else if (s.freq === "yearly") {
        s.day = Math.min(31, Math.max(1, Number(d._mDay) || 1));
        s.month = Math.min(12, Math.max(1, Number(d._yMonth) || 1));
      } else if (s.freq === "weekly" && (!s.weekdays || !s.weekdays.length)) {
        s.weekdays = [(new Date().getDay() + 6) % 7];
      }
      if (s.freq !== "weekly") s.weekdays = null;
      if (!d.due_date) d.due_date = toIso(nextRuleDate(s));
      d.interval = null; d.period = null;
    } else if (d.type === "after_completion") {
      d.schedule = null; d.period = null;
    } else if (d.type === "period") {
      d.schedule = null; d.interval = null; d.due_date = null; d.visible_from = null;
      d.due_time = null; d.reminders = [];
    } else {
      d.schedule = null; d.interval = null; d.period = null;
    }
    delete d.computed;
    // Assignment: with rotation the pool lives in rotation.persons and
    // assigned_to holds only the current person; without it the selection
    // is the assignment itself.
    if (d._rotate && d.type !== "simple" && (d._persons || []).length >= 2) {
      const start = d._persons.includes(d._rotate_start) ? d._rotate_start : d._persons[0];
      d.rotation = { persons: [...d._persons], index: d._persons.indexOf(start) };
      d.assigned_to = [start];
    } else {
      d.rotation = null;
      d.assigned_to = [...(d._persons || [])];
    }
    for (const key of Object.keys(d)) if (key.startsWith("_")) delete d[key];
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
      .menu-anchor { position: relative; display: inline-block; }
      .dropdown { position: absolute; right: 0; top: calc(100% + 4px); z-index: 10; min-width: 180px;
        background: var(--card-background-color, #fff); border: 1px solid var(--divider-color);
        border-radius: 10px; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25); overflow: hidden; }
      .dd-item { display: block; width: 100%; text-align: left; border: none; background: none;
        color: var(--primary-text-color); padding: 10px 14px; cursor: pointer; font: inherit;
        white-space: nowrap; }
      .dd-item:hover { background: var(--secondary-background-color); }
      .list-manage { display: flex; flex-direction: column; gap: 6px; }
      .tagpick { margin: -6px 0 12px; }
      .list-row { display: flex; justify-content: space-between; align-items: center; text-align: left; }
      .row-edit { opacity: 0.6; margin-left: 12px; }
      .menu { padding: 8px 0 4px; border-bottom: 1px solid var(--divider-color); margin-bottom: 8px; }
      .chips { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; align-items: center; }
      .chip { border: 1px solid var(--divider-color); background: none; color: var(--secondary-text-color);
        border-radius: 14px; padding: 3px 12px; cursor: pointer; font-size: 0.85em; }
      .chip.on { background: var(--primary-color); border-color: var(--primary-color); color: var(--text-primary-color, #fff); }
      .chip.ghost { border-style: dashed; }
      .chip.tagchip.on { background: var(--accent-color, var(--primary-color)); border-color: var(--accent-color, var(--primary-color)); }
      .chip-select { border: 1px dashed var(--divider-color); background: none; color: var(--secondary-text-color);
        border-radius: 14px; padding: 3px 8px; font-size: 0.85em; }
      .menu-row { margin: 6px 0; }
      .menu-row.selects { display: flex; gap: 8px; flex-wrap: wrap; }
      .menu-row select { flex: 1; min-width: 140px; padding: 5px 8px; border-radius: 8px;
        border: 1px solid var(--divider-color); background: var(--secondary-background-color); color: var(--primary-text-color); }
      .toggles { display: flex; gap: 14px; font-size: 0.85em; color: var(--secondary-text-color); flex-wrap: wrap; }
      .toggles label { display: flex; align-items: center; gap: 4px; cursor: pointer; }
      .list-block { margin-top: 4px; }
      .list-head { font-size: 0.8em; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;
        color: var(--secondary-text-color); margin: 12px 0 4px; }
      .task { border-radius: 10px; margin: 2px -8px; }
      .task:hover { background: var(--secondary-background-color); }
      .row { display: flex; align-items: flex-start; gap: 10px; padding: 7px 8px; cursor: pointer; }
      .compact .row { padding: 4px 8px; gap: 8px; }
      .compact .badges { margin-top: 1px; }
      .grip { color: var(--secondary-text-color); cursor: grab; letter-spacing: -2px; font-size: 0.9em; margin-top: 3px; }
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
      .badge { font-size: 0.8em; font-weight: 500; padding: 2px 9px; border-radius: 11px;
        line-height: 1.4; letter-spacing: 0.01em;
        background: var(--secondary-background-color); color: var(--secondary-text-color); white-space: nowrap; }
      .badge.err { background: color-mix(in srgb, var(--error-color) 24%, transparent); color: var(--error-color); }
      .badge.warn { background: color-mix(in srgb, var(--warning-color) 26%, transparent); color: var(--warning-color); }
      .badge.ok { background: color-mix(in srgb, var(--success-color, #4caf50) 18%, transparent); color: var(--success-color, #4caf50); }
      .badge.person { background: color-mix(in srgb, var(--primary-color) 15%, transparent); color: var(--primary-color); }
      .badge.tag { background: color-mix(in srgb, var(--accent-color, var(--primary-color)) 15%, transparent); color: var(--accent-color, var(--primary-color)); }
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
        color: var(--primary-text-color); padding: 20px; min-width: min(340px, 90vw); max-width: min(460px, 95vw);
        max-height: 90vh; overflow-y: auto; box-shadow: 0 8px 32px rgba(0,0,0,0.35); }
      dialog::backdrop { background: rgba(0,0,0,0.45); }
      .dlg-title { font-size: 1.1em; font-weight: 500; margin-bottom: 14px; }
      .field { display: flex; flex-direction: column; gap: 3px; margin-bottom: 10px; font-size: 0.85em; color: var(--secondary-text-color); }
      .field input, .field select, .field textarea, .sub-add input {
        font-size: 1rem; padding: 7px 10px; border-radius: 8px; border: 1px solid var(--divider-color);
        background: var(--secondary-background-color); color: var(--primary-text-color); width: 100%; }
      .field input[type="checkbox"] { width: auto; padding: 0; margin: 0; }
      .field-row { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; font-size: 0.9em; color: var(--secondary-text-color); flex-wrap: wrap; }
      .field-row2 { display: flex; gap: 8px; align-items: flex-end; }
      .field-row2 .grow { flex: 1; }
      .hint { font-size: 0.85em; opacity: 0.8; }
      .field-row .num { width: 64px; padding: 7px 8px; border-radius: 8px; border: 1px solid var(--divider-color);
        background: var(--secondary-background-color); color: var(--primary-text-color); }
      .field-row select { padding: 7px 8px; border-radius: 8px; border: 1px solid var(--divider-color);
        background: var(--secondary-background-color); color: var(--primary-text-color); }
      .wd-row { display: flex; gap: 6px; flex-wrap: wrap; }
      .wd { display: flex; flex-direction: column; align-items: center; gap: 2px; font-size: 0.8em;
        color: var(--primary-text-color); cursor: pointer; }
      .endblock { margin-bottom: 10px; font-size: 0.85em; color: var(--secondary-text-color); }
      .endblock summary { cursor: pointer; margin-bottom: 6px; }
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

/* ------------------------------------------------------------------ */
/* Visual config editor                                                */
/* ------------------------------------------------------------------ */

class BetterTodoCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._data = null;
    // Attached once — never inside _render (see card constructor note).
    this.shadowRoot.addEventListener("input", (e) => this._onInput(e));
  }

  setConfig(config) {
    this._config = { ...config };
    // Config changes we fired ourselves come straight back through here;
    // re-rendering then would destroy the focused input on every keystroke.
    if (this._suppressRender) { this._suppressRender = false; return; }
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._data && hass) {
      hass.callWS({ type: "better_todo/get_data" })
        .then((data) => { this._data = data; this._render(); })
        .catch(() => {});
    }
  }

  _fire() {
    this._suppressRender = true;
    const config = { type: "custom:better-todo-card", ...this._config };
    this.dispatchEvent(new CustomEvent("config-changed", {
      detail: { config }, bubbles: true, composed: true,
    }));
  }

  _render() {
    const t = pickLang(this._hass);
    const c = this._config;
    const lists = this._data?.lists || [];
    const persons = this._data?.persons || [];
    const selLists = c.lists || [];
    const toggles = [
      ["show_menu", "Menu", c.show_menu ?? true],
      ["show_add", "+ Add", c.show_add ?? true],
      ["show_completed", t.show_done, c.show_completed ?? false],
      ["show_upcoming", t.show_upcoming, c.show_upcoming ?? false],
      ["compact", "Compact", c.compact ?? false],
      ["confirm_complete", "Confirm", c.confirm_complete ?? false],
    ];
    this.shadowRoot.innerHTML = `<style>
        .ed { display: flex; flex-direction: column; gap: 10px; font-family: inherit; color: var(--primary-text-color); }
        label { display: flex; flex-direction: column; gap: 3px; font-size: 0.85em; color: var(--secondary-text-color); }
        input, select { font-size: 1rem; padding: 6px 10px; border-radius: 8px; border: 1px solid var(--divider-color);
          background: var(--secondary-background-color); color: var(--primary-text-color); }
        .row { display: flex; gap: 10px; flex-wrap: wrap; }
        .row label { flex: 1; min-width: 130px; }
        .checks { display: flex; flex-wrap: wrap; gap: 8px 16px; }
        .checks label { flex-direction: row; align-items: center; gap: 5px; font-size: 0.9em; color: var(--primary-text-color); }
        .lists { display: flex; flex-wrap: wrap; gap: 8px 16px; }
        .lists label { flex-direction: row; align-items: center; gap: 5px; font-size: 0.9em; color: var(--primary-text-color); }
        .hint { font-size: 0.75em; color: var(--secondary-text-color); }
      </style>
      <div class="ed">
        <label>${esc(t.title_f)}<input type="text" data-f="title" value="${esc(c.title || "")}"></label>
        ${lists.length ? `<div><label>${esc(t.list_f)}</label><div class="lists">
          ${lists.map((l) => `<label><input type="checkbox" data-list="${esc(l.id)}" ${selLists.includes(l.id) || selLists.includes(l.name) ? "checked" : ""}> ${esc(l.name)}</label>`).join("")}
        </div><div class="hint">∅ = alle / all</div></div>` : ""}
        <div class="row">
          <label>${esc(t.assigned_f)}<select data-f="assigned">
            <option value="all" ${(c.assigned || "all") === "all" ? "selected" : ""}>${esc(t.all_persons)}</option>
            <option value="me" ${c.assigned === "me" ? "selected" : ""}>${esc(t.logged_in)}</option>
            ${persons.map((p) => `<option value="${esc(p.entity_id)}" ${c.assigned === p.entity_id ? "selected" : ""}>${esc(p.name)}</option>`).join("")}
          </select></label>
          <label>${esc(t.sort_f)}<select data-f="sort">
            ${[["smart", t.sort_smart], ["manual", t.sort_manual], ["due", t.sort_due], ["priority", t.sort_prio], ["title", t.sort_title], ["person", t.sort_person]]
              .map(([v, label]) => `<option value="${v}" ${(c.sort || "smart") === v ? "selected" : ""}>${esc(label)}</option>`).join("")}
          </select></label>
        </div>
        <div class="row">
          <label>${esc(t.due_soon(c.due_soon_days ?? 7))}<input type="number" min="0" max="90" data-f="due_soon_days" value="${c.due_soon_days ?? 7}"></label>
          <label>max-height (px)<input type="number" min="0" data-f="max_height" value="${c.max_height ?? ""}"></label>
        </div>
        <div class="checks">
          ${toggles.map(([key, label, val]) => `<label><input type="checkbox" data-f="${key}" ${val ? "checked" : ""}> ${esc(label)}</label>`).join("")}
        </div>
      </div>`;
  }

  _onInput(e) {
    const el = e.target;
    if (el.dataset.list) {
      const checked = [...this.shadowRoot.querySelectorAll("[data-list]")]
        .filter((x) => x.checked).map((x) => x.dataset.list);
      if (checked.length) this._config.lists = checked;
      else delete this._config.lists;
      this._fire();
      return;
    }
    const f = el.dataset.f;
    if (!f) return;
    if (el.type === "checkbox") this._config[f] = el.checked;
    else if (el.type === "number") {
      const v = el.value === "" ? null : Number(el.value);
      if (v === null) delete this._config[f];
      else this._config[f] = v;
    } else if (el.value === "") delete this._config[f];
    else this._config[f] = el.value;
    this._fire();
  }
}

customElements.define("better-todo-card", BetterTodoCard);
customElements.define("better-todo-card-editor", BetterTodoCardEditor);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "better-todo-card",
  name: "Better ToDo Card",
  description: "Task list card for the Better ToDo integration.",
  preview: false,
});
