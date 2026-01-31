const fs = require('fs');

const input = JSON.parse(fs.readFileSync('effortless-rulebook.json', 'utf8'));

for (const key in input) {
  if (input[key] && typeof input[key] === 'object' && Array.isArray(input[key].data)) {
    input[key].data = input[key].data.slice(0, 3);
  }
}

fs.writeFileSync('effortless-rulebook-minified.json', JSON.stringify(input, null, 2));
console.log('Done! Created effortless-rulebook-minified.json');
