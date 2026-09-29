const API = {
  async request(method, url, body) {
    const opts = { 
      method, 
      headers: { 'Content-Type': 'application/json' },
      cache: 'no-store' // Запрещаем браузеру использовать кеш для этого запроса
    };
    if (body !== undefined) opts.body = JSON.stringify(body);
    
    // Добавляем уникальный параметр _t к GET-запросам для 100% обхода кеша
    const fetchUrl = method === 'GET' 
      ? `${url}${url.includes('?') ? '&' : '?'}_t=${Date.now()}` 
      : url;
    
    const res = await fetch(fetchUrl, opts);
    if (!res.ok) {
      let detail = res.statusText;
      try { detail = (await res.json()).detail || detail; } catch (e) {}
      throw new Error(detail);
    }
    if (res.status === 204) return null;
    return res.json();
  },
  listCampaigns: () => API.request('GET', '/api/v1/campaigns'),
  createCampaign: (p) => API.request('POST', '/api/v1/campaigns', p),
  getCampaign: (id) => API.request('GET', `/api/v1/campaigns/${id}`),
  fetchStreams: (id) => API.request('POST', `/api/v1/campaigns/${id}/fetch`),
  pushFlow: (fid) => API.request('POST', `/api/v1/flows/${fid}/push`),
  cancelFlow: (fid) => API.request('POST', `/api/v1/flows/${fid}/cancel`),
  addOffer: (fid, oid) => API.request('POST', `/api/v1/flows/${fid}/offers`, { offer_id: oid }),
  removeOffer: (fid, oid) => API.request('DELETE', `/api/v1/flows/${fid}/offers/${oid}`),
  bringBack: (fid, oid) => API.request('POST', `/api/v1/flows/${fid}/offers/${oid}/bring_back`),
  pinOffer: (fid, oid, share) => API.request('PUT', `/api/v1/flows/${fid}/offers/${oid}/pin`, { share }),
  unpinOffer: (fid, oid) => API.request('DELETE', `/api/v1/flows/${fid}/offers/${oid}/pin`),
  searchOffers: (q) => API.request('GET', `/api/v1/offers/search?q=${encodeURIComponent(q)}`),
};

function showError(err) {
  const el = document.getElementById('global-error');
  if (!el) return;
  el.textContent = err.message || String(err);
  el.classList.remove('hidden');
  setTimeout(() => el.classList.add('hidden'), 6000);
}

function escapeHtml(s) {
  const d = document.createElement('div');
  d.textContent = s ?? '';
  return d.innerHTML;
}