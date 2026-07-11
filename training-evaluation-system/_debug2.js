const fs = require('fs');
const c = fs.readFileSync('F:\\xiangmu\\training-evaluation-system\\frontend\\app.js', 'utf8');
const lines = c.split('\r\n');
for (let i = 4080; i < 4100; i++) {
    console.log(`${i+1}: ${lines[i]}`);
}
