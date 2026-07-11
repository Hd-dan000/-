const fs = require('fs');
const c = fs.readFileSync('F:\\xiangmu\\training-evaluation-system\\frontend\\app.js', 'utf8');
console.log('File size:', c.length);
const lines = c.split('\r\n');
console.log('Total lines:', lines.length);
const idx = lines.findIndex(l => l.includes("'training/create'"));
console.log("training/create at line:", idx + 1);
