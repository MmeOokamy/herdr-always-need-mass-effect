#!/usr/bin/env python3
"""Installs the three Mass Effect layouts in Herdr, one per game:

- "mission-computer": the Mass Effect 2 pause menu (amber plates with
  pointed ends, dark room with holographic rings);
- "normandy-sr1": the Mass Effect 1 menus (blue plates with cut corners,
  deep blue console);
- "war-room": the Mass Effect 3 mission computer (steel plates with
  slanted ends and silver edges, dark steel room).

Each layout has its own theme; the "ME1" / "ME2" / "ME3" plates of the
title bar switch between them.

1. Links the me-hud, me-sessions and me-toast mods into ~/.config/herdr-app/mods
   (symbolic links: a change made here is picked up live) and checks them.
2. Copies each theme (me-hud/theme.json, theme-me1.json, theme-me3.json) to
   ~/.config/herdr-app/themes/<layout>.json: named like its layout, it is
   that layout's own.
3. Writes ~/.config/herdr-app/layouts/<layout>.json for all three (built by
   layout() below: edit it here, the files are rewritten on every install)
   and shows one: the one asked with --style, otherwise the one already
   shown, otherwise mission-computer.
4. Binds ctrl-shift-j (Claude sessions) in the "layout:<layout>" section of
   ~/.config/herdr-app/keys.json for every layout, if the key is free there.

The layouts use Herdr's own mods for the sidebar, tabs, panes and
notifications; me-hud draws the title bar and the "Resources" panel;
me-sessions lists the Claude Code sessions (the Normandy button); me-toast
shows the notifications, with Glyph the holographic drone.

Usage: python3 install.py [--lang fr|en] [--style me1|me2|me3]
       python3 install.py --uninstall
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HERDR = os.path.join(os.path.expanduser("~"), ".config", "herdr-app")
MOD = "me-hud"
MODS = (MOD, "me-sessions", "me-toast")
KEYS_FILE = os.path.join(HERDR, "keys.json")
# (key, action, role): added to each layout's section of keys.json only if
# the key is free there.
KEYBINDINGS = (("ctrl-shift-j", "mod.open:me-sessions", "sessions Claude"),)

# One entry per game: layout name, files of the me-hud mod, colors of the
# frames drawn by Herdr.
STYLES = {
    "me2": {
        "name": "mission-computer",
        "theme": "theme.json",
        "background": "img/bg.png",
        "preview": "preview.svg",
        "edge": "#a8481a",
        "panel": "#140b06d9",
        "pane": "#0c0705e6",
        "focus": "#9be35a",
    },
    "me1": {
        "name": "normandy-sr1",
        "theme": "theme-me1.json",
        "background": "img/bg-me1.png",
        "preview": "preview-me1.svg",
        "edge": "#2f6fb0",
        "panel": "#08121fd9",
        "pane": "#050b16e6",
        "focus": "#9fd4ff",
    },
    "me3": {
        "name": "war-room",
        "theme": "theme-me3.json",
        "background": "img/bg-me3.png",
        "preview": "preview-me3.svg",
        "edge": "#56667a",
        "panel": "#0b1016d9",
        "pane": "#080c11e6",
        "focus": "#5fb0ff",
    },
}
LAYOUTS = {key: s["name"] for key, s in STYLES.items()}


def layout_file(style):
    return os.path.join(HERDR, "layouts", f"{STYLES[style]['name']}.json")


def theme_file(style):
    return os.path.join(HERDR, "themes", f"{STYLES[style]['name']}.json")


def herdr(*args):
    result = subprocess.run(["herdr-app", *args], capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"herdr-app {' '.join(args)} : {result.stdout.strip()} {result.stderr.strip()}")
    return result.stdout


def shown_layout():
    try:
        return json.loads(herdr("status")).get("layout")
    except (ValueError, SystemExit):
        return None


def layout(style, lang):
    s = STYLES[style]
    edge, panel = s["edge"], s["panel"]
    hud = lambda role: {"mod": MOD, "props": {"role": role, "lang": lang, "style": style, "layouts": LAYOUTS}}
    return {
        "id": "root",
        "type": "column",
        "children": [
            {"id": "header", "type": "block", "size": {"px": 64}, "window_drag": True, "content": hud("title")},
            {"id": "body", "type": "row", "padding": [0, 12], "gap": 12, "resizable": False, "children": [
                {"id": "sidebar", "type": "column", "size": {"px": 268}, "min": 44, "max": 480,
                 "background": panel, "border": {"width": 1, "color": edge},
                 "children": [
                     {"id": "spaces", "type": "block", "content": {"mod": "spaces"},
                      "size": {"weight": 1}, "min": 90},
                     {"id": "agents", "type": "block", "content": {"mod": "agents"},
                      "size": {"weight": 1}, "min": 90},
                     {"id": "sidebar-footer", "type": "block",
                      "content": {"mod": "workspace-chrome", "props": {"footer": True}}, "size": {"px": 69}},
                 ]},
                {"id": "work", "type": "column", "resizable": False, "children": [
                    {"id": "tabs", "type": "block", "content": {"mod": "tabs"}, "size": {"px": 42},
                     "window_drag": True},
                    {"id": "work-body", "type": "row", "gap": 8, "children": [
                        {"id": "main", "type": "block", "content": {"tab": "active", "pane": {
                            "header": {"content": {"mod": "pane"}, "height": 30, "position": "top",
                                       "reveal": "always"},
                            "background": s["pane"],
                            "border": {"width": 1, "color": edge},
                            "focus": {"width": 2, "color": s["focus"]},
                            "radius": 0,
                            "gap": 10,
                            "lone": True,
                        }}},
                        {"id": "panel", "type": "column", "size": {"px": 368}, "min": 280, "max": 900,
                         "hidden": True, "background": panel, "border": {"width": 1, "color": edge},
                         "children": [
                             {"id": "panel-body", "type": "stack", "active": "files", "children": [
                                 {"id": "files", "type": "block", "content": {"mod": "files"}},
                                 {"id": "changes", "type": "block", "content": {"mod": "changes"}},
                             ]},
                         ]},
                    ]},
                ]},
            ]},
            {"id": "resources", "type": "block", "size": {"px": 124}, "content": hud("resources")},
        ],
        "background": {"image": f"mods/{MOD}/{s['background']}", "fit": "cover"},
        "theme": s["name"],
        "ui_font": "Chakra Petch",
        "terminal_padding": [14, 10],
        "terminal_opacity": 0.0,
        "titlebar": "none",
        "traffic_lights": [12, 22],
        "preview": f"mods/{MOD}/{s['preview']}",
        "toast": "me-toast",
    }


def read_keys():
    try:
        with open(KEYS_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {}
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def write_keys(data):
    temporary = KEYS_FILE + ".tmp"
    with open(temporary, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(temporary, KEYS_FILE)


def install_keys():
    """Shortcuts in each layout's section (it wins over "global" while the
    layout shows), without taking a key already bound there."""
    data = read_keys()
    if data is None:
        print(f"{KEYS_FILE} illisible : raccourcis non ajoutés")
        return
    changed = False
    for style in STYLES.values():
        section = data.setdefault(f"layout:{style['name']}", {})
        for key, action, role in KEYBINDINGS:
            if section.get(key) == action:
                continue
            if section.get(key) is not None:
                print(f"{key} est déjà pris dans {style['name']} ({section[key]}) : {role} sans raccourci")
                continue
            section[key] = action
            changed = True
            print(f"Raccourci ajouté : {key} ({role}, {style['name']})")
    if changed:
        write_keys(data)


def uninstall_keys():
    data = read_keys()
    if not data:
        return
    changed = False
    for style in STYLES.values():
        name = f"layout:{style['name']}"
        section = data.get(name)
        if not isinstance(section, dict):
            continue
        for key, action, _role in KEYBINDINGS:
            if section.get(key) == action:
                del section[key]
                changed = True
                print(f"Raccourci retiré : {key} ({style['name']})")
        if not section:
            del data[name]
            changed = True
    if changed:
        write_keys(data)


def link_mod(name):
    source = os.path.join(HERE, name)
    target = os.path.join(HERDR, "mods", name)
    if os.path.islink(target):
        if os.path.realpath(target) != source:
            sys.exit(f"{target} pointe déjà ailleurs : {os.readlink(target)}")
    elif os.path.exists(target):
        sys.exit(f"{target} existe déjà (pas un lien) : à retirer à la main")
    else:
        os.symlink(source, target)
        print(f"Mod relié : {target}")
    result = subprocess.run(["herdr-app", "check", target], capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"herdr-app check en échec ({name}) :\n{result.stdout}{result.stderr}")


def install(lang, style):
    for name in MODS:
        link_mod(name)
    source = os.path.join(HERE, MOD)

    for key, s in STYLES.items():
        theme = theme_file(key)
        os.makedirs(os.path.dirname(theme), exist_ok=True)
        shutil.copyfile(os.path.join(source, s["theme"]), theme)
        print(f"Thème : {theme}")
        path = layout_file(key)
        temporary = path + ".tmp"
        with open(temporary, "w", encoding="utf-8") as f:
            json.dump(layout(key, lang), f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(temporary, path)
        print(f"Layout : {path}")

    shown = shown_layout()
    ours = {s["name"]: key for key, s in STYLES.items()}
    if style is None:
        style = ours.get(shown, "me2")
    name = STYLES[style]["name"]
    # Herdr only reloads a mod when the layout changes: go through main
    # when one of the layouts is already shown, to load the new version.
    if shown in ours:
        herdr("do", "layout.switch", json.dumps({"name": "main"}))
    herdr("do", "layout.switch", json.dumps({"name": name}))
    print(f"Layout affiché : {name} (plaques ME1 / ME2 / ME3 de la barre de titre pour changer de jeu)")
    install_keys()


def uninstall():
    if shown_layout() in {s["name"] for s in STYLES.values()}:
        subprocess.run(["herdr-app", "do", "layout.switch", json.dumps({"name": "main"})], capture_output=True)
    for key in STYLES:
        for path, what in ((layout_file(key), "Layout"), (theme_file(key), "Thème")):
            if os.path.exists(path):
                os.unlink(path)
                print(f"{what} supprimé : {path}")
    for name in MODS:
        target = os.path.join(HERDR, "mods", name)
        if os.path.islink(target) and os.path.realpath(target) == os.path.join(HERE, name):
            os.unlink(target)
            print(f"Mod retiré : {target}")
    uninstall_keys()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--lang", choices=("fr", "en"), default="fr", help="langue des textes (défaut : fr)")
    parser.add_argument("--style", choices=tuple(STYLES), help="layout à afficher : me1, me2 ou me3")
    parser.add_argument("--uninstall", action="store_true")
    args = parser.parse_args()
    if args.uninstall:
        uninstall()
    else:
        install(args.lang, args.style)


if __name__ == "__main__":
    main()
