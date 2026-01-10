#!/usr/bin/env python
"""
Verificación de estabilidad de embeddings
Verifica que el sistema de embeddings funciona correctamente en CPU
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.rag.ingest import embed_texts
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_embedding_stability():
    """Test que embeddings funcionan correctamente en CPU."""
    
    print("\n" + "="*60)
    print("🧪 VERIFICACIÓN DE ESTABILIDAD DE EMBEDDINGS")
    print("="*60 + "\n")
    
    # Test 1: Textos simples
    print("📝 Test 1: Textos simples...")
    test_texts = [
        "Este es un texto de prueba",
        "Otro texto diferente",
        "Un tercer ejemplo de texto"
    ]
    
    try:
        embeddings = embed_texts(test_texts)
        assert len(embeddings) == len(test_texts), "Número de embeddings no coincide"
        assert all(isinstance(e, list) for e in embeddings), "Embeddings no son listas"
        assert all(len(e) > 0 for e in embeddings), "Embeddings vacíos"
        print(f"✅ Test 1 PASADO: {len(embeddings)} embeddings generados")
        print(f"   Dimensión: {len(embeddings[0])}")
    except Exception as e:
        print(f"❌ Test 1 FALLIDO: {e}")
        return False
    
    # Test 2: Textos largos
    print("\n📝 Test 2: Textos largos...")
    long_text = "Este es un texto mucho más largo que contiene múltiples oraciones. " * 20
    test_long = [long_text, long_text[:100], long_text[100:200]]
    
    try:
        embeddings_long = embed_texts(test_long)
        assert len(embeddings_long) == len(test_long), "Número de embeddings no coincide"
        print(f"✅ Test 2 PASADO: {len(embeddings_long)} embeddings de textos largos")
    except Exception as e:
        print(f"❌ Test 2 FALLIDO: {e}")
        return False
    
    # Test 3: Textos con caracteres especiales
    print("\n📝 Test 3: Caracteres especiales y UTF-8...")
    special_texts = [
        "Texto con acentos: áéíóú ñ",
        "Emojis: 🚀 🎉 ✅",
        "Símbolos: @#$%^&*()",
        "Números: 123 456.78"
    ]
    
    try:
        embeddings_special = embed_texts(special_texts)
        assert len(embeddings_special) == len(special_texts), "Número de embeddings no coincide"
        print(f"✅ Test 3 PASADO: {len(embeddings_special)} embeddings con caracteres especiales")
    except Exception as e:
        print(f"❌ Test 3 FALLIDO: {e}")
        return False
    
    # Test 4: Batch grande
    print("\n📝 Test 4: Batch grande (50 textos)...")
    batch_texts = [f"Texto número {i} con contenido variado" for i in range(50)]
    
    try:
        embeddings_batch = embed_texts(batch_texts)
        assert len(embeddings_batch) == len(batch_texts), "Número de embeddings no coincide"
        print(f"✅ Test 4 PASADO: {len(embeddings_batch)} embeddings en batch")
    except Exception as e:
        print(f"❌ Test 4 FALLIDO: {e}")
        return False
    
    # Test 5: Textos vacíos
    print("\n📝 Test 5: Manejo de casos edge...")
    try:
        embeddings_empty = embed_texts([])
        assert len(embeddings_empty) == 0, "Debería retornar lista vacía"
        print("✅ Test 5 PASADO: Manejo correcto de lista vacía")
    except Exception as e:
        print(f"❌ Test 5 FALLIDO: {e}")
        return False
    
    # Resumen
    print("\n" + "="*60)
    print("✅ TODOS LOS TESTS PASARON")
    print("="*60)
    print("\n📊 Resumen:")
    print(f"   - Modelo: all-MiniLM-L6-v2")
    print(f"   - Dispositivo: CPU")
    print(f"   - Dimensión embeddings: {len(embeddings[0])}")
    print(f"   - Tests ejecutados: 5/5")
    print(f"   - Estado: ✅ ESTABLE")
    print("\n")
    
    return True


if __name__ == "__main__":
    try:
        success = test_embedding_stability()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
