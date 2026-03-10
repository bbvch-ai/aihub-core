---
title: Überlegungen zur Skalierung
source_sha: 8fda0e6ad1c2df54a219fcfb1bd763dcfd3f5424628578bece62c9557cec99e2
---

# Skalierbarkeit

Der Swiss AI Hub implementiert Skalierbarkeit als zentrales Architekturprinzip, das es Organisationen ermöglicht, ihre
KI-Fähigkeiten von Pilotprojekten bis hin zu unternehmensweiten Implementierungen ohne grundlegende architektonische
Änderungen auszubauen. Das Design der Plattform stellt sicher, dass die Skalierung der Kapazität lediglich operative
Anpassungen – das Bereitstellen zusätzlicher Instanzen – erfordert, anstatt Code-Modifikationen oder architektonische
Neugestaltungen.

## Horizontale Skalierbarkeit durch ereignisgesteuerte Architektur

Die ereignisgesteuerte Architektur ermöglicht horizontale Skalierbarkeit und Systemresilienz:

**Zustandsloser Agent-Code**: Die Agentenlogik enthält keinen veränderbaren Zustand, wodurch jede Instanz jedes Ereignis
verarbeiten kann. Dieses zustandslose Design eliminiert den Koordinationsaufwand, der typischerweise in verteilten
Systemen erforderlich ist, und ermöglicht es neuen Instanzen, die Arbeit sofort nach der Bereitstellung ohne
Synchronisation oder Zustandsübertragung zu beginnen.

**Lastverteilung**: Ereignisse werden zur parallelen Verarbeitung über mehrere Agenteninstanzen verteilt. Die
Messaging-Infrastruktur gleicht die Arbeit automatisch über die verfügbaren Instanzen aus und gewährleistet so eine
optimale Ressourcennutzung ohne manuelle Lastverteilungskonfiguration. Organisationen können die Kapazität einfach durch
Ändern der Anzahl laufender Instanzen anpassen.

**Fehlerwiederherstellung**: Fehlgeschlagene Operationen werden durch Ereigniswiederholung ohne Zustandsverlust erneut
versucht. Wenn eine Agenteninstanz während der Verarbeitung ausfällt, kann eine andere Instanz die Arbeit sofort wieder
aufnehmen, indem sie den Ereignisverlauf wiederholt. Dieses Resilienzmodell stellt sicher, dass keine Arbeit verloren
geht und keine manuelle Intervention für die Wiederherstellung erforderlich ist.

**Systemevolution**: Neue Ereignistypen werden eingeführt, ohne bestehende Komponenten zu modifizieren. Die automatische
Ereignistyp-Registrierung und die Mechanismen der graceful degradation ermöglichen eine kontinuierliche
Weiterentwicklung der Plattform. Organisationen können neue Funktionen inkrementell bereitstellen, wobei verschiedene
Versionen während Migrationsphasen gleichzeitig betrieben werden können.

## Operative Skalierung

Organisationen können die Agentenkapazität durch die Bereitstellung zusätzlicher Instanzen ohne architektonische
Änderungen skalieren. Die Plattform unterstützt mehrere Skalierungsdimensionen:

**Compute-Skalierung**: Stellen Sie zusätzliche Agenteninstanzen bereit, um ein erhöhtes Verarbeitungsvolumen zu
bewältigen. Jede Instanz arbeitet unabhängig, verbraucht Ereignisse aus gemeinsamen Streams und verarbeitet Aufgaben
parallel zu anderen Instanzen.

**Geografische Verteilung**: Agenteninstanzen können in verschiedenen geografischen Regionen betrieben werden, ohne
einen gemeinsamen Zustand zu benötigen. Die Messaging-Infrastruktur gewährleistet die Ereignisbereitstellung unabhängig
vom physischen Standort und ermöglicht globale Bereitstellungen, die die Latenz für verteilte Benutzerpopulationen
reduzieren.

**Inkrementelle Upgrades**: System-Upgrades werden inkrementell ohne Dienstunterbrechung bereitgestellt. Organisationen
können neue Agentenversionen parallel zu bestehenden Versionen bereitstellen und den Datenverkehr schrittweise auf
aktualisierte Implementierungen umleiten, während die Möglichkeit zum Rollback bei Problemen erhalten bleibt.

### Horizontale Skalierbarkeit

Die ereignisgesteuerte Architektur ermöglicht eine mühelose Skalierung zur Bewältigung schwankender Anforderungen. Wenn
die Systemlast steigt, können zusätzliche Worker-Instanzen bereitgestellt werden, um Ereignisse aus denselben Streams zu
verarbeiten, ohne dass Änderungen am Anwendungscode oder an der Architektur erforderlich sind. Diese Worker verteilen
die Verarbeitungslast automatisch, indem sie Ereignisse parallel verarbeiten.

Dieser Ansatz bietet mehrere betriebliche Vorteile: Die Kapazität kann in Spitzenzeiten dynamisch erhöht und in ruhigen
Zeiten reduziert werden, die Systemleistung bleibt bei wachsender Arbeitslast konstant, und es gibt keine Engpässe durch
zentralisierte Verarbeitung. Da die Ereignisverarbeitung zustandslos ist, arbeitet jeder Worker unabhängig – wenn einer
ausfällt, verarbeiten andere weiter, und der ausgefallene Worker kann neu gestartet werden, ohne laufende Operationen zu
beeinträchtigen.

Organisationen können spezifische Komponenten basierend auf den tatsächlichen Nachfragemustern skalieren. Wenn die
Agentenausführung mehr Kapazität erfordert, können zusätzliche Agenten-Worker bereitgestellt werden. Wenn die
Datenaufnahme zu einem Engpass wird, können weitere Pipeline-Worker hinzugefügt werden.
