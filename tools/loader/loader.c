#include <stdio.h>
#include <stdlib.h>
#include <windows.h>

const char *ERROR_PROMPT = (
    "游戏崩溃了！\n"
    "\n"
    "错误报告应该已经自动发送了，请耐心等等吧……\n"
    "如果游戏不停的崩溃，请确认是不是显卡驱动程序的问题，试着更新一下显卡驱动程序。\n"
    "nVIDIA卡：http://www.nvidia.cn/Download/index.aspx?lang=cn\n"
    "AMD卡：http://support.amd.com/us/gpudownload/Pages/index.aspx\n"
    "\n"
    "如果以前能正常游戏但是突然玩不了了，请执行一下游戏目录中的update.bat，\n"
    "然后再打开游戏。\n"
    "\n"
    "仍然不行的话，请去http://www.thbattle.net发帖抱怨！！"
);


int execute(const char *app, const char* args)
{
    PROCESS_INFORMATION pinfo;
    STARTUPINFO sinfo;
    BOOL rst;
    DWORD exitcode = 1;
    
    ZeroMemory(&sinfo, sizeof(sinfo));
    sinfo.cb = sizeof(sinfo);
    
    rst = CreateProcess(app, args, NULL, NULL, FALSE, 0, NULL, NULL, &sinfo, &pinfo);
    if(!rst) {
        return 1;
    }
    WaitForSingleObject(pinfo.hProcess, INFINITE);
    GetExitCodeProcess(pinfo.hProcess, &exitcode);
    
    return exitcode;
}


int __stdcall WinMain(HINSTANCE hInstance,
                     HINSTANCE hPrevInstance,
                     LPTSTR    lpCmdLine,
                     int       nCmdShow)
{
    int rst;
    rst = execute("Python27\\pythonw.exe", "pythonw.exe");
    if(rst) {
        // failed, install vcredist
        execute("Python27\\vcredist_x86.exe", "vcredist_x86.exe");
    }
    rst = execute("Python27\\pythonw.exe", "pythonw.exe src\\start_client.py");
    if(rst) {
        ShellExecute(0, "open", "update.bat", NULL, NULL, 0);
        MessageBox(NULL, ERROR_PROMPT, "游戏崩溃了", MB_ICONINFORMATION);
    }
    return 0;
}