# my_pocket_pos.py
# MY POCKET POS — Lite with offline upgrades (codes / license file)
# Workflow, logic, and UI preserved. New Sale has NO pay buttons (they’re upgrades).

# ------------------------------- Imports -------------------------------

import os, json, csv, webbrowser
from datetime import datetime
from urllib.parse import quote_plus

from kivy.app import App
from kivy.metrics import dp, sp
from kivy.core.window import Window
from kivy.core.clipboard import Clipboard
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.behaviors import ButtonBehavior

# Keep keyboard from covering inputs
Window.softinput_mode = "below_target"

# ------------------------------- Paths (with fallback) -----------------
# IMPORTANT: We don't create folders at import time (that can crash on Android 11+).
# We set them at app start via init_storage().

APP_DIR = None
IMPORT_DIR = None
INV_JSON = None
SALES_JSON = None
UP_JSON = None
LICENSE_TXT = None

def _set_paths(base_dir):
    """Set global paths based on a chosen base directory."""
    global APP_DIR, IMPORT_DIR, INV_JSON, SALES_JSON, UP_JSON, LICENSE_TXT
    APP_DIR = base_dir
    IMPORT_DIR = os.path.join(APP_DIR, "imports")
    INV_JSON   = os.path.join(APP_DIR, "inventory.json")
    SALES_JSON = os.path.join(APP_DIR, "sales_log.json")
    UP_JSON    = os.path.join(APP_DIR, "upgrades.json")
    LICENSE_TXT = os.path.join(IMPORT_DIR, "license.txt")

def init_storage(app_instance):
    """
    Try external shared storage first (your preferred path):
      /storage/emulated/0/projects/My Pocket Pos/App
    If that fails (scoped storage / permissions), fall back to app-private dir:
      app_instance.user_data_dir/App
    Returns the base path actually used.
    """
    # Preferred external path
    ext_base = os.path.join("/storage/emulated/0", "projects", "My Pocket Pos", "App")
    try:
        os.makedirs(os.path.join(ext_base, "imports"), exist_ok=True)
        _set_paths(ext_base)
        return ext_base
    except Exception:
        # Private, always-writable path
        priv_base = os.path.join(app_instance.user_data_dir, "App")
        try:
            os.makedirs(os.path.join(priv_base, "imports"), exist_ok=True)
        except Exception:
            pass
        _set_paths(priv_base)
        return priv_base

# ------------------------------ Helpers --------------------------------

def toast(msg, title="Notice", w=.92, h=.40):
    lbl = Label(text=msg, halign="left", valign="top", padding=(dp(10), dp(10)))
    lbl.bind(size=lambda i, *_: setattr(i, "text_size", (i.width - dp(20), i.height - dp(20))))
    pop = Popup(title=title, content=lbl, size_hint=(w, h))
    pop.open()
    return pop

def confirm(msg, title="Confirm", on_yes=None, on_no=None):
    box = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
    lbl = Label(text=msg, halign="left", valign="top")
    lbl.bind(size=lambda i, *_: setattr(i, "text_size", (i.width, None)))
    row = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(48))
    yes = Button(text="Yes"); no = Button(text="No")
    row.add_widget(yes); row.add_widget(no)
    box.add_widget(lbl); box.add_widget(row)
    pop = Popup(title=title, content=box, size_hint=(.9, .4))
    if on_yes: yes.bind(on_release=lambda *_: (on_yes(), pop.dismiss()))
    else:      yes.bind(on_release=pop.dismiss)
    if on_no:  no.bind(on_release=lambda *_: (on_no(), pop.dismiss()))
    else:      no.bind(on_release=pop.dismiss)
    pop.open()
    return pop

def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("SAVE JSON ERROR:", e)

def to_float(x):
    try:
        return float(str(x).replace("$", "").replace(",", "").strip() or 0)
    except Exception:
        return 0.0

def money(x):
    try:
        return f"${float(x):.2f}"
    except Exception:
        return "$0.00"

def header_box():
    """App header: 'My Pocket POS' (leave as-is)."""
    box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(96))
    t1 = Label(text="[b]My Pocket POS[/b]", markup=True,
               font_size=sp(34), size_hint_y=None, height=dp(60),
               halign="center", valign="middle")
    t1.bind(size=lambda i, *_: setattr(i, "text_size", (i.width, None)))
    t2 = Label(text="", size_hint_y=None, height=dp(4))
    box.add_widget(t1); box.add_widget(t2)
    return box

def page_title(text):
    box = BoxLayout(size_hint_y=None, height=dp(64), padding=[0, dp(8), 0, 0])
    lbl = Label(text=f"[b]{text}[/b]", markup=True, font_size=sp(28),
                size_hint_y=None, height=dp(56),
                halign="center", valign="middle")
    lbl.bind(size=lambda i, *_: setattr(i, "text_size", (i.width, None)))
    box.add_widget(lbl)
    return box

# --------------------------- Offline Upgrades ---------------------------

DEFAULT_UP = {"payments": False, "impexp": False, "reports": False, "scanner": False}

def load_upgrades():
    data = load_json(UP_JSON, None)
    if not isinstance(data, dict):
        data = DEFAULT_UP.copy()
        save_json(UP_JSON, data)
    merged = DEFAULT_UP.copy()
    merged.update({k: bool(v) for k, v in (data or {}).items() if k in DEFAULT_UP})
    if merged != data:
        save_json(UP_JSON, merged)
    return merged

def save_upgrades(flags):
    clean = DEFAULT_UP.copy()
    clean.update({k: bool(v) for k, v in (flags or {}).items() if k in DEFAULT_UP})
    save_json(UP_JSON, clean)
    return clean

def unlock_from_code(code: str):
    code = (code or "").strip().upper()
    flags = load_upgrades()
    MAP = {
        "PRO_ALL":    ["payments", "impexp", "reports", "scanner"],
        "PRO_PAY":    ["payments"],
        "PRO_IMPEXP": ["impexp"],
        "PRO_REPORT": ["reports"],
        "PRO_SCAN":   ["scanner"],
    }
    key = code.split("-")[0]
    if key in MAP:
        for f in MAP[key]:
            flags[f] = True
        save_upgrades(flags)
        return True, flags
    return False, flags

def unlock_from_license_file():
    if not os.path.exists(LICENSE_TXT):
        return False, "license.txt not found"
    try:
        with open(LICENSE_TXT, "r", encoding="utf-8") as f:
            content = f.read()
        tokens = [t.strip() for t in content.replace(",", "\n").splitlines() if t.strip()]
        ok = False
        last_flags = None
        for t in tokens:
            did, last_flags = unlock_from_code(t)
            ok = ok or did
        if ok:
            return True, "License applied"
        return False, "No valid codes in license.txt"
    except Exception as e:
        return False, f"Read error: {e}"

def unlocked_text(flags=None):
    f = flags or load_upgrades()
    on = [k for k, v in f.items() if v]
    return "Unlocked: " + (", ".join(on) if on else "none")

# --------------------------- Clickable Row ------------------------------

class ClickRow(ButtonBehavior, GridLayout):
    """Grid row that can be tapped to select."""
    pass

# ------------------------------- Screens --------------------------------

class HomeScreen(Screen):
    """Header kept as 'My Pocket POS'.
    Middle of screen: one row with 2 buttons (Inventory, New Sale)
    then a single long Upgrades button. Professional sizes.
    """
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(16))
        root.add_widget(header_box())

        spacer_top = Label(size_hint_y=None, height=dp(40))
        root.add_widget(spacer_top)

        # Buttons centered vertically
        mid = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(200), spacing=dp(12))
        row = GridLayout(cols=2, spacing=dp(12), size_hint_y=None, height=dp(56))
        inv_btn  = Button(text="Inventory", size_hint_y=None, height=dp(56))
        sale_btn = Button(text="New Sale", size_hint_y=None, height=dp(56))
        inv_btn.bind(on_release=lambda *_: self.manager.transition_to("inventory"))
        sale_btn.bind(on_release=lambda *_: self.manager.transition_to("sale"))
        row.add_widget(inv_btn); row.add_widget(sale_btn)
        mid.add_widget(row)

        up_btn = Button(text="Upgrades", size_hint_y=None, height=dp(56))
        up_btn.bind(on_release=lambda *_: self.manager.transition_to("upgrades"))
        mid.add_widget(up_btn)
        root.add_widget(mid)

        root.add_widget(Label())  # stretch spacer
        self.add_widget(root)

# ------------------------------ Inventory ------------------------------

class InventoryScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.inv = []

        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        root.add_widget(page_title("INVENTORY"))

        actions = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(50))
        add_btn = Button(text="Add Item")
        del_btn = Button(text="Delete All")
        actions.add_widget(add_btn); actions.add_widget(del_btn)
        root.add_widget(actions)

        add_btn.bind(on_release=lambda *_: self.add_item_popup())
        del_btn.bind(on_release=lambda *_: self.delete_all())

        header = self._mk_header()

        self.list_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(2), padding=[dp(6), 0])
        self.list_box.bind(minimum_height=lambda inst, val: setattr(inst, "height", val))
        scroller = ScrollView(); scroller.add_widget(self.list_box)

        back = Button(text="Back", size_hint_y=None, height=dp(56))
        back.bind(on_release=lambda *_: self.manager.transition_to("home"))

        root.add_widget(header)
        root.add_widget(scroller)
        root.add_widget(back)

        self.add_widget(root)

    # Table helpers
    def _cell(self, text, weight=1, align="left", bold=False):
        lbl = Label(text=f"[b]{text}[/b]" if bold else text, markup=True,
                    halign=align, valign="middle",
                    shorten=True, shorten_from="right",
                    size_hint_x=weight, size_hint_y=None, height=dp(34),
                    font_size=sp(18))
        lbl.bind(size=lambda inst, *_: setattr(inst, "text_size", (inst.width, None)))
        return lbl

    def _mk_header(self):
        h = BoxLayout(orientation="horizontal", spacing=dp(6),
                      size_hint_y=None, height=dp(36), padding=[dp(8), 0])
        h.add_widget(self._cell("Name", .68, "left", True))
        h.add_widget(self._cell("Price", .18, "right", True))
        h.add_widget(self._cell("Qty", .14, "right", True))
        return h

    def _add_row(self, name, price, qty):
        row = BoxLayout(orientation="horizontal", spacing=dp(6),
                        size_hint_y=None, height=dp(34), padding=[dp(8), 0])
        row.add_widget(self._cell(name, .68, "left"))
        row.add_widget(self._cell(price, .18, "right"))
        row.add_widget(self._cell(qty, .14, "right"))
        self.list_box.add_widget(row)

    def on_pre_enter(self, *a):
        self.inv = load_json(INV_JSON, [])
        self.refresh_table()

    def refresh_table(self):
        self.list_box.clear_widgets()
        for it in self.inv:
            self._add_row(it.get("name", ""), money(it.get("price", 0)), str(int(it.get("qty", 0))))

    def add_item_popup(self):
        box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(10))
        name  = TextInput(hint_text="Name",  multiline=False, size_hint_y=None, height=dp(48))
        price = TextInput(hint_text="Price (e.g. 2.50)", input_filter="float",
                          multiline=False, size_hint_y=None, height=dp(48))
        qty   = TextInput(hint_text="Qty", input_filter="int",
                          multiline=False, size_hint_y=None, height=dp(48))
        row = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(48))
        ok, cancel = Button(text="Save"), Button(text="Cancel")
        row.add_widget(ok); row.add_widget(cancel)
        box.add_widget(name); box.add_widget(price); box.add_widget(qty); box.add_widget(row)
        pop = Popup(title="Add Inventory", content=box,
                    size_hint=(None, None), size=(dp(360), dp(300)), pos_hint={"top": 0.98})
        cancel.bind(on_release=pop.dismiss)

        def save_item(*_):
            n = name.text.strip()
            if not n:
                return
            p = to_float(price.text)
            q = int(to_float(qty.text))
            self.inv.append({"name": n, "price": p, "qty": q})
            save_json(INV_JSON, self.inv)
            self.refresh_table()
            pop.dismiss()

        ok.bind(on_release=save_item)
        pop.open()

    def delete_all(self):
        self.inv = []
        save_json(INV_JSON, self.inv)
        self.refresh_table()
        toast("All inventory deleted.", "Inventory", .6, .28)

# ------------------------------- New Sale -------------------------------

class SaleScreen(Screen):
    """Cart/Qty/Spinner workflow; Clear Cart; Cash + History/Back. NO pay buttons."""
    def __init__(self, **kw):
        super().__init__(**kw)
        self.inv = []
        self.cart = []
        self.subtotal = 0.0

        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        root.add_widget(page_title("NEW SALE"))

        # Row: item spinner + search + qty
        top = GridLayout(cols=3, spacing=dp(8), size_hint_y=None, height=dp(52))
        self.item_spinner = Spinner(text="Select item")
        search_btn = Button(text="Search")
        self.qty_input = TextInput(text="1", input_filter="int", halign="center")
        top.add_widget(self.item_spinner); top.add_widget(search_btn); top.add_widget(self.qty_input)

        # Add/Clear row
        add_btn = Button(text="Add to Cart", size_hint_y=None, height=dp(50))
        clear_btn = Button(text="Clear Cart", size_hint_y=None, height=dp(50))
        add_row = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(50))
        add_row.add_widget(add_btn); add_row.add_widget(clear_btn)

        # Subtotal
        self.sub_lbl = Label(text="Subtotal: $0.00", font_size=sp(32),
                             size_hint_y=None, height=dp(46),
                             halign="center", valign="middle")
        self.sub_lbl.bind(size=lambda i, *_: setattr(i, "text_size", (i.width, None)))

        # Cart header + list
        hdr = GridLayout(cols=4, size_hint_y=None, height=dp(32), padding=[dp(6), 0], spacing=dp(6))
        for title, w in (("Item", .56), ("Price", .16), ("Qty", .12), ("Total", .16)):
            lbl = Label(text=f"[b]{title}[/b]", markup=True, size_hint_x=w, size_hint_y=None, height=dp(32))
            lbl.bind(size=lambda i, *_: setattr(i, "text_size", (i.width, None)))
            hdr.add_widget(lbl)

        self.cart_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(2), padding=[dp(6), 0])
        self.cart_box.bind(minimum_height=lambda inst, val: setattr(inst, "height", val))
        scroller = ScrollView(); scroller.add_widget(self.cart_box)

        # Bottom: Cash (long) then History/Back row (two buttons)
        cash_btn = Button(text="Cash", size_hint_y=None, height=dp(56))
        bottom = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(56))
        hist_btn = Button(text="History")
        back_btn = Button(text="Back")
        bottom.add_widget(hist_btn); bottom.add_widget(back_btn)

        # Bindings
        add_btn.bind(on_release=lambda *_: self.add_to_cart())
        clear_btn.bind(on_release=lambda *_: self.clear_cart())
        back_btn.bind(on_release=lambda *_: self.manager.transition_to("home"))
        hist_btn.bind(on_release=lambda *_: self.manager.transition_to("history"))
        search_btn.bind(on_release=lambda *_: self.open_search_popup())
        cash_btn.bind(on_release=lambda *_: self.complete_cash_sale())

        # Assemble
        root.add_widget(top)
        root.add_widget(add_row)
        root.add_widget(self.sub_lbl)
        root.add_widget(hdr)
        root.add_widget(scroller)
        root.add_widget(cash_btn)
        root.add_widget(bottom)
        self.add_widget(root)

    def on_pre_enter(self, *a):
        self.inv = load_json(INV_JSON, [])
        self.item_spinner.values = [i["name"] for i in self.inv] or ["(no items)"]
        if self.item_spinner.text not in self.item_spinner.values:
            self.item_spinner.text = "Select item"
        self.clear_cart()

    def _find_item(self, name):
        for i in self.inv:
            if i.get("name") == name:
                return i
        return None

    def _cart_row(self, name, price, qty):
        total = float(price) * int(qty)
        row = GridLayout(cols=4, size_hint_y=None, height=dp(30), spacing=dp(6), padding=[dp(6), 0])

        def _lbl(t, w, align="left"):
            lb = Label(text=t, size_hint_x=w, size_hint_y=None, height=dp(30), halign=align, valign="middle",
                       shorten=True, shorten_from="right")
            lb.bind(size=lambda i, *_: setattr(i, "text_size", (i.width, None)))
            return lb

        row.add_widget(_lbl(name, .56))
        row.add_widget(_lbl(money(price), .16, "right"))
        row.add_widget(_lbl(str(qty), .12, "right"))
        row.add_widget(_lbl(money(total), .16, "right"))
        return row

    def refresh_cart(self):
        self.cart_box.clear_widgets()
        for line in self.cart:
            self.cart_box.add_widget(self._cart_row(line["name"], line["price"], line["qty"]))
        self.sub_lbl.text = f"Subtotal: {money(self.subtotal)}"

    def add_to_cart(self):
        it = self._find_item(self.item_spinner.text)
        if not it:
            toast("Select an item first.", "New Sale", .7, .3); return
        q = max(1, int(to_float(self.qty_input.text)))
        available = int(it.get("qty", 0))
        q = min(q, available) if available > 0 else q
        self.cart.append({"name": it["name"], "price": float(it["price"]), "qty": q})
        self.subtotal += float(it["price"]) * q
        self.refresh_cart()

    def clear_cart(self):
        self.cart, self.subtotal = [], 0.0
        self.refresh_cart()

    def open_search_popup(self):
        if not self.inv:
            toast("Inventory is empty.", "Search", .7, .3)
            return

        box = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
        ti = TextInput(hint_text="Type to filter items…", multiline=False,
                       size_hint_y=None, height=dp(50), font_size=sp(18))
        results = GridLayout(cols=1, spacing=dp(6), size_hint_y=None, padding=[0, dp(6), 0, 0])
        results.bind(minimum_height=lambda g, h: setattr(g, "height", h))
        sc = ScrollView(size_hint=(1, None), height=dp(260)); sc.add_widget(results)

        pop = Popup(title="Search Items", content=box,
                    size_hint=(None, None), size=(dp(360), dp(360)))

        def refresh_list(*_):
            q = ti.text.strip().lower()
            results.clear_widgets()
            for it in self.inv:
                name = it["name"]
                if q in name.lower():
                    b = Button(text=name, size_hint_y=None, height=dp(44))

                    def choose(instance, nm=name):
                        self.item_spinner.text = nm
                        pop.dismiss()

                    b.bind(on_release=choose)
                    results.add_widget(b)

        ti.bind(text=refresh_list)
        refresh_list()

        box.add_widget(ti)
        box.add_widget(sc)
        pop.open()

    def complete_cash_sale(self):
        if not self.cart:
            toast("Cart is empty.", "Cash", .7, .3); return

        # Update inventory
        for line in self.cart:
            it = self._find_item(line["name"])
            if it:
                it["qty"] = max(0, int(it.get("qty", 0)) - int(line["qty"]))
        save_json(INV_JSON, self.inv)

        # Append sales log
        sales = load_json(SALES_JSON, [])
        sales.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "payment": "cash",
            "total": round(self.subtotal, 2),
            "lines": self.cart,
            "refunded": False
        })
        save_json(SALES_JSON, sales)

        self.clear_cart()
        toast("Cash sale saved.", "Complete", .7, .3)

# ---------------------------- Sales History ----------------------------

class HistoryScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.sales = []
        self.selected_index = None  # index in self.sales

        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        root.add_widget(page_title("SALES HISTORY"))

        # Header with Status column; no per-row refund button.
        header = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(6), padding=[dp(8), 0])
        header.add_widget(self._cell("Date/Time", .40, "left", True))
        header.add_widget(self._cell("Pay", .12, "left", True))
        header.add_widget(self._cell("Total", .16, "right", True))
        header.add_widget(self._cell("Items", .12, "right", True))
        header.add_widget(self._cell("Status", .20, "center", True))
        root.add_widget(header)

        self.list_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(2), padding=[dp(6), 0])
        self.list_box.bind(minimum_height=lambda inst, val: setattr(inst, "height", val))
        scroller = ScrollView(); scroller.add_widget(self.list_box)
        root.add_widget(scroller)

        # Long refund button above Back
        refund_btn = Button(text="Refund Selected Sale", size_hint_y=None, height=dp(56))
        refund_btn.bind(on_release=lambda *_: self._refund_selected())
        root.add_widget(refund_btn)

        back = Button(text="Back", size_hint_y=None, height=dp(56))
        back.bind(on_release=lambda *_: self.manager.transition_to("sale"))
        root.add_widget(back)

        self.add_widget(root)

    def _cell(self, text, weight=1, align="left", bold=False):
        lbl = Label(text=f"[b]{text}[/b]" if bold else text, markup=True,
                    halign=align, valign="middle",
                    shorten=True, shorten_from="right",
                    size_hint_x=weight, size_hint_y=None, height=dp(30),
                    font_size=sp(16))
        lbl.bind(size=lambda inst, *_: setattr(inst, "text_size", (inst.width, None)))
        return lbl

    def on_enter(self, *a):
        self.sales = load_json(SALES_JSON, [])
        self.selected_index = None
        self.refresh_table()

    def refresh_table(self):
        self.list_box.clear_widgets()
        # show newest first; keep mapping to real index
        for idx, s in enumerate(reversed(self.sales)):
            real_index = len(self.sales) - 1 - idx
            ts = s.get("timestamp", "")
            pay = s.get("payment", "")
            total = money(s.get("total", 0))
            items = sum(int(l.get("qty", 0)) for l in s.get("lines", []))
            status = "Refunded" if s.get("refunded") else ""

            row = ClickRow(cols=5, size_hint_y=None, height=dp(34), spacing=dp(6), padding=[dp(8), 0])
            row.add_widget(self._cell(ts, .40, "left"))
            row.add_widget(self._cell(pay, .12, "left"))
            row.add_widget(self._cell(total, .16, "right"))
            row.add_widget(self._cell(str(items), .12, "right"))
            row.add_widget(self._cell(status, .20, "center"))

            def select_row(_r, i=real_index, text=ts):
                self.selected_index = i
                toast(f"Selected: {text}", "Sales", .75, .28)

            row.bind(on_release=select_row)
            self.list_box.add_widget(row)

    def _refund_selected(self):
        if self.selected_index is None:
            toast("Tap a sale row first to select it.", "Refund", .8, .3); return
        if self.selected_index < 0 or self.selected_index >= len(self.sales):
            toast("Selected sale not found.", "Refund", .75, .3); return
        sale = self.sales[self.selected_index]
        if sale.get("refunded"):
            toast("This sale is already refunded.", "Refund", .75, .3); return

        msg = (f"Refund this sale?\n\n"
               f"{sale.get('timestamp','')} • {sale.get('payment','')}\n"
               f"Total: {money(sale.get('total',0))}")
        confirm(msg, "Confirm Refund",
                on_yes=lambda: self._apply_refund(self.selected_index))

    def _apply_refund(self, index):
        sale = self.sales[index]
        if sale.get("refunded"):
            self.refresh_table()
            return

        # 1) Restock inventory
        inv = load_json(INV_JSON, [])
        def find_inv(name):
            for it in inv:
                if it.get("name")==name:
                    return it
            return None
        for line in sale.get("lines", []):
            nm = line.get("name","")
            qty = int(line.get("qty",0))
            price = float(line.get("price",0))
            itm = find_inv(nm)
            if itm:
                itm["qty"] = int(itm.get("qty",0)) + qty
            else:
                inv.append({"name": nm, "price": price, "qty": qty})
        save_json(INV_JSON, inv)

        # 2) Mark sale as refunded (keep it in history)
        sale["refunded"] = True
        self.sales[index] = sale
        save_json(SALES_JSON, self.sales)

        self.refresh_table()
        toast("Sale refunded and inventory restored.", "Refund", .85, .32)

# ------------------------------- Upgrades -------------------------------

class UpgradesScreen(Screen):
    PRICE_BUNDLE = "$14.99"
    PRICE_PAY    = "$6.99"
    PRICE_IMP    = "$4.99"
    PRICE_REP    = "$4.99"
    PRICE_SCAN   = "$4.99"

    def __init__(self, **kw):
        super().__init__(**kw)
        self.flags = load_upgrades()

        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(12))
        root.add_widget(page_title("UPGRADES"))

        # Enter Code + Load File
        row_codes = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(50))
        btn_enter_code = Button(text="Enter Code")
        btn_load_file  = Button(text="Load License File")
        row_codes.add_widget(btn_enter_code); row_codes.add_widget(btn_load_file)
        root.add_widget(row_codes)

        # Bundle button (long)
        bundle = Button(text=f"Full Pro Bundle — {self.PRICE_BUNDLE}", size_hint_y=None, height=dp(56))
        root.add_widget(bundle)

        # Two rows (2x2)
        row1 = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(50))
        pay_btn = Button(text=f"Payments — {self.PRICE_PAY}")
        imp_btn = Button(text=f"Import/Export — {self.PRICE_IMP}")
        row1.add_widget(pay_btn); row1.add_widget(imp_btn)
        root.add_widget(row1)

        row2 = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(50))
        rep_btn = Button(text=f"Reports Pro — {self.PRICE_REP}")
        scan_btn = Button(text=f"Scanner Pro — {self.PRICE_SCAN}")
        row2.add_widget(rep_btn); row2.add_widget(scan_btn)
        root.add_widget(row2)

        # Info / Back
        self.info = Label(
            text="[i]After purchase, unlock with a code or a license file.\n"
                 "Unlocked features reflect automatically when license is loaded.\n"
                 f"{unlocked_text(self.flags)}[/i]",
            markup=True, size_hint_y=None, height=dp(72),
            halign="center", valign="middle"
        )
        self.info.bind(size=lambda i, *_: setattr(i, "text_size", (i.width - dp(12), None)))
        root.add_widget(self.info)

        how_btn = Button(text="How to Unlock", size_hint_y=None, height=dp(56))
        back = Button(text="Back", size_hint_y=None, height=dp(56))
        how_btn.bind(on_release=lambda *_: self.show_how())
        back.bind(on_release=lambda *_: self.manager.transition_to("home"))
        root.add_widget(how_btn)
        root.add_widget(back)

        # Wiring for code + file
        btn_enter_code.bind(on_release=lambda *_: self._enter_code_popup())
        btn_load_file.bind(on_release=lambda *_: self._load_file())

        # Store-like buttons just show the how-to
        for b in (bundle, pay_btn, imp_btn, rep_btn, scan_btn):
            b.bind(on_release=lambda *_: self.show_how())

        self.add_widget(root)

    def on_pre_enter(self, *a):
        self.flags = load_upgrades()
        self.info.text = (
            "[i]After purchase, unlock with a code or a license file.\n"
            "Unlocked features reflect automatically when license is loaded.\n"
            f"{unlocked_text(self.flags)}[/i]"
        )

    def _enter_code_popup(self):
        box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(10))
        ti = TextInput(hint_text="Enter upgrade code (e.g. PRO_ALL-9XK7)",
                       multiline=False, size_hint_y=None, height=dp(44))
        row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        ok = Button(text="Apply"); cancel = Button(text="Cancel")
        row.add_widget(ok); row.add_widget(cancel)
        box.add_widget(ti); box.add_widget(row)
        pop = Popup(title="Upgrade Code", content=box, size_hint=(None,None), size=(dp(360), dp(180)))
        def _apply(*_):
            good, flags = unlock_from_code(ti.text)
            pop.dismiss()
            if good:
                self.flags = flags
                self.on_pre_enter()
                toast("Upgrade applied.\n" + unlocked_text(flags), "Upgrades", 0.9, 0.38)
            else:
                toast("Invalid code.", "Upgrades", 0.7, 0.28)
        ok.bind(on_release=_apply); cancel.bind(on_release=pop.dismiss)
        pop.open()

    def _load_file(self):
        good, msg = unlock_from_license_file()
        self.flags = load_upgrades()
        self.on_pre_enter()
        toast((msg + "\n" + unlocked_text(self.flags)) if good else msg, "Upgrades", 0.95, 0.40)

    def show_how(self):
        txt = (
            "[b]How to unlock (offline)[/b]\n\n"
            "[b]Step 1.[/b] Pay the price shown.\n"
            "[b]Step 2.[/b] You receive an unlock code (e.g. PRO_PAY-ABCD) [i]or[/i] a license.txt file.\n"
            "[b]Step 3.[/b] In this screen, tap [b]Enter Code[/b] or [b]Load License File[/b].\n\n"
            f"License file path:\n{LICENSE_TXT}\n\n"
            f"{unlocked_text(self.flags)}"
        )
        toast(txt, "How to Unlock", 0.96, 0.64)

# ------------------------- Screen Manager / App -------------------------

class MyScreenManager(ScreenManager):
    def transition_to(self, name):
        self.transition = SlideTransition(direction="left")
        self.current = name

class MyPocketPOS(App):
    def build(self):
        # Decide writable storage now; set global paths.
        used = init_storage(self)  # ensures folders exist
        # Ensure upgrades file exists after paths are set
        load_upgrades()

        sm = MyScreenManager()
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(InventoryScreen(name="inventory"))
        sm.add_widget(SaleScreen(name="sale"))
        sm.add_widget(HistoryScreen(name="history"))
        sm.add_widget(UpgradesScreen(name="upgrades"))
        return sm

if __name__ == "__main__":
    MyPocketPOS().run()
