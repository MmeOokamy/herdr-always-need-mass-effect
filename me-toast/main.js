// me-toast: Herdr notifications with Glyph, the holographic drone, on the
// left. Selected by the "toast" key of the Mass Effect layouts; replaces the
// shipped "toast" mod and keeps what it does: a click runs the
// notification's action (show the agent) and closes it, Herdr closes it on
// its own after a few seconds, and a "needs login" notice offers to copy
// the command.
//
// Glyph's look follows the notification:
//   calm   blue          info, success, an agent that has finished
//   alert  orange        warning, an agent that needs you
//   error  orange, red lens
// The images (glyph/*.png) are rendered by tools/render_glyph.py.
//
// Frame and title colors follow the shown layout (props.style of me-hud).

import { View, div, image } from "gpui-kit";
import { v_flex, h_flex } from "gpui-base";
import { agents, closeOverlay, layout, props, run, theme } from "herdr";

const DIR = "mods/me-toast";
const TITLE_FONT = "Michroma";
const UI_FONT = "Chakra Petch";
const COLORS = {
  me1: { edge: "#4f9be0", title: "#cfe8ff" },
  me2: { edge: "#d8661f", title: "#ffbf6b" },
  me3: { edge: "#8a9bb0", title: "#e8eef5" },
};
const GLYPH = 48; // the toast is about 64 px high

function hudProps(node) {
  if (node?.content?.mod === "me-hud") return node.content.props;
  for (const child of node?.children ?? []) {
    const found = hudProps(child);
    if (found) return found;
  }
  return null;
}

// The agent the notification is about, from its action
// ({ name: "agent.focus", args: { terminal } } for Herdr's own).
function agentOf(p) {
  const args = p.action?.args ?? {};
  const keys = [args.terminal, args.address, args.agent, args.pane].filter(Boolean);
  if (!keys.length) return null;
  return (agents() ?? []).find((a) => keys.includes(a.address) || keys.includes(a.pane)) ?? null;
}

function stateOf(p, agent) {
  if (p.level === "error") return "error";
  if (p.level === "warning" || agent?.status === "blocked" || /needs you/i.test(p.title ?? "")) return "alert";
  return "calm";
}

export default class Toast extends View {
  init() {
    this.colors = COLORS[hudProps(layout())?.style] ?? COLORS.me2;
    this.copied = false;
  }

  render(cx) {
    const t = theme();
    const c = this.colors;
    const p = props() ?? {};
    const agent = agentOf(p);
    const state = stateOf(p, agent);
    const login = /^([a-z0-9][a-z0-9_.-]{0,31}) needs login; run hc machine login \1$/.exec(p.body ?? "");
    const command = login ? `hc machine login ${login[1]}` : null;
    // For an agent, its task (the title of its terminal) under the body.
    const task = agent?.title && agent.title !== p.body ? agent.title : null;

    return h_flex()
      .id("toast")
      .size_full()
      .pl(8)
      .pr(16)
      .gap(10)
      .items_center()
      .bg(t.popover)
      .border_1()
      .border_color(state === "calm" ? c.edge : t.blocked)
      .font_family(UI_FONT)
      .cursor_pointer()
      .hover((s) => s.bg(t.hover))
      .on_click(() => {
        if (p.action?.name) run(p.action.name, p.action.args ?? {});
        closeOverlay(p.overlay);
      })
      .child(image(`${DIR}/glyph/${state}.png`).w(GLYPH).h(GLYPH).flex_none())
      .child(
        v_flex()
          .flex_1()
          .min_w(0)
          .gap(1)
          .child(div().truncate().font_family(TITLE_FONT).text_size(11.5).text_color(c.title)
            .child(login ? `${login[1]} needs a login: run` : p.title ?? ""))
          .when(!login && Boolean(p.body), (el) => el.child(div().truncate().text_size(12.5).text_color(t.foreground).child(p.body ?? "")))
          .when(!login && Boolean(task), (el) => el.child(div().truncate().text_size(11.5).text_color(t.muted).child(task)))
          .when(Boolean(login), (el) => el.child(h_flex().gap(8).items_center()
            .child(div().flex_1().min_w(0).truncate().tooltip(command).text_size(12).text_color(t.muted).child(command))
            .child(div().id("toast-login-copy").flex_none().px(6).py(3).rounded(2).bg(t.raised)
              .text_size(12).text_color(t.foreground).cursor_pointer().hover((s) => s.bg(t.hover))
              .on_click((_e, cx) => { cx.stop_propagation(); cx.write_to_clipboard(command); this.copied = true; cx.notify(); })
              .child(this.copied ? "Copied" : "Copy")))),
      );
  }
}
