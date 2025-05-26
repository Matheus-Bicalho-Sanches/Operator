import os
import cv2
import mss
import numpy as np
import pyautogui
import json
from dotenv import load_dotenv
import threading
import openai
import base64

# Carrega a chave da API do arquivo .env
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    print("Erro: OPENAI_API_KEY não encontrada! Verifique seu arquivo .env.")
    exit(1)

openai.api_key = API_KEY
MODEL_ID = "gpt-4.1-mini"  # Usando OpenAI GPT-4.1 Mini (suporta texto + imagem)

# Kill switch global
kill_switch = threading.Event()

def kill_switch_listener():
    # Ativa o kill switch se Ctrl+Shift+Q for pressionado
    try:
        import keyboard
        while True:
            if keyboard.is_pressed('ctrl+shift+q'):
                print("[Sistema]: Kill switch ativado! Automação interrompida.")
                kill_switch.set()
                break
    except ImportError:
        print("[Sistema]: Instale o pacote 'keyboard' para usar o kill switch: pip install keyboard")

# Inicia o listener do kill switch em thread separada
threading.Thread(target=kill_switch_listener, daemon=True).start()

def capture_screen(monitor=1):
    with mss.mss() as sct:
        monitor = sct.monitors[monitor]  # 1 = tela inteira principal
        img = np.array(sct.grab(monitor))
        _, jpeg = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
        return jpeg.tobytes()

def img_bytes_to_base64(img_bytes):
    return base64.b64encode(img_bytes).decode('utf-8')

def ler_instrucoes():
    try:
        with open("instructions.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""

def executar_acao(resposta_ia):
    try:
        comando = json.loads(resposta_ia)
        # Se for um script (lista de ações)
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
            print("[Sistema]: Script de automação executado.")
        # Se for um comando simples
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
    except Exception as e:
        print("[Sistema]: Não foi possível interpretar/rodar comando JSON:", e)

def main():
    print("Sessão iniciada. Envie perguntas/comandos para o GPT-4.1 Mini. A cada pergunta, um print da tela será enviado junto.")
    print("Se a resposta da IA for um JSON de automação, o sistema executa. Caso contrário, apenas imprime a resposta.")
    print("[Kill switch]: Pressione Ctrl+Shift+Q para interromper a automação imediatamente.")
    while True:
        try:
            pergunta = input("Digite sua pergunta para o GPT-4.1 Mini (ou Ctrl+C para sair): ")
            img_bytes = capture_screen()
            img_b64 = img_bytes_to_base64(img_bytes)
            system_instruction = ler_instrucoes()
            prompt = ""
            if system_instruction:
                prompt += system_instruction + "\n\n"
            prompt += pergunta
            print("\n[Sistema][DEBUG] Prompt enviado ao modelo:\n" + prompt + "\n")
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
            # Tenta executar se for JSON, senão imprime normalmente
            try:
                executar_acao(resposta_ia)
            except Exception:
                print("[GPT-4.1 Mini]:", resposta_ia)
        except KeyboardInterrupt:
            print("\nSessão encerrada.")
            break

if __name__ == "__main__":
    main() 