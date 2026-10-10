08/09/2026, 22:59 

MSR 2027 - Mining Challenge - MSR 2027 

MSR 2027 

 () /  () / 

# Mining Challenge 

Call for Mining Challenge Papers Call for Mining Challenge Proposals 

## Call for Mining Challenge Papers 

This year the MSR Mining Challenge features two community datasets, both capturing new natural-language artefacts that AI coding agents produce and consume. Participants may work with either dataset, or combine both in a single submission: **GitSkills** , a dataset of agent skills, and **SpecMine** , a corpus of spec-driven development artefacts. Each dataset is introduced below with its own research directions; the submission, open-science, award, and logistics guidance that follows applies to both. 

**GitSkills** dataset preprint available here (https://arxiv.org/abs/2608.10906) 

**SpecMine** dataset preprint available here (https://arxiv.org/abs/2608.25202) 

#### **_GitSkills_** 

Agent skills are a new software artefact used by AI coding agents. An agent skill is a folder containing a `SKILL.md` file with instructions for a language-model agent and, optionally, scripts and reference files; the agent loads the skill when it judges that a task matches the skill description. Anthropic introduced the format in October 2025 as an open specification. Nine months later, millions of skill files were present in public GitHub repositories. Skills differ from the artefacts commonly mined in software engineering: their content is mainly written in natural language, selection occurs probabilistically at run time, and no compiler or type checker verifies whether the appropriate skill was selected. The format also has no central registry or package manager, allowing skills to spread through direct copying between repositories. How developers write, reuse, and maintain skills is therefore an empirical question, and no existing dataset had recorded this population before now. 

This year’s MSR Mining Challenge invites the global research community to explore novel research questions and present their insights using **GitSkills** , the first large-scale, openly available dataset of agent skills mined from GitHub repositories: 

- **Scale** : 3,797,117 `SKILL.md` file occurrences, grouped into 1,877,981 distinct contents **Breadth** : 282,200 repositories owned by 195,841 accounts, collected in July 2026 

- **Depth** : 7,264,865 bundled files (scripts and reference material) alongside representative skills, and 458,548 sampled commit histories with anonymized first- and last-commit author accounts 

#### **_SpecMine_** 

Spec-Driven Development (SDD) is a fast-emerging practice in which a structured natural- language specification, written by a developer or drafted by an AI tool and then curated by the developer, drives an AI coding agent’s implementation. A wave of tooling (GitHub Spec Kit, OpenSpec, AWS Kiro, and dozens of others) appeared in 2025, yet the specifications these tools produce had never been studied at scale. Specs differ from the source code the SE community usually mines: they are written mainly in natural language, they are becoming the primary artefact a developer writes and reviews, and how a spec turns into code is not directly observable. How developers write, structure, and implement specs is therefore an empirical question, and no existing dataset had recorded this population before now. 

https://2027.msrconf.org/track/msr-2027-mining-challenge#Call-for-Mining-Challenge-Papers 

1/8 

08/09/2026, 22:59 

MSR 2027 - Mining Challenge - MSR 2027 

This year’s MSR Mining Challenge invites the global research community to explore this practice using SpecMine, the first large-scale, openly available corpus of spec-driven development artefacts mined from GitHub repositories: 

- **Scale** : 470,795 ‘spec.md‘/‘specs.md‘ files across 73,030 repositories, attributed to 17 named SDD tools, plus a separate Kiro census of 98,574 ‘requirements‘/‘design‘/‘tasks‘ artefacts across 12,910 repositories **Breadth** : 18 SDD tool families, collected July 2026, with the full GitHub repository object (stars, license, language, topics, timestamps) recorded on every file 

- **Depth** : full commit history (780,335 commits) and 39 parsed structural features per spec; a curated layer of 5,992 spec-touching pull requests across 581 repositories with their complete change-sets; and a census-wide traceability index of 2,421,323 typed spec-to-code references 

### Challenges 

###### **_GitSkills_** 

The GitSkills dataset opens up rich and timely research directions around the adoption, reuse, structure, authorship, maintenance, and security of agent skills. Example research questions include (but are not limited to): 

###### **1) Adoption and linguistic evolution.** 

1. How quickly does the format spread, and which projects adopt it first, in terms of programming language, popularity, age, and activity? 

2. What do developers codify in skills, and in which contexts do skills appear, from operational projects to catalogs, templates, and demonstrations? A taxonomy of skill purposes does not yet exist. 

3. Do the linguistic properties of newly written skills change across monthly cohorts, in structure and phrasing as well as in topic coverage and semantic diversity? Convergence toward formulaic templates would indicate an emerging genre; shrinking diversity may also reflect rising machine authorship. 

4. How many skills do agents themselves create or maintain, and in which natural languages are skills written? A skill is read by a multilingual model, so a developer may state a procedure more precisely in their own language than in English. 

###### **2) Development of a shared format.** 

1. What proportion of skills use vendor-neutral rather than tool-specific locations, and how does this proportion change over time? 

2. Do skill texts address one named tool, or any agent that implements the specification? 

###### **3) Reuse without a package manager. Skills have no central registry; reuse happens by copying folders, and 50.5% of the collected files are verbatim copies.** 

1. How concentrated is reuse: a long tail of rarely copied contents, or a small set of widely copied templates? 

2. Through which mechanisms do skills move between repositories, such as direct addition, catalogs, or scaffolding tools? 

3. Do skill copies follow the genealogy patterns known from code clones, such as consistent and inconsistent propagation of changes? 

###### **4) Software metrics for natural-language instructions.** 

1. Which established metrics, such as size, churn, age, clone coverage, and readability, have meaningful equivalents for skills, and how do their distributions compare with those of source code? 

2. Can observable indicators of skill quality be defined and compared with proxies such as copy count and subsequent edits? 

3. Which properties of the description, the text the agent matches against when deciding whether to load the skill, are associated with reuse and maintenance? 

https://2027.msrconf.org/track/msr-2027-mining-challenge#Call-for-Mining-Challenge-Papers 

2/8 

08/09/2026, 22:59 

MSR 2027 - Mining Challenge - MSR 2027 

###### **5) Maintenance and trust. Skills can instruct agents to run commands, access external resources, and execute bundled scripts, and they are copied between repositories without formal review.** 

1. How often do skills become outdated relative to the projects and tools they describe? 

2. Do modified copies of widely reused skills introduce command execution or network access absent from the original, the analog of a supply-chain attack in an ecosystem without a registry? 

3. How often do skills bundle executable files, and how widely are these skills copied? 

We also suggest checking our preprint paper for more details on the collection pipeline and dataset construction: arXiv:2608.10906 (https://arxiv.org/abs/2608.10906) 

###### **_SpecMine_** 

The SpecMine corpus makes the specification a first-class unit of study, alongside the tool that produced it and the code it drives, opening directions around the adoption, anatomy, quality, implementation, and lifecycle of specifications. Example research questions include (but are not limited to): 

###### **1) Adoption and diffusion of spec-driven development.** 

1. Who adopts SDD (newcomers or experienced maintainers, which languages, domains, and team sizes), and how does adoption diffuse across ecosystems? 

2. How do the competing tool families grow, coexist, or displace one another, and do their document templates converge toward a shared structure? 

###### **2) Anatomy and quality of specifications.** 

1. What forms do specs take (EARS, Gherkin, user stories, free prose), and can a measurable notion of spec quality (completeness, testability, ambiguity, unfilled placeholders) be defined and validated? 

2. How much of a spec is reused template boilerplate versus genuinely project-specific content, and does that ratio differ by tool or author? 

###### **3) The spec-code relationship.** 

1. Where does the implementation of a spec live: co-changed with code in one pull request, in one or several later pull requests, before the spec is written, or never? Can these patterns be recognized at scale, and does the mix differ by tool, team size, or repository maturity? 

2. A spec names the files it expects to change. How often does that code actually exist, and does the gap between what a spec declares and what the repository contains widen as specs get longer? 

###### **4) Human-AI collaboration around specs.** 

1. Can human-authored and agent-generated specs be distinguished, and how is authorship of a single spec shared between developer and agent? 

2. Do higher-quality specs predict smoother downstream implementation (fewer follow-up fixes), and how does review differ when the artefact under discussion is a spec rather than code? 

###### **5) Lifecycle, evolution, and abandonment.** 

1. What are the churn and half-life of a spec, how often are specs abandoned mid-flight (open tasks that never close, placeholders never filled), and what predicts abandonment? 

2. Because every prior state is reconstructable from commit history, can spec-driven workflows be studied longitudinally without the data-leakage pitfalls of snapshot datasets? 

### How to Participate in the Challenge 

First, familiarize yourself with the datasets: 

###### **_GitSkills_** 

https://2027.msrconf.org/track/msr-2027-mining-challenge#Call-for-Mining-Challenge-Papers 

3/8 

08/09/2026, 22:59 

MSR 2027 - Mining Challenge - MSR 2027 

- The details about the GitSkills infrastructure and the data are provided in our preprint (https://arxiv.org/abs/2608.10906). 

- The full dataset, as a single self-contained SQLite file, can be downloaded from Zenodo (https://doi.org/10.5281/zenodo.21875637) (DOI: 10.5281/zenodo.21875637). 

- A Parquet mirror, partitioned by table, is available on Hugging Face (https://huggingface.co/datasets/mvaccargiu/gitskills). A sample of the dataset is available on GitHub at this link 

(https://github.com/giuseppedestefanis/gitskills-sample). 

###### **_SpecMine_** 

- The construction pipeline, schema, and data dictionary are described in our preprint (https://arxiv.org/abs/2608.25202). The full dataset is released on Zenodo (https://doi.org/10.5281/zenodo.22102779) (DOI: 

- 10.5281/zenodo.22102779) as a MySQL dump plus CSV/Parquet exports and a JSONL of spec contents. 

- A per-table Parquet mirror is available on Hugging Face 

- (https://huggingface.co/datasets/ShyAgarwal/specmine) 

- A GitHub mirror carries the schema, loader scripts, an example Jupyter/Colab notebook, and a curated 500-repository sample at this link (http://github.com/shyamagarwal13/specmine-official). 

Use the dataset to answer your research questions, and report your findings in a challenge paper that you submit to our challenge. If your paper is accepted, present your results at MSR 2027 in Dublin, Ireland! 

### Submission 

**IMPORTANT** : Accepted papers in the Mining Challenge will be published as Short Papers in IEEE Xplore. 

A challenge paper should describe the results of your work by providing an introduction to the problem you address and why it is worth studying, the version of the dataset you used, the approach and tools you used, your results and their implications, and conclusions. Make sure your report highlights the contributions and the importance of your work. See also our open science policy regarding the publication of software and additional data you used for the challenge. 

To ensure clarity and consistency in research submissions: 

- When detailing methodologies or presenting findings, authors should specify which snapshot/version of the SpecMine or GitSkills dataset was utilized (e.g., the dataset released July 2026 / version number, archived on Zenodo). 

- Given the possibility of future dataset updates, authors are reminded to be precise in their dataset references. This will help maintain transparency and ensure consistent replication of results. 

All submissions must conform to the IEEE conference proceedings template, specified in the IEEE Conference Proceedings Formatting Guidelines (title in 24pt font and full text in 10pt type, LaTeX users must use `\documentclass[10pt,conference]{IEEEtran}` without including the compsoc or compsocconf options). 

Submissions to the Challenge Track can be made via the submission site by the submission deadline. We encourage authors to upload their paper info early (the PDF can be submitted later) to properly enter conflicts for anonymous reviewing. All submissions must adhere to the following requirements: 

- Submissions must not exceed the page limit ( **4 pages** plus 1 additional page of references). The page limit is strict, and it will not be possible to purchase additional pages at any point in the process (including after acceptance). 

- Submissions must strictly conform to the IEEE formatting instructions. Alterations of spacing, font size, and other changes that deviate from the instructions may result in desk rejection without further review. Submissions must not reveal the authors’ identities. The authors must make every effort to honor the double-anonymous review process. In particular, the authors’ names must be omitted from the 

https://2027.msrconf.org/track/msr-2027-mining-challenge#Call-for-Mining-Challenge-Papers 

4/8 

08/09/2026, 22:59 

MSR 2027 - Mining Challenge - MSR 2027 

submission and references to their prior work should be in the third person. 

- Submissions should consider the ethical implications of the research conducted within a separate section before the conclusion. 

- The official publication date is the date the proceedings are made available in IEEE Xplore. This date may be up to two weeks prior to the first day of MSR 2027. The official publication date affects the deadline for any patent filings related to published work. 

Purchases of additional pages in the proceedings are not allowed. 

Any submission that does not comply with these requirements is likely to be desk rejected by the PC Chairs without further review. In addition, by submitting to the MSR Challenge Track, the authors acknowledge that they are aware of and agree to be bound by the following policies: 

- The ACM Policy and Procedures on Plagiarism and the IEEE Plagiarism FAQ. In particular, papers submitted to MSR 2027 must not have been published elsewhere and must not be under review or submitted for review elsewhere whilst under consideration for MSR 2027. Contravention of this concurrent submission policy will be deemed a serious breach of scientific ethics, and appropriate action will be taken in all such cases (including immediate rejection and reporting of the incident to ACM/IEEE). The authorship policy of the ACM and the authorship policy of the IEEE. 

Upon notification of acceptance, all authors of accepted papers will be asked to fill a copyright form and will receive further instructions for preparing the camera-ready version of their papers. At least one author of each paper is expected to register and present the paper at the MSR 2027 conference. All accepted contributions will be published in the electronic proceedings of the conference. 

The GitSkills dataset can be _cited_ as: 

```
@inproceedings{gitskills2027,
  author    = {Destefanis, Giuseppe and Graziotin, Daniel and Vaccargiu, Matteo and Ortu, Mar
co},
```

```
  title     = {GitSkills: A Dataset of Agent Skills on GitHub},
  year      = {2027},
  isbn      = {},
  publisher = {IEEE},
  address   = {Piscataway, NJ, USA},
  url       = {https://arxiv.org/abs/2608.10906},
  doi       = {https://doi.org/10.48550/arXiv.2608.10906},
```

```
  booktitle = {Proceedings of the 24th International Conference on Mining Software Repositori
es},
```

```
  pages     = {To Appear},
  numpages  = {},
  location  = {Dublin, Ireland},
  series    = {MSR '27}
}
```

The SpecMine dataset can be cited as: 

https://2027.msrconf.org/track/msr-2027-mining-challenge#Call-for-Mining-Challenge-Papers 

5/8 

08/09/2026, 22:59 

MSR 2027 - Mining Challenge - MSR 2027 

```
@inproceedings{specmine2027,
  author    = {Agarwal, Shyam and Singhal, Anmol and Breaux, Travis and Vasilescu, Bogdan},
  title     = {SpecMine: A Large-Scale Corpus of Spec-Driven Development Artifacts},
  year      = {2027},
  isbn      = {},
  publisher = {IEEE},
  address   = {Piscataway, NJ, USA},
  url       = {https://arxiv.org/abs/2608.25202},
  doi       = {https://doi.org/10.48550/arXiv.2608.25202},
  booktitle = {Proceedings of the 24th International Conference on Mining Software Repositori
es},
  pages     = {To Appear},
  numpages  = {},
  location  = {Dublin, Ireland},
  series    = {MSR '27}
}
```

### Submission Site 

Papers must be submitted through HotCRP: https://msr2027-challenge.hotcrp.com/ (https://msr2027challenge.hotcrp.com/) 

###### **Important Dates (AoE)** 

- Abstract Deadline: Dec 18, 2026 

- Paper Deadline: Dec 23, 2026 Author Notification: Jan 19, 2027 

- Camera Ready Deadline: Jan 26, 2027 

### Open Science Policy 

Openness in science is key to fostering progress via transparency, reproducibility and replicability. Our steering principle is that all research output should be accessible to the public and that empirical studies should be reproducible. In particular, we actively support the adoption of open data and open source principles. To increase reproducibility and replicability, we encourage all contributing authors to disclose: 

- the source code of the software they used to retrieve and analyze the data 

- the (anonymized and curated) empirical data they retrieved in addition to the GitSkills dataset a document with instructions for other researchers describing how to reproduce or replicate the results 

Already upon submission, authors can privately share their anonymized data and software on archives such as Zenodo or Figshare. Zenodo accepts up to 50GB per dataset (more upon request) — the full GitSkills SQLite file itself is 44GB and is archived there. There is no need to use Dropbox or Google Drive. After acceptance, data and software should be made public so that they receive a DOI and become citable. Zenodo and Figshare accounts can easily be linked with GitHub repositories to automatically archive software releases. 

We recognize that anonymizing artifacts such as source code is more difficult than preserving anonymity in a paper. We ask authors to take a best effort approach to not reveal their identities. We will also ask reviewers to avoid trying to identify authors by looking at commit histories and other such information that is not easily anonymized. Authors wanting to share GitHub repositories may want to look into using https://anonymous.4open.science/ (https://anonymous.4open.science/) which is an open source tool that helps you to quickly double-blind your repository. 

https://2027.msrconf.org/track/msr-2027-mining-challenge#Call-for-Mining-Challenge-Papers 

6/8 

08/09/2026, 22:59 

MSR 2027 - Mining Challenge - MSR 2027 

We encourage authors to self-archive pre- and postprints of their papers in open, preserved repositories such as arXiv.org. This is legal and allowed by all major publishers including ACM and IEEE and it lets anybody in the world reach your paper. Note that you are usually not allowed to self-archive the PDF of the published article (that is, the publisher proof or the Digital Library version). Please note that the success of the open science initiative depends on the willingness (and possibilities) of authors to disclose their data and that all submissions will undergo the same review process independent of whether or not they disclose their analysis code or data. We encourage authors who cannot disclose industrial or otherwise non-public data, for instance due to non-disclosure agreements, to provide an explicit (short) statement in the paper. 

### Best Mining Challenge Paper Award 

As mentioned above, all submissions will undergo the same review process independent of whether or not they disclose their analysis code or data. However, only accepted papers for which code and data are available on preserved archives, as described in the open science policy, will be considered by the program committee for the best mining challenge paper award. 

### Best Student Presentation Award 

There will be a public voting during the conference to select the best mining challenge presentation. This award often goes to authors of compelling work who present an engaging story to the audience. Only students can compete for this award. 

### FAQ 

###### **Q1. Can we augment GitSkills/SpecMine with additional data for the challenge?** 

Yes. You are welcome and encouraged to “bring your own data” (BYOD) by integrating the GitSkills dataset with information from other public, readily available sources (e.g., GitHub REST/GraphQL APIs, repository clones, ecosystem registries). Please document all sources and extraction steps. We urge participants to thoroughly consider the ethical implications of merging the GitSkills dataset with other sources. The share or use of personally identifiable information (PII) is strictly prohibited. 

###### **Q2. Where is the data dictionary/schema documentation?** 

Table I of the GitSkills paper (arXiv:2608.10906 (https://arxiv.org/abs/2608.10906)) summarizes all four tables ( `artifacts` , `repos` , `artifact_siblings` , `mining_runs` ). A more detailed column-by-column description is also available in the dataset card on Hugging Face (https://huggingface.co/datasets/mvaccargiu/gitskills). 

For SpecMine, an entity-relationship diagram and a condensed data dictionary of the core tables appear in the SpecMine preprint, and a data dictionary of the released tables ships as `DATA_DICTIONARY.md` in the GitHub (http://github.com/shyamagarwal13/specmine-official) mirror. A per-table Parquet mirror is also on Hugging Face (https://huggingface.co/datasets/ShyAgarwal/specmine). 

|Important Dates|AoE (UTC-12h)<br>|
|---|---|
|Fri 18 Dec 2026|**new**|
|Abstract Deadline||
|Wed 23 Dec 2026|**new**|
|Paper Deadline||
|Tue 19 Jan 2027|**new**|
|Author Notification||



https://2027.msrconf.org/track/msr-2027-mining-challenge#Call-for-Mining-Challenge-Papers 

7/8 

08/09/2026, 22:59 

MSR 2027 - Mining Challenge - MSR 2027 

Tue 26 Jan 2027 Camera Ready Deadline 

**new** 

Fri 7 Aug 2026 Notification Mon 3 Aug 2026 Deadline for Proposals 

##### Submission Link 

 https://msr2027-challenge.hotcrp.com/ (https://msr2027-challenge.hotcrp.com/) 

https://2027.msrconf.org/track/msr-2027-mining-challenge#Call-for-Mining-Challenge-Papers 

8/8 

