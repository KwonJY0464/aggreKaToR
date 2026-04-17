let allData = null;
let currentMode = 'news';

const resizer = document.getElementById('resizer');
const wrapper = document.getElementById('mainWrapper');
let isResizing = false;

if (resizer) {
    resizer.addEventListener('mousedown', () => isResizing = true);
    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        const x = e.clientX;
        if (x > 300 && x < window.innerWidth - 350) {
            document.documentElement.style.setProperty('--left-width', `${x}px`);
        }
    });
    document.addEventListener('mouseup', () => isResizing = false);
}

function toggleTheme() {
    const b = document.body; const isDark = b.getAttribute('data-theme') === 'dark';
    b.setAttribute('data-theme', isDark ? 'light' : 'dark');
    document.getElementById('themeIcon').innerText = isDark ? '🌙' : '☀️';
}

function renderItems(targetId, items) {
    const container = document.getElementById(targetId);
    if (!items || items.length === 0) {
        container.innerHTML = "<div style='padding:20px; color:#999;'>데이터가 없습니다.</div>";
        return;
    }
    container.innerHTML = items.map(item => `
        <div class="item" onclick="if('${item.link}') window.open('${item.link}', '_blank')">
            <h3>${item.title.replace(/<[^>]*>?/gm, '')}</h3>
            <p>${item.ai_summary || item.time || ''}</p>
            <span class="meta">${item.formatted_date || (item.committee ? item.committee + ' | ' + item.location : '')}</span>
        </div>`).join('');
}

function switchTab(p, kw, btn) {
    document.querySelectorAll(`#pane${p}-tabs .tab-btn`).forEach(b => b.classList.remove('active'));
    btn.classList.add('active'); 
    renderItems(`pane${p}-content`, allData[`pane${p}`][kw]);
}

async function switchMode(mode) {
    currentMode = mode;
    document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`mode-${mode}`).classList.add('active');
    
    if (mode === 'news') await loadNewsData();
    else await loadAssemblyData();
}

async function loadNewsData() {
    document.getElementById('pane1-title').innerText = "인기뉴스";
    document.getElementById('pane2-title').innerHTML = '부처/기관 <span id="pane2-tabs"></span>';
    document.getElementById('pane3-title').innerHTML = 'AI 키워드 타게팅 <span id="pane3-tabs"></span>';
    
    try {
        const res = await fetch(`news.json?t=${Date.now()}`); 
        if (!res.ok) throw new Error();
        allData = await res.json();
        
        renderItems('pane1-content', allData.pane1);
        ['pane2', 'pane3'].forEach(id => {
            const n = id.slice(-1); 
            const kws = Object.keys(allData[id]);
            const t = document.getElementById(`pane${n}-tabs`);
            if(t) {
                t.innerHTML = kws.map((kw, i) => `<button class="tab-btn ${i===0?'active':''}" onclick="switchTab(${n},'${kw}',this)">${kw}</button>`).join('');
                switchTab(n, kws[0], t.firstChild);
            }
        });
        const ts = `업데이트: ${allData.last_updated.substring(11, 16)}`;
        ['1','2','3'].forEach(n => document.getElementById(`time-${n}`).innerText = ts);
    } catch (e) {
        document.getElementById('pane1-content').innerHTML = "<div style='padding:20px;'>데이터를 불러오는 중입니다...</div>";
    }
}

async function loadAssemblyData() {
    document.getElementById('pane1-title').innerText = "핵심 의사일정";
    document.getElementById('pane2-title').innerText = "입법/정책 동향";
    document.getElementById('pane3-title').innerText = "AI 요약";
    
    const t2 = document.getElementById('pane2-tabs'); if(t2) t2.innerHTML = '';
    const t3 = document.getElementById('pane3-tabs'); if(t3) t3.innerHTML = '';

    try {
        const res = await fetch(`assembly.json?t=${Date.now()}`);
        if (!res.ok) throw new Error();
        const data = await res.json();
        
        renderItems('pane1-content', data.schedules);
        document.getElementById('pane2-content').innerHTML = `<div style="padding:50px; text-align:center; opacity:0.4;">의안 데이터 API 연동 대기 중</div>`;
        document.getElementById('pane3-content').innerHTML = `<div class="ai-box">${data.summary ? data.summary.replace(/\n/g, '<br>') : '요약 정보가 없습니다.'}</div>`;
        
        const ts = `업데이트: ${data.last_updated.substring(11, 16)}`;
        ['1','2','3'].forEach(n => document.getElementById(`time-${n}`).innerText = ts);
    } catch (e) {
        document.getElementById('pane1-content').innerHTML = "<div style='padding:20px;'>데이터가 아직 생성되지 않았습니다.</div>";
        document.getElementById('pane2-content').innerHTML = "";
        document.getElementById('pane3-content').innerHTML = "";
    }
}

// 초기 실행
switchMode('news');
