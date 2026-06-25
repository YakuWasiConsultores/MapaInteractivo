import json
import os

transcript_path = r'C:\Users\Armandd\.gemini\antigravity\brain\57b52505-9f2b-4362-8e84-b2e5bd1ed76a\.system_generated\logs\transcript.jsonl'
output_path = r'H:\Yakuwarmi\mapas interactivos\historial_conversacion.md'

with open(transcript_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

md_content = '# Historial de Conversación y Contexto del Proyecto\n\n'
md_content += 'Este documento contiene el registro de las instrucciones dadas y los cambios realizados durante la construcción del mapa interactivo del Corredor Biodiverso.\n\n---\n\n'

for line in lines:
    try:
        step = json.loads(line.strip())
        
        if step.get('type') == 'USER_INPUT':
            content = step.get('content', '')
            if '<USER_REQUEST>' in content:
                content = content.split('<USER_REQUEST>')[1].split('</USER_REQUEST>')[0].strip()
            md_content += f'### 🧑 Usuario:\n\n{content}\n\n'
            
        elif step.get('type') == 'PLANNER_RESPONSE' and step.get('content'):
            response_content = step.get('content')
            md_content += f'### 🤖 Asistente:\n\n{response_content}\n\n---\n\n'
            
    except Exception as e:
        continue

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(md_content)

print(f'Exportado exitosamente a {output_path}')
