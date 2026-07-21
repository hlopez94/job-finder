import json

data = json.load(open('output/2026-07-21/results.json'))
jobs = data.get('top_results', [])

print('Top 10 jobs:')
for j in jobs:
    print(f'  {j.get("rank")}: {j.get("title")[:50]} | {j.get("location")}')