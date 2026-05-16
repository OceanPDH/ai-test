"""
RAG Pipeline
============
1. 读取知识库文档 → 切块
2. 用本地 sentence-transformers 生成 embedding → 存入 ChromaDB
3. 用户提问 → 检索 Top-K 文档块
4. 拼接 context + question → 调用 DeepSeek 生成回答
"""

import os
import glob
from openai import OpenAI
import chromadb
from sentence_transformers import SentenceTransformer

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")
if not DEEPSEEK_API_KEY:
    raise EnvironmentError("请设置 DEEPSEEK_API_KEY 环境变量")

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
embedder = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.Client()


def load_and_chunk(docs_dir: str, chunk_size: int = 300) -> list[dict]:
    """读取 markdown 文件，按段落切块"""
    chunks = []
    for path in glob.glob(f"{docs_dir}/*.md"):
        with open(path, encoding="utf-8") as f:
            content = f.read()
        # 按双换行分段，过滤空段
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        for i, para in enumerate(paragraphs):
            chunks.append({
                "id": f"{os.path.basename(path)}_{i}",
                "text": para,
                "source": os.path.basename(path),
            })
    return chunks


def build_index(chunks: list[dict], collection_name: str = "knowledge_base"):
    """将文本块 embedding 后存入 ChromaDB"""
    try:
        chroma_client.delete_collection(collection_name)
    except Exception:
        pass
    collection = chroma_client.create_collection(collection_name)

    texts = [c["text"] for c in chunks]
    embeddings = embedder.encode(texts).tolist()

    collection.add(
        ids=[c["id"] for c in chunks],
        embeddings=embeddings,
        documents=texts,
        metadatas=[{"source": c["source"]} for c in chunks],
    )
    return collection


def retrieve(collection, query: str, top_k: int = 3) -> list[str]:
    """检索与问题最相关的 top_k 文档块"""
    query_embedding = embedder.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=top_k)
    return results["documents"][0]  # list of strings


def generate(question: str, contexts: list[str]) -> str:
    """将检索结果拼接成 context，调用 DeepSeek 生成回答"""
    context_text = "\n\n".join(f"[文档片段]\n{ctx}" for ctx in contexts)
    prompt = f"""你是一个产品帮助中心助手，只根据以下文档内容回答问题，不要编造文档中没有的信息。

{context_text}

用户问题：{question}

请用中文简洁回答："""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return response.choices[0].message.content


class RAGPipeline:
    def __init__(self, docs_dir: str):
        print("正在加载知识库...")
        chunks = load_and_chunk(docs_dir)
        print(f"共 {len(chunks)} 个文档块，正在构建索引...")
        self.collection = build_index(chunks)
        print("索引构建完成。\n")

    def query(self, question: str, top_k: int = 3) -> dict:
        contexts = retrieve(self.collection, question, top_k)
        answer = generate(question, contexts)
        return {
            "question": question,
            "contexts": contexts,
            "answer": answer,
        }


if __name__ == "__main__":
    pipeline = RAGPipeline("knowledge_base")
    result = pipeline.query("Pro 版本每个月多少钱？")
    print("问题：", result["question"])
    print("回答：", result["answer"])
    print("\n召回文档：")
    for i, ctx in enumerate(result["contexts"]):
        print(f"  [{i+1}] {ctx[:80]}...")
