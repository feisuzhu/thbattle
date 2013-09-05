#include <stdlib.h>
#include <tchar.h>
#include <windows.h>

LPCTSTR ERROR_PROMPT =
    _T("游戏崩溃了！\n")
    _T("\n")
    _T("错误报告应该已经自动发送了，请耐心等等吧……\n")
    _T("如果游戏不停的崩溃，请确认是不是显卡驱动程序的问题，试着更新一下显卡驱动程序。\n")
    _T("nVIDIA卡：http://www.nvidia.cn/Download/index.aspx?lang=cn\n")
    _T("AMD卡：http://support.amd.com/us/gpudownload/Pages/index.aspx\n")
    _T("\n")
    _T("如果以前能正常游戏但是突然玩不了了，请执行一下游戏目录中的update.bat，\n")
    _T("然后再打开游戏。\n")
    _T("\n")
    _T("仍然不行的话，请去http://www.thbattle.net发帖抱怨！！")
;

int execute(LPCTSTR app, LPCTSTR cargs)
{
    PROCESS_INFORMATION pinfo;
    STARTUPINFO sinfo = { sizeof(sinfo) };
    BOOL rst;
    DWORD exitcode = 1;

    LPTSTR args = _tcsdup(cargs);
    rst = CreateProcess(app, args, NULL, NULL, FALSE, 0, NULL, NULL, &sinfo, &pinfo);
    free(args);

    if(!rst) {
        return 1;
    }
    CloseHandle(pinfo.hThread);
    WaitForSingleObject(pinfo.hProcess, INFINITE);
    GetExitCodeProcess(pinfo.hProcess, &exitcode);
    CloseHandle(pinfo.hProcess);
    return exitcode;
}


int __stdcall _tWinMain(HINSTANCE hInstance,
                     HINSTANCE hPrevInstance,
                     LPTSTR    lpCmdLine,
                     int       nCmdShow)
{
    int rst;
    rst = execute(_T("Python27\\pythonw.exe"), _T("pythonw.exe"));
    if(rst) {
        // failed, install vcredist
        execute(_T("Python27\\vcredist_x86.exe"), _T("vcredist_x86.exe"));
    }
    rst = execute(_T("Python27\\pythonw.exe"), _T("Python27\\pythonw.exe src\\start_client.py"));
    if(rst) {
        ShellExecute(0, _T("open"), _T("update.bat"), NULL, NULL, 0);
        MessageBox(NULL, ERROR_PROMPT, _T("游戏崩溃了"), MB_ICONINFORMATION);
    }
    return 0;
}
