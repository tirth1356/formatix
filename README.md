# 🚀 FormatIX

**FormatIX** is an AI-powered document formatting tool that converts messy or unstructured text into properly formatted academic and professional documents.

It helps automatically format documents according to common research and publication standards such as **APA, IEEE, MLA, Vancouver**, or **custom user-defined templates**.

The goal of FormatIX is to remove the pain of manual formatting and allow users to focus on writing content while the system handles the formatting.

---

# ✨ Features

- 📄 **Automatic Document Formatting**
  - Converts raw or poorly formatted text into structured documents.

- 📚 **Multiple Citation Styles**
  - Supports:
  - IEEE (2-column research paper format)
  - APA
  - MLA
  - Vancouver
  - Custom template

- 🧠 **AI-Powered Formatting**
  - Uses LLMs to understand document structure and apply appropriate formatting.

- 🧹 **Style Cleanup**
  - Removes inconsistent styles, broken headings, and incorrect spacing.

- ⚡ **Fast Processing**
  - Uses API-based models for quick document transformation.

---

# 🏗️ Project Structure

```
FormatIX
│
├── backend/              # API server and formatting logic
├── agents/               # AI agents responsible for formatting tasks
├── templates/            # Formatting templates (IEEE, APA, etc.)
├── utils/                # Helper functions
├── main.py               # Entry point of the application
├── requirements.txt      # Python dependencies
└── README.md
```

---

# ⚙️ Tech Stack

- **Python**
- **FastAPI**
- **Groq API / LLM models**
- **Document parsing libraries**
- **Custom formatting rule engine**

---

# 🧠 How It Works

1. User uploads or pastes a document.
2. FormatIX analyzes the structure.
3. AI identifies headings, references, and sections.
4. Selected template rules are applied.
5. The system generates a **clean, formatted document**.

---

# 🚀 Installation

Clone the repository:

```bash
git clone https://github.com/tirth1356/deepseek_derek_2.git
cd deepseek_derek_2
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
python main.py
```

---

# 🔑 Environment Variables

Create a `.env` file and add:

```
GROQ_API_KEY=your_api_key
GROQ_MODEL=llama3-8b-8192
```

---

# 📌 Example Use Case

Input (messy AI output):

```
title Artificial intelligence
introduction
Artificial intelligence is growing fast
references
1 some paper
```

Output (IEEE formatted):

```
Title: Artificial Intelligence

I. Introduction
Artificial intelligence is growing fast...

References
[1] Author, Paper Title, Year
```

---

# 📈 Future Improvements
- 📑 PDF and DOCX export
- 🧩 Plugin support for editors
- 🌐 Web UI for document upload
- 📊 Automatic reference detection
- 🧾 Citation extraction
---

# 🤝 Contributing

Contributions are welcome!
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Submit a Pull Request

---

# ⭐ Support

If you find this project useful:
- ⭐ Star the repository
- 🍴 Fork it
- 🛠️ Contribute

---

# 👨‍💻 Author

**Tirth Patel**

GitHub:  
https://github.com/tirth1356
