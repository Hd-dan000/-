const fs = require('fs');
const c = fs.readFileSync('F:\\xiangmu\\training-evaluation-system\\frontend\\app.js', 'utf8');
const lines = c.split('\r\n');
for (let i = 3800; i < lines.length; i++) {
    if (lines[i].includes('validateStep')) {
        console.log(`Line ${i+1}: ${lines[i].trim().substring(0, 80)}`);
    }
}
