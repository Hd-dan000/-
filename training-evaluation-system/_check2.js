const fs = require('fs');
const c = fs.readFileSync('F:\\xiangmu\\training-evaluation-system\\frontend\\app.js', 'utf8');
const checks = [
  ['renderStepIndicator() in render()', c.includes('self.renderStepIndicator()')],
  ['loadTemplates in render()', c.includes('await self.loadTemplates()')],
  ['tc-draft-btn removed', !c.includes('tc-draft-btn')],
  ['bindUploadEvents removed from init area', !c.includes('self.bindUploadEvents()')],
  ['new renderStep0 (基本信息)', c.includes('<h4>基本信息</h4>') && c.includes('实训描述（选填）')],
  ['new renderStep1 (实训时间)', c.includes('<h4>实训时间</h4>') && c.includes('tc-end_time')],
  ['new renderStep1 (提交材料)', c.includes('<h4>提交材料</h4>') && c.includes('toggleMaterial')],
  ['new renderStep2 (评价规则)', c.includes('<h4>评价规则</h4>') && c.includes('evaluation_template_id')],
  ['getAutoStatus method', c.includes('getAutoStatus()')],
  ['getAutoStatusText method', c.includes('getAutoStatusText()')],
  ['toggleMaterial method', c.includes('toggleMaterial(value, checked)')],
  ['loadTemplates method', c.includes('async loadTemplates()')],
  ['handleSaveDraft removed', !c.includes('handleSaveDraft')],
  ['renderPreview removed', !c.includes('renderPreview()')],
  ['updatePreview removed', !c.includes('updatePreview()')],
  ['bindPreviewEvents removed', !c.includes('bindPreviewEvents')],
  ['selectScoringMethod removed', !c.includes('selectScoringMethod')],
  ['toggleDimension removed', !c.includes('toggleDimension')],
  ['bindUploadEvents method removed', !c.includes('bindUploadEvents()')],
  ['_bindUploadBox removed', !c.includes('_bindUploadBox')],
  ['handleFileChange removed', !c.includes('handleFileChange')],
  ['pendingFile in training/create data removed', !c.includes('pendingFile')],
  ['pendingCodeFile removed', !c.includes('pendingCodeFile')],
  ['collectPayload with new fields', c.includes('start_time: d.start_time') && c.includes('end_time: d.end_time') && c.includes('required_materials: d.required_materials')],
  ['handleSubmit updated', c.includes('status: self.getAutoStatus()')],
  ['no tc-section-icon in step0', !c.match(/tc-section-icon/)],
  ['no 📋 emoji in step0 headers', !c.includes('📋')],
  ['datetime-local inputs in step1', c.includes('datetime-local')],
];
checks.forEach(([label, result]) => {
  console.log(result ? '✅' : '❌', label);
});
