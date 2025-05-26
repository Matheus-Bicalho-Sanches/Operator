# Projeto: Assistente Multimodal com Gemma 3 e Automação Local

## Objetivo
Desenvolver uma aplicação que capture vídeo ao vivo da tela do computador do usuário e transmita os frames em tempo real para o modelo Gemma 3 via Live API (WebSockets), permitindo que o modelo receba o fluxo multimodal, produza respostas e gere function calls para executar comandos locais (mouse, teclado, etc). O objetivo é permitir que o usuário dê comandos verbais e o Gemma consiga usar o mouse e teclado para realizar tarefas no computador.

## Arquitetura Sugerida

```
[Tela do Usuário] --> [App Python] <==> [WebSocket] <==> [Gemma 3 Live API]
                                         |
                                         v
                                [Automação Local: pyautogui, etc]
```

- **Captura de tela:** Captura frames da tela do usuário (não webcam).
- **Transmissão:** Envia frames via WebSocket para a API do Gemma 3.
- **Recepção:** Recebe respostas e function calls do modelo.
- **Automação:** Executa comandos locais (mouse, teclado) conforme instruções do modelo.

## Passo a Passo Inicial

### 1. Preparação do Ambiente
- Instale Python 3.8+
- Instale as bibliotecas necessárias:
  - `pip install opencv-python mss websockets pyautogui google-genai`

### 2. Captura de Tela
- Use a biblioteca `mss` para capturar frames da tela do computador.
- Converta os frames para um formato leve (ex: JPEG/base64) para transmissão.

### 3. Conexão com a Live API do Gemma 3
- Utilize a biblioteca oficial `google-genai` para Python.
- Configure a sessão para resposta em texto (`response_modalities: ["TEXT"]`).
- Envie os frames capturados como input de vídeo em tempo real usando o método adequado (`send_realtime_input`).

### 4. Recepção de Respostas
- Receba as respostas do modelo (texto ou function calls).
- Interprete as function calls para automação local.

### 5. Automação Local
- Use `pyautogui` para executar comandos de mouse e teclado conforme solicitado pelo modelo.

### 6. (Opcional) Captura e Envio de Áudio
- Após o vídeo, implemente captura de áudio do microfone e envie para o modelo.

## Observações Importantes
- A Live API do Gemma 3 aceita streaming de vídeo e áudio via WebSocket.
- O modelo pode responder com texto, áudio ou function calls (para automação).
- A autenticação deve ser feita via API Key (NUNCA exponha a chave em código público).
- O envio de vídeo deve ser feito em tempo real, preferencialmente em baixa resolução para reduzir latência.

## Referências
- [Documentação oficial da Live API do Gemini/Gemma](https://ai.google.dev/gemini-api/docs/live)
- [Exemplo de uso da API com vídeo e áudio](https://ai.google.dev/gemini-api/docs/live)
- [Biblioteca google-genai para Python](https://pypi.org/project/google-genai/)
- [mss para captura de tela](https://python-mss.github.io/)
- [pyautogui para automação](https://pyautogui.readthedocs.io/en/latest/)

---

## Próximos Passos
1. Implementar a captura de tela e envio dos frames para a API.
2. Testar a recepção de respostas do modelo.
3. Implementar a automação local baseada nas function calls recebidas.
4. (Opcional) Adicionar suporte a comandos de voz. 