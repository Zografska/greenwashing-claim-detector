from bs4 import BeautifulSoup
import re
import json

with open('./UCPD.html', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f, 'html.parser')

def clean(text):
    return re.sub(r'\s+', ' ', text).strip()

chunks = []

# --- 1. New definitions from Art 1, section 1b (letters o-t) ---
# These are the greenwashing-specific new terms added to UCPD Art 2
art1 = soup.find(id='art_1')
art1_text = clean(art1.get_text())

# Extract the definitions block (letters o onwards = greenwashing terms)
# Find all lettered items in art_1
new_defs = {}
letter_pattern = re.compile(r'«([a-z]\w*)\)\s+"([^"]+)":([^«»]+)', re.DOTALL)

# simpler: just grab the whole definitions insertion as one chunk
# find the table row with "b)" which contains the new letters o-t
tables = art1.find_all('table')
for tbl in tables:
    cells = tbl.find_all('td')
    if len(cells) >= 2:
        label = clean(cells[0].get_text())
        content = clean(cells[1].get_text())
        if label == 'b)' and 'asserzione ambientale' in content:
            chunks.append({
                "id": "ECGT_Art1_NuoveDefinizioni",
                "title": "ECGT Art. 1 – Nuove definizioni (asserzione ambientale, marchio di sostenibilità, sistema di certificazione)",
                "source": "art_1",
                "text": f"ECGT Articolo 1 – Nuove definizioni inserite nella direttiva 2005/29/CE: {content}"
            })
            break

# --- 2. Annex items – new blacklist entries ---
print("Processing Annex I items...")
anx = soup.find(id='anx_1')

# The annex has outer tables (numbered 1-4) each inserting one or more inner items
# Inner items have labels like "2 bis)", "4 bis)", etc.
# We want each inner item as its own chunk

def get_inner_items(container):
    items = []
    for tbl in container.find_all('table', recursive=True):
        rows = tbl.find_all('tr', recursive=False)
        for row in rows:
            cells = row.find_all('td', recursive=False)
            if len(cells) < 2:
                continue
            label = clean(cells[0].get_text())
            content = clean(cells[1].get_text())
            # match labels like "2 bis)", "4 bis)", "4 ter)", "10 bis)", "23 quinquies)" etc.
            if re.match(r'^\d+\s+\w+\)$', label) or re.match(r'^\d+\s+\w+\s+\w+\)$', label):
                item_id = label.rstrip(')').replace(' ', '_')
                items.append((label, content, item_id))
    return items

inner = get_inner_items(anx)
print(f"Found {len(inner)} inner items in Annex I.")
for label, content, item_id in inner:
    # strip trailing footnote markers and quotes
    content = content.strip('»').strip('«').strip(';').strip()
    chunks.append({
        "id": f"ECGT_AnnexI_{item_id}",
        "title": f"ECGT Allegato – nuovo punto {label} (inserito in Allegato I UCPD)",
        "source": "anx_1",
        "text": f"ECGT Allegato I – punto {label}: {content}"
    })

print(f"Total chunks: {len(chunks)}")
for c in chunks:
    print(c['id'])
    print(c['text'][:200])
    print()

with open('ecgt_chunks.json', 'w', encoding='utf-8') as f:
    json.dump(chunks, f, ensure_ascii=False, indent=2)
