#!/usr/bin/env python3
"""
Script de limpeza para o projeto Amarelo Mind
Remove arquivos temporários e desnecessários
"""

import os
import glob
import shutil

def clean_project():
    """Remove arquivos desnecessários do projeto"""
    
    print("Limpando projeto Amarelo Mind...")
    
    # Remover arquivos de cache Python
    cache_patterns = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo",
        "**/*.pyd",
        ".pytest_cache",
        ".mypy_cache"
    ]
    
    removed_count = 0
    for pattern in cache_patterns:
        for item in glob.glob(pattern, recursive=True):
            try:
                if os.path.isdir(item):
                    shutil.rmtree(item)
                    print(f"Removido diretório: {item}")
                else:
                    os.remove(item)
                    print(f"Removido arquivo: {item}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Erro ao remover {item}: {e}")
    
    # Remover arquivos de build
    build_patterns = [
        "build",
        "dist",
        "*.egg-info"
    ]
    
    for pattern in build_patterns:
        for item in glob.glob(pattern):
            try:
                if os.path.isdir(item):
                    shutil.rmtree(item)
                    print(f"Removido diretório de build: {item}")
                else:
                    os.remove(item)
                    print(f"Removido arquivo de build: {item}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Erro ao remover {item}: {e}")
    
    print(f"\nLimpeza concluída! {removed_count} arquivos/diretórios removidos.")
    
    # Verificar arquivos essenciais
    essential_files = [
        "main.py",
        "requirements.txt",
        "README.md",
        "assets/",
        "core/",
        "items/"
    ]
    
    print("\nVerificando arquivos essenciais:")
    for item in essential_files:
        if os.path.exists(item):
            print(f"[OK] {item}")
        else:
            print(f"[FALTA] {item}")

if __name__ == "__main__":
    clean_project()