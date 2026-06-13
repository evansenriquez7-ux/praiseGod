# GED Knowledge Graph: Jump Start Kit

This directory contains everything you need to extract CCSS-aligned taxonomy, node descriptions, and AI practice problem templates (via Khan Academy's Perseus engine) **without** needing to install the Kolibri desktop app or download terabytes of video files.

## What's Included

### Data 
* `data/khan_academy.sqlite3`: The lightweight (130MB) offline Kolibri database. This contains the structural blueprint of the Khan Academy curriculum, including topic hierarchies and rich descriptions. 
* `ged_knowledge_graph.json` & `nodes.json`: The compiled JSON representations of the knowledge graph and its dependencies.
* `openstax_bank.json`: An aggregated bank of text-based questions and descriptions scraped from OpenStax textbooks.

### Scripts
* `extract_kolibri_skeleton.py`: Reads the SQLite database to build the baseline taxonomy graph (`nodes.json` and `edges.json`), skipping the heavy content files.
* `extract_perseus_templates.py`: Uses the SQLite database to locate exercise nodes, then queries the live Kolibri Studio API to selectively download **only** the lightweight `.perseus` problem templates (JSON blobs) directly into an `output/templates/` folder.
* `align_perseus_templates.py`: Modifies your `ged_knowledge_graph.json` to insert lightweight pointers to the downloaded templates (e.g., `"perseus_template_file": "templates/node_id.json"`).
* `fetch_openstax.py` & `parse_openstax.py`: Scripts used to fetch and parse OpenStax XML/HTML textbook content for supplementary ELA/Math practice problems.

---

## Setup Instructions

Because everything relies on the included offline SQLite database and lightweight API calls, the setup is incredibly simple. You do not need to install Kolibri.

### 1. Prerequisites
You need **Python 3.8+** installed on your system.

### 2. Install Dependencies
There is only one external dependency (`requests` for making API calls to Kolibri Studio and OpenStax). Install it via pip:
```bash
pip install -r requirements.txt
```

---

## Usage Pipeline

If you are starting fresh or want to re-run the extraction:

### Step 1: Extract the Skeleton
Run this to parse the SQLite database and generate the structural nodes and hierarchy.
```bash
python extract_kolibri_skeleton.py
```
*(This outputs `nodes.json` and `edges.json` in the `output/` directory)*

### Step 2: Download the Practice Problems
Run this to find all "exercise" nodes and download their `.perseus` JSON blueprints from the cloud.
```bash
python extract_perseus_templates.py
```
*(This extracts the templates into `output/templates/`)*
> **Note:** By default, the script might have a `limit` set for testing. Open the script and remove `limit=2` in the `download_and_extract_perseus` function call if you want to extract all nodes!

### Step 3: Align Templates to the Graph
Run this to attach the newly downloaded template references to your master graph file.
```bash
python align_perseus_templates.py
```

You are now ready to feed these highly-structured JSON templates to your AI generator!
