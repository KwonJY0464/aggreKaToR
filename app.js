window.allData = null;
window.radarDB = null;
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
    } catch(e) { console.warn("레이더 DB 대기 중..."); }

    const resizer = document.getElementById('resizer');
    let isResizing = false;
    if (resizer) {
        resizer.addEventListener('mousedown', () => { isResizing = true; });
        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;
            const x = e.clientX;
            if (x > 300 && x < window.innerWidth - 350) {
                document.documentElement.style.setProperty('--left-width', `${x}px`);
            }
        });
        document.addEventListener('mouseup', () => { isResizing = false; });
    }

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
    const activeBtn = document.getElementById(`mode-${mode}`);
    if (activeBtn) activeBtn.classList.add('active');

    if (mode === 'news') {
        document.documentElement.style.setProperty('--left-width', '350px');
        
        if (DOM.newsLeftPane) DOM.newsLeftPane.style.display = 'flex';
        if (DOM.assemblyLeftPane) DOM.assemblyLeftPane.style.display = 'none';
        if (DOM.searchContainer) DOM.searchContainer.style.display = 'none';
        if (DOM.profilePane) DOM.profilePane.style.flex = '1';
        if (DOM.activityPane) DOM.activityPane.style.flex = '1';
        
        await loadNewsData();
    } else {
        document.documentElement.style.setProperty('--left-width', '25vw');
        
        if (DOM.newsLeftPane) DOM.newsLeftPane.style.display = 'none';
        if (DOM.assemblyLeftPane) DOM.assemblyLeftPane.style.display = 'flex';
        if (DOM.searchContainer) DOM.searchContainer.style.display = 'flex';
        if (DOM.profilePane) DOM.profilePane.style.flex = '1.6';
        if (DOM.activityPane) DOM.activityPane.style.flex = '1';
        
        window.currentCalDate = new Date();
        await loadAssemblyData();
    }
};

function setHeaders({ title2, title3, useInnerHTML = false, clearTabs = false }) {
    if (DOM.pane2Title) useInnerHTML ? (DOM.pane2Title.innerHTML = title2) : (DOM.pane2Title.innerText = title2);
    if (DOM.pane3Title) useInnerHTML ? (DOM.pane3Title.innerHTML = title3) : (DOM.pane3Title.innerText = title3);
    if (clearTabs) {
        if (DOM.pane2Tabs) DOM.pane2Tabs.innerHTML = '';
        if (DOM.pane3Tabs) DOM.pane3Tabs.innerHTML = '';
    }
}

async function loadNewsData() {
    try {
        setHeaders({ title2: '부처/기관 <span id="pane2-tabs"></span>', title3: 'AI 키워드 타게팅 <span id="pane3-tabs"></span>', useInnerHTML: true });
        DOM.pane2Tabs = document.getElementById('pane2-tabs'); DOM.pane3Tabs = document.getElementById('pane3-tabs');
        if (DOM.pane1Title) DOM.pane1Title.innerText = '인기뉴스';

        const res = await fetch(`news.json?t=${Date.now()}`);
        if (!res.ok) throw new Error("news.json 로드 실패");
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
    } catch (e) {
        if (DOM.pane1Content) DOM.pane1Content.innerHTML = "<div style='padding:20px; color:#999;'>뉴스를 불러올 수 없습니다.</div>";
    }
}

async function loadAssemblyData() {
    try {
        setHeaders({ title2: '의원 프로필 상세', title3: '활동 내역', clearTabs: true });
        const res = await fetch(`assembly.json?t=${Date.now()}`);
        if (!res.ok) throw new Error("assembly.json 로드 실패");
        const data = await res.json();
        window.allData = data;

        if (data.schedules) {
            renderSingleCalendar(data.schedules);
            const todayStr = new Date().toISOString().split('T')[0];
            const todayEl = document.querySelector(`.cal-day[data-date="${todayStr}"]`);
            if (todayEl) selectDate(todayStr, todayEl);
        }

        if (DOM.pane2Content) DOM.pane2Content.innerHTML = `<div style="padding:40px; text-align:center; opacity:0.6;">위 검색창에 타겟 의원 이름을 입력하여<br>추적을 시작하십시오.</div>`;
        if (DOM.pane3Content) DOM.pane3Content.innerHTML = `<div style="padding:40px; text-align:center; opacity:0.6;">대기 중...</div>`;
        updateTimeDisplays(data.last_updated, 'assembly');
    } catch (e) { console.error("Assembly Load Error:", e); }
}

window.changeMonth = function(offset) {
    window.currentCalDate.setDate(1); window.currentCalDate.setMonth(window.currentCalDate.getMonth() + offset);
    if (window.allData && window.allData.schedules) renderSingleCalendar(window.allData.schedules);
};

function renderSingleCalendar(schedules) {
    if (!DOM.calendarWrapper) return;
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
            const dotColor = item.type === 'sanja' ? 'var(--sanja-color)' : 'var(--gihyu-color)';
            dot = `<div class="type-dot" style="background:${dotColor}"></div>`;
        }
        const titleText = item.title ? item.title.replace(/<[^>]*>?/gm, '') : '제목 없음';
        const pText = item.ai_summary || item.time || ''; const pTag = pText ? `<p>${pText}</p>` : '';
        const metaText = item.formatted_date || (item.time + ' | ' + (item.committee||'') + ' | ' + (item.location || '장소미정'));
        return `<div class="item" onclick="if('${item.link||''}' && '${item.link}' !== '#') window.open('${item.link}', '_blank')"><h3>${dot}${titleText}</h3>${pTag}<span class="meta">${metaText}</span></div>`;
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
// 🚀 국회의원 타겟 추적 레이더 (최종 본회의/사진/링크 패치)
// ==========================================

window.searchMember = function() {
    if (!DOM.searchInput) return;
    const name = DOM.searchInput.value.trim();
    if (!name) { alert("의원 이름을 입력하십시오."); return; }
    if (!window.radarDB) { alert("파이썬 정찰대가 만든 레이더 DB(radar_db.json)가 아직 로드되지 않았습니다."); return; }

    const info = window.radarDB.profiles.find(p => p.HG_NM === name);
    if (!info) {
        DOM.pane2Content.innerHTML = `<div style="padding:40px; text-align:center; color:#e74c3c;">제22대 현역 의원 중 '${name}' 의원을 찾을 수 없습니다.</div>`;
        DOM.pane3Content.innerHTML = '';
        return;
    }

    // 💡 사진 우선순위 적용 (API가 내려준 텍스트 주소가 최우선)
    const photoUrl = info.NAAS_PIC || `https://www.assembly.go.kr/static/portal/img/open_data/member/${info.MONA_CD}.jpg`;

    // 💡 홈페이지 링크 동적 생성 (정보가 있을 때만 클릭 가능하도록 처리)
    let nameHtml = `<h2 style="margin: 0; font-size: 1.6rem; color: var(--news-title);">${info.HG_NM}</h2>`;
    if (info.HOMEPAGE && info.HOMEPAGE.startsWith("http")) {
        nameHtml = `<h2 style="margin: 0; font-size: 1.6rem; color: var(--news-title); cursor: pointer;" onclick="window.open('${info.HOMEPAGE}', '_blank')" title="홈페이지 열기">🔗 ${info.HG_NM}</h2>`;
    }

    DOM.pane2Title.innerText = "의원 프로필 상세";
    DOM.pane2Content.innerHTML = `
        <div style="padding: 15px; background: var(--card); height: 100%; box-sizing: border-box;">
            
            <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 15px;">
                <img src="${info.NAAS_PIC}" onerror="this.src='https://www.assembly.go.kr/photo/${info.MONA_CD}.jpg'" 
                     style="width: 120px; height: 160px; border-radius: 6px; object-fit: cover; border: 1px solid var(--border); background: #333;">
                <div>
                    ${nameHtml}
                    <span style="display: inline-block; margin-top: 5px; padding: 3px 8px; background: var(--accent); color: var(--bg); border-radius: 4px; font-weight: bold; font-size: 0.85rem;">
                        ${info.POLY_NM}
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

    DOM.pane3Title.innerHTML = `활동 내역 (최근 데이터 기준)
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
    if (type === 'bills') {
        items = window.radarDB.bills.filter(b => 
            (b.RST_PROPOSER && b.RST_PROPOSER.includes(name)) || (b.PROPOSER && b.PROPOSER.includes(name))
        ).map(r => ({ title: `[의안] ${r.BILL_NM}`, meta: `제안일: ${r.PROPOSER_DT}`, link: r.LINK_URL }));
    } else if (type === 'minutes') {
        items = window.radarDB.minutes.filter(m => 
            (m.SPK_FIRST_NM && m.SPK_FIRST_NM.includes(name)) || (m.SUB_NAME && m.SUB_NAME.includes(name))
        ).map(r => ({ title: `[발언] ${r.COMM_NAME} - ${r.SUB_NAME}`, meta: `회의일: ${r.MEET_DATE}`, link: r.CONF_LINK_URL || r.PDF_LINK_URL || '#' }));
    } else if (type === 'votes') {
        // 💡 3번 칸: 파이썬이 AGE=22로 긁어온 표결 데이터 출력
        items = window.radarDB.votes.filter(v => v.HG_NM === name)
        .map(r => ({
            title: `[투표] ${r.BILL_NM}`,
            meta: `결과: <b style="color:${r.RESULT === '찬성' ? 'var(--sanja-color)' : '#e74c3c'}">${r.RESULT}</b> | 일시: ${r.DATE}`,
            link: '#'
            };
        });
    }

    renderItems('pane3-content', items);
};
