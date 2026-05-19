const API = {
  login: '/api/auth/login',
  register: '/api/auth/register',
  tasks: '/api/tasks',
  revoke: '/api/auth/revoke_others',
  logout: '/api/auth/logout'
};

function setStatus(msg) {
  document.getElementById('status').innerText = msg;
}

async function api(path, opts = {}) {
  const token = localStorage.getItem('TOKEN');
  opts.headers = opts.headers || {};
  if (token) opts.headers['Authorization'] = 'Bearer ' + token;
  if (opts.json) {
    opts.method = opts.method || 'POST';
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(opts.json);
  }
  const res = await fetch(path, opts);
  const data = await res.json().catch(() => ({}));
  return { ok: res.ok, status: res.status, data };
}

async function login() {
  const username = document.getElementById('username').value;
  const password = document.getElementById('password').value;
  const payload = { email: username, username, password };
  const r = await api(API.login, { json: payload });
  if (r.ok) {
    localStorage.setItem('TOKEN', r.data.token);
    setStatus('Logged in');
    showApp();
    await loadTasks();
  } else {
    setStatus('Login failed: ' + (r.data.detail || JSON.stringify(r.data)));
  }
}

async function register() {
  const email = document.getElementById('reg-email').value;
  const username = document.getElementById('reg-username').value;
  const password = document.getElementById('reg-password').value;
  const payload = { email, username, password };
  const r = await api(API.register, { json: payload });
  if (r.ok) {
    setStatus('Registered. You can now login.');
    document.getElementById('register-form').style.display = 'none';
  } else {
    setStatus('Register failed: ' + (r.data.detail || JSON.stringify(r.data)));
  }
}

function showApp() {
  document.getElementById('auth').style.display = 'none';
  document.getElementById('app').style.display = 'block';
}

function showAuth() {
  document.getElementById('auth').style.display = 'block';
  document.getElementById('app').style.display = 'none';
}

async function loadTasks() {
  const r = await api(API.tasks, { method: 'GET' });
  if (!r.ok) {
    setStatus('Failed to load tasks');
    return;
  }
  const ul = document.getElementById('tasks');
  ul.innerHTML = '';
  for (const t of r.data) {
    const li = document.createElement('li');
    li.innerHTML = `<label><input type="checkbox" data-id="${t.id}" ${t.completed ? 'checked' : ''}/> <strong>${t.title}</strong> - ${t.description || ''}</label>`;
    const cb = li.querySelector('input[type=checkbox]');
    cb.addEventListener('change', async (e) => {
      const checked = e.target.checked;
      const res = await api(`/api/tasks/${t.id}`, { method: 'PATCH', json: { completed: checked } });
      if (res.ok) {
        setStatus('Task updated');
      } else {
        setStatus('Failed to update task');
        e.target.checked = !checked; // revert
      }
    });
    ul.appendChild(li);
  }
}

async function addTask(e) {
  e.preventDefault();
  const title = document.getElementById('task-title').value;
  const description = document.getElementById('task-desc').value;
  const r = await api(API.tasks, { json: { title, description } });
  if (r.ok) {
    setStatus('Task created');
    document.getElementById('task-form').reset();
    await loadTasks();
  } else {
    setStatus('Failed to create task');
  }
}

async function logout() {
  const token = localStorage.getItem('TOKEN');
  const r = await api(API.logout, { method: 'POST' });
  if (r.ok) {
    localStorage.removeItem('TOKEN');
    setStatus('Logged out');
    showAuth();
  } else {
    setStatus('Logout failed');
  }
}

async function revokeOthers() {
  const r = await api(API.revoke, { method: 'POST' });
  if (r.ok) setStatus('Revoked other sessions');
  else setStatus('Failed to revoke');
}

document.getElementById('login').addEventListener('click', login);
document.getElementById('show-register').addEventListener('click', () => {
  const el = document.getElementById('register-form');
  el.style.display = el.style.display === 'none' ? 'block' : 'none';
});
document.getElementById('register').addEventListener('click', register);
document.getElementById('task-form').addEventListener('submit', addTask);
document.getElementById('logout').addEventListener('click', logout);
document.getElementById('revoke-others').addEventListener('click', revokeOthers);

// On load, if token exists, show app and load tasks
window.addEventListener('load', async () => {
  if (localStorage.getItem('TOKEN')) {
    showApp();
    await loadTasks();
  }
});
