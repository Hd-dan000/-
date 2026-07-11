const fs = require('fs');
const c = fs.readFileSync('F:\\xiangmu\\training-evaluation-system\\frontend\\app.js', 'utf8');
const lines = c.split('\r\n');
// Find collectPayload in the training/create view section (after line 3700)
for (let i = 3700; i < lines.length; i++) {
    if (lines[i].includes('collectPayload')) {
        console.log(`Line ${i+1}: ${lines[i].trim().substring(0, 80)}`);
    }
    if (lines[i].includes('handleSubmit')) {
        console.log(`Line ${i+1}: ${lines[i].trim().substring(0, 80)}`);
    }
    if (lines[i].includes('getAutoStatus')) {
        console.log(`Line ${i+1}: ${lines[i].trim().substring(0, 80)}`);
    }
}
