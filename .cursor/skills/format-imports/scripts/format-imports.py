#!/usr/bin/env -S uv run --script
# -*- coding: utf-8 -*-
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "pyflakes",
# ]
# ///

# -- prioritized --
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# -- stdlib --
from collections import defaultdict
from pathlib import Path
import argparse
import ast
import importlib.util
import sys
import sysconfig
import warnings

# -- third party --
# -- local --
# -- errord --
from pyflakes.checker import Checker as PyflakesChecker
from pyflakes.messages import UnusedImport


# -- code --
MAX_LINE_WIDTH = 100

MARKER_PRIORITIZED = '# -- prioritized --'
MARKER_STDLIB = '# -- stdlib --'
MARKER_THIRD_PARTY = '# -- third party --'
MARKER_LOCAL = '# -- local --'
MARKER_TYPING = '# -- typing --'
MARKER_ERRORD = '# -- errord --'
MARKER_CODE = '# -- code --'

CATEGORY_FUTURE = 'future'
CATEGORY_STDLIB = 'stdlib'
CATEGORY_THIRD_PARTY = 'third_party'
CATEGORY_LOCAL = 'local'
CATEGORY_TYPING = 'typing'
CATEGORY_ERROR = 'error'

_STDLIB_NAMES = getattr(sys, 'stdlib_module_names', None)
_third_party_top_levels = set()
_pyproject_root = None

SECTION_ORDER = [
    (MARKER_STDLIB, CATEGORY_STDLIB),
    (MARKER_THIRD_PARTY, CATEGORY_THIRD_PARTY),
    (MARKER_LOCAL, CATEGORY_LOCAL),
]

SECTION_MARKERS = frozenset({
    MARKER_PRIORITIZED, MARKER_STDLIB, MARKER_THIRD_PARTY,
    MARKER_LOCAL, MARKER_TYPING, MARKER_ERRORD, MARKER_CODE,
})


# -- Helpers --

def _find_project_site_packages(start_dir=None):
    """Find site-packages from the project's virtualenv.

    Searches upward from start_dir (or cwd if not given) for .venv/venv
    directories.
    """
    venv_path = None
    directory = Path(start_dir).resolve() if start_dir else Path.cwd()
    while True:
        for candidate in ('.venv', 'venv'):
            path = directory / candidate
            if (path / 'lib').is_dir() or (path / 'Lib').is_dir():
                venv_path = path
                break
        if venv_path:
            break
        parent = directory.parent
        if parent == directory:
            break
        directory = parent

    if not venv_path:
        return []

    return [
        str(p) for p in (
            *venv_path.glob('lib/python*/site-packages'),
            *venv_path.glob('Lib/site-packages'),
        )
    ]


def format_alias(node):
    """Format an ast.alias node as 'name' or 'name as alias'."""
    if node.asname:
        return '%s as %s' % (node.name, node.asname)
    return node.name


def is_import_stmt(stmt):
    """Check if an AST statement is an import or a TYPE_CHECKING guard."""
    if isinstance(stmt, (ast.Import, ast.ImportFrom)):
        return True
    if isinstance(stmt, ast.If):
        return isinstance(stmt.test, ast.Name) and stmt.test.id == 'TYPE_CHECKING'
    return False


def stmt_start_line(stmt):
    """Get the true start line of a statement, accounting for decorators."""
    if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        if stmt.decorator_list:
            return min(d.lineno for d in stmt.decorator_list)
    return stmt.lineno


def _scan_third_party_top_levels(site_packages_dirs):
    """Build a set of top-level package names from site-packages directories.

    Uses only filesystem inspection, so it works regardless of which Python
    version created the virtualenv.
    """
    names = set()
    for sp_dir in site_packages_dirs:
        sp = Path(sp_dir)
        if not sp.is_dir():
            continue
        for dist_info in sp.glob('*.dist-info'):
            top_level = dist_info / 'top_level.txt'
            if top_level.is_file():
                for line in top_level.read_text().splitlines():
                    name = line.strip()
                    if name:
                        names.add(name)
        for entry in sp.iterdir():
            ename = entry.name
            if ename == '__pycache__':
                continue
            if entry.is_dir() and not ename.endswith(('.dist-info', '.egg-info')):
                names.add(ename)
            elif ename.endswith('.py'):
                names.add(entry.stem)
    return names


def _find_pyproject_root(start_dir=None):
    """Find the nearest directory containing pyproject.toml by walking upward."""
    directory = Path(start_dir).resolve() if start_dir else Path.cwd()
    while True:
        if (directory / 'pyproject.toml').is_file():
            return directory
        parent = directory.parent
        if parent == directory:
            return None
        directory = parent


def _is_stdlib(name):
    """Check if a module belongs to the standard library."""
    if _STDLIB_NAMES is not None:
        return name in _STDLIB_NAMES
    try:
        spec = importlib.util.find_spec(name)
    except (ModuleNotFoundError, ValueError):
        return False
    if spec is None:
        return False
    if spec.origin in ('built-in', 'frozen'):
        return True
    if spec.origin:
        try:
            Path(spec.origin).resolve().relative_to(
                Path(sysconfig.get_path('stdlib')).resolve()
            )
            return True
        except ValueError:
            pass
    return False


def classify_module(name):
    """Classify a module into a category based on its origin."""
    if name.endswith('TT'):
        return CATEGORY_TYPING

    top_level = name.split('.')[0].split(' as ')[0]

    if top_level == '__future__':
        return CATEGORY_FUTURE
    if not top_level:
        return CATEGORY_LOCAL

    if top_level in _third_party_top_levels:
        return CATEGORY_THIRD_PARTY
    if _is_stdlib(top_level):
        return CATEGORY_STDLIB

    local_roots = [Path.cwd()]
    if _pyproject_root is not None and _pyproject_root not in local_roots:
        local_roots.append(_pyproject_root)
    for root in local_roots:
        if (root / top_level).is_dir() or (root / (top_level + '.py')).is_file():
            return CATEGORY_LOCAL

    return CATEGORY_ERROR


# -- Parsing --

def extract_preamble(src):
    """Extract preamble (shebang, encoding, comments) before imports.

    Returns (preamble, remaining_src) where preamble contains all
    leading comment lines before the first import or section marker.
    """
    lines = src.split('\n')
    last_comment_idx = -1

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('#') and stripped not in SECTION_MARKERS:
            last_comment_idx = i
        else:
            break

    if last_comment_idx < 0:
        return '', src

    preamble = '\n'.join(lines[:last_comment_idx + 1])
    remaining = '\n'.join(lines[last_comment_idx + 1:])
    return preamble, remaining


def extract_prioritized(src):
    """Extract the prioritized section, returning (prioritized_text, remaining_src).

    If no prioritized markers are found, returns ('', original_src).
    """
    try:
        start = src.index(MARKER_PRIORITIZED + '\n') + len(MARKER_PRIORITIZED) + 1
        end = src.index(MARKER_STDLIB + '\n')
        return src[start:end].strip(), src[end:]
    except ValueError:
        return '', src


def split_imports_and_code(module, src):
    """Partition module body into import statements and verbatim code text."""
    import_stmts = []
    first_code_line = None

    for stmt in module.body:
        if first_code_line is None and is_import_stmt(stmt):
            import_stmts.append(stmt)
        elif first_code_line is None:
            first_code_line = stmt_start_line(stmt)

    code_text = ''
    if first_code_line is not None:
        src_lines = src.split('\n')
        code_text = '\n'.join(src_lines[first_code_line - 1:])

    return import_stmts, code_text


# -- Unused import detection --

def detect_unused_imports(source, filename='<stdin>'):
    """Detect unused imports in the given source using pyflakes."""
    try:
        tree = ast.parse(source, filename)
        result = PyflakesChecker(tree, filename)

        return [
            msg.message_args[0]
            for msg in result.messages
            if isinstance(msg, UnusedImport)
        ]
    except Exception:
        return []


# -- Import collection --

def _collect_from_import(stmt, unused, froms):
    """Process an ImportFrom statement into the froms dict."""
    module_path = '.' * stmt.level + (stmt.module or '')

    if (stmt.module or '').endswith('TT'):
        froms['typing'].append('TYPE_CHECKING')

    for a in stmt.names:
        if '%s.%s' % (module_path, a.name) in unused:
            continue
        froms[module_path].append(format_alias(a))


def _collect_type_checking_block(stmt, froms, plain):
    """Process a TYPE_CHECKING if-block into froms/plain."""
    froms['typing'].append('TYPE_CHECKING')
    for inner in stmt.body:
        if isinstance(inner, ast.Import):
            plain.extend(format_alias(a) + 'TT' for a in inner.names)
        elif isinstance(inner, ast.ImportFrom):
            module_path = '.' * inner.level + (inner.module or '')
            froms[module_path + 'TT'].extend(
                format_alias(a) for a in inner.names
            )


def collect_imports(import_stmts, unused):
    """Walk import AST nodes and collect them.

    Returns (plain_imports, from_imports) where:
      plain_imports: list of alias strings (e.g. 'os', 'sys as system')
      from_imports:  defaultdict(list) mapping module -> [alias_strings]
    """
    froms = defaultdict(list)
    plain = []

    for stmt in import_stmts:
        if isinstance(stmt, ast.Import):
            plain.extend(
                format_alias(a) for a in stmt.names
                if a.name not in unused
            )
        elif isinstance(stmt, ast.ImportFrom):
            _collect_from_import(stmt, unused, froms)
        elif isinstance(stmt, ast.If):
            _collect_type_checking_block(stmt, froms, plain)

    return plain, froms


# -- Formatting --

def wrap_from_import(module_name, aliases):
    """Format 'from X import a, b, c' lines, wrapping at MAX_LINE_WIDTH."""
    header = 'from %s import ' % module_name
    lines = []
    current = []

    for alias in aliases:
        candidate = ', '.join(current + [alias])
        if current and len(header) + len(candidate) > MAX_LINE_WIDTH:
            lines.append(header + ', '.join(current))
            current = [alias]
        else:
            current.append(alias)

    if current:
        lines.append(header + ', '.join(current))

    return lines


def categorize_imports(plain_imports, from_imports):
    """Classify all imports into category buckets of formatted lines."""
    categories = defaultdict(list)

    sorted_froms = sorted(from_imports.items())
    for _, aliases in sorted_froms:
        aliases[:] = sorted(set(aliases))

    for module_name, aliases in sorted_froms:
        category = classify_module(module_name)
        categories[category].extend(wrap_from_import(module_name, aliases))

    for name in sorted(set(plain_imports)):
        category = classify_module(name)
        categories[category].append('import ' + name)

    return categories


# -- Output --

def format_output(categories, prioritized, code_text, preamble):
    """Assemble the final formatted output string."""
    lines = []

    if preamble:
        lines.append(preamble)

    future = categories.get(CATEGORY_FUTURE, [])
    if future:
        lines.extend(future)

    if lines:
        lines.append('')

    if prioritized:
        lines.append(MARKER_PRIORITIZED)
        lines.append(prioritized)
        lines.append('')

    for marker, category in SECTION_ORDER:
        lines.append(marker)
        items = categories.get(category, [])
        if items:
            lines.extend(items)
            lines.append('')

    typing_imports = categories.get(CATEGORY_TYPING, [])
    if typing_imports:
        lines.append(MARKER_TYPING)
        lines.append('if TYPE_CHECKING:')
        for imp in typing_imports:
            lines.append('    %s  # noqa: F401' % imp.replace('TT', ''))
        lines.append('')

    errors = categories.get(CATEGORY_ERROR, [])
    if errors:
        lines.append(MARKER_ERRORD)
        lines.extend(errors)
        lines.append('')

    lines.append('')
    lines.append(MARKER_CODE)

    result = '\n'.join(lines)
    if code_text:
        result += '\n' + code_text

    return result


def fallback_sort(src):
    """Last-resort handler for unparseable input: deduplicate and sort lines."""
    return '\n'.join(filter(None, sorted(set(src.split('\n')))))


# -- Entry point --

def format_source(raw_src, filename=None):
    """Format imports in raw_src. Returns the formatted output string.

    If filename is provided, it is used to detect unused imports via pyflakes.
    """
    try:
        ast.parse(raw_src)
    except SyntaxError:
        output = fallback_sort(raw_src)
        if not output.endswith('\n'):
            output += '\n'
        return output

    preamble, rest = extract_preamble(raw_src)
    prioritized, src = extract_prioritized(rest)
    module = ast.parse(src)

    import_stmts, code_text = split_imports_and_code(module, src)

    unused = detect_unused_imports(raw_src, filename or '<stdin>')

    plain_imports, from_imports = collect_imports(import_stmts, unused)
    categories = categorize_imports(plain_imports, from_imports)

    output = format_output(categories, prioritized, code_text, preamble)
    if not output.endswith('\n'):
        output += '\n'
    return output


def parse_args():
    parser = argparse.ArgumentParser(
        description='Format and sort Python imports.',
    )
    parser.add_argument(
        '--files', nargs='+', default=None, type=Path,
        help='Python files to format in place. If omitted, reads from stdin and writes to stdout.',
    )
    parser.add_argument(
        '--force-stdin', action='store_true', default=False,
        help='Read source from stdin instead of the file. Requires exactly one --files arg '
             'which is used only as the filename for virtualenv discovery and unused-import detection.',
    )
    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    global _pyproject_root

    if args.force_stdin and args.files:
        assert len(args.files) == 1, '--force-stdin requires at most one --files argument'
        filepath = args.files[0].resolve()
        _third_party_top_levels.update(
            _scan_third_party_top_levels(
                _find_project_site_packages(filepath.parent)
            )
        )
        _pyproject_root = _find_pyproject_root(filepath.parent)
        raw_src = sys.stdin.read()
        output = format_source(raw_src, str(filepath))
        sys.stdout.write(output)
    elif args.files:
        for filepath in args.files:
            filepath = filepath.resolve()
            _third_party_top_levels.clear()
            _third_party_top_levels.update(
                _scan_third_party_top_levels(
                    _find_project_site_packages(filepath.parent)
                )
            )
            _pyproject_root = _find_pyproject_root(filepath.parent)
            raw_src = filepath.read_text()
            output = format_source(raw_src, str(filepath))
            filepath.write_text(output)
    else:
        _third_party_top_levels.update(
            _scan_third_party_top_levels(_find_project_site_packages())
        )
        _pyproject_root = _find_pyproject_root()
        raw_src = sys.stdin.read()
        output = format_source(raw_src)
        sys.stdout.write(output)


if __name__ == '__main__':
    main()
