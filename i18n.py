"""Internationalization (i18n) support for the Todo List application."""

# All translatable strings keyed by ID
STRINGS = {
    # App
    "app_title": {"en": "📝 Todo List", "zh_tw": "📝 待辦清單"},
    "mini_title": {"en": "📝 Todo", "zh_tw": "📝 待辦"},

    # Navigation
    "nav_tasks": {"en": "Tasks", "zh_tw": "任務"},
    "nav_quick": {"en": "Quick", "zh_tw": "快速"},
    "nav_kanban": {"en": "Kanban", "zh_tw": "看板"},
    "nav_history": {"en": "History", "zh_tw": "歷史"},
    "nav_notes": {"en": "Notes", "zh_tw": "記事"},
    "nav_more": {"en": "Menu", "zh_tw": "選單"},

    # Task list
    "task_count": {"en": "{n} Task{s}", "zh_tw": "{n} 個任務"},
    "add_task": {"en": "+ Add Task", "zh_tw": "+ 新增任務"},
    "add_quick": {"en": "+ Add Quick", "zh_tw": "+ 新增快速"},
    "no_tasks": {"en": "No tasks yet. Click '+ Add Task' to get started!", "zh_tw": "目前沒有任務，點擊「+ 新增任務」開始吧！"},
    "all_done": {"en": "All done! 🎉", "zh_tw": "全部完成！🎉"},
    "quick_title": {"en": "⚡ Quick", "zh_tw": "⚡ 快速"},
    "quick_empty": {"en": "No quick items yet. Add one for sudden ideas.", "zh_tw": "目前沒有快速項目，想到就新增一張吧！"},
    "quick_reflow": {"en": "Reflow", "zh_tw": "重新整理"},

    # Mini mode views
    "mini_views_title": {"en": "Mini Window Content", "zh_tw": "迷你視窗顯示內容"},
    "mini_view_tasks": {"en": "Tasks", "zh_tw": "任務"},
    "mini_view_quick": {"en": "Quick", "zh_tw": "快速"},
    "mini_view_kanban": {"en": "Kanban", "zh_tw": "看板"},
    "mini_view_clock": {"en": "Big Clock", "zh_tw": "大時鐘"},
    "mini_cycle_view": {"en": "Switch content", "zh_tw": "切換顯示內容"},
    "mini_select_view": {"en": "Choose content", "zh_tw": "選擇顯示內容"},
    "mini_gadgets_title": {"en": "Mini Gadgets", "zh_tw": "小道具列表"},
    "mini_gadgets_enable": {"en": "Enable gadgets", "zh_tw": "啟用小道具"},
    "mini_gadget_clock": {"en": "Clock", "zh_tw": "時鐘"},
    "mini_gadget_digital": {"en": "Digital Clock", "zh_tw": "數位時鐘"},
    "clock_theme": {"en": "Clock Theme", "zh_tw": "時鐘樣式"},
    "clock_theme_classic": {"en": "Classic", "zh_tw": "經典"},
    "clock_theme_neon": {"en": "Neon", "zh_tw": "霓虹"},
    "clock_theme_minimal": {"en": "Minimal", "zh_tw": "極簡"},
    "clock_am": {"en": "AM", "zh_tw": "上午"},
    "clock_pm": {"en": "PM", "zh_tw": "下午"},

    # Task card
    "no_due_date": {"en": "No due date", "zh_tw": "無截止日期"},
    "overdue_by": {"en": "Overdue by {n} day{s}", "zh_tw": "已逾期 {n} 天"},
    "today": {"en": "Today", "zh_tw": "今天"},
    "tomorrow": {"en": "Tomorrow", "zh_tw": "明天"},
    "days_left": {"en": "{n} days left", "zh_tw": "剩餘 {n} 天"},
    "completed_label": {"en": "Completed: {t}", "zh_tw": "完成時間：{t}"},

    # Dialog - Add/Edit
    "new_task": {"en": "New Task", "zh_tw": "新增任務"},
    "edit_task": {"en": "Edit Task", "zh_tw": "編輯任務"},
    "new_quick": {"en": "New Quick", "zh_tw": "新增快速"},
    "edit_quick": {"en": "Edit Quick", "zh_tw": "編輯快速"},
    "title_required": {"en": "Title *", "zh_tw": "標題 *"},
    "title_placeholder": {"en": "Enter task title...", "zh_tw": "輸入任務標題…"},
    "description": {"en": "Description", "zh_tw": "描述"},
    "desc_placeholder": {"en": "Optional description...", "zh_tw": "選填描述…"},
    "due_date": {"en": "Due Date", "zh_tw": "截止日期"},
    "date_placeholder": {"en": "MM/DD or YYYY/MM/DD (leave empty for none)", "zh_tw": "MM/DD 或 YYYY/MM/DD（留空為無）"},
    "pick_date": {"en": "Pick from calendar", "zh_tw": "從月曆選擇日期"},
    "mark_important": {"en": "  Mark as important (★)", "zh_tw": "  標記為重要 (★)"},
    "task_color": {"en": "Task Color", "zh_tw": "任務顏色"},
    "task_color_custom": {"en": "Custom", "zh_tw": "自訂"},
    "task_color_none": {"en": "None", "zh_tw": "無"},
    "task_color_current": {"en": "Current: {c}", "zh_tw": "目前：{c}"},
    "cancel": {"en": "Cancel", "zh_tw": "取消"},
    "save": {"en": "Save", "zh_tw": "儲存"},

    # Kanban
    "kanban_add_category": {"en": "+ Add Category", "zh_tw": "+ 新增分類"},
    "kanban_show_quick": {"en": "Show Quick", "zh_tw": "顯示快速"},
    "kanban_quick_column": {"en": "Quick", "zh_tw": "快速"},
    "kanban_uncategorized": {"en": "Uncategorized", "zh_tw": "未分類"},
    "kanban_new_category": {"en": "New Category", "zh_tw": "新增分類"},
    "kanban_edit_category": {"en": "Edit Category", "zh_tw": "編輯分類"},
    "kanban_delete_category": {"en": "Delete Category", "zh_tw": "刪除分類"},
    "kanban_delete_category_confirm": {"en": "Delete this category? Tasks will move to Uncategorized.", "zh_tw": "確定刪除此分類？分類中的任務會移到未分類區。"},
    "kanban_category_name": {"en": "Category Name", "zh_tw": "分類名稱"},
    "kanban_category_name_placeholder": {"en": "Enter category name...", "zh_tw": "輸入分類名稱…"},
    "kanban_add_to_category": {"en": "Add task to this category", "zh_tw": "新增到此分類"},
    "kanban_mark_done": {"en": "Mark complete", "zh_tw": "標記完成"},
    "kanban_color_preview": {"en": "Color: {c}", "zh_tw": "顏色：{c}"},
    "kanban_reorder_category": {"en": "Drag to reorder category", "zh_tw": "拖曳以調整分類順序"},

    # Kanban settings
    "kanban_settings_title": {"en": "Kanban Options", "zh_tw": "看板設定"},
    "kanban_min_width": {"en": "Min column width", "zh_tw": "欄位最小寬度"},
    "kanban_auto_complete_toggle": {"en": "Enable Auto-complete column", "zh_tw": "啟用自動完成列"},
    "kanban_auto_complete_column": {"en": "Auto-complete", "zh_tw": "自動完成"},
    "recent_completed_toggle": {"en": "Show Recent Completed", "zh_tw": "顯示近期完成"},
    "recent_completed_column": {"en": "Recent Completed", "zh_tw": "近期完成"},
    "auto_complete_color_default": {"en": "Default Gray", "zh_tw": "預設灰色"},
    "auto_complete_color_light": {"en": "Light Gray", "zh_tw": "淺灰"},
    "auto_complete_color_muted": {"en": "Muted Gray", "zh_tw": "低飽和灰"},
    "backend_unavailable": {"en": "Backend unavailable. Please login again when it comes back online.", "zh_tw": "後端目前無法連線。請在服務恢復後重新登入。"},

    # Dialog - Detail
    "task_details": {"en": "Task Details", "zh_tw": "任務詳情"},
    "status_label": {"en": "Status: {s}", "zh_tw": "狀態：{s}"},
    "status_active": {"en": "Active", "zh_tw": "進行中"},
    "status_completed": {"en": "Completed", "zh_tw": "已完成"},
    "important": {"en": "★ Important", "zh_tw": "★ 重要"},
    "due_label": {"en": "Due: {d}", "zh_tw": "截止：{d}"},
    "created_label": {"en": "Created: {t}", "zh_tw": "建立時間：{t}"},
    "completed_at_label": {"en": "Completed: {t}", "zh_tw": "完成時間：{t}"},
    "close": {"en": "Close", "zh_tw": "關閉"},

    # History
    "no_completed_tasks": {"en": "No completed tasks yet", "zh_tw": "目前沒有已完成的任務"},
    "tab_list": {"en": "📋 List", "zh_tw": "📋 列表"},
    "tab_calendar": {"en": "📅 Calendar", "zh_tw": "📅 月曆"},
    "more_tasks": {"en": "+{n} more", "zh_tw": "+{n} 更多"},

    # Calendar day headers
    "mon": {"en": "Mon", "zh_tw": "一"},
    "tue": {"en": "Tue", "zh_tw": "二"},
    "wed": {"en": "Wed", "zh_tw": "三"},
    "thu": {"en": "Thu", "zh_tw": "四"},
    "fri": {"en": "Fri", "zh_tw": "五"},
    "sat": {"en": "Sat", "zh_tw": "六"},
    "sun": {"en": "Sun", "zh_tw": "日"},

    # Settings
    "settings_title": {"en": "⚙  Settings", "zh_tw": "⚙  設定"},
    "window_opacity": {"en": "Window Opacity", "zh_tw": "視窗透明度"},
    "always_on_top": {"en": "  Always on Top", "zh_tw": "  視窗置頂"},
    "auto_startup": {"en": "  Launch on Windows Startup", "zh_tw": "  Windows 開機自動啟動"},
    "mini_mode_btn": {"en": "🔲  Switch to Mini Mode", "zh_tw": "🔲  切換迷你模式"},
    "mini_size": {"en": "Mini Window Size", "zh_tw": "迷你視窗大小"},
    "reset_default": {"en": "Reset Default", "zh_tw": "恢復預設值"},
    "width": {"en": "Width", "zh_tw": "寬度"},
    "height": {"en": "Height", "zh_tw": "高度"},
    "language_label": {"en": "Language", "zh_tw": "語言"},
    "theme_label": {"en": "Theme", "zh_tw": "主題"},
    "theme_dark": {"en": "Dark", "zh_tw": "深色"},
    "theme_light": {"en": "Light", "zh_tw": "淺色"},
    "color_label": {"en": "Color", "zh_tw": "色彩"},
    "color_purple": {"en": "Purple", "zh_tw": "紫色"},
    "color_blue": {"en": "Blue", "zh_tw": "藍色"},
    "color_green": {"en": "Green", "zh_tw": "綠色"},
    "color_orange": {"en": "Orange", "zh_tw": "橘色"},
    "color_rose": {"en": "Rose", "zh_tw": "玫紅"},

    # Delete confirmations
    "delete_title": {"en": "Delete Task", "zh_tw": "刪除任務"},
    "delete_confirm": {"en": "Are you sure you want to permanently delete this task?", "zh_tw": "確定要永久刪除此任務嗎？"},
    "delete_completed_title": {"en": "Delete Record", "zh_tw": "刪除紀錄"},
    "delete_completed_confirm": {"en": "Are you sure you want to permanently delete this completed record?", "zh_tw": "確定要永久刪除這筆已完成的紀錄嗎？"},

    # Mini-mode
    "restore_tooltip": {"en": "Restore full window", "zh_tw": "還原完整視窗"},
    "mini_mode_kanban": {"en": "Kanban", "zh_tw": "看板"},
    "mini_mode_list": {"en": "List", "zh_tw": "清單"},

    # Notes
    "notes_title": {"en": "📒 Notes", "zh_tw": "📒 記事"},
    "add_note": {"en": "+ Add Note", "zh_tw": "+ 新增記事"},
    "edit_note": {"en": "Edit", "zh_tw": "編輯"},
    "copy_note": {"en": "Copy", "zh_tw": "複製"},
    "delete_note_title": {"en": "Delete Note", "zh_tw": "刪除記事"},
    "delete_note_confirm": {"en": "Are you sure you want to permanently delete this note?", "zh_tw": "確定要永久刪除這則記事嗎？"},
    "no_notes": {"en": "No notes yet. Write something!", "zh_tw": "目前沒有記事，開始寫點什麼吧！"},
    "note_placeholder": {"en": "Write a note...", "zh_tw": "輸入記事內容…"},
}

# Current language
_current_lang = "en"


def set_language(lang: str):
    """Set the current language ('en' or 'zh_tw')."""
    global _current_lang
    if lang in ("en", "zh_tw"):
        _current_lang = lang


def get_language() -> str:
    """Get the current language."""
    return _current_lang


def t(key: str, **kwargs) -> str:
    """Translate a string key to the current language."""
    entry = STRINGS.get(key, {})
    text = entry.get(_current_lang, entry.get("en", f"[{key}]"))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text
