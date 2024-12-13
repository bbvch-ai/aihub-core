# Verteilungssicht

> **How to arc42:** 💡
>
>**Inhalt**
>
>Die Verteilungssicht beschreibt:
>
>1.  die technische Infrastruktur, auf der Ihr System ausgeführt wird,
>    mit Infrastrukturelementen wie Standorten, Umgebungen, Rechnern,
>    Prozessoren, Kanälen und Netztopologien sowie sonstigen
>    Bestandteilen, und
>
>2.  die Abbildung von (Software-)Bausteinen auf diese Infrastruktur.
>
>Häufig laufen Systeme in unterschiedlichen Umgebungen, beispielsweise
>Entwicklung-/Test- oder Produktionsumgebungen. In solchen Fällen sollten
>Sie alle relevanten Umgebungen aufzeigen.
>
>Nutzen Sie die Verteilungssicht insbesondere dann, wenn Ihre Software
>auf mehr als einem Rechner, Prozessor, Server oder Container abläuft
>oder Sie Ihre Hardware sogar selbst konstruieren.
>
>Aus Softwaresicht genügt es, auf die Aspekte zu achten, die für die
>Softwareverteilung relevant sind. Insbesondere bei der
>Hardwareentwicklung kann es notwendig sein, die Infrastruktur mit
>beliebigen Details zu beschreiben.
>
>**Motivation**
>
>Software läuft nicht ohne Infrastruktur. Diese zugrundeliegende
>Infrastruktur beeinflusst Ihr System und/oder querschnittliche
>Lösungskonzepte, daher müssen Sie diese Infrastruktur kennen.
>
>**Form**
>
>Das oberste Verteilungsdiagramm könnte bereits in Ihrem technischen
>Kontext enthalten sein, mit Ihrer Infrastruktur als EINE Blackbox. Jetzt
>zoomen Sie in diese Infrastruktur mit weiteren Verteilungsdiagrammen
>hinein:
>
>-   Die UML stellt mit Verteilungsdiagrammen (Deployment diagrams) eine
>    Diagrammart zur Verfügung, um diese Sicht auszudrücken. Nutzen Sie
>    diese, evtl. auch geschachtelt, wenn Ihre Verteilungsstruktur es
>    verlangt.
>
>-   Falls Ihre Infrastruktur-Stakeholder andere Diagrammarten
>    bevorzugen, die beispielsweise Prozessoren und Kanäle zeigen, sind
>    diese hier ebenfalls einsetzbar.
>
>Siehe [Verteilungssicht](https://docs.arc42.org/section-7/) in der
>online-Dokumentation (auf Englisch!).
>
>## Infrastruktur Ebene 1
>
>An dieser Stelle beschreiben Sie (als Kombination von Diagrammen mit
>Tabellen oder Texten):
>
>-   die Verteilung des Gesamtsystems auf mehrere Standorte, Umgebungen,
>    Rechner, Prozessoren o. Ä., sowie die physischen Verbindungskanäle
>    zwischen diesen,
>
>-   wichtige Begründungen für diese Verteilungsstruktur,
>
>-   Qualitäts- und/oder Leistungsmerkmale dieser Infrastruktur,
>
>-   Zuordnung von Softwareartefakten zu Bestandteilen der Infrastruktur
>
>Für mehrere Umgebungen oder alternative Deployments kopieren Sie diesen
>Teil von arc42 für alle wichtigen Umgebungen/Varianten.
>
>***&lt;Übersichtsdiagramm>***
>
>Begründung  
>*&lt;Erläuternder Text>*
>
>Qualitäts- und/oder Leistungsmerkmale  
>*&lt;Erläuternder Text>*
>
>Zuordnung von Bausteinen zu Infrastruktur  
>*&lt;Beschreibung der Zuordnung>*
>
>## Infrastruktur Ebene 2
>
>An dieser Stelle können Sie den inneren Aufbau (einiger)
>Infrastrukturelemente aus Ebene 1 beschreiben.
>
>Für jedes Infrastrukturelement kopieren Sie die Struktur aus Ebene 1.
>
>### *&lt;Infrastrukturelement 1>*
>
>*&lt;Diagramm + Erläuterungen>*
>
>### *&lt;Infrastrukturelement 2>*
>
>*&lt;Diagramm + Erläuterungen>*
>
>…
>
>### *&lt;Infrastrukturelement n>*
>
>*&lt;Diagramm + Erläuterungen>*

 
```plantuml
@startuml

' !theme blueprint





cloud "Private SubNet" as SubNet {


  
  ' APP service
  node "APP" as APP {
    [API] as api
    [Frontend] as fapp
    database "Entity + Event store" as eventstore
    api -> eventstore
    fapp -> api : served by

  }

  ' Central messaging or event bus
  node "NATS" as nats

  ' Store layer: Document store, caches, vector DB, aggregator services
  node "STORES" as stores {
    database "Doc-Store" as docstore
    database "Vector-Store" as vectorDB

  }
  
  node "AG1" as ag1
  node "AG2" as ag2


   node "Phoenix" as PH {
     database "PostGres" as pg_ph
     [Phoenix] as phoenix
     phoenix -left-> pg_ph
   }
   
   node "Dagster" as DG {
     database "PostGres" as pg_dg
     [Dagster] as dagster
     [OAuth2Proxy] as dagster_proxy
     dagster -> pg_dg
     dagster_proxy -> dagster : forward
   }
}

' Example of relationships (adjust as per the drawing)
api <--> nats : Publish/Subscribe
dagster <--> nats : Publish/Subscribe
ag1 <-up-> nats : Publish/Subscribe
ag2 <-up-> nats : Publish/Subscribe
ag1 -up-> phoenix : trace
ag2 -up-> phoenix : trace
ag1 -down-> docstore
ag2 -down-> docstore
ag2 -down-> vectorDB
ag1 -down-> vectorDB

circle "port-3000" as p3000
circle "port-6006" as p6006
circle "port-80" as p80

p80 -down- api
p6006 - phoenix
p3000 -down- dagster_proxy

:Client User: as user
:Dagster User: as dg_user
:Phoenix User: as ph_user

user --> p80 : [].ai-agents.ch
dg_user --> p3000 : dagter.[].ai-agents.ch
ph_user -down-> p6006 : phoenix.[].ai-agents.ch


@enduml
```