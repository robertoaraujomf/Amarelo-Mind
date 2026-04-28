#!/usr/bin/env python3
"""Gera ícones coloridos e sugestivos para a toolbar."""

import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPainter, QPixmap, QColor, QPen, QBrush
from PySide6.QtCore import Qt, QRectF, QPointF

def criar_icon(nome, descritivo):
    """Cria um ícone de 256x256."""
    pix = QPixmap(256, 256)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    
    if descritivo == "novo":
        p.setBrush(QBrush(QColor("#2d6a4f")))
        p.setPen(QPen(Qt.NoPen))
        p.drawRoundedRect(QRectF(50, 50, 156, 176), 15, 15)
        p.setPen(QPen(QColor("#ffffff"), 6))
        p.drawLine(80, 100, 176, 100)
        p.drawLine(80, 140, 156, 140)
        p.drawLine(80, 180, 130, 180)
        
    elif descritivo == "abrir":
        p.setBrush(QBrush(QColor("#ff8c00")))
        p.setPen(QPen(Qt.NoPen))
        p.drawRoundedRect(QRectF(40, 70, 176, 150), 15, 15)
        p.setBrush(QBrush(QColor("#ffaa33")))
        p.drawRoundedRect(QRectF(40, 40, 176, 45), 10, 10)
        p.setPen(QPen(QColor("#ffffff"), 10))
        p.drawLine(100, 130, 156, 175)
        
    elif descritivo == "salvar":
        p.setBrush(QBrush(QColor("#6e7681")))
        p.setPen(QPen(Qt.NoPen))
        p.drawRoundedRect(QRectF(55, 55, 146, 156), 12, 12)
        p.setBrush(QBrush(QColor("#2d6a4f")))
        p.drawRoundedRect(QRectF(70, 30, 116, 40), 8, 8)
        
    elif descritivo == "exportar":
        p.setBrush(QBrush(QColor("#00b4d8")))
        p.setPen(QPen(Qt.NoPen))
        p.drawRoundedRect(QRectF(40, 40, 176, 176), 15, 15)
        p.setBrush(QBrush(QColor("#2d6a4f")))
        p.drawPolygon([QPointF(60, 200), QPointF(100, 100), QPointF(150, 160), QPointF(196, 90), QPointF(196, 200)])
        p.setBrush(QBrush(QColor("#ffd700")))
        p.drawEllipse(QRectF(170, 55, 30, 30))
        
    elif descritivo == "desfazer":
        p.setPen(QPen(QColor("#2d6a4f"), 18, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(180, 60, 80, 128)
        p.drawLine(80, 60, 180, 196)
        # Triângulo (simplificado com drawPolygon)
        pts = [QPointF(80, 128), QPointF(40, 90), QPointF(40, 166)]
        p.setBrush(QBrush(QColor("#2d6a4f")))
        p.drawPolygon(pts)
        
    elif descritivo == "refazer":
        p.setPen(QPen(QColor("#2d6a4f"), 18, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(76, 60, 176, 128)
        p.drawLine(76, 196, 176, 128)
        pts = [QPointF(176, 128), QPointF(216, 90), QPointF(216, 166)]
        p.setBrush(QBrush(QColor("#2d6a4f")))
        p.drawPolygon(pts)
        
    elif descritivo == "copiar":
        p.setBrush(QBrush(QColor("#00b4d8")))
        p.setPen(QPen(Qt.NoPen))
        p.drawRoundedRect(QRectF(50, 50, 130, 156), 12, 12)
        p.setBrush(QBrush(QColor("#0077b6")))
        p.drawRoundedRect(QRectF(76, 50, 130, 156), 12, 12)
        
    elif descritivo == "colar":
        p.setBrush(QBrush(QColor("#00b4d8")))
        p.setPen(QPen(Qt.NoPen))
        p.drawRoundedRect(QRectF(45, 45, 166, 170), 12, 12)
        p.setPen(QPen(QColor("#ffffff"), 6))
        p.drawLine(75, 95, 181, 95)
        p.drawLine(75, 135, 150, 135)
        p.drawLine(75, 175, 120, 175)
        
    elif descritivo == "adicionar":
        p.setBrush(QBrush(QColor("#2d6a4f")))
        p.setPen(QPen(Qt.NoPen))
        p.drawEllipse(58, 58, 140, 140)
        p.setPen(QPen(QColor("#ffffff"), 16, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(128, 85, 128, 171)
        p.drawLine(85, 128, 171, 128)
        
    elif descritivo == "midia":
        p.setBrush(QBrush(QColor("#ff6b6b")))
        p.setPen(QPen(Qt.NoPen))
        p.drawRoundedRect(QRectF(35, 85, 145, 115), 10, 10)
        p.setBrush(QBrush(QColor("#cc5555")))
        p.drawRoundedRect(QRectF(45, 55, 125, 45), 8, 8)
        
    elif descritivo == "conectar":
        p.setBrush(QBrush(QColor("#00b4d8")))
        p.setPen(QPen(Qt.NoPen))
        p.drawEllipse(50, 85, 90, 90)
        p.drawEllipse(116, 85, 90, 90)
        p.setPen(QPen(QColor("#ffffff"), 8))
        p.drawLine(125, 130, 131, 130)
        
    elif descritivo == "ocultar":
        p.setBrush(QBrush(Qt.NoBrush))
        p.setPen(QPen(QColor("#2d6a4f"), 12))
        p.drawRoundedRect(QRectF(45, 85, 166, 95), 50, 50)
        p.setBrush(QBrush(QColor("#2d6a4f")))
        p.drawEllipse(83, 105, 55, 55)
        p.setBrush(QBrush(QColor("#0f1621")))
        p.drawEllipse(98, 120, 25, 25)
        
    elif descritivo == "excluir":
        p.setBrush(QBrush(QColor("#ff6b6b")))
        p.setPen(QPen(Qt.NoPen))
        p.drawRoundedRect(QRectF(65, 95, 126, 130), 10, 10)
        p.setBrush(QBrush(QColor("#cc5555")))
        p.drawRoundedRect(QRectF(55, 65, 146, 40), 8, 8)
        p.setPen(QPen(QColor("#ffffff"), 8))
        p.drawLine(100, 135, 156, 175)
        p.drawLine(156, 135, 100, 175)
        
    elif descritivo == "fonte":
        p.setPen(QPen(QColor("#ffd700"), 14, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(85, 200, 128, 60)
        p.drawLine(128, 60, 171, 200)
        p.drawLine(100, 160, 156, 160)
        
    elif descritivo == "cores":
        p.setBrush(QBrush(QColor("#ffffff")))
        p.setPen(QPen(Qt.NoPen))
        p.drawRoundedRect(QRectF(45, 45, 166, 166), 12, 12)
        cores = ["#ff6b6b", "#ffd700", "#2d6a4f", "#00b4d8", "#9d4edd"]
        for i, c in enumerate(cores):
            p.setBrush(QBrush(c))
            x = 60 + (i % 3) * 50
            y = 60 + (i // 3) * 50
            p.drawEllipse(QRectF(x, y, 40, 40))
            
    elif descritivo == "localizar":
        p.setBrush(QBrush(Qt.NoBrush))
        p.setPen(QPen(QColor("#00b4d8"), 10))
        p.drawEllipse(70, 70, 100, 100)
        p.drawLine(155, 155, 205, 205)
        p.setBrush(QBrush(QColor("#003366")))
        p.drawEllipse(QRectF(95, 95, 50, 50))
        
    elif descritivo == "teclado":
        p.setBrush(QBrush(QColor("#6e7681")))
        p.setPen(QPen(Qt.NoPen))
        p.drawRoundedRect(QRectF(35, 55, 186, 146), 12, 12)
        p.setBrush(QBrush(QColor("#8b949e")))
        for y in [80, 120, 160]:
            p.drawRoundedRect(QRectF(55, y, 40, 25), 4, 4)
            p.drawRoundedRect(QRectF(108, y, 40, 25), 4, 4)
            p.drawRoundedRect(QRectF(161, y, 40, 25), 4, 4)
            
    elif descritivo == "ajuda":
        p.setBrush(QBrush(QColor("#ffd700")))
        p.setPen(QPen(Qt.NoPen))
        p.drawRoundedRect(QRectF(83, 45, 90, 165), 45, 45)
        p.setBrush(QBrush(QColor("#0f1621")))
        p.drawEllipse(QRectF(108, 100, 25, 25))
        
    elif descritivo == "sobre":
        p.setBrush(QBrush(QColor("#2d6a4f")))
        p.setPen(QPen(Qt.NoPen))
        p.drawRoundedRect(QRectF(95, 45, 66, 75), 10, 10)
        p.drawRoundedRect(QRectF(108, 140, 40, 40), 20, 20)
        
    p.end()
    return pix


icons_map = {
    "Novo.png": "novo",
    "Abrir.png": "abrir", 
    "Salvar.png": "salvar",
    "Exportar.png": "exportar",
    "Desfazer.png": "desfazer",
    "Refazer.png": "refazer",
    "Copiar.png": "copiar",
    "Colar.png": "colar",
    "Adicionar.png": "adicionar",
    "Midia.png": "midia",
    "Conectar.png": "conectar",
    "Ocultar.png": "ocultar",
    "Excluir.png": "excluir",
    "Fonte.png": "fonte",
    "Cores.png": "cores",
    "Localizar.png": "localizar",
    "TecladeAtalho.png": "teclado",
    "Ajuda.png": "ajuda",
    "Sobre.png": "sobre",
}

app = QApplication([])
output_dir = "assets/icons_new"
os.makedirs(output_dir, exist_ok=True)

for filename, descritivo in icons_map.items():
    print(f"Criando {filename}...")
    pix = criar_icon(filename, descritivo)
    pix.save(f"{output_dir}/{filename}")

print(f"\nFeito! Ícones em {output_dir}/")
app.quit()