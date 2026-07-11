const fs = require('fs');
const c = fs.readFileSync('F:\\xiangmu\\training-evaluation-system\\frontend\\app.js', 'utf8');
const checks = [
  ['renderStepIndicator() in render()', c.includes('self.renderStepIndicator()')],
  ['loadTemplates in render()', c.includes('await self.loadTemplates()')],
  ['tc-draft-btn removed', !c.includes('tc-draft-btn')],
  ['handleSaveDraft removed', !c.includes('handleSaveDraft')],
  ['bindUploadEvents removed from init', !c.includes('self.bindUploadEvents()')],
  ['new renderStep0 (基本信息)', c.includes('<h4>基本信息</h4>') && c.includes('实训描述（选填）')],
  ['new renderStep1 (实训时间)', c.includes('<h4>实训时间</h4>') && c.includes('tc-end_time')],
  ['renderStep1 uses this.value in toggleMaterial', c.includes('toggleMaterial(this.value, this.checked)')],
  ['renderStep1 has statusHintClass', c.includes('statusHintClass')],
  ['new renderStep1 (提交材料)', c.includes('<h4>提交材料</h4>')],
  ['new renderStep1 (分配班级)', c.includes('<h4>分配班级</h4>')],
  ['renderStep1 materials = this.data.formData.required_materials || []', c.includes('const materials = this.data.formData.required_materials || []')],
  ['new renderStep2 (评价规则)', c.includes('<h4>评价规则</h4>') && c.includes('evaluation_template_id')],
  ['getAutoStatus method', c.includes('getAutoStatus()')],
  ['getAutoStatusText method', c.includes('getAutoStatusText()')],
  ['toggleMaterial method', c.includes('toggleMaterial(value, checked)')],
  ['loadTemplates method', c.includes('async loadTemplates()')],
  ['renderPreview removed', !c.includes('renderPreview()')],
  ['updatePreview removed', !c.includes('updatePreview()')],
  ['bindPreviewEvents removed', !c.includes('bindPreviewEvents')],
  ['selectScoringMethod removed', !c.includes('selectScoringMethod')],
  ['toggleDimension removed', !c.includes('toggleDimension')],
  ['bindUploadEvents method removed', !c.includes('bindUploadEvents()')],
  ['_bindUploadBox removed', !c.includes('_bindUploadBox')],
  ['handleFileChange removed', !c.includes('handleFileChange')],
  ['pendingCodeFile removed', !c.includes('pendingCodeFile')],
  ['collectPayload updated', c.includes('start_time: d.start_time') && c.includes('end_time: d.end_time') && c.includes('required_materials: d.required_materials')],
  ['handleSubmit updated', c.includes('status: self.getAutoStatus()')],
  ['datetime-local inputs', c.includes('datetime-local')],
  ['no 📋 in tc-page-title-icon', !c.includes('tc-page-title-icon')],
  ['allow_late_submission removed', !c.includes('allow_late_submission')],
  ['no double comma },', !c.includes('},,')],
  ['no extra blank }, before syncForm', !c.match(/},\r\n\r\n        },\r\n\r\n        syncForm/)],
];

let allPassed = true;
checks.forEach(([label, result]) => {
    console.log(result ? '✅' : '❌', label);
    if (!result) allPassed = false;
});

console.log('\n' + (allPassed ? 'ALL CHECKS PASSED ✅' : 'SOME CHECKS FAILED ❌'));
console.log('File size:', c.length);
