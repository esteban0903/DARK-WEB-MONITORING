import google.generativeai as genai

# Configurar API
GEMINI_API_KEY = "AIzaSyAgILdcUFng3HiepvL5xVMPHnd0vmckidk"
genai.configure(api_key=GEMINI_API_KEY)

print("Listando modelos disponibles:\n")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"✓ {m.name}")
        print(f"  Display Name: {m.display_name}")
        print(f"  Descripción: {m.description}")
        print()
