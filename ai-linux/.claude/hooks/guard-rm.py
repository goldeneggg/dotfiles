
#!/usr/bin/env python3

import json
import os
import re
import shlex
import stat
import subprocess
import sys
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

# 自動承認の対象外とするシェル構文
COMPLEX_SYNTAX = re.compile(
    r"[;&|<>$`*?\[\]{}~\\\n\r()!#]"
)


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
        return "ask", f"Cannot inspect recursive target: {exc}"

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
                        # 配下の保護名は deny ではなくユーザー確認にする。
                        if is_protected_entry(entry_path):
                            return "ask", f"Protected entry inside target: {entry_path}"
                        if stat.S_ISDIR(entry.stat(follow_symlinks=False).st_mode):
                            directories.append(entry_path)
                    except OSError as exc:
                        inspection_error = exc
        except OSError as exc:
            inspection_error = exc

    if inspection_error is not None:
        return "ask", f"Cannot inspect recursive target: {inspection_error}"
    return None


def normalize_tmp_alias(path):
    """macOS の /tmp を /private/tmp に統一する。"""
    alias = Path("/tmp")
    actual = Path("/private/tmp")

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


@cache
def git_index_paths(root):
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        capture_output=True,
        timeout=3,
        check=False,
    )
    if result.returncode != 0:
        return None

    return os.fsdecode(result.stdout).split("\0")[:-1]


def has_tracked_files(root, target):
    """index と作業ツリーの名前が異なる場合も同じ対象か確認する。"""
    relative = target.relative_to(root)
    depth = len(relative.parts)
    relative_name = str(relative)
    key = case_key(relative_name)
    index_paths = git_index_paths(root)

    # Git の状態を確認できない場合は自動承認しない
    if index_paths is None:
        return True

    for index_path in index_paths:
        prefix = "/".join(index_path.split("/", depth)[:depth])
        if prefix == relative_name:
            return True
        if case_key(prefix) == key and canonicalize_case(root / prefix) == target:
            return True

    return False


def classify_target(target, cwd, root, home, recursive):
    """削除対象単位で allow / ask / deny を判定する。"""

    path = Path(target)

    if not path.is_absolute():
        path = cwd / path

    # macOS 標準の /tmp エイリアスを正規化
    path = normalize_tmp_alias(canonicalize_case(path))

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

        if symlink_detected:
            return (
                "ask",
                f"Symlink detected: {path}"
            )

        if has_tracked_files(root, resolved):
            return (
                "ask",
                f"Git tracked or unverifiable: {relative}"
            )

        if relative.parts[0] in SAFE_DIRS:
            return (
                "allow",
                f"Generated artifact: {relative}"
            )

        return (
            "ask",
            f"Not allowlisted: {relative}"
        )

    # /private/tmp 配下などの削除判定
    if in_external_temp:
        if symlink_detected:
            return (
                "ask",
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

    # その他のプロジェクト外パスはユーザー確認
    return (
        "ask",
        f"Outside permitted directories: {resolved}"
    )


def main():
    data = json.load(sys.stdin)

    command = data["tool_input"]["command"]
    root = canonicalize_case(Path(os.environ["CLAUDE_PROJECT_DIR"]).resolve())
    cwd = canonicalize_case(Path(data["cwd"]).resolve())
    home = canonicalize_case(Path.home().resolve())

    # 複雑なシェル構文は自動承認しない
    if COMPLEX_SYNTAX.search(command):
        return decide(
            "ask",
            "Complex shell syntax; approval required"
        )

    try:
        args = shlex.split(command)
    except ValueError:
        return decide(
            "ask",
            "Cannot parse command safely"
        )

    # 間接実行・ラッパー経由は自動承認しない
    if not args or args[0] not in (
        RM_COMMANDS | RMDIR_COMMANDS
    ):
        return decide(
            "ask",
            "Indirect or wrapped deletion command"
        )

    is_rmdir = args[0] in RMDIR_COMMANDS

    safe_options = (
        RMDIR_SAFE_OPTIONS if is_rmdir else RM_SAFE_OPTIONS
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
                return decide(
                    "deny",
                    "Unsafe rm option"
                )

            if arg not in safe_options:
                return decide(
                    "ask",
                    f"Unknown option: {arg}"
                )

            if arg in RM_RECURSIVE_OPTIONS:
                recursive = True
            continue

        targets.append(arg)

    if not targets:
        return decide(
            "ask",
            "No explicit deletion target"
        )

    # 全削除対象を評価する。
    # Deny > Ask > Allow の優先順位を維持する。
    approval_reasons = []

    for target in targets:
        decision, reason = classify_target(
            target,
            cwd,
            root,
            home,
            recursive,
        )

        if decision == "deny":
            return decide("deny", reason)

        if decision == "ask":
            approval_reasons.append(reason)

    if approval_reasons:
        return decide(
            "ask",
            "; ".join(approval_reasons)
        )

    return decide(
        "allow",
        "All targets are permitted temporary "
        "files or generated artifacts"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        decide(
            "deny",
            f"Deletion guard failed: {exc}"
        )
