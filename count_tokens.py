import json
import tiktoken
import argparse


def count_tokens(text, encoding):
    return len(encoding.encode(text))


def calculate_tokens_in_file(file_path, encoding_name, model_name, overhead):
    if encoding_name:
        encoding = tiktoken.get_encoding(encoding_name)
    elif model_name:
        encoding = tiktoken.encoding_for_model(model_name)
    else:
        encoding = tiktoken.get_encoding('cl100k_base')
    print('Encoding name:', encoding.name)
    total_tokens = 0

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            data = json.loads(line)
            messages = data.get('messages', [])
            for message in messages:
                content = message.get('content', '')
                tokens = count_tokens(content, encoding)
                total_tokens += tokens + overhead
    print(f"Total tokens in file: {total_tokens}")


def main():
    parser = argparse.ArgumentParser(description="Calculate the number of tokens in a JSONL file.")  # noqa: E501
    parser.add_argument('file_path', type=str, help='Path to the JSONL file')
    parser.add_argument('-e', '--encoding', type=str, help='Encoding to use for tokenization (default: cl100k_base)')  # noqa: E501
    parser.add_argument('-m', '--model', type=str, help='Encoding model')
    parser.add_argument('-o', '--overhead', type=int, default=3, help='Overhead token count for each message. Default: 3')  # noqa: E501

    args = parser.parse_args()

    calculate_tokens_in_file(args.file_path, args.encoding, args.model,
                             args.overhead)


if __name__ == "__main__":
    main()
