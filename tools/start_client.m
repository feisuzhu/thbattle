@import Foundation;
@import Python;

int main(int argc, char *argv[]) {
  if (argc <= 0)
    abort();

  Py_SetProgramName(argv[0]);
  Py_Initialize();
  PySys_SetArgv(argc - 1, argv + 1);

  NSBundle *bundle = [NSBundle mainBundle];
  NSString *path = [bundle pathForResource:@"bootstrap" ofType:@"py"];

  const char* cpath = [path UTF8String];
  FILE *f = fopen(cpath, "r");

  if (f)
    PyRun_AnyFileEx(f, cpath, 1);

  Py_Finalize();
}
