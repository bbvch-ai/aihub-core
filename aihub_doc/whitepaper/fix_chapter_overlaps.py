#!/usr/bin/env python3
"""
Fix chapter overlaps by establishing clear boundaries between chapters.

Major issues to fix:
1. Chapter 03 (Datensouveränität) should NOT cover compliance mechanisms (defer to Ch 09)
2. Chapter 07 (Datensicherheit) should focus on DATA FLOW, not architecture
3. Chapter 08 (Sicherheitsarchitektur) should focus on ARCHITECTURE, not data flow
4. All chapters should have "Technical details at END" reminders
"""

import re
from pathlib import Path

PROMPTS_DIR = Path("/home/user/aihub-core/aihub_doc/whitepaper/prompts")


def add_scope_boundaries_to_chapter(chapter_num: str, focus: str, defer_to: list[tuple[str, str]]):
    """Add clear scope boundaries to a chapter prompt."""

    prompt_file = PROMPTS_DIR / f"{chapter_num}_prompt.md"
    if not prompt_file.exists():
        print(f"Warning: {prompt_file} not found")
        return

    content = prompt_file.read_text()

    # Check if boundaries already exist
    if "## Kapitelabgrenzung und Fokus" in content:
        print(f"Chapter {chapter_num} already has boundaries section")
        return

    # Build boundaries section
    boundaries = f"""
## Kapitelabgrenzung und Fokus

**WICHTIG - Fokus dieses Kapitels**: {focus}

"""

    if defer_to:
        boundaries += "**Behandeln Sie NICHT** (wird in anderen Kapiteln abgedeckt):\n"
        for topic, target_chapter in defer_to:
            boundaries += f"- {topic} → siehe Kapitel {target_chapter}\n"
        boundaries += "\n"

    boundaries += """**Struktur-Anforderung**: Technische Details (falls vorhanden) IMMER am Ende des Kapitels als klar gekennzeichneter "Technischer Exkurs" oder "Technische Umsetzung".

"""

    # Insert after "Kapitelziel" section
    pattern = r"(## Kapitelziel\n.*?\n\n)"
    replacement = r"\1" + boundaries

    new_content = re.sub(pattern, replacement, content, count=1, flags=re.DOTALL)

    if new_content != content:
        prompt_file.write_text(new_content)
        print(f"✓ Updated {chapter_num}_prompt.md with scope boundaries")
    else:
        print(f"✗ Could not update {chapter_num}_prompt.md")


def fix_chapter_03():
    """Fix Chapter 03: Remove compliance details, focus on sovereignty"""
    print("\n=== Fixing Chapter 03: Datensouveränität ===")

    add_scope_boundaries_to_chapter(
        "03",
        "Deployment-Optionen für Datensouveränität, kundenseitige Kontrolle über Infrastruktur und Konfiguration, Vendor-Unabhängigkeit durch modulare Architektur",
        [
            ("Detaillierte Compliance-Mechanismen (revDSG, GDPR, AI Act)", "Kapitel 09 (Regulatorische Compliance)"),
            ("Implementierungsdetails von Consent-Management", "Kapitel 09"),
            ("Technische Details zu Lösch-Workflows", "Kapitel 09"),
            ("Detaillierte Audit-Trail-Implementierung", "Kapitel 04 (Plattform-Transparenz)"),
            ("Sicherheitsarchitektur-Details", "Kapitel 08 (Sicherheitsarchitektur)"),
        ]
    )

    # Update the "Compliance-Funktionen" section to be high-level
    prompt_file = PROMPTS_DIR / "03_prompt.md"
    content = prompt_file.read_text()

    # Replace the detailed compliance section with a high-level reference
    old_compliance = r"- \*\*Compliance-Funktionen und Datenschutz-Mechanismen\*\*:.*?Geschäftlicher Nutzen:.*?\n\n"
    new_compliance = """- **Compliance-Enabler durch Datensouveränität**: Vollständige Datenkontrolle ermöglicht Compliance (Details zu spezifischen Compliance-Mechanismen siehe Kapitel 09), Schweizer Hosting erfüllt Data-Residency-Anforderungen, Air-Gap-Option für höchste Sicherheitsanforderungen, Kunden-kontrollierte Administration erlaubt Umsetzung interner Governance-Vorgaben; Geschäftlicher Nutzen: Grundlage für revDSG/GDPR-Compliance durch vollständige Kontrolle, Transparenz-Anforderungen erfüllbar durch offene Architektur, Flexibilität zur Anpassung an sich ändernde regulatorische Anforderungen

"""

    new_content = re.sub(old_compliance, new_compliance, content, flags=re.DOTALL)

    if new_content != content:
        prompt_file.write_text(new_content)
        print("✓ Updated Ch03: Reduced compliance overlap")


def fix_chapter_07():
    """Fix Chapter 07: Focus on data flow, not architecture"""
    print("\n=== Fixing Chapter 07: Datensicherheit und Datenfluss ===")

    add_scope_boundaries_to_chapter(
        "07",
        "Sicherheit von Daten entlang ihres Lebenszyklus: Eingangspunkte → Verarbeitung → Ausgangspunkte. Datenfluss-Monitoring und Schutz an Ein-/Austrittspunkten.",
        [
            ("Infrastruktur-Sicherheitsarchitektur", "Kapitel 08 (Sicherheitsarchitektur)"),
            ("SSO und Enterprise-Authentifizierungs-Systeme", "Kapitel 05 (Administration) und 08 (Sicherheitsarchitektur)"),
            ("Container-Isolation und Netzwerk-Policies", "Kapitel 08"),
            ("Regulatorische Compliance-Details", "Kapitel 09"),
        ]
    )


def fix_chapter_08():
    """Fix Chapter 08: Focus on architecture, not data flow"""
    print("\n=== Fixing Chapter 08: Sicherheitsarchitektur ===")

    add_scope_boundaries_to_chapter(
        "08",
        "Mehrschichtige Sicherheitsarchitektur der Plattform: Infrastruktur, Netzwerk, Authentifizierung, Verschlüsselung. Defense-in-Depth-Ansatz.",
        [
            ("Datenfluss-Details (Ingress → Processing → Egress)", "Kapitel 07 (Datensicherheit und Datenfluss)"),
            ("Detaillierte Compliance-Mechanismen", "Kapitel 09"),
            ("Administrative Governance und RBAC-Details", "Kapitel 05 (Administration)"),
            ("PII-Detection im Datenfluss-Kontext", "Kapitel 07"),
        ]
    )


def fix_chapter_09():
    """Fix Chapter 09: Ensure it's the central compliance chapter"""
    print("\n=== Fixing Chapter 09: Regulatorische Compliance ===")

    add_scope_boundaries_to_chapter(
        "09",
        "Regulatorische Compliance: revDSG, GDPR, EU AI Act. Konkrete Compliance-Mechanismen und wie sie technisch umgesetzt sind.",
        [
            ("Deployment-Optionen und Datensouveränität-Konzept", "Kapitel 03 (Datensouveränität)"),
            ("Technische Sicherheitsarchitektur", "Kapitel 08"),
            ("Audit-Trails und Transparenz-Features", "Kapitel 04 (Plattform-Transparenz)"),
        ]
    )


def add_reminder_to_all_chapters():
    """Add technical details reminder to all chapter prompts"""
    print("\n=== Adding technical details reminder to all chapters ===")

    for prompt_file in sorted(PROMPTS_DIR.glob("*_prompt.md")):
        content = prompt_file.read_text()

        # Skip if already has the reminder
        if "Technische Details am ENDE" in content or "Technischer Exkurs" in content:
            continue

        # Add reminder after Business-Fragen section
        pattern = r"(## Business-Fragen, die das Kapitel beantwortet.*?)\n\n(\d+\.)"

        reminder = """

**ERINNERUNG**: Alle technischen Details müssen am ENDE des Kapitels stehen, klar gekennzeichnet als "Technischer Exkurs" oder "Technische Umsetzung".

"""

        replacement = r"\1" + reminder + r"\2"
        new_content = re.sub(pattern, replacement, content, count=1, flags=re.DOTALL)

        if new_content != content:
            prompt_file.write_text(new_content)
            print(f"✓ Added tech reminder to {prompt_file.name}")


if __name__ == "__main__":
    print("Fixing chapter overlaps...\n")

    fix_chapter_03()
    fix_chapter_07()
    fix_chapter_08()
    fix_chapter_09()

    add_reminder_to_all_chapters()

    print("\n✅ Done! Review the changes with: git diff aihub_doc/whitepaper/prompts/")
