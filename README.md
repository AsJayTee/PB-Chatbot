# Psychology Blossom Chatbot

![Psychology Blossom logo](resources/logo.png "Logo")

A powerful chatbot platform designed for **Psychology Blossom**, a Singapore-based counselling service. This chatbot helps clients find suitable therapists based on their preferences and answers frequently asked questions about the services offered.

---

## 🗝️ Key Features

### ⚙️ Optimized Retrieval-Augmented Generation (RAG) System
The chatbot employs a **custom RAG architecture** that optimizes for both accuracy and cost-efficiency. 

Unlike traditional RAG systems that embed entire document chunks, this architecture takes full advantage of the **structured nature** of Q&A data by embedding only the questions.

- **Smart Query Handling**: Refines user queries with contextual awareness.
- **Semantic Similarity Search**: Retrieves context efficiently by matching queries to pre-indexed questions using cosine similarity.
- **Direct Q&A Mapping**: Each embedded question maps directly to a corresponding answer, ensuring precise results.

By keeping answeres separate from embeddings, we:
- Prevent answers from skewing the embedding vectors.
- Eliminate the need for re-embedding when answers change. 

This enhances retrieval precision while keeping operational costs low.

### 🧠 Intelligent Therapist Matching
The system implements a **robust filtering mechanism** to match clients with therapists:

- **Multi-factor Filtering**: Matches therapists based on factors like:
  - Gender preferences
  - Language requirements
  - Specializations (anxiety, depression, etc.)
  - Target patient age groups (adults, children and teens)
  - Price range preferences
  - Appointment availability
- **Persistent Preference Memory**: The `Preferences` class maintains the client's stated preferences across the entire conversation, eliminating reliance on the LLM's conversational memory.
- **Set-based Operations**: Uses efficient set intersections to narrow down suitable therapists based on accumulated preferences.
- **Fuzzy Matching**: Implements distance calculations to handle slight misspellings or variations in preference statements.

This preference system provides reliable recommendations without the risk of hallucinations by structuring preference handling outside the LLM's memory.

### 🔧 Tool-Driven Reliability
The chatbot operates through a robust **tool-calling system** designed for reliability:

- **Minimal Argument Dependency**: Most tools operate without arguments or parameters, instead directly accessing the conversation.
- **Hardcoded Operations**: Core functionality is implemented in dedicated Python classes rather than relying on LLM reasoning.

This structured approach significantly reduces the opportunity for errors, especially for complex preferences that can often shift between being:
- **Relative** - "slightly cheaper", "available earlier", etc.
- **Absolute** - "speaks Mandarin", "available on Mondays", etc.

### ✨ Future Development
There are future plans to integrate an **appointment scheduling system** directly into the chatbot.

---

## Getting Started

### Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/your-repo/psychology-blossom-chatbot.git
   ```
2. Copy `.env.example` to `.env` and add your OpenAI API key.
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
4. Run the demo interface:
   ```sh
   streamlit run demo.py
   ```

### Demo Interface
The demo features an simple Streamlit web interface:

![Screenshot of the chatbot in use](resources/demo.png "Demo")

### Try It Online
Experience the chatbot in action on Streamlit:

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://pb-chatbot-demo.streamlit.app)

For access requests, please contact [AsJayTee](https://github.com/AsJayTee) on GitHub.

## Afterword
I'm grateful to **Psychology Blossom** for their support in making this chatbot a reality. Their commitment to mental health has helped shape a tool that makes finding the right support easier and more accessible.

Mental well-being is just as important as physical health. If you or someone you know needs help, don’t hesitate to reach out to them at:
- 🌐 **Website**: [psychologyblossom.com](https://psychologyblossom.com/)
- 📧 **Email**: hello@psychologyblossom.com
- 📞 **Phone**: +65 8686 8592

You’re never alone, help is always within reach. 💙
