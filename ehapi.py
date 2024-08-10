from requests import Response, Session


class EHC:
    def __init__(self):
        self.ses = Session()
        self.exit_handles = []
        self.base = "http://localhost:8080/api"

    def __enter__(self):
        return self

    def __exit__(self, _typ, _val, _tb):
        for e in self.exit_handles:
            e()

    def get(self, method: str, params=None, data=None):
        return self.ses.get(f"{self.base}{method}", params=params, data=data)

    def get_gallery(self, gid: int):
        return self.handle_api_result(self.get(f"/gallery/{gid}"))

    def handle_api_result(self, re: Response):
        re = re.json()
        if re['ok']:
            return re['data']
        else:
            raise ValueError((re['status'], re['error']))

    def post(self, method: str, data=None, json=None, headers=None):
        return self.ses.post(f"{self.base}{method}", data=data, json=json, headers=headers)  # noqa: E501

    def update_file_meta_json(self, json):
        return self.handle_api_result(self.post("/filemeta", json=json))
