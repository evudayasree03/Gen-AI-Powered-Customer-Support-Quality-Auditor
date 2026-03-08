In this task, I have to transcribe the call logs and summarize the calls and summarize the text Documents. I am using whisper to transcribe the call logs (from speech to text conversion) and GROQ's LLM "llama-3.3-70b-versatile" for summarization of both calls and text documents. The application supports large input files using chunk-based processing and provides an interactive web interface using Streamlit.

1. View of the Frontend and Uploading Call Log:
   &nbsp;&nbsp;&nbsp;
<img width="960" height="600" alt="Screenshot (138)" src="https://github.com/user-attachments/assets/a76ff0c8-9804-479f-a1d8-6ae17f809805" />
&nbsp;&nbsp;&nbsp;

2. Transcribing the call log:
&nbsp;&nbsp;&nbsp;
<img width="960" height="600" alt="Screenshot (140)" src="https://github.com/user-attachments/assets/bf184488-126a-43e7-8d5a-5a84d9872b0d" />
&nbsp;&nbsp;&nbsp;

3. Generating the Summary of the Call :
&nbsp;&nbsp;&nbsp;
It generates a concise and clear summary and it displays the speakers in the call and Speaker diarization.
&nbsp;&nbsp;&nbsp;
For call Logs :  
&nbsp;&nbsp;&nbsp;
<img width="960" height="600" alt="Screenshot (141)" src="https://github.com/user-attachments/assets/41766923-7219-4573-9d34-e6e8a4808ad4" />

&nbsp;&nbsp;&nbsp;

For chat conversations : 
<img width="960" height="600" alt="Screenshot (143)" src="https://github.com/user-attachments/assets/aaf932d5-db83-433c-a723-421e6350d96c" />

&nbsp;&nbsp;&nbsp;

&nbsp;&nbsp;&nbsp;
By clicking on the download button, we will be able to download the summary of the call log or chat conversation.



