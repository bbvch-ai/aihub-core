---
title: Berechtigungen und Zugriffssteuerung
source_sha: bd361125cef4f0771898aac3f0377aa388f9e18b432715c88170d0d772f60c21
---

# Berechtigungen und Zugriffssteuerung

Die Benutzeroberfläche der Swiss AI Hub Suite implementiert eine ausgeklügelte berechtigungsbasierte Zugriffssteuerung,
die das Benutzererlebnis dynamisch an das Autorisierungslevel jedes Einzelnen anpasst. Dieser Ansatz stellt sicher, dass
Benutzer nur relevante Funktionen sehen, während gleichzeitig Sicherheits- und Compliance-Anforderungen eingehalten
werden.

## Dynamische Dienstsichtbarkeit

Traditionelle Anwendungsoberflächen präsentieren oft alle Funktionen allen Benutzern und verlassen sich auf
Authentifizierungsprüfungen, um unautorisierten Zugriff zu blockieren. Dies führt zu überladenen Benutzeroberflächen mit
deaktivierten Schaltflächen und Funktionen, die Benutzer nicht nutzen können, was zu Verwirrung und Supportaufwand
führt. Der Swiss AI Hub denkt diesen Ansatz durch dynamische Dienstsichtbarkeit grundlegend neu.

**Berechtigungsgefilterter Dienstkatalog**: Wenn die Suite geladen wird, fragt sie das Backend nach dem autorisierten
Dienstkatalog des Benutzers ab. Das Backend bewertet die Berechtigungen des Benutzers anhand der Anforderungen jedes
registrierten Dienstes und gibt nur Dienste zurück, auf die der Benutzer zugreifen kann. Die Benutzeroberfläche rendert
Navigationselemente ausschließlich für autorisierte Dienste – Benutzer sehen einfach niemals Funktionen, die sie nicht
nutzen können.

**Saubere, fokussierte Benutzeroberfläche**: Dieser Ansatz schafft im Vergleich zu traditionellen Anwendungen dramatisch
einfachere Benutzeroberflächen. Ein Data Scientist sieht prominent präsentierte Evaluierungs- und Experimentierdienste.
Ein Business Analyst sieht Konversationsverläufe und Wissenserkundungstools. Ein Administrator sieht Benutzerverwaltung
und Systemkonfigurationsoptionen. Die Benutzeroberfläche jedes Benutzers spiegelt seine tatsächlichen Fähigkeiten wider,
nicht einen universellen Funktionssatz, der mit unzugänglichen Optionen überladen ist.

**Automatische Berechtigungsaktualisierungen**: Wenn ein Administrator die Rollenzuweisungen oder Berechtigungsvergaben
eines Benutzers ändert, spiegeln sich diese Änderungen bei der nächsten Sitzung des Benutzers automatisch in dessen
Benutzeroberfläche wider. Es ist keine Cache-Invalidierung, manuelle Aktualisierung oder ein Abmelde-Anmeldezyklus
erforderlich. Die Architektur der Suite stellt sicher, dass die Benutzeroberfläche stets eine genaue Ansicht des
aktuellen Autorisierungsstatus präsentiert.

**Sicherheit durch Unsichtbarkeit**: Indem die Suite keine Navigationselemente für nicht autorisierte Dienste rendert,
eliminiert sie eine ganze Klasse von Sicherheitslücken. Benutzer können nicht versuchen, auf eingeschränkte Dienste
durch Manipulation der Benutzeroberfläche zuzugreifen, da diese Dienste keine Schnittstellenpräsenz haben. Dieser
Defense-in-Depth-Ansatz ergänzt die Backend-Autorisierungsdurchsetzung.

## Hierarchisches Berechtigungssystem

Die Suite ist in das umfassende hierarchische Berechtigungssystem des Swiss AI Hub integriert, das eine fein abgestufte
Zugriffssteuerung durch eine strukturierte, Punkt-Notation-Berechtigungssyntax bietet.

**Berechtigungsstruktur**: Berechtigungen folgen dem Format
`aihub.[user|admin].<service>.<resource_type>.<resource_id>`, wodurch ein hierarchischer Namensraum geschaffen wird, der
eine präzise Zugriffssteuerung ermöglicht. Zum Beispiel gewährt `aihub.user.agent.support_agent.instance_001` Zugriff
auf eine bestimmte Agenteninstanz, während `aihub.admin.knowledge` administrativen Zugriff auf den gesamten
Wissensmanagementdienst gewährt.

**Wildcard-Unterstützung**: Das Berechtigungssystem unterstützt ausgeklügelte Wildcards, die eine flexible
Zugriffssteuerung ermöglichen, ohne dass jede Ressource explizit aufgelistet werden muss. Der `*`-Wildcard passt zu
jedem einzelnen Pfadsegment, während der `>`-Wildcard zu allen verbleibenden Pfadsegmenten passt. Dies ermöglicht Regeln
wie `aihub.user.agent.>`, um Zugriff auf alle Agentenressourcen in beliebiger Tiefe zu gewähren.

**Implizite Berechtigungen**: Benutzer mit dem impliziten Berechtigungsmuster `aihub.user.?>` erhalten Zugriff auf alle
Dienste auf Benutzerebene, ohne dass explizite Genehmigungen für jeden Dienst erforderlich sind. Dies vereinfacht die
Berechtigungsverwaltung für Standardbenutzer, während eine fein abgestufte Kontrolle für spezialisierte Zugriffsmuster
beibehalten wird.

**Zugriffssteuerung auf Dienstebene**: Jeder Dienst-Controller deklariert minimale Berechtigungsanforderungen für den
Zugriff. Der Suite-Endpunkt bewertet, ob der Benutzer diese minimalen Berechtigungen besitzt, wenn der Dienstkatalog
erstellt wird. Dienste, die Berechtigungen erfordern, die der Benutzer nicht besitzt, erscheinen einfach nicht in der
Katalogantwort.

## Rollenbasierte Oberflächenanpassung

Über die einfache Anzeige-/Ausblendlogik hinaus implementiert die Suite eine rollenbewusste Oberflächenanpassung, die
verschiedene Ansichten und Funktionen basierend auf den Benutzerautorisierungsstufen präsentiert.

**Administrative Privilegien**: Wenn der Suite-Endpunkt Berechtigungen bewertet, stellt er nicht nur fest, ob der
Benutzer auf einen Dienst zugreifen kann, sondern auch, ob er administrative Privilegien für diesen Dienst besitzt.
Diese Unterscheidung wird an das Frontend kommuniziert, das zusätzliche administrative Funktionen innerhalb der
Benutzeroberfläche dieses Dienstes präsentieren kann.

**Kontextsensitive Navigation**: Die Suite berücksichtigt den aktuellen Autorisierungskontext des Benutzers. Beim
Anzeigen eines Agenten kann die Benutzeroberfläche feststellen, ob der Benutzer administrativen Zugriff auf diesen
spezifischen Agenten hat, und administrative Steuerelemente wie die Konfigurationsbearbeitung nur dann präsentieren,
wenn er autorisiert ist. Standardbenutzer sehen schreibgeschützte Ansichten derselben Ressourcen.

**Feingranulare Funktionssteuerung**: Innerhalb einzelner Dienste kann die Benutzeroberfläche die Berechtigungen des
Benutzers für bestimmte Ressourcen oder Operationen abfragen. Ein Benutzer könnte Lesezugriff auf Wissensdatenbanken
haben, aber keine Upload-Berechtigungen. Die Benutzeroberfläche spiegelt dies wider, indem sie Funktionen zur
Wissenserforschung anzeigt, während sie Steuerelemente für den Dokumentenupload ausblendet.

**Multi-Tenant-Isolation**: In Bereitstellungen, die mehrere Organisationseinheiten oder Kunden-Tenants bedienen,
gewährleistet das Berechtigungssystem eine vollständige Datenisolation. Benutzer sehen nur Dienste und Ressourcen, die
zu ihrem organisatorischen Kontext gehören, wodurch sichere, isolierte Arbeitsbereiche innerhalb einer gemeinsam
genutzten Plattformbereitstellung geschaffen werden.

## Architektur der Berechtigungsbewertung

Das berechtigungsbewusste Verhalten der Suite resultiert aus einer ausgeklügelten Koordination zwischen
Frontend-Abfragen und Backend-Evaluierungslogik.

**Backend-Berechtigungsbewertung**: Die gesamte Berechtigungsbewertung erfolgt im Backend, wodurch sichergestellt wird,
dass die Sicherheitsdurchsetzung nicht durch clientseitige Manipulation umgangen werden kann. Der Suite-Endpunkt fragt
das Berechtigungssystem ab, bewertet Zugriffsregeln anhand der Rollen und Berechtigungen des Benutzers und gibt einen
vorgefilterten Dienstkatalog zurück. Das Frontend vertraut diesem Katalog, ohne eine eigene Berechtigungslogik
auszuführen.

**Access Checker Integration**: Das Backend verwendet eine Access Checker Komponente, die die Logik zur
Berechtigungsbewertung kapselt. Diese Komponente akzeptiert eine Benutzeridentität und ein Berechtigungsmuster,
bewertet, ob die Zugriffsregeln des Benutzers mit dem Muster übereinstimmen, und gibt entweder boolesche
Zugriffsentscheidungen oder eine detaillierte Aufzählung der Zugriffsebenen zurück (verweigert, Benutzerzugriff,
administrativer Zugriff).

**Effiziente Berechtigungsabfragen**: Die Berechtigungsbewertung ist durch Caching-Strategien und effiziente
Musterabgleichs-Algorithmen auf Leistung optimiert. Wenn der Suite-Endpunkt die Dienstsichtbarkeit für einen Benutzer
bewertet, führt er diese Bewertungen parallel statt sequenziell durch, um schnelle Ladezeiten der Benutzeroberfläche
auch bei zahlreichen Diensten zu gewährleisten.

**Generierung von Audit-Trails**: Jede Berechtigungsbewertung generiert Audit-Log-Einträge, die dokumentieren, welche
Berechtigungen geprüft wurden, für welchen Benutzer und welche Entscheidung getroffen wurde. Dies schafft umfassende
Audit-Trails zur Unterstützung der Compliance-Berichterstattung und der Sicherheitsforensik.

## Dienstspezifische Berechtigungsmuster

Verschiedene Dienste implementieren unterschiedliche Berechtigungsmuster basierend auf ihren funktionalen Anforderungen,
was die Flexibilität des hierarchischen Berechtigungssystems demonstriert.

**Agentendienst**: Implementiert eine Zugriffskontrolle pro Agent, bei der Benutzer möglicherweise Zugriff auf bestimmte
Agenteninstanzen haben, aber nicht auf andere. Berechtigungen wie `aihub.user.agent.customer_support.cs_001` gewähren
Zugriff auf einen spezifischen Agenten, während `aihub.user.agent.customer_support.*` Zugriff auf alle Instanzen dieser
Agentenklasse gewährt.

**Thread-Dienst**: Steuert den Zugriff auf Konversations-Threads basierend auf Eigentums- und Freigaberegeln. Benutzer
haben in der Regel Zugriff auf Threads, die sie erstellt oder an denen sie teilgenommen haben, wobei Administratoren
eine breitere Sichtbarkeit für Support- und Überwachungszwecke haben.

**Wissensdienst**: Implementiert eine Namespace-basierte Zugriffssteuerung, bei der Berechtigungen auf Datenbankebene
(`aihub.user.knowledge.hr_documents`) oder Namespace-Ebene (`aihub.user.knowledge.hr_documents.policies`) vergeben
werden können, mit hierarchischer Vererbung durch den Berechtigungsbaum.

**Administrative Dienste**: Erfordern explizite administrative Berechtigungen wie `aihub.admin.users` oder
`aihub.admin.roles`. Diese Dienste erscheinen niemals für Benutzer ohne administrative Berechtigungen, wodurch eine
klare Trennung zwischen Standard- und administrativen Benutzeroberflächen geschaffen wird.

## Vorteile für die Benutzererfahrung

Die berechtigungsbewusste Suite-Architektur bietet erhebliche Vorteile für die Benutzererfahrung und den Betrieb.

**Eliminierung von „Zugriff verweigert“-Fehlern**: Benutzer stoßen niemals auf „Zugriff verweigert“-Meldungen für
sichtbare Benutzeroberflächenelemente, da nicht autorisierte Funktionen einfach nicht erscheinen. Dies eliminiert eine
häufige Quelle von Benutzerfrustration und Support-Tickets in traditionellen Unternehmensanwendungen.

**Reduzierte Benutzeroberflächenkomplexität**: Indem nur autorisierte Funktionen angezeigt werden, bleibt die
Benutzeroberfläche übersichtlich und fokussiert. Benutzer müssen sichtbare, aber deaktivierte Funktionen nicht mental
von verfügbaren Funktionen filtern – alles, was sie sehen, können sie nutzen.

**Selbstbedienungs-Zugriffsverständnis**: Benutzer können ihre autorisierten Funktionen sofort verstehen, indem sie
beobachten, was in der Suite-Navigation erscheint. Es ist nicht nötig, separate Dokumentationen zu konsultieren oder den
Support zu kontaktieren, um herauszufinden, auf welche Funktionen sie zugreifen können.

**Optimiertes Onboarding**: Neue Benutzer sehen nur die für ihre Rolle relevanten Funktionen, was die anfängliche
Plattformorientierung dramatisch vereinfacht. Schulungen können sich auf relevante Funktionen konzentrieren, anstatt
Benutzern zu erklären, worauf sie nicht zugreifen können und warum.

## Sicherheits- und Compliance-Vorteile

Die berechtigungsbewusste Architektur bietet über die Verbesserungen der Benutzererfahrung hinaus Sicherheits- und
Compliance-Vorteile.

**Defense in Depth**: Die clientseitige Filterung nicht autorisierter Dienste ergänzt die
Backend-Berechtigungsdurchsetzung und schafft mehrere Sicherheitsebenen. Selbst wenn ein Angreifer das Frontend
manipuliert, verhindert die Backend-Autorisierungsdurchsetzung unautorisierte Operationen.

**Reduzierte Angriffsfläche**: Indem keine Informationen über Dienste preisgegeben werden, auf die Benutzer nicht
zugreifen können, enthüllt die Suite potenziellen Angreifern weniger über die Fähigkeiten der Bereitstellung. Benutzer
können deaktivierte Funktionen nicht sondieren, um Informationen für Angriffe zu sammeln.

**Compliance-Unterstützung**: Die umfassende Audit-Protokollierung von Berechtigungsbewertungen unterstützt
regulatorische Compliance-Anforderungen für die Zugriffssteuerung, insbesondere in Sektoren mit strengen
Datenschutzanforderungen wie Gesundheitswesen, Finanzen und öffentlicher Verwaltung.

**Zero-Trust-Architektur**: Die Suite implementiert Zero-Trust-Prinzipien, bei denen jeder Dienstzugriff eine explizite
Berechtigungsbewertung erfordert. Es gibt keine impliziten Vertrauensannahmen basierend auf dem Netzwerkstandort oder
einer früheren Authentifizierung – jede Operation wird unabhängig autorisiert.

## Betriebliche Vorteile

Über Sicherheit und Benutzererfahrung hinaus bietet das Berechtigungssystem betriebliche Vorteile für
Plattformadministratoren.

**Zentralisierte Berechtigungsverwaltung**: Administratoren verwalten Berechtigungen über den Rollenverwaltungsdienst,
wobei Änderungen automatisch in der gesamten Suite widergespiegelt werden. Es ist nicht erforderlich,
Zugriffssteuerungen für jeden Dienst separat zu konfigurieren oder Berechtigungen über mehrere Systeme hinweg zu
koordinieren.

**Flexible Delegation**: Das hierarchische Berechtigungssystem ermöglicht ausgeklügelte Delegationsmuster. Leitenden
Mitarbeitern können breite Zugriffsmuster wie `aihub.user.agent.>` gewährt werden, während jüngere Mitarbeiter
spezifische Berechtigungen für einzelne Ressourcen erhalten. Diese Flexibilität unterstützt Organisationsstrukturen,
ohne komplexe Zugriffssteuerungskonfigurationen zu erfordern.

**Berechtigungsvererbung**: Die hierarchische Struktur ermöglicht die Berechtigungsvererbung, wobei die Gewährung des
Zugriffs auf eine Ressource höherer Ebene automatisch den Zugriff auf enthaltene Ressourcen ermöglicht. Dies vereinfacht
die Berechtigungsverwaltung, während bei Bedarf eine präzise Kontrolle beibehalten wird.

**Rollenbasierte Administration**: Anstatt individuelle Benutzerberechtigungen zu verwalten, weisen Administratoren
Benutzern typischerweise Rollen zu, die Standardberechtigungssätze definieren. Rollenänderungen gelten automatisch für
alle zugewiesenen Benutzer, wodurch eine konsistente Zugriffssteuerung über Benutzerpopulationen hinweg gewährleistet
wird.

Diese berechtigungsbewusste Architektur stellt sicher, dass die Swiss AI Hub Suite jedem Benutzer eine fokussierte,
sichere Benutzeroberfläche bietet, die präzise auf dessen Autorisierungslevel und organisatorische Rolle zugeschnitten
ist, während die betriebliche Einfachheit und die Sicherheitsstrenge, die für Unternehmens- und öffentliche
Sektorbereitstellungen erforderlich sind, beibehalten werden.

# Rollenbasierte Zugriffssteuerung (RBAC) :shield: :lock:

::: info **Aktualisierung der Dokumentationsstruktur**
Die RBAC-Dokumentation wurde neu organisiert, um verschiedenen Zielgruppen besser gerecht zu werden. Diese Seite bietet
schnellen Zugriff auf die für Ihre Bedürfnisse passende Dokumentation.
:::

## Schnellnavigation

### Für Entwickler und SDK-Benutzer

Wenn Sie RBAC in Ihren benutzerdefinierten Agenten, APIs oder Diensten implementieren und technische
Implementierungsdetails benötigen:

::: tip **SDK-Dokumentation**
🛠️ **[Vollständiger SDK RBAC Implementierungsleitfaden](../../../3_sdk/5_advanced_topics/5_rbac/)**

Umfasst:

- Zugriffsschutz auf Controller-Ebene
- Dynamische Berechtigungsauflösung
- Implementierung der Zugriffssteuerung für Dienste und Agenten
- Erweiterte Berechtigungsmuster und Wildcards
- Benutzerdefinierte Validierungslogik
- Testen von RBAC-Implementierungen
- Leistungsoptimierung und Best Practices
:::

## Kurzübersicht

**Rollenbasierte Zugriffssteuerung (RBAC)** ist ein Sicherheitsframework, das den Systemzugriff basierend auf
Benutzerrollen innerhalb einer Organisation einschränkt. Der AI-Hub implementiert ein ausgeklügeltes, hierarchisches
RBAC-System, das eine granulare Kontrolle über jeden Aspekt Ihrer KI-Plattform bietet.

### Hauptvorteile

**🛡️ Enterprise Security Compliance**: Erfüllen Sie strenge regulatorische Anforderungen mit umfassenden Audit-Trails
und granularer Zugriffssteuerung.

**🎯 Granulare Ressourcenkontrolle**: Steuern Sie den Zugriff auf spezifische KI-Agenten, Prozesse und Dienste mit
Präzision.

**⚡ Skalierbare Berechtigungsverwaltung**: Verwalten Sie Berechtigungen effizient in großen Organisationen mithilfe
rollenbasierter Hierarchien.

**🔗 Nahtlose Enterprise-Integration**: Native Integration mit bestehenden Unternehmens-Identitätssystemen.

**🧠 Risikobewusste KI-Bereitstellung**: Stellen Sie KI-Funktionen mit Zuversicht bereit, da der Zugriff kontrolliert und
überwacht wird.

### Kernkomponenten

- **Rollen**: Benannte Sammlungen von Zugriffsregeln, die definieren, was Benutzer tun können
- **Zugriffsregeln**: Spezifische Berechtigungen in Punkt-Notation (z. B. `aihub.admin.service.roles`)
- **Benutzeridentität**: Integration mit bestehenden Unternehmens-Authentifizierungssystemen (Azure AD, OAuth2)
- **Berechtigungsvorlagen**: Dynamische Berechtigungsprüfung mit Pfadparameter-Substitution
- **Wildcard-Unterstützung**: Flexible Mustererkennung mit `*`, `>`, `?*` und `?>` Wildcards

### Berechtigungsstruktur

Das System verwendet eine strukturierte Namenskonvention für Berechtigungen:

```
aihub.[user|admin].[resource_type].[resource_category].[resource_identifier]
```

**Beispiele:**

- `aihub.user.agent.customer_service.chatbot_v2` - Benutzerzugriff auf spezifischen Agenten
- `aihub.admin.service.roles` - Admin-Zugriff auf die Rollenverwaltung
- `aihub.user.agent.?>` - Benutzerzugriff auf jeden Agenten (Wildcard)

## Wählen Sie Ihren Pfad

- **Entwickler & Integratoren**: Beginnen Sie mit dem
  [SDK Implementierungsleitfaden](../../../3_sdk/5_advanced_topics/5_rbac/)

Beide Leitfäden bieten eine umfassende Abdeckung des AI-Hub RBAC-Systems, zugeschnitten auf Ihre spezifischen
Bedürfnisse und Anwendungsfälle.
