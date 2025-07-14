from playground.minimal_processes.human_only_process.events.HumanAWork import HumanAWork

work = HumanAWork(input_text_a="test")
print(work.to_form_submission_model().model_json_schema())
