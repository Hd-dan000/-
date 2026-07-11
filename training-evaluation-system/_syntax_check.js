const fs = require('fs');
const c = fs.readFileSync('F:\\xiangmu\\training-evaluation-system\\frontend\\app.js', 'utf8');
const lines = c.split('\r\n');

// Check for obvious syntax issues in the training/create section
let inCreateView = false;
let braceBalance = 0;
let issues = [];
for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (line.includes("'training/create'")) inCreateView = true;
    if (inCreateView) {
        // Count braces
        for (const ch of line) {
            if (ch === '{') braceBalance++;
            if (ch === '}') braceBalance--;
        }
        // Check for double commas
        if (line.includes(',,')) {
            issues.push(`Line ${i+1}: double comma ,,`);
        }
    }
    // Exit when we hit the next view after training/create
    if (inCreateView && i > 3800 && line.match(/^\s+'[a-z]/) && !line.includes('training/create') && !line.includes('training') && !line.includes('evaluation')) {
        inCreateView = false;
    }
}

// Check last few lines for the view ending
const lastLines = lines.slice(lines.length - 10);
console.log('Last 10 lines:');
lastLines.forEach((l, i) => console.log(`${lines.length - 10 + i + 1}: ${l}`));

if (issues.length === 0) {
    console.log('\n✅ No syntax issues found in training/create section');
} else {
    console.log('\n❌ Found issues:');
    issues.forEach(i => console.log(i));
}

console.log('\nFile size:', c.length, 'bytes, Lines:', lines.length);
