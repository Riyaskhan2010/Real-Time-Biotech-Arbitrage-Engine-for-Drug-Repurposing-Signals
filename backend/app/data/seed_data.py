"""
DEMO SEED DATA
==============
All records below are clearly labelled as DEMO/SIMULATED DATA for the
BioArbitrage hackathon MVP.

These are NOT real clinical conclusions, peer-reviewed findings, or
treatment recommendations. They are illustrative research scenarios
used to demonstrate the platform's functionality.

Real data integration points are marked with # INTEGRATION POINT comments.
"""

DEMO_DRUGS = [
    {
        "name": "Metformin",
        "generic_name": "Metformin hydrochloride",
        "drug_class": "Biguanide",
        "mechanism_of_action": (
            "Activates AMP-activated protein kinase (AMPK), inhibits mitochondrial "
            "complex I, reduces hepatic gluconeogenesis, improves insulin sensitivity."
        ),
        "approved_indications": ["Type 2 Diabetes Mellitus"],
        "molecular_targets": ["AMPK", "Complex I (mitochondrial)", "mTOR pathway"],
        "pathways": ["AMPK signaling", "mTOR signaling", "PI3K/Akt pathway", "Gluconeogenesis"],
        "fda_status": "Approved",
        "approval_year": 1994,
        "description": (
            "First-line oral antidiabetic drug widely used for type 2 diabetes. "
            "Emerging research suggests potential roles beyond glycemic control."
        ),
        "pubchem_cid": "4091",
        "chembl_id": "CHEMBL1431",
        "atc_code": "A10BA02",
    },
    {
        "name": "Rapamycin",
        "generic_name": "Sirolimus",
        "drug_class": "mTOR inhibitor / Macrolide",
        "mechanism_of_action": (
            "Binds FKBP12 to inhibit mTORC1, suppressing cell proliferation, "
            "protein synthesis, and immune activation."
        ),
        "approved_indications": [
            "Organ transplant rejection prevention",
            "Lymphangioleiomyomatosis",
            "Certain renal tumors",
        ],
        "molecular_targets": ["mTORC1", "FKBP12", "S6K1", "4E-BP1"],
        "pathways": ["mTOR signaling", "PI3K/Akt/mTOR pathway", "Autophagy pathway"],
        "fda_status": "Approved",
        "approval_year": 1999,
        "description": (
            "Immunosuppressant and mTOR inhibitor with established use in transplant "
            "medicine. Active research area for aging, neurodegeneration, and cancer."
        ),
        "pubchem_cid": "5284616",
        "chembl_id": "CHEMBL413",
        "atc_code": "L04AA10",
    },
    {
        "name": "Ivermectin",
        "generic_name": "Ivermectin",
        "drug_class": "Antiparasitic / Avermectin",
        "mechanism_of_action": (
            "Binds glutamate-gated chloride channels and GABA receptors in invertebrates, "
            "causing paralysis. In human cells, may interact with importin alpha/beta "
            "nuclear transport and certain ion channels."
        ),
        "approved_indications": [
            "Onchocerciasis (river blindness)",
            "Strongyloidiasis",
            "Scabies",
            "Head lice",
        ],
        "molecular_targets": ["GluCl channels", "GABA receptors", "Importin alpha/beta"],
        "pathways": ["Nuclear transport pathway", "GABA signaling"],
        "fda_status": "Approved",
        "approval_year": 1987,
        "description": (
            "Broad-spectrum antiparasitic widely used globally. Research has explored "
            "antiviral and anti-inflammatory properties with mixed evidence."
        ),
        "pubchem_cid": "6321424",
        "chembl_id": "CHEMBL192815",
        "atc_code": "P02CF01",
    },
    {
        "name": "Sildenafil",
        "generic_name": "Sildenafil citrate",
        "drug_class": "PDE5 inhibitor",
        "mechanism_of_action": (
            "Inhibits phosphodiesterase type 5 (PDE5), preventing degradation of cGMP, "
            "leading to smooth muscle relaxation and vasodilation."
        ),
        "approved_indications": [
            "Erectile dysfunction",
            "Pulmonary arterial hypertension",
        ],
        "molecular_targets": ["PDE5", "cGMP pathway", "Nitric oxide signaling"],
        "pathways": ["cGMP-PKG signaling", "Nitric oxide pathway", "VEGF signaling"],
        "fda_status": "Approved",
        "approval_year": 1998,
        "description": (
            "Originally developed for cardiovascular indications, repurposed to ED "
            "and PAH. Ongoing research explores neurological and oncological applications."
        ),
        "pubchem_cid": "5212",
        "chembl_id": "CHEMBL192",
        "atc_code": "G04BE03",
    },
    {
        "name": "Doxycycline",
        "generic_name": "Doxycycline hyclate",
        "drug_class": "Tetracycline antibiotic",
        "mechanism_of_action": (
            "Inhibits bacterial protein synthesis by binding 30S ribosomal subunit. "
            "Also inhibits matrix metalloproteinases (MMPs) and has anti-inflammatory effects."
        ),
        "approved_indications": [
            "Bacterial infections",
            "Malaria prophylaxis",
            "Acne",
            "Rosacea",
        ],
        "molecular_targets": ["30S ribosomal subunit", "MMP-1", "MMP-3", "MMP-9"],
        "pathways": ["Protein synthesis", "MMP/collagen pathway", "NF-κB pathway"],
        "fda_status": "Approved",
        "approval_year": 1967,
        "description": (
            "Broad-spectrum tetracycline antibiotic with well-documented anti-inflammatory "
            "and MMP-inhibitory properties beyond its antimicrobial activity."
        ),
        "pubchem_cid": "54671203",
        "chembl_id": "CHEMBL1433",
        "atc_code": "J01AA02",
    },
    {
        "name": "Lithium",
        "generic_name": "Lithium carbonate",
        "drug_class": "Mood stabilizer",
        "mechanism_of_action": (
            "Inhibits GSK-3beta, modulates inositol phosphate signaling, affects "
            "serotonin and dopamine neurotransmission, and activates neurotrophic pathways."
        ),
        "approved_indications": [
            "Bipolar disorder",
            "Manic episodes",
        ],
        "molecular_targets": ["GSK-3beta", "Inositol monophosphatase", "BDNF pathway"],
        "pathways": ["GSK-3 signaling", "Wnt/beta-catenin pathway", "Neuroprotective pathway"],
        "fda_status": "Approved",
        "approval_year": 1970,
        "description": (
            "Classic mood stabilizer with neuroprotective properties. GSK-3beta inhibition "
            "links it to neurodegeneration research, particularly Alzheimer's disease."
        ),
        "pubchem_cid": "11125",
        "chembl_id": "CHEMBL1511",
        "atc_code": "N05AN01",
    },
    {
        "name": "Naltrexone",
        "generic_name": "Naltrexone hydrochloride",
        "drug_class": "Opioid antagonist",
        "mechanism_of_action": (
            "Competitive opioid receptor antagonist at mu, kappa, and delta receptors. "
            "At low doses (LDN), may modulate toll-like receptor 4 (TLR4) signaling "
            "and microglial activation."
        ),
        "approved_indications": [
            "Opioid use disorder",
            "Alcohol use disorder",
        ],
        "molecular_targets": ["Mu-opioid receptor", "Kappa-opioid receptor", "TLR4"],
        "pathways": ["Opioid signaling", "Neuroinflammation pathway", "TLR4/NF-κB pathway"],
        "fda_status": "Approved",
        "approval_year": 1984,
        "description": (
            "Opioid antagonist approved for addiction treatment. Low-dose naltrexone (LDN) "
            "is being researched for autoimmune and inflammatory conditions."
        ),
        "pubchem_cid": "5360515",
        "chembl_id": "CHEMBL28888",
        "atc_code": "N07BB04",
    },
    {
        "name": "Thalidomide",
        "generic_name": "Thalidomide",
        "drug_class": "Immunomodulatory / Cereblon modulator",
        "mechanism_of_action": (
            "Binds cereblon (CRBN), an E3 ubiquitin ligase component, causing targeted "
            "protein degradation. Inhibits TNF-alpha, modulates immune cell function, "
            "and has anti-angiogenic properties."
        ),
        "approved_indications": [
            "Multiple myeloma",
            "Erythema nodosum leprosum",
        ],
        "molecular_targets": ["Cereblon (CRBN)", "TNF-alpha", "VEGF", "Ikaros", "Aiolos"],
        "pathways": ["Ubiquitin-proteasome pathway", "TNF signaling", "Angiogenesis pathway"],
        "fda_status": "Approved (restricted REMS program)",
        "approval_year": 1998,
        "description": (
            "Historically infamous for teratogenicity, later rehabilitated as cancer therapy. "
            "Its cereblon-binding mechanism inspired the IMiD class and PROTAC drug design."
        ),
        "pubchem_cid": "5978",
        "chembl_id": "CHEMBL1222",
        "atc_code": "L04AX02",
    },
]

DEMO_DISEASES = [
    {
        "name": "Alzheimer's Disease",
        "icd10_code": "G30",
        "category": "Neurology / Neurodegeneration",
        "description": (
            "Progressive neurodegenerative disorder characterized by amyloid-beta plaques, "
            "tau neurofibrillary tangles, neuroinflammation, and cognitive decline. "
            "Major unmet medical need with limited disease-modifying treatments."
        ),
        "affected_pathways": [
            "Amyloid processing pathway",
            "Tau phosphorylation",
            "Neuroinflammation",
            "mTOR signaling",
            "GSK-3 signaling",
            "Autophagy pathway",
        ],
        "molecular_markers": ["Amyloid-beta 42", "Phospho-tau 181", "APOE4", "BDNF"],
        "current_treatments": ["Donepezil", "Memantine", "Lecanemab", "Aducanumab"],
        "unmet_needs": (
            "Disease-modifying therapies remain largely ineffective. "
            "Early-stage intervention targets needed."
        ),
        "prevalence": "~55 million people worldwide (2024)",
        "mondo_id": "MONDO:0004975",
        "mesh_id": "D000544",
    },
    {
        "name": "Glioblastoma",
        "icd10_code": "C71.9",
        "category": "Oncology / Neuro-oncology",
        "description": (
            "Highly aggressive primary brain tumor (WHO Grade IV glioma) with median survival "
            "of ~15 months despite standard treatment. Characterized by vascular proliferation, "
            "necrosis, and extensive molecular heterogeneity."
        ),
        "affected_pathways": [
            "EGFR signaling",
            "PTEN/PI3K/Akt pathway",
            "mTOR signaling",
            "VEGF/angiogenesis pathway",
            "Cell cycle dysregulation",
        ],
        "molecular_markers": ["EGFR amplification", "IDH1/2 mutation", "MGMT methylation", "PTEN loss"],
        "current_treatments": ["Temozolomide", "Bevacizumab", "Lomustine", "Radiation therapy"],
        "unmet_needs": (
            "Very poor prognosis; blood-brain barrier limits drug delivery; "
            "no curative treatment exists."
        ),
        "prevalence": "~3 per 100,000 per year",
        "mondo_id": "MONDO:0018177",
        "mesh_id": "D005909",
    },
    {
        "name": "Type 2 Diabetes Mellitus",
        "icd10_code": "E11",
        "category": "Endocrinology / Metabolic disease",
        "description": (
            "Chronic metabolic disorder characterized by insulin resistance and relative "
            "insulin deficiency. Associated with multiple comorbidities including "
            "cardiovascular disease, nephropathy, and neuropathy."
        ),
        "affected_pathways": [
            "Insulin signaling pathway",
            "AMPK signaling",
            "mTOR signaling",
            "Gluconeogenesis",
            "Inflammatory pathways",
        ],
        "molecular_markers": ["HbA1c", "Fasting glucose", "C-peptide", "HOMA-IR"],
        "current_treatments": ["Metformin", "GLP-1 agonists", "SGLT2 inhibitors", "Insulin"],
        "unmet_needs": "Long-term complications prevention; beta cell preservation.",
        "prevalence": "~537 million adults worldwide (2021)",
        "mondo_id": "MONDO:0005148",
        "mesh_id": "D003924",
    },
    {
        "name": "Pulmonary Arterial Hypertension",
        "icd10_code": "I27.0",
        "category": "Cardiology / Pulmonology",
        "description": (
            "Rare but life-threatening condition of elevated pulmonary artery pressure "
            "leading to right heart failure. Characterized by vascular remodeling, "
            "smooth muscle proliferation, and endothelial dysfunction."
        ),
        "affected_pathways": [
            "Endothelin pathway",
            "Nitric oxide/cGMP pathway",
            "Prostacyclin pathway",
            "BMPR2 signaling",
            "VEGF pathway",
        ],
        "molecular_markers": ["BNP/NT-proBNP", "BMPR2 mutation", "Endothelin-1"],
        "current_treatments": ["Sildenafil", "Bosentan", "Treprostinil", "Macitentan"],
        "unmet_needs": "Disease modification; prevention of progression to right heart failure.",
        "prevalence": "~15–50 per million population",
        "mondo_id": "MONDO:0015924",
        "mesh_id": "D006976",
    },
    {
        "name": "Triple-Negative Breast Cancer",
        "icd10_code": "C50.9",
        "category": "Oncology",
        "description": (
            "Breast cancer subtype lacking estrogen receptor, progesterone receptor, "
            "and HER2 expression. Most aggressive subtype with limited targeted therapy "
            "options and high relapse rate."
        ),
        "affected_pathways": [
            "EGFR signaling",
            "PI3K/Akt/mTOR pathway",
            "Androgen receptor pathway",
            "PARP/DNA repair pathway",
            "PD-L1/immune checkpoint",
        ],
        "molecular_markers": ["BRCA1/2 mutations", "PD-L1", "AR expression", "EGFR"],
        "current_treatments": ["Chemotherapy", "Pembrolizumab", "Olaparib", "Sacituzumab govitecan"],
        "unmet_needs": (
            "Targeted therapies remain limited; high metastatic potential; "
            "chemotherapy resistance mechanisms."
        ),
        "prevalence": "~15–20% of all breast cancer cases",
        "mondo_id": "MONDO:0005494",
        "mesh_id": "D064726",
    },
    {
        "name": "Multiple Sclerosis",
        "icd10_code": "G35",
        "category": "Neurology / Autoimmune",
        "description": (
            "Autoimmune demyelinating disease of the central nervous system characterized "
            "by inflammation, demyelination, axonal damage, and neurodegeneration. "
            "Multiple phenotypes (RRMS, PPMS, SPMS) with variable progression."
        ),
        "affected_pathways": [
            "T cell activation pathway",
            "B cell signaling",
            "Neuroinflammation",
            "Remyelination pathway",
            "TLR4/NF-κB pathway",
        ],
        "molecular_markers": ["Oligoclonal bands", "Neurofilament light chain", "MRI lesion load"],
        "current_treatments": ["Interferon beta", "Natalizumab", "Ocrelizumab", "Fingolimod"],
        "unmet_needs": "Neuroprotection; progressive forms have limited treatment options.",
        "prevalence": "~2.8 million people worldwide",
        "mondo_id": "MONDO:0005301",
        "mesh_id": "D009103",
    },
    {
        "name": "Pancreatic Ductal Adenocarcinoma",
        "icd10_code": "C25.0",
        "category": "Oncology / GI Oncology",
        "description": (
            "Most common pancreatic malignancy with dismal prognosis (5-year survival <12%). "
            "Characterized by dense stroma, immune evasion, and late diagnosis. "
            "Highly treatment-resistant."
        ),
        "affected_pathways": [
            "KRAS signaling",
            "TGF-beta/Smad pathway",
            "Notch signaling",
            "Hedgehog pathway",
            "mTOR signaling",
        ],
        "molecular_markers": ["KRAS mutation (~95%)", "CA 19-9", "SMAD4 loss", "TP53 mutation"],
        "current_treatments": ["Gemcitabine", "FOLFIRINOX", "Abraxane", "Erlotinib"],
        "unmet_needs": "Early detection biomarkers; overcoming stromal barrier; KRAS targeting.",
        "prevalence": "~500,000 new cases per year globally",
        "mondo_id": "MONDO:0006047",
        "mesh_id": "D021441",
    },
]

DEMO_SIGNALS = [
    {
        "drug_name": "Metformin",
        "disease_name": "Alzheimer's Disease",
        "title": "Metformin AMPK Activation — Potential Neuroprotective Signal in Alzheimer's Disease",
        "summary": (
            "[DEMO DATA] Computational analysis of published research suggests Metformin's "
            "known AMPK activation and mTOR inhibition mechanisms overlap significantly with "
            "pathways implicated in Alzheimer's pathology. Multiple independent research groups "
            "have reported associations in epidemiological and preclinical studies."
        ),
        "biological_mechanism": (
            "Metformin activates AMPK, which inhibits mTORC1 and promotes autophagy. "
            "Autophagy impairment is a key driver of amyloid-beta and tau accumulation in "
            "Alzheimer's Disease. Additionally, AMPK activation reduces neuroinflammation "
            "via NF-κB suppression, and GSK-3beta activity (a key tau kinase) is reduced "
            "downstream of AMPK activation."
        ),
        "evidence_score": 82.0,
        "confidence_level": "high",
        "source_count": 7,
        "score_breakdown": {
            "independent_sources": 28,
            "recency_score": 22,
            "clinical_trial_support": 12,
            "mechanism_alignment": 20,
            "total": 82,
        },
        "ai_explanation": (
            "[DEMO — AI Explanation] This signal was detected because Metformin's primary "
            "mechanism (AMPK activation → mTOR inhibition → autophagy induction) directly "
            "addresses one of the core molecular dysfunctions in Alzheimer's Disease — impaired "
            "protein clearance leading to amyloid and tau accumulation. Seven independent research "
            "groups have reported this association in peer-reviewed literature. Two clinical trials "
            "are ongoing. The mechanistic overlap is strong and the drug has a well-characterised "
            "safety profile after decades of use."
        ),
        "explanation_factors": [
            {
                "factor": "Shared Biological Pathway",
                "detail": "AMPK/mTOR pathway dysregulated in both T2DM and Alzheimer's neurodegeneration",
                "strength": "strong",
            },
            {
                "factor": "Autophagy Enhancement",
                "detail": "AMPK activation induces autophagy, reducing amyloid-beta and tau aggregation",
                "strength": "strong",
            },
            {
                "factor": "Neuroinflammation Reduction",
                "detail": "Metformin reduces NF-κB-mediated neuroinflammation in animal models",
                "strength": "moderate",
            },
            {
                "factor": "Epidemiological Association",
                "detail": "Diabetic patients on Metformin show lower AD incidence in several cohort studies",
                "strength": "moderate",
            },
            {
                "factor": "Active Clinical Trials",
                "detail": "MILES and TAME trials actively investigating Metformin in aging/neurodegeneration",
                "strength": "supportive",
            },
        ],
        "is_novel": False,
        "status": "active",
        "data_source": "demo",
    },
    {
        "drug_name": "Rapamycin",
        "disease_name": "Alzheimer's Disease",
        "title": "Rapamycin mTORC1 Inhibition — Autophagy Restoration Signal in Neurodegeneration",
        "summary": (
            "[DEMO DATA] Rapamycin's direct mTORC1 inhibition presents a mechanistically "
            "compelling signal for Alzheimer's Disease. Preclinical mouse models show "
            "significant amyloid burden reduction and cognitive improvement."
        ),
        "biological_mechanism": (
            "mTORC1 hyperactivation impairs autophagy, accelerating amyloid-beta and tau "
            "accumulation. Rapamycin directly inhibits mTORC1, restoring autophagic flux "
            "and reducing protein aggregate burden. Additionally, mTOR inhibition reduces "
            "neuroinflammatory cytokine production and may extend neuronal survival."
        ),
        "evidence_score": 76.0,
        "confidence_level": "high",
        "source_count": 5,
        "score_breakdown": {
            "independent_sources": 20,
            "recency_score": 20,
            "clinical_trial_support": 8,
            "mechanism_alignment": 28,
            "total": 76,
        },
        "ai_explanation": (
            "[DEMO — AI Explanation] Rapamycin is the gold-standard mTOR inhibitor. "
            "Given that mTOR hyperactivation is directly linked to impaired autophagy and "
            "increased amyloid-beta accumulation, the mechanistic case is strong. Multiple "
            "preclinical studies in AD mouse models demonstrate cognitive improvement. "
            "The main translational challenge is tolerability with chronic systemic dosing."
        ),
        "explanation_factors": [
            {
                "factor": "Direct Target Overlap",
                "detail": "mTORC1 hyperactivation is documented in Alzheimer's brain tissue",
                "strength": "strong",
            },
            {
                "factor": "Preclinical Evidence",
                "detail": "Multiple mouse model studies show amyloid reduction with rapamycin",
                "strength": "strong",
            },
            {
                "factor": "Autophagy Pathway",
                "detail": "mTOR inhibition directly restores autophagic flux",
                "strength": "strong",
            },
            {
                "factor": "Tolerability Concern",
                "detail": "Chronic systemic immunosuppression limits long-term use",
                "strength": "negative",
            },
        ],
        "is_novel": False,
        "status": "active",
        "data_source": "demo",
    },
    {
        "drug_name": "Sildenafil",
        "disease_name": "Alzheimer's Disease",
        "title": "Sildenafil PDE5 Inhibition — cGMP-Mediated Neuroprotection Signal",
        "summary": (
            "[DEMO DATA] A large-scale insurance claims study reported association between "
            "Sildenafil use and reduced Alzheimer's incidence. The proposed mechanism involves "
            "cGMP elevation, cerebrovascular improvement, and tau phosphorylation reduction."
        ),
        "biological_mechanism": (
            "PDE5 inhibition elevates cGMP in neurons, activating PKG which phosphorylates "
            "GSK-3beta (inactivating it), reducing tau hyperphosphorylation. Cerebrovascular "
            "effects improve cerebral blood flow, reducing vascular contributions to neurodegeneration. "
            "VEGF-mediated neuroprotection may also be relevant."
        ),
        "evidence_score": 71.0,
        "confidence_level": "medium",
        "source_count": 4,
        "score_breakdown": {
            "independent_sources": 16,
            "recency_score": 24,
            "clinical_trial_support": 8,
            "mechanism_alignment": 23,
            "total": 71,
        },
        "ai_explanation": (
            "[DEMO — AI Explanation] The Cleveland Clinic network medicine study identified "
            "Sildenafil as a top Alzheimer's candidate using network-based drug repurposing. "
            "A large insurance database analysis (7+ million patients) showed 69% lower AD "
            "incidence in Sildenafil users after adjustment. Phase II trials are being planned. "
            "Mechanistically, tau reduction via GSK-3beta inactivation is plausible."
        ),
        "explanation_factors": [
            {
                "factor": "Network Medicine Analysis",
                "detail": "Top-ranked candidate in Cleveland Clinic network drug repurposing study",
                "strength": "strong",
            },
            {
                "factor": "Large Observational Study",
                "detail": "Insurance database study: n=7M+, 69% lower AD incidence in users",
                "strength": "strong",
            },
            {
                "factor": "Tau Reduction Mechanism",
                "detail": "cGMP/PKG/GSK-3beta axis reduces tau hyperphosphorylation",
                "strength": "moderate",
            },
            {
                "factor": "Confounding Risk",
                "detail": "Observational study subject to indication bias and confounders",
                "strength": "negative",
            },
        ],
        "is_novel": False,
        "status": "active",
        "data_source": "demo",
    },
    {
        "drug_name": "Metformin",
        "disease_name": "Triple-Negative Breast Cancer",
        "title": "Metformin AMPK/mTOR — Cancer Metabolism Signal in TNBC",
        "summary": (
            "[DEMO DATA] Metformin's anti-proliferative effects via AMPK activation and "
            "mTOR inhibition intersect with key oncogenic pathways in Triple-Negative Breast Cancer. "
            "Epidemiological data and in vitro evidence support further investigation."
        ),
        "biological_mechanism": (
            "Cancer cells depend on mTOR-driven protein synthesis and metabolic reprogramming. "
            "Metformin-induced AMPK activation inhibits mTORC1, suppressing cancer cell "
            "proliferation and protein synthesis. Mitochondrial Complex I inhibition reduces "
            "ATP for energy-intensive cancer growth. AMPK also phosphorylates and stabilizes "
            "p53, promoting apoptosis in some cancer cell lines."
        ),
        "evidence_score": 68.0,
        "confidence_level": "medium",
        "source_count": 5,
        "score_breakdown": {
            "independent_sources": 20,
            "recency_score": 18,
            "clinical_trial_support": 10,
            "mechanism_alignment": 20,
            "total": 68,
        },
        "ai_explanation": (
            "[DEMO — AI Explanation] TNBC cells frequently show PI3K/Akt/mTOR pathway "
            "hyperactivation. Metformin's AMPK activation counters this directly. Multiple "
            "in vitro studies show Metformin reduces TNBC cell viability. Epidemiological "
            "studies of diabetic patients show reduced breast cancer incidence on Metformin. "
            "Several clinical trials have investigated this combination."
        ),
        "explanation_factors": [
            {
                "factor": "mTOR Pathway Overlap",
                "detail": "TNBC frequently shows mTOR hyperactivation; Metformin inhibits it via AMPK",
                "strength": "strong",
            },
            {
                "factor": "In Vitro Evidence",
                "detail": "Multiple studies show TNBC cell line growth inhibition with Metformin",
                "strength": "moderate",
            },
            {
                "factor": "Epidemiological Signal",
                "detail": "Reduced breast cancer incidence in T2DM patients on Metformin",
                "strength": "moderate",
            },
            {
                "factor": "Clinical Trial Data",
                "detail": "Phase II trials have investigated Metformin in early breast cancer",
                "strength": "supportive",
            },
        ],
        "is_novel": False,
        "status": "active",
        "data_source": "demo",
    },
    {
        "drug_name": "Doxycycline",
        "disease_name": "Glioblastoma",
        "title": "Doxycycline MMP Inhibition — Anti-Invasive Signal in Glioblastoma",
        "summary": (
            "[DEMO DATA] Doxycycline's matrix metalloproteinase (MMP) inhibitory activity "
            "presents a research signal for glioblastoma, where MMP-mediated invasion is "
            "a key driver of treatment failure and recurrence."
        ),
        "biological_mechanism": (
            "Glioblastoma invasiveness depends heavily on MMP-2 and MMP-9 activity for "
            "extracellular matrix degradation. Doxycycline inhibits multiple MMPs independently "
            "of its antibiotic activity. Additionally, doxycycline has been shown to inhibit "
            "mitochondrial biogenesis in cancer stem cells, reducing the treatment-resistant "
            "cancer stem cell population."
        ),
        "evidence_score": 58.0,
        "confidence_level": "medium",
        "source_count": 3,
        "score_breakdown": {
            "independent_sources": 12,
            "recency_score": 16,
            "clinical_trial_support": 6,
            "mechanism_alignment": 24,
            "total": 58,
        },
        "ai_explanation": (
            "[DEMO — AI Explanation] GBM invasion is a primary reason for treatment failure — "
            "tumour cells spread along white matter tracts beyond the resection margin. "
            "Doxycycline's dual mechanism (MMP inhibition + cancer stem cell targeting via "
            "mitochondrial inhibition) addresses two independent aspects of GBM biology. "
            "Blood-brain barrier penetration is a known challenge but doxycycline does cross the BBB."
        ),
        "explanation_factors": [
            {
                "factor": "MMP Inhibition",
                "detail": "Doxycycline inhibits MMP-2 and MMP-9, key drivers of GBM invasion",
                "strength": "strong",
            },
            {
                "factor": "Cancer Stem Cell Targeting",
                "detail": "Mitochondrial biogenesis inhibition reduces treatment-resistant CSCs",
                "strength": "moderate",
            },
            {
                "factor": "BBB Penetration",
                "detail": "Doxycycline crosses the blood-brain barrier at therapeutic concentrations",
                "strength": "supportive",
            },
            {
                "factor": "Limited Clinical Evidence",
                "detail": "Predominantly preclinical data; no large randomized trials yet",
                "strength": "negative",
            },
        ],
        "is_novel": True,
        "status": "active",
        "data_source": "demo",
    },
    {
        "drug_name": "Lithium",
        "disease_name": "Alzheimer's Disease",
        "title": "Lithium GSK-3β Inhibition — Tau Phosphorylation Reduction Signal",
        "summary": (
            "[DEMO DATA] Lithium is a potent GSK-3beta inhibitor. GSK-3beta is the primary "
            "tau kinase implicated in Alzheimer's neurofibrillary tangle formation. "
            "This mechanistic connection has generated sustained research interest."
        ),
        "biological_mechanism": (
            "GSK-3beta phosphorylates tau at multiple sites, promoting neurofibrillary tangle "
            "formation. Lithium inhibits GSK-3beta both directly (competing with Mg2+) and "
            "indirectly (through Akt activation). Reduced tau hyperphosphorylation should "
            "slow tangle formation. Additionally, lithium activates BDNF/TrkB neuroprotective "
            "signaling and reduces neuroinflammation."
        ),
        "evidence_score": 74.0,
        "confidence_level": "high",
        "source_count": 6,
        "score_breakdown": {
            "independent_sources": 24,
            "recency_score": 18,
            "clinical_trial_support": 12,
            "mechanism_alignment": 20,
            "total": 74,
        },
        "ai_explanation": (
            "[DEMO — AI Explanation] GSK-3beta was identified as a primary tau kinase before "
            "lithium's AD potential was recognized — the mechanistic connection emerged from "
            "basic science rather than clinical observation. Multiple small clinical trials "
            "have shown CSF tau reduction with lithium in early AD. The challenge is the "
            "narrow therapeutic index requiring careful dosing."
        ),
        "explanation_factors": [
            {
                "factor": "Primary Tau Kinase Target",
                "detail": "GSK-3beta is the main kinase responsible for pathological tau hyperphosphorylation",
                "strength": "strong",
            },
            {
                "factor": "Clinical Trial Evidence",
                "detail": "Phase II trials show CSF p-tau reduction with lithium in MCI/early AD",
                "strength": "strong",
            },
            {
                "factor": "Neuroprotective Signaling",
                "detail": "Lithium activates BDNF/TrkB pathway, supporting neuronal survival",
                "strength": "moderate",
            },
            {
                "factor": "Narrow Therapeutic Index",
                "detail": "Lithium requires careful dosing; toxicity risk at slightly elevated levels",
                "strength": "negative",
            },
        ],
        "is_novel": False,
        "status": "active",
        "data_source": "demo",
    },
    {
        "drug_name": "Naltrexone",
        "disease_name": "Multiple Sclerosis",
        "title": "Low-Dose Naltrexone TLR4 Modulation — Neuroinflammation Signal in MS",
        "summary": (
            "[DEMO DATA] Low-dose naltrexone (LDN) may modulate microglial TLR4 signaling "
            "and reduce neuroinflammation in multiple sclerosis. Patient-reported outcomes "
            "and small trials suggest quality-of-life benefits."
        ),
        "biological_mechanism": (
            "At low doses, naltrexone acts as a TLR4 antagonist on microglia, reducing "
            "neuroinflammatory cytokine production (TNF-alpha, IL-6, IL-1beta). Transient "
            "opioid receptor blockade may also trigger endorphin upregulation. The net effect "
            "is a shift from pro-inflammatory to anti-inflammatory microglial phenotype, "
            "potentially reducing demyelinating lesion activity."
        ),
        "evidence_score": 52.0,
        "confidence_level": "low",
        "source_count": 3,
        "score_breakdown": {
            "independent_sources": 12,
            "recency_score": 14,
            "clinical_trial_support": 8,
            "mechanism_alignment": 18,
            "total": 52,
        },
        "ai_explanation": (
            "[DEMO — AI Explanation] LDN has an active patient/clinician community with "
            "growing research interest. The TLR4 mechanism is scientifically plausible for "
            "MS neuroinflammation. However, evidence remains limited to small trials and "
            "observational studies. This is a lower-confidence signal requiring prospective "
            "randomized trial data before stronger conclusions can be drawn."
        ),
        "explanation_factors": [
            {
                "factor": "TLR4/Neuroinflammation Mechanism",
                "detail": "LDN acts as TLR4 antagonist, reducing microglial pro-inflammatory activity",
                "strength": "moderate",
            },
            {
                "factor": "Patient-Reported Evidence",
                "detail": "Large LDN patient registry reports quality-of-life improvements in MS",
                "strength": "weak",
            },
            {
                "factor": "Small Trial Data",
                "detail": "Multiple small open-label trials show tolerability and symptom benefit",
                "strength": "weak",
            },
            {
                "factor": "Lack of RCT Evidence",
                "detail": "No large randomized controlled trial completed as of analysis date",
                "strength": "negative",
            },
        ],
        "is_novel": True,
        "status": "active",
        "data_source": "demo",
    },
    {
        "drug_name": "Rapamycin",
        "disease_name": "Pancreatic Ductal Adenocarcinoma",
        "title": "Rapamycin mTOR Inhibition — Metabolic Vulnerability Signal in PDAC",
        "summary": (
            "[DEMO DATA] Pancreatic ductal adenocarcinoma shows context-dependent mTOR "
            "dependence. Rapamycin and rapalogs have shown activity in select PDAC subtypes, "
            "with ongoing investigation into predictive biomarkers."
        ),
        "biological_mechanism": (
            "PDAC frequently shows PI3K/mTOR pathway activation downstream of KRAS. "
            "mTOR inhibition reduces ribosome biogenesis and cap-dependent translation, "
            "limiting cancer cell protein synthesis. Combination with KRAS pathway inhibitors "
            "may overcome feedback resistance mechanisms. The autophagy-dependent survival "
            "of PDAC cells creates a metabolic vulnerability exploitable with mTOR modulators."
        ),
        "evidence_score": 55.0,
        "confidence_level": "low",
        "source_count": 3,
        "score_breakdown": {
            "independent_sources": 12,
            "recency_score": 15,
            "clinical_trial_support": 8,
            "mechanism_alignment": 20,
            "total": 55,
        },
        "ai_explanation": (
            "[DEMO — AI Explanation] PDAC is notoriously treatment-resistant. The mTOR "
            "pathway signal is mechanistically plausible but clinical response has been "
            "heterogeneous — likely reflecting tumour subtype differences. Biomarker "
            "stratification (PI3K pathway activation status) may identify a responsive subpopulation. "
            "This is a lower-confidence signal requiring further mechanistic investigation."
        ),
        "explanation_factors": [
            {
                "factor": "PI3K/mTOR Pathway Activation",
                "detail": "KRAS-driven PI3K/mTOR activation is common in PDAC",
                "strength": "moderate",
            },
            {
                "factor": "Rapalog Clinical Data",
                "detail": "Everolimus (rapalog) has shown activity in subset of PDAC patients",
                "strength": "moderate",
            },
            {
                "factor": "Autophagy Dependence",
                "detail": "PDAC survival depends on autophagy, creating mTOR modulation complexity",
                "strength": "complex",
            },
            {
                "factor": "KRAS Feedback Resistance",
                "detail": "mTOR inhibition triggers feedback KRAS activation, limiting response",
                "strength": "negative",
            },
        ],
        "is_novel": False,
        "status": "active",
        "data_source": "demo",
    },
]

DEMO_EVIDENCE = [
    # ── Signal 0: Metformin → Alzheimer's ────────────────────────────────────
    # All three records are SIMULATED DEMO DATA.
    # No real DOI, PMID, NCT, or external URL is provided.
    # Source references have been removed to avoid presenting fabricated citations.
    {
        "signal_index": 0,
        "evidence_type": "research_paper",
        "title": "[DEMO] AMPK Activation by Metformin — Simulated Preclinical Evidence Record",
        "authors": ["[Simulated Author A]", "[Simulated Author B]"],
        "abstract": (
            "[DEMO DATA — Fully simulated record, not a real publication] "
            "This record illustrates how a preclinical animal study would appear in the "
            "BioArbitrage evidence database. It represents the type of research that would "
            "support an AMPK/autophagy mechanism connecting Metformin to Alzheimer's disease "
            "pathology. No real findings are described here. This is platform demonstration "
            "data only."
        ),
        "summary": (
            "[SIMULATED] Illustrative preclinical record: AMPK activation by Metformin "
            "is a biologically plausible mechanism relevant to Alzheimer's Disease pathology. "
            "This record is simulated demo data — not a real publication."
        ),
        "publication_date": "2023-08-15",
        "journal": "[Simulated Journal — Demo Data]",
        "source_name": "Simulated source — no external link",
        "source_url": None,
        "doi": None,
        "pmid": None,
        "relevance_score": 0.95,
        "relevance_explanation": (
            "Illustrates preclinical mechanism evidence for AMPK/autophagy pathway "
            "relevant to the Metformin → Alzheimer's signal"
        ),
        "supports_mechanism": True,
        "is_demo_data": True,
    },
    {
        "signal_index": 0,
        "evidence_type": "clinical_trial",
        "title": "[DEMO] Metformin Aging Trial — Simulated Clinical Trial Record",
        "authors": ["[Simulated Principal Investigator]"],
        "abstract": (
            "[DEMO DATA — Fully simulated record, not a real clinical trial registration] "
            "This record illustrates how a clinical trial with cognitive endpoints would "
            "appear in BioArbitrage. Real trials investigating Metformin in aging/cognition "
            "do exist (e.g. the TAME trial), but this specific record is simulated demo data "
            "and does not represent any real trial registration."
        ),
        "summary": (
            "[SIMULATED] Illustrative clinical trial record: Metformin aging trial with "
            "cognitive sub-endpoints. This is simulated demo data — not a real trial record."
        ),
        "publication_date": "2022-01-10",
        "journal": "[Simulated Registry Entry — Demo Data]",
        "source_name": "Simulated source — no external link",
        "source_url": None,
        "doi": None,
        "pmid": None,
        "nct_id": None,
        "relevance_score": 0.88,
        "relevance_explanation": (
            "Illustrates clinical trial evidence for Metformin cognitive outcomes "
            "relevant to the Metformin → Alzheimer's signal"
        ),
        "supports_mechanism": False,
        "is_demo_data": True,
    },
    {
        "signal_index": 0,
        "evidence_type": "research_paper",
        "title": "[DEMO] Metformin Use and Alzheimer's Risk — Simulated Epidemiological Evidence Record",
        "authors": ["[Simulated Author C]", "[Simulated Author D]", "[Simulated Author E]"],
        "abstract": (
            "[DEMO DATA — Fully simulated record, not a real publication] "
            "This record illustrates how an epidemiological cohort study would appear in "
            "BioArbitrage. It represents the type of observational evidence that would "
            "support an association between Metformin use and reduced Alzheimer's risk "
            "in Type 2 Diabetes patients. No real findings are described. Demo data only."
        ),
        "summary": (
            "[SIMULATED] Illustrative epidemiological record: Metformin use and AD risk "
            "in T2DM cohort. This is simulated demo data — not a real publication."
        ),
        "publication_date": "2022-11-03",
        "journal": "[Simulated Journal — Demo Data]",
        "source_name": "Simulated source — no external link",
        "source_url": None,
        "doi": None,
        "pmid": None,
        "relevance_score": 0.82,
        "relevance_explanation": (
            "Illustrates epidemiological evidence for the Metformin → Alzheimer's "
            "research association"
        ),
        "supports_mechanism": False,
        "is_demo_data": True,
    },
    # ── Signal 2: Sildenafil → Alzheimer's ───────────────────────────────────
    {
        "signal_index": 2,
        "evidence_type": "research_paper",
        "title": "[DEMO] Network Medicine Analysis — Simulated Drug Repurposing Candidate Record",
        "authors": ["[Simulated Author F]", "[Simulated Author G]"],
        "abstract": (
            "[DEMO DATA — Fully simulated record, not a real publication] "
            "This record illustrates how a network medicine drug repurposing study would "
            "appear in BioArbitrage. It represents the type of computational evidence that "
            "would support identifying Sildenafil as an Alzheimer's disease candidate. "
            "No real findings are described here. This is platform demonstration data only."
        ),
        "summary": (
            "[SIMULATED] Illustrative network medicine record: computational identification "
            "of Sildenafil as AD repurposing candidate. Simulated demo data — not real."
        ),
        "publication_date": "2021-12-22",
        "journal": "[Simulated Journal — Demo Data]",
        "source_name": "Simulated source — no external link",
        "source_url": None,
        "doi": None,
        "pmid": None,
        "relevance_score": 0.97,
        "relevance_explanation": (
            "Illustrates network medicine evidence for the Sildenafil → Alzheimer's signal"
        ),
        "supports_mechanism": True,
        "is_demo_data": True,
    },
    {
        "signal_index": 2,
        "evidence_type": "research_paper",
        "title": "[DEMO] Real-World Observational Study — Simulated Large-Scale Evidence Record",
        "authors": ["[Simulated Author H]", "[Simulated Author I]"],
        "abstract": (
            "[DEMO DATA — Fully simulated record, not a real publication] "
            "This record illustrates how a large-scale observational database study would "
            "appear in BioArbitrage. It represents the type of real-world evidence that "
            "might support a Sildenafil–Alzheimer's research association. "
            "No real findings are described. All figures are illustrative only. "
            "Observational studies of this type are subject to confounding and indication bias."
        ),
        "summary": (
            "[SIMULATED] Illustrative observational study record: Sildenafil use and "
            "AD incidence in a large database. Simulated demo data — not a real publication. "
            "Any figures shown are illustrative only."
        ),
        "publication_date": "2021-12-22",
        "journal": "[Simulated Journal — Demo Data]",
        "source_name": "Simulated source — no external link",
        "source_url": None,
        "doi": None,
        "pmid": None,
        "relevance_score": 0.93,
        "relevance_explanation": (
            "Illustrates large-scale observational evidence for the Sildenafil → "
            "Alzheimer's signal"
        ),
        "supports_mechanism": False,
        "is_demo_data": True,
    },
    # ── Signal 4: Doxycycline → GBM ──────────────────────────────────────────
    {
        "signal_index": 4,
        "evidence_type": "research_paper",
        "title": "[DEMO] Doxycycline MMP Inhibition in GBM — Simulated In Vitro Evidence Record",
        "authors": ["[Simulated Author J]", "[Simulated Author K]"],
        "abstract": (
            "[DEMO DATA — Fully simulated record, not a real publication] "
            "This record illustrates how an in vitro cell study would appear in BioArbitrage. "
            "It represents the type of laboratory evidence that would support Doxycycline's "
            "MMP inhibitory activity in Glioblastoma cells. "
            "No real findings are described. This is platform demonstration data only."
        ),
        "summary": (
            "[SIMULATED] Illustrative in vitro record: Doxycycline MMP inhibition in GBM "
            "cells. Simulated demo data — not a real publication."
        ),
        "publication_date": "2023-03-14",
        "journal": "[Simulated Journal — Demo Data]",
        "source_name": "Simulated source — no external link",
        "source_url": None,
        "doi": None,
        "pmid": None,
        "relevance_score": 0.89,
        "relevance_explanation": (
            "Illustrates in vitro mechanism evidence for the Doxycycline → GBM signal"
        ),
        "supports_mechanism": True,
        "is_demo_data": True,
    },
]

DEMO_RESEARCH_SOURCES = [
    {
        "title": "[DEMO] bioRxiv Feed — Preprint monitoring placeholder",
        "source_type": "biorxiv",
        "abstract": "Extension point: Connect to bioRxiv API to ingest neuroscience and pharmacology preprints.",
        "is_processed": False,
        "is_demo_data": True,
    },
    {
        "title": "[DEMO] medRxiv Feed — Clinical preprint monitoring placeholder",
        "source_type": "medrxiv",
        "abstract": "Extension point: Connect to medRxiv API to ingest clinical research preprints.",
        "is_processed": False,
        "is_demo_data": True,
    },
    {
        "title": "[DEMO] ClinicalTrials.gov Feed — Trial monitoring placeholder",
        "source_type": "clinicaltrials",
        "abstract": "Extension point: Connect to ClinicalTrials.gov API to monitor trial status.",
        "is_processed": False,
        "is_demo_data": True,
    },
    {
        "title": "[DEMO] PubMed Metformin+Alzheimer Query — Simulated ingestion result",
        "source_type": "pubmed",
        "abstract": "Simulated PubMed query result for 'metformin AND Alzheimer's disease'.",
        "extracted_drugs": ["Metformin"],
        "extracted_diseases": ["Alzheimer's Disease"],
        "extracted_mechanisms": ["AMPK activation", "mTOR inhibition", "autophagy"],
        "is_processed": True,
        "is_demo_data": True,
    },
    {
        "title": "[DEMO] PubMed Sildenafil+Neurodegeneration Query — Simulated ingestion result",
        "source_type": "pubmed",
        "abstract": "Simulated PubMed query result for 'sildenafil AND neurodegeneration OR Alzheimer'.",
        "extracted_drugs": ["Sildenafil"],
        "extracted_diseases": ["Alzheimer's Disease"],
        "extracted_mechanisms": ["PDE5 inhibition", "cGMP elevation", "tau reduction"],
        "is_processed": True,
        "is_demo_data": True,
    },
]

DEMO_USERS = [
    {
        "email": "researcher@bioarbitrage.demo",
        "username": "demo_researcher",
        "full_name": "Dr. Alex Chen",
        "password": "demo1234",
        "role": "researcher",
        "institution": "BioArbitrage Research Platform",
    },
    {
        "email": "admin@bioarbitrage.demo",
        "username": "demo_admin",
        "full_name": "Admin User",
        "password": "admin1234",
        "role": "admin",
        "institution": "BioArbitrage Research Platform",
    },
]

# Signal trend data for dashboard chart (30 days of demo data)
DEMO_SIGNAL_TREND = [
    {"date": "2024-06-01", "total": 3, "high_confidence": 1},
    {"date": "2024-06-05", "total": 4, "high_confidence": 1},
    {"date": "2024-06-10", "total": 4, "high_confidence": 2},
    {"date": "2024-06-15", "total": 5, "high_confidence": 2},
    {"date": "2024-06-20", "total": 6, "high_confidence": 3},
    {"date": "2024-06-25", "total": 7, "high_confidence": 3},
    {"date": "2024-07-01", "total": 7, "high_confidence": 4},
    {"date": "2024-07-05", "total": 8, "high_confidence": 4},
    {"date": "2024-07-10", "total": 8, "high_confidence": 4},
    {"date": "2024-07-15", "total": 8, "high_confidence": 4},
]


# ─────────────────────────────────────────────────────────────────────────────
# ENRICHED SIGNAL DATA
# Keyed by (drug_name, disease_name) — merged into signals during seeding.
# Contains:
#   • enriched_score_breakdown  — 5-factor transparent scoring
#   • detection_rationale       — structured "how was this detected?" data
#   • relationship_graph        — Drug → Target → Pathway → Disease nodes
#   • pipeline_inputs           — what data entered the detection pipeline
# ─────────────────────────────────────────────────────────────────────────────

SIGNAL_ENRICHMENTS = {
    ("Metformin", "Alzheimer's Disease"): {
        "enriched_score_breakdown": {
            "research_evidence":   {"score": 24, "max": 24, "label": "Research Evidence",   "items": 3},
            "clinical_evidence":   {"score": 20, "max": 20, "label": "Clinical Evidence",   "items": 1},
            "mechanism_match":     {"score": 18, "max": 20, "label": "Mechanism Match",      "items": None},
            "independent_sources": {"score": 12, "max": 12, "label": "Independent Sources", "items": 7},
            "recency":             {"score":  8, "max":  8, "label": "Recency (post-2020)",  "items": 3},
            "total":               {"score": 82, "max": 100, "label": "Total Evidence Score"},
        },
        "detection_rationale": {
            "how_detected": (
                "BioArbitrage cross-referenced Metformin's known molecular targets (AMPK, mTOR pathway) "
                "against the biological pathways dysregulated in Alzheimer's Disease (mTOR signaling, "
                "autophagy pathway, GSK-3 signaling). A strong mechanistic overlap was identified: "
                "AMPK activation by Metformin directly counters mTOR hyperactivation — a key driver "
                "of impaired autophagy and protein aggregate accumulation in Alzheimer's. "
                "This mechanistic link was then corroborated by 3 independent research publications "
                "and 1 clinical trial record, generating a high-confidence signal."
            ),
            "mechanism_summary": "AMPK → mTOR inhibition → Autophagy restoration → Reduced Aβ/tau accumulation",
            "pathway_overlap": ["mTOR signaling", "Autophagy pathway", "AMPK signaling", "GSK-3 signaling"],
            "shared_targets": ["mTOR", "AMPK", "GSK-3beta"],
            "evidence_types_found": ["research_paper", "clinical_trial", "epidemiological"],
            "key_evidence_titles": [
                "AMPK Activation by Metformin Reduces Amyloid-β Accumulation in APP/PS1 Mice [DEMO]",
                "MILES Trial: Metformin In Longevity Study — Cognitive Sub-analysis [DEMO]",
                "Epidemiological Association: Metformin Use and Reduced AD Risk [DEMO]",
            ],
            "research_gaps": [
                "No completed large-scale RCT in AD patients",
                "Optimal dosing for CNS effects unknown",
                "BBB penetration at therapeutic doses requires further study",
            ],
            "validation_required": True,
            "clinical_readiness": "Phase II/III trials ongoing (MILES, TAME) [DEMO]",
        },
        "relationship_graph": {
            "drug_node":     {"label": "Metformin", "type": "drug", "approved_for": "Type 2 Diabetes"},
            "target_nodes":  [
                {"label": "AMPK",      "type": "target", "action": "Activates"},
                {"label": "mTORC1",    "type": "target", "action": "Inhibits (via AMPK)"},
                {"label": "GSK-3beta", "type": "target", "action": "Reduces activity"},
            ],
            "pathway_nodes": [
                {"label": "mTOR signaling pathway",   "type": "pathway", "disease_relevance": "high"},
                {"label": "Autophagy pathway",         "type": "pathway", "disease_relevance": "high"},
                {"label": "Neuroinflammation pathway", "type": "pathway", "disease_relevance": "moderate"},
            ],
            "disease_node":  {"label": "Alzheimer's Disease", "type": "disease", "affected_by": "mTOR hyperactivation, autophagy failure"},
            "evidence_nodes": [
                {"label": "Preclinical (Mouse Model) [DEMO]", "type": "evidence", "strength": "strong"},
                {"label": "Clinical Trial — MILES [DEMO]",     "type": "evidence", "strength": "supportive"},
                {"label": "Epidemiological Cohort [DEMO]",     "type": "evidence", "strength": "moderate"},
            ],
        },
    },

    ("Rapamycin", "Alzheimer's Disease"): {
        "enriched_score_breakdown": {
            "research_evidence":   {"score": 16, "max": 24, "label": "Research Evidence",   "items": 2},
            "clinical_evidence":   {"score":  8, "max": 20, "label": "Clinical Evidence",   "items": 0},
            "mechanism_match":     {"score": 20, "max": 20, "label": "Mechanism Match",      "items": None},
            "independent_sources": {"score": 12, "max": 12, "label": "Independent Sources", "items": 5},
            "recency":             {"score": 12, "max":  8, "label": "Recency (post-2020)",  "items": 2},
            "total":               {"score": 76, "max": 100, "label": "Total Evidence Score"},
        },
        "detection_rationale": {
            "how_detected": (
                "Rapamycin is the gold-standard mTOR inhibitor. BioArbitrage detected a direct target "
                "overlap: mTORC1 hyperactivation is documented in Alzheimer's brain tissue, and "
                "Rapamycin's mechanism directly addresses this. The preclinical evidence from multiple "
                "independent mouse model studies provided strong cross-source corroboration. "
                "The lower clinical evidence score reflects the absence of completed human trials, "
                "which is flagged as a research gap."
            ),
            "mechanism_summary": "mTORC1 inhibition → Autophagy restoration → Reduced Aβ/tau aggregate burden",
            "pathway_overlap": ["mTOR signaling", "Autophagy pathway", "PI3K/Akt/mTOR pathway"],
            "shared_targets": ["mTORC1", "S6K1", "4E-BP1"],
            "evidence_types_found": ["research_paper", "preclinical"],
            "key_evidence_titles": [
                "mTOR Inhibition Reduces Amyloid Burden in Transgenic AD Models [DEMO]",
                "Rapamycin Extends Lifespan and Improves Cognition in AD Mice [DEMO]",
            ],
            "research_gaps": [
                "No human clinical trials completed",
                "Chronic systemic immunosuppression limits long-term use",
                "CNS-targeted formulation needed",
            ],
            "validation_required": True,
            "clinical_readiness": "Pre-clinical stage — no completed human trials [DEMO]",
        },
        "relationship_graph": {
            "drug_node":    {"label": "Rapamycin", "type": "drug", "approved_for": "Organ transplant, LAM"},
            "target_nodes": [
                {"label": "mTORC1",  "type": "target", "action": "Directly inhibits"},
                {"label": "S6K1",    "type": "target", "action": "Suppresses (downstream)"},
                {"label": "4E-BP1",  "type": "target", "action": "Relieves inhibition"},
            ],
            "pathway_nodes": [
                {"label": "mTOR signaling pathway", "type": "pathway", "disease_relevance": "high"},
                {"label": "Autophagy pathway",       "type": "pathway", "disease_relevance": "high"},
            ],
            "disease_node":  {"label": "Alzheimer's Disease", "type": "disease", "affected_by": "mTOR hyperactivation"},
            "evidence_nodes": [
                {"label": "Multiple Mouse Model Studies [DEMO]", "type": "evidence", "strength": "strong"},
                {"label": "Mechanistic In Vitro Studies [DEMO]", "type": "evidence", "strength": "moderate"},
            ],
        },
    },

    ("Sildenafil", "Alzheimer's Disease"): {
        "enriched_score_breakdown": {
            "research_evidence":   {"score": 16, "max": 24, "label": "Research Evidence",   "items": 2},
            "clinical_evidence":   {"score":  8, "max": 20, "label": "Clinical Evidence",   "items": 0},
            "mechanism_match":     {"score": 17, "max": 20, "label": "Mechanism Match",      "items": None},
            "independent_sources": {"score": 12, "max": 12, "label": "Independent Sources", "items": 4},
            "recency":             {"score": 18, "max":  8, "label": "Recency (post-2020)",  "items": 2},
            "total":               {"score": 71, "max": 100, "label": "Total Evidence Score"},
        },
        "detection_rationale": {
            "how_detected": (
                "This signal emerged from a combination of network medicine analysis and a large "
                "real-world observational study. BioArbitrage identified Sildenafil's PDE5-inhibition "
                "mechanism as relevant to Alzheimer's via the cGMP/PKG/GSK-3beta axis — the same "
                "pathway that controls tau phosphorylation. The signal gained high recency weighting "
                "because the key supporting studies were published in 2021. The observational study "
                "finding (69% lower AD incidence) is flagged with a confounding-risk caveat."
            ),
            "mechanism_summary": "PDE5 inhibition → cGMP ↑ → PKG activation → GSK-3beta inactivation → Tau phosphorylation ↓",
            "pathway_overlap": ["cGMP-PKG signaling", "GSK-3 signaling", "Nitric oxide pathway"],
            "shared_targets": ["GSK-3beta", "cGMP pathway"],
            "evidence_types_found": ["research_paper", "observational_study", "network_medicine"],
            "key_evidence_titles": [
                "Network Medicine Integration Identifies Sildenafil as AD Candidate [DEMO]",
                "Real-World Evidence: 69% Lower AD Incidence in Sildenafil Users (n=7.2M) [DEMO]",
            ],
            "research_gaps": [
                "No Phase III RCT evidence",
                "Observational study susceptible to indication bias",
                "Primarily observed in male patients (original indication)",
            ],
            "validation_required": True,
            "clinical_readiness": "Phase II trial planning stage [DEMO]",
        },
        "relationship_graph": {
            "drug_node":    {"label": "Sildenafil", "type": "drug", "approved_for": "Erectile Dysfunction, Pulmonary Arterial Hypertension"},
            "target_nodes": [
                {"label": "PDE5",      "type": "target", "action": "Inhibits"},
                {"label": "cGMP",      "type": "target", "action": "Elevates (via PDE5)"},
                {"label": "GSK-3beta", "type": "target", "action": "Inactivates (via PKG)"},
            ],
            "pathway_nodes": [
                {"label": "cGMP-PKG signaling pathway", "type": "pathway", "disease_relevance": "moderate"},
                {"label": "GSK-3 / Tau phosphorylation", "type": "pathway", "disease_relevance": "high"},
                {"label": "Cerebrovascular pathway",     "type": "pathway", "disease_relevance": "moderate"},
            ],
            "disease_node":  {"label": "Alzheimer's Disease", "type": "disease", "affected_by": "Tau hyperphosphorylation, cerebrovascular dysfunction"},
            "evidence_nodes": [
                {"label": "Network Medicine Study [DEMO]",    "type": "evidence", "strength": "strong"},
                {"label": "Large Observational Study [DEMO]", "type": "evidence", "strength": "moderate"},
            ],
        },
    },

    ("Doxycycline", "Glioblastoma"): {
        "enriched_score_breakdown": {
            "research_evidence":   {"score":  8, "max": 24, "label": "Research Evidence",   "items": 1},
            "clinical_evidence":   {"score":  0, "max": 20, "label": "Clinical Evidence",   "items": 0},
            "mechanism_match":     {"score": 18, "max": 20, "label": "Mechanism Match",      "items": None},
            "independent_sources": {"score":  8, "max": 12, "label": "Independent Sources", "items": 3},
            "recency":             {"score": 16, "max":  8, "label": "Recency (post-2020)",  "items": 1},
            "total":               {"score": 58, "max": 100, "label": "Total Evidence Score"},
        },
        "detection_rationale": {
            "how_detected": (
                "BioArbitrage identified Doxycycline's MMP-inhibitory activity as mechanistically "
                "relevant to Glioblastoma invasion, one of the primary drivers of treatment failure. "
                "Doxycycline inhibits MMP-2 and MMP-9 at concentrations achievable in CNS tissue "
                "(it crosses the blood-brain barrier). A secondary mechanism — mitochondrial biogenesis "
                "inhibition targeting cancer stem cells — was also identified. The low clinical evidence "
                "score reflects the absence of clinical trial data, which is clearly flagged."
            ),
            "mechanism_summary": "MMP-2/9 inhibition → Reduced ECM degradation → Inhibited tumour invasion",
            "pathway_overlap": ["MMP/collagen pathway", "mTOR signaling"],
            "shared_targets": ["MMP-2", "MMP-9", "Mitochondrial Complex I"],
            "evidence_types_found": ["research_paper", "in_vitro"],
            "key_evidence_titles": [
                "Doxycycline Inhibits MMP-2/9 and Reduces GBM Cell Invasion In Vitro [DEMO]",
            ],
            "research_gaps": [
                "No clinical trial data available",
                "In vitro evidence only — no validated animal models",
                "Combination therapy context not studied",
            ],
            "validation_required": True,
            "clinical_readiness": "Pre-clinical / in vitro stage only [DEMO]",
        },
        "relationship_graph": {
            "drug_node":    {"label": "Doxycycline", "type": "drug", "approved_for": "Bacterial Infections, Malaria"},
            "target_nodes": [
                {"label": "MMP-2",                 "type": "target", "action": "Inhibits"},
                {"label": "MMP-9",                 "type": "target", "action": "Inhibits"},
                {"label": "Mitochondrial Complex I","type": "target", "action": "Inhibits (in CSCs)"},
            ],
            "pathway_nodes": [
                {"label": "MMP/ECM degradation pathway", "type": "pathway", "disease_relevance": "high"},
                {"label": "Cancer stem cell pathway",    "type": "pathway", "disease_relevance": "moderate"},
            ],
            "disease_node":  {"label": "Glioblastoma", "type": "disease", "affected_by": "MMP-driven invasion, cancer stem cells"},
            "evidence_nodes": [
                {"label": "In Vitro Invasion Assay [DEMO]", "type": "evidence", "strength": "moderate"},
            ],
        },
    },

    ("Lithium", "Alzheimer's Disease"): {
        "enriched_score_breakdown": {
            "research_evidence":   {"score": 16, "max": 24, "label": "Research Evidence",   "items": 2},
            "clinical_evidence":   {"score": 20, "max": 20, "label": "Clinical Evidence",   "items": 1},
            "mechanism_match":     {"score": 18, "max": 20, "label": "Mechanism Match",      "items": None},
            "independent_sources": {"score": 12, "max": 12, "label": "Independent Sources", "items": 6},
            "recency":             {"score":  8, "max":  8, "label": "Recency (post-2020)",  "items": 2},
            "total":               {"score": 74, "max": 100, "label": "Total Evidence Score"},
        },
        "detection_rationale": {
            "how_detected": (
                "This signal was detected through a target-first approach: GSK-3beta is the primary "
                "tau kinase in Alzheimer's pathology, and Lithium is a well-characterised GSK-3beta "
                "inhibitor. BioArbitrage matched Lithium's known target (GSK-3beta) against the "
                "disease's key pathological mechanism (tau hyperphosphorylation), generating a "
                "direct mechanistic hit. Clinical trial data (Phase II CSF tau reduction) elevated "
                "the score to high-confidence."
            ),
            "mechanism_summary": "GSK-3beta inhibition → Reduced tau phosphorylation → Slower tangle formation",
            "pathway_overlap": ["GSK-3 signaling", "Wnt/beta-catenin pathway", "Tau phosphorylation"],
            "shared_targets": ["GSK-3beta"],
            "evidence_types_found": ["research_paper", "clinical_trial"],
            "key_evidence_titles": [
                "Lithium Reduces CSF Phospho-tau in MCI Patients — Phase II Trial [DEMO]",
                "GSK-3beta Inhibition Prevents Tau Pathology in Animal Models [DEMO]",
            ],
            "research_gaps": [
                "Narrow therapeutic index requires careful monitoring",
                "No large Phase III trial in Alzheimer's completed",
                "Long-term safety in elderly patients requires evaluation",
            ],
            "validation_required": True,
            "clinical_readiness": "Phase II clinical evidence available [DEMO]",
        },
        "relationship_graph": {
            "drug_node":    {"label": "Lithium", "type": "drug", "approved_for": "Bipolar Disorder"},
            "target_nodes": [
                {"label": "GSK-3beta",             "type": "target", "action": "Inhibits (direct + indirect)"},
                {"label": "Inositol monophosphatase","type": "target", "action": "Inhibits"},
            ],
            "pathway_nodes": [
                {"label": "GSK-3 / Tau phosphorylation",  "type": "pathway", "disease_relevance": "high"},
                {"label": "Wnt/beta-catenin pathway",     "type": "pathway", "disease_relevance": "moderate"},
                {"label": "BDNF neuroprotective pathway", "type": "pathway", "disease_relevance": "moderate"},
            ],
            "disease_node":  {"label": "Alzheimer's Disease", "type": "disease", "affected_by": "Tau hyperphosphorylation, neurofibrillary tangles"},
            "evidence_nodes": [
                {"label": "Phase II Clinical Trial [DEMO]",   "type": "evidence", "strength": "strong"},
                {"label": "Preclinical Animal Models [DEMO]", "type": "evidence", "strength": "strong"},
            ],
        },
    },

    ("Metformin", "Triple-Negative Breast Cancer"): {
        "enriched_score_breakdown": {
            "research_evidence":   {"score": 16, "max": 24, "label": "Research Evidence",   "items": 2},
            "clinical_evidence":   {"score": 12, "max": 20, "label": "Clinical Evidence",   "items": 1},
            "mechanism_match":     {"score": 16, "max": 20, "label": "Mechanism Match",      "items": None},
            "independent_sources": {"score": 12, "max": 12, "label": "Independent Sources", "items": 5},
            "recency":             {"score": 12, "max":  8, "label": "Recency (post-2020)",  "items": 2},
            "total":               {"score": 68, "max": 100, "label": "Total Evidence Score"},
        },
        "detection_rationale": {
            "how_detected": (
                "BioArbitrage identified a metabolic vulnerability in TNBC: these tumours frequently "
                "show PI3K/mTOR hyperactivation, which Metformin's AMPK activation directly counters. "
                "The signal was strengthened by epidemiological data showing lower breast cancer "
                "incidence in diabetic patients on Metformin, and by in vitro cell-line studies. "
                "The presence of Phase II clinical trial data elevated this to medium confidence."
            ),
            "mechanism_summary": "AMPK activation → mTORC1 inhibition → Reduced cancer cell proliferation + protein synthesis",
            "pathway_overlap": ["AMPK signaling", "mTOR signaling", "PI3K/Akt pathway"],
            "shared_targets": ["mTOR", "AMPK", "Complex I (mitochondrial)"],
            "evidence_types_found": ["research_paper", "clinical_trial", "epidemiological", "in_vitro"],
            "key_evidence_titles": [
                "Metformin Inhibits TNBC Cell Growth via AMPK/mTOR [DEMO]",
                "Reduced Breast Cancer Incidence in T2DM Patients on Metformin [DEMO]",
            ],
            "research_gaps": [
                "Optimal patient selection criteria unknown",
                "Combination therapy context undefined",
                "Biomarker for Metformin response in TNBC not established",
            ],
            "validation_required": True,
            "clinical_readiness": "Phase II trials completed; Phase III needed [DEMO]",
        },
        "relationship_graph": {
            "drug_node":    {"label": "Metformin", "type": "drug", "approved_for": "Type 2 Diabetes"},
            "target_nodes": [
                {"label": "AMPK",        "type": "target", "action": "Activates"},
                {"label": "mTORC1",      "type": "target", "action": "Inhibits (via AMPK)"},
                {"label": "Complex I",   "type": "target", "action": "Inhibits"},
            ],
            "pathway_nodes": [
                {"label": "PI3K/Akt/mTOR pathway",  "type": "pathway", "disease_relevance": "high"},
                {"label": "AMPK metabolic pathway", "type": "pathway", "disease_relevance": "high"},
            ],
            "disease_node":  {"label": "Triple-Negative Breast Cancer", "type": "disease", "affected_by": "mTOR hyperactivation, metabolic reprogramming"},
            "evidence_nodes": [
                {"label": "In Vitro Cell Studies [DEMO]",   "type": "evidence", "strength": "moderate"},
                {"label": "Epidemiological Cohort [DEMO]",  "type": "evidence", "strength": "moderate"},
                {"label": "Phase II Clinical Trial [DEMO]", "type": "evidence", "strength": "supportive"},
            ],
        },
    },

    ("Naltrexone", "Multiple Sclerosis"): {
        "enriched_score_breakdown": {
            "research_evidence":   {"score":  8, "max": 24, "label": "Research Evidence",   "items": 1},
            "clinical_evidence":   {"score":  8, "max": 20, "label": "Clinical Evidence",   "items": 0},
            "mechanism_match":     {"score": 14, "max": 20, "label": "Mechanism Match",      "items": None},
            "independent_sources": {"score":  8, "max": 12, "label": "Independent Sources", "items": 3},
            "recency":             {"score": 14, "max":  8, "label": "Recency (post-2020)",  "items": 1},
            "total":               {"score": 52, "max": 100, "label": "Total Evidence Score"},
        },
        "detection_rationale": {
            "how_detected": (
                "BioArbitrage detected a plausible mechanism between Low-Dose Naltrexone (LDN) "
                "and Multiple Sclerosis via the TLR4/NF-kB neuroinflammation pathway. At low doses, "
                "Naltrexone acts as a TLR4 antagonist on microglia, the primary neuroinflammatory "
                "cell type in MS. The signal received a LOW confidence rating because available "
                "evidence is limited to small open-label trials and patient registries, with no "
                "completed randomized controlled trial."
            ),
            "mechanism_summary": "TLR4 antagonism → Reduced microglial activation → Lower neuroinflammatory cytokines",
            "pathway_overlap": ["TLR4/NF-kB pathway", "Neuroinflammation pathway"],
            "shared_targets": ["TLR4", "Mu-opioid receptor"],
            "evidence_types_found": ["small_trial", "patient_registry", "observational"],
            "key_evidence_titles": [
                "Low-Dose Naltrexone in MS: Open-Label Safety Study [DEMO]",
                "LDN Patient Registry: Quality-of-Life Reports in MS [DEMO]",
            ],
            "research_gaps": [
                "No completed randomised controlled trial",
                "Optimal dosing for TLR4 effect unclear",
                "Patient selection and responder identification unknown",
            ],
            "validation_required": True,
            "clinical_readiness": "Exploratory / small trial stage only [DEMO]",
        },
        "relationship_graph": {
            "drug_node":    {"label": "Naltrexone (Low Dose)", "type": "drug", "approved_for": "Opioid & Alcohol Use Disorder"},
            "target_nodes": [
                {"label": "TLR4",             "type": "target", "action": "Antagonises (at low dose)"},
                {"label": "Mu-opioid receptor","type": "target", "action": "Transiently blocks"},
            ],
            "pathway_nodes": [
                {"label": "TLR4/NF-kB neuroinflammation", "type": "pathway", "disease_relevance": "moderate"},
                {"label": "Microglial activation pathway", "type": "pathway", "disease_relevance": "moderate"},
            ],
            "disease_node":  {"label": "Multiple Sclerosis", "type": "disease", "affected_by": "Neuroinflammation, demyelination"},
            "evidence_nodes": [
                {"label": "Open-Label Trials [DEMO]",  "type": "evidence", "strength": "weak"},
                {"label": "Patient Registry [DEMO]",   "type": "evidence", "strength": "weak"},
            ],
        },
    },

    ("Rapamycin", "Pancreatic Ductal Adenocarcinoma"): {
        "enriched_score_breakdown": {
            "research_evidence":   {"score":  8, "max": 24, "label": "Research Evidence",   "items": 1},
            "clinical_evidence":   {"score":  8, "max": 20, "label": "Clinical Evidence",   "items": 0},
            "mechanism_match":     {"score": 15, "max": 20, "label": "Mechanism Match",      "items": None},
            "independent_sources": {"score":  8, "max": 12, "label": "Independent Sources", "items": 3},
            "recency":             {"score": 16, "max":  8, "label": "Recency (post-2020)",  "items": 1},
            "total":               {"score": 55, "max": 100, "label": "Total Evidence Score"},
        },
        "detection_rationale": {
            "how_detected": (
                "BioArbitrage flagged an mTOR pathway vulnerability in PDAC based on the known "
                "PI3K/mTOR activation downstream of KRAS. Rapamycin's direct mTOR inhibition "
                "is mechanistically relevant. However, the signal is LOW confidence due to "
                "feedback resistance via KRAS re-activation, and because clinical response to "
                "rapalogs in PDAC has been heterogeneous. This signal requires biomarker "
                "stratification to identify a responsive patient subpopulation."
            ),
            "mechanism_summary": "mTORC1 inhibition → Reduced protein synthesis → Impaired cancer cell growth (subtype-dependent)",
            "pathway_overlap": ["mTOR signaling", "PI3K/Akt pathway", "KRAS signaling"],
            "shared_targets": ["mTORC1", "S6K1"],
            "evidence_types_found": ["research_paper", "rapalog_clinical_data"],
            "key_evidence_titles": [
                "Everolimus (Rapalog) Activity in PDAC Subgroup — Phase II Data [DEMO]",
            ],
            "research_gaps": [
                "KRAS feedback resistance limits response",
                "No biomarker to identify mTOR-dependent PDAC subtype",
                "Combination strategies with KRAS inhibitors need evaluation",
            ],
            "validation_required": True,
            "clinical_readiness": "Early clinical data (rapalogs); no Rapamycin-specific PDAC trial [DEMO]",
        },
        "relationship_graph": {
            "drug_node":    {"label": "Rapamycin", "type": "drug", "approved_for": "Organ transplant, LAM"},
            "target_nodes": [
                {"label": "mTORC1", "type": "target", "action": "Directly inhibits"},
            ],
            "pathway_nodes": [
                {"label": "KRAS → PI3K/mTOR pathway", "type": "pathway", "disease_relevance": "high"},
                {"label": "Autophagy survival pathway", "type": "pathway", "disease_relevance": "complex"},
            ],
            "disease_node":  {"label": "Pancreatic Ductal Adenocarcinoma", "type": "disease", "affected_by": "KRAS/mTOR hyperactivation"},
            "evidence_nodes": [
                {"label": "Rapalog Phase II Data [DEMO]",  "type": "evidence", "strength": "moderate"},
                {"label": "Preclinical PDAC Models [DEMO]","type": "evidence", "strength": "moderate"},
            ],
        },
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# RESEARCH MONITOR — Simulated ingestion pipeline records
# Shows how new research would enter the BioArbitrage detection pipeline.
# ALL data is DEMO/SIMULATED. Clearly labelled.
# ─────────────────────────────────────────────────────────────────────────────

DEMO_RESEARCH_MONITOR = [
    {
        "id": "RM-001",
        "title": "[DEMO] New Preprint: Metformin Reduces Neuroinflammation in 3xTg-AD Mouse Model",
        "source": "bioRxiv",
        "source_type": "preprint",
        "ingested_at": "2024-07-15T09:23:00Z",
        "pipeline_stage": "signal_evaluation",
        "pipeline_status": "complete",
        "extracted_entities": {
            "drugs": ["Metformin"],
            "diseases": ["Alzheimer's Disease"],
            "mechanisms": ["AMPK activation", "neuroinflammation", "NF-kB suppression"],
            "targets": ["AMPK", "NF-kB", "IL-6"],
        },
        "matched_signals": [{"drug": "Metformin", "disease": "Alzheimer's Disease", "score_delta": +2}],
        "evaluation_result": "Corroborates existing Metformin→AD signal. Score updated.",
        "is_demo_data": True,
    },
    {
        "id": "RM-002",
        "title": "[DEMO] ClinicalTrials.gov Update: Sildenafil Phase II AD Trial Registration",
        "source": "ClinicalTrials.gov",
        "source_type": "clinical_trial",
        "ingested_at": "2024-07-10T14:05:00Z",
        "pipeline_stage": "signal_evaluation",
        "pipeline_status": "complete",
        "extracted_entities": {
            "drugs": ["Sildenafil"],
            "diseases": ["Alzheimer's Disease"],
            "mechanisms": ["PDE5 inhibition", "cGMP elevation"],
            "targets": ["PDE5", "GSK-3beta"],
        },
        "matched_signals": [{"drug": "Sildenafil", "disease": "Alzheimer's Disease", "score_delta": +5}],
        "evaluation_result": "New clinical trial registration strengthens Sildenafil→AD signal.",
        "is_demo_data": True,
    },
    {
        "id": "RM-003",
        "title": "[DEMO] PubMed: GSK-3beta Inhibition Reduces Tau in Organoid Model — Relevance to Lithium",
        "source": "PubMed",
        "source_type": "research_paper",
        "ingested_at": "2024-07-08T11:30:00Z",
        "pipeline_stage": "evidence_matching",
        "pipeline_status": "complete",
        "extracted_entities": {
            "drugs": ["Lithium"],
            "diseases": ["Alzheimer's Disease"],
            "mechanisms": ["GSK-3beta inhibition", "tau phosphorylation"],
            "targets": ["GSK-3beta", "tau"],
        },
        "matched_signals": [{"drug": "Lithium", "disease": "Alzheimer's Disease", "score_delta": +3}],
        "evaluation_result": "New organoid evidence corroborates Lithium→AD GSK-3beta mechanism.",
        "is_demo_data": True,
    },
    {
        "id": "RM-004",
        "title": "[DEMO] medRxiv Preprint: Doxycycline MMP Inhibition in GBM Patient Samples",
        "source": "medRxiv",
        "source_type": "preprint",
        "ingested_at": "2024-07-05T08:15:00Z",
        "pipeline_stage": "mechanism_identification",
        "pipeline_status": "complete",
        "extracted_entities": {
            "drugs": ["Doxycycline"],
            "diseases": ["Glioblastoma"],
            "mechanisms": ["MMP inhibition", "invasion"],
            "targets": ["MMP-2", "MMP-9"],
        },
        "matched_signals": [{"drug": "Doxycycline", "disease": "Glioblastoma", "score_delta": +4}],
        "evaluation_result": "New MMP inhibition data in patient samples strengthens novel Doxycycline→GBM signal.",
        "is_demo_data": True,
    },
    {
        "id": "RM-005",
        "title": "[DEMO] PubMed: Rapamycin Improves Cognitive Function in Aged Mice — Updated Meta-analysis",
        "source": "PubMed",
        "source_type": "research_paper",
        "ingested_at": "2024-07-01T16:45:00Z",
        "pipeline_stage": "entity_extraction",
        "pipeline_status": "complete",
        "extracted_entities": {
            "drugs": ["Rapamycin"],
            "diseases": ["Alzheimer's Disease", "Cognitive decline"],
            "mechanisms": ["mTOR inhibition", "autophagy"],
            "targets": ["mTORC1"],
        },
        "matched_signals": [{"drug": "Rapamycin", "disease": "Alzheimer's Disease", "score_delta": +1}],
        "evaluation_result": "Consistent with existing Rapamycin→AD signal. Minor score update.",
        "is_demo_data": True,
    },
]
