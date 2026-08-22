import unittest

from winsnap.collectors import taskscheduler
from winsnap.collectors.scheduled_tasks import (
    _TASK_STATE_NAMES,
    _collapse,
    _split_task_path,
    _trigger_class,
)


class ScheduledTaskHelperTests(unittest.TestCase):
    def test_collapse_empty(self):
        self.assertIsNone(_collapse([]))

    def test_collapse_single(self):
        self.assertEqual(_collapse(["MSFT_TaskBootTrigger"]), "MSFT_TaskBootTrigger")

    def test_collapse_multiple(self):
        self.assertEqual(
            _collapse(["MSFT_TaskLogonTrigger", "MSFT_TaskTimeTrigger"]),
            {"value": ["MSFT_TaskLogonTrigger", "MSFT_TaskTimeTrigger"], "Count": 2},
        )

    def test_trigger_class_well_known(self):
        self.assertEqual(_trigger_class("BootTrigger", ""), "MSFT_TaskBootTrigger")
        self.assertEqual(_trigger_class("WnfStateChangeTrigger", ""), "MSFT_TaskTrigger")

    def test_trigger_class_calendar_daily(self):
        self.assertEqual(_trigger_class("CalendarTrigger", "<ScheduleByDay>"), "MSFT_TaskDailyTrigger")

    def test_trigger_class_calendar_weekly(self):
        self.assertEqual(_trigger_class("CalendarTrigger", "<ScheduleByWeek>"), "MSFT_TaskWeeklyTrigger")

    def test_trigger_class_calendar_monthly(self):
        self.assertEqual(_trigger_class("CalendarTrigger", "<ScheduleByMonth>"), "MSFT_TaskTrigger")

    def test_split_task_path_root(self):
        self.assertEqual(_split_task_path("\\TaskName"), ("\\", "TaskName"))

    def test_split_task_path_subfolder(self):
        self.assertEqual(_split_task_path("\\Folder\\Sub\\TaskName"), ("\\Folder\\Sub\\", "TaskName"))

    def test_task_state_names(self):
        self.assertEqual(_TASK_STATE_NAMES[0], "Unknown")
        self.assertEqual(_TASK_STATE_NAMES[1], "Disabled")
        self.assertEqual(_TASK_STATE_NAMES[2], "Queued")
        self.assertEqual(_TASK_STATE_NAMES[3], "Ready")
        self.assertEqual(_TASK_STATE_NAMES[4], "Running")


class TaskSchedulerComTests(unittest.TestCase):
    def test_enumerate_tasks_returns_tuples(self):
        tasks = taskscheduler.enumerate_tasks()
        self.assertIsInstance(tasks, list)
        for entry in tasks:
            self.assertIsInstance(entry, tuple)
            self.assertEqual(len(entry), 3)


if __name__ == "__main__":
    unittest.main()
