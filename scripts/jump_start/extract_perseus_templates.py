import sqlite3
import os
import requests
import zipfile
import json
import io

def download_and_extract_perseus(db_path, limit=5):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT n.id as node_id, n.title, f.local_file_id, l.extension 
        FROM content_contentnode n
        JOIN content_file f ON n.id = f.contentnode_id
        JOIN content_localfile l ON f.local_file_id = l.id
        WHERE n.kind = 'exercise' AND l.extension = 'perseus'
        LIMIT ?
    ''', (limit,))
    
    os.makedirs("output/templates", exist_ok=True)
    
    results = []
    
    for row in cursor.fetchall():
        node_id = row['node_id']
        title = row['title']
        file_id = row['local_file_id']
        ext = row['extension']
        
        # Kolibri storage URL
        url = f"https://studio.learningequality.org/content/storage/{file_id[0]}/{file_id[1]}/{file_id}.{ext}"
        print(f"Downloading {title} from {url}...")
        
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                    # Look for assessment json files in the zip
                    json_files = [name for name in z.namelist() if name.endswith('.json')]
                    templates = []
                    for jf in json_files:
                        with z.open(jf) as f:
                            data = json.load(f)
                            templates.append(data)
                    
                    output_file = f"output/templates/{node_id}.json"
                    with open(output_file, 'w', encoding='utf-8') as out_f:
                        json.dump({
                            "node_id": node_id,
                            "title": title,
                            "templates": templates
                        }, out_f, indent=2)
                    
                    print(f"Saved {len(templates)} templates to {output_file}")
                    results.append(node_id)
            else:
                print(f"Failed to download {url}: {resp.status_code}")
        except Exception as e:
            print(f"Error processing {node_id}: {e}")
            
    print(f"Processed {len(results)} exercises successfully.")

if __name__ == '__main__':
    download_and_extract_perseus('data/khan_academy.sqlite3', limit=2)
