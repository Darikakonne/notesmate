
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate


def create_study_assistant(pages, api_key):
    documents = []

    for page in pages:
        documents.append(
            Document(
                page_content=page["content"],
                metadata={"page": page["page"]}
            )
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )

    chunks = splitter.split_documents(documents)

    embeddings = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-2",
        google_api_key=api_key
    )

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings
    )

    return vector_store


def ask_question(vector_store, question, api_key):
    relevant_docs = vector_store.similarity_search(
        question,
        k=4
    )

    context = "\n\n".join(
        f"Page {doc.metadata['page']}:\n{doc.page_content}"
        for doc in relevant_docs
    )

    prompt = ChatPromptTemplate.from_template("""
You are StudyMate AI, a helpful college study assistant.

Answer the student's question using ONLY the supplied notes.

INSTRUCTIONS:
1. Explain everything in simple English.
2. Give descriptive answers suitable for college students.
3. Use headings and bullet points where appropriate.
4. Explain technical terms with easy examples.
5. Never display JSON, XML, metadata or internal response objects.
6. Do not invent information missing from the notes.
7. Mention the original PDF page numbers.
8. Return a readable study answer, not technical output.

STUDY NOTES:
{context}

STUDENT QUESTION:
{question}

Write the final answer in clear, student-friendly English.
""")

    model = ChatGoogleGenerativeAI(
        model="gemini-3.8-flash",
        google_api_key=api_key
    )

    response = (prompt | model).invoke({
        "context": context,
        "question": question
    })

    content = response.content

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = []

        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(block.get("text", ""))

        return "\n".join(text_parts)

    return str(content)
