# JTC's EVA sets Evalia's governance bar

> **Provenance.** Victor supplied this research report on 29 October 2026, and it is reproduced here as he supplied it. Claude has not re-checked its sources in this session. Its labels (Fact, Interpretation, Speculation, with confidence levels) are the report's own.
>
> **Note on positioning.** The report was written for an earlier positioning, in which Evalia is an independent service whose findings a Chartered Civil Engineer signs. Victor has since decided that Evalia is software that clients run themselves; see [`../02-architecture.md`](../02-architecture.md), sections 1 and 6.4. Where the two conflict, the later decisions prevail. [`../05-positioning.md`](../05-positioning.md) records how they were reconciled.
>
> **The EVA screenshot** (published by The Business Times, credited to JTC) shows a two-step flow, "Evaluation Criteria" then "Upload Documents". Its criteria are grouped as Track Record (relevant completed projects, completed projects, relevant ongoing projects, ongoing projects, construction-related awards), Project Performance (safety demerit points, ConSASS audited scores) and Project Proposal – Resources (management and technical staff, resource-loaded programme, plant and machinery, IDD and CDE personnel). The criterion "Relevant completed projects" is set by parameters: relevance keywords ("industrial building or commercial building or institutional building"), a start and end year (2018 to 2026), a minimum contract value (S$11,000,000), a minimum performance rating ("Satisfactory"), the minimum and maximum number of projects counted (0 and 5), the points per project (2.5), and whether the tenderer must have been main contractor. The screenshot is not stored in this repository.

## Executive summary

**What EVA is.** EVA (Evaluation Virtual Assistant) is an in-house generative-AI tool built by JTC Corporation, Singapore's industrial-estate statutory board. Evaluators upload construction tender submissions to it. It uses large language models to extract technical, contractual and performance-related details, map them against JTC's evaluation criteria and produce a first-pass score with its reasoning shown. Human evaluators keep full authority over scores and recommendations. As of April 2026 it handled quantitative criteria only ([Business Times feature](https://www.businesstimes.com.sg/events-awards/design-ai-tech-awards/design-ai-and-tech-awards/jtc-bids-goodbye-paper-heavy-world-construction-tenders); [Business Times awards article](https://www.businesstimes.com.sg/events-awards/design-ai-tech-awards/diverse-ai-solutions-clinch-top-honours-design-ai-and-tech-awards)).

**How strong the evidence is: weak to moderate.**
- Every substantive detail comes from one outlet, The Business Times (BT), and specifically from coverage of BT's own Design AI and Tech Awards (Daita).
- The primary article is a finalist profile, published online on 8 April 2026 at 06:00 SGT. The awards article and the print run followed on 15 April 2026.
- The profile reads as JTC's self-description, not independent reporting.
- No JTC press release, GovTech write-up, parliamentary answer or third-party assessment names EVA.
- JTC has published a baseline workload and a *projected* schedule saving. It has not published measured time savings, accuracy figures or the number of tenders processed.

**The three most important implications for Evalia.**
1. **Copy EVA's architecture, not its silence on governance.**
   - EVA's strongest design idea is a fixed sequence: context, then who is assessed, then a check that the criteria have been interpreted correctly, and only then the submissions. Its documented win is a check of claims against evidence.
   - EVA has published nothing on audit trails, retention or telling tenderers.
   - The 2026 US Trax case shows that undocumented AI influence is the real legal exposure. Evalia's moat is therefore the governance layer JTC has not described: citation-linked findings, retained records, and an engineer's accept/reject/modify log and signature.
2. **Sell findings, not scores, by default.**
   - Courts and regulators so far accept AI as "mere support" with human judgement: Italy's Council of State, UK PPN 017 and US practitioner advice all say so.
   - An independent service that returns sourced findings and clarification questions sits more safely inside that doctrine than one that returns scores.
   - EVA itself scores, but EVA is the owner's own tool, inside the owner's own accountability chain. Evalia would be an outsider.
3. **EVA proves owner appetite for AI-assisted evaluation, not demand for a third-party service.**
   - No evidence was found of any owner or lender buying independent AI-assisted bid review.
   - Singapore public owners are likely to get EVA, or a government-built successor, at no cost.
   - Evalia should use EVA as a credibility signal, target private owners, lenders and non-Singapore public owners, and test willingness to pay before building further.

**Correction to the earlier "AEC startup gap deep dive" report.** That report said, as fact, that "owners have begun to pay for independent, AI-assisted tender scrutiny" and cited JTC. That is wrong for JTC. EVA is an in-house, evaluator-operated tool, not an independent service that JTC buys. The Italian ruling of October 2025 that the earlier report cited does exist; see the resolution section below.

---

## Resolving the earlier report's discrepancies

### The Italian rulings: three decisions, not one

The earlier report cited a Council of State ruling of October 2025 via Bird & Bird. The new global notes could not find it and instead identified two other decisions. A re-check of the Bird & Bird page and an independent Italian legal digest settles the question. **All three rulings exist and are distinct.**

| Ruling | Date | What it concerns | Holding | Source |
|---|---|---|---|---|
| TAR Lazio, Sez. II, n. 4546 | 3 March 2025 | Consip cleaning-services tender, Lot 2 (Umbria). A rival challenged awardee Dussmann's proposal to use ChatGPT-4 for technical criteria. | AI use is not in itself an anomaly; the challenger's own ChatGPT queries were not sufficient evidence; discretionary scores are reviewable only for manifest illogicality. | [Giustizia Insieme](https://giustiziainsieme.it/print/articolo_pdf?id=3745) |
| Consiglio di Stato, Sez. IV, n. 4857 | 4 June 2025 | A contracting authority's software that compared tender-offer parameters. | The software is "mero supporto" (mere support), not an algorithmic administrative decision, so the algorithmic-decision principles of art. 30 d.lgs. 36/2023 do not apply; humans decide. | [Giustizia Insieme](https://giustiziainsieme.it/print/articolo_pdf?id=3745) |
| Consiglio di Stato, Sez. III, n. 8092 | 20 October 2025 | The winning bidder declared that it used "ChatGPT-4/OpenAI" to prepare parts of its technical bid; the third-ranked bidder appealed. | Appeal rejected. The score rested on a "multi-factor, consistent, and informed assessment" that cannot be questioned unless "manifestly illogical"; a feasibility challenge needs "specific and verifiable demonstrations". On the organisational-model criterion, the commission gave *higher* marks to bidders that had not planned to use AI. | [Bird & Bird](https://cm.twobirds.com/en/insights/2025/ai-in-tenders-a-tool,-not-a-free-pass--the-lesson-from-the-council-of-state); [Segretari comunali Vighenzi digest](https://www.segretaricomunalivighenzi.it/?p=65916) |

- **Fact (High):** The October 2025 ruling is Consiglio di Stato Sez. III n. 8092/2025. The Bird & Bird article is by Massimiliano Castriconi of the Rome office; the page shows no publication date ([Bird & Bird](https://cm.twobirds.com/en/insights/2025/ai-in-tenders-a-tool,-not-a-free-pass--the-lesson-from-the-council-of-state)). A second, independent Italian digest confirms the number and the facts ([Vighenzi](https://www.segretaricomunalivighenzi.it/?p=65916)).
- **Interpretation (Medium-Low):** The facts of 8092/2025 closely match TAR Lazio 4546/2025: a ChatGPT-4 declaration by the winner, a challenge by the third-ranked bidder, a multi-lot tender and the manifest-illogicality standard. It is probably the appeal of that case. Neither source fetched for this report names Consip or Dussmann, so the link is not confirmed.
- **Correction to the earlier report:**
  - The earlier report said bidders write proposals with LLMs, "a practice an Italian court upheld in October 2025". That overstates the ruling. The Council of State upheld the *award and the commission's discretionary scores*. It did not endorse AI-written bids. It noted that the commission scored non-AI bidders higher on one criterion, and Bird & Bird's own title frames AI as "a tool, not a free pass".
  - The earlier report also missed the most useful Italian authority for Evalia: CdS 4857/2025 on owner-side support software.

### EVA's source and dates

- **Fact (High):** The primary EVA article is "JTC bids goodbye to the paper-heavy world of construction tenders" by Dylan Tan, BT, published online on **8 April 2026 at 06:00 SGT** ([BT feature](https://www.businesstimes.com.sg/events-awards/design-ai-tech-awards/design-ai-and-tech-awards/jtc-bids-goodbye-paper-heavy-world-construction-tenders)).
- **Fact (High):** DPEX Network's partial reprint, which the earlier report relied on, is timestamped 7 April 2026 at 22:07. That is the UTC equivalent of the BT time, so the two dates do not conflict. Some research notes recorded the article as "7 April" for this reason ([DPEX](https://www.dpexnetwork.org/news/view/MY5bRmbUsJQMRXGuzjFVjJ)).
- **Fact (High):** The awards results article appeared on **15 April 2026** ([BT awards article](https://www.businesstimes.com.sg/events-awards/design-ai-tech-awards/diverse-ai-solutions-clinch-top-honours-design-ai-and-tech-awards)).
- **Fact (Medium):** A BT print edition of 15 April 2026 is indexed under the same headline, which suggests a print run of the feature. The page blocks automated access and was not read ([PressReader](https://www.pressreader.com/singapore/the-business-times/20260415/281655376646834)).
- **Correction to the earlier report:**
  - The earlier report described EVA's outcomes as "paywalled". The full BT text has now been read, and no measured outcomes are published in it.
  - The earlier report also said JTC "introduced" EVA in April 2026. April 2026 is when EVA was *publicised*; its deployment date is unknown.

---

## EVA: what JTC has actually disclosed

### Functions

- **Fact (High):** EVA "deploy[s] large language models to perform the extraction and initial scoring work that currently falls to evaluators" ([BT feature](https://www.businesstimes.com.sg/events-awards/design-ai-tech-awards/design-ai-and-tech-awards/jtc-bids-goodbye-paper-heavy-world-construction-tenders)).
- **Fact (High):** Users upload tender documents. The system "reads and interprets the unstructured submissions by identifying technical, contractual, and performance-related details, then mapping them against JTC's evaluation criteria". It then "generates a scored output, with its reasoning made explicit, allowing evaluators to review the logic rather than reconstruct it from scratch" ([BT feature](https://www.businesstimes.com.sg/events-awards/design-ai-tech-awards/design-ai-and-tech-awards/jtc-bids-goodbye-paper-heavy-world-construction-tenders)).
- **Fact (High): The fixed sequence.** The interface "mirrors the natural cognitive sequence of an evaluator" ([BT feature](https://www.businesstimes.com.sg/events-awards/design-ai-tech-awards/design-ai-and-tech-awards/jtc-bids-goodbye-paper-heavy-world-construction-tenders)). The steps are:
  1. establish the context;
  2. confirm who is being assessed;
  3. validate that the evaluation criteria have been interpreted correctly;
  4. "only then" proceed to the submissions.
- **Fact (High): The one documented example.** "EVA correctly flagged that a tenderer's stated performance ratings were not substantiated by the supporting documents provided" ([BT feature](https://www.businesstimes.com.sg/events-awards/design-ai-tech-awards/design-ai-and-tech-awards/jtc-bids-goodbye-paper-heavy-world-construction-tenders)).
- **Fact (High): The current scope is quantitative only.** Adam Chern, project manager at JTC, said "EVA currently evaluates quantitative data" and "future phases will incorporate qualitative criteria" ([BT awards article](https://www.businesstimes.com.sg/events-awards/design-ai-tech-awards/diverse-ai-solutions-clinch-top-honours-design-ai-and-tech-awards)).
- **Interpretation (Medium):**
  - EVA scores the countable and verifiable parts of the quality envelope: track record, performance ratings, certifications and contractual compliance items. It does not score narrative methodology.
  - Its demonstrated value is substantiation checking. That is a test of consistency and compliance, not a judgement of quality.
- **Interpretation (Medium):** BT never mentions price analysis, side-by-side ranking, comparison matrices or the drafting of the award paper. The absence suggests these lie outside EVA's current scope, but no source confirms it.

### Build

- **Fact (High):** The design "drew on direct observation of EVA committee members navigating their existing workflows" ("EVA committee" is presumably the evaluation committee). It "was co-created with project managers, contract managers and procurement officers rather than developed in isolation by a technology team" ([BT feature](https://www.businesstimes.com.sg/events-awards/design-ai-tech-awards/design-ai-and-tech-awards/jtc-bids-goodbye-paper-heavy-world-construction-tenders)).
- **Fact (High):** No public source names the model, vendor, system integrator, hosting platform, data classification, retrieval architecture, build date or cost.
- **Fact (High):** JTC plans to "train the AI with more contextual knowledge" ([BT awards article](https://www.businesstimes.com.sg/events-awards/design-ai-tech-awards/diverse-ai-solutions-clinch-top-honours-design-ai-and-tech-awards)).
- **Fact, context (High):** JTC's chief executive since 1 April 2025, Jacqueline Poh, was GovTech's founding chief executive ([GovInsider](https://govinsider.asia/intl-en/article/jtc-corporation-to-get-new-ceo-from-april)).
- **Interpretation (Medium):** The build was business-led, with the user organisation specifying and owning the tool. Whether a contractor wrote the code is unknown.
- **Speculation (Low):** GovTech platforms underpin EVA. Nothing confirms this, and Evalia should not assert it.

### Governance

- **Fact (High):** "The tool is designed around a human-in-the-loop architecture. Evaluators retain full authority over scores and final recommendations; the AI structures, surfaces and highlights, but does not decide." BT calls this "a deliberate governance choice, rooted in the accountability requirements of public-sector procurement" ([BT feature](https://www.businesstimes.com.sg/events-awards/design-ai-tech-awards/design-ai-and-tech-awards/jtc-bids-goodbye-paper-heavy-world-construction-tenders)).
- **Fact (High):** Nothing has been published on:
  - audit-trail logging of AI outputs against human overrides;
  - retention;
  - whether tenderers are told that AI is used;
  - bias or consistency testing;
  - how confidential bid data is handled;
  - implications for challenges.
  No JTC tender document mentioning AI-assisted evaluation was found.
- **Interpretation (Medium):** Human authority over the final decision is necessary but not sufficient. The Trax litigation, covered below, turned on whether a hallucinated finding passed through human review unchecked. EVA's public account does not say how JTC would show that it was checked.

### Reported results versus projections

| Item | Status | Value | Source |
|---|---|---|---|
| Evaluators per tender | Baseline (fact) | about 8 | [BT feature](https://www.businesstimes.com.sg/events-awards/design-ai-tech-awards/design-ai-and-tech-awards/jtc-bids-goodbye-paper-heavy-world-construction-tenders) |
| Effort per evaluator | Baseline (fact) | about 14 man-days | same |
| Documents per tenderer | Baseline (fact) | about 30 | same |
| Construction tenders a year | Baseline (fact) | about 40 | same |
| Total evaluator effort | Baseline (fact) | about 34,000 man-hours a year | same; [DPEX](https://www.dpexnetwork.org/news/view/MY5bRmbUsJQMRXGuzjFVjJ) |
| Schedule saving | **Projection** | 2 to 3 months per project | [BT feature](https://www.businesstimes.com.sg/events-awards/design-ai-tech-awards/design-ai-and-tech-awards/jtc-bids-goodbye-paper-heavy-world-construction-tenders) |
| Hours saved, accuracy, agreement with human scores, tenders processed | **Not published** | none | none |
| Recognition | Fact | Daita large-enterprise winner, 15 April 2026, alongside SBS Transit and Thales | [BT awards article](https://www.businesstimes.com.sg/events-awards/design-ai-tech-awards/diverse-ai-solutions-clinch-top-honours-design-ai-and-tech-awards) |

- **Interpretation (High, arithmetic):** 8 × 14 × 40 = 4,480 man-days, or about 34,000 hours at roughly 7.6 hours a day. The baseline is internally consistent.
- **Interpretation (Medium):** Fourteen man-days per evaluator, worked in parallel, is about three weeks of elapsed time. A saving of two to three months therefore has to include approval cycles, clarification rounds or re-evaluation as well. The figure is a schedule claim, not an effort claim.
- **Interpretation (Medium):** Projected savings, a single anecdote and repeated references to "future phases" point to a pilot or early-production tool in April 2026.
- **Fact (Medium):** A search of BT's May to October 2026 coverage for this report found no update on EVA.

### Roadmap

- **Fact (High):**
  - qualitative criteria in "future phases";
  - "more contextual knowledge";
  - extension to consultancy tenders ([BT awards article](https://www.businesstimes.com.sg/events-awards/design-ai-tech-awards/diverse-ai-solutions-clinch-top-honours-design-ai-and-tech-awards));
  - "the same architecture could, with limited reconfiguration, be applied to consultancy and IT tenders" ([BT feature](https://www.businesstimes.com.sg/events-awards/design-ai-tech-awards/design-ai-and-tech-awards/jtc-bids-goodbye-paper-heavy-world-construction-tenders)).
- **Fact (High):** No statement was found on sharing EVA with other agencies, open-sourcing it or commercialising it.
- **Speculation (Low):** If MOF or GovTech generalises EVA, Singapore government procurement entities such as HDB, LTA and PUB would receive it at no cost.

### Named contacts

- **Adam Chern**, project manager, JTC Corporation. He represented EVA at the Daita finals on 15 April 2026, which comprised a five-minute pitch and a ten-minute Q&A ([BT awards article](https://www.businesstimes.com.sg/events-awards/design-ai-tech-awards/diverse-ai-solutions-clinch-top-honours-design-ai-and-tech-awards)). Fact (High). Whether he is a construction or a digital project manager is unknown.
- **Dylan Tan**, BT journalist and author of the feature ([BT feature](https://www.businesstimes.com.sg/events-awards/design-ai-tech-awards/design-ai-and-tech-awards/jtc-bids-goodbye-paper-heavy-world-construction-tenders)). Fact (High).
- **Jacqueline Poh**, JTC chief executive ([GovInsider](https://govinsider.asia/intl-en/article/jtc-corporation-to-get-new-ceo-from-april)). Fact (High). Her remarks at a 2026 JTC forum reported by The Edge Singapore could not be read, so it is unknown whether she mentioned EVA ([The Edge Singapore](https://www.theedgesingapore.com/news/sustainability/jtc-ceo-says-construction-experiencing-boom-forum-exploring-ai-and)).
- **Wei Ting Wong** (JTC): a LinkedIn profile surfaced in an EVA search but could not be opened. Any link to EVA is unverified (Low) ([LinkedIn](https://www.linkedin.com/in/wei-ting-wong-277102112/)).

---

## The Singapore context made EVA unusually easy to build

### Structured scoring under the Price-Quality Method

- **Fact (High):** The BCA Price-Quality Method (PQM) applies to public-sector CW01 and CW02 tenders with an estimated construction cost of S$3m or more. Since 1 June 2022 price has carried 40% to 60% of the weighting, and civil-engineering tenders use a price weighting ten points higher than building tenders. The Constructability Score Index was removed from 1 February 2023, shifting weight towards Integrated Planning and Design and Advanced Manufacturing and Assembly attributes. The page does not mention AI ([BCA PQM](https://www1.bca.gov.sg/procurement/tender-stage/price-quality-method-pqm-framework)).
- **Fact (High):** Consultancy tenders use the Quality-Fee Method. BCA will pilot a Resourcing Evaluation Guide from Q4 2026 to discourage unsustainably low bids. The release mentions AI only as something *tenderers* may cite as a productivity approach ([BCA, 21 August 2026](https://www1.bca.gov.sg/resources/newsroom/new-pilot-to-better-assess-resourcing-of-tender-proposals-for-public-sector-construction-consultancy-tenders/)).
- **Interpretation (Medium):** Published attributes and fixed weighting bands make PQM well suited to rubric-mapped LLM extraction, while the final weighted calculation stays deterministic. Most owners in the US, Gulf and Europe do not have so standardised a quality rubric, so Evalia must do the criteria-interpretation step itself for each tender.

### A challenge regime that tolerates experimentation

- **Fact (Medium, 2020 source):** Challenges go only to the Government Procurement Adjudication Tribunal, not to the courts. They must be lodged within 15 days, and the tenderer bears the burden of proof. Regulation 29 gives wide award discretion, Regulations 32 and 33 permit information to be withheld, and "detailed methods such as the BCA Price-Quality Method make challenges harder" ([Bird & Bird, 2020](https://www.twobirds.com/en/insights/2020/singapore/singapore-public-procurement-and-challenges-to-tender-awards)). Thresholds and procedures may have changed since then.
- **Interpretation (Medium):** Limited disclosure, tribunal-only review and a short window make AI-assisted evaluation less contestable in Singapore than in the US, where bid protests reach GAO and the Court of Federal Claims. **EVA's thin public governance is therefore less transferable than its architecture.** An independent service operating under US protest rules or UK assessment-summary duties needs a far stronger record.

### Policy pull from the Auditor-General

- **Fact (High):** On 22 September 2025, after the Auditor-General's FY24/25 findings on tender evaluation and contract management, Second Minister for Finance Indranee Rajah said the government "has been actively exploring the use of technology, including artificial intelligence, in procurement" and "has started to use them in suitable areas to reduce errors and increase efficiency". She named no tools ([MOF](https://www.mof.gov.sg/news-resources/newsroom/use-of-ai-and-technology-tools-to-reduce-errors-and-increase-efficiency-in-government-contract-evaluation--award-and-management/)).
- **Interpretation (Medium):** Reducing errors is as strong a rationale as saving time, and the "unsubstantiated performance ratings" example fits that rationale. Evalia's pitch should lead with error and defensibility, not with man-hours.

### GovTech data-classification rules and likely hosting

- **Fact (High):**
  - Pair, GovTech's LLM suite, is approved for RESTRICTED / SENSITIVE NORMAL data ([GovTech Pair](https://www.developer.tech.gov.sg/products/categories/productivity-tools/pair/overview)).
  - AIBots, GovTech's retrieval-augmented chatbot platform, is limited to the same level, runs on Azure OpenAI, and handles tables and images poorly ([AIBots roadmap](https://www.developer.tech.gov.sg/products/categories/productivity-tools/aibots/features-roadmap)).
- **Fact (High): GovTech's GenAI security standard.**
  - Overseas-hosted APIs may handle data only up to RESTRICTED / SENSITIVE NORMAL (GA-1).
  - Singapore-hosted APIs may handle data up to CONFIDENTIAL / SENSITIVE HIGH (GA-2).
  - Self-hosted models need environments cleared for the highest classification of data in the system (GA-4).
  - Providers must commit not to log, retain or train on inputs and outputs, with prompt caching of 24 hours or less permitted. GCC 2.0 GenAI APIs satisfy this control (GA-3).
  - Further controls require output testing against defined metrics (GA-7), user acknowledgement of hallucination risk (GA-8) and display of the maximum permitted input classification (DP-8).
  - Source: [GovTech SSP Gen-AI](https://info.standards.tech.gov.sg/ssp/gen-ai/).
- **Interpretation (Medium):** Tender submissions are commercially sensitive and would ordinarily be classified at least RESTRICTED, often CONFIDENTIAL. EVA therefore most plausibly runs as a bespoke application on Singapore-region, GCC 2.0-provisioned LLM APIs, not as an AIBots bot. **Speculation (Low)** as to the specific stack: no source names it.
- **Interpretation (High) for Evalia:** The GovTech controls are a ready-made minimum specification for Evalia's own data handling: in-region inference, contractual no-retention and no-training terms, output testing and an explicit acknowledgement of hallucination risk.

### JTC's digital agenda

- **Fact (Medium, c. December 2024):** JTC's OPTIMUS v2.0 common data environment had about 1,700 users, 70 projects and more than 20 digitalised processes. JTC's 2025 priorities included AI and machine learning to automate routine tasks ([GovInsider](https://govinsider.asia/intl-en/article/yve-xu-deputy-director-future-of-building-and-infrastructure-division-jtc)).
- **Fact (High):** On 17 July 2026 JTC onboarded the first solutions into the Integrated Digital Delivery Technology Alliance, a curated marketplace that integrates with OPTIMUS. A built-environment productivity Action Team was set up in 2026. The release does not mention EVA ([BCA and JTC release](https://isomer-user-content.by.gov.sg/338/fceb0128-6f7c-422c-89b0-4489c9bda1de/BCA%20&%20JTC%20Media%20Release%20for%20ConTech@PDD.pdf)).
- **Interpretation (Medium):** EVA is the procurement-stage extension of an owner that had already digitised its project documents. Owners without a common data environment will struggle to supply clean inputs. Evalia's intake process must therefore absorb messy PDFs and spreadsheets, which BT says nothing about in EVA's case.

### MOF Innovative Procurement Partnerships as a vendor route

- **Fact (High):** MOF's Innovative Procurement Partnerships (IPPs) lower the barriers to pilots. Under JTC's IPPs, a tenderer whose pilot succeeds can be considered for other JTC projects without a fresh tender. JTC's first two IPP tenders drew close to 20 submissions, covering computer vision for worksite productivity and robotics for drain inspection ([BCA and JTC release](https://isomer-user-content.by.gov.sg/338/fceb0128-6f7c-422c-89b0-4489c9bda1de/BCA%20&%20JTC%20Media%20Release%20for%20ConTech@PDD.pdf); [EdgeProp](https://www.edgeprop.sg/amp/property-news/robotics-automation-and-sandbox-rental-waivers-boost-productivity-and-innovation-construction-sector)).
- **Interpretation (Medium):** The IPPs are a real route in, but so far they target site technology, not procurement software. JTC already has EVA in-house, so an Evalia IPP bid would compete with JTC's own tool. **Singapore is a reference market for Evalia, not a revenue market.**

---

## International peers are defence buyers and courtrooms, not civil owners

### Owner-side deployments

- **UK MoD, Commercial X.** Fact (High): the team plans an "AI Evaluator" for tender and bid analysis in MoD competitions. Its aims are to cut evaluator workload, review more proposals and keep human oversight. The early stages are self-funded under a Collaborative Working Innovation Contract. A supplier webinar planned with techUK for 7 July 2026 was postponed with no new date ([techUK](https://www.techuk.org/events/using-ai-in-support-of-ministry-of-defence-tender-and-bid-analysis)). No results have been published.
- **US Special Operations Command.** Fact (High): solicitation H9240026RE001 states that the government "may employ AI as a tool to assist in the analysis and review of offeror proposals" and that "Any generated report data is not saved" ([Burr & Forman, 7 April 2026](https://www.burr.com/government-contracting/should-the-government-use-ai-tools-to-evaluate-contract-proposals)). Interpretation (High): not saving outputs is the opposite of what courts now ask for.
- **US Army, White Sands Missile Range.** Fact (High): on a mission-support contract of about US$450m, incumbent TRAX International alleged that the technical evaluation contained a "classic AI hallucination" citing invented proposal details. The Army said the Source Selection Authority did not use AI. GAO agreed that a weakness was wrongly assigned but found it non-prejudicial ([Federal News Network](https://federalnewsnetwork.com/contracting/2026/08/lawsuit-over-armys-use-of-ai-in-contract-award-could-increase-transparency-around-proposal-evaluations/)).

### Trax International v. United States

- **Fact (High):**
  - The Court of Federal Claims ruled against Trax, reported on 8 October 2026, because Trax did not connect the alleged hallucinations to evaluation errors or show over-reliance on AI.
  - The court did, however, require the Army to file its AI-generated evaluations in the administrative record.
  - Amy Fuentes of Holland & Knight called the opinion "important but narrow". She expects future protests to succeed where the record shows evaluators adopted AI output without meaningful review, invoking the independent-judgement requirement of FAR 15.308.
  - Sources: [Holland & Knight](https://www.hklaw.com/en/news/intheheadlines/2026/10/ai-hallucination-case-opens-new-era-for-procurement-litigation); [Bloomberg Government](https://news.bgov.com/federal-contracting/ai-hallucination-case-opens-new-era-for-procurement-litigation).
- **Fact (High):** Practitioners recommend disclosing AI use and its purpose in solicitations, describing the human review that follows, and documenting that a human meaningfully reviewed and endorsed AI output ([Federal News Network](https://federalnewsnetwork.com/contracting/2026/08/lawsuit-over-armys-use-of-ai-in-contract-award-could-increase-transparency-around-proposal-evaluations/)).
- **Fact (High):** In GAO's Salient CRGT decision (B-423640.2/.4, 5 January 2026), the protester raised reliance on AI but abandoned the ground, apparently for lack of information ([Burr & Forman](https://www.burr.com/government-contracting/should-the-government-use-ai-tools-to-evaluate-contract-proposals)).
- **Interpretation (High):** **The legal risk lies in undocumented AI influence, not in AI use itself.** For US clients, Evalia's record of findings is discoverable material and must be designed as such.

### Italian rulings

- See the table above.
- **Interpretation (Medium):** CdS 4857/2025 gives the clearest doctrinal home for Evalia in the EU. A tool that supports and does not decide falls outside the rules on algorithmic decisions. CdS 8092/2025 and TAR Lazio 4546/2025 show that courts defer to human commissions' discretionary scores and demand specific, verifiable evidence from challengers. That raises the value of a findings record that is itself specific and verifiable.

### UK PPN 017

- **Fact (High):**
  - PPN 017 (formerly PPN 02/24, updated February 2025) applies to procurements under the Procurement Act 2023 that commenced on or after 24 February 2025.
  - Paragraph 14: "decisions are made with the support of AI systems, not a reliance upon them."
  - Paragraph 15 warns that LLMs can produce plausible but false content and that care is needed "in assessing returns that have used LLMs".
  - Supplier AI-disclosure answers "should not be scored".
  - The note does not directly address authorities using AI to evaluate.
  - Source: [PPN 017](https://assets.publishing.service.gov.uk/media/67af7ba0e270ceae39f9e279/PPN_017_Improving_transparency_of_AI_use_in_procurement.pdf).
- **Interpretation (Medium):** Owner-side AI evaluation in the UK is governed by general principles, not specific guidance. An independent assurer can fill that gap if it brings its own written governance.

### The EU AI Act

- **Fact (Medium):** Public procurement is not one of the Annex III high-risk areas. Annex III obligations apply from 2 August 2026. Automated decisions that determine tender winners warrant case-by-case analysis, and the guide recommends keeping a human in the loop ([Jorpex guide](https://jorpex.com/guides/eu-ai-act-public-procurement/)).
- **Flag:** The guide does not discuss any "digital omnibus" postponement of the high-risk deadlines. The current timetable was not verified for this report.
- **Fact (Medium):** The EU Public Buyers Community publishes model AI procurement clauses ([EC MCC-AI template](https://public-buyers-community.ec.europa.eu/system/files/2023-10/AI_Procurement_Clauses_template_High_Risk%20EN.pdf)).
- **Interpretation (Medium):** A findings-only service with a human-signed output stays clear of any argument that it is an automated award system.

### nPlan and the vendor landscape

- **Fact (High):** An unnamed "large government agency" used nPlan at a Stage 4 gateway review to analyse the schedules of four tender submissions on two highway projects. nPlan reported a difference of "several million dollars" in delay costs between options. The agency used the findings to question bidders and select a contractor. No time saving was reported ([nPlan case study](https://www.casestudies.com/company/nplan/case-study/how-nplans-ai-provided-groundbreaking-insights-for-a-government-agency-overseeing-two-crucial-highway-projects)).
- **Fact (Medium):** The nPlan-hosted version of the case dates from 2023 and names neither the client nor the country ([nPlan](https://nplan.io/case-studies/using-ai-to-evaluate-tenders-for-a-unique-highways-project)).
- **Fact (High):** Stotles' guide describes buyer-side tools that "score and rank vendor submissions" but names no buyer-side vendor. The products it names are supplier-side or discovery tools ([Stotles](https://www.stotles.com/resource/blog/tender-evaluation-software-explained-features-and-benefits-guide)).
- **Interpretation (Medium):** nPlan is the nearest commercial analogue to Evalia: a third party providing narrow, quantified technical analysis to an owner at a formal gateway. Its deliverable, a monetised risk differential that turns into clarification questions, is a template for Evalia's output format.

### What is missing

- **No civil-agency equivalent of EVA was found** outside Singapore: no National Highways, Network Rail, Caltrans, state DOT, Australian or New Zealand state agency, Saudi Etimad, NEOM, Dubai or Abu Dhabi deployment. Australia's DTA is reported only to be "exploring" AI in tender evaluation (Low) ([TechPartner News](https://www.techpartner.news/news/dta-exploring-ai-use-in-tender-evaluations-621317)).
- **No evidence was found of owners or lenders buying third-party AI-assisted bid review as a service.** nPlan is software-led analytics on one dimension (schedule), not a cross-discipline review.
- No guidance from multilateral lenders (World Bank, ADB, EIB) on AI in bid evaluation was found. No Gulf rules on AI in evaluation were found.
- Each of these is an absence of evidence within a limited search budget, not proof of absence.

---

## EVA versus Evalia

| Dimension | EVA (JTC) | Evalia (proposed) | Why it matters |
|---|---|---|---|
| Operator | The owner's own evaluators, in-house ([BT](https://www.businesstimes.com.sg/events-awards/design-ai-tech-awards/design-ai-and-tech-awards/jtc-bids-goodbye-paper-heavy-world-construction-tenders)) | An independent third party engaged by the owner or lender | An outsider has no place in the owner's accountability chain, so its output must be advisory and fully traceable |
| Buyer | A public statutory board, about 40 tenders a year | Private owners, lenders and non-Singapore public owners in the US, Gulf and Europe | No evidence yet of third-party demand; willingness to pay must be tested |
| Criteria scope | Quantitative only; qualitative "future phases" ([BT awards](https://www.businesstimes.com.sg/events-awards/design-ai-tech-awards/diverse-ai-solutions-clinch-top-honours-design-ai-and-tech-awards)) | Quantitative substantiation first, then an engineer-led technical read (programme, method, resourcing, price abnormality) | Engineering judgement is the differentiator EVA lacks; it is also where hallucination risk is highest |
| Sequence | Context, then who is assessed, then criteria validation, then submissions | The same, with the client signing off the criteria interpretation before any bid is read | A criteria interpretation agreed in advance protects against later disputes over what was assessed |
| Output | A scored output with explicit reasoning | Source-cited findings and clarification questions by default; scores only on written request | Sits within "mere support" (Italy) and "support, not reliance" (UK) |
| Human authority | Evaluators decide | The owner's panel decides; the Chartered Civil Engineer signs the findings | Two layers of human judgement, both documented |
| Audit trail | Not published | Per-finding citation, model and prompt version, and a log of engineer actions, retained through the challenge period | Trax put AI output into the administrative record ([Holland & Knight](https://www.hklaw.com/en/news/intheheadlines/2026/10/ai-hallucination-case-opens-new-era-for-procurement-litigation)) |
| Tenderer disclosure | Not published | A model ITT/RFP clause supplied to the client | US practitioners advise disclosure ([FNN](https://federalnewsnetwork.com/contracting/2026/08/lawsuit-over-armys-use-of-ai-in-contract-award-could-increase-transparency-around-proposal-evaluations/)) |
| Hosting | Not published; likely Singapore-hosted under the GovTech standard (Interpretation) | In-region options (US, EU, GCC) with no-retention model terms | Mirrors GovTech controls GA-2 and GA-3 ([SSP](https://info.standards.tech.gov.sg/ssp/gen-ai/)) |
| Evidence of results | Baseline plus a projection; one anecdote | Must publish its own metrics: issues per bid, the share of findings the engineer accepts, false positives | EVA's absence of metrics is a gap Evalia can fill credibly |
| Conflicts | Internal staff under public-sector rules | A per-procurement declaration of no relationship with any bidder | The founder has a commercial history with contractors |
| Liability | The public body | The engineer's professional indemnity plus contractual limits | Not yet researched; see gaps |

---

## Design-and-governance checklist for Evalia

| # | Requirement | Evidence basis |
|---|---|---|
| 1 | **Source-cited findings.** Every finding links to a document, page and clause in the bid. Any finding without a citation is suppressed or marked "unsupported". | The Trax hallucination allegation ([FNN](https://federalnewsnetwork.com/contracting/2026/08/lawsuit-over-armys-use-of-ai-in-contract-award-could-increase-transparency-around-proposal-evaluations/)); EVA's "reasoning made explicit" ([BT](https://www.businesstimes.com.sg/events-awards/design-ai-tech-awards/design-ai-and-tech-awards/jtc-bids-goodbye-paper-heavy-world-construction-tenders)) |
| 2 | **Retention through the challenge period.** Keep inputs, outputs, prompts, model versions and engineer actions until the longest applicable challenge or limitation period has passed, then delete them on a documented schedule. Never adopt USSOCOM's "not saved" approach. | [Holland & Knight](https://www.hklaw.com/en/news/intheheadlines/2026/10/ai-hallucination-case-opens-new-era-for-procurement-litigation); [Burr & Forman](https://www.burr.com/government-contracting/should-the-government-use-ai-tools-to-evaluate-contract-proposals) |
| 3 | **Engineer accept/reject/modify log and signature.** Record the engineer's action on each AI finding, with a reason for each rejection or change. The Chartered Civil Engineer signs the final report. | The FAR 15.308 independent-judgement argument ([Holland & Knight](https://www.hklaw.com/en/news/intheheadlines/2026/10/ai-hallucination-case-opens-new-era-for-procurement-litigation)); PPN 017 para 14 ([PPN 017](https://assets.publishing.service.gov.uk/media/67af7ba0e270ceae39f9e279/PPN_017_Improving_transparency_of_AI_use_in_procurement.pdf)) |
| 4 | **Findings and clarification questions, not scores, by default.** Scoring is available only on the client's written instruction against the client's own rubric. Evalia never makes award recommendations. | CdS 4857/2025 "mero supporto" ([Giustizia Insieme](https://giustiziainsieme.it/print/articolo_pdf?id=3745)); [Jorpex](https://jorpex.com/guides/eu-ai-act-public-procurement/) on automated award decisions |
| 5 | **Criteria interpretation signed off first.** Adopt EVA's sequence: the client approves Evalia's reading of each criterion before any bid is processed. | [BT feature](https://www.businesstimes.com.sg/events-awards/design-ai-tech-awards/design-ai-and-tech-awards/jtc-bids-goodbye-paper-heavy-world-construction-tenders) |
| 6 | **Model tender-disclosure clause.** Supply wording for ITTs and RFPs that states independent AI-assisted scrutiny will be used, for what purpose, and under what human review and data handling. | Chvotkin and Rushing ([FNN](https://federalnewsnetwork.com/contracting/2026/08/lawsuit-over-armys-use-of-ai-in-contract-award-could-increase-transparency-around-proposal-evaluations/)); the USSOCOM solicitation wording ([Burr & Forman](https://www.burr.com/government-contracting/should-the-government-use-ai-tools-to-evaluate-contract-proposals)) |
| 7 | **No training on bid data.** Obtain contractual no-log, no-retain and no-train commitments from every model provider, and pass them through to the client. | GovTech GA-3 ([SSP](https://info.standards.tech.gov.sg/ssp/gen-ai/)); PPN 017 on confidential information ([PPN 017](https://assets.publishing.service.gov.uk/media/67af7ba0e270ceae39f9e279/PPN_017_Improving_transparency_of_AI_use_in_procurement.pdf)) |
| 8 | **Conflict-of-interest declaration** for each procurement: no current or recent commercial relationship with any bidder or its key subcontractors; recusal where one exists. | Interpretation; the founder's contractor-side business-development history makes this decisive |
| 9 | **In-region hosting options.** Offer US, EU and GCC inference and storage. Audit any existing prototype for calls to model APIs hosted outside the client's region before it touches live bids. | GovTech GA-1 and GA-2 ([SSP](https://info.standards.tech.gov.sg/ssp/gen-ai/)); the GovTech approach is the analogue for Gulf data-localisation regimes (Speculation) |
| 10 | **Scope limits and a "not assessed" list** in every report, plus a statement of hallucination risk the client acknowledges. | GovTech GA-8 ([SSP](https://info.standards.tech.gov.sg/ssp/gen-ai/)); PPN 017 para 15 |
| 11 | **Published performance metrics.** Track and disclose findings per bid, the share the engineer accepts, and false positives found on review. | No peer publishes metrics; EVA offers only projections ([BT](https://www.businesstimes.com.sg/events-awards/design-ai-tech-awards/design-ai-and-tech-awards/jtc-bids-goodbye-paper-heavy-world-construction-tenders)) |
| 12 | **Claim-versus-evidence checks as the first product.** Check stated track record, ratings, certifications, key-personnel claims and resourcing against the documents supplied. | EVA's one documented success ([BT](https://www.businesstimes.com.sg/events-awards/design-ai-tech-awards/design-ai-and-tech-awards/jtc-bids-goodbye-paper-heavy-world-construction-tenders)); LLM-assisted bids are now commonplace (CdS 8092/2025, [Bird & Bird](https://cm.twobirds.com/en/insights/2025/ai-in-tenders-a-tool,-not-a-free-pass--the-lesson-from-the-council-of-state)) |

---

## How to use EVA in the pitch and outreach

### In the pitch

- **Use EVA as precedent, not as proof of a market.** Suggested line: "A leading public industrial developer in Singapore now runs construction tender evaluation through an LLM assistant, against a baseline of some 34,000 evaluator hours a year." Cite BT. Do not claim savings that JTC has not measured. Present the two-to-three-month figure only as JTC's projection.
- **Pair EVA with Trax.** EVA shows what is possible. Trax shows what goes wrong when AI findings enter an evaluation without a documented check. Evalia's proposition is the documented check, signed by a Chartered Civil Engineer.
- **Position against EVA's stated limit.** EVA handles quantitative criteria; qualitative criteria are a future phase. Evalia offers engineer-led technical scrutiny now, as findings, with the owner's panel still scoring.
- **Avoid any suggestion of affiliation.** Do not use JTC's name in Evalia branding or describe Evalia as "EVA for X" in client materials. Describe JTC strictly as a public example with a citation.

### A suggested approach to Adam Chern

- **Channel:** LinkedIn, or email through JTC's general enquiry route, after the JTC website is back from maintenance. Keep the message short and identify the sender as a Chartered Civil Engineer researching owner-side AI evaluation governance.
- **Frame:** peer learning, with something to offer in return. Offer a two-page summary of international developments that JTC may not track: Trax v. United States, the three Italian rulings, UK PPN 017 and the MoD's Commercial X.
- **Ask for:** a 20-minute conversation on material already in the public domain:
  - how the criteria-validation step works in practice;
  - what the substantiation check looks for;
  - whether JTC has considered telling tenderers that AI is used;
  - what "qualitative" will mean in the next phase.
- **Do not ask for:** code, criteria, model or vendor names, tender data, unpublished metrics, or an endorsement.

### Realistic limits of what JTC might share

- **Interpretation (Medium):** JTC is a statutory board. Officers will need clearance from corporate communications for anything beyond the published account, and commercially sensitive tender information falls under confidentiality obligations. The most likely result is a polite conversation restating the BT material, or no reply.
- **Interpretation (Medium):** JTC has an in-house tool and a stated plan to extend it to consultancy and IT tenders. It has no evident reason to buy an external equivalent. The IPP route targets site technology. Treat any JTC contact as a source of credibility and learning, not as a sales lead.
- **Speculation (Low):** If EVA's next phase stalls on qualitative criteria, JTC could become interested in an independent engineering-review layer. Nothing in the record supports planning on that.

---

## Gaps and open questions

- **EVA internals:** model, vendor, hosting, data classification, retrieval or fine-tuning, document formats and the handling of drawings and spreadsheets are all unpublished.
- **EVA outcomes:** measured hours saved, accuracy, agreement with human scores, tenders processed, evaluator feedback and any update after April 2026 are all unpublished. JTC's website was under maintenance on 29 October 2026 and could not be searched.
- **EVA governance:** audit trail, retention, disclosure to tenderers, bias testing and the implications for challenges are all unknown.
- **Unread sources:** The Edge Singapore forum article (Cloudflare-blocked) and the PressReader print edition.
- **Italy:** whether CdS 8092/2025 is the appeal of TAR Lazio 4546/2025 is not confirmed. Neither full judgment was read for this report.
- **EU AI Act:** the current Annex III timetable, including any omnibus postponement, is unverified.
- **US federal policy:** whether OMB memos M-25-21 and M-25-22 treat AI used in source selection as "high-impact" is unverified.
- **Demand:** no evidence that owners or lenders buy third-party AI-assisted bid scrutiny. No lender guidance, no Gulf rules and no owner willingness-to-pay data were found.
- **Liability:** the professional-indemnity and chartered-engineer implications of signing AI-assisted findings were not researched. Evalia should consult its PI insurer and the Institution of Civil Engineers' guidance before the first paid engagement.
- **UK:** no case law on AI-assisted evaluation was found, and no source links Procurement Act assessment-summary duties to AI-derived findings.

---

## Sources

- [The Business Times: JTC bids goodbye to the paper-heavy world of construction tenders (8 April 2026)](https://www.businesstimes.com.sg/events-awards/design-ai-tech-awards/design-ai-and-tech-awards/jtc-bids-goodbye-paper-heavy-world-construction-tenders)
- [The Business Times: Diverse AI solutions clinch top honours at Design AI and Tech Awards (15 April 2026)](https://www.businesstimes.com.sg/events-awards/design-ai-tech-awards/diverse-ai-solutions-clinch-top-honours-design-ai-and-tech-awards)
- [DPEX Network reprint of BT feature](https://www.dpexnetwork.org/news/view/MY5bRmbUsJQMRXGuzjFVjJ)
- [PressReader: The Business Times, 15 April 2026](https://www.pressreader.com/singapore/the-business-times/20260415/281655376646834)
- [The Edge Singapore: JTC CEO says construction experiencing boom](https://www.theedgesingapore.com/news/sustainability/jtc-ceo-says-construction-experiencing-boom-forum-exploring-ai-and)
- [GovInsider: JTC Corporation to get new CEO from April](https://govinsider.asia/intl-en/article/jtc-corporation-to-get-new-ceo-from-april)
- [LinkedIn: Wei Ting Wong, JTC Corporation](https://www.linkedin.com/in/wei-ting-wong-277102112/)
- [MOF: Use of AI and technology tools in government contract evaluation (22 September 2025)](https://www.mof.gov.sg/news-resources/newsroom/use-of-ai-and-technology-tools-to-reduce-errors-and-increase-efficiency-in-government-contract-evaluation--award-and-management/)
- [BCA: Price-Quality Method framework](https://www1.bca.gov.sg/procurement/tender-stage/price-quality-method-pqm-framework)
- [BCA: Resourcing Evaluation Guide pilot (21 August 2026)](https://www1.bca.gov.sg/resources/newsroom/new-pilot-to-better-assess-resourcing-of-tender-proposals-for-public-sector-construction-consultancy-tenders/)
- [Bird & Bird: Singapore public procurement and challenges to tender awards (2020)](https://www.twobirds.com/en/insights/2020/singapore/singapore-public-procurement-and-challenges-to-tender-awards)
- [GovTech: Pair overview](https://www.developer.tech.gov.sg/products/categories/productivity-tools/pair/overview)
- [GovTech: AIBots features roadmap](https://www.developer.tech.gov.sg/products/categories/productivity-tools/aibots/features-roadmap)
- [GovTech Security Standards: Generative AI](https://info.standards.tech.gov.sg/ssp/gen-ai/)
- [GovInsider: Yve Xu, JTC, on OPTIMUS](https://govinsider.asia/intl-en/article/yve-xu-deputy-director-future-of-building-and-infrastructure-division-jtc)
- [BCA and JTC media release, ConTech@PDD (17 July 2026)](https://isomer-user-content.by.gov.sg/338/fceb0128-6f7c-422c-89b0-4489c9bda1de/BCA%20&%20JTC%20Media%20Release%20for%20ConTech@PDD.pdf)
- [EdgeProp: Robotics, automation and sandbox rental waivers (17 July 2026)](https://www.edgeprop.sg/amp/property-news/robotics-automation-and-sandbox-rental-waivers-boost-productivity-and-innovation-construction-sector)
- [techUK: Using AI in support of MoD tender and bid analysis](https://www.techuk.org/events/using-ai-in-support-of-ministry-of-defence-tender-and-bid-analysis)
- [Burr & Forman: Should the government use AI tools to evaluate contract proposals? (7 April 2026)](https://www.burr.com/government-contracting/should-the-government-use-ai-tools-to-evaluate-contract-proposals)
- [Federal News Network: Lawsuit over Army's use of AI in contract award (August 2026)](https://federalnewsnetwork.com/contracting/2026/08/lawsuit-over-armys-use-of-ai-in-contract-award-could-increase-transparency-around-proposal-evaluations/)
- [Holland & Knight: AI hallucination case opens new era for procurement litigation (October 2026)](https://www.hklaw.com/en/news/intheheadlines/2026/10/ai-hallucination-case-opens-new-era-for-procurement-litigation)
- [Bloomberg Government: AI hallucination case opens new era for procurement litigation](https://news.bgov.com/federal-contracting/ai-hallucination-case-opens-new-era-for-procurement-litigation)
- [UK Cabinet Office: PPN 017 Improving transparency of AI use in procurement](https://assets.publishing.service.gov.uk/media/67af7ba0e270ceae39f9e279/PPN_017_Improving_transparency_of_AI_use_in_procurement.pdf)
- [Giustizia Insieme: TAR Lazio 4546/2025 and Consiglio di Stato 4857/2025](https://giustiziainsieme.it/print/articolo_pdf?id=3745)
- [Bird & Bird: AI in tenders, a tool not a free pass (Consiglio di Stato 8092/2025)](https://cm.twobirds.com/en/insights/2025/ai-in-tenders-a-tool,-not-a-free-pass--the-lesson-from-the-council-of-state)
- [Segretari comunali Vighenzi: digest of Consiglio di Stato 8092/2025](https://www.segretaricomunalivighenzi.it/?p=65916)
- [Jorpex: EU AI Act and public procurement guide](https://jorpex.com/guides/eu-ai-act-public-procurement/)
- [European Commission: MCC-AI high-risk procurement clauses template](https://public-buyers-community.ec.europa.eu/system/files/2023-10/AI_Procurement_Clauses_template_High_Risk%20EN.pdf)
- [casestudies.com: nPlan government highways agency case study](https://www.casestudies.com/company/nplan/case-study/how-nplans-ai-provided-groundbreaking-insights-for-a-government-agency-overseeing-two-crucial-highway-projects)
- [nPlan: Using AI to evaluate tenders for a unique highways project](https://nplan.io/case-studies/using-ai-to-evaluate-tenders-for-a-unique-highways-project)
- [Stotles: Tender evaluation software explained](https://www.stotles.com/resource/blog/tender-evaluation-software-explained-features-and-benefits-guide)
- [TechPartner News: DTA exploring AI use in tender evaluations](https://www.techpartner.news/news/dta-exploring-ai-use-in-tender-evaluations-621317)
