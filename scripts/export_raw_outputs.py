import shutil, json
from pathlib import Path

# Copy raw outputs
shutil.copy('data/phase2-run.json', 'raw_outputs/full_corpus_discovery_run.json')
shutil.copy('data/editorial-shortlist.json', 'raw_outputs/editorial_ranked_promos.json')

# Create a human-readable text summary of the ranked promos
data = json.loads(Path('raw_outputs/editorial_ranked_promos.json').read_text(encoding='utf-8'))
lines = ['KUKU MICRODRAMA PROMO SELECTION - RANKED PROMOS (PROBLEM 1)', '='*65, '']
lines.append('Corpus: 50 Episodes, 100 Scenes, 3,727 Entries')
lines.append('Total Valid Continuous Candidates Generated: 23,602')
lines.append('Interior Candidates: 98.7% (not clustered at episode ends)')
lines.append('')
lines.append('TOP RANKED PROMO RECOMMENDATIONS TO POST FIRST:')
lines.append('='*65)
for item in data.get('shortlist', []):
    lines.append(f"RANK #{item['rank']}: Episode {item['episode']} | {item['start_text']} -> {item['end_text']} ({item['duration_text']})")
    lines.append(f"  * Hook (<=3s): {item['hook_quote']}")
    lines.append(f"  * Cliffhanger: {item['cliffhanger_text']}")
    lines.append(f"  * Unresolved Question: {item['unresolved_question']}")
    lines.append(f"  * Why it works: {item['why_it_works']}")
    lines.append(f"  * Standalone clarity: {item['standalone_clarity']}")
    lines.append('-'*65)

Path('raw_outputs/ranked_promos_summary.txt').write_text('\n'.join(lines), encoding='utf-8')
print('raw_outputs directory populated successfully!')
