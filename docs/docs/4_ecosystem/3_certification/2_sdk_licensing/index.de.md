---
title: SDK-Lizenzierung
source_sha: e5347335f26229cf324e8f2973ec1c5bcd08454452151c6cf4b470c0e1eff532
---

# Warum das Backend und die UI unterschiedliche Lizenzen verwenden

Der Swiss AI Hub verwendet bewusst zwei Open-Source-Lizenzen für seine beiden Hauptkomponenten:

- **Backend** – Apache Lizenz 2.0
- **Benutzeroberfläche (UI)** – GNU AGPL v3 (oder höher)

Diese Aufteilung ist beabsichtigt. Sie gleicht Offenheit mit den praktischen Bedürfnissen von Organisationen aus, die
KI-Agents auf der Plattform entwickeln und deployen. Die maßgebliche, paketweise Aufschlüsselung finden Sie unter
[LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md); diese Seite erläutert die dahinterstehende
Begründung.

## Backend: Apache 2.0

Im Backend definieren, konfigurieren und führen Sie Ihre Agents, Workflows, Prompts, Integrationen und Geschäftslogik
aus. Es ist unter der Apache 2.0 Lizenz lizenziert, um Ihnen maximale Flexibilität beim Deployment und der Erweiterung
der Plattform zu bieten.

Viele Organisationen betrachten ihre Agents und deren Logik als proprietäres geistiges Eigentum. Unter einer
Netzwerk-Copyleft-Lizenz wie AGPLv3 könnte der Betrieb eines *modifizierten* Backends als Netzwerkdienst Sie dazu
verpflichten, diese Modifikationen unter AGPL-Bedingungen verfügbar zu machen. In der Praxis schafft dies Unsicherheit
darüber, ob Ihre Agent-Implementierungen und die damit verbundene Geschäftslogik veröffentlicht werden müssen.

Apache 2.0 beseitigt diese Unsicherheit: Sie können proprietäre Agents und Backend-Erweiterungen entwickeln und
betreiben, ohne sich Sorgen machen zu müssen, dass Ihre Implementierungen offengelegt werden müssen. Als permissive
Lizenz gewährt sie auch explizite Patentrechte und wird von juristischen Teams in Unternehmen gut verstanden.

Dies umfasst die Plattform-Laufzeitumgebung und das SDK, auf dem Sie aufbauen – die Pakete `core`, `agent`, `api`,
`bot`, `pipeline` und `process`.

## Benutzeroberfläche (UI): AGPLv3

Die UI ist unter AGPLv3 lizenziert, um sicherzustellen, dass Verbesserungen an der benutzerorientierten Anwendung der
Community weiterhin zur Verfügung stehen. Organisationen steht es frei, die UI zu nutzen, aber wenn sie die UI selbst
modifizieren und als Netzwerkdienst bereitstellen, verlangt AGPLv3, dass diese UI-Modifikationen unter derselben Lizenz
geteilt werden.

Dies hilft, eine Situation zu verhindern, in der die Community die UI pflegt, während Dritte proprietäre Forks der
Benutzeroberfläche erstellen, ohne ihre Verbesserungen zurückzugeben. Der Backup- und Restore-Orchestrierungsdienst ist
aus demselben Grund auf dieselbe Weise lizenziert.

## Das Ziel

Das Ziel dieser Lizenzaufteilung ist es, Folgendes zu erreichen:

- Die Kernplattform offen und Community-gesteuert zu halten.
- Beiträge und die Weitergabe von Verbesserungen an der UI zu fördern.
- Organisationen zu ermöglichen, proprietäre Agents, Workflows und geschäftsspezifische Logik auf dem Backend
  aufzubauen.
- Lizenzierungsbedenken bezüglich der Offenlegung von Agent-Implementierungen zu vermeiden.

Kurz gesagt, das Backend bleibt permissiv lizenziert, um Ihre Fähigkeit zur Entwicklung proprietärer Agent-Lösungen zu
schützen, während die UI eine Copyleft-Lizenz verwendet, um sicherzustellen, dass Verbesserungen der Benutzererfahrung
weiterhin der breiteren Community zugutekommen.

::: tip Vollständige paketweise Bedingungen
Diese Seite erklärt das *Warum*. Die genaue Lizenz, die für jedes Paket gilt – einschließlich der wenigen Komponenten,
die unter anderen Bedingungen vertrieben werden – finden Sie unter
[LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md).
:::
