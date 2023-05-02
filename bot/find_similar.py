import datetime

import openai
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

import sessionized
from config import (
    COLLECTION_NAME,
    QDRANT_API_KEY,
    QDRANT_HOST,
    QDRANT_PORT,
)

qdrant_client = QdrantClient(
    host=QDRANT_HOST,
    port=QDRANT_PORT,
    api_key=QDRANT_API_KEY,
)

retrieval_model = SentenceTransformer("msmarco-MiniLM-L-6-v3")


def nearest_neighbour(message_id, messages_neighbour_count, messages):
    # Проверка на корректность входных данных
    if message_id < 0 or message_id >= len(messages) or messages_neighbour_count < 0:
        return []

    # Вычисляем начальный и конечный индексы для среза
    start_index = max(message_id - messages_neighbour_count, 0)
    end_index = min(message_id + messages_neighbour_count + 1, len(messages))

    # Возвращаем срез массива
    return messages[start_index:end_index]


# Search for nearest messages in result.json according to session_number and message_number
def get_nearest_messages(session_number, message_number) -> list:
    sessionized_messages: list = sessionized.get_sessionized_message()
    current_message_session = sessionized_messages[session_number]

    min_message_number = 0
    max_message_number = len(current_message_session) - 1

    message_number = int(message_number)
    messages_neighbour_count = 3

    nearest_messages = nearest_neighbour(message_number, 3, current_message_session)

    return nearest_messages


def build_prompt(question: str, references: list) -> tuple[str, str]:
    prompt = f"""
    You're Marcus Aurelius, emperor of Rome. You're giving advice to a friend who has asked you the following question: '{question}'

    You've selected the most relevant passages from your writings to use as source for your answer. Cite them in your answer.

    References:
    """.strip()

    references_text = ""

    for i, reference in enumerate(references, start=1):
        text = reference.payload["text"].strip()
        # Convert date 2023-04-04T09:55:58 to 2023-04-04
        date = datetime.datetime.strptime(reference.payload["date"], "%Y-%m-%dT%H:%M:%S").date()
        date = date.strftime("%Y-%m-%d")

        session_number = reference.payload["session_number"]
        message_number = reference.payload["message_number"]

        nearest_messages = get_nearest_messages(session_number, message_number)

        formatted_nearest = ''

        for message in nearest_messages:
            message_date = datetime.datetime.strptime(message['date'], "%Y-%m-%dT%H:%M:%S").date()
            message_date = message_date.strftime("%Y-%m-%d")

            formatted_nearest += f"\nДата({message_date}) " \
                                 f"Старое похожее сообщение от {message['from']}: {message['text']}"
            # formatted_nearest += f"\nСессия({message['session_number']}) " \
            #                      f"num({message['message_number']}) " \
            #                      f"Дата({message['date']}) " \
            #                      f"Сообщение от {message['from']}: {message['text']}" \
            #                      f""

        references_text += formatted_nearest

    prompt += (
            references_text
            + "\nHow to cite a reference: This is a citation [1]. This one too [3]. And this is sentence with many citations [2][3].\nAnswer:"
    )
    return prompt, references_text


def find_similar_messages(question):
    similar_docs = qdrant_client.search(
        collection_name=COLLECTION_NAME,
        query_vector=retrieval_model.encode(question),
        limit=2,
        append_payload=True,
    )

    prompt, references = build_prompt(question, similar_docs)

    return references


if __name__ == "__main__":
    refs = find_similar_messages("ссылка")
    print(refs)