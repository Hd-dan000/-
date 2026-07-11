const fs = require('fs');
const c = fs.readFileSync('F:\\xiangmu\\training-evaluation-system\\frontend\\app.js', 'utf8');
const lines = c.split('\r\n');

// Check updatePreview
console.log('=== updatePreview occurrences ===');
lines.forEach((l, i) => { if (l.includes('updatePreview')) console.log(`Line ${i+1}: ${l.trim().substring(0, 80)}`); });

// Check pendingFile in training/create context
console.log('\n=== pendingFile occurrences ===');
lines.forEach((l, i) => { if (l.includes('pendingFile')) console.log(`Line ${i+1}: ${l.trim().substring(0, 80)}`); });

// Check 📋 occurrences
console.log('\n=== 📋 occurrences ===');
lines.forEach((l, i) => { if (l.includes('📋')) console.log(`Line ${i+1}: ${l.trim().substring(0, 80)}`); });
