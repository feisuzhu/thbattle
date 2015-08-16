@import Foundation;
@import Python;

int main(int argc, char *argv[]) {
  Py_Initialize();
  PySys_SetArgv(argc, argv);

  NSBundle *bundle = [NSBundle mainBundle];
  NSString *path = [bundle pathForResource:@"bootstrap" ofType:@"py"];

  const char* cpath = [path UTF8String];
  FILE *f = fopen(cpath, "r");

  if (f)
    PyRun_AnyFileEx(f, cpath, 1);

  Py_Finalize();
}
