"""
Pandoc Conversion Utility
Compiles LaTeX strings to DOCX using the pandoc subprocess.
"""
import subprocess
from pathlib import Path

class PandocConverter:
    @staticmethod
    def latex_to_docx(latex_content: str, output_docx_path: str) -> bool:
        """
        Takes raw LaTeX string and uses pandoc to convert it to DOCX.
        Returns True if successful, raises exception otherwise.
        """
        output_path = Path(output_docx_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Temporary tex file next to the docx
        tex_path = output_path.with_suffix(".tex")
        
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_content)
            
        try:
            # pandoc document.tex -o formatted.docx
            result = subprocess.run(
                ["pandoc", str(tex_path), "-o", str(output_path)],
                check=True,
                capture_output=True,
                text=True
            )
            return True
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Pandoc conversion failed: {e.stderr}")
        except FileNotFoundError:
            raise RuntimeError("Pandoc is not installed or not in system PATH.")
