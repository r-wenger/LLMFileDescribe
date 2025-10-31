"""Dialog and logic for LLM File Describe plugin."""

import json
import os
from qgis.PyQt import QtWidgets, QtCore
from qgis.PyQt.QtWidgets import QStyle
from qgis.core import QgsVectorLayer, QgsRasterLayer
import requests


class LLMFileDescribeDialog(QtWidgets.QDialog):
    """A simple dialog to select a file and obtain a description via LLM."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('LLM File Describe')
        self.setMinimumWidth(400)

        # Hold the current dataset description so that questions can be asked later
        self.current_description = None

        layout = QtWidgets.QVBoxLayout(self)

        # File path input with browse button
        file_layout = QtWidgets.QHBoxLayout()
        file_label = QtWidgets.QLabel('File path:')
        self.file_edit = QtWidgets.QLineEdit()
        browse_button = QtWidgets.QPushButton('...')
        browse_button.setToolTip("Choose a vector or raster file")
        browse_button.clicked.connect(self.browse_file)
        file_layout.addWidget(file_label)
        file_layout.addWidget(self.file_edit)
        file_layout.addWidget(browse_button)
        layout.addLayout(file_layout)

        # Ollama model input
        model_layout = QtWidgets.QHBoxLayout()
        model_label = QtWidgets.QLabel('Ollama model:')
        self.model_edit = QtWidgets.QLineEdit('llama3.1')
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_edit)
        layout.addLayout(model_layout)

        # Language selection
        lang_layout = QtWidgets.QHBoxLayout()
        lang_label = QtWidgets.QLabel('Response language:')
        self.lang_combo = QtWidgets.QComboBox()
        self.lang_combo.addItems(['English', 'French'])
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.lang_combo)
        layout.addLayout(lang_layout)

        # Analyse button
        self.analyse_button = QtWidgets.QPushButton('Analyze')
        self.analyse_button.clicked.connect(self.on_analyse)
        layout.addWidget(self.analyse_button)

        # Progress bar
        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminate
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # Output text area
        self.output_edit = QtWidgets.QTextEdit()
        self.output_edit.setReadOnly(True)
        layout.addWidget(self.output_edit)

        # Question input row: initially disabled until a file is analysed
        question_layout = QtWidgets.QHBoxLayout()
        question_label = QtWidgets.QLabel('Question:')
        self.question_edit = QtWidgets.QLineEdit()
        self.question_edit.setEnabled(False)
        self.ask_button = QtWidgets.QPushButton('Ask')
        self.ask_button.setEnabled(False)
        self.ask_button.clicked.connect(self.on_ask_question)
        question_layout.addWidget(question_label)
        question_layout.addWidget(self.question_edit)
        question_layout.addWidget(self.ask_button)
        layout.addLayout(question_layout)

        # Information button with tooltip explaining the plugin
        info_btn = QtWidgets.QToolButton()
        # Use a standard information icon for better visual appearance
        info_btn.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxInformation))
        info_btn.setAutoRaise(True)
        info_btn.setToolTip(
            "This plugin allows you to choose a vector (SHP, GPKG) or raster (e.g. GeoTIFF) "
            "file and obtain a concise description of its contents using a local Ollama LLM. "
            "For vector data, the plugin samples the first rows and lists fields; for raster data, "
            "it provides bounding box coordinates and basic statistics. Select the response language "
            "and model, then click Analyze."
        )
        layout.addWidget(info_btn)

        # Connect information button to show a help dialog
        info_btn.clicked.connect(self.show_info)

    def browse_file(self):
        """Open a file dialog and set the selected file path."""
        filters = (
            'Geographic files (*.shp *.gpkg *.tif *.tiff *.img);;'
            'Shapefiles (*.shp);;GeoPackages (*.gpkg);;Rasters (*.tif *.tiff *.img);;All files (*)'
        )
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Choose a file', '', filters)
        if file_path:
            self.file_edit.setText(file_path)

    def on_analyse(self):
        """Triggered when the analyse button is clicked."""
        file_path = self.file_edit.text().strip()
        if not file_path or not os.path.exists(file_path):
            self.output_edit.setPlainText('Please choose a valid file.')
            return

        model_name = self.model_edit.text().strip() or 'llama3.1'
        language = self.lang_combo.currentText()

        # Show progress bar and disable button
        self.progress.setVisible(True)
        self.analyse_button.setEnabled(False)
        QtWidgets.QApplication.processEvents()

        # Build description of the file
        description = self.describe_file(file_path)
        # Call LLM to get a summary in the selected language
        answer = self.call_llm(model_name, description, language)

        # Hide progress bar and re-enable button
        self.progress.setVisible(False)
        self.analyse_button.setEnabled(True)
        self.output_edit.setPlainText(answer)

        # Store the description for subsequent questions and enable question input
        self.current_description = description
        self.question_edit.setEnabled(True)
        self.ask_button.setEnabled(True)

    def describe_file(self, file_path):
        """Inspect the provided file and return a description dict."""
        # Try to load as vector
        vlayer = QgsVectorLayer(file_path, 'tmp', 'ogr')
        if vlayer.isValid():
            fields = [f.name() for f in vlayer.fields()]
            count = vlayer.featureCount()
            # sample up to 10 features
            sample = []
            for i, feat in enumerate(vlayer.getFeatures()):
                row = {}
                for fname in fields:
                    try:
                        val = feat[fname]
                        # Ensure the value is JSON‑serialisable.  Some values may be
                        # QVariant instances which are not directly serialisable.  Try
                        # serialising; if it fails, attempt to convert to Python or
                        # fallback to string.
                        try:
                            json.dumps(val)
                            row[fname] = val
                        except TypeError:
                            # If it's a QVariant, convert to a Python object
                            try:
                                from qgis.PyQt.QtCore import QVariant
                                if isinstance(val, QVariant):
                                    val = val.toPyObject()
                            except Exception:
                                pass
                            # Try again
                            try:
                                json.dumps(val)
                                row[fname] = val
                            except TypeError:
                                # Fallback to string representation
                                row[fname] = str(val)
                    except Exception:
                        row[fname] = None
                sample.append(row)
                if i >= 9:
                    break
            return {'type': 'vector', 'fields': fields, 'feature_count': int(count), 'sample': sample}

        # Try to load as raster
        rlayer = QgsRasterLayer(file_path, 'tmp')
        if rlayer.isValid():
            bands = rlayer.bandCount()
            width = rlayer.width()
            height = rlayer.height()
            pixel_size = [rlayer.rasterUnitsPerPixelX(), rlayer.rasterUnitsPerPixelY()]
            crs = rlayer.crs().authid() if rlayer.crs() else ''
            # Bounding box coordinates (xMin, yMin, xMax, yMax)
            extent = rlayer.extent()
            bbox = [extent.xMinimum(), extent.yMinimum(), extent.xMaximum(), extent.yMaximum()]
            # Compute basic statistics for each band
            stats_list = []
            try:
                for b in range(1, bands + 1):
                    s = rlayer.dataProvider().bandStatistics(
                        b,
                        QgsRasterLayer.StatsAll,
                        rlayer.extent(),
                        1024
                    )
                    stats_list.append({
                        'band': b,
                        'min': float(s.minimumValue),
                        'max': float(s.maximumValue),
                        'mean': float(s.mean),
                        'stddev': float(s.stdDev),
                        'count': int(s.elementCount),
                    })
            except Exception:
                # If statistics computation fails, leave empty
                stats_list = []
            return {
                'type': 'raster',
                'bands': int(bands),
                'size': [int(width), int(height)],
                'pixel_size': pixel_size,
                'crs': crs,
                'bbox': bbox,
                'statistics': stats_list,
            }

        # If neither vector nor raster, return basic info
        return {'type': 'unknown', 'path': file_path}

    def call_llm(self, model, desc, language='English'):
        """Send the description to the LLM via Ollama and return its response.

        The language parameter defines the desired language of the response. A
        system prompt is composed in English instructing the model to analyse
        the JSON description of a geographic file and to summarise it. A final
        instruction requests that the answer be in the selected language.
        """
        # Build a system prompt in English; instruct the model about the task
        # and specify the response language.
        system_prompt = (
            "You are a geospatial assistant. You receive a JSON description of a "
            "geographic file (vector or raster). Analyse the fields, number of "
            "features, sample rows, bounding box and basic statistics to suggest "
            "what the dataset contains (e.g. cities, roads, buildings). If it is a raster, "
            "describe the bands, image size, pixel size, bounding box and statistical summary. "
            f"Always answer in {language}."
        )
        user_content = json.dumps(desc, ensure_ascii=False)
        payload = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_content},
            ],
            'stream': False,
            'options': {'temperature': 0.2},
        }
        try:
            response = requests.post('http://localhost:11434/api/chat', json=payload, timeout=180)
            response.raise_for_status()
            data = response.json()
            # Retrieve the assistant's message content; default to empty if missing
            return data.get('message', {}).get('content', '')
        except Exception as exc:
            return f'Error calling the model: {exc}'

    def call_llm_question(self, model, desc, question, language='English'):
        """Send a question about the dataset to the LLM and return its answer.

        The model receives both the description and the question and is instructed to
        base its answer on the provided description. The response language is
        controlled via the language parameter.
        """
        system_prompt = (
            "You are a geospatial assistant. You are given a description of a dataset "
            "(vector or raster) and a user question about that dataset. Answer the "
            "question based only on the description provided and do not speculate "
            "beyond it. Always answer in {}.".format(language)
        )
        # Combine description and question into a single JSON payload
        content_obj = {"description": desc, "question": question}
        try:
            user_content = json.dumps(content_obj, ensure_ascii=False)
        except TypeError:
            # Fallback to string representation if serialisation fails
            user_content = json.dumps(str(content_obj), ensure_ascii=False)
        payload = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_content},
            ],
            'stream': False,
            'options': {'temperature': 0.2},
        }
        try:
            resp = requests.post('http://localhost:11434/api/chat', json=payload, timeout=180)
            resp.raise_for_status()
            data = resp.json()
            return data.get('message', {}).get('content', '')
        except Exception as exc:
            return f'Error calling the model: {exc}'

    def on_ask_question(self):
        """Handle the user clicking the Ask button to query the LLM about the data."""
        if not self.current_description:
            # No description available
            return
        question = self.question_edit.text().strip()
        if not question:
            return
        model_name = self.model_edit.text().strip() or 'llama3.1'
        language = self.lang_combo.currentText()
        # Show progress and disable ask button
        self.progress.setVisible(True)
        self.ask_button.setEnabled(False)
        QtWidgets.QApplication.processEvents()
        # Call LLM to answer question
        answer = self.call_llm_question(model_name, self.current_description, question, language)
        # Hide progress and re-enable
        self.progress.setVisible(False)
        self.ask_button.setEnabled(True)
        # Append question and answer to output
        if answer:
            self.output_edit.append(f"\nQuestion: {question}\nAnswer: {answer}\n")
        else:
            self.output_edit.append(f"\nQuestion: {question}\nAnswer: (no response)\n")

    def show_info(self):
        """Display an information dialog about the plugin."""
        info_text = (
            "<p><b>LLM File Describe</b> allows you to select a vector (SHP, GPKG) or raster "
            "(e.g. GeoTIFF) file and uses a local Ollama LLM to generate a concise "
            "description of its contents. It samples the attribute table for vectors, "
            "computes bounding box coordinates and basic statistics for rasters, and "
            "supports answering follow-up questions based on the dataset description.</p>"
            "<p>Choose the response language and LLM model, click <em>Analyze</em> to get an overview, "
            "then type a question and click <em>Ask</em> for more insights.</p>"
        )
        QtWidgets.QMessageBox.information(self, 'About LLM File Describe', info_text)