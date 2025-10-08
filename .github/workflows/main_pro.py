# main_pro.py
import os, csv, shutil
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from kivy.metrics import dp
from kivy.utils import platform

if platform == "android":
    from android.storage import app_storage_path, primary_external_storage_path
    BASE_DIR = app_storage_path()  # internal, app-private
    DOWNLOADS = os.path.join(primary_external_storage_path(), "Download")
else:
    BASE_DIR = os.getcwd()
    DOWNLOADS = os.getcwd()

CSV_PATH = os.path.join(BASE_DIR, "flea_inventory.csv")
EXPORT_PATH = os.path.join(DOWNLOADS, "flea_inventory_backup.csv")

REQUIRED_HEADERS = ["name", "price", "qty", "barcode"]

def ensure_inventory_exists():
    if not os.path.exists(CSV_PATH):
        sample = os.path.join(os.path.dirname(__file__), "sample_inventory.csv")
        if os.path.exists(sample):
            shutil.copy(sample, CSV_PATH)

def validate_csv(path):
    try:
        with open(path, newline="", encoding="utf-8") as f:
            r = csv.reader(f)
            headers = next(r, [])
            headers = [h.strip().lower() for h in headers]
            return all(h in headers for h in REQUIRED_HEADERS)
    except Exception as e:
        print("validate_csv error:", e)
        return False

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
        self.add_widget(Label(text=f"Pocket POS Pro\n\nWorking file:\n{CSV_PATH}", halign="center"))

        # Top row: New Sale + Import + Export
        row = GridLayout(cols=3, size_hint_y=None, height=dp(52), spacing=dp(8))
        btn_sale = Button(text="New Sale", on_release=self.show_inventory)
        btn_imp  = Button(text="Import CSV", on_release=self.import_csv_dialog)
        btn_exp  = Button(text="Export CSV", on_release=self.export_csv)
        row.add_widget(btn_sale); row.add_widget(btn_imp); row.add_widget(btn_exp)
        self.add_widget(row)

    def show_popup(self, title, msg):
        Popup(title=title, content=Label(text=msg), size_hint=(.85, .4)).open()

    def show_inventory(self, *_):
        items = load_inventory()
        if not items:
            self.show_popup("Inventory empty",
                            "No items loaded.\nUse Import, or the app created a sample for you.")
            return
        names = [i["name"] for i in items]
        box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12))
        box.add_widget(Spinner(text="Select item", values=names, size_hint_y=None, height=dp(48)))
        Popup(title="Inventory", content=box, size_hint=(.9,.7)).open()

    def import_csv_dialog(self, *_):
        chooser = FileChooserIconView(path=DOWNLOADS, filters=["*.csv"])
        box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12))
        box.add_widget(chooser)

        def do_import(*_a):
            path = chooser.selection[0] if chooser.selection else ""
            if not path:
                self.show_popup("No file selected", "Please pick a .csv file.")
                return
            if not validate_csv(path):
                self.show_popup("Invalid CSV",
                                f"CSV must have headers: {', '.join(REQUIRED_HEADERS)}")
                return
            try:
                shutil.copy(path, CSV_PATH)
                self.show_popup("Imported", f"Inventory updated from:\n{path}")
            except Exception as e:
                self.show_popup("Import failed", f"{e}")

        btns = GridLayout(cols=2, size_hint_y=None, height=dp(48), spacing=dp(8))
        btns.add_widget(Button(text="Import", on_release=do_import))
        btns.add_widget(Button(text="Cancel", on_release=lambda *_: pop.dismiss()))
        box.add_widget(btns)

        pop = Popup(title="Import Inventory (pick .csv from Downloads)",
                    content=box, size_hint=(.95, .85))
        pop.open()

    def export_csv(self, *_):
        try:
            ensure_inventory_exists()
            os.makedirs(os.path.dirname(EXPORT_PATH), exist_ok=True)
            shutil.copy(CSV_PATH, EXPORT_PATH)
            self.show_popup("Exported", f"Saved to:\n{EXPORT_PATH}")
        except Exception as e:
            self.show_popup("Export failed", f"{e}")

class POSPro(App):
    def build(self):
        ensure_inventory_exists()
        return Root()

if __name__ == "__main__":
    POSPro().run()
