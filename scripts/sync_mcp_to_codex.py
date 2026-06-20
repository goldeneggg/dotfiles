#!/usr/bin/env python3
import json, os, re, sys


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <source_mcp_json> <dest_config_toml>", file=sys.stderr)
        sys.exit(1)

    src = sys.argv[1]
    dst = sys.argv[2]

    with open(src) as f:
        cfg = json.load(f)

    servers = cfg.get("mcpServers", {})
    lines = []
    for name, srv in servers.items():
        lines.append("[mcp_servers.{}]".format(name))
        cmd_expanded = os.path.expandvars(srv.get("command", ""))
        cmd = os.path.basename(cmd_expanded) if cmd_expanded else srv.get("command", "")
        lines.append('command = "{}"'.format(cmd))
        args = srv.get("args", [])
        if args:
            args_toml = ", ".join('"{}"'.format(a) for a in args)
            lines.append("args = [{}]".format(args_toml))
        lines.append('env_vars = ["PATH"]')
        env = srv.get("env", {})
        if env:
            lines.append("[mcp_servers.{}.env]".format(name))
            for k, v in env.items():
                lines.append('{} = "{}"'.format(k, v))
        lines.append("")

    new_section = "\n".join(lines)
    marker_begin = "# sync-mcp-begin\n"
    marker_end = "# sync-mcp-end\n"

    existing = open(dst).read() if os.path.exists(dst) else ""
    cleaned = re.sub(
        r"\n*# sync-mcp-begin\n.*?# sync-mcp-end\n?", "", existing, flags=re.DOTALL
    ).strip()
    content = (cleaned + "\n\n" if cleaned else "") + marker_begin + new_section + marker_end

    with open(dst, "w") as f:
        f.write(content)

    print("Synced {} MCP servers to {}".format(len(servers), dst))
    for name in servers:
        print("  - " + name)


if __name__ == "__main__":
    main()
