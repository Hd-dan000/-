/* ======================================
   API 工具 - 暂用模拟数据,后续连接真实后端
   ====================================== */
const API_BASE = '/api';
const MAX_DOC_UPLOAD_SIZE = 50 * 1024 * 1024; // 50MB
const ALLOWED_DOC_EXTENSIONS = ['.pdf', '.doc', '.docx', '.txt', '.md', '.xlsx', '.xls', '.ppt', '.pptx'];

function getAuthHeaders(extra = {}) {
    const headers = { ...extra };
    try {
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        if (user.id) headers['X-User-Id'] = user.id;
        if (user.username) headers['X-User-Name'] = user.username;
        if (user.role) headers['X-User-Role'] = user.role;
        if (user.account_type) headers['X-User-Type'] = user.account_type;
    } catch (e) {
        // ignore
    }
    return headers;
}

const api = {
    get: async (url) => {
        const resp = await fetch(`${API_BASE}${url}`, { headers: getAuthHeaders() });
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.detail || '请求失败');
        return data;
    },
    post: async (url, body) => {
        const isJson = typeof body === 'string';
        const resp = await fetch(`${API_BASE}${url}`, {
            method: 'POST',
            headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: isJson ? body : JSON.stringify(body)
        });
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.detail || '请求失败');
        return data;
    },
    put: async (url, body) => {
        const isJson = typeof body === 'string';
        const resp = await fetch(`${API_BASE}${url}`, {
            method: 'PUT',
            headers: getAuthHeaders(isJson ? { 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' }),
            body: isJson ? body : JSON.stringify(body)
        });
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.detail || '请求失败');
        return data;
    },
    delete: async (url) => {
        const resp = await fetch(`${API_BASE}${url}`, { method: 'DELETE', headers: getAuthHeaders() });
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.detail || '请求失败');
        return data;
    }
};

/* ======================================
   Toast 消息提示
   ====================================== */
const toast = {
    show: (message, type = 'success') => {
        const iconMap = { success: '&#10003;', error: '&#10007;', info: '&#9432;' };
        const el = document.createElement('div');
        el.className = `toast toast-${type}`;
        el.innerHTML = `<span>${iconMap[type] || iconMap.success}</span><span>${message}</span>`;
        document.body.appendChild(el);
        setTimeout(() => el.remove(), 3000);
    },
    success: (msg) => toast.show(msg, 'success'),
    error: (msg) => toast.show(msg, 'error'),
    info: (msg) => toast.show(msg, 'info')
};

/* ======================================
   Modal 弹窗
   ====================================== */
const modal = {
    open: (title, content, footer) => {
        const backdrop = document.getElementById('modal-backdrop');
        const container = document.getElementById('modal-container');
        container.innerHTML = `
            <div class="modal-header">
                <div class="modal-title">${title}</div>
                <button class="modal-close" onclick="modal.close()">&times;</button>
            </div>
            <div class="modal-body">${content}</div>
            ${footer ? `<div class="modal-footer">${footer}</div>` : ''}
        `;
        backdrop.style.display = 'block';
        container.style.display = 'flex';
        backdrop.onclick = () => modal.close();
    },
    close: () => {
        document.getElementById('modal-backdrop').style.display = 'none';
        document.getElementById('modal-container').style.display = 'none';
    }
};

/* ======================================
   模拟数据
   ====================================== */
const MOCK = {
    stats: {
        total_trainings: 12,
        total_submissions: 186,
        evaluated_count: 143,
        avg_score: 82.5,
        pass_rate: 91.4,
        active_students: 56
    },
    trend: {
        submissions: '+12.5%',
        evaluated: '+8.3%',
        score: '+3.2%'
    },
    score_distribution: {
        '优秀(90-100)': 38,
        '良好(80-89)': 52,
        '中等(70-79)': 31,
        '及格(60-69)': 16,
        '不及格(<60)': 6
    },
    status_distribution: {
        '已评价': 143,
        '待评价': 35,
        '未提交': 8
    },
    recent_submissions: [
        { student_name: '张三', training_title: 'Java Web实训项目', final_score: 92, status: 'evaluated', created_at: '2026-06-29 15:30' },
        { student_name: '李四', training_title: 'Python数据分析实训', final_score: 78, status: 'evaluated', created_at: '2026-06-29 14:20' },
        { student_name: '王五', training_title: 'Java Web实训项目', final_score: null, status: 'pending', created_at: '2026-06-29 11:45' },
        { student_name: '赵六', training_title: '数据库设计实训', final_score: 88, status: 'evaluated', created_at: '2026-06-28 16:10' },
        { student_name: '陈七', training_title: 'Python数据分析实训', final_score: 65, status: 'evaluated', created_at: '2026-06-28 14:30' },
        { student_name: '刘八', training_title: '前端开发实训', final_score: null, status: 'pending', created_at: '2026-06-28 10:00' },
        { student_name: '孙九', training_title: '数据库设计实训', final_score: 95, status: 'evaluated', created_at: '2026-06-27 15:45' },
        { student_name: '周十', training_title: 'Java Web实训项目', final_score: 71, status: 'evaluated', created_at: '2026-06-27 09:30' }
    ]
};

/* ======================================
   Router 路由
   ====================================== */
const router = {
    current: 'dashboard',
    navigate: (page) => {
        window.location.hash = page;
    },
    getQueryParam: (name) => {
        const hash = window.location.hash || '';
        const queryString = hash.split('?')[1] || '';
        const params = new URLSearchParams(queryString);
        return params.get(name);
    }
};

function syncNavActive() {
    const hash = window.location.hash || '#dashboard';
    const currentPage = hash.replace('#', '').split('?')[0] || 'dashboard';
    document.querySelectorAll('.top-nav-item').forEach(el => el.classList.remove('active'));
    const navEl = document.querySelector(`.top-nav-item[href="#${currentPage}"]`);
    if (navEl) {
        navEl.classList.add('active');
    }
    router.current = currentPage;
}

/* ======================================
   SVG 图标工具
   ====================================== */
const icons = {
    training: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
    evaluation: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>',
    report: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
    ai: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a4 4 0 0 0-4 4v1a4 4 0 0 0 8 0V6a4 4 0 0 0-4-4z"/><path d="M16 14H8"/><path d="M16 18H8"/><path d="M12 22v-4"/></svg>',
    users: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    list: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>',
    fileText: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
    warning: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    plus: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>',
    checkSquare: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>',
    wrench: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>'
};

/* ======================================
   学年学期选择器
   ====================================== */
const semesterSelector = {
    data: {
        options: [],
        selected: ''
    },
    STORAGE_KEY: 'teacher_selected_semester',
    formatSemester: function(raw) {
        if (!raw) return '';
        const parts = String(raw).split('-');
        if (parts.length < 3) return raw;
        const yearSpan = `${parts[0]}-${parts[1]}`;
        const terms = parts.slice(2).map(Number).filter(n => !isNaN(n));
        if (!terms.length) return raw;
        const termText = terms.map(n => `第${n}学期`).join('、');
        return `${yearSpan}学年-${termText}`;
    },
    groupSemesters: function(semesters) {
        const groups = {};
        semesters.forEach(raw => {
            const parts = String(raw).split('-');
            if (parts.length < 3) return;
            const key = `${parts[0]}-${parts[1]}`;
            if (!groups[key]) groups[key] = [];
            groups[key].push(Number(parts[parts.length - 1]));
        });
        return Object.keys(groups).sort().reverse().map(yearSpan => {
            const terms = groups[yearSpan].sort((a, b) => a - b);
            const termText = terms.map(n => `第${n}学期`).join('、');
            return {
                value: `${yearSpan}-${terms[0]}`,
                label: `${yearSpan}学年-${termText}`
            };
        });
    },
    loadOptions: async function() {
        let semesters = [];
        try {
            const res = await api.get('/courses/teacher/mine');
            const courses = res.courses || [];
            semesters = [...new Set(courses.map(c => c.semester).filter(Boolean))];
        } catch (e) {
            console.warn('获取学期数据失败:', e);
        }
        if (!semesters.length) {
            semesters = ['2024-2025-1'];
        }
        this.data.options = this.groupSemesters(semesters);
    },
    getSavedValue: function() {
        try {
            return localStorage.getItem(this.STORAGE_KEY) || '';
        } catch (e) {
            return '';
        }
    },
    saveValue: function(value) {
        try {
            localStorage.setItem(this.STORAGE_KEY, value);
        } catch (e) {}
    },
    findOption: function(value) {
        return this.data.options.find(o => o.value === value) || this.data.options[0];
    },
    render: function() {
        const triggerLabel = document.getElementById('hero-semester-label');
        const optionsContainer = document.getElementById('hero-semester-options');
        if (!triggerLabel || !optionsContainer) return;

        const selectedValue = this.data.selected;
        const selectedOption = this.findOption(selectedValue);
        triggerLabel.textContent = selectedOption ? selectedOption.label : '学年学期';

        optionsContainer.innerHTML = this.data.options.map(opt => `
            <div class="hero-semester-option ${opt.value === selectedValue ? 'selected' : ''}"
                 onclick="semesterSelector.select('${opt.value}')">
                ${opt.label}
            </div>
        `).join('');
    },
    toggle: function(event) {
        if (event) event.stopPropagation();
        const selector = document.getElementById('hero-semester-selector');
        const dropdown = document.getElementById('hero-semester-dropdown');
        if (!selector || !dropdown) return;
        const isOpen = selector.classList.contains('open');
        if (isOpen) {
            this.close();
        } else {
            selector.classList.add('open');
            dropdown.style.display = 'block';
        }
    },
    close: function() {
        const selector = document.getElementById('hero-semester-selector');
        const dropdown = document.getElementById('hero-semester-dropdown');
        if (selector) selector.classList.remove('open');
        if (dropdown) dropdown.style.display = 'none';
    },
    select: function(value) {
        this.data.selected = value;
        this.saveValue(value);
        this.render();
        this.close();
    },
    init: async function() {
        await this.loadOptions();
        const saved = this.getSavedValue();
        this.data.selected = saved && this.data.options.some(o => o.value === saved)
            ? saved
            : (this.data.options[0] ? this.data.options[0].value : '');
        this.render();
    }
};

/* ======================================
   视图
   ====================================== */
const views = {
    /* ---------- Dashboard 教师首页 ---------- */
    dashboard: {
        data: {
            classes: [],
            trainings: []
        },
        getClassTrainings: function(className) {
            return (this.data.trainings || []).filter(t =>
                (t.assignedClasses || []).some(c => c === className)
            );
        },
        renderMiniChart: function(seed) {
            const base = Math.max(24, Math.min(90, seed || 50));
            const bars = [0.55, 0.8, 0.45, 0.95, 0.7].map(f => Math.round(base * f));
            return `
                <div class="dash-summary-chart">
                    ${bars.map(h => `<div class="dash-summary-bar" style="height:${h}%"></div>`).join('')}
                </div>
            `;
        },
        renderSummaryCard: function({ title, pending, passRate, btnText, onClick }) {
            return `
                <div class="dash-summary-card">
                    <div class="dash-summary-main">
                        <div class="dash-summary-title">${title}</div>
                        <div class="dash-summary-metrics">
                            <div class="dash-summary-metric">
                                <div class="label">待批改</div>
                                <div class="value">${pending || 0}</div>
                            </div>
                            <div class="dash-summary-metric">
                                <div class="label">合格率</div>
                                <div class="value">${passRate || 0}%</div>
                            </div>
                        </div>
                        <button class="dash-summary-btn" onclick="${onClick}">${btnText}</button>
                    </div>
                    ${this.renderMiniChart(passRate)}
                </div>
            `;
        },
        renderTrainingCard: function(training, index) {
            const statusMap = {
                not_started: { cls: 'status-pending', text: '待开始', image: 'src/' + encodeURI('待开始.png') },
                in_progress: { cls: 'status-active', text: '进行中', image: 'src/' + encodeURI('进行中.png') },
                active: { cls: 'status-active', text: '进行中', image: 'src/' + encodeURI('进行中.png') },
                ended: { cls: 'status-ended', text: '已截止', image: 'src/' + encodeURI('已截止.png') }
            };
            const status = statusMap[training.status] || { cls: 'status-pending', text: '待开始', image: 'src/' + encodeURI('待开始.png') };
            const assignedClasses = (training.assignedClasses || []).join('、') || '未分配';
            const esc = views.training.escapeHtml;
            const title = esc(training.courseName || training.course_name || training.title || '未命名实训');
            return `
                <div class="course-card dash-training-card" onclick="router.navigate('training')">
                    <div class="course-card-cover">
                        <img src="${status.image}" class="course-card-image" alt="${status.text}">
                        <span class="dash-training-status ${status.cls}">${status.text}</span>
                    </div>
                    <div class="course-card-body">
                        <h3 class="course-card-title" title="${title}">${title}</h3>
                        <div class="course-card-meta">截止:${training.deadline || '--'} · ${assignedClasses}</div>
                        <div class="course-card-stats">
                            <div class="course-card-stat">
                                <span class="value">${training.submissionCount || 0}</span><span class="label">已提交</span>
                            </div>
                            <div class="course-card-stat">
                                <span class="value">${training.evaluatedCount || 0}</span><span class="label">已评价</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        },
        renderScheduleRows: function() {
            const trainings = (this.data.trainings || [])
                .filter(t => t.status === 'in_progress' || t.status === 'not_started' || t.status === 'active')
                .slice(0, 5);

            const timeSlots = ['09:00', '14:00', '18:30', '10:00', '16:00'];
            const rooms = ['A302', 'B205', 'A401', 'C308', 'D501'];
            const actions = ['查看', '编辑', '签到', '查看', '编辑'];

            if (!trainings.length) {
                return `
                    <tr>
                        <td colspan="7" class="empty-state" style="padding:40px 20px;">
                            <div class="empty-icon">📋</div>
                            <p>今日暂无实训安排</p>
                        </td>
                    </tr>
                `;
            }

            return trainings.map((t, i) => {
                const className = (t.assignedClasses || [])[0] || '-';
                return `
                    <tr>
                        <td class="checkbox-cell"><input type="checkbox"></td>
                        <td>${timeSlots[i % timeSlots.length]}</td>
                        <td>${className}</td>
                        <td>${t.title || '未命名实训'}</td>
                        <td>${rooms[i % rooms.length]}</td>
                        <td><span class="tag tag-info">进行中</span></td>
                        <td class="actions-cell">
                            <span class="action-link" onclick="router.navigate('training')">${actions[i % actions.length]}</span>
                        </td>
                    </tr>
                `;
            }).join('');
        },
        render: async function() {
            const content = document.getElementById('page-content');
            content.innerHTML = '<div class="loading-state"><div class="spinner"></div><p>加载中...</p></div>';

            let classes = [], trainings = [];
            try {
                const res = await api.get('/teacher/classes');
                classes = res.classes || [];
            } catch (e) {
                console.warn('获取授课班级失败:', e);
            }
            try {
                const res = await api.get('/courses/teacher/mine/trainings');
                trainings = (res.trainings || []).filter(t => t.status !== 'archived');
            } catch (e) {
                console.warn('获取实训任务失败:', e);
            }

            this.data.classes = classes;
            this.data.trainings = trainings;

            // 排序：进行中 > 待开始 > 已截止
            const dashOrder = { in_progress: 0, active: 0, not_started: 1, ended: 2 };
            const sortedTrainings = [...trainings].sort((a, b) => (dashOrder[a.status] || 9) - (dashOrder[b.status] || 9));

            const showMore = trainings.length > 8;
            const displayTrainings = sortedTrainings.slice(0, 8);
            const trainingCards = displayTrainings.map((t, i) => this.renderTrainingCard(t, i)).join('') +
                (showMore ? `
                    <div class="course-card more-card" onclick="router.navigate('training')">
                        <div class="more-card-inner">
                            <div class="more-card-icon">›</div>
                            <div class="more-card-text">更多</div>
                            <div class="more-card-sub">查看全部 ${trainings.length} 个项目</div>
                        </div>
                    </div>
                ` : '');

            const summaryCards = `
                <div class="teacher-classes-section">
                    <div class="teacher-classes-header">
                        <div class="teacher-classes-title">我的实训项目(${trainings.length})</div>
                        <a class="teacher-classes-more" href="#training" onclick="router.navigate('training')">实训管理 &gt;</a>
                    </div>
                    <div class="course-grid">
                        ${trainingCards || '<div class="teacher-classes-empty">暂无实训项目</div>'}
                    </div>
                </div>
            `;

            content.innerHTML = `
                <div class="dashboard-view">
                    <!-- Hero 横幅 -->
                    <div class="dash-hero">
                        <div class="dash-hero-content">
                            <div class="hero-semester-selector" id="hero-semester-selector">
                                <button class="hero-semester-trigger" id="hero-semester-trigger" onclick="semesterSelector.toggle(event)">
                                    <span id="hero-semester-label">学年学期</span>
                                    <svg class="hero-semester-arrow" id="hero-semester-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <polyline points="6 9 12 15 18 9"/>
                                    </svg>
                                </button>
                                <div class="hero-semester-dropdown" id="hero-semester-dropdown" style="display:none">
                                    <div class="hero-semester-options" id="hero-semester-options"></div>
                                </div>
                            </div>
                            <div class="hero-semester-status" id="hero-semester-status"></div>
                        </div>
                    </div>

                    ${summaryCards}

                    <!-- 底部:今日实训安排 + 下发课程安排 -->
                    <div class="dash-bottom-grid">
                        <div class="dash-schedule-card">
                            <div class="card-title">今日实训安排</div>
                            <table class="dash-table">
                                <thead>
                                    <tr>
                                        <th class="checkbox-cell"><input type="checkbox" id="schedule-select-all"></th>
                                        <th>时间</th>
                                        <th>班级</th>
                                        <th>实训项目</th>
                                        <th>机房</th>
                                        <th>状态</th>
                                        <th>操作</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${this.renderScheduleRows()}
                                </tbody>
                            </table>
                        </div>
                        <div class="quick-actions-card">
                            <div class="card-title">下发课程安排</div>
                            <div class="quick-action-grid">
                                <button class="quick-action-item" onclick="router.navigate('training?action=create')">创建实训任务</button>
                                <button class="quick-action-item" onclick="router.navigate('training')">批量批改报告</button>
                                <button class="quick-action-item" onclick="toast.info('功能开发中')">备课状态</button>
                                <button class="quick-action-item" onclick="toast.info('功能开发中')">待出成绩</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // 初始化 Hero 学期选择器
            semesterSelector.init().catch(e => console.warn('学期选择器初始化失败:', e));

            const selectAll = document.getElementById('schedule-select-all');
            if (selectAll) {
                selectAll.addEventListener('change', function() {
                    document.querySelectorAll('.dash-table tbody input[type="checkbox"]').forEach(cb => {
                        cb.checked = selectAll.checked;
                    });
                });
            }
        }
    },

    /* ---------- 课程班级列表(二级) ---------- */
    'course-detail': {
        render: async function() {
            const content = document.getElementById('page-content');
            const courseId = router.getQueryParam('course_id');
            if (!courseId) {
                content.innerHTML = '<div class="empty-state"><p>缺少课程参数</p></div>';
                return;
            }
            content.innerHTML = '<div class="loading-state"><div class="spinner"></div><p>加载中...</p></div>';

            try {
                const [mineRes, classesRes] = await Promise.all([
                    api.get('/courses/teacher/mine'),
                    api.get(`/courses/teacher/${courseId}/classes`)
                ]);
                const course = (mineRes.courses || []).find(c => String(c.id) === String(courseId)) || {};
                const classes = classesRes.classes || [];

                content.innerHTML = `
                    <div class="page-header">
                        <div class="page-header-left">
                            <button class="btn btn-default" onclick="router.navigate('dashboard')" style="margin-right:12px;">← 返回首页</button>
                            <div>
                                <h2>${course.course_name || '课程详情'}</h2>
                                <p>${course.semester || '--'} · 选择班级查看学生提交与评价情况</p>
                            </div>
                        </div>
                    </div>
                    <div class="class-list-page">
                        ${classes.length ? classes.map((cls, i) => `
                            <div class="class-list-item" onclick="router.navigate('class-students?class_id=${cls.id}')">
                                <div class="class-list-index">${i + 1}</div>
                                <div class="class-list-info">
                                    <div class="class-list-name">${cls.class_name}</div>
                                    <div class="class-list-meta">${cls.major || ''}${cls.grade ? ' · ' + cls.grade : ''}</div>
                                </div>
                                <div class="class-list-stats">
                                    <div class="class-list-stat"><span class="value">${cls.student_count || 0}</span><span class="label">学生</span></div>
                                    <div class="class-list-stat"><span class="value">${cls.pending_count || 0}</span><span class="label">待批改</span></div>
                                </div>
                                <div class="class-list-arrow">›</div>
                            </div>
                        `).join('') : '<div class="empty-state">该课程下暂无班级</div>'}
                    </div>
                `;
            } catch (e) {
                console.error('加载课程班级列表失败:', e);
                content.innerHTML = '<div class="empty-state"><p>加载失败,请稍后重试</p></div>';
                toast.error('加载失败: ' + (e.message || '未知错误'));
            }
        }
    },

    /* ---------- 班级学生详情(三级) ---------- */
    'class-students': {
        render: async function() {
            const content = document.getElementById('page-content');
            const classId = router.getQueryParam('class_id');
            if (!classId) {
                content.innerHTML = '<div class="empty-state"><p>缺少班级参数</p></div>';
                return;
            }
            content.innerHTML = '<div class="loading-state"><div class="spinner"></div><p>加载中...</p></div>';

            try {
                const data = await api.get(`/courses/teacher/classes/${classId}/students`);
                const cls = data.class || {};
                const students = data.students || [];

                content.innerHTML = `
                    <div class="page-header">
                        <div class="page-header-left">
                            <button class="btn btn-default" onclick="history.back()" style="margin-right:12px;">← 返回</button>
                            <div>
                                <h2>${cls.class_name || '班级学生'}</h2>
                                <p>${cls.major || ''}${cls.grade ? ' · ' + cls.grade : ''} · 共 ${students.length} 人</p>
                            </div>
                        </div>
                    </div>
                    <div class="card" style="overflow-x:auto;">
                        <table class="student-table">
                            <thead>
                                <tr>
                                    <th>学号</th>
                                    <th>姓名</th>
                                    <th>实训提交</th>
                                    <th>LLM评分</th>
                                    <th>最终得分</th>
                                    <th>教师评分</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${students.length ? students.map(s => `
                                    <tr>
                                        <td>${s.student_no || '--'}</td>
                                        <td>${s.name || '--'}</td>
                                        <td>
                                            <span class="status-badge ${s.submission_count ? (s.pending_count ? 'status-pending' : 'status-done') : 'status-none'}">
                                                ${s.submission_count ? (s.pending_count ? `${s.submission_count}份·待评` : `${s.submission_count}份·已评`) : '未提交'}
                                            </span>
                                        </td>
                                        <td>${s.llm_score != null ? s.llm_score : '-'}</td>
                                        <td>${s.final_score != null ? s.final_score : '-'}</td>
                                        <td>${s.teacher_score != null ? s.teacher_score : '-'}</td>
                                        <td><button class="btn btn-text" onclick="event.stopPropagation(); toast.info('智能核查报告功能开发中')">查看报告</button></td>
                                    </tr>
                                `).join('') : '<tr><td colspan="7" class="empty-state">暂无学生数据</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                `;
            } catch (e) {
                console.error('加载班级学生详情失败:', e);
                content.innerHTML = '<div class="empty-state"><p>加载失败,请稍后重试</p></div>';
                toast.error('加载失败: ' + (e.message || '未知错误'));
            }
        }
    },

    /* ---------- 实训管理 ---------- */
    training: {
        data: {
            trainings: [],
            classes: [],
            courses: [],
            filterStatus: 'all',
            searchQuery: '',
            selectedClass: 'all',
            showModal: false,
            editingId: null,
            pendingFile: null,
            formData: {
                title: '',
                description: '',
                deadline: '',
                dimensions: [],
                documentUrl: '',
                codeStandard: '',
                courseId: '',
                assignedClassIds: [],
                status: 'not_started'
            },
            classDetail: null,
            classLoading: false,
            classStatusSaving: false
        },

        // 开课状态选项
        teachingStatusOptions: [
            { value: 'not_started', label: '未开课' },
            { value: 'in_progress', label: '开课中' },
            { value: 'ended', label: '已结课' }
        ],

        // 获取 URL 查询参数
        getQueryParam(name) {
            const hash = window.location.hash || '';
            const queryString = hash.split('?')[1] || '';
            const params = new URLSearchParams(queryString);
            return params.get(name);
        },

        // 是否为教师/管理员
        isTeacherOrAdmin() {
            try {
                const user = JSON.parse(localStorage.getItem('user') || '{}');
                return ['teacher', 'admin'].includes(user.account_type) || ['teacher', 'admin', 'super_admin'].includes(user.role);
            } catch (e) {
                return false;
            }
        },

        // 加载班级详情
        async loadClassDetail(classId) {
            const self = views.training;
            self.data.classLoading = true;
            self.data.classDetail = null;
            try {
                const detail = await api.get(`/teacher/classes/${classId}`);
                self.data.classDetail = detail;
            } catch (e) {
                console.error('加载班级详情失败:', e);
                toast.error('加载班级详情失败: ' + (e.message || '未知错误'));
            } finally {
                self.data.classLoading = false;
            }
        },

        // 保存班级开课状态
        async saveClassStatus() {
            const self = views.training;
            const classId = self.getQueryParam('class_id');
            if (!classId) return;

            const select = document.getElementById('class-status-select');
            if (!select) return;
            const teachingStatus = select.value;

            self.data.classStatusSaving = true;
            self.renderClassStatusSaving();
            try {
                await api.put(`/teacher/classes/${classId}/status`, { teaching_status: teachingStatus });
                if (self.data.classDetail) {
                    self.data.classDetail.teaching_status = teachingStatus;
                    self.data.classDetail.status_text = {
                        'not_started': '未开课',
                        'in_progress': '开课中',
                        'ended': '已结课'
                    }[teachingStatus] || '未开课';
                }
                toast.success('班级状态已保存');
            } catch (e) {
                console.error('保存班级状态失败:', e);
                toast.error('保存班级状态失败: ' + (e.message || '未知错误'));
            } finally {
                self.data.classStatusSaving = false;
                self.renderClassStatusSaving();
            }
        },

        // 仅重新渲染保存按钮状态
        renderClassStatusSaving() {
            const btn = document.getElementById('class-status-save-btn');
            if (!btn) return;
            if (views.training.data.classStatusSaving) {
                btn.disabled = true;
                btn.innerHTML = `<span class="spinner-sm"></span> 保存中...`;
            } else {
                btn.disabled = false;
                btn.innerHTML = '保存状态';
            }
        },

        // 渲染班级状态标签
        getClassStatusBadgeClass(status) {
            return {
                'not_started': 'status-not-started',
                'in_progress': 'status-in-progress',
                'ended': 'status-ended'
            }[status] || 'status-not-started';
        },

        // 渲染班级详情页
        renderClassDetail: async () => {
            const self = views.training;
            const content = document.getElementById('page-content');
            const classId = self.getQueryParam('class_id');

            content.innerHTML = '<div class="loading-state"><div class="spinner"></div><p>加载班级信息...</p></div>';

            await self.loadClassDetail(classId);
            const detail = self.data.classDetail;

            if (!detail) {
                content.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">📋</div>
                        <p>无法加载班级信息</p>
                        <button class="btn btn-primary" onclick="router.navigate('training')">返回实训管理</button>
                    </div>
                `;
                return;
            }

            const statusOptions = self.teachingStatusOptions.map(opt =>
                `<option value="${opt.value}" ${detail.teaching_status === opt.value ? 'selected' : ''}>${opt.label}</option>`
            ).join('');

            const esc = self.escapeHtml;
            const canManage = self.isTeacherOrAdmin();

            content.innerHTML = `
                <div class="page-header">
                    <div class="page-header-left">
                        <button class="btn btn-default" onclick="router.navigate('training')" style="margin-right:12px;">
                            ← 返回实训管理
                        </button>
                        <div>
                            <h2>${esc(detail.class_name || '班级详情')}</h2>
                            <p>${esc(detail.class_code || '')} ${detail.grade ? '· ' + esc(detail.grade) : ''}</p>
                        </div>
                    </div>
                </div>

                <div class="class-detail-grid">
                    <div class="class-info-card">
                        <div class="class-info-header">
                            <div class="class-info-icon">📚</div>
                            <div>
                                <div class="class-info-title">${esc(detail.class_name || '未命名班级')}</div>
                                <div class="class-info-subtitle">${esc(detail.major || '')} ${detail.grade ? '· ' + esc(detail.grade) : ''}</div>
                            </div>
                        </div>
                        <div class="class-info-body">
                            <div class="class-info-item">
                                <span class="class-info-label">班级编号</span>
                                <span class="class-info-value">${esc(detail.class_code || '-')}</span>
                            </div>
                            <div class="class-info-item">
                                <span class="class-info-label">学生人数</span>
                                <span class="class-info-value">${detail.student_count || 0} 人</span>
                            </div>
                            <div class="class-info-item">
                                <span class="class-info-label">授课教师</span>
                                <span class="class-info-value">${esc(detail.teacher_name || '当前教师')}</span>
                            </div>
                            <div class="class-info-item">
                                <span class="class-info-label">当前状态</span>
                                <span class="class-status-badge ${self.getClassStatusBadgeClass(detail.teaching_status)}">${detail.status_text || '未开课'}</span>
                            </div>
                        </div>
                    </div>

                    <div class="class-status-card">
                        <div class="class-status-header">
                            <div class="class-status-title">开课状态设置</div>
                            <div class="class-status-desc">设置后会影响首页班级卡片的状态展示</div>
                        </div>
                        <div class="class-status-body">
                            <div class="form-group">
                                <label>选择班级状态</label>
                                <select id="class-status-select" class="filter-select" ${!canManage ? 'disabled' : ''}>
                                    ${statusOptions}
                                </select>
                            </div>
                            ${canManage ? `
                                <button id="class-status-save-btn" class="btn btn-primary" onclick="views.training.saveClassStatus()">
                                    保存状态
                                </button>
                            ` : '<p class="class-status-tip">仅教师或管理员可修改状态</p>'}
                        </div>
                    </div>
                </div>

                <div class="class-trainings-section">
                    <div class="class-section-title">班级实训任务</div>
                    <div id="class-trainings-list" class="training-list"></div>
                </div>
            `;

            // 加载并渲染该班级的实训列表
            await self.loadTrainings();
            const classTrainings = (self.data.trainings || []).filter(t =>
                (t.assignedClasses || []).some(c => String(c) === String(detail.class_name) || String(c) === String(detail.class_code))
            );
            // 排序：进行中 > 待开始 > 已截止
            const detailOrder = { in_progress: 0, active: 0, not_started: 1, ended: 2 };
            classTrainings.sort((a, b) => (detailOrder[a.status] || 9) - (detailOrder[b.status] || 9));
            const listEl = document.getElementById('class-trainings-list');
            if (listEl) {
                listEl.innerHTML = classTrainings.length > 0
                    ? classTrainings.map(t => self.renderTrainingCard(t)).join('')
                    : `<div class="empty-state" style="padding:40px 20px;"><div class="empty-icon">📋</div><p>该班级暂无实训任务</p></div>`;
            }
        },

        // 状态映射
        statusMap: {
            not_started: 'status-not-started',
            in_progress: 'status-in-progress',
            ended: 'status-ended',
            active: 'status-in-progress'
        },
        statusTextMap: {
            not_started: '待开始',
            in_progress: '进行中',
            ended: '已截止',
            active: '进行中'
        },

        // 加载当前教师授课课程
        async loadCourses() {
            const self = views.training;
            try {
                const res = await api.get('/courses/teacher/mine');
                self.data.courses = res.courses || [];
            } catch (e) {
                console.warn('加载授课课程失败:', e);
                self.data.courses = [];
            }
        },

        // 加载当前教师授课班级
        async loadClasses() {
            const self = views.training;
            try {
                const res = await api.get('/homework/teacher/class-list');
                self.data.classes = res.classes || [];
            } catch (e) {
                console.warn('加载授课班级失败:', e);
                self.data.classes = [];
            }
        },

        // 按课程过滤班级
        getClassesByCourse(courseId) {
            const self = views.training;
            if (!courseId || courseId === 'all') {
                return self.data.classes || [];
            }
            // 先通过 teach 关系推断班级:当前教师的课程下班级
            return (self.data.classes || []).filter(cls => {
                // 班级本身不直接含 course_id,这里简化:返回全部教师班级;
                // 后端会根据 course_id 校验权限,班级绑定由教师自行选择。
                return true;
            });
        },

        // 上传实训文档
        async uploadDocument(trainingId, file) {
            const form = new FormData();
            form.append('document', file);
            const resp = await fetch(`${API_BASE}/training/${trainingId}/document`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: form
            });
            const data = await resp.json();
            if (!resp.ok) throw new Error(data.detail || '文档上传失败');
            return data;
        },

        // 获取状态标签样式
        getStatusClass(status) {
            return this.statusMap[status] || '';
        },

        // 获取状态标签文字
        getStatusText(status) {
            return this.statusTextMap[status] || status;
        },

        // 获取进度百分比
        getProgress(training) {
            const total = training.studentCount || 0;
            if (!total) return 0;
            return Math.round(((training.submissionCount || 0) / total) * 100);
        },

        // 标准化后端返回的实训数据
        normalizeTraining(t) {
            return {
                ...t,
                id: t.id,
                title: t.title || '未命名实训',
                description: t.description || '',
                deadline: t.deadline || (t.updated_at ? t.updated_at.split(' ')[0] : ''),
                dimensions: Array.isArray(t.dimensions) ? t.dimensions : [],
                documentUrl: t.documentUrl || t.document_url || '',
                codeStandard: t.codeStandard || t.code_standard || '',
                assignedClasses: Array.isArray(t.assignedClasses) ? t.assignedClasses : [],
                assignedClassIds: Array.isArray(t.assignedClassIds) ? t.assignedClassIds : [],
                courseId: t.course_id || t.courseId || '',
                status: t.status || 'not_started',
                statusText: this.getStatusText(t.status || 'not_started'),
                createdAt: t.createdAt || t.created_at || '',
                studentCount: t.studentCount || t.student_count || 0,
                submissionCount: t.submissionCount || t.submission_count || 0,
                evaluatedCount: t.evaluatedCount || t.evaluated_count || 0
            };
        },

        // 过滤实训列表
        getFilteredTrainings() {
            let list = this.data.trainings || [];

            if (this.data.filterStatus === 'all') {
                // 默认"全部"不显示已归档项目
                list = list.filter(t => t.status !== 'archived');
            } else if (this.data.filterStatus !== 'all') {
                list = list.filter(t => t.status === this.data.filterStatus);
            }

            if (this.data.selectedClass !== 'all') {
                list = list.filter(t =>
                    (t.assignedClasses || []).includes(this.data.selectedClass) ||
                    (t.assignedClassIds || []).map(String).includes(String(this.data.selectedClass))
                );
            }

            if (this.data.searchQuery) {
                const q = this.data.searchQuery.toLowerCase();
                list = list.filter(t =>
                    (t.title || '').toLowerCase().includes(q) ||
                    (t.description || '').toLowerCase().includes(q)
                );
            }

            // 排序：进行中 > 待开始 > 已截止
            const order = { in_progress: 0, active: 0, not_started: 1, ended: 2 };
            list.sort((a, b) => (order[a.status] || 9) - (order[b.status] || 9));

            return list;
        },

        // 获取所有班级(去重)
        getAllClasses() {
            const classes = new Set();
            (this.data.trainings || []).forEach(t => {
                (t.assignedClasses || []).forEach(c => classes.add(c));
            });
            return Array.from(classes);
        },

        // 打开新建/编辑弹窗
        openModal(training = null) {
            this.data.editingId = training ? training.id : null;
            this.data.pendingFile = null;
            if (training) {
                this.data.formData = {
                    title: training.title || '',
                    description: training.description || '',
                    deadline: training.deadline || '',
                    dimensions: Array.isArray(training.dimensions) ? [...training.dimensions] : [],
                    documentUrl: training.documentUrl || '',
                    codeStandard: training.codeStandard || '',
                    assignedClassIds: Array.isArray(training.assignedClassIds) ? [...training.assignedClassIds] : [],
                    status: training.status || 'not_started'
                };
            } else {
                this.data.formData = {
                    title: '',
                    description: '',
                    deadline: '',
                    dimensions: [],
                    documentUrl: '',
                    codeStandard: '',
                    assignedClassIds: [],
                    status: 'not_started'
                };
            }
            this.data.showModal = true;
            this.renderModal();
        },

        // 关闭弹窗
        closeModal() {
            this.data.showModal = false;
            const backdrop = document.getElementById('modal-backdrop');
            const container = document.getElementById('modal-container');
            if (backdrop) backdrop.style.display = 'none';
            if (container) container.style.display = 'none';
        },

        // 切换班级选择
        toggleClassCheckbox(el, classId) {
            const isActive = el.classList.toggle('active');
            el.setAttribute('aria-checked', isActive ? 'true' : 'false');
        },

        // 保存实训
        async saveTraining() {
            const self = views.training;
            const form = document.getElementById('training-form');
            if (!form) return;

            const formData = new FormData(form);
            const title = formData.get('title')?.trim();
            const deadline = formData.get('deadline');
            const currentTraining = self.data.editingId
                ? self.data.trainings.find(t => t.id === self.data.editingId)
                : null;
            const courseId = currentTraining ? (currentTraining.courseId || currentTraining.course_id || '') : '';

            if (!title) {
                toast.error('请输入实训标题');
                return;
            }
            if (!deadline) {
                toast.error('请选择截止时间');
                return;
            }

            // 收集考核维度
            const dimensions = [];
            form.querySelectorAll('input[name="dimension"]:checked').forEach(cb => {
                dimensions.push(cb.value);
            });
            // 自定义维度
            const customDims = (formData.get('customDimensions') || '').split(/[,,]/).map(s => s.trim()).filter(Boolean);
            dimensions.push(...customDims);

            // 收集分配班级(按班级 id)
            const classIds = [];
            form.querySelectorAll('.class-checkbox.active').forEach(el => {
                classIds.push(parseInt(el.dataset.classId, 10));
            });

            const trainingPayload = {
                title: title,
                description: formData.get('description')?.trim() || '',
                course_name: title,
                deadline: deadline,
                dimensions: dimensions,
                document_url: formData.get('documentUrl')?.trim() || '',
                code_standard: formData.get('codeStandard')?.trim() || '',
                course_id: courseId ? parseInt(courseId, 10) : null,
                class_ids: classIds,
                status: formData.get('status') || 'not_started'
            };

            try {
                let result;
                if (self.data.editingId) {
                    result = await api.put(`/training/${self.data.editingId}`, trainingPayload);
                } else {
                    result = await api.post('/training/create', JSON.stringify(trainingPayload));
                }

                // 若有待上传文档,在上传后再刷新列表
                if (self.pendingFile && result && result.id) {
                    await self.uploadDocument(result.id, self.pendingFile);
                }

                toast.success(self.data.editingId ? '实训项目已更新' : '实训项目已创建');
                self.pendingFile = null;
                self.closeModal();
                await self.loadTrainings();
                self.render();
            } catch (e) {
                toast.error(e.message || '保存失败');
            }
        },

        // 归档实训
        async archiveTraining(id) {
            if (!confirm('确定要归档此实训项目吗?归档后可在"全部"中查看。')) return;
            try {
                await api.put(`/training/${id}`, JSON.stringify({ status: 'archived' }));
                toast.success('实训项目已归档');
                await views.training.loadTrainings();
                views.training.render();
            } catch (e) {
                toast.error(e.message || '归档失败');
            }
        },

        // 删除实训
        async deleteTraining(id, title) {
            if (!confirm(`确定要删除实训项目"${title || ''}"吗?此操作不可恢复。`)) return;
            try {
                await api.delete(`/training/${id}`);
                toast.success('实训项目已删除');
                await views.training.loadTrainings();
                // 如果当前在实训管理页则刷新列表,如果在首页则刷新首页
                if (router.current === 'training') {
                    views.training.render();
                } else {
                    views.dashboard.render();
                }
            } catch (e) {
                toast.error(e.message || '删除失败');
            }
        },

        // 渲染弹窗
        renderModal() {
            const self = views.training;
            const backdrop = document.getElementById('modal-backdrop');
            const container = document.getElementById('modal-container');
            const isEdit = self.data.editingId !== null;
            const formData = self.data.formData;

            const allDimensions = [
                '代码规范', '功能完整性', '架构设计', '文档质量',
                '数据清洗', '分析逻辑', '可视化效果', '代码质量',
                'ER图设计', 'SQL规范', '性能优化', '文档完整度',
                '组件设计', '状态管理', '响应式布局',
                '模型选择', '数据预处理', '训练效果'
            ];

            const classes = self.data.classes || [];
            const selectedClassIds = (formData.assignedClassIds || []).map(String);
            const esc = self.escapeHtml;

            container.innerHTML = `
                <div class="modal-header">
                    <div class="modal-title">${isEdit ? '编辑实训项目' : '新建实训项目'}</div>
                    <button class="modal-close" onclick="views.training.closeModal()">&times;</button>
                </div>
                <div class="modal-body" style="flex:1;overflow-y:auto;padding:0;">
                    <form id="training-form" class="training-form" onsubmit="event.preventDefault();views.training.saveTraining();">
                        <div class="form-section">
                            <h4>基本信息</h4>
                            <div class="form-row">
                                <div class="form-group required">
                                    <label>实训标题</label>
                                    <input type="text" name="title" value="${esc(formData.title)}" placeholder="请输入实训标题" required>
                                </div>
                                <div class="form-group required">
                                    <label for="training-deadline">截止时间</label>
                                    <input type="date" id="training-deadline" name="deadline" value="${formData.deadline || ''}" required>
                                </div>
                            </div>
                            <div class="form-group">
                                <label>项目状态</label>
                                <select name="status" class="filter-select">
                                    <option value="not_started" ${formData.status === 'not_started' ? 'selected' : ''}>待开始</option>
                                    <option value="in_progress" ${formData.status === 'in_progress' ? 'selected' : ''}>进行中</option>
                                    <option value="ended" ${formData.status === 'ended' ? 'selected' : ''}>已截止</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>实训描述</label>
                                <textarea name="description" rows="3" placeholder="请输入实训项目描述">${esc(formData.description)}</textarea>
                            </div>
                        </div>

                        <div class="form-section">
                            <h4>考核维度</h4>
                            <div class="dimension-tags">
                                ${allDimensions.map(d => `
                                    <label class="dimension-tag ${(formData.dimensions || []).includes(d) ? 'active' : ''}">
                                        <input type="checkbox" name="dimension" value="${d}" ${(formData.dimensions || []).includes(d) ? 'checked' : ''}
                                            onchange="this.parentElement.classList.toggle('active', this.checked)">
                                        <span>${d}</span>
                                    </label>
                                `).join('')}
                            </div>
                            <div class="form-group" style="margin-top:12px;">
                                <label>自定义维度(用逗号分隔)</label>
                                <input type="text" name="customDimensions" placeholder="例如:创新性, 团队协作, 代码复用性">
                            </div>
                        </div>

                        <div class="form-section">
                            <h4>任务文档</h4>
                            <div class="form-group">
                                <label>文档链接</label>
                                <input type="url" name="documentUrl" value="${esc(formData.documentUrl)}" placeholder="https://example.com/document.pdf">
                            </div>
                            <div class="form-group">
                                <label>或上传文档</label>
                                <div class="upload-area" id="doc-upload-area" onclick="document.getElementById('doc-upload').click()">
                                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                                    <span id="doc-upload-text">点击上传或拖拽文件到此处</span>
                                    <small>支持 ${ALLOWED_DOC_EXTENSIONS.join(' / ')},单个文件不超过 50MB</small>
                                </div>
                                <input type="file" id="doc-upload" style="display:none" accept="${ALLOWED_DOC_EXTENSIONS.join(',')}">
                                <div id="doc-upload-status" style="margin-top:8px;font-size:13px;">
                                    ${formData.documentUrl ? `<div class="doc-link">当前文档:<a href="${formData.documentUrl}" target="_blank">${esc(formData.documentUrl.split('/').pop())}</a></div>` : ''}
                                </div>
                            </div>
                        </div>

                        <div class="form-section">
                            <h4>代码提交规范</h4>
                            <div class="form-group">
                                <textarea name="codeStandard" rows="5" placeholder="请输入代码提交规范要求">${esc(formData.codeStandard)}</textarea>
                            </div>
                        </div>

                        <div class="form-section">
                            <h4>分配班级</h4>
                            <div class="class-checkboxes">
                                ${classes.length ? classes.map(c => `
                                    <div class="class-checkbox ${selectedClassIds.includes(String(c.id)) ? 'active' : ''}"
                                         role="checkbox"
                                         aria-checked="${selectedClassIds.includes(String(c.id)) ? 'true' : 'false'}"
                                         tabindex="0"
                                         data-class-id="${c.id}"
                                         onclick="views.training.toggleClassCheckbox(this, '${c.id}')"
                                         onkeydown="if(event.key===' '||event.key==='Enter'){event.preventDefault();views.training.toggleClassCheckbox(this,'${c.id}')}">
                                        <span class="check-icon">✓</span>
                                        <span class="class-name">${esc(c.class_name)} (${c.student_count || 0}人)</span>
                                    </div>
                                `).join('') : '<p style="color:var(--text-muted);padding:8px 0;">暂无授课班级,请先确认教师-班级关联</p>'}
                            </div>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-default" onclick="views.training.closeModal()">取消</button>
                    <button type="button" class="btn btn-primary" onclick="views.training.saveTraining()">${isEdit ? '保存修改' : '创建实训'}</button>
                </div>
            `;
            backdrop.style.display = 'block';
            container.style.display = 'flex';
            backdrop.onclick = () => views.training.closeModal();

            // 绑定文件选择事件
            const docInput = document.getElementById('doc-upload');
            const validateAndSetFile = (file) => {
                const textEl = document.getElementById('doc-upload-text');
                const statusEl = document.getElementById('doc-upload-status');
                const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
                if (!ALLOWED_DOC_EXTENSIONS.includes(ext)) {
                    toast.error(`不支持的文件格式:${ext},请上传 ${ALLOWED_DOC_EXTENSIONS.join(' / ')} 文件`);
                    self.pendingFile = null;
                    if (docInput) docInput.value = '';
                    if (textEl) textEl.textContent = '点击上传或拖拽文件到此处';
                    return;
                }
                if (file.size > MAX_DOC_UPLOAD_SIZE) {
                    toast.error('文件大小超过 50MB 限制');
                    self.pendingFile = null;
                    if (docInput) docInput.value = '';
                    if (textEl) textEl.textContent = '点击上传或拖拽文件到此处';
                    return;
                }
                self.pendingFile = file;
                if (textEl) textEl.textContent = `已选择:${file.name}`;
                if (statusEl) {
                    statusEl.innerHTML = `<div class="doc-link">待上传:<span style="color:var(--text-primary)">${self.escapeHtml(file.name)}</span>(${(file.size / 1024).toFixed(1)} KB)<button type="button" class="btn btn-text" onclick="views.training.clearPendingFile()">清除</button></div>`;
                }
            };
            if (docInput) {
                docInput.onchange = (e) => {
                    const file = e.target.files[0];
                    if (file) validateAndSetFile(file);
                };
                // 支持拖拽上传
                const uploadArea = document.getElementById('doc-upload-area');
                if (uploadArea) {
                    uploadArea.ondragover = (e) => { e.preventDefault(); uploadArea.classList.add('dragover'); };
                    uploadArea.ondragleave = (e) => { e.preventDefault(); uploadArea.classList.remove('dragover'); };
                    uploadArea.ondrop = (e) => {
                        e.preventDefault();
                        uploadArea.classList.remove('dragover');
                        const file = e.dataTransfer.files[0];
                        if (file) validateAndSetFile(file);
                    };
                }
            }
        },

        // 清除待上传文件
        clearPendingFile() {
            this.pendingFile = null;
            const docInput = document.getElementById('doc-upload');
            const textEl = document.getElementById('doc-upload-text');
            const statusEl = document.getElementById('doc-upload-status');
            if (docInput) docInput.value = '';
            if (textEl) textEl.textContent = '点击上传或拖拽文件到此处';
            if (statusEl) statusEl.innerHTML = '';
        },

        // HTML 转义
        escapeHtml(s) {
            return (s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        },

        // 渲染实训卡片
        renderTrainingCard(training) {
            const self = views.training;
            const progress = this.getProgress(training);
            const statusClass = this.getStatusClass(training.status);
            const statusText = this.getStatusText(training.status);
            const dimensions = training.dimensions || [];
            const assignedClasses = training.assignedClasses || [];
            const esc = self.escapeHtml;

            const statusImageMap = {
                'status-not-started': 'src/' + encodeURI('待开始.png'),
                'status-in-progress': 'src/' + encodeURI('进行中.png'),
                'status-ended': 'src/' + encodeURI('已截止.png')
            };
            const statusImage = statusImageMap[statusClass] || 'src/' + encodeURI('待开始.png');

            return `
                <div class="training-card ${statusClass}">
                    <div class="training-card-cover">
                        <img src="${statusImage}" class="training-card-image" alt="${statusText}">
                    </div>
                    <div class="training-card-header">
                        <div class="training-status-badge ${statusClass}">${statusText}</div>
                        <div class="training-actions">
                            <button class="action-btn" onclick="views.training.openModal(views.training.data.trainings.find(t=>t.id===${training.id}))" title="编辑">
                                <span style="font-size:14px;">✏️</span>
                            </button>
                            <button class="action-btn" onclick="views.training.archiveTraining(${training.id})" title="归档">
                                <span style="font-size:14px;">📦</span>
                            </button>
                        </div>
                    </div>
                    <div class="training-card-body">
                        <h4 class="training-title">${esc(training.title)}</h4>
                        <p class="training-desc">${esc(training.description)}</p>

                        <div class="training-meta">
                            <div class="meta-item">
                                <span style="font-size:13px;margin-right:4px;color:var(--text-muted);">⏰</span>
                                <span>截止:${training.deadline || '-'}</span>
                            </div>
                            <div class="meta-item">
                                <span style="font-size:13px;margin-right:4px;color:var(--text-muted);">👥</span>
                                <span>${training.studentCount || 0} 名学生</span>
                            </div>
                        </div>

                        <div class="training-dimensions">
                            ${dimensions.map(d => `<span class="dimension-chip">${esc(d)}</span>`).join('')}
                        </div>

                        <div class="training-classes">
                            <span class="classes-label">分配班级:</span>
                            ${assignedClasses.length ? assignedClasses.map(c => `<span class="class-tag">${esc(c)}</span>`).join('') : '<span class="class-tag">未分配</span>'}
                        </div>
                    </div>
                    <div class="training-card-footer">
                        <div class="progress-info">
                            <span>提交进度</span>
                            <span class="progress-text">${training.submissionCount || 0}/${training.studentCount || 0} (${progress}%)</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width:${progress}%"></div>
                        </div>
                        <div class="footer-stats">
                            <span>已评价 ${training.evaluatedCount || 0} 份</span>
                            ${training.documentUrl ? `<a href="${esc(training.documentUrl)}" target="_blank" class="has-doc" title="${esc(training.documentUrl)}">📄 ${esc(training.documentUrl.split('/').pop() || '文档')}</a>` : ''}
                        </div>
                    </div>
                </div>
            `;
        },

        // 加载实训列表
        async loadTrainings() {
            const self = views.training;
            try {
                const data = await api.get('/courses/teacher/mine/trainings');
                self.data.trainings = (data.trainings || []).map(t => self.normalizeTraining(t));
            } catch (e) {
                console.error('加载实训数据失败:', e);
                toast.error('加载实训数据失败: ' + (e.message || '未知错误'));
                self.data.trainings = [];
            }
        },

        render: async () => {
            const self = views.training;
            const content = document.getElementById('page-content');

            // 如果 URL 带有 class_id,渲染班级详情页
            const classId = self.getQueryParam('class_id');
            if (classId) {
                return self.renderClassDetail();
            }

            // 首页快捷入口:action=create 时自动打开新建弹窗
            const action = self.getQueryParam('action');
            if (action === 'create') {
                history.replaceState(null, null, '#training');
                content.innerHTML = '<div class="loading-state"><div class="spinner"></div><p>加载中...</p></div>';
                await Promise.all([self.loadTrainings(), self.loadClasses(), self.loadCourses()]);
                self.openModal();
                return;
            }

            content.innerHTML = '<div class="loading-state"><div class="spinner"></div><p>加载中...</p></div>';

            // 从后端加载教师真实授课课程、班级、实训
            await Promise.all([self.loadTrainings(), self.loadClasses(), self.loadCourses()]);

            // 去掉已归档选项后,避免残留 archived 筛选状态
            if (self.data.filterStatus === 'archived') {
                self.data.filterStatus = 'all';
            }

            const trainings = self.data.trainings;
            const filteredTrainings = self.getFilteredTrainings();
            const allClasses = self.data.classes || [];

            // 统计(不包含已归档)
            const activeTrainings = trainings.filter(t => t.status !== 'archived');
            const stats = {
                total: activeTrainings.length,
                notStarted: activeTrainings.filter(t => t.status === 'not_started').length,
                inProgress: activeTrainings.filter(t => t.status === 'in_progress' || t.status === 'active').length,
                ended: activeTrainings.filter(t => t.status === 'ended').length,
                totalStudents: activeTrainings.reduce((sum, t) => sum + (t.studentCount || 0), 0),
                totalSubmissions: activeTrainings.reduce((sum, t) => sum + (t.submissionCount || 0), 0)
            };

            content.innerHTML = `
                <!-- 页面标题 -->
                <div class="page-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <div class="page-header-left">
                        <h2>实训管理</h2>
                    </div>
                    <button class="btn btn-primary" onclick="views.training.openModal()">
                        <span style="font-size:16px;font-weight:700;margin-right:4px;">+</span>
                        新建实训
                    </button>
                </div>

                <!-- 统计卡片 -->
                <div class="training-stats">
                    <div class="training-stat-card">
                        <div class="stat-icon" style="background:#F0F5FF;color:#1677ff;">
                            <span style="font-size:20px;font-weight:600;">总</span>
                        </div>
                        <div class="stat-info">
                            <div class="stat-value">${stats.total}</div>
                            <div class="stat-label">实训总数</div>
                        </div>
                    </div>
                    <div class="training-stat-card">
                        <div class="stat-icon" style="background:#FFF7E6;color:#FAAD14;">
                            <span style="font-size:20px;font-weight:600;">待</span>
                        </div>
                        <div class="stat-info">
                            <div class="stat-value">${stats.notStarted}</div>
                            <div class="stat-label">待开始</div>
                        </div>
                    </div>
                    <div class="training-stat-card">
                        <div class="stat-icon" style="background:#F6FFED;color:#52C41A;">
                            <span style="font-size:20px;font-weight:600;">进</span>
                        </div>
                        <div class="stat-info">
                            <div class="stat-value">${stats.inProgress}</div>
                            <div class="stat-label">进行中</div>
                        </div>
                    </div>
                    <div class="training-stat-card">
                        <div class="stat-icon" style="background:#F5F5F5;color:#86909C;">
                            <span style="font-size:20px;font-weight:600;">截</span>
                        </div>
                        <div class="stat-info">
                            <div class="stat-value">${stats.ended}</div>
                            <div class="stat-label">已截止</div>
                        </div>
                    </div>
                </div>

                <!-- 筛选工具栏 -->
                <div class="training-toolbar">
                    <div class="filter-group">
                        <div class="filter-tabs">
                            <button class="filter-tab ${self.data.filterStatus === 'all' ? 'active' : ''}" onclick="views.training.data.filterStatus='all';views.training.render()">全部</button>
                            <button class="filter-tab ${self.data.filterStatus === 'not_started' ? 'active' : ''}" onclick="views.training.data.filterStatus='not_started';views.training.render()">待开始</button>
                            <button class="filter-tab ${self.data.filterStatus === 'in_progress' ? 'active' : ''}" onclick="views.training.data.filterStatus='in_progress';views.training.render()">进行中</button>
                            <button class="filter-tab ${self.data.filterStatus === 'ended' ? 'active' : ''}" onclick="views.training.data.filterStatus='ended';views.training.render()">已截止</button>
                        </div>
                    </div>
                    <div class="filter-right">
                        <select class="filter-select" onchange="views.training.data.selectedClass=this.value;views.training.render()">
                            <option value="all">所有班级</option>
                            ${allClasses.map(c => `<option value="${c.id}" ${String(self.data.selectedClass) === String(c.id) ? 'selected' : ''}>${self.escapeHtml(c.class_name)}</option>`).join('')}
                        </select>
                        <div class="search-box">
                            <span style="color:var(--text-muted);font-size:14px;margin-right:4px;">🔍</span>
                            <input type="text" placeholder="搜索实训..." value="${self.data.searchQuery}"
                                oninput="views.training.data.searchQuery=this.value;views.training.render()">
                        </div>
                    </div>
                </div>

                <!-- 实训列表 -->
                <div class="training-list">
                    ${filteredTrainings.length > 0
                        ? filteredTrainings.map(t => self.renderTrainingCard(t)).join('')
                        : `<div class="empty-state"><div class="empty-icon">📋</div><p>暂无符合条件的实训项目</p><button class="btn btn-primary" onclick="views.training.openModal()">创建第一个实训</button></div>`
                    }
                </div>
            `;
        }
    },
    evaluation: {
        data: {
            trainings: [],
            selectedTrainingId: null,
            currentTab: 'indicators',
            indicators: [],
            config: {
                comment_templates: [],
                error_rules: [],
                alert_thresholds: {},
                privacy_config: {}
            },
            loading: false
        },

        tabs: [
            { id: 'indicators', label: '评价指标配置', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>' },
            { id: 'templates', label: '智能评语模板', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>' },
            { id: 'errorRules', label: '错误识别规则', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>' },
            { id: 'thresholds', label: '预警阈值设置', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="12 22 12 12"/><polyline points="12 22 15 15"/><polyline points="12 22 9 15"/></svg>' },
            { id: 'privacy', label: '同辈对比隐私', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>' }
        ],

        async loadTrainings() {
            try {
                const res = await api.get('/training/list');
                this.data.trainings = (res || []).filter(t => t.status !== 'archived');
            } catch (e) {
                console.warn('加载实训列表失败:', e);
                this.data.trainings = [];
            }
        },

        async loadConfig(trainingId) {
            this.data.loading = true;
            try {
                const [indicatorsRes, configRes] = await Promise.all([
                    api.get(`/evaluation/indicators/${trainingId}`),
                    api.get(`/training/${trainingId}/eval-config`)
                ]);
                this.data.indicators = indicatorsRes || [];
                this.data.config = configRes;
            } catch (e) {
                console.warn('加载配置失败:', e);
                this.data.indicators = [];
                this.data.config = {
                    comment_templates: [],
                    error_rules: [],
                    alert_thresholds: {},
                    privacy_config: {}
                };
            } finally {
                this.data.loading = false;
            }
        },

        async saveConfig() {
            const trainingId = this.data.selectedTrainingId;
            if (!trainingId) {
                toast.error('请先选择实训项目');
                return;
            }

            try {
                await api.put(`/training/${trainingId}/eval-config`, JSON.stringify(this.data.config));
                toast.success('评价规则配置已保存');
            } catch (e) {
                toast.error('保存失败: ' + (e.message || '未知错误'));
            }
        },

        async saveIndicators() {
            const trainingId = this.data.selectedTrainingId;
            if (!trainingId) {
                toast.error('请先选择实训项目');
                return;
            }

            try {
                for (const indicator of this.data.indicators) {
                    if (indicator.id) {
                        await api.put(`/evaluation/indicators/${indicator.id}`, JSON.stringify({
                            name: indicator.name,
                            description: indicator.description,
                            weight: indicator.weight,
                            max_score: indicator.max_score
                        }));
                    } else {
                        await api.post('/evaluation/indicators', JSON.stringify({
                            training_id: trainingId,
                            name: indicator.name,
                            description: indicator.description,
                            weight: indicator.weight,
                            max_score: indicator.max_score
                        }));
                    }
                }
                await this.loadConfig(trainingId);
                toast.success('评价指标已保存');
            } catch (e) {
                toast.error('保存失败: ' + (e.message || '未知错误'));
            }
        },

        addIndicator() {
            this.data.indicators.push({
                id: null,
                name: '',
                description: '',
                weight: 1.0,
                max_score: 100.0
            });
            this.render();
        },

        removeIndicator(index) {
            const indicator = this.data.indicators[index];
            if (indicator.id) {
                api.delete(`/evaluation/indicators/${indicator.id}`).catch(e => console.warn('删除指标失败:', e));
            }
            this.data.indicators.splice(index, 1);
            this.render();
        },

        addErrorRule() {
            this.data.config.error_rules.push({
                id: Date.now(),
                name: '',
                keywords: [],
                severity: 'medium'
            });
            this.render();
        },

        removeErrorRule(index) {
            this.data.config.error_rules.splice(index, 1);
            this.render();
        },

        addKeyword(ruleIndex) {
            const input = document.getElementById(`keyword-input-${ruleIndex}`);
            if (input && input.value.trim()) {
                this.data.config.error_rules[ruleIndex].keywords.push(input.value.trim());
                input.value = '';
                this.render();
            }
        },

        removeKeyword(ruleIndex, keywordIndex) {
            this.data.config.error_rules[ruleIndex].keywords.splice(keywordIndex, 1);
            this.render();
        },

        addCommentTemplate() {
            const templates = this.data.config.comment_templates;
            const maxScore = templates.length > 0 ? templates[templates.length - 1].min_score : 0;
            this.data.config.comment_templates.push({
                min_score: 0,
                max_score: maxScore,
                label: '自定义',
                template: ''
            });
            this.render();
        },

        removeCommentTemplate(index) {
            if (this.data.config.comment_templates.length > 1) {
                this.data.config.comment_templates.splice(index, 1);
                this.render();
            } else {
                toast.info('至少保留一个评语模板');
            }
        },

        getTemplateLabelClass(score) {
            if (score >= 90) return 'high';
            if (score >= 70) return 'mid';
            return 'low';
        },

        renderIndicatorPanel() {
            const self = this;
            const indicators = this.data.indicators || [];
            return `
                <div class="eval-section">
                    <div class="eval-section-header">
                        <div>
                            <div class="eval-section-title">评价指标列表</div>
                            <div class="eval-section-desc">自定义实训打分维度,设置各维度权重与满分值</div>
                        </div>
                        <button class="btn btn-primary btn-sm" onclick="views.evaluation.saveIndicators()">保存指标</button>
                    </div>
                    <div class="eval-section-body">
                        <div class="indicator-list">
                            ${indicators.map((ind, i) => `
                                <div class="indicator-item">
                                    <div>
                                        <div class="indicator-name">${ind.name || '未命名指标'}</div>
                                        <div class="indicator-desc">${ind.description || '无描述'}</div>
                                    </div>
                                    <div>
                                        <div style="font-size:12px;color:var(--text-muted);margin-bottom:6px;">权重</div>
                                        <input type="range" class="weight-slider" min="0" max="5" step="0.1" value="${ind.weight || 1}"
                                            onchange="views.evaluation.data.indicators[${i}].weight=parseFloat(this.value);views.evaluation.render()">
                                        <div class="weight-value">${(ind.weight || 1).toFixed(1)}</div>
                                    </div>
                                    <div>
                                        <div style="font-size:12px;color:var(--text-muted);margin-bottom:6px;">满分值</div>
                                        <input type="number" class="max-score-input" value="${ind.max_score || 100}"
                                            onchange="views.evaluation.data.indicators[${i}].max_score=parseFloat(this.value);views.evaluation.render()">
                                    </div>
                                    <div>
                                        <div style="font-size:12px;color:var(--text-muted);margin-bottom:6px;">类型</div>
                                        <span class="tag tag-info">${ind.indicator_type === 'manual' ? '人工' : '自动'}</span>
                                    </div>
                                    <div class="indicator-actions">
                                        <button class="action-btn" title="编辑" onclick="toast.info('编辑功能开发中')">
                                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                                        </button>
                                        <button class="action-btn delete" title="删除" onclick="views.evaluation.removeIndicator(${i})">
                                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                                        </button>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                        <button class="add-indicator-btn" onclick="views.evaluation.addIndicator()">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                            添加评价指标
                        </button>
                    </div>
                </div>
            `;
        },

        renderTemplatesPanel() {
            const self = this;
            const templates = this.data.config.comment_templates || [];
            return `
                <div class="eval-section">
                    <div class="eval-section-header">
                        <div>
                            <div class="eval-section-title">智能评语模板</div>
                            <div class="eval-section-desc">分档位预设综合评语模板,AI自动匹配生成专属评语</div>
                        </div>
                        <button class="btn btn-primary btn-sm" onclick="views.evaluation.saveConfig()">保存模板</button>
                    </div>
                    <div class="eval-section-body">
                        <div class="template-list">
                            ${templates.map((tpl, i) => `
                                <div class="template-card">
                                    <div class="template-header">
                                        <span class="template-label ${this.getTemplateLabelClass(tpl.min_score)}">${tpl.label}</span>
                                        <span class="template-score">${tpl.min_score}-${tpl.max_score}分</span>
                                    </div>
                                    <textarea class="template-textarea" placeholder="请输入评语模板..."
                                        oninput="views.evaluation.data.config.comment_templates[${i}].template=this.value"
                                        >${self.escapeHtml(tpl.template)}</textarea>
                                    <div style="display:flex;justify-content:flex-end;margin-top:10px;">
                                        <button class="action-btn delete" onclick="views.evaluation.removeCommentTemplate(${i})" title="删除">
                                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                                        </button>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                        <button class="add-indicator-btn" onclick="views.evaluation.addCommentTemplate()" style="margin-top:16px;">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                            添加评语模板
                        </button>
                    </div>
                </div>
            `;
        },

        renderErrorRulesPanel() {
            const rules = this.data.config.error_rules || [];
            const self = this;
            return `
                <div class="eval-section">
                    <div class="eval-section-header">
                        <div>
                            <div class="eval-section-title">错误识别规则</div>
                            <div class="eval-section-desc">配置代码错误识别关键词、逻辑漏洞判定标准</div>
                        </div>
                        <button class="btn btn-primary btn-sm" onclick="views.evaluation.saveConfig()">保存规则</button>
                    </div>
                    <div class="eval-section-body">
                        <div class="error-rule-list">
                            ${rules.map((rule, i) => `
                                <div class="error-rule-item">
                                    <div class="error-rule-header">
                                        <div>
                                            <input type="text" class="form-control" style="width:200px;display:inline-block;"
                                                value="${rule.name}" placeholder="规则名称"
                                                oninput="views.evaluation.data.config.error_rules[${i}].name=this.value">
                                        </div>
                                        <select class="filter-select" style="width:120px;"
                                            onchange="views.evaluation.data.config.error_rules[${i}].severity=this.value">
                                            <option value="high" ${rule.severity === 'high' ? 'selected' : ''}>高严重</option>
                                            <option value="medium" ${rule.severity === 'medium' ? 'selected' : ''}>中严重</option>
                                            <option value="low" ${rule.severity === 'low' ? 'selected' : ''}>低严重</option>
                                        </select>
                                    </div>
                                    <div class="error-rule-keywords">
                                        ${(rule.keywords || []).map((kw, j) => `
                                            <span class="keyword-tag">${kw}<span class="remove" onclick="views.evaluation.removeKeyword(${i}, ${j})">×</span></span>
                                        `).join('')}
                                        <input type="text" id="keyword-input-${i}" class="keyword-input" placeholder="添加关键词"
                                            onkeypress="if(event.key==='Enter'){views.evaluation.addKeyword(${i});}">
                                        <button class="btn btn-sm" onclick="views.evaluation.addKeyword(${i})">添加</button>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                        <button class="add-indicator-btn" onclick="views.evaluation.addErrorRule()" style="margin-top:16px;">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                            添加错误识别规则
                        </button>
                    </div>
                </div>
            `;
        },

        renderThresholdsPanel() {
            const thresholds = this.data.config.alert_thresholds || {};
            return `
                <div class="eval-section">
                    <div class="eval-section-header">
                        <div>
                            <div class="eval-section-title">预警阈值设置</div>
                            <div class="eval-section-desc">自定义异常成果判定标准,控制重点关注学生筛选规则</div>
                        </div>
                        <button class="btn btn-primary btn-sm" onclick="views.evaluation.saveConfig()">保存阈值</button>
                    </div>
                    <div class="eval-section-body">
                        <div class="threshold-grid">
                            <div class="threshold-item">
                                <div class="threshold-label">分数下限</div>
                                <div class="threshold-desc">低于此分数的学生将被标记为重点关注</div>
                                <input type="number" class="threshold-input" value="${thresholds.min_score || 60}"
                                    onchange="views.evaluation.data.config.alert_thresholds.min_score=parseFloat(this.value)">
                                <div class="threshold-unit">分</div>
                            </div>
                            <div class="threshold-item">
                                <div class="threshold-label">代码完整度阈值</div>
                                <div class="threshold-desc">代码完成度低于此比例将触发预警</div>
                                <input type="number" class="threshold-input" value="${(thresholds.code_completeness || 0.6) * 100}"
                                    onchange="views.evaluation.data.config.alert_thresholds.code_completeness=parseFloat(this.value)/100">
                                <div class="threshold-unit">%</div>
                            </div>
                            <div class="threshold-item">
                                <div class="threshold-label">低分率阈值</div>
                                <div class="threshold-desc">班级低分人数比例超过此值将触发预警</div>
                                <input type="number" class="threshold-input" value="${(thresholds.low_score_rate || 0.3) * 100}"
                                    onchange="views.evaluation.data.config.alert_thresholds.low_score_rate=parseFloat(this.value)/100">
                                <div class="threshold-unit">%</div>
                            </div>
                            <div class="threshold-item">
                                <div class="threshold-label">启用可疑模式检测</div>
                                <div class="threshold-desc">检测雷同作业、异常提交行为等</div>
                                <label class="toggle-switch" style="margin-top:12px;">
                                    <input type="checkbox" ${thresholds.suspicious_pattern ? 'checked' : ''}
                                        onchange="views.evaluation.data.config.alert_thresholds.suspicious_pattern=this.checked">
                                    <div class="toggle-track"><div class="toggle-thumb"></div></div>
                                </label>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        },

        renderPrivacyPanel() {
            const privacy = this.data.config.privacy_config || {};
            return `
                <div class="eval-section">
                    <div class="eval-section-header">
                        <div>
                            <div class="eval-section-title">同辈对比隐私配置</div>
                            <div class="eval-section-desc">控制班级能力分布展示与学生姓名显示,平衡数据分析与隐私保护</div>
                        </div>
                        <button class="btn btn-primary btn-sm" onclick="views.evaluation.saveConfig()">保存配置</button>
                    </div>
                    <div class="eval-section-body">
                        <div class="privacy-switch-list">
                            <div class="privacy-switch-item">
                                <div class="privacy-switch-info">
                                    <div class="privacy-switch-label">展示班级能力分布</div>
                                    <div class="privacy-switch-desc">在评价报告中显示班级分数分布、排名区间等统计信息</div>
                                </div>
                                <label class="toggle-switch">
                                    <input type="checkbox" ${privacy.show_ability_distribution ? 'checked' : ''}
                                        onchange="views.evaluation.data.config.privacy_config.show_ability_distribution=this.checked">
                                    <div class="toggle-track"><div class="toggle-thumb"></div></div>
                                </label>
                            </div>
                            <div class="privacy-switch-item">
                                <div class="privacy-switch-info">
                                    <div class="privacy-switch-label">隐藏学生姓名</div>
                                    <div class="privacy-switch-desc">在统计报表和对比分析中使用学号或匿名标识</div>
                                </div>
                                <label class="toggle-switch">
                                    <input type="checkbox" ${privacy.hide_student_name ? 'checked' : ''}
                                        onchange="views.evaluation.data.config.privacy_config.hide_student_name=this.checked">
                                    <div class="toggle-track"><div class="toggle-thumb"></div></div>
                                </label>
                            </div>
                            <div class="privacy-switch-item">
                                <div class="privacy-switch-info">
                                    <div class="privacy-switch-label">隐藏具体分数</div>
                                    <div class="privacy-switch-desc">仅展示等级评价(优秀/良好/中等)而不显示具体分数</div>
                                </div>
                                <label class="toggle-switch">
                                    <input type="checkbox" ${privacy.hide_specific_scores ? 'checked' : ''}
                                        onchange="views.evaluation.data.config.privacy_config.hide_specific_scores=this.checked">
                                    <div class="toggle-track"><div class="toggle-thumb"></div></div>
                                </label>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        },

        escapeHtml(str) {
            if (!str) return '';
            return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
        },

        render: async function() {
            const self = this;
            const content = document.getElementById('page-content');
            content.innerHTML = '<div class="loading-state"><div class="spinner"></div><p>加载中...</p></div>';

            await this.loadTrainings();
            const trainings = this.data.trainings;

            if (trainings.length === 0) {
                content.innerHTML = `
                    <div class="page-header">
                        <h2>评价规则配置</h2>
                        <p>自定义 AI 打分、评语、错误识别逻辑,个性化适配不同实训课程</p>
                    </div>
                    <div class="empty-trainings">
                        <div class="empty-icon">📋</div>
                        <p>暂无实训项目</p>
                        <p style="font-size:13px;">请先创建实训项目,再进行评价规则配置</p>
                        <button class="btn btn-primary" style="margin-top:16px;" onclick="router.navigate('training')">创建实训项目</button>
                    </div>
                `;
                return;
            }

            const selectedId = this.data.selectedTrainingId || trainings[0].id;
            this.data.selectedTrainingId = selectedId;
            await this.loadConfig(selectedId);

            const tabsHtml = this.tabs.map(tab => `
                <button class="eval-tab ${this.data.currentTab === tab.id ? 'active' : ''}"
                    onclick="views.evaluation.data.currentTab='${tab.id}';views.evaluation.render()">
                    <span class="eval-tab-icon">${tab.icon}</span>
                    <span>${tab.label}</span>
                </button>
            `).join('');

            const panels = {
                indicators: this.renderIndicatorPanel(),
                templates: this.renderTemplatesPanel(),
                errorRules: this.renderErrorRulesPanel(),
                thresholds: this.renderThresholdsPanel(),
                privacy: this.renderPrivacyPanel()
            };

            content.innerHTML = `
                <div class="eval-config-page">
                    <div class="page-header">
                        <h2>评价规则配置</h2>
                        <p>自定义 AI 打分、评语、错误识别逻辑,个性化适配不同实训课程</p>
                    </div>

                    <div class="eval-config-header">
                        <div class="eval-config-header-left">
                            <select class="eval-training-select" onchange="views.evaluation.data.selectedTrainingId=parseInt(this.value);views.evaluation.render()">
                                ${trainings.map(t => `
                                    <option value="${t.id}" ${t.id === selectedId ? 'selected' : ''}>${self.escapeHtml(t.title)}</option>
                                `).join('')}
                            </select>
                        </div>
                        <div class="eval-config-header-right">
                            <button class="btn btn-primary" onclick="views.evaluation.saveConfig()">保存全部配置</button>
                        </div>
                    </div>

                    <div class="eval-tab-bar">
                        ${tabsHtml}
                    </div>

                    <div class="eval-panels">
                        ${Object.keys(panels).map(key => `
                            <div class="eval-panel ${this.data.currentTab === key ? 'active' : ''}" id="eval-panel-${key}">
                                ${panels[key]}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
    },
    report: {
        data: {
            trainings: [],
            selectedTraining: null,
            classes: [],
            selectedClass: null,
            studentReports: [],
            filteredReports: [],
            commonProblems: [],
            abnormalStudents: [],
            generatedReports: [],
            warningThreshold: 60,
            selectedStudent: null,
            selectedSubmissionId: null,
            searchQuery: '',
            currentFollowUpNote: '',
            reviewModalOpen: false,
            abnormalModalOpen: false,
            categoryModalOpen: false,
            categoryModalSubmissionId: null,
            editingScore: null,
            editingComment: ''
        },
        async loadTrainings() {
            try {
                const res = await api.get('/courses/teacher/mine/trainings');
                this.data.trainings = (res.trainings || []).filter(t => t.status !== 'archived');
                if (this.data.trainings.length && !this.data.selectedTraining) {
                    this.data.selectedTraining = this.data.trainings[0];
                    await this.loadClasses();
                }
            } catch (e) {
                console.warn('获取实训列表失败:', e);
                this.data.trainings = [];
            }
        },
        async loadClasses() {
            if (!this.data.selectedTraining) {
                this.data.classes = [];
                return;
            }
            try {
                const res = await api.get(`/report/classes?training_id=${this.data.selectedTraining.id}`);
                this.data.classes = res.classes || [];
            } catch (e) {
                console.warn('加载班级失败:', e);
                this.data.classes = [];
            }
        },
        async loadSubmissions() {
            if (!this.data.selectedTraining) return;
            try {
                const params = new URLSearchParams({
                    training_id: this.data.selectedTraining.id
                });
                if (this.data.selectedClass) {
                    params.set('class_id', this.data.selectedClass.class_id);
                }
                if (this.data.searchQuery) {
                    params.set('student_name', this.data.searchQuery.trim());
                }
                const res = await api.get(`/report/submissions?${params.toString()}`);
                this.data.studentReports = res.submissions || [];
                this.data.filteredReports = this.data.studentReports;
            } catch (e) {
                console.warn('获取学生报告失败:', e);
                this.data.studentReports = [];
                this.data.filteredReports = [];
            }
        },
        async loadCommonProblems() {
            if (!this.data.selectedTraining) return;
            try {
                const res = await api.get(`/report/training/${this.data.selectedTraining.id}/common-problems`);
                this.data.commonProblems = Array.isArray(res) ? res : (res.problems || []);
            } catch (e) {
                console.warn('获取共性问题失败:', e);
                this.data.commonProblems = [];
            }
        },
        async loadAbnormalStudents() {
            if (!this.data.selectedTraining) return;
            try {
                const res = await api.post(`/report/training/${this.data.selectedTraining.id}/abnormal-students`, {
                    threshold: this.data.warningThreshold
                });
                this.data.abnormalStudents = Array.isArray(res) ? res : (res.students || []);
            } catch (e) {
                console.warn('获取异常学生失败:', e);
                this.data.abnormalStudents = [];
            }
        },
        async loadGeneratedReports() {
            if (!this.data.selectedTraining) return;
            try {
                const res = await api.get(`/report/list/${this.data.selectedTraining.id}`);
                this.data.generatedReports = res || [];
            } catch (e) {
                console.warn('获取报告列表失败:', e);
                this.data.generatedReports = [];
            }
        },
        async viewStudentDetail(submissionId) {
            try {
                const res = await api.get(`/report/student/${submissionId}`);
                const student = this.normalizeStudentDetail(res);
                this.data.selectedStudent = student;
                this.data.selectedSubmissionId = submissionId;
                this.data.currentFollowUpNote = student.follow_up_note || '';
                this.render();
            } catch (e) {
                toast.error('加载学生报告失败: ' + (e.message || '未知错误'));
            }
        },
        normalizeStudentDetail(raw) {
            const submission = raw.submission || {};
            const scores = raw.scores || {};
            const annotations = (raw.code_annotations || []).map(a => ({
                line: a.line_number || a.line || 0,
                type: a.type || 'suggestion',
                message: a.message || '',
                suggestion: a.suggestion || ''
            }));
            const indicators = (scores.indicator_scores || []).map(i => ({
                dimension: i.name,
                score: i.score,
                max_score: i.max_score || 100,
                comment: i.reason || ''
            }));
            return {
                submission_id: submission.id,
                student_id: submission.student_id,
                student_name: submission.student_name,
                training_title: (raw.training || {}).title,
                final_score: scores.final_score,
                ai_score: scores.ai_total_score,
                teacher_score: scores.teacher_score,
                ai_comment: scores.overall_comment,
                teacher_comment: raw.teacher_comment,
                follow_up_note: raw.follow_up_note,
                dimension_scores: indicators,
                code_annotations: annotations,
                status_label: submission.status_label,
                document_status: submission.document_status
            };
        },
        getDimensionScore(report, dimName) {
            const scores = report.dimension_scores || {};
            if (scores[dimName] !== undefined && scores[dimName] !== null) return scores[dimName];
            const indicators = report.indicator_scores || [];
            const found = indicators.find(i => i.name && i.name.includes(dimName));
            return found ? found.score : null;
        },
        getAnnotationCount(report) {
            const detail = report.evaluation_detail || {};
            const annotations = detail.code_annotations || [];
            const aiScores = detail.ai_scores || [];
            if (annotations.length) return annotations.length;
            return aiScores.filter(s => {
                const reason = s.reason || '';
                return reason.includes('错误') || reason.includes('问题') || reason.includes('建议');
            }).length;
        },
        applySearch() {
            const q = (this.data.searchQuery || '').trim().toLowerCase();
            if (!q) {
                this.data.filteredReports = [...this.data.studentReports];
                return;
            }
            this.data.filteredReports = this.data.studentReports.filter(r =>
                (r.student_name && r.student_name.toLowerCase().includes(q)) ||
                (r.student_id && String(r.student_id).toLowerCase().includes(q))
            );
        },
        onSearchInput(value) {
            this.data.searchQuery = value;
        },
        async onSearchSubmit(event) {
            if (event.key === 'Enter') {
                await this.loadSubmissions();
                this.render();
            }
        },
        onSelectClass(classId) {
            this.data.selectedClass = classId ? this.data.classes.find(c => String(c.class_id) === String(classId)) : null;
            this.loadSubmissions().then(() => this.render());
        },
        async onSelectTraining(trainingId) {
            this.data.selectedTraining = this.data.trainings.find(t => String(t.id) === String(trainingId));
            this.data.selectedClass = null;
            this.data.selectedStudent = null;
            this.data.selectedSubmissionId = null;
            this.data.searchQuery = '';
            await this.loadClasses();
            await this.loadSubmissions();
            this.render();
        },
        async saveReview(submissionId, dimension, newScore, comment) {
            try {
                await api.post(`/evaluation/teacher-review/${submissionId}`, {
                    teacher_score: newScore,
                    teacher_comment: comment
                });
                toast.success('评分已保存,已同步存入学生成长档案');
                this.data.editingScore = null;
                this.data.editingComment = '';
                await this.loadSubmissions();
                if (this.data.selectedSubmissionId) {
                    await this.viewStudentDetail(this.data.selectedSubmissionId);
                } else {
                    this.render();
                }
            } catch (e) {
                toast.error('保存失败: ' + (e.message || '未知错误'));
            }
        },
        async addFollowNote(studentId, note) {
            try {
                await api.post(`/report/training/${this.data.selectedTraining.id}/follow-up`, {
                    student_id: studentId,
                    note: note
                });
                toast.success('跟进备注已添加');
                await this.loadAbnormalStudents();
            } catch (e) {
                toast.error('添加备注失败: ' + (e.message || '未知错误'));
            }
        },
        async saveCurrentFollowNote() {
            if (!this.data.selectedStudent) return;
            try {
                await api.post(`/evaluation/teacher-review/${this.data.selectedStudent.submission_id}`, {
                    teacher_comment: this.data.currentFollowUpNote
                });
                toast.success('跟进备注已保存');
                await this.loadSubmissions();
                await this.viewStudentDetail(this.data.selectedStudent.submission_id);
            } catch (e) {
                toast.error('保存失败: ' + (e.message || '未知错误'));
            }
        },
        async generateSingleReport(submissionId) {
            try {
                const report = await api.post(`/report/generate/student/${submissionId}`);
                toast.success('报告生成成功');
                await this.loadGeneratedReports();
                if (report && report.id) {
                    await this.downloadReport(report.id, 'pdf');
                }
            } catch (e) {
                toast.error('生成报告失败: ' + (e.message || '未知错误'));
            }
        },
        async batchGenerateReports() {
            if (!this.data.selectedTraining) return;
            try {
                const res = await api.post(`/report/batch-generate/${this.data.selectedTraining.id}`);
                toast.success(`批量报告生成成功,共${res.report_ids ? res.report_ids.length : 0}份`);
                await this.loadGeneratedReports();
                return res.report_ids || [];
            } catch (e) {
                toast.error('批量生成失败: ' + (e.message || '未知错误'));
                return [];
            }
        },
        async downloadReport(reportId, format) {
            const url = `${API_BASE}/report/download/${reportId}/${format}`;
            const resp = await fetch(url, { headers: getAuthHeaders() });
            if (!resp.ok) {
                const data = await resp.json().catch(() => ({}));
                throw new Error(data.detail || '下载失败');
            }
            const blob = await resp.blob();
            const disposition = resp.headers.get('Content-Disposition') || '';
            const filenameMatch = disposition.match(/filename\*?=['"]*(?:UTF-8['"]*)?([^;\n"']+)/i);
            let filename = filenameMatch ? decodeURIComponent(filenameMatch[1]) : `report_${reportId}.${format === 'pdf' ? 'html' : 'csv'}`;
            if (!filename.toLowerCase().endsWith(`.${format === 'pdf' ? 'html' : 'csv'}`)) {
                filename += `.${format === 'pdf' ? 'html' : 'csv'}`;
            }
            this.downloadBlob(blob, filename, format === 'pdf' ? 'text/html' : 'text/csv');
        },
        async batchExport(type) {
            if (!this.data.selectedTraining) return;
            if (!confirm(`确定批量导出全班${type === 'pdf' ? 'PDF' : 'Excel'}报告吗?`)) return;
            try {
                if (type === 'pdf') {
                    const reportIds = await this.batchGenerateReports();
                    if (!reportIds.length) {
                        toast.warning('没有可导出的评阅报告,请确保有学生提交并已完成AI评阅');
                        return;
                    }
                    for (const reportId of reportIds) {
                        await this.downloadReport(reportId, 'pdf');
                        await new Promise(r => setTimeout(r, 300));
                    }
                } else {
                    const res = await api.get(`/report/training/${this.data.selectedTraining.id}/data`);
                    const submissions = res.submissions || [];
                    const headers = ['学号', '姓名', 'AI评分', '教师评分', '最终评分', 'AI评阅状态', '文档状态'];
                    const rows = submissions.map(s => [
                        s.student_id || '', s.student_name || '', s.ai_total_score || '', s.teacher_score || '', s.final_score || '',
                        s.ai_review_status || '', s.document_status || ''
                    ].join(','));
                    const csv = '\uFEFF' + [headers.join(','), ...rows].join('\n');
                    this.downloadBlob(csv, `${this.data.selectedTraining.title}_全班成绩汇总.csv`, 'text/csv');
                }
                toast.success('批量导出完成');
            } catch (e) {
                toast.error('批量导出失败: ' + (e.message || '未知错误'));
            }
        },
        downloadBlob(content, filename, mimeType) {
            const blob = new Blob([content], { type: mimeType });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
            window.URL.revokeObjectURL(url);
        },
        async exportProblems() {
            if (!this.data.selectedTraining) return;
            try {
                const resp = await fetch(`${API_BASE}/report/training/${this.data.selectedTraining.id}/export-problems`, {
                    headers: getAuthHeaders()
                });
                const blob = await resp.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `共性问题汇总_${this.data.selectedTraining.title}.csv`;
                a.click();
                window.URL.revokeObjectURL(url);
                toast.success('导出成功');
            } catch (e) {
                toast.error('导出失败: ' + (e.message || '未知错误'));
            }
        },
        getScoreColor(score) {
            if (score >= 90) return '#52C41A';
            if (score >= 80) return '#1677ff';
            if (score >= 60) return '#FAAD14';
            return '#FF4D4F';
        },
        getScoreLabel(score) {
            if (score >= 90) return '优秀';
            if (score >= 80) return '良好';
            if (score >= 60) return '及格';
            return '不及格';
        },
        renderCategoryTags(categories) {
            const labels = { document: '文档', ui: 'UI截图', code: '源代码' };
            const icons = { document: '📄', ui: '🖼️', code: '💻' };
            if (!categories || !categories.length) return '<span class="tag tag-info">无</span>';
            return categories.map(cat => `<span class="tag tag-primary" title="${labels[cat] || cat}">${icons[cat] || ''} ${labels[cat] || cat}</span>`).join(' ');
        },
        getRingCircumference() {
            return 2 * Math.PI * 52;
        },
        getRingOffset(score) {
            const circumference = this.getRingCircumference();
            return circumference - (Math.min(score || 0, 100) / 100) * circumference;
        },
        openReviewModal() {
            if (!this.data.selectedStudent) return;
            this.data.reviewModalOpen = true;
            this.renderModals();
        },
        closeReviewModal() {
            this.data.reviewModalOpen = false;
            this.renderModals();
        },
        openCategoryModal(submissionId) {
            this.data.categoryModalOpen = true;
            this.data.categoryModalSubmissionId = submissionId;
            this.renderModals();
        },
        closeCategoryModal() {
            this.data.categoryModalOpen = false;
            this.data.categoryModalSubmissionId = null;
            this.renderModals();
        },
        confirmCategoryView() {
            const checked = Array.from(document.querySelectorAll('.category-checkbox-input:checked')).map(cb => cb.value);
            if (!checked.length) {
                toast.error('请至少选择一类查看');
                return;
            }
            const submissionId = this.data.categoryModalSubmissionId;
            this.closeCategoryModal();
            window.open(`#report-detail?submission_id=${submissionId}&categories=${checked.join(',')}`, '_blank');
        },
        async submitReview() {
            const scoreInput = document.getElementById('review-teacher-score');
            const commentInput = document.getElementById('review-teacher-comment');
            const score = scoreInput ? parseFloat(scoreInput.value) : null;
            const comment = commentInput ? commentInput.value : '';
            if (isNaN(score)) {
                toast.error('请输入有效分数');
                return;
            }
            await this.saveReview(this.data.selectedStudent.submission_id, null, score, comment);
            this.closeReviewModal();
        },
        openAbnormalModal() {
            this.data.abnormalModalOpen = true;
            this.renderModals();
        },
        closeAbnormalModal() {
            this.data.abnormalModalOpen = false;
            this.renderModals();
        },
        async updateThreshold() {
            const input = document.getElementById('abnormal-threshold');
            const threshold = input ? parseInt(input.value) : NaN;
            if (!isNaN(threshold)) {
                this.data.warningThreshold = threshold;
                await this.loadAbnormalStudents();
                this.renderModals();
            }
        },
        showAddNote(studentId, studentName) {
            const note = prompt(`为 ${studentName} 添加跟进备注:`);
            if (note) {
                this.addFollowNote(studentId, note);
            }
        },
        renderScoreRing(student) {
            const score = student.final_score || 0;
            const color = this.getScoreColor(score);
            const circumference = this.getRingCircumference();
            const offset = this.getRingOffset(score);
            return `
                <div class="report-score-ring">
                    <svg viewBox="0 0 120 120">
                        <circle cx="60" cy="60" r="52" fill="none" stroke="#E5E6EB" stroke-width="10" />
                        <circle cx="60" cy="60" r="52" fill="none" stroke="${color}" stroke-width="10" stroke-linecap="round"
                            stroke-dasharray="${circumference}" stroke-dashoffset="${offset}" transform="rotate(-90 60 60)" />
                    </svg>
                    <div class="report-score-text">
                        <div class="report-score-number">${score}</div>
                        <div class="report-score-unit">分</div>
                    </div>
                </div>
            `;
        },
        renderDimensionBars(student) {
            const dims = ['逻辑结构', '代码规范', '功能实现'];
            const colors = ['#1677ff', '#52C41A', '#FAAD14'];
            return dims.map((dim, idx) => {
                const item = (student.dimension_scores || []).find(d => d.dimension && d.dimension.includes(dim));
                const score = item ? item.score : null;
                const max = item ? (item.max_score || 100) : 100;
                const percentage = score !== null && score !== undefined ? Math.round((score / max) * 100) : 0;
                return `
                    <div class="report-dimension-bar">
                        <div class="report-dimension-bar-header">
                            <span>${dim}</span>
                            <span>${score !== null && score !== undefined ? score : '-'}</span>
                        </div>
                        <div class="report-dimension-bar-track">
                            <div class="report-dimension-bar-fill" style="width:${percentage}%; background:${colors[idx]}"></div>
                        </div>
                    </div>
                `;
            }).join('');
        },
        renderStudentPanel() {
            const student = this.data.selectedStudent;
            if (!student) {
                return `
                    <div class="report-card">
                        <div class="report-card-body">
                            <div class="report-empty">请从左侧表格选择学生查看详细报告</div>
                        </div>
                    </div>
                `;
            }
            const annotationsHtml = (student.code_annotations || []).length ? student.code_annotations.map(a => `
                <div class="report-annotation ${a.type}">
                    <div class="report-annotation-title">
                        <span class="icon">${a.type === 'error' ? '❌' : a.type === 'warning' ? '⚠️' : '💡'}</span>
                        <span>错误点:第${a.line}行${a.type === 'error' ? '错误' : a.type === 'warning' ? '警告' : '建议'}</span>
                    </div>
                    <div class="report-annotation-content">${a.message}</div>
                    ${a.suggestion ? `<div class="report-annotation-suggestion"><strong>修改建议:</strong>${a.suggestion}</div>` : ''}
                </div>
            `).join('') : '<div class="report-empty">暂无代码批注</div>';

            return `
                <div class="report-card">
                    <div class="report-card-body">
                        <div class="report-student-header">
                            <div>
                                <h3>单学生完整AI评价报告</h3>
                                <p>${student.student_name || '--'} | ${student.student_id || '--'} | ${student.training_title || '--'}</p>
                            </div>
                            <button class="btn btn-primary btn-sm" onclick="views.report.openReviewModal()">人工复核</button>
                        </div>

                        <div class="report-score-overview">
                            ${this.renderScoreRing(student)}
                            <div class="report-dimension-bars">
                                ${this.renderDimensionBars(student)}
                            </div>
                        </div>

                        <div class="report-section">
                            <div class="report-section-title">AI综合评语</div>
                            <div class="report-comment-box">${student.ai_comment || '暂无AI综合评语'}</div>
                        </div>

                        <div class="report-section">
                            <div class="report-section-title">班级添加跟进备注</div>
                            <textarea class="report-textarea" id="current-follow-note" rows="2" placeholder="输入跟进备注,修改记录将同步存入学生成长档案...">${this.escapeHtml(this.data.currentFollowUpNote)}</textarea>
                            <div class="report-section-actions">
                                <button class="btn btn-primary btn-sm" onclick="views.report.saveCurrentFollowNote()">保存复核记录</button>
                            </div>
                        </div>

                        <div class="report-section">
                            <div class="report-section-title">代码逐段批注</div>
                            ${annotationsHtml}
                        </div>
                    </div>
                </div>
            `;
        },
        renderCommonProblemsPanel() {
            const problems = this.data.commonProblems.slice(0, 5);
            return `
                <div class="report-card report-common-problems">
                    <div class="report-card-body">
                        <div class="report-section-title">班级共性问题汇总</div>
                        ${problems.length ? problems.map(p => `
                            <div class="problem-item">
                                <div class="report-problem-info">
                                    <span class="report-problem-name">${p.keyword}</span>
                                    <span class="report-problem-count">${p.student_count}人</span>
                                </div>
                                <div class="report-problem-bar">
                                    <div class="report-problem-bar-fill" style="width:${Math.min(p.student_count * 10, 100)}%; background:${p.severity === 'high' ? '#FF4D4F' : p.severity === 'medium' ? '#FAAD14' : '#1677ff'}"></div>
                                </div>
                            </div>
                        `).join('') : '<div class="report-empty">暂无共性问题数据</div>'}
                        <div class="report-common-problems-actions">
                            <button class="btn btn-primary btn-sm" onclick="views.report.exportProblems()">导出课堂讲解汇总</button>
                        </div>
                    </div>
                </div>
            `;
        },
        renderReviewModal() {
            const student = this.data.selectedStudent;
            if (!this.data.reviewModalOpen || !student) return '';
            return `
                <div class="report-modal-backdrop show" onclick="views.report.closeReviewModal()"></div>
                <div class="report-modal show">
                    <div class="report-modal-header">
                        <h3>人工复核</h3>
                        <button class="report-modal-close" onclick="views.report.closeReviewModal()">&times;</button>
                    </div>
                    <div class="report-modal-body">
                        <div class="form-group">
                            <label>AI评分</label>
                            <input type="text" class="form-control" value="${student.ai_score != null ? student.ai_score : '--'}" readonly>
                        </div>
                        <div class="form-group">
                            <label>教师评分</label>
                            <input type="number" class="form-control" id="review-teacher-score" value="${student.teacher_score != null ? student.teacher_score : ''}" min="0" max="100" step="0.5">
                        </div>
                        <div class="form-group">
                            <label>复核备注</label>
                            <textarea class="form-control" id="review-teacher-comment" rows="4" placeholder="输入教师评语,将同步存入学生成长档案...">${this.escapeHtml(student.teacher_comment || '')}</textarea>
                        </div>
                    </div>
                    <div class="report-modal-footer">
                        <button class="btn btn-default" onclick="views.report.closeReviewModal()">取消</button>
                        <button class="btn btn-primary" onclick="views.report.submitReview()">提交复核</button>
                    </div>
                </div>
            `;
        },
        renderAbnormalModal() {
            if (!this.data.abnormalModalOpen) return '';
            const students = this.data.abnormalStudents;
            return `
                <div class="report-modal-backdrop show" onclick="views.report.closeAbnormalModal()"></div>
                <div class="report-modal report-abnormal-modal show">
                    <div class="report-modal-header">
                        <h3>异常学生重点关注清单</h3>
                        <button class="report-modal-close" onclick="views.report.closeAbnormalModal()">&times;</button>
                    </div>
                    <div class="report-modal-body">
                        <div class="report-abnormal-toolbar">
                            <span>预警阈值:</span>
                            <input type="number" id="abnormal-threshold" value="${this.data.warningThreshold}" min="0" max="100">
                            <span>分以下</span>
                            <button class="btn btn-default btn-sm" onclick="views.report.updateThreshold()">更新</button>
                        </div>
                        ${students.length ? `
                            <div class="report-table-wrapper">
                                <table class="report-table">
                                    <thead>
                                        <tr>
                                            <th>学号</th>
                                            <th>姓名</th>
                                            <th>最终得分</th>
                                            <th>AI评分</th>
                                            <th>跟进备注</th>
                                            <th>操作</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${students.map(s => `
                                            <tr>
                                                <td>${s.student_id || '--'}</td>
                                                <td>${s.student_name || '--'}</td>
                                                <td style="color:#FF4D4F; font-weight:600">${s.final_score != null ? s.final_score : '--'}</td>
                                                <td>${s.ai_total_score != null ? s.ai_total_score : '--'}</td>
                                                <td>${s.follow_note || '-'}</td>
                                                <td>
                                                    <button class="btn btn-text" onclick="views.report.openCategoryModal(${s.id}); views.report.closeAbnormalModal()">查看报告</button>
                                                    <button class="btn btn-text" onclick="views.report.showAddNote(${s.student_id}, '${this.escapeHtml(s.student_name || '')}')">添加备注</button>
                                                </td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        ` : '<div class="report-empty">暂无低于预警阈值的学生</div>'}
                    </div>
                </div>
            `;
        },
        renderCategoryModal() {
            if (!this.data.categoryModalOpen) return '';
            const options = [
                { value: 'document', label: '文档', icon: '📄', desc: 'PDF、Word、TXT 等' },
                { value: 'ui', label: 'UI 设计截图', icon: '🖼️', desc: 'PNG、JPG、SVG 等' },
                { value: 'code', label: '源代码', icon: '💻', desc: 'PY、JS、JAVA、HTML 等' }
            ];
            return `
                <div class="report-modal-backdrop show" onclick="views.report.closeCategoryModal()"></div>
                <div class="report-modal show">
                    <div class="report-modal-header">
                        <h3>选择要查看的评价内容</h3>
                        <button class="report-modal-close" onclick="views.report.closeCategoryModal()">&times;</button>
                    </div>
                    <div class="report-modal-body">
                        <div class="category-select-grid">
                            ${options.map(opt => `
                                <label class="category-select-option">
                                    <input type="checkbox" class="category-checkbox-input" value="${opt.value}">
                                    <span class="category-select-icon">${opt.icon}</span>
                                    <span class="category-select-label">${opt.label}</span>
                                    <span class="category-select-desc">${opt.desc}</span>
                                </label>
                            `).join('')}
                        </div>
                    </div>
                    <div class="report-modal-footer">
                        <button class="btn btn-default" onclick="views.report.closeCategoryModal()">取消</button>
                        <button class="btn btn-primary" onclick="views.report.confirmCategoryView()">查看报告</button>
                    </div>
                </div>
            `;
        },
        renderModals() {
            const modalContainer = document.getElementById('report-modal-container');
            if (modalContainer) {
                modalContainer.innerHTML = this.renderCategoryModal() + this.renderReviewModal() + this.renderAbnormalModal();
            }
        },
        escapeHtml(text) {
            if (text == null) return '';
            return String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
        },
        render: async function() {
            const content = document.getElementById('page-content');
            content.innerHTML = '<div class="loading-state"><div class="spinner"></div><p>加载中...</p></div>';

            await this.loadTrainings();
            if (this.data.selectedTraining) {
                await Promise.all([
                    this.loadSubmissions(),
                    this.loadCommonProblems(),
                    this.loadAbnormalStudents(),
                    this.loadGeneratedReports()
                ]);
            }

            if (this.data.studentReports.length && !this.data.selectedStudent && !this.data.selectedSubmissionId) {
                await this.viewStudentDetail(this.data.studentReports[0].id);
                return;
            }

            const trainingOptions = this.data.trainings.map(t =>
                `<option value="${t.id}" ${this.data.selectedTraining && this.data.selectedTraining.id === t.id ? 'selected' : ''}>${this.escapeHtml(t.title)}</option>`
            ).join('');
            const reports = this.data.filteredReports;

            const activeEl = document.activeElement;
            const isSearchFocused = activeEl && activeEl.classList && activeEl.classList.contains('report-search');
            const searchSelectionStart = isSearchFocused ? activeEl.selectionStart : null;
            const searchSelectionEnd = isSearchFocused ? activeEl.selectionEnd : null;

            content.innerHTML = `
                <div class="report-page-header">
                    <div>
                        <h2>AI评阅报告</h2>
                        <p>AI自动完成全班级实训评阅,集中展示智能评价结果,减少重复批改工作</p>
                    </div>
                    <button class="btn btn-warning" onclick="views.report.openAbnormalModal()">⚠️ 异常学生清单</button>
                </div>

                <div class="report-toolbar">
                    <div class="report-toolbar-left">
                        <select class="report-select" onchange="views.report.onSelectTraining(this.value)">
                            ${trainingOptions}
                        </select>
                        <select class="report-select" onchange="views.report.onSelectClass(this.value)" ${!this.data.selectedTraining ? 'disabled' : ''}>
                            <option value="">全部班级</option>
                            ${this.data.classes.map(c => `<option value="${c.class_id}" ${this.data.selectedClass && this.data.selectedClass.class_id === c.class_id ? 'selected' : ''}>${this.escapeHtml(c.class_name)}</option>`).join('')}
                        </select>
                        <input type="text" class="report-search" placeholder="搜索学生姓名/学号,按回车搜索" value="${this.escapeHtml(this.data.searchQuery)}" oninput="views.report.onSearchInput(this.value)" onkeydown="views.report.onSearchSubmit(event)">
                        <button class="btn btn-primary" onclick="views.report.loadSubmissions().then(() => views.report.render())">查询</button>
                    </div>
                    <div class="report-toolbar-right">
                        <button class="btn btn-primary" onclick="views.report.batchExport('pdf')">批量导出全部PDF</button>
                        <button class="btn btn-success" onclick="views.report.batchExport('excel')">批量导出全部Excel</button>
                    </div>
                </div>

                <div class="report-main-grid">
                    <div class="report-card">
                        <div class="report-card-body report-table-wrapper">
                            <table class="report-table">
                                <thead>
                                    <tr>
                                        <th>序号</th>
                                        <th>学号</th>
                                        <th>姓名</th>
                                        <th>班级</th>
                                        <th>提交状态</th>
                                        <th>总分</th>
                                        <th>逻辑结构</th>
                                        <th>代码规范</th>
                                        <th>功能实现</th>
                                        <th>批注</th>
                                        <th>文件分类</th>
                                        <th>操作</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${reports.length ? reports.map((r, idx) => `
                                        <tr class="${this.data.selectedSubmissionId === r.id ? 'active' : ''}" onclick="views.report.viewStudentDetail(${r.id})">
                                            <td>${idx + 1}</td>
                                            <td>${r.student_id || '--'}</td>
                                            <td>${r.student_name || '--'}</td>
                                            <td>${r.class_name || '--'}</td>
                                            <td><span class="tag ${r.submission_status_label === '已评阅' ? 'tag-success' : r.submission_status_label === '已提交未评阅' ? 'tag-warning' : 'tag-info'}">${r.submission_status_label || '未提交'}</span></td>
                                            <td class="score-cell" style="color:${this.getScoreColor(r.final_score || 0)}">${r.final_score != null ? r.final_score : '--'}</td>
                                            <td>${this.getDimensionScore(r, '逻辑结构') != null ? this.getDimensionScore(r, '逻辑结构') : '-'}</td>
                                            <td>${this.getDimensionScore(r, '代码规范') != null ? this.getDimensionScore(r, '代码规范') : '-'}</td>
                                            <td>${this.getDimensionScore(r, '功能实现') != null ? this.getDimensionScore(r, '功能实现') : '-'}</td>
                                            <td>${this.getAnnotationCount(r)}</td>
                                            <td>${this.renderCategoryTags(r.categories)}</td>
                                            <td>
                                                <button class="btn btn-text" onclick="event.stopPropagation(); views.report.openCategoryModal(${r.id})">查看报告</button>
                                                <button class="btn btn-text" onclick="event.stopPropagation(); views.report.generateSingleReport(${r.id})">导出PDF</button>
                                            </td>
                                        </tr>
                                    `).join('') : '<tr><td colspan="12" class="report-empty">暂无数据</td></tr>'}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <div class="report-right-panel">
                        ${this.renderStudentPanel()}
                        ${this.renderCommonProblemsPanel()}
                    </div>
                </div>

                <div id="report-modal-container"></div>
            `;

            if (isSearchFocused) {
                const searchInput = content.querySelector('.report-search');
                if (searchInput) {
                    searchInput.focus();
                    if (searchSelectionStart !== null) {
                        searchInput.setSelectionRange(searchSelectionStart, searchSelectionEnd);
                    }
                }
            }

            this.renderModals();
        },
        selectTraining(trainingId) {
            this.onSelectTraining(trainingId);
        },
        switchTab(tab) {
            // 保留旧接口,避免其他调用报错
            this.data.activeTab = tab;
        }
    },

    'report-detail': {
        data: {
            submissionId: null,
            categories: [],
            detail: null,
            activeCategory: null,
            teacherScores: {},
            teacherComments: {},
            overallComment: '',
            saving: false,
            loading: true
        },
        reset() {
            this.data.submissionId = null;
            this.data.categories = [];
            this.data.detail = null;
            this.data.activeCategory = null;
            this.data.teacherScores = {};
            this.data.teacherComments = {};
            this.data.overallComment = '';
            this.data.saving = false;
            this.data.loading = true;
        },
        parseParams() {
            const submissionId = parseInt(router.getQueryParam('submission_id'), 10);
            const categoriesParam = router.getQueryParam('categories') || '';
            const categories = categoriesParam.split(',').filter(c => ['document', 'ui', 'code'].includes(c));
            return { submissionId, categories };
        },
        async loadDetail() {
            const { submissionId, categories } = this.parseParams();
            if (!submissionId || !categories.length) {
                this.data.loading = false;
                return;
            }
            this.data.submissionId = submissionId;
            this.data.categories = categories;
            try {
                const detail = await api.get(`/report/submission/${submissionId}/detail?categories=${categories.join(',')}`);
                this.data.detail = detail;
                this.data.activeCategory = categories[0];
                this.data.overallComment = detail.teacher_comment || '';
                detail.categories.forEach(cat => {
                    this.data.teacherScores[cat.category] = cat.teacher_score != null ? cat.teacher_score : '';
                    this.data.teacherComments[cat.category] = cat.teacher_comment || '';
                });
            } catch (e) {
                toast.error('加载报告详情失败: ' + (e.message || '未知错误'));
            } finally {
                this.data.loading = false;
            }
        },
        getCategoryLabel(category) {
            const labels = { document: '文档', ui: 'UI 设计截图', code: '源代码' };
            return labels[category] || category;
        },
        switchCategory(category) {
            this.data.activeCategory = category;
            this.renderContent();
        },
        onScoreInput(category, value) {
            this.data.teacherScores[category] = value;
            this.updateOverallScore();
        },
        onCommentInput(category, value) {
            this.data.teacherComments[category] = value;
        },
        onOverallCommentInput(value) {
            this.data.overallComment = value;
        },
        calculateOverallScore() {
            const weights = (this.data.detail?.training?.category_weights) || { document: 1 / 3, ui: 1 / 3, code: 1 / 3 };
            let totalWeight = 0;
            let weightedSum = 0;
            this.data.categories.forEach(cat => {
                const score = parseFloat(this.data.teacherScores[cat]);
                if (!isNaN(score)) {
                    weightedSum += score * (weights[cat] || 0);
                    totalWeight += (weights[cat] || 0);
                }
            });
            return totalWeight > 0 ? Math.round((weightedSum / totalWeight) * 10) / 10 : null;
        },
        updateOverallScore() {
            const score = this.calculateOverallScore();
            const el = document.getElementById('report-detail-overall-score');
            if (el) el.textContent = score != null ? score : '--';
        },
        goBack() {
            window.close();
            // 若未被允许关闭(非 window.open 打开),回到报告列表
            router.navigate('report');
        },
        async saveCategoryReview() {
            if (this.data.saving) return;
            const payload = {
                category_scores: {},
                category_comments: {},
                overall_comment: this.data.overallComment
            };
            this.data.categories.forEach(cat => {
                const score = parseFloat(this.data.teacherScores[cat]);
                if (!isNaN(score)) payload.category_scores[cat] = score;
                if (this.data.teacherComments[cat]) payload.category_comments[cat] = this.data.teacherComments[cat];
            });
            try {
                this.data.saving = true;
                this.renderContent();
                const res = await api.post(`/report/submission/${this.data.submissionId}/category-review`, payload);
                if (this.data.detail) this.data.detail.submission.final_score = res.final_score;
                toast.success('分类评分已保存,总体成绩已更新');
            } catch (e) {
                toast.error('保存失败: ' + (e.message || '未知错误'));
            } finally {
                this.data.saving = false;
                this.renderContent();
            }
        },
        escapeHtml(text) {
            if (text == null) return '';
            return String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
        },
        renderFilePreview(cat) {
            if (!cat.files || !cat.files.length) {
                return '<div class="report-empty">该分类下暂无文件</div>';
            }
            if (cat.category === 'ui') {
                return `
                    <div class="image-preview-grid">
                        ${cat.files.map(f => `
                            <div class="image-preview-item">
                                <img src="${f.url}" alt="${this.escapeHtml(f.filename)}" onclick="window.open('${f.url}', '_blank')">
                                <div class="image-preview-name">${this.escapeHtml(f.filename)}</div>
                            </div>
                        `).join('')}
                    </div>
                `;
            }
            if (cat.category === 'code') {
                return `
                    <div class="code-preview-list">
                        ${cat.files.map((f, idx) => `
                            <div class="code-preview-item">
                                <div class="code-preview-header">
                                    <span>${this.escapeHtml(f.filename)}</span>
                                    <a class="btn btn-text btn-sm" href="${f.url}" target="_blank">下载/查看</a>
                                </div>
                                <pre class="code-preview-body" id="code-preview-${this.data.submissionId}-${idx}" data-url="${f.url}"><code>加载中...</code></pre>
                            </div>
                        `).join('')}
                    </div>
                `;
            }
            return `
                <div class="document-preview-list">
                    ${cat.files.map(f => `
                        <div class="document-preview-item">
                            <span class="document-preview-icon">📄</span>
                            <div class="document-preview-info">
                                <div class="document-preview-name">${this.escapeHtml(f.filename)}</div>
                                <div class="document-preview-size">${this.formatFileSize(f.size)}</div>
                            </div>
                            ${f.filename.toLowerCase().endsWith('.pdf') ? `
                                <button class="btn btn-primary btn-sm" onclick="this.nextElementSibling.style.display='block';this.style.display='none'">预览 PDF</button>
                                <iframe src="${f.url}" style="display:none;width:100%;height:480px;border:1px solid var(--border-light);border-radius:var(--radius-sm);margin-top:12px;" title="${this.escapeHtml(f.filename)}"></iframe>
                            ` : `
                                <a class="btn btn-primary btn-sm" href="${f.url}" target="_blank">预览 / 下载</a>
                            `}
                        </div>
                    `).join('')}
                </div>
            `;
        },
        async loadCodeContents() {
            const nodes = document.querySelectorAll('.code-preview-body[data-url]');
            for (const node of nodes) {
                const url = node.getAttribute('data-url');
                if (!url || node.dataset.loaded) continue;
                try {
                    const res = await fetch(url);
                    if (!res.ok) throw new Error('加载失败');
                    const text = await res.text();
                    node.querySelector('code').textContent = text;
                } catch (e) {
                    node.querySelector('code').textContent = '[无法读取文件内容]';
                }
                node.dataset.loaded = 'true';
            }
        },
        formatFileSize(size) {
            if (size == null) return '';
            if (size < 1024) return size + ' B';
            if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB';
            return (size / (1024 * 1024)).toFixed(1) + ' MB';
        },
        renderScorePanel(cat) {
            const overallScore = this.calculateOverallScore();
            return `
                <div class="category-score-card">
                    <div class="category-score-row">
                        <div class="category-score-item">
                            <div class="category-score-label">AI 评分</div>
                            <div class="category-score-value">${cat.ai_score != null ? cat.ai_score : '--'}</div>
                        </div>
                        <div class="category-score-item">
                            <div class="category-score-label">教师评分</div>
                            <input type="number" class="form-control category-score-input" min="0" max="100" step="0.5"
                                value="${this.data.teacherScores[cat.category]}"
                                oninput="views['report-detail'].onScoreInput('${cat.category}', this.value)">
                        </div>
                    </div>
                    <div class="form-group" style="margin-top:12px;margin-bottom:0">
                        <label class="form-label">AI 评语</label>
                        <div class="report-comment-box">${cat.ai_reason || '暂无 AI 评语'}</div>
                    </div>
                    <div class="form-group" style="margin-top:12px;margin-bottom:0">
                        <label class="form-label">教师评语</label>
                        <textarea class="form-control" rows="3" placeholder="输入针对该分类的评语..."
                            oninput="views['report-detail'].onCommentInput('${cat.category}', this.value)">${this.escapeHtml(this.data.teacherComments[cat.category] || '')}</textarea>
                    </div>
                </div>
                <div class="overall-score-card">
                    <div class="overall-score-label">总体成绩(按训练权重自动计算)</div>
                    <div class="overall-score-value" id="report-detail-overall-score">${overallScore != null ? overallScore : '--'}</div>
                </div>
            `;
        },
        renderContent() {
            const content = document.getElementById('report-detail-content');
            if (!content) return;
            if (this.data.loading) {
                content.innerHTML = '<div class="loading-state"><div class="spinner"></div><p>加载中...</p></div>';
                return;
            }
            if (!this.data.detail) {
                content.innerHTML = '<div class="report-empty">报告详情加载失败或参数错误</div>';
                return;
            }
            const submission = this.data.detail.submission;
            const training = this.data.detail.training;
            const activeCat = this.data.detail.categories.find(c => c.category === this.data.activeCategory) || this.data.detail.categories[0];
            content.innerHTML = `
                <div class="report-detail-header">
                    <div class="report-detail-back">
                        <button class="btn btn-default" onclick="views['report-detail'].goBack()">← 返回报告列表</button>
                    </div>
                    <div class="report-detail-title">
                        <h2>${this.escapeHtml(submission.student_name || '--')} 的评阅报告</h2>
                        <p>学号:${submission.student_id || '--'} | 班级:${this.escapeHtml(submission.class_name || '--')} | 实训:${this.escapeHtml(training.title || '--')}</p>
                    </div>
                    <div class="report-detail-actions">
                        <button class="btn btn-primary" onclick="views['report-detail'].saveCategoryReview()" ${this.data.saving ? 'disabled' : ''}>
                            ${this.data.saving ? '<span class="spinner-sm"></span>保存中' : '保存复核'}
                        </button>
                    </div>
                </div>
                <div class="report-detail-body">
                    <div class="report-detail-tabs">
                        ${this.data.categories.map(cat => `
                            <button class="category-tab ${this.data.activeCategory === cat ? 'active' : ''}" onclick="views['report-detail'].switchCategory('${cat}')">
                                ${this.getCategoryLabel(cat)}
                            </button>
                        `).join('')}
                    </div>
                    <div class="report-detail-main">
                        <div class="report-detail-preview">
                            <div class="report-section-title">${this.getCategoryLabel(activeCat.category)}预览</div>
                            ${this.renderFilePreview(activeCat)}
                        </div>
                        <div class="report-detail-score">
                            ${this.renderScorePanel(activeCat)}
                            <div class="category-score-card" style="margin-top:16px">
                                <div class="form-group" style="margin-bottom:0">
                                    <label class="form-label">整体评语</label>
                                    <textarea class="form-control" rows="4" placeholder="输入整体评语,将同步存入学生成长档案..."
                                        oninput="views['report-detail'].onOverallCommentInput(this.value)">${this.escapeHtml(this.data.overallComment)}</textarea>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            this.updateOverallScore();
            this.loadCodeContents();
        },
        render: async function() {
            this.reset();
            const content = document.getElementById('page-content');
            content.innerHTML = `
                <div class="report-detail-page" id="report-detail-content">
                    <div class="loading-state"><div class="spinner"></div><p>加载中...</p></div>
                </div>
            `;
            await this.loadDetail();
            this.renderContent();
        }
    },
    growth: {
        data: {
            trainings: [],
            classes: [],
            selectedTraining: null,
            selectedClass: null,
            analysis: null,
            loading: false,
            activeFilter: '',
            searchQuery: '',
            page: 1,
            pageSize: 10,
            chartInstances: {}
        },
        async loadTrainings() {
            try {
                const res = await api.get('/courses/teacher/mine/trainings');
                this.data.trainings = (res.trainings || []).filter(t => t.status !== 'archived');
            } catch (e) {
                console.warn('获取实训列表失败:', e);
                this.data.trainings = [];
            }
        },
        async loadClasses() {
            if (!this.data.selectedTraining) {
                this.data.classes = [];
                return;
            }
            try {
                const res = await api.get(`/courses/teacher/${this.data.selectedTraining.course_id}/classes`);
                this.data.classes = res.classes || [];
            } catch (e) {
                console.warn('加载班级失败:', e);
                this.data.classes = [];
            }
        },
        async loadAnalysis() {
            if (!this.data.selectedTraining || !this.data.selectedClass) return;
            this.data.loading = true;
            this.data.analysis = null;
            this.render();
            try {
                const res = await api.get(`/growth/analysis?training_id=${this.data.selectedTraining.id}&class_id=${this.data.selectedClass.id}`);
                this.data.analysis = res;
                this.data.activeFilter = '';
                this.data.page = 1;
            } catch (e) {
                toast.error('加载成长分析失败: ' + (e.message || '未知错误'));
                this.data.analysis = null;
            } finally {
                this.data.loading = false;
                this.render();
            }
        },
        async onSelectTraining(trainingId) {
            this.data.selectedTraining = this.data.trainings.find(t => String(t.id) === String(trainingId)) || null;
            this.data.selectedClass = null;
            this.data.analysis = null;
            await this.loadClasses();
            this.render();
        },
        onSelectClass(classId) {
            this.data.selectedClass = this.data.classes.find(c => String(c.id) === String(classId)) || null;
            this.loadAnalysis();
        },
        onSearchInput(value) {
            this.data.searchQuery = value;
            this.data.page = 1;
            this.renderTableBody();
        },
        onFilterClick(key) {
            this.data.activeFilter = this.data.activeFilter === key ? '' : key;
            this.data.page = 1;
            this.renderTableBody();
        },
        onPageChange(page) {
            this.data.page = page;
            this.renderTableBody();
        },
        onPageSizeChange(size) {
            this.data.pageSize = parseInt(size, 10);
            this.data.page = 1;
            this.renderTableBody();
        },
        getFilteredStudents() {
            const analysis = this.data.analysis || {};
            let list = analysis.students || [];
            const tagMap = {
                'low_score': '连续低分',
                'declined': '提交率下降',
                'doc_weak': '文档薄弱',
                'code_weak': '代码规范薄弱',
                'logic_weak': '逻辑能力薄弱',
                'not_submitted': '未提交'
            };
            if (this.data.activeFilter) {
                const tag = tagMap[this.data.activeFilter];
                list = list.filter(s => (s.concern_tags || []).includes(tag));
            }
            const q = (this.data.searchQuery || '').trim().toLowerCase();
            if (q) {
                list = list.filter(s =>
                    (s.student_name || '').toLowerCase().includes(q) ||
                    (s.student_id || '').toLowerCase().includes(q)
                );
            }
            return list;
        },
        destroyCharts() {
            Object.values(this.data.chartInstances).forEach(chart => {
                if (chart && typeof chart.destroy === 'function') chart.destroy();
            });
            this.data.chartInstances = {};
        },
        renderTrendChart() {
            const ctx = document.getElementById('growth-trend-chart');
            if (!ctx || typeof Chart === 'undefined') return;
            const trend = (this.data.analysis && this.data.analysis.trend) || [];
            if (!trend.length) {
                ctx.parentElement.innerHTML = '<div class="report-empty" style="height:280px">暂无趋势数据</div>';
                return;
            }
            this.data.chartInstances.trend = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: trend.map(t => t.date || t.training_title),
                    datasets: [
                        {
                            label: '全班平均分',
                            data: trend.map(t => t.avg_score),
                            borderColor: '#0052D9',
                            backgroundColor: 'rgba(0, 82, 217, 0.1)',
                            fill: true,
                            tension: 0.4,
                            pointRadius: 4
                        },
                        {
                            label: '全班最高分',
                            data: trend.map(t => t.max_score),
                            borderColor: '#FAAD14',
                            backgroundColor: 'transparent',
                            fill: false,
                            tension: 0.4,
                            pointRadius: 4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { mode: 'index', intersect: false },
                    plugins: { legend: { position: 'bottom' } },
                    scales: {
                        y: { min: 0, max: 100 }
                    }
                }
            });
        },
        renderRadarChart() {
            const ctx = document.getElementById('growth-radar-chart');
            if (!ctx || typeof Chart === 'undefined') return;
            const dims = (this.data.analysis && this.data.analysis.dimensions) || [];
            if (!dims.length) {
                ctx.parentElement.innerHTML = '<div class="report-empty" style="height:280px">暂无维度数据</div>';
                return;
            }
            this.data.chartInstances.radar = new Chart(ctx, {
                type: 'radar',
                data: {
                    labels: dims.map(d => d.name),
                    datasets: [{
                        label: '班级平均',
                        data: dims.map(d => d.value),
                        borderColor: '#0052D9',
                        backgroundColor: 'rgba(0, 82, 217, 0.2)',
                        pointBackgroundColor: '#0052D9'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        r: {
                            min: 0,
                            max: 100,
                            ticks: { stepSize: 20 }
                        }
                    }
                }
            });
        },
        renderBarChart() {
            const ctx = document.getElementById('growth-bar-chart');
            if (!ctx || typeof Chart === 'undefined') return;
            const dims = (this.data.analysis && this.data.analysis.dimensions) || [];
            if (!dims.length) {
                ctx.parentElement.innerHTML = '<div class="report-empty" style="height:280px">暂无维度数据</div>';
                return;
            }
            this.data.chartInstances.bar = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: dims.map(d => d.name),
                    datasets: [{
                        label: '得分',
                        data: dims.map(d => d.value),
                        backgroundColor: dims.map(d => d.value >= 80 ? '#52C41A' : d.value >= 60 ? '#0052D9' : '#FF4D4F'),
                        borderRadius: 4,
                        barThickness: 20
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { min: 0, max: 100 },
                        y: {}
                    }
                }
            });
        },
        getConcernCounts(students) {
            const tagMap = {
                'low_score': '连续低分',
                'declined': '提交率下降',
                'doc_weak': '文档薄弱',
                'code_weak': '代码规范薄弱',
                'logic_weak': '逻辑能力薄弱',
                'not_submitted': '未提交'
            };
            const counts = {};
            Object.keys(tagMap).forEach(key => {
                counts[key] = students.filter(s => (s.concern_tags || []).includes(tagMap[key])).length;
            });
            return counts;
        },
        renderStatsCards() {
            const analysis = this.data.analysis || {};
            const stats = analysis.statistics || {};
            const rate = Math.round((stats.completion_rate || 0) * 100);
            return `
                <div class="growth-stats-row">
                    <div class="growth-stat-card primary">
                        <div class="growth-stat-value">${stats.avg_score != null ? stats.avg_score.toFixed(1) : '--'}</div>
                        <div class="growth-stat-label">班级综合平均分</div>
                        <div class="growth-stat-sub">班级人数 <strong>${stats.student_count || 0}</strong></div>
                    </div>
                    <div class="growth-stat-card success">
                        <div class="growth-stat-value">${stats.improved_count || 0}<span class="unit">人</span></div>
                        <div class="growth-stat-label">进步学生</div>
                        <div class="growth-stat-sub">待关注学生 <strong>${stats.concern_count || 0}人</strong></div>
                    </div>
                    <div class="growth-stat-card info">
                        <div class="growth-stat-value">${rate}<span class="unit">%</span></div>
                        <div class="growth-stat-label">实训完成率</div>
                        <div class="growth-stat-sub">已评价 <strong>${stats.evaluated_count || 0}/${stats.student_count || 0}</strong></div>
                    </div>
                </div>
            `;
        },
        renderTableBody() {
            const tbody = document.getElementById('growth-student-tbody');
            const pageInfo = document.getElementById('growth-page-info');
            if (!tbody) return;
            const list = this.getFilteredStudents();
            const start = (this.data.page - 1) * this.data.pageSize;
            const pageList = list.slice(start, start + this.data.pageSize);
            const totalPages = Math.ceil(list.length / this.data.pageSize) || 1;
            tbody.innerHTML = pageList.length ? pageList.map((s, idx) => {
                const change = s.change;
                const changeHtml = change != null
                    ? `<span class="growth-change ${change > 0 ? 'up' : change < 0 ? 'down' : ''}">${change > 0 ? '+' : ''}${change}</span>`
                    : '<span class="growth-change">-</span>';
                const tagsHtml = (s.concern_tags || []).length
                    ? s.concern_tags.map(t => `<span class="tag tag-danger">${t}</span>`).join(' ')
                    : '<span class="tag tag-success">正常</span>';
                return `
                    <tr>
                        <td>${start + idx + 1}</td>
                        <td>${this.escapeHtml(s.student_name)}</td>
                        <td>${this.escapeHtml(s.student_id)}</td>
                        <td>${s.current_score != null ? s.current_score : '<span class="text-muted">未提交</span>'}</td>
                        <td>${changeHtml}</td>
                        <td>${this.escapeHtml(s.strong_dimension) || '-'}</td>
                        <td>${this.escapeHtml(s.weak_dimension) || '-'}</td>
                        <td>${tagsHtml}</td>
                        <td>
                            ${s.submission_id ? `<button class="btn btn-text" onclick="views.growth.viewDetail(${s.submission_id})">详情</button>` : '-'}
                        </td>
                    </tr>
                `;
            }).join('') : '<tr><td colspan="9" class="report-empty">暂无数据</td></tr>';
            if (pageInfo) {
                pageInfo.innerHTML = `共 ${list.length} 条 第 ${this.data.page}/${totalPages} 页`;
            }
        },
        viewDetail(submissionId) {
            window.open(`#report-detail?submission_id=${submissionId}&categories=document,ui,code`, '_blank');
        },
        exportCSV() {
            const analysis = this.data.analysis;
            if (!analysis) return;
            const list = this.getFilteredStudents();
            if (!list.length) {
                toast.warning('暂无数据可导出');
                return;
            }
            const headers = ['序号', '学生姓名', '学号', '综合得分', '历史平均分', '较历史平均', '提升维度', '薄弱维度', '主要问题', '提交状态'];
            const rows = list.map((s, idx) => {
                const change = s.change != null ? `${s.change > 0 ? '+' : ''}${s.change}` : '-';
                const tags = (s.concern_tags || []).length ? s.concern_tags.join(';') : '正常';
                return [
                    idx + 1,
                    s.student_name || '',
                    s.student_id || '',
                    s.current_score != null ? s.current_score : '未提交',
                    s.historical_avg != null ? s.historical_avg : '-',
                    change,
                    s.strong_dimension || '-',
                    s.weak_dimension || '-',
                    tags,
                    s.submission_status === 'evaluated' ? '已评价' : s.submission_status === 'submitted' ? '已提交' : '未提交'
                ];
            });
            const csv = '\uFEFF' + [headers.join(','), ...rows.map(r => r.map(this.escapeCsvCell).join(','))].join('\n');
            const trainingTitle = (analysis.training && analysis.training.title) || '成长分析';
            const className = (this.data.selectedClass && this.data.selectedClass.class_name) || '';
            const filename = `${trainingTitle}${className ? '_' + className : ''}_学生成长分析.csv`;
            this.downloadBlob(csv, filename, 'text/csv');
            toast.success('导出成功');
        },
        escapeCsvCell(value) {
            const str = value == null ? '' : String(value);
            if (/[",\n\r]/.test(str)) {
                return '"' + str.replace(/"/g, '""') + '"';
            }
            return str;
        },
        downloadBlob(content, filename, mimeType) {
            const blob = new Blob([content], { type: mimeType });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
            window.URL.revokeObjectURL(url);
        },
        escapeHtml(text) {
            if (text == null) return '';
            return String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
        },
        renderConcernPanel(students) {
            const counts = this.getConcernCounts(students);
            const items = [
                { key: 'low_score', label: '连续低分', icon: '⚠️', color: '#FF4D4F' },
                { key: 'declined', label: '提交率下降', icon: '📉', color: '#FAAD14' },
                { key: 'doc_weak', label: '文档薄弱', icon: '📄', color: '#1890FF' },
                { key: 'code_weak', label: '代码规范薄弱', icon: '💻', color: '#52C41A' },
                { key: 'logic_weak', label: '逻辑能力薄弱', icon: '🧩', color: '#722ED1' },
                { key: 'not_submitted', label: '未提交', icon: '⛔', color: '#8C8C8C' }
            ];
            return `
                <div class="growth-concern-list">
                    ${items.map(item => `
                        <div class="growth-concern-item ${this.data.activeFilter === item.key ? 'active' : ''}" onclick="views.growth.onFilterClick('${item.key}')">
                            <div class="growth-concern-icon" style="background:${item.color}">${item.icon}</div>
                            <div class="growth-concern-text">
                                <div class="growth-concern-title">${item.label}</div>
                                <div class="growth-concern-count">${counts[item.key] || 0}人</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        },
        renderPagination() {
            const list = this.getFilteredStudents();
            const totalPages = Math.ceil(list.length / this.data.pageSize) || 1;
            const pages = [];
            for (let i = 1; i <= totalPages; i++) {
                pages.push(`<button class="growth-page-btn ${i === this.data.page ? 'active' : ''}" onclick="views.growth.onPageChange(${i})">${i}</button>`);
            }
            return `
                <div class="growth-pagination">
                    <button class="growth-page-btn" onclick="views.growth.onPageChange(${this.data.page - 1})" ${this.data.page <= 1 ? 'disabled' : ''}>&lt;</button>
                    ${pages.join('')}
                    <button class="growth-page-btn" onclick="views.growth.onPageChange(${this.data.page + 1})" ${this.data.page >= totalPages ? 'disabled' : ''}>&gt;</button>
                    <select class="growth-page-size" onchange="views.growth.onPageSizeChange(this.value)">
                        <option value="10" ${this.data.pageSize === 10 ? 'selected' : ''}>10条/页</option>
                        <option value="20" ${this.data.pageSize === 20 ? 'selected' : ''}>20条/页</option>
                        <option value="50" ${this.data.pageSize === 50 ? 'selected' : ''}>50条/页</option>
                    </select>
                    <span id="growth-page-info" class="growth-page-info"></span>
                </div>
            `;
        },
        render: async function() {
            await this.loadTrainings();
            const content = document.getElementById('page-content');
            const trainingOptions = this.data.trainings.map(t =>
                `<option value="${t.id}" ${this.data.selectedTraining && this.data.selectedTraining.id === t.id ? 'selected' : ''}>${this.escapeHtml(t.title)}</option>`
            ).join('');
            const classOptions = this.data.classes.map(c =>
                `<option value="${c.id}" ${this.data.selectedClass && this.data.selectedClass.id === c.id ? 'selected' : ''}>${this.escapeHtml(c.class_name)}</option>`
            ).join('');
            const analysis = this.data.analysis || {};
            const students = analysis.students || [];
            const hasData = !!analysis.statistics;

            content.innerHTML = `
                <style>
                    .growth-page-header { margin-bottom: 16px; }
                    .growth-page-header h2 { margin: 0 0 4px; font-size: 20px; color: #1D2129; }
                    .growth-page-header p { margin: 0; font-size: 13px; color: #86909C; }
                    .growth-filter-row { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; margin-bottom: 16px; }
                    .growth-filter-card { background: #fff; border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); border: 1px solid #E5E6EB; }
                    .growth-filter-card select { width: 100%; height: 36px; border: 1px solid #D9D9D9; border-radius: 6px; padding: 0 10px; margin-bottom: 10px; background: #fff; }
                    .growth-filter-card select:last-child { margin-bottom: 0; }
                    .growth-stats-row { display: contents; }
                    .growth-stat-card { background: #fff; border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); border: 1px solid #E5E6EB; border-left: 4px solid #0052D9; display: flex; flex-direction: column; justify-content: space-between; min-height: 120px; }
                    .growth-stat-card.success { border-left-color: #52C41A; }
                    .growth-stat-card.info { border-left-color: #1890FF; }
                    .growth-stat-value { font-size: 32px; font-weight: 700; color: #1D2129; line-height: 1.2; }
                    .growth-stat-value .unit { font-size: 14px; font-weight: 400; color: #86909C; margin-left: 4px; }
                    .growth-stat-label { font-size: 13px; color: #86909C; margin-top: 6px; }
                    .growth-stat-sub { font-size: 13px; color: #4E5969; display: flex; justify-content: space-between; padding-top: 10px; border-top: 1px solid #F0F0F0; }
                    .growth-stat-sub strong { color: #1D2129; }
                    .growth-chart-row { display: grid; grid-template-columns: 1.4fr 1fr 1fr; gap: 16px; margin-bottom: 16px; }
                    .growth-chart-card { background: #fff; border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); border: 1px solid #E5E6EB; }
                    .growth-chart-title { font-size: 15px; font-weight: 600; color: #1D2129; margin-bottom: 12px; }
                    .growth-chart-wrap { position: relative; height: 280px; }
                    .growth-bottom-row { display: grid; grid-template-columns: 1fr 300px; gap: 16px; }
                    .growth-table-card { background: #fff; border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); border: 1px solid #E5E6EB; min-height: 460px; }
                    .growth-table-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
                    .growth-table-header h3 { margin: 0; font-size: 15px; font-weight: 600; color: #1D2129; }
                    .growth-table-actions { display: flex; align-items: center; gap: 10px; }
                    .growth-search { width: 180px; height: 32px; border: 1px solid #D9D9D9; border-radius: 6px; padding: 0 10px; }
                    .growth-export-btn { height: 32px; padding: 0 14px; border: 1px solid #0052D9; border-radius: 6px; background: #fff; color: #0052D9; font-size: 13px; cursor: pointer; transition: all 0.2s; }
                    .growth-export-btn:hover { background: #0052D9; color: #fff; }
                    .growth-export-btn:disabled { border-color: #D9D9D9; color: #BFBFBF; background: #F5F5F5; cursor: not-allowed; }
                    .growth-concern-card { background: #fff; border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); border: 1px solid #E5E6EB; min-height: 460px; }
                    .growth-concern-card h3 { margin: 0 0 14px; font-size: 15px; font-weight: 600; color: #1D2129; }
                    .growth-concern-list { display: flex; flex-direction: column; gap: 10px; }
                    .growth-concern-item { display: flex; align-items: center; gap: 12px; padding: 12px; border-radius: 8px; background: #F7F9FC; cursor: pointer; transition: all 0.2s; border: 1px solid transparent; }
                    .growth-concern-item:hover { background: #E6F7FF; }
                    .growth-concern-item.active { background: #E6F7FF; border-color: #0052D9; }
                    .growth-concern-icon { width: 38px; height: 38px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; }
                    .growth-concern-title { font-size: 14px; font-weight: 600; color: #1D2129; }
                    .growth-concern-count { font-size: 12px; color: #86909C; margin-top: 2px; }
                    .growth-change.up { color: #52C41A; font-weight: 600; }
                    .growth-change.down { color: #FF4D4F; font-weight: 600; }
                    .growth-pagination { display: flex; align-items: center; gap: 6px; margin-top: 12px; }
                    .growth-page-btn { min-width: 28px; height: 28px; border: 1px solid #D9D9D9; border-radius: 4px; background: #fff; cursor: pointer; }
                    .growth-page-btn.active { background: #0052D9; color: #fff; border-color: #0052D9; }
                    .growth-page-btn:disabled { opacity: 0.5; cursor: not-allowed; }
                    .growth-page-size { height: 28px; border: 1px solid #D9D9D9; border-radius: 4px; background: #fff; margin-left: auto; }
                    .growth-page-info { font-size: 12px; color: #86909C; }
                    @media (max-width: 1200px) {
                        .growth-filter-row { grid-template-columns: repeat(2, minmax(0, 1fr)); }
                        .growth-chart-row { grid-template-columns: 1fr; }
                        .growth-bottom-row { grid-template-columns: 1fr; }
                    }
                    @media (max-width: 640px) {
                        .growth-filter-row { grid-template-columns: 1fr; }
                    }
                </style>

                <div class="growth-page-header">
                    <h2>学生成长分析</h2>
                    <p>基于实训评价数据,追踪班级与学生能力成长趋势</p>
                </div>

                <div class="growth-filter-row">
                    <div class="growth-filter-card">
                        <div style="font-size:14px;font-weight:600;color:#1D2129;margin-bottom:12px">班级筛选</div>
                        <select onchange="views.growth.onSelectTraining(this.value)">
                            <option value="">选择实训项目</option>
                            ${trainingOptions}
                        </select>
                        <select onchange="views.growth.onSelectClass(this.value)" ${!this.data.selectedTraining ? 'disabled' : ''}>
                            <option value="">选择班级</option>
                            ${classOptions}
                        </select>
                    </div>
                    ${hasData ? this.renderStatsCards() : '<div class="growth-stat-card" style="grid-column:span 3;justify-content:center;align-items:center;color:#86909C">请选择实训项目和班级以查看统计</div>'}
                </div>

                <div class="growth-chart-row">
                    <div class="growth-chart-card">
                        <div class="growth-chart-title">本学期成长趋势</div>
                        <div class="growth-chart-wrap">
                            <canvas id="growth-trend-chart"></canvas>
                        </div>
                    </div>
                    <div class="growth-chart-card">
                        <div class="growth-chart-title">能力维度分布</div>
                        <div class="growth-chart-wrap">
                            <canvas id="growth-radar-chart"></canvas>
                        </div>
                    </div>
                    <div class="growth-chart-card">
                        <div class="growth-chart-title">能力维度分布</div>
                        <div class="growth-chart-wrap">
                            <canvas id="growth-bar-chart"></canvas>
                        </div>
                    </div>
                </div>

                <div class="growth-bottom-row">
                    <div class="growth-table-card">
                        <div class="growth-table-header">
                            <h3>学生成长变动追踪</h3>
                            <div class="growth-table-actions">
                                <input type="text" class="growth-search" placeholder="搜索学生姓名/学号" value="${this.escapeHtml(this.data.searchQuery)}" oninput="views.growth.onSearchInput(this.value)">
                                <button class="growth-export-btn" onclick="views.growth.exportCSV()" ${!this.data.analysis ? 'disabled' : ''}>导出CSV</button>
                            </div>
                        </div>
                        <div class="report-table-wrapper">
                            <table class="report-table">
                                <thead>
                                    <tr>
                                        <th>序号</th>
                                        <th>学生姓名</th>
                                        <th>学号</th>
                                        <th>综合得分</th>
                                        <th>较历史平均</th>
                                        <th>提升维度</th>
                                        <th>薄弱维度</th>
                                        <th>主要问题</th>
                                        <th>操作</th>
                                    </tr>
                                </thead>
                                <tbody id="growth-student-tbody"></tbody>
                            </table>
                        </div>
                        ${this.renderPagination()}
                    </div>
                    <div class="growth-concern-card">
                        <h3>待关注学生</h3>
                        ${this.renderConcernPanel(students)}
                    </div>
                </div>
            `;

            if (this.data.loading) {
                content.innerHTML += '<div class="loading-state" style="position:fixed;top:50%;left:50%;transform:translate(-50%,-50%)"><div class="spinner"></div><p>加载中...</p></div>';
            }

            this.destroyCharts();
            if (hasData) {
                setTimeout(() => {
                    this.renderTrendChart();
                    this.renderRadarChart();
                    this.renderBarChart();
                    this.renderTableBody();
                }, 0);
            }
        }
    }
};

function updateMessageBadge(count) {
    const badge = document.getElementById('message-badge');
    if (!badge) return;
    badge.style.display = count > 0 ? 'block' : 'none';
}

const WEEKDAY_NAMES = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'];

function pad2(n) {
    return String(n).padStart(2, '0');
}

function updateWorkbenchClock() {
    const timeEl = document.getElementById('header-time');
    const dateEl = document.getElementById('header-date');
    if (!timeEl || !dateEl) return;
    const now = new Date();
    timeEl.textContent = `${pad2(now.getHours())}:${pad2(now.getMinutes())}`;
    dateEl.textContent = `${now.getFullYear()}年${pad2(now.getMonth() + 1)}月${pad2(now.getDate())}日 ${WEEKDAY_NAMES[now.getDay()]}`;
}

function renderSemesterInfo(info) {
    const weekEl = document.getElementById('header-week');
    const pillTextEl = weekEl ? weekEl.querySelector('.pill-text') : null;
    const statusEl = document.getElementById('hero-semester-status');
    if (pillTextEl) {
        if (!info || info.ended) {
            pillTextEl.textContent = info && info.label ? `${info.label}已结束` : '暂无学期数据';
        } else if (info.not_started) {
            pillTextEl.textContent = `${info.label}未开始`;
        } else {
            pillTextEl.textContent = `教学周:第 ${info.week} 周`;
        }
    }
    if (statusEl) {
        if (!info || info.ended) {
            statusEl.textContent = '';
        } else if (info.not_started) {
            statusEl.textContent = `距开学还有 ${info.days_remaining} 天`;
        } else {
            statusEl.textContent = `本学期剩余 ${info.days_remaining} 天`;
        }
    }
}

async function initWorkbench() {
    updateWorkbenchClock();
    if (window._workbenchTimer) {
        clearInterval(window._workbenchTimer);
    }
    window._workbenchTimer = setInterval(updateWorkbenchClock, 1000);

    try {
        const info = await api.get('/semesters/current');
        renderSemesterInfo(info);
    } catch (e) {
        console.warn('获取学期信息失败:', e);
        renderSemesterInfo(null);
    }
}

/* ======================================
   初始化
   ====================================== */
document.addEventListener('DOMContentLoaded', () => {
    // 加载用户信息
    const userStr = localStorage.getItem('user');
    if (!userStr) {
        // 未登录,跳回登录页
        window.location.href = 'login.html';
        return;
    }
    try {
        const user = JSON.parse(userStr);
        const avatarEl = document.getElementById('user-avatar-letter');
        const nameEl = document.getElementById('user-display-name');
        const roleEl = document.getElementById('user-role-label');
        if (avatarEl) avatarEl.textContent = user.display_name ? user.display_name.charAt(0) : '?';
        if (nameEl) nameEl.textContent = user.display_name || user.username;
        if (roleEl) roleEl.textContent = user.role === 'super_admin' ? '超级管理员' : user.role === 'admin' ? '管理员' : user.role === 'student' ? '学生' : '教师';
    } catch (e) {
        // ignore
    }

    // 初始化消息红点(有消息时显示,count 替换为真实未读数)
    updateMessageBadge(0);

    // 初始化顶部工作台信息(时间、日期、教学周)
    initWorkbench();

    // 点击 Hero 学期选择器外部时关闭下拉
    document.addEventListener('click', (e) => {
        const selector = document.getElementById('hero-semester-selector');
        if (selector && !selector.contains(e.target)) {
            semesterSelector.close();
        }
    });

    if (!window.location.hash) {
        window.location.hash = '#dashboard';
    }
    syncNavActive();
    const page = router.current || 'dashboard';
    if (views[page] && typeof views[page].render === 'function') {
        views[page].render().catch(function(e) {
            console.error('渲染失败:', e);
            document.getElementById('page-content').innerHTML = '<div style="padding:40px;color:#e74c3c">页面渲染失败: ' + (e && e.message ? e.message : e) + '</div>';
        }).finally(function() {
            window.scrollTo(0, 0);
        });
    } else {
        console.error('视图不存在:', page);
        document.getElementById('page-content').innerHTML = '<div style="padding:40px;color:#999">视图加载失败: ' + page + '</div>';
    }
});

window.addEventListener('hashchange', () => {
    syncNavActive();
    const page = router.current || 'dashboard';
    if (views[page] && typeof views[page].render === 'function') {
        Promise.resolve(views[page].render()).catch(function(e) {
            console.error('渲染失败:', e);
            document.getElementById('page-content').innerHTML = '<div style="padding:40px;color:#e74c3c">页面渲染失败: ' + (e && e.message ? e.message : e) + '</div>';
        }).finally(function() {
            window.scrollTo(0, 0);
        });
    }
});

/* ======================================
   退出登录
   ====================================== */
function handleLogout() {
    localStorage.removeItem('user');
    window.location.href = 'login.html';
}






