"""Generate the fictional request for proposal and three fictional tenders used by the demo and the tests.

Every page is stamped as fictional. The documents follow the structure of a typical
fit-out request for proposal: two lots and a combined offer, four volumes, standard
forms, a deviations form and contract particulars. Each tenderer is built to exercise
different parts of the evaluation:

- Northfield Builders: responsive, complete, one minor deviation, mid-priced.
- Cobalt Ridge Construction: lowest price, but a short validity period, no power of
  attorney, an under-extended item, a reduced provisional sum, front-loaded pricing,
  material contract deviations and an assumption stated outside the deviations form.
- Harbor & Pine Contractors: received after the deadline, a methodology that misses
  several requirements, a programme over the limit, an unsubstantiated rating claim,
  a litigation disclosure, unit rates identical to Cobalt Ridge's, an expired tax certificate,
  turnover below the threshold, words that differ from figures, and a price in the technical tender.

The request for proposal itself contains two deliberate contradictions (tender validity, and the
validity of the tender security), because real tender documents often do, and Evalia should flag
them before the framework is signed off.

Run from the repository root:

    python scripts/make_synthetic_tender.py
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUT = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "synthetic"
STAMP = "FICTIONAL - synthetic test document generated for the Evalia demo. No real project, company or person."
REF = "LG-2026-031"
TITLE = "Lakeshore Grand Hotel, Buildings A and B: Interior Fit-out Works (fictional)"
OWNER = "Lakeshore Development Authority (fictional)"

STYLES = getSampleStyleSheet()
PAGE = landscape(LETTER)

# Bill of quantities issued with the request for proposal: item, description, unit, quantity in lot A, quantity in lot B.
BOQ = [
    ("1", "Preliminaries and general conditions", "LS", 1, 1),
    ("2", "Demolition and strip-out", "SF", 96_000, 64_000),
    ("3", "Partitions, ceilings and finishes", "SF", 96_000, 64_000),
    ("4", "Guest room fit-out, complete", "KEY", 180, 120),
    ("5", "Public area joinery and millwork", "LS", 1, 1),
    ("6", "Mechanical, electrical and plumbing modifications", "LS", 1, 1),
    ("7", "Provisional sum: art, signage and wayfinding", "PS", 1, 1),
]
PROVISIONAL = {"A": 250_000.00, "B": 150_000.00}

REQUIREMENTS = [
    ("ER-01", "Building A remains open to guests while Building B is fitted out; the works shall be phased so that "
              "no guest area of Building A is closed for more than 72 hours."),
    ("ER-02", "A full-scale mock-up guest room shall be built and approved before any guest room installation starts."),
    ("ER-03", "Both buildings shall be complete within 40 weeks of the commencement date."),
    ("ER-04", "Noisy works are restricted to 08:00 to 18:00, Monday to Friday."),
    ("ER-05", "The Contractor shall maintain a BIM model to LOD 300 and deliver an as-built model at completion."),
    ("ER-06", "All fire-stopping shall be inspected and certified by an independent third-party inspector."),
    ("ER-07", "All deliveries shall use the service dock; no deliveries through guest entrances."),
    ("ER-08", "At least 75% of construction waste by weight shall be diverted from landfill."),
]

PARTICULARS = [
    ("Advance payment", "10% of the Contract Price, against an advance payment bond"),
    ("Retention", "10% of each interim payment, released half at completion and half at the end of the defects period"),
    ("Performance bond", "10% of the Contract Price"),
    ("Delay damages", "$15,000 per day, capped at 10% of the Contract Price"),
    ("Defects liability period", "24 months from completion"),
    ("Limit of liability", "100% of the Contract Price"),
    ("Insurance", "Contractor's all-risks insurance with a deductible not exceeding $25,000 per claim"),
    ("Existing conditions", "Risk of existing building conditions rests with the Contractor, who has had access to the surveys"),
]

FORMS = [
    ("Volume 1", "Letter of Tender", "signed by an authorized signatory; tender valid for 90 days"),
    ("Volume 1", "Tender Security", "2% of the Combined Offer, valid for 120 days"),
    ("Volume 1", "Power of Attorney", "for each signatory"),
    ("Volume 1", "Form B - Tenderer Information", ""),
    ("Volume 1", "Form G - Proposed Changes to Tender Requirements", "the only place deviations will be considered"),
    ("Volume 1", "Form O - Litigation and Arbitration", "disclose matters over $5,000,000 in the last three years"),
    ("Volume 1", "Form P - Termination of Contracts", "disclose terminations in the last five years"),
    ("Volume 1", "Form R - Anti-collusion Certificate", "signed"),
    ("Volume 1", "Form S - Conflict of Interest Declaration", ""),
    ("Volume 1", "Site Visit Certificate", "mandatory"),
    ("Volume 2", "Form C - Key Personnel", ""),
    ("Volume 2", "Form D - Plant and Workforce", ""),
    ("Volume 2", "Form T - Technical Data", ""),
    ("Volume 2", "Form E - Programme", ""),
    ("Volume 2", "Form F - Proposed Subcontractors", ""),
    ("Volume 2", "Form H - Methodology", ""),
    ("Volume 2", "Form I - Quality Plan", ""),
    ("Volume 2", "Form J - Health, Safety and Environment Plan", "including the certified Experience Modification Rate"),
    ("Volume 2", "Form K - Relevant Experience", "with the owner's performance evaluation for every project"),
    ("Volume 2", "Form L - BIM Capability", ""),
    ("Volume 3", "Pricing Schedule - Lot A", ""),
    ("Volume 3", "Pricing Schedule - Lot B", ""),
    ("Volume 3", "Combined Offer", ""),
    ("Volume 3", "Cash Flow Forecast", "monthly, for the combined offer"),
]

PLANT = [("Scissor lift", 4), ("Telehandler", 1), ("Goods hoist", 1)]
PERFORMANCE = [("Sound insulation between guest rooms (STC)", "minimum", "55"),
               ("Lighting power density in guest rooms (W/sq ft)", "maximum", "0.9")]
DOSSIER = [("1", "Employer's Requirements", "Section 4"), ("2", "Pricing schedules", "Section 5"),
           ("3", "Contract particulars", "Section 6"), ("4", "Drawings", "Section 9")]
KEY_ROLES = [("Project Manager", 10), ("Site Manager", 8), ("HSE Manager", 5), ("BIM Coordinator", 3)]


@dataclass
class Project:
    name: str
    sector: str
    owner: str
    completed: int
    value: int
    role: str
    claimed_rating: str
    letter_rating: str


@dataclass
class Tenderer:
    key: str
    company: str
    signatory: str
    rates: dict[str, dict[str, float]]          # lot -> item -> rate
    amount_overrides: dict[tuple[str, str], float] = field(default_factory=dict)
    provisional: dict[str, float] = field(default_factory=lambda: dict(PROVISIONAL))
    discount_pct: float = 0.0
    validity_days: int = 120
    power_of_attorney: bool = True
    collusion_signed: bool = True
    emr: float = 0.8
    programme_weeks: int = 38
    methodology: list[str] = field(default_factory=list)
    personnel: list[tuple[str, str, int]] = field(default_factory=list)
    subcontractors: list[tuple[str, str]] = field(default_factory=list)
    deviations: list[tuple[str, str, str, str]] = field(default_factory=list)
    litigation: list[str] = field(default_factory=list)
    terminations: list[str] = field(default_factory=list)
    pricing_note: str = ""
    home_state: str = "State of Lakeshore (fictional)"
    licence: tuple[str, str, str] = ("GB-0000", "Class A", "30 June 2027")
    tax_certificate: tuple[str, str] = ("TC-0000", "31 December 2026")
    turnover: tuple[int, int, int] = (40_000_000, 42_000_000, 45_000_000)
    security: tuple[float, int] = (0.0, 150)
    addenda: str = "Addenda No. 1 and No. 2"
    words: str = ""
    site_visit: bool = True
    plant: list[tuple[str, int, str]] = field(default_factory=list)
    resident_pct: int = 40
    technical_data: tuple[str, str] = ("55", "0.9")
    sales_tax: bool = True
    accounts: str = "2023, 2024, 2025"
    owners: str = ""
    jv: list[tuple[str, str, int]] = field(default_factory=list)
    sub_tax: list[str] = field(default_factory=list)
    cashflow_pct: list[float] = field(default_factory=list)
    projects: list[Project] = field(default_factory=list)


def rates(prelim, strip, finish, room, joinery, mep):
    return {"1": prelim, "2": strip, "3": finish, "4": room, "5": joinery, "6": mep}


TENDERERS = [
    Tenderer(
        key="northfield",
        company="Northfield Builders Inc. (fictional)",
        signatory="Dana Whitlock, President (fictional)",
        rates={"A": rates(780_000, 6.50, 21.00, 26_500, 820_000, 1_950_000),
               "B": rates(540_000, 6.50, 21.00, 26_500, 410_000, 1_050_000)},
        discount_pct=2.0,
        licence=("GB-4471", "Class A", "30 June 2027"),
        tax_certificate=("TC-88213", "31 December 2026"),
        turnover=(44_500_000, 47_200_000, 51_800_000),
        security=(360_000.00, 150),
        words="Seventeen million nine hundred thirty-four thousand dollars",
        plant=[("Scissor lift", 4, "Owned"), ("Telehandler", 1, "Owned"), ("Goods hoist", 1, "Leased")],
        resident_pct=41, technical_data=("56", "0.8"),
        owners="Dana Whitlock (fictional), 60%; Lakeport Capital (fictional), 40%",
        sub_tax=["31 December 2026", "30 September 2027"],
        emr=0.78,
        programme_weeks=38,
        methodology=[
            "We will phase the works so that Building A stays open to guests: Building B is fitted out first, and no guest area of "
            "Building A is closed for more than 48 hours at a time.",
            "A full-scale mock-up guest room will be built in week 3 and submitted for approval before any guest room installation starts.",
            "Noisy works will be limited to 08:00 to 18:00 on weekdays, with quiet works only outside those hours.",
            "We will maintain a federated BIM model to LOD 300 and hand over an as-built model at completion.",
            "Fire-stopping will be inspected and certified by an independent third-party inspector before ceilings are closed.",
            "All deliveries will be booked through the service dock with a delivery management plan.",
            "Our waste management plan targets 80% diversion of construction waste from landfill.",
        ],
        personnel=[("Project Manager", "Laura Brennan (fictional)", 14), ("Site Manager", "Tomas Reyes (fictional)", 11),
                   ("HSE Manager", "Grace Holloway (fictional)", 9), ("BIM Coordinator", "Ken Oduya (fictional)", 6)],
        subcontractors=[("Joinery and millwork", "Birchline Joinery (fictional)"), ("MEP", "Coldwater Mechanical (fictional)")],
        deviations=[("Insurance", "Deductible not exceeding $25,000 per claim",
                     "Deductible not exceeding $50,000 per claim", "Our insurer's standard deductible")],
        cashflow_pct=[4, 8, 11, 13, 14, 14, 13, 11, 8, 4],
        projects=[
            Project("Bayfront Suites Renovation", "hotel fit-out", "Bayfront Hospitality", 2022, 12_400_000, "Prime contractor", "Very Good", "Very Good"),
            Project("Granite Peak Lodge Interiors", "hotel fit-out", "Granite Peak Resorts", 2021, 9_300_000, "Prime contractor", "Satisfactory", "Satisfactory"),
            Project("Harborview Inn Refurbishment", "hotel fit-out", "Harborview Hotels", 2024, 15_800_000, "Prime contractor", "Exceptional", "Exceptional"),
            Project("Maple Court Conference Hotel", "hotel fit-out", "Maple Court Holdings", 2020, 8_600_000, "Prime contractor", "Very Good", "Very Good"),
        ],
    ),
    Tenderer(
        key="cobalt",
        company="Cobalt Ridge Construction LLC (fictional)",
        signatory="Marcus Ellery, Managing Member (fictional)",
        rates={"A": rates(1_250_000, 6.10, 19.40, 24_200, 760_000, 1_880_000),
               "B": rates(860_000, 6.10, 19.40, 24_200, 380_000, 1_190_000)},
        # Lot A item 4: 180 x $24,200.00 = $4,356,000.00, but the schedule states $4,176,000.00.
        amount_overrides={("A", "4"): 4_176_000.00},
        provisional={"A": 150_000.00, "B": 150_000.00},
        discount_pct=1.0,
        home_state="State of Westmoor (fictional)",
        licence=("WB-2290", "Class A", "31 March 2027"),
        tax_certificate=("TC-51907", "30 November 2026"),
        turnover=(36_100_000, 39_400_000, 41_900_000),
        security=(355_000.00, 90),
        addenda="Addendum No. 1",
        words="Seventeen million six hundred two thousand two hundred dollars",
        site_visit=False,
        plant=[("Scissor lift", 3, "Owned"), ("Telehandler", 1, "Leased")],
        resident_pct=33, technical_data=("55", "0.9"), sales_tax=False, accounts="2022, 2023, 2024",
        owners="Marcus Ellery (fictional), 70%; Westmoor Holdings (fictional), 30%",
        sub_tax=["31 March 2027", "31 January 2027"],
        validity_days=90,
        power_of_attorney=False,
        emr=0.95,
        programme_weeks=39,
        methodology=[
            "We will phase the works between the two buildings to suit the hotel's operations.",
            "A mock-up guest room will be provided for approval before guest room installation.",
            "Noisy works will be carried out between 08:00 and 18:00 on weekdays.",
            "We will work in BIM to LOD 300 and deliver an as-built model.",
            "Fire-stopping will be inspected by an independent third-party inspector.",
            "Deliveries will be made through the service dock.",
            "We will divert 75% of construction waste from landfill.",
        ],
        personnel=[("Project Manager", "Owen Pratt (fictional)", 12), ("Site Manager", "Lena Fisk (fictional)", 6),
                   ("HSE Manager", "Raj Malhotra (fictional)", 7)],
        subcontractors=[("Joinery and millwork", "Summit Interiors (fictional)"), ("MEP", "Ridgeway Electrical (fictional)")],
        deviations=[
            ("Delay damages", "$15,000 per day, capped at 10% of the Contract Price",
             "$15,000 per day, capped at 5% of the Contract Price", "To reflect the phased programme risk"),
            ("Limit of liability", "100% of the Contract Price", "50% of the Contract Price", "Company policy"),
        ],
        pricing_note="Our prices assume access to both buildings simultaneously from the commencement date.",
        cashflow_pct=[16, 15, 13, 11, 10, 9, 8, 7, 6, 5],
        projects=[
            Project("Westgate Business Hotel", "hotel fit-out", "Westgate Hospitality", 2020, 10_100_000, "Prime contractor", "Satisfactory", "Satisfactory"),
            Project("Pinecrest Boutique Hotel", "hotel fit-out", "Pinecrest Development", 2023, 7_200_000, "Prime contractor", "Very Good", "Very Good"),
            Project("Summit County Courthouse Interiors", "civic fit-out", "Summit County", 2022, 11_800_000, "Prime contractor", "Satisfactory", "Satisfactory"),
            Project("Bluewater Resort Rooms Upgrade", "hotel fit-out", "Bluewater Resorts", 2025, 13_300_000, "Prime contractor", "Very Good", "Very Good"),
        ],
    ),
    Tenderer(
        key="harborpine",
        company="Harbor & Pine Contractors (fictional)",
        signatory="Priya Natarajan, Chief Executive (fictional)",
        rates={"A": rates(900_000, 6.10, 19.40, 28_900, 980_000, 2_240_000),
               "B": rates(610_000, 6.10, 19.40, 28_900, 495_000, 1_190_000)},
        licence=("GB-3018", "Class A", "31 January 2027"),
        tax_certificate=("TC-60455", "31 August 2026"),
        turnover=(29_800_000, 31_500_000, 33_100_000),
        security=(391_300.00, 150),
        words="Nineteen million five hundred fifty-six thousand dollars",
        plant=[("Scissor lift", 4, "Leased"), ("Telehandler", 1, "Leased"), ("Goods hoist", 1, "Leased")],
        resident_pct=22, technical_data=("50", "0.85"),
        owners="Priya Natarajan (fictional), 55%; Marcus Ellery (fictional), 15%; Pine Street Builders (fictional), 30%",
        jv=[("Harbor Interiors (fictional)", "Lead member", 80), ("Pine Street Builders (fictional)", "Member", 20)],
        sub_tax=["31 March 2027", ""],
        emr=1.12,
        programme_weeks=46,
        methodology=[
            "We will close Building A in stages and complete both buildings in a single sequence to shorten the programme.",
            "Noisy works will be limited to 08:00 to 18:00 on weekdays.",
            "Our BIM coordinator will maintain a model to LOD 300 and deliver an as-built model.",
            "Deliveries will be routed through the service dock.",
            "We will divert 60% of construction waste from landfill.",
            "Our price excludes the removal of any concealed asbestos found behind existing finishes.",
            "Our preliminaries allowance of $610,000.00 for Building B covers the phased handover.",
        ],
        personnel=[("Project Manager", "Carla Jensen (fictional)", 16), ("Site Manager", "Ben Ashworth (fictional)", 9),
                   ("HSE Manager", "Mina Sato (fictional)", 4), ("BIM Coordinator", "Femi Adeyemi (fictional)", 5)],
        subcontractors=[("Joinery and millwork", "Summit Interiors (fictional)"), ("MEP", "Lakeline Services (fictional)")],
        litigation=["Arbitration with Crescent Towers Owner LLC (fictional) over delay to a residential tower; amount in dispute "
                    "$7,400,000; commenced 2025; pending."],
        cashflow_pct=[3, 6, 8, 10, 11, 12, 12, 11, 10, 9, 8],
        projects=[
            Project("Clearwater Harbour Hotel", "hotel fit-out", "Clearwater Hotels", 2021, 11_900_000, "Prime contractor", "Very Good", "Very Good"),
            Project("Ironwood Spa Resort Interiors", "hotel fit-out", "Ironwood Resorts", 2023, 14_250_000, "Prime contractor", "Very Good", "Marginal"),
            Project("Cedar Point Convention Hotel", "hotel fit-out", "Cedar Point Group", 2020, 18_400_000, "Subcontractor (joinery package)", "Satisfactory", "Satisfactory"),
            Project("Silver Lake Lodge Renovation", "hotel fit-out", "Silver Lake Resorts", 2024, 9_600_000, "Prime contractor", "Satisfactory", "Satisfactory"),
            Project("Brookfield Office Campus", "office fit-out", "Brookfield Partners", 2022, 19_000_000, "Prime contractor", "Very Good", "Very Good"),
        ],
    ),
]

# The tender portal's receipt log, recorded by the client at opening (fictional).
RECEIPTS = {"northfield": "2026-09-14T15:42:00", "cobalt": "2026-09-14T16:51:00", "harborpine": "2026-09-14T17:06:00"}
DEADLINE = "14 September 2026 at 17:00"


def money(x: float) -> str:
    return f"${x:,.2f}"


def stamp(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica-Oblique", 7)
    canvas.setFillColor(colors.red)
    canvas.drawString(36, 20, STAMP)
    canvas.drawRightString(PAGE[0] - 36, 20, f"Page {doc.page}")
    canvas.restoreState()


def grid(data, widths):
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def p(text, style="Normal"):
    return Paragraph(text, STYLES[style])


def lot_rows(t: Tenderer, lot: str) -> list[tuple[str, str, str, int, float, float]]:
    rows = []
    for item, desc, unit, qa, qb in BOQ:
        qty = qa if lot == "A" else qb
        rate = t.provisional[lot] if item == "7" else t.rates[lot][item]
        amount = t.amount_overrides.get((lot, item), round(qty * rate, 2))
        rows.append((item, desc, unit, qty, rate, amount))
    return rows


def lot_total(t: Tenderer, lot: str) -> float:
    return round(sum(r[5] for r in lot_rows(t, lot)), 2)


def build_rfp(path: Path) -> None:
    story = [
        p(f"Request for Proposal No. {REF}", "Title"),
        p(TITLE, "Heading2"),
        p(f"Employer: {OWNER}"),
        Spacer(1, 8),
        p("1. The Works", "Heading3"),
        p("Interior fit-out of two hotel buildings: Building A (180 keys) and Building B (120 keys). The Works are tendered "
          "as Lot A (Building A) and Lot B (Building B). Tenderers shall price each lot separately and also submit a Combined "
          "Offer for both lots. The Employer may award either lot separately or both lots together."),
        p("2. Submission", "Heading3"),
        p(f"2.1 Tenders shall be received through the tender portal no later than {DEADLINE} local time. "
          "Tenders received after that time may be rejected at the Employer's discretion."),
        p("2.2 Tenders shall remain valid for 120 days from the submission date. A tender valid for a shorter period shall be "
          "rejected as not substantially responsive."),
        p("2.3 The Letter of Tender shall be signed by an authorized signatory, and a power of attorney shall be provided for "
          "each signatory."),
        p("2.4 Any deviation from the tender requirements shall be stated in Form G only. Deviations or qualifications stated "
          "anywhere else in the tender shall not be considered."),
        p("2.5 The Works shall be valued on a lump-sum basis. The structure of the pricing schedules shall not be changed, and "
          "provisional sums shall be carried at the amounts stated by the Employer."),
        p("2.6 Arithmetic errors. If the stated total of a pricing schedule is lower than the arithmetically corrected sum, the "
          "stated total shall stand and the tenderer shall bear the difference. If the stated total is higher than the corrected "
          "sum, the tender shall be evaluated and accepted at the corrected sum."),
        p("2.7 Tender security. Each tender shall include a tender security of not less than 2% of the Combined Offer, valid "
          "for at least 150 days from the submission date."),
        p("2.8 Addenda. Addenda No. 1 and No. 2 have been issued. The Letter of Tender shall acknowledge every addendum."),
        p("2.9 The Combined Offer shall be stated in words and in figures. If they differ, the amount in words prevails."),
        p("2.10 The technical tender (Volume 2) shall contain no prices."),
        p("2.11 Eligibility. Each tenderer shall hold a General Building Contractor licence, Class A, and a tax clearance "
          "certificate, both valid on the submission date. Average annual turnover over 2023 to 2025 shall be at least 2 times "
          "the Combined Offer."),
        p("2.13 Site visit. Attendance at the site visit is mandatory, and each tender shall include the Site Visit Certificate."),
        p("2.14 Joint ventures and subcontractors. Each member of a joint venture shall hold at least 25% and the lead member at "
          "least 40%. Each named subcontractor shall provide its own tax clearance certificate, valid on the submission date."),
        p("2.15 Prices shall be in US dollars, excluding sales tax, which shall be stated separately on the Combined Offer."),
        p("2.16 Alternative tenders are considered only alongside a compliant base tender."),
        p("2.17 Form H shall not exceed 2 pages. The Employer will not negotiate with tenderers."),
        p("2.18 Audited accounts for 2023 to 2025 shall be provided, and Form B shall name every owner holding 10% or more."),
        p("2.19 Only one tender per tenderer will be considered. A representative attending the opening shall carry a letter of "
          "authority."),
        p("2.12 Domestic preference. For comparison only, the evaluated price of a tenderer not registered in the State of "
          "Lakeshore is increased by 5%."),
        PageBreak(),
        p("3. Tender content", "Heading3"),
        grid([["Volume", "Form", "Requirement"]] + [[v, f, r] for v, f, r in FORMS], [70, 300, 330]),
        PageBreak(),
        p("4. Employer's Requirements (summary)", "Heading3"),
        grid([["Ref", "Requirement"]] + [[r, t] for r, t in REQUIREMENTS], [50, 650]),
        p("4.9 Key personnel. The Tenderer shall name the following key personnel with the minimum years of relevant experience "
          "shown: " + "; ".join(f"{r}, {y} years" for r, y in KEY_ROLES) + "."),
        p("4.10 Minimum plant: " + "; ".join(f"{n}, {q}" for n, q in PLANT) + "."),
        p("4.11 At least 30% of the site workforce shall be resident in the State of Lakeshore."),
        p("4.12 Performance requirements"),
        grid([["Parameter", "Limit", "Value"]] + [list(r) for r in PERFORMANCE], [380, 100, 100]),
        PageBreak(),
        p("5. Pricing schedules", "Heading3"),
        p(f"Provisional sums: Lot A {money(PROVISIONAL['A'])}; Lot B {money(PROVISIONAL['B'])}."),
        grid([["Item", "Description", "Unit", "Quantity Lot A", "Quantity Lot B"]]
             + [[i, d, u, f"{a:,}", f"{b:,}"] for i, d, u, a, b in BOQ], [35, 330, 45, 90, 90]),
        PageBreak(),
        p("6. Contract particulars", "Heading3"),
        grid([["Particular", "Requirement"]] + [[k, v] for k, v in PARTICULARS], [160, 540]),
        PageBreak(),
        p("7. Evaluation", "Heading3"),
        p("7.1 Only substantially responsive tenders will be evaluated. A substantially responsive tender conforms to all the "
          "terms, conditions and requirements of this Request for Proposal without material deviation or reservation."),
        p("7.2 Responsive tenders will be scored out of 100 points: Technical 40 points; Commercial 50 points; Contract 10 points."),
        p("7.3 Technical (40 points): quality of submission 5; methodology 10; programme 5; health and safety 5; relevant "
          "experience 10; key personnel 5."),
        p("7.4 Commercial (50 points): the lowest evaluated price receives 50 points; other tenders receive 50 points multiplied "
          "by the lowest evaluated price divided by their own evaluated price. The evaluated price is the Combined Offer, "
          "corrected under clause 2.6 and normalised for any change to provisional sums."),
        p("7.5 Contract (10 points): 10 points less deductions for deviations from the contract particulars, according to their "
          "materiality."),
        p("7.6 Relevant experience: 2.5 points for each hotel fit-out project completed between 2019 and 2026 with a contract "
          "value of at least $8,000,000, an owner performance rating of Satisfactory or better, and performed as prime "
          "contractor; at most four projects are counted."),
        p("7.7 Technical threshold. A tender scoring fewer than 24 of the 40 technical points, or fewer than 4 points for "
          "methodology, is technically non-compliant and its commercial tender is not evaluated."),
        p("7.8 Award. The Employer will notify all tenderers of its decision and will not sign the Contract until a standstill "
          "period of 10 days has passed."),
        PageBreak(),
        p("8. Tender dossier", "Heading3"),
        grid([["Annex", "Title", "Where"]] + [list(r) for r in DOSSIER], [60, 300, 200]),
    ]
    SimpleDocTemplate(str(path), pagesize=PAGE, title=f"RFP {REF}").build(story, onFirstPage=stamp, onLaterPages=stamp)


def build_tender(t: Tenderer, path: Path) -> None:
    a, b = lot_total(t, "A"), lot_total(t, "B")
    combined = round((a + b) * (1 - t.discount_pct / 100), 2)
    sched = lambda lot: grid(  # noqa: E731
        [["Item", "Description", "Unit", "Quantity", "Rate", "Amount"]]
        + [[i, d, u, f"{q:,}", money(r), money(amt)] for i, d, u, q, r, amt in lot_rows(t, lot)]
        + [["", f"Total Lot {lot}", "", "", "", money(lot_total(t, lot))]],
        [35, 300, 45, 70, 110, 120])
    story = [
        p("Volume 1: Letter of Tender", "Title"),
        p(f"Request for Proposal No. {REF} - {TITLE}"),
        p(f"Tenderer: {t.company}"),
        p(f"We offer to execute the Works for the Combined Offer of {money(combined)}, or for Lot A at {money(a)} and Lot B at "
          f"{money(b)}."),
        p(f"Combined Offer in words: {t.words}."),
        p(f"We acknowledge {t.addenda}."),
        p(f"This tender remains valid for {t.validity_days} days from the submission date."),
        p(f"Signed: {t.signatory}"),
    ]
    if t.power_of_attorney:
        story += [PageBreak(), p("Power of Attorney", "Heading2"),
                  p(f"The board of {t.company} authorizes {t.signatory.split(',')[0]} to sign this tender and the Contract.")]
    story += [
        PageBreak(), p("Tender Security", "Heading2"),
        p("Issued by: First Harbor Bank (fictional)"),
        p(f"Amount: {money(t.security[0])}"),
        p(f"This security is valid for {t.security[1]} days from the submission date."),
    ]
    if t.site_visit:
        story += [PageBreak(), p("Site Visit Certificate", "Heading2"),
                  p(f"This certifies that a representative of {t.company} attended the site visit on 20 August 2026 (fictional).")]
    story += [
        PageBreak(), p("Form B - Tenderer Information", "Heading2"),
        p(f"Legal name: {t.company}"), p(f"Registered in: {t.home_state}"),
        grid([["Registration", "Number", "Class", "Valid until"],
              ["General Building Contractor licence", t.licence[0], t.licence[1], t.licence[2]],
              ["Tax clearance certificate", t.tax_certificate[0], "", t.tax_certificate[1]]], [220, 100, 80, 120]),
        grid([["Year", "Annual turnover"]] + [[str(y), money(v)] for y, v in zip((2023, 2024, 2025), t.turnover)], [80, 160]),
        p(f"Audited accounts provided for: {t.accounts}."),
        p(f"Owners holding 10% or more: {t.owners}."),
        *([p("Joint venture members"), grid([["Member", "Role", "Share"]] + [[n, r, f"{pc}%"] for n, r, pc in t.jv], [220, 120, 80])]
          if t.jv else []),
        PageBreak(), p("Form G - Proposed Changes to Tender Requirements", "Heading2"),
        grid([["No.", "Particular", "Tender requirement", "Proposed change", "Reason"]]
             + ([[str(n), *d] for n, d in enumerate(t.deviations, 1)] or [["", "None", "", "", ""]]),
             [30, 110, 200, 200, 160]),
        PageBreak(), p("Form O - Litigation and Arbitration", "Heading2"),
        p(t.litigation[0] if t.litigation else "No litigation or arbitration over $5,000,000 in the last three years."),
        PageBreak(), p("Form P - Termination of Contracts", "Heading2"),
        p(t.terminations[0] if t.terminations else "No contract has been terminated in the last five years."),
        PageBreak(), p("Form R - Anti-collusion Certificate", "Heading2"),
        p("We certify that this tender was prepared independently and without consultation with any other tenderer."),
        p(f"Signed: {t.signatory}" if t.collusion_signed else "Signed:"),
        PageBreak(), p("Form S - Conflict of Interest Declaration", "Heading2"),
        p("We declare no conflict of interest with the Employer or its advisers."),
        PageBreak(), p("Volume 2: Technical Tender", "Title"),
        p("Form C - Key Personnel", "Heading2"),
        grid([["Role", "Name", "Years of relevant experience"]] + [[r, n, str(y)] for r, n, y in t.personnel], [160, 260, 180]),
        p("Form E - Programme", "Heading2"),
        p(f"Total programme duration for both buildings: {t.programme_weeks} weeks from the commencement date."),
        p("Form F - Proposed Subcontractors", "Heading2"),
        grid([["Package", "Subcontractor", "Tax clearance valid until"]]
             + [[pk, nm, tx] for (pk, nm), tx in zip(t.subcontractors, t.sub_tax)], [200, 260, 160]),
        PageBreak(), p("Form D - Plant and Workforce", "Heading2"),
        grid([["Item", "Quantity", "Owned or leased"]] + [[n, str(q), o] for n, q, o in t.plant], [200, 100, 140]),
        p(f"Site workforce resident in the State of Lakeshore: {t.resident_pct}%"),
        p("Form T - Technical Data", "Heading2"),
        grid([["Parameter", "Offered"], [PERFORMANCE[0][0], t.technical_data[0]], [PERFORMANCE[1][0], t.technical_data[1]]], [380, 100]),
        PageBreak(), p("Form H - Methodology", "Heading2"),
        *[p(f"H.{n} {s}") for n, s in enumerate(t.methodology, 1)],
        PageBreak(), p("Form I - Quality Plan", "Heading2"),
        p("Our quality plan follows our certified quality management system, with inspection and test plans for each trade."),
        p("Form J - Health, Safety and Environment Plan", "Heading2"),
        p(f"The insurance carrier certifies that the current Experience Modification Rate of {t.company} is {t.emr:.2f}."),
        p("Form L - BIM Capability", "Heading2"),
        p("We have delivered BIM projects to LOD 300 with a dedicated coordinator."),
        PageBreak(), p("Form K - Relevant Experience", "Heading2"),
        grid([["No.", "Project", "Sector", "Owner", "Completed", "Contract value", "Role", "Owner rating"]]
             + [[str(n), pr.name, pr.sector, pr.owner, str(pr.completed), money(pr.value), pr.role, pr.claimed_rating]
                for n, pr in enumerate(t.projects, 1)],
             [24, 160, 75, 120, 52, 85, 140, 60]),
    ]
    for pr in t.projects:
        story += [PageBreak(), p("Owner Performance Evaluation", "Heading2"), p(f"Project: {pr.name}"),
                  p(f"Owner: {pr.owner} (fictional)"), p(f"Contractor evaluated: {t.company}"),
                  p(f"Year of completion: {pr.completed}"), p(f"Overall performance rating: {pr.letter_rating}")]
    story += [PageBreak(), p("Volume 3: Commercial Tender", "Title")]
    if t.pricing_note:
        story.append(p(f"Pricing note: {t.pricing_note}"))
    story += [p("Pricing Schedule - Lot A", "Heading2"), sched("A"),
              PageBreak(), p("Pricing Schedule - Lot B", "Heading2"), sched("B"),
              PageBreak(), p("Combined Offer", "Heading2"),
              p(f"Sum of Lot A and Lot B: {money(a + b)}"),
              p(f"Discount for award of both lots: {t.discount_pct:g}%"),
              p(f"Combined Offer: {money(combined)}"),
              *([p(f"Sales tax at 6%, stated separately: {money(round(combined * 0.06, 2))}")] if t.sales_tax else []),
              p("Cash Flow Forecast", "Heading2"),
              grid([["Month", *[str(m) for m in range(1, len(t.cashflow_pct) + 1)]],
                    ["Amount", *[f"{round(combined * pct / 100):,}" for pct in t.cashflow_pct]]],
                   [50] + [60] * len(t.cashflow_pct))]
    SimpleDocTemplate(str(path), pagesize=PAGE, title=f"Tender - {t.company}").build(story, onFirstPage=stamp, onLaterPages=stamp)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.pdf"):
        old.unlink()
    build_rfp(OUT / f"rfp_{REF}.pdf")
    for t in TENDERERS:
        build_tender(t, OUT / f"tender_{t.key}.pdf")
    (OUT / "receipts.yaml").write_text(
        "# Tender portal receipt log, recorded by the client at opening (fictional).\n"
        f"deadline: '2026-09-14T17:00:00'\n" + "".join(f"{k}: '{v}'\n" for k, v in RECEIPTS.items())
        + "# What the opening panel recorded for each tender.\nopening:\n"
        + "".join(f"  {k}: {{envelopes: 1, letter_of_authority: true}}\n" for k in RECEIPTS))
    print(f"Wrote {len(TENDERERS) + 1} fictional documents and the receipt log to {OUT}")


if __name__ == "__main__":
    main()
