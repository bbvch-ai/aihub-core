---
title: Dokumenttypen und Attribute
source_sha: 24866a04322fac27389742517d1fd2dd24cf9376e49ed09b4408404d58bf6c81
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

| Typ                       | Ein Dokument dieses Typs…                                                                                                                                                                                                                  |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `invoice`                 | fordert die Bezahlung von Waren oder Dienstleistungen, die geliefert oder vereinbart wurden. Dazu gehören Teil-, Schluss- und Akontorechnungen, QR-Rechnungen sowie Strom- und Telekomrechnungen.                                          |
| `credit_note`             | mindert, storniert oder vergütet einen Betrag, statt einen zu fordern: Gutschriften, Stornorechnungen, Rechnungskorrekturen mit negativem Total und eine Gutschrift nach § 14 UStG.                                                        |
| `offer`                   | bietet Waren oder Dienstleistungen zu einem genannten Preis an, bevor sie bestellt sind: Angebote, Offerten, Kostenvoranschläge und Proforma-Rechnungen.                                                                                   |
| `order`                   | erteilt oder bestätigt eine Bestellung: Bestellungen des Käufers und Auftragsbestätigungen des Lieferanten.                                                                                                                                |
| `delivery_note`           | begleitet gelieferte Ware oder bestätigt ihre Lieferung: Lieferscheine und Packlisten.                                                                                                                                                     |
| `receipt`                 | bestätigt eine bereits geleistete Zahlung: Kassenbons, Quittungen und Zahlungsbestätigungen.                                                                                                                                               |
| `account_statement`       | listet Bewegungen, Saldo oder offene Posten eines Kontos auf: Bank- und Kreditkartenauszüge sowie der Auszug offener Posten eines Lieferanten.                                                                                             |
| `payment_reminder`        | fordert die Bezahlung überfälliger Rechnungen: Zahlungserinnerungen, Mahnungen und Überfälligkeitsmitteilungen.                                                                                                                            |
| `contract`                | hält eine Vereinbarung zwischen benannten Parteien fest: Verträge, Rahmen-, Arbeits-, Miet- und Lizenzverträge sowie Nachträge.                                                                                                            |
| `service_level_agreement` | legt die Service Levels fest, die ein Anbieter zusagt, etwa Verfügbarkeit und Reaktionszeiten: ein eigenständiges SLA oder ein SLA-Anhang.                                                                                                 |
| `letter`                  | ist ein einzelner Brief oder eine einzelne E-Mail ohne anderen Typ: Mitteilungen, Anfragen, Bestätigungen, Kündigungen und Einladungen.                                                                                                    |
| `report`                  | berichtet über Ergebnisse, Stand oder Befunde: Jahres- und Quartalsberichte, Projektstatus-, Prüf- und Inspektionsberichte.                                                                                                                |
| `documentation`           | erklärt, wie man ein Produkt, ein System oder einen Ablauf installiert, nutzt, betreibt oder wartet: Handbücher, Anleitungen, Leitfäden, technische Dokumentationen und Spezifikationen, technisch oder nicht.                             |
| `policy`                  | setzt Regeln, die Mitarbeitende, Mitglieder oder Kundinnen und Kunden befolgen müssen: Reglemente, Richtlinien, Weisungen, Verhaltenskodizes, Personalhandbücher, die Arbeitszeit oder Ferien regeln, und Allgemeine Geschäftsbedingungen. |
| `email_thread`            | ist ein Verlauf mehrerer E-Mails, Antworten oder Weiterleitungen in einem Dokument, etwa ein exportierter Thread oder ein Postfachverlauf.                                                                                                 |
| `other`                   | ist alles andere, zum Beispiel Protokolle, Präsentationen, Formulare und Ausschreibungen.                                                                                                                                                  |

Eine Schlussrechnung bleibt eine Rechnung, wenn die abgezogenen Akontozahlungen ihr Total negativ machen; eine Korrektur
einer früheren Rechnung mit negativem Total ist eine Gutschrift. Ein QR-Zahlteil allein, ohne seine Rechnung, ist
`other`. Ein Angebot, eine Bestellung, eine Rechnung oder ein Vertrag in Briefform ist von diesem Typ, nicht ein Brief.
Ein Verlauf mehrerer E-Mails ist ein `email_thread`; eine einzelne E-Mail ist ein `letter`. Ein Reglement, eine
Richtlinie oder eine Weisung, die Regeln setzt, ist eine `policy`, nicht `documentation`, auch mit Versionsnummer oder
wenn sie erklärt, was zu tun ist; ebenso ein Personal- oder Mitarbeiterhandbuch, auch wenn es erklärt, wie man Ferien
beantragt oder sich krank meldet. Allgemeine Geschäftsbedingungen, die nicht zwischen genannten Parteien vereinbart
sind, sind eine `policy`, kein `contract`, und ein Anhang, der Service Levels zusagt, ist ein `service_level_agreement`,
auch wenn er Leistungsbeschreibung heisst.

Ein Dokument hat einen **primären Typ**, nämlich den, der es als Ganzes beschreibt. Es kann zusätzlich bis zu drei
**sekundäre Typen** aufführen, zum Beispiel eine Rechnung, die zugleich ihr Lieferschein ist, oder ein Vertrag mit
SLA-Anhang (`contract`, mit `service_level_agreement` als sekundärem Typ). Attribute gehören immer zum primären Typ; ein
sekundärer Typ macht das Dokument nur zusätzlich unter diesem Typ auffindbar. Ein Dokument, das die Nummer eines anderen
Dokuments lediglich erwähnt, ist nicht vom Typ dieses Dokuments.

## Attribute je Typ

Attribute sind über die Typen hinweg gemeinsam, sodass ein Filter wie «datiert 2025» oder «Aussteller Hooli AG» bei
jedem Typ wirkt, der das Attribut hat. Jeder Typ hat nur die Attribute, die für ihn sinnvoll sind:

| Attribut                      | Rechnung, Gutschrift | Offerte | Bestellung | Lieferschein | Quittung | Auszug | Mahnung | Vertrag | SLA | Brief | Bericht | Dokumentation | Reglement | E-Mail-Verlauf |
| ----------------------------- | :------------------: | :-----: | :--------: | :----------: | :------: | :----: | :-----: | :-----: | :-: | :---: | :-----: | :-----------: | :-------: | :------------: |
| `document_date`               |          ✓           |    ✓    |     ✓      |      ✓       |    ✓     |   ✓    |    ✓    |    ✓    |  ✓  |   ✓   |    ✓    |       ✓       |     ✓     |       ✓        |
| `document_reference_number`   |          ✓           |    ✓    |     ✓      |      ✓       |    ✓     |   ✓    |    ✓    |    ✓    |  ✓  |   ✓   |         |       ✓       |     ✓     |                |
| `document_issuer`             |          ✓           |    ✓    |     ✓      |      ✓       |    ✓     |   ✓    |    ✓    |    ✓    |  ✓  |   ✓   |    ✓    |       ✓       |     ✓     |                |
| `document_issuer_tax_id`      |          ✓           |    ✓    |     ✓      |              |    ✓     |        |         |         |     |       |         |               |           |                |
| `document_recipient`          |          ✓           |    ✓    |     ✓      |      ✓       |    ✓     |   ✓    |    ✓    |    ✓    |  ✓  |   ✓   |         |               |           |                |
| `document_parties`            |          ✓           |    ✓    |     ✓      |      ✓       |    ✓     |   ✓    |    ✓    |    ✓    |  ✓  |   ✓   |         |               |           |       ✓        |
| `document_total_amount`       |          ✓           |    ✓    |     ✓      |              |    ✓     |   ✓    |    ✓    |    ✓    |     |       |         |               |           |                |
| `document_currency`           |          ✓           |    ✓    |     ✓      |              |    ✓     |   ✓    |    ✓    |    ✓    |     |       |         |               |           |                |
| `document_due_date`           |          ✓           |         |     ✓      |              |          |   ✓    |    ✓    |         |     |       |         |               |           |                |
| `document_period_start`/`end` |          ✓           |         |            |              |          |   ✓    |         |    ✓    |  ✓  |       |    ✓    |               |           |                |
| `document_related_references` |          ✓           |    ✓    |     ✓      |      ✓       |    ✓     |        |    ✓    |    ✓    |  ✓  |   ✓   |         |               |           |       ✓        |
| `document_valid_until`        |                      |    ✓    |            |              |          |        |         |         |     |       |         |               |           |                |
| `document_notice_period`      |                      |         |            |              |          |        |         |    ✓    |  ✓  |       |         |               |           |                |
| `document_service_levels`     |                      |         |            |              |          |        |         |         |  ✓  |       |         |               |           |                |
| `document_product`            |                      |         |            |              |          |        |         |         |     |       |         |       ✓       |           |                |
| `document_participants`       |                      |         |            |              |          |        |         |         |     |       |         |               |           |       ✓        |
| `document_jurisdiction`       |                      |         |            |              |          |        |         |    ✓    |  ✓  |       |         |               |     ✓     |                |

Wo ein Attribut für einen Typ etwas Bestimmtes bedeutet:

- **Aussteller und Empfänger.** Der Aussteller ist die Partei, die das Dokument sendet; der Empfänger die Partei, an die
  es gerichtet ist. Bei einer Bestellung ist der Aussteller der Käufer, bei einer Auftragsbestätigung der Lieferant. Bei
  einem Vertrag oder SLA ist der Aussteller die Partei, welche die Ware, Leistung, Räume, Lizenz oder Stelle
  bereitstellt (Lieferant, Auftragnehmer, Vermieter, Lizenzgeber, Arbeitgeber, Dienstleister), der Empfänger die andere
  Partei. Bei einer Quittung ist der Aussteller der Händler und der Empfänger der Zahlende, nur wenn er genannt ist. Bei
  einer Gutschrift nach § 14 UStG ist der Aussteller der Käufer, der sie ausstellt. Bei einer Dokumentation ist der
  Aussteller der Hersteller, Herausgeber oder die Organisation, die sie verfasst hat, oder die Autorin oder der Autor,
  wenn keine Organisation genannt ist. Bei einem Reglement ist der Aussteller die Organisation, welche die Regeln setzt.
- **Total.** Bei einer Gutschrift der gutgeschriebene Betrag mit seinem Vorzeichen wie geschrieben; bei einem Auszug der
  Schlusssaldo oder der fällige Betrag; bei einer Mahnung der jetzt zu zahlende Betrag inklusive Gebühren und Zinsen;
  bei einem Vertrag der Vertragswert oder sonst die wiederkehrende Gebühr, Miete oder der Lohn.
- **Fälligkeitsdatum.** Bei einer Bestellung das Lieferdatum; bei einer Mahnung die neue Zahlungsfrist; bei einer
  Gutschrift das Datum, an dem sie ausbezahlt wird.
- **Referenznummer.** Die eigene Nummer eines Auszugs, nie eine Kontonummer oder IBAN; die eigene Nummer einer Mahnung,
  nie die Nummer der gemahnten Rechnung (diese ist eine verwandte Referenz); die eigene Referenz eines Briefs, etwa
  «Unser Zeichen»; bei einer Dokumentation oder einem Reglement die Dokumentnummer, und nur wenn es keine gibt, die
  Versions- oder Release-Nummer ohne das Wort «Version».
- **Datum.** Bei einer Dokumentation ihr Erscheinungs- oder Revisionsdatum; bei einem Reglement das Datum, ab dem es
  gilt, sonst sein Ausgabe- oder Revisionsdatum; bei einem E-Mail-Verlauf das Datum der neuesten Nachricht.
- **Zeitraum.** Bei einem Vertrag oder SLA seine Laufzeit. Ein einzelnes Datum ist der ganze Zeitraum, ausser ein Wort
  daneben sagt, welches Ende es ist: Ein Vertrag, der an einem Datum beginnt und bis zur Kündigung läuft («ab 1. Juli
  2025», «tritt am 1. März 2026 in Kraft», «prend effet le», «from»), speichert nur seinen Beginn, und einer, der nur
  sein Ende nennt («endet am 30. Juni 2027», «until»), nur sein Ende. Es zählen nur Wörter im Satz des Datums. So findet
  «Verträge, die 2026 enden» jeden Vertrag, der sein Ende nennt, und das Unterzeichnungsdatum ist nie sein Beginn. Ein
  Vertrag, der Beginn und Ende auf eigenen Zeilen nennt («Vertragsbeginn 1. April 2025», «Vertragsende 31. März 2028»),
  behält beide, sofern jedes Datum, das das Modell nennt, im Dokument steht; ein Wort, das das Modell einem Datum
  hinzufügt, wird nicht gelesen, nur die eigene Zeile des Datums. Der Zeitraum jedes anderen Typs bleibt ganz, welche
  Wörter auch daneben stehen.
- **Gültig bis**, **Kündigungsfrist** und **Service Levels** sind mit diesen Typen neu: das Datum, bis zu dem eine
  Offerte gilt; die Kündigungsfrist eines Vertrags oder SLA, wie geschrieben aufbewahrt; und bis zu fünf Service Levels,
  die ein SLA zusagt, wie geschrieben übernommen («Verfügbarkeit 99,9 % pro Monat»).
- **Produkt** gilt nur für Dokumentationen: das Produkt, System oder die Dienstleistung, die sie dokumentiert, mit dem
  Namen wie geschrieben, sodass ein Filter «die Handbücher zur AquaTherm WP 12» findet. Leer, wenn sie keines nennt;
  weder ein beschriebener Arbeitsablauf noch der eigene Titel eines Handbuchs ist ein Produkt.
- **Beteiligte** gilt nur für E-Mail-Verläufe: bis zu zehn Personen und Organisationen, die eine Nachricht des Verlaufs
  senden oder empfangen, mit dem Namen, den eine Kopfzeile oder Signatur angibt, einschliesslich des Unternehmens, das
  eine Signatur für eine Person nennt. Eine E-Mail-Adresse oder eine Domain ist nie ein Beteiligter.
- **Gerichtsstand** gilt für Verträge, SLAs und Reglemente: der Gerichtsstand für Streitigkeiten wie geschrieben
  (Gerichtsstand, for, foro, courts of), etwa «Luzern». Ein anwendbares Recht allein («Es gilt schweizerisches Recht»),
  die Adresse einer Partei und der Ort der Unterzeichnung sind kein Gerichtsstand: Der Code behält einen Ort nur, wo
  seine Zeile oder die Überschrift darüber ein Gericht nennt.
- **Parteien** führt Aussteller und Empfänger auf, oder die Beteiligten eines E-Mail-Verlaufs, sodass ein einziger
  Parteien-Filter die Rechnungen, Verträge und Korrespondenz eines Unternehmens gleichermassen findet.

Die Typen und ihre Bedeutungen folgen [UBL 2.1](https://docs.oasis-open.org/ubl/os-UBL-2.1/UBL-2.1.html) und den
Peppol-Dokumenten [Gutschrift](https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-creditnote/tree/),
[Bestellung](https://docs.peppol.eu/poacc/upgrade-3/syntax/Order/tree/),
[Bestellantwort](https://docs.peppol.eu/poacc/upgrade-3/syntax/OrderResponse/tree/) und
[Lieferavis](https://docs.peppol.eu/poacc/upgrade-3/syntax/DespatchAdvice/tree/), den
Azure-Document-Intelligence-Modellen für
[Quittungen](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/prebuilt/receipt),
[Kontoauszüge](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/prebuilt/bank-statement) und
[Verträge](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/prebuilt/contract), dem
Vertragsdatensatz [CUAD](https://www.atticusprojectai.org/cuad), dem Schweizer Obligationenrecht zum Verzug
([Art. 102 OR](https://www.fedlex.admin.ch/eli/cc/27/317_321_377/de#art_102)) und den
[EU-Leitlinien zur Standardisierung von Cloud-SLAs](https://digital-strategy.ec.europa.eu/en/news/cloud-service-level-agreement-standardisation-guidelines).

### E-Mail-Verläufe und Personendaten

Beteiligte sind Namen von Personen und werden wie geschrieben gespeichert, wie der Empfänger eines Briefs. Ein aus einem
internen Postfach exportierter Verlauf legt deshalb Namen von Mitarbeitenden in den Filter-Metadaten jedes Chunks ab.
Ist das Textmodell der Wissensdatenbank ein externes Modell hinter dem PII-Guardrail, sieht das Modell `<PERSON_1>`
statt eines Namens; dieser Platzhalter steht nicht im Dokument, wird daher verworfen, und die Beteiligten bleiben leer.
Ob Beteiligte interner E-Mails überhaupt gespeichert werden sollen, ist ein offener Entscheid der oder des
Datenschutzverantwortlichen.

## Attribute von Rechnungen im Detail

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
- Dokumente, die aufgenommen wurden, bevor es die Klassifizierung gab oder bevor sich die Liste der Typen änderte,
  klassifiziert ein Backfill aus dem bereits gespeicherten Text, ohne sie erneut zu parsen oder einzubetten. Er läuft,
  wenn er für eine Wissensdatenbank angefordert wird; hat sich nur das Lesen übernommener Werte verbessert, liest er die
  gespeicherten Kopien erneut, ohne ein Modell zu fragen. Eine Wissensadministratorin oder ein Wissensadministrator
  fordert ihn mit **Bestehende Dokumente klassifizieren** an (die Etiketten-Schaltfläche neben dem Namen der Datenbank
  auf der Seite Wissen). Solange die Anforderung auf die Pipeline wartet, wird stattdessen eine Uhr angezeigt. Jedes
  Dokument, das noch einen Typ braucht, kostet einen Modellaufruf. Schlägt der Backfill dreimal hintereinander fehl,
  etwa weil ein Speicher nicht erreichbar ist, wird er abgebrochen, und ein Warnzeichen neben der Schaltfläche weist
  darauf hin; eine erneute Anforderung beginnt von vorn.
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
  angehängtem `_precision`, damit „März 2025“ nie für den 1. März gehalten wird. Bei einem Zeitraum beschreibt sie jedes
  gespeicherte Ende: Eine Laufzeit „ab März 2025“ speichert ihren Beginn mit Monatsgenauigkeit und kein Ende.

Jedes Attribut des Typs ist vorhanden und leer, wo es unbekannt ist. Ein Filter sollte einen leeren Wert als unbekannt
behandeln, nicht als Nichtübereinstimmung. Ein Attribut, das für einen Typ nicht gilt, wird bei Dokumenten dieses Typs
nicht gespeichert.

Regeln, die verhindern, dass Werte geraten werden:

- **Nicht im Dokument, nicht gespeichert.** Text, den das Modell übernommen hat, der im Dokument aber nicht vorkommt,
  wird verworfen.
- **Eine Lücke einer Vorlage ist kein Wert.** Eine Kopie mit einem nicht ausgefüllten Platzhalter (`[YYYY]`, `[####]`,
  `______`, ein leeres Kästchen) wird leer gespeichert, damit eine halb ausgefüllte Vorlage nicht «NW-SLA-[YYYY]-[####]»
  als Nummer erhält.
- **Gespeicherter Text verwendet einfache Buchstaben.** Eine Ligatur, die ein PDF als ein Zeichen schreibt («ﬀ» in
  «Schaﬀhausen»), wird als ihre Buchstaben gespeichert, sodass ein Filter auf «Schaffhausen» sie findet; der kopierte
  Text bleibt wie geschrieben.
- **Mehrdeutige Daten werden nur in der Reihenfolge des Dokuments gelesen.** Daten mit Punkten oder Bindestrichen werden
  mit dem Tag zuerst gelesen. Ein Datum mit Schrägstrichen wie `03/04/2025` kann März oder April sein. Die übrigen
  Schrägstrich-Daten des Dokuments entscheiden, wenn eines davon nur eine Reihenfolge zulässt (`17/11/2025`: Tag zuerst,
  `11/17/2025`: Monat zuerst). Gibt es kein solches Datum, wird mit dem Tag zuerst gelesen, wenn die Währung des
  Dokuments CHF, EUR oder eine andere Nicht-Dollar-Währung ist, da der Monat zuerst die US-Reihenfolge ist. Bei USD,
  einem alleinstehenden `$`, ohne Währung oder bei widersprüchlichen Schrägstrich-Daten bleibt es leer, und nur der Text
  wird aufbewahrt.
- **Ein Name ist nie eine E-Mail-Adresse.** Eine E-Mail-Adresse, die mit einem Aussteller, Empfänger oder Beteiligten
  übernommen wurde, wird aus dem gespeicherten Namen entfernt («Anna Meier <anna@example.ch>» wird als «Anna Meier»
  gespeichert), und eine ohne Namen übernommene wird leer gespeichert, ihr Text bleibt erhalten: Die Adresse bezeichnet
  ein Postfach, nicht eine Partei. Ebenso wird ein Name verworfen, den das Dokument nur innerhalb einer E-Mail-Adresse
  schreibt («Northpeak» aus billing@northpeak.example).
- **Steuer-IDs werden geprüft.** Eine Schweizer UID muss ihre Prüfziffer bestehen. Eine EU-MWST-Nummer muss dem Format
  ihres Landes entsprechen. Eine deutsche Steuernummer hat keine einheitliche Form und wird nur als Text aufbewahrt.
- **Beträge in jeder Schreibweise.** `12'496.36`, `12.496,36`, `12 496,36` und `12,496.36` sind derselbe Betrag; das
  Schweizer `1'250.–` ist 1250.00. Ein negativer Endbetrag behält sein Vorzeichen, wenn das Minus direkt an der Zahl
  steht (`-500`, `CHF -500`, `500-`) oder Klammern nur die Zahl umschliessen (`(500.00)`); ein Gedankenstrich mit
  Leerzeichen (`Betrag - CHF 500`) oder ein eingeklammerter Betrag mit Währung (`Total (CHF 500.00)`) ist kein
  Vorzeichen. Nennt ein Betrag zwei Währungen, gilt die zuerst geschriebene. Ein alleinstehendes `$` wird nicht als
  Währung gelesen.

Jedes Dokument hält zudem die Versionen fest, mit denen es klassifiziert wurde, damit eine spätere Änderung nur die
Dokumente erneut bearbeitet, die sie betreffen kann:

- `document_type_version`: die Version des eigenen Typs des Dokuments. Ändert sich die Definition eines Typs, werden nur
  Dokumente dieses Typs erneut klassifiziert. Ein neuer Typ ändert die Bedeutung von `other`, daher werden nur die als
  `other` markierten Dokumente erneut klassifiziert.
- `document_classification_version`: steigt bei einer Änderung, die jedes Dokument betreffen kann, etwa der Bedeutung
  eines gemeinsamen Attributs; dann werden alle Dokumente erneut klassifiziert.
- `document_normalizer_version`: steigt, wenn nur das Lesen des übernommenen Texts besser wird; die Werte werden aus dem
  gespeicherten Text erneut gelesen, ohne ein Modell zu fragen.
