---
title: Berechtigungs- und Zugriffskontrolle
source_sha: "e92bf927d27b823e3a72d037c6b18e92f99989e4a50e108034670ec56dc30c2a"
---

# Berechtigungs- und Zugriffskontrolle

Die Benutzeroberfläche der Swiss AI Hub Suite implementiert eine hochentwickelte, berechtigungsbasierte Zugriffskontrolle, die das Benutzererlebnis dynamisch an das Autorisierungslevel jedes Einzelnen anpasst. Dieser Ansatz stellt sicher, dass Benutzer nur relevante Funktionen sehen, während gleichzeitig Sicherheits- und Compliance-Anforderungen erfüllt werden.

## Dynamische Dienstsichtbarkeit

Herkömmliche Anwendungsschnittstellen präsentieren oft allen Benutzern alle Funktionen und verlassen sich auf Authentifizierungsprüfungen, um unautorisierten Zugriff zu blockieren. Dies führt zu überladenen Benutzeroberflächen mit deaktivierten Schaltflächen und Funktionen, die Benutzer nicht nutzen können, was Verwirrung und Support-Aufwand verursacht. Der Swiss AI Hub überdenkt diesen Ansatz grundlegend durch dynamische Dienstsichtbarkeit.

**Berechtigungsgefilterter Dienstkatalog**: Wenn die Suite geladen wird, fragt sie das Backend nach dem autorisierten Dienstkatalog des Benutzers ab. Das Backend bewertet die Berechtigungen des Benutzers anhand der Anforderungen jedes registrierten Dienstes und gibt nur Dienste zurück, auf die der Benutzer zugreifen kann. Die Benutzeroberfläche rendert Navigationselemente ausschließlich für autorisierte Dienste – Benutzer sehen einfach niemals Funktionen, die sie nicht nutzen können.

**Saubere, fokussierte Oberfläche**: Dieser Ansatz schafft im Vergleich zu herkömmlichen Anwendungen dramatisch einfachere Benutzeroberflächen. Ein Datenwissenschaftler sieht Bewertungs- und Experimentierdienste prominent dargestellt. Ein Geschäftsanalyst sieht Konversationsverläufe und Wissenserkundungstools. Ein Administrator sieht Benutzerverwaltungs- und Systemkonfigurationsoptionen. Die Benutzeroberfläche jedes Benutzers spiegelt dessen tatsächliche Fähigkeiten wider, nicht einen universellen Funktionsumfang, der mit unzugänglichen Optionen überladen ist.

**Automatische Berechtigungsaktualisierungen**: Wenn ein Administrator die Rollenzuweisungen oder Berechtigungen eines Benutzers ändert, spiegeln sich diese Änderungen bei der nächsten Sitzung des Benutzers automatisch in dessen Benutzeroberfläche wider. Es ist keine Cache-Invalidierung, manuelle Aktualisierung oder ein Logout-Login-Zyklus erforderlich. Die Architektur der Suite stellt sicher, dass die Benutzeroberfläche stets eine genaue Ansicht des aktuellen Autorisierungszustands präsentiert.

**Sicherheit durch Unsichtbarkeit**: Indem keine unautorisierten Dienstnavigationselemente gerendert werden, eliminiert die Suite eine ganze Klasse von Sicherheitslücken. Benutzer können nicht versuchen, auf eingeschränkte Dienste durch Manipulation der Benutzeroberfläche zuzugreifen, da diese Dienste keine Schnittstellenpräsenz haben. Dieser Defense-in-Depth-Ansatz ergänzt die Backend-Autorisierungsdurchsetzung.

## Hierarchisches Berechtigungssystem

Die Suite ist in das umfassende hierarchische Berechtigungssystem des Swiss AI Hub integriert, das eine feingranulare Zugriffskontrolle durch eine strukturierte, Punktnotations-Berechtigungssyntax bietet.

**Berechtigungsstruktur**: Berechtigungen folgen dem Format `aihub.[user|admin].<service>.<resource_type>.<resource_id>`, wodurch ein hierarchischer Namespace geschaffen wird, der eine präzise Zugriffskontrolle ermöglicht. Zum Beispiel gewährt `aihub.user.agent.support_agent.instance_001` Zugriff auf eine bestimmte Agenteninstanz, während `aihub.admin.knowledge` administrativen Zugriff auf den gesamten Wissensmanagementdienst gewährt.

**Platzhalter-Unterstützung**: Das Berechtigungssystem unterstützt ausgeklügelte Platzhalter, die eine flexible Zugriffskontrolle ermöglichen, ohne dass jedes einzelne Ressource explizit aufgelistet werden muss. Der `*`-Platzhalter stimmt mit jedem einzelnen Pfadsegment überein, während der `>`-Platzhalter mit allen verbleibenden Pfadsegmenten übereinstimmt. Dies ermöglicht Regeln wie `aihub.user.agent.>`, um Zugriff auf alle Agentenressourcen in beliebiger Tiefe zu gewähren.

**Implizite Berechtigungen**: Benutzer mit dem impliziten Berechtigungsmuster `aihub.user.?>` erhalten Zugriff auf alle Dienste auf Benutzerebene, ohne dass für jeden Dienst explizite Zuweisungen erforderlich sind. Dies vereinfacht die Berechtigungsverwaltung für Standardbenutzer, während eine feingranulare Kontrolle für spezielle Zugriffsmuster beibehalten wird.

**Dienst-Level-Zugriffskontrolle**: Jeder Dienst-Controller deklariert Mindestberechtigungsanforderungen für den Zugriff. Der Suite-Endpunkt bewertet, ob der Benutzer diese Mindestberechtigungen besitzt, wenn er den Dienstkatalog erstellt. Dienste, die Berechtigungen erfordern, die der Benutzer nicht besitzt, erscheinen einfach nicht in der Katalogantwort.

## Rollenbasierte Oberflächenanpassung

Über eine einfache Zeigen/Verbergen-Logik hinaus implementiert die Suite eine rollenbewusste Oberflächenanpassung, die unterschiedliche Ansichten und Funktionen basierend auf den Autorisierungsstufen des Benutzers präsentiert.

**Administrative Privilegien**: Wenn der Suite-Endpunkt Berechtigungen bewertet, bestimmt er nicht nur, ob der Benutzer auf einen Dienst zugreifen kann, sondern auch, ob er administrative Privilegien für diesen Dienst besitzt. Diese Unterscheidung wird an das Frontend kommuniziert, das zusätzliche administrative Funktionen innerhalb der Schnittstelle dieses Dienstes präsentieren kann.

**Kontextbezogene Navigation**: Die Suite berücksichtigt den aktuellen Autorisierungskontext des Benutzers. Beim Betrachten eines Agenten kann die Benutzeroberfläche feststellen, ob der Benutzer administrativen Zugriff auf diesen spezifischen Agenten hat, und administrative Steuerungen wie die Konfigurationsbearbeitung nur bei Autorisierung anzeigen. Standardbenutzer sehen schreibgeschützte Ansichten derselben Ressourcen.

**Granulare Funktionskontrolle**: Innerhalb einzelner Dienste kann die Benutzeroberfläche die Berechtigungen des Benutzers für bestimmte Ressourcen oder Operationen abfragen. Ein Benutzer hat möglicherweise Lesezugriff auf Wissensdatenbanken, aber keine Upload-Berechtigungen. Die Benutzeroberfläche spiegelt dies wider, indem sie Funktionen zur Wissenserkundung anzeigt, während sie Steuerelemente für den Dokumenten-Upload ausblendet.

**Multi-Tenant-Isolation**: In Bereitstellungen, die mehrere Organisationseinheiten oder Kunden-Tenants bedienen, gewährleistet das Berechtigungssystem eine vollständige Datenisolation. Benutzer sehen nur Dienste und Ressourcen, die zu ihrem organisatorischen Kontext gehören, wodurch sichere, isolierte Arbeitsbereiche innerhalb einer gemeinsamen Plattformbereitstellung geschaffen werden.

## Architektur der Berechtigungsbewertung

Das berechtigungsbewusste Verhalten der Suite resultiert aus einer ausgeklügelten Koordination zwischen Frontend-Abfragen und Backend-Evaluierungslogik.

**Backend-Berechtigungsbewertung**: Die gesamte Berechtigungsbewertung findet im Backend statt, um sicherzustellen, dass die Sicherheitsdurchsetzung nicht durch clientseitige Manipulation umgangen werden kann. Der Suite-Endpunkt fragt das Berechtigungssystem ab, bewertet Zugriffsregeln anhand der Rollen und Berechtigungen des Benutzers und gibt einen vorgefilterten Dienstkatalog zurück. Das Frontend vertraut diesem Katalog, ohne eine eigene Berechtigungslogik durchzuführen.

**Access Checker Integration**: Das Backend verwendet eine Access Checker-Komponente, die die Berechtigungsbewertungslogik kapselt. Diese Komponente akzeptiert eine Benutzeridentität und ein Berechtigungsmuster, bewertet, ob die Zugriffsregeln des Benutzers mit dem Muster übereinstimmen, und gibt entweder boolesche Zugriffsentscheidungen oder eine detaillierte Aufzählung der Zugriffsebene (verweigert, Benutzerzugriff, administrativer Zugriff) zurück.

**Effiziente Berechtigungsabfragen**: Die Berechtigungsbewertung ist durch Caching-Strategien und effiziente Musterabgleichsalgorithmen auf Leistung optimiert. Wenn der Suite-Endpunkt die Dienstsichtbarkeit für einen Benutzer bewertet, führt er diese Bewertungen parallel statt sequenziell durch, um reaktionsschnelle Ladezeiten der Benutzeroberfläche auch bei zahlreichen Diensten zu gewährleisten.

**Audit-Trail-Generierung**: Jede Berechtigungsbewertung generiert Audit-Log-Einträge, die dokumentieren, welche Berechtigungen geprüft wurden, für welchen Benutzer und welche Entscheidung getroffen wurde. Dies schafft umfassende Audit-Trails zur Unterstützung der Compliance-Berichterstattung und der Sicherheitsforensik.

## Dienstspezifische Berechtigungsmuster

Verschiedene Dienste implementieren unterschiedliche Berechtigungsmuster basierend auf ihren funktionalen Anforderungen, was die Flexibilität des hierarchischen Berechtigungssystems demonstriert.

**Agenten-Dienst**: Implementiert eine Zugriffskontrolle pro Agent, bei der Benutzer möglicherweise Zugriff auf bestimmte Agenteninstanzen, aber nicht auf andere haben. Berechtigungen wie `aihub.user.agent.customer_support.cs_001` gewähren Zugriff auf einen bestimmten Agenten, während `aihub.user.agent.customer_support.*` Zugriff auf alle Instanzen dieser Agentenklasse gewährt.

**Thread-Dienst**: Steuert den Zugriff auf Konversations-Threads basierend auf Eigentums- und Freigaberegeln. Benutzer haben im Allgemeinen Zugriff auf Threads, die sie erstellt oder an denen sie teilgenommen haben, wobei Administratoren eine breitere Sichtbarkeit für Support- und Überwachungszwecke haben.

**Wissensdienst**: Implementiert eine Namespace-basierte Zugriffskontrolle, bei der Berechtigungen auf Datenbankebene (`aihub.user.knowledge.hr_documents`) oder Namespace-Ebene (`aihub.user.knowledge.hr_documents.policies`) gewährt werden können, mit hierarchischer Vererbung durch den Berechtigungsbaum.

**Administrative Dienste**: Erfordern explizite administrative Berechtigungen wie `aihub.admin.users` oder `aihub.admin.roles`. Diese Dienste erscheinen niemals für Benutzer ohne administrative Berechtigungen, wodurch eine klare Trennung zwischen Standard- und administrativen Schnittstellen geschaffen wird.

## Vorteile für die Benutzererfahrung

Die berechtigungsbewusste Suite-Architektur bietet erhebliche Vorteile für die Benutzererfahrung und den Betrieb.

**Eliminierung von "Zugriff verweigert"-Fehlern**: Benutzer stoßen nie auf „Zugriff verweigert“-Meldungen für sichtbare Oberflächenelemente, da unautorisierte Funktionen einfach nicht erscheinen. Dies eliminiert eine häufige Quelle für Benutzerfrustration und Support-Tickets in traditionellen Unternehmensanwendungen.

**Reduzierte Komplexität der Benutzeroberfläche**: Indem nur autorisierte Funktionen angezeigt werden, bleibt die Benutzeroberfläche übersichtlich und fokussiert. Benutzer müssen sichtbare, aber deaktivierte Funktionen nicht mental von verfügbaren Funktionen filtern – alles, was sie sehen, können sie nutzen.

**Self-Service-Zugriffsverständnis**: Benutzer können ihre autorisierten Funktionen sofort verstehen, indem sie beobachten, was in der Suite-Navigation erscheint. Es ist nicht erforderlich, separate Dokumentationen zu konsultieren oder den Support zu kontaktieren, um herauszufinden, auf welche Funktionen sie zugreifen können.

**Optimiertes Onboarding**: Neue Benutzer sehen nur die Funktionen, die für ihre Rolle relevant sind, was die anfängliche Plattformorientierung dramatisch vereinfacht. Schulungen können sich auf relevante Funktionen konzentrieren, anstatt Benutzern zu helfen, zu verstehen, worauf sie nicht zugreifen können und warum.

## Sicherheits- und Compliance-Vorteile

Die berechtigungsbewusste Architektur bietet Sicherheits- und Compliance-Vorteile, die über Verbesserungen der Benutzererfahrung hinausgehen.

**Defense in Depth**: Die clientseitige Filterung unautorisierter Dienste ergänzt die Backend-Berechtigungsdurchsetzung und schafft mehrere Sicherheitsebenen. Selbst wenn ein Angreifer das Frontend manipuliert, verhindert die Backend-Autorisierungsdurchsetzung unautorisierte Operationen.

**Reduzierte Angriffsfläche**: Indem Informationen über Dienste, auf die Benutzer nicht zugreifen können, nicht offengelegt werden, offenbart die Suite potenziellen Angreifern weniger über die Fähigkeiten der Bereitstellung. Benutzer können deaktivierte Funktionen nicht ausspionieren, um Informationen für Angriffe zu sammeln.

**Compliance-Unterstützung**: Die umfassende Audit-Protokollierung von Berechtigungsbewertungen unterstützt die Einhaltung regulatorischer Anforderungen für die Zugriffskontrolle, insbesondere in Sektoren mit strengen Datenschutzanforderungen wie Gesundheitswesen, Finanzen und öffentlicher Verwaltung.

**Zero-Trust-Architektur**: Die Suite implementiert Zero-Trust-Prinzipien, bei denen jeder Dienstzugriff eine explizite Berechtigungsbewertung erfordert. Es gibt keine impliziten Vertrauensannahmen basierend auf dem Netzwerkstandort oder einer früheren Authentifizierung – jeder Vorgang wird unabhängig autorisiert.

## Operationelle Vorteile

Über Sicherheit und Benutzererfahrung hinaus bietet das Berechtigungssystem operationelle Vorteile für Plattformadministratoren.

**Zentralisierte Berechtigungsverwaltung**: Administratoren verwalten Berechtigungen über den Rollenverwaltungsdienst, wobei Änderungen automatisch in der gesamten Suite widergespiegelt werden. Es ist nicht erforderlich, Zugriffskontrollen separat für jeden Dienst zu konfigurieren oder Berechtigungen über mehrere Systeme hinweg zu koordinieren.

**Flexible Delegation**: Das hierarchische Berechtigungssystem ermöglicht ausgeklügelte Delegationsmuster. Leitenden Mitarbeitern können breite Zugriffsmuster wie `aihub.user.agent.>` gewährt werden, während Junior-Mitarbeiter spezifische Berechtigungen für einzelne Ressourcen erhalten. Diese Flexibilität unterstützt organisatorische Strukturen, ohne komplexe Zugriffskontrollkonfigurationen zu erfordern.

**Berechtigungsvererbung**: Die hierarchische Struktur ermöglicht die Berechtigungsvererbung, bei der die Gewährung des Zugriffs auf eine Ressource auf höherer Ebene automatisch den Zugriff auf enthaltene Ressourcen ermöglicht. Dies vereinfacht die Berechtigungsverwaltung, während bei Bedarf eine präzise Kontrolle beibehalten wird.

**Rollenbasierte Administration**: Anstatt individuelle Benutzerberechtigungen zu verwalten, weisen Administratoren Benutzern in der Regel Rollen zu, die Standardberechtigungssätze definieren. Rollenänderungen gelten automatisch für alle zugewiesenen Benutzer und gewährleisten eine konsistente Zugriffskontrolle über Benutzerpopulationen hinweg.

Diese berechtigungsbewusste Architektur stellt sicher, dass die Swiss AI Hub Suite jedem Benutzer eine fokussierte, sichere Oberfläche bietet, die präzise auf dessen Autorisierungslevel und organisatorische Rolle zugeschnitten ist, während die operationelle Einfachheit und die Sicherheitsstrenge, die für Unternehmens- und öffentliche Sektor-Bereitstellungen erforderlich sind, beibehalten werden.

# Rollenbasierte Zugriffskontrolle (RBAC) :shield: :lock:

::: info **Dokumentationsstruktur-Update**
Die RBAC-Dokumentation wurde neu organisiert, um verschiedenen Zielgruppen besser zu dienen. Diese Seite bietet schnellen Zugriff auf die für Ihre Bedürfnisse passende Dokumentation.
:::

## Schnellnavigation

### Für Entwickler und SDK-Benutzer

Wenn Sie RBAC in Ihren benutzerdefinierten Agenten, APIs oder Diensten implementieren und technische Implementierungsdetails benötigen:

::: tip **SDK-Dokumentation**
🛠️ **[Vollständige SDK-RBAC-Implementierungsanleitung](../../../3_sdk/5_advanced_topics/5_rbac/)**

Behandelt:

- Zugriffsschutz auf Controller-Ebene
- Dynamische Berechtigungsauflösung
- Implementierung der Dienst- und Agenten-Zugriffskontrolle
- Erweiterte Berechtigungsmuster und Platzhalter
- Benutzerdefinierte Validierungslogik
- Testen von RBAC-Implementierungen
- Leistungsoptimierung und Best Practices
:::

## Schneller Überblick

**Rollenbasierte Zugriffskontrolle (RBAC)** ist ein Sicherheitsframework, das den Systemzugriff basierend auf Benutzerrollen innerhalb einer Organisation einschränkt. Der AI-Hub implementiert ein ausgeklügeltes, hierarchisches RBAC-System, das eine granulare Kontrolle über jeden Aspekt Ihrer KI-Plattform bietet.

### Hauptvorteile

**🛡️ Enterprise Security Compliance**: Erfüllen Sie strenge regulatorische Anforderungen mit umfassenden Audit-Trails und granularen Zugriffskontrollen.

**🎯 Granulare Ressourcenkontrolle**: Kontrollieren Sie den Zugriff auf spezifische KI-Agenten, Prozesse und Dienste mit Präzision.

**⚡ Skalierbare Berechtigungsverwaltung**: Verwalten Sie Berechtigungen effizient in großen Organisationen mithilfe rollenbasierter Hierarchien.

**🔗 Nahtlose Enterprise-Integration**: Native Integration mit bestehenden Enterprise-Identity-Systemen.

**🧠 Risikobewusste KI-Bereitstellung**: Stellen Sie KI-Funktionen mit Vertrauen bereit, wissend, dass der Zugriff kontrolliert und überwacht wird.

### Kernkomponenten

- **Rollen**: Benannte Sammlungen von Zugriffsregeln, die definieren, was Benutzer tun können
- **Zugriffsregeln**: Spezifische Berechtigungen mithilfe der Punktnotation (z. B. `aihub.admin.service.roles`)
- **Benutzeridentität**: Integration mit Unternehmensauthentifizierungssystemen (Azure AD, OAuth2)
- **Berechtigungsvorlagen**: Dynamische Berechtigungsprüfung mit Pfadparameter-Substitution
- **Platzhalter-Unterstützung**: Flexible Mustererkennung mit den Platzhaltern `*`, `>`, `?*` und `?>`

### Berechtigungsstruktur

Das System verwendet eine strukturierte Namenskonvention für Berechtigungen:

```
aihub.[user|admin].[resource_type].[resource_category].[resource_identifier]
```

**Beispiele:**

- `aihub.user.agent.customer_service.chatbot_v2` – Benutzerzugriff auf spezifischen Agenten
- `aihub.admin.service.roles` – Admin-Zugriff auf die Rollenverwaltung
- `aihub.user.agent.?>` – Benutzerzugriff auf jeden Agenten (Platzhalter)

## Wählen Sie Ihren Pfad

- **Entwickler & Integratoren**: Beginnen Sie mit der
  [SDK-Implementierungsanleitung](../../../3_sdk/5_advanced_topics/5_rbac/)

Beide Anleitungen bieten eine umfassende Abdeckung des AI-Hub RBAC-Systems, zugeschnitten auf Ihre spezifischen Bedürfnisse und Anwendungsfälle.
