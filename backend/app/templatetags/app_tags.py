# 祝日用のフィルタ
from django import template
import datetime

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """辞書からキーで値を取得するフィルタ"""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def is_holiday(holidays_dict, day):
    """指定日が祝日辞書に含まれるか判定するフィルタ"""
    if isinstance(holidays_dict, dict) and isinstance(day, datetime.date):
        return day in holidays_dict
    return False
