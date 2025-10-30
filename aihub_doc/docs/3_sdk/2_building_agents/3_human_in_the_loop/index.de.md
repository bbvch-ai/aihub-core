---
title: Human in the Loop
source_sha: 9bfd17ed1ca7b40338e30fafae52bca01ef79aa65dd6047f24dddbb8b5d51609
---

# Human in the Loop

Das **Human in the Loop (HITL)**-Muster ermöglicht es einem Agenten, seine Ausführung an einem kritischen Punkt zu
pausieren und Eingaben, Genehmigungen oder Anweisungen von einem menschlichen Benutzer anzufordern, bevor er fortfährt.

## Funktionsweise

Das HITL-Muster wird durch ein Paar von Ereignissen orchestriert, die die Logik zum Pausieren und Fortsetzen verwalten:

1. **Anfrage (Request)**: Ein Schritt in Ihrem Agenten gibt ein `HumanInTheLoop.request`-Ereignis zurück. Dies ist ein
   spezielles `ControlEvent`, das auch als `DisplayEvent` fungiert, den Workflow pausiert und dem Benutzer in der
   Benutzeroberfläche eine Frage präsentiert.
2. **Antwort (Response)**: Die Antwort des Benutzers wird als `HumanInTheLoop.response`-Ereignis an das System
   zurückgesendet.
3. **Fortsetzen (Resume)**: Ein weiterer Schritt in Ihrem Agenten ist so konfiguriert, dass er dieses Antwortereignis
   akzeptiert. Wenn das Ereignis eintrifft, leitet der Dispatcher es an den richtigen Schritt weiter, und der Workflow
   setzt seine Ausführung fort.

Die Helferklasse `HumanInTheLoop` vereinfacht diesen Prozess, indem sie eine bequeme `invoke`-Methode bereitstellt, um
das Anforderungsereignis mit den korrekten Routing-Informationen zu erstellen.

## Kernmuster: Einzelne Genehmigung

Dieses Beispiel zeigt einen einfachen Workflow, bei dem der Agent eine einzelne Bestätigung anfordert, bevor er
fortfährt.

**Referenz**: `playground/minimal_workflow/human_in_the_loop_workflow/`

```python
from aihub_lib.nats.events.human_in_the_loop.HumanInTheLoop import HumanInTheLoop

class ApprovalAgent(Agent):
    @step()
    async def request_approval(self, event: StartEvent) -> HumanInTheLoop.request:
        # 1. Pause the workflow and ask a question.
        return HumanInTheLoop.invoke(question="Should I proceed with this action?")

    @step()
    async def handle_response(self, event: HumanInTheLoop.response) -> StopEvent:
        # 2. Resume the workflow based on the human's response.
        if event.response.lower() == "yes":
            return StopEvent(final_message="Action approved and executed.")
        return StopEvent(final_message="Action cancelled by user.")
```

## Erweitertes Muster: Mehrstufige Genehmigung

Sie können mehrere HITL-Schritte miteinander verketten, um komplexere, mehrstufige Genehmigungs- oder
Datenerfassungs-Workflows zu erstellen.

**Referenz**: `playground/minimal_workflow/multistep_human_in_the_loop_workflow/`

```python
class MultistepApprovalAgent(Agent):
    @step()
    async def request_initial_approval(self, event: StartEvent) -> FirstStepHumanInTheLoop.request:
        # First checkpoint
        return FirstStepHumanInTheLoop.invoke(question="Shall I continue?")

    @step()
    async def request_final_confirmation(self, event: FirstStepHumanInTheLoop.response) -> SecondStepHumanInTheLoop.request:
        # Second checkpoint, only reached after the first is approved
        if event.response.lower() == "yes":
            return SecondStepHumanInTheLoop.invoke(question="Are you absolutely sure?")
        return StopEvent(final_message="Process cancelled at first step.")

    @step()
    async def execute_action(self, event: SecondStepHumanInTheLoop.response) -> StopEvent:
        # Final step, only reached after the second confirmation
        if event.response.lower() == "yes":
            return StopEvent(final_message="Action confirmed and executed.")
        return StopEvent(final_message="Process cancelled at final confirmation.")
```
