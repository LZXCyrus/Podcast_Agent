import os
import dashscope
import time
import requests
import wave
import array

# 解析对话文本
def parse_dialogue(text):
    lines = text.strip().split('\n')
    dialogues = []
    for line in lines:
        if ': ' in line:
            speaker, content = line.split(': ', 1)
            dialogues.append({'speaker': speaker, 'content': content})
    return dialogues

# 生成 TTS 音频（指定输出为 WAV 格式）
def generate_tts_audio(text, voice, output_file):
    api_key = ""  # 从环境变量获取密钥
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY environment variable not set")

    response = dashscope.audio.qwen_tts.SpeechSynthesizer.call(
        model="qwen3-tts-flash",
        api_key=api_key,
        text=text,
        voice=voice,
        format='wav'  # 明确指定输出为 WAV 格式
    )

    if response.status_code == 200:
        audio_info = response.output.audio
        if audio_info.get('url'):
            audio_response = requests.get(audio_info['url'])
            if audio_response.status_code == 200:
                with open(output_file, 'wb') as f:
                    f.write(audio_response.content)
                print(f"音频已生成: {output_file}")
                return output_file
            else:
                print(f"下载音频失败，状态码: {audio_response.status_code}")
                return None
        else:
            print("音频 URL 不存在")
            return None
    else:
        print(f"API 请求失败，状态码: {response.status_code}")
        return None

# 使用 wave 模块合并 WAV 文件
def merge_wav_files(audio_files, output_file, pause_duration=1000):
    """合并多个 WAV 文件，在对话之间添加停顿（毫秒）"""
    if not audio_files:
        return None

    # 读取第一个文件获取参数（假设所有文件参数相同）
    with wave.open(audio_files[0], 'rb') as first:
        nchannels = first.getnchannels()
        sampwidth = first.getsampwidth()
        framerate = first.getframerate()
        nframes = first.getnframes()

    # 计算停顿的帧数
    pause_frames = int(framerate * pause_duration / 1000)

    with wave.open(output_file, 'wb') as output:
        output.setnchannels(nchannels)
        output.setsampwidth(sampwidth)
        output.setframerate(framerate)

        for i, audio_file in enumerate(audio_files):
            with wave.open(audio_file, 'rb') as audio:
                # 读取所有帧并写入
                frames = audio.readframes(audio.getnframes())
                output.writeframes(frames)

                # 添加停顿（静音），除了最后一个文件
                if i < len(audio_files) - 1:
                    # 生成静音数据（采样点值为 0）
                    silence = array.array('h', [0] * (nchannels * pause_frames))  # 'h' 表示 16 位有符号整数
                    silence_bytes = silence.tobytes()
                    output.writeframes(silence_bytes)

    print(f"合并后的音频已保存: {output_file}")
    return output_file

# 主生成函数
def generate_podcast(dialogue_text):
    dialogues = parse_dialogue(dialogue_text)
    voice_mapping = {
        "Speaker 1": "Ethan",
        "Speaker 2": "Cherry"
    }
    audio_files = []
    temp_files = []

    for i, dialogue in enumerate(dialogues):
        speaker = dialogue['speaker']
        content = dialogue['content']
        voice = voice_mapping.get(speaker, "Cherry")
        print(f"生成 {speaker} 的音频 (声音: {voice}): {content}")

        # 使用 /tmp 目录保存临时文件
        temp_file = f"/tmp/temp_speaker_{i + 1}.wav"
        audio_file = generate_tts_audio(content, voice, temp_file)
        if audio_file:
            audio_files.append(audio_file)
            temp_files.append(temp_file)
        time.sleep(1)  # 避免 API 限制

    if audio_files:
        final_output = "/tmp/podcast_dialogue.wav"
        merge_wav_files(audio_files, final_output, pause_duration=1500)
        return final_output
    else:
        return None
