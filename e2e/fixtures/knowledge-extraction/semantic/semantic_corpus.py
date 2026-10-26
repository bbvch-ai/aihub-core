"""A small archive whose file names say nothing about the documents, for semantic discovery (#2200).

Supplier contracts in English, German and French sit next to minutes, policies, offers and invoices that use the
request's words without being contracts, so neither a path nor a keyword finds the right documents.
"""

CONTRACT_BRIGHTLINE = """# Master Services Agreement

This Master Services Agreement is made between Northwind Data AG, Zurich ("Customer") and Brightline Logistics Ltd,
Basel ("Supplier").

## 1. Services

The Supplier provides warehousing, pick-and-pack and same-day distribution of Customer goods in Switzerland, as set
out in the service descriptions agreed in writing from time to time.

## 2. Fees and invoicing

The Customer pays the fees in the price list in Annex 1. The Supplier invoices monthly in arrears; invoices are payable
within 30 days.

## 3. Term and ending the agreement

This Agreement starts on 1 March 2024 and runs for an indefinite period. Either party may end this Agreement by giving
six (6) months' written notice to the other party.

## 4. Responsibility for damage

The aggregate liability of the Supplier under or in connection with this Agreement shall not exceed EUR 75,000. This
limit does not apply to damage caused intentionally or by gross negligence.

## 5. Governing law

This Agreement is governed by Swiss law. Courts of Zurich have exclusive jurisdiction.
"""

CONTRACT_ORION = """# Equipment Supply Agreement

Between Northwind Data AG ("Buyer") and Orion Components Inc., Austin, Texas ("Seller").

## Article 1 - Scope

Seller shall manufacture and deliver rack-mounted power distribution units and cable assemblies according to the
purchase orders issued by Buyer under this agreement.

## Article 2 - Delivery

Delivery is DAP Zurich. Seller ships within four weeks of each purchase order.

## Article 3 - Duration

This agreement has an initial term of two years and renews for successive one-year periods. It may be terminated by
either party upon ninety (90) days' prior written notice.

## Article 4 - Limitation of liability

Seller's total liability arising out of this agreement is limited to the amounts paid by Buyer in the twelve (12)
months preceding the event giving rise to the claim.

## Article 5 - Law

The laws of the State of New York apply.
"""

CONTRACT_ALPENTECH = """# Rahmenvertrag über IT-Dienstleistungen

zwischen der Northwind Data AG, Zürich (Auftraggeberin) und der Alpentech Systems GmbH, Chur (Auftragnehmerin).

## 1. Gegenstand

Die Auftragnehmerin betreibt und wartet die Server- und Netzwerkinfrastruktur der Auftraggeberin an den Standorten
Zürich und Chur. Einzelne Leistungen werden in Leistungsscheinen vereinbart.

## 2. Vergütung

Die Vergütung richtet sich nach den Leistungsscheinen. Rechnungen sind innert 30 Tagen zahlbar.

## 3. Dauer und Beendigung

Der Vertrag tritt am 1. Januar 2024 in Kraft und gilt auf unbestimmte Zeit. Er kann von jeder Partei mit einer Frist
von drei Monaten auf das Ende eines Kalenderquartals schriftlich gekündigt werden.

## 4. Haftung

Die Gesamthaftung der Auftragnehmerin aus diesem Vertrag ist auf CHF 80'000 begrenzt. Für Vorsatz und grobe
Fahrlässigkeit haftet sie unbeschränkt.

## 5. Anwendbares Recht

Es gilt schweizerisches Recht. Gerichtsstand ist Zürich.
"""

CONTRACT_RHEINFELD = """# Liefervertrag Verpackungsmaterial

Die Rheinfeld Verpackungen AG, Schaffhausen (Lieferantin) liefert der Northwind Data AG (Bestellerin) Kartonagen,
Polstermaterial und Etiketten nach den jeweiligen Abrufen.

## Preise

Es gelten die Preise der Preisliste 2024. Preisänderungen sind drei Monate im Voraus anzukündigen.

## Laufzeit

Der Vertrag beginnt am 1. April 2024. Er verlängert sich jeweils um ein Jahr, wenn er nicht mit einer Frist von sechs
Monaten auf das Ende eines Kalenderjahres gekündigt wird.

## Haftung der Lieferantin

Die Haftung der Lieferantin für Schäden aus diesem Vertrag ist auf insgesamt EUR 500'000 beschränkt.

## Gerichtsstand

Schaffhausen. Schweizerisches Recht ist anwendbar.
"""

CONTRACT_LEMANIC = """# Contrat de prestation de services de nettoyage

entre Northwind Data SA, succursale de Lausanne (le Client) et Lémanic Nettoyage SA, Lausanne (le Prestataire).

## Objet

Le Prestataire assure le nettoyage quotidien des bureaux et des salles serveurs du Client à Lausanne.

## Rémunération

Forfait mensuel de CHF 4 800, facturé à la fin de chaque mois et payable à 30 jours.

## Durée et résiliation

Le contrat est conclu pour une durée indéterminée. Il est résiliable par chaque partie moyennant un préavis de deux
mois pour la fin d'un mois.

## Responsabilité

La responsabilité totale du Prestataire au titre du présent contrat est limitée à CHF 30 000.

## Droit applicable

Le droit suisse est applicable. For à Lausanne.
"""

CONTRACT_VANTAGE = """# Software License and Support Agreement

Vantage Analytics LLC ("Vendor") grants Northwind Data AG ("Licensee") a non-exclusive license to the Vantage
Insight platform, together with second-level support.

## Support

Vendor answers support requests on business days within eight business hours.

## Term

The subscription term is three years. Licensee may terminate for convenience on thirty (30) days' notice; prepaid fees
for the remaining term are not refunded.

## Liability

IN NO EVENT SHALL VENDOR'S CUMULATIVE LIABILITY UNDER THIS AGREEMENT EXCEED USD 2,000,000.

## Governing law

Delaware law governs this agreement.
"""

SLA_CIRRUS = """# Service Level Schedule - Managed Hosting

Provider: Cirrus Hosting AG, Lugano. Customer: Northwind Data AG.

## Availability

The hosting platform shall be reachable for the Customer 99.5% of the time in each calendar month, measured at the
Provider's network edge. Planned maintenance announced five days in advance is excluded.

## Service credits

For every full 0.5% below the commitment, the Customer receives a credit of 5% of the monthly hosting fee.

## Support

Critical incidents are answered within one hour, around the clock.
"""

SLA_MATTERHORN = """# Leistungsbeschreibung Betrieb Cloud-Plattform

Anbieterin: Matterhorn Cloud AG, Visp. Kundin: Northwind Data AG.

## Verfügbarkeit

Die Verfügbarkeit der Plattform beträgt 99,8 % pro Kalendermonat. Angekündigte Wartungsfenster am Sonntagmorgen
werden nicht angerechnet.

## Gutschriften

Wird die Verfügbarkeit unterschritten, erhält die Kundin eine Gutschrift von 10 % der Monatsgebühr.

## Störungsmeldungen

Störungen der Priorität 1 werden innert 30 Minuten bearbeitet.
"""

MINUTES_PROCUREMENT = """# Procurement steering committee - minutes of 14 May 2024

Present: Head of Procurement, CFO, Legal Counsel, IT Operations Lead.

## 1. Supplier contract with Orion Components

Legal reported on the draft supplier contract. The liability cap offered by Orion is too low; the committee wants a
cap of EUR 60,000 at minimum and a termination notice of no more than three months.

## 2. Cleaning services in Lausanne

The current provider performs well. No change.

## 3. Next meeting

The next meeting takes place on 11 June 2024.
"""

MINUTES_EINKAUF = """# Protokoll Einkaufsrunde vom 3. September 2024

## Traktandum 1: Lieferantenverträge

Die Haftungsbegrenzung und die Kündigungsfrist in den Lieferantenverträgen wurden besprochen. Künftig sollen alle
neuen Lieferantenverträge eine Kündigungsfrist von höchstens sechs Monaten vorsehen.

## Traktandum 2: Budget 2025

Das Einkaufsbudget 2025 wird um 4 % erhöht.
"""

POLICY_SUPPLIERS = """# Supplier Contract Policy

Version 3, approved by the Executive Board.

## Purpose

This policy sets the minimum terms every supplier contract of Northwind Data must contain.

## Liability cap

Every supplier contract must cap the supplier's liability at no less than the expected annual contract value.

## Termination notice

Supplier contracts must allow us to terminate with a notice of at most six months.

## Approval

Contracts above CHF 250,000 per year need the CFO's approval.
"""

INVOICE_BRIGHTLINE = """# Invoice BL-2024-0611

Brightline Logistics Ltd, Basel - to Northwind Data AG, Zurich. Invoice date: 30 June 2024.

| Item | Amount (CHF) |
|---|---|
| Warehousing June 2024 | 8,400.00 |
| Same-day deliveries (112) | 3,136.00 |
| Total | 11,536.00 |

Payable within 30 days as per our agreement.
"""

HANDBOOK_EMPLOYMENT = """# Personalhandbuch - Anstellung und Austritt

## Probezeit

Die Probezeit beträgt drei Monate. Während der Probezeit gilt eine Kündigungsfrist von sieben Tagen.

## Kündigung des Arbeitsverhältnisses

Nach der Probezeit beträgt die Kündigungsfrist im ersten Dienstjahr einen Monat, danach drei Monate, jeweils auf das
Monatsende.

## Ferien

Mitarbeitende haben Anspruch auf 25 Ferientage pro Jahr.
"""

NEWSLETTER = """# Northwind News - Summer 2024

Our summer party takes place on 23 August at the lake. The new office in Lausanne opened in July, and the IT team
moved the data centre to Chur without any downtime. Welcome to the twelve new colleagues who joined this quarter!
"""

TRAVEL_POLICY = """# Travel and Expenses Guideline

Train travel in second class is the default; first class is allowed for trips over three hours. Flights need the line
manager's approval. Hotel costs are reimbursed up to CHF 220 per night in Switzerland. Receipts must be submitted
within 30 days.
"""

OFFER_ALPENTECH = """# Angebot Nr. 2024-117

Alpentech Systems GmbH, Chur, an Northwind Data AG.

Wir bieten Ihnen die Erweiterung des Netzwerks am Standort Zürich um zwei Core-Switches an.

| Position | Betrag (CHF) |
|---|---|
| 2 Core-Switches inkl. Installation | 46'200.00 |
| Konfiguration und Tests | 6'800.00 |

Das Angebot ist 30 Tage gültig. Es gelten unsere Allgemeinen Geschäftsbedingungen.
"""

DATASHEET_ORION = """# Orion PDU-48 rack power distribution unit - datasheet

48 outlets, 3-phase 32 A input, per-outlet metering, network management card, operating temperature 0-45 °C.
Warranty: 3 years. Manufacturer: Orion Components Inc., Austin, Texas.
"""

DRAFT_KESTREL = """# Consulting Agreement (DRAFT - not signed)

Between Northwind Data AG and Kestrel Analytics GmbH, Bern ("Consultant").

## Term

Either party may terminate this agreement with one month's notice.

## Liability

The Consultant's liability is limited to CHF 40,000.
"""

DOCUMENTS = {
    "archive/2024/scan-0103.md": CONTRACT_BRIGHTLINE,
    "archive/2024/scan-0117.md": MINUTES_PROCUREMENT,
    "archive/2024/scan-0122.md": CONTRACT_ORION,
    "archive/2024/scan-0131.md": INVOICE_BRIGHTLINE,
    "archive/2024/scan-0140.md": CONTRACT_ALPENTECH,
    "archive/2024/scan-0146.md": NEWSLETTER,
    "archive/2024/scan-0152.md": CONTRACT_RHEINFELD,
    "archive/2024/scan-0158.md": HANDBOOK_EMPLOYMENT,
    "archive/2024/scan-0163.md": SLA_CIRRUS,
    "archive/2024/scan-0171.md": POLICY_SUPPLIERS,
    "archive/2023/scan-0201.md": CONTRACT_LEMANIC,
    "archive/2023/scan-0207.md": OFFER_ALPENTECH,
    "archive/2023/scan-0214.md": SLA_MATTERHORN,
    "archive/2023/scan-0219.md": TRAVEL_POLICY,
    "archive/2023/scan-0225.md": CONTRACT_VANTAGE,
    "archive/2023/scan-0232.md": MINUTES_EINKAUF,
    "archive/2023/scan-0238.md": DATASHEET_ORION,
    "drafts/kestrel-consulting-agreement.md": DRAFT_KESTREL,
}
