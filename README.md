# FormatIX

**FormatIX** is a production-grade, privacy-first agentic AI system that automatically converts research papers into correct journal formatting. Researchers upload a manuscript (DOCX, PDF, or TXT); the system parses it, detects structure, extracts formatting rules, applies journal formatting, validates citations, and generates a formatted DOCX. All formatting decisions are explainable.

---

## 📖 Introduction

Academic researchers often face significant difficulties when preparing manuscripts for submission. Each publisher requires strict formatting rules, including citation styles, reference formats, document structure, and layout requirements. Even small formatting mistakes can lead to manuscript rejection or additional revision cycles.

Most researchers write their drafts using plain text, word processors, or LaTeX, but converting these drafts into the required journal format is time-consuming and error-prone. **FormatIX** removes this pain, allowing authors to focus on their content while the system handles the formatting.

## 🛠️ Problem Statement

Researchers currently face several major challenges during manuscript preparation:

1.  **Manual Formatting Effort**: Significant time is spent adjusting margins, headings, and spacing.
2.  **Multiple Citation Styles**: Journals require varying styles (APA, IEEE, MLA, etc.), making it difficult to maintain consistency.
3.  **Reference Formatting Errors**: Incorrect author formatting, DOI placement, and punctuation are common mistakes that delay submission.
4.  **Time-Consuming Revisions**: When a journal requires a different style, authors often have to manually reformat the entire document from scratch.

## 💡 Proposed Solution

The **FormatIX** system uses a multi-agent AI architecture to analyze uploaded manuscripts, extract their structure, and apply precise formatting rules. It removes previous inconsistent formatting and rebuilds the document using standardized guidelines, ensuring a clean, publication-ready output.

---

## ✨ Key Features

- **🧠 Multi-Agent Architecture**: Specialized AI agents for parsing, structure detection, and rule extraction.
-  **🛡️ Privacy-First**: Optional **Ollama (Local AI)** support ensures sensitive data never leaves your machine.
-  **⚡ High-Speed Cloud**: Real-time transformation using **Groq (Llama 3.1 8B)**.
-  **🧪 Citation Validation**: Cross-validates in-text citations against the reference list.
-  **📜 Professional Output**: Generates both **DOCX** and **LaTeX** source files.

---

## 📚 Supported Citation Styles

### **IEEE (Two-Column Format)**
Commonly used in engineering and computer science.
- **Layout**: Two-column document layout.
- **Citations**: Numbered in square brackets (e.g., `[1]`).
- **Ordering**: Ordered by appearance in text.
- **Reference Example**: `[1] J. A. Smith and R. T. Lee, "Machine learning for document analysis," *AI Research*, vol. 65, no. 2, 2022.`

### **APA (7th Edition)**
Widely used in psychology, education, and social sciences.
- **Style**: Author-date (e.g., `(Smith & Lee, 2022)`).
- **Layout**: Double-spaced with hanging indents for references.
- **Reference Example**: `Smith, J. A., & Lee, R. T. (2022). Machine learning for document analysis. *AI Research*, 65(2), 123–145.`

### **MLA (9th Edition)**
The standard for humanities and literature.
- **Style**: Author-page (e.g., `(Smith 123)`).
- **Layout**: "Works Cited" section, double-spaced.
- **Reference Example**: `Smith, John A., and Robert T. Lee. "Machine Learning for Document Analysis." *AI Research*, vol. 65, no. 2, 2022, pp. 123–145.`

### **Vancouver Style**
Widely used in medical and scientific journals.
- **Style**: Numeric citations.
- **Reference Example**: `Smith JA, Lee RT. Machine learning for document analysis. AI Research. 2022;65(2):123-145.`

### **Chicago Manual of Style (Author–Date)**
Commonly used in physical, natural, and social sciences.
- **Reference Example**: `Smith, John A., and Robert T. Lee. 2022. "Machine Learning for Document Analysis." AI Research 65 (2): 123–145.`

---

## 🏗️ Project Structure

```text
FormatIX/
├── frontend2/             # Vite + React + Tailwind + Shadcn UI
│   ├── src/
│   │   ├── agents/        # UI for individual agent status
│   │   └── components/    # Reusable shadcn widgets
├── backend/               # FastAPI + AI Agent Logic
│   ├── agents/            # Parser, Structure, Rule, Format, Citation, Validation
│   ├── llm/               # Ollama + Groq inference clients
│   ├── utils/             # python-docx and document processing utilities
│   ├── main.py            # API entry point
```

---

## 🧪 System Workflow

1.  **Manuscript Upload**: Accepts `.docx`, `.pdf`, or `.txt`.
2.  **Parsing & Structure Detection**: Extracts key sections (Title, Abstract, Headings) and removes inconsistent existing styles.
3.  **Rule Extraction**: AI identifies the exact font, spacing, and citation requirements for the selected style.
4.  **Formatting & Corrections**: The system generates a list of suggested structural corrections for user review.
5.  **Document Generation**: Rebuilds the document from scratch as a natively formatted **DOCX** and **LaTeX** file.

---

## 🎯 Impact

By automating manuscript formatting, FormatIX significantly reduces the time researchers spend on tedious formatting tasks, allowing them to focus on the research content itself. It ensures compliance with academic standards and makes the submission process faster, more reliable, and less stressful.

---

## 🚀 Installation & Setup

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env      # Set your GROQ_API_KEY
python main.py
```

### Frontend
```bash
cd frontend2
npm install
npm run dev
```

---

## 👨‍💻 Author
**Tirth Patel** ([GitHub Profile](https://github.com/tirth1356))
