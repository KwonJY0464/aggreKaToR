window.allData = null;
window.radarDB = null;
window.profilesDB = null; // 💡 분리된 프로필 DB
window.currentMode = 'news';
window.currentCalDate = new Date();

let DOM = {};

document.addEventListener('DOMContentLoaded', async () => {
    DOM = {
        pane1Title:          document.getElementById('pane1-title'),
        pane2Title:          document.getElementById('pane2-title'),
        pane3Title:          document.getElementById('pane3-title'),
        pane2Tabs:           document.getElementById('pane2-tabs'),
        pane3Tabs:           document.getElementById('pane3-tabs'),
        pane1Content:        document.getElementById('pane1-content'),
        pane2Content:        document.getElementById('pane2-content'),
        pane3Content:        document.getElementById('pane3-content'),
        pane1AssemblyContent:document.getElementById('pane1-assembly-content'),
        calendarWrapper:     document.getElementById('calendar-wrapper'),
        newsLeftPane:        document.getElementById('news-left-pane'),
        assemblyLeftPane:    document.getElementById('assembly-left-pane'),
        time1News:           document.getElementById('time-1-news'),
        time1Assembly:       document.getElementById('time-1-assembly'),
        time2:               document.getElementById('time-2'),
        time3:               document.getElementById('time-3'),
        themeIcon:           document.getElementById('themeIcon'),
        searchContainer:     document.getElementById('member-search-container'),
        searchInput:         document.getElementById('member-search-input'),
        profilePane:         document.getElementById('profile-pane'),
        activityPane:        document.getElementById('activity-pane')
    };

    if (DOM.searchInput) {
        DOM.searchInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') searchMember();
        });
    }

    try {
        const radarRes = await fetch(`radar_db.json?t=${Date.now()}`);
        if (radarRes.ok) window.radarDB = await radarRes.json();
        
        // 💡 분리된 프로필 DB 호출
        const profRes = await fetch(`profiles_db.json?t=${Date.now()}`);
        if (profRes.ok) window.profilesDB = await profRes.json();
    } catch(e) { console.warn("DB 로드 중..."); }

    switchMode('news');
});

window.toggleTheme = function() {
    const b = document.body;
    const isDark = b.getAttribute('data-theme') === 'dark';
    b.setAttribute('data-theme', isDark ? 'light' : 'dark');
    DOM.themeIcon.innerText = isDark ? '🌙' : '☀️';
};

window.switchMode = async function(mode) {
    window.currentMode = mode;
    document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`mode-${mode}`).classList.add('active');

    if (mode === 'news') {
        document.documentElement.style.setProperty('--left-width', '350px');
        DOM.newsLeftPane.style.display = 'flex';
        DOM.assemblyLeftPane.style.display = 'none';
        DOM.searchContainer.style.display = 'none';
        DOM.profilePane.style.flex = '1';
        DOM.activityPane.style.flex = '1';
        await loadNewsData();
    } else {
        document.documentElement.style.setProperty('--left-width', '25vw');
        DOM.newsLeftPane.style.display = 'none';
        DOM.assemblyLeftPane.style.display = 'flex';
        DOM.searchContainer.style.display = 'flex';
        DOM.profilePane.style.flex = '1.6';
        DOM.activityPane.style.flex = '1';
        window.currentCalDate = new Date();
        await loadAssemblyData();
    }
};

function setHeaders({ title2, title3, useInnerHTML = false, clearTabs = false }) {
    if (useInnerHTML) {
        DOM.pane2Title.innerHTML = title2; DOM.pane3Title.innerHTML = title3;
    } else {
        DOM.pane2Title.innerText = title2; DOM.pane3Title.innerText = title3;
    }
    if (clearTabs) { DOM.pane2Tabs.innerHTML = ''; DOM.pane3Tabs.innerHTML = ''; }
}

async function loadNewsData() {
    try {
        setHeaders({ title2: '부처/기관 <span id="pane2-tabs"></span>', title3: 'AI 키워드 타게팅 <span id="pane3-tabs"></span>', useInnerHTML: true });
        DOM.pane2Tabs = document.getElementById('pane2-tabs'); DOM.pane3Tabs = document.getElementById('pane3-tabs');
        DOM.pane1Title.innerText = '인기뉴스';

        const res = await fetch(`news.json?t=${Date.now()}`);
        window.allData = await res.json();
        renderItems('pane1-content', window.allData.pane1);

        ['pane2', 'pane3'].forEach(id => {
            if (!window.allData[id]) return;
            const n = id.slice(-1); const kws = Object.keys(window.allData[id]);
            const t = document.getElementById(`pane${n}-tabs`);
            if (t && kws.length > 0) {
                t.innerHTML = kws.map((kw, i) => `<button class="tab-btn ${i===0?'active':''}" onclick="switchTab(${n},'${kw}',this)">${kw}</button>`).join('');
                switchTab(n, kws[0], t.firstChild);
            }
        });
        updateTimeDisplays(window.allData.last_updated, 'news');
    } catch (e) { DOM.pane1Content.innerHTML = "<div style='padding:20px;'>뉴스를 불러올 수 없습니다.</div>"; }
}

async function loadAssemblyData() {
    try {
        setHeaders({ title2: '의원 프로필 상세', title3: '활동 내역', clearTabs: true });
        const res = await fetch(`assembly.json?t=${Date.now()}`);
        const data = await res.json();
        window.allData = data;

        if (data.schedules) {
            renderSingleCalendar(data.schedules);
            const todayStr = new Date().toISOString().split('T')[0];
            const todayEl = document.querySelector(`.cal-day[data-date="${todayStr}"]`);
            if (todayEl) selectDate(todayStr, todayEl);
        }

        DOM.pane2Content.innerHTML = `<div style="padding:40px; text-align:center; opacity:0.6;">위 검색창에 타겟 의원 이름을 입력하여<br>추적을 시작하십시오.</div>`;
        DOM.pane3Content.innerHTML = `<div style="padding:40px; text-align:center; opacity:0.6;">대기 중...</div>`;
        updateTimeDisplays(data.last_updated, 'assembly');
    } catch (e) {}
}

window.changeMonth = function(offset) {
    window.currentCalDate.setDate(1); window.currentCalDate.setMonth(window.currentCalDate.getMonth() + offset);
    if (window.allData && window.allData.schedules) renderSingleCalendar(window.allData.schedules);
};

function renderSingleCalendar(schedules) {
    const year = window.currentCalDate.getFullYear(); const month = window.currentCalDate.getMonth();
    const days = ['일','월','화','수','목','금','토']; const firstDay = new Date(year, month, 1).getDay();
    const lastDate = new Date(year, month + 1, 0).getDate(); const todayStr = new Date().toISOString().split('T')[0];
    let html = `<div class="cal-header"><button class="cal-nav-btn" onclick="changeMonth(-1)">&#10094;</button><span>${year}년 ${month+1}월 국회 상황판</span><button class="cal-nav-btn" onclick="changeMonth(1)">&#10095;</button></div><div class="cal-grid">${days.map(d => `<div style="color:#999; padding-bottom:10px;">${d}</div>`).join('')}`;
    for (let i = 0; i < firstDay; i++) html += `<div></div>`;
    for (let d = 1; d <= lastDate; d++) {
        const dateStr = `${year}-${String(month+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
        const hasSanja = schedules.some(s => s.date === dateStr && s.type === 'sanja'); const hasGihyu = schedules.some(s => s.date === dateStr && s.type === 'gihyu'); const isToday = (todayStr === dateStr);
        html += `<div class="cal-day ${isToday?'today':''}" data-date="${dateStr}" onclick="selectDate('${dateStr}', this)"><span>${d}</span><div class="cal-dots-container">${hasSanja ? '<span class="cal-dot dot-sanja"></span>' : ''}${hasGihyu ? '<span class="cal-dot dot-gihyu"></span>' : ''}</div></div>`;
    }
    DOM.calendarWrapper.innerHTML = `<div class="single-calendar">${html}</div></div>`;
}

window.selectDate = function(date, el) {
    document.querySelectorAll('.cal-day').forEach(d => d.classList.remove('selected')); if (el) el.classList.add('selected');
    if (window.allData && window.allData.schedules) renderItems('pane1-assembly-content', window.allData.schedules.filter(s => s.date === date));
};

function renderItems(targetId, items) {
    const container = document.getElementById(targetId); if (!container) return;
    if (!items || items.length === 0) { container.innerHTML = `<div style="padding:40px; text-align:center; color:#999;">해당 항목에 데이터가 없습니다.</div>`; return; }
    container.innerHTML = items.map(item => {
        let dot = "";
        if (window.currentMode === 'assembly' && item.type !== 'session') {
            dot = `<div class="type-dot" style="background:${item.type === 'sanja' ? 'var(--sanja-color)' : 'var(--gihyu-color)'}"></div>`;
        }
        return `<div class="item" onclick="if('${item.link||''}' && '${item.link}' !== '#') window.open('${item.link}', '_blank')"><h3>${dot}${item.title}</h3><p>${item.ai_summary || ''}</p><span class="meta">${item.meta || item.formatted_date || item.time}</span></div>`;
    }).join('');
}

window.switchTab = function(p, kw, btn) {
    document.querySelectorAll(`#pane${p}-tabs .tab-btn`).forEach(b => b.classList.remove('active')); if (btn) btn.classList.add('active');
    if (window.allData && window.allData[`pane${p}`]) renderItems(`pane${p}-content`, window.allData[`pane${p}`][kw]);
};

function updateTimeDisplays(ts, mode) {
    const time = ts ? ts.substring(11, 16) : '--:--';
    const els = (mode === 'news') ? [DOM.time1News, DOM.time2, DOM.time3] : [DOM.time1Assembly, DOM.time2, DOM.time3];
    els.forEach(el => { if (el) el.innerText = `업데이트: ${time}`; });
}

// ==========================================
// 🚀 국회의원 타겟 추적 레이더 (프로필 DB 완전 분리)
// ==========================================

window.searchMember = function() {
    if (!DOM.searchInput) return;
    const name = DOM.searchInput.value.trim();
    if (!name) return;
    if (!window.profilesDB) { alert("profiles_db.json 파일이 로드되지 않았습니다."); return; }

    const info = window.profilesDB.find(p => p.HG_NM === name);
    if (!info) {
        DOM.pane2Content.innerHTML = `<div style="padding:40px; text-align:center; color:#e74c3c;">'${name}' 의원을 찾을 수 없습니다.</div>`;
        DOM.pane3Content.innerHTML = '';
        return;
    }

    const photoUrl = info.NAAS_PIC;

    let displayName = info.HG_NM;
    if (info.HOMEPAGE && info.HOMEPAGE.startsWith("http")) {
        displayName = `<a href="${info.HOMEPAGE}" target="_blank" style="color:var(--news-title); text-decoration:none;" title="홈페이지 이동">🔗 ${info.HG_NM}</a>`;
    }

    // 💡 정당별 퍼스널 컬러 지정 로직
    let partyColor = 'var(--accent)'; // 기본 테마색
    let partyName = info.POLY_NM || '무소속';
    
    if (partyName.includes('더불어민주')) {
        partyColor = '#230b8a'; // 짙은파란색
    } else if (partyName.includes('국민의')) {
        partyColor = '#E61E2B'; // 빨간색
    } else if (partyName.includes('개혁신당')) {
        partyColor = '#FF7A1F'; // 주황색
    } else if (partyName.includes('조국')) {
        partyColor = '#0073CF'; // 밝은 하늘색
    }

    DOM.pane2Title.innerText = "의원 프로필 상세";
    DOM.pane2Content.innerHTML = `
        <div style="padding: 15px; background: var(--card); height: 100%; box-sizing: border-box;">
            <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 15px;">
                <img src="${photoUrl}" alt="사진 없음" style="width: 85px; height: 110px; border-radius: 6px; object-fit: cover; border: 1px solid var(--border); background: #333;">
                <div>
                    <h2 style="margin: 0; font-size: 1.6rem;">${displayName}</h2>
                    <span style="display: inline-block; margin-top: 5px; padding: 3px 8px; background: ${partyColor}; color: #ffffff; border-radius: 4px; font-weight: bold; font-size: 0.85rem;">
                        ${partyName}
                    </span>
                </div>
            </div>

            <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem; border: 1px solid var(--border);">
                <tr>
                    <th style="width: 15%; background: rgba(255,255,255,0.05); padding: 8px; border: 1px solid var(--border); color: var(--accent);">선거구</th>
                    <td style="width: 30%; padding: 8px; border: 1px solid var(--border);">${info.ORIG_NM}</td>
                    <th rowspan="6" style="width: 15%; background: rgba(255,255,255,0.05); padding: 8px; border: 1px solid var(--border); text-align: center; color: var(--accent);">주요경력</th>
                    <td rowspan="6" style="width: 40%; padding: 12px; border: 1px solid var(--border); vertical-align: top; line-height: 1.6; white-space: pre-wrap;">${info.MEM_TITLE || '정보 없음'}</td>
                </tr>
                <tr>
                    <th style="background: rgba(255,255,255,0.05); padding: 8px; border: 1px solid var(--border); color: var(--accent);">소속위원회</th>
                    <td style="padding: 8px; border: 1px solid var(--border);">${info.CMITS}</td>
                </tr>
                <tr>
                    <th style="background: rgba(255,255,255,0.05); padding: 8px; border: 1px solid var(--border); color: var(--accent);">당선횟수</th>
                    <td style="padding: 8px; border: 1px solid var(--border);">${info.REELE_GBN_NM} (${info.UNITS})</td>
                </tr>
                <tr>
                    <th style="background: rgba(255,255,255,0.05); padding: 8px; border: 1px solid var(--border); color: var(--accent);">보좌관</th>
                    <td style="padding: 8px; border: 1px solid var(--border);">${info.STAFF || '정보 없음'}</td>
                </tr>
                <tr>
                    <th style="background: rgba(255,255,255,0.05); padding: 8px; border: 1px solid var(--border); color: var(--accent);">선임비서관</th>
                    <td style="padding: 8px; border: 1px solid var(--border);">${info.SECRETARY || '정보 없음'}</td>
                </tr>
                <tr>
                    <th style="background: rgba(255,255,255,0.05); padding: 8px; border: 1px solid var(--border); color: var(--accent);">비서관</th>
                    <td style="padding: 8px; border: 1px solid var(--border);">${info.SECRETARY2 || '정보 없음'}</td>
                </tr>
            </table>
        </div>
    `;

    DOM.pane3Title.innerHTML = `활동 내역 (최근 30건 기준)
        <span id="pane3-tabs">
            <button class="tab-btn active" onclick="switchActivityTab('${name}', 'bills', this)">발의의안</button>
            <button class="tab-btn" onclick="switchActivityTab('${name}', 'minutes', this)">회의발언</button>
            <button class="tab-btn" onclick="switchActivityTab('${name}', 'votes', this)">본회의투표</button>
        </span>`;
    
    switchActivityTab(name, 'bills', document.querySelector('#pane3-tabs .tab-btn'));
};

window.switchActivityTab = function(name, type, btn) {
    document.querySelectorAll('#pane3-tabs .tab-btn').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');

    let items = [];
    if (!window.radarDB) return;

    if (type === 'bills') {
        items = (window.radarDB.bills || []).filter(b => ((b.RST_PROPOSER || "").includes(name)) || ((b.PROPOSER || "").includes(name)))
        .map(r => ({ title: `[의안] ${r.BILL_NM || ''}`, meta: `제안일: ${r.PROPOSER_DT || ''}`, link: r.LINK_URL || '#' }));
    } else if (type === 'minutes') {
        items = (window.radarDB.minutes || []).filter(m => ((m.SPK_FIRST_NM || "").includes(name)) || ((m.SUB_NAME || "").includes(name)))
        .map(r => ({ title: `[발언] ${r.COMM_NAME || ''} - ${r.SUB_NAME || ''}`, meta: `회의일: ${r.MEET_DATE || ''}`, link: r.CONF_LINK_URL || r.PDF_LINK_URL || '#' }));
    } else if (type === 'votes') {
        items = (window.radarDB.votes || []).filter(v => (v.HG_NM || "").trim() === name)
        .map(r => {
            let resultColor = 'var(--text)';
            if(r.RESULT_VOTE_NM === '찬성') resultColor = 'var(--sanja-color)';
            if(r.RESULT_VOTE_NM === '반대') resultColor = '#e74c3c';
            return { title: `[투표] ${r.BILL_NM || ''}`, meta: `결과: <b style="color:${resultColor};">${r.RESULT_VOTE_NM || '미투표'}</b> | 표결일: ${r.VOTE_DATE || ''}`, link: '#' };
        });
    }

    renderItems('pane3-content', items);
};
