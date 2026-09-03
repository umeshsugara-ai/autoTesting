' Hidden launcher for monitor_task.cmd (Task Scheduler action target).
' WHY: an InteractiveToken task running a raw .cmd pops a visible blank console
' every fire. 0 = hidden window, True = wait so Task Scheduler sees the pass lifetime.
CreateObject("Wscript.Shell").Run """D:\autoTesting\.goal\monitor_task.cmd""", 0, True
