import os
import tempfile
import streamlit as st
import zipfile
import PyPDF2
import pyttsx3
from io import BytesIO

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
    return text

# Function to split text into sections based on numbered lines
def split_text_by_numbered_lines(text):
    sections = []
    current_section = ''
    for line in text.split('\n'):
        if line.strip().startswith(tuple(str(i) for i in range(10))):  # Check if line starts with a number
            if current_section:
                sections.append(current_section.strip())
            current_section = line + ' '
        else:
            current_section += line + ' '
    if current_section:
        sections.append(current_section.strip())
    return sections

# Function to convert text sections to speech and save as WAV files
def text_to_speech(sections, output_folder):
    engine = pyttsx3.init()
    audio_files = []
    for i, section in enumerate(sections):
        audio_file = os.path.join(output_folder, f'section_{i+1}.wav')
        engine.save_to_file(section, audio_file)
        audio_files.append(audio_file)
    engine.runAndWait()  # Wait for all speech tasks to complete
    return audio_files

# Function to combine a single video and audio file using FFmpeg
def combine_video_audio(video_path, audio_path, output_path):
    cmd = f"ffmpeg -i {video_path} -i {audio_path} -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 -shortest {output_path}"
    os.system(cmd)

# Function to process videos and audio files
def process_videos_and_audios(video_files, audio_files, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    num_outputs = max(len(video_files), len(audio_files))

    for i in range(num_outputs):
        video_index = i % len(video_files)
        audio_index = i % len(audio_files)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
            temp_video.write(video_files[video_index].getbuffer())
            video_path = temp_video.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            with open(audio_files[audio_index], 'rb') as audio_file:
                temp_audio.write(audio_file.read())
            audio_path = temp_audio.name

        output_path = os.path.join(output_folder, f"output_video_{i + 1}.mp4")
        combine_video_audio(video_path, audio_path, output_path)

        os.remove(video_path)
        os.remove(audio_path)

# Function to create a ZIP archive of all files in the output folder
def create_zip(output_folder, zip_path):
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for root, _, files in os.walk(output_folder):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.basename(file_path))

# Main Streamlit app
def main():
    st.title("Flexible Video and PDF-to-Speech Combiner")
    st.write("Upload video files and a PDF file. The app will convert the PDF text to speech and combine it with the videos.")

    # File uploaders for videos and PDF
    video_files = st.file_uploader("Upload video files", type=["mp4", "avi", "mov"], accept_multiple_files=True)
    pdf_file = st.file_uploader("Upload a PDF file", type="pdf")

    if video_files and pdf_file:
        output_folder = tempfile.mkdtemp()
        if st.button("Combine Videos and PDF-to-Speech"):
            st.write("Processing... This may take a while depending on the file sizes.")

            # Save the uploaded PDF file temporarily
            temp_pdf_path = os.path.join(output_folder, "temp.pdf")
            with open(temp_pdf_path, "wb") as f:
                f.write(pdf_file.getbuffer())

            # Extract text from PDF
            text = extract_text_from_pdf(temp_pdf_path)

            # Split text into sections
            sections = split_text_by_numbered_lines(text)

            # Convert text to speech
            audio_files = text_to_speech(sections, output_folder)

            # Process videos and audio files
            process_videos_and_audios(video_files, audio_files, output_folder)
            st.success("Processing complete!")

            # Create a ZIP file of all output videos
            zip_path = os.path.join(output_folder, "output_videos.zip")
            create_zip(output_folder, zip_path)

            # Provide a download link for the ZIP file
            st.write("Download all combined videos:")
            with open(zip_path, "rb") as f:
                st.download_button(
                    label="Download All Videos as ZIP",
                    data=f,
                    file_name="output_videos.zip",
                    mime="application/zip",
                )

            # Clean up temporary files
            os.remove(temp_pdf_path)
            for file in os.listdir(output_folder):
                os.remove(os.path.join(output_folder, file))
            os.rmdir(output_folder)

# Run the Streamlit app
if __name__ == "__main__":
    main()