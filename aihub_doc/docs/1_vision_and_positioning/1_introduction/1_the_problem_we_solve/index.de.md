---
title: Das Problem, das wir lösen
source_sha: 0ae9f2b91e8cd30df8cb8d5d7f4684624215b4732d65a90204fc9479a08a5d60
---

# Das Problem, das wir lösen

KI-Anwendungen zu erstellen ist einfach. Produktionsreife KI-Systeme zu erstellen ist schwer.

Wenn Sie mit KI-Tools gearbeitet haben, kennen Sie dieses Muster: Sie können an einem Nachmittag eine beeindruckende
Demo mit LangChain erstellen. Eine Woche später haben Sie einen funktionierenden Prototyp. Dann stellt jemand die
schwierigen Fragen:

- Wie deployen wir das?
- Wo bleiben unsere Daten?
- Können wir verfolgen, was die KI tut?
- Wie kontrollieren wir die Kosten?
- Was passiert, wenn es fehlschlägt?
- Wie greifen Benutzer tatsächlich darauf zu?
- Können wir es in unsere bestehenden Tools integrieren?

Plötzlich benötigt Ihr eleganter Prototyp Authentifizierung, Monitoring, Datenpipelines, Vektordatenbanken,
Kostenkontrollen, Audit-Trails, Benutzeroberflächen und Unternehmensintegrationen. Sie bauen keine KI-Lösung mehr – Sie
bauen Infrastruktur.

## Die Infrastrukturlücke

Aktuelle KI-Entwicklungstools fallen in zwei Kategorien:

**Bibliotheken und Frameworks** wie LangChain, LlamaIndex und Semantic Kernel helfen Ihnen, Agenten schnell zu
erstellen. Sie handhaben die KI-Logik gut, sind aber nur Codebibliotheken. Sie müssen immer noch Bereitstellung,
Skalierung, Überwachung und alles andere herausfinden, was Software produktionsreif macht.

**Cloud-KI-Dienste** wie Azure AI Studio oder Google Vertex AI stellen Infrastruktur bereit, aber sie binden Sie an ihr
Ökosystem. Ihre Daten liegen auf ihren Servern, Sie zahlen deren Margen auf Dauer, und Sie können die Plattform nicht
anpassen, wenn sie Ihren Anforderungen nicht entspricht.

Keiner der Ansätze löst das eigentliche Problem, mit dem Unternehmen konfrontiert sind: **Wie gelangen Sie von
KI-Experimenten zu Produktionssystemen, ohne entweder alles von Grund auf neu zu bauen oder die Kontrolle an einen
Anbieter abzugeben?**

## Die Schweizer Unternehmensherausforderung

Für Schweizer Organisationen werden diese Herausforderungen durch spezifische Anforderungen noch verstärkt:

::: warning Anforderungen an die Datenhoheit
Schweizer Datenschutzgesetze und Unternehmensrichtlinien verlangen oft, dass sensible Daten innerhalb der Schweizer
Grenzen bleiben. Die meisten KI-Plattformen können dies nicht garantieren – sie verarbeiten Daten dort, wo ihre
Infrastruktur läuft.
:::

Der typische Verlauf sieht so aus:

1. **Experimente blockiert**: Die IT genehmigt ChatGPT oder Claude nicht, weil Daten das Unternehmen verlassen.
2. **Lokale Versuche scheitern**: Teams versuchen, Open-Source-Modelle lokal auszuführen, aber es fehlt ihnen an der
   Infrastruktur.
3. **Anbieterbewertung stagniert**: Unternehmens-KI-Plattformen sind teuer, komplex und lösen das Problem der
   Datenresidenz immer noch nicht.
4. **Kundenspezifische Entwicklung überfordert**: Der Aufbau von Grund auf erfordert Fachwissen, das die Organisation
   nicht besitzt.

Organisationen stecken in einer Schleife fest: Sie können bestehende Lösungen aufgrund von Compliance nicht nutzen, aber
sie können ihre eigenen aufgrund der Komplexität nicht aufbauen.

## Die wahren Kosten der Fragmentierung

Wenn es Organisationen gelingt, KI zu deployen, enden sie oft mit einer fragmentierten Landschaft:

- **Team A** verwendet Azure OpenAI über Python-Skripte.
- **Team B** hat ein RAG-System mit LlamaIndex aufgebaut, das nur sie verstehen.
- **Team C** hat einen Chatbot, den niemand mehr pflegt.
- **Die Finanzabteilung** möchte eine Kostenverfolgung für die gesamte KI-Nutzung.
- **Die IT** möchte eine standardisierte Bereitstellung und Überwachung.
- **Compliance** wünscht sich Audit-Trails und Daten-Governance.

Jedes Team löst sein unmittelbares Problem, schafft aber neue. Es gibt keine gemeinsame Infrastruktur, keine konsistente
Governance, keinen einheitlichen Ansatz. Die Organisation verfügt über KI-Fähigkeiten, aber nicht über eine
KI-Plattform.

## Was Organisationen wirklich brauchen

Die Anforderungen sind klar:

1. **Komplette Infrastruktur**, die Bereitstellung, Überwachung und Skalierung übernimmt – nicht nur die KI-Logik.
2. **Datenhoheit** mit der Option, alles On-Premise oder in Schweizer Rechenzentren zu betreiben.
3. **Offenheit und Kontrolle**, um bestehende Systeme zu modifizieren, zu erweitern und zu integrieren.
4. **Produktionsreife** mit integrierter Unternehmensauthentifizierung, Audit-Trails und Kostenkontrollen.
5. **Eine einheitliche Plattform**, auf der verschiedene Teams aufbauen können, ohne Silos zu schaffen.

Dies ist die Lücke, die der Swiss AI Hub füllt. Anstatt sich zwischen dem Selbstbau von allem und der Akzeptanz von
Vendor Lock-in zu entscheiden, erhalten Sie eine komplette Plattform, die Sie besitzen und kontrollieren. Eine, die für
die Realitäten der KI-Bereitstellung in Unternehmen konzipiert ist, nicht nur für die Begeisterung der KI-Entwicklung.
