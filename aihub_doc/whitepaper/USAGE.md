# Swiss AI-Hub Whitepaper Generator - Verwendung

## Schnellstart

### 1. Kapitel generieren

```bash
cd aihub_doc/whitepaper

# Alle verfügbaren Kapitel generieren
./generate-whitepaper.sh

# Nur spezifische Kapitel
./generate-whitepaper.sh 00 01 02
```

### 2. Kapitel kombinieren

```bash
# Alle generierten Kapitel zu einem Dokument kombinieren
./combine-whitepaper.sh

# Ergebnis:
# - swiss_ai_hub_whitepaper.md  (Markdown)
# - swiss_ai_hub_whitepaper.docx (Word, falls pypandoc installiert)
```

## Scripts

### generate-whitepaper.sh

Generiert Whitepaper-Kapitel aus Prompts und technischer Dokumentation.

**Verwendung:**
```bash
./generate-whitepaper.sh [chapter_id...]

# Beispiele:
./generate-whitepaper.sh           # Alle Kapitel
./generate-whitepaper.sh 00 03 05  # Kapitel 00, 03, 05
./generate-whitepaper.sh --list    # Verfügbare Kapitel anzeigen
```

**Umgebungsvariablen:**
```bash
LLM_MODEL=gpt-4 ./generate-whitepaper.sh     # Anderes Modell verwenden
```

**Ausgabe:**
- Erstellt `output/XX_output.md` für jedes Kapitel
- Zeigt Fortschritt und Statistiken
- Automatische Wiederholungen bei Fehlern (max. 3x)

### combine-whitepaper.sh / combine_whitepaper.py

Kombiniert alle generierten Kapitel zu einem vollständigen Whitepaper.

**Verwendung (Bash):**
```bash
./combine-whitepaper.sh [output_dir] [output_name] [include_toc]

# Beispiele:
./combine-whitepaper.sh                      # Standard (mit TOC)
./combine-whitepaper.sh ./output mein_wp     # Custom Name
./combine-whitepaper.sh ./output wp false    # Ohne TOC
```

**Verwendung (Python direkt):**
```bash
python3 combine_whitepaper.py ./output swiss_ai_hub_whitepaper true
```

**Ausgabe:**
- `<output_name>.md` - Kombiniertes Markdown
- `<output_name>.docx` - Word-Dokument (falls pypandoc verfügbar)
- Inhaltsverzeichnis (optional)
- Seitenumbrüche zwischen Kapiteln

**Features:**
- Automatische Sortierung nach Kapitelnummer
- Extraktion von Kapiteltiteln für TOC
- Seitenumbrüche für DOCX-Export (`\newpage`)
- Wortanzahl und Seitenschätzung

## Verzeichnisse

```
whitepaper/
├── generate-whitepaper.sh       # Kapitel-Generator
├── combine-whitepaper.sh        # Kombinations-Wrapper
├── combine_whitepaper.py        # Kombinations-Script
├── general_prompt.md            # Allgemeine Schreibanweisungen
├── prompts/                     # Kapitel-spezifische Prompts
│   └── XX_prompt.md
├── sources/                     # Quelldokument-Listen
│   └── XX_sources.txt
└── output/                      # Generierte Kapitel
    └── XX_output.md
```

## Voraussetzungen

### Für Generierung

```bash
# llm CLI installieren
pipx install llm

# LLM-API konfigurieren (z.B. Gemini)
llm keys set gemini
```

### Für DOCX-Export (optional)

```bash
# Python-Paket
pip install pypandoc

# Pandoc
sudo apt install pandoc  # Linux/WSL
brew install pandoc      # macOS
```

## Workflow

1. **Prompts erstellen/anpassen**
   - `prompts/XX_prompt.md` für Kapitelstruktur
   - `sources/XX_sources.txt` für Quelldokumente

2. **Kapitel generieren**
   ```bash
   ./generate-whitepaper.sh
   ```

3. **Qualität prüfen**
   - Review `output/XX_output.md`
   - Bei Bedarf Prompt anpassen und neu generieren

4. **Whitepaper kombinieren**
   ```bash
   ./combine-whitepaper.sh
   ```

5. **Finales Dokument**
   - `swiss_ai_hub_whitepaper.md` (Markdown)
   - `swiss_ai_hub_whitepaper.docx` (Word)

## Tipps

### LLM-Modell wählen

```bash
# Schnell & kostengünstig (Standard)
LLM_MODEL=gemini-2.5-flash ./generate-whitepaper.sh

# Höhere Qualität
LLM_MODEL=gpt-4o ./generate-whitepaper.sh
LLM_MODEL=claude-3-5-sonnet-20241022 ./generate-whitepaper.sh
```

### Einzelnes Kapitel neu generieren

```bash
# Nur Kapitel 05 neu generieren
./generate-whitepaper.sh 05

# Dann neu kombinieren
./combine-whitepaper.sh
```

### Whitepaper ohne TOC

```bash
./combine-whitepaper.sh ./output swiss_ai_hub_whitepaper false
```

### Custom Output-Pfad

```bash
# Generiere in anderes Verzeichnis
./generate-whitepaper.sh
mv output/* /custom/path/

# Kombiniere von custom path
./combine-whitepaper.sh /custom/path my_whitepaper
```

## Fehlerbehandlung

### "No chapters found"

```bash
# Prüfe ob Prompts vorhanden
ls prompts/

# Sollte XX_prompt.md Dateien zeigen
```

### "llm command not found"

```bash
pipx install llm
```

### DOCX-Export schlägt fehl

```bash
# Installiere Dependencies
pip install pypandoc
sudo apt install pandoc  # oder brew install pandoc
```

### Kapitel zu lang/kurz

Passe `general_prompt.md` oder `prompts/XX_prompt.md` an:
- Zielwortanzahl anpassen
- Mehr/weniger Quelldokumente in `sources/XX_sources.txt`

## Beispiel-Output

### Konsolen-Ausgabe (Generierung)

```
╔══════════════════════════════════════════════════╗
║       Swiss AI-Hub Whitepaper Generator         ║
╚══════════════════════════════════════════════════╝

Total chapters to generate: 11
Model: gemini-2.5-flash

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Processing chapter 00 (1/11)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

═══════════════════════════════════════════════════
Generating Chapter: 00
═══════════════════════════════════════════════════
📝 Using prompt: prompts/00_prompt.md
🤖 Using model: gemini-2.5-flash
📚 Collecting source documentation...
  📄 1_vision_and_positioning/1_introduction/index.de.md
  ✓ Collected 6 source document(s)
🔨 Building combined prompt...
  📊 Combined prompt size: 57KiB
🔄 Attempt 1/3: Calling LLM...
✓ Chapter generated successfully
  📄 Output: output/00_output.md
  📊 Word count: 1068

✓ Chapter 00 completed successfully
Progress: ✓ 1 successful, ✗ 0 failed
```

### Konsolen-Ausgabe (Kombination)

```
╔══════════════════════════════════════════════════╗
║       Swiss AI-Hub Whitepaper Combiner          ║
╚══════════════════════════════════════════════════╝

Processing chapters from: /path/to/output

Creating table of contents...

Found 11 chapter file(s):

  ✓ Chapter 00: Executive Summary
  ✓ Chapter 01: Business Challenge
  ✓ Chapter 02: Platform Overview
  ...

✓ Created swiss_ai_hub_whitepaper.md
✓ Created swiss_ai_hub_whitepaper.docx

══════════════════════════════════════════════════
Statistics:
  Total word count: 25,430
  Estimated pages: 63.6
══════════════════════════════════════════════════

✓ Done!
```

## Weitere Informationen

- **Projekt-Repository**: https://github.com/bbvch-ai/aihub-core
- **LLM CLI**: https://github.com/simonw/llm
- **Pandoc**: https://pandoc.org/
