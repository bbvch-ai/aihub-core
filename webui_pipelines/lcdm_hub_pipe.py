"""
title: Swiss LCDM Hub Assistent
author: Noah Hermann
version: 0.1.0
"""

from pydantic import BaseModel, Field
import requests
import pandas as pd

GTO_PROMPT = """Sie sind Experte für Datenverarbeitung, das Abrufen von Daten aus 
Dateien und das Einfügen dieser Daten in vordefinierte Datenstrukturen, die so 
genannten GTOs (Generic Transfer Obejct). Sie werden mit GTOs und den dazugehörigen 
Daten versorgt. Bei diesen Daten handelt es sich hauptsächlich um 
Gebäudeinformationen. Durchsuchen Sie die Kontextdokumente nach Teilen, die mit den 
Schlüsseln in der GTO übereinstimmen, und legen Sie für jeden gefundenen Raum oder 
anderen Teil eines Gebäudes eine neue GTO an und füllen Sie sie mit allen 
relevanten Daten, die Sie finden können. Suchen Sie nach eindeutigen 
Identifikatoren wie Raumnamen oder Nummern, auf die in den Dokumenten verwiesen 
wird, und sammeln Sie alle relevanten Informationen dazu. Füllen Sie diese dann in 
die vordefinierte GTO-Struktur ein. Ändern Sie diese GTO-Struktur nicht, sondern 
finden Sie nur Input für sie. Verwenden Sie nur Daten, die vorhanden sind, und 
lassen Sie die Felder leer, wenn keine Informationen verfügbar sind. Es geht darum 
aus unstrukturierten Daten strukturierte zu machen, um diese dann in einer 
Datenbank abzulegen, deshalb ist es wichtig darauf zu achten, dass die Daten korrekt 
sind. Ansonsten werden die Einträge in der Datenbank falsch sein und dies kann 
schwere Folgen haben. Geben Sie also nur Daten an wenn Sie diese auch wirklich in 
finden und erfinden Sie nichts neues. Ebenfalls ist es wichtig zu überprüfen, dass 
die Daten dem richtigen key im GTO zugewiesen werden, daruch kann die Korrektheit 
der Daten sichergestellt werden.

Hier ist die GTO:

<GTO>
{gto}
<\GTO>

Zeigen Sie Ihre Ergebnisse in einer Tabelle mit den gefundenen Werten an. Wenn Sie 
mehrere Referenzen für denselben Raum finden, erstellen Sie nur ein einziges GTO für 
diesen Raum, indem Sie alle Daten zu diesem Raum in einer Instanz zusammenfassen. 
Nimm dir Zeit und überlege Schritt für Schritt wie du die Daten in das GTO einfügen 
sollst und achte darauf dass die Daten am korrekten Ort angezeigt werden. Gib das 
gesamte GTO an, auch die leeren Felder und achte dabei auf Korrektheit und 
Vollstándigkeit. Gib jegliche Attribute des GTOs an, wie wenn ich einen SELECT 
Befehl in einer Datenbank machen würde, formatiere die GTOs als Tabelle damit sie 
einfacher zu lesen sind. Gib nicht nur einzelne Beispiele an, sondern list ALLE 
Instanzen die du findest direkt auf. Gehe immer davon aus, dass der Benutzer alle 
gefundenen Daten aufgelistet haben will. Beachte dass nicht alle Felder eines 
GTO zwingend angegeben werden müssen, falls dies der Fall ist erstelle die GTOs 
mit den Daten die du findest. Extrahiere **IMMER ALLE** Instanzen des GTOs. Wenn 
es z.B. Fester oder Türen sind, extrahiere **IMMER ALLE** Fenster oder Türen."""

QUERY_PROMPT = "Based on the following question generate a standalone quey, that can be used to search for data transfer objects. <question>{question}</question>. Only generate a single query and nothing more."

TEST_DEFINITIONS = {
    "52": "ZZZBuilding X Floors",
    "53": "INSEL BB12 Doc Link",
    "103": "ZZZ Libal Floor GTO",
    "153": "ZZZ DaluxGTO",
    "202": "ZZZ DaluxGTO für Peter Krebs",
    "252": "ZZZ Building X Floors für Peter Krebs",
    "302": "INSEL BB12 Objekt GWK",
    "352": "ZZZ Libal",
    "402": "INSEL BB12 Objekt ARC Transportanlage",
    "403": "INSEL BB12 Objekt ELT Assembly StromSchienen",
    "404": "INSEL BB12 Objekt ELT Modellelemente",
    "405": "INSEL BB12 Objekt HEI Komponenten",
    "406": "INSEL BB12 Objekt KOO Brandabschottungen",
    "407": "INSEL BB12 Objekt LUF Assembly",
    "408": "INSEL BB12 Objekt LUF Komponenten",
    "409": "INSEL BB12 Objekt MED Komponenten",
    "410": "INSEL BB12 Objekt RPT Rohrpost",
    "411": "INSEL BB12 Objekte ARC Fenster Fassade",
    "412": "INSEL BB12 Objekte ARC Fenster Innenfenster",
    "413": "INSEL BB12 Objekte ARC Türen",
    "452": "KSSG 01 ROOM",
    "4364956": "INSEL General Katalog 2014 Elektro Raumkategorie",
    "4364972": "INSEL General Katalog 20 Abteilungen",
    "4364986": "INSEL General Katalog 20186 BACNet",
    "4365000": "INSEL General Katalog 20170 Betriebsmittel",
    "4365014": "INSEL General Katalog BKS ID",
    "4365029": "INSEL General Katalog 62 Bodenarten",
    "4365045": "INSEL General Katalog 61 Deckenarten",
    "4365067": "INSEL General Katalog 1201 eClass",
    "4365105": "INSEL General Katalog 2008 Export Hersteller",
    "4365135": "INSEL General Katalog 27 Lieferant",
    "4365157": "INSEL General Katalog 2011 Nutzung DIN 277",
    "4365187": "INSEL General Katalog 2003 Objektbezeichnung",
    "4365202": "INSEL General Katalog 20133 Raumtyp Insel",
    "4365219": "INSEL General Katalog 8512 Schaltschrank N Auf Objekt ID",
    "4365238": "INSEL General Katalog 2015 SKP",
    "4365259": "INSEL General Katalog 104 Standorte",
    "4365284": "INSEL General Katalog 2002 Typenkatalog",
    "4365331": "INSEL General Katalog 20171 Verortung ",
    "4365351": "INSEL General Katalog 49 Wandarten",
    "4365443": "INSEL General Katalog Lüftung",
    "4365481": "INSEL General Katalog 106 Waveware RaumCode",
    "5427724": "INSEL BB12 Raum strukturierte Daten",
    "6861396": "INSEL BB12 Objekt SAN Komponenten",
    "7217841": "ZZZ Muster Projekt Raum Daten",
    "7217842": "ZZZ BXLT Zone",
    "7217942": "KSB A02 ARC Raum strukturierte Daten",
    "7217943": "KSB A02 Objekt ELE Modellelemente",
    "7217944": "KSB A02 Objekt RPT Rohrpost",
    "7217945": "KSB A02 Objekt MOB Komponenten",
    "7217946": "KSB A02 Objekt LUE Assembly",
    "7217947": "KSB A02 Objekt LUE Komponenten",
    "7217948": "KSB A02 Objekt SAN Komponenten",
    "7217949": "KSB A02 Objekt STR Komponenten",
    "7217950": "ZZZ test 1",
    "7217951": "KSB A02 Excel CSV Heizung",
    "7217952": "KSB A02 Excel CSV Lüftung",
    "7217953": "INSEL BB12 Objekt LUF Assembly BXLT",
    "7217992": "GTO BB12 Objekt LUF Assembly copy",
    "7218042": "TestHubspotGtoContactsReader",
    "7220542": "TestHubspotGtoCompaniesReader",
    "7220592": "Test SOAP GTO Companies",
    "7220642": "Test SOAP GTO Contacts",
    "7220742": "Hubspot - PM Contacts",
    "7220792": "Hubspot - PM Companies",
    "7223292": "000_AT_BB12_Gto_Name",
    "7223342": "PM - Hubspot Companies",
}

TEST_GTO = {
    "id": 5427724,
    "name": "INSEL BB12 Raum strukturierte Daten",
    "idguid": "INSELBB12Raum",
    "gtoAttributeDefinitions": {
        "9001": {
            "id": 5427726,
            "key": "ARC Raumnummer BiG original",
            "dataType": None,
            "valueType": "",
            "unitOfMeasurement": "",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "9001",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "9006": {
            "id": 7217852,
            "key": "IFC GUID",
            "dataType": "MANUAL_VALUE_TYPE",
            "valueType": "",
            "unitOfMeasurement": "",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "9006",
            "mandatory": False,
            "relationFinderActive": None,
            "relatedGtoId": None,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0090": {
            "id": 5427725,
            "key": "Bodenablauf",
            "dataType": None,
            "valueType": "Int",
            "unitOfMeasurement": "",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0090",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0075": {
            "id": 5427727,
            "key": "Pissoirs",
            "dataType": None,
            "valueType": "Int",
            "unitOfMeasurement": "",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0075",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0010": {
            "id": 5427728,
            "key": "Gebäude",
            "dataType": None,
            "valueType": "String",
            "unitOfMeasurement": "",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0010",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0095": {
            "id": 5427729,
            "key": "Deckenart",
            "dataType": None,
            "valueType": "String",
            "unitOfMeasurement": "",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0095",
            "mandatory": False,
            "relationFinderActive": True,
            "relatedGtoId": 4365045,
            "relatedGtoAttributeKey": "Bezeichnung",
            "reportFields": {},
            "spellingValues": [],
        },
        "0030": {
            "id": 5427730,
            "key": "Raumnummer",
            "dataType": None,
            "valueType": "String",
            "unitOfMeasurement": "",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0030",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0170": {
            "id": 5427731,
            "key": "Raumkennzeichnung",
            "dataType": None,
            "valueType": "String",
            "unitOfMeasurement": "",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0170",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0050": {
            "id": 5427732,
            "key": "Bodenart",
            "dataType": None,
            "valueType": "String",
            "unitOfMeasurement": "",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0050",
            "mandatory": False,
            "relationFinderActive": True,
            "relatedGtoId": 4365029,
            "relatedGtoAttributeKey": "Bezeichnung",
            "reportFields": {},
            "spellingValues": [],
        },
        "0070": {
            "id": 5427733,
            "key": "WC's",
            "dataType": None,
            "valueType": "Int",
            "unitOfMeasurement": "",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0070",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0105": {
            "id": 5427734,
            "key": "Nutzhöhe",
            "dataType": None,
            "valueType": "Decimal",
            "unitOfMeasurement": "Meter",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0105",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0005": {
            "id": 5427735,
            "key": "Standort",
            "dataType": None,
            "valueType": "String",
            "unitOfMeasurement": "",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0005",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0500": {
            "id": 5427736,
            "key": "Fenster öffnenbar",
            "dataType": None,
            "valueType": "String",
            "unitOfMeasurement": "",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0500",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0145": {
            "id": 5427737,
            "key": "Max. Anzahl Betten",
            "dataType": None,
            "valueType": "Int",
            "unitOfMeasurement": "",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0145",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0025": {
            "id": 5427738,
            "key": "Raum-Code",
            "dataType": None,
            "valueType": "String",
            "unitOfMeasurement": "",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0025",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0520": {
            "id": 5427739,
            "key": "Hohlboden",
            "dataType": None,
            "valueType": "String",
            "unitOfMeasurement": "Ja/Nein",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0520",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0100": {
            "id": 5427740,
            "key": "Wandart",
            "dataType": None,
            "valueType": "String",
            "unitOfMeasurement": "",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0100",
            "mandatory": False,
            "relationFinderActive": True,
            "relatedGtoId": 4365351,
            "relatedGtoAttributeKey": "Bezeichnung",
            "reportFields": {},
            "spellingValues": [],
        },
        "0540": {
            "id": 5427741,
            "key": "GUID",
            "dataType": None,
            "valueType": "String",
            "unitOfMeasurement": "999",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0540",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0505": {
            "id": 5427742,
            "key": "Ableitwiderstand",
            "dataType": None,
            "valueType": "String",
            "unitOfMeasurement": "Ja/Nein",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0505",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0525": {
            "id": 5427743,
            "key": "Türen",
            "dataType": None,
            "valueType": "String",
            "unitOfMeasurement": "Türen",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0525",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0020": {
            "id": 5427744,
            "key": "Raum-ID",
            "dataType": None,
            "valueType": "String",
            "unitOfMeasurement": "",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0020",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0065": {
            "id": 5427745,
            "key": "Lavabos",
            "dataType": None,
            "valueType": "Int",
            "unitOfMeasurement": "",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0065",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0040": {
            "id": 5427746,
            "key": "Raumbeschriftung",
            "dataType": None,
            "valueType": "String",
            "unitOfMeasurement": "",
            "leadOfData": "TARGET",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0040",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0085": {
            "id": 5427747,
            "key": "Badewannen",
            "dataType": None,
            "valueType": "Int",
            "unitOfMeasurement": "",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0085",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0140": {
            "id": 5427748,
            "key": "Max. Belegung",
            "dataType": None,
            "valueType": "Int",
            "unitOfMeasurement": "",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0140",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0060": {
            "id": 5427749,
            "key": "Elektro Raumkategorie",
            "dataType": None,
            "valueType": "String",
            "unitOfMeasurement": "",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0060",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0080": {
            "id": 5427750,
            "key": "Duschen",
            "dataType": None,
            "valueType": "Int",
            "unitOfMeasurement": "",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0080",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0535": {
            "id": 5427751,
            "key": "Verortung",
            "dataType": None,
            "valueType": "String",
            "unitOfMeasurement": "",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0535",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0015": {
            "id": 5427752,
            "key": "Geschoss",
            "dataType": None,
            "valueType": "String",
            "unitOfMeasurement": "",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0015",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0510": {
            "id": 5427753,
            "key": "Ableitwiderstand Wert",
            "dataType": None,
            "valueType": "Int",
            "unitOfMeasurement": "Ohm",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0510",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0035": {
            "id": 5427754,
            "key": "Raumtyp IG",
            "dataType": None,
            "valueType": "String",
            "unitOfMeasurement": "",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0035",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0530": {
            "id": 5427755,
            "key": "DIN 277 IG",
            "dataType": None,
            "valueType": "String",
            "unitOfMeasurement": "",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0530",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0135": {
            "id": 5427756,
            "key": "Innenglasfläche",
            "dataType": None,
            "valueType": "Int",
            "unitOfMeasurement": "Meter2",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0135",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0055": {
            "id": 5427757,
            "key": "Raumfläche",
            "dataType": None,
            "valueType": "Decimal",
            "unitOfMeasurement": "Meter2",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0055",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0110": {
            "id": 5427758,
            "key": "Geschosshöhe",
            "dataType": None,
            "valueType": "Decimal",
            "unitOfMeasurement": "Meter",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0110",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0155": {
            "id": 5427759,
            "key": "Sprinkler",
            "dataType": None,
            "valueType": "Int",
            "unitOfMeasurement": "",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0155",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
        "0515": {
            "id": 5427760,
            "key": "Rutschwiderstand",
            "dataType": None,
            "valueType": "String",
            "unitOfMeasurement": "Ja/Nein",
            "leadOfData": "SOURCE",
            "reportRelevant": False,
            "gtoAttributeDefinitionsKey": "0515",
            "mandatory": False,
            "relationFinderActive": False,
            "relatedGtoId": 0,
            "relatedGtoAttributeKey": None,
            "reportFields": {},
            "spellingValues": [],
        },
    },
}


class Pipe:
    class Valves(BaseModel):
        OPENAI_API_BASE_URL: str = Field(
            default="https://bbvaihub-app-sui-api.azurewebsites.net/api/v1/openai",
            description="Base URL for accessing OpenAI API endpoints.",
        )
        OPENAI_API_KEY: str = Field(
            default="",
            description="API key for authenticating requests to the OpenAI API.",
        )
        LCDM_HUB_BASE_URL: str = Field(
            default="http://localhost:9991/restapi/1.0/gto/",
            description="URL for accessing LCDM Hub API endpoints.",
        )
        LCDM_HUB_TOKEN: str = Field(
            default="",
            description="Token to authenticate requests to the LCDM Hub API.",
        )

    def __init__(self):
        self.valves = self.Valves()
        self.current_gto = None

    def pipe(self, body: dict, __user__: dict, __metadata__: dict):
        messages = body.get("messages", [])
        user_message = messages[-1]["content"]

        if "<get_gto>" == user_message:
            gto_names = self.get_gto_names()
            return gto_names

        elif "<use_gto>" and "</use_gto>" in user_message:
            gto_key = user_message[9:-10]
            definition = self.get_gto_definition(gto_key)
            self.current_gto = definition

            body["messages"][-1]["content"] = GTO_PROMPT.replace(
                "{gto}", str(self.current_gto)
            )

        return self.query_model(body)

    def get_gto_names(self):
        table = dict_to_md_table(TEST_DEFINITIONS)
        return table
        headers = {
            "Authorization": f"Bearer {self.valves.LCDM_HUB_TOKEN}",
            "Content-Type": "application/json",
        }
        try:
            r = requests.get(
                f"{self.valves.LCDM_HUB_BASE_URL}/availablenames", json=headers
            )
            return r.json()

        except requests.exceptions.RequestException as e:
            print(f"Retrieving GTOs failed: {e}")

    def get_gto_definition(self, gto_key: str):
        return TEST_GTO
        headers = {
            "Authorization": f"Bearer {self.valves.LCDM_HUB_TOKEN}",
            "Content-Type": "application/json",
        }
        try:
            r = requests.get(f"{self.valves.LCDM_HUB_BASE_URL}/{gto_key}", json=headers)
            return r.json()

        except requests.exceptions.RequestException as e:
            print(f"Retrieving GTO definition failed: {e}")

    def query_model(self, body: dict):
        headers = {
            "Authorization": f"Bearer {self.valves.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            **body,
            "model": "gpt-4o",
        }
        try:
            r = requests.post(
                url=f"{self.valves.OPENAI_API_BASE_URL}/chat/completions",
                json=payload,
                headers=headers,
                stream=True,
            )
            r.raise_for_status()

            if body.get("stream", False):
                return r.iter_lines()
            else:
                return r.json()

        except Exception as e:
            return f"Error: {e}"


def dict_to_md_table(data):
    """Convert dictionary to markdown table (key-value format)"""
    md = "| ID | Name |\n|-----|-------|\n"
    for key, value in data.items():
        md += f"| {key} | {value} |\n"
    return md
