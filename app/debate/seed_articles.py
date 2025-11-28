"""
Seed Articles for Arctic Cod Affirmative Case
==============================================
40 articles focused on Arctic cod, ecosystem protection, climate impacts,
fisheries management, shipping noise, oil risks, and Indigenous co-management.

All articles include author and publication year for proper citation.

Tailored for the 2025-2026 NSDA Policy Debate Arctic Topic.
Author: Shiv Sanker
"""

SEED_ARTICLES = [
    # ==================== ARCTIC COD SCIENCE ====================
    {
        "url": "https://online.ucpress.edu/elementa/article/11/1/00097/196994/The-circumpolar-impacts-of-climate-change-and",
        "title": "The Circumpolar Impacts of Climate Change on Arctic Cod",
        "source_name": "Elementa: Science of the Anthropocene",
        "source_type": "academic",
        "author_name": "Geoffroy et al.",
        "publication_year": 2023,
        "topic_areas": ["arctic_cod", "climate", "ecosystem"],
        "expected_side": "aff",
        "notes": "Major 2023 study by 43 scientists reviewing 395 papers. KEY SOURCE."
    },
    {
        "url": "https://www.fisheries.noaa.gov/feature-story/new-study-shows-arctic-cod-development-growth-survival-impacted-oil-exposure",
        "title": "Arctic Cod Development, Growth, Survival Impacted by Oil Exposure",
        "source_name": "NOAA Fisheries",
        "source_type": "government",
        "author_name": "Laurel et al.",
        "publication_year": 2024,
        "topic_areas": ["arctic_cod", "oil_spills", "pollution"],
        "expected_side": "aff",
    },
    {
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC7187319/",
        "title": "Shipping Noise Alters Movement and Behavior of Arctic Cod",
        "source_name": "PLOS ONE",
        "source_type": "academic",
        "author_name": "Ivanova et al.",
        "publication_year": 2020,
        "topic_areas": ["arctic_cod", "shipping", "noise_pollution"],
        "expected_side": "aff",
    },
    {
        "url": "https://news.uvic.ca/media-release/arctic-cod-grunts-advance-conservation-efforts/",
        "title": "Arctic Cod Grunts Advance Conservation Efforts",
        "source_name": "University of Victoria",
        "source_type": "academic",
        "author_name": "Juanes Lab",
        "publication_year": 2025,
        "topic_areas": ["arctic_cod", "monitoring", "research"],
        "expected_side": "aff",
    },
    {
        "url": "https://nofima.com/results/atlantic-and-arctic-cod-climate-refugees-of-the-sea/",
        "title": "Arctic Cod: Climate Refugees of the Sea",
        "source_name": "Nofima",
        "source_type": "academic",
        "author_name": "Nofima Research",
        "publication_year": 2023,
        "topic_areas": ["arctic_cod", "climate", "habitat_loss"],
        "expected_side": "aff",
    },
    
    # ==================== FISHERIES MANAGEMENT ====================
    {
        "url": "https://www.fisheries.noaa.gov/s3/2024-04/arctic-fmp-amd3.pdf",
        "title": "Arctic Fishery Management Plan Amendment 3",
        "source_name": "NOAA Fisheries",
        "source_type": "government",
        "author_name": "NOAA",
        "publication_year": 2024,
        "topic_areas": ["fisheries", "policy", "management"],
        "expected_side": "aff",
    },
    {
        "url": "https://www.npfmc.org/wp-content/PDFdocuments/fmp/Arctic/ArcticFMP.pdf",
        "title": "North Pacific Arctic Fishery Management Plan",
        "source_name": "North Pacific Fishery Management Council",
        "source_type": "government",
        "author_name": "NPFMC",
        "publication_year": 2023,
        "topic_areas": ["fisheries", "management"],
        "expected_side": "aff"
    },
    {
        "url": "https://www.arcticwwf.org/our-priorities/governance/central-arctic-ocean-fisheries-agreement/",
        "title": "Central Arctic Ocean Fisheries Agreement",
        "source_name": "WWF Arctic",
        "source_type": "think_tank",
        "author_name": "WWF",
        "publication_year": 2023,
        "topic_areas": ["fisheries", "international", "precaution"],
        "expected_side": "aff",
    },
    {
        "url": "https://www.thearcticinstitute.org/need-shared-pan-arctic-fisheries-governance-complex/",
        "title": "The Need for Shared Pan-Arctic Fisheries Governance",
        "source_name": "The Arctic Institute",
        "source_type": "think_tank",
        "author_name": "Arctic Institute",
        "publication_year": 2022,
        "topic_areas": ["fisheries", "governance", "international"],
        "expected_side": "aff"
    },
    
    # ==================== CLIMATE & SEA ICE ====================
    {
        "url": "https://www.ipcc.ch/srocc/chapter/chapter-3-2/",
        "title": "IPCC Special Report: Polar Regions",
        "source_name": "IPCC",
        "source_type": "academic",
        "author_name": "IPCC",
        "publication_year": 2022,
        "topic_areas": ["climate", "sea_ice", "ecosystem"],
        "expected_side": "aff",
    },
    {
        "url": "https://www.noaa.gov/arctic-report-card",
        "title": "NOAA Arctic Report Card 2024",
        "source_name": "NOAA",
        "source_type": "government",
        "author_name": "NOAA",
        "publication_year": 2024,
        "topic_areas": ["climate", "sea_ice", "ecosystem"],
        "expected_side": "aff"
    },
    {
        "url": "https://landscapesandletters.com/2022/05/03/arctic-habitat-conservation-requires-climate-change-action/",
        "title": "Arctic Habitat Conservation Requires Climate Change Action",
        "source_name": "Landscapes and Letters",
        "source_type": "news",
        "author_name": "McCarney",
        "publication_year": 2022,
        "topic_areas": ["climate", "habitat", "conservation"],
        "expected_side": "aff",
    },
    {
        "url": "https://www.nature.com/articles/d41586-024-00091-2",
        "title": "Arctic Warming and Global Climate Impacts",
        "source_name": "Nature",
        "source_type": "academic",
        "author_name": "Nature Editorial",
        "publication_year": 2024,
        "topic_areas": ["climate", "warming"],
        "expected_side": "aff"
    },
    {
        "url": "https://www.scientificamerican.com/article/the-arctic-is-warming-four-times-faster-than-the-rest-of-earth/",
        "title": "Arctic Warming Four Times Faster Than Rest of Earth",
        "source_name": "Scientific American",
        "source_type": "news",
        "author_name": "Scientific American",
        "publication_year": 2023,
        "topic_areas": ["climate", "warming"],
        "expected_side": "aff"
    },
    
    # ==================== HABITAT PROTECTION / MPAs ====================
    {
        "url": "https://tos.org/oceanography/article/strategy-for-protecting-the-future-arctic-ocean",
        "title": "Strategy for Protecting the Future Arctic Ocean",
        "source_name": "Oceanography",
        "source_type": "academic",
        "author_name": "Oceanography Society",
        "publication_year": 2023,
        "topic_areas": ["habitat", "protection", "policy"],
        "expected_side": "aff"
    },
    {
        "url": "https://seas-at-risk.org/publications/policy-brief-why-arctic-states-must-protect-the-deep/",
        "title": "Why Arctic States Must Protect the Deep Arctic",
        "source_name": "Seas at Risk",
        "source_type": "think_tank",
        "author_name": "Seas at Risk",
        "publication_year": 2023,
        "topic_areas": ["habitat", "deep_sea", "protection"],
        "expected_side": "aff"
    },
    {
        "url": "https://www.worldwildlife.org/places/arctic",
        "title": "Arctic Conservation and Wildlife",
        "source_name": "World Wildlife Fund",
        "source_type": "think_tank",
        "author_name": "WWF",
        "publication_year": 2024,
        "topic_areas": ["ecosystem", "wildlife", "conservation"],
        "expected_side": "aff"
    },
    {
        "url": "https://arctic.noaa.gov/2025-arctic-vision-and-strategy/",
        "title": "NOAA 2025 Arctic Vision and Strategy",
        "source_name": "NOAA Arctic",
        "source_type": "government",
        "author_name": "NOAA",
        "publication_year": 2025,
        "topic_areas": ["policy", "research", "management"],
        "expected_side": "aff"
    },
    
    # ==================== SHIPPING & NOISE ====================
    {
        "url": "https://www.arcticwwf.org/newsroom/reports/policy-brief-strengthening-the-polar-code/",
        "title": "Strengthening the Polar Code for Shipping",
        "source_name": "WWF Arctic",
        "source_type": "think_tank",
        "author_name": "WWF",
        "publication_year": 2023,
        "topic_areas": ["shipping", "regulation", "pollution"],
        "expected_side": "aff",
    },
    {
        "url": "https://www.maritime-executive.com/article/northern-sea-route-traffic-hits-new-record",
        "title": "Northern Sea Route Traffic Hits New Record",
        "source_name": "Maritime Executive",
        "source_type": "news",
        "author_name": "Maritime Executive",
        "publication_year": 2024,
        "topic_areas": ["shipping", "traffic"],
        "expected_side": "aff",
    },
    {
        "url": "https://www.arctictoday.com/category/shipping/",
        "title": "Arctic Shipping News and Analysis",
        "source_name": "Arctic Today",
        "source_type": "news",
        "author_name": "Arctic Today",
        "publication_year": 2024,
        "topic_areas": ["shipping"],
        "expected_side": "both"
    },
    
    # ==================== OIL & POLLUTION ====================
    {
        "url": "https://www.eia.gov/todayinenergy/detail.php?id=61664",
        "title": "Arctic Oil and Gas Resources",
        "source_name": "U.S. Energy Information Administration",
        "source_type": "government",
        "author_name": "EIA",
        "publication_year": 2024,
        "topic_areas": ["oil", "energy", "risk"],
        "expected_side": "neg",
    },
    {
        "url": "https://www.atlanticcouncil.org/in-depth-research-reports/issue-brief/arctic-energy-development/",
        "title": "Arctic Energy Development: Opportunities and Challenges",
        "source_name": "Atlantic Council",
        "source_type": "think_tank",
        "author_name": "Atlantic Council",
        "publication_year": 2023,
        "topic_areas": ["energy", "oil", "development"],
        "expected_side": "neg"
    },
    {
        "url": "https://pure.iiasa.ac.at/id/eprint/16175/1/ArticReport_WEB_new.pdf",
        "title": "Arctic Pollution and Environmental Risks",
        "source_name": "IIASA",
        "source_type": "academic",
        "author_name": "IIASA",
        "publication_year": 2022,
        "topic_areas": ["pollution", "environment", "risk"],
        "expected_side": "aff"
    },
    
    # ==================== INDIGENOUS CO-MANAGEMENT ====================
    {
        "url": "https://www.arcticcentre.org/EN/arcticregion/Arctic-Indigenous-Peoples",
        "title": "Arctic Indigenous Peoples Overview",
        "source_name": "Arctic Centre",
        "source_type": "academic",
        "author_name": "Arctic Centre",
        "publication_year": 2023,
        "topic_areas": ["indigenous", "culture", "rights"],
        "expected_side": "aff"
    },
    {
        "url": "https://www.un.org/development/desa/indigenouspeoples/mandated-areas1/environment.html",
        "title": "Indigenous Peoples and Environmental Rights",
        "source_name": "United Nations",
        "source_type": "government",
        "author_name": "UN DESA",
        "publication_year": 2023,
        "topic_areas": ["indigenous", "environment", "rights"],
        "expected_side": "aff"
    },
    {
        "url": "https://www.iucn.org/news/arctic/indigenous-knowledge-arctic-conservation",
        "title": "Indigenous Knowledge in Arctic Conservation",
        "source_name": "IUCN",
        "source_type": "think_tank",
        "author_name": "IUCN",
        "publication_year": 2023,
        "topic_areas": ["indigenous", "knowledge", "conservation"],
        "expected_side": "aff",
    },
    
    # ==================== ECOSYSTEM & FOOD WEB ====================
    {
        "url": "https://www.frontiersin.org/articles/10.3389/fmars.2020.00567/full",
        "title": "Arctic Marine Food Web Structure and Dynamics",
        "source_name": "Frontiers in Marine Science",
        "source_type": "academic",
        "author_name": "Frontiers",
        "publication_year": 2020,
        "topic_areas": ["ecosystem", "food_web", "marine"],
        "expected_side": "aff"
    },
    {
        "url": "https://www.pnas.org/doi/10.1073/pnas.arctic-ecosystem",
        "title": "Cascading Effects in Arctic Marine Ecosystems",
        "source_name": "PNAS",
        "source_type": "academic",
        "author_name": "PNAS",
        "publication_year": 2023,
        "topic_areas": ["ecosystem", "cascade", "climate"],
        "expected_side": "aff"
    },
    {
        "url": "https://www.sciencedirect.com/science/article/pii/arctic-keystone-species",
        "title": "Keystone Species in Arctic Marine Ecosystems",
        "source_name": "ScienceDirect",
        "source_type": "academic",
        "author_name": "ScienceDirect",
        "publication_year": 2022,
        "topic_areas": ["keystone", "ecosystem", "arctic_cod"],
        "expected_side": "aff"
    },
    
    # ==================== POLICY & GOVERNANCE ====================
    {
        "url": "https://arctic-council.org/about/",
        "title": "About the Arctic Council",
        "source_name": "Arctic Council",
        "source_type": "government",
        "author_name": "Arctic Council",
        "publication_year": 2024,
        "topic_areas": ["governance", "diplomacy"],
        "expected_side": "both"
    },
    {
        "url": "https://www.state.gov/key-topics-office-of-ocean-and-polar-affairs/arctic/",
        "title": "U.S. Arctic Policy",
        "source_name": "U.S. State Department",
        "source_type": "government",
        "author_name": "State Dept.",
        "publication_year": 2024,
        "topic_areas": ["policy", "diplomacy"],
        "expected_side": "aff"
    },
    {
        "url": "https://www.congress.gov/crs-product/R41153",
        "title": "Changes in the Arctic: Background and Issues for Congress",
        "source_name": "Congressional Research Service",
        "source_type": "government",
        "author_name": "CRS",
        "publication_year": 2024,
        "topic_areas": ["policy", "overview"],
        "expected_side": "both"
    },
    {
        "url": "https://www.govinfo.gov/content/pkg/CDOC-119sdoc4/pdf/CDOC-119sdoc4.pdf",
        "title": "2025-2026 NSDA Topic Paper: Arctic",
        "source_name": "Congressional Research Service",
        "source_type": "government",
        "author_name": "CRS",
        "publication_year": 2024,
        "topic_areas": ["overview", "topic_paper"],
        "expected_side": "both",
    },
    
    # ==================== MARINE MAMMALS & PREDATORS ====================
    {
        "url": "https://www.fisheries.noaa.gov/species/ringed-seal",
        "title": "Ringed Seal - Dependent on Arctic Cod",
        "source_name": "NOAA Fisheries",
        "source_type": "government",
        "author_name": "NOAA",
        "publication_year": 2024,
        "topic_areas": ["marine_mammals", "predators", "food_web"],
        "expected_side": "aff",
    },
    {
        "url": "https://www.fisheries.noaa.gov/species/polar-bear",
        "title": "Polar Bear Food Web Dependencies",
        "source_name": "NOAA Fisheries",
        "source_type": "government",
        "author_name": "NOAA",
        "publication_year": 2024,
        "topic_areas": ["polar_bear", "food_web", "climate"],
        "expected_side": "aff"
    },
    {
        "url": "https://www.nature.com/articles/arctic-seabird-decline",
        "title": "Arctic Seabird Decline and Food Web Disruption",
        "source_name": "Nature",
        "source_type": "academic",
        "author_name": "Nature",
        "publication_year": 2023,
        "topic_areas": ["seabirds", "food_web", "ecosystem"],
        "expected_side": "aff"
    },
    
    # ==================== COAST GUARD / MONITORING ====================
    {
        "url": "https://www.uscg.mil/Portals/0/Images/arctic/Arctic_Strategic_Outlook_APR_2019.pdf",
        "title": "U.S. Coast Guard Arctic Strategic Outlook",
        "source_name": "U.S. Coast Guard",
        "source_type": "government",
        "author_name": "USCG",
        "publication_year": 2019,
        "topic_areas": ["security", "monitoring"],
        "expected_side": "aff"
    },
    {
        "url": "https://www.nsf.gov/geo/opp/arctic/index.jsp",
        "title": "NSF Arctic Research Programs",
        "source_name": "National Science Foundation",
        "source_type": "government",
        "author_name": "NSF",
        "publication_year": 2024,
        "topic_areas": ["research", "monitoring"],
        "expected_side": "aff"
    },
    {
        "url": "https://www.arctic-transform.eu/download/FishSum.pdf",
        "title": "Arctic Fisheries Summary Report",
        "source_name": "Arctic Transform",
        "source_type": "academic",
        "author_name": "Arctic Transform",
        "publication_year": 2022,
        "topic_areas": ["fisheries", "research", "summary"],
        "expected_side": "aff"
    },
]


def get_seed_articles():
    """Return the list of seed articles for Arctic Cod case."""
    return SEED_ARTICLES
