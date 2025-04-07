from typing import Union

JSON = Union[str, int, float, bool, None, dict[str, "JSON"], list["JSON"]]
JSONObject = dict[str, "JSON"]
