let campaign = null;

async function load() {
  console.log("🔄 Загрузка свежих данных кампании...");
  campaign = await API.getCampaign(CAMPAIGN_ID);
  console.log("✅ Получены данные:", campaign);
  render();
}

function render() {
  document.getElementById('camp-name').textContent =
    `${campaign.name} (#${campaign.keitaro_campaign_id})`;
  const root = document.getElementById('flows');
  root.innerHTML = '';
  for (const flow of campaign.flows) root.appendChild(renderFlow(flow));
}

function renderFlow(flow) {
  const card = document.createElement('div');
  card.className = `border rounded bg-white p-4 ${flow.is_synced ? '' : 'flow-dirty'}`;

  const head = document.createElement('div');
  head.className = 'flex items-center justify-between mb-2';
  head.innerHTML = `
    <div class="font-semibold">${escapeHtml(flow.name)}
      <span class="text-gray-400 text-sm">kt#${flow.keitaro_flow_id}</span>
      ${flow.is_synced ? '' :
        '<span class="ml-2 text-xs bg-yellow-200 text-yellow-800 px-2 py-0.5 rounded">не запушено</span>'}
    </div>`;
  const actions = document.createElement('div');
  if (flow.has_offers && !flow.is_synced) {
    actions.innerHTML = `
      <button class="btn-push bg-green-600 text-white px-3 py-1 rounded text-sm mr-2">Push to KT</button>
      <button class="btn-cancel bg-gray-500 text-white px-3 py-1 rounded text-sm">Cancel</button>`;
  }
  head.appendChild(actions);
  card.appendChild(head);

  if (!flow.has_offers) {
    const note = document.createElement('div');
    note.className = 'text-sm text-gray-500';
    note.textContent = 'Поток без офферов — детали не отображаются';
    card.appendChild(note);
    return card;
  }

  const table = document.createElement('table');
  table.className = 'w-full text-sm';
  table.innerHTML = `
    <thead><tr class="text-left text-gray-500 border-b">
      <th class="py-1 w-8">#</th><th>Оффер</th>
      <th class="w-24">Вес, %</th><th class="w-44">Pin</th><th class="w-40"></th>
    </tr></thead>`;
  const tbody = document.createElement('tbody');
  for (const o of flow.offers) tbody.appendChild(renderOfferRow(flow, o));
  table.appendChild(tbody);
  card.appendChild(table);

  const sum = flow.offers.filter(o => o.is_active).reduce((s, o) => s + o.share, 0);
  const sumRow = document.createElement('div');
  sumRow.className = `text-xs mt-1 ${sum === 100 ? 'text-gray-400' : 'text-orange-600 font-semibold'}`;
  sumRow.textContent = `Сумма активных весов: ${sum}%`;
  card.appendChild(sumRow);

  const addRow = document.createElement('div');
  addRow.className = 'mt-3 flex gap-2';
  addRow.innerHTML = `
    <input class="offer-search border rounded px-2 py-1 flex-1" placeholder="добавить офер (поиск)...">
    <button class="btn-add bg-blue-600 text-white px-3 py-1 rounded text-sm">Add offer</button>`;
  card.appendChild(addRow);

  // Wiring
  actions.querySelector('.btn-push')?.addEventListener('click', async () => {
    try { await API.pushFlow(flow.id); await load(); } catch (e) { showError(e); }
  });
  actions.querySelector('.btn-cancel')?.addEventListener('click', async () => {
    try { await API.cancelFlow(flow.id); await load(); } catch (e) { showError(e); }
  });

  let addId = null;
  const searchInput = addRow.querySelector('.offer-search');
  $(searchInput).autocomplete({
    minLength: 1,
    source: async (req, resp) => {
      try {
        const items = await API.searchOffers(req.term);
        resp(items.map(i => ({ label: `[${i.id}] ${i.name}`, value: i.name, id: i.id })));
      } catch (e) { resp([]); }
    },
    select: (ev, ui) => { addId = ui.item.id; return true; },
  });
  addRow.querySelector('.btn-add').addEventListener('click', async () => {
    if (!addId) { showError(new Error('Выбери офер из подсказок')); return; }
    try { await API.addOffer(flow.id, addId); await load(); } catch (e) { showError(e); }
  });

  return card;
}

function renderOfferRow(flow, o) {
  const tr = document.createElement('tr');
  tr.className = `border-b ${o.is_deleted_in_keitaro ? 'offer-grey' : ''} ${!o.is_active ? 'offer-removed' : ''}`;

  const badge = o.is_deleted_in_keitaro
    ? '<span class="ml-1 text-xs bg-gray-300 text-gray-700 px-1.5 rounded">удален в KT</span>'
    : (!o.is_active ? '<span class="ml-1 text-xs bg-gray-200 text-gray-600 px-1.5 rounded">в истории</span>' : '');

  tr.innerHTML = `
    <td class="py-1 text-gray-400">${o.position + 1}</td>
    <td>[${o.keitaro_offer_id}] ${escapeHtml(o.offer_name)} ${badge}</td>
    <td class="font-mono">${o.share}%</td>
    <td class="pin-cell"></td>
    <td class="text-right action-cell"></td>`;

  const pinCell = tr.querySelector('.pin-cell');
  const actCell = tr.querySelector('.action-cell');

  if (o.is_active) {
    if (o.pinned_share !== null) {
      pinCell.innerHTML = `<span class="text-purple-700 font-semibold">📌 ${o.pinned_share}%</span>`;
      pinCell.appendChild(mkBtn('Unpin', 'bg-purple-500',
        () => API.unpinOffer(flow.id, o.keitaro_offer_id)));
    } else {
      const input = document.createElement('input');
      input.type = 'number'; input.min = 0; input.max = 100; input.placeholder = '%';
      input.className = 'border rounded px-1 py-0.5 w-16';
      pinCell.appendChild(input);
      pinCell.appendChild(mkBtn('Pin', 'bg-purple-500', async () => {
        const val = parseInt(input.value, 10);
        if (Number.isNaN(val) || val < 0 || val > 100) throw new Error('Pin: укажи 0..100');
        await API.pinOffer(flow.id, o.keitaro_offer_id, val);
      }));
    }
    actCell.appendChild(mkBtn('Remove', 'bg-red-500',
      () => API.removeOffer(flow.id, o.keitaro_offer_id)));
  } else {
    actCell.appendChild(mkBtn('Bring back', 'bg-green-600',
      () => API.bringBack(flow.id, o.keitaro_offer_id)));
  }
  return tr;
}

function mkBtn(text, cls, handler) {
  const b = document.createElement('button');
  b.textContent = text;
  b.className = `${cls} text-white px-2 py-0.5 rounded text-xs ml-1`;
  b.onclick = async () => {
    try { 
      await handler(); 
      await load(); // Перерисовка после успешного действия
    } catch (e) { 
      showError(e); 
    }
  };
  return b;
}

document.getElementById('btn-fetch').onclick = async () => {
  try { await API.fetchStreams(CAMPAIGN_ID); await load(); } catch (e) { showError(e); }
};

load().catch(showError);