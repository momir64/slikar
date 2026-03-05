from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QIcon
from PyQt6.QtCore import Qt
from PIL import Image
import sys
import os

SUPPORTED = (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp")


class DropZone(QLabel):
    def __init__(self, parent=None):
        super().__init__("Prevuci i pusti slike ovde\nili klikni za odabir", parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAcceptDrops(True)
        self.setMinimumHeight(180)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("DropZone")

    def dragEnterEvent(self, event: QDragEnterEvent):
        mime = event.mimeData()
        if mime is not None and mime.hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        mime = event.mimeData()
        if mime is None:
            return
        valid = [url.toLocalFile() for url in mime.urls() if url.toLocalFile().lower().endswith(SUPPORTED)]
        if not valid:
            QMessageBox.warning(self, "Nema slika", "Ni jedan od prevčenih fajlova nije slika!")
            return
        parent = self.window()
        if isinstance(parent, MainWindow):
            parent.set_files(valid)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Obrada slika")
        self.setWindowIcon(QIcon("icon.png"))
        self.setFixedWidth(500)
        self.selected_files = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)

        self.drop_zone = DropZone()
        self.drop_zone.mousePressEvent = lambda event: self._open_files()
        layout.addWidget(self.drop_zone)

        self.file_count_label = QLabel("Prvo odaberi slike za obradu.")
        self.file_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_count_label.setObjectName("FileCountLabel")
        layout.addWidget(self.file_count_label)

        layout.addWidget(QLabel("Sačucaj slike u sledećeom folderu:"))

        folder_row = QHBoxLayout()
        self.output_edit = QLineEdit(os.path.join(os.path.expanduser("~"), "Desktop"))
        folder_row.addWidget(self.output_edit)
        browse_btn = QPushButton("Odaberi folder")
        browse_btn.setFixedWidth(120)
        browse_btn.setFixedHeight(26)
        browse_btn.clicked.connect(self._browse_output)
        folder_row.addWidget(browse_btn)
        layout.addLayout(folder_row)

        convert_btn = QPushButton("Konvertuj")
        convert_btn.setObjectName("ConvertButton")
        convert_btn.setMinimumHeight(44)
        convert_btn.clicked.connect(self._convert)
        layout.addWidget(convert_btn)

    def set_files(self, files):
        self.selected_files = files
        count = len(files)
        self.file_count_label.setText(f"Odabran{'a' if count == 1 else 'o' if count > 4 else 'e'} {count} slik{'a' if count == 1 or count > 4 else 'e'}")

    def _open_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Odaberi slike", "",
            "Image files (" + " ".join(f"*{ext}" for ext in SUPPORTED) + ")"
        )
        if files:
            self.set_files(files)

    def _browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Odaberi folder za čuvanje")
        if folder:
            self.output_edit.setText(folder)

    def _convert(self):
        if not self.selected_files:
            QMessageBox.warning(self, "Nema slika", "Odaberi barem jednu sliku za obradu.")
            return

        out_dir = self.output_edit.text().strip()
        if not out_dir or not os.path.isdir(out_dir):
            QMessageBox.critical(self, "Nevalidan folder", "Odabrani folder za čuvanje ne postoji.")
            return

        converted, errors = 0, []
        for path in self.selected_files:
            try:
                img = Image.open(path)
                if img.mode in ("RGBA", "LA", "PA"):
                    img = img.convert("RGBA")
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])
                    img = background
                img = img.convert("L")
                stem = os.path.splitext(os.path.basename(path))[0]
                file_ext = os.path.splitext(path)[1].lower()
                img.save(os.path.join(out_dir, f"{stem}_gray{file_ext}"))
                converted += 1
            except Exception as exc:
                errors.append(f"{os.path.basename(path)}: {exc}")

        msg = f"Uspešno konvertovan{'a' if converted == 1 else 'o' if converted > 4 else 'e'} slik{'a' if converted == 1 or converted > 4 else 'e'}."
        if errors:
            QMessageBox.warning(self, "Završeno sa greškom", msg + "\n\nGreška:\n" + "\n".join(errors))
        else:
            QMessageBox.information(self, "Završeno", msg)
        self.selected_files = []
        self.file_count_label.setText("Nema odabranih slika")


if __name__ == "__main__":
    application = QApplication(sys.argv)
    application.setStyle("Fusion")
    application.setStyleSheet("""
        #DropZone {
            border: 2px dashed palette(mid);
            border-radius: 10px;
            font-size: 14px;
            color: palette(text);
        }
        #DropZone:hover {
            border-color: palette(highlight);
            color: palette(highlight);
        }
        #ConvertButton {
            font-size: 14px;
            font-weight: bold;
        }
        #FileCountLabel {
            font-size: 11px;
        }
    """)
    window = MainWindow()
    window.show()
    sys.exit(application.exec())
