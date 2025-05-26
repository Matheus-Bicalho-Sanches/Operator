import os
import cv2
import mss
import numpy as np
import pyautogui
import json
from dotenv import load_dotenv
import threading
import base64
import re

# Importa as bibliotecas de IA
try:
    import openai
except ImportError:
    openai = None
try:
    from google import genai
except ImportError:
    genai = None

# Carrega as chaves das APIs do arquivo .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("API_AI")

# Kill switch global
kill_switch = threading.Event()

def kill_switch_listener():
    try:
        import keyboard
        while True:
            if keyboard.is_pressed('ctrl+shift+q'):
                print("[Sistema]: Kill switch ativado! Automação interrompida.")
                kill_switch.set()
                break
    except ImportError:
        print("[Sistema]: Instale o pacote 'keyboard' para usar o kill switch: pip install keyboard")

threading.Thread(target=kill_switch_listener, daemon=True).start()

def capture_screen(monitor=1):
    with mss.mss() as sct:
        monitor = sct.monitors[monitor]  # 1 = tela inteira principal
        img = np.array(sct.grab(monitor))
        _, jpeg = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
        return jpeg.tobytes()

def img_bytes_to_base64(img_bytes):
    return base64.b64encode(img_bytes).decode('utf-8')

def ler_instrucoes(width=None, height=None):
    try:
        with open("instructions.txt", "r", encoding="utf-8") as f:
            instr = f.read().strip()
            if width and height:
                instr += f"\n\n[RESOLUCAO_ATUAL_DA_TELA: {width}x{height}]"
            return instr
    except Exception:
        return ""

def get_screen_resolution(monitor=1):
    with mss.mss() as sct:
        monitor_info = sct.monitors[monitor]
        width = monitor_info['width']
        height = monitor_info['height']
        return width, height

def executar_acao(resposta_ia):
    # Procura todos os blocos JSON na resposta
    blocos_json = re.findall(r'```json\s*(\{[\s\S]*?\})\s*```', resposta_ia)
    if blocos_json:
        for bloco in blocos_json:
            try:
                comando = json.loads(bloco)
                if "script" in comando and isinstance(comando["script"], list):
                    for step in comando["script"]:
                        if kill_switch.is_set():
                            print("[Sistema]: Automação interrompida pelo kill switch.")
                            break
                        acao = step.get("action")
                        if acao in ("move_to", "move_mouse"):
                            pyautogui.moveTo(step["x"], step["y"], duration=0.25)
                        elif acao == "click":
                            pyautogui.click()
                        elif acao == "type":
                            pyautogui.write(step["text"])
                        elif acao == "hotkey":
                            pyautogui.hotkey(*step["keys"])
                        else:
                            print("Ação não reconhecida no script:", step)
                    print("[IA]:", bloco)
                else:
                    acao = comando.get("action")
                    if acao in ("move_to", "move_mouse"):
                        pyautogui.moveTo(comando["x"], comando["y"], duration=0.25)
                    elif acao == "click":
                        pyautogui.click()
                    elif acao == "type":
                        pyautogui.write(comando["text"])
                    elif acao == "hotkey":
                        pyautogui.hotkey(*comando["keys"])
                    else:
                        print("Ação não reconhecida:", comando)
                    print("[Sistema]: Comando executado:", comando)
            except Exception:
                print("[IA]: Falha ao interpretar bloco JSON:", bloco)
        # Exibe qualquer texto fora dos blocos JSON
        texto_fora_json = re.sub(r'```json[\s\S]*?```', '', resposta_ia).strip()
        if texto_fora_json:
            print("[IA]:", texto_fora_json)
    else:
        # Se não houver JSON, exibe normalmente
        print("[IA]:", resposta_ia)

def objetivo_atingido(resposta_ia):
    # Critérios simples: IA diz que objetivo foi atingido/concluído
    frases_fim = [
        "objetivo concluído", "tarefa concluída", "finalizado", "concluído", "atingido", "feito", "pronto", "completo"
    ]
    texto = resposta_ia.lower()
    return any(frase in texto for frase in frases_fim)

def main():
    print("Selecione o modelo de IA para usar:")
    print("1 - OpenAI GPT-4.1 Mini (openai)")
    print("2 - Gemma 3 27B (google)")
    modelo = input("Digite 1 ou 2: ").strip()
    if modelo == "1":
        if not openai or not OPENAI_API_KEY:
            print("[Erro]: Biblioteca openai não instalada ou chave não encontrada.")
            return
        openai.api_key = OPENAI_API_KEY
        MODEL_ID = "gpt-4.1-mini"
        print("Sessão iniciada. Usando OpenAI GPT-4.1 Mini.")
        print("Se a resposta da IA for um JSON de automação, o sistema executa. Caso contrário, apenas imprime a resposta.")
        print("[Kill switch]: Pressione Ctrl+Shift+Q para interromper a automação imediatamente.")
        objetivo = input("Descreva o objetivo da automação (ex: 'Abra o Chrome e acesse o site X'): ")
        contexto = objetivo
        while True:
            if kill_switch.is_set():
                print("[Sistema]: Kill switch ativado. Loop interrompido.")
                break
            try:
                img_bytes = capture_screen()
                img_b64 = img_bytes_to_base64(img_bytes)
                width, height = get_screen_resolution()
                system_instruction = ler_instrucoes(width, height)
                prompt = ""
                if system_instruction:
                    prompt += system_instruction + "\n\n"
                prompt += f"OBJETIVO: {objetivo}\n"
                prompt += f"CONTEXTO: {contexto}\n"
                # Monta a mensagem para o chat completions
                messages = [
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                    ]}
                ]
                response = openai.chat.completions.create(
                    model=MODEL_ID,
                    messages=messages
                )
                resposta_ia = response.choices[0].message.content.strip()
                executar_acao(resposta_ia)
                if objetivo_atingido(resposta_ia):
                    print("[Sistema]: Objetivo declarado como concluído pela IA. Loop encerrado.")
                    break
                contexto = resposta_ia  # Atualiza contexto para próxima iteração
            except KeyboardInterrupt:
                print("\nSessão encerrada.")
                break
    elif modelo == "2":
        if not genai or not GOOGLE_API_KEY:
            print("[Erro]: Biblioteca google-genai não instalada ou chave não encontrada.")
            return
        client = genai.Client(api_key=GOOGLE_API_KEY)
        MODEL_ID = "models/gemma-3-27b-it"
        print("Sessão iniciada. Usando Gemma 3 27B.")
        print("Se a resposta da IA for um JSON de automação, o sistema executa. Caso contrário, apenas imprime a resposta.")
        print("[Kill switch]: Pressione Ctrl+Shift+Q para interromper a automação imediatamente.")
        objetivo = input("Descreva o objetivo da automação (ex: 'Abra o Chrome e acesse o site X'): ")
        contexto = objetivo
        while True:
            if kill_switch.is_set():
                print("[Sistema]: Kill switch ativado. Loop interrompido.")
                break
            try:
                img_bytes = capture_screen()
                width, height = get_screen_resolution()
                system_instruction = ler_instrucoes(width, height)
                prompt = ""
                if system_instruction:
                    prompt += system_instruction + "\n\n"
                prompt += f"OBJETIVO: {objetivo}\n"
                prompt += f"CONTEXTO: {contexto}\n"
                contents = []
                contents.append({"role": "user", "parts": [
                    {"text": prompt},
                    {"inline_data": {"data": img_bytes, "mime_type": "image/jpeg"}}
                ]})
                response = client.models.generate_content(
                    model=MODEL_ID,
                    contents=contents
                )
                resposta_ia = response.text.strip()
                executar_acao(resposta_ia)
                if objetivo_atingido(resposta_ia):
                    print("[Sistema]: Objetivo declarado como concluído pela IA. Loop encerrado.")
                    break
                contexto = resposta_ia
            except KeyboardInterrupt:
                print("\nSessão encerrada.")
                break
    else:
        print("Opção inválida. Encerrando.")

if __name__ == "__main__":
    main() 