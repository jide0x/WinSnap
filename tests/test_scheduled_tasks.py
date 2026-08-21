import unittest

from winsnap.collectors.scheduled_tasks import (
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


if __name__ == "__main__":
    unittest.main()
