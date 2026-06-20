#!/usr/bin/env python3
import glob, os, re, sys


def parse_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n?(.*)\Z", text, re.DOTALL)
    if not m:
        return None, ""
    return m.group(1), m.group(2)


def parse_fields(fm):
    lines = fm.split("\n")
    data = {}
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        m = re.match(r"^([A-Za-z_]+):\s?(.*)\Z", line)
        if not m or line[:1] == " ":
            i += 1
            continue
        key = m.group(1)
        val = m.group(2).strip()
        if val in ("|", "|-", "|+", ">", ">-", ">+"):
            i += 1
            raw = []
            while i < n:
                bl = lines[i]
                if bl.strip() == "":
                    raw.append("")
                    i += 1
                    continue
                if bl[:1] == " ":
                    raw.append(bl)
                    i += 1
                else:
                    break
            indents = [len(x) - len(x.lstrip(" ")) for x in raw if x.strip()]
            ind = min(indents) if indents else 0
            block = [(x[ind:] if len(x) >= ind else x) for x in raw]
            while block and block[-1] == "":
                block.pop()
            data[key] = "\n".join(block)
        else:
            if len(val) >= 2 and (
                (val[0] == '"' and val[-1] == '"') or (val[0] == "'" and val[-1] == "'")
            ):
                val = val[1:-1]
            data[key] = val
            i += 1
    return data


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <source_agents_dir> <dest_agents_dir>", file=sys.stderr)
        sys.exit(1)

    src_dir = sys.argv[1]
    dst_dir = sys.argv[2]

    for old in glob.glob(os.path.join(dst_dir, "*.toml")):
        os.remove(old)

    files = sorted(glob.glob(os.path.join(src_dir, "*.md")))
    count = 0
    for path in files:
        fname = os.path.basename(path)
        with open(path) as f:
            text = f.read()
        fm, body = parse_frontmatter(text)
        if fm is None:
            print("  ! skip {}: frontmatter not found".format(fname))
            continue
        fields = parse_fields(fm)
        name = fields.get("name", "").strip()
        desc = fields.get("description", "").strip()
        body = body.strip()
        if not name:
            print("  ! skip {}: missing name".format(fname))
            continue
        if not body:
            print("  ! skip {}: empty body (developer_instructions)".format(fname))
            continue
        if ("'''" in desc) or ("'''" in body):
            print(
                "  ! skip {}: contains triple single-quote, needs manual handling".format(fname)
            )
            continue
        out = []
        out.append('name = "{}"'.format(name))
        out.append("description = '''\n{}\n'''".format(desc))
        out.append("developer_instructions = '''\n{}\n'''".format(body))
        content = "\n".join(out) + "\n"
        dst = os.path.join(dst_dir, name + ".toml")
        with open(dst, "w") as f:
            f.write(content)
        print("  - {} -> {}".format(fname, dst))
        count += 1

    print("Synced {} subagents to {}".format(count, dst_dir))


if __name__ == "__main__":
    main()
