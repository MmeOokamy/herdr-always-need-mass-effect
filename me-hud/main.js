// me-hud: the chrome of the three Mass Effect layouts, after props.style:
//   me2  mission-computer: the Mass Effect 2 pause menu, glowing amber plates
//        with pointed ends over a dark room with holographic rings
//   me1  normandy-sr1: the Mass Effect 1 menus, blue plates with cut
//        corners over a deep blue console
//   me3  war-room: the Mass Effect 3 mission computer, steel plates with
//        slanted ends and silver edges over a dark steel room
// props.layouts maps each style to its layout: the "ME1" / "ME2" / "ME3"
// plates of the title bar switch between them, the shown one lit.
//
// One mod, two roles (props.role in the layout):
//   title      the top bar: sidebar, search and sessions (the Normandy,
//              opens the me-sessions mod) buttons, the shown space as
//              the screen title, the clock and the window buttons
//   resources  the bottom panel: agents by status, Claude Code usage,
//              spaces and tabs, like the "Resources" panel of the menu
//
// Usage figures come from ~/.cache/usage-cat/state.json when a Claude Code
// status line writes it (herdr-always-need-cats, herdr-always-need-archives,
// we-always-need-cats); without it they show "--".
// Texts follow props.lang ("fr" or "en", set by install.py).

import { View, div, svg, PathBuilder } from "gpui-kit";
import { h_flex, v_flex } from "gpui-base";
import { agents, home, layout, props, readTextFile, run, setShared, shared, spaces, theme } from "herdr";

const TITLE_FONT = "Michroma";
const UI_FONT = "Chakra Petch";

// The chamfered ends of a plate (left, right) and the outline of the
// resources panel, per style.
const STYLES = {
  me2: {
    plate: "#2a1508e6",
    plateHot: "#5a2a0ef0",
    edge: "#d8661f",
    edgeHot: "#ffb15c",
    text: "#ffbf6b",
    label: "#f2d9b8",
    value: "#ffd46b",
    line: "#ff8a2b55",
    green: "#9be35a",
    warn: "#ff9d3c",
    panel: "#1a0d06e0",
    leftEnd: [["100%", "0%"], ["0%", "36%"], ["0%", "64%"], ["100%", "100%"]],
    rightEnd: [["0%", "0%"], ["100%", "36%"], ["100%", "64%"], ["0%", "100%"]],
    // a trapezoid open at the bottom, like the menu's
    shape: [["2.5%", "22%"], ["97.5%", "22%"], ["100%", "100%"], ["0%", "100%"]],
    inner: [["0.6%", "100%"], ["3.1%", "30%"], ["96.9%", "30%"], ["99.4%", "100%"]],
  },
  me1: {
    plate: "#0d2a4ae6",
    plateHot: "#1d4f80f0",
    edge: "#4f9be0",
    edgeHot: "#9fd4ff",
    text: "#cfe8ff",
    label: "#bcdcff",
    value: "#e6f4ff",
    line: "#5aaaff44",
    green: "#7be05a",
    warn: "#f4d03f",
    panel: "#08162ae0",
    leftEnd: [["100%", "0%"], ["60%", "0%"], ["0%", "32%"], ["0%", "100%"], ["100%", "100%"]],
    rightEnd: [["0%", "0%"], ["100%", "0%"], ["100%", "68%"], ["40%", "100%"], ["0%", "100%"]],
    // a frame with its top corners cut, like the menus' panels
    shape: [["0%", "100%"], ["0%", "40%"], ["1.6%", "22%"], ["98.4%", "22%"], ["100%", "40%"], ["100%", "100%"]],
    inner: [["0.6%", "100%"], ["0.6%", "44%"], ["2.1%", "30%"], ["97.9%", "30%"], ["99.4%", "44%"], ["99.4%", "100%"]],
  },
  me3: {
    plate: "#1a2129e6",
    plateHot: "#1f4f7af0",
    edge: "#8a9bb0",
    edgeHot: "#8fcbff",
    text: "#e8eef5",
    label: "#c9d3df",
    value: "#ffffff",
    line: "#8fb4d844",
    green: "#7be05a",
    warn: "#e8a33a",
    panel: "#0b1118e0",
    leftEnd: [["100%", "0%"], ["45%", "0%"], ["0%", "50%"], ["45%", "100%"], ["100%", "100%"]],
    rightEnd: [["0%", "0%"], ["55%", "0%"], ["100%", "50%"], ["55%", "100%"], ["0%", "100%"]],
    // a band whose top slopes down at both ends, like the menu's
    shape: [["1%", "100%"], ["0%", "38%"], ["4%", "22%"], ["96%", "22%"], ["100%", "38%"], ["99%", "100%"]],
    inner: [["1.4%", "100%"], ["0.6%", "42%"], ["4.3%", "30%"], ["95.7%", "30%"], ["99.4%", "42%"], ["98.6%", "100%"]],
  },
};
const GAMES = ["me1", "me2", "me3"];
let C = STYLES.me2;

const TEXTS = {
  fr: {
    resources: "Ressources",
    working: "Agents au travail",
    blocked: "En attente",
    done: "Terminés",
    idle: "Au repos",
    session: "Session",
    week: "Semaine",
    spaces: "Espaces",
    tabs: "Onglets",
    search: "Rechercher",
    sessions: "Sessions Claude",
    sidebar: "Barre latérale",
    nothing: "Aucun espace",
    tab_count: (n) => `${n} onglet${n > 1 ? "s" : ""}`,
    next_blocked: "Afficher l'agent qui attend",
    switch_to: (n) => `Passer au thème Mass Effect ${n}`,
  },
  en: {
    resources: "Resources",
    working: "Agents working",
    blocked: "Waiting",
    done: "Done",
    idle: "Idle",
    session: "Session",
    week: "Week",
    spaces: "Spaces",
    tabs: "Tabs",
    search: "Search",
    sessions: "Claude sessions",
    sidebar: "Sidebar",
    nothing: "No space",
    tab_count: (n) => `${n} tab${n > 1 ? "s" : ""}`,
    next_blocked: "Show the waiting agent",
    switch_to: (n) => `Switch to the Mass Effect ${n} theme`,
  },
};

const POLL_MS = 2000;

// ---- drawing

/** A path through points ([x, y], px or "n%"), filled or stroked. */
function path(points, stroke) {
  let b = stroke ? PathBuilder.stroke(stroke) : PathBuilder.fill();
  b = b.move_to(points[0][0], points[0][1]);
  for (const [x, y] of points.slice(1)) b = b.line_to(x, y);
  return (stroke ? b : b.close()).build();
}

/** A layer filling its (relative) parent. */
function layer(p, color) {
  return window.paint_path(p, color).absolute().top(0).left(0).size_full();
}

function end(points, w, h, fill, edge) {
  return div().relative().flex_none().w(w).h(h)
    .child(layer(path(points), fill))
    .child(layer(path(points, 1.5), edge));
}

/**
 * A plate of the menu: a bar with chamfered ends, amber edges, the content
 * centred. `hot` lights it (hover, selection).
 */
function plate(id, content, { h = 30, w = null, cap = 12, hot = false, fill = null, edge = null } = {}) {
  const f = fill ?? (hot ? C.plateHot : C.plate);
  const e = edge ?? (hot ? C.edgeHot : C.edge);
  const middle = h_flex().h(h).flex_1().min_w(0).justify_center().items_center().gap(6)
    .bg(f).border_t(1.5).border_b(1.5).border_color(e).px(4).child(content);
  return h_flex().id(id).flex_none().h(h).when(w != null, (el) => el.w(w))
    .child(end(C.leftEnd, cap, h, f, e)).child(middle).child(end(C.rightEnd, cap, h, f, e));
}

/** A plate that acts: lights up on hover, and never starts a window drag. */
function button(view, id, content, action, options = {}) {
  const hot = view.hot === id;
  return plate(id, content, { ...options, hot })
    .cursor_pointer()
    .on_hover((hovered, cx) => {
      const next = hovered ? id : view.hot === id ? null : view.hot;
      if (next !== view.hot) { view.hot = next; cx.notify(); }
    })
    .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
    .on_click((_e, cx) => { cx.stop_propagation(); action(); })
    .when(Boolean(options.tooltip), (el) => el.tooltip(options.tooltip));
}

// ---- data

function find(node, id) {
  if (node?.id === id) return node;
  for (const child of node?.children ?? []) {
    const found = find(child, id);
    if (found) return found;
  }
  return null;
}

const narrow = () => (find(layout(), "sidebar")?.size?.px ?? Infinity) < 160;

// To the rail, or back to the width it had (as workspace-chrome does).
function toggleSidebar() {
  const width = find(layout(), "sidebar")?.size?.px;
  if (!narrow()) setShared("sidebar.width", width);
  setShared("sidebar.collapsed", !narrow());
  run("layout.resize", { id: "sidebar", px: narrow() ? (shared("sidebar.width") ?? 268) : 44 });
}

const two = (n) => String(n).padStart(2, "0");

export default class Hud extends View {
  init(p, cx) {
    const pr = props() ?? p ?? {};
    this.role = pr.role === "resources" ? "resources" : "title";
    this.style = STYLES[pr.style] ? pr.style : "me2";
    this.layouts = pr.layouts ?? {};
    this.text = TEXTS.fr;
    this.usage = null;
    this.hot = null;
    this.now = new Date();
    const lang = String(pr.lang ?? "fr").toLowerCase();
    if (TEXTS[lang]) this.text = TEXTS[lang];
    if (this.role === "resources") {
      cx.spawn(async (cx) => this.poll(cx));
      cx.timer.every(POLL_MS, (cx) => cx.spawn(async (cx) => this.poll(cx)));
    } else {
      cx.timer.every(5000, (cx) => {
        const now = new Date();
        if (now.getMinutes() !== this.now.getMinutes()) { this.now = now; cx.notify(); }
      });
    }
  }

  async poll(cx) {
    let usage = null;
    try {
      const data = JSON.parse((await readTextFile(`${home()}/.cache/usage-cat/state.json`)) ?? "null");
      const pct = (w) => {
        const v = data?.[w];
        if (!v || typeof v.pct !== "number") return null;
        // A window whose reset has passed is back to zero.
        if (typeof v.resets_at === "number" && v.resets_at * 1000 < Date.now()) return 0;
        return Math.round(v.pct);
      };
      usage = { session: pct("five_hour"), week: pct("seven_day") };
    } catch {
      usage = null;
    }
    if (JSON.stringify(usage) !== JSON.stringify(this.usage)) { this.usage = usage; cx.notify(); }
  }

  render(cx) {
    C = STYLES[this.style];
    return this.role === "resources" ? this.resources() : this.title();
  }

  // ---- title bar

  title() {
    const t = theme();
    const T = this.text;
    const all = spaces();
    const space = all.find((s) => s.active) ?? null;
    const tabs = space?.tabs?.length ?? 0;
    const sub = [space?.branch, space ? T.tab_count(tabs) : null].filter(Boolean).join("  ·  ");
    const icon = (path) => div().text_color(C.text).child(svg(path).size(14));
    const label = (s) => div().font_family(UI_FONT).font_semibold().text_size(13).text_color(C.label).child(s);

    const left = h_flex().flex_1().min_w(0).gap(8).items_center()
      .child(button(this, "sidebar", icon("mods/workspace-chrome/sidebar.svg"), toggleSidebar, { w: 50, tooltip: T.sidebar }))
      .when(!narrow(), (el) => el.child(button(this, "search", h_flex().gap(6).items_center()
        .child(icon("mods/workspace-chrome/search.svg")).child(label(T.search)), () => run("mod.open", { name: "picker" }), { w: 150 })))
      .child(button(this, "sessions", div().text_color(C.text).child(svg("mods/me-sessions/normandy.svg").size(18)),
        () => run("mod.open", { name: "me-sessions" }), { w: 56, tooltip: T.sessions }));

    // The window buttons are the tab bar's (shipped tabs mod): only the clock here.
    const clock = plate("clock", div().font_family(TITLE_FONT).text_size(12).text_color(C.value)
      .child(`${two(this.now.getHours())}:${two(this.now.getMinutes())}`), { w: 92 });
    // One plate per game: the shown one lit, the others switch to their layout.
    const games = h_flex().gap(4).items_center().children(GAMES.filter((g) => this.layouts[g]).map((g) => {
      const n = g.slice(2);
      const tag = div().font_family(TITLE_FONT).text_size(11).text_color(g === this.style ? C.value : C.text).child(`ME${n}`);
      return g === this.style
        ? plate(`game-${g}`, tag, { w: 64, hot: true })
        : button(this, `game-${g}`, tag, () => run("layout.switch", { name: this.layouts[g] }), { w: 64, tooltip: T.switch_to(n) });
    }));
    const right = h_flex().flex_1().min_w(0).gap(8).items_center().justify_end().child(games).child(clock);

    // The screen title, between two lines that end in chevrons.
    const rule = (points) => div().relative().w(70).h(20).flex_none().child(layer(path(points, 1.5), C.edge));
    const center = h_flex().flex_none().gap(10).items_center()
      .child(rule([["0%", "50%"], ["80%", "50%"], ["100%", "15%"]]))
      .child(v_flex().items_center().gap(1)
        .child(div().font_family(TITLE_FONT).text_size(19).text_color(C.text).whitespace_nowrap()
          .child(space?.name ?? T.nothing))
        .when(Boolean(sub), (el) => el.child(div().font_family(UI_FONT).font_medium().text_size(12).text_color(t.dim).child(sub))))
      .child(rule([["0%", "15%"], ["20%", "50%"], ["100%", "50%"]]));

    return h_flex().size_full().relative().px(12).gap(12).items_center()
      // a thin glowing rule across the whole bar, under everything
      .child(layer(path([["0%", "50%"], ["100%", "50%"]], 1), C.line))
      .child(left).child(center).child(right);
  }

  // ---- resources panel

  resources() {
    const t = theme();
    const T = this.text;
    const list = agents();
    const count = (st) => list.filter((a) => a.status === st).length;
    const n = { working: count("working"), blocked: count("blocked"), done: count("done"), idle: count("idle") };
    const all = spaces();
    const space = all.find((s) => s.active);
    // Michroma's % reads as "o/o": the sign is set in the UI font.
    const pct = (v) => (v == null ? "--" : h_flex().gap(3).items_baseline().child(String(v))
      .child(div().font_family(UI_FONT).font_semibold().text_size(13).child("%")));
    const level = (v) => (v == null ? C.value : v >= 95 ? t.blocked : v >= 80 ? C.warn : C.value);

    const row = (id, name, value, color, action, tip) => h_flex().id(id).h(19).gap(14).items_center()
      .child(div().w(150).text_right().font_family(UI_FONT).font_medium().text_size(14).text_color(C.label).child(name))
      .child(div().w(80).font_family(TITLE_FONT).text_size(12).text_color(color).child(value))
      .when(Boolean(action), (el) => el.cursor_pointer().rounded(3).hover((s) => s.bg(C.plateHot))
        .on_click(() => action()).tooltip(tip));
    const blocked = list.find((a) => a.status === "blocked");

    const leftCol = v_flex().gap(1)
      .child(row("working", T.working, String(n.working), n.working ? t.working : C.value))
      .child(row("blocked", T.blocked, String(n.blocked), n.blocked ? t.blocked : C.value,
        blocked ? () => run("pane.focus", { pane: blocked.pane }) : null, T.next_blocked))
      .child(row("done", T.done, String(n.done), n.done ? C.green : C.value))
      .child(row("idle", T.idle, String(n.idle), C.value));
    const rightCol = v_flex().gap(1)
      .child(row("session", T.session, pct(this.usage?.session), level(this.usage?.session)))
      .child(row("week", T.week, pct(this.usage?.week), level(this.usage?.week)))
      .child(row("spaces", T.spaces, String(all.length), C.value))
      .child(row("tabs", T.tabs, String(space?.tabs?.length ?? 0), C.value));

    const { shape, inner } = C;
    return div().size_full().relative().px(10)
      .child(div().absolute().top(0).left(10).right(10).bottom(0)
        .child(layer(path(shape), C.panel))
        .child(layer(path(shape, 1.5), C.edge))
        .child(layer(path(inner, 1), C.line)))
      .child(v_flex().size_full().relative().items_center().pb(8)
        .child(plate("title", div().font_family(TITLE_FONT).text_size(12).text_color(C.text).child(T.resources), { h: 26, w: 220, cap: 14 }))
        .child(h_flex().flex_1().gap(40).items_center().justify_center().child(leftCol).child(rightCol)));
  }
}
