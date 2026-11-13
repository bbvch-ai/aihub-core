---
title: Dokumenttypen und Attribute
source_sha: 98ec8818d4779265ba18856e70594bdb6d70445e776bb1b90e9c7f11095de6b2
---

# Dokumenttypen und Attribute

Agents, die Dokumente aus einer Wissensdatenbank auswählen, etwa Document Tables, können danach filtern, was ein
Dokument ist, und nach einigen seiner geschäftlichen Werte, zum Beispiel „Rechnungen von Hooli AG mit Datum 2025“. Ein
Modell liest jedes Dokument einmal, ordnet ihm einen Typ aus einer festen Liste zu und übernimmt anschliessend die
Attribute dieses Typs daraus. Code prüft, was das Modell übernommen hat, und wandelt es in Werte um, die ein Filter
vergleichen kann.

Die Liste ist bewusst fest. Ein Filter über ein bekanntes Vokabular ist zuverlässig; Typen und Attributnamen, die ein
Modell pro Dokument erfindet, sind es nicht. Eine Änderung der Liste ist ein Release, keine Einstellung, und gilt für
jeden Mandanten und jede Wissensdatenbank gleich.

## Typen

| Typ       | Ein Dokument dieses Typs…                                                                                                                                                                                                                                            |
| --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `invoice` | fordert die Bezahlung von Waren oder Dienstleistungen, die geliefert oder vereinbart wurden, und nennt einen Betrag, den der Empfänger dem Aussteller schuldet. Dazu gehören Teil-, Schluss- und Akontorechnungen, QR-Rechnungen sowie Strom- und Telekomrechnungen. |
| `other`   | ist alles andere.                                                                                                                                                                                                                                                    |

Keine Rechnungen, obwohl sie ähnlich aussehen: Angebote und Offerten, Auftragsbestätigungen (auch mit Total),
Lieferscheine, Quittungen für eine bereits geleistete Zahlung, Gutschriften, Zahlungserinnerungen, Kontoauszüge und
Proforma-Rechnungen. Sie sind `other`, bis die Liste einen Typ für sie hat. Auch eine Gutschrift ist `other`, selbst
eine vom Leistungsempfänger nach § 14 UStG ausgestellte Gutschrift im Sinne einer Abrechnung: Das Wort bezeichnet auch
eine Rechnungskorrektur, und beide werden unterschieden, sobald die Liste einen Typ für Gutschriften hat.

Ein Dokument hat einen **primären Typ**, nämlich den, der es als Ganzes beschreibt. Es kann zusätzlich bis zu drei
**sekundäre Typen** aufführen, zum Beispiel eine Rechnung, die zugleich ihr Lieferschein ist. Attribute gehören immer
zum primären Typ; ein sekundärer Typ macht das Dokument nur zusätzlich unter diesem Typ auffindbar. Ein Dokument, das
die Nummer eines anderen Dokuments lediglich erwähnt, ist nicht vom Typ dieses Dokuments.

## Attribute von Rechnungen

| Attribut                      | Werttyp   | Bedeutung                                                                                                                                                                                        | Beispiel: übernommen → gespeichert           |
| ----------------------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------- |
| `document_date`               | Datum     | Rechnungsdatum. Nicht das Fälligkeitsdatum, das Lieferdatum oder das Leistungsdatum.                                                                                                             | `14. März 2025` → `2025-03-14`               |
| `document_reference_number`   | Text      | Rechnungsnummer.                                                                                                                                                                                 | `RE-2025-0412` → `RE-2025-0412`              |
| `document_issuer`             | Text      | Verkäufer, der die Rechnung ausgestellt hat und dem die Zahlung zusteht, mit seinem rechtlichen Namen. Nie ein Factoring- oder Inkassounternehmen, das als Zahlungsempfänger genannt ist.        | `Hooli AG`                                   |
| `document_issuer_tax_id`      | Steuer-ID | MWST-Nummer des Ausstellers, sonst seine Schweizer UID. Nie eine Handelsregisternummer oder die Nummer des Empfängers.                                                                           | `CHE-123.456.788 MWST` → `CHE123456788`      |
| `document_recipient`          | Text      | Kunde, an den die Rechnung gerichtet ist: die verrechnete Organisation oder Person, nicht eine Kontaktperson darin.                                                                              | `Muster Treuhand GmbH`                       |
| `document_parties`            | Textliste | Aussteller und Empfänger, berechnet aus den beiden obigen Attributen.                                                                                                                            | `[Hooli AG, Muster Treuhand GmbH]`           |
| `document_total_amount`       | Betrag    | Endbetrag dieser Rechnung, inklusive MWST, wo MWST erhoben wird. Nicht ein fälliger Betrag, der frühere offene Beträge einrechnet.                                                               | `CHF 12'496.36` → `12496.36`                 |
| `document_currency`           | Währung   | ISO-4217-Code dieses Betrags. In eine andere Währung umgerechnete Beträge werden ignoriert.                                                                                                      | `Fr.` → `CHF`                                |
| `document_due_date`           | Datum     | Fälligkeitsdatum der Zahlung. Zahlungsbedingungen ohne Datum werden nur als Text aufbewahrt.                                                                                                     | `Zahlbar innert 30 Tagen` → leer             |
| `document_period_start`/`end` | Zeitraum  | Leistungs- oder Abrechnungszeitraum, oder das einzelne Leistungsdatum.                                                                                                                           | `Februar 2025` → `2025-02-01` / `2025-02-28` |
| `document_related_references` | Textliste | Nummern der Bestellungen, Auftragsbestätigungen, Lieferscheine oder Verträge, auf die sich die Rechnung bezieht. Nicht die QR-Referenz, eine Kundennummer oder eine Kontonummer. Höchstens fünf. | `[PO-3333, LS-8812]`                         |

Bewusst weggelassen: Adressen und Kontaktangaben, Bankverbindungen, Kunden- und Kontonummern, Netto- und Steuerbeträge,
Steueraufschlüsselungen und Rechnungspositionen. Sie helfen nicht bei der Auswahl von Dokumenten, einige davon sind
persönliche oder finanzielle Daten, und Rechnungspositionen werden gelesen, wenn eine Anfrage sie benötigt.

Die Attribute folgen den Rechnungsmodellen von
[Azure Document Intelligence](https://github.com/Azure-Samples/document-intelligence-code-samples/blob/main/schema/2024-11-30-ga/invoice.md),
[Google Document AI](https://docs.cloud.google.com/document-ai/docs/processors-list),
[AWS Textract](https://docs.aws.amazon.com/textract/latest/dg/invoices-receipts.html) und dem
[DocILE-Benchmark](https://github.com/rossumai/docile/blob/main/docile/dataset/__init__.py); ihre Bedeutungen stammen
aus [EN 16931](https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/tree/), dem
[Schweizer Mehrwertsteuergesetz, Art. 26](https://justement.ch/de/doc/act/ch/641_20/tit_2/chap_6/art_26) und dem
[deutschen Umsatzsteuergesetz, § 14](https://www.gesetze-im-internet.de/ustg_1980/__14.html). Das Schweizer Recht
verlangt keine Rechnungsnummer, daher ist eine leere `document_reference_number` bei einer Schweizer Rechnung zu
erwarten.

## Wann Dokumente klassifiziert werden

Die Ingestion klassifiziert jedes neue oder geänderte Dokument einmal, nach dem Parsen und der Tabellenaufbereitung, mit
dem Textmodell der jeweiligen Wissensdatenbank. Die Einstellung **Dokumente klassifizieren** der Wissensdatenbank
schaltet das aus; standardmässig ist sie eingeschaltet.

- Aus Jira, Confluence oder MediaWiki synchronisierte Datensätze werden nicht klassifiziert: Ihre eigenen Felder sagen
  bereits, was sie sind.
- Schlägt der Modellaufruf fehl, wird das Dokument ohne Typ aufgenommen und bleibt vollständig durchsuchbar. Es wird
  später durch einen Backfill klassifiziert.
- Typ und Attribute sind reine Filter-Metadaten. Sie gehören nicht zum Text, der eingebettet oder einem Modell gezeigt
  wird, daher ändern sich die Suchergebnisse für bestehende Inhalte nicht.
- Jede Wissensdatenbank lässt sich nach `document_type`, `document_types` und dem Wert jedes Attributs filtern, in der
  Vektorsuche und in der Dokumentliste, ohne dass die Schlüssel konfiguriert werden müssen.

## Wie Werte gespeichert werden

Das Modell übernimmt nur Text; es wandelt nie einen Wert um und ergänzt ihn auch nicht. Für jedes Attribut tragen das
Dokument und jeder seiner Chunks im Vector Store:

- den **Wert** unter dem Schlüssel des Attributs, von Code aus dem übernommenen Text gelesen und leer, wenn er sich
  nicht lesen lässt;
- den **übernommenen Text** unter dem Schlüssel mit angehängtem `_raw`;
- bei Daten und Zeiträumen die **Genauigkeit** (`day`, `month`, `quarter` oder `year`) unter dem Schlüssel mit
  angehängtem `_precision`, damit „März 2025“ nie für den 1. März gehalten wird.

Jedes Attribut des Typs ist vorhanden und leer, wo es unbekannt ist. Ein Filter sollte einen leeren Wert als unbekannt
behandeln, nicht als Nichtübereinstimmung. Ein Attribut, das für einen Typ nicht gilt, wird bei Dokumenten dieses Typs
nicht gespeichert.

Regeln, die verhindern, dass Werte geraten werden:

- **Nicht im Dokument, nicht gespeichert.** Text, den das Modell übernommen hat, der im Dokument aber nicht vorkommt,
  wird verworfen.
- **Mehrdeutige Daten bleiben leer.** `03/04/2025` kann März oder April sein, daher wird nur der Text aufbewahrt. Daten
  mit Punkten oder Bindestrichen werden mit dem Tag zuerst gelesen; ein Datum mit Schrägstrichen nur, wenn eine
  Reihenfolge unmöglich ist.
- **Steuer-IDs werden geprüft.** Eine Schweizer UID muss ihre Prüfziffer bestehen. Eine EU-MWST-Nummer muss dem Format
  ihres Landes entsprechen. Eine deutsche Steuernummer hat keine einheitliche Form und wird nur als Text aufbewahrt.
- **Beträge in jeder Schreibweise.** `12'496.36`, `12.496,36`, `12 496,36` und `12,496.36` sind derselbe Betrag; das
  Schweizer `1'250.–` ist 1250.00. Ein negativer Endbetrag behält sein Vorzeichen. Ein alleinstehendes `$` wird nicht
  als Währung gelesen.

Jedes Dokument hält zudem `document_classification_version` und `document_normalizer_version` fest. Wenn sich die Liste
der Typen oder die Bedeutung eines Attributs ändert, steigt die Klassifizierungsversion und die Dokumente werden erneut
klassifiziert. Wenn nur das Lesen des übernommenen Texts besser wird, steigt die Normalizer-Version und die Werte werden
aus dem gespeicherten Text erneut gelesen, ohne ein Modell zu fragen.
