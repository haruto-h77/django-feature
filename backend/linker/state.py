# /home/hideaki/src/django-feature/backend/linker/state.py

# 無限ループ対応フラグ
# 削除処理用のフラグもここに追加
SYNC_FLAG = {"from_schedule": False, "from_todo": False, "deleting_from_todo": False}
