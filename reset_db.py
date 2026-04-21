"""重置 todo.db 資料庫腳本（雙重確認）"""
import os
import sys


def _get_data_dir() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


DB_NAME = "todo.db"
DB_PATH = os.path.join(_get_data_dir(), DB_NAME)


def main():
    print("=" * 50)
    print("  Todo List - 重置資料庫")
    print("=" * 50)
    print()

    if not os.path.exists(DB_PATH):
        print(f"[INFO] 資料庫檔案不存在：{DB_PATH}")
        print("[INFO] 無需重置。")
        input("\n按 Enter 結束...")
        return

    file_size = os.path.getsize(DB_PATH)
    print(f"資料庫路徑：{DB_PATH}")
    print(f"檔案大小：{file_size:,} bytes")
    print()

    # 第一次確認
    answer1 = input("⚠️  確定要刪除資料庫嗎？所有任務資料將永久消失！(y/N): ").strip().lower()
    if answer1 != "y":
        print("\n已取消操作。")
        input("按 Enter 結束...")
        return

    # 第二次確認
    print()
    answer2 = input("⚠️⚠️  再次確認：此操作無法復原，真的要刪除嗎？請輸入 'DELETE' 確認: ").strip()
    if answer2 != "DELETE":
        print("\n已取消操作。")
        input("按 Enter 結束...")
        return

    # 執行刪除
    try:
        os.remove(DB_PATH)
        print(f"\n✅ 資料庫已成功刪除：{DB_PATH}")
        print("下次啟動應用程式時將自動建立新的資料庫。")
    except OSError as e:
        print(f"\n❌ 刪除失敗：{e}")
        print("請確保應用程式已關閉後再試。")

    input("\n按 Enter 結束...")


if __name__ == "__main__":
    main()
