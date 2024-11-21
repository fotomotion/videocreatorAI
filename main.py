import os
from dotenv import load_dotenv
from video_processor import VideoProcessor
import shutil
import json
from datetime import datetime

def create_output_structure(video_name: str) -> dict:
    # Remove a extensão do vídeo para usar como base do nome da pasta
    base_name = os.path.splitext(video_name)[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join('videos', 'final', f"{base_name}_{timestamp}")
    
    # Criar estrutura de pastas
    folders = {
        'root': output_dir,
        'transcription': os.path.join(output_dir, '1_transcricao'),
        'script': os.path.join(output_dir, '2_roteiro'),
        'prompts': os.path.join(output_dir, '3_prompts'),
        'images': os.path.join(output_dir, '4_imagens'),
        'video': os.path.join(output_dir, '5_video_original')
    }
    
    # Criar todas as pastas
    for folder in folders.values():
        os.makedirs(folder, exist_ok=True)
        
    return folders

def save_processing_results(folders: dict, result: dict, original_video_path: str):
    # 1. Salvar transcrição
    with open(os.path.join(folders['transcription'], 'transcricao.txt'), 'w', encoding='utf-8') as f:
        f.write(result['original_transcription'])
    
    # 2. Salvar novo roteiro
    with open(os.path.join(folders['script'], 'roteiro.txt'), 'w', encoding='utf-8') as f:
        f.write(result['new_script'])
    
    # 3. Salvar prompts
    with open(os.path.join(folders['prompts'], 'prompts.json'), 'w', encoding='utf-8') as f:
        json.dump(result['image_data'], f, ensure_ascii=False, indent=2)
    
    # Salvar prompts em formato texto também
    with open(os.path.join(folders['prompts'], 'prompts.txt'), 'w', encoding='utf-8') as f:
        for idx, prompt in enumerate(result['image_data']['image_prompts'], 1):
            f.write(f"Imagem {idx}:\n")
            f.write(f"Descrição: {prompt['description']}\n")
            f.write(f"Prompt: {prompt['prompt']}\n\n")
    
    # 4. Salvar informações das imagens
    with open(os.path.join(folders['images'], 'info_imagens.txt'), 'w', encoding='utf-8') as f:
        for idx, img_info in enumerate(result['generated_images'], 1):
            f.write(f"Imagem {idx}:\n")
            f.write(f"Descrição: {img_info['description']}\n")
            f.write(f"Prompt: {img_info['prompt']}\n")
            f.write(f"URL Original: {img_info['url']}\n")
            f.write(f"Arquivo Local: {os.path.basename(img_info['local_path'])}\n\n")
    
    # 5. Copiar vídeo original
    video_filename = os.path.basename(original_video_path)
    shutil.copy2(original_video_path, os.path.join(folders['video'], video_filename))

def process_pending_videos():
    # Load environment variables
    load_dotenv()
    groq_api_key = os.getenv('GROQ_API_KEY')
    replicate_api_key = os.getenv('REPLICATE_API_KEY')

    # Initialize the video processor
    processor = VideoProcessor(groq_api_key, replicate_api_key)

    # Define directories
    to_process_dir = os.path.join('videos', 'to_process')
    completed_dir = os.path.join('videos', 'completed')

    # Create directories if they don't exist
    os.makedirs(to_process_dir, exist_ok=True)
    os.makedirs(completed_dir, exist_ok=True)

    # Get list of videos to process
    videos = [f for f in os.listdir(to_process_dir) if f.endswith(('.mp4', '.avi', '.mov', '.mkv'))]

    if not videos:
        print("Nenhum vídeo encontrado na pasta 'to_process'.")
        return

    print(f"Encontrados {len(videos)} vídeos para processar.")

    # Process each video
    for video_file in videos:
        video_path = os.path.join(to_process_dir, video_file)
        print(f"\nProcessando: {video_file}")

        try:
            # Create output structure
            folders = create_output_structure(video_file)
            
            # Process the video
            result = processor.process_video(video_path, folders['images'])
            
            # Save results
            save_processing_results(folders, result, video_path)
            
            # Move original video to completed folder
            completed_path = os.path.join(completed_dir, video_file)
            shutil.move(video_path, completed_path)
            
            print(f"\nProcessamento concluído com sucesso!")
            print(f"Todos os arquivos foram salvos em: {folders['root']}")
            print(f"O vídeo original foi movido para: {completed_path}")

        except Exception as e:
            print(f"Erro ao processar {video_file}: {str(e)}")
            print("O vídeo permanecerá na pasta 'to_process'")

if __name__ == "__main__":
    process_pending_videos()
