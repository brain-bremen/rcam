import sys
from PySide6.QtCore import QDate
from PySide6.QtWidgets import QCheckBox, QHBoxLayout

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QLabel,
    QDateEdit,
)


class MetadataDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enter Video Metadata")
        self.setModal(True)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.subject_edit = QLineEdit()
        self.experimenter_edit = QLineEdit()
        self.experiment_name_edit = QLineEdit()
        self.session_nr_edit = QLineEdit()
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setReadOnly(True)

        form.addRow("Subject:", self.subject_edit)
        form.addRow("Experimenter:", self.experimenter_edit)
        form.addRow("Experiment Name:", self.experiment_name_edit)
        form.addRow("Session Nr.:", self.session_nr_edit)
        form.addRow("Date:", self.date_edit)
        self.electrophysiology_cb = QCheckBox("Electrophysiology")
        self.imaging_cb = QCheckBox("Imaging")
        self.other_cb = QCheckBox("Other")

        checkbox_layout = QHBoxLayout()
        checkbox_layout.addWidget(self.electrophysiology_cb)
        checkbox_layout.addWidget(self.imaging_cb)
        checkbox_layout.addWidget(self.other_cb)

        form.addRow("Other Data Recorded:", checkbox_layout)
        layout.addLayout(form)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        # Add a freetext field for notes
        self.notes_edit = QLineEdit()
        form.addRow("Notes:", self.notes_edit)

        layout.addWidget(self.button_box)

    def get_metadata(self):
        return {
            "subject": self.subject_edit.text(),
            "experimenter": self.experimenter_edit.text(),
            "experiment_name": self.experiment_name_edit.text(),
            "session_nr": self.session_nr_edit.text(),
            "date": self.date_edit.date().toString("yyyy-MM-dd"),
            "start_time": self.start_time_edit.text(),
            "other_recorded_data": {
                "electrophysiology": self.electrophysiology_cb.isChecked(),
                "imaging": self.imaging_cb.isChecked(),
                "other": self.other_cb.isChecked(),
            },
        }


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = MetadataDialog()
    if dialog.exec_() == QDialog.Accepted:
        print(dialog.get_metadata())
