const fs = require('fs');
const filePath = 'F:\\xiangmu\\training-evaluation-system\\frontend\\app.js';
let content = fs.readFileSync(filePath, 'utf8');

// Helper: ensure CRLF in replacement text
function crlfify(str) {
    // Convert any bare \n to \r\n, but don't double-convert existing \r\n
    return str.replace(/\r?\n/g, '\r\n');
}

// =============================================
// 1. Replace renderStep0() method entirely
// =============================================
const newStep0 = crlfify(`        renderStep0() {
            const esc = views.training.escapeHtml;
            const d = this.data.formData;
            const materials = this.data.formData.required_materials || [];
            return \`
                <div class="training-create-step \${this.data.currentStep === 0 ? '' : 'hidden'}" data-step="0">
                    <div class="tc-section-card">
                        <div class="tc-section-header">
                            <div>
                                <h4>基本信息</h4>
                                <p>填写实训标题、课程与描述</p>
                            </div>
                        </div>
                        <div class="tc-section-body">
                            <div class="tc-form-row">
                                <div class="tc-form-group required tc-full">
                                    <label>实训标题</label>
                                    <input type="text" id="tc-title" value="\${esc(d.title)}" placeholder="如：Web全栈开发实训" oninput="views['training/create'].syncForm('title', this.value)">
                                </div>
                            </div>
                            <div class="tc-form-row">
                                <div class="tc-form-group required">
                                    <label>课程名称</label>
                                    <input type="text" id="tc-course_name" value="\${esc(d.course_name)}" placeholder="如：软件工程实训" oninput="views['training/create'].syncForm('course_name', this.value)">
                                </div>
                                <div class="tc-form-group">
                                    <label>指导教师</label>
                                    <input type="text" id="tc-teacher_name" value="\${esc(d.teacher_name)}" placeholder="请输入指导教师姓名" oninput="views['training/create'].syncForm('teacher_name', this.value)">
                                </div>
                            </div>
                            <div class="tc-form-row">
                                <div class="tc-form-group">
                                    <label>实训描述（选填）</label>
                                    <textarea id="tc-description" rows="4" placeholder="详细描述实训目标、要求和背景信息" oninput="views['training/create'].syncForm('description', this.value)">\${esc(d.description)}</textarea>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            \`;
        },`);

// Find renderStep0 start and end (up to the closing }, followed by blank line then renderStep1)
const step0Start = content.indexOf('        renderStep0() {\r\n');
const step0EndMarker = '        },\r\n\r\n        renderStep1()';
const step0End = content.indexOf(step0EndMarker);
if (step0Start === -1 || step0End === -1) {
    console.error('Could not find renderStep0 boundaries:', step0Start, step0End);
    process.exit(1);
}
// Replace from start of renderStep0 to end of its closing },
const step0ReplaceEnd = step0End + '        },'.length;
content = content.substring(0, step0Start) + newStep0 + content.substring(step0ReplaceEnd);

// =============================================
// 2. Replace renderStep1() method entirely
// =============================================
const newStep1 = crlfify(`        renderStep1() {
            const esc = views.training.escapeHtml;
            const d = this.data.formData;
            const classes = this.data.classes || [];
            const materials = this.data.formData.required_materials || [];
            const autoStatus = this.getAutoStatus();
            const autoStatusText = this.getAutoStatusText();
            const statusHintClass = autoStatus === 'unset' ? 'unset' : autoStatus;
            const statusHintColor = { pending: '#d48806', active: '#389e0d', closed: '#cf1322', unset: '#999' }[autoStatus];
            return \`
                <div class="training-create-step \${this.data.currentStep === 1 ? '' : 'hidden'}" data-step="1">
                    <div class="tc-section-card">
                        <div class="tc-section-header">
                            <div>
                                <h4>实训时间</h4>
                                <p>设置开始与截止时间，精确到分钟；截止时间不可早于开始时间</p>
                            </div>
                        </div>
                        <div class="tc-section-body">
                            <div class="tc-form-row">
                                <div class="tc-form-group required">
                                    <label>截止时间</label>
                                    <input type="datetime-local" id="tc-end_time" value="\${esc(d.end_time)}" onchange="views['training/create'].syncForm('end_time', this.value)">
                                </div>
                                <div class="tc-form-group required">
                                    <label>开始时间</label>
                                    <input type="datetime-local" id="tc-start_time" value="\${esc(d.start_time)}" onchange="views['training/create'].syncForm('start_time', this.value)">
                                </div>
                            </div>
                            <div class="tc-time-status-hint \${statusHintClass}" style="border-left:3px solid \${statusHintColor}">
                                <span>ℹ️</span>
                                <span>项目状态：<strong>\${autoStatusText}</strong>（根据开始/截止时间自动计算）</span>
                            </div>
                        </div>
                    </div>

                    <div class="tc-section-card">
                        <div class="tc-section-header">
                            <div>
                                <h4>提交材料</h4>
                                <p>选择学生需同时提交的材料类型（默认全选）</p>
                            </div>
                        </div>
                        <div class="tc-section-body">
                            <div class="tc-materials-group">
                                <label class="tc-material-checkbox \${materials.includes('source_code') ? 'active' : ''}">
                                    <input type="checkbox" value="source_code" \${materials.includes('source_code') ? 'checked' : ''} onchange="views['training/create'].toggleMaterial(this.value, this.checked)">
                                    <span>📄 源代码</span>
                                </label>
                                <label class="tc-material-checkbox \${materials.includes('document') ? 'active' : ''}">
                                    <input type="checkbox" value="document" \${materials.includes('document') ? 'checked' : ''} onchange="views['training/create'].toggleMaterial(this.value, this.checked)">
                                    <span>📝 文档</span>
                                </label>
                                <label class="tc-material-checkbox \${materials.includes('screenshot') ? 'active' : ''}">
                                    <input type="checkbox" value="screenshot" \${materials.includes('screenshot') ? 'checked' : ''} onchange="views['training/create'].toggleMaterial(this.value, this.checked)">
                                    <span>🖼️ 截图 / 界面</span>
                                </label>
                            </div>
                        </div>
                    </div>

                    <div class="tc-section-card">
                        <div class="tc-section-header">
                            <div>
                                <h4>分配班级</h4>
                                <p>选择可参与本实训的班级（可多选）</p>
                            </div>
                        </div>
                        <div class="tc-section-body">
                            <div class="training-class-grid">
                                \${classes.length ? classes.map(c => \`
                                    <div class="training-class-card \${d.class_ids.includes(String(c.id)) || d.class_ids.includes(Number(c.id)) ? 'active' : ''}"
                                         role="checkbox"
                                         tabindex="0"
                                         data-class-id="\${c.id}"
                                         onclick="views['training/create'].toggleClassCheckbox(this, '\${c.id}')"
                                         onkeydown="if(event.key===' '||event.key==='Enter'){event.preventDefault();views['training/create'].toggleClassCheckbox(this,'\${c.id}')}">
                                        <span class="training-class-check">✓</span>
                                        <span class="training-class-name">\${esc(c.class_name)}</span>
                                        <span class="training-class-count">\${c.student_count || 0}人</span>
                                    </div>
                                \`).join('') : '<p style="color:var(--text-muted);padding:8px 0;">暂无授课班级，请先确认教师-班级关联</p>'}
                            </div>
                        </div>
                    </div>
                </div>
            \`;
        },`);

const step1Start = content.indexOf('        renderStep1() {\r\n');
const step1EndMarker = '        },\r\n\r\n        renderStep2()';
const step1End = content.indexOf(step1EndMarker);
if (step1Start === -1 || step1End === -1) {
    console.error('Could not find renderStep1 boundaries:', step1Start, step1End);
    process.exit(1);
}
const step1ReplaceEnd = step1End + '        },'.length;
content = content.substring(0, step1Start) + newStep1 + content.substring(step1ReplaceEnd);

// =============================================
// 3. Replace renderStep2() method entirely
// =============================================
const newStep2 = crlfify(`        renderStep2() {
            const esc = views.training.escapeHtml;
            const d = this.data.formData;
            const templates = this.data.templates || [];
            return \`
                <div class="training-create-step \${this.data.currentStep === 2 ? '' : 'hidden'}" data-step="2">
                    <div class="tc-section-card">
                        <div class="tc-section-header">
                            <div>
                                <h4>评价规则</h4>
                                <p>配置评价模板、总分与及格分数线（可选）</p>
                            </div>
                        </div>
                        <div class="tc-section-body">
                            <div class="tc-form-row">
                                <div class="tc-form-group tc-full">
                                    <label>评价模板（可选）</label>
                                    <select id="tc-evaluation_template_id" onchange="views['training/create'].syncForm('evaluation_template_id', this.value)">
                                        <option value="">-- 选择评价模板 --</option>
                                        \${templates.map(t => \`<option value="\${t.id}" \${d.evaluation_template_id == t.id ? 'selected' : ''}>\${esc(t.name)}</option>\`).join('')}
                                    </select>
                                </div>
                            </div>
                            <div class="tc-form-row">
                                <div class="tc-form-group">
                                    <label>总分</label>
                                    <input type="number" id="tc-total_score" value="\${d.total_score}" min="0" max="100" step="5" onchange="views['training/create'].syncForm('total_score', parseInt(this.value||0,10))">
                                </div>
                                <div class="tc-form-group">
                                    <label>及格分数</label>
                                    <input type="number" id="tc-pass_score" value="\${d.pass_score}" min="0" max="\${d.total_score}" step="5" onchange="views['training/create'].syncForm('pass_score', parseInt(this.value||0,10))">
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            \`;
        },`);

const step2Start = content.indexOf('        renderStep2() {\r\n');
// Find the end of renderStep2 - it's followed by renderPreview() or similar
// Let's find the next method after renderStep2
const step2EndPattern = '        },\r\n\r\n        renderPreview()';
const step2End = content.indexOf(step2EndPattern);
if (step2Start === -1 || step2End === -1) {
    console.error('Could not find renderStep2 boundaries:', step2Start, step2End);
    process.exit(1);
}
const step2ReplaceEnd = step2End + '        },'.length;
content = content.substring(0, step2Start) + newStep2 + content.substring(step2ReplaceEnd);

// =============================================
// 4. Delete renderPreview(), updatePreview(), bindPreviewEvents()
// =============================================
const previewStart = content.indexOf('        renderPreview() {\r\n');
const previewEndPattern = '        },\r\n\r\n        syncForm(field, value, el)';
const previewEnd = content.indexOf(previewEndPattern);
if (previewStart !== -1 && previewEnd !== -1) {
    const previewReplaceEnd = previewEnd; // We'll remove up to just before syncForm
    content = content.substring(0, previewStart) + content.substring(previewReplaceEnd);
    console.log('Removed renderPreview, updatePreview, bindPreviewEvents');
} else {
    console.error('Could not find preview methods boundaries:', previewStart, previewEnd);
}

// =============================================
// 5. Remove toggleDimension() and selectScoringMethod() methods
// =============================================
// Find toggleDimension
const toggleDimStart = content.indexOf('        toggleDimension(value, el) {\r\n');
const toggleDimEnd = content.indexOf('        },\r\n\r\n        selectScoringMethod(value)');
if (toggleDimStart !== -1 && toggleDimEnd !== -1) {
    const toggleDimReplaceEnd = toggleDimEnd + '        },'.length;
    content = content.substring(0, toggleDimStart) + content.substring(toggleDimReplaceEnd);
    console.log('Removed toggleDimension');
} else {
    console.error('Could not find toggleDimension boundaries:', toggleDimStart, toggleDimEnd);
}

// Find selectScoringMethod
const selectScoreStart = content.indexOf('        selectScoringMethod(value) {\r\n');
const selectScoreEnd = content.indexOf('        },\r\n\r\n        toggleClassCheckbox(el, classId)');
if (selectScoreStart !== -1 && selectScoreEnd !== -1) {
    const selectScoreReplaceEnd = selectScoreEnd; // keep the blank line before toggleClassCheckbox
    content = content.substring(0, selectScoreStart) + content.substring(selectScoreReplaceEnd);
    console.log('Removed selectScoringMethod');
} else {
    console.error('Could not find selectScoringMethod boundaries:', selectScoreStart, selectScoreEnd);
}

// =============================================
// 6. Add getAutoStatus(), getAutoStatusText(), toggleMaterial() after toggleClassCheckbox
// =============================================
const newMethods = crlfify(`,

        getAutoStatus() {
            const d = this.data.formData;
            const now = new Date();
            if (d.start_time && new Date(d.start_time) > now) return 'pending';
            if (d.end_time && new Date(d.end_time) < now) return 'closed';
            if (d.start_time || d.end_time) return 'active';
            return 'unset';
        },

        getAutoStatusText() {
            const map = { pending: '未开始', active: '进行中', closed: '已结束', unset: '未设置' };
            return map[this.getAutoStatus()] || '未设置';
        },

        toggleMaterial(value, checked) {
            const mats = this.data.formData.required_materials;
            if (checked && !mats.includes(value)) {
                mats.push(value);
            } else if (!checked) {
                const idx = mats.indexOf(value);
                if (idx > -1) mats.splice(idx, 1);
            }
            // Update checkbox label styling
            document.querySelectorAll('.tc-material-checkbox').forEach(label => {
                const input = label.querySelector('input');
                label.classList.toggle('active', input.checked);
            });
        },`);

// Find the end of toggleClassCheckbox method
const toggleClassCheckboxEnd = content.indexOf('        },\r\n\r\n        bindUploadEvents()');
if (toggleClassCheckboxEnd !== -1) {
    const insertPoint = toggleClassCheckboxEnd + '        },'.length;
    content = content.substring(0, insertPoint) + newMethods + content.substring(insertPoint);
    console.log('Added getAutoStatus, getAutoStatusText, toggleMaterial');
} else {
    console.error('Could not find toggleClassCheckbox end:', toggleClassCheckboxEnd);
}

// =============================================
// 7. Add loadTemplates() after loadClasses()
// =============================================
const loadTemplatesMethod = crlfify(`,

        async loadTemplates() {
            try {
                const res = await api.get('/evaluation/templates');
                this.data.templates = res.templates || res || [];
            } catch (e) {
                this.data.templates = [];
            }
        },`);

const loadClassesEnd = content.indexOf('        },\r\n\r\n        async render() {\r\n            const self = views[');
if (loadClassesEnd !== -1) {
    const insertPoint = loadClassesEnd + '        },'.length;
    content = content.substring(0, insertPoint) + loadTemplatesMethod + content.substring(insertPoint);
    console.log('Added loadTemplates after loadClasses');
} else {
    console.error('Could not find loadClasses end:', loadClassesEnd);
}

// =============================================
// 8. Delete bindUploadEvents, _bindUploadBox, handleFileChange, updateUploadStatus, clearPendingFile
// =============================================
const uploadStart = content.indexOf('        bindUploadEvents() {\r\n');
// Find the end - these methods end before setStep
const uploadEndPattern = '        },\r\n\r\n        setStep(step)';
const uploadEnd = content.indexOf(uploadEndPattern);
if (uploadStart !== -1 && uploadEnd !== -1) {
    const uploadReplaceEnd = uploadEnd; // keep the blank line before setStep
    content = content.substring(0, uploadStart) + content.substring(uploadReplaceEnd);
    console.log('Removed upload-related methods');
} else {
    console.error('Could not find upload methods boundaries:', uploadStart, uploadEnd);
}

// =============================================
// 9. Replace validateStep() method
// =============================================
const newValidateStep = crlfify(`        validateStep(step) {
            const d = this.data.formData;
            if (step === 0) {
                const title = (document.getElementById('tc-title')?.value || '').trim();
                const courseName = (document.getElementById('tc-course_name')?.value || '').trim();
                if (!title) { toast.error('请输入实训标题'); return false; }
                if (!courseName) { toast.error('请输入课程名称'); return false; }
                d.title = title;
                d.course_name = courseName;
                d.teacher_name = (document.getElementById('tc-teacher_name')?.value || '').trim();
                d.description = (document.getElementById('tc-description')?.value || '').trim();
            } else if (step === 1) {
                const endTime = document.getElementById('tc-end_time')?.value || '';
                const startTime = document.getElementById('tc-start_time')?.value || '';
                if (!endTime) { toast.error('请选择截止时间'); return false; }
                if (!startTime) { toast.error('请选择开始时间'); return false; }
                if (endTime && startTime && new Date(endTime) < new Date(startTime)) {
                    toast.error('截止时间不可早于开始时间');
                    return false;
                }
                d.end_time = endTime;
                d.start_time = startTime;
            } else if (step === 2) {
                d.total_score = parseInt(document.getElementById('tc-total_score')?.value || '100', 10);
                d.pass_score = parseInt(document.getElementById('tc-pass_score')?.value || '60', 10);
                d.evaluation_template_id = document.getElementById('tc-evaluation_template_id')?.value || null;
                if (d.pass_score > d.total_score) {
                    toast.error('及格分数不能高于总分');
                    return false;
                }
            }
            return true;
        },`);

const validateStart = content.indexOf('        validateStep(step) {\r\n');
const validateEndPattern = '        },\r\n\r\n        collectPayload()';
const validateEnd = content.indexOf(validateEndPattern);
if (validateStart !== -1 && validateEnd !== -1) {
    const validateReplaceEnd = validateEnd + '        },'.length;
    content = content.substring(0, validateStart) + newValidateStep + content.substring(validateReplaceEnd);
    console.log('Replaced validateStep');
} else {
    console.error('Could not find validateStep boundaries:', validateStart, validateEnd);
}

// =============================================
// 10. Replace collectPayload() and handleSubmit() and remove handleSaveDraft()
// =============================================
// Replace from collectPayload through end of handleSubmit, removing handleSaveDraft too
const newPayloadAndSubmit = crlfify(`        collectPayload() {
            const d = this.data.formData;
            const self = views['training/create'];
            const classIds = d.class_ids.map(id => parseInt(id, 10)).filter(id => !isNaN(id));

            return {
                title: d.title,
                course_name: d.course_name,
                teacher_name: d.teacher_name,
                description: d.description,
                start_time: d.start_time,
                end_time: d.end_time,
                required_materials: d.required_materials,
                class_ids: classIds,
                evaluation_template_id: d.evaluation_template_id || null,
                scoring_method: d.scoring_method,
                total_score: d.total_score,
                pass_score: d.pass_score,
                status: self.getAutoStatus() === 'unset' ? 'active' : self.getAutoStatus(),
            };
        },

        async handleSubmit() {
            if (!this.validateStep(0) || !this.validateStep(1) || !this.validateStep(2)) return;

            const payload = this.collectPayload();
            try {
                this.data.loading = true;
                const result = await api.post('/training/create', JSON.stringify(payload));

                toast.success('实训项目已创建');
                this.resetForm();
                router.navigate('training');
                await views.training.loadTrainings();
                views.training.render();
            } catch (e) {
                toast.error(e.message || '创建失败');
            } finally {
                this.data.loading = false;
            }
        }
    }
};`);

// Find collectPayload start
const payloadStart = content.indexOf('        collectPayload() {\r\n');
// Find the end - this goes to the closing of the entire 'training/create' view
// which ends with the handleSubmit method and then `    }\n};`
const handleSubmitEndPattern = '        }\r\n    }\r\n};';
const payloadEnd = content.indexOf(handleSubmitEndPattern);
if (payloadStart !== -1 && payloadEnd !== -1) {
    const payloadReplaceEnd = payloadEnd + handleSubmitEndPattern.length;
    content = content.substring(0, payloadStart) + newPayloadAndSubmit + content.substring(payloadReplaceEnd);
    console.log('Replaced collectPayload, handleSubmit, removed handleSaveDraft');
} else {
    console.error('Could not find collectPayload/handleSubmit boundaries:', payloadStart, payloadEnd);
}

// =============================================
// 11. Remove pendingFile and pendingCodeFile from data object
// =============================================
content = content.replace('            pendingFile: null,\r\n            pendingCodeFile: null,\r\n', '');

// =============================================
// Write back
// =============================================
fs.writeFileSync(filePath, content, 'utf8');
console.log('File written successfully. New size:', content.length);
