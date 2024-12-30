import openai
import httpx
import yaml
import argparse
import asyncio
import json
from typing import Optional


class Config:
    def __init__(self, args, yaml_config):
        self._args = args
        self._cfg = cfg

    @property
    def model(self) -> str:
        if self._args.model:
            return self._args.model
        if 'model' in self._cfg and isinstance(self._cfg['model'], str):
            return self._cfg['model']
        return 'gpt-4o-mini'

    @property
    def max_completion_tokens(self) -> int:
        if self._args.max_completion_tokens:
            return self._args.max_completion_tokens
        if 'max_completion_tokens' in self._cfg and isinstance(self._cfg['max_completion_tokens'], int):  # noqa: E501
            return self._cfg['max_completion_tokens']
        return 4096

    @property
    def include_usage(self) -> bool:
        if self._args.include_usage:
            return self._args.include_usage
        if 'include_usage' in self._cfg and isinstance(self._cfg['include_usage'], bool):  # noqa: E501
            return self._cfg['include_usage']
        return False

    @property
    def output(self) -> Optional[str]:
        if self._args.output:
            return self._args.output
        if 'output' in self._cfg and isinstance(self._cfg['output'], str):
            return self._cfg['output']
        return None

    @property
    def temperature(self) -> float:
        if self._args.temperature:
            if self._args.temperature >= 0.0 and self._args.temperature <= 2.0:
                return self._args.temperature
        if 'temperature' in self._cfg and isinstance(self._cfg['temperature'], float):  # noqa: E501
            temperature = self._cfg['temperature']
            if temperature >= 0.0 and temperature <= 2.0:
                return temperature
        return 1.0

    @property
    def top_p(self) -> float:
        if self._args.top_p:
            if self._args.top_p >= 0.0 and self._args.top_p <= 1.0:
                return self._args.top_p
        if 'top_p' in self._cfg and isinstance(self._cfg['top_p'], float):
            top_p = self._cfg['top_p']
            if top_p >= 0.0 and top_p <= 1.0:
                return top_p
        return 1.0

    @property
    def presence_penalty(self) -> float:
        if self._args.presence_penalty:
            if self._args.presence_penalty >= -2.0 and self._args.presence_penalty <= 2.0:  # noqa: E501
                return self._args.presence_penalty
        if 'presence_penalty' in self._cfg and isinstance(self._cfg['presence_penalty'], float):  # noqa: E501
            presence_penalty = self._cfg['presence_penalty']
            if presence_penalty >= -2.0 and presence_penalty <= 2.0:
                return presence_penalty
        return 0.0

    @property
    def store(self) -> bool:
        if self._args.store:
            return self._args.store
        if 'store' in self._cfg and isinstance(self._cfg['store'], bool):
            return self._cfg['store']
        return False

    @property
    def proxy(self) -> Optional[str]:
        if self._args.proxy:
            return self._args.proxy
        if 'proxy' in self._cfg and isinstance(self._cfg['proxy'], str):
            return self._cfg['proxy']
        return None

    @property
    def skip_verify(self) -> bool:
        if self._args.skip_verify:
            return self._args.skip_verify
        if 'skip_verify' in self._cfg and isinstance(self._cfg['skip_verify'], bool):  # noqa: E501
            return self._cfg['skip_verify']
        return False


def load_config(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    openai.api_key = config['api_key']
    if 'base_url' in config:
        openai.base_url = config['base_url']
    return config


def get_user_prompt():
    prompt = ""
    print("Enter your prompt (leave empty to finish):")
    while True:
        line = input('')
        if line.strip() == "":
            break
        prompt += line + "\n"
    return prompt.strip()


async def stream_response(messages, prompt, args: Config):
    cli = httpx.AsyncClient(proxy=args.proxy, verify=not args.skip_verify)
    client = openai.AsyncClient(api_key=openai.api_key,
                                base_url=openai.base_url,
                                http_client=cli)
    messages.append({"role": "user", "content": prompt})
    response = await client.chat.completions.create(
        model=args.model,
        max_completion_tokens=args.max_completion_tokens,
        messages=messages,
        stream_options={"include_usage": args.include_usage},
        temperature=args.temperature,
        top_p=args.top_p,
        presence_penalty=args.presence_penalty,
        store=args.store,
        stream=True
    )
    res = ''
    async for chunk in response:
        if chunk.choices:
            choice = chunk.choices[0]
            if choice.delta and choice.delta.content:
                data = choice.delta.content
                res += data
                print(data, end='', flush=True)
    print(flush=True)
    if chunk.usage:
        print(f"Usage: {chunk.usage.to_json(indent=None)}")
    return {'role': 'assistant', 'content': res}


async def chat(args: Config):
    messages = []
    while True:
        try:
            user_prompt = get_user_prompt()
        except KeyboardInterrupt:
            break
        while True:
            try:
                res = await stream_response(messages, user_prompt, args)
                messages.append(res)
                break
            except KeyboardInterrupt:
                break
            except openai.InternalServerError:
                print("Internal server error, retrying...")
                continue
    if args.output and len(messages):
        save_to_jsonl(args.output, messages)


def save_to_jsonl(file_path, message):
    with open(file_path, 'a', encoding='utf-8') as f:
        json.dump({'messages': message}, f, ensure_ascii=False,
                  separators=(',', ':'))
        f.write('\n')


parser = argparse.ArgumentParser(description="Chat with OpenAI's model.")
parser.add_argument('-m', '--model', type=str, help='Chat model to use')  # noqa: E501
parser.add_argument('-M', '--max-completion-tokens', type=int, help='Maximum length of the response')  # noqa: E501
parser.add_argument('-c', '--config', type=str, default='./chat.yml', help='Path to the configuration file')  # noqa: E501
parser.add_argument('-o', '--output', type=str, help='Path to the output JSONL file')  # noqa: E501
parser.add_argument('-i', '--include-usage', action='store_true', help='Include usage information in the response')  # noqa: E501
parser.add_argument('-t', '--temperature', type=float, help='What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic. ')  # noqa: E501
parser.add_argument('-p', '--top-p', type=float, help='An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.')  # noqa: E501
parser.add_argument('-P', '--presence-penalty', type=float, help="Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the text so far, increasing the model's likelihood to talk about new topics.")  # noqa: E501
parser.add_argument('-s', '--store', action='store_true', help='Whether or not to store the output of this chat completion request for use in our model distillation or evals products.')  # noqa: E501
parser.add_argument('-x', '--proxy', type=str, help='Proxy server URL to use for requests')  # noqa: E501
parser.add_argument('-k', '--skip-verify', action='store_true', help='Skip SSL certificate verification for HTTPS requests')  # noqa: E501


if __name__ == "__main__":
    args = parser.parse_args()
    cfg = load_config(args.config)
    acfg = Config(args, cfg)
    asyncio.run(chat(acfg))
