
#!/usr/bin/env python3

import json
import os
import re
import shlex
import stat
import subprocess
import sys
import tempfile
import unicodedata
from functools import cache
from pathlib import Path


# プロジェクト内の自動削除許可ディレクトリ
SAFE_DIRS = {
    "dist",
    "build",
    "node_modules",
    ".cache",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "coverage",
    ".agent-tmp",
    "tmp",
}

# プロジェクト外の自動削除許可ディレクトリ
SAFE_EXTERNAL_DIRS = {
    Path("/tmp").resolve(),  # macOS では /private/tmp、Linux では /tmp
    # $TMPDIR（mktemp の作成先）。macOS では /private/var/folders/.../T
    Path(tempfile.gettempdir()).resolve(),
}

# プロジェクト外にある場合に削除を禁止するシステムディレクトリ（macOS / Linux 共通）。
# macOS の /etc, /var は /private 配下へ解決されるため、解決後のパスで比較する。
SYSTEM_DIRS = {
    Path(p).resolve()
    for p in (
        "/bin", "/sbin", "/usr", "/etc", "/var", "/lib", "/lib64", "/boot",
        "/dev", "/proc", "/sys", "/System", "/Library", "/Applications",
        "/private", "/opt",
    )
}

# 削除禁止対象
PROTECTED_NAMES = {
    ".git",
    ".claude",
    ".codex",
    ".ssh",
    ".aws",
    ".gnupg",
}

RM_RECURSIVE_OPTIONS = {
    "-r",
    "-R",
    "-rf",
    "-fr",
    "-Rf",
    "-fR",
    "--recursive",
}

# 自動承認可能な rm オプション
RM_SAFE_OPTIONS = RM_RECURSIVE_OPTIONS | {
    "-f",
    "-v",
    "--force",
    "--verbose",
}

RM_COMMANDS = {
    "rm",
    "/bin/rm",
    "/usr/bin/rm",
}

RMDIR_COMMANDS = {
    "rmdir",
    "/bin/rmdir",
    "/usr/bin/rmdir",
}

RMDIR_SAFE_OPTIONS = {
    "-v",
    "--verbose",
    "--ignore-fail-on-non-empty",
}

# 単純なコマンド列の区切りとして扱うトークン
COMMAND_SEPARATORS = {";", "&&", "||", "|", "&", "\n"}

# 区切り以外の記号（サブシェル・リダイレクト等）は対象を静的に確定できない
SHELL_PUNCTUATION = ";&|()<>\n"

# 分岐・ループ内での cd や変数代入は実行有無を追えないため、状態を不明にする
SHELL_KEYWORDS = {
    "if", "then", "elif", "else", "fi",
    "for", "while", "until", "do", "done",
    "case", "esac", "select", "function",
    "{", "}", "!", "[[", "]]",
}

# シェル変数を書き換え得るコマンド
VARIABLE_MUTATORS = {
    "read", "export", "declare", "typeset", "local", "readonly", "unset",
    "printf", "mapfile", "readarray", "getopts", "let",
}

# 作業ディレクトリと変数の両方を書き換え得るコマンド
STATE_MUTATORS = {"source", ".", "eval", "exec", "pushd", "popd"}

ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")
VARIABLE_REFERENCE = re.compile(
    r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)\}|([A-Za-z_][A-Za-z0-9_]*))"
)
# glob とブレース展開（{a,b} / {1..3}）
GLOB_CHARS = re.compile(r"[*?\[{}]")

# shlex はクォートの種類を保持しないため、$ の解釈が bash と食い違い得る構文
# （$'...' / $"..." / \$ / '...$...'）は判定しない
QUOTED_DOLLAR = re.compile(r"\$['\"]|\\\$|'[^']*\$[^']*'")

# コマンド探索・単語分割・cd・動的リンク等、シェルや rm の挙動自体を変える変数
SHELL_BEHAVIOR_VARIABLES = {
    "PATH", "IFS", "CDPATH", "GLOBIGNORE", "BASH_ENV", "ENV",
    "SHELLOPTS", "BASHOPTS", "POSIXLY_CORRECT",
}
SHELL_BEHAVIOR_VARIABLE_PREFIXES = ("LD_", "DYLD_", "BASH_FUNC_")


class UnresolvableCommand(Exception):
    """削除対象を静的に確定できないコマンド。"""


def decide(decision, reason):
    """Claude Code に権限判定を返す。"""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }, ensure_ascii=False))


def case_key(name):
    decomposed = unicodedata.normalize("NFD", name)
    return unicodedata.normalize("NFD", decomposed.casefold())


def actual_entry_name(parent, name):
    """ファイルシステムが別表記を受理する場合は実名を返す。"""
    try:
        requested = (parent / name).lstat()
    except (FileNotFoundError, NotADirectoryError):
        return name

    key = case_key(name)
    aliases = []
    with os.scandir(parent) as entries:
        for entry in entries:
            if entry.name == name:
                return name
            if case_key(entry.name) == key and os.path.samestat(
                requested, entry.stat(follow_symlinks=False)
            ):
                aliases.append(entry.name)

    if len(aliases) != 1:
        raise OSError(f"Cannot determine the on-disk name of {parent / name}")
    return aliases[0]


def canonicalize_case(path):
    """リンクや親参照を残し、存在するパス要素を実名に揃える。"""
    canonical = Path(path.anchor)
    for name in path.parts[1:]:
        if name != "..":
            name = actual_entry_name(canonical, name)
        canonical /= name
    return canonical


def is_protected_name(name):
    return name in PROTECTED_NAMES or name == ".env" or name.startswith(".env.")


def is_protected_entry(path):
    name = path.name
    if is_protected_name(name):
        return True

    protected_name = case_key(name)
    if protected_name.startswith(".env."):
        protected_name = ".env." + name[len(".env."):]
    return is_protected_name(protected_name) and (
        actual_entry_name(path.parent, protected_name) == name
    )


def is_protected(path):
    return any(is_protected_entry(entry) for entry in (path, *path.parents))


def inspect_recursive_target(path):
    """削除される配下を調べる。シンボリックリンクの先には降りない。"""
    try:
        mode = path.lstat().st_mode
    except (FileNotFoundError, NotADirectoryError):
        return None
    except OSError as exc:
        return "defer", f"Cannot inspect recursive target: {exc}"

    if not stat.S_ISDIR(mode):
        return None

    directories = [path]
    inspection_error = None
    while directories:
        try:
            with os.scandir(directories.pop()) as entries:
                for entry in entries:
                    entry_path = Path(entry.path)
                    try:
                        # node_modules 等には .env.example や .git が含まれ得るため、
                        # 配下の保護名は deny にせず通常の権限フローに任せる。
                        if is_protected_entry(entry_path):
                            return "defer", f"Protected entry inside target: {entry_path}"
                        if stat.S_ISDIR(entry.stat(follow_symlinks=False).st_mode):
                            directories.append(entry_path)
                    except OSError as exc:
                        inspection_error = exc
        except OSError as exc:
            inspection_error = exc

    if inspection_error is not None:
        return "defer", f"Cannot inspect recursive target: {inspection_error}"
    return None


def normalize_private_alias(path):
    """macOS の /tmp と /var（$TMPDIR の親）を /private 配下に統一する。"""
    for name in ("tmp", "var"):
        alias = Path("/") / name
        actual = Path("/private") / name

        if (
            alias.is_symlink()
            and alias.resolve() == actual.resolve()
            and path.is_relative_to(alias)
        ):
            return actual / path.relative_to(alias)

    return path


def has_symlink(path):
    """削除対象とその親ディレクトリを検査する。"""
    return any(
        p.is_symlink()
        for p in (path, *path.parents)
    )


def run_git(root, *args):
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        timeout=3,
        check=False,
    )
    if result.returncode != 0:
        return None

    return os.fsdecode(result.stdout).split("\0")[:-1]


@cache
def git_index_paths(root):
    return run_git(root, "ls-files", "-z")


@cache
def git_modified_paths(root):
    """HEAD から変更（staged / unstaged）がある Git 管理下のパス。

    ls-files と同じく root 基準の相対パスで得るため --relative を付ける
    （root がリポジトリのサブディレクトリでも照合できる）。
    rename は元パスも含めるため --no-renames を付ける。
    """
    return run_git(
        root, "diff", "HEAD", "--name-only", "--relative", "--no-renames", "-z",
    )


def contains_path(root, target, paths):
    """target 自身か配下が paths に含まれるか。index と作業ツリーの名前の違いも考慮する。"""
    # Git の状態を確認できない場合は含まれるものとして扱う
    if paths is None:
        return True

    relative = target.relative_to(root)
    depth = len(relative.parts)
    relative_name = str(relative)
    key = case_key(relative_name)

    for index_path in paths:
        prefix = "/".join(index_path.split("/", depth)[:depth])
        if prefix == relative_name:
            return True
        if case_key(prefix) == key and canonicalize_case(root / prefix) == target:
            return True

    return False


def classify_target(target, cwd, root, home, recursive):
    """削除対象単位で allow / ask / deny / defer を判定する。"""

    path = Path(target)

    if not path.is_absolute():
        path = cwd / path

    # macOS 標準の /tmp・/var エイリアスを正規化
    path = normalize_private_alias(canonicalize_case(path))

    # シンボリックリンクは自動承認しない
    symlink_detected = has_symlink(path)

    # ".." などを含めて実パスに正規化
    resolved = path.resolve()
    if symlink_detected:
        resolved = canonicalize_case(resolved)

    # ディレクトリそのものの削除は禁止
    protected_roots = {
        Path("/"),
        root,
        home,
        *SAFE_EXTERNAL_DIRS,
    }

    for protected in protected_roots:
        if (
            resolved == protected
            or protected.is_relative_to(resolved)
        ):
            return (
                "deny",
                f"Protected directory: {resolved}"
            )

    # 保護対象の名前を検査
    if is_protected(path) or is_protected(resolved):
        return (
            "deny",
            f"Protected target: {resolved}"
        )

    in_project = resolved.is_relative_to(root)
    in_external_temp = any(
        resolved.is_relative_to(safe_dir) for safe_dir in SAFE_EXTERNAL_DIRS
    )
    if recursive and (in_project or in_external_temp):
        # macOS の rm は末尾が / の場合にリンク先を走査し得る。
        recursive_target = resolved if target.endswith("/") else path
        inspection = inspect_recursive_target(recursive_target)
        if inspection is not None:
            return inspection

    # プロジェクト内の削除判定
    if in_project:
        relative = resolved.relative_to(root)

        if contains_path(root, resolved, git_index_paths(root)):
            # Bash の rm は checkpoint で戻せないため、未コミットの変更だけは確認する
            if contains_path(root, resolved, git_modified_paths(root)):
                return (
                    "ask",
                    f"Uncommitted changes or unverifiable Git state: {relative}"
                )
            return (
                "defer",
                f"Git tracked: {relative}"
            )

        if symlink_detected:
            return (
                "defer",
                f"Symlink detected: {path}"
            )

        if relative.parts[0] in SAFE_DIRS:
            return (
                "allow",
                f"Generated artifact: {relative}"
            )

        return (
            "defer",
            f"Not allowlisted: {relative}"
        )

    # /private/tmp 配下などの削除判定
    if in_external_temp:
        if symlink_detected:
            return (
                "defer",
                f"Symlink detected: {path}"
            )

        return (
            "allow",
            f"Temporary artifact: {resolved}"
        )

    if any(resolved.is_relative_to(system_dir) for system_dir in SYSTEM_DIRS):
        return (
            "deny",
            f"System directory: {resolved}"
        )

    # その他のプロジェクト外パスは通常の権限フローに任せる
    return (
        "defer",
        f"Outside permitted directories: {resolved}"
    )


def tokenize(command):
    """クォートを解釈し、区切り記号を独立したトークンに分ける。"""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=SHELL_PUNCTUATION)
    # 改行はコマンド区切りとして残す
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    # shlex は語の途中の # でも行末まで捨てるが bash は語頭の # だけをコメントとみなす。
    # 解釈差で後続の行を見落とさないよう、コメント処理を無効化して # を含む語は拒否する
    lexer.commenters = ""
    tokens = list(lexer)
    if any("#" in token for token in tokens):
        raise UnresolvableCommand("Comment or '#' in command")
    return tokens


def split_segments(tokens):
    """(直前の区切り, 単語列, 直後の区切り) の列に分解する。"""
    segments = []
    words = []
    separator_before = None

    for token in tokens:
        if "`" in token:
            raise UnresolvableCommand("Command substitution")
        if token in COMMAND_SEPARATORS:
            segments.append((separator_before, words, token))
            words = []
            separator_before = token
            continue
        if all(char in SHELL_PUNCTUATION for char in token):
            raise UnresolvableCommand(f"Subshell or redirection: {token}")
        if "\n" in token:
            raise UnresolvableCommand("Multi-line argument")
        words.append(token)

    segments.append((separator_before, words, None))
    return [segment for segment in segments if segment[1]]


def expand_variables(word, variables):
    """同一コマンド内でリテラル代入された変数だけを展開する。"""

    def replace(match):
        name = match.group(1) or match.group(2)
        if name not in variables:
            raise UnresolvableCommand(f"Unresolved variable: ${name}")
        return variables[name]

    expanded = VARIABLE_REFERENCE.sub(replace, word)
    if "$" in expanded:
        raise UnresolvableCommand(f"Unsupported expansion: {word}")
    return expanded


def literal_path(word, variables):
    """チルダ・変数を展開したパスを返す。glob 等の展開結果は確定できないため拒否する。"""
    # bash は語頭の ~ と ~/ を $HOME に展開する（~user は扱わない）
    if word == "~" or word.startswith("~/"):
        word = "${HOME}" + word[1:]
    path = expand_variables(word, variables)
    if path.startswith("~") or GLOB_CHARS.search(path):
        raise UnresolvableCommand(f"Unsupported expansion: {word}")
    return path


def changes_shell_behavior(assignment):
    name = assignment.split("=", 1)[0]
    return (
        name in SHELL_BEHAVIOR_VARIABLES
        or name.startswith(SHELL_BEHAVIOR_VARIABLE_PREFIXES)
    )


def record_assignments(words, variables, unconditional):
    for word in words:
        name, value = word.split("=", 1)
        variables.pop(name, None)
        if not unconditional:
            continue
        try:
            value = expand_variables(value, variables)
        except UnresolvableCommand:
            continue
        # 空白を含む値は未クォート参照で単語分割されるため追跡しない
        if value.startswith("~") or ":~" in value or any(c.isspace() for c in value):
            continue
        variables[name] = value


def parse_deletion_args(args):
    """rm / rmdir の引数を (deny/defer 判定 or None, 対象, 再帰削除か) に分ける。"""
    safe_options = (
        RMDIR_SAFE_OPTIONS if args[0] in RMDIR_COMMANDS else RM_SAFE_OPTIONS
    )

    targets = []
    end_options = False
    recursive = False

    for arg in args[1:]:
        if not end_options and arg == "--":
            end_options = True
            continue

        if not end_options and arg.startswith("-"):
            if arg == "--no-preserve-root":
                return ("deny", "Unsafe rm option"), [], False
            if arg not in safe_options:
                return ("defer", f"Unknown option: {arg}"), [], False
            if arg in RM_RECURSIVE_OPTIONS:
                recursive = True
            continue

        targets.append(arg)

    if not targets:
        return ("defer", "No explicit deletion target"), [], False

    return None, targets, recursive


def evaluate_command(command, cwd, root, home):
    """コマンド全体の判定を返す。None は判定せず通常の権限フローへ委譲することを表す。

    確実に危険なら deny、未コミットの変更を消し得るなら ask、確実に安全なら allow。
    静的に判定できないものは hook で止めず、acceptEdits / auto mode 等の判定に任せる。
    """
    if QUOTED_DOLLAR.search(command):
        return None

    try:
        segments = split_segments(tokenize(command))
    except (ValueError, UnresolvableCommand):
        return None

    deletion_commands = RM_COMMANDS | RMDIR_COMMANDS
    # cd の成否や && / || の分岐で取り得る作業ディレクトリをすべて保持する
    current_cwds = {cwd}
    seen_cwds = {cwd}
    cwd_unknown = False
    # ~ と $HOME の展開用。変数を書き換え得るコマンドの後は他の変数と同様に不明になる
    variables = {"HOME": str(home)}
    approval_reasons = []
    deferred = False
    has_other_commands = False
    has_deletion = False

    for separator_before, words, separator_after in segments:
        if separator_before is not None and separator_before != "&&":
            current_cwds = set(seen_cwds)

        command_index = 0
        while command_index < len(words) and ASSIGNMENT.match(words[command_index]):
            command_index += 1

        if any(changes_shell_behavior(word) for word in words[:command_index]):
            return None

        # 代入のみの segment は副作用がないため、他のコマンドとして扱わない
        # （コマンド置換は split_segments で拒否済み）
        if command_index == len(words):
            unconditional = (
                separator_before in (None, ";", "\n")
                and separator_after in (None, ";", "\n", "&&")
            )
            record_assignments(words, variables, unconditional)
            continue

        args = words[command_index:]
        head = args[0]

        if head not in deletion_commands:
            has_other_commands = True
            if any(word in deletion_commands for word in args[1:]):
                # xargs rm / git rm 等の間接実行
                deferred = True
            if head in SHELL_KEYWORDS or head in STATE_MUTATORS:
                cwd_unknown = True
                variables.clear()
            elif head in VARIABLE_MUTATORS:
                variables.clear()
            elif head == "cd":
                try:
                    if len(args) != 2 or args[1].startswith("-"):
                        raise UnresolvableCommand("Unsupported cd form")
                    destination = literal_path(args[1], variables)
                    # CDPATH があると相対パスの cd 先が作業ディレクトリ基準にならない
                    if os.environ.get("CDPATH") and not Path(destination).is_absolute():
                        raise UnresolvableCommand("cd with CDPATH")
                except UnresolvableCommand:
                    cwd_unknown = True
                    continue
                current_cwds = {base / destination for base in current_cwds}
                seen_cwds |= current_cwds
            continue

        has_deletion = True
        try:
            expanded_args = [head] + [
                literal_path(arg, variables) for arg in args[1:]
            ]
        except UnresolvableCommand:
            deferred = True
            continue

        rejection, targets, recursive = parse_deletion_args(expanded_args)
        if rejection is not None:
            if rejection[0] == "deny":
                return rejection
            deferred = True
            continue

        for target in targets:
            if cwd_unknown and not Path(target).is_absolute():
                deferred = True
                continue
            for target_cwd in sorted(current_cwds):
                decision, reason = classify_target(
                    target, target_cwd, root, home, recursive,
                )
                if decision == "deny":
                    return decision, reason
                if decision == "ask":
                    approval_reasons.append(reason)
                elif decision == "defer":
                    deferred = True

    if approval_reasons:
        return "ask", "; ".join(dict.fromkeys(approval_reasons))

    # hook の allow は Bash 呼び出し全体の確認を省くため、
    # 他のコマンドを含む場合は判定せず通常の権限フローに任せる
    if deferred or has_other_commands or not has_deletion:
        return None

    return (
        "allow",
        "All targets are permitted temporary files or generated artifacts",
    )


def main():
    data = json.load(sys.stdin)

    command = data["tool_input"]["command"]
    root = canonicalize_case(Path(os.environ["CLAUDE_PROJECT_DIR"]).resolve())
    cwd = canonicalize_case(Path(data["cwd"]).resolve())
    home = canonicalize_case(Path.home().resolve())

    result = evaluate_command(command, cwd, root, home)
    if result is not None:
        decide(*result)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        decide(
            "deny",
            f"Deletion guard failed: {exc}"
        )
