from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
import os

# Assurez-vous que le dossier static/icons existe
os.makedirs("static/icons", exist_ok=True)

# Conversion du fichier SVG en PNG
drawing = svg2rlg("static/icons/icon-192x192.svg")
renderPM.drawToFile(drawing, "static/icons/icon-192x192.png", fmt="PNG") 