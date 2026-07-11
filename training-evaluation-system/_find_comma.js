const fs = require('fs');
const c = fs.readFileSync('F:\\xiangmu\\training-evaluation-system\\frontend\\app.js', 'utf8');
// Find all occurrences of },,
const idx1 = c.indexOf('},,');
while (idx1 !== -1) {
    console.log('Found },, at index:', idx1);
    console.log('Context:', c.substring(idx1 - 30, idx1 + 30));
    const nextIdx = c.indexOf('},,', idx1 + 3);
    if (nextIdx === idx1) break;
    idx1 = nextIdx;
}
