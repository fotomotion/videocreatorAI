import json
from typing import Dict, List
import requests
from moviepy.editor import VideoFileClip
import whisper
import os
import groq
from replicate import Client

class VideoProcessor:
    def __init__(self, groq_api_key: str, replicate_api_key: str):
        self.groq_client = groq.Groq(api_key=groq_api_key)
        self.replicate_client = Client(api_token=replicate_api_key)
        self.whisper_model = whisper.load_model("base")

    def transcribe_video(self, video_path: str) -> str:
        # Extract audio from video
        video = VideoFileClip(video_path)
        audio_path = "temp_audio.mp3"
        video.audio.write_audiofile(audio_path)
        
        # Transcribe audio
        result = self.whisper_model.transcribe(audio_path)
        os.remove(audio_path)
        return result["text"]

    def generate_similar_content(self, transcription: str) -> str:
        prompt = f"""
        Analise o seguinte conteúdo e crie algo similar mantendo o mesmo estilo e tom.
        Mantenha o mesmo tipo de linguagem e formato, mas crie um conteúdo novo e único:

        CONTEÚDO ORIGINAL:
        {transcription}
        """
        
        try:
            print("Gerando novo conteúdo...")
            completion = self.groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": prompt}]
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"Erro ao gerar novo conteúdo: {str(e)}")
            raise

    def create_image_prompts(self, script: str) -> Dict:
        prompt = f"""
        Analise o roteiro abaixo e crie 3 prompts para gerar imagens que representem momentos chave.
        Retorne APENAS o JSON, sem texto adicional, seguindo este formato:
        {{
            "script": "{script}",
            "image_prompts": [
                {{"description": "breve descrição da cena", "prompt": "prompt detalhado em inglês para gerar a imagem"}}
            ]
        }}

        ROTEIRO:
        {script}
        """
        
        try:
            print("Criando prompts para imagens...")
            completion = self.groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = completion.choices[0].message.content.strip()
            
            # Remover caracteres de escape indesejados
            response_text = response_text.replace('\\_', '_')
            
            try:
                # Tentar fazer o parse do JSON
                result = json.loads(response_text)
                print("✓ JSON parseado com sucesso")
                return result
            except json.JSONDecodeError:
                print(f"Erro ao parsear resposta JSON. Resposta recebida:\n{response_text}")
                # Tentar limpar a string e fazer o parse novamente
                cleaned_response = ''.join(response_text.splitlines())
                try:
                    result = json.loads(cleaned_response)
                    print("✓ JSON parseado com sucesso após limpeza")
                    return result
                except json.JSONDecodeError:
                    print("Erro ao parsear JSON mesmo após limpeza")
                    raise
        except Exception as e:
            print(f"Erro ao criar prompts para imagens: {str(e)}")
            raise

    def download_image(self, url: str, save_path: str) -> bool:
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e:
            print(f"Erro ao baixar imagem: {str(e)}")
            return False

    def generate_images(self, image_data: Dict, output_dir: str = None) -> List[Dict]:
        generated_images = []
        try:
            print("Gerando imagens...")
            for idx, prompt_data in enumerate(image_data["image_prompts"], 1):
                print(f"Gerando imagem {idx}...")
                output = self.replicate_client.run(
                    "recraft-ai/recraft-v3",
                    input={
                        "prompt": prompt_data["prompt"],
                        "size": "1024x1820"
                    }
                )
                
                # Verificar e imprimir a resposta para debug
                print(f"Resposta do modelo para imagem {idx}:", output)
                
                # Garantir que temos uma URL válida
                image_url = output[0] if isinstance(output, list) and output else output
                if not isinstance(image_url, str) or not image_url.startswith('http'):
                    print(f"URL inválida recebida para imagem {idx}: {image_url}")
                    continue
                
                image_info = {
                    "url": image_url,
                    "description": prompt_data["description"],
                    "prompt": prompt_data["prompt"],
                    "local_path": ""
                }
                
                # Se um diretório de saída foi especificado, baixar a imagem
                if output_dir:
                    image_filename = f"imagem_{idx}.webp"
                    image_path = os.path.join(output_dir, image_filename)
                    print(f"Tentando baixar imagem de: {image_url}")
                    if self.download_image(image_url, image_path):
                        image_info["local_path"] = image_path
                        print(f"✓ Imagem {idx} baixada com sucesso")
                    else:
                        print(f"✗ Falha ao baixar imagem {idx}")
                
                generated_images.append(image_info)
                
            return generated_images
        except Exception as e:
            print(f"Erro ao gerar imagens: {str(e)}")
            raise

    def process_video(self, video_path: str, output_dir: str = None) -> Dict:
        result = {
            "original_transcription": "",
            "new_script": "",
            "image_data": {"script": "", "image_prompts": []},
            "generated_images": []
        }
        
        print("\nIniciando processamento do vídeo...")
        
        try:
            # Transcrição
            print("1. Transcrevendo o vídeo...")
            result["original_transcription"] = self.transcribe_video(video_path)
            print("✓ Transcrição concluída")
        except Exception as e:
            print(f"Erro na transcrição: {str(e)}")
            return result
        
        try:
            # Novo roteiro
            print("\n2. Gerando novo roteiro...")
            result["new_script"] = self.generate_similar_content(result["original_transcription"])
            print("✓ Novo roteiro gerado")
        except Exception as e:
            print(f"Erro ao gerar novo roteiro: {str(e)}")
            return result
        
        try:
            # Prompts para imagens
            print("\n3. Criando prompts para imagens...")
            result["image_data"] = self.create_image_prompts(result["new_script"])
            print("✓ Prompts criados")
        except Exception as e:
            print(f"Erro ao criar prompts: {str(e)}")
            return result
        
        try:
            # Geração de imagens
            print("\n4. Gerando imagens...")
            result["generated_images"] = self.generate_images(result["image_data"], output_dir)
            print("✓ Imagens geradas")
        except Exception as e:
            print(f"Erro ao gerar imagens: {str(e)}")
            
        return result

# Exemplo de uso:
"""
processor = VideoProcessor(
    groq_api_key="seu_groq_api_key",
    replicate_api_key="seu_replicate_api_key"
)

result = processor.process_video("caminho_do_video.mp4")
"""