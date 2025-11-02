import os
import dashscope
from pydub import AudioSegment
import time
import requests


# 解析对话文本
def parse_dialogue(text):
    lines = text.strip().split('\n')
    dialogues = []

    for line in lines:
        if ': ' in line:
            speaker, content = line.split(': ', 1)
            dialogues.append({'speaker': speaker, 'content': content})

    return dialogues


# 生成TTS音频
def generate_tts_audio(text, voice, output_file):
    response = dashscope.audio.qwen_tts.SpeechSynthesizer.call(
        model="qwen3-tts-flash",
        api_key="",
        text=text,
        voice=voice,
    )

    if response.status_code == 200:
        audio_info = response.output.audio
        print(audio_info)

        # 检查是否有可用的音频URL
        if audio_info.get('url'):
            # 从URL下载音频文件
            audio_response = requests.get(audio_info['url'])

            if audio_response.status_code == 200:
                # 保存音频文件
                with open(output_file, 'wb') as f:
                    f.write(audio_response.content)
                print(f"音频已生成: {output_file}")
                return output_file
            else:
                print(f"下载音频失败，状态码: {audio_response.status_code}")
                return None
        else:
            print("音频URL不存在")
            return None
    else:
        print(f"API请求失败，状态码: {response.status_code}")
        return None


# 合并音频文件
def merge_audio_files(audio_files, output_file, pause_duration=1000):
    """合并多个音频文件，在对话之间添加停顿"""
    combined = AudioSegment.silent(duration=0)

    for i, audio_file in enumerate(audio_files):
        if audio_file and os.path.exists(audio_file):
            audio_segment = AudioSegment.from_file(audio_file)
            combined += audio_segment

            # 在对话之间添加停顿（除了最后一个）
            if i < len(audio_files) - 1:
                combined += AudioSegment.silent(duration=pause_duration)

    # 导出合并后的音频
    combined.export(output_file, format="wav")
    print(f"合并后的音频已保存: {output_file}")
    return output_file


# 主函数
def main():
    # 你的对话文本
    dialogue_text = """Speaker 1: I just finished reading that fascinating paper on the role of gut microbiota in neurodevelopment and I'm still processing it all.
Speaker 2: Oh, the one linking early-life microbiome composition to cognitive and behavioral outcomes later in life? That's a huge area of research now.
Speaker 1: Exactly. The paper really dives deep into the concept of the gut-brain axis, explaining the biochemical signaling pathways involved.
Speaker 2: It's incredible how they detailed the role of microbial metabolites like short-chain fatty acids in modulating neuroinflammation."""

    # 解析对话
    dialogues = parse_dialogue(dialogue_text)

    # 声音映射（根据阿里百炼可用声音调整）
    voice_mapping = {
        "Speaker 1": "Ethan",  # 磁性男声
        "Speaker 2": "Cherry"  # 年轻女声
    }

    # 为每个对话片段生成音频
    audio_files = []
    temp_files = []

    for i, dialogue in enumerate(dialogues):
        speaker = dialogue['speaker']
        content = dialogue['content']
        voice = voice_mapping.get(speaker, "Cherry")  # 默认使用Cherry

        print(f"生成 {speaker} 的音频 (声音: {voice}): {content}")

        temp_file = f"temp_speaker_{i + 1}.wav"
        audio_file = generate_tts_audio(content, voice, temp_file)

        if audio_file:
            audio_files.append(audio_file)
            temp_files.append(temp_file)

        # 添加短暂延迟避免API限制
        time.sleep(1)

    # 合并所有音频
    if audio_files:
        final_output = "podcast_dialogue.wav"
        merge_audio_files(audio_files, final_output, pause_duration=1500)  # 1.5秒停顿

        # 清理临时文件
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except:
                pass

        print(f"播客对话音频生成完成: {final_output}")
    else:
        print("音频生成失败")


if __name__ == "__main__":
    main()
