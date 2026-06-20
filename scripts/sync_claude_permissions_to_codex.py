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


def write_config(path, settings_section, permissions_section):
    existing = open(path).read() if os.path.exists(path) else ""
    cleaned = remove_marker_section(existing, CONFIG_SETTINGS_MARKER_BEGIN, CONFIG_SETTINGS_MARKER_END)
    cleaned = remove_marker_section(cleaned, CONFIG_MARKER_BEGIN, CONFIG_MARKER_END)

    settings_block = CONFIG_SETTINGS_MARKER_BEGIN + settings_section + CONFIG_SETTINGS_MARKER_END
    permissions_block = CONFIG_MARKER_BEGIN + permissions_section + CONFIG_MARKER_END
    parts = [settings_block.strip()]
    if cleaned:
        parts.append(cleaned)
    parts.append(permissions_block.strip())
    content = "\n\n".join(parts) + "\n"

    with open(path, "w") as f:
        f.write(content)


def collect_permissions(cfg):
    permissions = cfg.get("permissions", {})
    return {
        "allow": permissions.get("allow", []),
        "deny": permissions.get("deny", []),
        "ask": permissions.get("ask", []),
    }


def build_config_sections(perms, unsupported):
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

    settings_lines = []
    settings_lines.append("# Generated from Claude Code permissions.")
    settings_lines.append('default_permissions = "{}"'.format(PROFILE_NAME))
    if web_search:
        settings_lines.append('web_search = "{}"'.format(web_search))

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

    return "\n".join(settings_lines) + "\n", "\n".join(lines) + "\n"


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
    settings_section, permissions_section = build_config_sections(perms, unsupported)
    rules_section, rules_count = build_rules_section(perms, unsupported)

    os.makedirs(os.path.dirname(dst_config), exist_ok=True)
    os.makedirs(os.path.dirname(dst_rules), exist_ok=True)

    write_config(dst_config, settings_section, permissions_section)
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
    print("  rules: {}".format(dst_rules))
    print("  Bash rules: {}".format(rules_count))
    print("  Read deny rules: {}".format(read_deny_count))
    print("  Web rules: {}".format(web_count))
    print_unsupported(unsupported)


if __name__ == "__main__":
    main()
