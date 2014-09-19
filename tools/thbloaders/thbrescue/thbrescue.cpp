// thbrescue.cpp : Defines the entry point for the console application.
//

#include "stdafx.h"

int transfer_progress(const git_transfer_progress *stats, void *data)
{
	static DWORD tick = 0;
	DWORD now;
	now = GetTickCount();
	if(now - tick < 500)
		return 0;

	tick = now;
	if(!stats->total_objects)
		return 0;

	_tprintf(
		_T("更新进度：%u%% (%u/%u), %.2f KiB\n"),
		100 * stats->received_objects / stats->total_objects,
		stats->received_objects,
		stats->total_objects,
		((float)(stats->received_bytes)) / 1024
	);
	return 0;
}

int fix(const char *path, const char *remote_name, const char *refname)
{
	int success = 0;
	git_repository *repo = NULL;
	git_object *desired = NULL;
	git_remote *remote = NULL;
	git_remote_callbacks callbacks = GIT_REMOTE_CALLBACKS_INIT;
	callbacks.transfer_progress = transfer_progress;

	do {
		if(git_repository_open(&repo, path)) break;
		if(git_remote_load(&remote, repo, remote_name)) break;
		git_remote_set_callbacks(remote, &callbacks);
		if(git_remote_connect(remote, GIT_DIRECTION_FETCH)) break;
		git_remote_fetch(remote);
		git_remote_disconnect(remote);
		git_remote_free(remote);
		if(git_revparse_single(&desired, repo, refname)) break;
		if(git_reset(repo, desired, GIT_RESET_HARD)) break;
		success = 1;
	} while(0);

	if(desired) git_object_free(desired);
	if(repo) git_repository_free(repo);
	return success;
}

int _tmain(int argc, _TCHAR* argv[])
{
#ifdef _UNICODE
	_setmode(_fileno(stdout), _O_WTEXT); 
#endif

	_tprintf(_T("THB紧急更新程序，用于尝试修复游戏里奇怪的问题\n"));
	git_threads_init();

	// interpreter
	_tprintf(_T("尝试重置解释器……\n"));
	if(!fix("Python27", "origin", "origin/master")) {
		_tprintf(_T("解释器重置失败！建议重新下载一份游戏……\n"));
	} else {
		_tprintf(_T("解释器重置完成。\n"));
	}

	// game
	_tprintf(_T("尝试重置游戏……\n"));
	if(!fix("src", "origin", "origin/production")) {
		_tprintf(_T("游戏重置失败！建议重新下载一份游戏……\n"));
	} else {
		_tprintf(_T("游戏重置完成。\n"));
	}
	system("pause");
	return 0;
}

