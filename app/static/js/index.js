let selectedOfferId = null;

async function renderCampaigns() {
  const list = await API.listCampaigns();
  const root = document.getElementById('campaigns');
  root.innerHTML = '';
  if (!list.length) {
    root.innerHTML = '<div class="p-4 text-gray-500">Пока нет кампаний</div>';
    return;
  }
  for (const c of list) {
    const row = document.createElement('a');
    row.href = `/campaigns/${c.id}`;
    row.className = 'block px-4 py-3 hover:bg-gray-50 flex justify-between items-center';
    row.innerHTML = `
      <span class="font-medium">${escapeHtml(c.name)}
        <span class="text-gray-400 text-sm">#${c.keitaro_campaign_id}</span></span>
      <span class="text-sm ${c.is_dirty ? 'text-yellow-600 font-semibold' : 'text-gray-400'}">
        ${c.is_dirty ? 'есть изменения' : 'synced'}</span>`;
    root.appendChild(row);
  }
}

document.getElementById('btn-new').onclick = () =>
  document.getElementById('create-panel').classList.toggle('hidden');

document.getElementById('btn-create').onclick = async () => {
  const name = document.getElementById('f-name').value.trim();
  const geo = document.getElementById('f-geo').value
    .split(',').map(s => s.trim().toUpperCase()).filter(Boolean);
  if (!name || !geo.length || !selectedOfferId) {
    showError(new Error('Заполни name, geo и выбери офер из подсказок'));
    return;
  }
  try {
    const camp = await API.createCampaign({ name, geo, offer_id: selectedOfferId });
    location.href = `/campaigns/${camp.id}`;
  } catch (e) { showError(e); }
};

$(function () {
  $('#f-offer').autocomplete({
    minLength: 1,
    source: async (req, resp) => {
      try {
        const items = await API.searchOffers(req.term);
        resp(items.map(i => ({ label: `[${i.id}] ${i.name}`, value: i.name, id: i.id })));
      } catch (e) { resp([]); }
    },
    select: (ev, ui) => { selectedOfferId = ui.item.id; return true; },
  });
  renderCampaigns().catch(showError);
});