// 简化 ApiClient（演示）
(function(global){
  const API_BASE = global.__API_BASE__ || '/api/v1';
  const storage = {
    getToken(){ return localStorage.getItem('sh_token') },
    setToken(t){ localStorage.setItem('sh_token', t) }
  };
  async function request(path, opts = {}) {
    const url = path.startsWith('http') ? path : (API_BASE + path);
    const headers = opts.headers || {};
    const token = storage.getToken();
    if (token) headers['Authorization'] = 'Bearer ' + token;
    if (!(opts.body instanceof FormData)) headers['Content-Type'] = headers['Content-Type'] || 'application/json';
    const final = Object.assign({}, opts, { headers });
    if (final.body && !(final.body instanceof FormData) && typeof final.body !== 'string') final.body = JSON.stringify(final.body);
    const res = await fetch(url, final);
    const txt = await res.text();
    try { return JSON.parse(txt); } catch(e){ return { raw: txt, status: res.status }; }
  }
  global.ApiClient = {
    sendSms(phone){ return request('/auth/send-sms', { method:'POST', body:{ phone } }); },
    login(phone, code){ return request('/auth/login',{ method:'POST', body:{ phone, code }}); },
    uploadFile(file){ const fd = new FormData(); fd.append('file', file); return request('/upload', { method:'POST', body: fd }); },
    listConversations(limit=20){ return request('/conversations?limit='+limit, { method:'GET' }); },
    createConversation(payload){ return request('/conversations',{ method:'POST', body: payload }); },
    getConversation(id){ return request('/conversations/'+id, { method:'GET' }); },
    sendMessage(convId, payload){ return request('/conversations/'+convId+'/messages', { method:'POST', body: payload }); },
    listTemplates(){ return request('/templates',{ method:'GET' }); },
    renderTemplate(id, values){ return request('/templates/'+id+'/render', { method:'POST', body: { values } }); },
    createOrder(payload){ return request('/orders/create', { method:'POST', body: payload }); }
  };
})(window);
