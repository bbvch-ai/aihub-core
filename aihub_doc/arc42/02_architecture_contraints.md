# Randbedingungen

<!--

> **How to arc42:** 💡
>
>**Inhalt**
>
>Randbedingungen und Vorgaben, die ihre Freiheiten bezüglich Entwurf,
>Implementierung oder Ihres Entwicklungsprozesses einschränken. Diese
>Randbedingungen gelten manchmal organisations- oder firmenweit über die
>Grenzen einzelner Systeme hinweg.
>
>**Motivation**
>
>Für eine tragfähige Architektur sollten Sie genau wissen, wo Ihre
>Freiheitsgrade bezüglich der Entwurfsentscheidungen liegen und wo Sie
>Randbedingungen beachten müssen. Sie können Randbedingungen vielleicht
>noch verhandeln, zunächst sind sie aber da.
>
>**Form**
>
>Einfache Tabellen der Randbedingungen mit Erläuterungen. Bei Bedarf
>unterscheiden Sie technische, organisatorische und politische
>Randbedingungen oder übergreifende Konventionen (beispielsweise
>Programmier- oder Versionierungsrichtlinien, Dokumentations- oder
>Namenskonvention).
>
>Siehe [Randbedingungen](https://docs.arc42.org/section-2/) in der
>online-Dokumentation (auf Englisch!).
-->

| Randbedingungen    | Beschreibung                                                                                                                                                            |
|--------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| IAM                |Die Nutzer des bbv AI Hub sollen sich mit ihren normalen Geschäftslogins (z.B. azure Entra ID) einloggen können|
| Cloud Plattform    |Die Applikation des bbv AI Hub soll auf verschiedenen Cloudplattformen betrieben werden. Fokus der Unterstützung ist aber Azure|
| On-Prem Betrieb    |Der AI Hub soll auch On-Prem betrieben werden können bei sensitiven Daten|
| Programmiersprache |Das Backend und die KI Logic wird mit Python entwickelt um nächstmöglich an der Wissenschaft und Forschung zu sein.|
| Mehrsprachigkeit   |Die Applikation als auch die Agenten-Konfiguration soll mehrsprachig sein. Fokus auf Schweizer Landessprachen und Englisch.|
| Datenhaltung       |Es muss möglich sein sämtlich Daten in der Schweiz zu halten.|
| Datenverarbeitung  |Es muss möglich sein sämtlich Daten in der Schweiz zu verarbeiten.|
| ...                |Die Applikation als auch die Agenten-Konfiguration soll mehrsprachig sein. Fokus auf Schweizer Landessprachen und Englisch.|


## Organisatorische Randbedingungen

| Randbedingungen    | Beschreibung                                                                                                                                   |
|--------------------|------------------------------------------------------------------------------------------------------------------------------------------------|
| Team                | Die Entwicklung des bbv AI Hubs wird durch das DSX-AI Team geleitet. Allfällige zusätzliche bbv Mitarbeiten können zwischenzeitlich mitwirken. |
| interner Betrieb    | Die Applikation wird auch bbv intern verwendet.                                                                                                |
| Testwerkzeuge    | <ul><li>Das Frontend (Client) wird über dedizierte Frontend Tests getestet, welche das Backend weg mocken.</li><li>Das Backend wird mittels Unit-Tests und Integrationstests getestet.</li><li>Integrationstests umfassen die deployten Ressourcen.</li><li>Die Tests werden vor den Deployments auf der Ziel-Umgebung getestet.<ul><li>z.B. Bei Merge auf dev wird auf der Dev-Umgebung/Infrastruktur getestet.</li><li>Bei Deployment zu Kunde X wird auf der Umgebung/Infrastruktur des Kunden X getestet.</li></ul></li></ul>                                                                      |
| ...                | Die Applikation als auch die Agenten-Konfiguration soll mehrsprachig sein. Fokus auf Schweizer Landessprachen und Englisch.                    |

