# 🧠 LLM File Describe

**LLM File Describe** is a **QGIS plugin** that uses a **locally hosted large language model (via [Ollama](https://ollama.ai))** to analyse and describe geospatial data files.  
It supports both **vector formats** (such as `.shp` and `.gpkg`) and **raster formats** (such as `.tif` and `.img`).  
The plugin reads metadata and sample data from the file and asks the language model to infer what the dataset represents (e.g., cities, roads, land use) and summarise its contents.

---

## 🚀 Features

- **Vector file support:**  
  Loads `.shp` or `.gpkg` files, extracts field names, counts features and samples up to 10 rows from the attribute table to provide context.

- **Raster file support:**  
  Loads raster formats (`.tif`, `.tiff`, `.img`), reports image dimensions, pixel size, bounding box coordinates, and basic statistics (minimum, maximum, mean, standard deviation, and pixel count) for each band.

- **Language selection:**  
  Choose the language of the model’s response (**English or French**) from a drop-down list.

- **Follow-up questions:**  
  After the initial description, you can ask questions about the dataset and the model will answer based on the previous context.

- **Information dialog:**  
  An info button (`?`) explains the purpose and usage of the plugin directly in QGIS.

---

## 🧩 Requirements

- **QGIS 3.0+** — Tested with QGIS 3.40 LTR, but should work with any modern version.  
- **Ollama** — Must be installed and running locally, with at least one LLM model (e.g. `llama3.1`).  
  The plugin sends HTTP requests to the Ollama API at:  
  `http://localhost:11434/api/chat`

---

## ⚙️ Installation

### Option 1 — From ZIP

1. **Download** or **clone** this repository and locate the file:  
   `llm_file_describe_final.zip`
2. In QGIS, open **Plugins → Manage and Install Plugins…**
3. Click **Install from ZIP…** and select the downloaded ZIP file.
4. Restart QGIS if necessary, then **enable** the plugin from the Plugins menu.

### Option 2 — Manual Installation

Unzip the folder `llm_file_describe` directly into your QGIS profile’s plugins directory:  
`~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`

---

## 🧭 Usage

1. **Open the plugin:**  
   Once enabled, access it from **Plugins → LLM File Describe**, or via the toolbar icon.

2. **Select a file:**  
   Use the `...` button to browse for a vector or raster file (`.shp`, `.gpkg`, `.tif`, etc.).

3. **Choose model and language:**
   - *Ollama model:* defaults to `llama3.1` (you can change it if needed).  
   - *Response language:* English or French.

4. **Analyze:**  
   Click **Analyze** — the plugin reads metadata, queries the LLM, and displays a textual summary.

5. **Ask questions:**  
   After the description appears, type a question in the **Question** field and click **Ask**.  
   The model will answer using the dataset’s description as context.

6. **Info:**  
   Click the **information icon (?)** to read about the plugin’s purpose and usage.

---

## 🤝 Contributing

Contributions are welcome!  
If you encounter a bug, have a feature request, or would like to improve the plugin, please open an **issue** or **pull request** on this GitHub repository.

---

## 📄 License

This project is licensed under the **GNU General Public License v3 (GPL-3)**.  
See the [LICENSE](LICENSE) file for details.

---

## 👤 Author

Developed and maintained by **Romain Wenger**  
📧 [romain.wenger@live-cnrs.unistra.fr](mailto:romain.wenger@live-cnrs.unistra.fr)

---
