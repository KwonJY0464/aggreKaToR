let allData = null;
let currentMode = 'news';

const resizer = document.getElementById('resizer');
if (resizer) {
    resizer.addEventListener('mousedown', () => {
        document.addEventListener('mousemove', handleResizing);
        document.addEventListener('mouseup', () => document.removeEventListener('mousemove', handleResizing));
    });
}

function handleResizing(e) {
    const x = e.clientX;
    if (x > 300 && x < window.innerWidth - 350) {
        document.documentElement.style.setProperty('--left-width', `${x}px`);
    }
}

function toggleTheme() {
    const b = document.body; const isDark = b.getAttribute('data-theme') === 'dark';
    b.setAttribute('data-theme', isDark ? 'light' : 'dark');
    document.getElementById('themeIcon').innerText = isDark ? '🌙' : '☀️';
}

async function switchMode(mode) {
    currentMode = mode;
    document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`mode-${mode}`).classList.add('active');
    
    // 💡 두 모드의 좌측 패널을 완전히 독립적으로 제어
    const newsLeft = document.getElementById('news-left-pane');
    const assemblyLeft = document.getElementById('assembly-left-pane');

    if (mode === 'news') {
        newsLeft.style.display = 'flex';
        assemblyLeft.style.display = 'none';
        await loadNewsData();
    } else {
        newsLeft.style.display = 'none';
        assemblyLeft.style.display = 'flex';
        await loadAssemblyData();
    }
}

// 🚨 실수로 날렸던 뉴스 렌더링 로직 100% 복구 완료
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
        // 뉴스 전용 시간표시기에 업데이트
        ['time-1-news', 'time-2', 'time-3'].forEach(id => {
            const el = document.getElementById(id);
            if(el) el.innerText = ts;
        });
    } catch (e) {
        document.getElementById('pane1-content').innerHTML = "<div style='padding:20px;'>데이터를 불러오는 중입니다...</div>";
    }
}

async function loadAssemblyData() {
    try {
        const res = await fetch(`assembly.json?t=${Date.now()}`);
        const data = await res.json();
        allData = data; 
        
        renderDualCalendar(data.schedules);
        
        document.getElementById('pane2-title').innerText = "입법/정책 동향";
        document.getElementById('pane3-title').innerText = "AI 요약";
        
        const t2 = document.getElementById('pane2-tabs'); if(t2) t2.innerHTML = '';
        const t3 = document.getElementById('pane3-tabs'); if(t3) t3.innerHTML = '';

        document.getElementById('pane2-content').innerHTML = `<div style="padding:40px; text-align:center; opacity:0.4;">의안 데이터 API 연동 대기 중</div>`;
        document.getElementById('pane3-content').innerHTML = `<div style="padding:20px; line-height:1.8;">${data.summary ? data.summary.replace(/\n/g, '<br>') : '요약 정보가 없습니다.'}</div>`;
        
        const ts = `업데이트: ${data.last_updated.substring(11, 16)}`;
        // 국회 전용 시간표시기에 업데이트
        ['time-1-assembly', 'time-2', 'time-3'].forEach(id => {
            const el = document.getElementById(id);
            if(el) el.innerText = ts;
        });
    } catch (e) { console.error(e); }
}

function renderDualCalendar(schedules) {
    const wrapper = document.getElementById('calendar-wrapper');
    const now = new Date();
    const next = new Date(now.getFullYear(), now.getMonth() + 1, 1);
    
    wrapper.innerHTML = `<div class="dual-calendar">
        ${generateMonthHTML(now.getFullYear(), now.getMonth(), schedules)}
        ${generateMonthHTML(next.getFullYear(), next.getMonth(), schedules)}
    </div>`;
}

function generateMonthHTML(year, month, schedules) {
    const days = ['일','월','화','수','목','금','토'];
    const firstDay = new Date(year, month, 1).getDay();
    const lastDate = new Date(year, month + 1, 0).getDate();
    
    let html = `<div class="cal-month">
        <div style="text-align:center; font-weight:bold; margin-bottom:8px;">${year}년 ${month+1}월</div>
        <div class="cal-grid">${days.map(d => `<div style="color:#999">${d}</div>`).join('')}`;
    
    for(let i=0; i<firstDay; i++) html += `<div></div>`;
    for(let d=1; d<=lastDate; d++) {
        const dateStr = `${year}-${String(month+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
        const hasSanja = schedules.some(s => s.date === dateStr && s.type === 'sanja');
        const hasGihyu = schedules.some(s => s.date === dateStr && s.type === 'gihyu');
        const isToday = new Date().toISOString().split('T')[0] === dateStr;
        
        html += `<div class="cal-day ${isToday?'today':''}" onclick="selectDate('${dateStr}', this)">
            ${d}
            <div style="height:4px;">
                ${hasSanja ? '<span class="cal-dot dot-sanja"></span>' : ''}
                ${hasGihyu ? '<span class="cal-dot dot-gihyu"></span>' : ''}
            </div>
        </div>`;
    }
    return html + `</div></div>`;
}

function selectDate(date, el) {
    document.querySelectorAll('.cal-day').forEach(d => d.classList.remove('selected'));
    el.classList.add('selected');
    
    const daySchedules = allData.schedules.filter(s => s.date === date);
    // 국회 전용 컨텐츠 영역에만 렌더링
    renderItems('pane1-assembly-content', daySchedules);
}

function renderItems(targetId, items) {
    const container = document.getElementById(targetId);
    if (!items || items.length === 0) {
        container.innerHTML = `<div style="padding:40px; text-align:center; color:#999;">해당 날짜에 일정이 없습니다.</div>`;
        return;
    }
    container.innerHTML = items.map(item => {
        let dot = "";
        // 국회수집기일 때만 색상 점 생성
        if(currentMode === 'assembly' && item.type !== 'session') {
            const dotColor = item.type === 'sanja' ? 'var(--sanja-color)' : 'var(--gihyu-color)';
            dot = `<div class="type-dot" style="background:${dotColor}"></div>`;
        }
        return `
        <div class="item" onclick="if('${item.link}') window.open('${item.link}', '_blank')">
            <h3>${dot}${item.title.replace(/<[^>]*>?/gm, '')}</h3>
            ${item.ai_summary ? `<p>${item.ai_summary}</p>` : ''}
            <span class="meta">${item.formatted_date || (item.time + ' | ' + item.committee + ' | ' + (item.location || '장소미정'))}</span>
        </div>`;
    }).join('');
}

function switchTab(p, kw, btn) {
    document.querySelectorAll(`#pane${p}-tabs .tab-btn`).forEach(b => b.classList.remove('active'));
    btn.classList.add('active'); 
    renderItems(`pane${p}-content`, allData[`pane${p}`][kw]);
}

switchMode('news');
