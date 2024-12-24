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

    def list_galleries(self, offset: int = 0, limit: int = 20,
                       all: bool = False, fields: str = '*',
                       sort_by_gid: bool = None, uploader: str = None,
                       category: str = None):
        params = {}
        if not all:
            params['offset'] = offset
            params['limit'] = limit
        else:
            params['all'] = '1'
        if fields and fields != '*':
            params['fields'] = fields
        if sort_by_gid is not None:
            params['sort_by_gid'] = '1' if sort_by_gid else '0'
        if uploader:
            params['uploader'] = uploader
        if category:
            params['category'] = category
        return self.handle_api_result(self.get("/gallery/list", params=params))

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
