const fs = require('fs');
const filePath = 'F:\\xiangmu\\training-evaluation-system\\frontend\\app.js';
let content = fs.readFileSync(filePath, 'utf8');

function crlfify(str) {
    return str.replace(/\r?\n/g, '\r\n');
}

// =============================================
// 1. Replace renderStep1() method to match spec exactly
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

// Find renderStep1 boundaries
const step1Start = content.indexOf('        renderStep1() {\r\n');
// Find the end of renderStep1 - it's followed by blank line then renderStep2
const step1EndMarker = '        },\r\n\r\n        renderStep2()';
const step1End = content.indexOf(step1EndMarker);
if (step1Start !== -1 && step1End !== -1) {
    const step1ReplaceEnd = step1End + '        },'.length;
    content = content.substring(0, step1Start) + newStep1 + content.substring(step1ReplaceEnd);
    console.log('✅ Replaced renderStep1');
} else {
    console.error('❌ Could not find renderStep1 boundaries:', step1Start, step1End);
    process.exit(1);
}

// =============================================
// 2. Fix renderStep2 - remove extra }, at end
// =============================================
// The current renderStep2 ends with:
//        },
//
//        },
//
// We need to remove the extra },
const pattern = '        },\r\n\r\n        },\r\n\r\n        syncForm(field, value, el)';
const replacement = '        },\r\n\r\n        syncForm(field, value, el)';
if (content.includes(pattern)) {
    content = content.replace(pattern, replacement);
    console.log('✅ Removed extra }, after renderStep2');
} else {
    console.log('⚠️ Extra }, after renderStep2 pattern not found - checking alternatives');
    // Try to find it with different whitespace
    const idx = content.indexOf('        },\r\n\r\n        },\r\n\r\n        syncForm');
    if (idx !== -1) {
        console.log('Found at index:', idx);
    } else {
        console.log('Pattern definitely not found, checking current state around syncForm');
        const sfIdx = content.indexOf('syncForm(field, value, el)');
        console.log('syncForm found at:', sfIdx);
        // Read 100 chars before syncForm
        console.log('Before syncForm:', content.substring(sfIdx - 50, sfIdx));
    }
}

// =============================================
// 3. Remove allow_late_submission references from syncForm  
// (already done in previous edit, verify)
// =============================================
if (content.includes('allow_late_submission')) {
    console.log('⚠️ allow_late_submission still found');
} else {
    console.log('✅ allow_late_submission removed');
}

// =============================================
// 4. Verify all other requirements
// =============================================
const checks = [
  ['renderStepIndicator in render()', content.includes('self.renderStepIndicator()')],
  ['loadTemplates in render()', content.includes('await self.loadTemplates()')],
  ['tc-draft-btn removed', !content.includes('tc-draft-btn')],
  ['handleSaveDraft removed', !content.includes('handleSaveDraft')],
  ['bindUploadEvents removed', !content.includes('self.bindUploadEvents()')],
  ['renderPreview removed', !content.includes('renderPreview()')],
  ['bindPreviewEvents removed', !content.includes('bindPreviewEvents')],
  ['selectScoringMethod removed', !content.includes('selectScoringMethod')],
  ['toggleDimension removed', !content.includes('toggleDimension')],
  ['bindUploadEvents method removed', !content.includes('bindUploadEvents() {')],
  ['_bindUploadBox removed', !content.includes('_bindUploadBox')],
  ['handleFileChange removed', !content.includes('handleFileChange')],
  ['pendingFile removed from create view data', !content.includes('pendingCodeFile')],
  ['updatePreview removed from syncForm', !content.includes('this.updatePreview()')],
  ['collectPayload updated', content.includes('start_time: d.start_time') && content.includes('end_time: d.end_time') && content.includes('required_materials: d.required_materials')],
  ['handleSubmit updated', content.includes('status: self.getAutoStatus()')],
  ['getAutoStatus method', content.includes('getAutoStatus()')],
  ['getAutoStatusText method', content.includes('getAutoStatusText()')],
  ['toggleMaterial method', content.includes('toggleMaterial(value, checked)')],
  ['loadTemplates method', content.includes('async loadTemplates()')],
  ['datetime-local inputs', content.includes('datetime-local')],
];

checks.forEach(([label, result]) => {
    console.log(result ? '✅' : '❌', label);
});

// Write back
fs.writeFileSync(filePath, content, 'utf8');
console.log('\nFile written successfully. New size:', content.length);
