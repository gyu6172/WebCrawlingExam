import fitz
import os
OUT = os.path.dirname(os.path.abspath(__file__))
doc = fitz.open(os.path.join(OUT, "preview.pdf"))
for i, page in enumerate(doc):
    pix = page.get_pixmap(dpi=110)
    pix.save(os.path.join(OUT, f"preview_{i+1}.png"))
print(f"converted {len(doc)} pages")
