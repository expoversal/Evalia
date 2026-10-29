"""Generate the fictional tender and three fictional bids used by the demo and the tests.

Every page is stamped as fictional. The bids are built so that each one shows a
different kind of finding:

- Northfield Builders: compliant, four qualifying projects.
- Cobalt Ridge Construction: no bid bond, an extension error in the bid schedule,
  and two projects that fail the value or date rules.
- Harbor & Pine Contractors: one project performed as a subcontractor, and one
  project whose claimed rating the owner's own evaluation contradicts.

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
TENDER_REF = "RC-2026-014"
TENDER_TITLE = "Riverbend County Light-Industrial Facility (fictional)"

STYLES = getSampleStyleSheet()
PAGE = landscape(LETTER)


@dataclass
class Project:
    name: str
    building_type: str
    owner: str
    completed: int
    value: int
    role: str
    claimed_rating: str
    letter_rating: str


@dataclass
class Bid:
    key: str
    company: str
    signatory: str
    emr: float
    bond: bool
    schedule: list[tuple[str, str, str, int, float, float]]
    projects: list[Project] = field(default_factory=list)


SCHEDULE_ITEMS = [
    ("1", "Site preparation and earthworks", "CY", 4800),
    ("2", "Concrete foundations and slab on grade", "CY", 1200),
    ("3", "Structural steel frame, furnished and erected", "TON", 410),
    ("4", "Insulated metal wall and roof panels", "SF", 52000),
    ("5", "Mechanical, electrical and plumbing systems", "LS", 1),
]


def schedule(rates: list[float], overrides: dict[str, float] | None = None):
    rows = []
    for (item, desc, unit, qty), rate in zip(SCHEDULE_ITEMS, rates):
        amount = round(qty * rate, 2)
        if overrides and item in overrides:
            amount = overrides[item]
        rows.append((item, desc, unit, qty, rate, amount))
    return rows


BIDS = [
    Bid(
        key="northfield",
        company="Northfield Builders Inc. (fictional)",
        signatory="Dana Whitlock, President (fictional)",
        emr=0.78,
        bond=True,
        schedule=schedule([18.50, 410.00, 4150.00, 31.25, 2985000.00]),
        projects=[
            Project("Elm Street Distribution Center", "warehouse", "Lakeport Logistics LLC", 2021, 14_600_000, "Prime contractor", "Very Good", "Very Good"),
            Project("Granite Valley Cold Storage Facility", "industrial building", "Granite Valley Foods", 2022, 12_250_000, "Prime contractor", "Satisfactory", "Satisfactory"),
            Project("Maple Ridge Light Manufacturing Plant", "industrial building", "Maple Ridge Components", 2019, 18_900_000, "Prime contractor", "Exceptional", "Exceptional"),
            Project("Harborview Regional Parts Warehouse", "warehouse", "Harborview Auto Group", 2024, 11_400_000, "Prime contractor", "Very Good", "Very Good"),
        ],
    ),
    Bid(
        key="cobalt",
        company="Cobalt Ridge Construction LLC (fictional)",
        signatory="Marcus Ellery, Managing Member (fictional)",
        emr=0.95,
        bond=False,
        # Item 2: 1,200 CY x $395.00 = $474,000.00, but the bid states $492,000.00.
        schedule=schedule([17.90, 395.00, 4090.00, 30.80, 3020000.00], overrides={"2": 492_000.00}),
        projects=[
            Project("Westgate Fulfillment Center", "warehouse", "Westgate Retail Holdings", 2020, 16_100_000, "Prime contractor", "Satisfactory", "Satisfactory"),
            Project("Pinecrest Industrial Flex Building", "industrial building", "Pinecrest Development", 2023, 9_200_000, "Prime contractor", "Very Good", "Very Good"),
            Project("Old Mill Packaging Plant", "industrial building", "Old Mill Packaging", 2016, 13_700_000, "Prime contractor", "Very Good", "Very Good"),
            Project("Summit County Maintenance Depot", "industrial building", "Summit County", 2022, 11_800_000, "Prime contractor", "Satisfactory", "Satisfactory"),
            Project("Bluewater Distribution Hub", "warehouse", "Bluewater Freight", 2025, 15_300_000, "Prime contractor", "Very Good", "Very Good"),
        ],
    ),
    Bid(
        key="harborpine",
        company="Harbor & Pine Contractors (fictional)",
        signatory="Priya Natarajan, Chief Executive (fictional)",
        emr=1.12,
        bond=True,
        schedule=schedule([19.20, 402.00, 4120.00, 32.10, 2940000.00]),
        projects=[
            Project("Clearwater Logistics Warehouse", "warehouse", "Clearwater Logistics", 2021, 13_900_000, "Prime contractor", "Very Good", "Very Good"),
            Project("Ironwood Tool and Die Facility", "industrial building", "Ironwood Manufacturing", 2023, 17_250_000, "Prime contractor", "Very Good", "Marginal"),
            Project("Cedar Point Regional Distribution Center", "warehouse", "Cedar Point Grocers", 2020, 21_400_000, "Subcontractor (steel package)", "Satisfactory", "Satisfactory"),
            Project("Silver Lake Assembly Plant", "industrial building", "Silver Lake Motors", 2024, 12_600_000, "Prime contractor", "Satisfactory", "Satisfactory"),
            Project("Brookfield Office Campus", "office building", "Brookfield Partners", 2022, 19_000_000, "Prime contractor", "Very Good", "Very Good"),
        ],
    ),
]


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


def build_tender(path: Path) -> None:
    story = [
        p(f"Invitation to Bid No. {TENDER_REF}", "Title"),
        p(TENDER_TITLE, "Heading2"),
        p("Owner: Riverbend County Department of Public Works (fictional)"),
        Spacer(1, 10),
        p("1. Scope of work", "Heading3"),
        p("Construction of a single-storey light-industrial building of approximately 52,000 square feet, "
          "with structural steel frame, insulated metal panels, slab on grade and building services."),
        p("2. Bid submission requirements", "Heading3"),
        p("2.1 Each bid shall include a bid bond in the amount of not less than five percent (5%) of the total base bid."),
        p("2.2 The Bid Form shall be signed by an authorized officer of the bidder and shall acknowledge Addendum No. 1."),
        p("2.3 Each bidder shall complete the Bid Schedule. Extended amounts shall equal quantity multiplied by unit price."),
        p("2.4 Each bidder shall complete the Statement of Experience and attach the owner's performance evaluation for every project listed."),
        p("2.5 Each bidder shall submit its current Experience Modification Rate (EMR) certified by its insurance carrier."),
        PageBreak(),
        p("3. Evaluation criteria", "Heading3"),
        p("3.1 Relevant completed projects. The County will award 2.5 points for each project that is an industrial building, "
          "warehouse or distribution center; was completed between 2018 and 2026 inclusive; had a contract value of not less than "
          "$11,000,000; received an owner performance rating of Satisfactory or better; and was performed by the bidder as prime "
          "contractor. A maximum of five projects will be counted."),
        p("3.2 Safety performance. Five points for an EMR of 0.85 or lower; three points for an EMR above 0.85 and not above 1.00; "
          "no points for an EMR above 1.00."),
        p("3.3 Qualitative criteria (method statement and programme) will be evaluated separately by the County's panel."),
    ]
    SimpleDocTemplate(str(path), pagesize=PAGE, title=f"ITB {TENDER_REF}").build(story, onFirstPage=stamp, onLaterPages=stamp)


def build_bid(bid: Bid, path: Path) -> None:
    total = round(sum(r[5] for r in bid.schedule), 2)
    story = [
        p("Bid Form", "Title"),
        p(f"Invitation to Bid No. {TENDER_REF} - {TENDER_TITLE}"),
        p(f"Bidder: {bid.company}"),
        p(f"Total base bid: {money(total)}"),
        p("The bidder acknowledges receipt of Addendum No. 1."),
        p(f"Signed: {bid.signatory}"),
        PageBreak(),
        p("Bid Schedule", "Heading2"),
        grid([["Item", "Description", "Unit", "Quantity", "Unit price", "Extended amount"]]
             + [[i, d, u, f"{q:,}", money(r), money(a)] for i, d, u, q, r, a in bid.schedule]
             + [["", "Total base bid", "", "", "", money(total)]],
             [35, 300, 45, 70, 110, 120]),
        PageBreak(),
        p("Statement of Experience", "Heading2"),
        grid([["No.", "Project", "Building type", "Owner", "Completed", "Contract value", "Role", "Owner rating"]]
             + [[str(n), pr.name, pr.building_type, pr.owner, str(pr.completed), money(pr.value), pr.role, pr.claimed_rating]
                for n, pr in enumerate(bid.projects, 1)],
             [24, 175, 85, 125, 52, 85, 115, 60]),
        PageBreak(),
        p("Experience Modification Rate", "Heading2"),
        p(f"The insurance carrier certifies that the current Experience Modification Rate of {bid.company} is {bid.emr:.2f}."),
    ]
    for pr in bid.projects:
        story += [
            PageBreak(),
            p("Owner Performance Evaluation", "Heading2"),
            p(f"Project: {pr.name}"),
            p(f"Owner: {pr.owner} (fictional)"),
            p(f"Contractor evaluated: {bid.company}"),
            p(f"Year of completion: {pr.completed}"),
            p(f"Overall performance rating: {pr.letter_rating}"),
        ]
    if bid.bond:
        story += [
            PageBreak(),
            p("Bid Bond", "Heading2"),
            p(f"Principal: {bid.company}. Obligee: Riverbend County (fictional). "
              f"Penal sum: five percent (5%) of the total base bid, being {money(round(total * 0.05, 2))}."),
        ]
    SimpleDocTemplate(str(path), pagesize=PAGE, title=f"Bid - {bid.company}").build(story, onFirstPage=stamp, onLaterPages=stamp)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    build_tender(OUT / "tender_ITB_RC-2026-014.pdf")
    for bid in BIDS:
        build_bid(bid, OUT / f"bid_{bid.key}.pdf")
    print(f"Wrote {len(BIDS) + 1} fictional documents to {OUT}")


if __name__ == "__main__":
    main()
