' ==============================================================================
' 脚本名称: 启动工具(无黑框静默).vbs
' 描述: 双击本文件可在后台完全静默启动主程序，绝不弹出任何黑色 cmd 对话框
' ==============================================================================
Set ws = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)

' 启动 main.pyw，第二个参数 0 表示以隐藏窗口运行
ws.Run "pythonw.exe """ & currentDir & "\main.pyw""", 0, False
