import re

with open('app.js', 'r', encoding='utf-8') as f:
    content = f.read()

with open('new_report_block.js', 'r', encoding='utf-8') as f:
    new_block = f.read()

start = content.find('    report: {')
if start == -1:
    raise ValueError('report object start not found')

end_match = re.search(r'    },\n    llm: \{', content[start:])
if not end_match:
    raise ValueError('report object end not found')

end = start + end_match.start() + len('    },\n')

new_content = content[:start] + new_block + content[end:]

with open('app.js', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Replacement done.')
