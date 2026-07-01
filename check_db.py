import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
col = client.get_collection("prompts")

print("Prompts:", col.count())
print("Malicious:", len(col.get(where={"label": 1}, include=[])["ids"]))
print("Benign:", len(col.get(where={"label": 0}, include=[])["ids"]))
