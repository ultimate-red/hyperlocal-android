from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.properties import NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

from api import api, get_user_id
from widgets import DangerBtn, ErrLabel, FieldLabel, OutlineBtn, PrimaryBtn, StatusBadge, TopBar
from theme import BG, ERROR, PRIMARY, SUCCESS, TXT, TXT2, WHITE


class TaskDetailScreen(Screen):
    task_id = NumericProperty(0)

    def __init__(self, **kw):
        kw.setdefault("name", "task_detail")
        super().__init__(**kw)
        self._task = None
        self._from_screen = "task_list"
        self._build_shell()

    def _build_shell(self):
        self._root = BoxLayout(orientation="vertical")
        with self._root.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=self._root.pos, size=self._root.size)
        self._root.bind(
            pos=lambda i, v: setattr(self._bg, "pos", v),
            size=lambda i, v: setattr(self._bg, "size", v),
        )
        self._root.add_widget(TopBar(
            title="Task Details",
            on_back=lambda: setattr(self.manager, "current", self._from_screen),
            show_menu=False,
        ))
        self._scroll = ScrollView()
        self._body = BoxLayout(
            orientation="vertical",
            padding=[dp(16), dp(16)],
            spacing=dp(0),
            size_hint_y=None,
        )
        self._body.bind(minimum_height=self._body.setter("height"))
        self._scroll.add_widget(self._body)
        self._root.add_widget(self._scroll)

        # Pinned bottom bar — shown only when user can rate
        self._rate_bar = BoxLayout(
            orientation="vertical",
            size_hint_y=None, height=0,
            padding=[dp(16), dp(10), dp(16), dp(14)],
            spacing=dp(8),
        )
        self._rate_bar.bind(minimum_height=self._rate_bar.setter("height"))
        with self._rate_bar.canvas.before:
            Color(*BG)
            self._rate_bar_bg = Rectangle(pos=self._rate_bar.pos, size=self._rate_bar.size)
        self._rate_bar.bind(
            pos=lambda i, v: setattr(self._rate_bar_bg, "pos", v),
            size=lambda i, v: setattr(self._rate_bar_bg, "size", v),
        )
        self._root.add_widget(self._rate_bar)
        self.add_widget(self._root)

    def on_enter(self):
        self._load()

    def _load(self):
        self._body.clear_widgets()
        self._rate_bar.clear_widgets()
        self._rate_bar.height = 0
        self._body.add_widget(Label(text="Loading…", color=TXT2, font_size=sp(14),
                                    size_hint_y=None, height=dp(40)))
        api("GET", f"/tasks/{self.task_id}",
            on_success=self._render, on_error=self._show_err)

    @staticmethod
    def _wrap_lbl(text, color, font_size, min_h=dp(22), **kw):
        """Label that wraps and auto-sizes its height to fit the content."""
        lbl = Label(
            text=text, color=color, font_size=font_size,
            halign="left", valign="top", size_hint_y=None, height=min_h, **kw,
        )
        lbl.bind(
            width=lambda inst, w: setattr(inst, "text_size", (w, None)),
            texture_size=lambda inst, ts: setattr(inst, "height", max(ts[1], min_h)),
        )
        return lbl

    @staticmethod
    def _section_card(spacing=dp(8), padding=None):
        """White rounded card with subtle shadow — groups related content."""
        pad = padding if padding is not None else [dp(16), dp(14)]
        box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=pad,
            spacing=spacing,
        )
        box.bind(minimum_height=box.setter("height"))
        with box.canvas.before:
            Color(0, 0, 0, 0.055)
            _sh = RoundedRectangle(
                pos=(box.x + dp(1), box.y - dp(2)), size=box.size, radius=[dp(12)]
            )
            Color(1, 1, 1, 1)
            _bg = RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(12)])
        box.bind(
            pos=lambda i, v: (
                setattr(_sh, "pos", (v[0] + dp(1), v[1] - dp(2))),
                setattr(_bg, "pos", v),
            ),
            size=lambda i, v: (setattr(_sh, "size", v), setattr(_bg, "size", v)),
        )
        return box

    @staticmethod
    def _fmt_time(iso_str):
        if not iso_str:
            return ""
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(str(iso_str).replace("Z", "+00:00"))
            return dt.strftime("%d %b, %H:%M")
        except Exception:
            return ""

    @staticmethod
    def _divider():
        d = Widget(size_hint_y=None, height=dp(1))
        with d.canvas:
            Color(0.88, 0.88, 0.90, 1)
            _r = Rectangle(pos=d.pos, size=d.size)
        d.bind(
            pos=lambda inst, v: setattr(_r, "pos", v),
            size=lambda inst, v: setattr(_r, "size", v),
        )
        return d

    @staticmethod
    def _info_row(label, value, val_color=None):
        _ROW_H = dp(28)
        _LBL_W = dp(130)
        _VAL_W = dp(162)
        row = BoxLayout(
            orientation="horizontal",
            size_hint=(None, None),
            size=(_LBL_W + dp(8) + _VAL_W, _ROW_H),
            spacing=dp(8),
        )
        lbl = Label(
            text=label, color=TXT2, font_size=sp(13),
            size_hint=(None, 1), width=_LBL_W,
            halign="left", valign="middle",
            text_size=(_LBL_W, None),
        )
        val = Label(
            text=value, color=val_color if val_color is not None else TXT,
            font_size=sp(16),
            size_hint=(None, None), width=_VAL_W, height=_ROW_H,
            halign="left", valign="top",
            text_size=(_VAL_W, None),
        )

        def _upd(inst, ts):
            h = max(ts[1], _ROW_H)
            inst.height = h
            row.height = h

        val.bind(texture_size=_upd)
        row.add_widget(lbl)
        row.add_widget(val)
        return row

    def _render(self, task):
        self._task = task
        b = self._body
        b.clear_widgets()

        task_type    = task.get("task_type", "request")
        task_status  = task.get("status", "")
        display_status = "deleted" if task.get("hidden_from_creator") else task_status
        reward  = task.get("reward")
        creator = task.get("creator_name") or str(task.get("created_by", ""))

        # ── Structured detail card ─────────────────────────────────────────
        card = self._section_card(spacing=dp(0), padding=[dp(14), dp(14)])

        # Title + badge row — row height follows the title height
        badge = StatusBadge(status=display_status)
        title_row = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(8))
        title_lbl = Label(
            text=task.get("title", ""),
            color=TXT, font_size=sp(17), bold=True,
            halign="left", valign="top",
            size_hint=(1, None), height=dp(28),
        )

        def _title_width(inst, w):
            inst.text_size = (w, None)

        def _title_texture(inst, ts):
            h = max(ts[1], dp(28))
            inst.height = h
            title_row.height = max(h, badge.height)

        title_lbl.bind(width=_title_width, texture_size=_title_texture)
        title_row.add_widget(title_lbl)
        title_row.add_widget(badge)
        card.add_widget(title_row)

        # Description
        desc = task.get("description")
        if desc:
            card.add_widget(Widget(size_hint_y=None, height=dp(8)))
            d = Label(
                text=desc, color=TXT2, font_size=sp(15),
                halign="left", valign="top",
                size_hint_y=None, height=dp(20),
            )
            d.bind(
                width=lambda inst, w: setattr(inst, "text_size", (w, None)),
                texture_size=lambda inst, ts: setattr(inst, "height", max(ts[1], dp(20))),
            )
            card.add_widget(d)

        # Divider + info rows
        card.add_widget(Widget(size_hint_y=None, height=dp(12)))
        card.add_widget(self._divider())
        card.add_widget(Widget(size_hint_y=None, height=dp(12)))

        info_items = []
        type_color = ERROR if task_type == "offer" else SUCCESS
        info_items.append(("Type", "Offer" if task_type == "offer" else "Request", type_color))
        if reward is not None:
            price_label  = "Price Charged" if task_type == "offer" else "Price Offered"
            reward_color = ERROR if task_type == "offer" else SUCCESS
            info_items.append((price_label, f"₹{reward:g}", reward_color))
        info_items.append(("Posted by", creator, TXT))
        if task.get("accepted_by"):
            acc = task.get("acceptor_name") or str(task["accepted_by"])
            info_items.append(("Accepted by", acc, TXT))
        if task.get("created_at"):
            info_items.append(("Posted on", self._fmt_time(task["created_at"]), TXT2))
        if task_status == "accepted" and task.get("updated_at"):
            info_items.append(("Accepted on", self._fmt_time(task["updated_at"]), TXT2))
        elif task_status == "completed" and task.get("updated_at"):
            info_items.append(("Completed on", self._fmt_time(task["updated_at"]), SUCCESS))
        elif task_status == "aborted" and task.get("updated_at"):
            info_items.append(("Aborted on", self._fmt_time(task["updated_at"]), ERROR))

        h_scroll = ScrollView(
            do_scroll_x=True, do_scroll_y=False,
            size_hint=(1, None), height=dp(28),
            bar_width=dp(3),
            bar_color=[0.72, 0.72, 0.74, 0.9],
            bar_inactive_color=[0.72, 0.72, 0.74, 0.3],
            scroll_type=['bars', 'content'],
        )
        info_col = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            width=dp(300), height=dp(28),
            spacing=dp(12),
        )
        info_col.bind(minimum_height=info_col.setter("height"))
        info_col.bind(height=lambda _, h: setattr(h_scroll, "height", h + dp(4)))
        for lbl_txt, val_txt, col in info_items:
            info_col.add_widget(self._info_row(lbl_txt, val_txt, col))
        h_scroll.add_widget(info_col)
        card.add_widget(h_scroll)

        # Abort reason
        if task.get("abort_reason"):
            acc_name = task.get("acceptor_name") or "acceptor"
            card.add_widget(Widget(size_hint_y=None, height=dp(12)))
            card.add_widget(self._divider())
            card.add_widget(Widget(size_hint_y=None, height=dp(8)))
            ar = Label(
                text="Abort Reason", color=ERROR, font_size=sp(13),
                halign="left", valign="middle",
                size_hint_y=None, height=dp(20),
            )
            ar.bind(size=ar.setter("text_size"))
            card.add_widget(ar)
            card.add_widget(self._wrap_lbl(
                f"{acc_name}: {task['abort_reason']}", ERROR, sp(14), min_h=dp(20),
            ))

        b.add_widget(card)

        # ── Deleted notice ─────────────────────────────────────────────────
        if task.get("hidden_from_creator"):
            notice = self._section_card(padding=[dp(14), dp(12)])
            notice.add_widget(Label(
                text="This task was removed by the creator.",
                color=TXT2, font_size=sp(13), bold=True,
                size_hint_y=None, height=dp(32),
            ))
            b.add_widget(Widget(size_hint_y=None, height=dp(16)))
            b.add_widget(notice)
            uid = get_user_id()
            if task.get("accepted_by") == uid:
                self._action_err = ErrLabel(text="")
                rem = DangerBtn(text="Remove Task")
                rem.bind(on_press=self._remove)
                b.add_widget(Widget(size_hint_y=None, height=dp(16)))
                b.add_widget(rem)
                b.add_widget(self._action_err)
            b.add_widget(Widget(size_hint_y=None, height=dp(24)))
            self._load_review_status(task)
            return

        # ── Actions (full-width, below card) ───────────────────────────────
        uid         = get_user_id()
        is_creator  = task.get("created_by")  == uid
        is_acceptor = task.get("accepted_by") == uid
        self._action_err = ErrLabel(text="", size_hint_y=None, height=0)
        err_in_bar = False

        b.add_widget(Widget(size_hint_y=None, height=dp(8)))

        if task_status == "open" and not is_creator:
            btn_text = "Hire" if task_type == "offer" else "Accept Task"
            btn = PrimaryBtn(text=btn_text)
            btn.bind(on_press=self._accept)
            self._rate_bar.add_widget(btn)
            self._rate_bar.add_widget(self._action_err)
            err_in_bar = True

        if task_status == "accepted" and is_acceptor:
            self._abort_expanded = False
            complete_btn = PrimaryBtn(text="Mark as Completed")
            complete_btn.bind(on_press=self._complete)
            abort_btn = DangerBtn(text="Abort Task")
            abort_btn.bind(on_press=lambda *_, b=abort_btn: self._show_abort_form(b))
            self._rate_bar.add_widget(complete_btn)
            self._rate_bar.add_widget(abort_btn)
            self._rate_bar.add_widget(self._action_err)
            err_in_bar = True

        if is_creator and task_status == "aborted":
            b.add_widget(Widget(size_hint_y=None, height=dp(8)))
            btn = PrimaryBtn(text="Repost as New Task")
            btn.bind(on_press=self._repost)
            b.add_widget(btn)

        if is_creator and task_status not in ("completed", "aborted"):
            rem = DangerBtn(text="Remove Task")
            rem.bind(on_press=self._remove)
            b.add_widget(rem)

        if not err_in_bar:
            b.add_widget(self._action_err)
        b.add_widget(Widget(size_hint_y=None, height=dp(8)))
        self._load_review_status(task)

    def _show_abort_form(self, trigger_btn):
        if self._abort_expanded:
            return
        self._abort_expanded = True
        trigger_btn.disabled = True

        form = self._section_card(spacing=dp(10))
        form.add_widget(FieldLabel("Reason for aborting (required)"))
        self._abort_input = TextInput(
            hint_text="Explain why you are aborting…",
            background_normal="", background_active="", background_color=WHITE,
            foreground_color=TXT, cursor_color=PRIMARY,
            hint_text_color=(0.55, 0.55, 0.55, 1),
            size_hint_y=None, height=dp(80),
            padding=[dp(12), dp(10)], font_size=sp(13), multiline=True,
        )
        form.add_widget(self._abort_input)
        # Error label sits above the confirm button so it is always visible
        self._abort_err = ErrLabel(text="")
        form.add_widget(self._abort_err)
        confirm = DangerBtn(text="Confirm Abort")
        confirm.bind(on_press=self._abort)
        form.add_widget(confirm)
        self._body.add_widget(form)
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: setattr(self._scroll, "scroll_y", 0), 0.15)

    # ── Actions ────────────────────────────────────────────────────────────────

    def _accept(self, *_):
        api("POST", f"/tasks/{self.task_id}/accept",
            on_success=self._render, on_error=self._action_err_cb)

    def _complete(self, *_):
        api("POST", f"/tasks/{self.task_id}/complete",
            on_success=self._render, on_error=self._action_err_cb)

    def _abort(self, *_):
        reason = self._abort_input.text.strip()
        if not reason:
            self._abort_err.text = "Please enter a reason before aborting."
            return
        self._abort_err.text = ""
        api("POST", f"/tasks/{self.task_id}/abort",
            body={"reason": reason},
            on_success=self._render, on_error=self._abort_err_cb)

    def _abort_err_cb(self, error):
        if hasattr(self, "_abort_err"):
            self._abort_err.text = str(error)

    def _repost(self, *_):
        api("POST", f"/tasks/{self.task_id}/repost",
            on_success=self._reposted, on_error=self._action_err_cb)

    def _reposted(self, new_task):
        self.task_id = new_task["id"]
        self._render(new_task)

    def _remove(self, *_):
        api("DELETE", f"/tasks/{self.task_id}",
            on_success=self._removed, on_error=self._action_err_cb)

    def _removed(self, _):
        if self.manager and self.manager.current == "task_detail":
            self.manager.current = "my_tasks"

    def _action_err_cb(self, error):
        if hasattr(self, "_action_err"):
            self._action_err.text = str(error)
            self._action_err.height = dp(28)

    # ── Reviews ───────────────────────────────────────────────────────────────

    def _load_review_status(self, task):
        uid        = get_user_id()
        status     = task.get("status", "")
        is_creator  = task.get("created_by")  == uid
        is_acceptor = task.get("accepted_by") == uid
        hidden      = task.get("hidden_from_creator", False)

        creator_can  = (
            is_creator and status in ("completed", "aborted") and task.get("accepted_by")
        )
        acceptor_can = is_acceptor and (status in ("completed", "aborted") or hidden)

        if not creator_can and not acceptor_can:
            return

        reviewee_name = (
            task.get("acceptor_name") or "the doer"
            if is_creator else
            task.get("creator_name") or "the creator"
        )
        api(
            "GET", f"/tasks/{self.task_id}/my-review",
            on_success=lambda d: self._show_review_ui(task, d, reviewee_name),
            on_error=lambda _e: None,
        )

    def _show_review_ui(self, task, existing, reviewee_name):
        b = self._body
        review = self._section_card(spacing=dp(10))

        if existing:
            done = Label(
                text=f"You rated {reviewee_name}: {existing['rating']}/5",
                color=PRIMARY, font_size=sp(14), bold=True,
                size_hint_y=None, height=dp(36),
                halign="left", valign="middle",
            )
            done.bind(size=done.setter("text_size"))
            review.add_widget(done)
            if existing.get("comment"):
                note = Label(
                    text=f'"{existing["comment"]}"',
                    color=TXT2, font_size=sp(12),
                    size_hint_y=None, height=dp(24),
                    halign="left", valign="middle",
                )
                note.bind(size=note.setter("text_size"))
                review.add_widget(note)
        else:
            rate_btn = OutlineBtn(text=f"Rate {reviewee_name}")
            rate_btn.bind(on_press=lambda *_: self._go_rate(reviewee_name))
            self._rate_bar.add_widget(rate_btn)
            self._rate_bar.add_widget(ErrLabel(text=""))
            # btn(44) + spacing(4) + ErrLabel(28) + pad_top(10) + pad_bottom(14)
            self._rate_bar.height = dp(100)
            return

        b.add_widget(review)

    def _go_rate(self, reviewee_name):
        if not self.manager:
            return
        rate_screen = self.manager.get_screen("rate_user")
        rate_screen.task_id = self.task_id
        rate_screen.reviewee_name = reviewee_name
        rate_screen._from_screen = "task_detail"
        self.manager.current = "rate_user"

    def _show_err(self, error):
        b = self._body
        b.clear_widgets()
        b.add_widget(Label(text=f"Error: {error}", color=ERROR, font_size=sp(14),
                           size_hint_y=None, height=dp(40)))
        retry = PrimaryBtn(text="Retry")
        retry.bind(on_press=lambda *_: self._load())
        b.add_widget(retry)
