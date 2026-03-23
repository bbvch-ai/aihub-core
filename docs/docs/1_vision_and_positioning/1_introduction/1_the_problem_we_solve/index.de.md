---
title: Das Problem, das wir lösen
source_sha: 4314a00596ef5b60da31b5a27ec45f80d756f7a914d20e9fcf9933ff2683ab15
---

# Das Problem, das wir lösen

KI-Anwendungen zu erstellen ist einfach. Produktionsreife KI-Systeme zu bauen ist schwer.

Wenn Sie mit KI-Tools gearbeitet haben, kennen Sie dieses Muster: Sie können an einem Nachmittag eine beeindruckende
Demo mit LangChain erstellen. Eine Woche später haben Sie einen funktionierenden Prototyp. Dann stellt jemand die
schwierigen Fragen:

- Wie deployen wir das?
- Wo bleiben unsere Daten?
- Können wir nachverfolgen, was die KI tut?
- Wie kontrollieren wir die Kosten?
- Was passiert, wenn es fehlschlägt?
- Wie greifen Benutzer tatsächlich darauf zu?
- Können wir es in unsere bestehenden Tools integrieren?

Plötzlich benötigt Ihr eleganter Prototyp Authentifizierung, Monitoring, Daten-Pipelines, Vektordatenbanken,
Kostenkontrollen, Audit-Trails, Benutzeroberflächen und Unternehmensintegrationen. Sie bauen keine KI-Lösung mehr – Sie
bauen Infrastruktur.

## Die Infrastrukturlücke

Aktuelle KI-Entwicklungstools fallen in zwei Kategorien:

**Bibliotheken und Frameworks** wie LangChain, LlamaIndex und Semantic Kernel helfen Ihnen, Agents schnell zu erstellen.
Sie handhaben die KI-Logik gut, sind aber nur Code-Bibliotheken. Sie müssen immer noch das Deployment, die Skalierung,
das Monitoring und alles andere, was Software produktionsreif macht, herausfinden.

**Cloud KI-Services** wie Azure AI Studio oder Google Vertex AI bieten Infrastruktur, sperren Sie aber in deren
Ökosystem ein. Ihre Daten leben auf deren Servern, Sie zahlen deren Margen für immer und Sie können die Plattform nicht
anpassen, wenn sie nicht Ihren Anforderungen entspricht.

Keiner der Ansätze löst das eigentliche Problem, mit dem Unternehmen konfrontiert sind: **Wie gelangen Sie von
KI-Experimenten zu Produktionssystemen, ohne entweder alles von Grund auf neu zu bauen oder die Kontrolle an einen
Anbieter abzugeben?**

## Die Schweizer Unternehmensherausforderung

Für Schweizer Organisationen werden diese Herausforderungen durch spezifische Anforderungen noch verschärft:

::: warning Anforderungen an die Datenhoheit
Schweizer Datenschutzgesetze und Unternehmensrichtlinien verlangen oft, dass sensible Daten innerhalb der Schweizer
Grenzen bleiben. Die meisten KI-Plattformen können dies nicht garantieren – sie verarbeiten Daten dort, wo ihre
Infrastruktur läuft.
:::

Der typische Weg sieht wie folgt aus:

1. **Experimente blockiert**: Die IT wird ChatGPT oder Claude nicht genehmigen, weil Daten das Unternehmen verlassen.
2. **Lokale Versuche scheitern**: Teams versuchen, Open-Source-Modelle lokal auszuführen, aber es fehlt ihnen an der
   Infrastruktur.
3. **Anbieterbewertung stockt**: Enterprise KI-Plattformen sind teuer, komplex und lösen immer noch nicht das Problem
   der Datenresidenz.
4. **Eigenentwicklung überfordert**: Der Aufbau von Grund auf erfordert Expertise, die die Organisation nicht besitzt.

Organisationen stecken in einer Schleife fest: Sie können bestehende Lösungen aufgrund der Compliance nicht nutzen, aber
sie können ihre eigenen aufgrund der Komplexität nicht aufbauen.

## Die wahren Kosten der Fragmentierung

Wenn Organisationen es schaffen, KI zu deployen, enden sie oft mit einer fragmentierten Landschaft:

- **Team A** nutzt Azure OpenAI über Python-Skripte.
- **Team B** hat ein RAG-System mit LlamaIndex aufgebaut, das nur sie verstehen.
- **Team C** hat einen Chatbot, den niemand mehr wartet.
- **Finanzen** wünschen sich eine Kostenverfolgung über die gesamte KI-Nutzung hinweg.
- **IT** wünscht sich standardisiertes Deployment und Monitoring.
- **Compliance** wünscht sich Audit-Trails und Data Governance.

Jedes Team löst sein unmittelbares Problem, schafft aber neue. Es gibt keine gemeinsame Infrastruktur, keine konsistente
Governance, keinen einheitlichen Ansatz. Die Organisation verfügt über KI-Fähigkeiten, aber nicht über eine
KI-Plattform.

## Was Organisationen tatsächlich brauchen

Die Anforderungen sind klar:

1. **Komplette Infrastruktur**, die Deployment, Monitoring und Skalierung übernimmt – nicht nur die KI-Logik.
2. **Datenhoheit** mit der Option, alles On-Premise oder in Schweizer Rechenzentren zu betreiben.
3. **Offenheit und Kontrolle**, um bestehende Systeme zu modifizieren, zu erweitern und zu integrieren.
4. **Produktionsreife** mit integrierter Unternehmensauthentifizierung, Audit-Trails und Kostenkontrollen.
5. **Eine einheitliche Plattform**, auf der verschiedene Teams aufbauen können, ohne Silos zu schaffen.

Dies ist die Lücke, die der Swiss AI Hub schliesst. Anstatt zwischen dem Eigenbau von allem oder der Akzeptanz eines
Vendor Lock-ins zu wählen, erhalten Sie eine komplette Plattform, die Sie besitzen und kontrollieren. Eine Plattform,
die für die Realitäten des Enterprise KI-Deployments entwickelt wurde, nicht nur für die Begeisterung der
KI-Entwicklung.
