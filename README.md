# VideoCreator

Sistema de processamento de vídeos com IA para geração automática de conteúdo.

## Funcionalidades

- Transcrição automática de vídeos usando Whisper
- Geração de novo conteúdo baseado na transcrição usando Groq AI
- Geração de imagens usando Recraft AI
- Sistema de organização automática de arquivos

## Estrutura do Projeto

```
videos/
├── to_process/    # Coloque os vídeos a serem processados aqui
├── completed/     # Vídeos processados são movidos para cá
└── final/         # Resultados do processamento
    └── [nome_video]_[timestamp]/
        ├── 1_transcricao/
        ├── 2_roteiro/
        ├── 3_prompts/
        ├── 4_imagens/
        └── 5_video_original/
```

## Configuração

1. Clone o repositório
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure as variáveis de ambiente no arquivo `.env`:
   ```
   GROQ_API_KEY=sua_chave_groq
   REPLICATE_API_KEY=sua_chave_replicate
   ```

## Uso

1. Coloque os vídeos que deseja processar na pasta `videos/to_process/`
2. Execute o script:
   ```bash
   python3 main.py
   ```
3. Os resultados serão organizados em pastas dentro de `videos/final/`

## Dependências

- Python 3.10+
- whisper-openai
- groq
- replicate
- python-dotenv
- moviepy

## Licença

MIT
