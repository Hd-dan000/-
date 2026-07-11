const fs = require('fs');
const filePath = 'F:\\xiangmu\\training-evaluation-system\\frontend\\app.js';
let content = fs.readFileSync(filePath, 'utf8');

// Find the extra }, near syncForm
const sfIdx = content.indexOf('syncForm(field, value, el)');
console.log('syncForm at:', sfIdx);
console.log('150 chars before syncForm:');
console.log(content.substring(sfIdx - 150, sfIdx));
