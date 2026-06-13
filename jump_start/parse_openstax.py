import os
import json
from bs4 import BeautifulSoup

def parse_openstax_github_directory(input_dir, output_path):
    print(f"Parsing OpenStax XHTML files from {input_dir}...")
    
    extracted_data = []
    file_count = 0

    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.cnxml'):
                file_path = os.path.join(root, file)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f.read(), 'lxml-xml')
                    
                    title_el = soup.find('title')
                    title = title_el.text.strip() if title_el else file
                    
                    description = ""
                    # CNXML often uses <section id="summary"> or <abstract>
                    summary_section = soup.find('abstract') or soup.find(id="summary")
                    if summary_section:
                        description = " ".join([p.text.strip() for p in summary_section.find_all('para')])
                    
                    problems = []
                    # CNXML uses <exercise> containing <problem> and <solution>
                    exercises = soup.find_all("exercise")
                    
                    # If we can't find data-type="exercise", try looking for problem blocks
                    if not exercises:
                        exercises = soup.find_all(attrs={"class": "exercise"})
                        
                    for ex in exercises[:15]: # Limit to 15 problems per node for size
                        question_el = ex.find("problem")
                        answer_el = ex.find("solution")
                        
                        q_text = question_el.text.strip() if question_el else ex.text.strip()
                        a_text = answer_el.text.strip() if answer_el else "Answer not provided"
                        
                        if q_text:
                            problems.append({
                                "question": q_text,
                                "answer": a_text,
                                "source": f"OpenStax Prealgebra (GitHub)"
                            })

                    if description or problems:
                        extracted_data.append({
                            "title": title,
                            "url_slug": file,
                            "description": description,
                            "example_problems": problems
                        })
                file_count += 1

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(extracted_data, f, indent=2)

    print(f"Extraction complete! Scanned {file_count} XHTML files.")
    print(f"Extracted data for {len(extracted_data)} sections containing problems/descriptions.")
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    input_directory = "data/openstax/osbooks-prealgebra-bundle"
    output_file = "output/openstax_bank.json"
    
    if os.path.exists(input_directory):
        parse_openstax_github_directory(input_directory, output_file)
    else:
        print(f"Directory {input_directory} not found. Please run fetch_openstax.py first.")
