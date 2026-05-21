from .reminders import run_system_reminders


def run_task_reminders(lead_minutes=60, tolerance_minutes=5):
    """Compat wrapper: retorna apenas bloco de tarefas."""
    result = run_system_reminders(
        task_lead_minutes=lead_minutes,
        event_lead_minutes=1440,
        job_lead_minutes=1440,
        time_tolerance_minutes=tolerance_minutes,
        slot_tolerance_minutes=tolerance_minutes,
    )
    task_result = result["tasks"]
    task_result.update(
        {
            "lead_minutes": lead_minutes,
            "tolerance_minutes": tolerance_minutes,
        }
    )
    return task_result
