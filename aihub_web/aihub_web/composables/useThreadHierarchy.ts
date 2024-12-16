import { computed } from 'vue'
import { useThread } from '@core/composables/useThread'
import type { WSServerEvent } from '@core/types/Events/WSEvent/WSServerEvent'

interface HierarchyRun {
  run_id: string
  earliest_event_timestamp: number
  latest_event_timestamp: number
  events: WSServerEvent[]
}

interface HierarchyDisplay {
  display_id: string
  earliest_event_timestamp: number
  latest_event_timestamp: number
  runs: HierarchyRun[]
}

type Hierarchy = HierarchyDisplay[]

export const useThreadHierarchy = (thread_id: string) => {
  const { events, ...thread_return_vals } = useThread(thread_id)

  // Construct hierarchy
  const hierarchy = computed<Hierarchy>(() => {
    const displayMap = new Map<string, HierarchyDisplay>()

    for (const event of events.value) {
      const { display_id, run_id, event_data } = event
      const event_timestamp = event_data.created_at

      // Get or create display
      let display = displayMap.get(display_id)
      if (!display) {
        display = {
          display_id,
          earliest_event_timestamp: event_timestamp,
          latest_event_timestamp: event_timestamp,
          runs: [],
        }
        displayMap.set(display_id, display)
      }
      else {
        // Update earliest and latest timestamps
        display.earliest_event_timestamp = Math.min(
          display.earliest_event_timestamp,
          event_timestamp,
        )
        display.latest_event_timestamp = Math.max(
          display.latest_event_timestamp,
          event_timestamp,
        )
      }

      // Get or create run within display
      let run = display.runs.find(r => r.run_id === run_id)
      if (!run) {
        run = {
          run_id,
          earliest_event_timestamp: event_timestamp,
          latest_event_timestamp: event_timestamp,
          events: [],
        }
        display.runs.push(run)
      }
      else {
        // Update earliest and latest timestamps
        run.earliest_event_timestamp = Math.min(
          run.earliest_event_timestamp,
          event_timestamp,
        )
        run.latest_event_timestamp = Math.max(
          run.latest_event_timestamp,
          event_timestamp,
        )
      }

      // Add event to run
      run.events.push(event)
    }

    // Sort events within runs, runs within displays, and displays themselves
    for (const display of displayMap.values()) {
      for (const run of display.runs) {
        run.events.sort(
          (a, b) => a.event_data.created_at - b.event_data.created_at,
        )
      }
      display.runs.sort(
        (a, b) => a.latest_event_timestamp - b.latest_event_timestamp,
      )
    }

    const displays = Array.from(displayMap.values())
    displays.sort(
      (a, b) => a.latest_event_timestamp - b.latest_event_timestamp,
    )

    return displays
  })

  return {
    ...thread_return_vals,
    hierarchy,
  }
}
