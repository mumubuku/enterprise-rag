import chromadb
from chromadb.config import Settings

chroma_path = "./data/chroma"

client = chromadb.PersistentClient(path=chroma_path)

print("=" * 60)
print("ChromaDB 向量库查询工具")
print("=" * 60)

collections = client.list_collections()
print(f"\n找到 {len(collections)} 个集合:")
for idx, collection in enumerate(collections, 1):
    count = collection.count()
    print(f"{idx}. {collection.name} (ID: {collection.id}) - 文档数: {count}")

if not collections:
    print("\n没有找到任何集合！")
    exit(0)

collection_with_data = None
for collection in collections:
    if collection.count() > 0:
        collection_with_data = collection
        break

if not collection_with_data:
    print("\n所有集合都是空的！")
    exit(0)

collection_name = collection_with_data.name
print(f"\n使用集合: {collection_name}")

collection = client.get_collection(collection_name)

count = collection.count()
print(f"文档总数: {count}")

print("\n" + "=" * 60)
print("获取所有文档（不使用向量查询）")
print("=" * 60)

all_results = collection.get(
    limit=10,
    include=["documents", "metadatas"]
)

print(f"\n前10个文档:")
for idx, (doc_id, document, metadata) in enumerate(zip(
    all_results['ids'],
    all_results['documents'],
    all_results['metadatas']
), 1):
    print(f"\n--- 文档 {idx} ---")
    print(f"文档ID: {doc_id}")
    print(f"文件名: {metadata.get('file_name', '未知')}")
    print(f"页码: {metadata.get('page', '未知')}")
    print(f"内容预览: {document[:150]}...")

print("\n" + "=" * 60)
print("按元数据过滤查询")
print("=" * 60)

file_name = all_results['metadatas'][0].get('file_name', '')
if file_name:
    print(f"\n查询文件名包含: {file_name}")
    
    filtered_results = collection.get(
        where={"file_name": file_name},
        limit=5,
        include=["documents", "metadatas"]
    )
    
    print(f"找到 {len(filtered_results['ids'])} 个文档:")
    for idx, (doc_id, document, metadata) in enumerate(zip(
        filtered_results['ids'],
        filtered_results['documents'],
        filtered_results['metadatas']
    ), 1):
        print(f"\n--- 文档 {idx} ---")
        print(f"文档ID: {doc_id}")
        print(f"页码: {metadata.get('page', '未知')}")
        print(f"内容预览: {document[:150]}...")

print("\n" + "=" * 60)
print("按页码过滤查询")
print("=" * 60)

page_num = all_results['metadatas'][0].get('page', 0)
print(f"\n查询页码: {page_num}")

filtered_results = collection.get(
    where={"page": page_num},
    limit=5,
    include=["documents", "metadatas"]
)

print(f"找到 {len(filtered_results['ids'])} 个文档:")
for idx, (doc_id, document, metadata) in enumerate(zip(
    filtered_results['ids'],
    filtered_results['documents'],
    filtered_results['metadatas']
), 1):
    print(f"\n--- 文档 {idx} ---")
    print(f"文档ID: {doc_id}")
    print(f"文件名: {metadata.get('file_name', '未知')}")
    print(f"内容预览: {document[:150]}...")

print("\n" + "=" * 60)
print("查询完成！")
print("=" * 60)
print("\n提示：要进行向量相似度查询，需要使用与创建向量库时相同的嵌入模型。")
print("当前向量库使用的嵌入模型维度为1536，可能是OpenAI的text-embedding-ada-002模型。")