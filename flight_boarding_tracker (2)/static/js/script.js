function escapeHtml(value){return String(value ?? '').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}

async function postJSON(url, payload){const response=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const data=await response.json();if(!response.ok)throw new Error(data.error||data.message||'Request failed');return data;}

const sortButton=document.getElementById('quick-sort-btn');
if(sortButton){
  sortButton.addEventListener('click',async()=>{
    const key=document.getElementById('sort-key').value;
    const descending=document.getElementById('sort-order').value==='true';
    sortButton.disabled=true; sortButton.textContent='Sorting...';
    try{
      const data=await postJSON('/api/quick-sort',{records:window.sortRecords,key,descending});
      const tbody=document.querySelector('#after-table tbody');
      tbody.innerHTML=data.records.map(p=>`<tr><td>${escapeHtml(p.passenger_id)}</td><td>${escapeHtml(p.name)}</td><td>${escapeHtml(p.flight_number)}</td><td>${escapeHtml(p.seat_number)}</td><td>P${escapeHtml(p.priority)}</td></tr>`).join('');
      document.getElementById('sort-status').textContent='Sorted using Quick Sort';
      document.getElementById('sort-metrics').innerHTML=`<div class="metric"><span>Elements</span><b>${data.records.length}</b></div><div class="metric"><span>Execution Time</span><b>${data.metrics.time_ms} ms</b></div><div class="metric"><span>Comparisons</span><b>${data.metrics.comparisons}</b></div><div class="metric"><span>Swaps</span><b>${data.metrics.swaps}</b></div>`;
    }catch(e){alert(e.message)}finally{sortButton.disabled=false;sortButton.textContent='Sort Using Quick Sort'}
  });
}

const compareButton=document.getElementById('compare-btn');
if(compareButton){
  compareButton.addEventListener('click',async()=>{
    const key=document.getElementById('compare-key').value;
    compareButton.disabled=true;compareButton.textContent='Running...';
    try{
      const data=await postJSON('/api/compare',{key});
      const tbody=document.querySelector('#comparison-table tbody');
      tbody.innerHTML=data.results.map(r=>`<tr><td><b>${escapeHtml(r.algorithm)}</b></td><td>${r.input_size}</td><td>${r.time_ms}</td><td>${r.comparisons}</td><td>${r.swaps}</td></tr>`).join('');
      const chart=document.getElementById('time-chart'); const max=Math.max(...data.results.map(r=>Number(r.time_ms)),0.00001);
      chart.innerHTML=data.results.map(r=>`<div class="bar-item"><b>${escapeHtml(r.algorithm)}</b><div class="bar-track"><div class="bar-fill" style="width:${Math.max(2,Number(r.time_ms)/max*100)}%"></div></div><span>${r.time_ms} ms</span></div>`).join('');
      document.getElementById('compare-message').textContent='Completed using the same passenger dataset for every algorithm.';
    }catch(e){document.getElementById('compare-message').textContent=e.message}finally{compareButton.disabled=false;compareButton.textContent='Run Comparison'}
  });
}

const searchDemo=document.getElementById('search-demo-btn');
if(searchDemo){searchDemo.addEventListener('click',async()=>{const passenger_id=document.getElementById('search-passenger-id').value.trim();if(!passenger_id)return;searchDemo.disabled=true;try{const data=await postJSON('/api/passenger-search',{passenger_id});const box=document.getElementById('search-results');const render=(name,r)=>`<div class="result-box"><h4>${name}</h4><b class="${r.found?'found':'not-found'}">${r.found?'Found':'Not Found'}</b>${r.found?`<p>${escapeHtml(r.record.name)} · Flight ${escapeHtml(r.record.flight_number)}</p>`:''}<p>Comparisons: <b>${r.comparisons}</b><br>Execution time: <b>${r.time_ms} ms</b></p></div>`;box.innerHTML=render('Linear Search',data.linear)+render('Binary Search',data.binary)+`<p class="small-note">Binary Search was performed after ordering the records by Passenger ID using Quick Sort.</p>`}catch(e){alert(e.message)}finally{searchDemo.disabled=false}})}

const trackingForm=document.getElementById('tracking-form');
if(trackingForm){trackingForm.addEventListener('submit',async e=>{e.preventDefault();const flight=document.getElementById('tracking-flight').value.trim().toUpperCase();const msg=document.getElementById('tracking-message');const result=document.getElementById('tracking-result');msg.textContent='Requesting flight data...';result.classList.add('hidden');try{const r=await fetch(`${window.trackingUrl}?flight=${encodeURIComponent(flight)}`);const data=await r.json();if(!r.ok||!data.ok)throw new Error(data.message||'Flight data unavailable');const f=data.flight;document.getElementById('tracking-status').textContent=f.status||'Unknown';const fields=[['Flight Number',f.flight_number],['Airline',f.airline],['Departure Airport',f.departure_airport],['Arrival Airport',f.arrival_airport],['Departure Time',f.departure_time],['Arrival Time',f.arrival_time],['Departure Terminal',f.departure_terminal],['Departure Gate',f.departure_gate],['Arrival Terminal',f.arrival_terminal],['Arrival Gate',f.arrival_gate],['Latitude',f.latitude],['Longitude',f.longitude],['Altitude',f.altitude],['Speed',f.speed]];document.getElementById('tracking-details').innerHTML=fields.filter(x=>x[1]!==null&&x[1]!==undefined&&x[1]!=='').map(x=>`<div class="detail-item"><span>${x[0]}</span><b>${escapeHtml(x[1])}</b></div>`).join('');msg.textContent='Flight information received from Aviationstack.';result.classList.remove('hidden')}catch(err){msg.textContent='Live flight data is currently unavailable. You can still use the local flight management and DAA features.'} });}
