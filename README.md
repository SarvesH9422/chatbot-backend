# 🤖 AI Chatbot – Modern Web UI with Groq & Dark Mode  

An elegant, mobile-friendly **AI chat interface** powered by **Groq’s Llama models**, featuring smooth animations, markdown-style replies, dark mode, and a clean chat UX.  

***

## ✨ Features  

- 🧠 **AI-powered chat** using Groq’s `llama-3.3-70b-versatile` model (configurable).  
- 💬 **Streaming-like UX** with typing indicator and typewriter effect for bot replies.  
- 🧩 **Rich text formatting**: bold, bullets, paragraphs rendered cleanly in the UI.  
- 🌗 **Dark / Light mode toggle** with smooth transitions and local preference saving.  
- 📱 **Mobile-first layout**: fixed header + input, only chat scrolls (optimized for phones).  
- 🧍 **Per-user conversations**: each user (or tab) has its own isolated chat history.  
- 🎨 **Modern UI/UX**: glassmorphism touches, gradients, rounded chat bubbles, icons.  
- 🧹 **Clear chat** button to reset the conversation instantly.  

***

## 🏗️ Tech Stack  

- **Frontend**  
  - HTML5, CSS3 (responsive, mobile-first)  
  - Vanilla JavaScript (no framework)  
  - Custom markdown-like renderer for messages  

- **Backend**  
  - Python + Flask  
  - Groq Python SDK for chat completions  
  - Simple in-memory per-session conversation store  

---

## 🚀 Getting Started  

### 1. Clone the repository  

```bash
git clone https://github.com/your-username/ai-chatbot-groq-ui.git
cd ai-chatbot-groq-ui
```

### 2. Create & activate a virtual environment (recommended)  

```bash
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows
```

### 3. Install dependencies  

```bash
pip install -r requirements.txt
```

Typical `requirements.txt` contains:  

```text
flask
flask-cors
groq
python-dotenv
```

***

### 4. Configure environment variables  

Create a `.env` file in the project root:  

```env
GROQ_API_KEY=your_groq_api_key_here
SECRET_KEY=some_super_secret_random_string
PORT=5000
```

- `GROQ_API_KEY` → your Groq API key from the Groq dashboard.  
- `SECRET_KEY` → any random string (for session security).  

***

### 5. Run the app locally  

```bash
python app.py
```

Then open in your browser:  

```text
http://localhost:5000
```

You should see the chatbot UI with:  
- Header, model badge, dark-mode toggle.  
- Chat area with welcome message.  
- Input bar with send + clear buttons.  

***

## 💡 How It Works  

### Backend Flow (Flask + Groq)  

- Maintains **per-user conversation history** using a session-based or ID-based key.  
- For each user message:
  - Appends `{ role: "user", content: "..." }` to that user’s history.  
  - Sends the full history to Groq’s chat completion API.  
  - Receives the AI message and appends `{ role: "assistant", content: "..." }`.  
- `POST /api/chat`  
  - Input: `{ "message": "your text" }`  
  - Output: `{ "status": "success", "response": "AI reply here..." }`  
- `POST /api/clear`  
  - Clears only the current user’s conversation.  

### Frontend Flow  

- Sends user input to `/api/chat` and shows:
  - User bubble immediately.  
  - Typing indicator while waiting for the response.  
  - Typewriter effect to render the formatted AI reply.  
- Parses markdown-style patterns from the AI:
  - `**bold**` → highlighted text.  
  - Lines starting with `-` / `*` → bullet points.  
  - `1.`, `2.` → numbered lists.  
- Dark mode:
  - Controlled via `data-theme="light" | "dark"` on `<html>`.  
  - Theme is stored in `localStorage` so it persists across reloads.  

***

## 🎛 Key UI/UX Features  

- **Header**  
  - Title, model badge, and a dark-mode toggle (🌙 / ☀️).  

- **Messages**  
  - User messages: right-aligned, blue gradient bubble.  
  - Assistant messages: left-aligned, light/dark bubble depending on theme.  
  - Typing indicator: animated dots + “Thinking…” text.  

- **Input Area**  
  - Wide textarea that auto-resizes.  
  - Small circular **send** button (➤ or SVG icon).  
  - Small circular **clear** button (🗑️ or SVG icon).  
  - Send button shows a loading spinner state while the request is in progress.  

- **Mobile Optimizations**  
  - Header and input bar remain visible; only chat content scrolls.  
  - Layout works correctly on devices like Redmi / Samsung / iPhone with soft keyboards.  

***

## 🌐 Deployment (Example: Render / Railway / Any VPS)  

1. Push your code to GitHub.  
2. Create a new web service (Python) on your hosting provider.  
3. Set build and start commands, for example:  

```bash
# Build
pip install -r requirements.txt

# Start
python app.py
```

4. Configure environment variables (`GROQ_API_KEY`, `SECRET_KEY`, `PORT`).  
5. Open the service URL in your browser to use the chatbot.  

***

## 🧪 Ideas & Extensions  

- 🧾 **Chat history persistence** in a database (PostgreSQL, MongoDB, etc.).  
- 👤 **Auth & profiles** so each logged-in user can save conversations.  
- 📚 **Knowledge grounding**: connect to your own documents or APIs.  
- 🌍 **Multi-language UI** and AI replies.  
- 🧩 **Plugin-style tools**: web search, code execution, calculators, etc.  

---

## 🤝 Contributing  

Contributions, issues, and feature requests are welcome!  

1. Fork the repo  
2. Create a feature branch  
3. Commit your changes  
4. Open a pull request  

***

## 📜 License  

This project is licensed under the **MIT License** – free to use, modify, and share.  

---

## ⭐ Support  

If you like this project:  

- ⭐ Star the repository  
- 🧑‍💻 Use it as a base for your own AI apps  
- 🔁 Share it with friends or teammates  

Happy building! 🚀

[7](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/88387933/3b3b0638-152b-4260-8b0e-170b0bbcc6f8/image.jpg)
[8](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/88387933/10d32034-24cc-4d1f-955a-efeaef9eb0c5/app.py)
[9](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/88387933/6b1f6f92-4e17-4ec0-943d-48508864d0cd/script.js)
