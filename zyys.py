from argparse import ArgumentParser
from getpass import getpass
from hashlib import sha1 as _sha1
from json import dumps as _dumps, load
from math import ceil
from random import random
from urllib.parse import urlencode
from requests import Session


def stringify(json):
    return _dumps(json, ensure_ascii=False, separators=(",", ":"))


def sha1(data: str):
    f = _sha1()
    f.update(data.encode())
    return f.hexdigest()


class Client():
    MYSHOP_FORAPP_KEY = "987654321"
    SOFTWARE = "0"
    LOGINDEVICETYPE = "android"
    FROMANDROID = "1"
    VERSION = "131"
    DEVICEID = "设备Id获取失败,null值!版本\u003d131"

    def __init__(self):
        self._ses = Session()
        self._ses.headers.update({
            "User-Agent": "okhttp/3.6.0",
            "Accept-Encoding": "gzip",
        })
        self._baseUrl = "http://39.104.60.22:6023/"
        self._token = ""
        self._fromteacher = False
        self._portalUrl = None

    def check_in(self, longitude: float, latitude: float, localname, note):
        if self._portalUrl is None:
            raise Exception("请先选择医院")
        if not self._token:
            raise Exception("请先登录")
        url = self._portalUrl + "doctor_train/rest/ningboschedule/signstudent.do"  # noqa: E501
        url += f"?{self.get_base_params()}"
        d = stringify({
            "logindevicetype": self.LOGINDEVICETYPE,
            "longitude": f"{longitude:.06f}",
            "latitude": f"{latitude:.06f}",
            "fromandroid": self.FROMANDROID,
            "note": note,
            "fromteacher": "1" if self._fromteacher else "0",
            "localname": localname,
        })
        re = self._ses.post(url, data={"data": d})
        if re.status_code != 200:
            raise Exception(f"HTTP {re.status_code} {re.reason}")
        return self.check_error2(re.json())

    def check_error(self, r):
        if r["code"] != "1" or "data" not in r or r["data"] is None:
            raise Exception(f"Error: {r['msg']}")
        return r["data"]

    def check_error2(self, r):
        if r["code"] != "1":
            raise Exception(f"Error: {r['msg']}")
        return r

    def get_base_params(self):
        d = {
            "token": self._token,
            "myshop_app_key": self.MYSHOP_FORAPP_KEY,
            "software": self.SOFTWARE,
        }
        return urlencode(d)

    def get_ningbo_schedule_init_data(self):
        if self._portalUrl is None:
            raise Exception("请先选择医院")
        if not self._token:
            raise Exception("请先登录")
        url = self._portalUrl + "doctor_train/rest/ningboschedule/getInitData.do"  # noqa: E501
        url += f"?{self.get_base_params()}"
        d = stringify({
            "logindevicetype": self.LOGINDEVICETYPE,
            "fromteacher": "1" if self._fromteacher else "0",
            "fromandroid": self.FROMANDROID,
        })
        re = self._ses.post(url, data={"data": d})
        if re.status_code != 200:
            raise Exception(f"HTTP {re.status_code} {re.reason}")
        return self.check_error2(re.json())

    def login_check(self, loginid: str, password: str):
        if self._portalUrl is None:
            raise Exception("请先选择医院")
        url = self._portalUrl + "doctor_portal/rest/loginCheck.do"
        url += f"?{self.get_base_params()}"
        d = stringify({
            "logindevicetype": self.LOGINDEVICETYPE,
            "password": sha1(password),
            "fromandroid": self.FROMANDROID,
            "devicetype": self.LOGINDEVICETYPE,
            "deviceid": self.DEVICEID,
            "fromteacher": "1" if self._fromteacher else "0",
            "loginid": loginid,
            "mac": self.DEVICEID,
        })
        re = self._ses.post(url, data={"data": d})
        if re.status_code != 200:
            raise Exception(f"HTTP {re.status_code} {re.reason}")
        return self.check_error2(re.json())

    def init_with_hospital(self, hospital):
        self._portalUrl = f'http://{hospital["portalurl"]}/'

    def init_with_user(self, user):
        self._token = user["token"]

    def query_train_hospital(self):
        url = self._baseUrl + "cloud_doctor_train/rest/trainHospital/query.do"
        url += f"?{self.get_base_params()}"
        d = stringify({
            "logindevicetype": self.LOGINDEVICETYPE,
            "fromteacher": "1" if self._fromteacher else "0",
            "fromandroid": self.FROMANDROID,
        })
        re = self._ses.post(url, data={"data": d})
        if re.status_code != 200:
            raise Exception(f"HTTP {re.status_code} {re.reason}")
        return self.check_error(re.json())


class Main():
    def __init__(self, config, arg):
        self._config = config
        self._arg = arg
        self._client = Client()

    def ask_choice(self, choices: list, prompt="请选择：", fn=None, extra=None):
        count = len(choices)
        total_pages = ceil(count / self._arg.page_size)
        page = 1

        def show_page():
            nonlocal page
            base = (page - 1) * self._arg.page_size
            if total_pages > 1:
                print(f"第{page}/{total_pages}页")
            for i in range(self._arg.page_size):
                index = base + i
                if index >= count:
                    break
                s = fn(choices[index]) if fn else choices[index]
                print(f"{i}. {s}")
            if page > 1:
                print("f. 第一页")
                print("p. 上一页")
            if page < total_pages:
                print("n. 下一页")
                print("l. 最后一页")
            if extra is not None:
                for t in extra:
                    print(f"{t[0]}. {t[1]}")

        while True:
            show_page()
            s = input(prompt)
            if s == "f":
                page = 1
            elif s == "p":
                page = max(1, page - 1)
            elif s == "n":
                page = min(total_pages, page + 1)
            elif s == "l":
                page = total_pages
            else:
                if extra is not None:
                    for t in extra:
                        if t[0] == s:
                            return t[2]
                try:
                    index = int(s)
                except Exception:
                    continue
                base = (page - 1) * self._arg.page_size
                index += base
                if index < 0 or index >= count:
                    continue
                return choices[index]

    def checkIn(self):
        self.init_client()
        if "location" not in self._config:
            self._config["location"] = []
        location = self.ask_choice(self._config["location"], "请选择位置：", lambda x: f'{x["name"]} ({x["longitude"]},{x["latitude"]},{x["localname"]})', [("a", "添加位置", "add")])  # noqa: E501
        if location == "add":
            name = input("请输入位置名称（仅用作标识，不会上传到服务器）：")
            longitude = float(input("请输入经度："))
            latitude = float(input("请输入纬度："))
            localname = input("请输入地名（会在签到时上传到服务器）：")
            location = {
                "name": name,
                "longitude": longitude,
                "latitude": latitude,
                "localname": localname,
                "longitude_radius": 0.00001,
                "latitude_radius": 0.00001,
            }
            while True:
                self.show_location(location)
                s = input("是否需要进行调整？(y/n)")
                if s == "n":
                    break
                elif s == "y":
                    t = {
                        "name": "位置名称",
                        "longitude": "经度",
                        "latitude": "纬度",
                        "localname": "地名",
                        "longitude_radius": "随机化经度半径",
                        "latitude_radius": "随机化纬度半径",
                    }
                    c = self.ask_choice(["name", "longitude", "latitude",
                                         "localname", "longitude_radius",
                                         "latitude_radius"], "请选择要修改的内容：",
                                        lambda x: t[x])
                    if c == "name":
                        location["name"] = input("请输入位置名称：")
                    elif c == "longitude":
                        location["longitude"] = float(input("请输入经度："))
                    elif c == "latitude":
                        location["latitude"] = float(input("请输入纬度："))
                    elif c == "localname":
                        location["localname"] = input("请输入地名：")
                    elif c == "longitude_radius":
                        location["longitude_radius"] = float(
                            input("请输入随机化经度半径："))
                    elif c == "latitude_radius":
                        location["latitude_radius"] = float(
                            input("请输入随机化纬度半径："))
                else:
                    continue
            self._config["location"].append(location)
        print("获取签到信息...")
        data = self._client.get_ningbo_schedule_init_data()
        print("已签到列表：")
        i = 1
        for x in data["signlist"]:
            print(f"{i}.签到时间：{x['signtime']}")
            print(f"地点：{x['longitude']},{x['latitude']}({x['localname']})")
            print(f"签到类型：{x['signtype']}")
            print(f"位置ID：{x['localtionid']}")
            print(f"备注：{x['note']}")
            i += 1
        prompt = f"要进行{data['buttonname']}吗？(y/n)"
        while True:
            s = input(prompt)
            if s == "y":
                break
            elif s == "n":
                return
        localname = location["localname"]
        longitude = round(location["longitude"] + (random() - 0.5) * location["longitude_radius"], 6)  # noqa: E501
        latitude = round(location["latitude"] + (random() - 0.5) * location["latitude_radius"], 6)  # noqa: E501
        note = ""
        if self._arg.note:
            note = self._arg.note
        while True:
            print("经度：", longitude)
            print("纬度：", latitude)
            print("地名：", localname)
            print("备注：", note)
            s = input("是否需要进行调整？(y/n)")
            if s == "n":
                break
            elif s == "y":
                t = {
                    "longitude": "经度",
                    "latitude": "纬度",
                    "localname": "地名",
                    "note": "备注",
                }
                c = self.ask_choice(["longitude", "latitude", "localname",
                                     "note"], "请选择要修改的内容：", lambda x: t[x])
                if c == "longitude":
                    longitude = float(input("请输入经度："))
                elif c == "latitude":
                    latitude = float(input("请输入纬度："))
                elif c == "localname":
                    localname = input("请输入地名：")
                elif c == "note":
                    note = input("请输入备注：")
        print("签到中...")
        self._client.check_in(longitude, latitude, localname, note)
        print("签到成功")

    def get_hospital(self):
        print("获取医院列表...")
        data = self._client.query_train_hospital()
        if self._arg.hospital_id:
            for x in data:
                if x["trainhospitalid"] == self._arg.hospital_id:
                    return x
            raise Exception(f"医院ID {self._arg.hospital_id} 不存在")
        if self._arg.hospital_name:
            for x in data:
                if x["name"] == self._arg.hospital_name:
                    return x
            raise Exception(f"医院名称 {self._arg.hospital_name} 不存在")
        if self._arg.hospital_code:
            for x in data:
                if x["hospitalcode"] == self._arg.hospital_code:
                    return x
            raise Exception(f"医院编码 {self._arg.hospital_code} 不存在")
        return self.ask_choice(data, "请选择医院：", lambda x: x["name"])

    def init_client(self):
        if "hospital" not in self._config or "user" not in self._config:
            self.login()
        else:
            self._client.init_with_hospital(self._config["hospital"])
            self._client.init_with_user(self._config["user"])

    def login(self):
        if "hospital" not in self._config or self._arg.change_hospital:
            self._config["hospital"] = self.get_hospital()
        self._client.init_with_hospital(self._config["hospital"])
        if self._arg.login_id is None:
            self._arg.login_id = input("请输入登录ID：")
        if self._arg.password is None:
            if self._arg.no_getpass:
                self._arg.password = input("请输入密码：")
            else:
                self._arg.password = getpass("请输入密码：")
        print("登录中...")
        self._config["user"] = self._client.login_check(
            self._arg.login_id, self._arg.password)
        self._client.init_with_user(self._config["user"])
        print("登录成功")

    def show_location(self, loc):
        print("位置名称：", loc["name"])
        print("经度：", loc["longitude"])
        print("纬度：", loc["latitude"])
        print("地名：", loc["localname"])
        print("随机化经度半径：", loc["longitude_radius"])
        print("随机化纬度半径：", loc["latitude_radius"])


ACTIONS = ["login", "checkin"]
EACTIONS = ["login2"]


def get_action_str(action):
    if action == "login":
        return "登录"
    elif action == "login2":
        return "登录（重新选择医院）"
    elif action == "checkin":
        return "签到"


def main(args=None):
    p = ArgumentParser()
    p.add_argument("-c", "--config", default="zyys.json", help="配置文件")
    p.add_argument("-l", "--login-id", help="登录ID")
    p.add_argument("-p", "--password", help="密码")
    p.add_argument("--hospital-id", help="医院ID", type=int)
    p.add_argument("--hospital-name", help="医院名称")
    p.add_argument("--hospital-code", help="医院编码")
    p.add_argument("-P", "--page-size", default=10, help="每页数量", type=int)
    p.add_argument("-C", "--change-hospital", action="store_true",
                   help="重新选择医院")
    p.add_argument("--no-getpass", action="store_true", help="不使用getpass")
    p.add_argument("-n", "--note", help="备注")
    p.add_argument("action", choices=ACTIONS, help="操作", nargs="?")
    arg = p.parse_args(args)
    try:
        with open(arg.config) as f:
            config = load(f)
    except Exception:
        config = {}
    m = Main(config, arg)
    if arg.action is None:
        arg.action = m.ask_choice(ACTIONS + EACTIONS, "请选择操作：", get_action_str)
    try:
        if arg.action == "login":
            m.login()
        elif arg.action == "login2":
            arg.change_hospital = True
            m.login()
        elif arg.action == "checkin":
            m.checkIn()
    finally:
        with open(arg.config, "w") as f:
            f.write(stringify(config))


if __name__ == "__main__":
    main()
