rc resource.rc
cl /D_UNICODE /DUNICODE /MT loader.c kernel32.lib user32.lib shell32.lib resource.res /link /subsystem:windows