---
license: odc-by
language:
- en
tags:
- education
- math
size_categories:
- n<1K
---

# Dataset Card for Achieve the Core

<!-- Provide a quick summary of the dataset. -->

This repository includes Common Core math standards, their descriptions, and metadata obtained from [Achieve the Core](https://github.com/achievethecore/atc-coherence-map/).

Example of a math standard: 

```
{
  "id": "K.CC.B.4",
  "description": "Understand the relationship between numbers and quantities; connect counting to cardinality.",
  "source": "Achieve the Core",
  "level": "Standard",
  "cluster_type": "major cluster",
  "aspects": [],
  "parent": "K.CC.B",
  "children": ["K.CC.B.4c", "K.CC.B.4b", "K.CC.B.4a"],
  "connections": {"progress to": ["1.OA.C.5", "K.CC.B.5"], "progress from": [], "related": ["K.CC.A.2", "K.CC.C.6", "K.CC.A.1"]},
  "modeling": false
}
```

See [MathFish](https://huggingface.co/datasets/allenai/mathfish) for more details on uses of this data.

This data can be used to evaluate language models' abilities to assess whether math problems enable students to learn specific skills/concepts. Code to support this can be found in this [Github repository](https://github.com/allenai/mathfish/tree/main).

## Dataset Details

### Dataset Description

<!-- Provide a longer summary of what this dataset is. -->

- **Curated by:** Lucy Li, Tal August, Rose E Wang, Luca Soldaini, Courtney Allison, Kyle Lo
- **Funded by:** The Gates Foundation
- **Language(s) (NLP):** English
- **License:** ODC-By 1.0

### Dataset Sources

<!-- Provide the basic links for the dataset. -->

- **Repository:** [Achieve the Core's Github](https://github.com/achievethecore/atc-coherence-map/)
- **Website:** [Achieve the Core's Coherence Map](https://tools.achievethecore.org/coherence-map/)


## Dataset Structure

<!-- This section provides a description of the dataset fields, and additional information about the dataset structure such as criteria used to create the splits, relationships between data points, etc. -->

This repository includes two key files: `domain_groups.json` and `standards.jsonl`.

We created `domain_groups.json` because the "domains" we evaluate with for our tagging task do not have a one-to-one mapping to K-8 domains and high school (HS) categories in Common Core State Standards (CCSS). Some HS categories are equivalent or similar to a domain in K-8, and some differences in K-8 domains are difficult to explain a brief description at the domain-level. Thus, a "domain" in our paper sometimes groups multiple actual CCSS domains/categories. We mostly retain the original CCSS K-8 domains and HS categories, but make exceptions for the following: we group OA (Operations & Algebraic Thinking), EE (Expressions & Equations), and A (HS Algebra) into Operations & Algebra, S (HS Statistics & Probability) and SP (K-8 Statistics & Probability) to \textit{Statistics & Probability}, and finally NS (K-8 The Number System) and N (HS Number and Quantity) to Number Systems and Quantity. Since CCSS and Achieve the Core do not provide brief descriptions of domains, we worked with a curriculum specialist to write domains' descriptions.

Within `standards.jsonl`, each line is a standard, sub-standard, cluster, domain, or grade level: 

```
{
  id: '', # e.g. 'K.OA.A.1'
  description: 'description of standard from achieve the core',
  source: 'Achieve the Core',
  level: '', # one of Grade, HS Category, Domain, Cluster, Standard, Sub-standard
  cluster_type: '', # e.g. major cluster, additional cluster, minor cluster
  aspects: [], # a list containing items such as "Application", "conceptual understanding", "Procedural Skill and Fluency"
  parent: '',
  children: [],
  connections: {''progress to': [], 'progress from': [], 'related': []} # standard-level Achieve the Core connections
  modeling: # True or False depending on whether the standard is a "modeling" standard
}
```

After downloading each file, you can load them: 

```
import json
with open('domain_groups.json', 'r') as infile:
    domain_groups = json.load(infile)
    print(domain_groups.keys()) # should print the keys of this dictionary

with open('standards.jsonl', 'r') as infile:
    for line in infile:
        this_standard = json.loads(line)
        print(this_standard['id']) # should print the ID of the row in this file
```

## Citation 

<!-- If there is a paper or blog post introducing the dataset, the APA and Bibtex information for that should go in this section. -->

```
@misc{lucy2024evaluatinglanguagemodelmath,
      title={Evaluating Language Model Math Reasoning via Grounding in Educational Curricula}, 
      author={Li Lucy and Tal August and Rose E. Wang and Luca Soldaini and Courtney Allison and Kyle Lo},
      year={2024},
      eprint={2408.04226},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2408.04226}, 
}
```

## Dataset Card Contact

kylel@allenai.org