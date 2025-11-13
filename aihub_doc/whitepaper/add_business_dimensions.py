#!/usr/bin/env python3
"""
Add Business-Dimensionen sections to all chapter prompts
This is a follow-up script to fix the missing business dimensions
"""

import re
from pathlib import Path

# Business dimensions for each chapter (same as before)
CHAPTERS = {
    "01": [
        "**KOSTEN** - Wichtig: Versteckte Kosten in fragmentierten Lösungen",
        "**MANAGEMENT** - Sehr wichtig: Komplexität aktueller AI-Landschaften",
        "**ZUKUNFTSSICHERHEIT** - Wichtig: Vendor Lock-in Risiken",
    ],
    "02": [
        "**ALLE DIMENSIONEN** - Kurze Erwähnung als Lösungsüberblick",
        "  Fokus: Wie die Plattform die in Kap. 01 genannten Probleme löst",
    ],
    "03": [
        "**MANAGEMENT** - Sehr wichtig: Benutzerakzeptanz, Change Management",
        "**INTEGRATION** - Wichtig: Multi-Kanal-Zugriff (Teams, Slack, Web)",
        "**DATENSCHUTZ** - Wichtig: Transparenz über Datennutzung für Benutzer",
    ],
    "04": [
        "**DATENSCHUTZ** - SEHR WICHTIG: Zugriffskontrolle, Collection-Scoping",
        "**SICHERHEIT** - Wichtig: Document-Level Security",
        "**INTEGRATION** - Wichtig: SharePoint-Sync, Auto-Crawling",
        "**MANAGEMENT** - Wichtig: Automatische Pipelines, minimaler Aufwand",
    ],
    "05": [
        "**DATENSCHUTZ** - SEHR WICHTIG: Transparenz, Auditierbarkeit (revDSG)",
        "**SICHERHEIT** - Wichtig: Workflow-Kontrolle, Nachvollziehbarkeit",
        "**ZUKUNFTSSICHERHEIT** - Wichtig: Erweiterbarkeit, Custom Workflows",
    ],
    "06": [
        "**KOSTEN** - Wichtig: Effizienzgewinne durch Automatisierung",
        "**INTEGRATION** - Sehr wichtig: Orchestrierung AI + Menschen + Systeme",
        "**MANAGEMENT** - Wichtig: Prozessüberwachung, Governance",
    ],
    "07": [
        "**MANAGEMENT** - SEHR WICHTIG: Benutzer, Rollen, Policies, Budgets",
        "**KOSTEN** - Sehr wichtig: Cost Control, Budget-Limits, Tracking",
        "**DATENSCHUTZ** - Sehr wichtig: RBAC, granulare Zugriffskontrolle",
        "**SICHERHEIT** - Wichtig: SSO/Azure AD, Session Management",
    ],
    "08": [
        "**SICHERHEIT** - SEHR WICHTIG: E2E-Verschlüsselung, Zero-Trust, Network Security",
        "**DATENSCHUTZ** - Sehr wichtig: Data-at-Rest, Data-in-Transit, Key Management",
        "**INTEGRATION** - Wichtig: Enterprise SSO, Security Monitoring",
    ],
    "09": [
        "**DATENSCHUTZ** - ABSOLUT KRITISCH: revDSG, FADP, DSGVO, AI Act",
        "  Dieser Dimension **30-50% mehr Raum** geben als anderen Kapiteln!",
        "  Schweizer Organisationen bewerten Datenschutz als Top-Priorität.",
        "**SICHERHEIT** - Sehr wichtig: Compliance-relevante Sicherheitskontrollen",
        "**ZUKUNFTSSICHERHEIT** - Wichtig: Regulatory Roadmap, AI Act Preparedness",
    ],
    "10": [
        "**MANAGEMENT** - Sehr wichtig: Einfacher Betrieb, Wartungsaufwand",
        "**KOSTEN** - Wichtig: Infrastrukturkosten, TCO verschiedener Deployment-Modelle",
        "**ZUKUNFTSSICHERHEIT** - Wichtig: Upgrade-Pfade, Langzeit-Wartbarkeit",
        "**INTEGRATION** - Wichtig: Enterprise-Infrastruktur-Anbindung",
    ],
}


def add_business_dimensions(chapter_num: str, dimensions: list, prompts_dir: Path):
    """Add Business-Dimensionen section to a chapter prompt"""

    prompt_file = prompts_dir / f"{chapter_num}_prompt.md"

    if not prompt_file.exists():
        print(f"⚠️  {prompt_file.name} not found")
        return

    content = prompt_file.read_text()

    # Check if Business-Dimensionen already exists
    if "## Business-Dimensionen" in content:
        print(f"  {prompt_file.name}: Business-Dimensionen already exists, skipping")
        return

    # Build the Business-Dimensionen section
    dims_text = "\n".join(f"{i+1}. {dim}" for i, dim in enumerate(dimensions))

    business_section = f"""## Business-Dimensionen (Priorität für dieses Kapitel)
{dims_text}

**Behandeln Sie diese Dimensionen explizit** mit konkreten Antworten auf Business-Fragen.

"""

    # Find the insertion point: after WICHTIG note or after Kapitelziel
    # Look for the pattern: WICHTIG note followed by next section
    match = re.search(
        r"(\*\*WICHTIG\*\*:.*?\n)\s*\n(## )",
        content,
        re.DOTALL
    )

    if match:
        # Insert after WICHTIG note
        content = content[:match.end(1)] + "\n\n" + business_section + content[match.start(2):]
        print(f"✓ {prompt_file.name}: Added Business-Dimensionen after WICHTIG note")
    else:
        # Fallback: Insert after Kapitelziel section
        match = re.search(
            r"(## Kapitelziel.*?\n)\s*\n(## )",
            content,
            re.DOTALL
        )
        if match:
            content = content[:match.end(1)] + "\n\n" + business_section + content[match.start(2):]
            print(f"✓ {prompt_file.name}: Added Business-Dimensionen after Kapitelziel")
        else:
            print(f"⚠️  {prompt_file.name}: Could not find insertion point")
            return

    # Write updated content
    prompt_file.write_text(content)


def main():
    """Add Business-Dimensionen to all chapters"""
    prompts_dir = Path(__file__).parent / "prompts"

    print("Adding Business-Dimensionen sections to chapter prompts...\n")

    for chapter_num in sorted(CHAPTERS.keys()):
        dimensions = CHAPTERS[chapter_num]
        add_business_dimensions(chapter_num, dimensions, prompts_dir)

    print("\n✓ Done!")


if __name__ == "__main__":
    main()
