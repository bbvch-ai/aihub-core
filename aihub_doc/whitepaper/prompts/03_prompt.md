# Kapitel 03: Datensouveränität und vollständige Kundenkontrolle

## Kapitelziel

Dieses Kapitel legt dar, wie die Auftraggeber die uneingeschränkte Hoheit über sämtliche Daten und Informationsflüsse
wahren, unabhängig vom gewählten Betriebsmodell. Es wird aufgezeigt, wie durch strikte Trennung von Datenhaltung und
Verarbeitungsprozessen sichergestellt wird, dass strengste Vorgaben zur Data Residency jederzeit erfüllt und
kontrolliert werden können. Ein zentraler Schwerpunkt liegt auf der Befähigung der Organisation, das Verhalten der
eingesetzten KI-Modelle transparent zu steuern und die Nachvollziehbarkeit der Ergebnisse zu garantieren, um
intransparente Entscheidungsprozesse („Black-Box“-Effekte) systematisch auszuschließen. Des Weiteren wird der Nachweis
erbracht, dass die Systemarchitektur durch Standardisierung und Interoperabilität eine maximale technologische
Unabhängigkeit gewährleistet. Ziel ist es, aufzuzeigen, wie Risiken eines Vendor-Lock-ins eliminiert werden und eine
langfristige Investitionssicherheit sowie strategische Handlungsfähigkeit für die öffentliche Verwaltung sichergestellt
wird.

## Kernaussagen

- Garantierte Datenresidenz: Die Plattformarchitektur ermöglicht den Betrieb in vollständig isolierten Umgebungen
  (Air-Gap) oder im eigenen Rechenzentrum, wodurch sichergestellt wird, dass Daten den definierten Rechtsraum (z. B.
  Schweiz) physisch niemals verlassen.
- Ausschluss externer Zugriffe: Im Gegensatz zu SaaS-Modellen verbleibt die operative Hoheit vollständig bei der
  auftraggebenden Organisation; der Plattformanbieter hat keinen technischen oder administrativen Zugriff auf
  verarbeitete Inhalte oder die Wissensdatenbanken.
- Unabhängigkeit von Modell-Anbietern: Die Plattform entkoppelt die Anwendungsebene von den KI-Modellen, sodass die
  Organisation frei entscheiden kann, welche LLMs (Proprietär oder Open Source) eingesetzt werden, ohne strategische
  Abhängigkeiten von einzelnen US-Hyperscalern einzugehen.
- Vermeidung von Vendor-Lock-in: Durch die Speicherung von Vektordaten und Konfigurationen in offenen, standardisierten
  Formaten wird verhindert, dass Unternehmenswissen in proprietären Datensilos gefangen ist; ein Systemwechsel oder
  Datenexport ist jederzeit möglich.
- Nachhaltige Investitionssicherheit: Die Modularität der Architektur stellt sicher, dass bei Marktaustritt eines
  Teilanbieters oder bei technologischen Paradigmenwechseln einzelne Komponenten (wie Vektor-Stores oder LLMs)
  ausgetauscht werden können, ohne die gesamte Lösung neu aufbauen zu müssen.

## Umfang

max. 1200 Wörter, 4 Seiten

## Business-Fragen, die das Kapitel beantwortet

- Welche Deployment-Optionen bietet die Plattform zur Sicherstellung der Datensouveränität?
- Kann die Plattform vollständig in der Schweiz betrieben werden, ohne dass Daten ins Ausland übertragen werden?
- Unterstützt die Plattform On-Premise-Deployment mit unseren bestehenden Datenbanken (MSSQL, Oracle, PostgreSQL)?
- Was ist Air-Gap-Betrieb und wann ist er erforderlich?
- Wie stellt die Plattform sicher, dass keine Daten unkontrolliert die Schweiz verlassen?
- Können wir verschiedene Deployment-Modelle für unterschiedliche Datensensitivitäten kombinieren?
- Wer kontrolliert die Administration der Plattform – wir oder der Anbieter?
- Wie funktioniert die rollenbasierte Zugriffskontrolle (RBAC) und welche Rollen sind verfügbar?
- Welche Kontrolle habe ich über Datenquellen und RAG-Konfigurationen?
- Kann ich kontrollieren, welche AI-Modelle verwendet werden und wie sie trainiert werden?
- Wie stelle ich sicher, dass AI-Entscheidungen von Menschen überprüft werden können (Human-in-the-Loop)?
- Welche Governance-Mechanismen sind eingebaut (Feedback, Bias-Monitoring)?
- Wie erfüllt die Plattform revDSG-Anforderungen?
- Unterstützt die Plattform Anonymisierung sensibler Daten (PII-Erkennung)?
- Wie wird Consent-Management gehandhabt?
- Können Daten vollständig gelöscht werden (Right to be Forgotten / Art. 17 DSGVO)?
- Wie werden Audit-Trails für Compliance-Nachweise bereitgestellt?
- Unterstützt die Plattform Data Lineage für regulatorische Audits?
- Wie integriert sich die Plattform mit eGov-Portalen und staatlichen Identitätssystemen?
- Verhindert die Architektur Vendor Lock-in?
- Können einzelne Komponenten (Datenbank, Vector-Store, LLM-Provider) ausgetauscht werden?
- Basiert die Plattform auf offenen Standards oder proprietären Technologien?
- Sind unsere Daten jederzeit exportierbar und in anderen Systemen nutzbar?
- Kann ich mehrere LLM-Anbieter gleichzeitig nutzen?
