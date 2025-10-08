# main_lite.py
import os, csv, shutil
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.utils import platform

if platform == "android":
    from android.storage import app_storage_path
    BASE_DIR = app_storage_path()  # app-private, no permission required
else:
    BASE_DIR = os.getcwd()

CSV_PATH = os.path.join(BASE_DIR, "flea_inventory.csv")

def ensure_inventory_exists():
    if not os.path.exists(CSV_PATH):
        # copy starter inventory bundled inside APK
        sample = os.path.join(os.path.dirname(__file__), "sample_inventory.csv")
        if os.path.exists(sample):
            shutil.copy(sample, CSV_PATH)

def load_inventory():
    ensure_inventory_exists()
    items = []
    if not os.path.exists(CSV_PATH):
        return items
    try:
        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                if row.get("name"):
                    items.append(row)
    except Exception as e:
        print("Inventory load error:", e)
    return items

class Root(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation="vertical", spacing=dp(10), padding=dp(14), **kw)
        self.add_widget(Label(text=f"Pocket POS Lite\n\nWorking file:\n{CSV_PATH}", halign="center"))
        b = Button(text="New Sale → Select Inventory", size_hint_y=None, height=dp(48))
        b.bind(on_release=self.show_inventory)
        self.add_widget(b)

    def show_inventory(self, *_):
        items = load_inventory()
        if not items:
            Popup(title="Inventory empty",
                  content=Label(text="No items found.\nThe app created sample_inventory for you."),
                  size_hint=(.85,.4)).open()
            return
        names = [i["name"] for i in items]
        box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12))
        box.add_widget(Spinner(text="Select item", values=names, size_hint_y=None, height=dp(48)))
        Popup(title="Inventory", content=box, size_hint=(.9,.7)).open()

class POSLite(App):
    def build(self):
        ensure_inventory_exists()
        return Root()

if __name__ == "__main__":
    POSLite().run()
