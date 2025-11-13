#!/usr/bin/env python3
"""
Update all chapter prompts to align with general_prompt.md structure
Ensures consistent word count targets and business dimension priorities
"""

import re
from pathlib import Path

# Define word count targets and business dimensions for each chapter
CHAPTERS = {
    "01": {
        "title": "Business Challenge",
        "words": (400, 600),
        "type": "sehr_kurz",
        "dimensions": [
            "**KOSTEN** - Wichtig: Versteckte Kosten in fragmentierten Lösungen",
            "**MANAGEMENT** - Sehr wichtig: Komplexität aktueller AI-Landschaften",
            "**ZUKUNFTSSICHERHEIT** - Wichtig: Vendor Lock-in Risiken",
        ]
    },
    "02": {
        "title": "Platform Overview",
        "words": (400, 600),
        "type": "sehr_kurz",
        "dimensions": [
            "**ALLE DIMENSIONEN** - Kurze Erwähnung als Lösungsüberblick",
            "  Fokus: Wie die Plattform die in Kap. 01 genannten Probleme löst",
        ]
    },
    "03": {
        "title": "Benutzererfahrung",
        "words": (900, 1300),
        "type": "mittel",
        "dimensions": [
            "**MANAGEMENT** - Sehr wichtig: Benutzerakzeptanz, Change Management",
            "**INTEGRATION** - Wichtig: Multi-Kanal-Zugriff (Teams, Slack, Web)",
            "**DATENSCHUTZ** - Wichtig: Transparenz über Datennutzung für Benutzer",
        ]
    },
    "04": {
        "title": "Wissensmanagement & RAG",
        "words": (1300, 1800),
        "type": "lang",
        "dimensions": [
            "**DATENSCHUTZ** - SEHR WICHTIG: Zugriffskontrolle, Collection-Scoping",
            "**SICHERHEIT** - Wichtig: Document-Level Security",
            "**INTEGRATION** - Wichtig: SharePoint-Sync, Auto-Crawling",
            "**MANAGEMENT** - Wichtig: Automatische Pipelines, minimaler Aufwand",
        ]
    },
    "05": {
        "title": "AI-Agents",
        "words": (1300, 1800),
        "type": "lang",
        "dimensions": [
            "**DATENSCHUTZ** - SEHR WICHTIG: Transparenz, Auditierbarkeit (revDSG)",
            "**SICHERHEIT** - Wichtig: Workflow-Kontrolle, Nachvollziehbarkeit",
            "**ZUKUNFTSSICHERHEIT** - Wichtig: Erweiterbarkeit, Custom Workflows",
        ]
    },
    "06": {
        "title": "Prozessautomatisierung",
        "words": (600, 900),
        "type": "kurz",
        "dimensions": [
            "**KOSTEN** - Wichtig: Effizienzgewinne durch Automatisierung",
            "**INTEGRATION** - Sehr wichtig: Orchestrierung AI + Menschen + Systeme",
            "**MANAGEMENT** - Wichtig: Prozessüberwachung, Governance",
        ]
    },
    "07": {
        "title": "Administration & Governance",
        "words": (1300, 1800),
        "type": "lang",
        "dimensions": [
            "**MANAGEMENT** - SEHR WICHTIG: Benutzer, Rollen, Policies, Budgets",
            "**KOSTEN** - Sehr wichtig: Cost Control, Budget-Limits, Tracking",
            "**DATENSCHUTZ** - Sehr wichtig: RBAC, granulare Zugriffskontrolle",
            "**SICHERHEIT** - Wichtig: SSO/Azure AD, Session Management",
        ]
    },
    "08": {
        "title": "Sicherheitsarchitektur",
        "words": (1300, 1800),
        "type": "lang",
        "dimensions": [
            "**SICHERHEIT** - SEHR WICHTIG: E2E-Verschlüsselung, Zero-Trust, Network Security",
            "**DATENSCHUTZ** - Sehr wichtig: Data-at-Rest, Data-in-Transit, Key Management",
            "**INTEGRATION** - Wichtig: Enterprise SSO, Security Monitoring",
        ]
    },
    "09": {
        "title": "Compliance & Datenschutz",
        "words": (1800, 2100),
        "type": "sehr_lang",
        "dimensions": [
            "**DATENSCHUTZ** - ABSOLUT KRITISCH: revDSG, FADP, DSGVO, AI Act",
            "  Dieser Dimension **30-50% mehr Raum** geben als anderen Kapiteln!",
            "  Schweizer Organisationen bewerten Datenschutz als Top-Priorität.",
            "**SICHERHEIT** - Sehr wichtig: Compliance-relevante Sicherheitskontrollen",
            "**ZUKUNFTSSICHERHEIT** - Wichtig: Regulatory Roadmap, AI Act Preparedness",
        ]
    },
    "10": {
        "title": "Deployment & Betrieb",
        "words": (900, 1300),
        "type": "mittel",
        "dimensions": [
            "**MANAGEMENT** - Sehr wichtig: Einfacher Betrieb, Wartungsaufwand",
            "**KOSTEN** - Wichtig: Infrastrukturkosten, TCO verschiedener Deployment-Modelle",
            "**ZUKUNFTSSICHERHEIT** - Wichtig: Upgrade-Pfade, Langzeit-Wartbarkeit",
            "**INTEGRATION** - Wichtig: Enterprise-Infrastruktur-Anbindung",
        ]
    },
}

def update_chapter_prompt(chapter_num: str, config: dict, prompts_dir: Path):
    """Update a single chapter prompt file"""

    prompt_file = prompts_dir / f"{chapter_num}_prompt.md"

    if not prompt_file.exists():
        print(f"⚠️  Warning: {prompt_file} not found, skipping")
        return

    content = prompt_file.read_text()

    # Extract chapter title from first heading
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if not title_match:
        print(f"⚠️  Warning: Could not find title in {prompt_file}")
        return

    original_title = title_match.group(1).strip()

    # 1. Update word count in "Kapitelziel" section
    words_min, words_max = config["words"]

    # Find and replace word count
    content = re.sub(
        r"(\d+[-–]\d+\s+Wörter|\d+\s+Seiten,\s+\d+[-–]\d+\s+Wörter|\d+-\d+\s+Seiten)",
        f"{words_min}-{words_max} Wörter",
        content
    )

    # 2. Add/update WICHTIG note about general_prompt.md
    wichtig_note = f"\n\n**WICHTIG**: Folgen Sie den Richtlinien in `general_prompt.md` für Textfluss, Struktur und Business-Fragen. Dieses Kapitel ist **{config['type'].replace('_', ' ')}** ({words_min}-{words_max} Wörter).\n"

    # Check if WICHTIG note already exists
    if "**WICHTIG**: Folgen Sie den Richtlinien" not in content:
        # Add after Kapitelziel section
        content = re.sub(
            r"(## Kapitelziel\n[^\n]+(?:\n[^\n]+)*?)(\n\n##)",
            r"\1" + wichtig_note + r"\2",
            content
        )

    # 3. Add/update Business-Dimensionen section
    dims_text = "\n".join(f"{i+1}. {dim}" for i, dim in enumerate(config["dimensions"]))

    business_section = f"""## Business-Dimensionen (Priorität für dieses Kapitel)
{dims_text}

**Behandeln Sie diese Dimensionen explizit** mit konkreten Antworten auf Business-Fragen.
"""

    # Remove old Business-Dimensionen section if exists
    content = re.sub(
        r"## Business-Dimensionen.*?\n\n(?=##)",
        "",
        content,
        flags=re.DOTALL
    )

    # Add new Business-Dimensionen after Kapitelziel
    if "## Business-Dimensionen" not in content:
        content = re.sub(
            r"(## Kapitelziel\n[^\n]+(?:\n[^\n]+)*?)\n\n(## (?!Business-Dimensionen))",
            r"\1\n\n" + business_section + r"\2",
            content
        )

    # 4. Remove page-based subsection markers (e.g., "(0.5 Seiten)", "(1-2 Seiten)")
    content = re.sub(r"\s*\([0-9.]+-?[0-9.]*\s+Seiten?\)", "", content)

    # 5. Replace "Inhaltsstruktur" with "Themen und Inhalte" if exists
    content = content.replace("## Inhaltsstruktur", "## Themen und Inhalte")

    # Write updated content
    prompt_file.write_text(content)
    print(f"✓ Updated {chapter_num}: {original_title} -> {words_min}-{words_max} words ({config['type']})")


def main():
    """Update all chapter prompts"""
    prompts_dir = Path(__file__).parent / "prompts"

    if not prompts_dir.exists():
        print(f"✗ Error: {prompts_dir} not found")
        return 1

    print("╔══════════════════════════════════════════════════╗")
    print("║       Updating Chapter Prompts                  ║")
    print("╚══════════════════════════════════════════════════╝\n")

    # Chapter 00 already updated manually, skip it
    for chapter_num in sorted(CHAPTERS.keys()):
        config = CHAPTERS[chapter_num]
        update_chapter_prompt(chapter_num, config, prompts_dir)

    print("\n✓ All chapters updated!")
    print("\nNext steps:")
    print("  1. Review updated prompts in prompts/ directory")
    print("  2. Run: ./generate-whitepaper.sh")
    print("  3. Run: ./combine-whitepaper.sh")
    print("  4. Run: ./measure-whitepaper.sh swiss_ai_hub_whitepaper.md")

    return 0


if __name__ == "__main__":
    exit(main())
