#!/usr/bin/env python3
import json
import os
import re
import shlex
import sys


PROFILE_NAME = "claude-synced"
CONFIG_SETTINGS_MARKER_BEGIN = "# sync-claude-permissions-settings-begin\n"
CONFIG_SETTINGS_MARKER_END = "# sync-claude-permissions-settings-end\n"
CONFIG_MARKER_BEGIN = "# sync-claude-permissions-begin\n"
CONFIG_MARKER_END = "# sync-claude-permissions-end\n"
EXTENDS_MARKER_BEGIN = "# sync-claude-permissions-extends-begin\n"
EXTENDS_MARKER_END = "# sync-claude-permissions-extends-end\n"
RULES_MARKER_BEGIN = "# sync-claude-permissions-begin\n"
RULES_MARKER_END = "# sync-claude-permissions-end\n"


def toml_quote(value):
    return json.dumps(value)


def starlark_quote(value):
    return json.dumps(value)


def parse_rule(rule):
    m = re.match(r"^([A-Za-z0-9_*_-]+)(?:\((.*)\))?$", rule)
    if not m:
        return None, None
    return m.group(1), m.group(2)


def strip_trailing_wildcard(spec):
    if spec.endswith(":*"):
        return spec[:-2].rstrip()
    if spec.endswith(" *"):
        return spec[:-2].rstrip()
    return spec


def bash_rule_to_pattern(spec):
    if spec is None:
        return None, "bare Bash rules cannot be represented as a Codex prefix_rule"

    prefix = strip_trailing_wildcard(spec)
    if "*" in prefix:
        return None, "non-trailing Bash wildcards cannot be represented as a Codex prefix_rule"

    try:
        pattern = shlex.split(prefix)
    except ValueError as e:
        return None, "failed to parse Bash rule with shlex: {}".format(e)

    if not pattern:
        return None, "empty Bash rule"
    return pattern, None


def claude_read_path_to_codex(path):
    if path.startswith("//"):
        return "filesystem", "/" + path[2:]
    if path.startswith("~/"):
        return "filesystem", path
    if path.startswith("./"):
        return "workspace", path[2:]
    if path.startswith("/"):
        return "workspace", path[1:]
    return "workspace", path


def append_marker_section(path, marker_begin, marker_end, section):
    existing = open(path).read() if os.path.exists(path) else ""
    cleaned = remove_marker_section(existing, marker_begin, marker_end)
    content = (cleaned + "\n\n" if cleaned else "") + marker_begin + section + marker_end
    with open(path, "w") as f:
        f.write(content)


def remove_marker_section(text, marker_begin, marker_end):
    pattern = r"\n*{}.*?{}?".format(re.escape(marker_begin), re.escape(marker_end))
    return re.sub(pattern, "", text, flags=re.DOTALL).strip()


def remove_profile_toml_sections(text, profile_name):
    """テキストから [permissions.X] および [permissions.X.*] セクションを除去する。

    マーカー外に残った同名プロファイル定義がマーカー内の定義と重複するのを防ぐ。
    """
    lines = text.split("\n")
    result = []
    skipping = False
    section_pattern = re.compile(
        r"^\s*\[permissions\.{}(?:\..*)?\]".format(re.escape(profile_name))
    )
    next_section_pattern = re.compile(r"^\s*\[(?!permissions\.{}[\]\.])".format(re.escape(profile_name)))

    for line in lines:
        if not skipping:
            if section_pattern.match(line):
                skipping = True
                continue
            result.append(line)
        else:
            if next_section_pattern.match(line):
                skipping = False
                result.append(line)

    cleaned = "\n".join(result)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def detect_existing_permissions(text):
    """既存config.tomlのpermission関連設定を検出する。

    Returns:
        (default_perms_match, has_sandbox_mode)
        - default_perms_match: re.Match or None (グループ1にプロファイル名)
        - has_sandbox_mode: bool
    """
    default_perms = re.search(
        r'^\s*default_permissions\s*=\s*"([^"]*)"', text, re.MULTILINE
    )
    has_sandbox_mode = bool(
        re.search(r"^\s*sandbox_mode\s*=", text, re.MULTILINE)
    )
    return default_perms, has_sandbox_mode


def find_profile_section(text, profile_name):
    """[permissions.X] or [permissions.X.*] セクションの存在を確認する。"""
    pattern = r"^\s*\[permissions\.{}(?:\.\w+)?\]".format(re.escape(profile_name))
    return re.search(pattern, text, re.MULTILINE)


def profile_has_extends(text, profile_name):
    """プロファイルが既に extends を持っているか確認する。

    [permissions.X] セクション内の extends = "..." を探す。
    マーカー内の extends も含めて検索する。
    """
    section_pattern = r'\[permissions\.{}\]'.format(re.escape(profile_name))
    section_match = re.search(section_pattern, text, re.MULTILINE)
    if not section_match:
        return None

    after_section = text[section_match.end():]
    next_section = re.search(r"^\s*\[", after_section, re.MULTILINE)
    section_body = after_section[:next_section.start()] if next_section else after_section

    extends_match = re.search(r'^\s*extends\s*=\s*"([^"]*)"', section_body, re.MULTILINE)
    if extends_match:
        return extends_match.group(1)
    return None


def remove_extends_marker(text):
    """extends マーカーを除去する（インライン対応: 改行を1つ保持）。"""
    pattern = r"{}.*?{}".format(re.escape(EXTENDS_MARKER_BEGIN), re.escape(EXTENDS_MARKER_END))
    return re.sub(pattern, "", text, flags=re.DOTALL)


def add_extends_to_profile(text, profile_name):
    """既存プロファイルに extends = "claude-synced" を付与する。

    Returns:
        (modified_text, status)
        status: "added" | "already-extends-claude-synced" | "has-other-extends" | "created"
    """
    # マーカー除去前に、既に正しい extends が設定されているか確認
    existing_extends = profile_has_extends(text, profile_name)
    if existing_extends == PROFILE_NAME:
        return text, "already-extends-claude-synced"
    if existing_extends is not None:
        return text, "has-other-extends"

    text = remove_extends_marker(text)

    extends_content = 'extends = "{}"\n'.format(PROFILE_NAME)
    extends_block = EXTENDS_MARKER_BEGIN + extends_content + EXTENDS_MARKER_END

    bare_section_pattern = r'^(\s*\[permissions\.{}\]\s*\n)'.format(re.escape(profile_name))
    bare_match = re.search(bare_section_pattern, text, re.MULTILINE)
    if bare_match:
        insert_pos = bare_match.end()
        text = text[:insert_pos] + extends_block + text[insert_pos:]
        return text, "added"

    sub_section_pattern = r'^(\s*\[permissions\.{}\.(\w+)\])'.format(re.escape(profile_name))
    sub_match = re.search(sub_section_pattern, text, re.MULTILINE)
    if sub_match:
        insert_pos = sub_match.start()
        new_section = "[permissions.{}]\n".format(profile_name) + extends_block + "\n"
        text = text[:insert_pos] + new_section + text[insert_pos:]
        return text, "added"

    new_section = "[permissions.{}]\n".format(profile_name) + extends_content
    extends_block_full = EXTENDS_MARKER_BEGIN + new_section + EXTENDS_MARKER_END
    text = text.rstrip() + "\n\n" + extends_block_full if text.strip() else extends_block_full
    return text, "created"


def write_config(path, web_search, permissions_section):
    """config.toml を既存設定を壊さず更新する。

    Returns:
        mode description string for user output
    """
    existing = open(path).read() if os.path.exists(path) else ""

    cleaned = remove_marker_section(existing, CONFIG_SETTINGS_MARKER_BEGIN, CONFIG_SETTINGS_MARKER_END)
    cleaned = remove_marker_section(cleaned, CONFIG_MARKER_BEGIN, CONFIG_MARKER_END)
    # マーカー外に残った claude-synced プロファイル定義を除去（TOML重複防止）
    cleaned = remove_profile_toml_sections(cleaned, PROFILE_NAME)

    default_perms_match, has_sandbox_mode = detect_existing_permissions(cleaned)

    # ケース判定
    if default_perms_match:
        existing_profile = default_perms_match.group(1)
        if existing_profile == PROFILE_NAME:
            mode = "updated (default_permissions already points to {})".format(PROFILE_NAME)
        else:
            cleaned, extends_status = add_extends_to_profile(cleaned, existing_profile)
            if extends_status == "added":
                mode = 'extended profile "{}" with {} rules'.format(existing_profile, PROFILE_NAME)
            elif extends_status == "created":
                mode = 'created [permissions.{}] with extends = "{}"'.format(existing_profile, PROFILE_NAME)
            elif extends_status == "already-extends-claude-synced":
                mode = 'profile "{}" already extends {}'.format(existing_profile, PROFILE_NAME)
            else:
                mode = 'WARNING: profile "{}" already extends "{}"; {} rules added but not auto-linked'.format(
                    existing_profile, profile_has_extends(cleaned, existing_profile), PROFILE_NAME
                )
    elif has_sandbox_mode:
        mode = "added profile definitions only (sandbox_mode detected; legacy mode)"
    else:
        mode = "set default_permissions = {}".format(PROFILE_NAME)

    # settings セクション構築
    settings_lines = []
    need_default_permissions = (
        not default_perms_match and not has_sandbox_mode
    )
    if need_default_permissions:
        settings_lines.append('default_permissions = "{}"'.format(PROFILE_NAME))
    if web_search and not re.search(r"^\s*web_search\s*=", cleaned, re.MULTILINE):
        settings_lines.append('web_search = "{}"'.format(web_search))

    # permissions プロファイル定義ブロック
    permissions_block = CONFIG_MARKER_BEGIN + permissions_section + CONFIG_MARKER_END

    # 組み立て
    parts = []
    if settings_lines:
        settings_section = "# Generated from Claude Code permissions.\n" + "\n".join(settings_lines) + "\n"
        settings_block = CONFIG_SETTINGS_MARKER_BEGIN + settings_section + CONFIG_SETTINGS_MARKER_END
        parts.append(settings_block.strip())
    if cleaned:
        parts.append(cleaned)
    parts.append(permissions_block.strip())
    content = "\n\n".join(parts) + "\n"
    content = re.sub(r"\n{3,}", "\n\n", content)

    with open(path, "w") as f:
        f.write(content)

    return mode


def collect_permissions(cfg):
    permissions = cfg.get("permissions", {})
    return {
        "allow": permissions.get("allow", []),
        "deny": permissions.get("deny", []),
        "ask": permissions.get("ask", []),
    }


def build_config_sections(perms, unsupported):
    """permissions プロファイル定義と web_search 設定を生成する。

    Returns:
        (web_search, permissions_section)
        - web_search: str or None
        - permissions_section: str (TOML profile definition)
    """
    filesystem_denies = []
    workspace_denies = []
    domain_rules = {}
    web_search = None

    for decision, rules in perms.items():
        for rule in rules:
            tool, spec = parse_rule(rule)
            if tool == "Read":
                if decision != "deny":
                    continue
                if spec is None:
                    unsupported.append((decision, rule, "bare Read deny is too broad for this converter"))
                    continue
                scope, codex_path = claude_read_path_to_codex(spec)
                if scope == "workspace":
                    workspace_denies.append(codex_path)
                else:
                    filesystem_denies.append(codex_path)
            elif tool == "WebFetch":
                if spec is None:
                    if decision == "allow":
                        domain_rules["*"] = "allow"
                    else:
                        unsupported.append((decision, rule, "bare WebFetch deny/ask is not converted"))
                    continue
                if not spec.startswith("domain:"):
                    unsupported.append((decision, rule, "only WebFetch(domain:...) rules are supported"))
                    continue
                domain = spec.removeprefix("domain:")
                if decision in ("allow", "deny"):
                    if domain == "*" and decision == "deny":
                        unsupported.append((decision, rule, "Codex network policy only supports global * for allow"))
                        continue
                    domain_rules[domain] = decision
                else:
                    unsupported.append((decision, rule, "Codex network policy does not support ask domains"))
            elif tool == "WebSearch":
                if decision == "deny":
                    web_search = "disabled"
                elif decision == "allow" and web_search != "disabled":
                    web_search = "cached"

    lines = []
    lines.append("# Generated from Claude Code permissions.")
    lines.append("[permissions.{}.filesystem]".format(PROFILE_NAME))
    lines.append('":minimal" = "read"')
    if any("**" in path for path in workspace_denies):
        lines.append("glob_scan_max_depth = 6")
    for path in sorted(set(filesystem_denies)):
        lines.append("{} = \"deny\"".format(toml_quote(path)))
    lines.append("")

    lines.append('[permissions.{}.filesystem.":workspace_roots"]'.format(PROFILE_NAME))
    lines.append('"." = "write"')
    for path in sorted(set(workspace_denies)):
        lines.append("{} = \"deny\"".format(toml_quote(path)))

    if domain_rules:
        lines.append("")
        lines.append("[permissions.{}.network]".format(PROFILE_NAME))
        lines.append("enabled = true")
        lines.append("")
        lines.append("[permissions.{}.network.domains]".format(PROFILE_NAME))
        for domain, decision in sorted(domain_rules.items()):
            lines.append("{} = {}".format(toml_quote(domain), toml_quote(decision)))

    return web_search, "\n".join(lines) + "\n"


def build_rules_section(perms, unsupported):
    decision_map = {
        "allow": "allow",
        "ask": "prompt",
        "deny": "forbidden",
    }
    lines = ["# Generated from Claude Code Bash permissions."]
    count = 0

    for decision in ("deny", "ask", "allow"):
        for rule in perms[decision]:
            tool, spec = parse_rule(rule)
            if tool != "Bash":
                continue
            pattern, error = bash_rule_to_pattern(spec)
            if error:
                unsupported.append((decision, rule, error))
                continue

            lines.append("")
            lines.append("prefix_rule(")
            lines.append(
                "    pattern = [{}],".format(
                    ", ".join(starlark_quote(part) for part in pattern)
                )
            )
            lines.append('    decision = "{}",'.format(decision_map[decision]))
            lines.append(
                "    justification = {},".format(
                    starlark_quote("Synced from Claude permissions.{}: {}".format(decision, rule))
                )
            )
            lines.append(")")
            count += 1

    if count == 0:
        lines.append("# No Bash permission rules found.")

    return "\n".join(lines) + "\n", count


def print_unsupported(unsupported):
    if not unsupported:
        return
    print("Unsupported Claude permission rules:")
    for decision, rule, reason in unsupported:
        print("  - {}: {} ({})".format(decision, rule, reason))


def main():
    if len(sys.argv) != 4:
        print(
            "Usage: {} <source_settings_json> <dest_config_toml> <dest_rules_file>".format(
                sys.argv[0]
            ),
            file=sys.stderr,
        )
        sys.exit(1)

    src = sys.argv[1]
    dst_config = sys.argv[2]
    dst_rules = sys.argv[3]

    with open(src) as f:
        cfg = json.load(f)

    perms = collect_permissions(cfg)
    unsupported = []
    web_search, permissions_section = build_config_sections(perms, unsupported)
    rules_section, rules_count = build_rules_section(perms, unsupported)

    os.makedirs(os.path.dirname(dst_config), exist_ok=True)
    os.makedirs(os.path.dirname(dst_rules), exist_ok=True)

    mode = write_config(dst_config, web_search, permissions_section)
    append_marker_section(dst_rules, RULES_MARKER_BEGIN, RULES_MARKER_END, rules_section)

    read_deny_count = sum(
        1 for rule in perms["deny"] if parse_rule(rule)[0] == "Read"
    )
    web_count = sum(
        1
        for decision in ("allow", "deny")
        for rule in perms[decision]
        if parse_rule(rule)[0] in ("WebFetch", "WebSearch")
    )

    print("Synced Claude permissions to Codex:")
    print("  config: {}".format(dst_config))
    print("  mode: {}".format(mode))
    print("  rules: {}".format(dst_rules))
    print("  Bash rules: {}".format(rules_count))
    print("  Read deny rules: {}".format(read_deny_count))
    print("  Web rules: {}".format(web_count))
    print_unsupported(unsupported)


if __name__ == "__main__":
    main()
