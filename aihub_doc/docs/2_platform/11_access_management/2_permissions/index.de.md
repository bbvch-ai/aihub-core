---
title: Berechtigungs- und Zugriffssteuerung
index: 2
source_sha: "c512664abc783d532303562dbcb519fe908de8f7dc1fb00323a8017ab27b13ba"
---

# Berechtigungs- und Zugriffssteuerung

Die Oberfläche der Swiss AI Hub Suite implementiert eine ausgeklügelte berechtigungsbasierte Zugriffssteuerung, die das Benutzererlebnis dynamisch an das Autorisierungsniveau jedes Einzelnen anpasst. Dieser Ansatz stellt sicher, dass Benutzer nur relevante Funktionen sehen, während gleichzeitig Sicherheits- und Compliance-Anforderungen eingehalten werden.

## Dynamische Dienstsichtbarkeit

Herkömmliche Anwendungsoberflächen präsentieren oft alle Funktionen allen Benutzern und verlassen sich auf Authentifizierungsprüfungen, um unautorisierten Zugriff zu blockieren. Dies führt zu überladenen Oberflächen voller deaktivierter Schaltflächen und Funktionen, die Benutzer nicht nutzen können, was zu Verwirrung und Supportaufwand führt. Der Swiss AI Hub überdenkt diesen Ansatz grundlegend durch dynamische Dienstsichtbarkeit.

**Berechtigungsgefilterter Dienstkatalog**: Wenn die Suite geladen wird, fragt sie das Backend nach dem autorisierten Dienstkatalog des Benutzers. Das Backend bewertet die Berechtigungen des Benutzers anhand der Anforderungen jedes registrierten Dienstes und gibt nur Dienste zurück, auf die der Benutzer zugreifen kann. Die Oberfläche rendert Navigationselemente ausschließlich für autorisierte Dienste – Benutzer sehen einfach niemals Funktionen, die sie nicht nutzen können.

**Saubere, fokussierte Oberfläche**: Dieser Ansatz schafft im Vergleich zu herkömmlichen Anwendungen dramatisch einfachere Oberflächen. Ein Datenwissenschaftler sieht Bewertungs- und Experimentierdienste prominent dargestellt. Ein Business Analyst sieht Konversationsverläufe und Wissenserkundungstools. Ein Administrator sieht Benutzerverwaltung und Systemkonfigurationsoptionen. Die Oberfläche jedes Benutzers spiegelt seine tatsächlichen Fähigkeiten wider, nicht einen universellen Funktionsumfang, der mit unzugänglichen Optionen überladen ist.

**Automatische Berechtigungsaktualisierungen**: Wenn ein Administrator die Rollenzuweisungen oder Berechtigungsvergaben eines Benutzers ändert, spiegeln sich diese Änderungen bei der nächsten Sitzung des Benutzers automatisch in dessen Oberfläche wider. Es ist keine Cache-Invalidierung, manuelle Aktualisierung oder Abmelden-Anmelden-Zyklus erforderlich. Die Architektur der Suite stellt sicher, dass die Oberfläche stets eine genaue Ansicht des aktuellen Autorisierungsstatus präsentiert.

**Sicherheit durch Unsichtbarkeit**: Indem keine nicht autorisierten Dienstnavigationselemente gerendert werden, eliminiert die Suite eine ganze Klasse von Sicherheitslücken. Benutzer können nicht versuchen, auf eingeschränkte Dienste durch Manipulation der Oberfläche zuzugreifen, da diese Dienste keine Schnittstellenpräsenz haben. Dieser Defense-in-Depth-Ansatz ergänzt die Backend-Autorisierungsdurchsetzung.

## Hierarchisches Berechtigungssystem

Die Suite integriert sich in das umfassende hierarchische Berechtigungssystem des Swiss AI Hub, das eine feingranulare Zugriffssteuerung durch eine strukturierte Berechtigungssyntax im Dot-Notation-Format bietet.

**Berechtigungsstruktur**: Berechtigungen folgen dem Format `aihub.[user|admin].<service>.<resource_type>.<resource_id>`, wodurch ein hierarchischer Namespace entsteht, der eine präzise Zugriffssteuerung ermöglicht. Zum Beispiel gewährt `aihub.user.agent.support_agent.instance_001` Zugriff auf eine spezifische Agenteninstanz, während `aihub.admin.knowledge` administrativen Zugriff auf den gesamten Wissensmanagementdienst gewährt.

**Platzhalter-Unterstützung**: Das Berechtigungssystem unterstützt ausgefeilte Platzhalter, die eine flexible Zugriffssteuerung ermöglichen, ohne dass jede Ressource explizit aufgelistet werden muss. Der Platzhalter `*` stimmt mit jedem einzelnen Pfadsegment überein, während der Platzhalter `>` mit allen verbleibenden Pfadsegmenten übereinstimmt. Dies ermöglicht Regeln wie `aihub.user.agent.>` um Zugriff auf alle Agentenressourcen in beliebiger Tiefe zu gewähren.

**Implizite Berechtigungen**: Benutzer mit dem impliziten Berechtigungsmuster `aihub.user.?>` erhalten Zugriff auf alle Dienste auf Benutzerebene, ohne dass für jeden Dienst explizite Berechtigungen erforderlich sind. Dies vereinfacht die Berechtigungsverwaltung für Standardbenutzer, während gleichzeitig eine feingranulare Kontrolle für spezielle Zugriffsmuster beibehalten wird.

**Dienstebenen-Zugriffssteuerung**: Jeder Dienst-Controller deklariert Mindestberechtigungsanforderungen für den Zugriff. Der Suite-Endpunkt bewertet, ob der Benutzer diese Mindestberechtigungen besitzt, wenn er den Dienstkatalog erstellt. Dienste, die Berechtigungen erfordern, die dem Benutzer fehlen, erscheinen einfach nicht in der Katalogantwort.

## Rollenbasierte Oberfläche-Anpassung

Über die einfache Anzeige-/Verbergelogik hinaus implementiert die Suite eine rollenbewusste Oberflächenanpassung, die basierend auf den Benutzerautorisierungsstufen unterschiedliche Ansichten und Funktionen präsentiert.

**Administrative Privilegien**: Wenn der Suite-Endpunkt Berechtigungen bewertet, bestimmt er nicht nur, ob der Benutzer auf einen Dienst zugreifen kann, sondern auch, ob er administrative Privilegien für diesen Dienst besitzt. Diese Unterscheidung wird an das Frontend kommuniziert, das innerhalb der Oberfläche dieses Dienstes zusätzliche administrative Funktionen präsentieren kann.

**Kontextbewusste Navigation**: Die Suite behält das Bewusstsein für den aktuellen Autorisierungskontext des Benutzers. Beim Betrachten eines Agenten kann die Oberfläche bestimmen, ob der Benutzer administrativen Zugriff auf diesen spezifischen Agenten hat, und administrative Steuerungen wie die Konfigurationsbearbeitung nur dann präsentieren, wenn er autorisiert ist. Standardbenutzer sehen schreibgeschützte Ansichten derselben Ressourcen.

**Granulare Funktionssteuerung**: Innerhalb einzelner Dienste kann die Oberfläche die Berechtigungen des Benutzers für spezifische Ressourcen oder Operationen abfragen. Ein Benutzer könnte Lesezugriff auf Wissensdatenbanken haben, aber keine Upload-Berechtigungen. Die Oberfläche spiegelt dies wider, indem sie Wissenserkundungsfunktionen anzeigt, während sie Dokumenten-Upload-Steuerungen verbirgt.

**Multi-Tenant-Isolation**: In Bereitstellungen, die mehrere Organisationseinheiten oder Kunden-Mandanten bedienen, gewährleistet das Berechtigungssystem eine vollständige Datenisolation. Benutzer sehen nur Dienste und Ressourcen, die zu ihrem organisatorischen Kontext gehören, wodurch sichere, isolierte Arbeitsbereiche innerhalb einer gemeinsamen Plattformbereitstellung geschaffen werden.

## Architektur der Berechtigungsprüfung

Das berechtigungsbewusste Verhalten der Suite resultiert aus einer ausgeklügelten Koordination zwischen Frontend-Anfragen und Backend-Evaluierungslogik.

**Backend-Berechtigungsprüfung**: Die gesamte Berechtigungsprüfung erfolgt im Backend, um sicherzustellen, dass die Sicherheitsdurchsetzung nicht durch clientseitige Manipulation umgangen werden kann. Der Suite-Endpunkt fragt das Berechtigungssystem ab, bewertet Zugriffsregeln anhand der Rollen und Berechtigungen des Benutzers und gibt einen vorgefilterten Dienstkatalog zurück. Das Frontend vertraut diesem Katalog, ohne eine eigene Berechtigungslogik auszuführen.

**Access Checker Integration**: Das Backend verwendet eine Access-Checker-Komponente, die die Berechtigungsprüfungslogik kapselt. Diese Komponente akzeptiert eine Benutzeridentität und ein Berechtigungsmuster, bewertet, ob die Zugriffsregeln des Benutzers mit dem Muster übereinstimmen, und gibt entweder boolesche Zugriffsentscheidungen oder eine detaillierte Aufzählung der Zugriffsebene (verweigert, Benutzerzugriff, administrativer Zugriff) zurück.

**Effiziente Berechtigungsabfragen**: Die Berechtigungsprüfung ist durch Caching-Strategien und effiziente Mustererkennungsalgorithmen auf Leistung optimiert. Wenn der Suite-Endpunkt die Dienstsichtbarkeit für einen Benutzer bewertet, führt er diese Evaluierungen parallel und nicht sequenziell durch, um reaktionsschnelle Ladezeiten der Oberfläche auch bei zahlreichen Diensten zu gewährleisten.

**Generierung von Audit-Trails**: Jede Berechtigungsprüfung generiert Audit-Log-Einträge, die dokumentieren, welche Berechtigungen geprüft wurden, für welchen Benutzer und welche Entscheidung getroffen wurde. Dies erstellt umfassende Audit-Trails zur Unterstützung von Compliance-Berichterstattung und Sicherheitsforensik.

## Dienstspezifische Berechtigungsmuster

Verschiedene Dienste implementieren unterschiedliche Berechtigungsmuster basierend auf ihren funktionalen Anforderungen, was die Flexibilität des hierarchischen Berechtigungssystems demonstriert.

**Agenten-Dienst**: Implementiert eine pro-Agenten-Zugriffssteuerung, bei der Benutzer möglicherweise Zugriff auf bestimmte Agenteninstanzen, aber nicht auf andere haben. Berechtigungen wie `aihub.user.agent.customer_support.cs_001` gewähren Zugriff auf einen spezifischen Agenten, während `aihub.user.agent.customer_support.*` Zugriff auf alle Instanzen dieser Agentenklasse gewährt.

**Thread-Dienst**: Steuert den Zugriff auf Konversations-Threads basierend auf Eigentums- und Freigaberegeln. Benutzer haben in der Regel Zugriff auf Threads, die sie erstellt oder an denen sie teilgenommen haben, wobei Administratoren eine breitere Sichtbarkeit für Support- und Überwachungszwecke haben.

**Wissensdienst**: Implementiert eine Namespace-basierte Zugriffssteuerung, bei der Berechtigungen auf Datenbankebene (`aihub.user.knowledge.hr_documents`) oder Namespace-Ebene (`aihub.user.knowledge.hr_documents.policies`) vergeben werden können, mit hierarchischer Vererbung durch den Berechtigungsbaum.

**Administrative Dienste**: Erfordern explizite administrative Berechtigungen wie `aihub.admin.users` oder `aihub.admin.roles`. Diese Dienste erscheinen niemals für Benutzer ohne administrative Berechtigungen, wodurch eine klare Trennung zwischen Standard- und administrativen Oberflächen geschaffen wird.

## Vorteile für die Benutzerfreundlichkeit

Die berechtigungsbewusste Suite-Architektur bietet erhebliche Vorteile in Bezug auf Benutzerfreundlichkeit und Betrieb.

**Eliminierung von „Zugriff verweigert“-Fehlern**: Benutzer stoßen niemals auf „Zugriff verweigert“-Meldungen für sichtbare Oberflächenelemente, da nicht autorisierte Funktionen einfach nicht erscheinen. Dies eliminiert eine häufige Ursache für Benutzerfrustration und Support-Tickets in traditionellen Unternehmensanwendungen.

**Reduzierte Oberflächenkomplexität**: Durch die Anzeige nur autorisierter Funktionen bleibt die Oberfläche übersichtlich und fokussiert. Benutzer müssen sichtbare, aber deaktivierte Funktionen nicht von verfügbaren Funktionen mental filtern – alles, was sie sehen, können sie nutzen.

**Self-Service-Zugriffsverständnis**: Benutzer können ihre autorisierten Funktionen sofort verstehen, indem sie beobachten, was in der Suite-Navigation erscheint. Es ist nicht erforderlich, separate Dokumentationen zu konsultieren oder den Support zu kontaktieren, um zu ermitteln, auf welche Funktionen sie zugreifen können.

**Optimiertes Onboarding**: Neue Benutzer sehen nur die für ihre Rolle relevanten Funktionen, was die anfängliche Plattformorientierung dramatisch vereinfacht. Schulungen können sich auf relevante Funktionen konzentrieren, anstatt Benutzern zu helfen, zu verstehen, worauf sie nicht zugreifen können und warum.

## Sicherheits- und Compliance-Vorteile

Die berechtigungsbewusste Architektur bietet über die Verbesserungen der Benutzerfreundlichkeit hinaus Sicherheits- und Compliance-Vorteile.

**Verteidigung in der Tiefe**: Die clientseitige Filterung nicht autorisierter Dienste ergänzt die Backend-Berechtigungsdurchsetzung und schafft so mehrere Sicherheitsebenen. Selbst wenn ein Angreifer das Frontend manipuliert, verhindert die Backend-Autorisierungsdurchsetzung unautorisierte Operationen.

**Reduzierte Angriffsfläche**: Indem keine Informationen über Dienste preisgegeben werden, auf die Benutzer keinen Zugriff haben, offenbart die Suite potenziellen Angreifern weniger über die Funktionen der Bereitstellung. Benutzer können deaktivierte Funktionen nicht ausforschen, um Informationen für Angriffe zu sammeln.

**Compliance-Unterstützung**: Die umfassende Audit-Protokollierung von Berechtigungsprüfungen unterstützt die regulatorischen Compliance-Anforderungen für die Zugriffssteuerung, insbesondere in Sektoren mit strengen Datenschutzanforderungen wie Gesundheitswesen, Finanzen und öffentlicher Verwaltung.

**Zero-Trust-Architektur**: Die Suite implementiert Zero-Trust-Prinzipien, bei denen jeder Dienstzugriff eine explizite Berechtigungsprüfung erfordert. Es gibt keine impliziten Vertrauensannahmen basierend auf dem Netzwerkstandort oder einer früheren Authentifizierung – jede Operation wird unabhängig autorisiert.

## Betriebliche Vorteile

Neben Sicherheit und Benutzerfreundlichkeit bietet das Berechtigungssystem betriebliche Vorteile für Plattformadministratoren.

**Zentralisierte Berechtigungsverwaltung**: Administratoren verwalten Berechtigungen über den Rollenverwaltungsdienst, wobei Änderungen automatisch in der gesamten Suite widergespiegelt werden. Es ist nicht erforderlich, Zugriffssteuerungen für jeden Dienst separat zu konfigurieren oder Berechtigungen über mehrere Systeme hinweg zu koordinieren.

**Flexible Delegation**: Das hierarchische Berechtigungssystem ermöglicht ausgefeilte Delegationsmuster. Senior-Mitarbeitern können breite Zugriffsmuster wie `aihub.user.agent.>` gewährt werden, während Junior-Mitarbeiter spezifische Berechtigungen für einzelne Ressourcen erhalten. Diese Flexibilität unterstützt organisatorische Strukturen, ohne komplexe Zugriffssteuerungskonfigurationen zu erfordern.

**Berechtigungsvererbung**: Die hierarchische Struktur ermöglicht die Berechtigungsvererbung, bei der die Gewährung des Zugriffs auf eine Ressource höherer Ebene automatisch den Zugriff auf enthaltene Ressourcen ermöglicht. Dies vereinfacht die Berechtigungsverwaltung, während bei Bedarf eine präzise Kontrolle beibehalten wird.

**Rollenbasierte Administration**: Anstatt individuelle Benutzerberechtigungen zu verwalten, weisen Administratoren Benutzern typischerweise Rollen zu, die Standard-Berechtigungssätze definieren. Rollenänderungen gelten automatisch für alle zugewiesenen Benutzer und gewährleisten so eine konsistente Zugriffssteuerung über alle Benutzergruppen hinweg.

Diese berechtigungsbewusste Architektur stellt sicher, dass die Swiss AI Hub Suite jedem Benutzer eine fokussierte, sichere Oberfläche bietet, die präzise auf sein Autorisierungsniveau und seine organisatorische Rolle zugeschnitten ist, während gleichzeitig die betriebliche Einfachheit und die Sicherheitsstrenge gewährleistet werden, die für Unternehmens- und öffentliche Sektor-Bereitstellungen erforderlich sind.

# Rollenbasierte Zugriffssteuerung (RBAC) :shield: :lock:

::: info **Aktualisierung der Dokumentationsstruktur**
Die RBAC-Dokumentation wurde neu organisiert, um verschiedenen Zielgruppen besser gerecht zu werden. Diese Seite bietet schnellen Zugriff auf die für Ihre Bedürfnisse passende Dokumentation.
:::

## Schnelle Navigation

### Für Plattformbenutzer und Administratoren

Wenn Sie verstehen möchten, wie RBAC aus geschäftlicher und betrieblicher Sicht funktioniert, einschließlich der Konfiguration von Rollen, der Verwaltung von Berechtigungen und der Einrichtung der Authentifizierung:

::: tip **Plattformdokumentation**
📖 **[Vollständiger RBAC-Leitfaden für die Plattform](../../../1_vision_and_positioning/3_solution/4_security/2_rbac/index.md)**

Behandelt:

- Konzepte der Rollenverwaltung und geschäftlicher Nutzen
- Architektur des Berechtigungssystems und Beispiele
- Benutzer- und Administrator-Privilegien
- Authentifizierung und Integration von Identitätsprovidern
- Rollenkonfiguration und Best Practices
- Sicherheit, Compliance und Überwachung
- Bereitstellung und Erste Schritte
:::

### Für Entwickler und SDK-Benutzer

Wenn Sie RBAC in Ihren benutzerdefinierten Agenten, APIs oder Diensten implementieren und technische Implementierungsdetails benötigen:

::: tip **SDK-Dokumentation**
🛠️ **[Vollständiger RBAC-Implementierungsleitfaden für das SDK](../../../3_sdk/5_advanced_topics/5_rbac/index.md)**

Behandelt:

- Zugriffssteuerung auf Controller-Ebene
- Dynamische Berechtigungsauflösung
- Implementierung der Dienst- und Agenten-Zugriffssteuerung
- Erweiterte Berechtigungsmuster und Platzhalter
- Benutzerdefinierte Validierungslogik
- Testen von RBAC-Implementierungen
- Leistungsoptimierung und Best Practices
:::

## Kurzübersicht

**Rollenbasierte Zugriffssteuerung (RBAC)** ist ein Sicherheitsframework, das den Systemzugriff basierend auf Benutzerrollen innerhalb einer Organisation einschränkt. Der AI-Hub implementiert ein ausgeklügeltes, hierarchisches RBAC-System, das eine granulare Kontrolle über jeden Aspekt Ihrer KI-Plattform bietet.

### Hauptvorteile

**🛡️ Enterprise-Sicherheits-Compliance**: Erfüllen Sie strenge regulatorische Anforderungen mit umfassenden Audit-Trails und granularer Zugriffssteuerung.

**🎯 Granulare Ressourcenkontrolle**: Steuern Sie den Zugriff auf spezifische KI-Agenten, Prozesse und Dienste mit Präzision.

**⚡ Skalierbare Berechtigungsverwaltung**: Verwalten Sie Berechtigungen effizient in großen Organisationen mithilfe rollenbasierter Hierarchien.

**🔗 Nahtlose Enterprise-Integration**: Native Integration mit bestehenden Enterprise-Identitätssystemen.

**🧠 Risikobewusste KI-Bereitstellung**: Stellen Sie KI-Funktionen mit Vertrauen bereit, wissend, dass der Zugriff kontrolliert und überwacht wird.

### Kernkomponenten

- **Rollen**: Benannte Sammlungen von Zugriffsregeln, die definieren, was Benutzer tun können
- **Zugriffsregeln**: Spezifische Berechtigungen unter Verwendung der Dot-Notation (z. B. `aihub.admin.service.roles`)
- **Benutzeridentität**: Integration mit Enterprise-Authentifizierungssystemen (Azure AD, OAuth2)
- **Berechtigungsvorlagen**: Dynamische Berechtigungsprüfung mit Pfadparameter-Substitution
- **Platzhalter-Unterstützung**: Flexible Mustererkennung unter Verwendung von `*`, `>`, `?*` und `?>` Platzhaltern

### Berechtigungsstruktur

Das System verwendet eine strukturierte Namenskonvention für Berechtigungen:

```
aihub.[user|admin].[resource_type].[resource_category].[resource_identifier]
```

**Beispiele:**

- `aihub.user.agent.customer_service.chatbot_v2` - Benutzerzugriff auf spezifischen Agenten
- `aihub.admin.service.roles` - Administratorzugriff auf die Rollenverwaltung
- `aihub.user.agent.?>` - Benutzerzugriff auf beliebigen Agenten (Platzhalter)

## Wählen Sie Ihren Weg

- **Geschäftsbenutzer & Administratoren**: Beginnen Sie mit dem
  [RBAC-Leitfaden für die Plattform](../../../1_vision_and_positioning/3_solution/4_security/2_rbac/index.md)
- **Entwickler & Integratoren**: Beginnen Sie mit dem
  [SDK-Implementierungsleitfaden](../../../3_sdk/5_advanced_topics/5_rbac/index.md)

Beide Leitfäden bieten eine umfassende Abdeckung des AI-Hub RBAC-Systems, zugeschnitten auf Ihre spezifischen Bedürfnisse und Anwendungsfälle.
