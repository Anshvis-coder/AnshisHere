"""
Automation Controller for Freddie
==================================
Handles complex automation workflows and scheduled tasks.
"""

import logging
from typing import Optional, Callable, Dict, Any
import threading
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class AutomationController:
    """Controls automation workflows and scheduled tasks."""

    def __init__(self):
        self._scheduled_tasks: Dict[str, dict] = {}
        self._running = False
        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_flag = False

    def start_scheduler(self) -> None:
        """Start the background task scheduler."""
        if self._running:
            logger.warning("Scheduler already running")
            return

        self._running = True
        self._stop_flag = False
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        logger.info("Task scheduler started")

    def stop_scheduler(self) -> None:
        """Stop the background task scheduler."""
        self._stop_flag = True
        self._running = False

        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=2.0)
            self._scheduler_thread = None

        logger.info("Task scheduler stopped")

    def _scheduler_loop(self) -> None:
        """Main scheduler loop that checks for due tasks."""
        while not self._stop_flag:
            try:
                self._check_due_tasks()
            except Exception as e:
                logger.error(f"Scheduler error: {e}")

            time.sleep(1)  # Check every second

    def _check_due_tasks(self) -> None:
        """Check and execute any due tasks."""
        now = datetime.now()

        for task_id, task in list(self._scheduled_tasks.items()):
            if task.get("active", True):
                due_time = task.get("due_time")
                if due_time and due_time <= now:
                    # Execute the task
                    self._execute_task(task_id, task)

                    # Remove one-time tasks
                    if not task.get("recurring", False):
                        del self._scheduled_tasks[task_id]

    def _execute_task(self, task_id: str, task: dict) -> None:
        """Execute a scheduled task."""
        try:
            callback = task.get("callback")
            args = task.get("args", ())
            kwargs = task.get("kwargs", {})

            if callback:
                logger.info(f"Executing scheduled task: {task_id}")
                callback(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {e}")

    def schedule_reminder(self, task_id: str, content: str, due_time: datetime,
                          callback: Callable = None, recurring: bool = False) -> bool:
        """
        Schedule a reminder.

        Args:
            task_id: Unique identifier for the task
            content: Reminder content/message
            due_time: When the reminder should trigger
            callback: Optional callback function
            recurring: Whether the reminder should repeat

        Returns:
            True if scheduled successfully
        """
        try:
            self._scheduled_tasks[task_id] = {
                "content": content,
                "due_time": due_time,
                "callback": callback,
                "args": (content,),
                "recurring": recurring,
                "active": True,
                "created_at": datetime.now(),
            }

            logger.info(f"Scheduled reminder '{task_id}' for {due_time}")
            return True
        except Exception as e:
            logger.error(f"Failed to schedule reminder: {e}")
            return False

    def cancel_reminder(self, task_id: str) -> bool:
        """
        Cancel a scheduled reminder.

        Args:
            task_id: ID of the reminder to cancel

        Returns:
            True if cancelled successfully
        """
        if task_id in self._scheduled_tasks:
            del self._scheduled_tasks[task_id]
            logger.info(f"Cancelled reminder: {task_id}")
            return True
        return False

    def get_scheduled_tasks(self) -> list:
        """Get list of all scheduled tasks."""
        tasks = []
        for task_id, task in self._scheduled_tasks.items():
            tasks.append({
                "id": task_id,
                "content": task.get("content"),
                "due_time": task.get("due_time"),
                "recurring": task.get("recurring", False),
                "active": task.get("active", True),
            })
        return tasks

    def create_workflow(self, name: str, steps: list) -> bool:
        """
        Create an automation workflow.

        Args:
            name: Name of the workflow
            steps: List of step definitions

        Returns:
            True if created successfully
        """
        # Placeholder for workflow creation
        # In a full implementation, this would store and manage workflows
        logger.info(f"Created workflow: {name} with {len(steps)} steps")
        return True

    def run_workflow(self, name: str) -> bool:
        """
        Run a predefined workflow.

        Args:
            name: Name of the workflow to run

        Returns:
            True if executed successfully
        """
        # Placeholder for workflow execution
        logger.info(f"Running workflow: {name}")
        return True


# Singleton instance
_automation_controller: Optional[AutomationController] = None


def get_automation_controller() -> AutomationController:
    """Get the singleton AutomationController instance."""
    global _automation_controller
    if _automation_controller is None:
        _automation_controller = AutomationController()
    return _automation_controller
