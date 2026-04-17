window.allData = null;
window.currentMode = 'news';
window.currentCalDate = new Date();

let DOM = {};

document.addEventListener('DOMContentLoaded', () => {
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
    };

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
        if (DOM.newsLeftPane)     DOM.newsLeftPane.style.display = 'flex';
        if (DOM.assemblyLeftPane) DOM.assemblyLeftPane.style.display = 'none';
        await loadNewsData();
    } else {
        if (DOM.newsLeftPane)     DOM.newsLeftPane.style.display = 'none';
        if (DOM.assemblyLeftPane) DOM.assemblyLeftPane.style.display = 'flex';
        window.currentCalDate = new Date();
        await loadAssemblyData();
    }
};

function setHeaders({ title2, title3, useInnerHTML = false, clearTabs = false }) {
    if (DOM.pane2Title) {
        useInnerHTML
            ? (DOM.pane2Title.innerHTML = title2)
            : (DOM.pane2Title.innerText = title2);
    }
    if (DOM.pane3Title) {
        useInnerHTML
            ? (DOM.pane3Title.innerHTML = title3)
            : (DOM.pane3Title.innerText = title3);
    }
    if (clearTabs) {
        if (DOM.pane2Tabs) DOM.pane2Tabs.innerHTML = '';
        if (DOM.pane3Tabs) DOM.pane3Tabs.innerHTML = '';
    }
}

async function loadNewsData() {
    try {
        setHeaders({
            title2: '부처/기관 <span id="pane2-tabs"></span>',
            title3: 'AI 키워드 타게팅 <span id="pane3-tabs"></span>',
            useInnerHTML: true,
        });

        DOM.pane2Tabs = document.getElementById('pane2-tabs');
        DOM.pane3Tabs = document.getElementById('pane3-tabs');

        if (DOM.pane1Title) DOM.pane1Title.innerText = '인기뉴스';

        const res = await fetch(`news.json?t=${Date.now()}`);
        if (!res.ok) throw new Error("news.json 로드 실패");
        window.allData = await res.json();

        renderItems('pane1-content', window.allData.pane1);

        ['pane2', 'pane3'].forEach(id => {
            if (!window.allData[id]) return;
            const n = id.slice(-1);
            const kws = Object.keys(window.allData[id]);
            const t = document.getElementById(`pane${n}-tabs`);
            if (t && kws.length > 0) {
                t.innerHTML = kws.map((kw, i) =>
                    `<button class="tab-btn ${i===0?'active':''}" onclick="switchTab(${n},'${kw}',this)">${kw}</button>`
                ).join('');
                switchTab(n, kws[0], t.firstChild);
            }
        });

        updateTimeDisplays(window.allData.last_updated, 'news');
    } catch (e) {
        console.error("News Load Error:", e);
        if (DOM.pane1Content) DOM.pane1Content.innerHTML = "<div style='padding:20px; color:#999;'>뉴스를 불러올 수 없습니다.</div>";
    }
}

async function loadAssemblyData() {
    try {
        setHeaders({
            title2: '입법/정책 동향',
            title3: 'AI 요약',
            clearTabs: true,
        });

        const res = await fetch(`assembly.json?t=${Date.now()}`);
        if (!res.ok) throw new Error("assembly.json 로드 실패");
        const data = await res.json();
        window.allData = data;

        if (data.schedules) {
            renderSingleCalendar(data.schedules);
            
            // 💡 달력 렌더링 직후 오늘 날짜 자동 선택 로직
            const todayStr = new Date().toISOString().split('T')[0];
            const todayEl = document.querySelector(`.cal-day[data-date="${todayStr}"]`);
            if (todayEl) {
                selectDate(todayStr, todayEl);
            }
        }

        if (DOM.pane2Content) DOM.pane2Content.innerHTML =
            `<div style="padding:40px; text-align:center; opacity:0.4;">의안 데이터 API 연동 대기 중</div>`;
        if (DOM.pane3Content) DOM.pane3Content.innerHTML =
            `<div style="padding:20px; line-height:1.8;">${data.summary ? data.summary.replace(/\n/g, '<br>') : '요약 정보가 없습니다.'}</div>`;

        updateTimeDisplays(data.last_updated, 'assembly');
    } catch (e) {
        console.error("Assembly Load Error:", e);
    }
}

window.changeMonth = function(offset) {
    window.currentCalDate.setDate(1);
    window.currentCalDate.setMonth(window.currentCalDate.getMonth() + offset);
    if (window.allData && window.allData.schedules) {
        renderSingleCalendar(window.allData.schedules);
    }
};

function renderSingleCalendar(schedules) {
    if (!DOM.calendarWrapper) return;

    const year = window.currentCalDate.getFullYear();
    const month = window.currentCalDate.getMonth();
    const days = ['일','월','화','수','목','금','토'];
    const firstDay = new Date(year, month, 1).getDay();
    const lastDate = new Date(year, month + 1, 0).getDate();
    const todayStr = new Date().toISOString().split('T')[0];

    let html = `
        <div class="cal-header">
            <button class="cal-nav-btn" onclick="changeMonth(-1)">&#10094;</button>
            <span>${year}년 ${month+1}월 국회 상황판</span>
            <button class="cal-nav-btn" onclick="changeMonth(1)">&#10095;</button>
        </div>
        <div class="cal-grid">${days.map(d => `<div style="color:#999; padding-bottom:10px;">${d}</div>`).join('')}`;

    for (let i = 0; i < firstDay; i++) html += `<div></div>`;

    for (let d = 1; d <= lastDate; d++) {
        const dateStr = `${year}-${String(month+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
        const hasSanja = schedules.some(s => s.date === dateStr && s.type === 'sanja');
        const hasGihyu = schedules.some(s => s.date === dateStr && s.type === 'gihyu');
        const isToday = (todayStr === dateStr);

        // 💡 요소 선택을 위해 data-date 속성 추가
        html += `<div class="cal-day ${isToday?'today':''}" data-date="${dateStr}" onclick="selectDate('${dateStr}', this)">
            <span>${d}</span>
            <div class="cal-dots-container">
                ${hasSanja ? '<span class="cal-dot dot-sanja"></span>' : ''}
                ${hasGihyu ? '<span class="cal-dot dot-gihyu"></span>' : ''}
            </div>
        </div>`;
    }
    DOM.calendarWrapper.innerHTML = `<div class="single-calendar">${html}</div></div>`;
}

window.selectDate = function(date, el) {
    document.querySelectorAll('.cal-day').forEach(d => d.classList.remove('selected'));
    if (el) el.classList.add('selected');

    if (window.allData && window.allData.schedules) {
        const daySchedules = window.allData.schedules.filter(s => s.date === date);
        renderItems('pane1-assembly-content', daySchedules);
    }
};

function renderItems(targetId, items) {
    const container = document.getElementById(targetId);
    if (!container) return;

    if (!items || items.length === 0) {
        container.innerHTML = `<div style="padding:40px; text-align:center; color:#999;">해당 항목에 데이터가 없습니다.</div>`;
        return;
    }

    container.innerHTML = items.map(item => {
        let dot = "";
        if (window.currentMode === 'assembly' && item.type !== 'session') {
            const dotColor = item.type === 'sanja' ? 'var(--sanja-color)' : 'var(--gihyu-color)';
            dot = `<div class="type-dot" style="background:${dotColor}"></div>`;
        }

        const titleText = item.title ? item.title.replace(/<[^>]*>?/gm, '') : '제목 없음';
        // 💡 Claude가 실수로 누락했던 ai_summary 출력 복구
        const pText = item.ai_summary || item.time || '';
        const pTag = pText ? `<p>${pText}</p>` : '';
        const metaText = item.formatted_date || (item.time + ' | ' + (item.committee||'') + ' | ' + (item.location || '장소미정'));

        return `
        <div class="item" onclick="if('${item.link||''}') window.open('${item.link}', '_blank')">
            <h3>${dot}${titleText}</h3>
            ${pTag}
            <span class="meta">${metaText}</span>
        </div>`;
    }).join('');
}

window.switchTab = function(p, kw, btn) {
    document.querySelectorAll(`#pane${p}-tabs .tab-btn`).forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
    if (window.allData && window.allData[`pane${p}`]) {
        renderItems(`pane${p}-content`, window.allData[`pane${p}`][kw]);
    }
};

function updateTimeDisplays(ts, mode) {
    const time = ts ? ts.substring(11, 16) : '--:--';
    const els = (mode === 'news')
        ? [DOM.time1News, DOM.time2, DOM.time3]
        : [DOM.time1Assembly, DOM.time2, DOM.time3];
    els.forEach(el => { if (el) el.innerText = `업데이트: ${time}`; });
}
