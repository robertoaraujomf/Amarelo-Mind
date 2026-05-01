#!/usr/bin/env python3
"""Gera ícones intuitivos e sugestivos para a toolbar."""

import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPainter, QPixmap, QColor, QPen, QBrush
from PySide6.QtCore import Qt, QRectF, QPointF

def criar_icon(tipo):
    """Cria um ícone de 256x256 com design intuitivo."""
    pix = QPixmap(256, 256)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    
    if tipo == "novo":
        # Página branca/doc novo - mais intuitivo
        p.setBrush(QBrush(QColor("#2d6a4f")))
        p.setPen(QPen(Qt.NoPen))
        p.drawRoundedRect(QRectF(40, 40, 176, 196), 15, 15)
        # dobrinha no canto
        p.setBrush(QBrush(QColor("#3d7a5f")))
        p.drawPolygon([QPointF(160, 40), QPointF(216, 40), QPointF(216, 96), QPointF(160, 80)])
        # linhas de texto
        p.setPen(QPen(QColor("#ffffff"), 8))
        p.drawLine(64, 100, 192, 100)
        p.drawLine(64, 140, 176, 140)
        p.drawLine(64, 180, 140, 180)
        
    elif tipo == "abrir":
        # Pasta aberta com seta para baixo - Abrir
        p.setBrush(QBrush(QColor("#ff8c00")))
        p.setPen(QPen(Qt.NoPen))
        p.drawRoundedRect(QRectF(30, 70, 196, 155), 15, 15)
        # Aba da pasta
        p.setBrush(QBrush(QColor("#ffaa33")))
        p.drawRoundedRect(QRectF(30, 35, 196, 50), 12, 12)
        # Seta apontando para baixo dentro
        p.setPen(QPen(QColor("#ffffff"), 14, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(128, 100, 128, 170)
        p.drawLine(100, 140, 128, 170)
        p.drawLine(156, 140, 128, 170)
        
    elif tipo == "salvar":
        # Disquete clássico - Salvar
        p.setBrush(QBrush(QColor("#6e7681")))
        p.setPen(QPen(Qt.NoPen))
        p.drawRoundedRect(QRectF(50, 60, 156, 155), 12, 12)
        # Tampa superior (etiqueta)
        p.setBrush(QBrush(QColor("#2d6a4f")))
        p.drawRoundedRect(QRectF(65, 30, 126, 45), 8, 8)
        # Furos de Borracha
        p.setBrush(QBrush(QColor("#4a5568")))
        p.drawEllipse(90, 175, 20, 20)
        p.drawEllipse(166, 175, 20, 20)
        # Checkmark
        p.setPen(QPen(QColor("#90EE90"), 10, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(108, 210, 138, 240)
        p.drawLine(138, 240, 180, 180)
        
    elif tipo == "desfazer":
        # Seta curva para esquerda com volta
        p.setPen(QPen(QColor("#2d6a4f"), 20, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(180, 70, 80, 128)
        p.drawLine(80, 70, 180, 214)
        p.drawLine(80, 128, 180, 186)
        # Triângulo
        p.setBrush(QBrush(QColor("#2d6a4f")))
        p.drawPolygon([QPointF(80, 128), QPointF(35, 80), QPointF(35, 176)])
        
    elif tipo == "refazer":
        # Seta curva para direita
        p.setPen(QPen(QColor("#2d6a4f"), 20, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(76, 70, 176, 128)
        p.setPen(QPen(QColor("#2d6a4f"), 16, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(76, 128, 176, 186)
        p.drawLine(176, 128, 76, 214)
        # Triângulo
        p.setBrush(QBrush(QColor("#2d6a4f")))
        p.drawPolygon([QPointF(176, 128), QPointF(221, 80), QPointF(221, 176)])
        
    elif tipo == "copiar":
        # Dois retângulos sobrepostos - Copiar
        p.setBrush(QBrush(QColor("#00b4d8")))
        p.setPen(QPen(Qt.NoPen))
        p.drawRoundedRect(QRectF(45, 45, 140, 166), 12, 12)
        # Segundo retângulo levemente deslocado
        p.setBrush(QBrush(QColor("#0077b6")))
        p.drawRoundedRect(QRectF(71, 45, 140, 166), 12, 12)
        # Seta indicando copia
        p.setPen(QPen(QColor("#ffffff"), 10, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(156, 95, 200, 140)
        
    elif tipo == "colar":
        # Prancheta com clipe - Colar
        p.setBrush(QBrush(QColor("#00b4d8")))
        p.setPen(QPen(Qt.NoPen))
        p.drawRoundedRect(QRectF(40, 50, 176, 175), 12, 12)
        # Clipe no topo
        p.setBrush(QBrush(QColor("#ffd700")))
        p.drawRoundedRect(QRectF(98, 25, 60, 40), 6, 6)
        # Linhas de texto
        p.setPen(QPen(QColor("#ffffff"), 8))
        p.drawLine(70, 105, 186, 105)
        p.drawLine(70, 150, 150, 150)
        p.drawLine(70, 195, 110, 195)
        
    elif tipo == "midia":
        # Claquete de cinema - Mídia
        p.setBrush(QBrush(QColor("#ff6b6b")))
        p.setPen(QPen(Qt.NoPen))
        p.drawRoundedRect(QRectF(35, 90, 145, 120), 10, 10)
        # Haste suporte
        p.setBrush(QBrush(QColor("#8b949e")))
        p.drawRoundedRect(QRectF(180, 100, 30, 80), 4, 4)
        # Detalhe filme
        p.setBrush(QBrush(QColor("#cc5555")))
        p.drawRoundedRect(QRectF(45, 100, 125, 40), 6, 6)
        p.setBrush(QBrush(QColor("#e53935")))
        p.drawEllipse(65, 112, 20, 16)
        
    elif tipo == "ocultar":
        # Olho - mostrar
        p.setBrush(QBrush(Qt.NoBrush))
        p.setPen(QPen(QColor("#2d6a4f"), 14))
        p.drawRoundedRect(QRectF(40, 75, 176, 100), 55, 55)
        p.setBrush(QBrush(QColor("#2d6a4f")))
        p.drawEllipse(88, 100, 80, 80)
        p.setBrush(QBrush(QColor("#ffffff")))
        p.drawEllipse(108, 120, 40, 40)
        p.setBrush(QBrush(QColor("#0d1117")))
        p.drawEllipse(123, 135, 20, 20)
        
    elif tipo == "ocultar_off":
        # Olho riscado - ocultar 
        p.setBrush(QBrush(Qt.NoBrush))
        p.setPen(QPen(QColor("#ff6b6b"), 14))
        p.drawRoundedRect(QRectF(40, 75, 176, 100), 55, 55)
        p.setBrush(QBrush(QColor("#ff6b6b")))
        p.drawEllipse(88, 100, 80, 80)
        p.setBrush(QBrush(QColor("#cc5555")))
        p.drawEllipse(108, 120, 40, 40)
        # Risco no olho
        p.setPen(QPen(QColor("#8b0000"), 16, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(60, 100, 196, 180)
        
    elif tipo == "ajuda":
        # Ponto de interrogação - Ajuda
        p.setBrush(QBrush(QColor("#ffd700")))
        p.setPen(QPen(Qt.NoPen))
        p.drawRoundedRect(QRectF(78, 40, 100, 175), 50, 50)
        # Detalhe ponto
        p.setBrush(QBrush(QColor("#0d1117")))
        p.drawEllipse(103, 95, 30, 30)
        # Ponto do ?
        p.setBrush(QBrush(QColor("#0d1117")))
        p.drawEllipse(113, 165, 35, 35)
        
    elif tipo == "sobre":
        # Info - Sobre
        p.setBrush(QBrush(QColor("#2d6a4f")))
        p.setPen(QPen(Qt.NoPen))
        p.drawRoundedRect(QRectF(90, 45, 76, 80), 12, 12)
        p.drawRoundedRect(QRectF(108, 140, 40, 45), 20, 20)
        # i
        p.setBrush(QBrush(QColor("#ffffff")))
        p.drawEllipse(113, 65, 20, 20)
        p.setBrush(QBrush(QColor("#0d1117")))
        p.drawPolygon([QPointF(128, 140), QPointF(128, 185), QPointF(108, 185)])
        
    p.end()
    return pix


# Restaurar app_icon dos velhos
import shutil
if os.path.exists("assets/icons_old/App_icon.png"):
    shutil.copy("assets/icons_old/App_icon.png", "assets/icons/App_icon.png")
if os.path.exists("assets/icons_old/App_icon.ico"):
    shutil.copy("assets/icons_old/App_icon.ico", "assets/icons/App_icon.ico")

# Recriar ícones específicos (0,1,2,4,5,6,7,9,11,17,18)
icons = [
    ("Novo.png", "novo"),
    ("Abrir.png", "abrir"),
    ("Salvar.png", "salvar"),
    ("Desfazer.png", "desfazer"),
    ("Refazer.png", "refazer"),
    ("Copiar.png", "copiar"),
    ("Colar.png", "colar"),
    ("Midia.png", "midia"),
    ("Ocultar.png", "ocultar"),
    ("Ajuda.png", "ajuda"),
    ("Sobre.png", "sobre"),
]

app = QApplication([])
for filename, tipo in icons:
    print(f"Criando {filename}...")
    pix = criar_icon(tipo)
    pix.save(f"assets/icons/{filename}")

# Criar versão oculta (olho riscado)
print("Criando Ocultar_off.png...")
pix = criar_icon("ocultar_off")
pix.save("assets/icons/Ocultar_off.png")

print("\nFeito!")
app.quit()