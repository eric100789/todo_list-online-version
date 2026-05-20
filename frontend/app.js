function normalizePath(value) {
  if (!value || value === '/') return '/'
  return `/${String(value).trim().replace(/^\/+/, '').replace(/\/+$/, '')}`
}

function joinPath(base, path) {
  const cleanBase = normalizePath(base)
  const cleanPath = `/${String(path || '').replace(/^\/+/, '')}`
  return cleanBase === '/' ? cleanPath : `${cleanBase}${cleanPath}`
}

const APP_CONFIG = window.__TODO_CONFIG__ || {}
const API_BASE_PATH = normalizePath(APP_CONFIG.apiBasePath || '/api')

const API = {
  login: joinPath(API_BASE_PATH, '/auth/login'),
  register: joinPath(API_BASE_PATH, '/auth/register'),
  me: joinPath(API_BASE_PATH, '/users/me'),
  logout: joinPath(API_BASE_PATH, '/auth/logout'),
  revokeOthers: joinPath(API_BASE_PATH, '/auth/revoke_others'),
  sessions: joinPath(API_BASE_PATH, '/auth/sessions'),
  revokeSessions: joinPath(API_BASE_PATH, '/auth/sessions/revoke'),
  tasks: joinPath(API_BASE_PATH, '/tasks'),
  categories: joinPath(API_BASE_PATH, '/categories'),
  categoriesReorder: joinPath(API_BASE_PATH, '/categories/reorder'),
  notes: joinPath(API_BASE_PATH, '/notes')
}

const ACCENTS = {
  teal: ['#0f766e', '#115e59'],
  amber: ['#c2410c', '#9a3412'],
  blue: ['#2563eb', '#1d4ed8'],
  rose: ['#be123c', '#9f1239']
}

const state = {
  token: localStorage.getItem('TOKEN') || '',
  user: null,
  view: 'tasks',
  tasks: [],
  categories: [],
  notes: [],
  sessions: [],
  historyMonth: new Date(),
  prefs: loadPrefs(),
  editingTaskId: null,
  editingNoteId: null
}

const els = {
  authShell: document.getElementById('auth-shell'),
  appShell: document.getElementById('app-shell'),
  authStatus: document.getElementById('auth-status'),
  loginForm: document.getElementById('login-form'),
  registerForm: document.getElementById('register-form'),
  loginTab: document.getElementById('auth-tab-login'),
  registerTab: document.getElementById('auth-tab-register'),
  viewRoot: document.getElementById('view-root'),
  viewTitle: document.getElementById('view-title'),
  viewKicker: document.getElementById('view-kicker'),
  topbarBadge: document.getElementById('topbar-badge'),
  userMeta: document.getElementById('user-meta'),
  toastRoot: document.getElementById('toast-root')
}

function loadPrefs() {
  try {
    return JSON.parse(localStorage.getItem('TODO_PREFS') || '{}')
  } catch {
    return {}
  }
}

function savePrefs() {
  localStorage.setItem('TODO_PREFS', JSON.stringify(state.prefs))
  applyPrefs()
}

function applyPrefs() {
  const theme = state.prefs.theme || 'light'
  const accent = state.prefs.accent || 'teal'
  const palette = ACCENTS[accent] || ACCENTS.teal
  document.body.dataset.theme = theme
  document.body.style.setProperty('--primary', palette[0])
  document.body.style.setProperty('--primary-strong', palette[1])
  document.body.style.setProperty('--accent', palette[0])
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

function formatDateTime(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return new Intl.DateTimeFormat(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}

function formatDate(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value).slice(0, 10)
  return new Intl.DateTimeFormat(undefined, { year: 'numeric', month: 'short', day: 'numeric' }).format(date)
}

function parseDateInput(value) {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

function isOverdue(dueDate) {
  const date = parseDateInput(dueDate)
  if (!date) return false
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return date.getTime() < today.getTime()
}

function setAuthStatus(message, kind = 'info') {
  els.authStatus.textContent = message || ''
  els.authStatus.className = `status-line ${kind}`.trim()
}

function setTopbarBadge(message, kind = 'info') {
  els.topbarBadge.textContent = message || ''
  els.topbarBadge.className = `status-pill ${kind}`.trim()
}

function toast(message) {
  const node = document.createElement('div')
  node.className = 'toast'
  node.textContent = message
  els.toastRoot.appendChild(node)
  setTimeout(() => node.remove(), 2600)
}

function showAuth(message = '') {
  els.authShell.classList.remove('hidden')
  els.appShell.classList.add('hidden')
  if (message) setAuthStatus(message, 'error')
}

function showApp() {
  els.authShell.classList.add('hidden')
  els.appShell.classList.remove('hidden')
}

function setView(view) {
  state.view = view
  document.querySelectorAll('.nav-btn').forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.view === view)
  })
  const labels = {
    tasks: ['Dashboard', 'Tasks'],
    quick: ['Dashboard', 'Quick'],
    kanban: ['Board', 'Kanban'],
    history: ['Archive', 'History'],
    notes: ['Notebook', 'Notes'],
    settings: ['Control', 'Settings']
  }
  const [kicker, title] = labels[view] || ['Dashboard', 'Tasks']
  els.viewKicker.textContent = kicker
  els.viewTitle.textContent = title
  renderCurrentView()
}

async function request(path, opts = {}) {
  const headers = Object.assign({}, opts.headers || {})
  if (state.token) headers.Authorization = `Bearer ${state.token}`
  if (opts.json !== undefined) {
    headers['Content-Type'] = 'application/json'
    opts.body = JSON.stringify(opts.json)
    if (!opts.method) opts.method = 'POST'
  }
  const config = Object.assign({}, opts, { headers })
  try {
    const response = await fetch(path, config)
    const contentType = response.headers.get('content-type') || ''
    const data = contentType.includes('application/json') ? await response.json().catch(() => ({})) : await response.text()
    return { ok: response.ok, status: response.status, data }
  } catch (error) {
    return { ok: false, status: 0, data: { detail: error.message || 'Network error' }, networkError: true }
  }
}

function handleAuthFailure(message) {
  state.token = ''
  state.user = null
  localStorage.removeItem('TOKEN')
  setTopbarBadge('Disconnected', 'error')
  setAuthStatus(message || 'Session expired. Please sign in again.', 'error')
  showAuth(message || 'Session expired. Please sign in again.')
}

async function secureRequest(path, opts = {}) {
  const response = await request(path, opts)
  if ((response.status === 401 || response.status === 403) && state.token) {
    handleAuthFailure('Your session is no longer valid.')
  }
  return response
}

async function login(event) {
  event.preventDefault()
  const identity = document.getElementById('login-identity').value.trim()
  const password = document.getElementById('login-password').value
  const response = await request(API.login, {
    json: { identity, email: identity, username: identity, password }
  })
  if (response.ok) {
    state.token = response.data.token
    localStorage.setItem('TOKEN', state.token)
    setAuthStatus('Signed in successfully.', 'success')
    await bootstrapAuthenticated()
    return
  }
  setAuthStatus(`Login failed: ${response.data?.detail || 'Unknown error'}`, 'error')
}

async function register(event) {
  event.preventDefault()
  const email = document.getElementById('register-email').value.trim()
  const username = document.getElementById('register-username').value.trim()
  const password = document.getElementById('register-password').value
  const response = await request(API.register, {
    json: { email, username, password }
  })
  if (response.ok) {
    setAuthStatus('Account created. You can sign in now.', 'success')
    document.getElementById('login-identity').value = email || username
    switchAuthMode('login')
    return
  }
  setAuthStatus(`Register failed: ${response.data?.detail || 'Unknown error'}`, 'error')
}

async function logout() {
  await secureRequest(API.logout, { method: 'POST' })
  state.token = ''
  state.user = null
  localStorage.removeItem('TOKEN')
  showAuth('Signed out.')
}

async function revokeOthers() {
  const response = await secureRequest(API.revokeOthers, { method: 'POST' })
  if (response.ok) {
    toast('Other sessions revoked.')
    await loadSessions()
    renderCurrentView()
  } else {
    toast('Unable to revoke other sessions.')
  }
}

function switchAuthMode(mode) {
  const loginMode = mode === 'login'
  els.loginTab.classList.toggle('active', loginMode)
  els.registerTab.classList.toggle('active', !loginMode)
  els.loginForm.classList.toggle('hidden', !loginMode)
  els.registerForm.classList.toggle('hidden', loginMode)
}

function activeTasks() {
  return state.tasks.filter((task) => task.status !== 'completed' && (task.task_type || 'task') !== 'quick')
}

function quickTasks() {
  return state.tasks.filter((task) => task.status !== 'completed' && (task.task_type || 'task') === 'quick')
}

function completedTasks() {
  return state.tasks.filter((task) => task.status === 'completed')
}

function groupedTasks(includeQuick = true) {
  const groups = new Map()
  groups.set('uncategorized', [])
  state.categories.forEach((category) => groups.set(String(category.id), []))
  for (const task of activeTasks()) {
    if ((task.task_type || 'task') === 'quick' && !includeQuick) continue
    const key = task.category_id == null ? 'uncategorized' : String(task.category_id)
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key).push(task)
  }
  return groups
}

async function loadUser() {
  if (!state.token) return false
  const response = await request(API.me, { method: 'GET' })
  if (response.ok) {
    state.user = response.data
    return true
  }
  if (response.status === 401 || response.status === 403) {
    handleAuthFailure('Saved token expired or was revoked.')
  }
  return false
}

async function loadTasks() {
  const response = await secureRequest(API.tasks, { method: 'GET' })
  if (response.ok && Array.isArray(response.data)) {
    state.tasks = response.data
  } else if (!state.tasks.length) {
    state.tasks = []
  }
}

async function loadCategories() {
  const response = await secureRequest(API.categories, { method: 'GET' })
  state.categories = response.ok && Array.isArray(response.data) ? response.data : []
}

async function loadNotes() {
  const response = await secureRequest(API.notes, { method: 'GET' })
  state.notes = response.ok && Array.isArray(response.data) ? response.data : []
}

async function loadSessions() {
  const response = await secureRequest(API.sessions, { method: 'GET' })
  state.sessions = response.ok && Array.isArray(response.data) ? response.data : []
}

async function autoCompleteOverdueTasks() {
  if (!state.prefs.autoCompleteEnabled) return
  const candidates = activeTasks().filter((task) => task.due_date && isOverdue(task.due_date))
  if (!candidates.length) return
  await Promise.all(
    candidates.map((task) =>
      secureRequest(`${API.tasks}/${task.id}`, {
        method: 'PATCH',
        json: { completed: true, status: 'completed', auto_completed: true }
      })
    )
  )
}

async function bootstrapAuthenticated() {
  showApp()
  setTopbarBadge('Connected', 'success')
  await Promise.all([loadUser(), loadTasks(), loadCategories(), loadNotes(), loadSessions()])
  await autoCompleteOverdueTasks()
  await loadTasks()
  renderCurrentView()
  updateUserMeta()
}

async function bootstrap() {
  applyPrefs()
  if (state.token && (await loadUser())) {
    await bootstrapAuthenticated()
    return
  }
  showAuth('Sign in to continue.')
  updateUserMeta()
}

function updateUserMeta() {
  if (state.user) {
    els.userMeta.textContent = `${state.user.username} · ${state.user.email}`
    return
  }
  els.userMeta.textContent = state.token ? 'Loading session…' : 'Not signed in'
}

async function saveTask(formData, existingId = null) {
  const payload = {
    title: formData.get('title').trim(),
    description: formData.get('description').trim(),
    due_date: formData.get('due_date') || null,
    is_starred: formData.get('is_starred') === 'on',
    color: formData.get('color') || '',
    task_type: formData.get('task_type') || 'task',
    category_id: formData.get('category_id') ? Number(formData.get('category_id')) : null
  }
  if (payload.task_type === 'quick') {
    payload.category_id = null
  }
  const response = existingId
    ? await secureRequest(`${API.tasks}/${existingId}`, { method: 'PATCH', json: payload })
    : await secureRequest(API.tasks, { json: payload })
  if (response.ok) {
    toast(existingId ? 'Task updated.' : 'Task created.')
    await loadTasks()
    renderCurrentView()
    return true
  }
  toast(response.data?.detail || 'Unable to save task.')
  return false
}

async function saveCategory(formData, existingId = null) {
  const payload = {
    name: formData.get('name').trim(),
    color: formData.get('color') || ''
  }
  const response = existingId
    ? await secureRequest(`${API.categories}/${existingId}`, { method: 'PATCH', json: payload })
    : await secureRequest(API.categories, { json: payload })
  if (response.ok) {
    await loadCategories()
    renderCurrentView()
    toast(existingId ? 'Category updated.' : 'Category created.')
    return true
  }
  toast(response.data?.detail || 'Unable to save category.')
  return false
}

async function saveNote(formData, existingId = null) {
  const payload = { content: formData.get('content').trim() }
  const response = existingId
    ? await secureRequest(`${API.notes}/${existingId}`, { method: 'PATCH', json: payload })
    : await secureRequest(API.notes, { json: payload })
  if (response.ok) {
    await loadNotes()
    renderCurrentView()
    toast(existingId ? 'Note updated.' : 'Note created.')
    return true
  }
  toast(response.data?.detail || 'Unable to save note.')
  return false
}

async function deleteTask(id) {
  const response = await secureRequest(`${API.tasks}/${id}`, { method: 'DELETE' })
  if (response.ok) {
    await loadTasks()
    renderCurrentView()
  }
}

async function completeTask(id) {
  const response = await secureRequest(`${API.tasks}/${id}`, {
    method: 'PATCH',
    json: { completed: true, status: 'completed' }
  })
  if (response.ok) {
    await loadTasks()
    renderCurrentView()
  }
}

async function starTask(task) {
  const response = await secureRequest(`${API.tasks}/${task.id}`, {
    method: 'PATCH',
    json: { is_starred: !task.is_starred }
  })
  if (response.ok) {
    await loadTasks()
    renderCurrentView()
  }
}

async function updateTaskCategory(id, categoryId) {
  const response = await secureRequest(`${API.tasks}/${id}`, {
    method: 'PATCH',
    json: { category_id: categoryId === '' ? null : Number(categoryId) }
  })
  if (response.ok) {
    await loadTasks()
    renderCurrentView()
  }
}

async function deleteCategory(id) {
  const response = await secureRequest(`${API.categories}/${id}`, { method: 'DELETE' })
  if (response.ok) {
    await loadCategories()
    await loadTasks()
    renderCurrentView()
  }
}

async function deleteNote(id) {
  const response = await secureRequest(`${API.notes}/${id}`, { method: 'DELETE' })
  if (response.ok) {
    await loadNotes()
    renderCurrentView()
  }
}

function taskCard(task, options = {}) {
  const categoryName = task.category_id == null
    ? 'Uncategorized'
    : (state.categories.find((category) => String(category.id) === String(task.category_id))?.name || 'Category')
  const due = task.due_date ? formatDate(task.due_date) : 'No due date'
  const overdue = task.status !== 'completed' && task.due_date && isOverdue(task.due_date)
  const kindLabel = task.task_type === 'quick' ? 'Quick' : 'Task'
  const columnColor = task.color || (options.color || '')
  const card = document.createElement('article')
  card.className = 'task-card'
  card.innerHTML = `
    <div class="row-between">
      <div>
        <div class="task-title">${escapeHtml(task.title)}</div>
        <div class="task-meta">${escapeHtml(kindLabel)} · ${escapeHtml(categoryName)} · ${escapeHtml(due)}</div>
      </div>
      <span class="chip ${overdue ? 'warn' : 'ghost'}">${overdue ? 'Overdue' : task.status}</span>
    </div>
    ${task.description ? `<p class="small-meta">${escapeHtml(task.description)}</p>` : ''}
    <div class="compact-actions">
      <span class="chip" style="${columnColor ? `border-left: 4px solid ${columnColor}; padding-left: 10px;` : ''}">${escapeHtml(task.is_starred ? 'Starred' : 'Normal')}</span>
      <div class="task-actions">
        ${task.status !== 'completed' ? '<button class="ghost-btn" data-action="complete">Done</button>' : ''}
        <button class="ghost-btn" data-action="edit">Edit</button>
        <button class="ghost-btn" data-action="star">Star</button>
        <button class="ghost-btn" data-action="delete">Delete</button>
      </div>
    </div>
  `

  card.querySelector('[data-action="complete"]')?.addEventListener('click', () => completeTask(task.id))
  card.querySelector('[data-action="edit"]')?.addEventListener('click', () => openTaskEditor(task))
  card.querySelector('[data-action="star"]')?.addEventListener('click', () => starTask(task))
  card.querySelector('[data-action="delete"]')?.addEventListener('click', () => deleteTask(task.id))
  return card
}

function noteCard(note) {
  const card = document.createElement('article')
  card.className = 'note-card'
  card.innerHTML = `
    <p>${escapeHtml(note.content)}</p>
    <div class="row-between">
      <span class="small-meta">Updated ${escapeHtml(formatDateTime(note.updated_at))}</span>
      <div class="note-actions">
        <button class="ghost-btn" data-action="edit">Edit</button>
        <button class="ghost-btn" data-action="delete">Delete</button>
      </div>
    </div>
  `
  card.querySelector('[data-action="edit"]')?.addEventListener('click', () => openNoteEditor(note))
  card.querySelector('[data-action="delete"]')?.addEventListener('click', () => deleteNote(note.id))
  return card
}

function sessionCard(session) {
  const card = document.createElement('article')
  card.className = 'session-card'
  card.innerHTML = `
    <label class="row-between" style="align-items:flex-start; gap: 10px;">
      <div>
        <div class="task-title">${escapeHtml(session.device_info || 'Unknown device')}</div>
        <div class="small-meta">${escapeHtml(formatDateTime(session.created_at))} · ${session.is_current ? 'current' : `session #${session.id}`}</div>
      </div>
      <input type="checkbox" data-session-id="${session.id}" ${session.is_current ? 'checked' : ''} />
    </label>
  `
  return card
}

function openTaskEditor(task = null) {
  state.editingTaskId = task ? task.id : null
  state.view = task && task.task_type === 'quick' ? 'quick' : state.view
  if (task && task.task_type === 'quick') setView('quick')
  else if (task) setView('tasks')
  renderCurrentView()
  setTimeout(() => {
    const form = document.getElementById('task-form')
    if (!form) return
    form.elements.title.value = task?.title || ''
    form.elements.description.value = task?.description || ''
    form.elements.due_date.value = task?.due_date || ''
    form.elements.is_starred.checked = Boolean(task?.is_starred)
    form.elements.color.value = task?.color || ''
    form.elements.category_id.value = task?.category_id == null ? '' : String(task.category_id)
    form.elements.task_type.value = task?.task_type || 'task'
    form.scrollIntoView({ behavior: 'smooth', block: 'start' })
  })
}

function openNoteEditor(note = null) {
  state.editingNoteId = note ? note.id : null
  if (state.view !== 'notes') setView('notes')
  renderCurrentView()
  setTimeout(() => {
    const form = document.getElementById('note-form')
    if (!form) return
    form.elements.content.value = note?.content || ''
    form.scrollIntoView({ behavior: 'smooth', block: 'start' })
  })
}

function taskFormMarkup(kind = 'task') {
  const categoriesOptions = ['<option value="">Uncategorized</option>']
  state.categories.forEach((category) => {
    categoriesOptions.push(`<option value="${category.id}">${escapeHtml(category.name)}</option>`)
  })
  return `
    <section class="panel">
      <div class="panel-header">
        <div>
          <p class="eyebrow">${kind === 'quick' ? 'Quick entry' : 'Task editor'}</p>
          <h2 style="margin:0; font-family: Space Grotesk, Inter, sans-serif;">${kind === 'quick' ? 'Quick cards' : 'Task board'}</h2>
        </div>
        <span class="chip">${kind === 'quick' ? quickTasks().length : activeTasks().length} active</span>
      </div>
      <div class="panel-body">
        <form id="task-form" class="view-grid">
          <input type="hidden" name="task_type" value="${kind}" />
          <div class="form-grid">
            <label class="span-2">Title<input name="title" required placeholder="Enter a title" /></label>
            <label class="span-2">Description<textarea name="description" placeholder="Add details"></textarea></label>
            <label>Due date<input name="due_date" type="date" /></label>
            <label>Category<select name="category_id">${categoriesOptions.join('')}</select></label>
            <label>Accent color<input name="color" type="color" value="#0f766e" /></label>
            <label class="row-between" style="align-items:center; gap: 10px;">Important<input name="is_starred" type="checkbox" /></label>
          </div>
          <div class="row-between">
            <button class="primary-btn" type="submit">${state.editingTaskId ? 'Save changes' : 'Add task'}</button>
            ${state.editingTaskId ? '<button class="secondary-btn" type="button" id="cancel-task-edit">Cancel edit</button>' : ''}
          </div>
        </form>
      </div>
    </section>
  `
}

function quickFormMarkup() {
  return taskFormMarkup('quick')
}

function renderTasksView() {
  const tasks = activeTasks().filter((task) => (task.task_type || 'task') !== 'quick')
  return `
    <div class="view-grid">
      ${taskFormMarkup('task')}
      <section class="panel">
        <div class="panel-header">
          <div>
            <p class="eyebrow">Active work</p>
            <h2 style="margin:0; font-family: Space Grotesk, Inter, sans-serif;">Tasks</h2>
          </div>
          <span class="chip">${tasks.length} items</span>
        </div>
        <div class="panel-body task-list" id="task-list"></div>
      </section>
    </div>
  `
}

function renderQuickView() {
  const tasks = quickTasks()
  return `
    <div class="view-grid">
      ${quickFormMarkup()}
      <section class="panel">
        <div class="panel-header">
          <div>
            <p class="eyebrow">Sticky space</p>
            <h2 style="margin:0; font-family: Space Grotesk, Inter, sans-serif;">Quick</h2>
          </div>
          <span class="chip">${tasks.length} items</span>
        </div>
        <div class="panel-body task-list" id="quick-list"></div>
      </section>
    </div>
  `
}

function renderKanbanView() {
  const prefs = state.prefs
  return `
    <div class="view-grid">
      <section class="panel">
        <div class="panel-header">
          <div>
            <p class="eyebrow">Board controls</p>
            <h2 style="margin:0; font-family: Space Grotesk, Inter, sans-serif;">Kanban</h2>
          </div>
          <span class="chip">${state.categories.length} categories</span>
        </div>
        <div class="panel-body">
          <div class="form-grid">
            <label>Category name<input id="new-category-name" placeholder="New column" /></label>
            <label>Category color<input id="new-category-color" type="color" value="#0f766e" /></label>
          </div>
          <div class="row-between" style="margin-top: 12px; flex-wrap: wrap;">
            <button class="secondary-btn" id="add-category-btn" type="button">Add category</button>
            <div class="compact-actions">
              <label class="chip ghost"><input id="pref-show-quick" type="checkbox" ${prefs.showQuick ? 'checked' : ''} /> Show quick</label>
              <label class="chip ghost"><input id="pref-auto-complete" type="checkbox" ${prefs.autoCompleteEnabled ? 'checked' : ''} /> Auto-complete</label>
              <label class="chip ghost"><input id="pref-recent-completed" type="checkbox" ${prefs.recentCompletedEnabled ? 'checked' : ''} /> Recent completed</label>
            </div>
          </div>
          <div class="form-grid" style="margin-top: 14px;">
            <label>Auto-complete days<input id="pref-auto-days" type="number" min="1" max="30" value="${prefs.autoCompleteDays || 3}" /></label>
            <label>Recent completed days<input id="pref-recent-days" type="number" min="1" max="30" value="${prefs.recentCompletedDays || 3}" /></label>
            <label>Auto-complete color<select id="pref-auto-color">
              <option value="#D1D5DB" ${prefs.autoCompleteColor === '#D1D5DB' ? 'selected' : ''}>Gray</option>
              <option value="#E5E7EB" ${prefs.autoCompleteColor === '#E5E7EB' ? 'selected' : ''}>Light gray</option>
              <option value="#BDBDBD" ${prefs.autoCompleteColor === '#BDBDBD' ? 'selected' : ''}>Muted gray</option>
            </select></label>
            <div></div>
          </div>
        </div>
      </section>
      <div class="board-grid" id="kanban-board"></div>
    </div>
  `
}

function renderHistoryView() {
  const month = state.historyMonth
  const monthLabel = new Intl.DateTimeFormat(undefined, { month: 'long', year: 'numeric' }).format(month)
  return `
    <div class="view-grid">
      <section class="panel">
        <div class="panel-header">
          <div>
            <p class="eyebrow">Archive</p>
            <h2 style="margin:0; font-family: Space Grotesk, Inter, sans-serif;">History</h2>
          </div>
          <div class="compact-actions">
            <button class="ghost-btn" id="history-prev">Prev</button>
            <span class="chip">${escapeHtml(monthLabel)}</span>
            <button class="ghost-btn" id="history-next">Next</button>
          </div>
        </div>
        <div class="panel-body split-grid">
          <div>
            <div class="calendar-grid" id="history-calendar"></div>
          </div>
          <div>
            <div class="timeline" id="history-list"></div>
          </div>
        </div>
      </section>
    </div>
  `
}

function renderNotesView() {
  return `
    <div class="view-grid">
      <section class="panel">
        <div class="panel-header">
          <div>
            <p class="eyebrow">Notebook</p>
            <h2 style="margin:0; font-family: Space Grotesk, Inter, sans-serif;">Notes</h2>
          </div>
          <span class="chip">${state.notes.length} notes</span>
        </div>
        <div class="panel-body split-grid">
          <form id="note-form" class="view-grid">
            <label>Note<textarea name="content" placeholder="Write something useful"></textarea></label>
            <div class="row-between">
              <button class="primary-btn" type="submit">${state.editingNoteId ? 'Save note' : 'Add note'}</button>
              ${state.editingNoteId ? '<button class="secondary-btn" type="button" id="cancel-note-edit">Cancel edit</button>' : ''}
            </div>
          </form>
          <div class="note-list" id="note-list"></div>
        </div>
      </section>
    </div>
  `
}

function renderSettingsView() {
  const selectedSessions = state.sessions.filter((session) => session.selected)
  return `
    <div class="view-grid">
      <section class="panel">
        <div class="panel-header">
          <div>
            <p class="eyebrow">Control room</p>
            <h2 style="margin:0; font-family: Space Grotesk, Inter, sans-serif;">Settings</h2>
          </div>
          <span class="chip">Local prefs</span>
        </div>
        <div class="panel-body view-grid">
          <div class="form-grid">
            <label>Theme<select id="pref-theme">
              <option value="light" ${state.prefs.theme !== 'dark' ? 'selected' : ''}>White</option>
              <option value="dark" ${state.prefs.theme === 'dark' ? 'selected' : ''}>Ink</option>
            </select></label>
            <label>Accent<select id="pref-accent">
              <option value="teal" ${state.prefs.accent === 'teal' ? 'selected' : ''}>Teal</option>
              <option value="blue" ${state.prefs.accent === 'blue' ? 'selected' : ''}>Blue</option>
              <option value="amber" ${state.prefs.accent === 'amber' ? 'selected' : ''}>Amber</option>
              <option value="rose" ${state.prefs.accent === 'rose' ? 'selected' : ''}>Rose</option>
            </select></label>
          </div>
          <div class="row-between" style="flex-wrap: wrap;">
            <button class="secondary-btn" id="save-prefs-btn" type="button">Save preferences</button>
            <button class="ghost-btn" id="refresh-sessions-btn" type="button">Refresh sessions</button>
          </div>
          <div class="panel" style="padding: 16px; background: rgba(248,250,252,0.8);">
            <div class="row-between">
              <div>
                <p class="eyebrow">Sessions</p>
                <h3 style="margin:0; font-family: Space Grotesk, Inter, sans-serif;">Active API tokens</h3>
              </div>
              <div class="compact-actions">
                <button class="ghost-btn" id="revoke-selected-sessions-btn" type="button">Revoke selected</button>
              </div>
            </div>
            <div class="session-list" id="session-list"></div>
          </div>
        </div>
      </section>
    </div>
  `
}

function renderTaskList(list, targetId, mode = 'task') {
  const target = document.getElementById(targetId)
  if (!target) return
  target.innerHTML = ''
  if (!list.length) {
    const empty = document.createElement('div')
    empty.className = 'small-meta'
    empty.textContent = mode === 'task' ? 'No tasks yet.' : 'Nothing here yet.'
    target.appendChild(empty)
    return
  }
  list.forEach((task) => {
    target.appendChild(taskCard(task))
  })
}

function renderKanbanBoard() {
  const board = document.getElementById('kanban-board')
  if (!board) return
  board.innerHTML = ''
  const showQuick = Boolean(state.prefs.showQuick)
  const groups = groupedTasks(showQuick)
  const recentCompleted = Boolean(state.prefs.recentCompletedEnabled)
  const autoEnabled = Boolean(state.prefs.autoCompleteEnabled)
  const autoRecent = autoEnabled
    ? state.tasks.filter((task) => task.auto_completed_at && new Date(task.auto_completed_at).getTime() >= Date.now() - ((Number(state.prefs.autoCompleteDays) || 3) * 86400000))
    : []
  const recentTasks = recentCompleted
    ? completedTasks().filter((task) => task.completed_at && new Date(task.completed_at).getTime() >= Date.now() - ((Number(state.prefs.recentCompletedDays) || 3) * 86400000))
    : []

  const columns = []
  if (showQuick) {
    columns.push({ key: 'quick', title: 'Quick', tasks: quickTasks(), quick: true })
  }
  if (autoEnabled && autoRecent.length) {
    columns.push({ key: 'auto', title: 'Auto-complete', tasks: autoRecent, muted: true, color: state.prefs.autoCompleteColor || '#D1D5DB' })
  }
  columns.push({ key: 'uncategorized', title: 'Uncategorized', tasks: groups.get('uncategorized') || [] })
  state.categories.forEach((category) => {
    columns.push({ key: String(category.id), title: category.name, tasks: groups.get(String(category.id)) || [], color: category.color || '' })
  })
  if (recentCompleted && recentTasks.length) {
    columns.push({ key: 'recent', title: 'Recent completed', tasks: recentTasks, muted: true })
  }

  columns.forEach((column) => {
    const el = document.createElement('section')
    el.className = 'column'
    if (column.color) {
      el.style.borderTop = `4px solid ${column.color}`
    }
    el.innerHTML = `
      <h3>
        <span>${escapeHtml(column.title)}</span>
        <span class="chip ${column.muted ? 'ghost' : ''}">${column.tasks.length}</span>
      </h3>
    `
    const list = document.createElement('div')
    list.className = 'task-list'
    column.tasks.forEach((task) => {
      const card = taskCard(task, { color: column.color })
      const footer = document.createElement('div')
      footer.className = 'task-actions'
      if (!column.quick && (task.status !== 'completed')) {
        const select = document.createElement('select')
        select.innerHTML = ['<option value="">Uncategorized</option>']
          .concat(state.categories.map((category) => `<option value="${category.id}">${escapeHtml(category.name)}</option>`))
          .join('')
        select.value = task.category_id == null ? '' : String(task.category_id)
        select.addEventListener('change', () => updateTaskCategory(task.id, select.value))
        footer.appendChild(select)
      }
      card.appendChild(footer)
      list.appendChild(card)
    })
    el.appendChild(list)
    board.appendChild(el)
  })
}

function renderHistoryCalendar() {
  const root = document.getElementById('history-calendar')
  if (!root) return
  root.innerHTML = ''
  const month = state.historyMonth
  const year = month.getFullYear()
  const monthIndex = month.getMonth()
  const firstDay = new Date(year, monthIndex, 1)
  const lastDay = new Date(year, monthIndex + 1, 0)
  const firstWeekday = (firstDay.getDay() + 6) % 7
  const days = []
  for (let i = 0; i < firstWeekday; i += 1) days.push(null)
  for (let day = 1; day <= lastDay.getDate(); day += 1) days.push(day)

  const completedByDay = new Map()
  completedTasks().forEach((task) => {
    const date = task.completed_at ? new Date(task.completed_at) : null
    if (!date || Number.isNaN(date.getTime())) return
    if (date.getFullYear() !== year || date.getMonth() !== monthIndex) return
    const key = date.getDate()
    if (!completedByDay.has(key)) completedByDay.set(key, [])
    completedByDay.get(key).push(task)
  })

  days.forEach((day) => {
    const cell = document.createElement('div')
    cell.className = 'calendar-day'
    if (day === null) {
      cell.style.visibility = 'hidden'
      root.appendChild(cell)
      return
    }
    const today = new Date()
    if (today.getFullYear() === year && today.getMonth() === monthIndex && today.getDate() === day) {
      cell.classList.add('today')
    }
    const header = document.createElement('div')
    header.className = 'day-num'
    header.textContent = String(day)
    cell.appendChild(header)
    const items = completedByDay.get(day) || []
    items.slice(0, 3).forEach((task) => {
      const span = document.createElement('span')
      span.className = 'item'
      span.textContent = task.title
      cell.appendChild(span)
    })
    if (items.length > 3) {
      const more = document.createElement('span')
      more.className = 'item'
      more.textContent = `+${items.length - 3} more`
      cell.appendChild(more)
    }
    root.appendChild(cell)
  })
}

function renderHistoryList() {
  const root = document.getElementById('history-list')
  if (!root) return
  root.innerHTML = ''
  const items = completedTasks().slice().sort((a, b) => new Date(b.completed_at || 0) - new Date(a.completed_at || 0))
  if (!items.length) {
    root.innerHTML = '<div class="small-meta">No completed tasks yet.</div>'
    return
  }
  items.forEach((task) => {
    const card = document.createElement('article')
    card.className = 'history-card'
    card.innerHTML = `
      <div class="row-between">
        <div>
          <div class="task-title">${escapeHtml(task.title)}</div>
          <div class="small-meta">Completed ${escapeHtml(formatDateTime(task.completed_at))}</div>
        </div>
        <span class="chip">${escapeHtml(task.task_type || 'task')}</span>
      </div>
    `
    root.appendChild(card)
  })
}

function renderNoteList() {
  const root = document.getElementById('note-list')
  if (!root) return
  root.innerHTML = ''
  if (!state.notes.length) {
    root.innerHTML = '<div class="small-meta">No notes yet.</div>'
    return
  }
  state.notes.forEach((note) => root.appendChild(noteCard(note)))
}

function renderSessionList() {
  const root = document.getElementById('session-list')
  if (!root) return
  root.innerHTML = ''
  if (!state.sessions.length) {
    root.innerHTML = '<div class="small-meta">No active sessions.</div>'
    return
  }
  state.sessions.forEach((session) => {
    const row = sessionCard(session)
    row.querySelector('input[type="checkbox"]')?.addEventListener('change', (event) => {
      session.selected = event.target.checked
    })
    root.appendChild(row)
  })
}

function renderCurrentView() {
  if (!els.viewRoot) return
  if (!state.user && state.token) return

  if (state.view === 'tasks') els.viewRoot.innerHTML = renderTasksView()
  else if (state.view === 'quick') els.viewRoot.innerHTML = renderQuickView()
  else if (state.view === 'kanban') els.viewRoot.innerHTML = renderKanbanView()
  else if (state.view === 'history') els.viewRoot.innerHTML = renderHistoryView()
  else if (state.view === 'notes') els.viewRoot.innerHTML = renderNotesView()
  else if (state.view === 'settings') els.viewRoot.innerHTML = renderSettingsView()

  wireCurrentView()
}

function wireCurrentView() {
  const taskForm = document.getElementById('task-form')
  if (taskForm) {
    taskForm.addEventListener('submit', async (event) => {
      event.preventDefault()
      const formData = new FormData(taskForm)
      await saveTask(formData, state.editingTaskId)
      state.editingTaskId = null
    })
    document.getElementById('cancel-task-edit')?.addEventListener('click', () => {
      state.editingTaskId = null
      renderCurrentView()
    })
    if (state.view === 'tasks') renderTaskList(activeTasks().filter((task) => (task.task_type || 'task') !== 'quick'), 'task-list')
    if (state.view === 'quick') renderTaskList(quickTasks(), 'quick-list', 'quick')
  }

  const noteForm = document.getElementById('note-form')
  if (noteForm) {
    noteForm.addEventListener('submit', async (event) => {
      event.preventDefault()
      const formData = new FormData(noteForm)
      await saveNote(formData, state.editingNoteId)
      state.editingNoteId = null
    })
    document.getElementById('cancel-note-edit')?.addEventListener('click', () => {
      state.editingNoteId = null
      renderCurrentView()
    })
    renderNoteList()
  }

  if (state.view === 'kanban') {
    renderKanbanBoard()
    document.getElementById('add-category-btn')?.addEventListener('click', async () => {
      const nameInput = document.getElementById('new-category-name')
      const colorInput = document.getElementById('new-category-color')
      const formData = new FormData()
      formData.append('name', nameInput.value)
      formData.append('color', colorInput.value)
      await saveCategory(formData)
    })
    document.getElementById('pref-show-quick')?.addEventListener('change', (event) => {
      state.prefs.showQuick = event.target.checked
      savePrefs()
      renderCurrentView()
    })
    document.getElementById('pref-auto-complete')?.addEventListener('change', (event) => {
      state.prefs.autoCompleteEnabled = event.target.checked
      savePrefs()
      renderCurrentView()
    })
    document.getElementById('pref-recent-completed')?.addEventListener('change', (event) => {
      state.prefs.recentCompletedEnabled = event.target.checked
      savePrefs()
      renderCurrentView()
    })
    document.getElementById('pref-auto-days')?.addEventListener('change', (event) => {
      state.prefs.autoCompleteDays = Number(event.target.value) || 3
      savePrefs()
      renderCurrentView()
    })
    document.getElementById('pref-recent-days')?.addEventListener('change', (event) => {
      state.prefs.recentCompletedDays = Number(event.target.value) || 3
      savePrefs()
      renderCurrentView()
    })
    document.getElementById('pref-auto-color')?.addEventListener('change', (event) => {
      state.prefs.autoCompleteColor = event.target.value
      savePrefs()
      renderCurrentView()
    })
  }

  if (state.view === 'history') {
    renderHistoryCalendar()
    renderHistoryList()
    document.getElementById('history-prev')?.addEventListener('click', () => {
      state.historyMonth = new Date(state.historyMonth.getFullYear(), state.historyMonth.getMonth() - 1, 1)
      renderCurrentView()
    })
    document.getElementById('history-next')?.addEventListener('click', () => {
      state.historyMonth = new Date(state.historyMonth.getFullYear(), state.historyMonth.getMonth() + 1, 1)
      renderCurrentView()
    })
  }

  if (state.view === 'settings') {
    renderSessionList()
    document.getElementById('save-prefs-btn')?.addEventListener('click', () => {
      state.prefs.theme = document.getElementById('pref-theme').value
      state.prefs.accent = document.getElementById('pref-accent').value
      savePrefs()
      toast('Preferences saved.')
    })
    document.getElementById('refresh-sessions-btn')?.addEventListener('click', async () => {
      await loadSessions()
      renderCurrentView()
      toast('Sessions refreshed.')
    })
    document.getElementById('revoke-selected-sessions-btn')?.addEventListener('click', async () => {
      const selected = state.sessions.filter((session) => session.selected).map((session) => session.id)
      if (!selected.length) {
        toast('Select one or more sessions first.')
        return
      }
      const response = await secureRequest(API.revokeSessions, {
        method: 'POST',
        json: { session_ids: selected }
      })
      if (response.ok) {
        if (response.data?.revoked_current) {
          handleAuthFailure('This session was revoked. Please sign in again.')
          return
        }
        await loadSessions()
        renderCurrentView()
        toast('Selected sessions revoked.')
      } else {
        toast('Unable to revoke selected sessions.')
      }
    })
  }
}

document.querySelectorAll('.nav-btn').forEach((btn) => {
  btn.addEventListener('click', () => setView(btn.dataset.view))
})

document.getElementById('logout-btn').addEventListener('click', logout)
document.getElementById('revoke-others-btn').addEventListener('click', revokeOthers)
document.getElementById('auth-tab-login').addEventListener('click', () => switchAuthMode('login'))
document.getElementById('auth-tab-register').addEventListener('click', () => switchAuthMode('register'))
document.getElementById('login-form').addEventListener('submit', login)
document.getElementById('register-form').addEventListener('submit', register)

window.addEventListener('load', bootstrap)
