rc resource.rc
cl /D_UNICODE /DUNICODE /MT /O2 loader.c kernel32.lib user32.lib shell32.lib resource.res /link /subsystem:windows
