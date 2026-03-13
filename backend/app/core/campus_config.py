from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class CampusProfile:
    assistant_name: str
    school_name: str
    short_school_name: str
    primary_campus: str
    supported_locations: Tuple[str, ...]
    location_aliases: Dict[str, Tuple[str, ...]]
    scene_labels: Tuple[str, ...]
    taste_labels: Tuple[str, ...]
    time_labels: Tuple[str, ...]
    hot_keywords: Tuple[str, ...]
    hot_query_template: str
    feedback_success_message: str


CAMPUS_PROFILE = CampusProfile(
    assistant_name="天大吃什么",
    school_name="天津大学",
    short_school_name="TJU",
    primary_campus="北洋园",
    supported_locations=("北洋园", "卫津路"),
    location_aliases={
        "北洋园": ("北洋园", "北洋园校区", "天大北洋园", "天津大学北洋园"),
        "卫津路": ("卫津路", "卫津路校区", "七里台", "天津大学卫津路"),
    },
    scene_labels=("一个人", "同学聚餐"),
    taste_labels=("辣", "清淡"),
    time_labels=("早餐", "午餐", "晚餐", "夜宵"),
    hot_keywords=(
        "夜宵",
        "午饭",
        "晚饭",
        "早餐",
        "一个人",
        "一人食",
        "聚餐",
        "清淡",
        "辣",
        "不辣",
        "火锅",
        "烧烤",
        "面",
        "盖饭",
        "饺子",
        "奶茶",
        "米线",
        "快餐",
        "轻食",
        "食堂",
        "性价比",
        "预算",
    ),
    hot_query_template="{location}附近，{keyword}有什么推荐？",
    feedback_success_message="反馈提交成功，感谢你共建天大北洋园美食地图。",
)
