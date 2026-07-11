const fs = require('fs');
const content = fs.readFileSync('F:\\xiangmu\\training-evaluation-system\\frontend\\app.js', 'utf8');

// Find the training/create view section
const startMarker = "'training/create': {";
const startIdx = content.indexOf(startMarker);

// Old field names to check
const oldFields = ['deadline', 'start_date', 'active_status', 'subtitle', 'allow_late', 'allow_late_submission', 'dimensions', 'customDimensions', 'document_url', 'code_standard', 'pendingFile', 'pendingCodeFile', 'updatePreview', 'renderPreview', 'bindPreviewEvents', 'selectScoringMethod', 'toggleDimension', 'bindUploadEvents', '_bindUploadBox', 'handleFileChange', 'handleSaveDraft', 'collectPayload'];

// Extract the training/create section
const endMarker = '\n};\n\nfunction updateMessageBadge';
const endIdx = content.indexOf(endMarker, startIdx);
const section = content.substring(startIdx, endIdx);

let totalIssues = 0;
for (const field of oldFields) {
    const regex = new RegExp(field, 'g');
    const matches = section.match(regex);
    if (matches) {
        console.log(field + ': ' + matches.length + ' references');
        totalIssues += matches.length;
    }
}
console.log('Total old field references in training/create: ' + totalIssues);

// Also check the full file for old field references outside training/create
console.log('\n--- Full file check ---');
for (const field of oldFields) {
    const regex = new RegExp('\\b' + field + '\\b', 'g');
    const matches = content.match(regex);
    if (matches) {
        console.log(field + ': ' + matches.length + ' total references in file');
    }
}
